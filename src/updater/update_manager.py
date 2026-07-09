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
import shutil
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

        # For onedir (folder) builds an update is staged next to the install and
        # applied by an external helper after the app exits. When set, this is a
        # (content_root, staging_dir, install_dir) tuple consumed by
        # restart_application(). None means "single-file swap" (the classic path).
        self._pending_folder_update: tuple[Path, Path, Path] | None = None

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
    # Archives we can extract and install as a whole folder (onedir builds).
    # Ordered longest-first so '.tar.gz' matches before '.tar'. Installers such
    # as .dmg/.msi/.deb are deliberately excluded — they are not extract-in-place.
    _FOLDER_ARCHIVE_SUFFIXES = ('.tar.gz', '.tgz', '.tar', '.zip')

    def _find_asset_url(self, release_data: dict) -> str | None:
        """Find the correct asset URL for the current platform."""
        system = platform.system()
        assets = release_data.get('assets', [])

        def is_metadata(name: str) -> bool:
            return name.endswith(self._NON_BINARY_SUFFIXES) or 'sha256sums' in name

        # Tier 1: a native single-file binary for this platform (onefile build).
        for asset in assets:
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

        # Tier 2: a folder-build archive (onedir). Only reached when no native
        # single-file binary was published, so an archive means "extract and
        # replace the whole install". Linux/macOS prefer tarballs because they
        # preserve the executable bit and symlinks; .zip loses both.
        if system == "Windows":
            archive_prefs = ('.zip',)
        else:
            archive_prefs = ('.tar.gz', '.tgz', '.zip')
        for ext in archive_prefs:
            for asset in assets:
                name = asset['name'].lower()
                if is_metadata(name):
                    continue
                if name.endswith(ext):
                    return asset['browser_download_url']

        # Fallback: a single non-metadata, non-archive asset is unambiguous.
        loose = [a for a in assets
                 if not is_metadata(a['name'].lower())
                 and not a['name'].lower().endswith(self._ARCHIVE_SUFFIXES)]
        if len(loose) == 1:
            return loose[0]['browser_download_url']

        return release_data.get('html_url', f"https://github.com/{self.github_repo}/releases/latest")

    @classmethod
    def _url_archive_suffix(cls, url: str | None) -> str | None:
        """Return the folder-archive suffix of a URL, or None if not an archive."""
        if not url:
            return None
        path = url.split('?', 1)[0].split('#', 1)[0].lower()
        for suffix in cls._FOLDER_ARCHIVE_SUFFIXES:
            if path.endswith(suffix):
                return suffix
        return None

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
        """Background thread to download and install an update.

        Routes to the folder (onedir) or single-file (onefile) installer based
        on the asset type: an archive URL replaces the whole install directory,
        anything else swaps the single executable in place.
        """
        try:
            import requests  # noqa: F401  # fail fast if unavailable
        except ImportError:
            self.error_occurred.emit("Requests library missing.")
            return

        try:
            if self._url_archive_suffix(self.download_url):
                self._download_and_stage_archive()
            else:
                self._download_and_swap_single_file()
        except Exception as e:
            logger.error("Update failed: %s", e, exc_info=True)
            self.error_occurred.emit(str(e))

    def _download_to(self, url: str, dest: Path) -> None:
        """Stream ``url`` to ``dest``, reporting progress and verifying size.

        Raises if the download is truncated. On truncation the partial file is
        removed so a broken download is never mistaken for a complete one.
        """
        import requests

        response = requests.get(url, stream=True, timeout=60)
        if response.status_code != 200:
            raise Exception(f"Download failed: {response.status_code}")

        total_size_str = response.headers.get('content-length', '0')
        total_size = int(total_size_str) if total_size_str.isdigit() else 0

        block_size = 1024 * 8
        wrote = 0
        last_reported_progress = 0

        with open(dest, 'wb') as f:
            for data in response.iter_content(block_size):
                wrote += len(data)
                f.write(data)
                if total_size:
                    progress = int((wrote / total_size) * 100)
                    if progress > last_reported_progress:
                        self.download_progress.emit(progress)
                        last_reported_progress = progress

        if total_size and wrote != total_size:
            try:
                dest.unlink()
            except OSError:
                pass
            raise Exception(f"Download incomplete: got {wrote} of {total_size} bytes.")

    def _download_and_swap_single_file(self) -> None:
        """Download and swap a single-file (onefile) executable in place."""
        current_exe = Path(sys.executable)
        download_dest = current_exe.with_name(f"{current_exe.stem}_update_temp{current_exe.suffix}")

        self._download_to(self.download_url, download_dest)
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

    def _download_and_stage_archive(self) -> None:
        """Download and extract a folder (onedir) build ready to be installed.

        The archive is expanded into a staging directory beside the install. The
        running executable and its DLLs are locked while the app is live, so the
        actual folder swap is deferred to an external helper spawned at restart
        (see _apply_folder_update_and_restart).
        """
        suffix = self._url_archive_suffix(self.download_url) or ".zip"
        install_dir = Path(sys.executable).resolve().parent
        parent = install_dir.parent

        staging_dir = parent / (install_dir.name + "_update_staging")
        archive_dest = parent / ("_bpm_update" + suffix)

        # Clear leftovers from a previous interrupted attempt.
        if staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)
        if archive_dest.exists():
            try:
                archive_dest.unlink()
            except OSError:
                pass

        self._download_to(self.download_url, archive_dest)
        self.download_complete.emit()

        staging_dir.mkdir(parents=True, exist_ok=True)
        self._extract_archive(archive_dest, staging_dir)
        try:
            archive_dest.unlink()
        except OSError:
            pass

        content_root = self._normalize_extracted_root(staging_dir, Path(sys.executable).name)
        self._pending_folder_update = (content_root, staging_dir, install_dir)
        self.restart_required.emit()

    def _extract_archive(self, archive_path: Path, dest_dir: Path) -> None:
        """Extract a .zip or .tar(.gz) archive into ``dest_dir`` safely."""
        name = archive_path.name.lower()
        if name.endswith(('.tar.gz', '.tgz', '.tar')):
            import tarfile
            with tarfile.open(archive_path) as tf:
                self._safe_extract_tar(tf, dest_dir)
        elif name.endswith('.zip'):
            import zipfile
            with zipfile.ZipFile(archive_path) as zf:
                self._safe_extract_zip(zf, dest_dir)
        else:
            raise Exception(f"Unsupported archive type: {archive_path.name}")

    @staticmethod
    def _is_within(base: Path, target: str) -> bool:
        """True if ``target`` (joined onto ``base``) stays inside ``base``."""
        base_r = os.path.realpath(base)
        target_r = os.path.realpath(os.path.join(base_r, target))
        try:
            return os.path.commonpath([base_r, target_r]) == base_r
        except ValueError:
            # Different drives on Windows — definitely an escape.
            return False

    def _safe_extract_zip(self, zf, dest_dir: Path) -> None:
        """Extract a zip, rejecting members that would escape ``dest_dir``."""
        for name in zf.namelist():
            if not self._is_within(dest_dir, name):
                raise Exception(f"Unsafe path in archive: {name}")
        zf.extractall(dest_dir)

    def _safe_extract_tar(self, tf, dest_dir: Path) -> None:
        """Extract a tar, rejecting members that would escape ``dest_dir``."""
        try:
            # Python 3.12+: the 'data' filter blocks traversal and unsafe members.
            tf.extractall(dest_dir, filter="data")
            return
        except TypeError:
            pass  # Older Python without extraction filters — validate manually.
        for member in tf.getmembers():
            if not self._is_within(dest_dir, member.name):
                raise Exception(f"Unsafe path in archive: {member.name}")
        tf.extractall(dest_dir)

    def _normalize_extracted_root(self, staging_dir: Path, exe_name: str) -> Path:
        """Return the directory that actually holds the app files.

        Archives are sometimes wrapped in a single top-level folder
        (``app/...``) and sometimes not (files at the root). Descend into a lone
        wrapper directory so the caller always copies the real install tree.
        """
        entries = list(staging_dir.iterdir())
        # Must be the executable *file* at the top — not a wrapper directory that
        # happens to share the exe's name (on Linux both are 'baby_project_manager').
        if any(p.name == exe_name and p.is_file() for p in entries):
            return staging_dir
        dirs = [p for p in entries if p.is_dir()]
        files = [p for p in entries if p.is_file()]
        if len(dirs) == 1 and not files:
            return dirs[0]
        return staging_dir

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

            # A staged folder (onedir) update cannot be applied while the app is
            # running because its files are locked. Hand off to an external
            # helper that waits for exit, swaps the folder, and relaunches.
            if self._pending_folder_update:
                self._apply_folder_update_and_restart()
                return

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

    # ------------------------------------------------------------------
    # Folder (onedir) update application
    # ------------------------------------------------------------------

    def _apply_folder_update_and_restart(self) -> None:
        """Spawn the external helper that swaps the folder and relaunches.

        The helper is detached so it outlives this process; we then quit so the
        install directory's files unlock and the copy can proceed.
        """
        content_root, staging_dir, install_dir = self._pending_folder_update
        exe_path = Path(sys.executable)

        if platform.system() == "Windows":
            script = self._write_windows_swap_script(content_root, staging_dir, install_dir, exe_path)
            flags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
            subprocess.Popen(["cmd", "/c", str(script)], creationflags=flags, close_fds=True)
        else:
            script = self._write_posix_swap_script(content_root, staging_dir, install_dir, exe_path)
            subprocess.Popen(["/bin/sh", str(script)], start_new_session=True, close_fds=True)

        import PySide6.QtWidgets
        app = PySide6.QtWidgets.QApplication.instance()
        if app:
            app.quit()

    def _write_windows_swap_script(self, content_root: Path, staging_dir: Path,
                                   install_dir: Path, exe_path: Path) -> Path:
        """Write a .bat that waits for exit, mirrors the new files, relaunches."""
        pid = os.getpid()
        script_path = install_dir.parent / "_bpm_update_apply.bat"
        # robocopy /E copies the whole tree and overwrites; /IS /IT force files
        # that look unchanged to be refreshed too. It is present on all supported
        # Windows versions, unlike xcopy edge cases.
        lines = [
            "@echo off",
            "setlocal",
            f'set "PID={pid}"',
            f'set "SRC={content_root}"',
            f'set "STG={staging_dir}"',
            f'set "DST={install_dir}"',
            f'set "EXE={exe_path}"',
            ":waitloop",
            'tasklist /FI "PID eq %PID%" 2>nul | find "%PID%" >nul',
            "if not errorlevel 1 (",
            "    ping -n 2 127.0.0.1 >nul",
            "    goto waitloop",
            ")",
            'robocopy "%SRC%" "%DST%" /E /IS /IT /R:2 /W:1 /NFL /NDL /NJH /NJS >nul',
            'rmdir /S /Q "%STG%"',
            'start "" "%EXE%"',
            'del "%~f0"',
        ]
        script_path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
        return script_path

    def _write_posix_swap_script(self, content_root: Path, staging_dir: Path,
                                 install_dir: Path, exe_path: Path) -> Path:
        """Write a shell script that waits for exit, copies files, relaunches."""
        pid = os.getpid()
        script_path = install_dir.parent / "_bpm_update_apply.sh"
        src_q = self._sh_quote(str(content_root))
        stg_q = self._sh_quote(str(staging_dir))
        dst_q = self._sh_quote(str(install_dir))
        exe_q = self._sh_quote(str(exe_path))
        lines = [
            "#!/bin/sh",
            f"PID={pid}",
            # Wait for the app to exit so its files unlock. Treat a zombie (Z)
            # process as gone: kill -0 still succeeds on a not-yet-reaped process.
            'while kill -0 "$PID" 2>/dev/null; do',
            '    case "$(ps -o stat= -p "$PID" 2>/dev/null)" in *Z*) break;; esac',
            "    sleep 0.5",
            "done",
            # 'SRC/.' copies the directory contents (including dotfiles) into DST.
            f"cp -a {src_q}/. {dst_q}/ 2>/dev/null",
            f"rm -rf {stg_q}",
            f"chmod +x {exe_q} 2>/dev/null",
            f"{exe_q} &",
            'rm -- "$0"',
        ]
        script_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        try:
            script_path.chmod(0o755)
        except OSError:
            pass
        return script_path

    @staticmethod
    def _sh_quote(value: str) -> str:
        """Single-quote a string for safe POSIX shell embedding."""
        return "'" + value.replace("'", "'\\''") + "'"
