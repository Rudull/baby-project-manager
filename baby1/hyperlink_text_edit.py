# Este widget permitirá a los usuarios insertar, editar y gestionar hipervínculos de manera intuitiva dentro de las notas de las tareas la aplicación
# hyperlink_text_edit.py

from PySide6.QtWidgets import QTextEdit, QAction, QMenu, QToolBar, QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel
from PySide6.QtGui import QIcon, QTextCursor, QKeySequence, QDesktopServices, QTextCharFormat, QColor
from PySide6.QtCore import Qt, QUrl, Signal
import re

class HyperlinkTextEdit(QTextEdit):
    """
    QTextEdit personalizado que maneja la inserción y gestión de hipervínculos.
    Permite al usuario insertar hipervínculos, seguirlos y editarlos fácilmente.
    """
    # Señal emitida cuando se inserta o edita un hipervínculo
    hyperlinkAdded = Signal(str, str)  # (text, url)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.custom_context_menu)

        # Configurar atajos de teclado
        self.setup_shortcuts()

        # Configurar barra de herramientas
        self.setup_toolbar()

        # Conectar señal para detectar clics en hipervínculos
        self.anchorClicked.connect(self.on_anchor_clicked)

    def setup_shortcuts(self):
        """
        Configura atajos de teclado para insertar y editar hipervínculos.
        """
        # Atajo para insertar hipervínculo (Ctrl+K)
        insert_hyperlink_shortcut = QAction(QIcon(), "Insertar Hipervínculo", self)
        insert_hyperlink_shortcut.setShortcut(QKeySequence("Ctrl+K"))
        insert_hyperlink_shortcut.triggered.connect(self.insert_hyperlink_dialog)
        self.addAction(insert_hyperlink_shortcut)

    def setup_toolbar(self):
        """
        Configura una barra de herramientas con acciones para insertar hipervínculos.
        """
        self.toolbar = QToolBar("Hyperlink Tools")
        self.toolbar.setIconSize(Qt.Size(16, 16))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        # Acción para insertar hipervínculo
        insert_link_action = QAction(QIcon.fromTheme("insert-link"), "Insertar Hipervínculo", self)
        insert_link_action.setShortcut(QKeySequence("Ctrl+K"))
        insert_link_action.triggered.connect(self.insert_hyperlink_dialog)
        self.toolbar.addAction(insert_link_action)

        # Acción para eliminar hipervínculo
        remove_link_action = QAction(QIcon.fromTheme("edit-clear"), "Eliminar Hipervínculo", self)
        remove_link_action.triggered.connect(self.remove_hyperlink)
        self.toolbar.addAction(remove_link_action)

    def custom_context_menu(self, position):
        """
        Crea un menú contextual personalizado que incluye opciones para manejar hipervínculos.
        
        Args:
            position (QPoint): Posición donde se solicitó el menú contextual.
        """
        menu = self.createStandardContextMenu()

        cursor = self.cursorForPosition(position)
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        selected_text = cursor.selectedText()

        # Verificar si el texto seleccionado es un hipervínculo
        char_format = cursor.charFormat()
        if char_format.isAnchor():
            href = char_format.anchorHref()
            follow_link_action = QAction("Seguir Hipervínculo", self)
            follow_link_action.triggered.connect(lambda: self.follow_hyperlink(href))
            menu.addAction(follow_link_action)

            edit_link_action = QAction("Editar Hipervínculo", self)
            edit_link_action.triggered.connect(lambda: self.edit_hyperlink_dialog(cursor))
            menu.addAction(edit_link_action)
        else:
            # Opciones para texto normal
            insert_link_action = QAction("Insertar Hipervínculo", self)
            insert_link_action.setShortcut(QKeySequence("Ctrl+K"))
            insert_link_action.triggered.connect(self.insert_hyperlink_dialog)
            menu.addAction(insert_link_action)

        menu.exec(self.viewport().mapToGlobal(position))

    def insert_hyperlink_dialog(self):
        """
        Abre un diálogo para que el usuario inserte un hipervínculo.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Insertar Hipervínculo")
        dialog.setModal(True)
        dialog.setFixedSize(400, 150)

        layout = QVBoxLayout()

        # Campo para el texto del enlace
        text_label = QLabel("Texto del Enlace:")
        self.link_text_edit = QLineEdit()
        layout.addWidget(text_label)
        layout.addWidget(self.link_text_edit)

        # Campo para la URL del enlace
        url_label = QLabel("URL del Enlace:")
        self.link_url_edit = QLineEdit()
        layout.addWidget(url_label)
        layout.addWidget(self.link_url_edit)

        # Botones de acción
        button_layout = QHBoxLayout()
        insert_button = QPushButton("Insertar")
        insert_button.clicked.connect(lambda: self.insert_hyperlink(dialog))
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addStretch()
        button_layout.addWidget(insert_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        dialog.setLayout(layout)
        dialog.exec()

    def insert_hyperlink(self, dialog):
        """
        Inserta un hipervínculo en el texto editado.
        
        Args:
            dialog (QDialog): Diálogo desde el cual se llamo la inserción.
        """
        text = self.link_text_edit.text().strip()
        url = self.link_url_edit.text().strip()

        if not text or not url:
            # Mostrar mensaje de error si faltan datos
            error_dialog = QDialog(self)
            error_dialog.setWindowTitle("Error")
            error_layout = QVBoxLayout()
            error_label = QLabel("Ambos campos, Texto y URL, son obligatorios.")
            error_layout.addWidget(error_label)
            ok_button = QPushButton("OK")
            ok_button.clicked.connect(error_dialog.accept)
            error_layout.addWidget(ok_button)
            error_dialog.setLayout(error_layout)
            error_dialog.exec()
            return

        # Validar la URL
        if not re.match(r'^https?://', url):
            url = 'http://' + url  # Prepend 'http://' si no está presente

        # Insertar el hipervínculo en el cursor actual
        cursor = self.textCursor()
        cursor.insertHtml(f'<a href="{url}">{text}</a>')
        self.hyperlinkAdded.emit(text, url)
        dialog.accept()

    def edit_hyperlink_dialog(self, cursor):
        """
        Abre un diálogo para que el usuario edite un hipervínculo existente.
        
        Args:
            cursor (QTextCursor): Cursor que apunta al hipervínculo a editar.
        """
        if not cursor.charFormat().isAnchor():
            return

        current_text = cursor.selectedText()
        current_href = cursor.charFormat().anchorHref()

        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Hipervínculo")
        dialog.setModal(True)
        dialog.setFixedSize(400, 150)

        layout = QVBoxLayout()

        # Campo para el texto del enlace
        text_label = QLabel("Texto del Enlace:")
        self.edit_link_text_edit = QLineEdit(current_text)
        layout.addWidget(text_label)
        layout.addWidget(self.edit_link_text_edit)

        # Campo para la URL del enlace
        url_label = QLabel("URL del Enlace:")
        self.edit_link_url_edit = QLineEdit(current_href)
        layout.addWidget(url_label)
        layout.addWidget(self.edit_link_url_edit)

        # Botones de acción
        button_layout = QHBoxLayout()
        save_button = QPushButton("Guardar")
        save_button.clicked.connect(lambda: self.save_edited_hyperlink(cursor, dialog))
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        dialog.setLayout(layout)
        dialog.exec()

    def save_edited_hyperlink(self, cursor, dialog):
        """
        Guarda los cambios realizados en un hipervínculo existente.
        
        Args:
            cursor (QTextCursor): Cursor que apunta al hipervínculo a editar.
            dialog (QDialog): Diálogo desde el cual se llamo la edición.
        """
        new_text = self.edit_link_text_edit.text().strip()
        new_url = self.edit_link_url_edit.text().strip()

        if not new_text or not new_url:
            # Mostrar mensaje de error si faltan datos
            error_dialog = QDialog(self)
            error_dialog.setWindowTitle("Error")
            error_layout = QVBoxLayout()
            error_label = QLabel("Ambos campos, Texto y URL, son obligatorios.")
            error_layout.addWidget(error_label)
            ok_button = QPushButton("OK")
            ok_button.clicked.connect(error_dialog.accept)
            error_layout.addWidget(ok_button)
            error_dialog.setLayout(error_layout)
            error_dialog.exec()
            return

        # Validar la URL
        if not re.match(r'^https?://', new_url):
            new_url = 'http://' + new_url  # Prepend 'http://' si no está presente

        # Modificar el hipervínculo en el cursor
        char_format = cursor.charFormat()
        char_format.setAnchorHref(new_url)
        cursor.mergeCharFormat(char_format)
        cursor.insertHtml(new_text)
        self.hyperlinkAdded.emit(new_text, new_url)
        dialog.accept()

    def remove_hyperlink(self):
        """
        Elimina el hipervínculo del texto seleccionado.
        """
        cursor = self.textCursor()
        if cursor.charFormat().isAnchor():
            cursor.setCharFormat(QTextCharFormat())  # Restablecer el formato
            self.setTextCursor(cursor)

    def on_anchor_clicked(self, url):
        """
        Maneja el evento cuando se hace clic en un hipervínculo.
        
        Args:
            url (QUrl): URL del hipervínculo clicado.
        """
        QDesktopServices.openUrl(url)

    def follow_hyperlink(self, url):
        """
        Abre el hipervínculo en el navegador predeterminado.
        
        Args:
            url (str): URL del hipervínculo a seguir.
        """
        QDesktopServices.openUrl(QUrl(url))

    def mouseDoubleClickEvent(self, event):
        """
        Maneja el evento de doble clic para editar un hipervínculo.
        
        Args:
            event (QMouseEvent): Evento de doble clic.
        """
        cursor = self.cursorForPosition(event.pos())
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        char_format = cursor.charFormat()
        if char_format.isAnchor():
            self.edit_hyperlink_dialog(cursor)
        else:
            super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        """
        Maneja eventos de teclas para facilitar la edición de hipervínculos.
        
        Args:
            event (QKeyEvent): Evento de tecla presionada.
        """
        if event.matches(QKeySequence.StandardKey.InsertLink):
            self.insert_hyperlink_dialog()
            event.accept()
        else:
            super().keyPressEvent(event)
