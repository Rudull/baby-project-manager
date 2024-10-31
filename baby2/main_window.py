from PySide6.QtWidgets import (
    QMainWindow, QWidget, QGridLayout, QMessageBox, 
    QScrollBar, QSizePolicy, QFileDialog
)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QKeySequence, QShortcut, QWheelEvent

from table_views import TaskTableWidget
from gantt_views import GanttWidget

class MainWindow(QMainWindow):
    """Ventana principal de la aplicación."""
    
    ROW_HEIGHT = 25

    def __init__(self):
        super().__init__()
        self.initialize_attributes()
        self.setup_ui()
        self.setup_connections()

    def initialize_attributes(self):
        """Inicializa los atributos de la ventana principal."""
        self.unsaved_changes = False
        self.base_title = "Baby project manager"
        self.tasks = []
        self.current_file_path = None
        self.selected_period = 365  # 1 año en días
        self.current_view = "complete"
        self.wheel_accumulator = 0
        self.wheel_threshold = 100

        self.setWindowTitle(self.base_title)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMinMaxButtonsHint)
        self.setMinimumSize(800, 600)
        self.setGeometry(100, 100, 1200, 800)

    def setup_ui(self):
        """Configura la interfaz de usuario."""
        # Widget central con layout de cuadrícula
        main_widget = QWidget()
        main_layout = QGridLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Configurar factores de estiramiento
        main_layout.setColumnStretch(0, 0)  # TaskTableWidget (fijo)
        main_layout.setColumnStretch(1, 1)  # GanttWidget (expansible)
        main_layout.setColumnStretch(2, 0)  # Scrollbar (fijo)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Crear y configurar componentes principales
        self.setup_task_table()
        self.setup_gantt_widget()
        self.setup_scrollbar()

        # Añadir widgets al layout
        main_layout.addWidget(self.left_widget, 0, 0)
        main_layout.addWidget(self.gantt_widget, 0, 1)
        main_layout.addWidget(self.shared_scrollbar, 0, 2)

        # Configurar scroll bars
        self.table_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.gantt_chart.set_vertical_offset(0)

        self.update_gantt_chart()

    def setup_task_table(self):
        """Configura la tabla de tareas."""
        self.left_widget = QWidget()
        left_layout = QVBoxLayout(self.left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.task_table_widget = TaskTableWidget(self)
        left_layout.addWidget(self.task_table_widget)
        self.table_view = self.task_table_widget.table_view
        self.model = self.task_table_widget.model

        self.left_widget.setFixedWidth(600)
        self.task_table_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def setup_gantt_widget(self):
        """Configura el widget del diagrama de Gantt."""
        self.gantt_widget = GanttWidget(self.tasks, self.ROW_HEIGHT, self)
        self.gantt_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.gantt_header = self.gantt_widget.header
        self.gantt_chart = self.gantt_widget.chart
        self.gantt_chart.main_window = self
        self.gantt_chart.colorChanged.connect(self.update_task_color)

    def setup_scrollbar(self):
        """Configura la barra de desplazamiento compartida."""
        self.shared_scrollbar = QScrollBar(Qt.Orientation.Vertical)
        self.shared_scrollbar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.shared_scrollbar.setFixedWidth(20)
        self.shared_scrollbar.valueChanged.connect(self.sync_scroll)

    def setup_connections(self):
        """Configura las conexiones de señales."""
        self.model.layoutChanged.connect(self.on_model_layout_changed)
        self.table_view.verticalScrollBar().valueChanged.connect(self.on_table_scroll)
        
        # Configurar atajo de teclado para guardar
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.quick_save)

        # Inicializar el scrollbar compartido
        QTimer.singleShot(0, self.initialize_shared_scrollbar)

    def initialize_shared_scrollbar(self):
        """Inicializa la barra de desplazamiento compartida."""
        self.update_shared_scrollbar_range()

    def update_shared_scrollbar_range(self):
        """Actualiza el rango de la barra de desplazamiento."""
        total_tasks = self.model.rowCount()
        visible_tasks = self.calculate_visible_tasks()
        max_scroll = max(total_tasks - visible_tasks, 0)
        
        self.shared_scrollbar.setRange(0, max_scroll)
        self.shared_scrollbar.setPageStep(visible_tasks)
        self.shared_scrollbar.setEnabled(total_tasks > visible_tasks)
        
        if not self.shared_scrollbar.isEnabled():
            self.shared_scrollbar.setValue(0)
            self.gantt_chart.set_vertical_offset(0)

    def calculate_visible_tasks(self):
        """Calcula el número de tareas visibles."""
        visible_height = self.table_view.viewport().height()
        return max(1, visible_height // self.ROW_HEIGHT)

    def sync_scroll(self, value):
        """Sincroniza el desplazamiento entre la tabla y el diagrama."""
        self.table_view.verticalScrollBar().setValue(value)
        self.gantt_chart.set_vertical_offset(value * self.ROW_HEIGHT)

    def on_table_scroll(self, value):
        """Maneja el evento de desplazamiento de la tabla."""
        self.shared_scrollbar.setValue(value)

    def update_title(self):
        """Actualiza el título de la ventana."""
        self.setWindowTitle(f"*{self.base_title}" if self.unsaved_changes else self.base_title)

    def set_unsaved_changes(self, value):
        """Establece el estado de cambios sin guardar."""
        if self.unsaved_changes != value:
            self.unsaved_changes = value
            self.update_title()

    def update_gantt_chart(self, set_unsaved=True):
        """Actualiza el diagrama de Gantt."""
        self.tasks = [self.model.getTask(row) for row in range(self.model.rowCount())]

        today = QDate.currentDate()
        if self.tasks:
            dates = [(QDate.fromString(task.start_date, "dd/MM/yyyy"),
                     QDate.fromString(task.end_date, "dd/MM/yyyy"))
                    for task in self.tasks]
            min_date = min((date[0] for date in dates), default=today)
            max_date = max((date[1] for date in dates), default=today.addDays(30))
        else:
            min_date = today
            max_date = today.addDays(30)

        # Ajustar fechas según la vista actual
        min_date, max_date = self.adjust_dates_for_view(min_date, max_date, today)

        # Asegurar que haya al menos un día de diferencia
        if min_date == max_date:
            max_date = min_date.addDays(1)

        # Calcular pixels_per_day
        days_total = min_date.daysTo(max_date) + 1
        available_width = self.gantt_widget.width() - self.shared_scrollbar.width()
        pixels_per_day = max(0.1, available_width / days_total)

        # Actualizar widgets
        self.gantt_widget.update_parameters(min_date, max_date, pixels_per_day)
        self.gantt_chart.setMinimumHeight(max(len(self.tasks) * self.ROW_HEIGHT, self.gantt_widget.height()))
        
        if set_unsaved and self.tasks:
            self.set_unsaved_changes(True)

        self.update_shared_scrollbar_range()

    def adjust_dates_for_view(self, min_date, max_date, today):
        """Ajusta las fechas según la vista seleccionada."""
        if self.current_view == "one_month":
            min_date = today.addDays(-7)
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
        
        return min_date, max_date

    def update_task_color(self, task_index, color):
        """Actualiza el color de una tarea."""
        if 0 <= task_index < len(self.tasks):
            task = self.tasks[task_index]
            if task:
                task.color = color
                task.is_editing = False

                # Actualizar subtareas si es necesario
                if not task.is_subtask and task.subtasks:
                    for subtask in task.subtasks:
                        subtask.color = color

                self.model.dataChanged.emit(
                    self.model.index(task_index, 1),
                    self.model.index(task_index, 1),
                    [Qt.ItemDataRole.BackgroundRole]
                )

                self.set_unsaved_changes(True)
                self.update_gantt_chart()

    def add_new_task(self):
        """Agrega una nueva tarea."""
        task_data = {
            'NAME': "Nueva Tarea",
            'START': QDate.currentDate().toString("dd/MM/yyyy"),
            'END': QDate.currentDate().toString("dd/MM/yyyy"),
            'DURATION': "1",
            'DEDICATION': "40",
            'COLOR': "#22a39f",
            'NOTES': ""
        }
        self.task_table_widget.add_task_to_table(task_data, editable=True)
        
        # Seleccionar y editar la nueva tarea
        new_task_row = self.model.rowCount() - 1
        self.table_view.selectRow(new_task_row)
        self.table_view.scrollTo(self.model.index(new_task_row, 0))
        self.table_view.edit(self.model.index(new_task_row, 1))

    def show_task_context_menu(self, global_pos, task_index):
        """Muestra el menú contextual para una tarea."""
        # [La implementación del menú contextual va aquí]
        pass

    def check_unsaved_changes(self):
        """Verifica si hay cambios sin guardar."""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self,
                'Cambios sin guardar',
                '¿Desea guardar los cambios antes de continuar?',
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            
            if reply == QMessageBox.StandardButton.Save:
                return self.task_table_widget.save_file()
            elif reply == QMessageBox.StandardButton.Cancel:
                return False
                
        return True

    def quick_save(self):
        """Guarda rápidamente los cambios actuales."""
        if self.task_table_widget.save_file():
            self.set_unsaved_changes(False)

    def wheelEvent(self, event: QWheelEvent):
        """Maneja el evento de la rueda del mouse."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.wheel_accumulator += event.angleDelta().y()
            
            if abs(self.wheel_accumulator) >= self.wheel_threshold:
                if self.wheel_accumulator > 0:
                    self.zoom_in_view()
                else:
                    self.zoom_out_view()
                    
                self.wheel_accumulator = 0
            event.accept()
        else:
            super().wheelEvent(event)

    def set_view(self, view_type):
        """Establece el tipo de vista actual."""
        self.current_view = view_type
        self.update_gantt_chart(set_unsaved=False)

    def set_complete_view(self): self.set_view("complete")
    def set_year_view(self): self.set_view("year")
    def set_six_month_view(self): self.set_view("six_month")
    def set_three_month_view(self): self.set_view("three_month")
    def set_one_month_view(self): self.set_view("one_month")

    def zoom_in_view(self):
        """Aumenta el zoom de la vista."""
        view_order = ["complete", "year", "six_month", "three_month", "one_month"]
        current_index = view_order.index(self.current_view)
        if current_index < len(view_order) - 1:
            self.set_view(view_order[current_index + 1])

    def zoom_out_view(self):
        """Disminuye el zoom de la vista."""
        view_order = ["complete", "year", "six_month", "three_month", "one_month"]
        current_index = view_order.index(self.current_view)
        if current_index > 0:
            self.set_view(view_order[current_index - 1])

    def update_gantt_highlight(self, task_index):
        """Actualiza el resaltado en el diagrama de Gantt."""
        self.gantt_chart.highlighted_task_index = task_index
        self.gantt_chart.update()

    def closeEvent(self, event):
        """Maneja el evento de cierre de la ventana."""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self,
                'Cambios sin guardar',
                '¿Desea guardar los cambios antes de salir?',
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            
            if reply == QMessageBox.StandardButton.Save:
                if self.task_table_widget.save_file():
                    event.accept()
                else:
                    self.handle_save_error(event)
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def handle_save_error(self, event):
        """Maneja errores durante el guardado."""
        secondary_reply = QMessageBox.question(
            self,
            'Error al guardar',
            'No se pudieron guardar los cambios. ¿Desea salir sin guardar?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if secondary_reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

    def resizeEvent(self, event):
        """Maneja el evento de redimensionamiento de la ventana."""
        super().resizeEvent(event)
        self.update_gantt_chart(set_unsaved=False)
        self.task_table_widget.adjust_button_size()
        self.update_shared_scrollbar_range()

    def showEvent(self, event):
        """Maneja el evento de mostrar la ventana."""
        super().showEvent(event)
        QTimer.singleShot(0, self.initial_layout_adjustment)

    def initial_layout_adjustment(self):
        """Realiza el ajuste inicial del diseño."""
        self.update_gantt_chart(set_unsaved=False)