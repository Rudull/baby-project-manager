#loading_animation_widget.py
#
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtGui import QMovie
from PySide6.QtCore import Qt

class LoadingAnimationWidget(QWidget):
    def __init__(self, parent=None, movie_file="loading.gif"):
        super().__init__(parent)
        self.loading_label = QLabel(self)
        self.loading_movie = QMovie(movie_file)
        self.loading_label.setMovie(self.loading_movie)
        self.loading_label.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout()
        layout.addWidget(self.loading_label)
        self.setLayout(layout)
        self.hide()  # Comienza oculto

    def start(self):
        self.show()
        self.loading_movie.start()

    def stop(self):
        self.loading_movie.stop()
        self.hide()
