#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Baby Project Manager
Un gestor de proyectos simple y efectivo.

Este es el punto de entrada principal de la aplicación.
"""

import sys
import os
import platform
import logging
from datetime import datetime
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from main_window import MainWindow

def setup_logging():
    """Configura el sistema de logging."""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, f"bpm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def setup_dark_palette():
    """Configura la paleta de colores para el tema oscuro."""
    dark_palette = QPalette()

    # Colores base
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.Text, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, QColor(35, 35, 35))

    # Colores deshabilitados
    dark_palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
    dark_palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
    dark_palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
    dark_palette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127))

    return dark_palette

def setup_light_palette():
    """Configura la paleta de colores para el tema claro."""
    light_palette = QPalette()

    # Colores base
    light_palette.setColor(QPalette.Window, QColor(240, 240, 240))
    light_palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.Base, QColor(255, 255, 255))
    light_palette.setColor(QPalette.AlternateBase, QColor(233, 233, 233))
    light_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    light_palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.Text, QColor(0, 0, 0))
    light_palette.setColor(QPalette.Button, QColor(240, 240, 240))
    light_palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    light_palette.setColor(QPalette.Link, QColor(0, 122, 255))
    light_palette.setColor(QPalette.Highlight, QColor(0, 122, 255))
    light_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

    # Colores deshabilitados
    light_palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(120, 120, 120))
    light_palette.setColor(QPalette.Disabled, QPalette.Text, QColor(120, 120, 120))
    light_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(120, 120, 120))
    light_palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(180, 180, 180))
    light_palette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(120, 120, 120))

    return light_palette

def detect_system_theme():
    """Detecta el tema del sistema operativo."""
    if platform.system() == 'Windows':
        try:
            import winreg
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return value == 0  # True si es tema oscuro
        except:
            return False
    elif platform.system() == 'Darwin':  # macOS
        try:
            import subprocess
            cmd = 'defaults read -g AppleInterfaceStyle'
            subprocess.check_output(cmd.split())
            return True  # Si no hay error, está en modo oscuro
        except:
            return False
    else:  # Linux y otros
        try:
            import subprocess
            cmd = 'gsettings get org.gnome.desktop.interface gtk-theme'
            theme = subprocess.check_output(cmd.split()).decode().strip().lower()
            return 'dark' in theme
        except:
            return False

def setup_high_dpi():
    """Configura el soporte para pantallas de alta resolución."""
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

def main():
    """Función principal de la aplicación."""
    try:
        # Configurar logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Iniciando Baby Project Manager")

        # Crear la aplicación
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        # Configurar DPI
        setup_high_dpi()

        # Detectar y aplicar tema
        is_dark_theme = detect_system_theme()
        app.setPalette(setup_dark_palette() if is_dark_theme else setup_light_palette())
        
        logger.info(f"Tema detectado: {'oscuro' if is_dark_theme else 'claro'}")

        # Crear y mostrar la ventana principal
        window = MainWindow()
        window.show()

        # Ejecutar el loop principal
        sys.exit(app.exec())

    except Exception as e:
        logger.error(f"Error fatal en la aplicación: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()