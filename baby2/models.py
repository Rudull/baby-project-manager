from datetime import datetime, timedelta
from PySide6.QtCore import Qt, QAbstractTableModel, QDate, QModelIndex
from PySide6.QtGui import QColor
from workalendar.america import Colombia

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

    def has_subtasks(self):
        """Verifica si la tarea tiene subtareas."""
        return bool(self.subtasks)

    def toggle_editing(self):
        """Alterna el estado de edición de la tarea."""
        self.is_editing = not self.is_editing

    def set_editing(self, value):
        """Establece el estado de edición de la tarea."""
        self.is_editing = value

    def toggle_collapsed(self):
        """Alterna el estado de colapso de la tarea."""
        self.is_collapsed = not self.is_collapsed

    def update_subtasks(self):
        """Actualiza las relaciones de las subtareas."""
        if self.parent_task:
            self.parent_task.subtasks = [task for task in self.parent_task.subtasks if task != self]
        for subtask in self.subtasks:
            subtask.parent_task = self

class TaskTableModel(QAbstractTableModel):
    def __init__(self, tasks=None):
        super().__init__()
        self.headers = ["", "Nombre", "Fecha inicial", "Fecha final", "Días", "%"]
        self.tasks = tasks or []
        self.visible_tasks = []
        self.visible_to_actual = []
        self.actual_to_visible = {}
        self.cal = Colombia()
        self.update_visible_tasks()

    def update_visible_tasks(self):
        """Actualiza las listas de tareas visibles y sus mapeos."""
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
        """Retorna el número de filas en el modelo."""
        return len(self.visible_tasks)

    def columnCount(self, parent=QModelIndex()):
        """Retorna el número de columnas en el modelo."""
        return len(self.headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """Retorna los datos para el índice y rol especificados."""
        if not index.isValid():
            return None

        task = self.visible_tasks[index.row()]
        column = index.column()

        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            return self._get_display_data(task, column)
        elif role == Qt.ItemDataRole.UserRole:
            return task
        elif role == Qt.ItemDataRole.BackgroundRole:
            if column == 1:
                return task.color
        return None

    def _get_display_data(self, task, column):
        """Obtiene los datos de visualización para una tarea y columna específicas."""
        if column == 0:
            return ""
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

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """Retorna los datos del encabezado."""
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]
        return None

    def flags(self, index):
        """Retorna los flags para el índice especificado."""
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled
        flags = super().flags(index)
        if index.column() in [1, 2, 3, 4, 5]:
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def insertTask(self, task, actual_position=None):
        """Inserta una nueva tarea en la posición especificada."""
        if actual_position is not None:
            position = self.actual_to_visible.get(actual_position, self.rowCount())
        else:
            actual_position = len(self.tasks)
            position = self.rowCount()
            
        self.beginInsertRows(QModelIndex(), position, position)
        self.tasks.insert(actual_position, task)
        self.update_visible_tasks()
        self.endInsertRows()

    def removeTask(self, position):
        """Elimina una tarea de la posición especificada."""
        if 0 <= position < self.rowCount():
            actual_position = self.visible_to_actual[position]
            self.beginRemoveRows(QModelIndex(), position, position)
            del self.tasks[actual_position]
            self.update_visible_tasks()
            self.endRemoveRows()
            return True
        return False

    def getTask(self, row):
        """Obtiene una tarea específica por su índice de fila."""
        if 0 <= row < self.rowCount():
            return self.visible_tasks[row]
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        """Establece los datos para el índice y rol especificados."""
        if not index.isValid():
            return False

        task = self.visible_tasks[index.row()]
        column = index.column()

        if role == Qt.ItemDataRole.EditRole:
            return self._set_edit_data(task, column, value, index)
        return False

    def _set_edit_data(self, task, column, value, index):
        """Establece los datos de edición para una tarea y columna específicas."""
        if column == 1:
            task.name = str(value)
        elif column == 2:
            task.start_date = str(value)
            self.recalculate_duration(task)
        elif column == 3:
            task.end_date = str(value)
            self.recalculate_duration(task)
        elif column == 4:
            task.duration = str(value)
            self.recalculate_end_date(task)
        elif column == 5:
            task.dedication = str(value)
        
        task.is_editing = False
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.EditRole])
        return True

    def recalculate_duration(self, task):
        """Recalcula la duración de una tarea basada en sus fechas."""
        start_date = QDate.fromString(task.start_date, "dd/MM/yyyy")
        end_date = QDate.fromString(task.end_date, "dd/MM/yyyy")
        
        if not start_date.isValid() or not end_date.isValid():
            return
            
        if end_date < start_date:
            end_date = start_date
            task.end_date = end_date.toString("dd/MM/yyyy")
            
        business_days = self._calculate_business_days(start_date.toPython(), end_date.toPython())
        task.duration = str(business_days)
        
        row = self.visible_tasks.index(task)
        duration_index = self.index(row, 4)
        self.dataChanged.emit(duration_index, duration_index, [Qt.ItemDataRole.DisplayRole])

    def recalculate_end_date(self, task):
        """Recalcula la fecha final de una tarea basada en su duración."""
        start_date = QDate.fromString(task.start_date, "dd/MM/yyyy")
        if not start_date.isValid() or not task.duration.isdigit():
            return

        target_days = int(task.duration)
        current_date = start_date.toPython()
        business_days = 0
        
        while business_days < target_days:
            if self.cal.is_working_day(current_date):
                business_days += 1
            if business_days < target_days:
                current_date += timedelta(days=1)

        task.end_date = QDate(current_date.year, current_date.month, current_date.day).toString("dd/MM/yyyy")
        
        row = self.visible_tasks.index(task)
        end_date_index = self.index(row, 3)
        self.dataChanged.emit(end_date_index, end_date_index, [Qt.ItemDataRole.DisplayRole])

    def _calculate_business_days(self, start_date, end_date):
        """Calcula los días laborables entre dos fechas."""
        business_days = 0
        current_date = start_date
        while current_date <= end_date:
            if self.cal.is_working_day(current_date):
                business_days += 1
            current_date += timedelta(days=1)
        return business_days

    def sort(self, column, order=Qt.SortOrder.AscendingOrder):
        """Ordena las tareas según la columna y orden especificados."""
        self.layoutAboutToBeChanged.emit()
        
        blocks = self._create_task_blocks()
        self._sort_blocks(blocks, column, order)
        self._reconstruct_tasks_from_blocks(blocks)
        
        self.update_visible_tasks()
        self.layoutChanged.emit()

    def _create_task_blocks(self):
        """Crea bloques de tareas (tarea padre con sus subtareas)."""
        blocks = []
        i = 0
        while i < len(self.tasks):
            task = self.tasks[i]
            if not task.is_subtask:
                block = [task]
                j = i + 1
                while j < len(self.tasks) and self.tasks[j].is_subtask:
                    block.append(self.tasks[j])
                    j += 1
                blocks.append(block)
                i = j
            else:
                blocks.append([task])
                i += 1
        return blocks

    def _sort_blocks(self, blocks, column, order):
        """Ordena los bloques de tareas."""
        for block in blocks:
            if len(block) > 1:
                parent_task = block[0]
                subtasks = block[1:]
                subtasks.sort(
                    key=lambda task: self._get_sort_value(task, column),
                    reverse=(order == Qt.SortOrder.DescendingOrder)
                )
                block[1:] = subtasks

        blocks.sort(
            key=lambda block: self._get_sort_value(block[0], column),
            reverse=(order == Qt.SortOrder.DescendingOrder)
        )

    def _get_sort_value(self, task, column):
        """Obtiene el valor de ordenamiento para una tarea y columna específicas."""
        if column == 1:
            return task.name.lower()
        elif column == 2:
            return QDate.fromString(task.start_date, "dd/MM/yyyy")
        elif column == 3:
            return QDate.fromString(task.end_date, "dd/MM/yyyy")
        return task.name.lower()

    def _reconstruct_tasks_from_blocks(self, blocks):
        """Reconstruye la lista de tareas a partir de los bloques ordenados."""
        self.tasks = []
        for block in blocks:
            self.tasks.extend(block)