# Inicia soporte de subtareas 11
import sys
from datetime import timedelta, datetime
from workalendar.america import Colombia
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QDateEdit, QScrollArea, QTableView,
    QHeaderView, QMenu, QScrollBar, QFileDialog, QMessageBox, QColorDialog,
    QTextEdit, QStyledItemDelegate
)
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QPainterPath, QPalette, QContextMenuEvent, QKeySequence, QShortcut, QWheelEvent
from PySide6.QtCore import Qt, QDate, QRect, QTimer, QSize, QRectF, QEvent, Signal, QPoint, QAbstractTableModel, QModelIndex

class LineEditDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(LineEditDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        return editor

    def setEditorData(self, editor, index):
        text = index.model().data(index, Qt.EditRole)
        editor.setText(text)

    def setModelData(self, editor, model, index):
        text = editor.text()
        model.setData(index, text, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class DateEditDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(DateEditDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        editor = QDateEdit(parent)
        editor.setCalendarPopup(True)
        editor.setDisplayFormat("dd/MM/yyyy")
        return editor

    def setEditorData(self, editor, index):
        date_str = index.model().data(index, Qt.EditRole)
        date = QDate.fromString(date_str, "dd/MM/yyyy")
        if not date.isValid():
            date = QDate.currentDate()
        editor.setDate(date)

    def setModelData(self, editor, model, index):
        date = editor.date()
        date_str = date.toString("dd/MM/yyyy")
        model.setData(index, date_str, Qt.EditRole)

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
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        if value.isdigit():
            editor.setValue(int(value))
        else:
            editor.setValue(self.minimum)

    def setModelData(self, editor, model, index):
        value = editor.value()
        model.setData(index, str(value), Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

        class StateButtonDelegate(QStyledItemDelegate):
            def __init__(self, parent=None):
                super(StateButtonDelegate, self).__init__(parent)

            def paint(self, painter, option, index):
                task = index.model().data(index, Qt.UserRole)
                if not task:
                    return

                button = StateButton(is_subtask=task.is_subtask, parent=None)
                button.set_task(task)
                button.resize(option.rect.size())
                pixmap = button.grab()
                painter.drawPixmap(option.rect.topLeft(), pixmap)

            def createEditor(self, parent, option, index):
                # No editor; clicks manejados via signals
                return None

            def editorEvent(self, event, model, option, index):
                if event.type() == QEvent.MouseButtonRelease:
                    # Alternar el estado
                    task = model.getTask(index.row())
                    if task:
                        task.is_editing = not task.is_editing
                        model.dataChanged.emit(index, index, [Qt.DisplayRole])
                        return True
                return False

class StateButtonDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(StateButtonDelegate, self).__init__(parent)
        self.timer = QTimer()
        self.timer.timeout.connect(self.toggle_color)
        self.timer.start(500)  # Parpadeo cada 500 ms
        self.current_color = "red"

    def createEditor(self, parent, option, index):
        return None

    def paint(self, painter, option, index):
        task = index.data(Qt.ItemDataRole.UserRole)
        if not task:
            return

        rect = option.rect
        painter.save()

        # Dibujar el fondo del botón
        if task.is_editing:
            if self.current_color == "red":
                painter.setBrush(QColor("red"))
            else:
                painter.setBrush(QColor("gray"))
        else:
            painter.setBrush(QColor(34, 151, 153))  # color botón de filas

        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(rect)

        # Dibujar el texto
        painter.setPen(Qt.GlobalColor.white)
        painter.setFont(QFont("Arial", 12))
        text = ""
        if task.is_subtask:
            text = "↳"
        elif task.has_subtasks():
            text = "—"
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

        painter.restore()

    def toggle_color(self):
        self.current_color = "gray" if self.current_color == "red" else "red"

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonPress:
            task = index.data(Qt.ItemDataRole.UserRole)
            if task:
                task.is_editing = not task.is_editing
                model.dataChanged.emit(index, index)
                return True
        return False

    def sizeHint(self, option, index):
        return QSize(25, 25)

class StateButton(QPushButton):
    def __init__(self, parent=None, is_subtask=False):
        super().__init__(parent)
        self.setFixedSize(25, 25)
        self.is_editing = True
        self.is_subtask = is_subtask
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.toggle_color)
        self.timer.start(500)  # Parpadeo cada 500 ms
        self.current_color = "red"
        self.task = None
        self.update_text()

    def toggle_color(self):
        if self.is_editing:
            if self.current_color == "red":
                self.setStyleSheet("background-color: gray;")
                self.current_color = "gray"
            else:
                self.setStyleSheet("background-color: red;")
                self.current_color = "red"
        else:
            self.setStyleSheet("background-color: rgb(34,151,153);")  # Color botón de filas
        self.update_text()

    def set_task(self, task):
        self.task = task
        self.update_text()

    def update_text(self):
        if self.task:
            if self.task.is_subtask:
                self.setText("↳")
            elif self.task.has_subtasks():
                self.setText("—")
            else:
                self.setText("")
        else:
            self.setText("")

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.toggle_state()
        super().mousePressEvent(e)

    def toggle_state(self):
        self.is_editing = not self.is_editing
        if self.is_editing:
            self.setStyleSheet("background-color: red;")
            self.current_color = "red"
            self.timer.start(500)
        else:
            self.setStyleSheet("background-color: rgb(34,151,153);")  # Color botón de filas
            self.timer.stop()
        self.update_text()

class Task:
    def __init__(self, name, start_date, end_date, duration, dedication, color=None, notes=""):
        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.duration = duration
        self.dedication = dedication
        self.color = color or QColor(34, 163, 159)  # Color por defecto si no se especifica
        self.notes = notes
        self.subtasks = []  # Lista para almacenar las subtareas
        self.is_subtask = False
        self.parent_task = None

    def has_subtasks(self):
        return len(self.subtasks) > 0

class TaskTableModel(QAbstractTableModel):
    def __init__(self, tasks=None):
        super(TaskTableModel, self).__init__()
        self.headers = ["", "Nombre", "Fecha inicial", "Fecha final", "Días", "%"]
        self.tasks = tasks or []

    def rowCount(self, parent=QModelIndex()):
        return len(self.tasks)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        task = self.tasks[index.row()]
        column = index.column()

        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            if column == 0:
                return ""  # Para el botón de estado, se usará un delegado
            elif column == 1:
                return task.name
            elif column == 2:
                return task.start_date
            elif column == 3:
                return task.end_date
            elif column == 4:
                return task.duration
            elif column == 5:
                return task.dedication
        elif role == Qt.ItemDataRole.UserRole:
            return task  # Para almacenar el objeto Task
        elif role == Qt.ItemDataRole.BackgroundRole:
            if column == 1:
                return task.color
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled
        flags = super().flags(index)
        if index.column() in [1, 2, 3, 4, 5]:
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid():
            return False

        task = self.tasks[index.row()]
        column = index.column()

        if role == Qt.ItemDataRole.EditRole:
            if column == 1:
                task.name = str(value)
            elif column == 2:
                task.start_date = str(value)
            elif column == 3:
                task.end_date = str(value)
            elif column == 4:
                task.duration = str(value)
            elif column == 5:
                task.dedication = str(value)
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    def insertTask(self, task, position=None):
        self.beginInsertRows(QModelIndex(), position if position is not None else self.rowCount(), position if position is not None else self.rowCount())
        if position is not None:
            self.tasks.insert(position, task)
        else:
            self.tasks.append(task)
        self.endInsertRows()

    def removeTask(self, position):
        if 0 <= position < self.rowCount():
            self.beginRemoveRows(QModelIndex(), position, position)
            del self.tasks[position]
            self.endRemoveRows()
            return True
        return False

    def getTask(self, row):
        if 0 <= row < self.rowCount():
            return self.tasks[row]
        return None

class GanttHeaderView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.min_date = None
        self.max_date = None
        self.pixels_per_day = None
        self.header_height = 20
        self.setFixedHeight(self.header_height)
        self.scroll_offset = 0
        self.update_colors()

    def update_colors(self):
        palette = self.palette()
        self.background_color = palette.color(QPalette.ColorRole.Base)
        self.text_color = palette.color(QPalette.ColorRole.Text)

        # Determinar si estamos en modo claro u oscuro
        is_light_mode = palette.color(QPalette.ColorRole.Window).lightness() > 128
        if is_light_mode:
            # Modo claro: usar gris oscuro
            self.year_color = QColor(80, 80, 80)  # Gris oscuro
            self.year_separator_color = QColor(120, 120, 120)  # Gris un poco más claro para las líneas
        else:
            # Modo oscuro: usar gris claro
            self.year_color = QColor(200, 200, 200)  # Gris claro
            self.year_separator_color = QColor(160, 160, 160)  # Gris un poco más oscuro para las líneas

    def update_parameters(self, min_date, max_date, pixels_per_day):
        self.min_date = min_date
        self.max_date = max_date
        self.pixels_per_day = pixels_per_day
        self.update()

    def paintEvent(self, event):
        if not self.min_date or not self.max_date or not self.pixels_per_day:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(event.rect(), self.background_color)

        year_font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(year_font)

        start_year = self.min_date.year()
        end_year = self.max_date.year()

        for year in range(start_year, end_year + 1):
            year_start = QDate(year, 1, 1)
            year_end = QDate(year, 12, 31)
            if year_start < self.min_date:
                year_start = self.min_date
            if year_end > self.max_date:
                year_end = self.max_date

            start_x = self.min_date.daysTo(year_start) * self.pixels_per_day - self.scroll_offset
            end_x = self.min_date.daysTo(year_end) * self.pixels_per_day - self.scroll_offset

            # Dibuja líneas verticales para separar los años
            painter.setPen(QPen(self.year_separator_color, 1))
            painter.drawLine(int(end_x), 0, int(end_x), self.header_height)

            year_width = end_x - start_x
            year_rect = QRect(int(start_x), 0, int(year_width), self.header_height)
            painter.setPen(self.year_color)
            painter.drawText(year_rect, Qt.AlignmentFlag.AlignCenter, str(year))

        # Dibujar la etiqueta para el día de hoy
        today = QDate.currentDate()
        if self.min_date <= today <= self.max_date:
            today_x = self.min_date.daysTo(today) * self.pixels_per_day - self.scroll_offset

            # Dibuja la etiqueta "Hoy" con un fondo gris redondeado
            label_width = 50
            label_height = 20
            label_x = today_x - label_width / 2
            label_y = self.height() - label_height - 0

            # Dibuja el fondo redondeado
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(128, 128, 128, 180))
            painter.drawRoundedRect(QRectF(label_x, label_y, label_width, label_height), 10, 10)

            # Dibuja el texto "Hoy"
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            painter.setPen(QColor(242,211,136)) #color del texto del día de hoy
            painter.drawText(QRectF(label_x, label_y, label_width, label_height), Qt.AlignmentFlag.AlignCenter, "Hoy")

        painter.end()

    def scrollTo(self, value):
        self.scroll_offset = value
        self.update()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.PaletteChange:
            self.update_colors()
            self.update()
        super().changeEvent(event)

class GanttChart(QWidget):
    colorChanged = Signal(int, QColor)
    SINGLE_CLICK_INTERVAL = 100  # Intervalo en milisegundos para el clic simple

    def __init__(self, tasks, row_height, header_height, main_window):
        super().__init__()
        self.main_window = main_window
        self.tasks = tasks
        self.row_height = row_height
        self.header_height = header_height
        self.min_date = None
        self.max_date = None
        self.pixels_per_day = None
        self.floating_menu = None
        self.setMinimumHeight(self.header_height + self.row_height * len(tasks))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.update_colors()
        self.today_line_color = QColor(242,211,136)  # Color para la línea "Hoy"
        self.double_click_occurred = False  # Bandera para controlar doble clic
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.colorChanged.connect(self.on_color_changed)

    def update_colors(self):
        palette = self.palette()
        self.background_color = palette.color(QPalette.ColorRole.Base)
        self.task_color = palette.color(QPalette.ColorRole.Highlight)
        self.text_color = palette.color(QPalette.ColorRole.Text)
        self.grid_color = palette.color(QPalette.ColorRole.Mid)

    def update_parameters(self, min_date, max_date, pixels_per_day):
        self.min_date = min_date
        self.max_date = max_date
        self.pixels_per_day = pixels_per_day
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_click_occurred = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        task_index = self.get_task_at_position(event.position().toPoint())
        if task_index is not None and self.is_click_on_task_bar(event.position().toPoint(), task_index):
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Almacenar las posiciones
            self.click_pos = event.position().toPoint()
            self.click_global_pos = self.mapToGlobal(self.click_pos)
            # Iniciar el temporizador para el clic simple
            self.single_click_timer = QTimer()
            self.single_click_timer.setSingleShot(True)
            self.single_click_timer.timeout.connect(self.handle_single_click)
            self.single_click_timer.start(self.SINGLE_CLICK_INTERVAL)
        super().mouseReleaseEvent(event)

    def handle_single_click(self):
        if not self.double_click_occurred:
            task_index = int(self.click_pos.y() / self.row_height)
            if 0 <= task_index < len(self.tasks):
                task = self.tasks[task_index]
                self.show_floating_menu(self.click_pos, task)
        # Restablecer la bandera
        self.double_click_occurred = False

    def mouseDoubleClickEvent(self, event):
        self.double_click_occurred = True
        if hasattr(self, 'single_click_timer'):
            self.single_click_timer.stop()

        x = int(event.position().x())
        y = int(event.position().y())
        row_height = self.row_height

        # Determinar el índice de la tarea basada en la posición Y
        task_index = int(y / row_height)
        if 0 <= task_index < len(self.tasks):
            task = self.tasks[task_index]

            # Calcular la posición X de inicio y fin de la barra de la tarea
            start_date = QDate.fromString(task.start_date, "dd/MM/yyyy")
            end_date = QDate.fromString(task.end_date, "dd/MM/yyyy")
            task_start_x = self.min_date.daysTo(start_date) * self.pixels_per_day if self.min_date else 0
            task_end_x = self.min_date.daysTo(end_date) * self.pixels_per_day if self.min_date else 0

            # Verificar si el doble clic fue dentro de la barra de la tarea
            if task_start_x <= x <= task_end_x:
                # Abrir el diálogo de selección de color
                color = QColorDialog.getColor(initial=task.color, parent=self)
                if color.isValid():
                    # Actualizar el color de la tarea
                    task.color = color
                    self.update()
                    # Emitir señal para actualizar la tabla
                    self.colorChanged.emit(task_index, color)
        super().mouseDoubleClickEvent(event)

    def show_floating_menu(self, position, task):
        if self.floating_menu:
            self.floating_menu.close()
        # Obtener la información actualizada de la tarea
        updated_task = self.get_updated_task(task)
        self.floating_menu = FloatingTaskMenu(updated_task, self)
        self.floating_menu.notesChanged.connect(self.on_notes_changed)

        # Calcular la posición ajustada
        menu_size = self.floating_menu.sizeHint()
        adjusted_position = self.adjust_menu_position(position, menu_size)

        self.floating_menu.move(adjusted_position)
        self.floating_menu.show()

    def adjust_menu_position(self, position, menu_size):
        screen = QApplication.primaryScreen().geometry()
        global_pos = self.mapToGlobal(position)

        # Calcular las coordenadas preferidas (cerca del puntero del mouse)
        preferred_x = global_pos.x()
        preferred_y = global_pos.y()

        # Ajustar horizontalmente
        if preferred_x + menu_size.width() > screen.right():
            preferred_x = screen.right() - menu_size.width()
        if preferred_x < screen.left():
            preferred_x = screen.left()

        # Ajustar verticalmente
        if preferred_y + menu_size.height() > screen.bottom():
            preferred_y = preferred_y - menu_size.height()  # Mostrar encima del cursor
        if preferred_y < screen.top():
            preferred_y = screen.top()

        return QPoint(preferred_x, preferred_y)

    def get_updated_task(self, task):
        for row in range(self.main_window.task_table_widget.table_view.model().rowCount()):
            index = self.main_window.task_table_widget.table_view.model().index(row, 1)
            current_task = self.main_window.task_table_widget.table_view.model().data(index, Qt.ItemDataRole.UserRole)
            if current_task == task:
                task.name = self.main_window.task_table_widget.table_view.model().data(index, Qt.ItemDataRole.DisplayRole)
                break
        return task

    def on_notes_changed(self):
        if hasattr(self, 'main_window'):
            self.main_window.set_unsaved_changes(True)

    def on_color_changed(self, task_index, color):
        if hasattr(self, 'main_window'):
            self.main_window.set_unsaved_changes(True)

    def paintEvent(self, event):
        if not self.min_date or not self.max_date or not self.pixels_per_day:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(event.rect(), self.background_color)

        for i, task in enumerate(self.tasks):
            start = QDate.fromString(task.start_date, "dd/MM/yyyy")
            end = QDate.fromString(task.end_date, "dd/MM/yyyy")
            if end < self.min_date or start > self.max_date:
                continue

            x = self.min_date.daysTo(start) * self.pixels_per_day
            width = start.daysTo(end) * self.pixels_per_day + self.pixels_per_day  # Incluye el día final
            y = i * self.row_height

            painter.setBrush(QBrush(task.color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(QRectF(x, y + 1, width, self.row_height - 2))

            # Agregar el identificador "↳" para subtareas
            if hasattr(task, 'is_subtask') and task.is_subtask:
                painter.setPen(QPen(self.text_color))
                painter.setFont(QFont("Arial", 12))
                rect = QRectF(x, y, width, self.row_height)
                painter.drawText(rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "↳")

        # Dibujar la línea vertical para el día de hoy
        today = QDate.currentDate()
        if self.min_date <= today <= self.max_date:
            today_x = self.min_date.daysTo(today) * self.pixels_per_day
            painter.setPen(QPen(self.today_line_color, 2))
            painter.drawLine(int(today_x), 0, int(today_x), self.height())

        if not self.tasks:
            # Mostrar un mensaje de bienvenida en el centro del gráfico Gantt
            welcome_text = "Bienvenido a Baby Project Manager\nHaga clic en 'Agregar Nueva Tarea' para comenzar"
            painter.setPen(QPen(self.text_color))
            painter.setFont(QFont("Arial", 14))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, welcome_text)

        painter.end()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.PaletteChange:
            self.update_colors()
            self.update()
        super().changeEvent(event)

    def show_context_menu(self, position):
        task_index = self.get_task_at_position(position)
        if task_index is not None:
            # Verificar si el clic fue sobre la barra de la tarea
            if self.is_click_on_task_bar(position, task_index):
                global_pos = self.mapToGlobal(position)
                self.main_window.show_task_context_menu(global_pos, task_index)

    def is_click_on_task_bar(self, position, task_index):
        if 0 <= task_index < len(self.tasks):
            task = self.tasks[task_index]
            start_date = QDate.fromString(task.start_date, "dd/MM/yyyy")
            end_date = QDate.fromString(task.end_date, "dd/MM/yyyy")

            x = position.x()
            y = position.y()

            task_start_x = self.min_date.daysTo(start_date) * self.pixels_per_day if self.min_date else 0
            task_end_x = self.min_date.daysTo(end_date) * self.pixels_per_day if self.min_date else 0
            task_y = task_index * self.row_height

            # Añadir un pequeño margen para facilitar el clic
            margin = 2

            if (task_start_x - margin <= x <= task_end_x + margin and
                task_y <= y <= task_y + self.row_height):
                return True

        return False

    def get_task_at_position(self, position):
        y = position.y()
        task_index = y // self.row_height
        if 0 <= task_index < len(self.tasks):
            return task_index
        return None

    def scrollTo(self, value):
        self.update()

    def calculate_today_position(self):
        if self.min_date and self.max_date:
            today = QDate.currentDate()
            if self.min_date <= today <= self.max_date:
                total_days = self.min_date.daysTo(self.max_date)
                days_to_today = self.min_date.daysTo(today)
                return days_to_today / total_days
        return None

    def contextMenuEvent(self, event):
        self.show_context_menu(event.pos())

class GanttWidget(QWidget):
    def __init__(self, tasks, row_height, main_window):
        super().__init__()
        self.main_window = main_window
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.header = GanttHeaderView()
        self.chart = GanttChart(tasks, row_height, self.header.header_height, main_window)
        self.chart.setMouseTracking(True)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_layout.addWidget(self.header)
        self.content_layout.addWidget(self.chart)

        self.layout.addWidget(self.content_widget)

        self.pixels_per_day = 0

    def update_parameters(self, min_date, max_date, pixels_per_day):
        available_width = self.width()
        days_total = min_date.daysTo(max_date) + 1
        self.pixels_per_day = max(0.1, available_width / days_total)

        self.header.update_parameters(min_date, max_date, self.pixels_per_day)
        self.chart.update_parameters(min_date, max_date, self.pixels_per_day)
        self.content_widget.setFixedWidth(int(days_total * self.pixels_per_day))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_parameters(self.header.min_date, self.header.max_date, 0)
        self.chart.update()

    def scrollTo(self, value):
        self.chart.scrollTo(value)

class FloatingTaskMenu(QWidget):
    notesChanged = Signal()

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.cal = Colombia()  # crear una instancia del calendario
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        name_label = QLabel(f"{self.task.name}")  # Usar self.task.name en lugar de task.name
        start_label = QLabel(f"Inicio: {self.task.start_date}")
        end_label = QLabel(f"Fin: {self.task.end_date}")

        days_left_label = QLabel(f"Días restantes: {self.calculate_working_days_left()}")

        for label in (name_label, start_label, end_label, days_left_label):
            label.setAlignment(Qt.AlignmentFlag.AlignRight)
            layout.addWidget(label)

        self.notes_edit = QTextEdit(self)
        self.notes_edit.setPlainText(self.task.notes)
        self.notes_edit.setMinimumHeight(100)
        layout.addWidget(self.notes_edit)

        self.setMinimumWidth(250)  # Ajusta este valor según tus necesidades
        self.setMaximumWidth(400)  # Ajusta este valor según tus necesidades
        self.setMaximumHeight(300)  # Ajusta este valor según tus necesidades

        self.adjustSize()
        self.update_colors()

        self.notes_edit.textChanged.connect(self.update_task_notes)

    def calculate_working_days_left(self):
        today = datetime.now().date()
        start_date = datetime.strptime(self.task.start_date, "%d/%m/%Y").date()
        end_date = datetime.strptime(self.task.end_date, "%d/%m/%Y").date()

        if end_date < today:
            return 0
        elif start_date <= today <= end_date:
            count_from = today
        else:
            count_from = start_date

        working_days = 0
        current_date = count_from
        while current_date <= end_date:
            if self.cal.is_working_day(current_date):
                working_days += 1
            current_date += timedelta(days=1)

        return working_days

    def update_task_notes(self):
        if self.task.notes != self.notes_edit.toPlainText():
            self.task.notes = self.notes_edit.toPlainText()
            self.notesChanged.emit()  # Emite la señal cuando las notas cambian

    def update_colors(self):
        palette = self.palette()
        self.background_color = palette.color(QPalette.ColorRole.Window)
        self.text_color = palette.color(QPalette.ColorRole.WindowText)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self.background_color)
        painter.setPen(Qt.PenStyle.NoPen)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 10, 10)
        painter.drawPath(path)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.PaletteChange:
            self.update_colors()
            for child in self.findChildren(QLabel):
                child.setStyleSheet(f"color: {self.text_color.name()};")
            self.update()
        super().changeEvent(event)

    def sizeHint(self):
        return self.layout().sizeHint()

class TaskTableWidget(QWidget):
    taskDataChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Crear el modelo y la vista
        self.model = TaskTableModel()
        self.table_view = QTableView()
        self.table_view.setModel(self.model)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_task_context_menu)
        self.main_layout.addWidget(self.table_view)

        # Configurar los delegados
        self.table_view.setItemDelegateForColumn(0, StateButtonDelegate(self.table_view))
        self.table_view.setItemDelegateForColumn(1, LineEditDelegate(self.table_view))
        self.table_view.setItemDelegateForColumn(2, DateEditDelegate(self.table_view))
        self.table_view.setItemDelegateForColumn(3, DateEditDelegate(self.table_view))
        self.table_view.setItemDelegateForColumn(4, SpinBoxDelegate(minimum=1, maximum=1000, parent=self.table_view))
        self.table_view.setItemDelegateForColumn(5, SpinBoxDelegate(minimum=0, maximum=100, parent=self.table_view))

        # Configurar los encabezados
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table_view.verticalHeader().setDefaultSectionSize(self.main_window.ROW_HEIGHT if self.main_window else 25)
        self.table_view.verticalHeader().setMinimumSectionSize(self.main_window.ROW_HEIGHT if self.main_window else 25)

        # Botón de menú
        self.menu_button = QPushButton("☰", self)
        self.menu_button.clicked.connect(self.show_menu)
        QTimer.singleShot(0, self.adjust_button_size)

        self.current_file_path = None
        self.setup_table_style()
        self.setup_item_change_detection()

    def setup_table_style(self):
        self.table_view.setStyleSheet("""
        QTableView {
            gridline-color: transparent;
            border: none;
        }
        QTableView::item {
            padding: 0px;
            border: none;
        }
        """)
        self.table_view.setColumnWidth(0, 25)
        self.menu_button.setFixedSize(QSize(25, self.main_window.ROW_HEIGHT if self.main_window else 25))
        self.menu_button.move(0, 0)

    def setup_item_change_detection(self):
        self.model.dataChanged.connect(self.on_data_changed)

    def on_data_changed(self, topLeft, bottomRight, roles):
        if Qt.ItemDataRole.EditRole in roles or Qt.ItemDataRole.DisplayRole in roles:
            if self.main_window:
                self.main_window.set_unsaved_changes(True)
                self.main_window.update_gantt_chart()

    def show_menu(self):
        menu = QMenu(self)

        save_action = menu.addAction("Guardar")
        save_action.triggered.connect(self.save_file)

        save_as_action = menu.addAction("Guardar como")
        save_as_action.triggered.connect(self.save_file_as)

        new_action = menu.addAction("Nuevo")
        new_action.triggered.connect(self.new_project)

        open_action = menu.addAction("Abrir")
        open_action.triggered.connect(self.open_file)

        view_menu = menu.addMenu("Vista")
        # Submenús de Vista
        complete_action = view_menu.addAction("Completa")
        year_action = view_menu.addAction("Año")
        six_month_action = view_menu.addAction("6 Meses")
        three_month_action = view_menu.addAction("3 Meses")
        one_month_action = view_menu.addAction("1 Mes")

        # Conectar las acciones de vista
        if self.main_window:
            complete_action.triggered.connect(self.main_window.set_complete_view)
            year_action.triggered.connect(self.main_window.set_year_view)
            six_month_action.triggered.connect(self.main_window.set_six_month_view)
            three_month_action.triggered.connect(self.main_window.set_three_month_view)
            one_month_action.triggered.connect(self.main_window.set_one_month_view)

        reset_all_colors_action = menu.addAction("Restablecer colores")
        reset_all_colors_action.triggered.connect(self.reset_all_colors)

        import_menu = menu.addMenu("Importar")
        import_menu.addAction("PDF")
        import_menu.addAction("MPP")
        import_menu.addAction("XLSX")

        export_menu = menu.addMenu("Exportar")
        export_menu.addAction("PDF")
        export_menu.addAction("XLSX")

        config_menu = menu.addMenu("Configuración")
        appearance_menu = config_menu.addMenu("Apariencia")
        appearance_menu.addAction("Modo claro")
        appearance_menu.addAction("Modo oscuro")
        language_menu = config_menu.addMenu("Idioma")
        language_menu.addAction("Español")
        language_menu.addAction("Inglés")
        language_menu.addAction("Alemán")
        language_menu.addAction("Francés")
        region_menu = config_menu.addMenu("Región")
        region_menu.addAction("Detectar automáticamente")
        region_menu.addAction("Seleccionar país")
        config_menu.addAction("API AI")
        config_menu.addAction("Abrir al iniciar el OS")
        config_menu.addAction("Alertas")

        menu.addAction("Acerca de")

        action = menu.exec(self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft()))
        if action:
            print(f"Acción seleccionada: {action.text()}")

    def adjust_button_size(self):
        header = self.table_view.horizontalHeader()
        header_height = header.height()
        button_width = 25  # Ya establecido en setup_table_style
        self.menu_button.setFixedSize(QSize(button_width, header_height))
        self.menu_button.move(0, 0)

    def show_task_context_menu(self, position):
        index = self.table_view.indexAt(position)
        if index.isValid() and self.main_window:
            global_pos = self.table_view.viewport().mapToGlobal(position)
            self.main_window.show_task_context_menu(global_pos, index.row())

    def save_file(self):
        if hasattr(self, 'current_file_path') and self.current_file_path:
            success = self.save_tasks_to_file(self.current_file_path)
        else:
            success = self.save_file_as()

        if success and self.main_window:
            self.main_window.set_unsaved_changes(False)
        return success

    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar como", "", "Archivos BPM (*.bpm);;Todos los archivos (*)"
        )
        if file_path:
            if not file_path.lower().endswith('.bpm'):
                file_path += '.bpm'
            success = self.save_tasks_to_file(file_path)
            if success:
                self.current_file_path = file_path
                if self.main_window:
                    self.main_window.set_unsaved_changes(False)
            return success
        return False

    def open_file(self):
        if self.main_window and self.main_window.check_unsaved_changes():
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Abrir archivo", "", "Archivos BPM (*.bpm);;Todos los archivos (*)"
            )
            if file_path:
                self.load_tasks_from_file(file_path)

    def save_tasks_to_file(self, file_path):
        try:
            with open(file_path, 'w') as file:
                for task in self.model.tasks:
                    file.write("[TASK]\n")
                    file.write(f"NAME: {task.name}\n")
                    # Agregar el campo PARENT
                    if task.is_subtask and task.parent_task:
                        file.write(f"PARENT: {task.parent_task.name}\n")
                    else:
                        file.write("PARENT:\n")
                    file.write(f"START: {task.start_date}\n")
                    file.write(f"END: {task.end_date}\n")
                    file.write(f"DURATION: {task.duration}\n")
                    dedication = task.dedication
                    file.write(f"DEDICATION: {dedication}\n")
                    for note_line in task.notes.split('\n'):
                        file.write(f"NOTES: {note_line}\n")
                    file.write("[/TASK]\n\n")
            self.current_file_path = file_path
            print(f"Archivo guardado en: {file_path}")
            return True
        except Exception as e:
            print(f"Error al guardar el archivo: {e}")
            return False

    def load_tasks_from_file(self, file_path):
        try:
            self.model.beginResetModel()
            self.model.tasks = []
            with open(file_path, 'r') as file:
                task_data_list = []
                task_data = {}
                notes = []
                for line in file:
                    line = line.strip()
                    if line == "[TASK]":
                        task_data = {}
                        notes = []
                    elif line == "[/TASK]":
                        task_data['NOTES'] = '\n'.join(notes)
                        task_data_list.append(task_data)
                    elif ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip()
                        value = value.strip()
                        if key == "NOTES":
                            notes.append(value)
                        else:
                            task_data[key] = value

            # Procesar task_data_list
            name_to_task = {}
            for task_data in task_data_list:
                parent_name = task_data.get('PARENT', '').strip()
                is_subtask = bool(parent_name)
                task = Task(
                    task_data.get('NAME', "Nueva Tarea"),
                    task_data.get('START', QDate.currentDate().toString("dd/MM/yyyy")),
                    task_data.get('END', QDate.currentDate().addDays(1).toString("dd/MM/yyyy")),
                    task_data.get('DURATION', "1"),
                    task_data.get('DEDICATION', "100"),
                    QColor(task_data.get('COLOR', '#22a39f')) if 'COLOR' in task_data else QColor(34, 163, 159),
                    task_data.get('NOTES', "")
                )
                task.is_subtask = is_subtask
                task.parent_task = None  # Se establecerá después

                self.model.tasks.append(task)
                name_to_task[task.name] = task

            # Establecer relaciones de padres
            for task in self.model.tasks:
                if task.is_subtask:
                    parent_name = task_data.get('PARENT', '').strip()
                    parent_task = name_to_task.get(parent_name)
                    if parent_task:
                        task.parent_task = parent_task
                        parent_task.subtasks.append(task)
                    else:
                        print(f"Warning: parent task '{parent_name}' not found for task '{task.name}'")

            self.model.endResetModel()
            self.current_file_path = file_path
            if self.main_window:
                self.main_window.set_unsaved_changes(False)
                self.main_window.update_gantt_chart()
            print(f"Archivo cargado desde: {file_path}")
        except Exception as e:
            print(f"Error al cargar el archivo: {e}")

    def add_task_to_table(self, task_data, editable=False):
        task = Task(
            task_data.get('NAME', "Nueva Tarea"),
            task_data.get('START', QDate.currentDate().toString("dd/MM/yyyy")),
            task_data.get('END', QDate.currentDate().addDays(1).toString("dd/MM/yyyy")),
            task_data.get('DURATION', "1"),
            task_data.get('DEDICATION', "40"),
            QColor(task_data.get('COLOR', '#22a39f')),
            task_data.get('NOTES', "")
        )
        self.model.insertTask(task)
        self.taskDataChanged.emit()
        if self.main_window:
            self.main_window.set_unsaved_changes(True)
            self.main_window.update_gantt_chart()

    def reset_all_colors(self):
        default_color = QColor(34, 163, 159)  # Color por defecto
        for task in self.model.tasks:
            task.color = default_color
        self.model.dataChanged.emit(self.model.index(0, 1), self.model.index(self.model.rowCount()-1, 1), [Qt.ItemDataRole.BackgroundRole])
        if self.main_window:
            self.main_window.set_unsaved_changes(True)
            self.main_window.update_gantt_chart()

    def new_project(self):
        # Implementar la lógica para crear un nuevo proyecto
        pass

class MainWindow(QMainWindow):
    ROW_HEIGHT = 25

    def __init__(self):
        super().__init__()
        self.unsaved_changes = False
        self.base_title = "Baby project manager"
        self.setWindowTitle(self.base_title)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.setMinimumSize(800, 600)  # Establece un tamaño mínimo para la ventana
        self.setGeometry(100, 100, 1200, 800)
        self.tasks = []
        self.current_file_path = None
        self.selected_period = 365  # Por defecto, 1 año (en días)
        self.setMouseTracking(True)
        self.wheel_accumulator = 0
        self.wheel_threshold = 100  # Ajusta este valor
        self.current_view = "complete"  # Añadir esta línea

        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.task_table_widget = TaskTableWidget(self)
        left_layout.addWidget(self.task_table_widget)
        self.table_view = self.task_table_widget.table_view
        self.model = self.task_table_widget.model

        self.table_view.horizontalHeader().sectionClicked.connect(self.on_header_click)

        add_task_button = QPushButton("Agregar Nueva Tarea")
        add_task_button.clicked.connect(self.add_new_task)
        left_layout.addWidget(add_task_button)

        left_widget.setMinimumWidth(int(self.width() * 0.43))
        main_layout.addWidget(left_widget)

        self.gantt_widget = GanttWidget(self.tasks, self.ROW_HEIGHT, self)
        self.gantt_header = self.gantt_widget.header
        self.gantt_chart = self.gantt_widget.chart
        self.gantt_chart.main_window = self

        # Conectar la señal colorChanged
        self.gantt_chart.colorChanged.connect(self.update_task_color)

        main_layout.addWidget(self.gantt_widget, 1)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.table_view.verticalScrollBar().valueChanged.connect(self.sync_scroll)
        self.table_view.verticalScrollBar().valueChanged.connect(self.sync_scroll)

        self.adjust_all_row_heights()

        self.update_gantt_chart()

        from PySide6.QtGui import QKeySequence, QShortcut

        # Atajo de teclado para guardar
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.quick_save)

        self.set_unsaved_changes(False)

    def update_title(self):
        if self.unsaved_changes:
            self.setWindowTitle(f"*{self.base_title}")
        else:
            self.setWindowTitle(self.base_title)

    def set_unsaved_changes(self, value):
        if self.unsaved_changes != value:
            self.unsaved_changes = value
            self.update_title()

    def delete_task(self, row):
        if row >= 0:
            # Obtener la tarea a eliminar
            task = self.model.getTask(row)

            if task:
                # Si es una subtarea, actualizar la tarea padre
                if task.is_subtask and task.parent_task:
                    task.parent_task.subtasks.remove(task)

                # Si es una tarea padre, eliminar también sus subtareas
                if not task.is_subtask:
                    # Encontrar todas las subtareas y eliminarlas
                    rows_to_remove = [row]
                    for i in range(row + 1, self.model.rowCount()):
                        subtask = self.model.getTask(i)
                        if subtask and subtask.is_subtask:
                            rows_to_remove.append(i)
                        else:
                            break
                    for i in reversed(rows_to_remove):
                        self.model.removeTask(i)
                else:
                    # Si es una subtarea, solo eliminar la fila actual
                    self.model.removeTask(row)

                # Actualizar la estructura de datos
                self.update_task_structure()

                # Actualizar los botones de estado
                self.task_table_widget.reset_all_colors()

                self.set_unsaved_changes(True)
                self.update_gantt_chart()

    def update_task_structure(self):
        # Reconstruir la estructura de tareas
        self.tasks = []
        current_parent = None

        for row in range(self.model.rowCount()):
            task = self.model.getTask(row)
            if task:
                if not task.is_subtask:
                    current_parent = task
                    current_parent.subtasks = []
                    self.tasks.append(current_parent)
                else:
                    if current_parent:
                        current_parent.subtasks.append(task)
                        task.parent_task = current_parent

        # Actualizar los botones de estado después de reconstruir la estructura
        self.task_table_widget.reset_all_colors()

    def count_subtasks(self, row):
        count = 0
        for i in range(row + 1, self.model.rowCount()):
            task = self.model.getTask(i)
            if task and task.is_subtask:
                count += 1
            else:
                break
        return count

    def sync_scroll(self):
        sender = self.sender()
        if sender == self.table_view.verticalScrollBar():
            self.gantt_widget.chart.update()

    def add_new_task(self):
        default_color = QColor(34, 163, 159)  # Color por defecto
        task_data = {
            'NAME': "Nueva Tarea",
            'START': QDate.currentDate().toString("dd/MM/yyyy"),
            'END': QDate.currentDate().toString("dd/MM/yyyy"),
            'DURATION': "1",
            'DEDICATION': "40",
            'COLOR': default_color.name(),
            'NOTES': ""
        }
        self.task_table_widget.add_task_to_table(task_data, editable=True)
        self.adjust_all_row_heights()
        self.update_gantt_chart()
        if self.model.rowCount() > 0:
            self.set_unsaved_changes(True)

    def adjust_all_row_heights(self):
        for row in range(self.model.rowCount()):
            self.table_view.setRowHeight(row, self.ROW_HEIGHT)

    def validateAndCalculateDays(self, start_entry, end_entry, days_entry):
        cal = Colombia()
        start_date = start_entry.date().toPython()
        end_date = end_entry.date().toPython()

        if end_date < start_date:
            end_entry.setDate(QDate(start_date))
            end_date = start_date

        business_days = 0
        current_date = start_date
        while current_date <= end_date:
            if cal.is_working_day(current_date):
                business_days += 1
            current_date += timedelta(days=1)

        days_entry.setText(str(business_days))
        self.set_unsaved_changes(True)
        self.update_gantt_chart()

    def calculateEndDateIfChanged(self, start_entry, days_entry, end_entry):
        if not days_entry.text().isdigit():
            return

        cal = Colombia()
        start_date = start_entry.date().toPython()
        target_days = int(days_entry.text())

        business_days = 0
        end_date = start_date
        while business_days < target_days:
            if cal.is_working_day(end_date):
                business_days += 1
            if business_days < target_days:
                end_date += timedelta(days=1)

        end_entry.setDate(QDate(end_date))
        self.set_unsaved_changes(True)
        self.update_gantt_chart()

    def show_task_context_menu(self, global_pos, task_index):
        if task_index < 0 or task_index >= self.model.rowCount():
            return

        task = self.model.getTask(task_index)
        if not task:
            return

        menu = QMenu()
        duplicate_action = menu.addAction("Duplicar")
        if not task.is_subtask:
            insert_action = menu.addAction("Insertar")
        move_up_action = menu.addAction("Mover arriba")
        move_down_action = menu.addAction("Mover abajo")
        if not task.is_subtask:
            add_subtask_action = menu.addAction("Agregar subtarea")
        delete_action = menu.addAction("Eliminar")
        reset_color_action = menu.addAction("Color por defecto")

        action = menu.exec(global_pos)

        # Manejar la acción seleccionada
        if action:
            self.handle_context_menu_action(action, task_index, task)

        # Asegurarse de que el menú se cierre
        menu.close()

    def handle_context_menu_action(self, action, task_index, task):
        action_text = action.text()
        if action_text == "Duplicar":
            self.duplicate_task(task_index)
        elif action_text == "Insertar" and not task.is_subtask:
            self.insert_task(task_index)
        elif action_text == "Mover arriba":
            self.move_task_up(task_index)
        elif action_text == "Mover abajo":
            self.move_task_down(task_index)
        elif action_text == "Agregar subtarea" and not task.is_subtask:
            self.add_subtask(task_index)
        elif action_text == "Eliminar":
            self.delete_task(task_index)
        elif action_text == "Color por defecto":
            self.reset_task_color(task_index)

    def duplicate_task(self, row):
        if row >= 0:
            task = self.model.getTask(row)
            if task:
                # Duplicar la tarea
                task_data = {
                    'NAME': task.name + " (copia)",
                    'START': task.start_date,
                    'END': task.end_date,
                    'DURATION': task.duration,
                    'DEDICATION': task.dedication,
                    'COLOR': task.color.name(),
                    'NOTES': task.notes
                }
                duplicated_task = Task(
                    task_data.get('NAME'),
                    task_data.get('START'),
                    task_data.get('END'),
                    task_data.get('DURATION'),
                    task_data.get('DEDICATION'),
                    QColor(task_data.get('COLOR')),
                    task_data.get('NOTES', '')
                )
                duplicated_task.is_subtask = task.is_subtask
                duplicated_task.parent_task = task.parent_task
                self.model.insertTask(duplicated_task, row + 1)

                # Si la tarea original tiene subtareas, duplicarlas también
                if not task.is_subtask and task.subtasks:
                    for subtask in task.subtasks:
                        subtask_data = {
                            'NAME': subtask.name + " (copia)",
                            'START': subtask.start_date,
                            'END': subtask.end_date,
                            'DURATION': subtask.duration,
                            'DEDICATION': subtask.dedication,
                            'COLOR': subtask.color.name(),
                            'NOTES': subtask.notes
                        }
                        duplicated_subtask = Task(
                            subtask_data.get('NAME'),
                            subtask_data.get('START'),
                            subtask_data.get('END'),
                            subtask_data.get('DURATION'),
                            subtask_data.get('DEDICATION'),
                            QColor(subtask_data.get('COLOR')),
                            subtask_data.get('NOTES', '')
                        )
                        duplicated_subtask.is_subtask = True
                        duplicated_subtask.parent_task = duplicated_task
                        self.model.insertTask(duplicated_subtask, row + 2)

                self.update_gantt_chart()
                self.set_unsaved_changes(True)

    def insert_task(self, row):
        # Insertar una nueva tarea en la fila especificada
        task_data = {
            'NAME': "Nueva Tarea",
            'START': QDate.currentDate().toString("dd/MM/yyyy"),
            'END': QDate.currentDate().toString("dd/MM/yyyy"),
            'DURATION': "1",
            'DEDICATION': "40",
            'COLOR': QColor(34, 163, 159).name(),
            'NOTES': ""
        }
        self.model.insertTask(Task(
            task_data.get('NAME'),
            task_data.get('START'),
            task_data.get('END'),
            task_data.get('DURATION'),
            task_data.get('DEDICATION'),
            QColor(task_data.get('COLOR')),
            task_data.get('NOTES', '')
        ), row + 1)
        self.update_gantt_chart()
        self.set_unsaved_changes(True)

    def move_task_up(self, row):
        if row > 0:
            task = self.model.getTask(row)
            above_task = self.model.getTask(row - 1)
            if task and above_task:
                # Verificar si se está intentando mover una subtarea sobre su padre
                if above_task == task.parent_task:
                    return  # No permitir mover una subtarea sobre su padre

                # Intercambiar las tareas
                self.model.tasks[row], self.model.tasks[row - 1] = self.model.tasks[row - 1], self.model.tasks[row]
                self.model.dataChanged.emit(self.model.index(row - 1, 0), self.model.index(row, 5), [Qt.DisplayRole, Qt.BackgroundRole])
                self.update_gantt_chart()
                self.set_unsaved_changes(True)

    def move_task_down(self, row):
        if row < self.model.rowCount() - 1:
            task = self.model.getTask(row)
            below_task = self.model.getTask(row + 1)
            if task and below_task:
                # Verificar si se está intentando mover una subtarea
                if task.is_subtask:
                    # Verificar si la tarea de abajo es del mismo padre
                    if below_task.is_subtask and below_task.parent_task == task.parent_task:
                        # Mover la subtarea hacia abajo
                        self.model.tasks[row], self.model.tasks[row + 1] = self.model.tasks[row + 1], self.model.tasks[row]
                        self.model.dataChanged.emit(self.model.index(row, 0), self.model.index(row + 1, 5), [Qt.DisplayRole, Qt.BackgroundRole])
                        self.update_gantt_chart()
                        self.set_unsaved_changes(True)
                else:
                    # Contar cuántas subtareas tiene la tarea actual
                    subtask_count = self.count_subtasks(row)

                    # Verificar si hay una tarea después de las subtareas
                    if row + subtask_count + 1 < self.model.rowCount():
                        # Obtener la tarea que está debajo
                        next_task = self.model.getTask(row + subtask_count + 1)

                        # Mover la tarea actual y sus subtareas a la nueva posición
                        for i in range(subtask_count + 1):
                            self.model.tasks.insert(row + subtask_count + 2, self.model.tasks.pop(row))
                        self.model.dataChanged.emit(self.model.index(0, 0), self.model.index(self.model.rowCount()-1, 5), [Qt.DisplayRole, Qt.BackgroundRole])
                        self.update_gantt_chart()
                        self.set_unsaved_changes(True)
                    else:
                        # Es la última tarea padre con subtareas, no hacer nada
                        pass

    def reset_task_color(self, row):
        if row >= 0:
            task = self.model.getTask(row)
            if task:
                default_color = QColor(34, 163, 159)  # Color por defecto
                task.color = default_color
                index = self.model.index(row, 1)
                self.model.dataChanged.emit(index, index, [Qt.BackgroundRole])
                self.set_unsaved_changes(True)
                self.update_gantt_chart()

    def show_context_menu(self, position):
        index = self.table_view.indexAt(position)
        if index.isValid():
            global_pos = self.table_view.viewport().mapToGlobal(position)
            self.show_task_context_menu(global_pos, index.row())

    def update_gantt_chart(self, set_unsaved=True):
        self.tasks = []
        for row in range(self.model.rowCount()):
            task = self.model.getTask(row)
            if task:
                # Actualizar la información de la tarea
                # En este caso, los datos ya están actualizados en el modelo
                # Solo agregamos todas las tareas, incluyendo subtareas
                self.tasks.append(task)

        if self.tasks:
            min_date = min(QDate.fromString(task.start_date, "dd/MM/yyyy") for task in self.tasks)
            max_date = max(QDate.fromString(task.end_date, "dd/MM/yyyy") for task in self.tasks)
        else:
            current_date = QDate.currentDate()
            min_date = current_date
            max_date = current_date.addDays(30)  # Mostrar un mes por defecto si no hay tareas

        today = QDate.currentDate()

        if self.current_view == "year":
            min_date = today.addDays(-int(today.daysTo(today.addYears(1)) * 0.125))
            max_date = min_date.addYears(1)
        elif self.current_view == "one_month":
            min_date = today.addDays(-7)  # Una semana antes de hoy
            max_date = min_date.addMonths(1)
        elif self.current_view == "three_month":
            min_date = today.addDays(-int(today.daysTo(today.addMonths(3)) * 0.125))
            max_date = min_date.addMonths(3)
        elif self.current_view == "six_month":
            min_date = today.addDays(-int(today.daysTo(today.addMonths(6)) * 0.125))
            max_date = min_date.addMonths(6)
        elif self.current_view == "complete":
            pass  # 'pass' para evitar un bloque vacío

        # Asegúrate de que haya al menos un día de diferencia
        if min_date == max_date:
            max_date = min_date.addDays(1)

        days_total = min_date.daysTo(max_date) + 1
        available_width = self.gantt_widget.width()
        pixels_per_day = max(0.1, available_width / days_total)

        self.gantt_widget.update_parameters(min_date, max_date, pixels_per_day)
        self.gantt_chart.tasks = self.tasks
        self.gantt_chart.setMinimumHeight(max(len(self.tasks) * self.ROW_HEIGHT, self.gantt_widget.height()))
        self.gantt_chart.update()
        self.gantt_header.update()

        # Forzar la actualización del diseño
        self.gantt_widget.updateGeometry()

        if set_unsaved and self.tasks:
            self.set_unsaved_changes(True)

    def update_task_color(self, task_index, color):
        task = self.model.getTask(task_index)
        if task:
            task.color = color  # Actualizar el color en el objeto Task
            index = self.model.index(task_index, 1)
            self.model.dataChanged.emit(index, index, [Qt.BackgroundRole])
            self.set_unsaved_changes(True)
            self.update_gantt_chart()

    def set_period(self, days):
        self.selected_period = days
        self.update_gantt_chart()

    def closeEvent(self, event):
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self, 'Cambios sin guardar',
                '¿Desea guardar los cambios antes de salir?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            if reply == QMessageBox.Save:
                if self.task_table_widget.save_file():
                    event.accept()
                else:
                    # Si el guardado falla, pregunta al usuario si desea salir sin guardar
                    secondary_reply = QMessageBox.question(
                        self, 'Error al guardar',
                        'No se pudieron guardar los cambios. ¿Desea salir sin guardar?',
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if secondary_reply == QMessageBox.Yes:
                        event.accept()
                    else:
                        event.ignore()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_gantt_chart(set_unsaved=False)
        self.task_table_widget.adjust_button_size()

    def check_unsaved_changes(self):
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self,
                'Cambios sin guardar',
                '¿Desea guardar los cambios antes de continuar?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            if reply == QMessageBox.Save:
                return self.task_table_widget.save_file()
            elif reply == QMessageBox.Cancel:
                return False
        return True

    def quick_save(self):
        if self.task_table_widget.save_file():
            self.set_unsaved_changes(False)

    def print_task_table_contents(self):
        print("Task Table Contents:")
        for row in range(self.model.rowCount()):
            task = self.model.getTask(row)
            print(f"Row {row}: Name={task.name}, Task={task}")

    def set_year_view(self):
        self.current_view = "year"
        self.update_gantt_chart(set_unsaved=False)

    def set_complete_view(self):
        self.current_view = "complete"
        self.update_gantt_chart(set_unsaved=False)

    def set_one_month_view(self):
        self.current_view = "one_month"
        self.update_gantt_chart(set_unsaved=False)

    def set_three_month_view(self):
        self.current_view = "three_month"
        self.update_gantt_chart(set_unsaved=False)

    def set_six_month_view(self):
        self.current_view = "six_month"
        self.update_gantt_chart(set_unsaved=False)

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            self.wheel_accumulator += delta

            if self.wheel_accumulator >= self.wheel_threshold:
                self.zoom_in_view()
                self.wheel_accumulator = 0  # Reiniciar después de zoom in
            elif self.wheel_accumulator <= -self.wheel_threshold:
                self.zoom_out_view()
                self.wheel_accumulator = 0  # Reiniciar después de zoom out

            event.accept()
        else:
            super().wheelEvent(event)

    def zoom_in_view(self):
        if self.current_view == "complete":
            self.set_year_view()
        elif self.current_view == "year":
            self.set_six_month_view()
        elif self.current_view == "six_month":
            self.set_three_month_view()
        elif self.current_view == "three_month":
            self.set_one_month_view()
        else:  # Si ya está en "one_month"
            self.wheel_accumulator = 0  # Reiniciar el acumulador

    def zoom_out_view(self):
        if self.current_view == "one_month":
            self.set_three_month_view()
        elif self.current_view == "three_month":
            self.set_six_month_view()
        elif self.current_view == "six_month":
            self.set_year_view()
        elif self.current_view == "year":
            self.set_complete_view()
        else:  # Si ya está en "complete"
            self.wheel_accumulator = 0  # Reiniciar el acumulador

    def add_subtask(self, parent_task_index):
        parent_task = self.model.getTask(parent_task_index)

        # Crear una nueva subtarea
        subtask = Task(
            f"Subtarea de {parent_task.name}",
            parent_task.start_date,
            parent_task.end_date,
            "1",
            "40",
            parent_task.color.lighter(120),
            ""
        )
        subtask.is_subtask = True
        subtask.parent_task = parent_task

        # Insertar la subtarea justo después de la tarea padre
        self.model.insertTask(subtask, parent_task_index + 1)

        # Actualizar el botón de estado de la tarea padre si es necesario
        self.task_table_widget.reset_all_colors()

        # Actualizar el gráfico de Gantt
        self.update_gantt_chart()
        self.set_unsaved_changes(True)

    def on_header_click(self, logical_index):
        # Implementar la lógica de ordenamiento aquí
        # Por ejemplo, puedes usar el método sort del modelo
        self.model.sort(logical_index, Qt.AscendingOrder)
        self.update_gantt_chart()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Usar el estilo Fusion que soporta temas oscuros/claros
    # Aplicar la paleta del sistema
    app.setPalette(app.style().standardPalette())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
