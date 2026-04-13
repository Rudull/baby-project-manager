"""startup_manager.py
Manages application auto-start configuration for Windows and Linux.
"""
from __future__ import annotations

import logging
import os
import platform
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config_manager import ConfigManager

logger = logging.getLogger("bpm.startup")


class StartupManager:
    def __init__(
        self, config_manager: ConfigManager, app_name: str = "BabyProjectManager"
    ) -> None:
        self.app_name = app_name
        self.system = platform.system()
        self.config = config_manager

    def is_startup_enabled(self) -> bool:
        """Verifica si la aplicación está configurada para iniciar con el sistema."""
        config_enabled = self.config.get("General", "start_with_os") == "true"
        system_enabled = (
            self._check_windows_startup()
            if self.system == "Windows"
            else self._check_linux_startup()
        )
        return config_enabled and system_enabled

    def toggle_startup(self) -> bool:
        """Activa/desactiva el inicio automático."""
        try:
            current_state = self.is_startup_enabled()
            success = self._remove_startup() if current_state else self._create_startup()
            if success:
                self.config.set("General", "start_with_os", str(not current_state).lower())
            return success
        except Exception as err:
            logger.error("Error toggling startup: %s", err, exc_info=True)
            return False

    def _get_executable_path(self) -> str:
        """Obtiene la ruta del ejecutable actual."""
        if getattr(sys, "frozen", False):
            return sys.executable
        return os.path.abspath(sys.argv[0])

    # ---------- Windows ----------

    def _check_windows_startup(self) -> bool:
        return os.path.exists(self._get_windows_startup_path())

    def _get_windows_startup_path(self) -> str:
        startup_folder = os.path.join(
            os.getenv("APPDATA", ""),
            r"Microsoft\Windows\Start Menu\Programs\Startup",
        )
        return os.path.join(startup_folder, f"{self.app_name}.lnk")

    def _create_windows_startup(self) -> bool:
        try:
            from win32com.client import Dispatch  # type: ignore[import]

            shortcut_path = self._get_windows_startup_path()
            app_path = self._get_executable_path()
            shell = Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = app_path
            shortcut.WorkingDirectory = os.path.dirname(app_path)
            shortcut.save()
            return True
        except Exception as err:
            logger.error("Error creating Windows startup shortcut: %s", err, exc_info=True)
            return False

    def _remove_windows_startup(self) -> bool:
        try:
            shortcut_path = self._get_windows_startup_path()
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
            return True
        except OSError as err:
            logger.error("Error removing Windows startup shortcut: %s", err, exc_info=True)
            return False

    # ---------- Linux ----------

    def _check_linux_startup(self) -> bool:
        return os.path.exists(self._get_linux_desktop_file())

    def _get_linux_desktop_file(self) -> str:
        return os.path.expanduser(
            f"~/.config/autostart/{self.app_name.lower()}.desktop"
        )

    def _create_linux_startup(self) -> bool:
        try:
            autostart_dir = Path.home() / ".config" / "autostart"
            autostart_dir.mkdir(parents=True, exist_ok=True)
            desktop_entry = (
                "[Desktop Entry]\n"
                "Type=Application\n"
                f"Name={self.app_name}\n"
                f"Exec={self._get_executable_path()}\n"
                "Hidden=false\n"
                "NoDisplay=false\n"
                "X-GNOME-Autostart-enabled=true\n"
            )
            desktop_file = Path(self._get_linux_desktop_file())
            desktop_file.write_text(desktop_entry, encoding="utf-8")
            desktop_file.chmod(0o755)
            return True
        except OSError as err:
            logger.error("Error creating Linux startup entry: %s", err, exc_info=True)
            return False

    def _remove_linux_startup(self) -> bool:
        try:
            desktop_file = Path(self._get_linux_desktop_file())
            if desktop_file.exists():
                desktop_file.unlink()
            return True
        except OSError as err:
            logger.error("Error removing Linux startup entry: %s", err, exc_info=True)
            return False

    def _create_startup(self) -> bool:
        """Crea la entrada de inicio automático según el sistema operativo."""
        if self.system == "Windows":
            return self._create_windows_startup()
        if self.system == "Linux":
            return self._create_linux_startup()
        return False

    def _remove_startup(self) -> bool:
        """Elimina la entrada de inicio automático según el sistema operativo."""
        if self.system == "Windows":
            return self._remove_windows_startup()
        if self.system == "Linux":
            return self._remove_linux_startup()
        return False
