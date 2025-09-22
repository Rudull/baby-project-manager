#!/usr/bin/env python3
"""
Baby Project Manager - Main Entry Point
"""
import sys
import os

# Add src directory to Python path
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from PySide6.QtWidgets import QApplication
from main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(app.style().standardPalette())

    window = MainWindow()
    window.show()

    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
