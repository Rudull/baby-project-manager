from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QColorDialog, QSizePolicy, QFileDialog, QMessageBox
)
from PySide6.QtGui import (
    QPainter, QColor, QBrush, QPen, QFont, QPainterPath, QPalette,
    QFontMetrics
)
from PySide6.QtCore import Qt, QDate, QRect, QRectF, Signal, QSize, QPoint
from workalendar.america import Colombia
from hipervinculo import HyperlinkTextEdit

class GanttHeaderView(QWidget):
    """Vista del encabezado del diagrama de Gantt."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.min_date = None
        self.max_date = None
        self.pixels_per_day = None
        self.header_height = 20
        self.scroll_offset = 0
        self.update_colors()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(self.header_height)

    def update_colors(self):
        """Actualiza los colores basados en el tema actual."""
        palette = self.palette()
        self.background_color = palette.color(QPalette.ColorRole.Base)
        self.text_color = palette.color(QPalette.ColorRole.Text)

        is_light_mode = palette.color(QPalette.ColorRole.Window).lightness() > 128
        if is_light_mode:
            self._set_light_theme_colors()
        else:
            self._set_dark_theme_colors()

    def _set_light_theme_colors(self):
        """Configura colores para tema claro."""
        self.year_color = QColor(80, 80, 80)
        self.year_separator_color = QColor(120, 120, 120)
        self.month_color = QColor(100, 100, 100)
        self.month_separator_color = QColor(150, 150, 150)
        self.week_color = QColor(120, 120, 120)
        self.week_separator_color = QColor(180, 180, 180)

    def _set_dark_theme_colors(self):
        """Configura colores para tema oscuro."""
        self.year_color = QColor(200, 200, 200)
        self.year_separator_color = QColor(160, 160, 160)
        self.month_color = QColor(180, 180, 180)
        self.month_separator_color = QColor(130, 130, 130)
        self.week_color = QColor(150, 150, 150)
        self.week_separator_color = QColor(110, 110, 110)

    def update_parameters(self, min_date, max_date, pixels_per_day):
        """Actualiza los parámetros de visualización."""
        self.min_date = min_date
        self.max_date = max_date
        self.pixels_per_day = pixels_per_day
        self.update()

    def paintEvent(self, event):
        """Maneja el evento de pintado del encabezado."""
        if not all([self.min_date, self.max_date, self.pixels_per_day]):
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_background(painter, event.rect())

        total_days = self.min_date.daysTo(self.max_date)
        show_months = 30 < total_days <= 366
        show_weeks = total_days <= 100

        self._setup_fonts(show_weeks, show_months)
        self._draw_timeline(painter, show_weeks, show_months)
        self._draw_today_marker(painter)

    def _draw_background(self, painter, rect):
        """Dibuja el fondo del encabezado."""
        painter.fillRect(rect, self.background_color)

    def _setup_fonts(self, show_weeks, show_months):
        """Configura las fuentes según el nivel de detalle."""
        if show_weeks:
            self.year_font = QFont("Arial", 8, QFont.Weight.Bold)
            self.detail_font = QFont("Arial", 7)
        elif show_months:
            self.year_font = QFont("Arial", 9, QFont.Weight.Bold)
            self.detail_font = QFont("Arial", 8)
        else:
            self.year_font = QFont("Arial", 10, QFont.Weight.Bold)

    def _draw_timeline(self, painter, show_weeks, show_months):
        """Dibuja la línea de tiempo con años, meses y/o semanas."""
        painter.setFont(self.year_font)
        half_height = self.height() // 2

        start_year = self.min_date.year()
        end_year = self.max_date.year()

        for year in range(start_year, end_year + 1):
            self._draw_year(painter, year, half_height)

            if show_weeks:
                self._draw_weeks(painter, year)
            elif show_months:
                self._draw_months(painter, year)

    def _draw_year(self, painter, year, half_height):
        """Dibuja un año en la línea de tiempo."""
        year_start = max(QDate(year, 1, 1), self.min_date)
        year_end = min(QDate(year + 1, 1, 1).addDays(-1), self.max_date)

        start_x = self.min_date.daysTo(year_start) * self.pixels_per_day - self.scroll_offset
        end_x = self.min_date.daysTo(year_end.addDays(1)) * self.pixels_per_day - self.scroll_offset

        # Dibujar separador de año
        painter.setPen(QPen(self.year_separator_color, 1))
        painter.drawLine(int(start_x), 0, int(start_x), self.height())

        # Dibujar etiqueta del año
        year_rect = QRectF(start_x, 0, end_x - start_x, half_height)
        painter.setPen(self.year_color)
        painter.drawText(year_rect, Qt.AlignmentFlag.AlignCenter, str(year))

    def _draw_weeks(self, painter, current_date):
        """Dibuja las semanas en la línea de tiempo."""
        painter.setFont(self.detail_font)
        while current_date <= self.max_date:
            week_start = current_date
            week_end = week_start.addDays(6)
            if week_end > self.max_date:
                week_end = self.max_date

            start_x = self.min_date.daysTo(week_start) * self.pixels_per_day - self.scroll_offset
            end_x = self.min_date.daysTo(week_end.addDays(1)) * self.pixels_per_day - self.scroll_offset

            # Dibujar separador de semana
            painter.setPen(QPen(self.week_separator_color, 1))
            line_top = self.height() * 0.5
            painter.drawLine(int(start_x), int(line_top), int(start_x), self.height())

            # Dibujar etiqueta de semana
            week_rect = QRectF(start_x, line_top, end_x - start_x, self.height() - line_top)
            week_number = week_start.weekNumber()[0]
            painter.setPen(self.week_color)
            painter.drawText(week_rect, Qt.AlignmentFlag.AlignCenter, f"Semana {week_number}")

            current_date = week_end.addDays(1)

    def _draw_months(self, painter, current_date):
        """Dibuja los meses en la línea de tiempo."""
        painter.setFont(self.detail_font)
        while current_date <= self.max_date:
            month_start = QDate(current_date.year(), current_date.month(), 1)
            month_end = month_start.addMonths(1).addDays(-1)
            if month_end > self.max_date:
                month_end = self.max_date

            start_x = self.min_date.daysTo(month_start) * self.pixels_per_day - self.scroll_offset
            end_x = self.min_date.daysTo(month_end.addDays(1)) * self.pixels_per_day - self.scroll_offset

            # Dibujar separador de mes
            painter.setPen(QPen(self.month_separator_color, 1))
            line_top = self.height() * 0.5
            painter.drawLine(int(start_x), int(line_top), int(start_x), self.height())

            # Dibujar etiqueta de mes
            month_rect = QRectF(start_x, line_top, end_x - start_x, self.height() - line_top)
            month_name = month_start.toString("MMM")
            painter.setPen(self.month_color)
            painter.drawText(month_rect, Qt.AlignmentFlag.AlignCenter, month_name)

            current_date = current_date.addMonths(1)

    def _draw_today_marker(self, painter):
        """Dibuja el marcador del día actual."""
        today = QDate.currentDate()
        if self.min_date <= today <= self.max_date:
            today_x = self.min_date.daysTo(today) * self.pixels_per_day - self.scroll_offset

            label_width = 50
            label_height = 20
            label_x = today_x - label_width / 2
            label_y = self.height() - label_height

            # Dibujar fondo
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(128, 128, 128, 180))
            painter.drawRoundedRect(QRectF(label_x, label_y, label_width, label_height), 10, 10)

            # Dibujar texto
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            painter.setPen(QColor(242, 211, 136))
            painter.drawText(QRectF(label_x, label_y, label_width, label_height),
                           Qt.AlignmentFlag.AlignCenter, "Hoy")

    def scrollTo(self, value):
        """Ajusta el desplazamiento del encabezado."""
        self.scroll_offset = value
        self.update()

    def changeEvent(self, event):
        """Maneja cambios en el widget (como cambios de tema)."""
        if event.type() == QEvent.Type.PaletteChange:
            self.update_colors()
            self.update()
        super().changeEvent(event)

class GanttChart(QWidget):
    """Widget principal del diagrama de Gantt."""

    colorChanged = Signal(int, QColor)
    wheelScrolled = Signal(int)

    def __init__(self, tasks, row_height, header_height, main_window):
        super().__init__()
        self.initialize(tasks, row_height, header_height, main_window)

    def initialize(self, tasks, row_height, header_height, main_window):
        """Inicializa los atributos del diagrama de Gantt."""
        self.tasks = tasks
        self.row_height = row_height
        self.header_height = header_height
        self.main_window = main_window
        self.min_date = None
        self.max_date = None
        self.pixels_per_day = None
        self.floating_menu = None
        self.highlighted_task_index = None
        self.wheel_accumulator = 0
        self.vertical_offset = 0

        self.setup_widget()
        self.update_colors()

    def setup_widget(self):
        """Configura las propiedades del widget."""
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(self.header_height + self.row_height * len(self.tasks))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def update_colors(self):
        """Actualiza los colores según el tema actual."""
        palette = self.palette()
        self.background_color = palette.color(QPalette.ColorRole.Base)
        self.task_color = palette.color(QPalette.ColorRole.Highlight)
        self.text_color = palette.color(QPalette.ColorRole.Text)
        self.grid_color = palette.color(QPalette.ColorRole.Mid)
        self.today_line_color = QColor(242, 211, 136)

    def paintEvent(self, event):
        """Maneja el evento de pintado del diagrama."""
        if not all([self.min_date, self.max_date, self.pixels_per_day]):
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_background(painter, event.rect())
        painter.translate(0, -self.vertical_offset)

        self._draw_tasks(painter)
        self._draw_today_line(painter)
        self._draw_welcome_message(painter, event.rect())

    def _draw_background(self, painter, rect):
        """Dibuja el fondo del diagrama."""
        painter.fillRect(rect, self.background_color)

    def _draw_tasks(self, painter):
        """Dibuja las tareas en el diagrama."""
        for i, task in enumerate(self.tasks):
            y = i * self.row_height

            # Dibujar resaltado si corresponde
            if i == self.highlighted_task_index:
                highlight_color = QColor(200, 200, 255, 50)
                painter.fillRect(QRectF(0, y, self.width(), self.row_height), highlight_color)

            # Dibujar barra de tarea
            start = QDate.fromString(task.start_date, "dd/MM/yyyy")
            end = QDate.fromString(task.end_date, "dd/MM/yyyy")

            if end < self.min_date or start > self.max_date:
                continue

            self._draw_task_bar(painter, task, start, end, y)

    def _draw_task_bar(self, painter, task, start, end, y):
        """Dibuja la barra de una tarea específica."""
        x = self.min_date.daysTo(start) * self.pixels_per_day
        width = start.daysTo(end) * self.pixels_per_day + self.pixels_per_day
        bar_height = self.row_height * 0.9
        bar_y = y + (self.row_height - bar_height) / 2

        # Dibujar la barra
        painter.setBrush(QBrush(task.color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(x, bar_y, width, bar_height), 5, 5)

        # Dibujar indicador de subtarea si corresponde
        if task.is_subtask:
            painter.setPen(QPen(self.text_color))
            painter.setFont(QFont("Arial", 12))
            rect = QRectF(x, y, width, self.row_height)
            painter.drawText(rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "↳")

    def _draw_today_line(self, painter):
        """Dibuja la línea vertical que indica el día actual."""
        today = QDate.currentDate()
        if self.min_date <= today <= self.max_date:
            today_x = self.min_date.daysTo(today) * self.pixels_per_day
            painter.setPen(QPen(self.today_line_color, 2))
            painter.drawLine(int(today_x), 0, int(today_x), self.height())

    def _draw_welcome_message(self, painter, rect):
        """Dibuja el mensaje de bienvenida si no hay tareas."""
        if not self.tasks:
            welcome_text = "Bienvenido a Baby Project Manager\nHaga clic en 'Agregar Nueva Tarea' para comenzar"
            painter.setPen(QPen(self.text_color))
            painter.setFont(QFont("Arial", 14))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, welcome_text)

    def mousePressEvent(self, event):
        """Maneja el evento de presionar el botón del mouse."""
        if event.button() == Qt.MouseButton.LeftButton:
            task_index = self.get_task_at_position(event.position().toPoint())
            if task_index is None or not self.is_click_on_task_bar(event.position().toPoint(), task_index):
                self.highlighted_task_index = None
                self.update()
                if self.main_window:
                    self.main_window.task_table_widget.table_view.clearSelection()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Maneja el evento de doble clic."""
        task_index = self.get_task_at_position(event.position().toPoint())
        if task_index is not None and self.is_click_on_task_bar(event.position().toPoint(), task_index):
            self.show_color_dialog(task_index)
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        """Maneja el evento de movimiento del mouse."""
        task_index = self.get_task_at_position(event.position().toPoint())
        if task_index is not None and self.is_click_on_task_bar(event.position().toPoint(), task_index):
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def show_color_dialog(self, task_index):
        """Muestra el diálogo de selección de color."""
        if 0 <= task_index < len(self.tasks):
            task = self.tasks[task_index]
            color = QColorDialog.getColor(initial=task.color, parent=self)
            if color.isValid():
                self.colorChanged.emit(task_index, color)

class FloatingTaskMenu(QWidget):
    """Menú flotante para mostrar detalles de una tarea."""

    notesChanged = Signal()

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.cal = Colombia()
        self.initialize_ui()
        self.setup_connections()

    def initialize_ui(self):
        """Inicializa la interfaz de usuario del menú flotante."""
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Agregar labels
        self.add_task_labels(layout)

        # Agregar editor de notas
        self.setup_notes_editor(layout)

        # Agregar botón de hipervínculo
        self.add_hyperlink_button(layout)

        self.setMinimumWidth(250)
        self.setMaximumWidth(400)
        self.setMaximumHeight(300)
        self.adjustSize()
        self.update_colors()

    def add_task_labels(self, layout):
        """Agrega las etiquetas con información de la tarea."""
        labels = [
            f"{self.task.name}",
            f"Inicio: {self.task.start_date}",
            f"Fin: {self.task.end_date}",
            f"Días restantes: {self.calculate_working_days_left()}"
        ]

        for text in labels:
            label = QLabel(text)
            label.setAlignment(Qt.AlignmentFlag.AlignRight)
            layout.addWidget(label)

    def setup_notes_editor(self, layout):
        """Configura el editor de notas."""
        self.notes_edit = HyperlinkTextEdit(self)
        self.notes_edit.setHtml(self.task.notes_html if isinstance(self.task.notes_html, str) else "")
        self.notes_edit.file_links = self.task.file_links
        self.notes_edit.setMinimumHeight(100)
        layout.addWidget(self.notes_edit)

    def add_hyperlink_button(self, layout):
        """Agrega el botón para añadir hipervínculos."""
        add_link_button = QPushButton("Agregar Hipervínculo")
        add_link_button.clicked.connect(self.open_file_dialog_for_link)
        layout.addWidget(add_link_button)

    def setup_connections(self):
        """Configura las conexiones de señales."""
        self.notes_edit.textChanged.connect(self.update_task_notes)
        self.notes_edit.doubleClicked.connect(self.open_hyperlink)

    def calculate_working_days_left(self):
        """Calcula los días laborables restantes."""
        today = datetime.now().date()
        start_date = datetime.strptime(self.task.start_date, "%d/%m/%Y").date()
        end_date = datetime.strptime(self.task.end_date, "%d/%m/%Y").date()

        if end_date < today:
            return 0

        count_from = today if start_date <= today <= end_date else start_date
        working_days = 0
        current_date = count_from

        while current_date <= end_date:
            if self.cal.is_working_day(current_date):
                working_days += 1
            current_date += timedelta(days=1)

        return working_days

    def update_task_notes(self):
        """Actualiza las notas de la tarea."""
        if self.task.notes_html != self.notes_edit.toHtml():
            self.task.notes_html = self.notes_edit.toHtml()
            self.task.notes = self.notes_edit.toPlainText()
            self.task.file_links = self.notes_edit.file_links
            self.notesChanged.emit()
            self.is_editing = True

    def open_file_dialog_for_link(self):
        """Abre el diálogo para seleccionar un archivo para vincular."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Seleccionar archivo",
                "",
                "Todos los archivos (*.*)"
            )
            if file_path:
                self.add_file_link(file_path)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al seleccionar archivo: {str(e)}")

    def add_file_link(self, file_path):
        """Añade un hipervínculo al archivo seleccionado."""
        file_path = os.path.normpath(file_path)
        file_name = os.path.basename(file_path)
        self.notes_edit.file_links[file_name] = file_path
        self.notes_edit.insertHyperlink(file_name)

    def open_hyperlink(self, file_name):
        """Abre el archivo vinculado."""
        try:
            file_path = self.notes_edit.file_links.get(file_name)
            if file_path and os.path.exists(file_path):
                self.open_file(file_path)
            else:
                QMessageBox.warning(self, "Error", "No se pudo encontrar el archivo.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo abrir el archivo: {str(e)}")

    def open_file(self, file_path):
        """Abre el archivo usando el programa predeterminado del sistema."""
        import platform
        try:
            if platform.system() == 'Windows':
                os.startfile(os.path.normpath(file_path))
            elif platform.system() == 'Darwin':
                subprocess.run(['open', file_path], check=True)
            else:
                subprocess.run(['xdg-open', file_path], check=True)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al abrir el archivo: {str(e)}")

class GanttWidget(QWidget):
    """Widget contenedor que combina el encabezado y el diagrama de Gantt."""

    def __init__(self, tasks, row_height, main_window):
        super().__init__()
        self.initialize(tasks, row_height, main_window)
        self.setup_ui()

    def initialize(self, tasks, row_height, main_window):
        """Inicializa los atributos del widget."""
        self.tasks = tasks
        self.row_height = row_height
        self.main_window = main_window
        self.pixels_per_day = 0
        self.min_date = None
        self.max_date = None

    def setup_ui(self):
        """Configura la interfaz de usuario."""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Crear y configurar el header
        self.header = GanttHeaderView()
        self.header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Crear y configurar el chart
        self.chart = GanttChart(self.tasks, self.row_height, self.header.header_height, self.main_window)
        self.chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.chart.setMouseTracking(True)

        # Configurar el contenedor
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_layout.addWidget(self.header)
        self.content_layout.addWidget(self.chart)

        self.layout.addWidget(self.content_widget)

        # Configurar políticas de tamaño
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def update_parameters(self, min_date, max_date, pixels_per_day):
        """Actualiza los parámetros de visualización."""
        self.min_date = min_date
        self.max_date = max_date
        self.pixels_per_day = pixels_per_day
        self.header.update_parameters(min_date, max_date, pixels_per_day)
        self.chart.update_parameters(min_date, max_date, pixels_per_day)
        self.content_widget.updateGeometry()

    def resizeEvent(self, event):
        """Maneja el evento de redimensionamiento."""
        super().resizeEvent(event)
        if self.min_date and self.max_date:
            self.update_pixels_per_day()

    def update_pixels_per_day(self):
        """Actualiza la escala de píxeles por día."""
        days_total = self.min_date.daysTo(self.max_date) + 1
        available_width = self.width()
        self.pixels_per_day = max(0.1, available_width / days_total)
        self.update_parameters(self.min_date, self.max_date, self.pixels_per_day)
