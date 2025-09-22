#loading_animation_widget.py
#
import os
from PySide6.QtWidgets import QWidget, QVBoxLayout
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    QWebEngineView = None
    WEBENGINE_AVAILABLE = False
from PySide6.QtCore import Qt, QUrl

class LoadingAnimationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Establecer el widget como hijo de la ventana principal
        self.setParent(parent)
        self.setWindowFlags(Qt.Widget | Qt.FramelessWindowHint)

        if WEBENGINE_AVAILABLE:
            # Crear el widget web
            self.web_view = QWebEngineView()

            # Habilitar fondo transparente
            self.web_view.page().setBackgroundColor(Qt.transparent)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.web_view.setAttribute(Qt.WA_TranslucentBackground)

            # Obtener la ruta absoluta del HTML
            html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "loading.html")
            html_url = QUrl.fromLocalFile(html_path)

            # Cargar el archivo HTML
            self.web_view.load(html_url)

            # Configurar el layout para que ocupe todo el espacio disponible
            layout = QVBoxLayout()
            layout.addWidget(self.web_view)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            self.setLayout(layout)
        else:
            # Fallback: crear un label simple con texto de carga
            from PySide6.QtWidgets import QLabel
            from PySide6.QtCore import Qt

            self.web_view = QLabel("Cargando...")
            self.web_view.setAlignment(Qt.AlignCenter)
            self.web_view.setStyleSheet("color: #22A39F; font-size: 16px; font-weight: bold;")

            layout = QVBoxLayout()
            layout.addWidget(self.web_view)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            self.setLayout(layout)

        # Ocultar inicialmente
        self.hide()

    def start(self):
        if self.parent():
            # Hacer que ocupe todo el espacio de la ventana principal
            self.setGeometry(self.parent().rect())
            self.web_view.setGeometry(self.rect())
        self.show()
        self.raise_()
        if WEBENGINE_AVAILABLE and hasattr(self.web_view, 'reload'):
            self.web_view.reload()

    def stop(self):
        self.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.parent():
            # Actualizar tamaño cuando la ventana principal cambie de tamaño
            self.setGeometry(self.parent().rect())
            if hasattr(self.web_view, 'setGeometry'):
                self.web_view.setGeometry(self.rect())
