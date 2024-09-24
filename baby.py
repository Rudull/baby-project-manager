#se cloca en no edicion ok-7
import sys
from datetime import timedelta
from workalendar.america import Colombia
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QDateEdit, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QMenu, QScrollBar, QFileDialog, QMessageBox, QColorDialog,
    QTextEdit
)
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QPainterPath, QPalette
from PySide6.QtCore import Qt, QDate, QRect, QTimer, QSize, QRectF, QEvent, Signal

class FloatingTaskMenu(QWidget):
    notesChanged = Signal()

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        name_label = QLabel(f"{task.name}")
        start_label = QLabel(f"Inicio: {task.start_date}")
        end_label = QLabel(f"Fin: {task.end_date}")

        for label in (name_label, start_label, end_label):
            label.setAlignment(Qt.AlignmentFlag.AlignRight)
            layout.addWidget(label)

        self.notes_edit = QTextEdit(self)
        self.notes_edit.setPlainText(self.task.notes)
        self.notes_edit.setMinimumHeight(100)  # Aumentar la altura mínima
        layout.addWidget(self.notes_edit)

        self.adjustSize()
        self.update_colors()

        self.notes_edit.textChanged.connect(self.update_task_notes)

    def update_task_notes(self):
        if self.task.notes != self.notes_edit.toPlainText():
            self.task.notes = self.notes_edit.toPlainText()
            self.notesChanged.emit()  # Emite la señal cuando las notas cambian

    def update_colors(self):
        palette = self.palette()
        self.background_color = palette.color(QPalette.ColorRole.Window)
        self.text_color = palette.color(QPalette.ColorRole.WindowText)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self.background_color)
        painter.setPen(Qt.PenStyle.NoPen)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 10, 10)
        painter.drawPath(path)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.PaletteChange:
            self.update_colors()
            for child in self.findChildren(QLabel):
                child.setStyleSheet(f"color: {self.text_color.name()};")
            self.update()
        super().changeEvent(event)

from PySide6.QtGui import QMouseEvent

class StateButton(QPushButton):
    stateChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(25, 25)
        self.setStyleSheet("background-color: rgb(34,151,153);")
        self.is_editing = False
        self.subtask_level = 0
        self.has_subtasks = False
        self.is_subtask = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.toggle_color)
        self.current_color = "blue"

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.toggle_state()
        else:
            super().mousePressEvent(event)

    def toggle_state(self):
        self.is_editing = not self.is_editing
        if self.is_editing:
            self.setStyleSheet("background-color: red;")
            self.current_color = "red"
            self.timer.start(500)
        else:
            self.setStyleSheet("background-color: rgb(34,151,153);")
            self.current_color = "blue"
            self.timer.stop()
        self.stateChanged.emit(self.is_editing)

    def toggle_color(self):
        if self.is_editing:
            if self.current_color == "red":
                self.setStyleSheet("background-color: gray;")
                self.current_color = "gray"
            else:
                self.setStyleSheet("background-color: red;")
                self.current_color = "red"

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        try:
            painter.setPen(QPen(Qt.white, 2))
            if self.is_subtask:
                painter.setFont(QFont("Arial", 8))
                painter.drawText(QRect(2, 2, 21, 21), Qt.AlignCenter, f"{self.subtask_level}↳")
            if self.has_subtasks:
                painter.drawLine(7, 12, 18, 12)
        finally:
            painter.end()

    def set_subtask_level(self, level):
        self.subtask_level = level
        self.is_subtask = level > 0
        self.update()

    def set_has_subtasks(self, value):
        self.has_subtasks = value
        self.update()

class Task:
    def __init__(self, name, start_date, end_date, duration, dedication, color=None, notes=""):
        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.duration = duration
        self.dedication = dedication
        self.color = color or QColor(34, 163, 159)  # Color por defecto si no se especifica
        self.notes = notes
        self.indent_level = 0
        self.parent = None
        self.subtasks = []
        self.collapsed = False
        self.is_editing = False  # Nuevo atributo

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
        self.background_color = palette.color(QPalette.ColorRole.Base)
        self.text_color = palette.color(QPalette.ColorRole.Text)

        # Determinar si estamos en modo claro u oscuro
        is_light_mode = palette.color(QPalette.ColorRole.Window).lightness() > 128
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
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(event.rect(), self.background_color)

        year_font = QFont("Arial", 10, QFont.Weight.Bold)
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
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(128, 128, 128, 180))
            painter.drawRoundedRect(QRectF(label_x, label_y, label_width, label_height), 10, 10)

            # Dibuja el texto "Hoy"
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            painter.setPen(QColor(242,211,136)) #color del texto del día de hoy
            painter.drawText(QRectF(label_x, label_y, label_width, label_height), Qt.AlignCenter, "Hoy")

        painter.end()

    def scrollTo(self, value):
        self.scroll_offset = value
        self.update()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.PaletteChange:
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

    def update_colors(self):
        palette = self.palette()
        self.background_color = palette.color(QPalette.ColorRole.Base)
        self.task_color = palette.color(QPalette.ColorRole.Highlight)
        self.text_color = palette.color(QPalette.ColorRole.Text)
        self.grid_color = palette.color(QPalette.ColorRole.Mid)

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
        self.floating_menu = FloatingTaskMenu(task, self)
        self.floating_menu.notesChanged.connect(self.on_notes_changed)  # Conecta la señal
        self.floating_menu.move(position)
        self.floating_menu.show()

    def on_notes_changed(self):
        if hasattr(self, 'main_window'):
            self.main_window.unsaved_changes = True

    def paintEvent(self, event):
        if not self.min_date or not self.max_date or not self.pixels_per_day:
            return

        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(event.rect(), self.background_color)

            for i, task in enumerate(self.tasks):
                start = QDate.fromString(task.start_date, "dd/MM/yyyy")
                end = QDate.fromString(task.end_date, "dd/MM/yyyy")
                if end < self.min_date or start > self.max_date:
                    continue

                start = max(start.toPython(), self.min_date.toPython())
                end = min(end.toPython(), self.max_date.toPython())

                x = self.min_date.daysTo(QDate.fromString(start.strftime("%d/%m/%Y"), "dd/MM/yyyy")) * self.pixels_per_day
                width = QDate.fromString(start.strftime("%d/%m/%Y"), "dd/MM/yyyy").daysTo(QDate.fromString(end.strftime("%d/%m/%Y"), "dd/MM/yyyy")) * self.pixels_per_day
                y = i * self.row_height

                y_adjusted = y + 1

                indent_width = getattr(task, 'indent_level', 0) * 20  # Usar getattr para evitar AttributeError
                x += indent_width
                width -= indent_width

                if task.is_editing:
                    painter.setBrush(QBrush(task.color.lighter(150)))  # Color más claro para tareas en edición
                else:
                    painter.setBrush(QBrush(task.color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(QRectF(x, y_adjusted, width, self.row_height - 2))

            # Dibujar la línea vertical para el día de hoy
            today = QDate.currentDate()
            if self.min_date <= today <= self.max_date:
                today_x = self.min_date.daysTo(today) * self.pixels_per_day
                painter.setPen(QPen(self.today_line_color, 2))
                painter.drawLine(int(today_x), 0, int(today_x), self.height())
        finally:
            painter.end()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.PaletteChange:
            self.update_colors()
            self.update()
        super().changeEvent(event)

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
        self.main_window.unsaved_changes = True

    def on_item_changed(self, item):
        if item.column() in [1, 5]:  # Columna del nombre de la tarea o dedicación
            self.main_window.unsaved_changes = True

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
            self.save_tasks_to_file(self.current_file_path)
        else:
            self.save_file_as()

        if hasattr(self, 'main_window'):
            self.main_window.unsaved_changes = False

    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar como", "", "Archivos BPM (*.bpm);;Todos los archivos (*)"
        )
        if file_path:
            if not file_path.lower().endswith('.bpm'):
                file_path += '.bpm'
            self.current_file_path = file_path
            self.save_tasks_to_file(file_path)

    def open_file(self):
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
                    task = name_item.data(Qt.ItemDataRole.UserRole + 1)
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
            self.main_window.unsaved_changes = False
            print(f"Archivo guardado en: {file_path}")
        except Exception as e:
            print(f"Error al guardar el archivo: {e}")

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
            self.main_window.unsaved_changes = False
            self.main_window.update_gantt_chart()
            print(f"Archivo cargado desde: {file_path}")
        except Exception as e:
            print(f"Error al cargar el archivo: {e}")

    def add_task_to_table(self, task_data, editable=False, row=None):
        if row is None:
            row_position = self.task_table.rowCount()
            self.task_table.insertRow(row_position)
        else:
            row_position = row
            self.task_table.insertRow(row_position)

        state_button = StateButton(self.task_table)
        state_button.is_editing = editable
        if not editable:
            state_button.setStyleSheet("background-color: rgb(34,151,153);")
        else:
            state_button.setStyleSheet("background-color: red;")
            state_button.timer.start(500)
        state_button.stateChanged.connect(lambda is_editing: self.toggle_row_state(row_position, is_editing))
        self.task_table.setCellWidget(row_position, 0, state_button)

        task = Task(
            task_data['NAME'],
            task_data['START'],
            task_data['END'],
            task_data['DURATION'],
            task_data['DEDICATION'],
            QColor(task_data.get('COLOR', '#22a39f')),
            task_data.get('NOTES', "")
        )
        task.parent = task_data.get('PARENT')
        task.subtasks = []

        # Calcular el nivel de subtarea
        subtask_level = 0
        parent = task.parent
        while parent:
            subtask_level += 1
            parent = parent.parent
        state_button.set_subtask_level(subtask_level)

        # Actualizar el botón de la tarea padre
        if task.parent:
            parent_row = self.find_task_row(task.parent)
            if parent_row is not None:
                parent_button = self.task_table.cellWidget(parent_row, 0)
                parent_button.set_has_subtasks(True)

        name_item = QTableWidgetItem(task.name)
        name_item.setData(Qt.ItemDataRole.UserRole, task.color)
        name_item.setData(Qt.ItemDataRole.UserRole + 1, task)
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

        # Configurar el estado inicial de los widgets
        self.toggle_row_state(row_position, editable)

        return task

    def find_task_row(self, task):
        for row in range(self.task_table.rowCount()):
            item = self.task_table.item(row, 1)
            if item and item.data(Qt.ItemDataRole.UserRole + 1) == task:
                return row
        return None

    def toggle_row_state(self, row, is_editing):
        for col in range(2, 6):  # Columnas: Fecha inicial, Fecha final, Días, Dedicación
            widget = self.task_table.cellWidget(row, col)
            if isinstance(widget, QDateEdit):
                widget.setReadOnly(not is_editing)
            elif isinstance(widget, QLineEdit):
                widget.setReadOnly(not is_editing)

        # Actualizar el estado de edición en el objeto Task
        name_item = self.task_table.item(row, 1)
        if name_item:
            task = name_item.data(Qt.ItemDataRole.UserRole + 1)
            if task:
                task.is_editing = is_editing

        # Actualizar el gráfico de Gantt si es necesario
        if hasattr(self, 'main_window'):
            self.main_window.update_gantt_chart()

    def new_project(self):
        if self.main_window.unsaved_changes:
            reply = QMessageBox.question(
                self, 'Cambios sin guardar',
                'Hay cambios sin guardar. ¿Desea guardar antes de crear un nuevo proyecto?',
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Save
            )
            if reply == QMessageBox.StandardButton.Save:
                self.save_file()
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        # Limpiar la tabla de tareas
        self.task_table.setRowCount(0)
        # Reinicializar variables
        self.current_file_path = None
        self.main_window.unsaved_changes = False
        # Actualizar el gráfico de Gantt
        self.main_window.update_gantt_chart()
        print("Nuevo proyecto creado")

    def reset_all_colors(self):
        default_color = QColor(34, 163, 159)  # Color por defecto
        for row in range(self.task_table.rowCount()):
            name_item = self.task_table.item(row, 1)
            if name_item:
                task = name_item.data(Qt.ItemDataRole.UserRole + 1)
                if task:
                    task.color = default_color
                    name_item.setData(Qt.ItemDataRole.UserRole, default_color)

        if hasattr(self, 'main_window'):
            self.main_window.unsaved_changes = True
            self.main_window.update_gantt_chart()

    def update_task_visibility(self):
        for row in range(self.task_table.rowCount()):
            item = self.task_table.item(row, 1)
            if item:
                task = item.data(Qt.ItemDataRole.UserRole + 1)
                visible = True
                parent = task.parent
                while parent:
                    if parent.collapsed:
                        visible = False
                        break
                    parent = parent.parent
                self.task_table.setRowHidden(row, not visible)
        self.main_window.update_gantt_chart()

    def sender(self):
        return self.task_table.sender()

    def add_subtask(self):
        current_row = self.task_table.currentRow()
        if current_row >= 0:
            parent_task = self.task_table.item(current_row, 1).data(Qt.ItemDataRole.UserRole + 1)

            # Calcular el nivel de subtarea
            subtask_level = 1
            temp_parent = parent_task
            while temp_parent.parent:
                subtask_level += 1
                temp_parent = temp_parent.parent

            # Crear una nueva tarea como subtarea
            subtask_data = {
                'NAME': f"Subtarea de {parent_task.name}",
                'START': parent_task.start_date,
                'END': parent_task.end_date,
                'DURATION': parent_task.duration,
                'DEDICATION': "100",
                'COLOR': QColor(34, 163, 159).name(),
                'PARENT': parent_task
            }

            # Insertar la subtarea justo después de la tarea padre
            new_task = self.add_task_to_table(subtask_data, editable=True, row=current_row + 1)

            # Actualizar la estructura de datos
            parent_task.subtasks.append(new_task)

            # Actualizar el botón de estado de la tarea padre
            parent_button = self.task_table.cellWidget(current_row, 0)
            parent_button.set_has_subtasks(True)

            # Actualizar el botón de estado de la nueva subtarea
            new_row = current_row + 1
            state_button = self.task_table.cellWidget(new_row, 0)
            state_button.set_subtask_level(subtask_level)

            self.adjust_row_heights()
            self.main_window.update_gantt_chart()
            self.main_window.unsaved_changes = True

class MainWindow(QMainWindow):
    ROW_HEIGHT = 25

    def __init__(self):
        super().__init__()
        self.unsaved_changes = False
        self.setWindowTitle("Control de Tareas con Diagrama de Gantt")
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

        # Agregar esta línea al final del método __init__
        self.add_default_task()

        self.update_gantt_chart()

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
        self.unsaved_changes = True

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

        business_days = sum(1 for day in (start_date + timedelta(n) for n in range((end_date - start_date).days + 1))
                            if cal.is_working_day(day))
        days_entry.setText(str(business_days))
        self.unsaved_changes = True
        self.update_gantt_chart()

    def calculateEndDateIfChanged(self, start_entry, days_entry, end_entry):
        if not days_entry.text().isdigit():
            return

        cal = Colombia()
        start_date = start_entry.date().toPython()
        days = int(days_entry.text())

        end_date = start_date
        if cal.is_working_day(start_date):
            days -= 1

        while days > 0:
            end_date += timedelta(1)
            if cal.is_working_day(end_date):
                days -= 1

        end_entry.setDate(QDate(end_date))
        self.unsaved_changes = True
        self.update_gantt_chart()

    def show_context_menu(self, position):
        # Obtener el índice del ítem en la posición del clic
        index = self.task_table.indexAt(position)

        # Comprobar si el clic fue en la columna del nombre de la tarea (columna 1)
        if index.isValid() and index.column() == 1:
            menu = QMenu()
            duplicate_action = menu.addAction("Duplicar")
            insert_action = menu.addAction("Insertar")
            add_subtask_action = menu.addAction("Agregar subtarea")
            move_up_action = menu.addAction("Mover arriba")
            move_down_action = menu.addAction("Mover abajo")
            delete_action = menu.addAction("Eliminar")
            reset_color_action = menu.addAction("Color por defecto")

            action = menu.exec(self.task_table.viewport().mapToGlobal(position))
            if action == duplicate_action:
                self.duplicate_task()
            elif action == insert_action:
                self.insert_task()
            elif action == add_subtask_action:
                self.add_subtask()
            elif action == move_up_action:
                self.move_task_up()
            elif action == move_down_action:
                self.move_task_down()
            elif action == delete_action:
                self.delete_task()
            elif action == reset_color_action:
                self.reset_task_color()

    def duplicate_task(self):
        current_row = self.task_table.currentRow()
        if current_row >= 0:
            name_item = self.task_table.item(current_row, 1)
            task = name_item.data(Qt.ItemDataRole.UserRole + 1)
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
                self.task_table_widget.add_task_to_table(task_data, editable=True)
                self.update_gantt_chart()
                self.unsaved_changes = True

    def insert_task(self):
        current_row = self.task_table.currentRow()
        if current_row >= 0:
            task_data = {
                'NAME': "Nueva Tarea",
                'START': QDate.currentDate().toString("dd/MM/yyyy"),
                'END': QDate.currentDate().toString("dd/MM/yyyy"),
                'DURATION': "1",
                'DEDICATION': "100",
                'COLOR': QColor(34,163,159).name()
            }
            self.task_table_widget.add_task_to_table(task_data, editable=True)
            self.update_gantt_chart()
            self.unsaved_changes = True

    def add_subtask(self):
        current_row = self.task_table.currentRow()
        if current_row >= 0:
            parent_task = self.task_table.item(current_row, 1).data(Qt.ItemDataRole.UserRole + 1)

            # Crear una nueva tarea como subtarea
            subtask_data = {
                'NAME': f"Subtarea de {parent_task.name}",
                'START': parent_task.start_date,
                'END': parent_task.end_date,
                'DURATION': parent_task.duration,
                'DEDICATION': "100",
                'COLOR': QColor(34, 163, 159).name(),
                'PARENT': parent_task
            }

            # Insertar la subtarea justo después de la tarea padre
            new_task = self.task_table_widget.add_task_to_table(subtask_data, editable=True, row=current_row + 1)

            # Actualizar la estructura de datos
            parent_task.subtasks.append(new_task)

            # Actualizar el botón de estado de la nueva subtarea
            new_row = current_row + 1
            state_button = self.task_table.cellWidget(new_row, 0)
            state_button.set_is_subtask(True)

            self.adjust_row_heights()
            self.update_gantt_chart()
            self.unsaved_changes = True

    def move_task_up(self):
        current_row = self.task_table.currentRow()
        if current_row > 0:
            self.task_table.insertRow(current_row - 1)
            for col in range(self.task_table.columnCount()):
                self.task_table.setItem(current_row - 1, col, self.task_table.takeItem(current_row + 1, col))
                self.task_table.setCellWidget(current_row - 1, col, self.task_table.cellWidget(current_row + 1, col))
            self.task_table.removeRow(current_row + 1)
            self.task_table.setCurrentCell(current_row - 1, 1)
            self.adjust_row_heights()
            self.unsaved_changes = True
            self.update_gantt_chart()

    def move_task_down(self):
        current_row = self.task_table.currentRow()
        if current_row < self.task_table.rowCount() - 1:
            self.task_table.insertRow(current_row + 2)
            for col in range(self.task_table.columnCount()):
                self.task_table.setItem(current_row + 2, col, self.task_table.takeItem(current_row, col))
                self.task_table.setCellWidget(current_row + 2, col, self.task_table.cellWidget(current_row, col))
            self.task_table.removeRow(current_row)
            self.task_table.setCurrentCell(current_row + 1, 1)
            self.adjust_row_heights()
            self.unsaved_changes = True
            self.update_gantt_chart()

    def delete_task(self):
        current_row = self.task_table.currentRow()
        if current_row >= 0:
            task = self.task_table.item(current_row, 1).data(Qt.ItemDataRole.UserRole + 1)

            # Eliminar la tarea de la lista de subtareas de su padre
            if task.parent:
                task.parent.subtasks.remove(task)
                parent_row = self.task_table_widget.find_task_row(task.parent)
                if parent_row is not None:
                    parent_button = self.task_table.cellWidget(parent_row, 0)
                    parent_button.set_has_subtasks(bool(task.parent.subtasks))

            # Eliminar todas las subtareas
            for subtask in task.subtasks:
                subtask_row = self.task_table_widget.find_task_row(subtask)
                if subtask_row is not None:
                    self.task_table.removeRow(subtask_row)

            self.task_table.removeRow(current_row)
            self.unsaved_changes = True
            self.update_gantt_chart()

    def reset_task_color(self):
        current_row = self.task_table.currentRow()
        if current_row >= 0:
            name_item = self.task_table.item(current_row, 1)
            task = name_item.data(Qt.ItemDataRole.UserRole + 1)
            if task:
                default_color = QColor(34, 163, 159)  # Color por defecto
                task.color = default_color
                name_item.setData(Qt.ItemDataRole.UserRole, default_color)
                self.update_gantt_chart()
                self.unsaved_changes = True

    def update_gantt_chart(self):
        self.tasks = []
        for row in range(self.task_table_widget.task_table.rowCount()):
            if not self.task_table_widget.task_table.isRowHidden(row):
                name_item = self.task_table_widget.task_table.item(row, 1)
                task = name_item.data(Qt.ItemDataRole.UserRole + 1)
                if task:
                    task.name = name_item.text()
                    task.start_date = self.task_table_widget.task_table.cellWidget(row, 2).date().toString("dd/MM/yyyy")
                    task.end_date = self.task_table_widget.task_table.cellWidget(row, 3).date().toString("dd/MM/yyyy")
                    task.duration = self.task_table_widget.task_table.cellWidget(row, 4).text()
                    dedication_widget = self.task_table_widget.task_table.cellWidget(row, 5)
                    task.dedication = dedication_widget.text() if isinstance(dedication_widget, QLineEdit) else task.dedication
                    task.color = name_item.data(Qt.ItemDataRole.UserRole) or QColor(34, 163, 159)

                    # Calcular el nivel de subtarea
                    subtask_level = 0
                    parent = task.parent
                    while parent:
                        subtask_level += 1
                        parent = parent.parent

                    state_button = self.task_table_widget.task_table.cellWidget(row, 0)
                    state_button.set_subtask_level(subtask_level)
                    state_button.set_has_subtasks(bool(task.subtasks))

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

    def update_task_color(self, task_index, color):
        name_item = self.task_table_widget.task_table.item(task_index, 1)
        if name_item:
            task = name_item.data(Qt.ItemDataRole.UserRole + 1)
            if task:
                task.color = color  # Actualizar el color en el objeto Task
            name_item.setData(Qt.ItemDataRole.UserRole, color)
            self.unsaved_changes = True
            self.update_gantt_chart()

    def set_period(self, days):
        self.selected_period = days
        self.update_gantt_chart()

    def closeEvent(self, event):
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self, 'Cambios sin guardar',
                '¿Desea guardar los cambios antes de salir?',
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            if reply == QMessageBox.StandardButton.Save:
                self.task_table_widget.save_file()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
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
        self.unsaved_changes = True

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_gantt_chart()

    def update_task_hierarchy(self):
        # Este método se puede implementar más adelante para manejar la jerarquía de tareas
        # Por ahora, solo actualizamos el gráfico de Gantt
        self.update_gantt_chart()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Usar el estilo Fusion que soporta temas oscuros/claros
    # Aplicar la paleta del sistema
    app.setPalette(app.style().standardPalette())
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
