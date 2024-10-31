from PySide6.QtWidgets import (
    QStyledItemDelegate, QLineEdit, QDateEdit, QSpinBox,
    QStyle
)
from PySide6.QtCore import Qt, QDate, QRect
from PySide6.QtGui import (
    QPainter, QColor, QBrush, QPen, QFont
)

class LineEditDelegate(QStyledItemDelegate):
    """Delegado para edición de texto en línea."""
    
    def createEditor(self, parent, option, index):
        """Crea y retorna un editor de texto."""
        editor = QLineEdit(parent)
        task = index.data(Qt.ItemDataRole.UserRole)
        if task:
            task.is_editing = True
            # Emitir señal para repintar la celda
            self._notify_data_change(index)
        return editor

    def setEditorData(self, editor: QLineEdit, index):
        """Establece los datos iniciales en el editor."""
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.setText(str(value))

    def setModelData(self, editor: QLineEdit, model, index):
        """Guarda los datos del editor en el modelo."""
        value = editor.text()
        model.setData(index, value, Qt.ItemDataRole.EditRole)
        task = index.data(Qt.ItemDataRole.UserRole)
        if task:
            task.is_editing = False
            self._notify_data_change(index)

    def updateEditorGeometry(self, editor, option, index):
        """Actualiza la geometría del editor."""
        editor.setGeometry(option.rect)

    def _notify_data_change(self, index):
        """Notifica cambios en los datos del modelo."""
        model = index.model()
        model.dataChanged.emit(index, index, [Qt.ItemDataRole.UserRole])

class DateEditDelegate(QStyledItemDelegate):
    """Delegado para edición de fechas."""
    
    def createEditor(self, parent, option, index):
        """Crea y retorna un editor de fecha."""
        editor = QDateEdit(parent)
        editor.setCalendarPopup(True)
        editor.setDisplayFormat("dd/MM/yyyy")
        task = index.data(Qt.ItemDataRole.UserRole)
        if task:
            task.is_editing = True
            self._notify_data_change(index)
        return editor

    def setEditorData(self, editor: QDateEdit, index):
        """Establece la fecha inicial en el editor."""
        date_str = index.model().data(index, Qt.ItemDataRole.EditRole)
        date = QDate.fromString(date_str, "dd/MM/yyyy")
        if not date.isValid():
            date = QDate.currentDate()
        editor.setDate(date)

    def setModelData(self, editor: QDateEdit, model, index):
        """Guarda la fecha del editor en el modelo."""
        date = editor.date()
        date_str = date.toString("dd/MM/yyyy")
        model.setData(index, date_str, Qt.ItemDataRole.EditRole)
        task = index.data(Qt.ItemDataRole.UserRole)
        if task:
            task.is_editing = False
            self._notify_data_change(index)

    def updateEditorGeometry(self, editor, option, index):
        """Actualiza la geometría del editor."""
        editor.setGeometry(option.rect)

    def _notify_data_change(self, index):
        """Notifica cambios en los datos del modelo."""
        model = index.model()
        model.dataChanged.emit(index, index, [Qt.ItemDataRole.UserRole])

class SpinBoxDelegate(QStyledItemDelegate):
    """Delegado para edición de valores numéricos."""
    
    def __init__(self, minimum=0, maximum=100, parent=None):
        super().__init__(parent)
        self.minimum = minimum
        self.maximum = maximum

    def createEditor(self, parent, option, index):
        """Crea y retorna un editor numérico."""
        editor = QSpinBox(parent)
        editor.setMinimum(self.minimum)
        editor.setMaximum(self.maximum)
        task = index.data(Qt.ItemDataRole.UserRole)
        if task:
            task.is_editing = True
            self._notify_data_change(index)
        return editor

    def setEditorData(self, editor: QSpinBox, index):
        """Establece el valor inicial en el editor."""
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        if isinstance(value, str) and value.isdigit():
            editor.setValue(int(value))
        elif isinstance(value, int):
            editor.setValue(value)
        else:
            editor.setValue(self.minimum)

    def setModelData(self, editor: QSpinBox, model, index):
        """Guarda el valor del editor en el modelo."""
        value = editor.value()
        model.setData(index, str(value), Qt.ItemDataRole.EditRole)
        task = index.data(Qt.ItemDataRole.UserRole)
        if task:
            task.is_editing = False
            self._notify_data_change(index)

    def updateEditorGeometry(self, editor, option, index):
        """Actualiza la geometría del editor."""
        editor.setGeometry(option.rect)

    def _notify_data_change(self, index):
        """Notifica cambios en los datos del modelo."""
        model = index.model()
        model.dataChanged.emit(index, index, [Qt.ItemDataRole.UserRole])

class StateButtonDelegate(QStyledItemDelegate):
    """Delegado para el botón de estado de las tareas."""
    
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self._button_size = 25
        self._color = QColor(34, 151, 153)
        self._font = QFont("Arial", 12)

    def createEditor(self, parent, option, index):
        """No se crea editor para este delegado."""
        return None

    def paint(self, painter: QPainter, option, index):
        """Pinta el botón de estado."""
        task = index.data(Qt.ItemDataRole.UserRole)
        if not task:
            return

        # Configurar el pintor
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dibujar el fondo
        painter.setBrush(QBrush(self._color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(QRect(option.rect))

        # Configurar el texto
        painter.setPen(Qt.GlobalColor.white)
        painter.setFont(self._font)

        # Determinar el texto a mostrar
        text = self._get_button_text(task)

        # Dibujar el texto
        painter.drawText(
            QRect(option.rect),
            Qt.AlignmentFlag.AlignCenter,
            text
        )

        painter.restore()

    def _get_button_text(self, task):
        """Determina el texto a mostrar en el botón."""
        if task.has_subtasks():
            return "+" if task.is_collapsed else "-"
        elif task.is_subtask:
            return "↳"
        return ""

    def editorEvent(self, event, model, option, index):
        """Maneja los eventos del editor."""
        if event.type() == Qt.Type.MouseButtonPress:
            task = index.data(Qt.ItemDataRole.UserRole)
            if task and not task.is_subtask:
                task.is_collapsed = not task.is_collapsed
                model.update_visible_tasks()
                model.layoutChanged.emit()
                return True
        return False

    def sizeHint(self, option, index):
        """Retorna el tamaño sugerido para el delegado."""
        return option.rect.size()

    def paint(self, painter: QPainter, option, index):
        """Pinta el botón de estado con efectos visuales mejorados."""
        task = index.data(Qt.ItemDataRole.UserRole)
        if not task:
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Crear un rectángulo con bordes redondeados
        rect = QRect(option.rect)
        rect.adjust(2, 2, -2, -2)  # Márgenes

        # Dibujar el fondo
        if option.state & QStyle.StateFlag.State_MouseOver:
            # Color más claro cuando el mouse está encima
            color = self._color.lighter(110)
        else:
            color = self._color

        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 5, 5)  # Bordes redondeados

        # Dibujar el texto
        painter.setPen(Qt.GlobalColor.white)
        painter.setFont(self._font)
        text = self._get_button_text(task)

        # Efecto de sombra sutil
        if option.state & QStyle.StateFlag.State_MouseOver:
            shadow_rect = rect.adjusted(1, 1, 1, 1)
            painter.setPen(QColor(0, 0, 0, 30))
            painter.drawText(shadow_rect, Qt.AlignmentFlag.AlignCenter, text)

        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

        painter.restore()