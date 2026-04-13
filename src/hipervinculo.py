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
    QTextBlockFormat, QTextOption, QKeySequence, QShortcut
)
from PySide6.QtCore import Qt, Signal, QEvent

class HyperlinkTextEdit(QTextEdit):
    doubleClicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(True)
        self.hyperlink_format = QTextCharFormat()
        self.normal_format = QTextCharFormat()
        self.file_links = {}
        self.setWordWrapMode(QTextOption.WordWrap)
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.update_colors()
        self.setMouseTracking(True)
        self.last_cursor = None
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)

    def keyPressEvent(self, event):
        # Solo mantener los atajos básicos Ctrl+C, Ctrl+V, Ctrl+X, Ctrl+A
        modifiers = event.modifiers()
        if modifiers == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_C:
                self.copy()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_V:
                self.paste()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_X:
                self.cut()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_A:
                self.selectAll()
                event.accept()
                return
        super().keyPressEvent(event)

    def update_colors(self):
        palette = self.palette()
        text_color = palette.color(QPalette.ColorRole.Text)
        link_color = palette.color(QPalette.ColorRole.Link)

        bg_color = palette.color(QPalette.ColorRole.Base)
        luminance = 0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue()
        is_dark = luminance < 128  # Umbral para determinar si es oscuro

        if is_dark:
            link_color = QColor(85, 170, 255)  # Azul claro
        else:
            link_color = palette.color(QPalette.ColorRole.Link)

        self.hyperlink_format.setForeground(link_color)
        self.hyperlink_format.setFontUnderline(True)
        self.hyperlink_format.setFontItalic(True)
        self.normal_format.setForeground(text_color)
        self.normal_format.setFontUnderline(False)
        self.normal_format.setFontItalic(False)
        self.update_existing_text_formats()

    def changeEvent(self, e):
        if e.type() == QEvent.Type.PaletteChange:
            self.update_colors()
        super().changeEvent(e)

    def update_existing_text_formats(self):
        self.document().blockSignals(True)

        # Guardar la selección actual
        cursor = self.textCursor()
        saved_selection = (cursor.selectionStart(), cursor.selectionEnd())

        # Aplicar formato normal a todo el documento
        doc_cursor = QTextCursor(self.document())
        doc_cursor.select(QTextCursor.SelectionType.Document)
        doc_cursor.setCharFormat(self.normal_format)

        # Restaurar hipervínculos
        for link in self.file_links.keys():
            cursor = QTextCursor(self.document())
            while True:
                # Buscar la siguiente ocurrencia del hipervínculo
                cursor = self.document().find(link, cursor)
                if cursor.isNull():
                    break
                cursor.setCharFormat(self.hyperlink_format)

        # Restaurar la selección original
        restore_cursor = self.textCursor()
        restore_cursor.setPosition(saved_selection[0])
        restore_cursor.setPosition(saved_selection[1],
                                 QTextCursor.MoveMode.KeepAnchor)
        self.setTextCursor(restore_cursor)

        self.document().blockSignals(False)

    def mouseDoubleClickEvent(self, e):
        cursor = self.cursorForPosition(e.pos())
        block = cursor.block()
        block_text = block.text().strip()

        for link in self.file_links.keys():
            if link in block_text:
                self.doubleClicked.emit(link)
                return

        super().mouseDoubleClickEvent(e)

    def mouseMoveEvent(self, e):
        # Manejar la selección durante el arrastre
        super().mouseMoveEvent(e)
        if e.buttons() & Qt.MouseButton.LeftButton:  # Si está arrastrando con botón izquierdo
            cursor = self.textCursor()
            if cursor.hasSelection():
                # Preservar el formato original mientras se arrastra
                self.update_selection_formats(cursor)
                return

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

        if is_link:
            if self.viewport().cursor().shape() != Qt.CursorShape.PointingHandCursor:
                self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
                self.last_cursor = Qt.CursorShape.PointingHandCursor

            file_path = self.file_links[link_text]
            self.setToolTip(f"Abrir: {file_path}")
        else:
            if self.viewport().cursor().shape() != Qt.CursorShape.IBeamCursor:
                self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
                self.last_cursor = Qt.CursorShape.IBeamCursor
            self.setToolTip("")

    def update_selection_formats(self, cursor):
        if not cursor.hasSelection():
            return

        # Guardar la posición actual
        start = cursor.selectionStart()
        end = cursor.selectionEnd()

        # Restaurar formato normal
        restore_cursor = QTextCursor(self.document())
        restore_cursor.setPosition(start)
        restore_cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        restore_cursor.setCharFormat(self.normal_format)

        # Restaurar hipervínculos
        selected_text = restore_cursor.selectedText()
        for link in self.file_links.keys():
            pos = 0
            while True:
                pos = selected_text.find(link, pos)
                if pos == -1:
                    break

                link_cursor = QTextCursor(self.document())
                absolute_pos = start + pos
                link_cursor.setPosition(absolute_pos)
                link_cursor.setPosition(absolute_pos + len(link),
                                     QTextCursor.MoveMode.KeepAnchor)
                link_cursor.setCharFormat(self.hyperlink_format)

                pos += len(link)

    def leaveEvent(self, event):
        self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
        self.last_cursor = Qt.CursorShape.IBeamCursor
        super().leaveEvent(event)

    def insertHyperlink(self, text):
        # Usar el cursor actual en lugar de mover al final
        cursor = self.textCursor()

        # Configurar el formato del bloque para permitir ajuste de línea
        block_format = QTextBlockFormat()
        block_format.setLineHeight(200, 0)
        block_format.setTextIndent(0)
        block_format.setAlignment(Qt.AlignmentFlag.AlignLeft)
        cursor.setBlockFormat(block_format)

        # Insertar el texto con el formato de hipervínculo
        cursor.insertText(text, self.hyperlink_format)
        cursor.insertBlock(block_format)

        # Mantener el foco y el formato
        self.setTextCursor(cursor)
        self.setCurrentCharFormat(self.normal_format)
        self.update_existing_text_formats()

    def focusOutEvent(self, e):
        super().focusOutEvent(e)
        self.update_existing_text_formats()

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
        try:
            # Uso correcto de las opciones
            options = QFileDialog.Option.DontUseNativeDialog
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Seleccionar archivo",
                "",
                "Todos los archivos (*.*)",
                options=options
            )
            if file_path:
                file_path = os.path.normpath(file_path)  # Normalizar ruta
                file_name = os.path.basename(file_path)
                self.file_links[file_name] = file_path
                self.note_box.file_links[file_name] = file_path
                self.note_box.insertHyperlink(file_name)
                self.note_box.setFocus()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al seleccionar archivo: {str(e)}")

    def open_hyperlink(self, line):
        try:
            file_path = self.note_box.file_links.get(line)
            if file_path and os.path.exists(file_path):
                file_path = os.path.normpath(file_path)  # Normalizar ruta
                if sys.platform.startswith('win32') and hasattr(os, 'startfile'):
                    os.startfile(file_path)
                elif sys.platform.startswith('darwin'):
                    subprocess.run(['open', file_path], check=True)
                else:
                    subprocess.run(['xdg-open', file_path], check=True)
            else:
                QMessageBox.warning(self, "Error", "No se pudo encontrar el archivo.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo abrir el archivo: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    notes_app = NotesApp()
    notes_app.show()
    sys.exit(app.exec())
