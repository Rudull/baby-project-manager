import logging

#calendar_view.py
#Módulo encargado de la vista de calendario de las tareas. Muestra un mes o un
#año completo con un estilo minimalista tipo "calendario de pared": solo los
#números de los días, resaltando el día de hoy y marcando con una pequeña
#barra los días de inicio/fin de tarea (los "hitos"), incluyendo un punto
#amarillo si la tarea tiene notas. Esta vista es intercambiable con el
#diagrama de Gantt desde la ventana principal.
#
import math

from PySide6.QtCore import QDate, QEvent, QPoint, QPointF, QRect, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QFontMetrics, QPainter, QPalette, QPen
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QToolTip,
    QVBoxLayout,
    QWidget,
)
from workalendar.america import Colombia

from core.models import Task
from ui.gantt_views import FloatingTaskMenu

logger = logging.getLogger("bpm.calendar")

MESES = (
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
)
DIAS_SEMANA = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")

# Instancia compartida: workalendar cachea los festivos por año internamente,
# así que reutilizarla evita recalcularlos en cada celda dibujada.
_HOLIDAY_CALENDAR = Colombia()


def _parse_task_dates(task):
    """Devuelve (inicio, fin) como QDate, o (None, None) si no son válidas."""
    start = QDate.fromString(task.start_date, "dd/MM/yyyy")
    end = QDate.fromString(task.end_date, "dd/MM/yyyy")
    if not start.isValid() or not end.isValid():
        return None, None
    if end < start:
        start, end = end, start
    return start, end


def _milestone_entry_text(task, date, kind):
    etiqueta = "Inicio" if kind == "start" else "Fin"
    return f"{date.toString('dd/MM/yyyy')} · {etiqueta} · {task.name.strip()}"


def _day_shade_kind(day: QDate):
    """'holiday' | 'weekend' | None: cómo debe sombrearse el día dado."""
    if day.toPython() in {d for d, _label in _HOLIDAY_CALENDAR.holidays(day.year())}:
        return "holiday"
    if day.dayOfWeek() >= 6:  # Qt: sábado=6, domingo=7
        return "weekend"
    return None


class CalendarGridWidget(QWidget):
    """Rejilla mensual minimalista: números de día y barras de hito.

    En vez de barras que abarcan todo el rango de la tarea, cada día que
    coincide con un inicio o un fin de tarea ("hito") se marca con una
    barra horizontal (del ancho de la celda del día), una por fila, debajo
    del número del día. Si la tarea tiene notas, la barra incluye un punto
    amarillo indicador.
    """

    monthChanged = Signal(QDate)

    WEEKDAY_HEADER_H = 22   # Altura de la fila con los nombres de los días
    DAY_NUM_H = 22          # Espacio reservado al número del día en cada celda
    MARKER_H = 13           # Alto de cada barra de hito
    MARKER_MARGIN = 3       # Margen horizontal de la barra respecto al borde de la celda
    ROW_GAP = 2             # Separación vertical entre filas de barras
    NOTE_DOT_D = 7          # Diámetro del punto indicador de notas
    WHEEL_STEP = 120        # Paso estándar de la rueda del mouse

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.tasks = []
        self.highlighted_task = None
        self.floating_menu = None
        self._month = QDate(QDate.currentDate().year(), QDate.currentDate().month(), 1)
        self._marker_hits = []   # [(QRectF, Task, kind)] rellenado en cada paintEvent
        self._wheel_accumulator = 0
        self.today_color = QColor(242, 211, 136)  # Mismo acento "Hoy" del Gantt
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(200)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.update_colors()

    # ------------------------------------------------------------------
    # Estado (mes visible, tareas, resaltado)
    # ------------------------------------------------------------------

    def month(self) -> QDate:
        return self._month

    def set_month(self, date: QDate) -> None:
        if not date.isValid():
            return
        self._month = QDate(date.year(), date.month(), 1)
        self.monthChanged.emit(self._month)
        self.update()

    def next_month(self) -> None:
        self.set_month(self._month.addMonths(1))

    def previous_month(self) -> None:
        self.set_month(self._month.addMonths(-1))

    def go_to_today(self) -> None:
        self.set_month(QDate.currentDate())

    def set_tasks(self, tasks) -> None:
        self.tasks = tasks or []
        self.update()

    def set_highlight(self, task: Task | None) -> None:
        if task is not self.highlighted_task:
            self.highlighted_task = task
            self.update()

    def milestones_in_month(self, month: QDate):
        """[(idx, task, fecha, kind)] de los hitos de inicio/fin dentro del mes dado."""
        entries = []
        for idx, task in enumerate(self.tasks):
            start, end = _parse_task_dates(task)
            if start is None:
                continue
            if start.year() == month.year() and start.month() == month.month():
                entries.append((idx, task, start, "start"))
            if end != start and end.year() == month.year() and end.month() == month.month():
                entries.append((idx, task, end, "end"))
        entries.sort(key=lambda e: e[2])
        return entries

    # ------------------------------------------------------------------
    # Colores según la paleta (modo claro / oscuro)
    # ------------------------------------------------------------------

    def update_colors(self) -> None:
        palette = self.palette()
        self.background_color = palette.color(QPalette.ColorRole.Base)
        self.text_color = palette.color(QPalette.ColorRole.Text)
        self.grid_color = palette.color(QPalette.ColorRole.Mid)
        self.highlight_color = palette.color(QPalette.ColorRole.Highlight)
        is_light_mode = palette.color(QPalette.ColorRole.Window).lightness() > 128
        if is_light_mode:
            self.muted_text_color = QColor(160, 160, 160)
            self.weekday_color = QColor(100, 100, 100)
            self.weekend_shade_color = QColor(0, 0, 0, 32)
            self.holiday_shade_color = QColor(214, 69, 69, 65)
        else:
            self.muted_text_color = QColor(110, 110, 110)
            self.weekday_color = QColor(170, 170, 170)
            self.weekend_shade_color = QColor(255, 255, 255, 30)
            self.holiday_shade_color = QColor(214, 90, 90, 78)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.PaletteChange:
            self.update_colors()
            self.update()
        super().changeEvent(event)

    # ------------------------------------------------------------------
    # Geometría de la rejilla
    # ------------------------------------------------------------------

    def _grid_start(self) -> QDate:
        """Primer lunes en (o antes de) el día 1 del mes visible."""
        first = self._month
        return first.addDays(-(first.dayOfWeek() - 1))

    def _week_count(self) -> int:
        grid_start = self._grid_start()
        last = self._month.addMonths(1).addDays(-1)
        total_days = grid_start.daysTo(last) + 1
        return max(1, math.ceil(total_days / 7))

    def _milestones_by_day(self):
        """dict[QDate] -> [(task, kind)] con los hitos de inicio/fin."""
        by_day = {}
        for task in self.tasks:
            start, end = _parse_task_dates(task)
            if start is None:
                continue
            by_day.setdefault(start, []).append((task, "start"))
            if end != start:
                by_day.setdefault(end, []).append((task, "end"))
        return by_day

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------

    def paintEvent(self, event):
        self._marker_hits = []
        with QPainter(self) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(event.rect(), self.background_color)

            width = self.width()
            weeks = self._week_count()
            grid_top = self.WEEKDAY_HEADER_H
            grid_h = max(1, self.height() - grid_top)
            cell_w = width / 7.0
            cell_h = grid_h / weeks
            grid_start = self._grid_start()

            # Sombreado de fines de semana y festivos, debajo de las líneas de la rejilla
            for row in range(weeks):
                week_start = grid_start.addDays(7 * row)
                cell_top = grid_top + row * cell_h
                for col in range(7):
                    day = week_start.addDays(col)
                    kind = _day_shade_kind(day)
                    if kind == "holiday":
                        painter.fillRect(QRectF(col * cell_w, cell_top, cell_w, cell_h), self.holiday_shade_color)
                    elif kind == "weekend":
                        painter.fillRect(QRectF(col * cell_w, cell_top, cell_w, cell_h), self.weekend_shade_color)

            # Encabezado con los nombres de los días de la semana
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.setPen(self.weekday_color)
            for col, name in enumerate(DIAS_SEMANA):
                rect = QRect(int(col * cell_w), 0, int(cell_w), self.WEEKDAY_HEADER_H)
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, name)

            # Líneas de la rejilla
            painter.setPen(QPen(self.grid_color, 1))
            for col in range(8):
                x = int(round(min(col * cell_w, width - 1)))
                painter.drawLine(x, grid_top, x, self.height())
            for row in range(weeks + 1):
                y = int(round(min(grid_top + row * cell_h, self.height() - 1)))
                painter.drawLine(0, y, width, y)

            today = QDate.currentDate()
            milestones_by_day = self._milestones_by_day()
            fm_bar = QFontMetrics(QFont("Arial", 8, QFont.Weight.Bold))

            for row in range(weeks):
                week_start = grid_start.addDays(7 * row)
                cell_top = grid_top + row * cell_h

                for col in range(7):
                    day = week_start.addDays(col)
                    x = col * cell_w
                    in_month = day.month() == self._month.month() and day.year() == self._month.year()

                    # Número de día (y resaltado del día de hoy)
                    num_rect = QRectF(x + 4, cell_top + 2, cell_w - 8, self.DAY_NUM_H - 4)
                    painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                    if day == today and in_month:
                        label = str(day.day())
                        chip_w = max(18, fm_bar.horizontalAdvance(label) + 10)
                        chip = QRectF(x + 3, cell_top + 2, chip_w, self.DAY_NUM_H - 3)
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.setBrush(QBrush(self.today_color))
                        painter.drawRoundedRect(chip, 7, 7)
                        painter.setPen(QColor(40, 40, 40))
                        painter.drawText(chip, Qt.AlignmentFlag.AlignCenter, label)
                    else:
                        painter.setPen(self.text_color if in_month else self.muted_text_color)
                        painter.drawText(
                            num_rect,
                            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                            str(day.day()),
                        )

                    # Barras de hito (inicio/fin de tarea) de este día, una por fila,
                    # con el ancho de la celda del día
                    day_milestones = milestones_by_day.get(day, [])
                    if not day_milestones:
                        continue

                    bar_x = x + self.MARKER_MARGIN
                    bar_w = max(1.0, cell_w - 2 * self.MARKER_MARGIN)
                    row_step = self.MARKER_H + self.ROW_GAP

                    available_h = cell_h - self.DAY_NUM_H - self.ROW_GAP
                    max_rows = max(1, int(available_h / row_step))
                    overflow = len(day_milestones) > max_rows
                    visible = day_milestones[: max_rows - 1] if overflow else day_milestones

                    bar_y = cell_top + self.DAY_NUM_H
                    for task, kind in visible:
                        color = QColor(task.color)
                        rect = QRectF(bar_x, bar_y, bar_w, self.MARKER_H)
                        if kind == "start":
                            painter.setPen(Qt.PenStyle.NoPen)
                            painter.setBrush(QBrush(color))
                        else:
                            painter.setPen(QPen(color, 2))
                            painter.setBrush(Qt.BrushStyle.NoBrush)
                        painter.drawRoundedRect(rect, 3, 3)

                        if task.has_notes:
                            dot = QRectF(0, 0, self.NOTE_DOT_D, self.NOTE_DOT_D)
                            dot.moveCenter(QPointF(rect.right() - self.NOTE_DOT_D, rect.center().y()))
                            painter.setPen(Qt.PenStyle.NoPen)
                            painter.setBrush(QBrush(self.today_color))
                            painter.drawEllipse(dot)

                        if task is self.highlighted_task:
                            painter.setPen(QPen(self.highlight_color, 1.5))
                            painter.setBrush(Qt.BrushStyle.NoBrush)
                            painter.drawRoundedRect(rect.adjusted(-1, -1, 1, 1), 3, 3)

                        self._marker_hits.append((rect.adjusted(0, -1, 0, 1), task, kind))
                        bar_y += row_step

                    if overflow:
                        hidden = len(day_milestones) - len(visible)
                        painter.setFont(QFont("Arial", 6))
                        painter.setPen(self.muted_text_color)
                        painter.drawText(
                            QRectF(bar_x, bar_y, bar_w, self.MARKER_H),
                            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                            f"+{hidden}",
                        )

            # Mensaje de bienvenida cuando no hay tareas (paridad con el Gantt)
            if not self.tasks:
                welcome_text = (
                    "Bienvenido a Baby Project Manager\n"
                    "Haga clic en 'Agregar Nueva Tarea' para comenzar"
                )
                painter.setPen(QPen(self.text_color))
                painter.setFont(QFont("Arial", 14))
                painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, welcome_text)

    # ------------------------------------------------------------------
    # Interacción
    # ------------------------------------------------------------------

    def _marker_at(self, pos) -> Task | None:
        for rect, task, _kind in self._marker_hits:
            if rect.contains(pos):
                return task
        return None

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        if self._marker_at(pos) is not None:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            task = self._marker_at(pos)
            if task is not None:
                self.set_highlight(task)
                # La tarea puede ser una subtarea oculta (padre contraído):
                # reveal_task la expande primero y devuelve su fila visible.
                row = self.main_window.reveal_task(task)
                if row is not None:
                    table_view = self.main_window.task_table_widget.table_view
                    table_view.selectRow(row)
                    table_view.scrollTo(self.main_window.task_table_widget.model.index(row, 0))
                self.show_floating_menu(pos, task)
            else:
                self.set_highlight(None)
                self.main_window.task_table_widget.table_view.clearSelection()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.set_highlight(None)
            self.main_window.task_table_widget.table_view.clearSelection()
        elif event.key() in (Qt.Key.Key_PageUp, Qt.Key.Key_Left):
            self.previous_month()
        elif event.key() in (Qt.Key.Key_PageDown, Qt.Key.Key_Right):
            self.next_month()
        super().keyPressEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Dejar que la ventana principal maneje Ctrl+rueda (zoom del Gantt)
            event.ignore()
            return
        self._wheel_accumulator += event.angleDelta().y()
        while self._wheel_accumulator >= self.WHEEL_STEP:
            self.previous_month()
            self._wheel_accumulator -= self.WHEEL_STEP
        while self._wheel_accumulator <= -self.WHEEL_STEP:
            self.next_month()
            self._wheel_accumulator += self.WHEEL_STEP
        event.accept()

    def event(self, ev):
        if ev.type() == QEvent.Type.ToolTip:
            task = self._marker_at(ev.pos())
            if task is not None:
                text = f"{task.name.strip()}\n{task.start_date} – {task.end_date}"
                if task.has_notes:
                    text += "\n(tiene notas)"
                QToolTip.showText(ev.globalPos(), text, self)
            else:
                QToolTip.hideText()
            return True
        return super().event(ev)

    def show_context_menu(self, position):
        task = self._marker_at(position)
        if task is not None:
            row = self.main_window.reveal_task(task)
            if row is not None:
                global_pos = self.mapToGlobal(position)
                self.main_window.show_task_context_menu(global_pos, row)

    # ------------------------------------------------------------------
    # Menú flotante (mismo componente que usa el Gantt)
    # ------------------------------------------------------------------

    def show_floating_menu(self, position, task):
        if self.floating_menu:
            self.floating_menu.close()
        self.floating_menu = FloatingTaskMenu(task, self)
        self.floating_menu.notesChanged.connect(self.on_notes_changed)

        menu_size = self.floating_menu.sizeHint()
        primary_screen = self.main_window.get_primary_screen()
        adjusted_position = self.adjust_menu_position(position, menu_size, primary_screen)

        self.floating_menu.move(adjusted_position)
        self.floating_menu.show()

    def adjust_menu_position(self, position, menu_size, primary_screen):
        screen_geometry = primary_screen.geometry()
        global_pos = self.mapToGlobal(position)

        preferred_x = global_pos.x()
        preferred_y = global_pos.y()

        if preferred_x + menu_size.width() > screen_geometry.right():
            preferred_x = screen_geometry.right() - menu_size.width()
        if preferred_x < screen_geometry.left():
            preferred_x = screen_geometry.left()

        if preferred_y + menu_size.height() > screen_geometry.bottom():
            preferred_y = preferred_y - menu_size.height()
        if preferred_y < screen_geometry.top():
            preferred_y = screen_geometry.top()

        return QPoint(preferred_x, preferred_y)

    def on_notes_changed(self):
        if hasattr(self, "main_window"):
            self.main_window.set_unsaved_changes(True)


class YearOverviewWidget(QWidget):
    """Vista de "calendario de pared" con los 12 meses de un año a la vez.

    Cada mini-mes solo muestra los números de los días (sin barras); los
    días de inicio/fin de tarea se marcan con un punto de color. Al hacer
    clic sobre un mes se solicita (vía `monthActivated`) mostrar ese mes en
    detalle en `CalendarGridWidget`.
    """

    monthActivated = Signal(QDate)
    yearChanged = Signal(int)

    COLS = 4
    ROWS = 3
    MONTH_PADDING = 32
    HEADER_H = 20
    WEEKDAY_H = 14
    WHEEL_STEP = 120

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.tasks = []
        self._year = QDate.currentDate().year()
        self._wheel_accumulator = 0
        self._month_rects = []   # [(QRect, mes 1..12)]
        self._day_hits = []      # [(QRectF, QDate, [(task, kind), ...])]
        self.today_color = QColor(242, 211, 136)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(420)
        self.update_colors()

    # ------------------------------------------------------------------
    # Estado (año visible, tareas)
    # ------------------------------------------------------------------

    def year(self) -> int:
        return self._year

    def set_year(self, year: int) -> None:
        if year == self._year:
            return
        self._year = year
        self.yearChanged.emit(self._year)
        self.update()

    def next_year(self) -> None:
        self.set_year(self._year + 1)

    def previous_year(self) -> None:
        self.set_year(self._year - 1)

    def go_to_today(self) -> None:
        self.set_year(QDate.currentDate().year())

    def set_tasks(self, tasks) -> None:
        self.tasks = tasks or []
        self.update()

    # ------------------------------------------------------------------
    # Colores según la paleta (modo claro / oscuro)
    # ------------------------------------------------------------------

    def update_colors(self) -> None:
        palette = self.palette()
        self.background_color = palette.color(QPalette.ColorRole.Base)
        self.text_color = palette.color(QPalette.ColorRole.Text)
        is_light_mode = palette.color(QPalette.ColorRole.Window).lightness() > 128
        if is_light_mode:
            self.muted_text_color = QColor(170, 170, 170)
            self.weekday_color = QColor(120, 120, 120)
            self.weekend_shade_color = QColor(0, 0, 0, 32)
            self.holiday_shade_color = QColor(214, 69, 69, 65)
        else:
            self.muted_text_color = QColor(110, 110, 110)
            self.weekday_color = QColor(170, 170, 170)
            self.weekend_shade_color = QColor(255, 255, 255, 30)
            self.holiday_shade_color = QColor(214, 90, 90, 78)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.PaletteChange:
            self.update_colors()
            self.update()
        super().changeEvent(event)

    # ------------------------------------------------------------------
    # Datos
    # ------------------------------------------------------------------

    def _milestones_by_day(self):
        """dict[(mes, día)] -> [(task, kind)] de los hitos del año visible."""
        by_day = {}
        for task in self.tasks:
            start, end = _parse_task_dates(task)
            if start is None:
                continue
            for date, kind in ((start, "start"), (end, "end")):
                if kind == "end" and end == start:
                    continue
                if date.year() == self._year:
                    by_day.setdefault((date.month(), date.day()), []).append((task, kind))
        return by_day

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------

    def paintEvent(self, event):
        self._month_rects = []
        self._day_hits = []
        with QPainter(self) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(event.rect(), self.background_color)

            milestones_by_day = self._milestones_by_day()
            today = QDate.currentDate()

            cell_w = self.width() / self.COLS
            cell_h = self.height() / self.ROWS

            for month_idx in range(12):
                col = month_idx % self.COLS
                row = month_idx // self.COLS
                area = QRectF(col * cell_w, row * cell_h, cell_w, cell_h).adjusted(
                    self.MONTH_PADDING, self.MONTH_PADDING,
                    -self.MONTH_PADDING, -self.MONTH_PADDING,
                )
                self._month_rects.append((area.toRect(), month_idx + 1))
                self._paint_month(painter, area, month_idx + 1, milestones_by_day, today)

    def _paint_month(self, painter, area, month, milestones_by_day, today):
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.setPen(self.text_color)
        header_rect = QRectF(area.x(), area.y(), area.width(), self.HEADER_H)
        painter.drawText(
            header_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, MESES[month - 1]
        )

        first = QDate(self._year, month, 1)
        grid_start = first.addDays(-(first.dayOfWeek() - 1))
        last = first.addMonths(1).addDays(-1)
        weeks = max(1, math.ceil((grid_start.daysTo(last) + 1) / 7))

        col_w = area.width() / 7.0
        weekday_top = area.y() + self.HEADER_H
        painter.setFont(QFont("Arial", 6, QFont.Weight.Bold))
        painter.setPen(self.weekday_color)
        for col, name in enumerate(DIAS_SEMANA):
            rect = QRectF(area.x() + col * col_w, weekday_top, col_w, self.WEEKDAY_H)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, name[0])

        grid_top = weekday_top + self.WEEKDAY_H
        grid_h = max(1, area.bottom() - grid_top)
        row_h = grid_h / weeks

        painter.setFont(QFont("Arial", 7))
        for r in range(weeks):
            week_start = grid_start.addDays(7 * r)
            for c in range(7):
                day = week_start.addDays(c)
                cell = QRectF(area.x() + c * col_w, grid_top + r * row_h, col_w, row_h)
                in_month = day.month() == month and day.year() == self._year
                label = str(day.day())

                shade_kind = _day_shade_kind(day)
                if shade_kind == "holiday":
                    painter.fillRect(cell, self.holiday_shade_color)
                elif shade_kind == "weekend":
                    painter.fillRect(cell, self.weekend_shade_color)

                if day == today and in_month:
                    chip_d = min(col_w, row_h) - 4
                    chip = QRectF(0, 0, chip_d, chip_d)
                    chip.moveCenter(cell.center())
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QBrush(self.today_color))
                    painter.drawEllipse(chip)
                    painter.setPen(QColor(40, 40, 40))
                    painter.drawText(cell, Qt.AlignmentFlag.AlignCenter, label)
                else:
                    painter.setPen(self.text_color if in_month else self.muted_text_color)
                    painter.drawText(cell, Qt.AlignmentFlag.AlignCenter, label)

                if in_month:
                    entries = milestones_by_day.get((day.month(), day.day()))
                    if entries:
                        dot_d = 6.0
                        dot = QRectF(0, 0, dot_d, dot_d)
                        dot.moveCenter(QPointF(cell.center().x(), cell.bottom() - dot_d))
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.setBrush(QBrush(QColor(entries[0][0].color)))
                        painter.drawEllipse(dot)
                        self._day_hits.append((cell, day, entries))

    # ------------------------------------------------------------------
    # Interacción
    # ------------------------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            for rect, month in self._month_rects:
                if rect.contains(pos):
                    self.monthActivated.emit(QDate(self._year, month, 1))
                    break
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        on_month = any(rect.contains(pos) for rect, _ in self._month_rects)
        self.setCursor(Qt.CursorShape.PointingHandCursor if on_month else Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            event.ignore()
            return
        self._wheel_accumulator += event.angleDelta().y()
        while self._wheel_accumulator >= self.WHEEL_STEP:
            self.previous_year()
            self._wheel_accumulator -= self.WHEEL_STEP
        while self._wheel_accumulator <= -self.WHEEL_STEP:
            self.next_year()
            self._wheel_accumulator += self.WHEEL_STEP
        event.accept()

    def event(self, ev):
        if ev.type() == QEvent.Type.ToolTip:
            pos = ev.pos()
            for rect, _date, entries in self._day_hits:
                if rect.contains(pos):
                    lines = [
                        f"{'Inicio' if kind == 'start' else 'Fin'}: {task.name.strip()}"
                        for task, kind in entries
                    ]
                    QToolTip.showText(ev.globalPos(), "\n".join(lines), self)
                    return True
            QToolTip.hideText()
            return True
        return super().event(ev)


class MonthMilestonesDialog(QDialog):
    """Popup que lista los hitos (inicio/fin de tarea) de un mes y permite
    copiar su información al portapapeles."""

    def __init__(self, month: QDate, tasks, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Hitos de {MESES[month.month() - 1]} {month.year()}")
        self.setMinimumWidth(380)

        entries = self._collect_entries(month, tasks)

        layout = QVBoxLayout(self)

        if not entries:
            layout.addWidget(QLabel("No hay hitos (inicio o fin de tarea) en este mes."))
        else:
            list_widget = QListWidget()
            list_widget.setAlternatingRowColors(True)
            for _idx, task, date, kind in entries:
                text = _milestone_entry_text(task, date, kind)

                row = QWidget()
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(6, 4, 6, 4)

                label = QLabel(text)
                label.setWordWrap(True)
                row_layout.addWidget(label, 1)

                copy_btn = QPushButton("Copiar")
                copy_btn.setFixedWidth(70)
                copy_btn.setToolTip("Copiar este hito al portapapeles")
                copy_btn.clicked.connect(lambda _checked=False, t=text: self._copy_to_clipboard(t))
                row_layout.addWidget(copy_btn)

                item = QListWidgetItem()
                item.setSizeHint(row.sizeHint())
                list_widget.addItem(item)
                list_widget.setItemWidget(item, row)

            layout.addWidget(list_widget)

            full_text = "\n".join(
                _milestone_entry_text(task, date, kind) for _idx, task, date, kind in entries
            )
            copy_all_btn = QPushButton("Copiar todo")
            copy_all_btn.setToolTip("Copiar todos los hitos del mes al portapapeles")
            copy_all_btn.clicked.connect(lambda: self._copy_to_clipboard(full_text))
            layout.addWidget(copy_all_btn)

        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    @staticmethod
    def _collect_entries(month: QDate, tasks):
        entries = []
        for idx, task in enumerate(tasks or []):
            start, end = _parse_task_dates(task)
            if start is None:
                continue
            if start.year() == month.year() and start.month() == month.month():
                entries.append((idx, task, start, "start"))
            if end != start and end.year() == month.year() and end.month() == month.month():
                entries.append((idx, task, end, "end"))
        entries.sort(key=lambda e: e[2])
        return entries

    def _copy_to_clipboard(self, text: str) -> None:
        QApplication.clipboard().setText(text)


class CalendarViewWidget(QWidget):
    """Contenedor de la vista de calendario: barra de navegación + rejilla de
    mes o de año (alternables), y acceso al popup de hitos del mes."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.mode = "month"  # "month" | "year"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Barra de navegación. El margen derecho deja sitio al botón de
        # alternar vista (Gantt/Calendario) superpuesto en la ventana principal.
        nav_bar = QWidget()
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(4, 2, 44, 2)
        nav_layout.setSpacing(4)

        self.btn_mode_month = QPushButton("Mes")
        self.btn_mode_month.setCheckable(True)
        self.btn_mode_month.setChecked(True)
        self.btn_mode_month.setFixedSize(44, 22)
        self.btn_mode_year = QPushButton("Año")
        self.btn_mode_year.setCheckable(True)
        self.btn_mode_year.setFixedSize(44, 22)

        self.btn_prev = QPushButton("◀")
        self.btn_prev.setFixedSize(28, 22)
        self.btn_today = QPushButton("Hoy")
        self.btn_today.setFixedSize(44, 22)
        self.btn_next = QPushButton("▶")
        self.btn_next.setFixedSize(28, 22)

        self.period_label = QLabel()
        font = QFont("Arial", 10, QFont.Weight.Bold)
        self.period_label.setFont(font)
        self.period_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_milestones = QPushButton("Hitos del mes")
        self.btn_milestones.setToolTip("Ver los hitos (inicio/fin de tarea) del mes mostrado")
        self.btn_milestones.clicked.connect(self.show_month_milestones)

        nav_layout.addWidget(self.btn_mode_month)
        nav_layout.addWidget(self.btn_mode_year)
        nav_layout.addSpacing(8)
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.btn_today)
        nav_layout.addWidget(self.btn_next)
        nav_layout.addWidget(self.period_label, 1)
        nav_layout.addWidget(self.btn_milestones)
        nav_bar.setFixedHeight(28)

        self.grid = CalendarGridWidget(main_window, self)
        self.year_grid = YearOverviewWidget(main_window, self)
        self.year_grid.setVisible(False)

        layout.addWidget(nav_bar)
        layout.addWidget(self.grid, 1)
        layout.addWidget(self.year_grid, 1)

        self.btn_mode_month.clicked.connect(lambda: self.set_mode("month"))
        self.btn_mode_year.clicked.connect(lambda: self.set_mode("year"))
        self.btn_prev.clicked.connect(self._go_previous)
        self.btn_today.clicked.connect(self._go_today)
        self.btn_next.clicked.connect(self._go_next)
        self.grid.monthChanged.connect(self._update_period_label)
        self.year_grid.yearChanged.connect(self._update_period_label)
        self.year_grid.monthActivated.connect(self._activate_month)

        self._update_period_label()

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Restaurar el modo (mes/año) de la sesión anterior.
        saved_mode = "month"
        if self.main_window is not None:
            saved_mode = self.main_window.config.get("View", "calendar_mode") or "month"
        self.set_mode(saved_mode)

    # ------------------------------------------------------------------
    # Alternancia mes / año
    # ------------------------------------------------------------------

    def set_mode(self, mode: str) -> None:
        if mode not in ("month", "year"):
            mode = "month"
        self.mode = mode
        self.btn_mode_month.setChecked(mode == "month")
        self.btn_mode_year.setChecked(mode == "year")
        self.grid.setVisible(mode == "month")
        self.year_grid.setVisible(mode == "year")
        self.btn_milestones.setEnabled(mode == "month")
        self._update_period_label()
        if self.main_window is not None:
            self.main_window.config.set("View", "calendar_mode", mode)

    def _activate_month(self, month: QDate) -> None:
        self.grid.set_month(month)
        self.set_mode("month")

    def _go_previous(self) -> None:
        if self.mode == "year":
            self.year_grid.previous_year()
        else:
            self.grid.previous_month()

    def _go_next(self) -> None:
        if self.mode == "year":
            self.year_grid.next_year()
        else:
            self.grid.next_month()

    def _go_today(self) -> None:
        if self.mode == "year":
            self.year_grid.go_to_today()
        else:
            self.grid.go_to_today()

    # ------------------------------------------------------------------
    # Popup de hitos del mes
    # ------------------------------------------------------------------

    def show_month_milestones(self) -> None:
        dialog = MonthMilestonesDialog(self.grid.month(), self.grid.tasks, self)
        dialog.exec()

    # ------------------------------------------------------------------
    # API usada por la ventana principal
    # ------------------------------------------------------------------

    def set_tasks(self, tasks) -> None:
        self.grid.set_tasks(tasks)
        self.year_grid.set_tasks(tasks)

    def set_highlight(self, task: Task | None) -> None:
        self.grid.set_highlight(task)

    def _update_period_label(self, *_args) -> None:
        if self.mode == "year":
            self.period_label.setText(str(self.year_grid.year()))
        else:
            month = self.grid.month()
            self.period_label.setText(f"{MESES[month.month() - 1]} {month.year()}")
