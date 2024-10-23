# conectado con baby 4
import os
import sys
import subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QTextEdit, QFileDialog, QMessageBox
)
from PySide6.QtGui import QFont, QColor, QPalette, QTextCursor, QTextCharFormat
from PySide6.QtCore import Qt, Signal, QEvent

class HyperlinkTextEdit(QTextEdit):
    doubleClicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(True)
        self.hyperlink_format = QTextCharFormat()
        self.normal_format = QTextCharFormat()
        self.file_links = {}
        self.update_colors()
        # Eliminamos la conexión a contentsChanged
        # self.document().contentsChanged.connect(self.update_text_formats)

    def update_colors(self):
        palette = self.palette()
        text_color = palette.color(QPalette.ColorRole.Text)
        link_color = palette.color(QPalette.ColorRole.Link)

        # Determinar si el fondo es oscuro o claro
        bg_color = palette.color(QPalette.ColorRole.Base)
        luminance = 0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue()
        is_dark = luminance < 128  # Umbral para determinar si es oscuro

        if is_dark:
            # Elegir un color de enlace más brillante para fondos oscuros
            link_color = QColor(85, 170, 255)  # Azul claro
        else:
            # Usar el color de enlace del sistema para fondos claros
            link_color = palette.color(QPalette.ColorRole.Link)

        self.hyperlink_format.setForeground(link_color)
        self.hyperlink_format.setFontUnderline(True)
        self.hyperlink_format.setFontItalic(True)
        self.normal_format.setForeground(text_color)
        self.normal_format.setFontUnderline(False)
        self.normal_format.setFontItalic(False)
        self.update_existing_text_formats()  # Actualizar formatos existentes

    def changeEvent(self, event):
        if event.type() == QEvent.Type.PaletteChange:
            self.update_colors()
        super().changeEvent(event)

    def update_existing_text_formats(self):
        # Evitar recursión bloqueando señales
        self.document().blockSignals(True)
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        while not cursor.atEnd():
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
            line_text = cursor.selectedText()
            if line_text.strip() in self.file_links:
                cursor.setCharFormat(self.hyperlink_format)
            else:
                cursor.setCharFormat(self.normal_format)
            cursor.clearSelection()
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
        self.document().blockSignals(False)

    def mouseDoubleClickEvent(self, e):
        cursor = self.cursorForPosition(e.pos())
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        line = cursor.selectedText().strip()
        self.doubleClicked.emit(line)

    def insertHyperlink(self, text):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text, self.hyperlink_format)
        cursor.insertText("\n", self.normal_format)
        self.setTextCursor(cursor)
        self.setCurrentCharFormat(self.normal_format)
        # Aplicar formato inmediatamente
        self.update_existing_text_formats()

    def keyPressEvent(self, e):
        super().keyPressEvent(e)
        self.setCurrentCharFormat(self.normal_format)

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
        self.note_box.doubleClicked.connect(self.open_hyperlink)
        layout.addWidget(self.note_box)

        open_button = QPushButton("Agregar Hipervínculo")
        open_button.clicked.connect(self.open_file)
        layout.addWidget(open_button)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo")
        if file_path:
            file_name = os.path.basename(file_path)
            self.file_links[file_name] = file_path
            self.note_box.file_links[file_name] = file_path
            self.note_box.insertHyperlink(file_name)
            self.note_box.setFocus()

    def open_hyperlink(self, line):
        file_path = self.note_box.file_links.get(line)
        if file_path and os.path.exists(file_path):
            try:
                if sys.platform.startswith('darwin'):
                    subprocess.call(('open', file_path))
                elif sys.platform.startswith('win32'):
                    os.startfile(file_path)
                else:
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
