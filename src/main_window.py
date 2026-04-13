"""main_window.py
Ventana principal de Baby Project Manager.
La lógica de manipulación de tareas está delegada a TaskOperationsMixin.
"""
from __future__ import annotations

import logging
import math
import os
import sys
import subprocess
from datetime import timedelta, datetime
from pathlib import Path

from workalendar.america import Colombia
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QGridLayout,
    QScrollBar, QMessageBox, QMenu, QSizePolicy,
)
from PySide6.QtGui import (
    QColor, QKeySequence, QShortcut, QWheelEvent, QGuiApplication,
)
from PySide6.QtCore import (
    Qt, QDate, QTimer, QModelIndex, QEvent, QPoint, QRect,
)

from gantt_views import GanttWidget
from models import Task, TaskTableModel
from table_views import TaskTableWidget
from about_dialog import AboutDialog
from report_dialog import ReportDialog
from config_manager import ConfigManager
from task_operations_mixin import TaskOperationsMixin
from alert_manager import AlertManager
from command_system import (
    CommandManager, AddTaskCommand, DeleteTaskCommand, MoveTaskCommand,
    EditTaskCommand, ChangeColorCommand, DuplicateTaskCommand,
    ConvertTaskCommand, AddSubtaskCommand, InsertTaskCommand,
    ResetColorsCommand, EditNotesCommand, ToggleLinkedDurationCommand,
)
from updater.update_manager import UpdateManager
from updater.version import __version__

logger = logging.getLogger("bpm.main_window")


class MainWindow(TaskOperationsMixin, QMainWindow):
    ROW_HEIGHT = 25
    HEADER_HEIGHT = 25

    def __init__(self) -> None:
        super().__init__()

        self.config = ConfigManager()
        self.load_window_geometry()

        self.unsaved_changes: bool = False
        self.base_title: str = "Baby project manager"
        self.setWindowTitle(self.base_title)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMinMaxButtonsHint)
        self.setMinimumSize(800, 600)
        self.tasks: list[Task] = []
        self.current_file_path: str | None = None
        self.selected_period: int = 365
        self.setMouseTracking(True)
        self.wheel_accumulator: int = 0
        self.wheel_threshold: int = 100
        self.current_view: str = "complete"
        self.file_gui_windows: list = []
        self._loading_file: bool = False

        # Sistema de comandos
        self.command_manager = CommandManager()
        self.command_manager.canUndoChanged.connect(self.update_undo_status)
        self.command_manager.canRedoChanged.connect(self.update_redo_status)

        # Layout principal
        main_widget = QWidget()
        main_layout = QGridLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setColumnStretch(0, 0)
        main_layout.setColumnStretch(1, 1)
        main_layout.setColumnStretch(2, 0)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Widget izquierdo (tabla de tareas)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.task_table_widget = TaskTableWidget(self)
        left_layout.addWidget(self.task_table_widget)
        self.table_view = self.task_table_widget.table_view
        self.model = self.task_table_widget.model
        self.model.main_window = self

        self.model.layoutChanged.connect(self.on_model_layout_changed)
        self.model.dataChanged.connect(self.on_model_data_changed)

        # Nota: el ancho del panel izquierdo es gestionado dinámicamente por
        # TaskTableWidget.on_column_resized a través de table_view.setFixedWidth().
        # NO usar left_widget.setFixedWidth aquí para no bloquear el redimensionado
        # horizontal de la ventana principal.
        self.task_table_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        # Widget derecho (gráfico de Gantt)
        self.gantt_widget = GanttWidget(self.tasks, self.ROW_HEIGHT, self.HEADER_HEIGHT, self)
        self.gantt_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.gantt_header = self.gantt_widget.header
        self.gantt_chart = self.gantt_widget.chart
        self.gantt_chart.main_window = self

        # Scrollbar vertical compartido
        self.shared_scrollbar = QScrollBar(Qt.Orientation.Vertical)
        self.shared_scrollbar.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding
        )
        self.shared_scrollbar.setFixedWidth(20)
        self.shared_scrollbar.valueChanged.connect(self.sync_scroll)

        main_layout.addWidget(left_widget, 0, 0)
        main_layout.addWidget(self.gantt_widget, 0, 1)
        main_layout.addWidget(self.shared_scrollbar, 0, 2)

        self.table_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.gantt_chart.set_vertical_offset(0)
        self.table_view.verticalScrollBar().valueChanged.connect(self.on_table_scroll)

        self.adjust_all_row_heights()
        self.update_gantt_chart(set_unsaved=False)
        self.set_unsaved_changes(False)

        # Atajos de teclado
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.quick_save)
        QShortcut(QKeySequence("Ctrl+Z"), self).activated.connect(self.undo_action)
        QShortcut(QKeySequence("Ctrl+Y"), self).activated.connect(self.redo_action)

        self.installEventFilter(self)
        QTimer.singleShot(0, self.load_last_file)
        # Alerts: start the daily background timer and schedule startup check.
        # The startup check fires 600 ms after the event loop is running so the
        # main window is fully visible before the dialog appears.
        self.alert_manager = AlertManager(self.config)
        self._daily_alert_timer = self.alert_manager.schedule_daily_check(
            self._on_daily_alert_check
        )
        QTimer.singleShot(600, self._check_alerts_on_startup)

        # Update manager initialization
        self.app_version = __version__
        self.update_manager = UpdateManager(
            current_version=self.app_version,
            github_repo="Rudull/baby-project-manager",
            main_script_path=os.path.join(os.path.dirname(__file__), "main.py") if not getattr(sys, 'frozen', False) else None
        )
        
        self.update_manager.restart_required.connect(self._on_update_restart_required)
        self.update_manager.update_available.connect(self._on_background_update_available)
        
        # Cleanup old .old files from previous updates
        self.update_manager.cleanup_old_updates()
        
        # Delay auto check to not freeze startup
        QTimer.singleShot(2000, lambda: self.update_manager.check_updates(manual=False))

    def _on_background_update_available(self, version: str, download_url: str) -> None:
        """Handle background update detection."""
        reply = QMessageBox.information(
            self,
            "Actualización Disponible",
            f"Hay una nueva versión disponible ({version}).\n¿Deseas descargarla e instalarla ahora?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # We will use the about dialog to show progress, or create a simple progress dialog here
            from PySide6.QtWidgets import QProgressDialog
            self._bg_progress = QProgressDialog("Descargando actualización...", "Cancelar", 0, 100, self)
            self._bg_progress.setWindowTitle("Actualizando Baby Project Manager")
            self._bg_progress.setWindowModality(Qt.WindowModal)
            self._bg_progress.setAutoClose(True)
            self.update_manager.download_progress.connect(self._bg_progress.setValue)
            self._bg_progress.show()
            self.update_manager.perform_update()

    def _on_update_restart_required(self) -> None:
        """Handle the prompt to restart the application after update finishes."""
        reply = QMessageBox.information(
            self,
            "Actualización Completada",
            "La actualización se ha descargado e instalado.\nLa aplicación se reiniciará ahora.",
            QMessageBox.StandardButton.Ok
        )
        # We need to save configuration and changes before restarting
        self.config.set("Window", "width", self.width())
        self.config.set("Window", "height", self.height())
        self.config.set("Window", "pos_x", self.x())
        self.config.set("Window", "pos_y", self.y())
        if hasattr(self, 'task_table_widget'):
            self.task_table_widget.save_column_widths()
            if self.unsaved_changes:
                self.task_table_widget.save_file()
                
        # Call the update manager's restart function
        self.update_manager.restart_application()

    # ------------------------------------------------------------------
    # Undo / Redo
    # ------------------------------------------------------------------

    def undo_action(self) -> None:
        """Ejecuta deshacer."""
        logger.debug(
            "undo_action: can_undo=%s, history=%d",
            self.command_manager.can_undo(),
            len(self.command_manager.command_history),
        )
        if not self.command_manager.undo():
            logger.debug("Nothing to undo.")

    def redo_action(self) -> None:
        """Ejecuta rehacer."""
        logger.debug("redo_action: can_redo=%s", self.command_manager.can_redo())
        if not self.command_manager.redo():
            logger.debug("Nothing to redo.")

    def update_undo_status(self, can_undo: bool) -> None:
        pass  # Extension future: update toolbar button

    def update_redo_status(self, can_redo: bool) -> None:
        pass  # Extension future: update toolbar button

    # ------------------------------------------------------------------
    # Alert integration
    # ------------------------------------------------------------------

    def _check_alerts_on_startup(self) -> None:
        """Show the alert summary dialog once per calendar day if relevant."""
        if not self.alert_manager.should_show_dialog_today():
            return
        alerts = self.alert_manager.get_active_alerts(self.model.tasks)
        if not alerts:
            return
        from alerts_dialog import AlertsDialog
        dlg = AlertsDialog(alerts, self.alert_manager, self)
        dlg.show()
        self.alert_manager.mark_shown_today()

    def _on_daily_alert_check(self) -> None:
        """Silent daily background check — resets the shown-today flag for tomorrow."""
        alerts = self.alert_manager.get_active_alerts(self.model.tasks)
        logger.info("Daily alert check: %d active alert(s).", len(alerts))
        # Reset so that tomorrows startup will show the dialog again if needed.
        self.config.set("Alerts", "last_shown_date", "")

    def show_task_reminder_dialog(self, task_index: int) -> None:
        """Opens the per-task reminder configuration dialog."""
        task = self.model.getTask(task_index)
        if not task:
            return
        from task_reminder_dialog import TaskReminderDialog
        dlg = TaskReminderDialog(task, self.config, self)
        if dlg.exec():
            self.set_unsaved_changes(True)


    # ------------------------------------------------------------------
    # Window geometry
    # ------------------------------------------------------------------

    def ensure_window_on_screen(self) -> None:
        """Mueve la ventana al monitor principal si está completamente fuera de pantalla."""
        window_rect = self.frameGeometry()
        on_screen = any(
            screen.availableGeometry().intersects(window_rect)
            for screen in QGuiApplication.screens()
        )
        if not on_screen:
            primary_geom = QGuiApplication.primaryScreen().availableGeometry()
            new_x = primary_geom.x() + (primary_geom.width() - self.width()) // 2
            new_y = primary_geom.y() + (primary_geom.height() - self.height()) // 2
            self.move(new_x, new_y)
            self.config.set("Window", "pos_x", str(new_x))
            self.config.set("Window", "pos_y", str(new_y))

    def load_window_geometry(self) -> None:
        try:
            width = int(self.config.get("Window", "width") or 1200)
            height = int(self.config.get("Window", "height") or 800)
            pos_x = int(self.config.get("Window", "pos_x") or 100)
            pos_y = int(self.config.get("Window", "pos_y") or 100)
        except (ValueError, TypeError):
            width, height, pos_x, pos_y = 1200, 800, 100, 100
        self.resize(width, height)
        self.move(pos_x, pos_y)
        self.ensure_window_on_screen()

    def load_last_file(self) -> None:
        """Carga el último archivo usado si existe."""
        last_file = self.config.get_last_file()
        if last_file:
            self._loading_file = True
            self.task_table_widget.load_tasks_from_file(last_file)
            self.command_manager.clear()
            self.set_unsaved_changes(False)
            self._loading_file = False

    # ------------------------------------------------------------------
    # Notes
    # ------------------------------------------------------------------

    def copy_current_notes(self) -> None:
        pass  # placeholder

    def paste_to_current_notes(self) -> None:
        pass  # placeholder

    def copy_task_notes(self, from_task: Task, to_task: Task) -> None:
        to_task.copy_notes_from(from_task)

    # ------------------------------------------------------------------
    # Scrollbar
    # ------------------------------------------------------------------

    def initialize_shared_scrollbar(self) -> None:
        self.update_shared_scrollbar_range()

    def update_shared_scrollbar_range(self) -> None:
        total_tasks = self.model.rowCount()
        visible_tasks = self.calculate_visible_tasks()
        max_scroll = max(total_tasks - visible_tasks, 0)
        self.shared_scrollbar.setRange(0, max_scroll)
        self.shared_scrollbar.setPageStep(visible_tasks)
        if total_tasks > visible_tasks:
            self.shared_scrollbar.setEnabled(True)
        else:
            self.shared_scrollbar.setEnabled(False)
            self.shared_scrollbar.setValue(0)
            self.gantt_chart.set_vertical_offset(0)

    def calculate_visible_tasks(self) -> int:
        visible_height = self.table_view.viewport().height()
        return math.ceil(visible_height / self.ROW_HEIGHT)

    def sync_scroll(self, value: int) -> None:
        self.table_view.verticalScrollBar().setValue(value)
        self.gantt_chart.set_vertical_offset(self.table_view.verticalOffset())

    def on_table_scroll(self, value: int) -> None:
        self.shared_scrollbar.setValue(value)
        self.gantt_chart.set_vertical_offset(self.table_view.verticalOffset())

    # ------------------------------------------------------------------
    # Title / unsaved state
    # ------------------------------------------------------------------

    def update_title(self) -> None:
        if self.unsaved_changes:
            self.setWindowTitle(f"*{self.base_title}")
        else:
            self.setWindowTitle(self.base_title)

    def set_unsaved_changes(self, value: bool) -> None:
        if self.unsaved_changes != value:
            self.unsaved_changes = value
            self.update_title()

    # ------------------------------------------------------------------
    # Row heights
    # ------------------------------------------------------------------

    def adjust_all_row_heights(self) -> None:
        for row in range(self.model.rowCount()):
            self.table_view.setRowHeight(row, self.ROW_HEIGHT)

    # ------------------------------------------------------------------
    # Date helpers (used by table_views delegates)
    # ------------------------------------------------------------------

    def validateAndCalculateDays(self, start_entry, end_entry, days_entry) -> None:
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

    def calculateEndDateIfChanged(self, start_entry, days_entry, end_entry) -> None:
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

    # ------------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------------

    def show_task_context_menu(self, global_pos: QPoint, task_index: int) -> None:
        if task_index < 0 or task_index >= self.model.rowCount():
            return
        task = self.model.getTask(task_index)
        if not task:
            return

        menu = QMenu()
        menu.addAction("Duplicar")
        if not task.is_subtask:
            menu.addAction("Insertar")
        menu.addAction("Mover arriba")
        menu.addAction("Mover abajo")
        if not task.is_subtask:
            menu.addAction("Convertir en subtarea")
            menu.addAction("Agregar subtarea")
        else:
            menu.addAction("Convertir en tarea padre")
        menu.addAction("Eliminar")
        menu.addAction("Color por defecto")
        if not task.is_subtask:
            menu.addSeparator()
            link_action = menu.addAction("Vincular con subtareas")
            link_action.setCheckable(True)
            link_action.setChecked(task.linked_to_subtasks)
        menu.addSeparator()
        menu.addAction("Copiar notas")
        paste_action = menu.addAction("Pegar notas")
        paste_action.setEnabled(hasattr(self, "_copied_notes"))
        menu.addSeparator()
        menu.addAction("🔔 Recordatorios...")

        action = menu.exec(global_pos)
        if action:
            self.handle_context_menu_action(action, task_index, task)
        menu.close()

    def handle_context_menu_action(self, action, task_index: int, task: Task) -> None:
        text = action.text()
        if text == "Duplicar":
            self.duplicate_task(task_index)
        elif text == "Insertar" and not task.is_subtask:
            self.insert_task(task_index)
        elif text == "Convertir en subtarea" and not task.is_subtask:
            self.convert_to_subtask(task_index)
        elif text == "Convertir en tarea padre" and task.is_subtask:
            self.convert_to_parent_task(task_index)
        elif text == "Mover arriba":
            self.move_task_up(task_index)
        elif text == "Mover abajo":
            self.move_task_down(task_index)
        elif text == "Agregar subtarea" and not task.is_subtask:
            self.add_subtask(task_index)
        elif text == "Eliminar":
            self.delete_task(task_index)
        elif text == "Color por defecto":
            self.reset_task_color(task_index)
        elif text == "Copiar notas":
            self._copied_notes = task
        elif text == "Pegar notas":
            if hasattr(self, "_copied_notes") and self._copied_notes:
                task.copy_notes_from(self._copied_notes)
                self.set_unsaved_changes(True)
        elif text == "Vincular con subtareas":
            command = ToggleLinkedDurationCommand(self, task_index, action.isChecked())
            self.command_manager.execute_command(command)
        elif text == "🔔 Recordatorios...":
            self.show_task_reminder_dialog(task_index)


    def show_context_menu(self, position: QPoint) -> None:
        index = self.table_view.indexAt(position)
        if index.isValid():
            global_pos = self.table_view.viewport().mapToGlobal(position)
            self.show_task_context_menu(global_pos, index.row())

    # ------------------------------------------------------------------
    # Gantt
    # ------------------------------------------------------------------

    def update_gantt_chart(self, set_unsaved: bool = True) -> None:
        self.tasks = [
            task
            for row in range(self.model.rowCount())
            if (task := self.model.getTask(row)) is not None
        ]

        self.gantt_chart.tasks = self.tasks
        today = QDate.currentDate()

        if self.tasks:
            min_date = min(
                (QDate.fromString(t.start_date, "dd/MM/yyyy") for t in self.tasks),
                default=today,
            )
            max_date = max(
                (QDate.fromString(t.end_date, "dd/MM/yyyy") for t in self.tasks),
                default=today.addDays(30),
            )
        else:
            min_date = today
            max_date = today.addDays(30)

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

        if min_date == max_date:
            max_date = min_date.addDays(1)

        days_total = min_date.daysTo(max_date) + 1
        available_width = self.gantt_widget.width() - self.shared_scrollbar.width()
        pixels_per_day = max(0.1, available_width / days_total)

        self.gantt_widget.update_parameters(min_date, max_date, pixels_per_day)
        self.gantt_chart.setMinimumHeight(
            max(len(self.tasks) * self.ROW_HEIGHT, self.gantt_widget.height())
        )
        self.gantt_chart.update()
        self.gantt_header.update()
        self.gantt_widget.updateGeometry()

        if set_unsaved and self.tasks:
            self.set_unsaved_changes(True)

        self.update_shared_scrollbar_range()

    # ------------------------------------------------------------------
    # View modes
    # ------------------------------------------------------------------

    def set_period(self, days: int) -> None:
        self.selected_period = days
        self.update_gantt_chart()

    def set_year_view(self) -> None:
        self.current_view = "year"
        self.update_gantt_chart(set_unsaved=False)

    def set_complete_view(self) -> None:
        self.current_view = "complete"
        self.update_gantt_chart(set_unsaved=False)

    def set_one_month_view(self) -> None:
        self.current_view = "one_month"
        self.update_gantt_chart(set_unsaved=False)

    def set_three_month_view(self) -> None:
        self.current_view = "three_month"
        self.update_gantt_chart(set_unsaved=False)

    def set_six_month_view(self) -> None:
        self.current_view = "six_month"
        self.update_gantt_chart(set_unsaved=False)

    # ------------------------------------------------------------------
    # Zoom
    # ------------------------------------------------------------------

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            self.wheel_accumulator += delta
            if self.wheel_accumulator >= self.wheel_threshold:
                self.zoom_in_view()
                self.wheel_accumulator = 0
            elif self.wheel_accumulator <= -self.wheel_threshold:
                self.zoom_out_view()
                self.wheel_accumulator = 0
            event.accept()
        else:
            super().wheelEvent(event)

    def zoom_in_view(self) -> None:
        transitions = {
            "complete": self.set_year_view,
            "year": self.set_six_month_view,
            "six_month": self.set_three_month_view,
            "three_month": self.set_one_month_view,
        }
        action = transitions.get(self.current_view)
        if action:
            action()
        else:
            self.wheel_accumulator = 0

    def zoom_out_view(self) -> None:
        transitions = {
            "one_month": self.set_three_month_view,
            "three_month": self.set_six_month_view,
            "six_month": self.set_year_view,
            "year": self.set_complete_view,
        }
        action = transitions.get(self.current_view)
        if action:
            action()
        else:
            self.wheel_accumulator = 0

    # ------------------------------------------------------------------
    # Model events
    # ------------------------------------------------------------------

    def on_model_layout_changed(self) -> None:
        self.update_gantt_chart(set_unsaved=False)
        if not getattr(self, "_loading_file", False):
            self.set_unsaved_changes(True)

    def on_model_data_changed(
        self, topLeft: QModelIndex, bottomRight: QModelIndex, roles: list[int]
    ) -> None:
        if getattr(self, "_loading_file", False):
            return
        if not getattr(self.model, "_editing_programmatically", False):
            self.set_unsaved_changes(True)
            if Qt.ItemDataRole.EditRole in roles:
                self.update_gantt_chart(set_unsaved=False)

    def update_gantt_highlight(self, task_index: int | None) -> None:
        logger.debug("update_gantt_highlight: index=%s", task_index)
        self.gantt_chart.highlighted_task_index = task_index
        self.gantt_chart.update()

    # ------------------------------------------------------------------
    # Save / Close
    # ------------------------------------------------------------------

    def quick_save(self) -> None:
        if self.task_table_widget.save_file():
            self.set_unsaved_changes(False)

    def check_unsaved_changes(self) -> bool:
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Cambios sin guardar",
                "¿Desea guardar los cambios antes de continuar?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save,
            )
            if reply == QMessageBox.StandardButton.Save:
                return self.task_table_widget.save_file()
            if reply == QMessageBox.StandardButton.Cancel:
                return False
        return True

    def closeEvent(self, event) -> None:
        self.config.set("Window", "width", self.width())
        self.config.set("Window", "height", self.height())
        self.config.set("Window", "pos_x", self.x())
        self.config.set("Window", "pos_y", self.y())
        if hasattr(self, 'task_table_widget'):
            self.task_table_widget.save_column_widths()

        if self.unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Cambios sin guardar",
                "¿Desea guardar los cambios antes de salir?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save,
            )
            if reply == QMessageBox.StandardButton.Save:
                if self.task_table_widget.save_file():
                    self.cleanup_and_exit(event)
                else:
                    secondary = QMessageBox.question(
                        self,
                        "Error al guardar",
                        "No se pudieron guardar los cambios. ¿Desea salir sin guardar?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No,
                    )
                    if secondary == QMessageBox.StandardButton.Yes:
                        self.cleanup_and_exit(event)
                    else:
                        event.ignore()
            elif reply == QMessageBox.StandardButton.Discard:
                self.cleanup_and_exit(event)
            else:
                event.ignore()
        else:
            self.cleanup_and_exit(event)

    def cleanup_and_exit(self, event) -> None:
        for window in self.file_gui_windows:
            window.close()
        try:
            from jvm_manager import JVMManager
            if JVMManager.is_jvm_started():
                JVMManager.shutdown()
        except Exception as err:
            logger.error("Error shutting down JVM: %s", err, exc_info=True)
        event.accept()

    # ------------------------------------------------------------------
    # Resize / Show events
    # ------------------------------------------------------------------

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.update_gantt_chart(set_unsaved=False)
        self.task_table_widget.adjust_button_size()
        self.update_shared_scrollbar_range()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self.initial_layout_adjustment)

    def initial_layout_adjustment(self) -> None:
        self.update_gantt_chart(set_unsaved=False)

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------

    def show_about_dialog(self) -> None:
        about_dialog = AboutDialog(self)
        about_dialog.exec()

    def show_report_dialog(self) -> None:
        """Opens the dual-option report problem dialog."""
        from report_dialog import ReportDialog
        dlg = ReportDialog(self)
        dlg.exec()

    def get_primary_screen(self):
        return self.screen()

    def print_task_table_contents(self) -> None:
        """Debug helper: logs task table contents at DEBUG level."""
        for task in self.model.tasks:
            logger.debug("Task: name=%s obj=%r", task.name, task)


if __name__ == "__main__":
    import sys as _sys
    from logger_config import setup_logging as _setup_logging

    _setup_logging()

    _app = QApplication(_sys.argv)
    _app.setStyle("Fusion")
    _app.setPalette(_app.style().standardPalette())

    _window = MainWindow()
    _window.show()
    _sys.exit(_app.exec())
