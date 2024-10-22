import os
import sys
import subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QTextEdit, QFileDialog, QMessageBox
)
from PySide6.QtGui import QFont, QColor, QPalette, QTextCursor, QTextCharFormat
from PySide6.QtCore import Qt, Signal

class HyperlinkTextEdit(QTextEdit):
    doubleClicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(True)
        self.hyperlink_format = QTextCharFormat()
        self.hyperlink_format.setForeground(QColor(0, 0, 255))  # Color azul
        self.hyperlink_format.setFontUnderline(True)
        self.hyperlink_format.setFontItalic(True)

        self.normal_format = QTextCharFormat()
        self.normal_format.setForeground(QColor(0, 0, 0))  # Color negro
        self.normal_format.setFontUnderline(False)
        self.normal_format.setFontItalic(False)

    def mouseDoubleClickEvent(self, event):
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        line = cursor.selectedText().strip()
        self.doubleClicked.emit(line)

    def insertHyperlink(self, text):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text, self.hyperlink_format)
        cursor.insertText(" ", self.normal_format)  # Añade un espacio con formato normal
        self.setTextCursor(cursor)  # Coloca el cursor después del espacio
        self.setCurrentCharFormat(self.normal_format)  # Establece el formato normal para el texto siguiente

class NotesApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.file_links = {}
        self.initUI()

    def initUI(self):
        self.setWindowTitle("App con Hipervínculos y Nombres de Archivos")
        self.setGeometry(100, 100, 600, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.note_box = HyperlinkTextEdit()
        self.note_box.setFont(QFont("Arial", 10))
        self.note_box.setStyleSheet("""
            QTextEdit {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """)
        self.note_box.doubleClicked.connect(self.open_hyperlink)
        layout.addWidget(self.note_box)

        open_button = QPushButton("Agregar Hipervínculo")
        open_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        open_button.clicked.connect(self.open_file)
        layout.addWidget(open_button)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo")
        if file_path:
            file_name = os.path.basename(file_path)
            self.file_links[file_name] = file_path
            self.note_box.insertHyperlink(file_name)
            self.note_box.setFocus()  # Asegura que el foco vuelva al note_box después de insertar el hipervínculo

    def open_hyperlink(self, line):
        file_path = self.file_links.get(line)
        if file_path and os.path.exists(file_path):
            try:
                if sys.platform.startswith('darwin'):  # macOS
                    subprocess.call(('open', file_path))
                elif sys.platform.startswith('win32'):  # Windows
                    os.startfile(file_path)
                else:  # Linux y otros sistemas Unix
                    subprocess.call(('xdg-open', file_path))
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo abrir el archivo: {str(e)}")
        else:
            QMessageBox.warning(self, "Error", "No se pudo abrir el archivo.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    notes_app = NotesApp()
    notes_app.show()
    sys.exit(app.exec())
