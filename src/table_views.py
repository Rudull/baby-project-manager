#table_views.py
#contiene la definición del widget de tabla de tareas (TaskTableWidget),
#el cual proporciona la interfaz de usuario para visualizar, editar,
#agregar y gestionar las tareas dentro de la aplicación. Este módulo
#organiza la lógica de presentación de la tabla, sus delegados, el menú
#contextual, los métodos de guardado/carga de archivos y la sincronización
#con el resto de la aplicación.
#1
import os
import ast
from datetime import timedelta, datetime
from workalendar.america import Colombia

from PySide6.QtCore import Qt, QDate, QTimer, Signal, QModelIndex, QSize
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QPushButton, QMenu,
    QFileDialog, QSizePolicy, QHeaderView, QMessageBox
)

from models import Task, TaskTableModel
from delegates import LineEditDelegate, DateEditDelegate, SpinBoxDelegate, StateButtonDelegate
from file_gui import MainWindow as FileGUIWindow
from startup_manager import StartupManager

class TaskTableWidget(QWidget):
    taskDataChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.startup_manager = StartupManager(self.main_window.config)

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

        # Agregar submenú de archivos recientes
        recent_menu = menu.addMenu("Archivos recientes")
        if self.main_window:
            recent_files = self.main_window.config.get_recent_files()
            if recent_files:
                for file_path in recent_files:
                    action = recent_menu.addAction(os.path.basename(file_path))
                    action.setData(file_path)
                recent_menu.triggered.connect(self.open_recent_file)
            else:
                action = recent_menu.addAction("(No hay archivos recientes)")
                action.setEnabled(False)

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
        if self.main_window:
            startup_action = config_menu.addAction("Abrir al iniciar el OS")
            startup_action.setCheckable(True)
            startup_action.setChecked(self.startup_manager.is_startup_enabled())
            startup_action.triggered.connect(self.toggle_startup)
        config_menu.addAction("Alertas")

        about_action = menu.addAction("Acerca de")
        about_action.triggered.connect(self.main_window.show_about_dialog)

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
            if success:
                self.main_window.config.update_last_directory(self.current_file_path)
                self.main_window.config.add_recent_file(self.current_file_path)
                self.main_window.config.set_last_file(self.current_file_path)
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
                self.main_window.config.set_last_file(file_path)
                self.main_window.config.update_last_directory(file_path)
                self.main_window.config.add_recent_file(file_path)
                self.main_window.set_unsaved_changes(False)
            return success
        return False

    def open_file(self):
        if self.main_window.check_unsaved_changes():
            initial_dir = self.main_window.config.get('General', 'last_directory')
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Abrir archivo",
                initial_dir,
                "Archivos BPM (*.bpm);;Todos los archivos (*)"
            )
            if file_path:
                self.load_tasks_from_file(file_path)
                self.main_window.config.update_last_directory(file_path)
                self.main_window.config.add_recent_file(file_path)

    def open_recent_file(self, action):
            file_path = action.data()
            if os.path.exists(file_path):
                if self.main_window.check_unsaved_changes():
                    self.load_tasks_from_file(file_path)
                    self.main_window.config.update_last_directory(file_path)
                    self.main_window.config.add_recent_file(file_path)
            else:
                QMessageBox.warning(
                    self,
                    "Archivo no encontrado",
                    f"No se puede encontrar el archivo:\n{file_path}"
                )

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
                self.main_window.config.set_last_file(file_path)
                self.main_window.set_unsaved_changes(False)
                self.main_window.update_gantt_chart()
            print(f"Archivo cargado desde: {file_path}")
        except Exception as e:
            print(f"Error al cargar el archivo: {e}")

    def add_task_to_table(self, task_data, editable=False):
        # Determinar si la tarea es padre o subtarea basado en el nivel
        level = task_data.get('level', '')
        is_subtask = False
        parent_task = None

        # Si hay tareas existentes, buscar el padre potencial
        if self.model.tasks:
            # Si el nivel indica que es una subtarea
            if level and '.' in level:  # Por ejemplo: "1.1", "2.1", etc.
                is_subtask = True
                parent_level = level.rsplit('.', 1)[0]  # Obtener el nivel del padre
                # Buscar la tarea padre
                for task in reversed(self.model.tasks):
                    if hasattr(task, 'level') and task.level == parent_level:
                        parent_task = task
                        break

        # Crear la nueva tarea
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

        task.level = level  # Guardar el nivel
        task.is_subtask = is_subtask
        task.is_editing = editable
        task.is_collapsed = False

        # Si es una subtarea y encontramos el padre
        if is_subtask and parent_task:
            task.parent_task = parent_task
            parent_task.subtasks.append(task)

        self.model.insertTask(task)
        self.model.update_visible_tasks()
        self.taskDataChanged.emit()

    def reset_all_colors(self):
        default_color = QColor(34, 163, 159)  # Color por defecto
        for task in self.model.tasks:
            task.color = default_color
        self.model.dataChanged.emit(self.model.index(0, 1), self.model.index(self.model.rowCount()-1, 1), [Qt.ItemDataRole.BackgroundRole])
        if self.main_window:
            self.main_window.set_unsaved_changes(True)
            self.main_window.update_gantt_chart()

    def new_project(self):
        # Verificar si hay cambios sin guardar
        if self.main_window and self.main_window.check_unsaved_changes():
            # Limpiar todas las tareas existentes
            self.model.beginResetModel()
            self.model.tasks = []
            self.model.update_visible_tasks()
            self.model.endResetModel()

            # Reiniciar variables relacionadas con el archivo
            if hasattr(self, 'current_file_path'):
                self.current_file_path = None

            # Actualizar el diagrama de Gantt
            if self.main_window:
                self.main_window.update_gantt_chart(set_unsaved=False)
                self.main_window.set_unsaved_changes(False)

            # Reiniciar el scrollbar compartido
            if hasattr(self, 'shared_scrollbar'):
                self.shared_scrollbar.setValue(0)
                self.update_shared_scrollbar_range()

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

    def toggle_startup(self):
            """Maneja el cambio en la configuración de inicio automático"""
            success = self.startup_manager.toggle_startup()

            if success:
                QMessageBox.information(
                    self,
                    "Inicio automático",
                    "La configuración de inicio automático se ha actualizado correctamente."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "No se pudo actualizar la configuración de inicio automático."
                )
