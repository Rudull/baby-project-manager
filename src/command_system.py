# command_system.py
# Sistema de comandos para deshacer/rehacer operaciones en Baby Project Manager

import copy
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QColor

class Command:
    """Clase base para todos los comandos."""

    def __init__(self, description=""):
        self.description = description

    def execute(self):
        """Ejecuta el comando."""
        raise NotImplementedError

    def undo(self):
        """Deshace el comando."""
        raise NotImplementedError

    def __str__(self):
        return self.description

class CommandManager(QObject):
    """Gestor de comandos para manejar deshacer/rehacer."""

    commandExecuted = Signal(str)
    canUndoChanged = Signal(bool)
    canRedoChanged = Signal(bool)

    def __init__(self):
        super().__init__()
        self.command_history = []
        self.current_index = -1
        self.max_history = 50  # Límite de comandos en el historial

    def execute_command(self, command):
        """Ejecuta un comando y lo añade al historial."""
        try:
            print(f"🔧 CommandManager.execute_command: Ejecutando '{command.description}'")
            command.execute()

            # Eliminar comandos posteriores al índice actual
            self.command_history = self.command_history[:self.current_index + 1]

            # Añadir el nuevo comando
            self.command_history.append(command)
            self.current_index += 1

            # Mantener el límite del historial
            if len(self.command_history) > self.max_history:
                self.command_history.pop(0)
                self.current_index -= 1

            print(f"✅ CommandManager.execute_command: '{command.description}' ejecutado exitosamente")
            print(f"📊 Historial: {len(self.command_history)} comandos, índice actual: {self.current_index}")
            self.commandExecuted.emit(command.description)
            self._emit_status_changes()

        except Exception as e:
            print(f"❌ Error ejecutando comando '{command.description}': {e}")
            import traceback
            traceback.print_exc()

    def undo(self):
        """Deshace el último comando."""
        if self.can_undo():
            try:
                command = self.command_history[self.current_index]
                print(f"↩️ CommandManager.undo: Deshaciendo '{command.description}'")
                command.undo()
                self.current_index -= 1
                print(f"✅ CommandManager.undo: '{command.description}' deshecho exitosamente")
                print(f"📊 Historial: {len(self.command_history)} comandos, índice actual: {self.current_index}")
                self._emit_status_changes()
                return True
            except Exception as e:
                print(f"❌ Error deshaciendo comando: {e}")
                import traceback
                traceback.print_exc()
                return False
        else:
            print(f"❌ CommandManager.undo: No hay comandos para deshacer")
        return False

    def redo(self):
        """Rehace el siguiente comando."""
        if self.can_redo():
            try:
                self.current_index += 1
                command = self.command_history[self.current_index]
                command.execute()
                self._emit_status_changes()
                return True
            except Exception as e:
                print(f"Error rehaciendo comando: {e}")
                self.current_index -= 1
                return False
        return False

    def can_undo(self):
        """Verifica si se puede deshacer."""
        return self.current_index >= 0

    def can_redo(self):
        """Verifica si se puede rehacer."""
        return self.current_index < len(self.command_history) - 1

    def clear(self):
        """Limpia el historial de comandos."""
        self.command_history.clear()
        self.current_index = -1
        self._emit_status_changes()

    def _emit_status_changes(self):
        """Emite señales de cambio de estado."""
        self.canUndoChanged.emit(self.can_undo())
        self.canRedoChanged.emit(self.can_redo())

    def get_undo_text(self):
        """Obtiene el texto del comando a deshacer."""
        if self.can_undo():
            return f"Deshacer {self.command_history[self.current_index].description}"
        return "Deshacer"

    def get_redo_text(self):
        """Obtiene el texto del comando a rehacer."""
        if self.can_redo():
            return f"Rehacer {self.command_history[self.current_index + 1].description}"
        return "Rehacer"

class AddTaskCommand(Command):
    """Comando para agregar una nueva tarea."""

    def __init__(self, main_window, task_data=None, editable=False):
        super().__init__("agregar tarea")
        self.main_window = main_window
        self.task_data = task_data
        self.editable = editable
        self.added_task = None
        self.task_index = None

    def execute(self):
        if self.task_data:
            # Usar datos específicos
            self.main_window.task_table_widget.add_task_to_table(
                self.task_data, self.editable
            )
        else:
            # Agregar nueva tarea por defecto
            self.main_window._add_new_task_internal()

        # Guardar referencia a la tarea agregada
        if self.main_window.model.rowCount() > 0:
            self.task_index = self.main_window.model.rowCount() - 1
            self.added_task = self.main_window.model.getTask(self.task_index)

    def undo(self):
        if self.added_task and self.task_index is not None:
            self.main_window._delete_task_internal(self.task_index)

class DeleteTaskCommand(Command):
    """Comando para eliminar una tarea."""

    def __init__(self, main_window, task_index):
        super().__init__("eliminar tarea")
        self.main_window = main_window
        self.task_index = task_index
        self.deleted_tasks = []
        self.task_structure = None

    def execute(self):
        # Guardar la estructura antes de eliminar
        task = self.main_window.model.getTask(self.task_index)
        if task:
            actual_row = self.main_window.model.visible_to_actual[self.task_index]

            # Guardar la tarea y sus subtareas
            self.deleted_tasks = [copy.deepcopy(task)]
            if not task.is_subtask:
                # Si es tarea padre, guardar subtareas
                subtask_count = self.main_window.count_subtasks(actual_row)
                for i in range(1, subtask_count + 1):
                    if actual_row + i < len(self.main_window.model.tasks):
                        subtask = copy.deepcopy(self.main_window.model.tasks[actual_row + i])
                        self.deleted_tasks.append(subtask)

            # Ejecutar eliminación
            self.main_window._delete_task_internal(self.task_index)

    def undo(self):
        # Restaurar tareas eliminadas
        model = self.main_window.model
        insert_position = min(self.task_index, len(model.tasks))

        for i, task in enumerate(self.deleted_tasks):
            model.insertTask(task, insert_position + i)

            # Restaurar relaciones padre-hijo
            if i == 0 and not task.is_subtask:
                # Tarea padre
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

    def __init__(self, main_window, task_index, direction):
        direction_text = "arriba" if direction == "up" else "abajo"
        super().__init__(f"mover tarea {direction_text}")
        self.main_window = main_window
        self.task_index = task_index
        self.direction = direction
        self.original_state = None
        self.new_state = None

    def execute(self):
        # Guardar estado original
        self.original_state = copy.deepcopy(self.main_window.model.tasks)

        # Ejecutar movimiento
        if self.direction == "up":
            self.main_window._move_task_up_internal(self.task_index)
        else:
            self.main_window._move_task_down_internal(self.task_index)

        # Guardar nuevo estado
        self.new_state = copy.deepcopy(self.main_window.model.tasks)

    def undo(self):
        # Restaurar estado original
        self.main_window.model.tasks = copy.deepcopy(self.original_state)
        self.main_window.model.update_visible_tasks()
        self.main_window.model.layoutChanged.emit()
        self.main_window.update_gantt_chart()

class EditTaskCommand(Command):
    """Comando para editar propiedades de una tarea."""

    def __init__(self, main_window, task_index, field, old_value, new_value):
        super().__init__(f"editar {field}")
        self.main_window = main_window
        self.task_index = task_index
        self.field = field
        self.old_value = old_value
        self.new_value = new_value

    def execute(self):
        task = self.main_window.model.getTask(self.task_index)
        if task:
            # Usar el método programático del modelo para evitar crear comandos recursivos
            self.main_window.model.set_data_programmatically(task, self.field, self.new_value)
            self.main_window.update_gantt_chart()
            self.main_window.set_unsaved_changes(True)

    def undo(self):
        task = self.main_window.model.getTask(self.task_index)
        if task:
            # Usar el método programático del modelo para evitar crear comandos recursivos
            self.main_window.model.set_data_programmatically(task, self.field, self.old_value)
            self.main_window.update_gantt_chart()
            self.main_window.set_unsaved_changes(True)

class ChangeColorCommand(Command):
    """Comando para cambiar el color de una tarea."""

    def __init__(self, main_window, task_index, old_color, new_color):
        super().__init__("cambiar color")
        self.main_window = main_window
        self.task_index = task_index
        self.old_color = old_color
        self.new_color = new_color

    def execute(self):
        print(f"🎨 ChangeColorCommand.execute: Cambiando color de tarea {self.task_index} a {self.new_color.name()}")
        self.main_window._update_task_color_internal(self.task_index, self.new_color)
        self._update_ui()
        print(f"🎨 Color cambiado exitosamente")

    def undo(self):
        print(f"🎨 ChangeColorCommand.undo: Restaurando color de tarea {self.task_index} a {self.old_color.name()}")
        self.main_window._update_task_color_internal(self.task_index, self.old_color)
        self._update_ui()
        print(f"🎨 Color restaurado exitosamente")

    def _update_ui(self):
        """Actualiza la interfaz de usuario después del cambio de color."""
        # Forzar actualización de la tabla
        model = self.main_window.model
        if self.task_index < model.rowCount():
            index = model.index(self.task_index, 1)
            model.dataChanged.emit(index, index, [Qt.ItemDataRole.BackgroundRole])

        # Actualizar el gantt chart
        self.main_window.update_gantt_chart()

class DuplicateTaskCommand(Command):
    """Comando para duplicar una tarea."""

    def __init__(self, main_window, task_index):
        super().__init__("duplicar tarea")
        self.main_window = main_window
        self.task_index = task_index
        self.duplicated_tasks = []
        self.original_tasks = []

    def execute(self):
        print(f"📋 DuplicateTaskCommand.execute: Iniciando duplicación de tarea {self.task_index}")

        # Guardar snapshot del estado original
        self.original_tasks = self.main_window.model.tasks.copy()
        print(f"📋 Snapshot original: {len(self.original_tasks)} tareas")

        # Ejecutar la duplicación
        self.main_window._duplicate_task_internal(self.task_index)

        # Identificar las tareas nuevas comparando con el snapshot
        current_tasks = self.main_window.model.tasks
        self.duplicated_tasks = []

        for task in current_tasks:
            if task not in self.original_tasks:
                self.duplicated_tasks.append(task)
                print(f"📋 Tarea duplicada identificada: {task.name}")

        print(f"📋 Total de tareas duplicadas: {len(self.duplicated_tasks)}")

    def undo(self):
        print(f"📋 DuplicateTaskCommand.undo: Deshaciendo duplicación")
        print(f"📋 Eliminando {len(self.duplicated_tasks)} tareas duplicadas")

        # Eliminar las tareas duplicadas
        for task in self.duplicated_tasks:
            try:
                if task in self.main_window.model.tasks:
                    print(f"📋 Eliminando tarea duplicada: {task.name}")
                    self.main_window.model.tasks.remove(task)
                    if task in self.main_window.tasks:
                        self.main_window.tasks.remove(task)
                    # Remover de relaciones padre-hijo
                    if hasattr(task, 'parent_task') and task.parent_task:
                        if hasattr(task.parent_task, 'subtasks') and task in task.parent_task.subtasks:
                            task.parent_task.subtasks.remove(task)
            except ValueError as e:
                print(f"❌ Error eliminando tarea duplicada: {e}")
                continue

        # Actualizar vista
        self.main_window.model.update_visible_tasks()
        self.main_window.model.layoutChanged.emit()
        self.main_window.update_gantt_chart()

class ConvertTaskCommand(Command):
    """Comando para convertir tarea padre a subtarea o viceversa."""

    def __init__(self, main_window, task_index, conversion_type):
        conversion_text = "a subtarea" if conversion_type == "to_subtask" else "a tarea padre"
        super().__init__(f"convertir {conversion_text}")
        self.main_window = main_window
        self.task_index = task_index
        self.conversion_type = conversion_type
        self.original_state = None

    def execute(self):
        # Guardar estado original
        self.original_state = copy.deepcopy(self.main_window.model.tasks)

        # Ejecutar conversión
        if self.conversion_type == "to_subtask":
            self.main_window._convert_to_subtask_internal(self.task_index)
        else:
            self.main_window._convert_to_parent_task_internal(self.task_index)

    def undo(self):
        # Restaurar estado original
        self.main_window.model.tasks = copy.deepcopy(self.original_state)
        self.main_window.model.update_visible_tasks()
        self.main_window.model.layoutChanged.emit()
        self.main_window.update_gantt_chart()

class AddSubtaskCommand(Command):
    """Comando para agregar una subtarea."""

    def __init__(self, main_window, parent_task_index):
        super().__init__("agregar subtarea")
        self.main_window = main_window
        self.parent_task_index = parent_task_index
        self.added_subtask = None
        self.parent_task = None
        self.original_tasks = []

    def execute(self):
        print(f"👶 AddSubtaskCommand.execute: Agregando subtarea a tarea {self.parent_task_index}")

        # Guardar snapshot del estado original
        self.original_tasks = self.main_window.model.tasks.copy()
        print(f"👶 Snapshot original: {len(self.original_tasks)} tareas")

        # Obtener referencia a la tarea padre
        if self.parent_task_index < len(self.main_window.model.visible_tasks):
            self.parent_task = self.main_window.model.visible_tasks[self.parent_task_index]

        # Ejecutar agregación de subtarea
        self.main_window._add_subtask_internal(self.parent_task_index)

        # Identificar la subtarea agregada comparando con el snapshot
        current_tasks = self.main_window.model.tasks
        for task in current_tasks:
            if task not in self.original_tasks:
                self.added_subtask = task
                print(f"👶 Subtarea agregada identificada: {task.name}")
                break

    def undo(self):
        print(f"👶 AddSubtaskCommand.undo: Deshaciendo agregación de subtarea")
        if self.added_subtask:
            try:
                print(f"👶 Eliminando subtarea: {self.added_subtask.name}")
                # Eliminar directamente del modelo
                if self.added_subtask in self.main_window.model.tasks:
                    self.main_window.model.tasks.remove(self.added_subtask)
                if self.added_subtask in self.main_window.tasks:
                    self.main_window.tasks.remove(self.added_subtask)

                # Remover de la lista de subtareas del padre
                if self.parent_task and hasattr(self.parent_task, 'subtasks'):
                    if self.added_subtask in self.parent_task.subtasks:
                        self.parent_task.subtasks.remove(self.added_subtask)

                # Actualizar vista
                self.main_window.model.update_visible_tasks()
                self.main_window.model.layoutChanged.emit()
                self.main_window.update_gantt_chart()
                print(f"👶 Subtarea eliminada exitosamente")
            except Exception as e:
                print(f"❌ Error eliminando subtarea: {e}")

class InsertTaskCommand(Command):
    """Comando para insertar una tarea."""

    def __init__(self, main_window, task_index):
        super().__init__("insertar tarea")
        self.main_window = main_window
        self.task_index = task_index
        self.inserted_task = None
        self.original_tasks = []

    def execute(self):
        print(f"📝 InsertTaskCommand.execute: Insertando tarea en posición {self.task_index}")

        # Guardar snapshot del estado original
        self.original_tasks = self.main_window.model.tasks.copy()
        print(f"📝 Snapshot original: {len(self.original_tasks)} tareas")

        # Ejecutar inserción
        self.main_window._insert_task_internal(self.task_index)

        # Identificar la tarea insertada comparando con el snapshot
        current_tasks = self.main_window.model.tasks
        for task in current_tasks:
            if task not in self.original_tasks:
                self.inserted_task = task
                print(f"📝 Tarea insertada identificada: {task.name}")
                break

    def undo(self):
        print(f"📝 InsertTaskCommand.undo: Deshaciendo inserción")
        if self.inserted_task:
            try:
                print(f"📝 Eliminando tarea insertada: {self.inserted_task.name}")
                # Eliminar directamente del modelo
                if self.inserted_task in self.main_window.model.tasks:
                    self.main_window.model.tasks.remove(self.inserted_task)
                if self.inserted_task in self.main_window.tasks:
                    self.main_window.tasks.remove(self.inserted_task)

                # Actualizar vista
                self.main_window.model.update_visible_tasks()
                self.main_window.model.layoutChanged.emit()
                self.main_window.update_gantt_chart()
                print(f"📝 Tarea insertada eliminada exitosamente")
            except Exception as e:
                print(f"❌ Error eliminando tarea insertada: {e}")

class ResetColorsCommand(Command):
    """Comando para restablecer todos los colores."""

    def __init__(self, main_window):
        super().__init__("restablecer colores")
        self.main_window = main_window
        self.original_colors = {}

    def execute(self):
        # Guardar colores originales
        for i, task in enumerate(self.main_window.model.tasks):
            self.original_colors[i] = copy.copy(task.color)

        # Restablecer colores directamente
        default_color = QColor(34, 163, 159)
        for task in self.main_window.model.tasks:
            task.color = default_color

        self._update_ui()

    def undo(self):
        # Restaurar colores originales
        for i, task in enumerate(self.main_window.model.tasks):
            if i in self.original_colors:
                task.color = self.original_colors[i]

        self._update_ui()

    def _update_ui(self):
        """Actualiza la interfaz de usuario después del cambio de colores."""
        # Actualizar vista de tabla
        model = self.main_window.model
        model.dataChanged.emit(
            model.index(0, 1),
            model.index(model.rowCount()-1, 1),
            [Qt.ItemDataRole.BackgroundRole]
        )
        # Forzar repintado de la columna 0 (botón de estado)
        model.dataChanged.emit(
            model.index(0, 0),
            model.index(model.rowCount()-1, 0),
            [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.DecorationRole, Qt.ItemDataRole.UserRole]
        )
        # Forzar actualización visual de la tabla para que el botón de estado cambie de inmediato
        if hasattr(self.main_window, "task_table_widget"):
            table_view = self.main_window.task_table_widget.table_view
            table_view.viewport().update()

        # Actualizar gantt chart
        self.main_window.update_gantt_chart()

        # Marcar cambios sin guardar
        self.main_window.set_unsaved_changes(True)

class EditNotesCommand(Command):
    """Comando para editar notas de una tarea."""

    def __init__(self, main_window, task, old_notes_html, new_notes_html, old_file_links, new_file_links):
        super().__init__("editar notas")
        self.main_window = main_window
        self.task = task
        self.old_notes_html = old_notes_html
        self.new_notes_html = new_notes_html
        self.old_file_links = old_file_links.copy() if old_file_links else {}
        self.new_file_links = new_file_links.copy() if new_file_links else {}

    def execute(self):
        self.task.notes_html = self.new_notes_html
        self.task.notes = self._extract_plain_text(self.new_notes_html)
        self.task.file_links = self.new_file_links.copy()
        self.main_window.update_gantt_chart()
        self.main_window.set_unsaved_changes(True)

    def undo(self):
        self.task.notes_html = self.old_notes_html
        self.task.notes = self._extract_plain_text(self.old_notes_html)
        self.task.file_links = self.old_file_links.copy()
        self.main_window.update_gantt_chart()
        self.main_window.set_unsaved_changes(True)

    def _extract_plain_text(self, html_text):
        """Extrae texto plano del HTML."""
        if not html_text:
            return ""
        # Remover tags HTML básicos
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', html_text).strip()
