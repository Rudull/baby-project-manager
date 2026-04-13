"""global_alerts_dialog.py
Dialog to configure global alert settings.
Allows configuring whether alerts are enabled, global days threshold,
daily check time, and whether to show summary on startup.
"""
from __future__ import annotations

import logging
from PySide6.QtCore import Qt, QTime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QSpinBox, QTimeEdit, QDialogButtonBox, QWidget
)

from config_manager import ConfigManager

logger = logging.getLogger("bpm.global_alerts_dialog")


class GlobalAlertsDialog(QDialog):
    def __init__(
        self,
        config: ConfigManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("Configuración de Alertas")
        self.setMinimumWidth(350)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Enabled toggle
        self._chk_enabled = QCheckBox("Habilitar sistema de alertas")
        is_enabled = self._config.get("Alerts", "enabled", "true") == "true"
        self._chk_enabled.setChecked(is_enabled)
        layout.addWidget(self._chk_enabled)

        # Show on startup toggle
        self._chk_startup = QCheckBox("Mostrar resumen al arrancar (1 vez por día)")
        is_startup = self._config.get("Alerts", "show_on_startup", "true") == "true"
        self._chk_startup.setChecked(is_startup)
        layout.addWidget(self._chk_startup)

        # Days threshold
        days_layout = QHBoxLayout()
        days_layout.addWidget(QLabel("Umbral global (días antes del vencimiento):"))
        self._spin_days = QSpinBox()
        self._spin_days.setRange(1, 365)
        try:
            days_before = int(self._config.get("Alerts", "days_before") or "7")
        except ValueError:
            days_before = 7
        self._spin_days.setValue(days_before)
        days_layout.addStretch()
        days_layout.addWidget(self._spin_days)
        layout.addLayout(days_layout)

        # Automatic check time
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Hora de verificación automática diaria:"))
        self._time_edit = QTimeEdit()
        self._time_edit.setDisplayFormat("HH:mm")
        time_str = self._config.get("Alerts", "check_time", "08:00") or "08:00"
        try:
            h, m = map(int, time_str.split(":"))
            self._time_edit.setTime(QTime(h, m))
        except ValueError:
            self._time_edit.setTime(QTime(8, 0))
        time_layout.addStretch()
        time_layout.addWidget(self._time_edit)
        layout.addLayout(time_layout)

        # Enable/disable fields based on master toggle
        self._chk_enabled.toggled.connect(self._chk_startup.setEnabled)
        self._chk_enabled.toggled.connect(self._spin_days.setEnabled)
        self._chk_enabled.toggled.connect(self._time_edit.setEnabled)

        if not is_enabled:
            self._chk_startup.setEnabled(False)
            self._spin_days.setEnabled(False)
            self._time_edit.setEnabled(False)

        # Buttons
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _on_accept(self) -> None:
        self._config.set("Alerts", "enabled", str(self._chk_enabled.isChecked()).lower())
        self._config.set("Alerts", "show_on_startup", str(self._chk_startup.isChecked()).lower())
        self._config.set("Alerts", "days_before", str(self._spin_days.value()))
        self._config.set("Alerts", "check_time", self._time_edit.time().toString("HH:mm"))
        
        logger.debug("Alerts config updated.")
        self.accept()
