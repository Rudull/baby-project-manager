"""command_system.py
Sistema de comandos para deshacer/rehacer operaciones en Baby Project Manager.
Implementa el patrón Command con historial limitado.
"""
from __future__ import annotations

import copy
import logging
import traceback
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QColor

if TYPE_CHECKING:
    # Imported only for type annotations to avoid circular imports at runtime.
    # MainWindow imports command_system, so we cannot import it back at module level.
    from core.models import Task
    from ui.main_window import MainWindow

logger = logging.getLogger("bpm.commands")


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class Command:
    """Clase base para todos los comandos."""

    def __init__(self, description: str = "") -> None:
        self.description = description

    def execute(self) -> None:
        """Ejecuta el comando."""
        raise NotImplementedError

    def undo(self) -> None:
        """Deshace el comando."""
        raise NotImplementedError

    def __str__(self) -> str:
        return self.description


class CommandManager(QObject):
    """Gestor de comandos para manejar deshacer/rehacer."""

    commandExecuted: Signal = Signal(str)
    canUndoChanged: Signal = Signal(bool)
    canRedoChanged: Signal = Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.command_history: list[Command] = []
        self.current_index: int = -1
        self.max_history: int = 50

    def execute_command(self, command: Command) -> None:
        """Ejecuta un comando y lo añade al historial."""
        try:
            logger.debug("Executing command: '%s'", command.description)
            command.execute()

            # Eliminar comandos posteriores al índice actual
            self.command_history = self.command_history[: self.current_index + 1]
            self.command_history.append(command)
            self.current_index += 1

            # Mantener el límite del historial
            if len(self.command_history) > self.max_history:
                self.command_history.pop(0)
                self.current_index -= 1

            logger.debug(
                "Command '%s' executed. History: %d commands, index: %d",
                command.description,
                len(self.command_history),
                self.current_index,
            )
            self.commandExecuted.emit(command.description)
            self._emit_status_changes()

        except Exception as err:
            logger.error(
                "Error executing command '%s': %s\n%s",
                command.description,
                err,
                traceback.format_exc(),
            )

    def undo(self) -> bool:
        """Deshace el último comando."""
        if self.can_undo():
            try:
                command = self.command_history[self.current_index]
                logger.debug("Undoing command: '%s'", command.description)
                command.undo()
                self.current_index -= 1
                logger.debug(
                    "Command '%s' undone. History index: %d",
                    command.description,
                    self.current_index,
                )
                self._emit_status_changes()
                return True
            except Exception as err:
                logger.error(
                    "Error undoing command: %s\n%s", err, traceback.format_exc()
                )
                return False
        else:
            logger.debug("No commands to undo.")
        return False

    def redo(self) -> bool:
        """Rehace el siguiente comando."""
        if self.can_redo():
            try:
                self.current_index += 1
                command = self.command_history[self.current_index]
                command.execute()
                self._emit_status_changes()
                return True
            except Exception as err:
                logger.error("Error redoing command: %s", err, exc_info=True)
                self.current_index -= 1
                return False
        return False

    def can_undo(self) -> bool:
        """Verifica si se puede deshacer."""
        return self.current_index >= 0

    def can_redo(self) -> bool:
        """Verifica si se puede rehacer."""
        return self.current_index < len(self.command_history) - 1

    def clear(self) -> None:
        """Limpia el historial de comandos."""
        self.command_history.clear()
        self.current_index = -1
        self._emit_status_changes()

    def _emit_status_changes(self) -> None:
        """Emite señales de cambio de estado."""
        self.canUndoChanged.emit(self.can_undo())
        self.canRedoChanged.emit(self.can_redo())

    def get_undo_text(self) -> str:
        """Obtiene el texto del comando a deshacer."""
        if self.can_undo():
            return f"Deshacer {self.command_history[self.current_index].description}"
        return "Deshacer"

    def get_redo_text(self) -> str:
        """Obtiene el texto del comando a rehacer."""
        if self.can_redo():
            return f"Rehacer {self.command_history[self.current_index + 1].description}"
        return "Rehacer"


# ---------------------------------------------------------------------------
# Concrete Commands
# ---------------------------------------------------------------------------

class AddTaskCommand(Command):
    """Comando para agregar una nueva tarea."""

    def __init__(self, main_window: MainWindow, task_data: dict[str, Any] | None = None, editable: bool = False) -> None:
        super().__init__("agregar tarea")
        self.main_window = main_window
        self.task_data = task_data
        self.editable = editable
        self.added_task: Task | None = None
        self.task_index: int | None = None

    def execute(self) -> None:
        if self.task_data:
            self.main_window.task_table_widget.add_task_to_table(
                self.task_data, self.editable
            )
        else:
            self.main_window._add_new_task_internal()

        if self.main_window.model.rowCount() > 0:
            self.task_index = self.main_window.model.rowCount() - 1
            self.added_task = self.main_window.model.getTask(self.task_index)

    def undo(self) -> None:
        if self.added_task is not None and self.task_index is not None:
            self.main_window._delete_task_internal(self.task_index)


class DeleteTaskCommand(Command):
    """Comando para eliminar una tarea."""

    def __init__(self, main_window: MainWindow, task_index: int) -> None:
        super().__init__("eliminar tarea")
        self.main_window = main_window
        self.task_index = task_index
        self.deleted_tasks: list[Task] = []

    def execute(self) -> None:
        task = self.main_window.model.getTask(self.task_index)
        if task:
            actual_row = self.main_window.model.visible_to_actual[self.task_index]
            self.deleted_tasks = [copy.deepcopy(task)]
            if not task.is_subtask:
                subtask_count = self.main_window.count_subtasks(actual_row)
                for i in range(1, subtask_count + 1):
                    if actual_row + i < len(self.main_window.model.tasks):
                        self.deleted_tasks.append(
                            copy.deepcopy(self.main_window.model.tasks[actual_row + i])
                        )
            self.main_window._delete_task_internal(self.task_index)

    def undo(self) -> None:
        model = self.main_window.model
        insert_position = min(self.task_index, len(model.tasks))

        for i, task in enumerate(self.deleted_tasks):
            model.insertTask(task, insert_position + i)
            if i == 0 and not task.is_subtask:
                task.subtasks = []
                for j in range(1, len(self.deleted_tasks)):
                    subtask = self.deleted_tasks[j]
                    if subtask.is_subtask:
                        subtask.parent_task = task
                        task.subtasks.append(subtask)

        model.update_visible_tasks()
        model.layoutChanged.emit()
        self.main_window.update_gantt_chart()


class MoveTaskCommand(Command):
    """Comando para mover una tarea."""

    def __init__(self, main_window: MainWindow, task_index: int, direction: str) -> None:
        direction_text = "arriba" if direction == "up" else "abajo"
        super().__init__(f"mover tarea {direction_text}")
        self.main_window = main_window
        self.task_index = task_index
        self.direction = direction
        self.original_state: list[Task] | None = None

    def execute(self) -> None:
        self.original_state = copy.deepcopy(self.main_window.model.tasks)
        if self.direction == "up":
            self.main_window._move_task_up_internal(self.task_index)
        else:
            self.main_window._move_task_down_internal(self.task_index)

    def undo(self) -> None:
        if self.original_state is not None:
            self.main_window.model.tasks = copy.deepcopy(self.original_state)
            self.main_window.model.update_visible_tasks()
            self.main_window.model.layoutChanged.emit()
            self.main_window.update_gantt_chart()


class EditTaskCommand(Command):
    """Comando para editar propiedades de una tarea."""

    def __init__(
        self,
        main_window: MainWindow,
        task_index: int,
        field: str,
        old_value: str,
        new_value: str,
    ) -> None:
        super().__init__(f"editar {field}")
        self.main_window = main_window
        self.task_index = task_index
        self.field = field
        self.old_value = old_value
        self.new_value = new_value

    def execute(self) -> None:
        task = self.main_window.model.getTask(self.task_index)
        if task:
            self.main_window.model.set_data_programmatically(task, self.field, self.new_value)
            self.main_window.update_gantt_chart()
            self.main_window.set_unsaved_changes(True)

    def undo(self) -> None:
        task = self.main_window.model.getTask(self.task_index)
        if task:
            self.main_window.model.set_data_programmatically(task, self.field, self.old_value)
            self.main_window.update_gantt_chart()
            self.main_window.set_unsaved_changes(True)


class ChangeColorCommand(Command):
    """Comando para cambiar el color de una tarea."""

    def __init__(
        self,
        main_window: MainWindow,
        task_index: int,
        old_color: QColor,
        new_color: QColor,
    ) -> None:
        super().__init__("cambiar color")
        self.main_window = main_window
        self.task_index = task_index
        self.old_color = old_color
        self.new_color = new_color

    def execute(self) -> None:
        logger.debug(
            "ChangeColorCommand: task %d → %s",
            self.task_index,
            self.new_color.name(),
        )
        self.main_window._update_task_color_internal(self.task_index, self.new_color)
        self._update_ui()

    def undo(self) -> None:
        logger.debug(
            "ChangeColorCommand.undo: task %d → %s",
            self.task_index,
            self.old_color.name(),
        )
        self.main_window._update_task_color_internal(self.task_index, self.old_color)
        self._update_ui()

    def _update_ui(self) -> None:
        """Actualiza la interfaz de usuario después del cambio de color."""
        model = self.main_window.model
        if self.task_index < model.rowCount():
            index = model.index(self.task_index, 1)
            model.dataChanged.emit(index, index, [Qt.ItemDataRole.BackgroundRole])
        self.main_window.update_gantt_chart()


class DuplicateTaskCommand(Command):
    """Comando para duplicar una tarea."""

    def __init__(self, main_window: MainWindow, task_index: int) -> None:
        super().__init__("duplicar tarea")
        self.main_window = main_window
        self.task_index = task_index
        self.duplicated_tasks: list[Task] = []
        self.original_tasks: list[Task] = []

    def execute(self) -> None:
        logger.debug("DuplicateTaskCommand: duplicating task %d", self.task_index)
        self.original_tasks = self.main_window.model.tasks.copy()
        self.main_window._duplicate_task_internal(self.task_index)

        current_tasks = self.main_window.model.tasks
        self.duplicated_tasks = [t for t in current_tasks if t not in self.original_tasks]
        logger.debug("%d task(s) duplicated.", len(self.duplicated_tasks))

    def undo(self) -> None:
        logger.debug(
            "DuplicateTaskCommand.undo: removing %d duplicated task(s)",
            len(self.duplicated_tasks),
        )
        for task in self.duplicated_tasks:
            try:
                if task in self.main_window.model.tasks:
                    self.main_window.model.tasks.remove(task)
                if task in self.main_window.tasks:
                    self.main_window.tasks.remove(task)
                if hasattr(task, "parent_task") and task.parent_task:
                    if task in task.parent_task.subtasks:
                        task.parent_task.subtasks.remove(task)
            except ValueError as err:
                logger.warning("Error removing duplicated task: %s", err)

        self.main_window.model.update_visible_tasks()
        self.main_window.model.layoutChanged.emit()
        self.main_window.update_gantt_chart()


class ConvertTaskCommand(Command):
    """Comando para convertir tarea padre a subtarea o viceversa."""

    def __init__(
        self, main_window: MainWindow, task_index: int, conversion_type: str
    ) -> None:
        conversion_text = "a subtarea" if conversion_type == "to_subtask" else "a tarea padre"
        super().__init__(f"convertir {conversion_text}")
        self.main_window = main_window
        self.task_index = task_index
        self.conversion_type = conversion_type
        self.original_state: list[Task] | None = None

    def execute(self) -> None:
        self.original_state = copy.deepcopy(self.main_window.model.tasks)
        if self.conversion_type == "to_subtask":
            self.main_window._convert_to_subtask_internal(self.task_index)
        else:
            self.main_window._convert_to_parent_task_internal(self.task_index)

    def undo(self) -> None:
        if self.original_state is not None:
            self.main_window.model.tasks = copy.deepcopy(self.original_state)
            self.main_window.model.update_visible_tasks()
            self.main_window.model.layoutChanged.emit()
            self.main_window.update_gantt_chart()


class AddSubtaskCommand(Command):
    """Comando para agregar una subtarea."""

    def __init__(self, main_window: MainWindow, parent_task_index: int) -> None:
        super().__init__("agregar subtarea")
        self.main_window = main_window
        self.parent_task_index = parent_task_index
        self.added_subtask: Task | None = None
        self.parent_task: Task | None = None
        self.original_tasks: list[Task] = []

    def execute(self) -> None:
        logger.debug(
            "AddSubtaskCommand: adding subtask to task %d", self.parent_task_index
        )
        self.original_tasks = self.main_window.model.tasks.copy()

        model = self.main_window.model
        if self.parent_task_index < len(model.visible_tasks):
            self.parent_task = model.visible_tasks[self.parent_task_index]

        self.main_window._add_subtask_internal(self.parent_task_index)

        current_tasks = self.main_window.model.tasks
        for task in current_tasks:
            if task not in self.original_tasks:
                self.added_subtask = task
                logger.debug("Subtask identified: '%s'", task.name)
                break

    def undo(self) -> None:
        if self.added_subtask:
            try:
                if self.added_subtask in self.main_window.model.tasks:
                    self.main_window.model.tasks.remove(self.added_subtask)
                if self.added_subtask in self.main_window.tasks:
                    self.main_window.tasks.remove(self.added_subtask)
                if self.parent_task and self.added_subtask in self.parent_task.subtasks:
                    self.parent_task.subtasks.remove(self.added_subtask)

                self.main_window.model.update_visible_tasks()
                self.main_window.model.layoutChanged.emit()
                self.main_window.update_gantt_chart()
                logger.debug("Subtask removed successfully.")
            except Exception as err:
                logger.error("Error removing subtask: %s", err, exc_info=True)


class InsertTaskCommand(Command):
    """Comando para insertar una tarea."""

    def __init__(self, main_window: MainWindow, task_index: int) -> None:
        super().__init__("insertar tarea")
        self.main_window = main_window
        self.task_index = task_index
        self.inserted_task: Task | None = None
        self.original_tasks: list[Task] = []

    def execute(self) -> None:
        logger.debug("InsertTaskCommand: inserting at position %d", self.task_index)
        self.original_tasks = self.main_window.model.tasks.copy()
        self.main_window._insert_task_internal(self.task_index)

        current_tasks = self.main_window.model.tasks
        for task in current_tasks:
            if task not in self.original_tasks:
                self.inserted_task = task
                logger.debug("Inserted task identified: '%s'", task.name)
                break

    def undo(self) -> None:
        if self.inserted_task:
            try:
                if self.inserted_task in self.main_window.model.tasks:
                    self.main_window.model.tasks.remove(self.inserted_task)
                if self.inserted_task in self.main_window.tasks:
                    self.main_window.tasks.remove(self.inserted_task)

                self.main_window.model.update_visible_tasks()
                self.main_window.model.layoutChanged.emit()
                self.main_window.update_gantt_chart()
                logger.debug("Inserted task removed successfully.")
            except Exception as err:
                logger.error("Error undoing task insert: %s", err, exc_info=True)


class ResetColorsCommand(Command):
    """Comando para restablecer todos los colores."""

    def __init__(self, main_window: MainWindow) -> None:
        super().__init__("restablecer colores")
        self.main_window = main_window
        self.original_colors: dict[int, QColor] = {}

    def execute(self) -> None:
        for i, task in enumerate(self.main_window.model.tasks):
            self.original_colors[i] = copy.copy(task.color)

        default_color = QColor(34, 163, 159)
        for task in self.main_window.model.tasks:
            task.color = default_color

        self._update_ui()

    def undo(self) -> None:
        for i, task in enumerate(self.main_window.model.tasks):
            if i in self.original_colors:
                task.color = self.original_colors[i]
        self._update_ui()

    def _update_ui(self) -> None:
        """Actualiza la interfaz de usuario después del cambio de colores."""
        model = self.main_window.model
        model.dataChanged.emit(
            model.index(0, 1),
            model.index(model.rowCount() - 1, 1),
            [Qt.ItemDataRole.BackgroundRole],
        )
        model.dataChanged.emit(
            model.index(0, 0),
            model.index(model.rowCount() - 1, 0),
            [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.DecorationRole, Qt.ItemDataRole.UserRole],
        )
        if hasattr(self.main_window, "task_table_widget"):
            self.main_window.task_table_widget.table_view.viewport().update()

        self.main_window.update_gantt_chart()
        self.main_window.set_unsaved_changes(True)


class EditNotesCommand(Command):
    """Comando para editar notas de una tarea."""

    def __init__(
        self,
        main_window: MainWindow,
        task: Task,
        old_notes_html: str,
        new_notes_html: str,
        old_file_links: dict[str, str],
        new_file_links: dict[str, str],
    ) -> None:
        super().__init__("editar notas")
        self.main_window = main_window
        self.task = task
        self.old_notes_html = old_notes_html
        self.new_notes_html = new_notes_html
        self.old_file_links = old_file_links.copy() if old_file_links else {}
        self.new_file_links = new_file_links.copy() if new_file_links else {}

    def execute(self) -> None:
        self.task.notes_html = self.new_notes_html
        self.task.notes = self._extract_plain_text(self.new_notes_html)
        self.task.file_links = self.new_file_links.copy()
        self.main_window.update_gantt_chart()
        self.main_window.set_unsaved_changes(True)

    def undo(self) -> None:
        self.task.notes_html = self.old_notes_html
        self.task.notes = self._extract_plain_text(self.old_notes_html)
        self.task.file_links = self.old_file_links.copy()
        self.main_window.update_gantt_chart()
        self.main_window.set_unsaved_changes(True)

    def _extract_plain_text(self, html_text: str) -> str:
        """Extrae texto plano del HTML."""
        if not html_text:
            return ""
        import re
        return re.sub(re.compile("<.*?>"), "", html_text).strip()


class ToggleLinkedDurationCommand(Command):
    """Comando para activar/desactivar la vinculación con subtareas."""

    def __init__(self, main_window: MainWindow, task_index: int, enabled: bool) -> None:
        super().__init__("vincular con subtareas" if enabled else "desvincular de subtareas")
        self.main_window = main_window
        self.task_index = task_index
        self.enabled = enabled
        self.old_linked_state: bool = False
        self.old_start: str | None = None
        self.old_end: str | None = None
        self.old_duration: str | None = None

    def execute(self) -> None:
        task = self.main_window.model.getTask(self.task_index)
        if task:
            self.old_linked_state = task.linked_to_subtasks
            self.old_start = task.start_date
            self.old_end = task.end_date
            self.old_duration = task.duration

            task.linked_to_subtasks = self.enabled
            if self.enabled:
                # Al activar, guardamos los tiempos manuales actuales
                task.stored_start_date = self.old_start
                task.stored_end_date = self.old_end
                task.stored_duration = self.old_duration
                # Ajustar a subtareas
                self.main_window.model.update_parent_linked_duration(task)
            else:
                # Al desactivar, restauramos los tiempos manuales guardados anteriormente si existen
                if task.stored_start_date:
                    task.start_date = task.stored_start_date
                    task.end_date = task.stored_end_date
                    task.duration = task.stored_duration

            self._update_ui()

    def undo(self) -> None:
        task = self.main_window.model.getTask(self.task_index)
        if task:
            task.linked_to_subtasks = self.old_linked_state
            task.start_date = self.old_start
            task.end_date = self.old_end
            task.duration = self.old_duration
            self._update_ui()

    def _update_ui(self) -> None:
        self.main_window.model.layoutChanged.emit()
        self.main_window.update_gantt_chart()
        self.main_window.set_unsaved_changes(True)
