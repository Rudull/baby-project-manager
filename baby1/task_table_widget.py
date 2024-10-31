# Este archivo contendrá la clase TaskTableWidget, que maneja la vista de tabla de tareas, incluyendo la configuración de delegados personalizados, manejo de menús contextuales, y la interacción con el modelo de datos (TaskTableModel).
# task_table_widget.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QPushButton, QMenu, QFileDialog,
    QMessageBox, QHeaderView, QShortcut, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal, QModelIndex, QPoint
from PySide6.QtGui import QKeySequence, QContextMenuEvent, QColor
from models import TaskTableModel, Task
from delegates import LineEditDelegate, DateEditDelegate, SpinBoxDelegate, StateButtonDelegate
from hyperlink_text_edit import HyperlinkTextEdit
from floating_menu import FloatingTaskMenu
import os
import sys
import math
import ast

class TaskTableWidget(QWidget):
    """
    Widget que contiene y maneja la vista de tabla de tareas.
    """
    taskDataChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent

        # Configuración del diseño
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Inicialización del modelo de datos
        self.model = TaskTableModel()
        self.table_view = QTableView()
        self.table_view.setModel(self.model)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table_view.setEditTriggers(QTableView.EditTrigger.DoubleClicked | QTableView.EditTrigger.SelectedClicked)
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_context_menu)

        # Configuración de las cabeceras
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.verticalHeader().setDefaultSectionSize(self.main_window.ROW_HEIGHT)
        self.table_view.verticalHeader().setVisible(False)

        # Asignación de delegados personalizados a las columnas
        self.table_view.setItemDelegateForColumn(0, StateButtonDelegate(self.table_view, main_window=self.main_window))
        self.table_view.setItemDelegateForColumn(1, LineEditDelegate(self.table_view))
        self.table_view.setItemDelegateForColumn(2, DateEditDelegate(self.table_view))
        self.table_view.setItemDelegateForColumn(3, DateEditDelegate(self.table_view))
        self.table_view.setItemDelegateForColumn(4, SpinBoxDelegate(minimum=1, maximum=100, parent=self.table_view))
        self.table_view.setItemDelegateForColumn(5, SpinBoxDelegate(minimum=0, maximum=100, parent=self.table_view))

        # Conectar la señal del delegado de botones de estado
        state_delegate = self.table_view.itemDelegateForColumn(0)
        if isinstance(state_delegate, StateButtonDelegate):
            state_delegate.stateButtonClicked.connect(self.handle_state_button_clicked)

        # Añadir la tabla al diseño
        self.main_layout.addWidget(self.table_view)

        # Configuración de los atajos de teclado
        self.setup_shortcuts()

        # Configuración de la edición rápida de notas con hipervínculos
        self.setup_notes_editor()

        # Actualizar la altura de todas las filas
        self.adjust_all_row_heights()

        # Conectar señales del modelo
        self.model.layoutChanged.connect(self.on_model_layout_changed)
        self.model.dataChanged.connect(self.on_model_data_changed)

    def setup_shortcuts(self):
        """
        Configura los atajos de teclado para la tabla de tareas.
        """
        # Atajo para agregar una nueva tarea
        add_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        add_shortcut.activated.connect(self.add_new_task)

        # Atajo para eliminar la tarea seleccionada
        delete_shortcut = QShortcut(QKeySequence("Delete"), self)
        delete_shortcut.activated.connect(self.delete_selected_task)

    def setup_notes_editor(self):
        """
        Configura el editor de notas con hipervínculos.
        """
        # Esta función puede ser implementada según las necesidades específicas.
        # Por ejemplo, si cada tarea tiene un editor de notas, podrías integrar
        # el widget HyperlinkTextEdit aquí o en una ventana flotante.
        pass

    def on_model_layout_changed(self):
        """
        Maneja el cambio de layout del modelo.
        """
        self.main_window.update_gantt_chart()
        self.main_window.set_unsaved_changes(True)

    def on_model_data_changed(self, topLeft, bottomRight, roles):
        """
        Maneja el cambio de datos en el modelo.
        """
        self.main_window.update_gantt_chart()
        self.main_window.set_unsaved_changes(True)

    def handle_state_button_clicked(self, row):
        """
        Maneja el clic en el botón de estado de una tarea.
    
        Args:
            row (int): Índice visible de la fila de la tarea.
        """
        task = self.model.getTask(row)
        if task:
            if task.has_subtasks():
                task.is_collapsed = not task.is_collapsed
                self.model.update_visible_tasks()
                self.model.layoutChanged.emit()
                self.main_window.update_gantt_chart()
            else:
                # Aquí podrías implementar otras acciones de estado si es necesario
                pass
            self.main_window.set_unsaved_changes(True)

    def show_context_menu(self, position):
        """
        Muestra el menú contextual para la tarea en la posición dada.
    
        Args:
            position (QPoint): Posición del clic.
        """
        index = self.table_view.indexAt(position)
        if not index.isValid():
            return

        row = index.row()
        task = self.model.getTask(row)
        if not task:
            return

        menu = QMenu(self)
        duplicate_action = menu.addAction("Duplicar")
        if not task.is_subtask:
            insert_action = menu.addAction("Insertar")
        move_up_action = menu.addAction("Mover arriba")
        move_down_action = menu.addAction("Mover abajo")
        if not task.is_subtask:
            add_subtask_action = menu.addAction("Agregar subtarea")
        delete_action = menu.addAction("Eliminar")
        reset_color_action = menu.addAction("Color por defecto")

        action = menu.exec(self.table_view.viewport().mapToGlobal(position))

        if action:
            self.handle_context_menu_action(action, row, task)

    def handle_context_menu_action(self, action, row, task):
        """
        Maneja la acción seleccionada en el menú contextual.
    
        Args:
            action (QAction): Acción seleccionada.
            row (int): Índice visible de la fila de la tarea.
            task (Task): Tarea correspondiente.
        """
        action_text = action.text()
        if action_text == "Duplicar":
            self.duplicate_task(row)
        elif action_text == "Insertar" and not task.is_subtask:
            self.insert_task(row)
        elif action_text == "Mover arriba":
            self.move_task_up(row)
        elif action_text == "Mover abajo":
            self.move_task_down(row)
        elif action_text == "Agregar subtarea" and not task.is_subtask:
            self.add_subtask(row)
        elif action_text == "Eliminar":
            self.delete_task(row)
        elif action_text == "Color por defecto":
            self.reset_task_color(row)

    def duplicate_task(self, row):
        """
        Duplica una tarea en el modelo.
    
        Args:
            row (int): Índice visible de la fila de la tarea a duplicar.
        """
        model = self.model
        if 0 <= row < model.rowCount():
            task = model.getTask(row)
            if task:
                duplicated_task = Task(
                    name=f"{task.name} (copia)",
                    start_date=task.start_date,
                    end_date=task.end_date,
                    duration=task.duration,
                    dedication=task.dedication,
                    color=QColor(task.color),
                    notes=task.notes,
                    notes_html=task.notes_html,
                    file_links=task.file_links.copy()
                )
                duplicated_task.is_subtask = task.is_subtask
                duplicated_task.parent_task = task.parent_task
                duplicated_task.is_editing = False
                duplicated_task.is_collapsed = False

                if task.is_subtask:
                    # Insertar la subtarea duplicada después de la original
                    actual_row = model.visible_to_actual[row]
                    insert_index = actual_row + 1
                    model.insertTask(duplicated_task, insert_index)
                    if duplicated_task.parent_task:
                        duplicated_task.parent_task.subtasks.append(duplicated_task)
                else:
                    # Insertar la tarea duplicada después de todas sus subtareas
                    actual_row = model.visible_to_actual[row]
                    total_subtasks = self.count_subtasks(actual_row)
                    insert_index = actual_row + total_subtasks + 1
                    model.insertTask(duplicated_task, insert_index)
                    if task.subtasks:
                        duplicated_task.subtasks = []
                        subtask_insert_index = insert_index + 1
                        for subtask in task.subtasks:
                            duplicated_subtask = Task(
                                name=f"{subtask.name} (copia)",
                                start_date=subtask.start_date,
                                end_date=subtask.end_date,
                                duration=subtask.duration,
                                dedication=subtask.dedication,
                                color=QColor(subtask.color),
                                notes=subtask.notes,
                                notes_html=subtask.notes_html,
                                file_links=subtask.file_links.copy()
                            )
                            duplicated_subtask.is_subtask = True
                            duplicated_subtask.parent_task = duplicated_task
                            duplicated_subtask.is_editing = False
                            duplicated_subtask.is_collapsed = False

                            duplicated_task.subtasks.append(duplicated_subtask)
                            model.insertTask(duplicated_subtask, subtask_insert_index)
                            subtask_insert_index += 1

                model.update_visible_tasks()
                model.layoutChanged.emit()
                self.main_window.update_gantt_chart()
                self.main_window.update_shared_scrollbar_range()
                self.main_window.set_unsaved_changes(True)

                # Seleccionar y editar la tarea duplicada
                new_visible_row = model.actual_to_visible.get(insert_index)
                if new_visible_row is not None and new_visible_row < model.rowCount():
                    self.table_view.selectRow(new_visible_row)
                    self.table_view.scrollTo(model.index(new_visible_row, 0))
                    self.table_view.edit(model.index(new_visible_row, 1))  # Columna "Nombre"

    def insert_task(self, row):
        """
        Inserta una nueva tarea en el modelo.
    
        Args:
            row (int): Índice visible de la fila donde insertar.
        """
        model = self.model
        if row < len(model.visible_to_actual):
            actual_row = model.visible_to_actual[row]
            task = model.tasks[actual_row]
            if task:
                if task.is_subtask:
                    # Insertar después de todas las subtareas del padre
                    parent_task = task.parent_task
                    parent_actual_index = model.tasks.index(parent_task)
                    insert_index = parent_actual_index + 1
                    while insert_index < len(model.tasks) and model.tasks[insert_index].is_subtask:
                        insert_index += 1
                elif task.has_subtasks():
                    # Insertar después de todas las subtareas existentes
                    insert_index = actual_row + self.count_subtasks(actual_row) + 1
                else:
                    # Insertar en la siguiente posición
                    insert_index = actual_row + 1
        else:
            # Insertar al final si el índice está fuera de rango
            insert_index = len(model.tasks)

        # Crear una nueva tarea con valores por defecto
        new_task = Task(
            name="Nueva Tarea",
            start_date=QDate.currentDate().toString("dd/MM/yyyy"),
            end_date=QDate.currentDate().toString("dd/MM/yyyy"),
            duration="1",
            dedication="40",
            color=QColor(34, 163, 159),
            notes=""
        )
        new_task.is_editing = False
        new_task.is_collapsed = False

        # Insertar la nueva tarea
        model.insertTask(new_task, insert_index)
        model.update_visible_tasks()
        model.layoutChanged.emit()
        self.main_window.update_gantt_chart()
        self.main_window.update_shared_scrollbar_range()
        self.main_window.set_unsaved_changes(True)

        # Seleccionar y editar la nueva tarea
        new_visible_row = model.actual_to_visible.get(insert_index)
        if new_visible_row is not None and new_visible_row < model.rowCount():
            self.table_view.selectRow(new_visible_row)
            self.table_view.scrollTo(model.index(new_visible_row, 0))
            self.table_view.edit(model.index(new_visible_row, 1))  # Columna "Nombre"

    def delete_selected_task(self):
        """
        Elimina la tarea actualmente seleccionada.
        """
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if selected_indexes:
            row = selected_indexes[0].row()
            self.delete_task(row)

    def delete_task(self, row):
        """
        Elimina una tarea del modelo.
    
        Args:
            row (int): Índice visible de la fila de la tarea a eliminar.
        """
        model = self.model
        if 0 <= row < model.rowCount():
            task = model.getTask(row)
            if task:
                confirm = QMessageBox.question(
                    self,
                    "Eliminar Tarea",
                    f"¿Está seguro de que desea eliminar la tarea '{task.name}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if confirm == QMessageBox.StandardButton.Yes:
                    actual_row = model.visible_to_actual[row]

                    if task.is_subtask and task.parent_task:
                        # Eliminar la subtarea de la lista de subtareas del padre
                        task.parent_task.subtasks.remove(task)

                    elif not task.is_subtask:
                        # Si es una tarea padre, eliminarla y todas sus subtareas
                        total_subtasks = self.count_subtasks(actual_row)
                        for _ in range(total_subtasks + 1):
                            del model.tasks[actual_row]

                    # Actualizar las tareas visibles y emitir señales
                    model.update_visible_tasks()
                    model.layoutChanged.emit()

                    # Actualizar la estructura de datos en la ventana principal
                    self.main_window.update_task_structure()

                    # Actualizar la interfaz de usuario
                    self.main_window.update_gantt_chart()
                    self.main_window.update_shared_scrollbar_range()
                    self.main_window.set_unsaved_changes(True)

                    # Seleccionar la siguiente tarea si existe
                    if model.rowCount() > 0:
                        new_row = min(row, model.rowCount() - 1)
                        self.table_view.selectRow(new_row)
                        self.table_view.scrollTo(model.index(new_row, 0))
                    else:
                        self.table_view.clearSelection()
                        self.main_window.update_gantt_highlight(None)

    def add_new_task(self):
        """
        Añade una nueva tarea al modelo.
        """
        model = self.model
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
        new_task = Task(
            name=task_data['NAME'],
            start_date=task_data['START'],
            end_date=task_data['END'],
            duration=task_data['DURATION'],
            dedication=task_data['DEDICATION'],
            color=QColor(task_data['COLOR']),
            notes=task_data['NOTES']
        )
        new_task.is_editing = True  # Iniciar en modo edición
        new_task.is_collapsed = False

        # Insertar la nueva tarea al final
        model.insertTask(new_task)
        model.update_visible_tasks()
        model.layoutChanged.emit()
        self.main_window.update_gantt_chart()
        self.main_window.update_shared_scrollbar_range()
        self.main_window.set_unsaved_changes(True)

        # Seleccionar y editar la nueva tarea
        new_visible_row = model.actual_to_visible.get(len(model.tasks) - 1)
        if new_visible_row is not None and new_visible_row < model.rowCount():
            self.table_view.selectRow(new_visible_row)
            self.table_view.scrollTo(model.index(new_visible_row, 0))
            self.table_view.edit(model.index(new_visible_row, 1))  # Columna "Nombre"

    def count_subtasks(self, actual_row):
        """
        Cuenta cuántas subtareas tiene una tarea padre.
    
        Args:
            actual_row (int): Índice real de la tarea padre en la lista de tareas.
    
        Returns:
            int: Número de subtareas.
        """
        count = 0
        for i in range(actual_row + 1, len(self.model.tasks)):
            if self.model.tasks[i].is_subtask:
                count += 1
            else:
                break
        return count

    def add_subtask(self, parent_visible_row):
        """
        Añade una subtarea a una tarea padre.
    
        Args:
            parent_visible_row (int): Índice visible de la fila de la tarea padre.
        """
        model = self.model
        if 0 <= parent_visible_row < model.rowCount():
            parent_task = model.getTask(parent_visible_row)
            if parent_task and not parent_task.is_subtask:
                # Crear una nueva subtarea
                subtask = Task(
                    name=f"Subtarea de {parent_task.name}",
                    start_date=parent_task.start_date,
                    end_date=parent_task.end_date,
                    duration=parent_task.duration,
                    dedication=parent_task.dedication,
                    color=parent_task.color,
                    notes=""
                )
                subtask.is_subtask = True
                subtask.parent_task = parent_task
                subtask.is_editing = True  # Iniciar en modo edición
                subtask.is_collapsed = False

                # Insertar la subtarea después de todas las subtareas existentes del padre
                actual_parent_index = model.visible_to_actual[parent_visible_row]
                insert_index = actual_parent_index + 1 + self.count_subtasks(actual_parent_index)

                model.insertTask(subtask, insert_index)
                parent_task.subtasks.append(subtask)
                model.update_visible_tasks()
                model.layoutChanged.emit()
                self.main_window.update_gantt_chart()
                self.main_window.update_shared_scrollbar_range()
                self.main_window.set_unsaved_changes(True)

                # Seleccionar y editar la subtarea
                new_visible_row = model.actual_to_visible.get(insert_index)
                if new_visible_row is not None and new_visible_row < model.rowCount():
                    self.table_view.selectRow(new_visible_row)
                    self.table_view.scrollTo(model.index(new_visible_row, 0))
                    self.table_view.edit(model.index(new_visible_row, 1))  # Columna "Nombre"

    def move_task_up(self, row):
        """
        Mueve una tarea hacia arriba en el modelo.
    
        Args:
            row (int): Índice visible de la fila de la tarea a mover.
        """
        model = self.model
        if row <= 0:
            return  # Ya está en la primera posición

        actual_row = model.visible_to_actual[row]
        task = model.tasks[actual_row]
        if not task:
            return

        if not task.is_subtask:
            # Mover tarea padre junto con sus subtareas
            block_size = 1 + self.count_subtasks(actual_row)
            if actual_row - block_size < 0:
                return  # No hay suficiente espacio para mover hacia arriba

            # Intercambiar bloques
            target_row = actual_row - block_size
            moving_block = model.tasks[actual_row:actual_row + block_size]
            target_block = model.tasks[target_row:target_row + block_size]

            model.beginResetModel()
            model.tasks[target_row:target_row + block_size] = moving_block
            model.tasks[target_row + block_size:target_row + 2 * block_size] = target_block
            model.update_visible_tasks()
            model.endResetModel()

            model.layoutChanged.emit()
            self.main_window.update_gantt_chart()
            self.main_window.update_shared_scrollbar_range()
            self.main_window.set_unsaved_changes(True)

            # Seleccionar la tarea en la nueva posición
            new_visible_row = model.actual_to_visible.get(target_row)
            if new_visible_row is not None and new_visible_row < model.rowCount():
                self.table_view.selectRow(new_visible_row)
                self.table_view.scrollTo(model.index(new_visible_row, 0))

    def move_task_down(self, row):
        """
        Mueve una tarea hacia abajo en el modelo.
    
        Args:
            row (int): Índice visible de la fila de la tarea a mover.
        """
        model = self.model
        if row >= model.rowCount() - 1:
            return  # Ya está en la última posición

        actual_row = model.visible_to_actual[row]
        task = model.tasks[actual_row]
        if not task:
            return

        if not task.is_subtask:
            # Mover tarea padre junto con sus subtareas
            block_size = 1 + self.count_subtasks(actual_row)
            target_row = actual_row + block_size
            if target_row + block_size > len(model.tasks):
                return  # No hay suficiente espacio para mover hacia abajo

            # Intercambiar bloques
            moving_block = model.tasks[actual_row:actual_row + block_size]
            target_block = model.tasks[target_row:target_row + block_size]

            model.beginResetModel()
            model.tasks[actual_row:actual_row + 2 * block_size] = target_block + moving_block
            model.update_visible_tasks()
            model.endResetModel()

            model.layoutChanged.emit()
            self.main_window.update_gantt_chart()
            self.main_window.update_shared_scrollbar_range()
            self.main_window.set_unsaved_changes(True)

            # Seleccionar la tarea en la nueva posición
            new_visible_row = model.actual_to_visible.get(target_row)
            if new_visible_row is not None and new_visible_row < model.rowCount():
                self.table_view.selectRow(new_visible_row)
                self.table_view.scrollTo(model.index(new_visible_row, 0))

    def reset_task_color(self, row):
        """
        Restablece el color de una tarea a su color por defecto.
    
        Args:
            row (int): Índice visible de la fila de la tarea.
        """
        model = self.model
        if 0 <= row < model.rowCount():
            task = model.getTask(row)
            if task:
                default_color = QColor(34, 163, 159)
                self.main_window.update_task_color(row, default_color)

    def update_task_color(self, row, color):
        """
        Actualiza el color de una tarea.
    
        Args:
            row (int): Índice visible de la fila de la tarea.
            color (QColor): Nuevo color.
        """
        model = self.model
        if 0 <= row < model.rowCount():
            task = model.getTask(row)
            if task:
                task.color = color
                # Emitir señal para actualizar la vista
                index = model.index(row, 1)
                model.dataChanged.emit(index, index, [Qt.ItemDataRole.BackgroundRole])
                self.main_window.update_gantt_chart()
                self.main_window.set_unsaved_changes(True)

    def duplicate_task(self, row):
        """
        Duplica una tarea en el modelo.
    
        Args:
            row (int): Índice visible de la fila de la tarea a duplicar.
        """
        self.handle_context_menu_action(self.table_view.itemDelegateForColumn(0), row, self.model.getTask(row))

    def adjust_all_row_heights(self):
        """
        Ajusta la altura de todas las filas de la tabla según ROW_HEIGHT.
        """
        for row in range(self.model.rowCount()):
            self.table_view.setRowHeight(row, self.main_window.ROW_HEIGHT)

    def count_subtasks(self, actual_row):
        """
        Cuenta cuántas subtareas tiene una tarea padre.
    
        Args:
            actual_row (int): Índice real de la tarea padre en la lista de tareas.
    
        Returns:
            int: Número de subtareas.
        """
        count = 0
        for i in range(actual_row + 1, len(self.model.tasks)):
            if self.model.tasks[i].is_subtask:
                count += 1
            else:
                break
        return count

    def update_shared_scrollbar_range(self):
        """
        Actualiza el rango del scrollbar compartido basado en el número de tareas visibles.
        """
        total_tasks = self.model.rowCount()
        visible_tasks = self.calculate_visible_tasks()

        max_scroll = max(total_tasks - visible_tasks, 0)

        self.main_window.shared_scrollbar.setRange(0, max_scroll)
        self.main_window.shared_scrollbar.setPageStep(visible_tasks)

        if total_tasks > visible_tasks:
            self.main_window.shared_scrollbar.setEnabled(True)
        else:
            self.main_window.shared_scrollbar.setEnabled(False)
            self.main_window.shared_scrollbar.setValue(0)
            self.main_window.gantt_chart.set_vertical_offset(0)

    def calculate_visible_tasks(self):
        """
        Calcula cuántas filas son visibles en la tabla y el gráfico de Gantt.
    
        Returns:
            int: Número de tareas visibles.
        """
        visible_height = self.table_view.viewport().height()
        row_height = self.main_window.ROW_HEIGHT
        return math.ceil(visible_height / row_height)

    def sync_scroll(self, value):
        """
        Sincroniza el desplazamiento entre la tabla y el gráfico de Gantt.
    
        Args:
            value (int): Nuevo valor del scrollbar.
        """
        self.main_window.gantt_chart.set_vertical_offset(value * self.main_window.ROW_HEIGHT)

    def on_task_color_changed(self, row, color):
        """
        Slot para manejar el cambio de color de una tarea.
    
        Args:
            row (int): Índice visible de la fila de la tarea.
            color (QColor): Nuevo color.
        """
        self.update_task_color(row, color)

    def handle_context_menu_action(self, action, row, task):
        """
        Maneja la acción seleccionada en el menú contextual.
    
        Args:
            action (QAction): Acción seleccionada.
            row (int): Índice visible de la fila de la tarea.
            task (Task): Tarea correspondiente.
        """
        action_text = action.text()
        if action_text == "Duplicar":
            self.duplicate_task(row)
        elif action_text == "Insertar" and not task.is_subtask:
            self.insert_task(row)
        elif action_text == "Mover arriba":
            self.move_task_up(row)
        elif action_text == "Mover abajo":
            self.move_task_down(row)
        elif action_text == "Agregar subtarea" and not task.is_subtask:
            self.add_subtask(row)
        elif action_text == "Eliminar":
            self.delete_task(row)
        elif action_text == "Color por defecto":
            self.reset_task_color(row)

    def save_tasks_to_file(self, file_path):
        """
        Guarda las tareas en un archivo BPM.
    
        Args:
            file_path (str): Ruta del archivo donde guardar.
    
        Returns:
            bool: True si se guardó exitosamente, False en caso contrario.
        """
        try:
            tasks_data = []
            for task in self.model.tasks:
                task_dict = {
                    'name': task.name,
                    'start_date': task.start_date,
                    'end_date': task.end_date,
                    'duration': task.duration,
                    'dedication': task.dedication,
                    'color': task.color.name(),
                    'notes': task.notes,
                    'is_subtask': task.is_subtask,
                    'parent_task': task.parent_task.name if task.parent_task else None,
                    'file_links': task.file_links
                }
                tasks_data.append(task_dict)
            with open(file_path, 'w') as f:
                f.write(str(tasks_data))
            return True
        except Exception as e:
            QMessageBox.warning(self, "Error al guardar", f"No se pudieron guardar las tareas: {str(e)}")
            return False

    def load_tasks_from_file(self, file_path):
        """
        Carga las tareas desde un archivo BPM.
    
        Args:
            file_path (str): Ruta del archivo desde donde cargar.
    
        Returns:
            bool: True si se cargó exitosamente, False en caso contrario.
        """
        try:
            with open(file_path, 'r') as f:
                tasks_data = ast.literal_eval(f.read())
            self.model.beginResetModel()
            self.model.tasks = []
            task_lookup = {}
            for task_dict in tasks_data:
                task = Task(
                    name=task_dict['name'],
                    start_date=task_dict['start_date'],
                    end_date=task_dict['end_date'],
                    duration=task_dict['duration'],
                    dedication=task_dict['dedication'],
                    color=QColor(task_dict['color']),
                    notes=task_dict['notes'],
                    file_links=task_dict.get('file_links', {})
                )
                task.is_subtask = task_dict.get('is_subtask', False)
                self.model.tasks.append(task)
                task_lookup[task.name] = task

            # Asignar tareas padres a las subtareas
            for task_dict in tasks_data:
                if task_dict.get('is_subtask', False):
                    parent_name = task_dict.get('parent_task')
                    if parent_name and parent_name in task_lookup:
                        task = task_lookup[task_dict['name']]
                        parent_task = task_lookup[parent_name]
                        task.parent_task = parent_task
                        parent_task.subtasks.append(task)

            self.model.update_visible_tasks()
            self.model.endResetModel()
            self.model.layoutChanged.emit()
            self.main_window.update_task_structure()
            self.main_window.update_gantt_chart()
            self.main_window.update_shared_scrollbar_range()
            self.main_window.set_unsaved_changes(False)
            return True
        except Exception as e:
            QMessageBox.warning(self, "Error al cargar", f"No se pudieron cargar las tareas: {str(e)}")
            return False

    def save_file(self):
        """
        Guarda las tareas en un archivo BPM seleccionado por el usuario.
    
        Returns:
            bool: True si se guardó exitosamente, False en caso contrario.
        """
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar tareas",
            "",
            "Baby Project Manager Files (*.bpm)"
        )
        if file_path:
            if not file_path.endswith('.bpm'):
                file_path += '.bpm'
            return self.save_tasks_to_file(file_path)
        return False

    def load_file(self):
        """
        Carga las tareas desde un archivo BPM seleccionado por el usuario.
    
        Returns:
            bool: True si se cargó exitosamente, False en caso contrario.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Cargar tareas",
            "",
            "Baby Project Manager Files (*.bpm)"
        )
        if file_path:
            return self.load_tasks_from_file(file_path)
        return False

    def set_unsaved_changes(self, value):
        """
        Marca si hay cambios sin guardar.
    
        Args:
            value (bool): Nuevo estado de cambios sin guardar.
        """
        self.main_window.set_unsaved_changes(value)

    def update_gantt_chart(self):
        """
        Actualiza el diagrama de Gantt en la ventana principal.
        """
        self.main_window.update_gantt_chart()

    def update_shared_scrollbar_range(self):
        """
        Actualiza el rango del scrollbar compartido en la ventana principal.
        """
        self.main_window.update_shared_scrollbar_range()

    def update_task_structure(self):
        """
        Actualiza la estructura de tareas en la ventana principal.
        """
        self.main_window.update_task_structure()

    def quick_save(self):
        """
        Guarda rápidamente las tareas en el archivo actual.
        """
        if self.main_window.current_file_path:
            if self.save_tasks_to_file(self.main_window.current_file_path):
                self.set_unsaved_changes(False)
        else:
            self.save_file()

    def print_task_table_contents(self):
        """
        Imprime el contenido de la tabla de tareas para depuración.
        """
        print("Task Table Contents:")
        for task in self.model.tasks:
            print(f"Task: Name={task.name}, Task={task}")

    def wheelEvent(self, event):
        """
        Maneja el evento de rueda del ratón para la tabla.
        """
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            self.main_window.wheel_accumulator += delta

            if self.main_window.wheel_accumulator >= self.main_window.wheel_threshold:
                self.main_window.zoom_in_view()
                self.main_window.wheel_accumulator = 0  # Reiniciar después de zoom in
            elif self.main_window.wheel_accumulator <= -self.main_window.wheel_threshold:
                self.main_window.zoom_out_view()
                self.main_window.wheel_accumulator = 0  # Reiniciar después de zoom out

            event.accept()
        else:
            super().wheelEvent(event)
