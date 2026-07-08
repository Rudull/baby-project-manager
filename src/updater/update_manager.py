"""
update_manager.py
Gestor de actualizaciones automáticas para Baby Project Manager.
Descarga nuevas versiones desde GitHub Releases de forma asíncrona y
notifica a la interfaz mediante señales de Qt.
"""
from __future__ import annotations

import logging
import os
import platform
import re
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger("bpm.updater")


class UpdateManager(QObject):
    """
    Manages the application update process:
    - Checks for updates from GitHub Releases
    - Downloads and installs updates
    - Emits signals to PySide6 UI for progress and notifications
    - Handles application restart and old executable cleanup
    """

    # Signals for asynchronous UI updates
    update_available = Signal(str, str)  # version, download_url
    no_update_available = Signal()
    download_progress = Signal(int)      # percentage (0-100)
    download_complete = Signal()
    error_occurred = Signal(str)         # error message
    log_message = Signal(str)            # info messages to show in UI if needed
    restart_required = Signal()

    def __init__(self, current_version: str, github_repo: str, main_script_path: str | None = None):
        super().__init__()
        self.current_version = current_version
        self.github_repo = github_repo
        self.main_script_path = main_script_path

        self.is_frozen = getattr(sys, 'frozen', False)
        self.latest_version: str | None = None
        self.download_url: str | None = None

    def check_updates(self, manual: bool = False) -> None:
        """Asynchronously check for updates on GitHub Releases."""
        threading.Thread(target=self._check_updates_thread, args=(manual,), daemon=True).start()

    def _check_updates_thread(self, manual: bool) -> None:
        try:
            # Import diferido: requests solo hace falta aquí, en un hilo en
            # segundo plano, no en el arranque de la app.
            try:
                import requests
            except ImportError:
                err = "Requests library is not installed. Cannot check for updates."
                logger.error(err)
                if manual:
                    self.error_occurred.emit(err)
                return

            logger.info("Checking for updates...")
            api_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            headers = {'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}

            response = requests.get(api_url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                tag_name = data.get('tag_name', '')
                version_match = re.search(r'(\d+(?:\.\d+)+)', tag_name)

                if version_match:
                    remote_version = version_match.group(1)
                    logger.info("Local: %s, Remote: %s", self.current_version, remote_version)

                    if manual:
                        self.log_message.emit(f"Local: {self.current_version}, Remota: {remote_version}")

                    if self.is_newer_version(self.current_version, remote_version):
                        self.latest_version = remote_version
                        self.download_url = self._find_asset_url(data)

                        if self.download_url:
                            self.update_available.emit(self.latest_version, self.download_url)
                        else:
                            msg = "Se encontró una nueva versión pero no hay recursos descargables para esta plataforma."
                            if manual:
                                self.error_occurred.emit(msg)
                            logger.warning(msg)
                    else:
                        if manual:
                            self.no_update_available.emit()
                else:
                    msg = f"No se pudo analizar la versión: {tag_name}"
                    logger.warning(msg)
                    if manual:
                        self.error_occurred.emit(msg)
            else:
                if response.status_code == 404:
                    msg = "No se encontraron actualizaciones (releases) publicadas."
                else:
                    msg = f"Error HTTP {response.status_code} al buscar actualizaciones."

                logger.warning(msg)
                if manual:
                    self.error_occurred.emit(msg)

        except Exception as err:
            logger.error("Error checking updates: %s", err, exc_info=True)
            if manual:
                self.error_occurred.emit(str(err))

    def is_newer_version(self, current: str, remote: str) -> bool:
        """Compare two version strings (e.g. 1.2.3 and 1.3.0)."""
        try:
            c_parts = [int(x) for x in current.split('.')]
            r_parts = [int(x) for x in remote.split('.')]
            return r_parts > c_parts
        except Exception:
            return False

    # Asset names that are metadata (checksums, signatures, notes), never the
    # executable itself. Matching these avoids installing e.g. SHA256SUMS as the
    # app binary when the picker falls through to a loose match.
    _NON_BINARY_SUFFIXES = (
        '.txt', '.md', '.html', '.asc', '.sig', '.sha256', '.sha256sum',
        '.sha512', '.sum', '.pem', '.json', '.yml', '.yaml',
    )
    _ARCHIVE_SUFFIXES = (
        '.dmg', '.pkg', '.msi', '.zip', '.tar', '.tar.gz', '.tgz',
        '.deb', '.rpm',
    )

    def _find_asset_url(self, release_data: dict) -> str | None:
        """Find the correct asset URL for the current platform."""
        system = platform.system()

        def is_metadata(name: str) -> bool:
            return name.endswith(self._NON_BINARY_SUFFIXES) or 'sha256sums' in name

        for asset in release_data.get('assets', []):
            name = asset['name'].lower()
            url = asset['browser_download_url']

            if is_metadata(name):
                continue

            if system == "Windows" and name.endswith('.exe'):
                return url
            elif system == "Linux":
                # A raw Linux binary has no extension; explicitly skip Windows,
                # macOS and packaged archives so we only accept the bare binary.
                if name.endswith('.exe') or name.endswith(self._ARCHIVE_SUFFIXES):
                    continue
                if name.endswith('.app'):
                    continue
                return url
            elif system == "Darwin" and (name.endswith('.dmg') or name.endswith('.app')):
                return url

        # Fallback: a single non-metadata, non-archive asset is unambiguous.
        assets = [a for a in release_data.get('assets', [])
                  if not is_metadata(a['name'].lower())
                  and not a['name'].lower().endswith(self._ARCHIVE_SUFFIXES)]
        if len(assets) == 1:
            return assets[0]['browser_download_url']

        return release_data.get('html_url', f"https://github.com/{self.github_repo}/releases/latest")

    def perform_update(self) -> None:
        """Start the download process in a background thread."""
        if not self.download_url or not self.latest_version:
            return

        # If dev mode or it's just a web URL, open browser
        if not self.is_frozen or ("github.com" in self.download_url and "/releases/tag/" in self.download_url):
            webbrowser.open(self.download_url)
            return

        threading.Thread(target=self._download_and_install_thread, daemon=True).start()

    def _download_and_install_thread(self) -> None:
        """Background thread to download and swap executables."""
        try:
            import requests
        except ImportError:
            self.error_occurred.emit("Requests library missing.")
            return

        try:
            current_exe = Path(sys.executable)
            download_dest = current_exe.with_name(f"{current_exe.stem}_update_temp{current_exe.suffix}")

            response = requests.get(self.download_url, stream=True, timeout=60)
            total_size_str = response.headers.get('content-length', '0')
            total_size = int(total_size_str) if total_size_str.isdigit() else 0

            if response.status_code != 200:
                raise Exception(f"Download failed: {response.status_code}")

            block_size = 1024 * 8
            wrote = 0
            last_reported_progress = 0

            with open(download_dest, 'wb') as f:
                for data in response.iter_content(block_size):
                    wrote += len(data)
                    f.write(data)
                    if total_size:
                        progress = int((wrote / total_size) * 100)
                        if progress > last_reported_progress:
                            self.download_progress.emit(progress)
                            last_reported_progress = progress

            # Integrity check: refuse to install a truncated download. Swapping a
            # partial file in as the app executable would leave the user with a
            # broken install and no working binary to relaunch.
            if total_size and wrote != total_size:
                try:
                    download_dest.unlink()
                except OSError:
                    pass
                raise Exception(
                    f"Download incomplete: got {wrote} of {total_size} bytes."
                )

            self.download_complete.emit()

            # Install: backup old exe and swap
            old_exe = current_exe.with_name(current_exe.name + ".old")
            if old_exe.exists():
                try:
                    old_exe.unlink()
                except OSError:
                    pass

            current_exe.rename(old_exe)
            download_dest.rename(current_exe)

            if platform.system() != "Windows":
                try:
                    current_exe.chmod(current_exe.stat().st_mode | 0o755)
                except OSError:
                    pass

            self.restart_required.emit()

        except Exception as e:
            logger.error("Update failed: %s", e, exc_info=True)
            self.error_occurred.emit(str(e))

    def cleanup_old_updates(self) -> None:
        """Remove old executable files (.old) left from previous updates."""
        if not self.is_frozen:
            return

        try:
            current_exe = Path(sys.executable)
            old_exe = current_exe.with_name(current_exe.name + ".old")

            if old_exe.exists():
                old_exe.unlink()
                logger.info("Removed old version: %s", old_exe)
        except Exception as e:
            logger.warning("Could not remove old version: %s", e)

    def restart_application(self) -> None:
        """Restart the application with the new executable."""
        try:
            logger.info("Restarting application to apply updates...")
            sys.stdout.flush()
            sys.stderr.flush()

            if platform.system() == "Windows":
                if self.is_frozen:
                    flags = 0x00000008 | 0x00000200 # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
                    subprocess.Popen([sys.executable] + sys.argv[1:], creationflags=flags, close_fds=True)
                else:
                    if self.main_script_path:
                        args = [sys.executable, self.main_script_path] + sys.argv[1:]
                        subprocess.Popen(args, close_fds=True)
            else:
                if self.is_frozen:
                    os.execv(sys.executable, [sys.executable] + sys.argv[1:])
                elif self.main_script_path:
                    os.execv(sys.executable, [sys.executable, self.main_script_path] + sys.argv[1:])

            import PySide6.QtWidgets
            app = PySide6.QtWidgets.QApplication.instance()
            if app:
                app.quit()
        except Exception as e:
            logger.error("Restart failed: %s", e, exc_info=True)
            raise
