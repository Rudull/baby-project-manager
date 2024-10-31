# Este archivo contendrá la clase FloatingTaskMenu, que es un menú flotante diseñado para editar propiedades específicas de una tarea, como las notas y el color.
# floating_menu.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QColorDialog,
    QTextEdit, QHBoxLayout, QDialog, QFormLayout, QLineEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette, QFont


class FloatingTaskMenu(QDialog):
    """
    Menú flotante para editar las propiedades de una tarea.
    Permite al usuario cambiar las notas y el color de la tarea.
    """
    notesChanged = Signal()
    colorChanged = Signal(QColor)

    def __init__(self, task, parent=None):
        """
        Inicializa el menú flotante con los datos de la tarea proporcionada.

        Args:
            task (Task): La tarea a editar.
            parent (QWidget, optional): Widget padre. Por defecto es None.
        """
        super().__init__(parent)
        self.task = task
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(False)
        self.setFixedSize(300, 200)

        self.init_ui()

    def init_ui(self):
        """
        Inicializa la interfaz de usuario del menú flotante.
        """
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Título
        title = QLabel("Editar Tarea")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        main_layout.addWidget(title)

        # Formulario de edición
        form_layout = QFormLayout()

        # Campo de nombre (no editable aquí, pero puedes hacerlo editable si lo deseas)
        self.name_edit = QLineEdit(self.task.name)
        self.name_edit.setReadOnly(True)
        form_layout.addRow("Nombre:", self.name_edit)

        # Campo de notas
        self.notes_edit = QTextEdit(self.task.notes_html)
        self.notes_edit.setPlaceholderText("Escribe las notas de la tarea aquí...")
        form_layout.addRow("Notas:", self.notes_edit)

        # Botón para seleccionar color
        color_layout = QHBoxLayout()
        self.color_label = QLabel("Color:")
        self.color_display = QLabel()
        self.color_display.setFixedSize(50, 20)
        self.color_display.setAutoFillBackground(True)
        self.set_color_display(self.task.color)
        self.change_color_button = QPushButton("Cambiar Color")
        self.change_color_button.clicked.connect(self.change_color)
        color_layout.addWidget(self.color_label)
        color_layout.addWidget(self.color_display)
        color_layout.addWidget(self.change_color_button)
        form_layout.addRow("", color_layout)

        main_layout.addLayout(form_layout)

        # Botones de acción
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.save_changes)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.close)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def set_color_display(self, color):
        """
        Actualiza el color mostrado en el display de color.

        Args:
            color (QColor): El color a mostrar.
        """
        palette = self.color_display.palette()
        palette.setColor(QPalette.ColorRole.Window, color)
        self.color_display.setPalette(palette)

    def change_color(self):
        """
        Abre un diálogo para seleccionar un nuevo color y actualiza el display.
        """
        color = QColorDialog.getColor(initial=self.task.color, parent=self, title="Seleccionar Color")
        if color.isValid():
            self.set_color_display(color)
            self.selected_color = color
        else:
            self.selected_color = self.task.color

    def save_changes(self):
        """
        Guarda los cambios realizados en las notas y el color de la tarea.
        """
        new_notes = self.notes_edit.toHtml()
        if new_notes != self.task.notes_html:
            self.task.notes_html = new_notes
            self.task.notes = self.notes_edit.toPlainText()
            self.notesChanged.emit()

        new_color = getattr(self, 'selected_color', self.task.color)
        if new_color != self.task.color:
            self.task.color = new_color
            self.colorChanged.emit(new_color)

        self.close()
