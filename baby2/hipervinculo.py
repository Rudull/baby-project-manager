import os
import sys
import subprocess
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QTextEdit, QFileDialog, QMessageBox
)
from PySide6.QtGui import (
    QFont, QColor, QPalette, QTextCursor, QTextCharFormat,
    QTextBlockFormat, QTextOption
)
from PySide6.QtCore import Qt, Signal, QEvent

class HyperlinkTextEdit(QTextEdit):
    """Editor de texto con soporte para hipervínculos."""
    
    doubleClicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_editor()
        self.setup_formats()
        self.setup_ui_properties()

    def setup_editor(self):
        """Configura las propiedades básicas del editor."""
        self.setAcceptRichText(True)
        self.file_links = {}
        self.last_cursor = None
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)

    def setup_formats(self):
        """Configura los formatos de texto."""
        self.hyperlink_format = QTextCharFormat()
        self.normal_format = QTextCharFormat()
        self.update_colors()

    def setup_ui_properties(self):
        """Configura propiedades de la interfaz de usuario."""
        self.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.setMouseTracking(True)

    def update_colors(self):
        """Actualiza los colores según el tema actual."""
        palette = self.palette()
        text_color = palette.color(QPalette.ColorRole.Text)
        bg_color = palette.color(QPalette.ColorRole.Base)
        
        # Determinar si es tema oscuro
        luminance = 0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue()
        is_dark = luminance < 128

        # Configurar color de enlaces
        link_color = QColor(85, 170, 255) if is_dark else palette.color(QPalette.ColorRole.Link)

        # Configurar formatos
        self.setup_link_format(link_color)
        self.setup_normal_format(text_color)
        
        # Actualizar formatos existentes
        self.update_existing_text_formats()

    def setup_link_format(self, color):
        """Configura el formato para hipervínculos."""
        self.hyperlink_format.setForeground(color)
        self.hyperlink_format.setFontUnderline(True)
        self.hyperlink_format.setFontItalic(True)

    def setup_normal_format(self, color):
        """Configura el formato para texto normal."""
        self.normal_format.setForeground(color)
        self.normal_format.setFontUnderline(False)
        self.normal_format.setFontItalic(False)

    def changeEvent(self, e):
        """Maneja cambios en el widget (como cambios de tema)."""
        if e.type() == QEvent.Type.PaletteChange:
            self.update_colors()
        super().changeEvent(e)

    def update_existing_text_formats(self):
        """Actualiza los formatos de texto existentes."""
        self.document().blockSignals(True)
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.MoveOperation.Start)

        while not cursor.atEnd():
            block = cursor.block()
            block_text = block.text().strip()

            if self.is_link_in_block(block_text):
                self.format_link_in_block(cursor, block, block_text)
            else:
                self.format_normal_text(cursor, block)

            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)

        self.document().blockSignals(False)

    def is_link_in_block(self, block_text):
        """Verifica si hay un enlace en el bloque de texto."""
        return any(link in block_text for link in self.file_links.keys())

    def format_link_in_block(self, cursor, block, block_text):
        """Aplica formato de enlace al texto."""
        for link in self.file_links.keys():
            if link in block_text:
                start = block_text.index(link)
                cursor.setPosition(block.position() + start)
                cursor.setPosition(block.position() + start + len(link),
                                QTextCursor.MoveMode.KeepAnchor)
                cursor.setCharFormat(self.hyperlink_format)
                break

    def format_normal_text(self, cursor, block):
        """Aplica formato normal al texto."""
        cursor.setPosition(block.position())
        cursor.setPosition(block.position() + block.length() - 1,
                         QTextCursor.MoveMode.KeepAnchor)
        cursor.setCharFormat(self.normal_format)

    def mouseDoubleClickEvent(self, e):
        """Maneja el evento de doble clic."""
        cursor = self.cursorForPosition(e.pos())
        block = cursor.block()
        block_text = block.text().strip()

        for link in self.file_links.keys():
            if link in block_text:
                self.doubleClicked.emit(link)
                return

        super().mouseDoubleClickEvent(e)

    def mouseMoveEvent(self, e):
        """Maneja el evento de movimiento del mouse."""
        cursor = self.cursorForPosition(e.pos())
        block = cursor.block()
        block_text = block.text().strip()

        is_link = False
        link_text = None
        for link in self.file_links.keys():
            if link in block_text:
                is_link = True
                link_text = link
                break

        self.update_cursor_and_tooltip(is_link, link_text)
        super().mouseMoveEvent(e)

    def update_cursor_and_tooltip(self, is_link, link_text):
        """Actualiza el cursor y el tooltip según la posición."""
        if is_link:
            if self.viewport().cursor().shape() != Qt.CursorShape.PointingHandCursor:
                self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
                self.last_cursor = Qt.CursorShape.PointingHandCursor
            self.setToolTip(f"Abrir: {self.file_links[link_text]}")
        else:
            if self.viewport().cursor().shape() != Qt.CursorShape.IBeamCursor:
                self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
                self.last_cursor = Qt.CursorShape.IBeamCursor
            self.setToolTip("")

    def leaveEvent(self, event):
        """Maneja el evento de salida del mouse."""
        self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
        self.last_cursor = Qt.CursorShape.IBeamCursor
        super().leaveEvent(event)

    def insertHyperlink(self, text):
        """Inserta un hipervínculo en el texto."""
        cursor = self.textCursor()
        
        block_format = QTextBlockFormat()
        block_format.setLineHeight(200, 0)
        block_format.setTextIndent(0)
        block_format.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        cursor.setBlockFormat(block_format)
        cursor.insertText(text, self.hyperlink_format)
        cursor.insertBlock(block_format)
        
        self.setTextCursor(cursor)
        self.setCurrentCharFormat(self.normal_format)
        self.update_existing_text_formats()

    def keyPressEvent(self, e):
        """Maneja el evento de presionar una tecla."""
        super().keyPressEvent(e)
        self.setCurrentCharFormat(self.normal_format)

class NotesApp(QMainWindow):
    """Aplicación de ejemplo para probar HyperlinkTextEdit."""

    def __init__(self):
        super().__init__()
        self.file_links = {}
        self.initUI()

    def initUI(self):
        """Inicializa la interfaz de usuario."""
        self.setWindowTitle("App con Hipervínculos y Nombres de Archivos")
        self.setGeometry(100, 100, 600, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Configurar el editor de notas
        self.note_box = HyperlinkTextEdit()
        self.note_box.setFont(QFont("Arial", 10))
        self.note_box.doubleClicked.connect(self.open_hyperlink)
        layout.addWidget(self.note_box)

        # Agregar botón
        open_button = QPushButton("Agregar Hipervínculo")
        open_button.clicked.connect(self.open_file)
        layout.addWidget(open_button)

    def open_file(self):
        """Abre el diálogo de selección de archivo."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Seleccionar archivo",
                "",
                "Todos los archivos (*.*)"
            )
            if file_path:
                self.add_file_link(file_path)
        except Exception as e:
            self.show_error("Error al seleccionar archivo", str(e))

    def add_file_link(self, file_path):
        """Añade un hipervínculo al archivo seleccionado."""
        file_path = os.path.normpath(file_path)
        file_name = os.path.basename(file_path)
        self.file_links[file_name] = file_path
        self.note_box.file_links[file_name] = file_path
        self.note_box.insertHyperlink(file_name)
        self.note_box.setFocus()

    def open_hyperlink(self, file_name):
        """Abre el archivo vinculado."""
        try:
            file_path = self.note_box.file_links.get(file_name)
            if file_path and os.path.exists(file_path):
                self.open_file_with_default_app(file_path)
            else:
                self.show_error("Error", "No se pudo encontrar el archivo.")
        except Exception as e:
            self.show_error("Error", f"No se pudo abrir el archivo: {str(e)}")

    def open_file_with_default_app(self, file_path):
        """Abre el archivo con la aplicación predeterminada."""
        try:
            if sys.platform.startswith('win32'):
                os.startfile(os.path.normpath(file_path))
            elif sys.platform.startswith('darwin'):
                subprocess.run(['open', file_path], check=True)
            else:
                subprocess.run(['xdg-open', file_path], check=True)
        except Exception as e:
            self.show_error("Error", f"Error al abrir el archivo: {str(e)}")

    def show_error(self, title, message):
        """Muestra un mensaje de error."""
        QMessageBox.warning(self, title, message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    notes_app = NotesApp()
    notes_app.show()
    sys.exit(app.exec())