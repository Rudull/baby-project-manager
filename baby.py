import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLineEdit, QLabel, QDateEdit, QScrollArea, QTableWidget,
                               QTableWidgetItem, QHeaderView, QMenu, QScrollBar, QFileDialog, QMessageBox)
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QPainterPath, QPalette
from PySide6.QtCore import Qt, QDate, QRect, QTimer, QSize, QRectF, QEvent
from datetime import timedelta, date
from workalendar.america import Colombia

class FloatingTaskMenu(QWidget):
    def __init__(self, task_name, start_date, end_date, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        name_label = QLabel(f"<b>{task_name}</b>")
        start_label = QLabel(f"Inicio: {start_date}")
        end_label = QLabel(f"Fin: {end_date}")

        for label in (name_label, start_label, end_label):
            label.setAlignment(Qt.AlignRight)  # Alinea el texto a la derecha
            layout.addWidget(label)

        self.adjustSize()
        self.update_colors()

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
            self.setStyleSheet("background-color: blue;")

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
            self.setStyleSheet("background-color: blue;")
            self.timer.stop()

class Task:
    def __init__(self, name, start_date, end_date, dedication):
        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.dedication = dedication

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

        # Dibuja la línea vertical para el día de hoy
        today = QDate.currentDate()
        if self.min_date <= today <= self.max_date:
            today_x = self.min_date.daysTo(today) * self.pixels_per_day - self.scroll_offset
            painter.setPen(QPen(Qt.red, 2))
            painter.drawLine(int(today_x), 0, int(today_x), self.height())

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
            painter.setPen(Qt.white)
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
        self.today_line_color = QColor(255, 0, 0)  # Rojo para la línea "Hoy"

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
        width = max(0, int((max_date.daysTo(min_date) + 1) * self.pixels_per_day))
        self.setMinimumWidth(min(width, 16777215))  # Limita el ancho máximo
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            task_index = int(event.y() / self.row_height)
            if 0 <= task_index < len(self.tasks):
                task = self.tasks[task_index]
                self.show_floating_menu(event.globalPos(), task)

    def show_floating_menu(self, position, task):
        if self.floating_menu:
            self.floating_menu.close()

        self.floating_menu = FloatingTaskMenu(
            task.name,
            task.start_date,
            task.end_date,
            self
        )
        self.floating_menu.move(position)
        self.floating_menu.show()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.floating_menu:
            if not self.floating_menu.geometry().contains(event.globalPos()):
                self.floating_menu.close()
                self.floating_menu = None

    def paintEvent(self, event):
        if not self.min_date or not self.max_date or not self.pixels_per_day:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(event.rect(), self.background_color)

        for task in self.tasks:
            start = QDate.fromString(task.start_date, "dd/MM/yyyy")
            end = QDate.fromString(task.end_date, "dd/MM/yyyy")

            if end < self.min_date or start > self.max_date:
                continue

            start = max(start, self.min_date)
            end = min(end, self.max_date)

            x = self.min_date.daysTo(start) * self.pixels_per_day
            width = start.daysTo(end) * self.pixels_per_day

            y = self.tasks.index(task) * self.row_height

            painter.setBrush(QBrush(self.task_color))
            painter.setPen(Qt.NoPen)
            painter.drawRect(QRectF(x, y, width, self.row_height))

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

    def update_parameters(self, min_date, max_date, pixels_per_day):
        self.header.update_parameters(min_date, max_date, pixels_per_day)
        self.chart.update_parameters(min_date, max_date, pixels_per_day)
        self.content_widget.setFixedWidth(self.chart.width())

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

    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar como",
            "",
            "Archivos BPM (*.bpm);;Todos los archivos (*)"
        )
        if file_path:
            if not file_path.lower().endswith('.bpm'):
                file_path += '.bpm'
            self.current_file_path = file_path
            self.save_tasks_to_file(file_path)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir archivo",
            "",
            "Archivos BPM (*.bpm);;Todos los archivos (*)"
        )
        if file_path:
            self.load_tasks_from_file(file_path)

    def save_tasks_to_file(self, file_path):
        try:
            with open(file_path, 'w') as file:
                for row in range(self.task_table.rowCount()):
                    task_name = self.task_table.item(row, 1).text()
                    start_date = self.task_table.cellWidget(row, 2).date().toString("dd/MM/yyyy")
                    end_date = self.task_table.cellWidget(row, 3).date().toString("dd/MM/yyyy")
                    duration = self.task_table.cellWidget(row, 4).text()
                    dedication = self.task_table.cellWidget(row, 5).text()

                    file.write("[TASK]\n")
                    file.write(f"NAME: {task_name}\n")
                    file.write(f"START: {start_date}\n")
                    file.write(f"END: {end_date}\n")
                    file.write(f"DURATION: {duration}\n")
                    file.write(f"DEDICATION: {dedication}\n")
                    file.write("[/TASK]\n\n")

            self.current_file_path = file_path
            self.main_window.unsaved_changes = False
            print(f"Archivo guardado en: {file_path}")
        except Exception as e:
            print(f"Error al guardar el archivo: {e}")

    def load_tasks_from_file(self, file_path):
        try:
            self.task_table.setRowCount(0)  # Limpia la tabla actual
            with open(file_path, 'r') as file:
                task_data = {}
                for line in file:
                    line = line.strip()
                    if line == "[TASK]":
                        task_data = {}
                    elif line == "[/TASK]":
                        self.add_task_to_table(task_data, editable=False)  # Cargar en modo no editable
                    elif ":" in line:
                        key, value = line.split(":", 1)
                        task_data[key.strip()] = value.strip()

            self.current_file_path = file_path
            self.main_window.unsaved_changes = False
            self.main_window.update_gantt_chart()
            print(f"Archivo cargado desde: {file_path}")
        except Exception as e:
            print(f"Error al cargar el archivo: {e}")

    def add_task_to_table(self, task_data, editable=False):
        row_position = self.task_table.rowCount()
        self.task_table.insertRow(row_position)

        # Botón de estado
        state_button = StateButton()
        if not editable:
            state_button.toggle_state()  # Cambia al estado no editable
        self.task_table.setCellWidget(row_position, 0, state_button)

        # Nombre de la tarea
        self.task_table.setItem(row_position, 1, QTableWidgetItem(task_data['NAME']))

        # Fecha inicial
        start_date = QDateEdit()
        start_date.setDate(QDate.fromString(task_data['START'], "dd/MM/yyyy"))
        start_date.setCalendarPopup(True)
        start_date.setDisplayFormat("dd/MM/yyyy")
        start_date.setReadOnly(not editable)
        self.task_table.setCellWidget(row_position, 2, start_date)

        # Fecha final
        end_date = QDateEdit()
        end_date.setDate(QDate.fromString(task_data['END'], "dd/MM/yyyy"))
        end_date.setCalendarPopup(True)
        end_date.setDisplayFormat("dd/MM/yyyy")
        end_date.setReadOnly(not editable)
        self.task_table.setCellWidget(row_position, 3, end_date)

        # Duración
        duration = QLineEdit(task_data['DURATION'])
        duration.setReadOnly(not editable)
        self.task_table.setCellWidget(row_position, 4, duration)

        # Dedicación
        dedication = QLineEdit(task_data['DEDICATION'])
        dedication.setReadOnly(not editable)
        self.task_table.setCellWidget(row_position, 5, dedication)

        # Conectar señales
        start_date.dateChanged.connect(lambda: self.main_window.validateAndCalculateDays(start_date, end_date, duration))
        end_date.dateChanged.connect(lambda: self.main_window.validateAndCalculateDays(start_date, end_date, duration))
        duration.textChanged.connect(lambda: self.main_window.calculateEndDateIfChanged(start_date, duration, end_date))

        self.task_table.setRowHeight(row_position, self.main_window.ROW_HEIGHT)

        # Conectar el botón de estado con la función de toggle
        state_button.clicked.connect(lambda: self.toggle_row_state(row_position))

    def toggle_row_state(self, row):
        state_button = self.task_table.cellWidget(row, 0)
        is_editable = state_button.is_editing

        for col in range(2, 6):  # Columnas de fecha inicial, fecha final, días y dedicación
            widget = self.task_table.cellWidget(row, col)
            if isinstance(widget, QDateEdit):
                widget.setReadOnly(not is_editable)
            elif isinstance(widget, QLineEdit):
                widget.setReadOnly(not is_editable)

    def new_project(self):
        if self.main_window.unsaved_changes:
            reply = QMessageBox.question(
                self,
                'Cambios sin guardar',
                '¿Hay cambios sin guardar. ¿Desea guardar antes de crear un nuevo proyecto?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )

            if reply == QMessageBox.Save:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                return

        # Limpiar la tabla de tareas
        self.task_table.setRowCount(0)

        # Reinicializar variables
        self.current_file_path = None
        self.main_window.unsaved_changes = False

        # Actualizar el gráfico de Gantt
        self.main_window.update_gantt_chart()

        print("Nuevo proyecto creado")

class Task:
    def __init__(self, name, start_date, end_date, duration, dedication):
        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.duration = duration
        self.dedication = dedication

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir archivo",
            "",
            "Archivos de texto (*.txt);;Archivos CSV (*.csv);;Todos los archivos (*.*)"
        )
        if file_path:
            self.load_tasks_from_file(file_path)

    def load_tasks_from_file(self, file_path):
        try:
            self.task_table.setRowCount(0)  # Limpia la tabla actual
            with open(file_path, 'r') as file:
                lines = file.readlines()
                for line in lines[1:]:  # Ignora la primera línea si es un encabezado
                    task_data = line.strip().split(',')
                    if len(task_data) == 5:  # Asegúrate de que haya 5 campos
                        self.add_task_to_table(task_data)
            self.current_file_path = file_path
            self.main_window.unsaved_changes = False
            print(f"Archivo cargado desde: {file_path}")
            self.main_window.update_gantt_chart()
        except Exception as e:
            print(f"Error al cargar el archivo: {e}")

    def add_task_to_table(self, task_data):
        row_position = self.task_table.rowCount()
        self.task_table.insertRow(row_position)

        # Botón de estado
        state_button = StateButton()
        self.task_table.setCellWidget(row_position, 0, state_button)

        # Nombre de la tarea
        self.task_table.setItem(row_position, 1, QTableWidgetItem(task_data[0]))

        # Fecha inicial
        start_date = QDateEdit()
        start_date.setDate(QDate.fromString(task_data[1], "dd/MM/yyyy"))
        start_date.setCalendarPopup(True)
        start_date.setDisplayFormat("dd/MM/yyyy")
        self.task_table.setCellWidget(row_position, 2, start_date)

        # Fecha final
        end_date = QDateEdit()
        end_date.setDate(QDate.fromString(task_data[2], "dd/MM/yyyy"))
        end_date.setCalendarPopup(True)
        end_date.setDisplayFormat("dd/MM/yyyy")
        self.task_table.setCellWidget(row_position, 3, end_date)

        # Duración
        duration = QLineEdit(task_data[3])
        self.task_table.setCellWidget(row_position, 4, duration)

        # Dedicación
        dedication = QLineEdit(task_data[4])
        self.task_table.setCellWidget(row_position, 5, dedication)

        # Conectar señales
        start_date.dateChanged.connect(lambda: self.main_window.validateAndCalculateDays(start_date, end_date, duration))
        end_date.dateChanged.connect(lambda: self.main_window.validateAndCalculateDays(start_date, end_date, duration))
        duration.textChanged.connect(lambda: self.main_window.calculateEndDateIfChanged(start_date, duration, end_date))

        self.task_table.setRowHeight(row_position, self.main_window.ROW_HEIGHT)

class MainWindow(QMainWindow):
    ROW_HEIGHT = 25

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control de Tareas con Diagrama de Gantt")
        self.setGeometry(100, 100, 1200, 800)

        self.tasks = []
        self.unsaved_changes = False
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
        self.scroll_area = self.gantt_widget.scroll_area

        main_layout.addWidget(self.gantt_widget, 1)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.task_table.verticalScrollBar().valueChanged.connect(self.sync_scroll)
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.sync_scroll)

        self.adjust_all_row_heights()
        self.update_gantt_chart()

    def sync_scroll(self):
        sender = self.sender()
        if isinstance(sender, QScrollBar):
            if sender == self.task_table.verticalScrollBar():
                self.scroll_area.verticalScrollBar().setValue(sender.value())
            else:
                self.task_table.verticalScrollBar().setValue(sender.value())

    def create_state_button(self):
        button = StateButton()
        button.clicked.connect(lambda: self.toggle_row_state(button))
        return button

    def toggle_row_state(self, button):
        row = self.task_table.indexAt(button.pos()).row()
        is_editing = button.is_editing
        for col in range(2, 6):  # Columnas de fecha inicial, fecha final, días y dedicación
            widget = self.task_table.cellWidget(row, col)
            if isinstance(widget, QDateEdit):
                widget.setReadOnly(not is_editing)
            elif isinstance(widget, QLineEdit):
                widget.setReadOnly(not is_editing)

    def add_new_task(self):
        task_data = {
            'NAME': "Nueva Tarea",
            'START': QDate.currentDate().toString("dd/MM/yyyy"),
            'END': QDate.currentDate().toString("dd/MM/yyyy"),
            'DURATION': "1",
            'DEDICATION': "100"
        }
        self.task_table_widget.add_task_to_table(task_data, editable=True)
        self.update_gantt_chart()
        self.unsaved_changes = True

    def adjust_all_row_heights(self):
        for row in range(self.task_table.rowCount()):
            self.task_table.setRowHeight(row, self.ROW_HEIGHT)

    def validateAndCalculateDays(self, start_entry, end_entry, days_entry):
        cal = Colombia()
        start_date = start_entry.date().toPython()
        end_date = end_entry.date().toPython()

        if end_date < start_date:
            end_entry.setDate(QDate(start_date))
            end_date = start_date

        business_days = sum(1 for day in (start_date + timedelta(n) for n in range((end_date - start_date).days + 1)) if cal.is_working_day(day))
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
        menu = QMenu()
        duplicate_action = menu.addAction("Duplicar")
        insert_action = menu.addAction("Insertar")
        move_up_action = menu.addAction("Mover arriba")
        move_down_action = menu.addAction("Mover abajo")
        delete_action = menu.addAction("Eliminar")

        action = menu.exec(self.task_table.viewport().mapToGlobal(position))

        if action == duplicate_action:
            self.duplicate_task()
        elif action == insert_action:
            self.insert_task()
        elif action == move_up_action:
            self.move_task_up()
        elif action == move_down_action:
            self.move_task_down()
        elif action == delete_action:
            self.delete_task()

    def duplicate_task(self):
        current_row = self.task_table.currentRow()
        if current_row >= 0:
            task_data = {
                'NAME': self.task_table.item(current_row, 1).text() + " (copia)",
                'START': self.task_table.cellWidget(current_row, 2).date().toString("dd/MM/yyyy"),
                'END': self.task_table.cellWidget(current_row, 3).date().toString("dd/MM/yyyy"),
                'DURATION': self.task_table.cellWidget(current_row, 4).text(),
                'DEDICATION': self.task_table.cellWidget(current_row, 5).text()
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
                'DEDICATION': "100"
            }
            self.task_table_widget.add_task_to_table(task_data, editable=True)
            self.update_gantt_chart()
            self.unsaved_changes = True

    def move_task_up(self):
        current_row = self.task_table.currentRow()
        if current_row > 0:
            self.task_table.insertRow(current_row - 1)
            for col in range(self.task_table.columnCount()):
                if col == 0:
                    widget = self.task_table.cellWidget(current_row + 1, col)
                    new_widget = self.create_state_button()
                    new_widget.toggle_state()  # Para aplicar el estilo correcto
                    self.task_table.setCellWidget(current_row - 1, col, new_widget)
                else:
                    self.task_table.setItem(current_row - 1, col, self.task_table.takeItem(current_row + 1, col))
                    self.task_table.setCellWidget(current_row - 1, col, self.task_table.cellWidget(current_row + 1, col))
            self.task_table.removeRow(current_row + 1)
            self.task_table.setCurrentCell(current_row - 1, 1)
            self.unsaved_changes = True
            self.update_gantt_chart()

    def move_task_down(self):
        current_row = self.task_table.currentRow()
        if current_row < self.task_table.rowCount() - 1:
            self.task_table.insertRow(current_row + 2)
            for col in range(self.task_table.columnCount()):
                if col == 0:
                    widget = self.task_table.cellWidget(current_row, col)
                    new_widget = self.create_state_button()
                    new_widget.toggle_state()  # Para aplicar el estilo correcto
                    self.task_table.setCellWidget(current_row + 2, col, new_widget)
                else:
                    self.task_table.setItem(current_row + 2, col, self.task_table.takeItem(current_row, col))
                    self.task_table.setCellWidget(current_row + 2, col, self.task_table.cellWidget(current_row, col))
            self.task_table.removeRow(current_row)
            self.task_table.setCurrentCell(current_row + 1, 1)
            self.unsaved_changes = True
            self.update_gantt_chart()

    def delete_task(self):
        current_row = self.task_table.currentRow()
        if current_row >= 0:
            self.task_table.removeRow(current_row)
            self.unsaved_changes = True
            self.update_gantt_chart()

    def update_gantt_chart(self):
        self.tasks = []
        for row in range(self.task_table_widget.task_table.rowCount()):
            name = self.task_table_widget.task_table.item(row, 1).text()
            start_date = self.task_table_widget.task_table.cellWidget(row, 2).date().toString("dd/MM/yyyy")
            end_date = self.task_table_widget.task_table.cellWidget(row, 3).date().toString("dd/MM/yyyy")
            duration = self.task_table_widget.task_table.cellWidget(row, 4).text()
            dedication = self.task_table_widget.task_table.cellWidget(row, 5).text()
            task = Task(name, start_date, end_date, duration, dedication)
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
        available_width = max(1, self.scroll_area.viewport().width())
        pixels_per_day = max(0.1, available_width / days_total)

        self.gantt_widget.update_parameters(min_date, max_date, pixels_per_day)
        self.gantt_chart.tasks = self.tasks

        self.gantt_chart.update()
        self.gantt_header.update()

    def set_period(self, days):
        self.selected_period = days
        self.update_gantt_chart()

    def load_tasks_from_db(self):
        # Implementar la carga de tareas desde la base de datos
        pass

    def save_task_to_db(self, task):
        # Implementar el guardado de tareas en la base de datos
        pass

    def closeEvent(self, event):
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self,
                'Cambios sin guardar',
                '¿Hay cambios sin guardar. ¿Desea guardar antes de salir?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )

            if reply == QMessageBox.Save:
                self.task_table_widget.save_file()
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Usar el estilo Fusion que soporta temas oscuros/claros
    # Aplicar la paleta del sistema
    app.setPalette(app.style().standardPalette())
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
