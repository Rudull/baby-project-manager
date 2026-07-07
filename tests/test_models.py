"""Tests for the Task dataclass and TaskTableModel visibility/CRUD logic."""
from __future__ import annotations

from PySide6.QtGui import QColor

from core.models import Task, TaskTableModel


def _task(name, is_subtask=False):
    return Task(
        name=name,
        start_date="01/01/2026",
        end_date="02/01/2026",
        duration="1",
        dedication="40",
        is_subtask=is_subtask,
    )


def test_task_defaults(qapp):
    t = _task("A")
    # __post_init__ fills in the default color and file_links.
    assert isinstance(t.color, QColor)
    assert t.color == QColor(34, 163, 159)
    assert t.file_links == {}


def test_formatted_name_indents_subtasks(qapp):
    parent = _task("Parent")
    child = _task("Child", is_subtask=True)
    assert parent.formatted_name == "Parent"
    assert child.formatted_name.strip() == "Child"
    assert child.formatted_name.startswith(" ")


def test_visible_rows_track_task_list(qapp):
    tasks = [_task("A"), _task("B", is_subtask=True), _task("C")]
    model = TaskTableModel(tasks=tasks)
    assert model.rowCount() == 3


def test_collapsed_parent_hides_subtasks(qapp):
    parent = _task("Parent")
    sub1 = _task("Sub1", is_subtask=True)
    sub2 = _task("Sub2", is_subtask=True)
    tail = _task("Tail")
    model = TaskTableModel(tasks=[parent, sub1, sub2, tail])
    assert model.rowCount() == 4

    parent.is_collapsed = True
    model.update_visible_tasks()
    # Parent + Tail visible; the two subtasks are hidden.
    assert model.rowCount() == 2
    assert model.getTask(0) is parent
    assert model.getTask(1) is tail


def test_insert_and_remove_task(qapp):
    model = TaskTableModel(tasks=[_task("A")])
    model.insertTask(_task("B"))
    assert model.rowCount() == 2

    assert model.removeTask(0) is True
    assert model.rowCount() == 1
    assert model.getTask(0).name == "B"


def test_remove_out_of_range_returns_false(qapp):
    model = TaskTableModel(tasks=[_task("A")])
    assert model.removeTask(5) is False


def test_reminders_repr_roundtrips_via_literal_eval(qapp):
    # The .bpm format persists these two fields with repr()/ast.literal_eval;
    # this guards that fragile serialization for the common shapes.
    import ast

    reminders = ["01/01/2026", "15/03/2026"]
    file_links = {"spec": "/home/user/spec.pdf", "sheet": "C:\\data\\plan.xlsx"}

    assert ast.literal_eval(repr(reminders)) == reminders
    assert ast.literal_eval(repr(file_links)) == file_links
