#models.py
#Contiene la lógica y estructuras de datos del modelo de la aplicación.
#En este archivo se definen las clases y métodos encargados de representar
#y gestionar las tareas, su información, y su interacción con la tabla de
#datos subyacente. Estas clases no incluyen lógica de interfaz gráfica,
#sino que suministran datos y funcionalidades que luego pueden ser utilizados
#por la vista y el controlador.
#
from datetime import datetime, timedelta
import ast

from PySide6.QtCore import Qt, QDate, QAbstractTableModel, QModelIndex
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

    @property
    def formatted_name(self):
        return "       " + self.name if self.is_subtask else self.name

    @property
    def has_notes(self):
        return bool(self.notes_html and self.notes_html.strip())

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

    def copy_notes_from(self, other_task):
        # Modificar el método para concatenar las notas
        if other_task.notes_html:
            # Concatenar el HTML de las notas
            if self.notes_html:
                self.notes_html = other_task.notes_html + "<br><br>" + self.notes_html
            else:
                self.notes_html = other_task.notes_html

        if other_task.notes:
            # Concatenar el texto plano
            if self.notes:
                self.notes = other_task.notes + "\n\n" + self.notes
            else:
                self.notes = other_task.notes

        # Combinar los file_links
        for key, value in other_task.file_links.items():
            if key not in self.file_links:
                self.file_links[key] = value

class TaskTableModel(QAbstractTableModel):
    def __init__(self, tasks=None, main_window=None):
        super(TaskTableModel, self).__init__()
        self.headers = ["", "Nombre", "Fecha inicial", "Fecha final", "Días", "%"]
        self.tasks = tasks or []
        self.main_window = main_window
        self._editing_programmatically = False
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
                # Si estamos editando programáticamente (desde un comando), no crear nuevo comando
                if self._editing_programmatically:
                    return self._set_data_direct(task, column, value, index)

                # Si tenemos acceso al main_window y no estamos cargando archivo, crear comando
                if (self.main_window and
                    hasattr(self.main_window, 'command_manager') and
                    not getattr(self.main_window, '_loading_file', False)):

                    # Crear comando de edición con valores anteriores
                    old_value = self._get_current_value(task, column)
                    new_value = str(value)

                    if old_value != new_value:
                        from command_system import EditTaskCommand
                        field_map = {1: 'name', 2: 'start_date', 3: 'end_date',
                                   4: 'duration', 5: 'dedication'}

                        if column in field_map:
                            command = EditTaskCommand(
                                self.main_window,
                                index.row(),
                                field_map[column],
                                old_value,
                                new_value
                            )
                            self.main_window.command_manager.execute_command(command)
                            return True

                # Fallback para edición directa
                return self._set_data_direct(task, column, value, index)
            return False

    def _get_current_value(self, task, column):
        """Obtiene el valor actual de la tarea para la columna especificada."""
        if column == 1:
            return task.name
        elif column == 2:
            return task.start_date
        elif column == 3:
            return task.end_date
        elif column == 4:
            return task.duration
        elif column == 5:
            return task.dedication
        return ""

    def _set_data_direct(self, task, column, value, index):
        """Establece datos directamente sin crear comandos."""
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
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.EditRole])
        return True

    def set_data_programmatically(self, task, field, value):
        """Permite establecer datos programáticamente sin crear comandos."""
        self._editing_programmatically = True
        try:
            setattr(task, field, value)

            # Recalcular dependencias si es necesario
            if field == 'start_date' or field == 'end_date':
                self.recalculate_duration(task)
            elif field == 'duration':
                self.recalculate_end_date(task)

            # Encontrar el índice de la tarea y emitir señal
            try:
                row = self.visible_tasks.index(task)
                column_map = {'name': 1, 'start_date': 2, 'end_date': 3, 'duration': 4, 'dedication': 5}
                if field in column_map:
                    index = self.index(row, column_map[field])
                    self.dataChanged.emit(index, index, [Qt.ItemDataRole.EditRole])
            except ValueError:
                pass

        finally:
            self._editing_programmatically = False

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
