#Integracion file_gui
#9
import os
import sys
import subprocess
from pathlib import Path
import inspect
import math
import ast
from datetime import timedelta, datetime
from workalendar.america import Colombia
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QDateEdit, QScrollArea, QTableView,
    QHeaderView, QMenu, QScrollBar, QFileDialog, QMessageBox, QColorDialog,
    QTextEdit, QStyledItemDelegate, QStyle, QSpinBox, QGridLayout, QSizePolicy
)
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QPainterPath, QPalette, QContextMenuEvent, QKeySequence, QShortcut, QWheelEvent
from PySide6.QtCore import Qt, QDate, QRect, QTimer, QSize, QRectF, QEvent, Signal, QPoint, QAbstractTableModel, QModelIndex
from hipervinculo import HyperlinkTextEdit
from file_gui import MainWindow as FileGUIWindow

#from file import class1 , class2, class3

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

class Task:
    def __init__(self, name, start_date, end_date, duration, dedication, color=None, notes="", notes_html="", file_links=None):
        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.duration = duration
        self.dedication = dedication
        self.color = color or QColor(34, 163, 159)
        self.notes = notes
        self.notes_html = notes_html
        self.file_links = file_links or {}
        self.subtasks = []
        self.is_subtask = False
        self.parent_task = None
        self.is_editing = False
        self.is_collapsed = False

    @property
    def formatted_name(self):
        return "       " + self.name if self.is_subtask else self.name

    def has_subtasks(self):
        return bool(self.subtasks)

    def toggle_editing(self):
        self.is_editing = not self.is_editing

    def set_editing(self, value):
        self.is_editing = value

    def toggle_collapsed(self):
        self.is_collapsed = not self.is_collapsed

    def update_subtasks(self):
        if self.parent_task:
            self.parent_task.subtasks = [task for task in self.parent_task.subtasks if task != self]
        for subtask in self.subtasks:
            subtask.parent_task = self

class TaskTableModel(QAbstractTableModel):
    def __init__(self, tasks=None):
        super(TaskTableModel, self).__init__()
        self.headers = ["", "Nombre", "Fecha inicial", "Fecha final", "Días", "%"]
        self.tasks = tasks or []
        self.update_visible_tasks()

    def update_visible_tasks(self):
        self.visible_tasks = []
        self.visible_to_actual = []
        self.actual_to_visible = {}
        idx = 0
        visible_idx = 0
        while idx < len(self.tasks):
            task = self.tasks[idx]
            self.visible_tasks.append(task)
            self.visible_to_actual.append(idx)
            self.actual_to_visible[idx] = visible_idx
            idx += 1
            visible_idx += 1
            if not task.is_subtask and task.is_collapsed:
                while idx < len(self.tasks) and self.tasks[idx].is_subtask:
                    idx += 1

    def rowCount(self, parent=QModelIndex()):
        return len(self.visible_tasks)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        task = self.visible_tasks[index.row()]
        column = index.column()

        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            if column == 0:
                return ""  # Para el botón de estado, se usará un delegado
            elif column == 1:
                return task.formatted_name  # Cambia aquí
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

    def insertTask(self, task, actual_position=None):
        if actual_position is not None:
            # Calcular la posición visible correspondiente
            position = self.actual_to_visible.get(actual_position, self.rowCount())
        else:
            actual_position = len(self.tasks)
            position = self.rowCount()
        self.beginInsertRows(QModelIndex(), position, position)
        self.tasks.insert(actual_position, task)
        self.update_visible_tasks()
        self.endInsertRows()

    def removeTask(self, position):
        if 0 <= position < self.rowCount():
            actual_position = self.visible_to_actual[position]
            self.beginRemoveRows(QModelIndex(), position, position)
            del self.tasks[actual_position]
            self.update_visible_tasks()
            self.endRemoveRows()
            return True
        return False

    def getTask(self, row):
        if 0 <= row < self.rowCount():
            return self.visible_tasks[row]
        return None

    def move_block_down(self, start_row, block_size, insertion_row):
            """
            Mueve un bloque de tareas hacia abajo en el modelo.
            start_row: La fila de inicio del bloque.
            block_size: El tamaño del bloque de tareas (incluye la tarea y subtareas).
            insertion_row: La fila de inserción donde se moverá el bloque.
            """
            if start_row < 0 or start_row + block_size > self.rowCount() or insertion_row > self.rowCount():
                return False  # Validar si las filas son válidas.

            self.beginMoveRows(QModelIndex(), start_row, start_row + block_size - 1, QModelIndex(), insertion_row)

            # Extraer el bloque de tareas desde start_row hasta start_row + block_size
            moving_tasks = self.visible_tasks[start_row:start_row + block_size]
            # Eliminar el bloque de tareas original
            del self.visible_tasks[start_row:start_row + block_size]

            # Insertar el bloque en la nueva posición
            self.visible_tasks[insertion_row:insertion_row] = moving_tasks

            self.update_visible_tasks()
            self.endMoveRows()
            return True

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
            if not index.isValid():
                return False

            task = self.visible_tasks[index.row()]
            column = index.column()

            if role == Qt.ItemDataRole.EditRole:
                if column == 1:
                    task.name = str(value)
                elif column == 2:
                    task.start_date = str(value)
                    # Recalcular la duración al cambiar la fecha inicial
                    self.recalculate_duration(task)
                elif column == 3:
                    task.end_date = str(value)
                    # Recalcular la duración al cambiar la fecha final
                    self.recalculate_duration(task)
                elif column == 4:
                    task.duration = str(value)
                    # Recalcular la fecha final al cambiar la duración
                    self.recalculate_end_date(task)
                elif column == 5:
                    task.dedication = str(value)
                task.is_editing = False  # Reset is_editing after editing
                self.dataChanged.emit(index, index, [role])
                return True
            return False

    def recalculate_duration(self, task):
        # Parsear las fechas de inicio y fin
        start_date = QDate.fromString(task.start_date, "dd/MM/yyyy")
        end_date = QDate.fromString(task.end_date, "dd/MM/yyyy")
        if not start_date.isValid() or not end_date.isValid():
            return
        if end_date < start_date:
            # Ajustar la fecha final para que sea igual a la fecha inicial
            end_date = start_date
            task.end_date = end_date.toString("dd/MM/yyyy")
        # Calcular los días laborables entre las fechas
        cal = Colombia()
        business_days = 0
        current_date = start_date.toPython()
        end_date_python = end_date.toPython()
        while current_date <= end_date_python:
            if cal.is_working_day(current_date):
                business_days += 1
            current_date += timedelta(days=1)
        task.duration = str(business_days)
        # Emitir señal de cambio para la columna de duración
        row = self.visible_tasks.index(task)
        duration_index = self.index(row, 4)
        self.dataChanged.emit(duration_index, duration_index, [Qt.ItemDataRole.DisplayRole])

    def recalculate_end_date(self, task):
        # Parsear la fecha de inicio
        start_date = QDate.fromString(task.start_date, "dd/MM/yyyy")
        if not start_date.isValid():
            return
        # Obtener la duración
        if not task.duration.isdigit():
            return
        target_days = int(task.duration)
        # Calcular la fecha final basada en la duración
        cal = Colombia()
        business_days = 0
        end_date = start_date.toPython()
        while business_days < target_days:
            if cal.is_working_day(end_date):
                business_days += 1
            if business_days < target_days:
                end_date += timedelta(days=1)
        task.end_date = QDate(end_date).toString("dd/MM/yyyy")
        # Emitir señal de cambio para la columna de fecha final
        row = self.visible_tasks.index(task)
        end_date_index = self.index(row, 3)
        self.dataChanged.emit(end_date_index, end_date_index, [Qt.ItemDataRole.DisplayRole])

    def sort(self, column, order=Qt.SortOrder.AscendingOrder):
        if column in [1, 2, 3]:  # Columnas "Nombre", "Fecha inicial" y "Fecha final"
            self.layoutAboutToBeChanged.emit()

            # Crear bloques de tareas (tarea padre con sus subtareas)
            blocks = []
            i = 0
            while i < len(self.tasks):
                task = self.tasks[i]
                if not task.is_subtask:
                    # Tarea padre, agregar sus subtareas
                    block = [task]
                    j = i + 1
                    while j < len(self.tasks) and self.tasks[j].is_subtask:
                        block.append(self.tasks[j])
                        j += 1
                    # Ordenar las subtareas dentro del bloque si lo deseas
                    parent_task = block[0]
                    subtasks = block[1:]
                    # Ordenar las subtareas dentro del bloque
                    subtasks.sort(key=self.get_sort_key(column), reverse=(order == Qt.SortOrder.DescendingOrder))
                    block = [parent_task] + subtasks
                    blocks.append(block)
                    i = j
                else:
                    # Si encontramos una subtarea sin padre, la tratamos como bloque individual
                    blocks.append([task])
                    i += 1

            # Ordenar las tareas padres entre sí
            reverse = (order == Qt.SortOrder.DescendingOrder)
            blocks.sort(key=lambda block: self.get_sort_key(column)(block[0]), reverse=reverse)

            # Reconstruir la lista de tareas a partir de los bloques ordenados
            self.tasks = [task for block in blocks for task in block]

            self.update_visible_tasks()
            self.layoutChanged.emit()
        else:
            # Si se hace clic en otra columna, no hacemos nada o implementamos otro ordenamiento
            pass

    def get_sort_key(self, column):
        if column == 1:  # Nombre
            return lambda task: task.name.lower()
        elif column == 2:  # Fecha inicial
            return lambda task: QDate.fromString(task.start_date, "dd/MM/yyyy")
        elif column == 3:  # Fecha final
            return lambda task: QDate.fromString(task.end_date, "dd/MM/yyyy")
        else:
            return lambda task: task.name.lower()  # Valor por defecto

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
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # Permitir expansión horizontal

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
            self.month_color = QColor(100, 100, 100)  # Color para los meses
            self.month_separator_color = QColor(150, 150, 150)  # Color para las líneas de los meses
            self.week_color = QColor(120, 120, 120)  # Color para las semanas
            self.week_separator_color = QColor(180, 180, 180)  # Color para las líneas de las semanas
        else:
            # Modo oscuro: usar gris claro
            self.year_color = QColor(200, 200, 200)  # Gris claro
            self.year_separator_color = QColor(160, 160, 160)  # Gris un poco más oscuro para las líneas
            self.month_color = QColor(180, 180, 180)  # Color para los meses
            self.month_separator_color = QColor(130, 130, 130)  # Color para las líneas de los meses
            self.week_color = QColor(150, 150, 150)  # Color para las semanas
            self.week_separator_color = QColor(110, 110, 110)  # Color para las líneas de las semanas

    def update_parameters(self, min_date, max_date, pixels_per_day):
        self.min_date = min_date
        self.max_date = max_date
        self.pixels_per_day = pixels_per_day
        self.update()  # Redibuja el encabezado

    def paintEvent(self, event):
        if not self.min_date or not self.max_date or not self.pixels_per_day:
            return

        with QPainter(self) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(event.rect(), self.background_color)

            total_days = self.min_date.daysTo(self.max_date)
            show_months = 30 < total_days <= 366  # Mostrar meses si el rango es entre 1 mes y 1 año
            show_weeks = total_days <= 100  # Mostrar semanas si el rango es menor o igual a 3 meses

            if show_weeks:
                year_font = QFont("Arial", 8, QFont.Weight.Bold)
                week_font = QFont("Arial", 7)
                half_height = self.height() // 2
            elif show_months:
                year_font = QFont("Arial", 9, QFont.Weight.Bold)
                month_font = QFont("Arial", 8)
                half_height = self.height() // 2
            else:
                year_font = QFont("Arial", 10, QFont.Weight.Bold)
                half_height = self.height()

            painter.setFont(year_font)

            start_year = self.min_date.year()
            end_year = self.max_date.year()

            # Dibuja los años
            for year in range(start_year, end_year + 1):
                year_start = QDate(year, 1, 1)
                if year_start < self.min_date:
                    year_start = self.min_date

                # El año termina un día antes del inicio del próximo año
                year_end = QDate(year + 1, 1, 1).addDays(-1)
                if year_end > self.max_date:
                    year_end = self.max_date

                start_x = self.min_date.daysTo(year_start) * self.pixels_per_day - self.scroll_offset
                end_x = self.min_date.daysTo(year_end.addDays(1)) * self.pixels_per_day - self.scroll_offset  # Agregar un día para incluir el último día

                # Dibuja líneas verticales para separar los años en el inicio del año
                painter.setPen(QPen(self.year_separator_color, 1))
                line_x = start_x
                painter.drawLine(int(line_x), 0, int(line_x), self.height())

                year_width = end_x - start_x
                year_rect = QRect(int(start_x), 0, int(year_width), half_height)
                painter.setPen(self.year_color)
                painter.drawText(year_rect, Qt.AlignmentFlag.AlignCenter, str(year))

            if show_weeks:
                # Dibujar semanas
                painter.setFont(week_font)
                current_date = self.min_date

                # Alinear current_date al inicio de la semana (por ejemplo, lunes)
                day_of_week = current_date.dayOfWeek()
                if day_of_week != 1:  # Si no es lunes
                    current_date = current_date.addDays(1 - day_of_week)  # Retroceder al lunes anterior

                while current_date <= self.max_date:
                    week_start = current_date
                    week_end = week_start.addDays(6)
                    if week_end > self.max_date:
                        week_end = self.max_date

                    start_x = self.min_date.daysTo(week_start) * self.pixels_per_day - self.scroll_offset
                    end_x = self.min_date.daysTo(week_end.addDays(1)) * self.pixels_per_day - self.scroll_offset  # Agregar un día para incluir el último día

                    # Dibuja líneas verticales para separar las semanas en el inicio de la semana
                    painter.setPen(QPen(self.week_separator_color, 1))
                    line_x = start_x
                    line_top = self.height() * 0.5  # Inicia la línea a la mitad del encabezado
                    painter.drawLine(int(line_x), int(line_top), int(line_x), self.height())

                    # Dibuja las etiquetas de las semanas
                    week_width = end_x - start_x
                    week_rect = QRect(int(start_x), int(line_top), int(week_width), int(self.height() - line_top))
                    week_number = week_start.weekNumber()[0]
                    week_label = f"Semana {week_number}"
                    painter.setPen(self.week_color)
                    painter.drawText(week_rect, Qt.AlignmentFlag.AlignCenter, week_label)

                    # Avanzar a la siguiente semana
                    current_date = week_end.addDays(1)

            elif show_months:
                # Dibujar meses
                painter.setFont(month_font)
                current_date = QDate(self.min_date.year(), self.min_date.month(), 1)
                while current_date <= self.max_date:
                    month_start = current_date
                    month_end = current_date.addMonths(1).addDays(-1)
                    if month_end > self.max_date:
                        month_end = self.max_date

                    start_x = self.min_date.daysTo(month_start) * self.pixels_per_day - self.scroll_offset
                    end_x = self.min_date.daysTo(month_end.addDays(1)) * self.pixels_per_day - self.scroll_offset  # Agregar un día para incluir el último día

                    # Dibuja líneas verticales para separar los meses en el inicio del mes
                    painter.setPen(QPen(self.month_separator_color, 1))
                    line_x = start_x
                    line_top = self.height() * 0.5  # Inicia la línea a la mitad del encabezado
                    painter.drawLine(int(line_x), int(line_top), int(line_x), self.height())

                    # Dibuja las etiquetas de los meses
                    month_width = end_x - start_x
                    month_rect = QRect(int(start_x), int(line_top), int(month_width), int(self.height() - line_top))
                    month_name = current_date.toString("MMM")
                    painter.setPen(self.month_color)
                    painter.drawText(month_rect, Qt.AlignmentFlag.AlignCenter, month_name)

                    # Avanzar al siguiente mes
                    current_date = current_date.addMonths(1)

            # Dibujar la etiqueta para el día de hoy
            today = QDate.currentDate()
            if self.min_date <= today <= self.max_date:
                today_x = self.min_date.daysTo(today) * self.pixels_per_day - self.scroll_offset

                # Dibuja la etiqueta "Hoy" con un fondo gris redondeado
                label_width = 50
                label_height = 20
                label_x = today_x - label_width / 2
                label_y = self.height() - label_height

                # Dibuja el fondo redondeado
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(128, 128, 128, 180))
                painter.drawRoundedRect(QRectF(label_x, label_y, label_width, label_height), 10, 10)

                # Dibuja el texto "Hoy"
                painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                painter.setPen(QColor(242, 211, 136))  # Color del texto del día de hoy
                painter.drawText(QRectF(label_x, label_y, label_width, label_height), Qt.AlignmentFlag.AlignCenter, "Hoy")

    def scrollTo(self, value):
        self.scroll_offset = value
        self.update()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.PaletteChange:
            self.update_colors()
            self.update()
        super().changeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update()  # Asegura que el widget se redibuje cuando cambia de tamaño

class GanttChart(QWidget):
    colorChanged = Signal(int, QColor)
    wheelScrolled = Signal(int)  # Nueva señal para eventos de rueda
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
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)  # Permitir expansión
        self.setMinimumHeight(self.header_height + self.row_height * len(tasks))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.update_colors()
        self.today_line_color = QColor(242,211,136)  # Color para la línea "Hoy"
        self.double_click_occurred = False  # Bandera para controlar doble clic
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.colorChanged.connect(self.on_color_changed)
        self.vertical_offset = 0  # Nuevo atributo para el desplazamiento vertical
        self.highlighted_task_index = None

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
        self.update()  # Redibuja el diagrama de Gantt

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_click_occurred = False
            # Verificar si se hizo clic fuera de una tarea
            task_index = self.get_task_at_position(event.position().toPoint())
            if task_index is None or not self.is_click_on_task_bar(event.position().toPoint(), task_index):
                self.highlighted_task_index = None
                self.update()
                # Deseleccionar cualquier selección en la tabla de tareas
                self.main_window.task_table_widget.table_view.clearSelection()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.highlighted_task_index = None
            self.update()
            self.main_window.task_table_widget.table_view.clearSelection()
        super().keyPressEvent(event)

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
            task_index = int((self.click_pos.y() + self.vertical_offset) / self.row_height)
            if 0 <= task_index < len(self.tasks):
                task = self.tasks[task_index]
                self.highlighted_task_index = task_index  # Resaltar la tarea
                self.update()  # Redibujar el diagrama de Gantt
                # Seleccionar la fila en la tabla de tareas
                self.main_window.task_table_widget.table_view.selectRow(task_index)
                # Asegurarse de que la fila sea visible
                self.main_window.task_table_widget.table_view.scrollTo(
                    self.main_window.task_table_widget.model.index(task_index, 0)
                )
                self.show_floating_menu(self.click_pos, task)
        # Restablecer la bandera
        self.double_click_occurred = False

    def mouseDoubleClickEvent(self, event):
        self.double_click_occurred = True
        if hasattr(self, 'single_click_timer'):
            self.single_click_timer.stop()

        x = int(event.position().x())
        y = int(event.position().y() + self.vertical_offset)
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

        with QPainter(self) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(event.rect(), self.background_color)

            painter.translate(0, -self.vertical_offset)

            for i, task in enumerate(self.tasks):
                y = i * self.row_height

                # Resaltar la fila si corresponde
                if i == self.highlighted_task_index:
                    highlight_color = QColor(200, 200, 255, 50)  # Color de resaltado
                    painter.fillRect(QRectF(0, y, self.width(), self.row_height), highlight_color)

                # Dibujar la barra de la tarea
                start = QDate.fromString(task.start_date, "dd/MM/yyyy")
                end = QDate.fromString(task.end_date, "dd/MM/yyyy")
                if end < self.min_date or start > self.max_date:
                    continue

                x = self.min_date.daysTo(start) * self.pixels_per_day
                width = start.daysTo(end) * self.pixels_per_day + self.pixels_per_day  # Incluye el día final
                bar_height = self.row_height * 0.9
                bar_y = y + (self.row_height - bar_height) / 2

                if task.is_subtask:
                    # Oscurecer el color para las subtareas
                    darker_color = task.parent_task.color.darker(120)  # Oscurecer el color en 20%
                    painter.setBrush(QBrush(darker_color))
                else:
                    painter.setBrush(QBrush(task.color))

                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(QRectF(x, bar_y, width, bar_height))

                # Agregar identificadores para subtareas
                if hasattr(task, 'is_subtask') and task.is_subtask:
                    painter.setPen(QPen(self.text_color))
                    painter.setFont(QFont("Arial", 12))
                    rect = QRectF(x, y, width, self.row_height)
                    painter.drawText(rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "↳")

            # Dibujar la línea del día de hoy
            today = QDate.currentDate()
            if self.min_date <= today <= self.max_date:
                today_x = self.min_date.daysTo(today) * self.pixels_per_day
                painter.setPen(QPen(self.today_line_color, 2))
                painter.drawLine(int(today_x), 0, int(today_x), self.height())

            # Si no hay tareas, mostrar mensaje de bienvenida (opcional)
            if not self.tasks:
                welcome_text = "Bienvenido a Baby Project Manager\nHaga clic en 'Agregar Nueva Tarea' para comenzar"
                painter.setPen(QPen(self.text_color))
                painter.setFont(QFont("Arial", 14))
                painter.drawText(event.rect(), Qt.AlignmentFlag.AlignCenter, welcome_text)

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
            y = position.y() + self.vertical_offset

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
        y = position.y() + self.vertical_offset
        task_index = int(y // self.row_height)
        if 0 <= task_index < len(self.tasks):
            return task_index
        return None

    def set_vertical_offset(self, offset):
        self.vertical_offset = offset
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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update()  # Asegura que el widget se redibuje cuando cambia de tamaño

class GanttWidget(QWidget):
    def __init__(self, tasks, row_height, main_window):
        super().__init__()
        self.main_window = main_window
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.header = GanttHeaderView()
        self.header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # Permitir expansión horizontal
        self.chart = GanttChart(tasks, row_height, self.header.header_height, main_window)
        self.chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)  # Permitir expansión horizontal y vertical
        self.chart.setMouseTracking(True)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_layout.addWidget(self.header)
        self.content_layout.addWidget(self.chart)

        self.layout.addWidget(self.content_widget)

        self.pixels_per_day = 0

        # Establecer la política de tamaño para permitir la expansión horizontal y vertical
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def update_parameters(self, min_date, max_date, pixels_per_day):
        self.min_date = min_date
        self.max_date = max_date
        self.pixels_per_day = pixels_per_day
        self.header.update_parameters(min_date, max_date, pixels_per_day)
        self.chart.update_parameters(min_date, max_date, pixels_per_day)
        self.content_widget.updateGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.min_date and self.max_date:
            days_total = self.min_date.daysTo(self.max_date) + 1
            available_width = self.width()
            self.pixels_per_day = max(0.1, available_width / days_total)
            self.update_parameters(self.min_date, self.max_date, self.pixels_per_day)

class FloatingTaskMenu(QWidget):
    notesChanged = Signal()

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.cal = Colombia()
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        name_label = QLabel(f"{self.task.name}")
        start_label = QLabel(f"Inicio: {self.task.start_date}")
        end_label = QLabel(f"Fin: {self.task.end_date}")

        days_left_label = QLabel(f"Días restantes: {self.calculate_working_days_left()}")

        for label in (name_label, start_label, end_label, days_left_label):
            label.setAlignment(Qt.AlignmentFlag.AlignRight)
            layout.addWidget(label)

        self.notes_edit = HyperlinkTextEdit(self)

        # Validación añadida
        if isinstance(self.task.notes_html, str):
            self.notes_edit.setHtml(self.task.notes_html)
        else:
            print(f"Error: notes_html debe ser una cadena, pero es {type(self.task.notes_html)}. Asignando cadena vacía.")
            self.notes_edit.setHtml("")

        self.notes_edit.file_links = self.task.file_links
        self.notes_edit.setMinimumHeight(100)
        layout.addWidget(self.notes_edit)

        self.setMinimumWidth(250)
        self.setMaximumWidth(400)
        self.setMaximumHeight(300)

        self.adjustSize()
        self.update_colors()

        self.notes_edit.textChanged.connect(self.update_task_notes)
        self.notes_edit.doubleClicked.connect(self.open_hyperlink)
        self.is_editing = False

        # Después de layout.addWidget(self.notes_edit), agregar:
        add_link_button = QPushButton("Agregar Hipervínculo")
        add_link_button.clicked.connect(self.open_file_dialog_for_link)
        layout.addWidget(add_link_button)

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
        if self.task.notes_html != self.notes_edit.toHtml():
            self.task.notes_html = self.notes_edit.toHtml()
            self.task.notes = self.notes_edit.toPlainText()
            self.task.file_links = self.notes_edit.file_links
            self.notesChanged.emit()
            self.is_editing = True

    def update_colors(self):
        palette = self.palette()
        self.background_color = palette.color(QPalette.ColorRole.Window)
        self.text_color = palette.color(QPalette.ColorRole.WindowText)
        self.update()  # Forzar repintado

    def paintEvent(self, event):
        with QPainter(self) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(event.rect(), self.background_color)
            painter.setBrush(self.background_color)
            painter.setPen(Qt.PenStyle.NoPen)
            path = QPainterPath()
            path.addRoundedRect(QRectF(self.rect()), 10, 10)
            painter.drawPath(path)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.PaletteChange:
            self.update_colors()
            for child in self.findChildren(QLabel):
                child.setPalette(self.palette())
            self.update()
        super().changeEvent(event)

    def sizeHint(self):
        return self.layout().sizeHint()

    def toggle_editing(self):
        self.is_editing = not self.is_editing

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def open_file_dialog_for_link(self):
        try:
            print("Abriendo diálogo de selección de archivo")
            options = QFileDialog.DontUseNativeDialog  # Usar diálogo Qt en lugar del nativo
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Seleccionar archivo",
                "",
                "Todos los archivos (*.*)",
                options=options
            )
            if file_path:
                print(f"Archivo seleccionado: {file_path}")
                # Convertir a ruta normalizada del sistema
                file_path = os.path.normpath(file_path)
                file_name = os.path.basename(file_path)
                self.notes_edit.file_links[file_name] = file_path
                self.notes_edit.insertHyperlink(file_name)
            else:
                print("No se seleccionó ningún archivo")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al seleccionar archivo: {str(e)}")
            print(f"Excepción en open_file_dialog_for_link: {e}")

    def open_hyperlink(self, line):
        try:
            file_path = self.notes_edit.file_links.get(line)
            if file_path and os.path.exists(file_path):
                file_path = os.path.normpath(file_path)  # Normalizar ruta
                if sys.platform.startswith('win32'):
                    os.startfile(file_path)  # Cambiado a file_path directamente
                elif sys.platform.startswith('darwin'):
                    subprocess.run(['open', file_path], check=True)
                else:
                    subprocess.run(['xdg-open', file_path], check=True)
            else:
                QMessageBox.warning(self, "Error", "No se pudo encontrar el archivo.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo abrir el archivo: {str(e)}")

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

        # Conectar la señal de cambio de selección
        self.table_view.selectionModel().selectionChanged.connect(self.on_selection_changed)

        # Habilitar la clasificación en la vista de tabla
        self.table_view.setSortingEnabled(True)

        # Configurar los delegados, pasando la referencia a MainWindow
        self.table_view.setItemDelegateForColumn(0, StateButtonDelegate(self.table_view, main_window=self.main_window))
        self.table_view.setItemDelegateForColumn(1, LineEditDelegate(self.table_view))
        self.table_view.setItemDelegateForColumn(2, DateEditDelegate(self.table_view))
        self.table_view.setItemDelegateForColumn(3, DateEditDelegate(self.table_view))
        self.table_view.setItemDelegateForColumn(4, SpinBoxDelegate(minimum=1, maximum=99999, parent=self.table_view))
        self.table_view.setItemDelegateForColumn(5, SpinBoxDelegate(minimum=0, maximum=100, parent=self.table_view))

        # Configurar los encabezados
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Columna Nombre
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        self.table_view.verticalHeader().setDefaultSectionSize(self.main_window.ROW_HEIGHT if self.main_window else 25)
        self.table_view.verticalHeader().setMinimumSectionSize(self.main_window.ROW_HEIGHT if self.main_window else 25)

        # Establecer anchos iniciales para las columnas
        self.table_view.setColumnWidth(1, 150)  # Columna 1: Nombre
        self.table_view.setColumnWidth(2, 100)  # Columna 2: Fecha inicial
        self.table_view.setColumnWidth(3, 100)  # Columna 3: Fecha final
        self.table_view.setColumnWidth(4, 70)   # Columna 4: Días
        self.table_view.setColumnWidth(5, 40)   # Columna 5: Dedicación

        # Botón de menú
        self.menu_button = QPushButton("☰", self)
        self.menu_button.clicked.connect(self.show_menu)
        QTimer.singleShot(0, self.adjust_button_size)

        self.current_file_path = None
        self.setup_table_style()
        self.setup_item_change_detection()

        # Ocultar el scrollbar vertical de la tabla
        self.table_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Ocultar la barra de desplazamiento horizontal
        self.table_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Establecer política de tamaño para permitir expansión horizontal
        self.table_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Agregar QShortcut para la tecla Escape
        escape_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self.table_view)
        escape_shortcut.activated.connect(self.clear_selection)

    # Definir el Método para Deseleccionar las Filas Seleccionadas
    def clear_selection(self):
        self.table_view.clearSelection()
        if self.main_window:
            self.main_window.update_gantt_highlight(None)  # Opcional: También deseleccionar en el Gantt

    def on_selection_changed(self, selected, deselected):
        if self.main_window:
            selected_rows = self.table_view.selectionModel().selectedRows()
            if selected_rows:
                # Obtener el índice de la tarea seleccionada en el modelo
                selected_index = selected_rows[0]
                task_index = selected_index.row()
                # Asegurarse de que el índice es válido y corresponde a la tarea correcta
                print(f"Selected task index: {task_index}")
                self.main_window.update_gantt_highlight(task_index)
            else:
                self.main_window.update_gantt_highlight(None)

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
        if Qt.ItemDataRole.EditRole in roles or Qt.ItemDataRole.DisplayRole in roles or Qt.ItemDataRole.UserRole in roles:
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

        add_task_action = menu.addAction("Agregar Nueva Tarea")
        add_task_action.triggered.connect(self.main_window.add_new_task)

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

        import_action = menu.addAction("Importar cronogramas")
        import_action.triggered.connect(lambda: self.show_file_gui())

        config_menu = menu.addMenu("Configuración")
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
            with open(file_path, 'w', encoding='utf-8') as file:
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
                    file.write(f"COLOR: {task.color.name()}\n")
                    file.write(f"COLLAPSED: {task.is_collapsed}\n")
                    file.write("NOTES_HTML_BEGIN\n")
                    file.write(task.notes_html)
                    file.write("\nNOTES_HTML_END\n")
                    file.write("FILE_LINKS_BEGIN\n")
                    file.write(repr(task.file_links))
                    file.write("\nFILE_LINKS_END\n")
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
            tasks_with_parents = []
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                tasks_data = content.split("[TASK]")
                for task_block in tasks_data:
                    if "[/TASK]" in task_block:
                        task_data = {}
                        lines = task_block.split("\n")
                        notes_html = ""
                        file_links_str = ""
                        reading_notes = False
                        reading_links = False
                        for line in lines:
                            line = line.strip()
                            if line.startswith("NAME:"):
                                task_data['NAME'] = line[5:].strip()
                            elif line.startswith("PARENT:"):
                                task_data['PARENT'] = line[7:].strip()
                            elif line.startswith("START:"):
                                task_data['START'] = line[6:].strip()
                            elif line.startswith("END:"):
                                task_data['END'] = line[4:].strip()
                            elif line.startswith("DURATION:"):
                                task_data['DURATION'] = line[9:].strip()
                            elif line.startswith("DEDICATION:"):
                                task_data['DEDICATION'] = line[11:].strip()
                            elif line.startswith("COLOR:"):
                                task_data['COLOR'] = line[6:].strip()
                            elif line.startswith("COLLAPSED:"):
                                task_data['COLLAPSED'] = line[10:].strip()
                            elif line == "NOTES_HTML_BEGIN":
                                reading_notes = True
                                notes_html = ""
                            elif line == "NOTES_HTML_END":
                                reading_notes = False
                                task_data['NOTES_HTML'] = notes_html
                            elif line == "FILE_LINKS_BEGIN":
                                if reading_notes:
                                    # Si 'NOTES_HTML_END' falta, cerramos la sección de notas aquí
                                    reading_notes = False
                                    task_data['NOTES_HTML'] = notes_html
                                reading_links = True
                                file_links_str = ""
                            elif line == "FILE_LINKS_END":
                                reading_links = False
                                task_data['FILE_LINKS'] = ast.literal_eval(file_links_str)
                            elif reading_notes:
                                notes_html += line + "\n"
                            elif reading_links:
                                file_links_str += line + "\n"
                        # Crear la instancia de Task
                        task = Task(
                            name=task_data.get('NAME', "Nueva Tarea"),
                            start_date=task_data.get('START', QDate.currentDate().toString("dd/MM/yyyy")),
                            end_date=task_data.get('END', QDate.currentDate().addDays(1).toString("dd/MM/yyyy")),
                            duration=task_data.get('DURATION', "1"),
                            dedication=task_data.get('DEDICATION', "40"),
                            color=QColor(task_data.get('COLOR', '#22a39f')) if 'COLOR' in task_data else QColor(34, 163, 159),
                            notes=task_data.get('NOTES', ""),
                            notes_html=task_data.get('NOTES_HTML', ""),
                            file_links=task_data.get('FILE_LINKS', {})
                        )
                        # Asegurarse de que 'NOTES_HTML' siempre sea una cadena
                        if not isinstance(task_data['NOTES_HTML'], str):
                            print(f"Advertencia: 'NOTES_HTML' para la tarea '{task_data.get('NAME', 'Unnamed')}' no es una cadena. Asignando cadena vacía.")
                            task_data['NOTES_HTML'] = ""

                        parent_name = task_data.get('PARENT', '').strip()
                        task.is_subtask = bool(parent_name)
                        task.is_collapsed = task_data.get('COLLAPSED', 'False') == 'True'
                        self.model.tasks.append(task)
                        tasks_with_parents.append((task, parent_name))
            # Establecer relaciones de padres
            name_to_task = {task.name: task for task in self.model.tasks}
            for task, parent_name in tasks_with_parents:
                if parent_name:
                    parent_task = name_to_task.get(parent_name)
                    if parent_task:
                        task.parent_task = parent_task
                        parent_task.subtasks.append(task)
                    else:
                        print(f"Tarea padre con nombre '{parent_name}' no encontrada para la tarea '{task.name}'")
            self.model.update_visible_tasks()
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
            name=task_data.get('NAME', "Nueva Tarea"),
            start_date=task_data.get('START', QDate.currentDate().toString("dd/MM/yyyy")),
            end_date=task_data.get('END', QDate.currentDate().addDays(1).toString("dd/MM/yyyy")),
            duration=task_data.get('DURATION', "1"),
            dedication=task_data.get('DEDICATION', "40"),
            color=QColor(task_data.get('COLOR', '#22a39f')),
            notes=task_data.get('NOTES', ""),
            notes_html=task_data.get('NOTES_HTML', ""),
            file_links=task_data.get('FILE_LINKS', {})
        )
        task.is_editing = editable  # Establecer is_editing según el parámetro editable
        task.is_collapsed = False  # Inicializar is_collapsed
        self.model.insertTask(task)
        self.model.update_visible_tasks()
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

    def update_state_buttons(self):
        # Emitir una señal para actualizar la vista sin cambiar los colores
        self.model.dataChanged.emit(
            self.model.index(0, 0),
            self.model.index(self.model.rowCount() - 1, self.model.columnCount() - 1),
            [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.DecorationRole, Qt.ItemDataRole.UserRole]
        )

    def show_file_gui(self, file_type=None):
        # Verificar si ya existe una ventana abierta
        for window in self.main_window.file_gui_windows:
            if not window.isHidden():
                window.raise_()
                window.activateWindow()
                return

        # Crear nueva ventana
        self.file_gui_window = FileGUIWindow()
        self.file_gui_window.tasks_imported.connect(self.import_tasks)
        self.main_window.file_gui_windows.append(self.file_gui_window)

        # Conectar señal de cierre para limpieza
        self.file_gui_window.destroyed.connect(
            lambda: self.main_window.file_gui_windows.remove(self.file_gui_window)
            if self.file_gui_window in self.main_window.file_gui_windows else None
        )

        self.file_gui_window.show()

    def import_tasks(self, tasks):
        for task_data in tasks:
            # Convertir el formato de fecha si es necesario
            start_date = self.convert_date_format(task_data.get('start_date'))
            end_date = self.convert_date_format(task_data.get('end_date'))
            # Usar el color proporcionado en los datos de la tarea
            color = task_data.get('color', QColor(34, 163, 159).name())

            # Obtener el nombre de la tarea directamente de task_data
            task_name = task_data.get('name', '').lstrip()  # Usar get para evitar KeyError

            new_task = {
                'NAME': task_name,
                'START': self.convert_date_format(task_data.get('start_date', '')),
                'END': self.convert_date_format(task_data.get('end_date', '')),
                'DURATION': self.calculate_duration(
                    self.convert_date_format(task_data.get('start_date', '')),
                    self.convert_date_format(task_data.get('end_date', ''))
                ),
                'DEDICATION': "40",  # valor por defecto
                'COLOR': color,
                'NOTES': ""
            }
            self.add_task_to_table(new_task)

            # Actualizar el Gantt después de agregar cada tarea
            if self.main_window:
                self.main_window.update_gantt_chart()

    def convert_date_format(self, date_str):
        """Convierte el formato de fecha del archivo importado al formato usado en Baby."""
        if not date_str or date_str == "N/A":
            return QDate.currentDate().toString("dd/MM/yyyy")
        try:
            # Intentar diferentes formatos de fecha comunes
            formats = [
                "%Y-%m-%d",      # 2023-12-31
                "%d/%m/%Y",      # 31/12/2023
                "%d-%m-%Y",      # 31-12-2023
                "%Y/%m/%d",      # 2023/12/31
                "%m/%d/%Y",      # 12/31/2023
                "%d.%m.%Y",      # 31.12.2023
                "%Y.%m.%d",      # 2023.12.31
                "%d %b %Y",      # 31 Dec 2023
                "%d %B %Y",      # 31 December 2023
                "%Y%m%d"         # 20231231
            ]

            for fmt in formats:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime("%d/%m/%Y")
                except ValueError:
                    continue

            # Si ningún formato coincide
            return QDate.currentDate().toString("dd/MM/yyyy")
        except Exception as e:
            print(f"Error al convertir fecha '{date_str}': {e}")
            return QDate.currentDate().toString("dd/MM/yyyy")

    def calculate_duration(self, start_date, end_date):
        """Calcula la duración en días laborables entre dos fechas."""
        try:
            start = datetime.strptime(start_date, "%d/%m/%Y")
            end = datetime.strptime(end_date, "%d/%m/%Y")

            cal = Colombia()
            business_days = 0
            current_date = start
            while current_date <= end:
                if cal.is_working_day(current_date.date()):
                    business_days += 1
                current_date += timedelta(days=1)

            return str(business_days)
        except Exception as e:
               print(f"Error al calcular duración: {e}")
               return "1"

class MainWindow(QMainWindow):
    ROW_HEIGHT = 25

    def __init__(self):
        super().__init__()
        self.unsaved_changes = False
        self.base_title = "Baby project manager"
        self.setWindowTitle(self.base_title)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMinMaxButtonsHint)
        self.setMinimumSize(800, 600)  # Tamaño mínimo
        self.setGeometry(100, 100, 1200, 800)
        self.tasks = []
        self.current_file_path = None
        self.selected_period = 365  # 1 año en días
        self.setMouseTracking(True)
        self.wheel_accumulator = 0
        self.wheel_threshold = 100  # Ajusta este valor
        self.current_view = "complete"  # Vista por defecto
        self.file_gui_windows = []

        # Crear un widget central con QGridLayout
        main_widget = QWidget()
        main_layout = QGridLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Configurar factores de estiramiento
        main_layout.setColumnStretch(0, 0)  # Columna 0: TaskTableWidget (fijo)
        main_layout.setColumnStretch(1, 1)  # Columna 1: GanttWidget (expansible)
        main_layout.setColumnStretch(2, 0)  # Columna 2: Scrollbar (fijo)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Crear el widget izquierdo (tabla de tareas)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.task_table_widget = TaskTableWidget(self)
        left_layout.addWidget(self.task_table_widget)
        self.table_view = self.task_table_widget.table_view
        self.model = self.task_table_widget.model

        # Conectar la señal layoutChanged del modelo con update_gantt_chart
        self.model.layoutChanged.connect(self.on_model_layout_changed)

        left_widget.setFixedWidth(600)  # Tamaño fijo para la tabla de tareas
        self.task_table_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Crear el widget derecho (gráfico de Gantt)
        self.gantt_widget = GanttWidget(self.tasks, self.ROW_HEIGHT, self)
        self.gantt_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.gantt_header = self.gantt_widget.header
        self.gantt_chart = self.gantt_widget.chart
        self.gantt_chart.main_window = self

        # Conectar la señal colorChanged
        self.gantt_chart.colorChanged.connect(self.update_task_color)

        # Crear un scrollbar vertical compartido
        self.shared_scrollbar = QScrollBar(Qt.Orientation.Vertical)
        self.shared_scrollbar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.shared_scrollbar.setFixedWidth(20)  # Ancho fijo para evitar cambios de tamaño
        self.shared_scrollbar.valueChanged.connect(self.sync_scroll)

        # Añadir widgets al layout en una cuadrícula
        main_layout.addWidget(left_widget, 0, 0)
        main_layout.addWidget(self.gantt_widget, 0, 1)
        main_layout.addWidget(self.shared_scrollbar, 0, 2)

        # Ocultar los scrollbars individuales
        self.table_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.gantt_chart.set_vertical_offset(0)

        # Conectar la barra de desplazamiento de la tabla para sincronizar
        self.table_view.verticalScrollBar().valueChanged.connect(self.on_table_scroll)

        self.adjust_all_row_heights()

        self.update_gantt_chart()

        from PySide6.QtGui import QKeySequence, QShortcut

        # Atajo de teclado para guardar
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.quick_save)

        self.set_unsaved_changes(False)

        # Inicializar el scrollbar compartido
        QTimer.singleShot(0, self.initialize_shared_scrollbar)

    def initialize_shared_scrollbar(self):
        self.update_shared_scrollbar_range()

    def update_shared_scrollbar_range(self):
        total_tasks = self.model.rowCount()
        visible_tasks = self.calculate_visible_tasks()

        # Evitar que el valor máximo sea negativo
        max_scroll = max(total_tasks - visible_tasks, 0)

        self.shared_scrollbar.setRange(0, max_scroll)
        self.shared_scrollbar.setPageStep(visible_tasks)

        # Habilitar o deshabilitar el scrollbar basado en si es necesario
        if total_tasks > visible_tasks:
            self.shared_scrollbar.setEnabled(True)
        else:
            self.shared_scrollbar.setEnabled(False)
            self.shared_scrollbar.setValue(0)  # Asegurar que esté en la posición inicial
            self.gantt_chart.set_vertical_offset(0)  # Resetear el desplazamiento del Gantt

    def calculate_visible_tasks(self):
        # Calcula cuántas filas son visibles en la tabla y el gráfico de Gantt
        visible_height = self.table_view.viewport().height()
        row_height = self.ROW_HEIGHT
        return math.ceil(visible_height / row_height)

    def sync_scroll(self, value):
        # Desplazar la tabla
        self.table_view.verticalScrollBar().setValue(value)
        # Desplazar el gráfico de Gantt
        self.gantt_chart.set_vertical_offset(value * self.ROW_HEIGHT)

    def on_table_scroll(self, value):
        # Sincronizar el scrollbar compartido con la tabla
        self.shared_scrollbar.setValue(value)

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
            # Obtener la tarea a eliminar desde visible_tasks
            task = self.model.getTask(row)

            if task:
                # Obtener el índice real de la tarea en self.model.tasks
                actual_row = self.model.visible_to_actual[row]

                # Si es una subtarea, eliminarla y actualizar la lista de subtareas del padre
                if task.is_subtask and task.parent_task:
                    self.model.tasks.pop(actual_row)
                    task.parent_task.subtasks.remove(task)
                # Si es una tarea padre, eliminarla junto con sus subtareas
                elif not task.is_subtask:
                    # Calcular cuántas subtareas tiene
                    total_subtasks = self.count_subtasks(actual_row)
                    # Eliminar la tarea padre y sus subtareas de self.model.tasks
                    for _ in range(total_subtasks + 1):
                        self.model.tasks.pop(actual_row)
                # Actualizar las tareas visibles
                self.model.update_visible_tasks()
                # Emitir señal de cambio de layout
                self.model.layoutChanged.emit()

                # Actualizar la estructura de datos
                self.update_task_structure()

                # Actualizar los botones de estado sin restablecer colores
                self.task_table_widget.update_state_buttons()

                self.set_unsaved_changes(True)
                self.update_gantt_chart()
                self.update_shared_scrollbar_range()  # Actualizar el rango del scrollbar

                # Nuevo código para actualizar la selección
                if self.model.rowCount() > 0:
                    # Si es posible, seleccionar la tarea en la misma posición
                    new_row = min(row, self.model.rowCount() - 1)
                    self.table_view.selectRow(new_row)
                    self.table_view.scrollTo(self.model.index(new_row, 0))
                else:
                    # Si no hay más tareas, limpiar la selección y el resaltado
                    self.table_view.clearSelection()
                    self.update_gantt_highlight(None)

    def update_task_structure(self):
        # Reconstruir la estructura de tareas
        self.tasks = []
        current_parent = None

        for task in self.model.tasks:
            if task:
                if not task.is_subtask:
                    current_parent = task
                    current_parent.subtasks = []
                    self.tasks.append(current_parent)
                else:
                    if current_parent:
                        current_parent.subtasks.append(task)
                        task.parent_task = current_parent

        # Actualizar los botones de estado sin restablecer colores
        self.task_table_widget.update_state_buttons()

    def count_subtasks(self, actual_row):
        count = 0
        for i in range(actual_row + 1, len(self.model.tasks)):
            task = self.model.tasks[i]
            if task.is_subtask:
                count += 1
            else:
                break
        return count

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
        self.update_shared_scrollbar_range()  # Actualizar el rango del scrollbar
        if self.model.rowCount() > 0:
            self.set_unsaved_changes(True)

        # Obtener el índice de la nueva tarea
        new_task_row = self.model.rowCount() - 1

        # Establecer el foco en la nueva tarea y activar la edición en el campo "Nombre"
        self.table_view.selectRow(new_task_row)
        self.table_view.scrollTo(self.model.index(new_task_row, 0))
        self.table_view.edit(self.model.index(new_task_row, 1))  # Columna "Nombre"

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
        model = self.model
        if row >= 0 and row < model.rowCount():
            # Convertir índice visible a índice real
            actual_row = model.visible_to_actual[row]
            if actual_row < len(model.tasks):
                task = model.tasks[actual_row]
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
                        name=task_data.get('NAME'),
                        start_date=task_data.get('START'),
                        end_date=task_data.get('END'),
                        duration=task_data.get('DURATION'),
                        dedication=task_data.get('DEDICATION'),
                        color=QColor(task_data.get('COLOR')),
                        notes=task_data.get('NOTES', ''),
                        notes_html="",  # Si es necesario, ajustar este valor
                        file_links={}   # Si es necesario, ajustar este valor
                    )
                    duplicated_task.is_subtask = task.is_subtask
                    duplicated_task.parent_task = task.parent_task
                    duplicated_task.is_editing = False
                    duplicated_task.is_collapsed = False

                    if task.is_subtask:
                        # Si es una subtarea, insertar justo después de la tarea original
                        actual_insert_index = actual_row + 1
                        model.insertTask(duplicated_task, actual_insert_index)
                        if duplicated_task.parent_task:
                            duplicated_task.parent_task.subtasks.append(duplicated_task)
                    else:
                        # Si es una tarea principal, insertar después de todas sus subtareas
                        current_block_size = self.count_subtasks(actual_row) + 1
                        actual_insert_index = actual_row + current_block_size
                        model.insertTask(duplicated_task, actual_insert_index)
                        if task.subtasks:
                            duplicated_task.subtasks = []
                            subtask_insert_index = actual_insert_index + 1
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
                                    name=subtask_data.get('NAME'),
                                    start_date=subtask_data.get('START'),
                                    end_date=subtask_data.get('END'),
                                    duration=subtask_data.get('DURATION'),
                                    dedication=subtask_data.get('DEDICATION'),
                                    color=QColor(subtask_data.get('COLOR')),
                                    notes=subtask_data.get('NOTES', ''),
                                    notes_html="",  # Si es necesario, ajustar este valor
                                    file_links={}   # Si es necesario, ajustar este valor
                                )
                                duplicated_subtask.is_subtask = True
                                duplicated_subtask.parent_task = duplicated_task
                                duplicated_subtask.is_editing = False
                                duplicated_subtask.is_collapsed = False

                                duplicated_task.subtasks.append(duplicated_subtask)
                                model.insertTask(duplicated_subtask, subtask_insert_index)
                                subtask_insert_index += 1

                    # Actualizar las tareas visibles
                    model.update_visible_tasks()
                    # Emitir señal de cambio de layout
                    model.layoutChanged.emit()
                    # Actualizar la interfaz
                    self.update_gantt_chart()
                    self.update_shared_scrollbar_range()
                    self.set_unsaved_changes(True)

                    # Calcular el nuevo índice visible de la tarea duplicada
                    new_visible_row = model.actual_to_visible.get(actual_insert_index, None)
                    if new_visible_row is not None and new_visible_row < model.rowCount():
                        # Establecer el foco en la tarea duplicada y activar edición en "Nombre"
                        self.table_view.selectRow(new_visible_row)
                        self.table_view.scrollTo(model.index(new_visible_row, 0))
                        self.table_view.edit(model.index(new_visible_row, 1))  # Columna "Nombre"
                    else:
                        # Si la tarea duplicada está oculta, expandir el padre
                        duplicated_task.is_collapsed = False
                        model.update_visible_tasks()
                        model.layoutChanged.emit()
                        new_visible_row = model.actual_to_visible.get(actual_insert_index, None)
                        if new_visible_row is not None and new_visible_row < model.rowCount():
                            self.table_view.selectRow(new_visible_row)
                            self.table_view.scrollTo(model.index(new_visible_row, 0))
                            self.table_view.edit(model.index(new_visible_row, 1))

    def insert_task(self, row):
        model = self.model
        if row < len(model.visible_to_actual):
            # Convertir índice visible a índice real
            actual_row = model.visible_to_actual[row]
            task = model.tasks[actual_row]
            if task:
                if task.is_subtask:
                    # Si la tarea es una subtarea, encontrar la tarea padre y su posición
                    parent_task = task.parent_task
                    parent_actual_index = actual_row
                    while parent_actual_index >= 0:
                        if model.tasks[parent_actual_index] == parent_task:
                            break
                        parent_actual_index -= 1
                    # Insertar después de todas las subtareas del padre
                    actual_insert_index = parent_actual_index + self.count_subtasks(parent_actual_index) + 1
                elif task.subtasks:
                    # Si la tarea es una tarea padre con subtareas, insertar después de sus subtareas
                    actual_insert_index = actual_row + self.count_subtasks(actual_row) + 1
                else:
                    # Si es una tarea individual sin subtareas, insertar en actual_row + 1
                    actual_insert_index = actual_row + 1
            else:
                # Si no hay tarea, insertar al final
                actual_insert_index = len(model.tasks)
        else:
            # Si el índice de fila está fuera de los límites, insertar al final
            actual_insert_index = len(model.tasks)

        # Crear una nueva tarea
        task_data = {
            'NAME': "Nueva Tarea",
            'START': QDate.currentDate().toString("dd/MM/yyyy"),
            'END': QDate.currentDate().toString("dd/MM/yyyy"),
            'DURATION': "1",
            'DEDICATION': "40",
            'COLOR': QColor(34, 163, 159).name(),
            'NOTES': ""
        }
        new_task = Task(
            name=task_data.get('NAME'),
            start_date=task_data.get('START'),
            end_date=task_data.get('END'),
            duration=task_data.get('DURATION'),
            dedication=task_data.get('DEDICATION'),
            color=QColor(task_data.get('COLOR')),
            notes=task_data.get('NOTES', '')
        )
        new_task.is_editing = False
        new_task.is_collapsed = False

        # Insertar la nueva tarea
        model.insertTask(new_task, actual_insert_index)
        model.update_visible_tasks()
        self.update_gantt_chart()
        self.update_shared_scrollbar_range()
        self.set_unsaved_changes(True)

        # Seleccionar la nueva tarea
        visible_index = model.actual_to_visible.get(actual_insert_index)
        if visible_index is not None and visible_index < model.rowCount():
            self.table_view.selectRow(visible_index)
            self.table_view.scrollTo(model.index(visible_index, 0))
            self.table_view.edit(model.index(visible_index, 1))  # Columna "Nombre"

    def move_task_up(self, row):
        model = self.model
        if row > 0:
            # Asegurarse de que el índice visible es válido
            if row < len(model.visible_to_actual):
                # Convertir índice visible a índice real
                actual_row = model.visible_to_actual[row]
                if actual_row > 0 and actual_row < len(model.tasks):
                    task = model.tasks[actual_row]
                    if task and not task.is_subtask:
                        # Obtener el tamaño del bloque anterior
                        prev_actual_row = actual_row - 1
                        while prev_actual_row >= 0 and model.tasks[prev_actual_row].is_subtask:
                            prev_actual_row -= 1
                        if prev_actual_row >= 0:
                            prev_block_size = self.count_subtasks(prev_actual_row) + 1
                            # Definir los índices de inicio y fin de los bloques
                            start1 = prev_actual_row
                            end1 = prev_actual_row + prev_block_size
                            start2 = actual_row
                            end2 = actual_row + self.count_subtasks(actual_row) + 1
                            # Intercambiar los bloques
                            model.tasks[start1:end2] = model.tasks[start2:end2] + model.tasks[start1:end1]
                            # Actualizar las tareas visibles
                            model.update_visible_tasks()
                            model.layoutChanged.emit()
                            self.update_gantt_chart()
                            self.set_unsaved_changes(True)
                            # Calcular el nuevo índice visible
                            new_visible_row = model.actual_to_visible.get(start1, row - prev_block_size)
                            # Establecer el foco en la tarea padre en la nueva posición
                            if new_visible_row < model.rowCount():
                                self.table_view.selectRow(new_visible_row)
                                self.table_view.scrollTo(model.index(new_visible_row, 0))
                    else:
                        # Manejar el caso de mover una subtarea hacia arriba
                        if task and task.is_subtask and actual_row > 0:
                            above_task = model.tasks[actual_row - 1]
                            if above_task.is_subtask and above_task.parent_task == task.parent_task:
                                # Intercambiar las subtareas
                                model.tasks[actual_row], model.tasks[actual_row - 1] = model.tasks[actual_row - 1], model.tasks[actual_row]
                                # Actualizar las tareas visibles
                                model.update_visible_tasks()
                                model.dataChanged.emit(
                                    model.index(row - 1, 0),
                                    model.index(row, model.columnCount() - 1),
                                    [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.BackgroundRole]
                                )
                                self.update_gantt_chart()
                                self.set_unsaved_changes(True)
                                # Establecer el foco en la subtarea movida
                                new_visible_row = model.actual_to_visible.get(actual_row - 1, row - 1)
                                self.table_view.selectRow(new_visible_row)
                                self.table_view.scrollTo(model.index(new_visible_row, 0))
                else:
                    print(f"Actual row {actual_row} está fuera de rango.")
            else:
                print(f"Visible row {row} está fuera de rango.")
        else:
            # Si ya está en la primera posición, no hacer nada
            pass

    def move_task_down(self, row):
        model = self.model
        if row < model.rowCount() - 1:
            # Asegurarse de que el índice visible es válido
            if row < len(model.visible_to_actual):
                # Convertir índice visible a índice real
                actual_row = model.visible_to_actual[row]
                if actual_row < len(model.tasks):
                    task = model.tasks[actual_row]
                    if task and not task.is_subtask:
                        current_block_size = self.count_subtasks(actual_row) + 1
                        next_actual_row = actual_row + current_block_size
                        if next_actual_row < len(model.tasks):
                            next_block_size = self.count_subtasks(next_actual_row) + 1
                            # Intercambiar los bloques
                            model.tasks[actual_row:next_actual_row + next_block_size] = \
                                model.tasks[next_actual_row:next_actual_row + next_block_size] + \
                                model.tasks[actual_row:next_actual_row]
                            # Actualizar las tareas visibles
                            model.update_visible_tasks()
                            model.layoutChanged.emit()
                            self.update_gantt_chart()
                            self.set_unsaved_changes(True)
                            # Recalcular el índice actual de la tarea movida
                            new_actual_row = model.tasks.index(task)
                            new_visible_row = model.actual_to_visible.get(new_actual_row, row)
                            # Establecer el foco en la tarea movida
                            if new_visible_row < model.rowCount():
                                self.table_view.selectRow(new_visible_row)
                                self.table_view.scrollTo(model.index(new_visible_row, 0))
                    else:
                        # Manejar el caso de mover una subtarea hacia abajo
                        if task and task.is_subtask:
                            if actual_row + 1 < len(model.tasks):
                                below_task = model.tasks[actual_row + 1]
                                if below_task.is_subtask and below_task.parent_task == task.parent_task:
                                    model.tasks[actual_row], model.tasks[actual_row + 1] = model.tasks[actual_row + 1], model.tasks[actual_row]
                                    model.update_visible_tasks()
                                    model.dataChanged.emit(
                                        model.index(row, 0),
                                        model.index(row + 1, model.columnCount() - 1),
                                        [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.BackgroundRole]
                                    )
                                    self.update_gantt_chart()
                                    self.set_unsaved_changes(True)
                                    new_actual_row = actual_row + 1
                                    new_visible_row = model.actual_to_visible.get(new_actual_row, row + 1)
                                    self.table_view.selectRow(new_visible_row)
                                    self.table_view.scrollTo(model.index(new_visible_row, 0))
                else:
                    print(f"Actual row {actual_row} está fuera de rango.")
            else:
                print(f"Visible row {row} está fuera de rango.")
        else:
            # Si ya está en la última posición, no hacer nada
            pass

    def reset_task_color(self, task_index):
        if 0 <= task_index < len(self.tasks):
            task = self.tasks[task_index]
            if task:
                default_color = QColor(34, 163, 159)  # Color por defecto
                task.color = default_color
                task.is_editing = False  # Restablecer is_editing al cambiar el color

                # Encontrar el índice real de la tarea en self.model.tasks
                actual_row = self.model.tasks.index(task)

                # Encontrar el índice visible de la tarea en la tabla
                visible_row = self.model.actual_to_visible.get(actual_row)
                if visible_row is not None:
                    index = self.model.index(visible_row, 1)
                    self.model.dataChanged.emit(index, index, [Qt.ItemDataRole.BackgroundRole])

                # Si la tarea tiene subtareas, restablecer sus colores también
                if not task.is_subtask and task.subtasks:
                    for subtask in task.subtasks:
                        subtask.color = default_color
                        subtask_actual_row = self.model.tasks.index(subtask)
                        subtask_visible_row = self.model.actual_to_visible.get(subtask_actual_row)
                        if subtask_visible_row is not None:
                            index = self.model.index(subtask_visible_row, 1)
                            self.model.dataChanged.emit(index, index, [Qt.ItemDataRole.BackgroundRole])

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
                self.tasks.append(task)
        # Imprimir la lista de tareas para depuración
        print("Updated self.tasks:")
        for idx, task in enumerate(self.tasks):
            print(f"Index {idx}: Task Name: {task.name}")
        # Actualizar las tareas en el diagrama de Gantt
        self.gantt_chart.tasks = self.tasks

        today = QDate.currentDate()

        if self.tasks:
            min_date = min((QDate.fromString(task.start_date, "dd/MM/yyyy") for task in self.tasks), default=today)
            max_date = max((QDate.fromString(task.end_date, "dd/MM/yyyy") for task in self.tasks), default=today.addDays(30))
        else:
            min_date = today
            max_date = today.addDays(30)  # Mostrar un mes por defecto si no hay tareas

        # Lógica para ajustar min_date y max_date según la vista actual
        if self.current_view == "one_month":
            min_date = today.addDays(-7)  # Una semana antes de hoy
            max_date = min_date.addMonths(1)
        elif self.current_view == "three_month":
            min_date = today.addDays(-int(today.daysTo(today.addMonths(3)) * 0.125))
            max_date = min_date.addMonths(3)
        elif self.current_view == "six_month":
            min_date = today.addDays(-int(today.daysTo(today.addMonths(6)) * 0.125))
            max_date = min_date.addMonths(6)
        elif self.current_view == "year":
            min_date = today.addDays(-int(today.daysTo(today.addYears(1)) * 0.125))
            max_date = min_date.addYears(1)
        else:
            # Vista completa: ajustar min_date y max_date según las tareas
            pass

        # Asegúrate de que haya al menos un día de diferencia
        if min_date == max_date:
            max_date = min_date.addDays(1)

        days_total = min_date.daysTo(max_date) + 1
        available_width = self.gantt_widget.width() - self.shared_scrollbar.width()
        pixels_per_day = max(0.1, available_width / days_total)

        self.gantt_widget.update_parameters(min_date, max_date, pixels_per_day)
        self.gantt_chart.setMinimumHeight(max(len(self.tasks) * self.ROW_HEIGHT, self.gantt_widget.height()))
        self.gantt_chart.update()
        self.gantt_header.update()

        # Forzar la actualización del diseño
        self.gantt_widget.updateGeometry()

        if set_unsaved and self.tasks:
            self.set_unsaved_changes(True)

        self.update_shared_scrollbar_range()  # Actualizar el rango del scrollbar

    def update_task_color(self, task_index, color):
        if 0 <= task_index < len(self.tasks):
            task = self.tasks[task_index]
            if task:
                task.color = color  # Actualizar el color en el objeto Task
                task.is_editing = False  # Restablecer is_editing al cambiar el color

                # Encontrar el índice real de la tarea en self.model.tasks
                actual_row = self.model.tasks.index(task)

                # Encontrar el índice visible de la tarea en la tabla
                visible_row = self.model.actual_to_visible.get(actual_row)
                if visible_row is not None:
                    index = self.model.index(visible_row, 1)
                    self.model.dataChanged.emit(index, index, [Qt.ItemDataRole.BackgroundRole])

                # Si la tarea tiene subtareas, actualizar sus colores también
                if not task.is_subtask and task.subtasks:
                    for subtask in task.subtasks:
                        subtask.color = color
                        subtask_actual_row = self.model.tasks.index(subtask)
                        subtask_visible_row = self.model.actual_to_visible.get(subtask_actual_row)
                        if subtask_visible_row is not None:
                            index = self.model.index(subtask_visible_row, 1)
                            self.model.dataChanged.emit(index, index, [Qt.ItemDataRole.BackgroundRole])

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
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            if reply == QMessageBox.StandardButton.Save:
                if self.task_table_widget.save_file():
                    self.cleanup_and_exit(event)
                else:
                    # Si el guardado falla, pregunta al usuario si desea salir sin guardar
                    secondary_reply = QMessageBox.question(
                        self, 'Error al guardar',
                        'No se pudieron guardar los cambios. ¿Desea salir sin guardar?',
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    if secondary_reply == QMessageBox.StandardButton.Yes:
                        self.cleanup_and_exit(event)
                    else:
                        event.ignore()
            elif reply == QMessageBox.StandardButton.Discard:
                self.cleanup_and_exit(event)
            else:
                event.ignore()
        else:
            self.cleanup_and_exit(event)

    def cleanup_and_exit(self, event):
            # Cerrar todas las ventanas de FileGUI abiertas
            for window in self.file_gui_windows:
                window.close()

            # Cerrar la JVM al final
            try:
                from jvm_manager import JVMManager
                if JVMManager.is_jvm_started():
                    JVMManager.shutdown()
            except Exception as e:
                print(f"Error al cerrar la JVM: {e}")

            event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_gantt_chart(set_unsaved=False)
        self.task_table_widget.adjust_button_size()
        self.update_shared_scrollbar_range()
        # Eliminar la fijación de ancho para permitir el redimensionamiento dinámico
        # gantt_width = self.width() - self.task_table_widget.width() - self.shared_scrollbar.width()
        # self.gantt_widget.setFixedWidth(max(0, gantt_width))

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self.initial_layout_adjustment)

    def initial_layout_adjustment(self):
        self.update_gantt_chart(set_unsaved=False)

    def check_unsaved_changes(self):
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self,
                'Cambios sin guardar',
                '¿Desea guardar los cambios antes de continuar?',
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            if reply == QMessageBox.StandardButton.Save:
                return self.task_table_widget.save_file()
            elif reply == QMessageBox.StandardButton.Cancel:
                return False
        return True

    def quick_save(self):
        if self.task_table_widget.save_file():
            self.set_unsaved_changes(False)

    def print_task_table_contents(self):
        print("Task Table Contents:")
        for task in self.model.tasks:
            print(f"Task: Name={task.name}, Task={task}")

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
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
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
        model = self.model
        if parent_task_index < len(model.visible_to_actual):
            # Convertir índice visible a índice real
            actual_parent_index = model.visible_to_actual[parent_task_index]
            if actual_parent_index < len(model.tasks):
                parent_task = model.tasks[actual_parent_index]
                if parent_task:
                    # Crear una nueva subtarea
                    subtask = Task(
                        f"Subtarea de {parent_task.name}",
                        parent_task.start_date,
                        parent_task.end_date,
                        parent_task.duration,
                        parent_task.dedication,
                        parent_task.color,
                        ""
                    )
                    subtask.is_subtask = True
                    subtask.parent_task = parent_task
                    subtask.is_editing = False
                    subtask.is_collapsed = False

                    # Si la tarea padre está contraída, expandirla
                    if parent_task.is_collapsed:
                        parent_task.is_collapsed = False

                    # Calcular el índice de inserción real
                    insert_index = actual_parent_index + 1
                    while insert_index < len(model.tasks) and model.tasks[insert_index].is_subtask:
                        insert_index += 1

                    self.model.insertTask(subtask, insert_index)
                    parent_task.subtasks.append(subtask)

                    # Actualizar las tareas visibles y emitir señal de cambio de layout
                    self.model.update_visible_tasks()
                    self.model.layoutChanged.emit()

                    self.update_gantt_chart()
                    self.update_shared_scrollbar_range()
                    self.set_unsaved_changes(True)

                    # Después de insertar, seleccionar la subtarea agregada
                    # Necesitamos recalcular el índice visible
                    new_actual_row = model.tasks.index(subtask)
                    visible_index = model.actual_to_visible.get(new_actual_row)
                    if visible_index is not None and visible_index < model.rowCount():
                        self.table_view.selectRow(visible_index)
                        self.table_view.scrollTo(model.index(visible_index, 0))
                        self.table_view.edit(model.index(visible_index, 1))  # Columna "Nombre"
            else:
                print(f"Actual parent row {actual_parent_index} está fuera de rango.")
        else:
            print(f"Parent visible row {parent_task_index} está fuera de rango.")

    # Método para manejar cambios en el modelo
    def on_model_layout_changed(self):
        self.update_gantt_chart()
        self.set_unsaved_changes(True)

    def update_gantt_highlight(self, task_index):
        print(f"update_gantt_highlight called with task_index: {task_index}")
        if task_index is not None and 0 <= task_index < len(self.tasks):
            print(f"Highlighting task: {self.tasks[task_index].name}")
        else:
            print("No task to highlight")
        self.gantt_chart.highlighted_task_index = task_index
        self.gantt_chart.update()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Usar el estilo Fusion que soporta temas oscuros/claros
    # Aplicar la paleta del sistema
    app.setPalette(app.style().standardPalette())

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
