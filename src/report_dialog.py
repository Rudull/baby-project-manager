import logging
import platform
import sys
import requests
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QLineEdit, QMessageBox, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QDesktopServices, QColor
from secrets_loader import SecretsLoader
from updater.version import __version__

logger = logging.getLogger("bpm.report_dialog")

class ReportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reportar un problema")
        self.setMinimumSize(500, 550)
        self.main_window = parent
        
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Header
        header_label = QLabel("¿Cómo te gustaría reportar el problema?")
        header_label.setObjectName("headerLabel")
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)

        # Option 1: GitHub (Browser)
        github_frame = QFrame()
        github_frame.setObjectName("optionFrame")
        github_layout = QVBoxLayout(github_frame)
        
        github_title = QLabel("Opción 1: GitHub (Recomendado)")
        github_title.setObjectName("optionTitle")
        github_desc = QLabel("Si tienes una cuenta de GitHub, esta es la mejor forma de seguir el progreso del error.")
        github_desc.setWordWrap(True)
        github_desc.setObjectName("optionDesc")
        
        self.github_btn = QPushButton("Abrir GitHub Issues")
        self.github_btn.setCursor(Qt.PointingHandCursor)
        self.github_btn.clicked.connect(self.open_github)
        
        github_layout.addWidget(github_title)
        github_layout.addWidget(github_desc)
        github_layout.addWidget(self.github_btn)
        layout.addWidget(github_frame)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)

        # Option 2: Discord/Direct (In-app)
        discord_frame = QFrame()
        discord_frame.setObjectName("optionFrame")
        discord_layout = QVBoxLayout(discord_frame)
        
        discord_title = QLabel("Opción 2: Reporte Directo")
        discord_title.setObjectName("optionTitle")
        discord_desc = QLabel("Envía un reporte anónimo directamente desde la aplicación. No necesitas ninguna cuenta.")
        discord_desc.setWordWrap(True)
        discord_desc.setObjectName("optionDesc")
        
        # Form
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("Describe el problema detalladamente...")
        self.desc_edit.setMinimumHeight(100)
        
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Tu email (opcional, para contactarte)")
        
        self.send_btn = QPushButton("Enviar Reporte")
        self.send_btn.setObjectName("sendButton")
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.clicked.connect(self.send_direct_report)
        
        if not SecretsLoader.is_discord_available():
            self.send_btn.setEnabled(False)
            self.send_btn.setText("Servicio no configurado")
            discord_desc.setText("El servicio de reporte directo no está configurado (falta URL de Webhook).")

        discord_layout.addWidget(discord_title)
        discord_layout.addWidget(discord_desc)
        discord_layout.addWidget(QLabel("Descripción:"))
        discord_layout.addWidget(self.desc_edit)
        discord_layout.addWidget(QLabel("Contacto (Opcional):"))
        discord_layout.addWidget(self.email_edit)
        discord_layout.addWidget(self.send_btn)
        layout.addWidget(discord_frame)

    def apply_styles(self):
        # Base styles for a premium look
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            #headerLabel {
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 10px;
                color: #ffffff;
            }
            #optionFrame {
                background-color: #2d2d2d;
                border-radius: 10px;
                padding: 15px;
                border: 1px solid #3d3d3d;
            }
            #optionTitle {
                font-weight: bold;
                font-size: 14px;
                color: #22a39f;
            }
            #optionDesc {
                color: #aaaaaa;
                font-size: 12px;
                margin-bottom: 5px;
            }
            QPushButton {
                background-color: #3d3d3d;
                border: none;
                padding: 8px;
                border-radius: 5px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
            #sendButton {
                background-color: #22a39f;
            }
            #sendButton:hover {
                background-color: #2bc1bc;
            }
            #sendButton:disabled {
                background-color: #333333;
                color: #666666;
            }
            QTextEdit, QLineEdit {
                background-color: #1a1a1a;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 5px;
                color: white;
            }
            QLabel {
                color: #dddddd;
            }
        """)

    def open_github(self):
        url = "https://github.com/Rudull/baby-project-manager/issues/new"
        QDesktopServices.openUrl(url)
        self.accept()

    def send_direct_report(self):
        description = self.desc_edit.toPlainText().strip()
        if not description:
            QMessageBox.warning(self, "Error", "Por favor describe el problema antes de enviar.")
            return

        webhook_url = SecretsLoader.get_discord_webhook_url()
        if not webhook_url:
            QMessageBox.critical(self, "Error", "No se encontró la URL del Webhook de Discord.")
            return

        self.send_btn.setEnabled(False)
        self.send_btn.setText("Enviando...")
        
        # Prepare payload with metadata
        sys_info = {
            "version": __version__,
            "os": platform.system(),
            "os_release": platform.release(),
            "python": platform.python_version(),
        }
        
        msg = f"**[NUEVO REPORTE DE ERROR]**\n\n"
        msg += f"**Descripción:**\n{description}\n\n"
        if self.email_edit.text().strip():
            msg += f"**Contacto:** {self.email_edit.text().strip()}\n"
        msg += f"---\n"
        msg += f"**Versión:** {sys_info['version']}\n"
        msg += f"**S.O.:** {sys_info['os']} {sys_info['os_release']}\n"
        msg += f"**Python:** {sys_info['python']}"

        payload = {
            "content": msg,
            "username": "Baby Error Reporter"
        }

        try:
            # Using requests (which is already in requirements.txt)
            response = requests.post(webhook_url, json=payload, timeout=10)
            if response.status_code in [200, 204]:
                QMessageBox.information(self, "Éxito", "Reporte enviado con éxito. ¡Gracias por ayudarnos a mejorar!")
                self.accept()
            else:
                raise Exception(f"Error {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Error sending report to Discord: {e}")
            QMessageBox.critical(self, "Error de Envío", f"No se pudo enviar el reporte: {str(e)}")
            self.send_btn.setEnabled(True)
            self.send_btn.setText("Enviar Reporte")
