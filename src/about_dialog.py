# about_dialog.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Baby Project Manager")
        self.setFixedSize(400, 300)

        layout = QVBoxLayout()

        # Logo (opcional)
        # logo_label = QLabel()
        # logo_pixmap = QPixmap("path/to/logo.png")
        # logo_label.setPixmap(logo_pixmap.scaled(100, 100, Qt.KeepAspectRatio))
        # logo_label.setAlignment(Qt.AlignCenter)
        # layout.addWidget(logo_label)

        # Versión
        version_label = QLabel("Versión 0.1.0")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(version_label)

        # contacto
        version_label = QLabel("Contacto: www.linkedin.com/in/rafaelhernandezbustamante")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)

        # proyecto
        version_label = QLabel("Proyecto: https://github.com/Rudull")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)

        # Descripción
        description = """

        Desarrollado por: Rafael Hernandez Bustamante.
        """
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        self.setLayout(layout)
