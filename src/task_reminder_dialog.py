"""task_reminder_dialog.py
Per-task reminder configuration dialog, accessible via the task context menu.

Allows the user to:
  - Override the global alert threshold for this specific task.
  - Permanently silence alerts for this task.
  - Add / remove exact-date extra reminders.

Changes are applied directly to the Task object on dialog acceptance.
The caller is responsible for marking unsaved changes.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QSpinBox, QGroupBox,
    QListWidget, QListWidgetItem, QWidget, QFrame, QDialogButtonBox,
    QDateEdit, QLineEdit, QComboBox, QFormLayout
)

if TYPE_CHECKING:
    from models import Task
from config_manager import ConfigManager

logger = logging.getLogger("bpm.task_reminder_dialog")

_DATE_FMT = "dd/MM/yyyy"


class TaskReminderDialog(QDialog):
    """Dialog for per-task reminder configuration."""

    def __init__(
        self,
        task: "Task",
        config: ConfigManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._task = task
        self._config = config
        # Working copies — only written to task on accept()
        self._threshold_override: int | None = task.alert_threshold_days
        self._snoozed_until: str | None = task.alert_snoozed_until
        self._reminders: list[dict] = []
        for r in task.extra_reminders:
            if isinstance(r, str):
                self._reminders.append({"date": r, "comment": "Recordatorio general", "frequency": "once"})
            else:
                self._reminders.append(r.copy())
        self._build_ui()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.setWindowTitle(f"Recordatorios — {self._task.name}")
        self.setMinimumWidth(400)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(14, 14, 14, 14)

        # ── Threshold section ──────────────────────────────────────────
        threshold_box = QGroupBox("Umbral de alerta")
        t_layout = QVBoxLayout(threshold_box)
        t_layout.setSpacing(6)

        global_days = self._get_global_threshold()
        self._btn_global = QRadioButton(
            f"Usar configuración global ({global_days} días)"
        )
        self._btn_custom = QRadioButton("Personalizar:")
        self._btn_silence = QRadioButton("Silenciar esta tarea (no molestar)")

        self._btn_group = QButtonGroup(self)
        for btn in (self._btn_global, self._btn_custom, self._btn_silence):
            self._btn_group.addButton(btn)
            t_layout.addWidget(btn)

        # Inline spinbox for custom threshold
        custom_row = QHBoxLayout()
        custom_row.setContentsMargins(22, 0, 0, 0)
        self._spin_days = QSpinBox()
        self._spin_days.setRange(1, 365)
        self._spin_days.setValue(
            self._threshold_override if self._threshold_override is not None
            else global_days
        )
        self._spin_days.setSuffix(" días antes del vencimiento")
        self._spin_days.setEnabled(False)
        custom_row.addWidget(self._spin_days)
        custom_row.addStretch()
        t_layout.addLayout(custom_row)

        # Set initial radio state
        if self._snoozed_until == "never":
            self._btn_silence.setChecked(True)
        elif self._threshold_override is not None:
            self._btn_custom.setChecked(True)
            self._spin_days.setEnabled(True)
        else:
            self._btn_global.setChecked(True)

        self._btn_custom.toggled.connect(self._spin_days.setEnabled)

        root.addWidget(threshold_box)

        # ── Extra reminders section ────────────────────────────────────
        rem_box = QGroupBox("Recordatorios adicionales independientes")
        r_layout = QVBoxLayout(rem_box)
        r_layout.setSpacing(6)

        self._list = QListWidget()
        self._list.setMaximumHeight(120)
        for rem in self._reminders:
            self._add_list_item(rem)
        
        remove_btn = QPushButton("Eliminar seleccionada")
        remove_btn.clicked.connect(self._on_remove_reminder)
        
        r_layout.addWidget(self._list)
        r_layout.addWidget(remove_btn, alignment=Qt.AlignmentFlag.AlignRight)

        # Separator for the form
        r_line = QFrame()
        r_line.setFrameShape(QFrame.Shape.HLine)
        r_layout.addWidget(r_line)

        # Form to add new reminder
        form_layout = QFormLayout()
        
        self._edit_comment = QLineEdit()
        self._edit_comment.setPlaceholderText("Ej: Enviar correo solicitando equipos")
        form_layout.addRow("Comentario:", self._edit_comment)
        
        date_freq_layout = QHBoxLayout()
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDisplayFormat(_DATE_FMT)
        self._date_edit.setDate(QDate.currentDate())
        
        self._freq_combo = QComboBox()
        self._freq_combo.addItems(["Una vez", "Diario", "Semanal", "Mensual"])
        
        date_freq_layout.addWidget(self._date_edit)
        date_freq_layout.addWidget(QLabel(" Frecuencia:"))
        date_freq_layout.addWidget(self._freq_combo)
        
        form_layout.addRow("Fecha:", date_freq_layout)
        r_layout.addLayout(form_layout)

        add_btn = QPushButton("+ Añadir recordatorio")
        add_btn.clicked.connect(self._on_add_reminder)
        r_layout.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignRight)

        root.addWidget(rem_box)

        # ── Separator + buttons ────────────────────────────────────────
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        root.addWidget(line)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        root.addWidget(btn_box)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_global_threshold(self) -> int:
        try:
            return int(self._config.get("Alerts", "days_before") or "7")
        except (ValueError, TypeError):
            return 7

    def _add_list_item(self, rem: dict) -> None:
        date_str = rem.get("date", "")
        comment = rem.get("comment", "")
        freq = rem.get("frequency", "once")
        
        icons = {"once": "📅", "daily": "🔁", "weekly": "🔁", "monthly": "🔁"}
        icon = icons.get(freq, "📅")
        
        freq_es = {"once": "Una vez", "daily": "Diario", "weekly": "Semanal", "monthly": "Mensual"}
        freq_label = freq_es.get(freq, "Una vez")
        
        display_text = f"{icon} [{freq_label}] {date_str} - {comment}"
        item = QListWidgetItem(display_text)
        # We index it by reference or id? No, just store the dict string or index.
        # Actually storing the dict id could be problematic for deletion if copies are made.
        # Let's store the dict directly as python object in UserRole.
        item.setData(Qt.ItemDataRole.UserRole, rem)
        self._list.addItem(item)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_add_reminder(self) -> None:
        date_str = self._date_edit.date().toString(_DATE_FMT)
        comment = self._edit_comment.text().strip()
        if not comment:
            comment = "Sin título"
            
        freq_map = {0: "once", 1: "daily", 2: "weekly", 3: "monthly"}
        freq = freq_map.get(self._freq_combo.currentIndex(), "once")
        
        new_rem = {"date": date_str, "comment": comment, "frequency": freq}
        self._reminders.append(new_rem)
        
        # Sort by date
        self._reminders.sort(key=lambda x: QDate.fromString(x.get("date", ""), _DATE_FMT))
        
        self._list.clear()
        for d in self._reminders:
            self._add_list_item(d)
            
        self._edit_comment.clear()

    def _on_remove_reminder(self) -> None:
        current = self._list.currentItem()
        if current is None:
            return
        rem = current.data(Qt.ItemDataRole.UserRole)
        # Remove by exact match
        for i, r in enumerate(self._reminders):
            if r.get("date") == rem.get("date") and r.get("comment") == rem.get("comment"):
                self._reminders.pop(i)
                break
        self._list.takeItem(self._list.row(current))

    def _on_accept(self) -> None:
        task = self._task

        # Apply threshold choice
        if self._btn_silence.isChecked():
            task.alert_snoozed_until = "never"
            task.alert_threshold_days = None
        elif self._btn_custom.isChecked():
            task.alert_threshold_days = self._spin_days.value()
            if task.alert_snoozed_until == "never":
                task.alert_snoozed_until = None   # un-silence if switching away
        else:   # global
            task.alert_threshold_days = None
            if task.alert_snoozed_until == "never":
                task.alert_snoozed_until = None

        # Apply extra reminders (deep copy just to be safe)
        task.extra_reminders = [r.copy() for r in self._reminders]

        logger.debug(
            "Reminder config saved for '%s': threshold=%s, snoozed=%s, extras=%s",
            task.name,
            task.alert_threshold_days,
            task.alert_snoozed_until,
            task.extra_reminders,
        )
        self.accept()
