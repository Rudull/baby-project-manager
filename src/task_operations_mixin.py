"""task_operations_mixin.py
Mixin que agrupa todas las operaciones CRUD sobre tareas para MainWindow.
Separa la lógica de manipulación de tareas de la lógica de layout de UI,
reduciendo main_window.py a sus responsabilidades de configuración y eventos.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import QDate
from PySide6.QtGui import QColor

from models import Task
from command_system import (
    AddTaskCommand,
    DeleteTaskCommand,
    MoveTaskCommand,
    ChangeColorCommand,
    DuplicateTaskCommand,
    ConvertTaskCommand,
    AddSubtaskCommand,
    InsertTaskCommand,
)

if TYPE_CHECKING:
    from models import TaskTableModel

logger = logging.getLogger("bpm.task_ops")

_DEFAULT_COLOR = QColor(34, 163, 159)


class TaskOperationsMixin:
    """Mixin con las operaciones de tareas. Requiere que la clase host sea MainWindow."""

    # Attributes expected from MainWindow (declared for type checker only)
    model: TaskTableModel
    tasks: list[Task]

    # ------------------------------------------------------------------
    # Add
    # ------------------------------------------------------------------

    def add_new_task(self) -> None:
        """Añade una nueva tarea usando el sistema de comandos."""
        command = AddTaskCommand(self)  # type: ignore[arg-type]
        self.command_manager.execute_command(command)

    def _add_new_task_internal(self) -> None:
        """Añade nueva tarea internamente (llamada por el comando)."""
        task_data = {
            "NAME": "Nueva Tarea",
            "START": QDate.currentDate().toString("dd/MM/yyyy"),
            "END": QDate.currentDate().toString("dd/MM/yyyy"),
            "DURATION": "1",
            "DEDICATION": "40",
            "COLOR": _DEFAULT_COLOR.name(),
            "NOTES": "",
        }
        self.task_table_widget.add_task_to_table(task_data, editable=True)
        self.adjust_all_row_heights()
        self.update_gantt_chart()
        self.update_shared_scrollbar_range()
        if self.model.rowCount() > 0:
            self.set_unsaved_changes(True)

        new_task_row = self.model.rowCount() - 1
        self.table_view.selectRow(new_task_row)
        self.table_view.scrollTo(self.model.index(new_task_row, 0))
        self.table_view.edit(self.model.index(new_task_row, 1))

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_task(self, row: int) -> None:
        """Elimina una tarea usando el sistema de comandos."""
        if row >= 0:
            command = DeleteTaskCommand(self, row)  # type: ignore[arg-type]
            self.command_manager.execute_command(command)

    def _delete_task_internal(self, row: int) -> None:
        """Eliminación interna de tarea (llamada por el comando)."""
        if row < 0:
            return
        task = self.model.getTask(row)
        if not task:
            return

        actual_row = self.model.visible_to_actual[row]

        if task.is_subtask and task.parent_task:
            self.model.tasks.pop(actual_row)
            task.parent_task.subtasks.remove(task)
        elif not task.is_subtask:
            total_subtasks = self.count_subtasks(actual_row)
            for _ in range(total_subtasks + 1):
                self.model.tasks.pop(actual_row)

        self.model.update_visible_tasks()
        self.model.layoutChanged.emit()
        self.update_task_structure()
        self.task_table_widget.update_state_buttons()
        self.set_unsaved_changes(True)
        self.update_gantt_chart()
        self.update_shared_scrollbar_range()

        if self.model.rowCount() > 0:
            new_row = min(row, self.model.rowCount() - 1)
            self.table_view.selectRow(new_row)
            self.table_view.scrollTo(self.model.index(new_row, 0))
        else:
            self.table_view.clearSelection()
            self.update_gantt_highlight(None)

    # ------------------------------------------------------------------
    # Structure helpers
    # ------------------------------------------------------------------

    def update_task_structure(self) -> None:
        """Reconstruye la estructura de tareas (lista plana → árbol padre/hijo)."""
        self.tasks = []
        current_parent: Task | None = None

        for task in self.model.tasks:
            if task:
                if not task.is_subtask:
                    current_parent = task
                    current_parent.subtasks = []
                    self.tasks.append(current_parent)
                elif current_parent:
                    current_parent.subtasks.append(task)
                    task.parent_task = current_parent

        self.task_table_widget.update_state_buttons()

    def count_subtasks(self, actual_row: int) -> int:
        """Cuenta las subtareas inmediatamente después de ``actual_row``."""
        count = 0
        for i in range(actual_row + 1, len(self.model.tasks)):
            if self.model.tasks[i].is_subtask:
                count += 1
            else:
                break
        return count

    # ------------------------------------------------------------------
    # Duplicate
    # ------------------------------------------------------------------

    def duplicate_task(self, row: int) -> None:
        """Duplica una tarea usando el sistema de comandos."""
        logger.debug("duplicate_task: row %d", row)
        command = DuplicateTaskCommand(self, row)  # type: ignore[arg-type]
        self.command_manager.execute_command(command)

    def _duplicate_task_internal(self, row: int) -> None:
        """Duplicación interna de tarea (llamada por el comando)."""
        model = self.model
        if not (0 <= row < model.rowCount()):
            return

        actual_row = model.visible_to_actual[row]
        if actual_row >= len(model.tasks):
            return

        task = model.tasks[actual_row]
        if not task:
            return

        duplicated_task = Task(
            name=task.name + " (copia)",
            start_date=task.start_date,
            end_date=task.end_date,
            duration=task.duration,
            dedication=task.dedication,
            color=QColor(task.color),
            notes=task.notes,
            notes_html=task.notes_html,
            file_links=task.file_links.copy(),
        )
        duplicated_task.is_subtask = task.is_subtask
        duplicated_task.parent_task = task.parent_task

        if task.is_subtask:
            actual_insert_index = actual_row + 1
            model.insertTask(duplicated_task, actual_insert_index)
            if duplicated_task.parent_task:
                duplicated_task.parent_task.subtasks.append(duplicated_task)
        else:
            current_block_size = self.count_subtasks(actual_row) + 1
            actual_insert_index = actual_row + current_block_size
            model.insertTask(duplicated_task, actual_insert_index)
            if task.subtasks:
                duplicated_task.subtasks = []
                subtask_insert_index = actual_insert_index + 1
                for subtask in task.subtasks:
                    dup_subtask = Task(
                        name=subtask.name + " (copia)",
                        start_date=subtask.start_date,
                        end_date=subtask.end_date,
                        duration=subtask.duration,
                        dedication=subtask.dedication,
                        color=QColor(subtask.color),
                        notes=subtask.notes,
                        notes_html=subtask.notes_html,
                        file_links=subtask.file_links.copy(),
                    )
                    dup_subtask.is_subtask = True
                    dup_subtask.parent_task = duplicated_task
                    duplicated_task.subtasks.append(dup_subtask)
                    model.insertTask(dup_subtask, subtask_insert_index)
                    subtask_insert_index += 1

        model.update_visible_tasks()
        model.layoutChanged.emit()
        self.update_gantt_chart()
        self.update_shared_scrollbar_range()
        self.set_unsaved_changes(True)

        new_visible_row = model.actual_to_visible.get(actual_insert_index)
        if new_visible_row is not None and new_visible_row < model.rowCount():
            self.table_view.selectRow(new_visible_row)
            self.table_view.scrollTo(model.index(new_visible_row, 0))
            self.table_view.edit(model.index(new_visible_row, 1))
        else:
            duplicated_task.is_collapsed = False
            model.update_visible_tasks()
            model.layoutChanged.emit()
            new_visible_row = model.actual_to_visible.get(actual_insert_index)
            if new_visible_row is not None and new_visible_row < model.rowCount():
                self.table_view.selectRow(new_visible_row)
                self.table_view.scrollTo(model.index(new_visible_row, 0))
                self.table_view.edit(model.index(new_visible_row, 1))

    # ------------------------------------------------------------------
    # Insert
    # ------------------------------------------------------------------

    def insert_task(self, row: int) -> None:
        """Inserta una tarea usando el sistema de comandos."""
        logger.debug("insert_task: row %d", row)
        command = InsertTaskCommand(self, row)  # type: ignore[arg-type]
        self.command_manager.execute_command(command)

    def _insert_task_internal(self, row: int) -> None:
        """Inserción interna de tarea (llamada por el comando)."""
        model = self.model
        if row < len(model.visible_to_actual):
            actual_row = model.visible_to_actual[row]
            task = model.tasks[actual_row]
            if task:
                if task.is_subtask:
                    parent_task = task.parent_task
                    parent_actual_index = actual_row
                    while parent_actual_index >= 0:
                        if model.tasks[parent_actual_index] is parent_task:
                            break
                        parent_actual_index -= 1
                    actual_insert_index = (
                        parent_actual_index + self.count_subtasks(parent_actual_index) + 1
                    )
                elif task.subtasks:
                    actual_insert_index = actual_row + self.count_subtasks(actual_row) + 1
                else:
                    actual_insert_index = actual_row + 1
            else:
                actual_insert_index = len(model.tasks)
        else:
            actual_insert_index = len(model.tasks)

        new_task = Task(
            name="Nueva Tarea",
            start_date=QDate.currentDate().toString("dd/MM/yyyy"),
            end_date=QDate.currentDate().toString("dd/MM/yyyy"),
            duration="1",
            dedication="40",
            color=QColor(_DEFAULT_COLOR),
            notes="",
        )
        model.insertTask(new_task, actual_insert_index)
        model.update_visible_tasks()
        self.update_gantt_chart()
        self.update_shared_scrollbar_range()
        self.set_unsaved_changes(True)

        visible_index = model.actual_to_visible.get(actual_insert_index)
        if visible_index is not None and visible_index < model.rowCount():
            self.table_view.selectRow(visible_index)
            self.table_view.scrollTo(model.index(visible_index, 0))
            self.table_view.edit(model.index(visible_index, 1))

    # ------------------------------------------------------------------
    # Move Up / Down
    # ------------------------------------------------------------------

    def move_task_up(self, row: int) -> None:
        """Mueve una tarea hacia arriba usando el sistema de comandos."""
        if row > 0:
            command = MoveTaskCommand(self, row, "up")  # type: ignore[arg-type]
            self.command_manager.execute_command(command)

    def _move_task_up_internal(self, row: int) -> None:
        """Movimiento interno hacia arriba (llamado por el comando)."""
        model = self.model
        if row <= 0:
            return

        if row >= len(model.visible_to_actual):
            logger.warning("Visible row %d out of range.", row)
            return

        actual_row = model.visible_to_actual[row]
        if actual_row >= len(model.tasks):
            logger.warning("Actual row %d out of range.", actual_row)
            return

        task = model.tasks[actual_row]
        if not task:
            return

        if not task.is_subtask:
            prev_actual_row = actual_row - 1
            while prev_actual_row >= 0 and model.tasks[prev_actual_row].is_subtask:
                prev_actual_row -= 1
            if prev_actual_row < 0:
                return
            prev_block_size = self.count_subtasks(prev_actual_row) + 1
            start1, end1 = prev_actual_row, prev_actual_row + prev_block_size
            start2, end2 = actual_row, actual_row + self.count_subtasks(actual_row) + 1
            model.tasks[start1:end2] = model.tasks[start2:end2] + model.tasks[start1:end1]
            model.update_visible_tasks()
            model.layoutChanged.emit()
            self.update_gantt_chart()
            self.set_unsaved_changes(True)
            new_visible_row = model.actual_to_visible.get(start1, row - prev_block_size)
            if new_visible_row < model.rowCount():
                self.table_view.selectRow(new_visible_row)
                self.table_view.scrollTo(model.index(new_visible_row, 0))
        elif task.is_subtask and actual_row > 0:
            above_task = model.tasks[actual_row - 1]
            if above_task.is_subtask and above_task.parent_task is task.parent_task:
                model.tasks[actual_row], model.tasks[actual_row - 1] = (
                    model.tasks[actual_row - 1],
                    model.tasks[actual_row],
                )
                model.update_visible_tasks()
                model.dataChanged.emit(
                    model.index(row - 1, 0),
                    model.index(row, model.columnCount() - 1),
                    [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.BackgroundRole],
                )
                self.update_gantt_chart()
                self.set_unsaved_changes(True)
                new_visible_row = model.actual_to_visible.get(actual_row - 1, row - 1)
                self.table_view.selectRow(new_visible_row)
                self.table_view.scrollTo(model.index(new_visible_row, 0))

    def move_task_down(self, row: int) -> None:
        """Mueve una tarea hacia abajo usando el sistema de comandos."""
        if row < self.model.rowCount() - 1:
            command = MoveTaskCommand(self, row, "down")  # type: ignore[arg-type]
            self.command_manager.execute_command(command)

    def _move_task_down_internal(self, row: int) -> None:
        """Movimiento interno hacia abajo (llamado por el comando)."""
        model = self.model
        if row >= model.rowCount() - 1:
            return

        if row >= len(model.visible_to_actual):
            logger.warning("Visible row %d out of range.", row)
            return

        actual_row = model.visible_to_actual[row]
        if actual_row >= len(model.tasks):
            logger.warning("Actual row %d out of range.", actual_row)
            return

        task = model.tasks[actual_row]
        if not task:
            return

        if not task.is_subtask:
            current_block_size = self.count_subtasks(actual_row) + 1
            next_actual_row = actual_row + current_block_size
            if next_actual_row < len(model.tasks):
                next_block_size = self.count_subtasks(next_actual_row) + 1
                model.tasks[actual_row : next_actual_row + next_block_size] = (
                    model.tasks[next_actual_row : next_actual_row + next_block_size]
                    + model.tasks[actual_row:next_actual_row]
                )
                model.update_visible_tasks()
                model.layoutChanged.emit()
                self.update_gantt_chart()
                self.set_unsaved_changes(True)
                new_actual_row = model.tasks.index(task)
                new_visible_row = model.actual_to_visible.get(new_actual_row, row)
                if new_visible_row < model.rowCount():
                    self.table_view.selectRow(new_visible_row)
                    self.table_view.scrollTo(model.index(new_visible_row, 0))
        elif task.is_subtask and actual_row + 1 < len(model.tasks):
            below_task = model.tasks[actual_row + 1]
            if below_task.is_subtask and below_task.parent_task is task.parent_task:
                model.tasks[actual_row], model.tasks[actual_row + 1] = (
                    model.tasks[actual_row + 1],
                    model.tasks[actual_row],
                )
                model.update_visible_tasks()
                model.dataChanged.emit(
                    model.index(row, 0),
                    model.index(row + 1, model.columnCount() - 1),
                    [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.BackgroundRole],
                )
                self.update_gantt_chart()
                self.set_unsaved_changes(True)
                new_actual_row = actual_row + 1
                new_visible_row = model.actual_to_visible.get(new_actual_row, row + 1)
                self.table_view.selectRow(new_visible_row)
                self.table_view.scrollTo(model.index(new_visible_row, 0))

    # ------------------------------------------------------------------
    # Convert
    # ------------------------------------------------------------------

    def convert_to_subtask(self, task_index: int) -> None:
        """Convierte tarea a subtarea usando el sistema de comandos."""
        command = ConvertTaskCommand(self, task_index, "to_subtask")  # type: ignore[arg-type]
        self.command_manager.execute_command(command)

    def _convert_to_subtask_internal(self, task_index: int) -> None:
        """Conversión interna a subtarea (llamada por el comando)."""
        model = self.model
        if task_index >= len(model.visible_to_actual):
            return

        actual_row = model.visible_to_actual[task_index]
        task = model.tasks[actual_row]
        if not task or task.is_subtask:
            return

        prev_parent_index = actual_row - 1
        while prev_parent_index >= 0 and model.tasks[prev_parent_index].is_subtask:
            prev_parent_index -= 1

        if prev_parent_index < 0:
            return

        parent_task = model.tasks[prev_parent_index]
        task.is_subtask = True
        task.parent_task = parent_task
        parent_task.subtasks.append(task)

        # Transferir subtareas existentes al nuevo padre
        owned_subtasks = task.subtasks[:]
        task.subtasks = []
        for subtask in owned_subtasks:
            subtask.parent_task = parent_task
            parent_task.subtasks.append(subtask)

        model.update_visible_tasks()
        model.layoutChanged.emit()
        self.update_gantt_chart()
        self.set_unsaved_changes(True)

    def convert_to_parent_task(self, task_index: int) -> None:
        """Convierte subtarea a tarea padre usando el sistema de comandos."""
        command = ConvertTaskCommand(self, task_index, "to_parent")  # type: ignore[arg-type]
        self.command_manager.execute_command(command)

    def _convert_to_parent_task_internal(self, task_index: int) -> None:
        """Conversión interna a tarea padre (llamada por el comando)."""
        model = self.model
        if task_index >= len(model.visible_to_actual):
            return

        actual_row = model.visible_to_actual[task_index]
        task = model.tasks[actual_row]
        if not task or not task.is_subtask:
            return

        current_parent = task.parent_task
        if current_parent:
            current_parent.subtasks.remove(task)

        task.is_subtask = False
        task.parent_task = None
        task.subtasks = []
        task.is_collapsed = False

        last_block_index = actual_row
        while last_block_index + 1 < len(model.tasks):
            if not model.tasks[last_block_index + 1].is_subtask:
                break
            last_block_index += 1

        model.tasks.remove(task)
        model.tasks.insert(last_block_index, task)
        model.update_visible_tasks()
        model.layoutChanged.emit()
        self.update_gantt_chart()
        self.set_unsaved_changes(True)

        new_actual_row = model.tasks.index(task)
        new_visible_row = model.actual_to_visible.get(new_actual_row)
        if new_visible_row is not None:
            self.table_view.selectRow(new_visible_row)
            self.table_view.scrollTo(model.index(new_visible_row, 0))

    # ------------------------------------------------------------------
    # Add Subtask
    # ------------------------------------------------------------------

    def add_subtask(self, parent_task_index: int) -> None:
        """Añade una subtarea usando el sistema de comandos."""
        logger.debug("add_subtask: parent index %d", parent_task_index)
        command = AddSubtaskCommand(self, parent_task_index)  # type: ignore[arg-type]
        self.command_manager.execute_command(command)

    def _add_subtask_internal(self, parent_task_index: int) -> None:
        """Añade subtarea internamente (llamada por el comando)."""
        model = self.model
        if parent_task_index >= len(model.visible_to_actual):
            logger.warning("Parent visible row %d out of range.", parent_task_index)
            return

        actual_parent_index = model.visible_to_actual[parent_task_index]
        if actual_parent_index >= len(model.tasks):
            logger.warning("Actual parent row %d out of range.", actual_parent_index)
            return

        parent_task = model.tasks[actual_parent_index]
        if not parent_task:
            return

        subtask = Task(
            name=f"Subtarea de {parent_task.name}",
            start_date=parent_task.start_date,
            end_date=parent_task.end_date,
            duration=parent_task.duration,
            dedication=parent_task.dedication,
            color=QColor(parent_task.color),
            notes="",
        )
        subtask.is_subtask = True
        subtask.parent_task = parent_task

        if parent_task.is_collapsed:
            parent_task.is_collapsed = False

        insert_index = actual_parent_index + 1
        while insert_index < len(model.tasks) and model.tasks[insert_index].is_subtask:
            insert_index += 1

        model.insertTask(subtask, insert_index)
        parent_task.subtasks.append(subtask)
        model.update_visible_tasks()
        model.layoutChanged.emit()
        self.update_gantt_chart()
        self.update_shared_scrollbar_range()
        self.set_unsaved_changes(True)

        new_actual_row = model.tasks.index(subtask)
        visible_index = model.actual_to_visible.get(new_actual_row)
        if visible_index is not None and visible_index < model.rowCount():
            self.table_view.selectRow(visible_index)
            self.table_view.scrollTo(model.index(visible_index, 0))
            self.table_view.edit(model.index(visible_index, 1))

    # ------------------------------------------------------------------
    # Color
    # ------------------------------------------------------------------

    def reset_task_color(self, task_index: int) -> None:
        """Restablece el color de una tarea usando el sistema de comandos."""
        if 0 <= task_index < len(self.tasks):
            task = self.tasks[task_index]
            if task:
                command = ChangeColorCommand(  # type: ignore[arg-type]
                    self, task_index, task.color, QColor(_DEFAULT_COLOR)
                )
                self.command_manager.execute_command(command)

    def update_task_color(
        self, task_index: int, color: QColor, use_command: bool = True
    ) -> None:
        """Actualiza el color de una tarea."""
        if use_command and 0 <= task_index < len(self.tasks):
            task = self.tasks[task_index]
            if task:
                logger.debug(
                    "update_task_color: task %d → %s", task_index, color.name()
                )
                command = ChangeColorCommand(  # type: ignore[arg-type]
                    self, task_index, task.color, color
                )
                self.command_manager.execute_command(command)
        else:
            self._update_task_color_internal(task_index, color)

    def _update_task_color_internal(self, task_index: int, color: QColor) -> None:
        """Actualización interna del color (llamada por el comando)."""
        if not (0 <= task_index < len(self.tasks)):
            return
        task = self.tasks[task_index]
        if not task:
            return

        task.color = color
        task.is_editing = False

        actual_row = self.model.tasks.index(task)
        visible_row = self.model.actual_to_visible.get(actual_row)
        if visible_row is not None:
            index = self.model.index(visible_row, 1)
            self.model.dataChanged.emit(index, index, [Qt.ItemDataRole.BackgroundRole])

        if not task.is_subtask and task.subtasks:
            for subtask in task.subtasks:
                subtask.color = color
                subtask_actual_row = self.model.tasks.index(subtask)
                subtask_visible_row = self.model.actual_to_visible.get(subtask_actual_row)
                if subtask_visible_row is not None:
                    idx = self.model.index(subtask_visible_row, 1)
                    self.model.dataChanged.emit(idx, idx, [Qt.ItemDataRole.BackgroundRole])

        self.task_table_widget.update_state_buttons()
        self.set_unsaved_changes(True)
        self.update_gantt_chart()


# Bring Qt import needed inside mixin methods
from PySide6.QtCore import Qt  # noqa: E402
