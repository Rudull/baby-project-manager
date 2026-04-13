import os
import sys
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox, 
    QHBoxLayout, QProgressDialog, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, QUrl
from PySide6.QtGui import QPixmap, QDesktopServices, QIcon, QFont
from updater.version import __version__
from resource_helper import get_resource_path

logger = logging.getLogger("bpm.about_dialog")

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Acerca de Baby Project Manager")
        self.setFixedSize(450, 520)
        self.main_window = parent
        
        self.init_ui()
        self.apply_styles()
        self.progress_dialog = None

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Header Section (Logo & Name)
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 30, 20, 20)
        header_layout.setSpacing(10)

        # Attempt to load logo
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        
        # Search for logo in assets using resource_helper
        logo_paths = [
            get_resource_path("assets/icono.ico"),
            get_resource_path("assets/1_baby_project_manager_0-4-3.png"),
        ]
        
        logo_found = False
        for path in logo_paths:
            if path.exists():
                pixmap = QPixmap(str(path))
                if not pixmap.isNull():
                    logo_label.setPixmap(pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    logo_found = True
                    break
        
        if not logo_found:
            logo_label.setText("👶")
            logo_label.setStyleSheet("font-size: 60px;")

        app_name_label = QLabel("Baby Project Manager")
        app_name_label.setObjectName("appName")
        app_name_label.setAlignment(Qt.AlignCenter)

        version_badge = QLabel(f"Versión {__version__}")
        version_badge.setObjectName("versionBadge")
        version_badge.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(logo_label)
        header_layout.addWidget(app_name_label)
        header_layout.addWidget(version_badge)
        main_layout.addWidget(header_frame)

        # Content Section
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(30, 10, 30, 20)
        content_layout.setSpacing(15)

        description = QLabel(
            "Una herramienta ligera y potente para la gestión de proyectos, "
            "diseñada para ser intuitiva y eficiente."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        description.setObjectName("descriptionText")

        credits_label = QLabel("Desarrollado por <b>Rafael Hernandez Bustamante</b>")
        credits_label.setAlignment(Qt.AlignCenter)
        credits_label.setTextFormat(Qt.RichText)
        credits_label.setObjectName("creditsText")

        license_label = QLabel("Licenciado bajo <b>GNU GPL v3</b>")
        license_label.setAlignment(Qt.AlignCenter)
        license_label.setTextFormat(Qt.RichText)
        license_label.setObjectName("licenseText")

        # Links Row
        links_layout = QHBoxLayout()
        links_layout.setSpacing(10)
        
        github_btn = QPushButton("GitHub")
        github_btn.setCursor(Qt.PointingHandCursor)
        github_btn.clicked.connect(lambda: QDesktopServices.openUrl("https://github.com/Rudull"))
        
        linkedin_btn = QPushButton("LinkedIn")
        linkedin_btn.setCursor(Qt.PointingHandCursor)
        linkedin_btn.clicked.connect(lambda: QDesktopServices.openUrl("https://www.linkedin.com/in/rafaelhernandezbustamante"))
        
        license_btn = QPushButton("Licencia")
        license_btn.setCursor(Qt.PointingHandCursor)
        license_btn.clicked.connect(self.show_license)
        
        links_layout.addWidget(github_btn)
        links_layout.addWidget(linkedin_btn)
        links_layout.addWidget(license_btn)

        content_layout.addWidget(description)
        content_layout.addWidget(credits_label)
        content_layout.addWidget(license_label)
        content_layout.addLayout(links_layout)
        main_layout.addWidget(content_frame)

        # Actions Section (Updates & Report)
        actions_frame = QFrame()
        actions_frame.setObjectName("actionsFrame")
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setContentsMargins(30, 10, 30, 30)
        actions_layout.setSpacing(10)

        self.update_status_label = QLabel("")
        self.update_status_label.setAlignment(Qt.AlignCenter)
        self.update_status_label.setObjectName("statusLabel")

        self.check_update_btn = QPushButton("Buscar actualizaciones")
        self.check_update_btn.setObjectName("updateButton")
        self.check_update_btn.setCursor(Qt.PointingHandCursor)
        self.check_update_btn.clicked.connect(self.check_updates_manually)

        self.report_btn = QPushButton("Reportar un problema")
        self.report_btn.setObjectName("reportButton")
        self.report_btn.setCursor(Qt.PointingHandCursor)
        self.report_btn.clicked.connect(lambda: self.main_window.show_report_dialog() if self.main_window else None)

        actions_layout.addWidget(self.update_status_label)
        actions_layout.addWidget(self.check_update_btn)
        actions_layout.addWidget(self.report_btn)
        main_layout.addWidget(actions_frame)

    def apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            #headerFrame {
                background-color: #252525;
                border-bottom: 1px solid #333333;
            }
            #appName {
                font-size: 22px;
                font-weight: bold;
                color: #ffffff;
            }
            #versionBadge {
                color: #22a39f;
                font-weight: bold;
                font-size: 12px;
            }
            #contentFrame {
                background-color: transparent;
            }
            #descriptionText {
                color: #bbbbbb;
                font-size: 13px;
                line-height: 1.4;
            }
            #creditsText {
                color: #ffffff;
                font-size: 14px;
            }
            #licenseText {
                color: #bbbbbb;
                font-size: 13px;
            }
            #statusLabel {
                color: #22a39f;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton {
                background-color: #333333;
                border: 1px solid #444444;
                border-radius: 6px;
                padding: 8px 15px;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #444444;
                border-color: #555555;
            }
            #updateButton {
                background-color: #22a39f;
                border: none;
            }
            #updateButton:hover {
                background-color: #2bc1bc;
            }
            #reportButton {
                background-color: transparent;
                border: 1px solid #22a39f;
                color: #22a39f;
            }
            #reportButton:hover {
                background-color: rgba(34, 163, 159, 0.1);
            }
        """)

    def check_updates_manually(self):
        if not self.main_window or not hasattr(self.main_window, 'update_manager'):
            QMessageBox.warning(self, "Error", "El gestor de actualizaciones no está disponible.")
            return
            
        self.check_update_btn.setEnabled(False)
        self.update_status_label.setText("Buscando actualizaciones...")
        
        um = self.main_window.update_manager
        # Desconectar señales previas para evitar duplicidad si el diálogo se abre/cierra mucho
        self._disconnect_manual_signals()
        
        um.update_available.connect(self.on_update_available_manual)
        um.no_update_available.connect(self.on_no_update_manual)
        um.error_occurred.connect(self.on_update_error_manual)
        um.check_updates(manual=True)

    def on_update_available_manual(self, version, download_url):
        self._disconnect_manual_signals()
        self.update_status_label.setText("¡Actualización encontrada!")
        self.check_update_btn.setEnabled(True)
        
        reply = QMessageBox.question(
            self,
            "Actualización Disponible",
            f"Se ha encontrado la versión {version}. ¿Deseas descargarla e instalarla ahora?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.start_download()

    def on_no_update_manual(self):
        self._disconnect_manual_signals()
        self.update_status_label.setText("Estás en la última versión")
        self.check_update_btn.setEnabled(True)
        QMessageBox.information(self, "Baby Project Manager", "Ya tienes instalada la versión más reciente.")

    def on_update_error_manual(self, error_msg):
        self._disconnect_manual_signals()
        self.update_status_label.setText("Error al buscar")
        self.check_update_btn.setEnabled(True)
        QMessageBox.warning(self, "Error de Actualización", error_msg)

    def _disconnect_manual_signals(self):
        if not self.main_window or not hasattr(self.main_window, 'update_manager'):
            return
        um = self.main_window.update_manager
        # Use a more descriptive way to avoid noisy Qt warnings in some environments
        try:
            um.update_available.disconnect(self.on_update_available_manual)
        except (RuntimeError, TypeError):
            pass
        try:
            um.no_update_available.disconnect(self.on_no_update_manual)
        except (RuntimeError, TypeError):
            pass
        try:
            um.error_occurred.disconnect(self.on_update_error_manual)
        except (RuntimeError, TypeError):
            pass

    def start_download(self):
        um = self.main_window.update_manager
        self.progress_dialog = QProgressDialog("Descargando actualización...", "Cancelar", 0, 100, self)
        self.progress_dialog.setWindowTitle("Actualizando Sistema")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(True)
        
        self._disconnect_download_signals()
        um.download_progress.connect(self.update_download_progress)
        um.download_complete.connect(self.on_download_complete)
        um.error_occurred.connect(self.on_download_error)
        
        self.progress_dialog.show()
        um.perform_update()

    def update_download_progress(self, percentage):
        if self.progress_dialog:
            self.progress_dialog.setValue(percentage)

    def on_download_complete(self):
        self._disconnect_download_signals()
        if self.progress_dialog:
            self.progress_dialog.setValue(100)
            
    def on_download_error(self, error_msg):
        self._disconnect_download_signals()
        if self.progress_dialog:
            self.progress_dialog.cancel()
        QMessageBox.warning(self, "Error de Descarga", error_msg)

    def _disconnect_download_signals(self):
        if not self.main_window or not hasattr(self.main_window, 'update_manager'):
            return
        um = self.main_window.update_manager
        try:
            um.download_progress.disconnect(self.update_download_progress)
            um.download_complete.disconnect(self.on_download_complete)
            um.error_occurred.disconnect(self.on_download_error)
        except RuntimeError:
            pass

    def show_license(self):
        license_path = get_resource_path("LICENSE")
        if license_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(license_path.absolute())))
        else:
            QMessageBox.warning(self, "Error", "No se encontró el archivo de licencia.")
