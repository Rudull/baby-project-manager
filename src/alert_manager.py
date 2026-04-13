"""alert_manager.py
Pure business-logic layer for the milestone alerts system.
No Qt widgets here — only QDate, QTimer and the Config/Task model.

Rules enforced:
  1. Only one dialog per calendar day (last_shown_date in config.ini).
  2. Tasks silenced with snoozed_until="never" are always excluded.
  3. Tasks snoozed until a future date are excluded until that date passes.
  4. Only tasks whose end_date is in the *future* are shown as "upcoming".
  5. Overdue tasks (end_date < today) are shown as a secondary group.
  6. Extra reminders are compared against today independently.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Literal

from PySide6.QtCore import QDate, QTimer

from config_manager import ConfigManager

# Import Task lazily to avoid circular imports at module level.
# alert_manager is imported by main_window; models imports command_system.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from models import Task

logger = logging.getLogger("bpm.alert_manager")

AlertKind = Literal["upcoming", "overdue", "extra_reminder"]


@dataclass(frozen=True)
class AlertEntry:
    """Represents a single actionable alert for a task."""

    task: "Task"
    kind: AlertKind
    days_remaining: int          # negative → already overdue
    reminder_date: str | None = None   # only set for extra_reminder kind
    reminder_comment: str | None = None # only set for extra_reminder kind


class AlertManager:
    """Manages alert detection, snooze state, and daily QTimer scheduling."""

    _DATE_FMT = "dd/MM/yyyy"

    def __init__(self, config: ConfigManager) -> None:
        self._config = config
        self._daily_timer: QTimer | None = None

    # ------------------------------------------------------------------
    # Public API — detection
    # ------------------------------------------------------------------

    def is_enabled(self) -> bool:
        return self._config.get("Alerts", "enabled", "true").lower() == "true"

    def global_threshold(self) -> int:
        """Returns the global days-before threshold."""
        try:
            return int(self._config.get("Alerts", "days_before") or "7")
        except (ValueError, TypeError):
            return 7

    def should_show_dialog_today(self) -> bool:
        """Returns True only if the startup dialog has NOT been shown today."""
        if not self.is_enabled():
            return False
        show_on_startup = self._config.get("Alerts", "show_on_startup", "true")
        if show_on_startup.lower() != "true":
            return False
        last = self._config.get("Alerts", "last_shown_date", "")
        today_str = QDate.currentDate().toString(self._DATE_FMT)
        return last != today_str

    def mark_shown_today(self) -> None:
        """Records today as the last date the dialog was shown."""
        today_str = QDate.currentDate().toString(self._DATE_FMT)
        self._config.set("Alerts", "last_shown_date", today_str)

    def get_active_alerts(self, tasks: list["Task"]) -> list[AlertEntry]:
        """
        Returns the list of AlertEntry items that should be shown right now.

        Order: upcoming (soonest first) → extra_reminders → overdue (most recent first).
        Silenced and snoozed tasks are excluded.
        """
        today = QDate.currentDate()
        threshold = self.global_threshold()
        upcoming: list[AlertEntry] = []
        overdue: list[AlertEntry] = []
        extra: list[AlertEntry] = []

        for task in tasks:
            if self._is_silenced(task, today):
                continue

            # --- extra reminders (checked independently of end_date) ---
            for rem in task.extra_reminders:
                if isinstance(rem, str):
                    rem = {"date": rem, "comment": "Recordatorio general", "frequency": "once"}
                
                rem_str = rem.get("date", "")
                comment = rem.get("comment", "")
                freq = rem.get("frequency", "once")

                rem_date = QDate.fromString(rem_str, self._DATE_FMT)
                if not rem_date.isValid():
                    continue
                
                days_to_rem = today.daysTo(rem_date)
                fires = False
                
                if days_to_rem <= 0:  # Today is on or after the scheduled date
                    if freq == "once":
                        # For "once", we alert on the exact day. If missed, it still fires 
                        # until they delete it? Let's say if days_to_rem <= 0 it fires 
                        # so they don't miss it.
                        fires = True
                    elif freq == "daily":
                        fires = True
                    elif freq == "weekly":
                        # Fires on the exact same day of the week, on or after the date
                        fires = (abs(days_to_rem) % 7 == 0)
                    elif freq == "monthly":
                        # Fires on the same day of the month
                        fires = (today.day() == rem_date.day())
                        
                if fires:
                    extra.append(
                        AlertEntry(
                            task=task,
                            kind="extra_reminder",
                            days_remaining=0,  # Or days_to_rem if we want to show it's overdue
                            reminder_date=rem_str,
                            reminder_comment=comment
                        )
                    )

            # --- end_date proximity ---
            end_date = QDate.fromString(task.end_date, self._DATE_FMT)
            if not end_date.isValid():
                continue

            days_remaining = today.daysTo(end_date)
            task_threshold = (
                task.alert_threshold_days
                if task.alert_threshold_days is not None
                else threshold
            )

            if days_remaining < 0:
                overdue.append(
                    AlertEntry(task=task, kind="overdue", days_remaining=days_remaining)
                )
            elif days_remaining <= task_threshold:
                upcoming.append(
                    AlertEntry(task=task, kind="upcoming", days_remaining=days_remaining)
                )

        # Sort: upcoming soonest first; overdue most-recent-first (least negative)
        upcoming.sort(key=lambda e: e.days_remaining)
        overdue.sort(key=lambda e: e.days_remaining, reverse=True)

        return upcoming + extra + overdue

    # ------------------------------------------------------------------
    # Snooze / silence helpers
    # ------------------------------------------------------------------

    def snooze_task(self, task: "Task", days: int | None) -> None:
        """
        Snooze *task* for *days* days.
        Pass days=None to silence permanently ("never").
        """
        if days is None:
            task.alert_snoozed_until = "never"
        else:
            snooze_until = QDate.currentDate().addDays(days)
            task.alert_snoozed_until = snooze_until.toString(self._DATE_FMT)
        logger.debug(
            "Task '%s' snoozed until %s", task.name, task.alert_snoozed_until
        )

    def unsnooze_task(self, task: "Task") -> None:
        """Clears any active snooze/silence on *task*."""
        task.alert_snoozed_until = None

    def _is_silenced(self, task: "Task", today: QDate) -> bool:
        """Returns True if the task should be excluded from alerts."""
        val = task.alert_snoozed_until
        if not val:
            return False
        if val == "never":
            return True
        snooze_date = QDate.fromString(val, self._DATE_FMT)
        if not snooze_date.isValid():
            return False
        return today <= snooze_date

    # ------------------------------------------------------------------
    # Scheduling — daily background check
    # ------------------------------------------------------------------

    def schedule_daily_check(self, callback: Callable[[], None]) -> QTimer:
        """
        Returns a QTimer that fires *callback* at the configured check_time
        each day, starting from the *next* occurrence.

        The timer chains itself: after firing it reschedules for 24 h later.
        """
        timer = QTimer()
        timer.setSingleShot(True)

        def _fire() -> None:
            logger.info("Daily alert check triggered.")
            callback()
            # Reschedule for exactly 24 hours later (drift-safe)
            timer.start(24 * 60 * 60 * 1000)

        timer.timeout.connect(_fire)
        ms_until = self._ms_until_next_check()
        timer.start(ms_until)
        logger.debug(
            "Daily alert timer scheduled: fires in %.1f h", ms_until / 3_600_000
        )
        self._daily_timer = timer
        return timer

    def _ms_until_next_check(self) -> int:
        """Milliseconds from now until the next configured check_time today or tomorrow."""
        from datetime import datetime, timedelta

        check_time_str = self._config.get("Alerts", "check_time", "08:00") or "08:00"
        try:
            hour, minute = (int(p) for p in check_time_str.split(":"))
        except (ValueError, AttributeError):
            hour, minute = 8, 0

        now = datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)

        delta_ms = int((target - now).total_seconds() * 1000)
        return max(delta_ms, 1000)   # at least 1 s to avoid immediate fire on startup
