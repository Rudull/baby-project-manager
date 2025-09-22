#gantt_views.py
#Módulo encargado de gestionar la visualización del diagrama de Gantt dentro de la
#aplicación. Contiene todas las clases y widgets relacionados con la presentación
#gráfica del cronograma, incluyendo el encabezado del Gantt, el gráfico donde se
#representan las tareas y subtareas, así como el menú flotante de edición de notas.
#
import os
import sys
import subprocess
import math
import ast
from datetime import timedelta, datetime

from workalendar.america import Colombia

from PySide6.QtCore import (
    Qt, QDate, QRect, QTimer, QSize, QRectF, QEvent, Signal, QPoint
)
from PySide6.QtGui import (
    QPainter, QColor, QBrush, QPen, QFont, QPainterPath, QPalette,
    QContextMenuEvent, QWheelEvent
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QMessageBox, QColorDialog, QTextEdit, QSizePolicy, QMenu, QApplication
)

from hipervinculo import HyperlinkTextEdit

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
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # Permitir expansión horizontal

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
            self.month_color = QColor(100, 100, 100)  # Color para los meses
            self.month_separator_color = QColor(150, 150, 150)  # Color para las líneas de los meses
            self.week_color = QColor(120, 120, 120)  # Color para las semanas
            self.week_separator_color = QColor(180, 180, 180)  # Color para las líneas de las semanas
        else:
            # Modo oscuro: usar gris claro
            self.year_color = QColor(200, 200, 200)  # Gris claro
            self.year_separator_color = QColor(160, 160, 160)  # Gris un poco más oscuro para las líneas
            self.month_color = QColor(180, 180, 180)  # Color para los meses
            self.month_separator_color = QColor(130, 130, 130)  # Color para las líneas de los meses
            self.week_color = QColor(150, 150, 150)  # Color para las semanas
            self.week_separator_color = QColor(110, 110, 110)  # Color para las líneas de las semanas

    def update_parameters(self, min_date, max_date, pixels_per_day):
        self.min_date = min_date
        self.max_date = max_date
        self.pixels_per_day = pixels_per_day
        self.update()  # Redibuja el encabezado

    def paintEvent(self, event):
        if not self.min_date or not self.max_date or not self.pixels_per_day:
            return

        with QPainter(self) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(event.rect(), self.background_color)

            total_days = self.min_date.daysTo(self.max_date)
            show_months = 30 < total_days <= 366  # Mostrar meses si el rango es entre 1 mes y 1 año
            show_weeks = total_days <= 100  # Mostrar semanas si el rango es menor o igual a 3 meses

            if show_weeks:
                year_font = QFont("Arial", 8, QFont.Weight.Bold)
                week_font = QFont("Arial", 7)
                half_height = self.height() // 2
            elif show_months:
                year_font = QFont("Arial", 9, QFont.Weight.Bold)
                month_font = QFont("Arial", 8)
                half_height = self.height() // 2
            else:
                year_font = QFont("Arial", 10, QFont.Weight.Bold)
                half_height = self.height()

            painter.setFont(year_font)

            start_year = self.min_date.year()
            end_year = self.max_date.year()

            # Dibuja los años
            for year in range(start_year, end_year + 1):
                year_start = QDate(year, 1, 1)
                if year_start < self.min_date:
                    year_start = self.min_date

                # El año termina un día antes del inicio del próximo año
                year_end = QDate(year + 1, 1, 1).addDays(-1)
                if year_end > self.max_date:
                    year_end = self.max_date

                start_x = self.min_date.daysTo(year_start) * self.pixels_per_day - self.scroll_offset
                end_x = self.min_date.daysTo(year_end.addDays(1)) * self.pixels_per_day - self.scroll_offset  # Agregar un día para incluir el último día

                # Dibuja líneas verticales para separar los años en el inicio del año
                painter.setPen(QPen(self.year_separator_color, 1))
                line_x = start_x
                painter.drawLine(int(line_x), 0, int(line_x), self.height())

                year_width = end_x - start_x
                year_rect = QRect(int(start_x), 0, int(year_width), half_height)
                painter.setPen(self.year_color)
                painter.drawText(year_rect, Qt.AlignmentFlag.AlignCenter, str(year))

            if show_weeks:
                # Dibujar semanas
                painter.setFont(week_font)
                current_date = self.min_date

                # Alinear current_date al inicio de la semana (por ejemplo, lunes)
                day_of_week = current_date.dayOfWeek()
                if day_of_week != 1:  # Si no es lunes
                    current_date = current_date.addDays(1 - day_of_week)  # Retroceder al lunes anterior

                while current_date <= self.max_date:
                    week_start = current_date
                    week_end = week_start.addDays(6)
                    if week_end > self.max_date:
                        week_end = self.max_date

                    start_x = self.min_date.daysTo(week_start) * self.pixels_per_day - self.scroll_offset
                    end_x = self.min_date.daysTo(week_end.addDays(1)) * self.pixels_per_day - self.scroll_offset  # Agregar un día para incluir el último día

                    # Dibuja líneas verticales para separar las semanas en el inicio de la semana
                    painter.setPen(QPen(self.week_separator_color, 1))
                    line_x = start_x
                    line_top = self.height() * 0.5  # Inicia la línea a la mitad del encabezado
                    painter.drawLine(int(line_x), int(line_top), int(line_x), self.height())

                    # Dibuja las etiquetas de las semanas
                    week_width = end_x - start_x
                    week_rect = QRect(int(start_x), int(line_top), int(week_width), int(self.height() - line_top))
                    week_number = week_start.weekNumber()[0]
                    week_label = f"Semana {week_number}"
                    painter.setPen(self.week_color)
                    painter.drawText(week_rect, Qt.AlignmentFlag.AlignCenter, week_label)

                    # Avanzar a la siguiente semana
                    current_date = week_end.addDays(1)

            elif show_months:
                # Dibujar meses
                painter.setFont(month_font)
                current_date = QDate(self.min_date.year(), self.min_date.month(), 1)
                while current_date <= self.max_date:
                    month_start = current_date
                    month_end = current_date.addMonths(1).addDays(-1)
                    if month_end > self.max_date:
                        month_end = self.max_date

                    start_x = self.min_date.daysTo(month_start) * self.pixels_per_day - self.scroll_offset
                    end_x = self.min_date.daysTo(month_end.addDays(1)) * self.pixels_per_day - self.scroll_offset  # Agregar un día para incluir el último día

                    # Dibuja líneas verticales para separar los meses en el inicio del mes
                    painter.setPen(QPen(self.month_separator_color, 1))
                    line_x = start_x
                    line_top = self.height() * 0.5  # Inicia la línea a la mitad del encabezado
                    painter.drawLine(int(line_x), int(line_top), int(line_x), self.height())

                    # Dibuja las etiquetas de los meses
                    month_width = end_x - start_x
                    month_rect = QRect(int(start_x), int(line_top), int(month_width), int(self.height() - line_top))
                    month_name = current_date.toString("MMM")
                    painter.setPen(self.month_color)
                    painter.drawText(month_rect, Qt.AlignmentFlag.AlignCenter, month_name)

                    # Avanzar al siguiente mes
                    current_date = current_date.addMonths(1)

            # Dibujar la etiqueta para el día de hoy
            today = QDate.currentDate()
            if self.min_date <= today <= self.max_date:
                today_x = self.min_date.daysTo(today) * self.pixels_per_day - self.scroll_offset

                # Dibuja la etiqueta "Hoy" con un fondo gris redondeado
                label_width = 50
                label_height = 20
                label_x = today_x - label_width / 2
                label_y = self.height() - label_height

                # Dibuja el fondo redondeado
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(128, 128, 128, 180))
                painter.drawRoundedRect(QRectF(label_x, label_y, label_width, label_height), 10, 10)

                # Dibuja el texto "Hoy"
                painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                painter.setPen(QColor(242, 211, 136))  # Color del texto del día de hoy
                painter.drawText(QRectF(label_x, label_y, label_width, label_height), Qt.AlignmentFlag.AlignCenter, "Hoy")

    def scrollTo(self, value):
        self.scroll_offset = value
        self.update()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.PaletteChange:
            self.update_colors()
            self.update()
        super().changeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update()  # Asegura que el widget se redibuje cuando cambia de tamaño

class GanttChart(QWidget):
    colorChanged = Signal(int, QColor)
    wheelScrolled = Signal(int)  # Nueva señal para eventos de rueda
    SINGLE_CLICK_INTERVAL = 100  # Intervalo en milisegundos para el clic simple

    def __init__(self, tasks, row_height, header_height, main_window):
        super().__init__()
        self.main_window = main_window
        self.tasks = tasks
        self.row_height = row_height
        self.header_height = header_height
        self.min_date = None
        self.max_date = None
        self.pixels_per_day = None
        self.floating_menu = None
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)  # Permitir expansión
        self.setMinimumHeight(self.header_height + self.row_height * len(tasks))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.update_colors()
        self.today_line_color = QColor(242,211,136)  # Color para la línea "Hoy"
        self.double_click_occurred = False  # Bandera para controlar doble clic
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.colorChanged.connect(self.on_color_changed)
        self.vertical_offset = 0  # Nuevo atributo para el desplazamiento vertical
        self.highlighted_task_index = None

    def update_colors(self):
        palette = self.palette()
        self.background_color = palette.color(QPalette.ColorRole.Base)
        self.task_color = palette.color(QPalette.ColorRole.Highlight)
        self.text_color = palette.color(QPalette.ColorRole.Text)
        self.grid_color = palette.color(QPalette.ColorRole.Mid)

    def update_parameters(self, min_date, max_date, pixels_per_day):
        self.min_date = min_date
        self.max_date = max_date
        self.pixels_per_day = pixels_per_day
        self.update()  # Redibuja el diagrama de Gantt

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_click_occurred = False
            # Verificar si se hizo clic fuera de una tarea
            task_index = self.get_task_at_position(event.position().toPoint())
            if task_index is None or not self.is_click_on_task_bar(event.position().toPoint(), task_index):
                self.highlighted_task_index = None
                self.update()
                # Deseleccionar cualquier selección en la tabla de tareas
                self.main_window.task_table_widget.table_view.clearSelection()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.highlighted_task_index = None
            self.update()
            self.main_window.task_table_widget.table_view.clearSelection()
        super().keyPressEvent(event)

    def mouseMoveEvent(self, event):
        task_index = self.get_task_at_position(event.position().toPoint())
        if task_index is not None and self.is_click_on_task_bar(event.position().toPoint(), task_index):
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Almacenar las posiciones
            self.click_pos = event.position().toPoint()
            self.click_global_pos = self.mapToGlobal(self.click_pos)
            # Iniciar el temporizador para el clic simple
            self.single_click_timer = QTimer()
            self.single_click_timer.setSingleShot(True)
            self.single_click_timer.timeout.connect(self.handle_single_click)
            self.single_click_timer.start(self.SINGLE_CLICK_INTERVAL)
        super().mouseReleaseEvent(event)

    def handle_single_click(self):
        if not self.double_click_occurred:
            task_index = int((self.click_pos.y() + self.vertical_offset) / self.row_height)
            if 0 <= task_index < len(self.tasks):
                task = self.tasks[task_index]
                task.name = task.name.lstrip()  # Eliminar espacios al inicio
                self.highlighted_task_index = task_index  # Resaltar la tarea
                self.update()  # Redibujar el diagrama de Gantt

                # Seleccionar la fila en la tabla de tareas
                self.main_window.task_table_widget.table_view.selectRow(task_index)
                # Asegurarse de que la fila sea visible
                self.main_window.task_table_widget.table_view.scrollTo(
                    self.main_window.task_table_widget.model.index(task_index, 0)
                )
                self.show_floating_menu(self.click_pos, task)
                task.name = task.name.lstrip()  # Eliminar espacios al inicio
        # Restablecer la bandera
        self.double_click_occurred = False

    def mouseDoubleClickEvent(self, event):
        self.double_click_occurred = True
        if hasattr(self, 'single_click_timer'):
            self.single_click_timer.stop()

        x = int(event.position().x())
        y = int(event.position().y() + self.vertical_offset)
        row_height = self.row_height

        # Determinar el índice de la tarea basada en la posición Y
        task_index = int(y / row_height)
        if 0 <= task_index < len(self.tasks):
            task = self.tasks[task_index]

            # Calcular la posición X de inicio y fin de la barra de la tarea
            start_date = QDate.fromString(task.start_date, "dd/MM/yyyy")
            end_date = QDate.fromString(task.end_date, "dd/MM/yyyy")
            task_start_x = self.min_date.daysTo(start_date) * self.pixels_per_day if self.min_date else 0
            task_end_x = self.min_date.daysTo(end_date) * self.pixels_per_day if self.min_date else 0

            # Verificar si el doble clic fue dentro de la barra de la tarea
            if task_start_x <= x <= task_end_x:
                # Abrir el diálogo de selección de color
                color = QColorDialog.getColor(initial=task.color, parent=self)
                if color.isValid():
                    # Usar el método de la ventana principal que maneja comandos
                    self.main_window.update_task_color(task_index, color, use_command=True)
        super().mouseDoubleClickEvent(event)

    def show_floating_menu(self, position, task):
        if self.floating_menu:
            self.floating_menu.close()
        # Obtener la información actualizada de la tarea
        updated_task = self.get_updated_task(task)
        self.floating_menu = FloatingTaskMenu(updated_task, self)
        self.floating_menu.notesChanged.connect(self.on_notes_changed)

        # Calcular la posición ajustada usando la pantalla principal
        menu_size = self.floating_menu.sizeHint()
        primary_screen = self.main_window.get_primary_screen()
        adjusted_position = self.adjust_menu_position(position, menu_size, primary_screen)

        self.floating_menu.move(adjusted_position)
        self.floating_menu.show()

    def adjust_menu_position(self, position, menu_size, primary_screen):
        screen_geometry = primary_screen.geometry()
        global_pos = self.mapToGlobal(position)

        # Ajustar la posición al espacio de la pantalla principal
        preferred_x = global_pos.x()
        preferred_y = global_pos.y()

        # Ajustar horizontalmente
        if preferred_x + menu_size.width() > screen_geometry.right():
            preferred_x = screen_geometry.right() - menu_size.width()
        if preferred_x < screen_geometry.left():
            preferred_x = screen_geometry.left()

        # Ajustar verticalmente
        if preferred_y + menu_size.height() > screen_geometry.bottom():
            preferred_y = preferred_y - menu_size.height()
        if preferred_y < screen_geometry.top():
            preferred_y = screen_geometry.top()

        return QPoint(preferred_x, preferred_y)

    def get_updated_task(self, task):
        for row in range(self.main_window.task_table_widget.table_view.model().rowCount()):
            index = self.main_window.task_table_widget.table_view.model().index(row, 1)
            current_task = self.main_window.task_table_widget.table_view.model().data(index, Qt.ItemDataRole.UserRole)
            if current_task == task:
                task.name = self.main_window.task_table_widget.table_view.model().data(index, Qt.ItemDataRole.DisplayRole)
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

        with QPainter(self) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(event.rect(), self.background_color)

            painter.translate(0, -self.vertical_offset)

            for i, task in enumerate(self.tasks):
                y = i * self.row_height

                # Resaltar la fila si corresponde
                if i == self.highlighted_task_index:
                    highlight_color = QColor(200, 200, 255, 50)  # Color de resaltado
                    painter.fillRect(QRectF(0, y, self.width(), self.row_height), highlight_color)

                # Dibujar la barra de la tarea
                start = QDate.fromString(task.start_date, "dd/MM/yyyy")
                end = QDate.fromString(task.end_date, "dd/MM/yyyy")
                if end < self.min_date or start > self.max_date:
                    continue

                x = self.min_date.daysTo(start) * self.pixels_per_day
                width = start.daysTo(end) * self.pixels_per_day + self.pixels_per_day  # Incluye el día final
                bar_height = self.row_height * 0.9
                bar_y = y + (self.row_height - bar_height) / 2

                if task.is_subtask:
                    # Oscurecer el color para las subtareas
                    darker_color = task.parent_task.color.darker(120)  # Oscurecer el color en 20%
                    painter.setBrush(QBrush(darker_color))
                else:
                    painter.setBrush(QBrush(task.color))

                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(QRectF(x, bar_y, width, bar_height))

                # Agregar identificadores para subtareas
                if hasattr(task, 'is_subtask') and task.is_subtask:
                    painter.setPen(QPen(self.text_color))
                    painter.setFont(QFont("Arial", 12))
                    rect = QRectF(x, y, width, self.row_height)
                    painter.drawText(rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "↳")

                # Después de dibujar la barra, verificar si tiene notas
                if task.notes_html and task.notes_html.strip():
                    # Dibujar indicador de notas (solo un pequeño círculo amarillo)
                    note_indicator_size = 8
                    note_x = x + width - note_indicator_size
                    note_y = bar_y

                    # Dibujar círculo amarillo
                    painter.setPen(QPen(QColor(242, 211, 136)))  # Amarillo
                    painter.setBrush(QBrush(QColor(242, 211, 136)))
                    painter.drawEllipse(
                        note_x, note_y,
                        note_indicator_size, note_indicator_size
                    )

            # Dibujar la línea del día de hoy
            today = QDate.currentDate()
            if self.min_date <= today <= self.max_date:
                today_x = self.min_date.daysTo(today) * self.pixels_per_day
                painter.setPen(QPen(self.today_line_color, 2))
                painter.drawLine(int(today_x), 0, int(today_x), self.height())

            # Si no hay tareas, mostrar mensaje de bienvenida (opcional)
            if not self.tasks:
                welcome_text = "Bienvenido a Baby Project Manager\nHaga clic en 'Agregar Nueva Tarea' para comenzar"
                painter.setPen(QPen(self.text_color))
                painter.setFont(QFont("Arial", 14))
                painter.drawText(event.rect(), Qt.AlignmentFlag.AlignCenter, welcome_text)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.PaletteChange:
            self.update_colors()
            self.update()
        super().changeEvent(event)

    def show_context_menu(self, position):
        task_index = self.get_task_at_position(position)
        if task_index is not None:
            # Verificar si el clic fue sobre la barra de la tarea
            if self.is_click_on_task_bar(position, task_index):
                global_pos = self.mapToGlobal(position)
                self.main_window.show_task_context_menu(global_pos, task_index)

    def is_click_on_task_bar(self, position, task_index):
        if 0 <= task_index < len(self.tasks):
            task = self.tasks[task_index]
            start_date = QDate.fromString(task.start_date, "dd/MM/yyyy")
            end_date = QDate.fromString(task.end_date, "dd/MM/yyyy")

            x = position.x()
            y = position.y() + self.vertical_offset

            task_start_x = self.min_date.daysTo(start_date) * self.pixels_per_day if self.min_date else 0
            task_end_x = self.min_date.daysTo(end_date) * self.pixels_per_day if self.min_date else 0
            task_y = task_index * self.row_height

            # Añadir un pequeño margen para facilitar el clic
            margin = 2

            if (task_start_x - margin <= x <= task_end_x + margin and
                task_y <= y <= task_y + self.row_height):
                return True

        return False

    def get_task_at_position(self, position):
        y = position.y() + self.vertical_offset
        task_index = int(y // self.row_height)
        if 0 <= task_index < len(self.tasks):
            return task_index
        return None

    def set_vertical_offset(self, offset):
        self.vertical_offset = offset
        self.update()

    def calculate_today_position(self):
        if self.min_date and self.max_date:
            today = QDate.currentDate()
            if self.min_date <= today <= self.max_date:
                total_days = self.min_date.daysTo(self.max_date)
                days_to_today = self.min_date.daysTo(today)
                return days_to_today / total_days
        return None

    def contextMenuEvent(self, event):
        self.show_context_menu(event.pos())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update()  # Asegura que el widget se redibuje cuando cambia de tamaño

class GanttWidget(QWidget):
    def __init__(self, tasks, row_height, main_window):
        super().__init__()
        self.main_window = main_window
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.header = GanttHeaderView()
        self.header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # Permitir expansión horizontal
        self.chart = GanttChart(tasks, row_height, self.header.header_height, main_window)
        self.chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)  # Permitir expansión horizontal y vertical
        self.chart.setMouseTracking(True)
        self.chart.setStyleSheet("""
            QWidget {
                font-family: Arial;
                font-size: 10px;
            }
        """)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_layout.addWidget(self.header)
        self.content_layout.addWidget(self.chart)

        self.layout.addWidget(self.content_widget)

        self.pixels_per_day = 0

        # Establecer la política de tamaño para permitir la expansión horizontal y vertical
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def update_parameters(self, min_date, max_date, pixels_per_day):
        self.min_date = min_date
        self.max_date = max_date
        self.pixels_per_day = pixels_per_day
        self.header.update_parameters(min_date, max_date, pixels_per_day)
        self.chart.update_parameters(min_date, max_date, pixels_per_day)
        self.content_widget.updateGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.min_date and self.max_date:
            days_total = self.min_date.daysTo(self.max_date) + 1
            available_width = self.width()
            self.pixels_per_day = max(0.1, available_width / days_total)
            self.update_parameters(self.min_date, self.max_date, self.pixels_per_day)

class FloatingTaskMenu(QWidget):
    notesChanged = Signal()
    notesCopied = Signal(object)
    notesPasted = Signal()

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.cal = Colombia()
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        name_label = QLabel(f"{self.task.name}")
        start_label = QLabel(f"Inicio: {self.task.start_date}")
        end_label = QLabel(f"Fin: {self.task.end_date}")

        days_left_label = QLabel(f"Días restantes: {self.calculate_working_days_left()}")

        for label in (name_label, start_label, end_label, days_left_label):
            label.setAlignment(Qt.AlignmentFlag.AlignRight)
            layout.addWidget(label)

        self.notes_edit = HyperlinkTextEdit(self)
        self.notes_edit.setAcceptRichText(True)
        self.notes_edit.hyperlink_format.setForeground(self.notes_edit.palette().link())

        # Validación añadida
        if isinstance(self.task.notes_html, str):
            self.notes_edit.setHtml(self.task.notes_html)
        else:
            print(f"Error: notes_html debe ser una cadena, pero es {type(self.task.notes_html)}. Asignando cadena vacía.")
            self.notes_edit.setHtml("")

        self.notes_edit.file_links = self.task.file_links
        self.notes_edit.setMinimumHeight(100)
        layout.addWidget(self.notes_edit)

        self.setMinimumWidth(250)
        self.setMaximumWidth(400)
        self.setMaximumHeight(300)

        self.adjustSize()
        self.update_colors()

        self.notes_edit.textChanged.connect(self.update_task_notes)
        self.notes_edit.doubleClicked.connect(self.open_hyperlink)
        self.is_editing = False
        self.original_notes_html = self.task.notes_html if self.task.notes_html else ""
        self.original_file_links = self.task.file_links.copy() if self.task.file_links else {}
        self._initializing = True
        self._last_saved_html = self.original_notes_html
        self._last_saved_links = self.original_file_links.copy()
        self._initializing = False

        # Después de layout.addWidget(self.notes_edit), agregar:
        add_link_button = QPushButton("Agregar Hipervínculo")
        add_link_button.clicked.connect(self.open_file_dialog_for_link)
        layout.addWidget(add_link_button)

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
        # Evitar procesar cambios durante la inicialización
        if getattr(self, '_initializing', False):
            return

        # Evitar procesar cambios cuando se está actualizando desde un comando
        if getattr(self, '_updating_from_command', False):
            return

        # Solo actualizar directamente durante la edición, sin crear comandos
        current_html = self.notes_edit.toHtml()
        current_text = self.notes_edit.toPlainText().strip()
        current_links = self.notes_edit.file_links.copy()

        # Normalizar HTML vacío
        if not current_text:
            current_html = ""

        # Actualización directa temporal (no permanente hasta cerrar)
        self.task.notes_html = current_html
        self.task.notes = current_text
        self.task.file_links = current_links

        self.notesChanged.emit()
        self.is_editing = True

    def update_colors(self):
        palette = self.palette()
        self.background_color = palette.color(QPalette.ColorRole.Window)
        self.text_color = palette.color(QPalette.ColorRole.WindowText)
        self.update()  # Forzar repintado

    def paintEvent(self, event):
        with QPainter(self) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(event.rect(), self.background_color)
            painter.setBrush(self.background_color)
            painter.setPen(Qt.PenStyle.NoPen)
            path = QPainterPath()
            path.addRoundedRect(QRectF(self.rect()), 10, 10)
            painter.drawPath(path)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.PaletteChange:
            self.update_colors()
            for child in self.findChildren(QLabel):
                child.setPalette(self.palette())
            self.update()
        super().changeEvent(event)

    def sizeHint(self):
        return self.layout().sizeHint()

    def toggle_editing(self):
        self.is_editing = not self.is_editing



    def closeEvent(self, event):
        """Manejar el cierre del menú flotante."""
        print(f"📝 FloatingTaskMenu cerrándose, procesando cambios finales")
        self._process_final_changes()
        super().closeEvent(event)

    def _process_final_changes(self):
        """Procesa los cambios finales y crea comando si es necesario."""
        if not hasattr(self, 'notes_edit'):
            return

        current_html = self.notes_edit.toHtml()
        current_text = self.notes_edit.toPlainText().strip()
        current_links = self.notes_edit.file_links.copy()

        # Normalizar HTML vacío
        if not current_text:
            current_html = ""

        # Solo crear comando si hay cambios reales
        original_text = self._extract_plain_text(self.original_notes_html)
        if (current_html != self.original_notes_html or
            current_links != self.original_file_links or
            current_text != original_text):

            print(f"📝 Detectados cambios en notas:")
            print(f"   HTML original: '{self.original_notes_html[:50]}...'")
            print(f"   HTML actual: '{current_html[:50]}...'")
            print(f"   Links cambiaron: {current_links != self.original_file_links}")

            # Buscar la ventana principal
            main_window = None
            parent = self.parent()
            while parent and not hasattr(parent, 'command_manager'):
                parent = parent.parent()
            if hasattr(parent, 'command_manager'):
                main_window = parent

            if main_window and not getattr(main_window, '_loading_file', False):
                print(f"📝 Creando comando EditNotesCommand")
                # Crear comando para cambio de notas
                from command_system import EditNotesCommand
                command = EditNotesCommand(
                    main_window,
                    self.task,
                    self.original_notes_html,
                    current_html,
                    self.original_file_links,
                    current_links
                )

                main_window.command_manager.execute_command(command)
            else:
                print(f"📝 No se creó comando: main_window={main_window}, loading={getattr(main_window, '_loading_file', False) if main_window else 'N/A'}")

    def _extract_plain_text(self, html_text):
        """Extrae texto plano del HTML."""
        if not html_text:
            return ""
        # Remover tags HTML básicos
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', html_text).strip()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            print(f"📝 Escape presionado, procesando cambios finales")
            self._process_final_changes()
            self.close()
        else:
            super().keyPressEvent(event)

    def open_file_dialog_for_link(self):
        try:
            print("Abriendo diálogo de selección de archivo")
            options = QFileDialog.DontUseNativeDialog  # Usar diálogo Qt en lugar del nativo
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Seleccionar archivo",
                "",
                "Todos los archivos (*.*)",
                options=options
            )
            if file_path:
                print(f"Archivo seleccionado: {file_path}")
                # Convertir a ruta normalizada del sistema
                file_path = os.path.normpath(file_path)
                file_name = os.path.basename(file_path)
                self.notes_edit.file_links[file_name] = file_path
                self.notes_edit.insertHyperlink(file_name)
            else:
                print("No se seleccionó ningún archivo")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al seleccionar archivo: {str(e)}")
            print(f"Excepción en open_file_dialog_for_link: {e}")

    def open_hyperlink(self, line):
        try:
            file_path = self.notes_edit.file_links.get(line)
            if file_path and os.path.exists(file_path):
                file_path = os.path.normpath(file_path)  # Normalizar ruta
                if sys.platform.startswith('win32'):
                    os.startfile(file_path)  # Cambiado a file_path directamente
                elif sys.platform.startswith('darwin'):
                    subprocess.run(['open', file_path], check=True)
                else:
                    subprocess.run(['xdg-open', file_path], check=True)
            else:
                QMessageBox.warning(self, "Error", "No se pudo encontrar el archivo.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo abrir el archivo: {str(e)}")

    def copy_selected_text(self):
        if self.notes_edit.textCursor().hasSelection():
            self.notes_edit.copy()
            self.notesCopied.emit(self.task)

    def paste_text(self):
        if self.notes_edit.canPaste():
            self.notes_edit.paste()
            self.notesPasted.emit()
