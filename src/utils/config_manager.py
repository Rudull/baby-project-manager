"""config_manager.py
Manages persistent application configuration using INI files.
"""
from __future__ import annotations

import configparser
import logging
import os
import platform
from pathlib import Path

from utils.atomic_io import atomic_write

logger = logging.getLogger("bpm.config")


class ConfigManager:
    def __init__(self) -> None:
        # Determinar el directorio de configuración según el sistema operativo
        if platform.system() == "Windows":
            app_data = os.getenv("APPDATA")
            if app_data:
                self.config_dir = Path(app_data) / "BabyProjectManager"
            else:
                self.config_dir = Path.home() / ".baby-project-manager"
        else:
            self.config_dir = Path.home() / ".baby-project-manager"

        self.config_file = self.config_dir / "config.ini"
        self.config = configparser.ConfigParser()

        # Configuraciones por defecto
        self.default_config: dict[str, dict[str, str]] = {
            "General": {
                "last_directory": str(Path.home()),
                "default_color": "#22a39f",
                "view_mode": "complete",
                "theme": "system",
                "language": "es",
                "last_file": "",
                "start_with_os": "false",
            },
            "RecentFiles": {
                "max_recent_files": "10",
            },
            "Window": {
                "width": "1200",
                "height": "800",
                "pos_x": "100",
                "pos_y": "100",
                "maximized": "false",
            },
            "Columns": {
                "col_1_width": "300",
                "col_2_width": "110",
                "col_3_width": "110",
                "col_4_width": "50",
                "col_5_width": "40",
            },
            "Alerts": {
                "enabled": "true",
                "days_before": "7",
                "check_time": "08:00",
                "show_on_startup": "true",
                "last_shown_date": "",
            },
        }

        self.load_config()

    def load_config(self) -> None:
        """Carga la configuración desde el archivo."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            logger.debug("Config dir: %s", self.config_dir)
            logger.debug("Config file: %s", self.config_file)

            if self.config_file.exists():
                logger.debug("Loading existing configuration...")
                self.config.read(self.config_file, encoding="utf-8")
            else:
                logger.debug("Creating new configuration file...")

            for section, options in self.default_config.items():
                if not self.config.has_section(section):
                    self.config.add_section(section)
                for key, value in options.items():
                    if not self.config.has_option(section, key):
                        self.config.set(section, key, value)

            self.save_config()
            logger.debug("Configuration loaded successfully.")
        except Exception as err:
            logger.error("Error loading configuration: %s", err, exc_info=True)

    def save_config(self) -> None:
        """Guarda la configuración actual en el archivo."""
        try:
            with atomic_write(self.config_file, encoding="utf-8") as f:
                self.config.write(f)
        except OSError as err:
            logger.error("Error saving configuration: %s", err, exc_info=True)

    def get(self, section: str, key: str, fallback: str | None = None) -> str | None:
        """Obtiene un valor de configuración."""
        return self.config.get(section, key, fallback=fallback)

    def set(self, section: str, key: str, value: object) -> None:
        """Establece un valor de configuración y lo guarda."""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))
        self.save_config()

    def update_last_directory(self, path: str) -> None:
        """Actualiza el último directorio utilizado."""
        target = Path(path)
        directory = target if target.is_dir() else target.parent
        if directory.exists():
            self.set("General", "last_directory", str(directory))

    def add_recent_file(self, file_path: str) -> None:
        """Añade un archivo a la lista de archivos recientes."""
        max_files = self.config.getint("RecentFiles", "max_recent_files")
        recent_files: list[str] = []

        for i in range(max_files):
            key = f"file{i + 1}"
            if self.config.has_option("RecentFiles", key):
                path = self.config.get("RecentFiles", key)
                if path and path != file_path and os.path.exists(path):
                    recent_files.append(path)

        recent_files.insert(0, file_path)
        recent_files = recent_files[:max_files]

        for i, path in enumerate(recent_files):
            self.set("RecentFiles", f"file{i + 1}", path)

        for i in range(len(recent_files), max_files):
            key = f"file{i + 1}"
            if self.config.has_option("RecentFiles", key):
                self.config.remove_option("RecentFiles", key)

    def get_recent_files(self) -> list[str]:
        """Obtiene la lista de archivos recientes."""
        recent_files: list[str] = []
        max_files = self.config.getint("RecentFiles", "max_recent_files")

        for i in range(max_files):
            key = f"file{i + 1}"
            if self.config.has_option("RecentFiles", key):
                path = self.config.get("RecentFiles", key)
                if path and os.path.exists(path):
                    recent_files.append(path)

        return recent_files

    def set_last_file(self, file_path: str) -> None:
        """Guarda la ruta del último archivo abierto."""
        if file_path and os.path.exists(file_path):
            self.set("General", "last_file", file_path)

    def get_last_file(self) -> str | None:
        """Obtiene la ruta del último archivo abierto."""
        last_file = self.get("General", "last_file")
        return last_file if last_file and os.path.exists(last_file) else None
