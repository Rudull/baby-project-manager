"""Shared pytest fixtures.

A single ``QApplication`` is created for the whole test session. Several of the
classes under test derive from ``QObject``/``QAbstractTableModel`` and are safest
to construct with a live application instance, even in headless CI (where the
Qt platform should be set to ``offscreen``).
"""
from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
