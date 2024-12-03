#loading_animation_widget.py
#
import os
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtGui import QMovie
from PySide6.QtCore import Qt

class LoadingAnimationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Obtener la ruta absoluta del GIF
        gif_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "loading.gif")

        self.loading_label = QLabel(self)
        self.loading_movie = QMovie(gif_path)
        self.loading_label.setMovie(self.loading_movie)
        self.loading_label.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout()
        layout.addWidget(self.loading_label)
        self.setLayout(layout)
        self.hide()

    def start(self):
        self.show()
        self.loading_movie.start()

    def stop(self):
        self.loading_movie.stop()
        self.hide()
