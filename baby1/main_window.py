# main_window.py

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QGridLayout, QScrollBar, QMessageBox, QSizePolicy, QAction, QToolBar
)
from PySide6.QtCore import Qt, QDate, QTimer, Signal
from PySide6.QtGui import QKeySequence, QWheelEvent, QColor
from task_table_widget import TaskTableWidget
from gantt import GanttWidget
from PySide6.QtWidgets import QShortcut
import math


class MainWindow(QMainWindow):
    """
    La clase MainWindow es la ventana principal de la aplicación Baby Project Manager.
    Integra el widget de tabla de tareas, el diagrama de Gantt y un scrollbar compartido.
    Gestiona acciones como abrir, guardar, agregar tareas y manejar eventos de zoom.
    """

    ROW_HEIGHT = 25  # Define la altura fija para las filas

    def __init__(self):
        super().__init__()
        self.unsaved_changes = False
        self.base_title = "Baby Project Manager"
        self.setWindowTitle(self.base_title)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMinMaxButtonsHint)
        self.setMinimumSize(800, 600)
        self.setGeometry(100, 100, 1200, 800)
        self.tasks = []
        self.current_file_path = None
        self.selected_period = 365  # Por defecto, un año de periodos
        self.setMouseTracking(True)
        self.wheel_accumulator = 0
        self.wheel_threshold = 100
        self.current_view = "complete"  # Vistas posibles: complete, year, six_month, three_month, one_month

        # Configuración del diseño principal
        main_widget = QWidget()
        main_layout = QGridLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Configuración de las columnas del layout
        main_layout.setColumnStretch(0, 0)  # Columna de la tabla de tareas
        main_layout.setColumnStretch(1, 1)  # Columna del diagrama de Gantt
        main_layout.setColumnStretch(2, 0)  # Columna del scrollbar

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Widget izquierdo (tabla de tareas)
        self.task_table_widget = TaskTableWidget(self)
        left_widget = self.task_table_widget
        left_widget.setFixedWidth(600)  # Ancho fijo para la tabla de tareas
        self.task_table_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Widget derecho (diagrama de Gantt)
        self.gantt_widget = GanttWidget(self.tasks, self.ROW_HEIGHT, 50, self)
        self.gantt_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.gantt_header = self.gantt_widget.header
        self.gantt_chart = self.gantt_widget.chart
        self.gantt_chart.main_window = self  # Referencia a MainWindow

        # Conectar señales del diagrama de Gantt con la tabla de tareas
        self.gantt_chart.colorChanged.connect(self.task_table_widget.on_color_changed)

        # Scrollbar vertical compartido
        self.shared_scrollbar = QScrollBar(Qt.Orientation.Vertical)
        self.shared_scrollbar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.shared_scrollbar.setFixedWidth(20)
        self.shared_scrollbar.valueChanged.connect(self.task_table_widget.sync_scroll)

        # Añadir widgets al layout principal
        main_layout.addWidget(left_widget, 0, 0)
        main_layout.addWidget(self.gantt_widget, 0, 1)
        main_layout.addWidget(self.shared_scrollbar, 0, 2)

        # Ocultar el scrollbar vertical de la tabla de tareas
        self.task_table_widget.table_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.gantt_chart.set_vertical_offset(0)  # Inicializar desplazamiento vertical

        # Conectar el scrollbar de la tabla con el scrollbar compartido
        self.task_table_widget.table_view.verticalScrollBar().valueChanged.connect(self.on_table_scroll)

        # Ajustar la altura de todas las filas y actualizar el diagrama de Gantt
        self.adjust_all_row_heights()
        self.update_gantt_chart()

        # Atajo de teclado para guardar (Ctrl+S)
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.task_table_widget.quick_save)

        self.set_unsaved_changes(False)
        QTimer.singleShot(0, self.initialize_shared_scrollbar)

        # Configurar la barra de herramientas
        self.setup_toolbar()

    def setup_toolbar(self):
        """
        Configura la barra de herramientas con acciones como abrir, guardar y agregar tareas.
        """
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        # Acción para abrir archivo (Ctrl+O)
        open_action = QAction("Abrir", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.task_table_widget.load_file)
        toolbar.addAction(open_action)

        # Acción para guardar archivo (Ctrl+S)
        save_action = QAction("Guardar", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.task_table_widget.quick_save)
        toolbar.addAction(save_action)

        # Acción para agregar nueva tarea (Ctrl+N)
        add_task_action = QAction("Agregar Tarea", self)
        add_task_action.setShortcut("Ctrl+N")
        add_task_action.triggered.connect(self.task_table_widget.add_new_task)
        toolbar.addAction(add_task_action)

    def initialize_shared_scrollbar(self):
        """
        Inicializa el scrollbar compartido al inicio, ajustando su rango.
        """
        self.task_table_widget.update_shared_scrollbar_range()

    def on_table_scroll(self, value):
        """
        Sincroniza el scrollbar compartido con el scrollbar de la tabla de tareas.

        Args:
            value (int): Nuevo valor del scrollbar de la tabla de tareas.
        """
        self.shared_scrollbar.setValue(value)

    def update_gantt_chart(self, set_unsaved=True):
        """
        Actualiza el diagrama de Gantt con las tareas actuales.

        Args:
            set_unsaved (bool, optional): Marca los cambios como sin guardar. Por defecto es True.
        """
        self.tasks = self.task_table_widget.model.tasks
        self.gantt_chart.tasks = self.tasks

        if self.tasks:
            min_date = min(
                (QDate.fromString(task.start_date, "dd/MM/yyyy") for task in self.tasks),
                default=QDate.currentDate()
            )
            max_date = max(
                (QDate.fromString(task.end_date, "dd/MM/yyyy") for task in self.tasks),
                default=QDate.currentDate().addDays(30)
            )
        else:
            min_date = QDate.currentDate()
            max_date = QDate.currentDate().addDays(30)

        # Ajustar min_date y max_date según la vista actual
        if self.current_view == "one_month":
            min_date = QDate.currentDate().addDays(-7)  # Una semana antes de hoy
            max_date = min_date.addMonths(1)
        elif self.current_view == "three_month":
            min_date = QDate.currentDate().addDays(-int(QDate.currentDate().daysTo(QDate.currentDate().addMonths(3)) * 0.125))
            max_date = min_date.addMonths(3)
        elif self.current_view == "six_month":
            min_date = QDate.currentDate().addDays(-int(QDate.currentDate().daysTo(QDate.currentDate().addMonths(6)) * 0.125))
            max_date = min_date.addMonths(6)
        elif self.current_view == "year":
            min_date = QDate.currentDate().addDays(-int(QDate.currentDate().daysTo(QDate.currentDate().addYears(1)) * 0.125))
            max_date = min_date.addYears(1)
        else:
            # Vista completa: usar las fechas mínimas y máximas de las tareas
            pass

        if min_date == max_date:
            max_date = min_date.addDays(1)

        days_total = min_date.daysTo(max_date) + 1
        available_width = self.gantt_widget.width()
        pixels_per_day = max(0.1, available_width / days_total)

        self.gantt_widget.update_parameters(min_date, max_date, pixels_per_day)
        self.gantt_widget.adjustSize()

        if set_unsaved and self.tasks:
            self.set_unsaved_changes(True)

        self.task_table_widget.update_shared_scrollbar_range()

    def update_task_structure(self):
        """
        Reconstruye la estructura de tareas en el modelo después de cambios.
        """
        self.tasks = self.task_table_widget.model.tasks
        self.task_table_widget.model.update_visible_tasks()
        self.task_table_widget.model.layoutChanged.emit()
        self.update_gantt_chart()

    def set_unsaved_changes(self, value):
        """
        Marca si hay cambios sin guardar en la aplicación.

        Args:
            value (bool): Nuevo estado de cambios sin guardar.
        """
        if self.unsaved_changes != value:
            self.unsaved_changes = value
            self.update_title()

    def update_title(self):
        """
        Actualiza el título de la ventana principal para reflejar cambios sin guardar.
        """
        if self.unsaved_changes:
            self.setWindowTitle(f"*{self.base_title}")
        else:
            self.setWindowTitle(self.base_title)

    def closeEvent(self, event):
        """
        Maneja el evento de cierre de la ventana principal, preguntando al usuario si desea guardar cambios.

        Args:
            event (QCloseEvent): Evento de cierre.
        """
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self, 'Cambios sin guardar',
                '¿Desea guardar los cambios antes de salir?',
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            if reply == QMessageBox.StandardButton.Save:
                if self.task_table_widget.save_file():
                    event.accept()
                else:
                    secondary_reply = QMessageBox.question(
                        self, 'Error al guardar',
                        'No se pudieron guardar los cambios. ¿Desea salir sin guardar?',
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    if secondary_reply == QMessageBox.StandardButton.Yes:
                        event.accept()
                    else:
                        event.ignore()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def resizeEvent(self, event):
        """
        Maneja el evento de cambio de tamaño de la ventana principal.

        Args:
            event (QResizeEvent): Evento de cambio de tamaño.
        """
        super().resizeEvent(event)
        self.update_gantt_chart(set_unsaved=False)
        self.task_table_widget.adjust_all_row_heights()
        self.task_table_widget.update_shared_scrollbar_range()

    def show_task_context_menu(self, global_pos, task_index):
        """
        Muestra el menú contextual para una tarea específica.

        Args:
            global_pos (QPoint): Posición global del cursor.
            task_index (int): Índice visible de la tarea.
        """
        self.task_table_widget.show_context_menu(QPoint(), task_index)

    def update_gantt_highlight(self, task_index):
        """
        Actualiza la tarea resaltada en el diagrama de Gantt.

        Args:
            task_index (int): Índice visible de la tarea a resaltar.
        """
        self.gantt_chart.highlighted_task_index = task_index
        self.gantt_chart.update()

    def wheelEvent(self, event: QWheelEvent):
        """
        Maneja el evento de rueda del ratón para la ventana principal.

        Args:
            event (QWheelEvent): Evento de rueda.
        """
        self.task_table_widget.wheelEvent(event)

    def zoom_in_view(self):
        """
        Realiza un zoom in en el diagrama de Gantt.
        """
        if self.current_view == "complete":
            self.current_view = "year"
        elif self.current_view == "year":
            self.current_view = "six_month"
        elif self.current_view == "six_month":
            self.current_view = "three_month"
        elif self.current_view == "three_month":
            self.current_view = "one_month"
        else:
            # Si ya está en "one_month", no hacer nada
            return
        self.update_gantt_chart()

    def zoom_out_view(self):
        """
        Realiza un zoom out en el diagrama de Gantt.
        """
        if self.current_view == "one_month":
            self.current_view = "three_month"
        elif self.current_view == "three_month":
            self.current_view = "six_month"
        elif self.current_view == "six_month":
            self.current_view = "year"
        elif self.current_view == "year":
            self.current_view = "complete"
        else:
            # Si ya está en "complete", no hacer nada
            return
        self.update_gantt_chart()

    def add_subtask(self, parent_task_index):
        """
        Añade una subtarea a una tarea padre.

        Args:
            parent_task_index (int): Índice visible de la fila de la tarea padre.
        """
        self.task_table_widget.add_subtask(parent_task_index)
