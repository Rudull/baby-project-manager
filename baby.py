import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLineEdit, QLabel, QDateEdit, QScrollArea, QTableWidget,
                               QTableWidgetItem, QHeaderView, QMenu, QScrollBar)
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QAction
from PySide6.QtCore import Qt, QDate, QRect, QTimer, QSize
from datetime import timedelta
from workalendar.america import Colombia

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

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_state()
        super().mousePressEvent(event)

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

class GanttChart(QWidget):
    def __init__(self, tasks, row_height, header_height):
        super().__init__()
        self.tasks = tasks
        self.row_height = row_height
        self.header_height = header_height
        self.setMinimumHeight(self.header_height + self.row_height * len(tasks))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        background_color = QColor(240, 240, 240)
        task_color = QColor(100, 150, 200)
        year_color = QColor(50, 50, 50)
        year_font = QFont("Arial", 10, QFont.Weight.Bold)

        painter.fillRect(event.rect(), background_color)

        if not self.tasks:
            return

        min_date = min((QDate.fromString(task.start_date, "dd/MM/yyyy") for task in self.tasks), key=lambda x: x.toJulianDay())
        max_date = max((QDate.fromString(task.end_date, "dd/MM/yyyy") for task in self.tasks), key=lambda x: x.toJulianDay())

        days_total = min_date.daysTo(max_date) + 1
        pixels_per_day = max(1, self.width() / days_total)

        painter.setFont(year_font)
        painter.setPen(year_color)
        year = min_date.year()
        year_width = 365 * pixels_per_day
        x = 0
        while x < self.width():
            painter.drawText(QRect(int(x), 0, int(year_width), self.header_height),
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(year))
            x += year_width
            year += 1

        y = self.header_height
        for task in self.tasks:
            start = QDate.fromString(task.start_date, "dd/MM/yyyy")
            end = QDate.fromString(task.end_date, "dd/MM/yyyy")
            duration = start.daysTo(end) + 1
            x = min_date.daysTo(start) * pixels_per_day

            painter.setBrush(QBrush(task_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(QRect(int(x), y, int(duration * pixels_per_day), self.row_height))

            y += self.row_height

        painter.end()

class TaskTableWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

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
            self.task_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)

    def show_menu(self):
        menu = QMenu(self)

        menu.addAction("Guardar")
        menu.addAction("Guardar como")
        menu.addAction("Nuevo")
        menu.addAction("Abrir")

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

class MainWindow(QMainWindow):
    ROW_HEIGHT = 25

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control de Tareas con Diagrama de Gantt")
        self.setGeometry(100, 100, 1200, 800)

        self.tasks = []
        self.load_tasks_from_db()

        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.task_table_widget = TaskTableWidget()
        left_layout.addWidget(self.task_table_widget)
        self.task_table = self.task_table_widget.task_table

        self.task_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_table.customContextMenuRequested.connect(self.show_context_menu)

        add_task_button = QPushButton("Agregar Nueva Tarea")
        add_task_button.clicked.connect(self.add_new_task)
        left_layout.addWidget(add_task_button)

        left_widget.setMinimumWidth(int(self.width() * 0.43))
        main_layout.addWidget(left_widget)

        gantt_widget = QWidget()
        gantt_layout = QVBoxLayout(gantt_widget)
        gantt_layout.setContentsMargins(0, 0, 0, 0)
        gantt_layout.setSpacing(0)

        header_height = self.task_table.horizontalHeader().height()
        self.gantt_chart = GanttChart(self.tasks, self.ROW_HEIGHT, header_height)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.gantt_chart)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        gantt_layout.addWidget(self.scroll_area)

        main_layout.addWidget(gantt_widget, 1)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.task_table.verticalScrollBar().valueChanged.connect(self.sync_scroll)
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.sync_scroll)

        self.adjust_all_row_heights()

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
        row_position = self.task_table.rowCount()
        self.task_table.insertRow(row_position)

        self.task_table.setRowHeight(row_position, self.ROW_HEIGHT)

        state_button = self.create_state_button()
        self.task_table.setCellWidget(row_position, 0, state_button)

        self.task_table.setItem(row_position, 1, QTableWidgetItem("Nueva Tarea"))

        start_date = QDateEdit()
        start_date.setDate(QDate.currentDate())
        start_date.setCalendarPopup(True)
        start_date.setDisplayFormat("dd/MM/yyyy")
        self.task_table.setCellWidget(row_position, 2, start_date)

        end_date = QDateEdit()
        end_date.setDate(QDate.currentDate())
        end_date.setCalendarPopup(True)
        end_date.setDisplayFormat("dd/MM/yyyy")
        self.task_table.setCellWidget(row_position, 3, end_date)

        duration = QLineEdit("1")
        self.task_table.setCellWidget(row_position, 4, duration)

        dedication = QLineEdit("100")
        self.task_table.setCellWidget(row_position, 5, dedication)

        start_date.dateChanged.connect(lambda: self.validateAndCalculateDays(start_date, end_date, duration))
        end_date.dateChanged.connect(lambda: self.validateAndCalculateDays(start_date, end_date, duration))
        duration.textChanged.connect(lambda: self.calculateEndDateIfChanged(start_date, duration, end_date))

        self.update_gantt_chart()

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
            self.task_table.insertRow(current_row + 1)

            # Crear un nuevo botón de estado en modo de edición
            new_state_button = self.create_state_button()
            self.task_table.setCellWidget(current_row + 1, 0, new_state_button)

            for col in range(1, self.task_table.columnCount()):
                if col == 1:
                    new_item = QTableWidgetItem(self.task_table.item(current_row, col).text() + " (copia)")
                    self.task_table.setItem(current_row + 1, col, new_item)
                elif col in [2, 3]:
                    original_widget = self.task_table.cellWidget(current_row, col)
                    new_widget = QDateEdit()
                    new_widget.setDate(original_widget.date())
                    new_widget.setCalendarPopup(True)
                    new_widget.setDisplayFormat("dd/MM/yyyy")
                    self.task_table.setCellWidget(current_row + 1, col, new_widget)
                else:
                    original_widget = self.task_table.cellWidget(current_row, col)
                    new_widget = QLineEdit(original_widget.text())
                    self.task_table.setCellWidget(current_row + 1, col, new_widget)

            self.task_table.setRowHeight(current_row + 1, self.ROW_HEIGHT)

            # Obtener los widgets de la nueva fila
            start_date = self.task_table.cellWidget(current_row + 1, 2)
            end_date = self.task_table.cellWidget(current_row + 1, 3)
            duration = self.task_table.cellWidget(current_row + 1, 4)

            # Conectar las señales para la nueva fila
            start_date.dateChanged.connect(lambda: self.validateAndCalculateDays(start_date, end_date, duration))
            end_date.dateChanged.connect(lambda: self.validateAndCalculateDays(start_date, end_date, duration))
            duration.textChanged.connect(lambda: self.calculateEndDateIfChanged(start_date, duration, end_date))

            self.update_gantt_chart()

    def insert_task(self):
        current_row = self.task_table.currentRow()
        if current_row >= 0:
            self.task_table.insertRow(current_row + 1)

            state_button = self.create_state_button()
            self.task_table.setCellWidget(current_row + 1, 0, state_button)

            self.task_table.setItem(current_row + 1, 1, QTableWidgetItem("Nueva Tarea"))

            start_date = QDateEdit()
            start_date.setDate(QDate.currentDate())
            start_date.setCalendarPopup(True)
            start_date.setDisplayFormat("dd/MM/yyyy")
            self.task_table.setCellWidget(current_row + 1, 2, start_date)

            end_date = QDateEdit()
            end_date.setDate(QDate.currentDate())
            end_date.setCalendarPopup(True)
            end_date.setDisplayFormat("dd/MM/yyyy")
            self.task_table.setCellWidget(current_row + 1, 3, end_date)

            duration = QLineEdit("1")
            self.task_table.setCellWidget(current_row + 1, 4, duration)

            dedication = QLineEdit("100")
            self.task_table.setCellWidget(current_row + 1, 5, dedication)

            start_date.dateChanged.connect(lambda: self.validateAndCalculateDays(start_date, end_date, duration))
            end_date.dateChanged.connect(lambda: self.validateAndCalculateDays(start_date, end_date, duration))
            duration.textChanged.connect(lambda: self.calculateEndDateIfChanged(start_date, duration, end_date))

            self.task_table.setRowHeight(current_row + 1, self.ROW_HEIGHT)
            self.update_gantt_chart()

    def move_task_up(self):
        current_row = self.task_table.currentRow()
        if current_row > 0:
            self.task_table.insertRow(current_row - 1)
            for col in range(self.task_table.columnCount()):
                if col == 0:
                    widget = self.task_table.cellWidget(current_row + 1, col)
                    new_widget = self.create_state_button()
                    #new_widget.is_editing = widget.is_editing
                    new_widget.toggle_state()  # Para aplicar el estilo correcto
                    self.task_table.setCellWidget(current_row - 1, col, new_widget)
                else:
                    self.task_table.setItem(current_row - 1, col, self.task_table.takeItem(current_row + 1, col))
                    self.task_table.setCellWidget(current_row - 1, col, self.task_table.cellWidget(current_row + 1, col))
            self.task_table.removeRow(current_row + 1)
            self.task_table.setCurrentCell(current_row - 1, 1)
            self.update_gantt_chart()

    def move_task_down(self):
        current_row = self.task_table.currentRow()
        if current_row < self.task_table.rowCount() - 1:
            self.task_table.insertRow(current_row + 2)
            for col in range(self.task_table.columnCount()):
                if col == 0:
                    widget = self.task_table.cellWidget(current_row, col)
                    new_widget = self.create_state_button()
                    #new_widget.is_editing = widget.is_editing
                    new_widget.toggle_state()  # Para aplicar el estilo correcto
                    self.task_table.setCellWidget(current_row + 2, col, new_widget)
                else:
                    self.task_table.setItem(current_row + 2, col, self.task_table.takeItem(current_row, col))
                    self.task_table.setCellWidget(current_row + 2, col, self.task_table.cellWidget(current_row, col))
            self.task_table.removeRow(current_row)
            self.task_table.setCurrentCell(current_row + 1, 1)
            self.update_gantt_chart()

    def delete_task(self):
        current_row = self.task_table.currentRow()
        if current_row >= 0:
            self.task_table.removeRow(current_row)
            self.update_gantt_chart()

    def update_gantt_chart(self):
        self.tasks = []
        for row in range(self.task_table.rowCount()):
            name = self.task_table.item(row, 1).text()
            start_date = self.task_table.cellWidget(row, 2).date().toString("dd/MM/yyyy")
            end_date = self.task_table.cellWidget(row, 3).date().toString("dd/MM/yyyy")
            dedication = self.task_table.cellWidget(row, 5).text()
            task = Task(name, start_date, end_date, dedication)
            self.tasks.append(task)

        header_height = self.task_table.horizontalHeader().height()
        self.gantt_chart.tasks = self.tasks
        self.gantt_chart.row_height = self.ROW_HEIGHT
        self.gantt_chart.header_height = header_height
        self.gantt_chart.setMinimumHeight(header_height +
                                          self.gantt_chart.row_height * len(self.tasks))
        self.gantt_chart.update()

    def load_tasks_from_db(self):
        # Implementar la carga de tareas desde la base de datos
        pass

    def save_task_to_db(self, task):
        # Implementar el guardado de tareas en la base de datos
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
