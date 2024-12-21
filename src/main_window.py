#main_window.py
#1
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
    QApplication, QMainWindow, QWidget, QVBoxLayout, QGridLayout,
    QScrollBar, QMessageBox, QMenu, QSizePolicy
)
from PySide6.QtGui import (
    QColor, QKeySequence, QShortcut, QWheelEvent
)
from PySide6.QtCore import (
    Qt, QDate, QTimer, Signal, QModelIndex, QEvent
)

from gantt_views import GanttWidget
from models import Task, TaskTableModel
from table_views import TaskTableWidget
from about_dialog import AboutDialog
from config_manager import ConfigManager

class MainWindow(QMainWindow):
    ROW_HEIGHT = 25

    def __init__(self):
        super().__init__()

        # Inicializar el gestor de configuración
        self.config = ConfigManager()

        # Cargar geometría de la ventana
        self.resize(
            int(self.config.get('Window', 'width')),
            int(self.config.get('Window', 'height'))
        )
        self.move(
            int(self.config.get('Window', 'pos_x')),
            int(self.config.get('Window', 'pos_y'))
        )

        self.unsaved_changes = False
        self.base_title = "Baby project manager"
        self.setWindowTitle(self.base_title)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMinMaxButtonsHint)
        self.setMinimumSize(800, 600)  # Tamaño mínimo
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

        self.set_unsaved_changes(False)

        # Atajo de teclado para guardar
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.quick_save)

        # Instalar el filtro de eventos al final del __init__
        self.installEventFilter(self)

        # Cargar el último archivo usado
        QTimer.singleShot(0, self.load_last_file)

    def load_last_file(self):
        """Carga el último archivo usado si existe."""
        last_file = self.config.get_last_file()
        if last_file:
            self.task_table_widget.load_tasks_from_file(last_file)

    def copy_current_notes(self):
        pass  # Método vacío

    def paste_to_current_notes(self):
        pass  # Método vacío

    def copy_task_notes(self, from_task, to_task):
        # Usar el método modificado de la clase Task
        to_task.copy_notes_from(from_task)

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
            convert_to_subtask_action = menu.addAction("Convertir en subtarea")
            add_subtask_action = menu.addAction("Agregar subtarea")
        else:
            convert_to_parent_action = menu.addAction("Convertir en tarea padre")
        delete_action = menu.addAction("Eliminar")
        reset_color_action = menu.addAction("Color por defecto")
        menu.addSeparator()
        copy_notes_action = menu.addAction("Copiar notas")
        paste_notes_action = menu.addAction("Pegar notas")
        paste_notes_action.setEnabled(hasattr(self, '_copied_notes'))

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
        elif action_text == "Convertir en subtarea" and not task.is_subtask:
            self.convert_to_subtask(task_index)
        elif action_text == "Convertir en tarea padre" and task.is_subtask:
            self.convert_to_parent_task(task_index)
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
        elif action_text == "Copiar notas":
            self._copied_notes = task
        elif action_text == "Pegar notas":
            if hasattr(self, '_copied_notes') and self._copied_notes:
                task.copy_notes_from(self._copied_notes)
                self.set_unsaved_changes(True)

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
                        notes_html=task.notes_html,
                        file_links=task.file_links.copy()
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

    def convert_to_subtask(self, task_index):
        model = self.model
        if task_index < len(model.visible_to_actual):
            actual_row = model.visible_to_actual[task_index]
            task = model.tasks[actual_row]

            if task and not task.is_subtask:
                # Buscar la tarea padre anterior
                prev_parent_index = actual_row - 1
                while prev_parent_index >= 0 and model.tasks[prev_parent_index].is_subtask:
                    prev_parent_index -= 1

                if prev_parent_index >= 0:
                    parent_task = model.tasks[prev_parent_index]
                    # Convertir la tarea en subtarea
                    task.is_subtask = True
                    task.parent_task = parent_task
                    parent_task.subtasks.append(task)

                    # Mover todas las subtareas existentes
                    subtasks = task.subtasks
                    task.subtasks = []

                    # Si la tarea tenía subtareas, transferirlas al nuevo padre
                    for subtask in subtasks:
                        subtask.parent_task = parent_task
                        parent_task.subtasks.append(subtask)

                    # Actualizar el modelo
                    model.update_visible_tasks()
                    model.layoutChanged.emit()
                    self.update_gantt_chart()
                    self.set_unsaved_changes(True)

    def convert_to_parent_task(self, task_index):
        model = self.model
        if task_index < len(model.visible_to_actual):
            actual_row = model.visible_to_actual[task_index]
            task = model.tasks[actual_row]

            if task and task.is_subtask:
                # Guardar el padre actual
                current_parent = task.parent_task

                # Quitar la tarea de la lista de subtareas del padre actual
                if current_parent:
                    current_parent.subtasks.remove(task)

                # Convertir en tarea padre
                task.is_subtask = False
                task.parent_task = None
                task.subtasks = []
                task.is_collapsed = False

                # Encontrar el último índice del bloque actual de tareas
                last_block_index = actual_row
                while last_block_index + 1 < len(model.tasks):
                    next_task = model.tasks[last_block_index + 1]
                    if not next_task.is_subtask:
                        break
                    last_block_index += 1

                # Mover la tarea al final del último bloque
                model.tasks.remove(task)
                model.tasks.insert(last_block_index , task)

                # Actualizar el modelo
                model.update_visible_tasks()
                model.layoutChanged.emit()
                self.update_gantt_chart()
                self.set_unsaved_changes(True)

                # Seleccionar la tarea en su nueva posición
                new_actual_row = model.tasks.index(task)
                new_visible_row = model.actual_to_visible.get(new_actual_row)
                if new_visible_row is not None:
                    self.table_view.selectRow(new_visible_row)
                    self.table_view.scrollTo(model.index(new_visible_row, 0))

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
        # Guardar geometría de la ventana
        self.config.set('Window', 'width', self.width())
        self.config.set('Window', 'height', self.height())
        self.config.set('Window', 'pos_x', self.x())
        self.config.set('Window', 'pos_y', self.y())

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

    def show_about_dialog(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Usar el estilo Fusion que soporta temas oscuros/claros
    # Aplicar la paleta del sistema
    app.setPalette(app.style().standardPalette())

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
