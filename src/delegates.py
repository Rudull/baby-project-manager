# delegates.py
#1
from PySide6.QtWidgets import QStyledItemDelegate, QLineEdit, QDateEdit, QSpinBox
from PySide6.QtCore import Qt, QDate, QEvent
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont

class LineEditDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(LineEditDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        task = index.data(Qt.ItemDataRole.UserRole)
        if task:
            task.is_editing = True
            # Emitir señal para repintar la celda de estado
            model = index.model()
            model.dataChanged.emit(index, index, [Qt.ItemDataRole.UserRole])
        return editor

    def setEditorData(self, editor, index):
        text = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.setText(text)

    def setModelData(self, editor, model, index):
        text = editor.text().lstrip()  # Eliminar espacios al inicio

        # Asumiendo que una subtarea puede tener un nombre con espacios antes, eliminamos esos espacios
        task = index.data(Qt.ItemDataRole.UserRole)
        if task and task.is_subtask:
            # Eliminar la indentación al guardar el nombre de una subtarea
            text = text.lstrip()  # Elimina espacios en blanco iniciales que podrían ser la indentación

        model.setData(index, text, Qt.ItemDataRole.EditRole)
        task = index.data(Qt.ItemDataRole.UserRole)
        if task:
            task.is_editing = False
            # Emitir señal para repintar la celda de estado
            model.dataChanged.emit(index, index, [Qt.ItemDataRole.UserRole])

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class DateEditDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(DateEditDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        editor = QDateEdit(parent)
        editor.setCalendarPopup(True)
        editor.setDisplayFormat("dd/MM/yyyy")
        task = index.data(Qt.ItemDataRole.UserRole)
        if task:
            task.is_editing = True
            # Emitir señal para repintar la celda de estado
            model = index.model()
            model.dataChanged.emit(index, index, [Qt.ItemDataRole.UserRole])
        return editor

    def setEditorData(self, editor, index):
        date_str = index.model().data(index, Qt.ItemDataRole.EditRole)
        date = QDate.fromString(date_str, "dd/MM/yyyy")
        if not date.isValid():
            date = QDate.currentDate()
        editor.setDate(date)

    def setModelData(self, editor, model, index):
        date = editor.date()
        date_str = date.toString("dd/MM/yyyy")
        model.setData(index, date_str, Qt.ItemDataRole.EditRole)
        task = index.data(Qt.ItemDataRole.UserRole)
        if task:
            task.is_editing = False
            # Emitir señal para repintar la celda de estado
            model.dataChanged.emit(index, index, [Qt.ItemDataRole.UserRole])

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class SpinBoxDelegate(QStyledItemDelegate):
    def __init__(self, minimum=0, maximum=100, parent=None):
        super(SpinBoxDelegate, self).__init__(parent)
        self.minimum = minimum
        self.maximum = maximum

    def createEditor(self, parent, option, index):
        editor = QSpinBox(parent)
        editor.setMinimum(self.minimum)
        editor.setMaximum(self.maximum)
        task = index.data(Qt.ItemDataRole.UserRole)
        if task:
            task.is_editing = True
            # Emitir señal para repintar la celda de estado
            model = index.model()
            model.dataChanged.emit(index, index, [Qt.ItemDataRole.UserRole])
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        if isinstance(value, str) and value.isdigit():
            editor.setValue(int(value))
        elif isinstance(value, int):
            editor.setValue(value)
        else:
            editor.setValue(self.minimum)

    def setModelData(self, editor, model, index):
        value = editor.value()
        model.setData(index, str(value), Qt.ItemDataRole.EditRole)
        task = index.data(Qt.ItemDataRole.UserRole)
        if task:
            task.is_editing = False
            # Emitir señal para repintar la celda de estado
            model.dataChanged.emit(index, index, [Qt.ItemDataRole.UserRole])

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class StateButtonDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, main_window=None):
        super(StateButtonDelegate, self).__init__(parent)
        self.main_window = main_window

    def createEditor(self, parent, option, index):
        return None

    def paint(self, painter, option, index):
        task = index.data(Qt.ItemDataRole.UserRole)
        if not task:
            return

        color = QColor(34, 151, 153)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(option.rect)

        painter.setPen(Qt.GlobalColor.white)
        painter.setFont(QFont("Arial", 12))

        if task.has_subtasks():
            text = "+" if task.is_collapsed else "-"
        elif task.is_subtask:
            text = "↳"
        else:
            text = ""

        painter.drawText(option.rect, Qt.AlignmentFlag.AlignCenter, text)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonPress:
            task = index.data(Qt.ItemDataRole.UserRole)
            if task and not task.is_subtask:  # Solo actuar si no es una subtarea
                task.is_collapsed = not task.is_collapsed
                model.update_visible_tasks()
                model.layoutChanged.emit()
                return True
        return False  # No hacer nada si es una subtarea

    def sizeHint(self, option, index):
        return QSize(25, 25)
