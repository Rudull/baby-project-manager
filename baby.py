# Orden fecha inicial ok 12
import sys
from datetime import timedelta, datetime
from workalendar.america import Colombia
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QDateEdit, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QMenu, QScrollBar, QFileDialog, QMessageBox, QColorDialog,
    QTextEdit
)
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QPainterPath, QPalette, QContextMenuEvent, QKeySequence, QShortcut
from PySide6.QtCore import Qt, QDate, QRect, QTimer, QSize, QRectF, QEvent, Signal, QPoint

class FloatingTaskMenu(QWidget):
    notesChanged = Signal()

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.cal = Colombia()  # crear una instancia del calendario
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        name_label = QLabel(f"{self.task.name}")  # Usar self.task.name en lugar de task.name
        start_label = QLabel(f"Inicio: {self.task.start_date}")
        end_label = QLabel(f"Fin: {self.task.end_date}")

        days_left_label = QLabel(f"Días restantes: {self.calculate_working_days_left()}")

        for label in (name_label, start_label, end_label, days_left_label):
            label.setAlignment(Qt.AlignRight)
            layout.addWidget(label)

        self.notes_edit = QTextEdit(self)
        self.notes_edit.setPlainText(self.task.notes)
        self.notes_edit.setMinimumHeight(100)
        layout.addWidget(self.notes_edit)

        self.adjustSize()
        self.update_colors()

        self.notes_edit.textChanged.connect(self.update_task_notes)

    def calculate_working_days_left(self):
        today = datetime.now().date()
        start_date = datetime.strptime(self.task.start_date, "%d/%m/%Y").date()
        end_date = datetime.strptime(self.task.end_date, "%d/%m/%Y").date()

        if end_date < today:
            return 0
        elif start_date <= today <= end_date:
            count_from = today
        else:
            count_from = start_date

        working_days = 0
        current_date = count_from
        while current_date <= end_date:
            if self.cal.is_working_day(current_date):
                working_days += 1
            current_date += timedelta(days=1)

        return working_days

    def update_task_notes(self):
        if self.task.notes != self.notes_edit.toPlainText():
            self.task.notes = self.notes_edit.toPlainText()
            self.notesChanged.emit()  # Emite la señal cuando las notas cambian

    def update_colors(self):
        palette = self.palette()
        self.background_color = palette.color(QPalette.Window)
        self.text_color = palette.color(QPalette.WindowText)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.background_color)
        painter.setPen(Qt.NoPen)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 10, 10)
        painter.drawPath(path)

    def changeEvent(self, event):
        if event.type() == QEvent.PaletteChange:
            self.update_colors()
            for child in self.findChildren(QLabel):
                child.setStyleSheet(f"color: {self.text_color.name()};")
            self.update()
        super().changeEvent(event)

class StateButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(25, 25)
        self.setStyleSheet("background-color: red;")
        self.is_editing = True
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.toggle_color)
        self.timer.start(500)  # Parpadeo cada 500 ms
        self.current_color = "red"

    def toggle_color(self):
        if self.is_editing:
            if self.current_color == "red":
                self.setStyleSheet("background-color: gray;")
                self.current_color = "gray"
            else:
                self.setStyleSheet("background-color: red;")
                self.current_color = "red"
        else:
            self.setStyleSheet("background-color: rgb(34,151,153);") #color boton de filas

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.toggle_state()
        super().mousePressEvent(e)

    def toggle_state(self):
        self.is_editing = not self.is_editing
        if self.is_editing:
            self.setStyleSheet("background-color: red;")
            self.current_color = "red"
            self.timer.start(500)
        else:
            self.setStyleSheet("background-color: rgb(34,151,153);") #color boton de filas
            self.timer.stop()

class Task:
    def __init__(self, name, start_date, end_date, duration, dedication, color=None, notes=""):
        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.duration = duration
        self.dedication = dedication
        self.color = color or QColor(34, 163, 159)  # Color por defecto si no se especifica
        self.notes = notes

class GanttHeaderView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.min_date = None
        self.max_date = None
        self.pixels_per_day = None
        self.header_height = 20
        self.setFixedHeight(self.header_height)
        self.scroll_offset = 0
        self.update_colors()

    def update_colors(self):
        palette = self.palette()
        self.background_color = palette.color(QPalette.Base)
        self.text_color = palette.color(QPalette.Text)

        # Determinar si estamos en modo claro u oscuro
        is_light_mode = palette.color(QPalette.Window).lightness() > 128
        if is_light_mode:
            # Modo claro: usar gris oscuro
            self.year_color = QColor(80, 80, 80)  # Gris oscuro
            self.year_separator_color = QColor(120, 120, 120)  # Gris un poco más claro para las líneas
        else:
            # Modo oscuro: usar gris claro
            self.year_color = QColor(200, 200, 200)  # Gris claro
            self.year_separator_color = QColor(160, 160, 160)  # Gris un poco más oscuro para las líneas

    def update_parameters(self, min_date, max_date, pixels_per_day):
        self.min_date = min_date
        self.max_date = max_date
        self.pixels_per_day = max(0.1, pixels_per_day)  # Evita valores demasiado pequeños
        width = max(0, int((max_date.daysTo(min_date) + 1) * self.pixels_per_day))
        self.setMinimumWidth(min(width, 16777215))  # Limita el ancho máximo
        self.update()

    def paintEvent(self, event):
        if not self.min_date or not self.max_date or not self.pixels_per_day:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(event.rect(), self.background_color)

        year_font = QFont("Arial", 10, QFont.Bold)
        painter.setFont(year_font)

        start_year = self.min_date.year()
        end_year = self.max_date.year()

        for year in range(start_year, end_year + 1):
            year_start = QDate(year, 1, 1)
            year_end = QDate(year, 12, 31)
            if year_start < self.min_date:
                year_start = self.min_date
            if year_end > self.max_date:
                year_end = self.max_date

            start_x = self.min_date.daysTo(year_start) * self.pixels_per_day - self.scroll_offset
            end_x = self.min_date.daysTo(year_end) * self.pixels_per_day - self.scroll_offset

            # Dibuja líneas verticales para separar los años
            painter.setPen(QPen(self.year_separator_color, 1))
            painter.drawLine(int(end_x), 0, int(end_x), self.header_height)

            year_width = end_x - start_x
            year_rect = QRect(int(start_x), 0, int(year_width), self.header_height)
            painter.setPen(self.year_color)
            painter.drawText(year_rect, Qt.AlignCenter, str(year))

        # Dibujar la etiqueta para el día de hoy
        today = QDate.currentDate()
        if self.min_date <= today <= self.max_date:
            today_x = self.min_date.daysTo(today) * self.pixels_per_day - self.scroll_offset

            # Dibuja la etiqueta "Hoy" con un fondo gris redondeado
            label_width = 50
            label_height = 20
            label_x = today_x - label_width / 2
            label_y = self.height() - label_height - 0

            # Dibuja el fondo redondeado
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(128, 128, 128, 180))
            painter.drawRoundedRect(QRectF(label_x, label_y, label_width, label_height), 10, 10)

            # Dibuja el texto "Hoy"
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.setPen(QColor(242,211,136)) #color del texto del día de hoy
            painter.drawText(QRectF(label_x, label_y, label_width, label_height), Qt.AlignCenter, "Hoy")

        painter.end()

    def scrollTo(self, value):
        self.scroll_offset = value
        self.update()

    def changeEvent(self, event):
        if event.type() == QEvent.PaletteChange:
            self.update_colors()
            self.update()
        super().changeEvent(event)

class GanttChart(QWidget):
    colorChanged = Signal(int, QColor)
    SINGLE_CLICK_INTERVAL = 100  # Intervalo en milisegundos para el clic simple

    def __init__(self, tasks, row_height, header_height):
        super().__init__()
        self.tasks = tasks
        self.row_height = row_height
        self.header_height = header_height
        self.min_date = None
        self.max_date = None
        self.pixels_per_day = None
        self.floating_menu = None
        self.setMinimumHeight(self.header_height + self.row_height * len(tasks))
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.update_colors()
        self.today_line_color = QColor(242,211,136)  # Color para la línea "Hoy"
        self.double_click_occurred = False  # Bandera para controlar doble clic
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.colorChanged.connect(self.on_color_changed)

    def update_colors(self):
        palette = self.palette()
        self.background_color = palette.color(QPalette.Base)
        self.task_color = palette.color(QPalette.Highlight)
        self.text_color = palette.color(QPalette.Text)
        self.grid_color = palette.color(QPalette.Mid)

    def update_parameters(self, min_date, max_date, pixels_per_day):
        self.min_date = min_date
        self.max_date = max_date
        self.pixels_per_day = max(0.1, pixels_per_day)  # Evita valores demasiado pequeños

        width = self.parent().width() if self.parent() else self.width()

        self.setMinimumWidth(width)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.double_click_occurred = False
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Almacenar las posiciones
            self.click_pos = event.position().toPoint()
            self.click_global_pos = event.globalPosition().toPoint()
            # Iniciar el temporizador para el clic simple
            self.single_click_timer = QTimer()
            self.single_click_timer.setSingleShot(True)
            self.single_click_timer.timeout.connect(self.handle_single_click)
            self.single_click_timer.start(self.SINGLE_CLICK_INTERVAL)
        super().mouseReleaseEvent(event)

    def handle_single_click(self):
        if not self.double_click_occurred:
            task_index = int(self.click_pos.y() / self.row_height)
            if 0 <= task_index < len(self.tasks):
                task = self.tasks[task_index]
                self.show_floating_menu(self.click_global_pos, task)
        # Restablecer la bandera
        self.double_click_occurred = False

    def mouseDoubleClickEvent(self, event):
        self.double_click_occurred = True
        if hasattr(self, 'single_click_timer'):
            self.single_click_timer.stop()

        x = int(event.position().x())
        y = int(event.position().y())
        row_height = self.row_height

        # Determinar el índice de la tarea basada en la posición Y
        task_index = int(y / row_height)
        if 0 <= task_index < len(self.tasks):
            task = self.tasks[task_index]

            # Calcular la posición X de inicio y fin de la barra de la tarea
            start_date = QDate.fromString(task.start_date, "dd/MM/yyyy")
            end_date = QDate.fromString(task.end_date, "dd/MM/yyyy")
            task_start_x = self.min_date.daysTo(start_date) * self.pixels_per_day
            task_end_x = self.min_date.daysTo(end_date) * self.pixels_per_day

            # Verificar si el doble clic fue dentro de la barra de la tarea
            if task_start_x <= x <= task_end_x:
                # Abrir el diálogo de selección de color
                color = QColorDialog.getColor(initial=task.color, parent=self)
                if color.isValid():
                    # Actualizar el color de la tarea
                    task.color = color
                    self.update()
                    # Emitir señal para actualizar la tabla
                    self.colorChanged.emit(task_index, color)
        super().mouseDoubleClickEvent(event)

    def show_floating_menu(self, position, task):
        if self.floating_menu:
            self.floating_menu.close()
        # Obtener la información actualizada de la tarea
        updated_task = self.get_updated_task(task)
        self.floating_menu = FloatingTaskMenu(updated_task, self)
        self.floating_menu.notesChanged.connect(self.on_notes_changed)
        self.floating_menu.move(position)
        self.floating_menu.show()

    def get_updated_task(self, task):
        for row in range(self.main_window.task_table_widget.task_table.rowCount()):
            name_item = self.main_window.task_table_widget.task_table.item(row, 1)
            current_task = name_item.data(Qt.UserRole + 1)
            if current_task == task:
                task.name = name_item.text()
                break
        return task

    def on_notes_changed(self):
        if hasattr(self, 'main_window'):
            self.main_window.set_unsaved_changes(True)

    def on_color_changed(self, task_index, color):
        if hasattr(self, 'main_window'):
            self.main_window.set_unsaved_changes(True)

    def paintEvent(self, event):
        if not self.min_date or not self.max_date or not self.pixels_per_day:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(event.rect(), self.background_color)

        for i, task in enumerate(self.tasks):
            start = QDate.fromString(task.start_date, "dd/MM/yyyy")
            end = QDate.fromString(task.end_date, "dd/MM/yyyy")
            if end < self.min_date or start > self.max_date:
                continue

            start = max(start, self.min_date)
            end = min(end, self.max_date)

            x = self.min_date.daysTo(start) * self.pixels_per_day
            width = start.daysTo(end) * self.pixels_per_day
            y = i * self.row_height

            y_adjusted = y + 1

            painter.setBrush(QBrush(task.color))  # Usar el color de la tarea
            painter.setPen(Qt.NoPen)
            painter.drawRect(QRectF(x, y_adjusted, width, self.row_height - 2))

        # Dibujar la línea vertical para el día de hoy
        today = QDate.currentDate()
        if self.min_date <= today <= self.max_date:
            today_x = self.min_date.daysTo(today) * self.pixels_per_day
            painter.setPen(QPen(self.today_line_color, 2))
            painter.drawLine(int(today_x), 0, int(today_x), self.height())

        painter.end()

    def changeEvent(self, event):
        if event.type() == QEvent.PaletteChange:
            self.update_colors()
            self.update()
        super().changeEvent(event)

    def show_context_menu(self, position):
        task_index = self.get_task_at_position(position)
        if task_index is not None:
            self.main_window.show_task_context_menu(QPoint(self.mapToGlobal(position)), task_index)

    def get_task_at_position(self, position):
        y = position.y()
        task_index = y // self.row_height
        if 0 <= task_index < len(self.tasks):
            task = self.tasks[task_index]
            x = position.x()
            start_date = QDate.fromString(task.start_date, "dd/MM/yyyy")
            end_date = QDate.fromString(task.end_date, "dd/MM/yyyy")
            start_x = self.min_date.daysTo(start_date) * self.pixels_per_day
            end_x = self.min_date.daysTo(end_date) * self.pixels_per_day
            if start_x <= x <= end_x:
                return task_index
        return None

class GanttWidget(QWidget):
    def __init__(self, tasks, row_height):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.header = GanttHeaderView()
        self.chart = GanttChart(tasks, row_height, self.header.header_height)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # Crear un widget contenedor para el encabezado y el gráfico
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_layout.addWidget(self.header)
        self.content_layout.addWidget(self.chart)

        # Establecer el widget contenedor como widget del área de desplazamiento
        self.scroll_area.setWidget(self.content_widget)
        self.layout.addWidget(self.scroll_area)

        self.scroll_area.horizontalScrollBar().valueChanged.connect(self.sync_horizontal_scroll)

    def sync_horizontal_scroll(self, value):
        self.header.scrollTo(value)
        # Añadir un pequeño retraso para asegurar que la sincronización sea suave
        QTimer.singleShot(10, lambda: self.chart.update())

    def update_parameters(self, min_date, max_date, pixels_per_day):
        days_total = min_date.daysTo(max_date) + 1
        available_width = self.width()  # Usa el ancho del widget completo
        pixels_per_day = max(0.1, available_width / days_total)

        self.header.update_parameters(min_date, max_date, pixels_per_day)
        self.chart.update_parameters(min_date, max_date, pixels_per_day)
        self.content_widget.setFixedWidth(available_width)

class TaskTableWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.task_table = QTableWidget(0, 6, self)
        self.task_table.setHorizontalHeaderLabels(["", "Nombre", "Fecha inicial", "Fecha final", "Días", "%"])
        self.task_table.verticalHeader().setVisible(False)
        self.main_layout.addWidget(self.task_table)

        self.task_table.horizontalHeader().sectionClicked.connect(self.on_header_click)
        self.task_table.cellChanged.connect(self.on_cell_changed)

        self.menu_button = QPushButton("☰", self)
        self.menu_button.clicked.connect(self.show_menu)
        QTimer.singleShot(0, self.adjust_button_size)

        self.current_file_path = None
        self.setup_table_style()
        self.setup_item_change_detection()

    def setup_table_style(self):
        self.task_table.setStyleSheet("""
        QTableWidget {
            gridline-color: transparent;
            border: none;
        }
        QTableWidget::item {
            padding: 0px;
            border: none;
        }
        """)
        self.task_table.verticalHeader().setDefaultSectionSize(self.main_window.ROW_HEIGHT)
        self.task_table.verticalHeader().setMinimumSectionSize(self.main_window.ROW_HEIGHT)

    def setup_item_change_detection(self):
        self.task_table.itemChanged.connect(self.on_item_changed)
        for row in range(self.task_table.rowCount()):
            dedication_widget = self.task_table.cellWidget(row, 5)
            if isinstance(dedication_widget, QLineEdit):
                dedication_widget.textChanged.connect(self.on_dedication_changed)

    def on_dedication_changed(self):
        if hasattr(self, 'main_window'):
            self.main_window.set_unsaved_changes(True)

    def on_item_changed(self, item):
        if item.column() in [1, 5]:  # Columna del nombre de la tarea o dedicación
            if hasattr(self, 'main_window'):
                self.main_window.set_unsaved_changes(True)

    def on_cell_changed(self, row, column):
        if column == 1:  # Columna del nombre
            item = self.task_table.item(row, column)
            task = item.data(Qt.UserRole + 1)
            if task:
                task.name = item.text()
                if hasattr(self, 'main_window'):
                    self.main_window.update_gantt_chart()

    def adjust_button_size(self):
        header = self.task_table.horizontalHeader()
        header_height = header.height()
        button_width = int(header_height * 1.3)
        self.menu_button.setFixedSize(QSize(button_width, header_height))
        self.menu_button.move(0, header.pos().y())

        self.task_table.setColumnWidth(0, button_width)
        available_width = self.task_table.width() - button_width
        name_width = int(available_width * 0.30)
        date_width = int(available_width * 0.21)
        duration_width = int(available_width * 0.09)
        dedication_width = int(available_width * 0.075)

        new_name_width = int(name_width * 1.3)
        new_total_width = button_width + new_name_width + (2 * date_width) + duration_width + dedication_width
        self.task_table.setMinimumWidth(new_total_width)

        self.task_table.setColumnWidth(1, new_name_width)
        self.task_table.setColumnWidth(2, date_width)
        self.task_table.setColumnWidth(3, date_width)
        self.task_table.setColumnWidth(4, duration_width)
        self.task_table.setColumnWidth(5, dedication_width)

        for i in range(6):
            self.task_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Fixed)

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

        reset_all_colors_action = menu.addAction("Restablecer colores")
        reset_all_colors_action.triggered.connect(self.reset_all_colors)

        import_menu = menu.addMenu("Importar")
        import_menu.addAction("PDF")
        import_menu.addAction("MPP")
        import_menu.addAction("XLSX")

        export_menu = menu.addMenu("Exportar")
        export_menu.addAction("PDF")
        export_menu.addAction("XLSX")

        config_menu = menu.addMenu("Configuración")
        view_menu = config_menu.addMenu("Vista")
        view_menu.addAction("Semana")
        view_menu.addAction("Mes")
        view_menu.addAction("Año")
        appearance_menu = config_menu.addMenu("Apariencia")
        appearance_menu.addAction("Modo claro")
        appearance_menu.addAction("Modo oscuro")
        language_menu = config_menu.addMenu("Idioma")
        language_menu.addAction("Español")
        language_menu.addAction("Inglés")
        language_menu.addAction("Alemán")
        language_menu.addAction("Francés")
        region_menu = config_menu.addMenu("Región")
        region_menu.addAction("Detectar automáticamente")
        region_menu.addAction("Seleccionar país")
        config_menu.addAction("API AI")
        config_menu.addAction("Abrir al iniciar el OS")
        config_menu.addAction("Alertas")

        menu.addAction("Acerca de")

        action = menu.exec(self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft()))
        if action:
            print(f"Acción seleccionada: {action.text()}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_button_size()

    def save_file(self):
        if hasattr(self, 'current_file_path') and self.current_file_path:
            success = self.save_tasks_to_file(self.current_file_path)
        else:
            success = self.save_file_as()

        if success and hasattr(self, 'main_window'):
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
                if hasattr(self, 'main_window'):
                    self.main_window.set_unsaved_changes(False)
            return success
        return False

    def open_file(self):
        if self.main_window.check_unsaved_changes():
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Abrir archivo", "", "Archivos BPM (*.bpm);;Todos los archivos (*)"
            )
            if file_path:
                self.load_tasks_from_file(file_path)

    def save_tasks_to_file(self, file_path):
        try:
            with open(file_path, 'w') as file:
                for row in range(self.task_table.rowCount()):
                    name_item = self.task_table.item(row, 1)
                    task = name_item.data(Qt.UserRole + 1)
                    if not task:
                        continue
                    file.write("[TASK]\n")
                    file.write(f"NAME: {name_item.text()}\n")
                    file.write(f"START: {task.start_date}\n")
                    file.write(f"END: {task.end_date}\n")
                    file.write(f"DURATION: {task.duration}\n")
                    dedication_widget = self.task_table.cellWidget(row, 5)
                    dedication = dedication_widget.text() if isinstance(dedication_widget, QLineEdit) else task.dedication
                    file.write(f"DEDICATION: {dedication}\n")
                    file.write(f"COLOR: {task.color.name()}\n")
                    for note_line in task.notes.split('\n'):
                        file.write(f"NOTES: {note_line}\n")
                    file.write("[/TASK]\n\n")
            self.current_file_path = file_path
            print(f"Archivo guardado en: {file_path}")
            return True
        except Exception as e:
            print(f"Error al guardar el archivo: {e}")
            return False

    def load_tasks_from_file(self, file_path):
        try:
            self.task_table.setRowCount(0)
            with open(file_path, 'r') as file:
                task_data = {}
                notes = []
                for line in file:
                    line = line.strip()
                    if line == "[TASK]":
                        task_data = {}
                        notes = []
                    elif line == "[/TASK]":
                        task_data['NOTES'] = '\n'.join(notes)
                        self.add_task_to_table(task_data, editable=False)
                    elif ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip()
                        value = value.strip()
                        if key == "NOTES":
                            notes.append(value)
                        else:
                            task_data[key] = value
            self.current_file_path = file_path
            if hasattr(self, 'main_window'):
                self.main_window.set_unsaved_changes(False)
                self.main_window.update_gantt_chart()
            print(f"Archivo cargado desde: {file_path}")
        except Exception as e:
            print(f"Error al cargar el archivo: {e}")

    def add_task_to_table(self, task_data, editable=False):
        row_position = self.task_table.rowCount()
        self.task_table.insertRow(row_position)

        state_button = StateButton()
        if not editable:
            state_button.toggle_state()
        self.task_table.setCellWidget(row_position, 0, state_button)

        task = Task(
            task_data['NAME'],
            task_data['START'],
            task_data['END'],
            task_data['DURATION'],
            task_data['DEDICATION'],
            QColor(task_data.get('COLOR', '#22a39f')),  # Usar el color especificado o el predeterminado
            task_data.get('NOTES', "")
        )

        name_item = QTableWidgetItem(task.name)
        name_item.setData(Qt.UserRole, task.color)
        name_item.setData(Qt.UserRole + 1, task)
        self.task_table.setItem(row_position, 1, name_item)

        # Fecha inicial
        start_date = QDateEdit()
        start_date.setDate(QDate.fromString(task.start_date, "dd/MM/yyyy"))
        start_date.setCalendarPopup(True)
        start_date.setDisplayFormat("dd/MM/yyyy")
        start_date.setReadOnly(not editable)
        self.task_table.setCellWidget(row_position, 2, start_date)

        # Fecha final
        end_date = QDateEdit()
        end_date.setDate(QDate.fromString(task.end_date, "dd/MM/yyyy"))
        end_date.setCalendarPopup(True)
        end_date.setDisplayFormat("dd/MM/yyyy")
        end_date.setReadOnly(not editable)
        self.task_table.setCellWidget(row_position, 3, end_date)

        # Duración
        duration = QLineEdit(task.duration)
        duration.setReadOnly(not editable)
        self.task_table.setCellWidget(row_position, 4, duration)

        # Dedicación
        dedication = QLineEdit(task.dedication)
        dedication.setReadOnly(not editable)
        dedication.textChanged.connect(self.on_dedication_changed)
        self.task_table.setCellWidget(row_position, 5, dedication)

        # Conectar señales
        start_date.dateChanged.connect(lambda: self.main_window.validateAndCalculateDays(start_date, end_date, duration))
        end_date.dateChanged.connect(lambda: self.main_window.validateAndCalculateDays(start_date, end_date, duration))
        duration.textChanged.connect(lambda: self.main_window.calculateEndDateIfChanged(start_date, duration, end_date))

        self.task_table.setRowHeight(row_position, self.main_window.ROW_HEIGHT)

        # Conectar el botón de estado con el nuevo método
        state_button.clicked.connect(self.toggle_row_state)

        if hasattr(self, 'main_window'):
            self.main_window.set_unsaved_changes(True)

    def toggle_row_state(self):
        state_button = self.sender()
        index = self.task_table.indexAt(state_button.pos())
        row = index.row()
        is_editing = state_button.is_editing
        for col in range(2, 6):  # Columnas: Fecha inicial, Fecha final, Días, Dedicación
            widget = self.task_table.cellWidget(row, col)
            if isinstance(widget, QDateEdit):
                widget.setReadOnly(not is_editing)
            elif isinstance(widget, QLineEdit):
                widget.setReadOnly(not is_editing)
        if hasattr(self, 'main_window'):
            self.main_window.set_unsaved_changes(True)

    def new_project(self):
        if hasattr(self, 'main_window') and self.main_window.unsaved_changes:
            reply = QMessageBox.question(
                self, 'Cambios sin guardar',
                'Hay cambios sin guardar. ¿Desea guardar antes de crear un nuevo proyecto?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Save
            )
            if reply == QMessageBox.Save:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                return

        # Limpiar la tabla de tareas
        self.task_table.setRowCount(0)
        # Reinicializar variables
        self.current_file_path = None
        if hasattr(self, 'main_window'):
            self.main_window.set_unsaved_changes(False)
            # Actualizar el gráfico de Gantt
            self.main_window.update_gantt_chart()
        print("Nuevo proyecto creado")

    def reset_all_colors(self):
        default_color = QColor(34, 163, 159)  # Color por defecto
        for row in range(self.task_table.rowCount()):
            name_item = self.task_table.item(row, 1)
            if name_item:
                task = name_item.data(Qt.UserRole + 1)
                if task:
                    task.color = default_color
                    name_item.setData(Qt.UserRole, default_color)

        if hasattr(self, 'main_window'):
            self.main_window.set_unsaved_changes(True)
            self.main_window.update_gantt_chart()

    def insert_task_at_position(self, row, task_data):
        # Si row es mayor que el número de filas, inserta al final
        if row > self.task_table.rowCount():
            row = self.task_table.rowCount()

        self.task_table.insertRow(row)

        state_button = StateButton()
        self.task_table.setCellWidget(row, 0, state_button)

        task = Task(
            task_data['NAME'],
            task_data['START'],
            task_data['END'],
            task_data['DURATION'],
            task_data['DEDICATION'],
            QColor(task_data['COLOR']),
            task_data.get('NOTES', "")
        )

        name_item = QTableWidgetItem(task.name)
        name_item.setData(Qt.UserRole, task.color)
        name_item.setData(Qt.UserRole + 1, task)
        self.task_table.setItem(row, 1, name_item)

        # Fecha inicial
        start_date = QDateEdit()
        start_date.setDate(QDate.fromString(task.start_date, "dd/MM/yyyy"))
        start_date.setCalendarPopup(True)
        start_date.setDisplayFormat("dd/MM/yyyy")
        self.task_table.setCellWidget(row, 2, start_date)

        # Fecha final
        end_date = QDateEdit()
        end_date.setDate(QDate.fromString(task.end_date, "dd/MM/yyyy"))
        end_date.setCalendarPopup(True)
        end_date.setDisplayFormat("dd/MM/yyyy")
        self.task_table.setCellWidget(row, 3, end_date)

        # Duración
        duration = QLineEdit(task.duration)
        self.task_table.setCellWidget(row, 4, duration)

        # Dedicación
        dedication = QLineEdit(task.dedication)
        dedication.textChanged.connect(self.on_dedication_changed)
        self.task_table.setCellWidget(row, 5, dedication)

        # Conectar señales
        start_date.dateChanged.connect(lambda: self.main_window.validateAndCalculateDays(start_date, end_date, duration))
        end_date.dateChanged.connect(lambda: self.main_window.validateAndCalculateDays(start_date, end_date, duration))
        duration.textChanged.connect(lambda: self.main_window.calculateEndDateIfChanged(start_date, duration, end_date))

        self.task_table.setRowHeight(row, self.main_window.ROW_HEIGHT)

        # Conectar el botón de estado con el nuevo método
        state_button.clicked.connect(self.toggle_row_state)

        # Después de insertar la tarea, selecciona la nueva fila
        self.task_table.selectRow(row)

        # Establecer el foco en el nombre de la nueva tarea
        self.task_table.setCurrentCell(row, 1)
        self.task_table.editItem(self.task_table.item(row, 1))

        if hasattr(self, 'main_window'):
            self.main_window.set_unsaved_changes(True)

    def sort_tasks_by_start_date(self):
        # Obtener todas las tareas
        tasks = []
        for row in range(self.task_table.rowCount()):
            name_item = self.task_table.item(row, 1)
            task = name_item.data(Qt.UserRole + 1)
            if task:
                tasks.append((task, row))

        # Ordenar las tareas por fecha de inicio
        tasks.sort(key=lambda x: QDate.fromString(x[0].start_date, "dd/MM/yyyy"))

        # Reordenar las filas en la tabla
        for new_index, (task, old_index) in enumerate(tasks):
            if new_index != old_index:
                self.task_table.insertRow(new_index)
                for col in range(self.task_table.columnCount()):
                    self.task_table.setItem(new_index, col, self.task_table.takeItem(old_index + 1, col))
                    self.task_table.setCellWidget(new_index, col, self.task_table.cellWidget(old_index + 1, col))
                self.task_table.removeRow(old_index + 1)

        # Actualizar el gráfico de Gantt
        if hasattr(self, 'main_window'):
            self.main_window.update_gantt_chart()

    def sort_tasks_by_end_date(self):
        # Obtener todas las tareas
        tasks = []
        for row in range(self.task_table.rowCount()):
            name_item = self.task_table.item(row, 1)
            task = name_item.data(Qt.UserRole + 1)
            if task:
                tasks.append((task, row))

        # Ordenar las tareas por fecha de fin
        tasks.sort(key=lambda x: QDate.fromString(x[0].end_date, "dd/MM/yyyy"))

        # Reordenar las filas en la tabla
        for new_index, (task, old_index) in enumerate(tasks):
            if new_index != old_index:
                self.task_table.insertRow(new_index)
                for col in range(self.task_table.columnCount()):
                    self.task_table.setItem(new_index, col, self.task_table.takeItem(old_index + 1, col))
                    self.task_table.setCellWidget(new_index, col, self.task_table.cellWidget(old_index + 1, col))
                self.task_table.removeRow(old_index + 1)

        # Actualizar el gráfico de Gantt
        if hasattr(self, 'main_window'):
            self.main_window.update_gantt_chart()

    def sort_tasks_by_name(self):
        # Obtener todas las tareas
        tasks = []
        for row in range(self.task_table.rowCount()):
            name_item = self.task_table.item(row, 1)
            task = name_item.data(Qt.UserRole + 1)
            if task:
                tasks.append((task, row))

        # Ordenar las tareas alfabéticamente por nombre
        tasks.sort(key=lambda x: x[0].name.lower())

        # Reordenar las filas en la tabla
        for new_index, (task, old_index) in enumerate(tasks):
            if new_index != old_index:
                self.task_table.insertRow(new_index)
                for col in range(self.task_table.columnCount()):
                    self.task_table.setItem(new_index, col, self.task_table.takeItem(old_index + 1, col))
                    self.task_table.setCellWidget(new_index, col, self.task_table.cellWidget(old_index + 1, col))
                self.task_table.removeRow(old_index + 1)

        # Actualizar el gráfico de Gantt
        if hasattr(self, 'main_window'):
            self.main_window.update_gantt_chart()

        # Marcar que se han realizado cambios
        if hasattr(self, 'main_window'):
            self.main_window.set_unsaved_changes(True)

    def on_header_click(self, logical_index):
        if logical_index == 1:  # 1 es el índice de la columna "Nombre"
            self.sort_tasks_by_name()
        elif logical_index == 2:  # 2 es el índice de la columna "Fecha inicial"
            self.sort_tasks_by_start_date()
        elif logical_index == 3:  # 3 es el índice de la columna "Fecha final"
            self.sort_tasks_by_end_date()

class MainWindow(QMainWindow):
    ROW_HEIGHT = 25

    def __init__(self):
        super().__init__()
        self.unsaved_changes = False
        self.base_title = "Baby project manager"
        self.setWindowTitle(self.base_title)
        self.setGeometry(100, 100, 1200, 800)

        self.tasks = []
        self.current_file_path = None
        self.selected_period = 365  # Por defecto, 1 año (en días)

        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.task_table_widget = TaskTableWidget(self)
        left_layout.addWidget(self.task_table_widget)
        self.task_table = self.task_table_widget.task_table

        self.task_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.task_table.customContextMenuRequested.connect(self.show_context_menu)

        add_task_button = QPushButton("Agregar Nueva Tarea")
        add_task_button.clicked.connect(self.add_new_task)
        left_layout.addWidget(add_task_button)

        left_widget.setMinimumWidth(int(self.width() * 0.43))
        main_layout.addWidget(left_widget)

        self.gantt_widget = GanttWidget(self.tasks, self.ROW_HEIGHT)
        self.gantt_header = self.gantt_widget.header
        self.gantt_chart = self.gantt_widget.chart
        self.gantt_chart.main_window = self
        self.scroll_area = self.gantt_widget.scroll_area

        # Conectar la señal colorChanged
        self.gantt_chart.colorChanged.connect(self.update_task_color)

        main_layout.addWidget(self.gantt_widget, 1)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.task_table.verticalScrollBar().valueChanged.connect(self.sync_scroll)
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.sync_scroll)

        self.adjust_all_row_heights()

        self.add_default_task()

        self.update_gantt_chart()

        from PySide6.QtGui import QKeySequence, QShortcut

        # Atajo de teclado para guardar
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.quick_save)

    def update_title(self):
        if self.unsaved_changes:
            self.setWindowTitle(f"*{self.base_title}")
        else:
            self.setWindowTitle(self.base_title)

    def set_unsaved_changes(self, value):
        if self.unsaved_changes != value:
            self.unsaved_changes = value
            self.update_title()

    def sync_scroll(self):
        sender = self.sender()
        if isinstance(sender, QScrollBar):
            if sender == self.task_table.verticalScrollBar():
                self.scroll_area.verticalScrollBar().setValue(sender.value())
            else:
                self.task_table.verticalScrollBar().setValue(sender.value())

    def add_new_task(self):
        default_color = QColor(34, 163, 159)  # Color por defecto
        task_data = {
            'NAME': "Nueva Tarea",
            'START': QDate.currentDate().toString("dd/MM/yyyy"),
            'END': QDate.currentDate().toString("dd/MM/yyyy"),
            'DURATION': "1",
            'DEDICATION': "100",
            'COLOR': default_color.name()
        }
        self.task_table_widget.add_task_to_table(task_data, editable=True)
        self.adjust_row_heights()
        self.update_gantt_chart()
        self.set_unsaved_changes(True)

    def adjust_all_row_heights(self):
        for row in range(self.task_table.rowCount()):
            self.task_table.setRowHeight(row, self.ROW_HEIGHT)

    def adjust_row_heights(self):
        for row in range(self.task_table.rowCount()):
            self.task_table.setRowHeight(row, self.ROW_HEIGHT)
        # Forzar la actualización del diseño
        self.task_table.updateGeometry()
        self.gantt_widget.chart.update()

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
        menu = QMenu()
        duplicate_action = menu.addAction("Duplicar")
        insert_action = menu.addAction("Insertar")
        move_up_action = menu.addAction("Mover arriba")
        move_down_action = menu.addAction("Mover abajo")
        delete_action = menu.addAction("Eliminar")
        reset_color_action = menu.addAction("Color por defecto")

        action = menu.exec(global_pos)
        if action == duplicate_action:
            self.duplicate_task(task_index)
        elif action == insert_action:
            self.insert_task(task_index)
        elif action == move_up_action:
            self.move_task_up(task_index)
        elif action == move_down_action:
            self.move_task_down(task_index)
        elif action == delete_action:
            self.delete_task(task_index)
        elif action == reset_color_action:
            self.reset_task_color(task_index)

    def show_context_menu(self, position):
        index = self.task_table.indexAt(position)
        if index.column() == 1:
            self.show_task_context_menu(self.task_table.viewport().mapToGlobal(position), index.row())

    def duplicate_task(self, row):
        if row >= 0:
            name_item = self.task_table.item(row, 1)
            task = name_item.data(Qt.UserRole + 1)
            if task:
                task_data = {
                    'NAME': task.name + " (copia)",
                    'START': task.start_date,
                    'END': task.end_date,
                    'DURATION': task.duration,
                    'DEDICATION': task.dedication,
                    'COLOR': task.color.name(),
                    'NOTES': task.notes
                }
                # Insertar la tarea duplicada justo después de la tarea original
                self.task_table_widget.insert_task_at_position(row + 1, task_data)
                self.update_gantt_chart()
                self.set_unsaved_changes(True)

    def insert_task(self, row):
        row += 1
        task_data = {
            'NAME': "Nueva Tarea",
            'START': QDate.currentDate().toString("dd/MM/yyyy"),
            'END': QDate.currentDate().toString("dd/MM/yyyy"),
            'DURATION': "1",
            'DEDICATION': "100",
            'COLOR': QColor(34,163,159).name()
        }
        self.task_table_widget.insert_task_at_position(row, task_data)
        self.update_gantt_chart()
        self.set_unsaved_changes(True)

        # Hacer visible la nueva tarea
        self.task_table_widget.task_table.scrollToItem(self.task_table_widget.task_table.item(row, 1))

    def move_task_up(self, row):
        if row > 0:
            self.task_table.insertRow(row - 1)
            for col in range(self.task_table.columnCount()):
                self.task_table.setItem(row - 1, col, self.task_table.takeItem(row + 1, col))
                self.task_table.setCellWidget(row - 1, col, self.task_table.cellWidget(row + 1, col))
            self.task_table.removeRow(row + 1)
            self.task_table.setCurrentCell(row - 1, 1)
            self.adjust_row_heights()
            self.set_unsaved_changes(True)
            self.update_gantt_chart()

    def move_task_down(self, row):
        if row < self.task_table.rowCount() - 1:
            self.task_table.insertRow(row + 2)
            for col in range(self.task_table.columnCount()):
                self.task_table.setItem(row + 2, col, self.task_table.takeItem(row, col))
                self.task_table.setCellWidget(row + 2, col, self.task_table.cellWidget(row, col))
            self.task_table.removeRow(row)
            self.task_table.setCurrentCell(row + 1, 1)
            self.adjust_row_heights()
            self.set_unsaved_changes(True)
            self.update_gantt_chart()

    def delete_task(self, row):
        if row >= 0:
            self.task_table.removeRow(row)
            self.set_unsaved_changes(True)
            self.update_gantt_chart()

    def reset_task_color(self, row):
        if row >= 0:
            name_item = self.task_table.item(row, 1)
            task = name_item.data(Qt.UserRole + 1)
            if task:
                default_color = QColor(34, 163, 159)  # Color por defecto
                task.color = default_color
                name_item.setData(Qt.UserRole, default_color)
                self.update_gantt_chart()
                self.set_unsaved_changes(True)

    def update_gantt_chart(self):
        self.tasks = []
        for row in range(self.task_table_widget.task_table.rowCount()):
            name_item = self.task_table_widget.task_table.item(row, 1)
            task = name_item.data(Qt.UserRole + 1)
            if task:
                task.name = name_item.text()  # Actualizar el nombre
                task.start_date = self.task_table_widget.task_table.cellWidget(row, 2).date().toString("dd/MM/yyyy")
                task.end_date = self.task_table_widget.task_table.cellWidget(row, 3).date().toString("dd/MM/yyyy")
                task.duration = self.task_table_widget.task_table.cellWidget(row, 4).text()
                dedication_widget = self.task_table_widget.task_table.cellWidget(row, 5)
                task.dedication = dedication_widget.text() if isinstance(dedication_widget, QLineEdit) else task.dedication
                task.color = name_item.data(Qt.UserRole) or QColor(34, 163, 159)
                self.tasks.append(task)

        if self.tasks:
            min_date = min(QDate.fromString(task.start_date, "dd/MM/yyyy") for task in self.tasks)
            max_date = max(QDate.fromString(task.end_date, "dd/MM/yyyy") for task in self.tasks)
        else:
            # Si no hay tareas, usar la fecha actual
            current_date = QDate.currentDate()
            min_date = current_date
            max_date = current_date.addDays(30)  # Mostrar un mes por defecto

        days_total = min_date.daysTo(max_date) + 1
        available_width = self.gantt_widget.width()
        pixels_per_day = max(0.1, available_width / days_total)

        self.gantt_widget.update_parameters(min_date, max_date, pixels_per_day)
        self.gantt_chart.tasks = self.tasks
        self.gantt_chart.setMinimumHeight(len(self.tasks) * self.ROW_HEIGHT)
        self.gantt_chart.update()
        self.gantt_header.update()

        # Forzar la actualización del diseño
        self.gantt_widget.updateGeometry()

        self.set_unsaved_changes(True)

    def update_task_color(self, task_index, color):
        name_item = self.task_table_widget.task_table.item(task_index, 1)
        if name_item:
            task = name_item.data(Qt.UserRole + 1)
            if task:
                task.color = color  # Actualizar el color en el objeto Task
            name_item.setData(Qt.UserRole, color)
            self.set_unsaved_changes(True)
            self.update_gantt_chart()

    def set_period(self, days):
        self.selected_period = days
        self.update_gantt_chart()

    def closeEvent(self, event):
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self, 'Cambios sin guardar',
                '¿Desea guardar los cambios antes de salir?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            if reply == QMessageBox.Save:
                if self.task_table_widget.save_file():
                    event.accept()
                else:
                    # Si el guardado falla, pregunta al usuario si desea salir sin guardar
                    secondary_reply = QMessageBox.question(
                        self, 'Error al guardar',
                        'No se pudieron guardar los cambios. ¿Desea salir sin guardar?',
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if secondary_reply == QMessageBox.Yes:
                        event.accept()
                    else:
                        event.ignore()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def add_default_task(self):
        today = QDate.currentDate()
        end_date = today.addDays(7)  # La tarea dura una semana por defecto
        task_data = {
            'NAME': "Tarea por defecto",
            'START': today.toString("dd/MM/yyyy"),
            'END': end_date.toString("dd/MM/yyyy"),
            'DURATION': "5",  # 5 días hábiles en una semana
            'DEDICATION': "100",
            'COLOR': QColor(34,163,159).name(),
            'NOTES': "Esta es una tarea de ejemplo."
        }
        self.task_table_widget.add_task_to_table(task_data, editable=True)
        self.adjust_row_heights()
        self.set_unsaved_changes(True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_gantt_chart()

    def check_unsaved_changes(self):
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self,
                'Cambios sin guardar',
                '¿Desea guardar los cambios antes de continuar?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            if reply == QMessageBox.Save:
                return self.task_table_widget.save_file()
            elif reply == QMessageBox.Cancel:
                return False
        return True

    def quick_save(self):
        if self.task_table_widget.save_file():
            self.set_unsaved_changes(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Usar el estilo Fusion que soporta temas oscuros/claros
    # Aplicar la paleta del sistema
    app.setPalette(app.style().standardPalette())
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
