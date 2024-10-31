# models.py
# manejan la lógica de la aplicación

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor
from datetime import timedelta
from workalendar.america import Colombia
import ast

class Task:
    """
    Clase que representa una tarea en el proyecto.
    """
    def __init__(self, name, start_date, end_date, duration, dedication, color=None, notes="", notes_html="", file_links=None):
        """
        Inicializa una nueva instancia de Task.

        Args:
            name (str): Nombre de la tarea.
            start_date (str): Fecha de inicio en formato "dd/MM/yyyy".
            end_date (str): Fecha de fin en formato "dd/MM/yyyy".
            duration (str): Duración de la tarea en días laborables.
            dedication (str): Porcentaje de dedicación.
            color (QColor, optional): Color asociado a la tarea. Por defecto es QColor(34, 163, 159).
            notes (str, optional): Notas de la tarea. Por defecto es una cadena vacía.
            notes_html (str, optional): Notas en formato HTML. Por defecto es una cadena vacía.
            file_links (dict, optional): Enlaces a archivos asociados a la tarea. Por defecto es un diccionario vacío.
        """
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
        """
        Verifica si la tarea tiene subtareas.

        Returns:
            bool: True si tiene subtareas, False en caso contrario.
        """
        return bool(self.subtasks)

    def toggle_editing(self):
        """
        Alterna el estado de edición de la tarea.
        """
        self.is_editing = not self.is_editing

    def set_editing(self, value):
        """
        Establece el estado de edición de la tarea.

        Args:
            value (bool): Nuevo estado de edición.
        """
        self.is_editing = value

    def toggle_collapsed(self):
        """
        Alterna el estado de colapso de la tarea.
        """
        self.is_collapsed = not self.is_collapsed

    def update_subtasks(self):
        """
        Actualiza las subtareas de la tarea.
        """
        if self.parent_task:
            self.parent_task.subtasks = [task for task in self.parent_task.subtasks if task != self]
        for subtask in self.subtasks:
            subtask.parent_task = self


class TaskTableModel(QAbstractTableModel):
    """
    Modelo de tabla para manejar las tareas en la vista de tabla.
    """
    def __init__(self, tasks=None):
        """
        Inicializa el modelo de tabla.

        Args:
            tasks (list of Task, optional): Lista inicial de tareas. Por defecto es una lista vacía.
        """
        super(TaskTableModel, self).__init__()
        self.headers = ["", "Nombre", "Fecha inicial", "Fecha final", "Días", "%"]
        self.tasks = tasks or []
        self.update_visible_tasks()

    def update_visible_tasks(self):
        """
        Actualiza la lista de tareas visibles en función del estado de colapso.
        """
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
        """
        Retorna el número de filas en el modelo.

        Args:
            parent (QModelIndex, optional): Índice padre. Por defecto es QModelIndex().

        Returns:
            int: Número de filas visibles.
        """
        return len(self.visible_tasks)

    def columnCount(self, parent=QModelIndex()):
        """
        Retorna el número de columnas en el modelo.

        Args:
            parent (QModelIndex, optional): Índice padre. Por defecto es QModelIndex().

        Returns:
            int: Número de columnas.
        """
        return len(self.headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """
        Retorna los datos para una celda específica según el rol.

        Args:
            index (QModelIndex): Índice de la celda.
            role (Qt.ItemDataRole, optional): Rol de los datos. Por defecto es DisplayRole.

        Returns:
            QVariant: Datos de la celda según el rol.
        """
        if not index.isValid():
            return None

        task = self.visible_tasks[index.row()]
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
        """
        Retorna los datos de los encabezados.

        Args:
            section (int): Sección del encabezado.
            orientation (Qt.Orientation): Orientación del encabezado (Horizontal o Vertical).
            role (Qt.ItemDataRole, optional): Rol de los datos. Por defecto es DisplayRole.

        Returns:
            QVariant: Datos del encabezado según el rol.
        """
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]
        return None

    def flags(self, index):
        """
        Retorna las banderas para una celda específica.

        Args:
            index (QModelIndex): Índice de la celda.

        Returns:
            Qt.ItemFlags: Banderas para la celda.
        """
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled
        flags = super().flags(index)
        if index.column() in [1, 2, 3, 4, 5]:
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def insertTask(self, task, actual_position=None):
        """
        Inserta una tarea en el modelo.

        Args:
            task (Task): Tarea a insertar.
            actual_position (int, optional): Posición real en la lista de tareas. Por defecto es None.

        Returns:
            None
        """
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
        """
        Elimina una tarea del modelo.

        Args:
            position (int): Posición visible de la tarea a eliminar.

        Returns:
            bool: True si la tarea se eliminó exitosamente, False en caso contrario.
        """
        if 0 <= position < self.rowCount():
            actual_position = self.visible_to_actual[position]
            self.beginRemoveRows(QModelIndex(), position, position)
            del self.tasks[actual_position]
            self.update_visible_tasks()
            self.endRemoveRows()
            return True
        return False

    def getTask(self, row):
        """
        Obtiene una tarea visible por su fila.

        Args:
            row (int): Fila visible.

        Returns:
            Task or None: Tarea correspondiente o None si el índice es inválido.
        """
        if 0 <= row < self.rowCount():
            return self.visible_tasks[row]
        return None

    def move_block_down(self, start_row, block_size, insertion_row):
        """
        Mueve un bloque de tareas hacia abajo en el modelo.

        Args:
            start_row (int): Fila de inicio del bloque.
            block_size (int): Tamaño del bloque de tareas (incluye la tarea y subtareas).
            insertion_row (int): Fila de inserción donde se moverá el bloque.

        Returns:
            bool: True si el movimiento fue exitoso, False en caso contrario.
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
        """
        Establece los datos para una celda específica.

        Args:
            index (QModelIndex): Índice de la celda.
            value (QVariant): Nuevo valor.
            role (Qt.ItemDataRole, optional): Rol de los datos. Por defecto es EditRole.

        Returns:
            bool: True si los datos se establecieron exitosamente, False en caso contrario.
        """
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
        """
        Recalcula la duración de una tarea en días laborables.

        Args:
            task (Task): Tarea cuya duración se recalculará.
        """
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
        """
        Recalcula la fecha final de una tarea basada en la duración.

        Args:
            task (Task): Tarea cuya fecha final se recalculará.
        """
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
        """
        Ordena las tareas según una columna específica.

        Args:
            column (int): Índice de la columna por la cual ordenar.
            order (Qt.SortOrder, optional): Orden de clasificación. Por defecto es AscendingOrder.
        """
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
        """
        Retorna la clave de ordenamiento basada en la columna.

        Args:
            column (int): Índice de la columna.

        Returns:
            function: Función que retorna el valor de ordenamiento para una tarea.
        """
        if column == 1:  # Nombre
            return lambda task: task.name.lower()
        elif column == 2:  # Fecha inicial
            return lambda task: QDate.fromString(task.start_date, "dd/MM/yyyy")
        elif column == 3:  # Fecha final
            return lambda task: QDate.fromString(task.end_date, "dd/MM/yyyy")
        else:
            return lambda task: task.name.lower()  # Valor por defecto
