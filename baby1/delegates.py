# delegates.py
# Este archivo contendrá las clases delegadas personalizadas necesarias para manejar la edición de diferentes tipos de datos en la vista de tabla de tareas (TaskTableWidget).

from PySide6.QtWidgets import (
    QStyledItemDelegate, QLineEdit, QDateEdit, QSpinBox, QApplication
)
from PySide6.QtCore import Qt, QDate, QRect, QPoint, QSize, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QTextOption
import sys

class LineEditDelegate(QStyledItemDelegate):
    """
    Delegado para manejar la edición de textos en QLineEdit.
    Utilizado para la columna "Nombre" de las tareas.
    """
    def createEditor(self, parent, option, index):
        """
        Crea el editor QLineEdit.

        Args:
            parent (QWidget): Widget padre.
            option (QStyleOptionViewItem): Opciones de estilo.
            index (QModelIndex): Índice del modelo.

        Returns:
            QLineEdit: Editor creado.
        """
        editor = QLineEdit(parent)
        return editor

    def setEditorData(self, editor, index):
        """
        Establece los datos del editor desde el modelo.

        Args:
            editor (QLineEdit): Editor.
            index (QModelIndex): Índice del modelo.
        """
        text = index.model().data(index, Qt.ItemDataRole.DisplayRole)
        editor.setText(text)

    def setModelData(self, editor, model, index):
        """
        Establece los datos del modelo desde el editor.

        Args:
            editor (QLineEdit): Editor.
            model (QAbstractItemModel): Modelo de datos.
            index (QModelIndex): Índice del modelo.
        """
        text = editor.text()
        model.setData(index, text, Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        """
        Actualiza la geometría del editor.

        Args:
            editor (QLineEdit): Editor.
            option (QStyleOptionViewItem): Opciones de estilo.
            index (QModelIndex): Índice del modelo.
        """
        editor.setGeometry(option.rect)


class DateEditDelegate(QStyledItemDelegate):
    """
    Delegado para manejar la edición de fechas en QDateEdit.
    Utilizado para las columnas "Fecha inicial" y "Fecha final" de las tareas.
    """
    def createEditor(self, parent, option, index):
        """
        Crea el editor QDateEdit.

        Args:
            parent (QWidget): Widget padre.
            option (QStyleOptionViewItem): Opciones de estilo.
            index (QModelIndex): Índice del modelo.

        Returns:
            QDateEdit: Editor creado.
        """
        editor = QDateEdit(parent)
        editor.setDisplayFormat("dd/MM/yyyy")
        editor.setCalendarPopup(True)
        return editor

    def setEditorData(self, editor, index):
        """
        Establece los datos del editor desde el modelo.

        Args:
            editor (QDateEdit): Editor.
            index (QModelIndex): Índice del modelo.
        """
        date_str = index.model().data(index, Qt.ItemDataRole.DisplayRole)
        date = QDate.fromString(date_str, "dd/MM/yyyy")
        if date.isValid():
            editor.setDate(date)
        else:
            editor.setDate(QDate.currentDate())

    def setModelData(self, editor, model, index):
        """
        Establece los datos del modelo desde el editor.

        Args:
            editor (QDateEdit): Editor.
            model (QAbstractItemModel): Modelo de datos.
            index (QModelIndex): Índice del modelo.
        """
        date = editor.date()
        date_str = date.toString("dd/MM/yyyy")
        model.setData(index, date_str, Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        """
        Actualiza la geometría del editor.

        Args:
            editor (QDateEdit): Editor.
            option (QStyleOptionViewItem): Opciones de estilo.
            index (QModelIndex): Índice del modelo.
        """
        editor.setGeometry(option.rect)


class SpinBoxDelegate(QStyledItemDelegate):
    """
    Delegado para manejar la edición de números enteros en QSpinBox.
    Utilizado para las columnas "Días" y "%" de las tareas.
    """
    def __init__(self, minimum=0, maximum=100, parent=None):
        """
        Inicializa el delegado con los valores mínimo y máximo.

        Args:
            minimum (int, optional): Valor mínimo. Por defecto es 0.
            maximum (int, optional): Valor máximo. Por defecto es 100.
            parent (QObject, optional): Padre. Por defecto es None.
        """
        super().__init__(parent)
        self.minimum = minimum
        self.maximum = maximum

    def createEditor(self, parent, option, index):
        """
        Crea el editor QSpinBox.

        Args:
            parent (QWidget): Widget padre.
            option (QStyleOptionViewItem): Opciones de estilo.
            index (QModelIndex): Índice del modelo.

        Returns:
            QSpinBox: Editor creado.
        """
        editor = QSpinBox(parent)
        editor.setMinimum(self.minimum)
        editor.setMaximum(self.maximum)
        return editor

    def setEditorData(self, editor, index):
        """
        Establece los datos del editor desde el modelo.

        Args:
            editor (QSpinBox): Editor.
            index (QModelIndex): Índice del modelo.
        """
        value = index.model().data(index, Qt.ItemDataRole.DisplayRole)
        if value.isdigit():
            editor.setValue(int(value))
        else:
            editor.setValue(self.minimum)

    def setModelData(self, editor, model, index):
        """
        Establece los datos del modelo desde el editor.

        Args:
            editor (QSpinBox): Editor.
            model (QAbstractItemModel): Modelo de datos.
            index (QModelIndex): Índice del modelo.
        """
        value = editor.value()
        model.setData(index, str(value), Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        """
        Actualiza la geometría del editor.

        Args:
            editor (QSpinBox): Editor.
            option (QStyleOptionViewItem): Opciones de estilo.
            index (QModelIndex): Índice del modelo.
        """
        editor.setGeometry(option.rect)


class StateButtonDelegate(QStyledItemDelegate):
    """
    Delegado para manejar la representación y el manejo de un botón de estado en la primera columna.
    Utilizado para expandir/contraer subtareas o para cambiar el estado de la tarea.
    """
    # Señal para emitir cuando se hace clic en el botón de estado
    stateButtonClicked = Signal(int)

    def __init__(self, parent=None, main_window=None):
        """
        Inicializa el delegado con una referencia a la ventana principal.

        Args:
            parent (QObject, optional): Padre. Por defecto es None.
            main_window (QMainWindow, optional): Referencia a la ventana principal. Por defecto es None.
        """
        super().__init__(parent)
        self.main_window = main_window
        self.button_size = QSize(20, 20)  # Tamaño del botón

    def paint(self, painter, option, index):
        """
        Dibuja el botón de estado en la celda.

        Args:
            painter (QPainter): Pincel para dibujar.
            option (QStyleOptionViewItem): Opciones de estilo.
            index (QModelIndex): Índice del modelo.
        """
        task = index.model().data(index, Qt.ItemDataRole.UserRole)
        if not task:
            return

        # Determinar el símbolo del botón según el estado de colapso
        if task.has_subtasks():
            symbol = "-" if not task.is_collapsed else "+"
        else:
            symbol = ""

        # Dibujar el botón
        button_rect = QRect(option.rect.center() - QPoint(self.button_size.width() // 2, self.button_size.height() // 2),
                            self.button_size)
        painter.save()
        if option.state & QStyleOptionViewItem.State_Selected:
            painter.setBrush(QBrush(Qt.GlobalColor.lightGray))
        else:
            painter.setBrush(QBrush(Qt.GlobalColor.white))
        painter.setPen(QPen(Qt.GlobalColor.black))
        painter.drawRect(button_rect)

        # Dibujar el símbolo
        if symbol:
            painter.setPen(QPen(Qt.GlobalColor.black))
            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(button_rect, Qt.AlignmentFlag.AlignCenter, symbol)
        painter.restore()

    def editorEvent(self, event, model, option, index):
        """
        Maneja los eventos del editor, como clics del ratón.

        Args:
            event (QEvent): Evento.
            model (QAbstractItemModel): Modelo de datos.
            option (QStyleOptionViewItem): Opciones de estilo.
            index (QModelIndex): Índice del modelo.

        Returns:
            bool: True si el evento fue manejado, False en caso contrario.
        """
        if event.type() == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton:
                # Calcular la posición del botón
                button_rect = QRect(option.rect.center() - QPoint(self.button_size.width() // 2, self.button_size.height() // 2),
                                    self.button_size)
                if button_rect.contains(event.pos()):
                    # Emitir señal con el índice de la fila
                    self.stateButtonClicked.emit(index.row())
                    return True
        return super().editorEvent(event, model, option, index)
