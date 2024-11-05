from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableView, QHeaderView,
    QMenu, QMessageBox, QFileDialog, QColorDialog, QSizePolicy
)
from PySide6.QtCore import Qt, QDate, Signal, QTimer
from PySide6.QtGui import QColor, QKeySequence, QShortcut

from delegates import (
    LineEditDelegate, DateEditDelegate, SpinBoxDelegate, StateButtonDelegate
)
from models import Task, TaskTableModel

class TaskTableWidget(QWidget):
    """Widget principal para la tabla de tareas."""

    taskDataChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setup_ui()
        self.setup_connections()
        self.current_file_path = None

    def setup_ui(self):
        """Configura la interfaz de usuario."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Configurar modelo y vista
        self.setup_model_view()

        # Configurar botón de menú
        self.setup_menu_button()

        # Configurar atajo de teclado para Escape
        self.setup_shortcuts()

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def setup_model_view(self):
        """Configura el modelo y la vista de la tabla."""
        self.model = TaskTableModel()
        self.table_view = QTableView()
        self.table_view.setModel(self.model)

        # Configurar selección
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)

        # Configurar menú contextual
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_context_menu)

        # Configurar delegados
        self.setup_delegates()

        # Configurar encabezados
        self.setup_headers()

        # Configurar scrollbars
        self.table_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.main_layout.addWidget(self.table_view)

    def setup_delegates(self):
        """Configura los delegados para cada columna."""
        self.table_view.setItemDelegateForColumn(0, StateButtonDelegate(self.table_view, main_window=self.main_window))
        self.table_view.setItemDelegateForColumn(1, LineEditDelegate(self.table_view))
        self.table_view.setItemDelegateForColumn(2, DateEditDelegate(self.table_view))
        self.table_view.setItemDelegateForColumn(3, DateEditDelegate(self.table_view))
        self.table_view.setItemDelegateForColumn(4, SpinBoxDelegate(minimum=1, maximum=99999, parent=self.table_view))
        self.table_view.setItemDelegateForColumn(5, SpinBoxDelegate(minimum=0, maximum=100, parent=self.table_view))

    def setup_headers(self):
        """Configura los encabezados de la tabla."""
        header = self.table_view.horizontalHeader()

        # Configurar modos de redimensionamiento
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)

        # Configurar alturas
        row_height = self.main_window.ROW_HEIGHT if self.main_window else 25
        self.table_view.verticalHeader().setDefaultSectionSize(row_height)
        self.table_view.verticalHeader().setMinimumSectionSize(row_height)

        # Configurar anchos iniciales
        self.table_view.setColumnWidth(0, 25)   # Estado
        self.table_view.setColumnWidth(1, 150)  # Nombre
        self.table_view.setColumnWidth(2, 100)  # Fecha inicial
        self.table_view.setColumnWidth(3, 100)  # Fecha final
        self.table_view.setColumnWidth(4, 70)   # Días
        self.table_view.setColumnWidth(5, 40)   # Dedicación

    def setup_menu_button(self):
        """Configura el botón de menú."""
        self.menu_button = QPushButton("☰", self)
        self.menu_button.clicked.connect(self.show_menu)
        QTimer.singleShot(0, self.adjust_button_size)

    def setup_shortcuts(self):
        """Configura los atajos de teclado."""
        escape_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self.table_view)
        escape_shortcut.activated.connect(self.clear_selection)

    def setup_connections(self):
        """Configura las conexiones de señales."""
        self.model.dataChanged.connect(self.on_data_changed)
        self.table_view.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def clear_selection(self):
        """Limpia la selección actual."""
        self.table_view.clearSelection()
        if self.main_window:
            self.main_window.update_gantt_highlight(None)

    def on_selection_changed(self, selected, deselected):
        """Maneja cambios en la selección."""
        if self.main_window:
            selected_rows = self.table_view.selectionModel().selectedRows()
            task_index = selected_rows[0].row() if selected_rows else None
            self.main_window.update_gantt_highlight(task_index)

    def on_data_changed(self, topLeft, bottomRight, roles):
        """Maneja cambios en los datos del modelo."""
        if any(role in roles for role in [Qt.ItemDataRole.EditRole, Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.UserRole]):
            if self.main_window:
                self.main_window.set_unsaved_changes(True)
                self.main_window.update_gantt_chart()

    def show_menu(self):
        """Muestra el menú principal."""
        menu = QMenu(self)

        # Acciones de archivo
        menu.addAction("Guardar").triggered.connect(self.save_file)
        menu.addAction("Guardar como").triggered.connect(self.save_file_as)
        menu.addAction("Nuevo").triggered.connect(self.new_project)
        menu.addAction("Abrir").triggered.connect(self.open_file)
        menu.addAction("Agregar Nueva Tarea").triggered.connect(self.main_window.add_new_task)

        # Submenú de vista
        view_menu = menu.addMenu("Vista")
        view_menu.addAction("Completa").triggered.connect(self.main_window.set_complete_view)
        view_menu.addAction("Año").triggered.connect(self.main_window.set_year_view)
        view_menu.addAction("6 Meses").triggered.connect(self.main_window.set_six_month_view)
        view_menu.addAction("3 Meses").triggered.connect(self.main_window.set_three_month_view)
        view_menu.addAction("1 Mes").triggered.connect(self.main_window.set_one_month_view)

        # Otras acciones
        menu.addAction("Restablecer colores").triggered.connect(self.reset_all_colors)

        # Submenús adicionales
        self.add_import_export_menus(menu)
        self.add_config_menu(menu)

        menu.addAction("Acerca de")

        menu.exec(self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft()))

    def add_import_export_menus(self, menu):
        """Agrega los submenús de importación y exportación."""
        import_menu = menu.addMenu("Importar")
        import_menu.addAction("PDF")
        import_menu.addAction("MPP")
        import_menu.addAction("XLSX")

        export_menu = menu.addMenu("Exportar")
        export_menu.addAction("PDF")
        export_menu.addAction("XLSX")

    def add_config_menu(self, menu):
        """Agrega el submenú de configuración."""
        config_menu = menu.addMenu("Configuración")

        language_menu = config_menu.addMenu("Idioma")
        for lang in ["Español", "Inglés", "Alemán", "Francés"]:
            language_menu.addAction(lang)

        region_menu = config_menu.addMenu("Región")
        region_menu.addAction("Detectar automáticamente")
        region_menu.addAction("Seleccionar país")

        config_menu.addAction("API AI")
        config_menu.addAction("Abrir al iniciar el OS")
        config_menu.addAction("Alertas")

    def adjust_button_size(self):
        """Ajusta el tamaño del botón de menú."""
        header = self.table_view.horizontalHeader()
        self.menu_button.setFixedSize(25, header.height())
        self.menu_button.move(0, 0)

    def save_file(self):
        """Guarda el archivo actual."""
        if hasattr(self, 'current_file_path') and self.current_file_path:
            success = self.save_tasks_to_file(self.current_file_path)
        else:
            success = self.save_file_as()

        if success and self.main_window:
            self.main_window.set_unsaved_changes(False)
        return success

    def save_file_as(self):
        """Guarda el archivo con un nuevo nombre."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar como",
            "",
            "Archivos BPM (*.bpm);;Todos los archivos (*)"
        )
        if file_path:
            if not file_path.lower().endswith('.bpm'):
                file_path += '.bpm'
            success = self.save_tasks_to_file(file_path)
            if success:
                self.current_file_path = file_path
                if self.main_window:
                    self.main_window.set_unsaved_changes(False)
            return success
        return False

    def save_tasks_to_file(self, file_path):
        """Guarda las tareas en un archivo."""
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                for task in self.model.tasks:
                    self.write_task_to_file(file, task)
            self.current_file_path = file_path
            return True
        except Exception as e:
            print(f"Error al guardar el archivo: {e}")
            return False

    def write_task_to_file(self, file, task):
        """Escribe una tarea en el archivo."""
        file.write("[TASK]\n")
        file.write(f"NAME: {task.name}\n")
        file.write(f"PARENT: {task.parent_task.name if task.is_subtask and task.parent_task else ''}\n")
        file.write(f"START: {task.start_date}\n")
        file.write(f"END: {task.end_date}\n")
        file.write(f"DURATION: {task.duration}\n")
        file.write(f"DEDICATION: {task.dedication}\n")
        file.write(f"COLOR: {task.color.name()}\n")
        file.write(f"COLLAPSED: {task.is_collapsed}\n")
        file.write("NOTES_HTML_BEGIN\n")
        file.write(task.notes_html)
        file.write("\nNOTES_HTML_END\n")
        file.write("FILE_LINKS_BEGIN\n")
        file.write(repr(task.file_links))
        file.write("\nFILE_LINKS_END\n")
        file.write("[/TASK]\n\n")

    def open_file(self):
        """Abre un archivo existente."""
        if self.main_window and self.main_window.check_unsaved_changes():
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Abrir archivo",
                "",
                "Archivos BPM (*.bpm);;Todos los archivos (*)"
            )
            if file_path:
                self.load_tasks_from_file(file_path)

    def load_tasks_from_file(self, file_path):
        """Carga las tareas desde un archivo."""
        try:
            self.model.beginResetModel()
            self.model.tasks = []
            tasks_with_parents = []

            with open(file_path, 'r', encoding='utf-8') as file:
                self.parse_file_content(file, tasks_with_parents)

            self.establish_task_relationships(tasks_with_parents)

            self.model.update_visible_tasks()
            self.model.endResetModel()
            self.current_file_path = file_path

            if self.main_window:
                self.main_window.set_unsaved_changes(False)
                self.main_window.update_gantt_chart()

        except Exception as e:
            print(f"Error al cargar el archivo: {e}")

    def parse_file_content(self, file, tasks_with_parents):
        """Analiza el contenido del archivo y crea las tareas."""
        content = file.read()
        tasks_data = content.split("[TASK]")

        for task_block in tasks_data:
            if "[/TASK]" in task_block:
                task_data = self.parse_task_block(task_block)
                if task_data:
                    task = self.create_task_from_data(task_data)
                    self.model.tasks.append(task)
                    tasks_with_parents.append((task, task_data.get('PARENT', '')))

    def parse_task_block(self, task_block):
        """Analiza un bloque de tarea individual."""
        task_data = {}
        lines = task_block.split("\n")
        reading_notes = False
        reading_links = False
        notes_html = ""
        file_links_str = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if ":" in line and not reading_notes and not reading_links:
                key, value = line.split(":", 1)
                task_data[key.strip()] = value.strip()
            elif line == "NOTES_HTML_BEGIN":
                reading_notes = True
            elif line == "NOTES_HTML_END":
                reading_notes = False
                task_data['NOTES_HTML'] = notes_html
            elif line == "FILE_LINKS_BEGIN":
                reading_links = True
            elif line == "FILE_LINKS_END":
                reading_links = False
                try:
                    task_data['FILE_LINKS'] = eval(file_links_str)
                except:
                    task_data['FILE_LINKS'] = {}
            elif reading_notes:
                notes_html += line + "\n"
            elif reading_links:
                file_links_str += line + "\n"

        return task_data

    def create_task_from_data(self, task_data):
        """Crea una instancia de Task a partir de los datos parseados."""
        return Task(
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

    def establish_task_relationships(self, tasks_with_parents):
        """Establece las relaciones entre tareas padre e hijas."""
        name_to_task = {task.name: task for task, _ in tasks_with_parents}

        for task, parent_name in tasks_with_parents:
            if parent_name:
                parent_task = name_to_task.get(parent_name)
                if parent_task:
                    task.is_subtask = True
                    task.parent_task = parent_task
                    parent_task.subtasks.append(task)

    def add_task_to_table(self, task_data, editable=False):
        """Agrega una nueva tarea a la tabla."""
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

        task.is_editing = editable
        task.is_collapsed = False

        self.model.insertTask(task)
        self.model.update_visible_tasks()
        self.taskDataChanged.emit()

        if self.main_window:
            self.main_window.set_unsaved_changes(True)
            self.main_window.update_gantt_chart()

    def reset_all_colors(self):
        """Restablece todos los colores de las tareas al valor por defecto."""
        default_color = QColor(34, 163, 159)
        for task in self.model.tasks:
            task.color = default_color

        self.model.dataChanged.emit(
            self.model.index(0, 1),
            self.model.index(self.model.rowCount()-1, 1),
            [Qt.ItemDataRole.BackgroundRole]
        )

        if self.main_window:
            self.main_window.set_unsaved_changes(True)
            self.main_window.update_gantt_chart()

    def new_project(self):
        """Crea un nuevo proyecto."""
        if self.main_window and self.main_window.check_unsaved_changes():
            self.model.beginResetModel()
            self.model.tasks = []
            self.model.update_visible_tasks()
            self.model.endResetModel()
            self.current_file_path = None
            if self.main_window:
                self.main_window.set_unsaved_changes(False)
                self.main_window.update_gantt_chart()

    def update_state_buttons(self):
        """Actualiza los botones de estado sin cambiar los colores."""
        self.model.dataChanged.emit(
            self.model.index(0, 0),
            self.model.index(self.model.rowCount() - 1, self.model.columnCount() - 1),
            [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.DecorationRole, Qt.ItemDataRole.UserRole]
        )

    def show_context_menu(self, position):
        """Muestra el menú contextual en la posición del clic."""
        index = self.table_view.indexAt(position)
        if index.isValid():
            menu = QMenu()
            row = index.row()
            task = self.model.getTask(row)

            # Acciones del menú contextual
            actions = []

            # Duplicar tarea
            duplicate_action = menu.addAction("Duplicar")
            actions.append((duplicate_action, lambda: self.duplicate_task(row)))

            # Insertar tarea (solo si no es subtarea)
            if not task.is_subtask:
                insert_action = menu.addAction("Insertar")
                actions.append((insert_action, lambda: self.insert_task(row)))

            # Mover arriba/abajo
            move_up_action = menu.addAction("Mover arriba")
            actions.append((move_up_action, lambda: self.move_task_up(row)))

            move_down_action = menu.addAction("Mover abajo")
            actions.append((move_down_action, lambda: self.move_task_down(row)))

            # Agregar subtarea (solo si no es subtarea)
            if not task.is_subtask:
                add_subtask_action = menu.addAction("Agregar subtarea")
                actions.append((add_subtask_action, lambda: self.main_window.add_subtask(row)))

            # Eliminar tarea
            delete_action = menu.addAction("Eliminar")
            actions.append((delete_action, lambda: self.main_window.delete_task(row)))

            # Color por defecto
            reset_color_action = menu.addAction("Color por defecto")
            actions.append((reset_color_action, lambda: self.main_window.reset_task_color(row)))

            # Mostrar el menú
            action = menu.exec(self.table_view.viewport().mapToGlobal(position))

            # Ejecutar la acción seleccionada
            if action:
                for act, func in actions:
                    if act == action:
                        func()
                        break
