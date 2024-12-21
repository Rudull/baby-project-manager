#config_manager.py
#
import configparser
import os
import platform
from pathlib import Path

class ConfigManager:
    def __init__(self):
        # Determinar el directorio de configuración según el sistema operativo
        if platform.system() == 'Windows':
            # En Windows, usar APPDATA si está disponible
            app_data = os.getenv('APPDATA')
            if app_data:
                self.config_dir = Path(app_data) / 'BabyProjectManager'
            else:
                self.config_dir = Path.home() / '.baby-project-manager'
        else:
            # En Linux/Mac, usar el directorio home
            self.config_dir = Path.home() / '.baby-project-manager'

        self.config_file = self.config_dir / 'config.ini'
        self.config = configparser.ConfigParser()

        # Configuraciones por defecto
        self.default_config = {
            'General': {
                'last_directory': str(Path.home()),
                'default_color': '#22a39f',
                'view_mode': 'complete',
                'theme': 'system',
                'language': 'es',
                'last_file': ''
            },
            'RecentFiles': {
                'max_recent_files': '10'
            },
            'Window': {
                'width': '1200',
                'height': '800',
                'pos_x': '100',
                'pos_y': '100'
            }
        }

        self.load_config()

    def load_config(self):
        """Carga la configuración desde el archivo."""
        try:
            # Crear el directorio si no existe
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # Imprimir información de depuración
            print(f"Directorio de configuración: {self.config_dir}")
            print(f"Archivo de configuración: {self.config_file}")

            if self.config_file.exists():
                print("Cargando configuración existente...")
                self.config.read(self.config_file, encoding='utf-8')
            else:
                print("Creando nueva configuración...")

            # Asegurar que existan todas las secciones y valores por defecto
            for section, options in self.default_config.items():
                if not self.config.has_section(section):
                    self.config.add_section(section)
                for key, value in options.items():
                    if not self.config.has_option(section, key):
                        self.config.set(section, key, value)

            self.save_config()
            print("Configuración cargada exitosamente.")
        except Exception as e:
            print(f"Error al cargar la configuración: {e}")

    def save_config(self):
        """Guarda la configuración actual en el archivo."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
        except Exception as e:
            print(f"Error al guardar la configuración: {e}")

    def get(self, section, key, fallback=None):
        """Obtiene un valor de configuración."""
        return self.config.get(section, key, fallback=fallback)

    def set(self, section, key, value):
        """Establece un valor de configuración y lo guarda."""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))
        self.save_config()

    def update_last_directory(self, path):
        """Actualiza el último directorio utilizado."""
        if os.path.exists(path):
            directory = path if os.path.isdir(path) else os.path.dirname(path)
            self.set('General', 'last_directory', directory)

    def add_recent_file(self, file_path):
        """Añade un archivo a la lista de archivos recientes."""
        max_files = self.config.getint('RecentFiles', 'max_recent_files')
        recent_files = []

        # Obtener archivos recientes existentes
        for i in range(max_files):
            key = f'file{i+1}'
            if self.config.has_option('RecentFiles', key):
                path = self.config.get('RecentFiles', key)
                if path != file_path and os.path.exists(path):
                    recent_files.append(path)

        # Insertar el nuevo archivo al inicio
        recent_files.insert(0, file_path)
        recent_files = recent_files[:max_files]

        # Guardar la lista actualizada
        for i, path in enumerate(recent_files):
            self.set('RecentFiles', f'file{i+1}', path)

        # Eliminar entradas sobrantes
        for i in range(len(recent_files), max_files):
            key = f'file{i+1}'
            if self.config.has_option('RecentFiles', key):
                self.config.remove_option('RecentFiles', key)

    def get_recent_files(self):
        """Obtiene la lista de archivos recientes."""
        recent_files = []
        max_files = self.config.getint('RecentFiles', 'max_recent_files')

        for i in range(max_files):
            key = f'file{i+1}'
            if self.config.has_option('RecentFiles', key):
                path = self.config.get('RecentFiles', key)
                if os.path.exists(path):
                    recent_files.append(path)

        return recent_files

    def set_last_file(self, file_path):
        """Guarda la ruta del último archivo abierto."""
        if file_path and os.path.exists(file_path):
            self.set('General', 'last_file', file_path)

    def get_last_file(self):
        """Obtiene la ruta del último archivo abierto."""
        last_file = self.get('General', 'last_file')
        return last_file if last_file and os.path.exists(last_file) else None
