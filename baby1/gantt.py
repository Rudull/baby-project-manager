# Este archivo contendrá las clases necesarias para manejar la visualización y la interacción con el diagrama de Gantt
# gantt.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QPainterPath
from PySide6.QtCore import Qt, QDate, QRect, QRectF, QPoint, Signal, QEvent, QSize
from models import Task
from datetime import datetime, timedelta
from PySide6.QtWidgets import QApplication, QLabel

class GanttHeaderView(QWidget):
    """
    Vista de encabezado para el diagrama de Gantt que muestra las fechas.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.min_date = None
        self.max_date = None
        self.pixels_per_day = 0
        self.header_height = 50  # Altura fija para el encabezado

    def update_parameters(self, min_date, max_date, pixels_per_day):
        """
        Actualiza los parámetros del encabezado.

        Args:
            min_date (QDate): Fecha mínima.
            max_date (QDate): Fecha máxima.
            pixels_per_day (float): Número de píxeles por día.
        """
        self.min_date = min_date
        self.max_date = max_date
        self.pixels_per_day = pixels_per_day
        self.update()

    def paintEvent(self, event):
        """
        Dibuja el encabezado con las fechas.

        Args:
            event (QPaintEvent): Evento de pintura.
        """
        if not self.min_date or not self.max_date or not self.pixels_per_day:
            return

        with QPainter(self) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(event.rect(), QColor(240, 240, 240))  # Fondo del encabezado

            total_days = self.min_date.daysTo(self.max_date) + 1
            for day in range(total_days):
                current_date = self.min_date.addDays(day)
                x = day * self.pixels_per_day

                # Dibujar líneas divisorias
                painter.setPen(QPen(QColor(200, 200, 200)))
                painter.drawLine(x, 0, x, self.header_height)

                # Dibujar el día y el mes
                painter.setPen(QPen(Qt.GlobalColor.black))
                painter.setFont(QFont("Arial", 10))
                date_text = current_date.toString("dd MMM")
                painter.drawText(QRectF(x, 5, self.pixels_per_day, self.header_height - 10),
                                 Qt.AlignmentFlag.AlignCenter, date_text)

            # Línea final
            painter.setPen(QPen(QColor(200, 200, 200)))
            painter.drawLine(total_days * self.pixels_per_day, 0,
                             total_days * self.pixels_per_day, self.header_height)


class GanttChart(QWidget):
    """
    Gráfico de diagrama de Gantt que muestra las tareas y permite la interacción.
    """
    colorChanged = Signal(int, QColor)  # Señal para cambiar el color de una tarea

    def __init__(self, tasks, row_height, header_height, main_window):
        super().__init__()
        self.tasks = tasks
        self.row_height = row_height
        self.header_height = header_height
        self.main_window = main_window

        self.min_date = None
        self.max_date = None
        self.pixels_per_day = 0

        self.vertical_offset = 0  # Desplazamiento vertical
        self.background_color = QColor(255, 255, 255)
        self.today_line_color = QColor(255, 0, 0)
        self.text_color = QColor(0, 0, 0)
        self.highlighted_task_index = None

        self.floating_menu = None
        self.click_pos = QPoint()
        self.double_click_occurred = False

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

    def update_parameters(self, min_date, max_date, pixels_per_day):
        """
        Actualiza los parámetros del gráfico de Gantt.

        Args:
            min_date (QDate): Fecha mínima.
            max_date (QDate): Fecha máxima.
            pixels_per_day (float): Número de píxeles por día.
        """
        self.min_date = min_date
        self.max_date = max_date
        self.pixels_per_day = pixels_per_day
        self.update()

    def set_vertical_offset(self, offset):
        """
        Establece el desplazamiento vertical.

        Args:
            offset (int): Nuevo desplazamiento.
        """
        self.vertical_offset = offset
        self.update()

    def get_updated_task(self, task):
        """
        Obtiene la información actualizada de una tarea.

        Args:
            task (Task): Tarea a actualizar.

        Returns:
            Task: Tarea actualizada.
        """
        for row in range(self.main_window.task_table_widget.model.rowCount()):
            index = self.main_window.task_table_widget.table_view.model().index(row, 1)
            current_task = self.main_window.task_table_widget.table_view.model().data(index, Qt.ItemDataRole.UserRole)
            if current_task == task:
                task.name = self.main_window.task_table_widget.table_view.model().data(index, Qt.ItemDataRole.DisplayRole)
                break
        return task

    def show_floating_menu(self, position, task):
        """
        Muestra un menú flotante al hacer clic en una tarea.

        Args:
            position (QPoint): Posición del clic.
            task (Task): Tarea en la que se hizo clic.
        """
        if self.floating_menu:
            self.floating_menu.close()

        updated_task = self.get_updated_task(task)
        self.floating_menu = FloatingTaskMenu(updated_task, self)
        self.floating_menu.notesChanged.connect(self.on_notes_changed)

        menu_size = self.floating_menu.sizeHint()
        adjusted_position = self.adjust_menu_position(position, menu_size)

        self.floating_menu.move(adjusted_position)
        self.floating_menu.show()

    def adjust_menu_position(self, position, menu_size):
        """
        Ajusta la posición del menú flotante para que no salga de la pantalla.

        Args:
            position (QPoint): Posición original.
            menu_size (QSize): Tamaño del menú.

        Returns:
            QPoint: Posición ajustada.
        """
        screen = QApplication.primaryScreen().geometry()
        global_pos = self.mapToGlobal(position)

        preferred_x = global_pos.x()
        preferred_y = global_pos.y()

        if preferred_x + menu_size.width() > screen.right():
            preferred_x = screen.right() - menu_size.width()
        if preferred_x < screen.left():
            preferred_x = screen.left()

        if preferred_y + menu_size.height() > screen.bottom():
            preferred_y = preferred_y - menu_size.height()
        if preferred_y < screen.top():
            preferred_y = screen.top()

        return QPoint(preferred_x, preferred_y)

    def on_notes_changed(self):
        """
        Maneja el cambio en las notas de una tarea.
        """
        if hasattr(self, 'main_window'):
            self.main_window.set_unsaved_changes(True)

    def on_color_changed(self, task_index, color):
        """
        Maneja el cambio de color de una tarea.

        Args:
            task_index (int): Índice de la tarea.
            color (QColor): Nuevo color.
        """
        if hasattr(self, 'main_window'):
            self.main_window.set_unsaved_changes(True)

    def paintEvent(self, event):
        """
        Dibuja las barras de las tareas y otros elementos en el gráfico de Gantt.

        Args:
            event (QPaintEvent): Evento de pintura.
        """
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

                painter.setBrush(QBrush(task.color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(QRectF(x, bar_y, width, bar_height))

                # Agregar identificadores para subtareas
                if hasattr(task, 'is_subtask') and task.is_subtask:
                    painter.setPen(QPen(self.text_color))
                    painter.setFont(QFont("Arial", 12))
                    rect = QRectF(x, y, width, self.row_height)
                    painter.drawText(rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "↳")

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
        """
        Maneja los cambios de evento, como cambios de paleta.

        Args:
            event (QEvent): Evento de cambio.
        """
        if event.type() == QEvent.Type.PaletteChange:
            self.update_colors()
            self.update()
        super().changeEvent(event)

    def update_colors(self):
        """
        Actualiza los colores utilizados en el gráfico de Gantt según la paleta del sistema.
        """
        palette = self.palette()
        self.background_color = palette.color(QPalette.ColorRole.Window)
        self.text_color = palette.color(QPalette.ColorRole.WindowText)

    def show_context_menu(self, position):
        """
        Muestra un menú contextual al hacer clic derecho sobre una tarea.

        Args:
            position (QPoint): Posición del clic.
        """
        task_index = self.get_task_at_position(position)
        if task_index is not None:
            if self.is_click_on_task_bar(position, task_index):
                global_pos = self.mapToGlobal(position)
                self.main_window.show_task_context_menu(global_pos, task_index)

    def is_click_on_task_bar(self, position, task_index):
        """
        Verifica si el clic fue sobre la barra de una tarea.

        Args:
            position (QPoint): Posición del clic.
            task_index (int): Índice de la tarea.

        Returns:
            bool: True si el clic fue sobre la barra, False en caso contrario.
        """
        if 0 <= task_index < len(self.tasks):
            task = self.tasks[task_index]
            start_date = QDate.fromString(task.start_date, "dd/MM/yyyy")
            end_date = QDate.fromString(task.end_date, "dd/MM/yyyy")

            x = position.x()
            y = position.y() + self.vertical_offset

            task_start_x = self.min_date.daysTo(start_date) * self.pixels_per_day if self.min_date else 0
            task_end_x = self.min_date.daysTo(end_date) * self.pixels_per_day if self.min_date else 0
            task_y = task_index * self.row_height

            margin = 2

            if (task_start_x - margin <= x <= task_end_x + margin and
                task_y <= y <= task_y + self.row_height):
                return True

        return False

    def get_task_at_position(self, position):
        """
        Obtiene el índice de la tarea en la posición dada.

        Args:
            position (QPoint): Posición del clic.

        Returns:
            int or None: Índice de la tarea o None si no hay tarea en esa posición.
        """
        y = position.y() + self.vertical_offset
        task_index = int(y // self.row_height)
        if 0 <= task_index < len(self.tasks):
            return task_index
        return None

    def contextMenuEvent(self, event):
        """
        Maneja el evento de menú contextual.

        Args:
            event (QContextMenuEvent): Evento de menú contextual.
        """
        self.show_context_menu(event.pos())

    def resizeEvent(self, event):
        """
        Maneja el evento de cambio de tamaño.

        Args:
            event (QResizeEvent): Evento de cambio de tamaño.
        """
        super().resizeEvent(event)
        self.update()

    def calculate_today_position(self):
        """
        Calcula la posición de hoy en el gráfico de Gantt.

        Returns:
            float or None: Posición relativa de hoy entre 0 y 1 o None si no está dentro del rango.
        """
        if self.min_date and self.max_date:
            today = QDate.currentDate()
            if self.min_date <= today <= self.max_date:
                total_days = self.min_date.daysTo(self.max_date)
                days_to_today = self.min_date.daysTo(today)
                return days_to_today / total_days
        return None

class GanttWidget(QWidget):
    """
    Widget que combina el encabezado y el gráfico de Gantt.
    """
    def __init__(self, tasks, row_height, header_height, main_window):
        super().__init__()
        self.main_window = main_window
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.header = GanttHeaderView()
        self.header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.chart = GanttChart(tasks, row_height, header_height, main_window)
        self.chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.chart.setMouseTracking(True)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_layout.addWidget(self.header)
        self.content_layout.addWidget(self.chart)

        self.layout.addWidget(self.content_widget)

        self.pixels_per_day = 0

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def update_parameters(self, min_date, max_date, pixels_per_day):
        """
        Actualiza los parámetros del widget de Gantt.

        Args:
            min_date (QDate): Fecha mínima.
            max_date (QDate): Fecha máxima.
            pixels_per_day (float): Número de píxeles por día.
        """
        self.min_date = min_date
        self.max_date = max_date
        self.pixels_per_day = pixels_per_day
        self.header.update_parameters(min_date, max_date, pixels_per_day)
        self.chart.update_parameters(min_date, max_date, pixels_per_day)
        self.content_widget.updateGeometry()

    def resizeEvent(self, event):
        """
        Maneja el evento de cambio de tamaño.

        Args:
            event (QResizeEvent): Evento de cambio de tamaño.
        """
        super().resizeEvent(event)
        if self.min_date and self.max_date:
            days_total = self.min_date.daysTo(self.max_date) + 1
            available_width = self.width()
            self.pixels_per_day = max(0.1, available_width / days_total)
            self.update_parameters(self.min_date, self.max_date, self.pixels_per_day)
