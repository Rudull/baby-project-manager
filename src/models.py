"""models.py
Contiene la lógica y estructuras de datos del modelo de la aplicación.
Define las clases para representar tareas y el modelo de tabla de Qt.
No incluye lógica de interfaz gráfica.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from PySide6.QtCore import Qt, QDate, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QColor

from workalendar.america import Colombia

# command_system imports models indirectly (via main_window). To avoid a
# circular import at module level we import EditTaskCommand here at the top
# since command_system does NOT import models at module level.
from command_system import EditTaskCommand  # noqa: E402

logger = logging.getLogger("bpm.models")


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass(eq=False)
class Task:
    """Representa una tarea o subtarea del proyecto.

    Se usa ``eq=False`` para preservar la identidad de objeto (``is``/``not in``
    list comparisons) que command_system.py requiere en snapshots. QColor tampoco
    implementa __hash__ de forma compatible con dataclass frozen.

    ``color=None`` sigue siendo válido: ``__post_init__`` lo reemplaza por el
    color por defecto, manteniendo la API original del constructor.
    """

    name: str
    start_date: str
    end_date: str
    duration: str
    dedication: str
    color: QColor | None = None
    notes: str = ""
    notes_html: str = ""
    file_links: dict[str, str] | None = None
    subtasks: list[Task] = field(default_factory=list, repr=False)
    is_subtask: bool = False
    parent_task: Task | None = field(default=None, repr=False)
    is_editing: bool = False
    is_collapsed: bool = False
    linked_to_subtasks: bool = True
    stored_start_date: str | None = None
    stored_end_date: str | None = None
    stored_duration: str | None = None
    # Alerts — None means "use global config"; "never" means silenced
    alert_threshold_days: int | None = None
    alert_snoozed_until: str | None = None   # "dd/MM/yyyy" or "never"
    extra_reminders: list[str] = field(default_factory=list)  # exact dates "dd/MM/yyyy"

    def __post_init__(self) -> None:
        if self.color is None:
            self.color = QColor(34, 163, 159)
        if self.file_links is None:
            self.file_links = {}

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def formatted_name(self) -> str:
        return "       " + self.name if self.is_subtask else self.name

    @property
    def has_notes(self) -> bool:
        return bool(self.notes_html and self.notes_html.strip())

    def has_subtasks(self) -> bool:
        return bool(self.subtasks)

    # ------------------------------------------------------------------
    # Mutators
    # ------------------------------------------------------------------

    def toggle_editing(self) -> None:
        self.is_editing = not self.is_editing

    def set_editing(self, value: bool) -> None:
        self.is_editing = value

    def toggle_collapsed(self) -> None:
        self.is_collapsed = not self.is_collapsed

    def update_subtasks(self) -> None:
        if self.parent_task:
            self.parent_task.subtasks = [
                t for t in self.parent_task.subtasks if t is not self
            ]
        for subtask in self.subtasks:
            subtask.parent_task = self

    def copy_notes_from(self, other_task: Task) -> None:
        """Concatena las notas del ``other_task`` al inicio de las propias."""
        if other_task.notes_html:
            if self.notes_html:
                self.notes_html = other_task.notes_html + "<br><br>" + self.notes_html
            else:
                self.notes_html = other_task.notes_html

        if other_task.notes:
            if self.notes:
                self.notes = other_task.notes + "\n\n" + self.notes
            else:
                self.notes = other_task.notes

        for key, value in other_task.file_links.items():
            if key not in self.file_links:
                self.file_links[key] = value


# ---------------------------------------------------------------------------
# TaskTableModel
# ---------------------------------------------------------------------------

class TaskTableModel(QAbstractTableModel):
    def __init__(
        self, tasks: list[Task] | None = None, main_window: object | None = None
    ) -> None:
        super().__init__()
        self.headers: list[str] = ["", "Nombre", "Fecha inicial", "Fecha final", "Días", "%"]
        self.tasks: list[Task] = tasks or []
        self.main_window = main_window
        self._editing_programmatically: bool = False

        # O(n) state — rebuilt on every update_visible_tasks() call
        self.visible_tasks: list[Task] = []
        self.visible_to_actual: list[int] = []
        self.actual_to_visible: dict[int, int] = {}
        # O(1) task → visible-row lookup (kept in sync with update_visible_tasks)
        self._task_to_row: dict[int, int] = {}  # id(task) → visible_row

        self.update_visible_tasks()

    # ------------------------------------------------------------------
    # Index management
    # ------------------------------------------------------------------

    def update_visible_tasks(self) -> None:
        self.visible_tasks = []
        self.visible_to_actual = []
        self.actual_to_visible = {}
        self._task_to_row = {}

        idx = 0
        visible_idx = 0
        while idx < len(self.tasks):
            task = self.tasks[idx]
            self.visible_tasks.append(task)
            self.visible_to_actual.append(idx)
            self.actual_to_visible[idx] = visible_idx
            self._task_to_row[id(task)] = visible_idx
            idx += 1
            visible_idx += 1
            if not task.is_subtask and task.is_collapsed:
                while idx < len(self.tasks) and self.tasks[idx].is_subtask:
                    idx += 1

    def _get_visible_row(self, task: Task) -> int:
        """Retorna la fila visible de ``task`` en O(1). Lanza KeyError si no visible."""
        return self._task_to_row[id(task)]

    # ------------------------------------------------------------------
    # QAbstractTableModel interface
    # ------------------------------------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.visible_tasks)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.headers)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        if not index.isValid():
            return None

        task = self.visible_tasks[index.row()]
        column = index.column()

        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            if column == 0:
                return ""
            if column == 1:
                return task.formatted_name
            if column == 2:
                return task.start_date
            if column == 3:
                return task.end_date
            if column == 4:
                return task.duration
            if column == 5:
                return task.dedication
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if column in (2, 3, 4, 5):
                return int(Qt.AlignmentFlag.AlignCenter)
            return int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        elif role == Qt.ItemDataRole.UserRole:
            return task
        elif role == Qt.ItemDataRole.BackgroundRole:
            if column == 1:
                return task.color
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled
        flags = super().flags(index)
        if index.column() in [1, 2, 3, 4, 5]:
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def insertTask(self, task: Task, actual_position: int | None = None) -> None:
        if actual_position is not None:
            position = self.actual_to_visible.get(actual_position, self.rowCount())
        else:
            actual_position = len(self.tasks)
            position = self.rowCount()
        self.beginInsertRows(QModelIndex(), position, position)
        self.tasks.insert(actual_position, task)
        self.update_visible_tasks()
        self.endInsertRows()

    def removeTask(self, position: int) -> bool:
        if 0 <= position < self.rowCount():
            actual_position = self.visible_to_actual[position]
            self.beginRemoveRows(QModelIndex(), position, position)
            del self.tasks[actual_position]
            self.update_visible_tasks()
            self.endRemoveRows()
            return True
        return False

    def getTask(self, row: int) -> Task | None:
        if 0 <= row < self.rowCount():
            return self.visible_tasks[row]
        return None

    # ------------------------------------------------------------------
    # Move
    # ------------------------------------------------------------------

    def move_block_down(
        self, start_row: int, block_size: int, insertion_row: int
    ) -> bool:
        """Mueve un bloque de tareas hacia abajo en el modelo."""
        if (
            start_row < 0
            or start_row + block_size > self.rowCount()
            or insertion_row > self.rowCount()
        ):
            return False

        self.beginMoveRows(
            QModelIndex(),
            start_row,
            start_row + block_size - 1,
            QModelIndex(),
            insertion_row,
        )
        moving_tasks = self.visible_tasks[start_row : start_row + block_size]
        del self.visible_tasks[start_row : start_row + block_size]
        self.visible_tasks[insertion_row:insertion_row] = moving_tasks
        self.update_visible_tasks()
        self.endMoveRows()
        return True

    # ------------------------------------------------------------------
    # setData / data helpers
    # ------------------------------------------------------------------

    def setData(
        self, index: QModelIndex, value: object, role: int = Qt.ItemDataRole.EditRole
    ) -> bool:
        if not index.isValid():
            return False

        task = self.visible_tasks[index.row()]
        column = index.column()

        if role == Qt.ItemDataRole.EditRole:
            if self._editing_programmatically:
                return self._set_data_direct(task, column, value, index)

            if (
                self.main_window
                and hasattr(self.main_window, "command_manager")
                and not getattr(self.main_window, "_loading_file", False)
            ):
                old_value = self._get_current_value(task, column)
                new_value = str(value)

                if old_value != new_value:
                    # EditTaskCommand is imported at module level (top of file).
                    # command_system does NOT import models, so there is no
                    # circular dependency despite the coupling direction.
                    field_map = {
                        1: "name",
                        2: "start_date",
                        3: "end_date",
                        4: "duration",
                        5: "dedication",
                    }
                    if column in field_map:
                        command = EditTaskCommand(
                            self.main_window,  # type: ignore[arg-type]
                            index.row(),
                            field_map[column],
                            old_value,
                            new_value,
                        )
                        self.main_window.command_manager.execute_command(command)
                        return True

            return self._set_data_direct(task, column, value, index)
        return False

    def _get_current_value(self, task: Task, column: int) -> str:
        """Obtiene el valor actual de la tarea para la columna especificada."""
        mapping = {
            1: task.name,
            2: task.start_date,
            3: task.end_date,
            4: task.duration,
            5: task.dedication,
        }
        return mapping.get(column, "")

    def _set_data_direct(
        self, task: Task, column: int, value: object, index: QModelIndex
    ) -> bool:
        """Establece datos directamente sin crear comandos."""
        if column == 1:
            task.name = str(value)
        elif column == 2:
            task.start_date = str(value)
            self.recalculate_duration(task)
            if task.is_subtask and task.parent_task:
                self.update_parent_linked_duration(task.parent_task)
        elif column == 3:
            task.end_date = str(value)
            self.recalculate_duration(task)
            if task.is_subtask and task.parent_task:
                self.update_parent_linked_duration(task.parent_task)
        elif column == 4:
            task.duration = str(value)
            self.recalculate_end_date(task)
            if task.is_subtask and task.parent_task:
                self.update_parent_linked_duration(task.parent_task)
        elif column == 5:
            task.dedication = str(value)

        task.is_editing = False
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.EditRole])
        return True

    def set_data_programmatically(self, task: Task, field: str, value: object) -> None:
        """Permite establecer datos programáticamente sin crear comandos."""
        self._editing_programmatically = True
        try:
            setattr(task, field, value)

            if field in ("start_date", "end_date"):
                self.recalculate_duration(task)
                if task.is_subtask and task.parent_task:
                    self.update_parent_linked_duration(task.parent_task)
            elif field == "duration":
                self.recalculate_end_date(task)
                if task.is_subtask and task.parent_task:
                    self.update_parent_linked_duration(task.parent_task)

            try:
                row = self._get_visible_row(task)  # O(1)
                column_map = {
                    "name": 1,
                    "start_date": 2,
                    "end_date": 3,
                    "duration": 4,
                    "dedication": 5,
                }
                if field in column_map:
                    idx = self.index(row, column_map[field])
                    self.dataChanged.emit(idx, idx, [Qt.ItemDataRole.EditRole])
            except KeyError:
                logger.debug(
                    "Task '%s' not in visible rows during set_data_programmatically", task.name
                )
        finally:
            self._editing_programmatically = False

    # ------------------------------------------------------------------
    # Date / duration recalculation
    # Note: the day-loop is O(calendar_days) by design (workalendar).
    # For very long projects caching holiday sets could help, but correctness
    # is prioritised over micro-optimisation here.
    # ------------------------------------------------------------------

    def recalculate_duration(self, task: Task) -> None:
        start_date = QDate.fromString(task.start_date, "dd/MM/yyyy")
        end_date = QDate.fromString(task.end_date, "dd/MM/yyyy")
        if not start_date.isValid() or not end_date.isValid():
            return
        if end_date < start_date:
            end_date = start_date
            task.end_date = end_date.toString("dd/MM/yyyy")

        cal = Colombia()
        business_days = 0
        current = start_date.toPython()
        end = end_date.toPython()
        while current <= end:
            if cal.is_working_day(current):
                business_days += 1
            current += timedelta(days=1)
        task.duration = str(business_days)

        try:
            row = self._get_visible_row(task)  # O(1)
            self.dataChanged.emit(
                self.index(row, 4), self.index(row, 4), [Qt.ItemDataRole.DisplayRole]
            )
        except KeyError:
            pass

    def recalculate_end_date(self, task: Task) -> None:
        start_date = QDate.fromString(task.start_date, "dd/MM/yyyy")
        if not start_date.isValid():
            return
        if not task.duration.isdigit():
            return

        target_days = int(task.duration)
        cal = Colombia()
        business_days = 0
        end = start_date.toPython()
        while business_days < target_days:
            if cal.is_working_day(end):
                business_days += 1
            if business_days < target_days:
                end += timedelta(days=1)
        task.end_date = QDate(end).toString("dd/MM/yyyy")

        try:
            row = self._get_visible_row(task)  # O(1)
            self.dataChanged.emit(
                self.index(row, 3), self.index(row, 3), [Qt.ItemDataRole.DisplayRole]
            )
        except KeyError:
            pass

    def update_parent_linked_duration(self, parent_task: Task) -> None:
        """Actualiza la duración y fechas de la tarea padre basándose en sus subtareas."""
        if not parent_task or not parent_task.subtasks or not parent_task.linked_to_subtasks:
            return

        min_start: QDate | None = None
        max_end: QDate | None = None

        for subtask in parent_task.subtasks:
            s_date = QDate.fromString(subtask.start_date, "dd/MM/yyyy")
            e_date = QDate.fromString(subtask.end_date, "dd/MM/yyyy")

            if s_date.isValid():
                if min_start is None or s_date < min_start:
                    min_start = s_date
            if e_date.isValid():
                if max_end is None or e_date > max_end:
                    max_end = e_date

        if min_start and max_end:
            new_start_str = min_start.toString("dd/MM/yyyy")
            new_end_str = max_end.toString("dd/MM/yyyy")

            if parent_task.start_date != new_start_str or parent_task.end_date != new_end_str:
                self._editing_programmatically = True
                try:
                    parent_task.start_date = new_start_str
                    parent_task.end_date = new_end_str
                    self.recalculate_duration(parent_task)

                    try:
                        row = self._get_visible_row(parent_task)
                        idx_start = self.index(row, 2)
                        idx_end = self.index(row, 3)
                        self.dataChanged.emit(idx_start, idx_end, [Qt.ItemDataRole.EditRole])
                    except KeyError:
                        pass
                finally:
                    self._editing_programmatically = False

    # ------------------------------------------------------------------
    # Sort
    # ------------------------------------------------------------------

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        if column not in (1, 2, 3):
            return

        self.layoutAboutToBeChanged.emit()

        blocks: list[list[Task]] = []
        i = 0
        while i < len(self.tasks):
            task = self.tasks[i]
            if not task.is_subtask:
                block: list[Task] = [task]
                j = i + 1
                while j < len(self.tasks) and self.tasks[j].is_subtask:
                    block.append(self.tasks[j])
                    j += 1
                parent_task = block[0]
                subtasks = block[1:]
                subtasks.sort(
                    key=self.get_sort_key(column),
                    reverse=(order == Qt.SortOrder.DescendingOrder),
                )
                blocks.append([parent_task] + subtasks)
                i = j
            else:
                blocks.append([task])
                i += 1

        blocks.sort(
            key=lambda blk: self.get_sort_key(column)(blk[0]),
            reverse=(order == Qt.SortOrder.DescendingOrder),
        )
        self.tasks = [task for block in blocks for task in block]
        self.update_visible_tasks()
        self.layoutChanged.emit()

    def get_sort_key(self, column: int):  # type: ignore[return]
        if column == 1:
            return lambda task: task.name.lower()
        if column == 2:
            return lambda task: QDate.fromString(task.start_date, "dd/MM/yyyy")
        if column == 3:
            return lambda task: QDate.fromString(task.end_date, "dd/MM/yyyy")
        return lambda task: task.name.lower()
