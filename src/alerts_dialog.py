"""alerts_dialog.py
Modal summary dialog shown at app startup when there are active alerts.

Design rules (anti-saturation):
 - Upcoming tasks shown first, grouped and sorted soonest→latest.
 - Overdue tasks shown collapsed inside a QGroupBox (secondary importance).
 - Extra reminders shown between the two groups.
 - Each row has a Snooze drop-down (1d / 3d / 7d) and a Silence button.
 - "Dismiss" closes without recording anything (dialog may reappear tomorrow).
 - "Don't show today" calls mark_shown_today() so it won't reopen same day.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QScrollArea, QWidget, QComboBox, QFrame, QSizePolicy,
)

from alert_manager import AlertEntry, AlertManager

if TYPE_CHECKING:
    from models import Task

logger = logging.getLogger("bpm.alerts_dialog")


class _AlertRow(QWidget):
    """A single row in the alert list."""

    _SNOOZE_OPTIONS: list[tuple[str, int | None]] = [
        ("Posponer…", -1),
        ("1 día",      1),
        ("3 días",     3),
        ("7 días",     7),
        ("Silenciar",  None),
    ]

    def __init__(
        self,
        entry: AlertEntry,
        alert_manager: AlertManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._entry = entry
        self._manager = alert_manager
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        # Bullet + task name + days badge
        task = self._entry.task
        if self._entry.kind == "upcoming":
            days = self._entry.days_remaining
            if days == 0:
                badge = "hoy"
                color = "#e05252"
            elif days == 1:
                badge = "mañana"
                color = "#e07a52"
            else:
                badge = f"en {days} días"
                color = "#d4a017" if days <= 3 else "#555"
        elif self._entry.kind == "overdue":
            days_ago = abs(self._entry.days_remaining)
            badge = f"venció hace {days_ago} día{'s' if days_ago != 1 else ''}"
            color = "#888"
        else:  # extra_reminder
            badge = f"🗓️ {self._entry.reminder_date}"
            color = "#3a8fd4"

        name_text = f"<b>{task.name}</b>"
        if self._entry.kind == "extra_reminder" and self._entry.reminder_comment:
            name_text += f"<br><span style='color:#666; font-size:11px;'>{self._entry.reminder_comment}</span>"

        name_label = QLabel(name_text)
        name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        badge_label = QLabel(f"<span style='color:{color};'>{badge}</span>")
        badge_label.setFixedWidth(160)
        badge_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Snooze combo — only for upcoming / extra_reminder
        self._snooze_combo = QComboBox()
        for label, _ in self._SNOOZE_OPTIONS:
            self._snooze_combo.addItem(label)
        self._snooze_combo.setFixedWidth(110)
        self._snooze_combo.currentIndexChanged.connect(self._on_snooze_selected)

        if self._entry.kind == "overdue":
            self._snooze_combo.setEnabled(False)
            self._snooze_combo.setToolTip("No disponible para tareas vencidas")

        layout.addWidget(name_label)
        layout.addWidget(badge_label)
        layout.addWidget(self._snooze_combo)

    def _on_snooze_selected(self, index: int) -> None:
        if index == 0:  # "Posponer…" placeholder
            return
        _, days = self._SNOOZE_OPTIONS[index]
        self._manager.snooze_task(self._entry.task, days)
        label = "Silenciada" if days is None else f"Pospuesta {days}d"
        self.setEnabled(False)
        self.setToolTip(f"Acción aplicada: {label}")
        logger.debug("Alert action on '%s': %s", self._entry.task.name, label)


class AlertsDialog(QDialog):
    """
    Non-blocking summary dialog.

    Call .show() (not .exec()) so the user can still interact with the app.
    """

    def __init__(
        self,
        alerts: list[AlertEntry],
        alert_manager: AlertManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._alerts = alerts
        self._manager = alert_manager
        self._build_ui()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        from PySide6.QtCore import QDate

        today_str = QDate.currentDate().toString("dd/MM/yyyy")
        self.setWindowTitle("Recordatorios del proyecto")
        self.setMinimumWidth(520)
        self.setWindowFlags(
            self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
        )

        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(14, 14, 14, 14)

        # Header
        hdr = QLabel(
            f"<h3 style='margin:0;'>🔔 Recordatorios</h3>"
            f"<small style='color:#888;'>{today_str}</small>"
        )
        hdr.setTextFormat(Qt.TextFormat.RichText)
        root.addWidget(hdr)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        root.addWidget(line)

        # Separate alert kinds
        upcoming = [e for e in self._alerts if e.kind == "upcoming"]
        extra    = [e for e in self._alerts if e.kind == "extra_reminder"]
        overdue  = [e for e in self._alerts if e.kind == "overdue"]

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setSpacing(6)
        inner_layout.setContentsMargins(0, 0, 0, 0)

        if upcoming or extra:
            section_label = QLabel(
                f"<b>PRÓXIMAS ({len(upcoming) + len(extra)})</b>"
            )
            section_label.setStyleSheet("color: #333; font-size: 11px;")
            inner_layout.addWidget(section_label)
            for entry in upcoming + extra:
                inner_layout.addWidget(
                    _AlertRow(entry, self._manager, inner)
                )

        if overdue:
            overdue_box = QGroupBox(f"Vencidas ({len(overdue)})")
            overdue_box.setCheckable(True)
            overdue_box.setChecked(False)   # collapsed by default
            overdue_box.setStyleSheet(
                "QGroupBox { color: #888; font-size: 11px; }"
            )
            box_layout = QVBoxLayout(overdue_box)
            box_layout.setSpacing(4)
            for entry in overdue:
                box_layout.addWidget(_AlertRow(entry, self._manager, overdue_box))
            inner_layout.addWidget(overdue_box)

        inner_layout.addStretch()
        scroll.setWidget(inner)
        root.addWidget(scroll, 1)

        # Separator
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        root.addWidget(line2)

        # Footer buttons
        footer = QHBoxLayout()
        footer.setSpacing(8)

        no_today_btn = QPushButton("No mostrar hoy")
        no_today_btn.setToolTip(
            "Cierra el diálogo y no lo vuelve a mostrar hasta mañana"
        )
        no_today_btn.clicked.connect(self._on_no_today)

        close_btn = QPushButton("Cerrar")
        close_btn.setDefault(True)
        close_btn.clicked.connect(self.close)

        footer.addWidget(no_today_btn)
        footer.addStretch()
        footer.addWidget(close_btn)
        root.addLayout(footer)

        # Resize to content (cap height at 500 px)
        self.adjustSize()
        if self.height() > 500:
            self.resize(self.width(), 500)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _on_no_today(self) -> None:
        self._manager.mark_shown_today()
        logger.debug("User dismissed alerts dialog for today.")
        self.close()
