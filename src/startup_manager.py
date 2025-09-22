# startup_manager.py
import os
import sys
import platform

class StartupManager:
    def __init__(self, config_manager, app_name="BabyProjectManager"):
        self.app_name = app_name
        self.system = platform.system()
        self.config = config_manager

    def is_startup_enabled(self):
        """Verifica si la aplicación está configurada para iniciar con el sistema."""
        config_enabled = self.config.get('General', 'start_with_os') == 'true'
        system_enabled = self._check_windows_startup() if self.system == 'Windows' else self._check_linux_startup()
        return config_enabled and system_enabled

    def toggle_startup(self):
        """Activa/desactiva el inicio automático."""
        try:
            current_state = self.is_startup_enabled()
            if current_state:
                success = self._remove_startup()
            else:
                success = self._create_startup()

            if success:
                # Actualizar la configuración solo si la operación del sistema fue exitosa
                self.config.set('General', 'start_with_os', str(not current_state).lower())

            return success
        except Exception as e:
            print(f"Error toggling startup: {e}")
            return False

    def _get_executable_path(self):
        """Obtiene la ruta del ejecutable actual."""
        if getattr(sys, 'frozen', False):
            return sys.executable
        return os.path.abspath(sys.argv[0])

    # Métodos específicos para Windows
    def _check_windows_startup(self):
        startup_path = self._get_windows_startup_path()
        return os.path.exists(startup_path)

    def _get_windows_startup_path(self):
        startup_folder = os.path.join(
            os.getenv('APPDATA'),
            r'Microsoft\Windows\Start Menu\Programs\Startup'
        )
        return os.path.join(startup_folder, f"{self.app_name}.lnk")

    def _create_windows_startup(self):
        try:
            from win32com.client import Dispatch

            shortcut_path = self._get_windows_startup_path()
            app_path = self._get_executable_path()

            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = app_path
            shortcut.WorkingDirectory = os.path.dirname(app_path)
            shortcut.save()

            return True
        except Exception as e:
            print(f"Error creating Windows startup shortcut: {e}")
            return False

    def _remove_windows_startup(self):
        try:
            shortcut_path = self._get_windows_startup_path()
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
            return True
        except Exception as e:
            print(f"Error removing Windows startup shortcut: {e}")
            return False

    # Métodos específicos para Linux
    def _check_linux_startup(self):
        desktop_file = self._get_linux_desktop_file()
        return os.path.exists(desktop_file)

    def _get_linux_desktop_file(self):
        return os.path.expanduser(f'~/.config/autostart/{self.app_name.lower()}.desktop')

    def _create_linux_startup(self):
        try:
            autostart_dir = os.path.expanduser('~/.config/autostart')
            os.makedirs(autostart_dir, exist_ok=True)

            desktop_entry = f"""[Desktop Entry]
Type=Application
Name={self.app_name}
Exec={self._get_executable_path()}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
            desktop_file = self._get_linux_desktop_file()
            with open(desktop_file, 'w') as f:
                f.write(desktop_entry)

            os.chmod(desktop_file, 0o755)
            return True
        except Exception as e:
            print(f"Error creating Linux startup entry: {e}")
            return False

    def _remove_linux_startup(self):
        try:
            desktop_file = self._get_linux_desktop_file()
            if os.path.exists(desktop_file):
                os.remove(desktop_file)
            return True
        except Exception as e:
            print(f"Error removing Linux startup entry: {e}")
            return False

    def _create_startup(self):
        """Crea la entrada de inicio automático según el sistema operativo."""
        if self.system == 'Windows':
            return self._create_windows_startup()
        elif self.system == 'Linux':
            return self._create_linux_startup()
        return False

    def _remove_startup(self):
        """Elimina la entrada de inicio automático según el sistema operativo."""
        if self.system == 'Windows':
            return self._remove_windows_startup()
        elif self.system == 'Linux':
            return self._remove_linux_startup()
        return False
