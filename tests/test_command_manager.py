"""Tests for CommandManager's undo/redo history bookkeeping.

These exercise the manager's index/history logic with lightweight stub commands,
independent of the real MainWindow. Full command-with-window integration lives
in scratch/integration/.
"""
from __future__ import annotations

from core.command_system import Command, CommandManager


class RecordingCommand(Command):
    """A stub command that appends markers to a shared log on execute/undo."""

    def __init__(self, log, tag):
        super().__init__(f"cmd-{tag}")
        self.log = log
        self.tag = tag

    def execute(self):
        self.log.append(f"do-{self.tag}")

    def undo(self):
        self.log.append(f"undo-{self.tag}")


def test_execute_updates_state(qapp):
    mgr = CommandManager()
    log = []
    assert not mgr.can_undo()
    mgr.execute_command(RecordingCommand(log, "a"))
    assert log == ["do-a"]
    assert mgr.can_undo()
    assert not mgr.can_redo()


def test_undo_then_redo(qapp):
    mgr = CommandManager()
    log = []
    mgr.execute_command(RecordingCommand(log, "a"))

    assert mgr.undo() is True
    assert log == ["do-a", "undo-a"]
    assert not mgr.can_undo()
    assert mgr.can_redo()

    assert mgr.redo() is True
    assert log == ["do-a", "undo-a", "do-a"]
    assert mgr.can_undo()
    assert not mgr.can_redo()


def test_undo_with_empty_history_returns_false(qapp):
    mgr = CommandManager()
    assert mgr.undo() is False
    assert mgr.redo() is False


def test_new_command_truncates_redo_branch(qapp):
    mgr = CommandManager()
    log = []
    mgr.execute_command(RecordingCommand(log, "a"))
    mgr.execute_command(RecordingCommand(log, "b"))
    mgr.undo()  # back to state after 'a'
    assert mgr.can_redo()

    mgr.execute_command(RecordingCommand(log, "c"))
    # 'b' is now unreachable — redo must not resurrect it.
    assert not mgr.can_redo()
    assert len(mgr.command_history) == 2


def test_clear_resets_history(qapp):
    mgr = CommandManager()
    log = []
    mgr.execute_command(RecordingCommand(log, "a"))
    mgr.clear()
    assert not mgr.can_undo()
    assert not mgr.can_redo()
    assert mgr.command_history == []


def test_history_is_capped(qapp):
    mgr = CommandManager()
    mgr.max_history = 3
    log = []
    for i in range(5):
        mgr.execute_command(RecordingCommand(log, str(i)))
    assert len(mgr.command_history) == 3
    # Oldest commands were dropped; newest survive.
    assert [c.tag for c in mgr.command_history] == ["2", "3", "4"]
