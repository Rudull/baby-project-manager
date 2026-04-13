"""pdf_extractor.py
Extracts task data from PDF project files in a background QThread.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

import pdfplumber
from PySide6.QtCore import QThread, Signal

from filter_util import is_start_end_task

logger = logging.getLogger("bpm.pdf_extractor")


class TaskTreeNode:
    def __init__(self, task: dict[str, Any]) -> None:
        self.task = task
        self.children: list[TaskTreeNode] = []


def extract_tasks(
    file_path: str,
) -> tuple[list[dict[str, Any]], list[TaskTreeNode]]:
    """Extrae tareas y construye un árbol de tareas desde un archivo PDF."""
    tasks: list[dict[str, Any]] = []
    task_tree: list[TaskTreeNode] = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            for line in text.split("\n"):
                task_id: str | None = None
                task_name: str | None = None
                start_date: str | None = None
                end_date: str | None = None
                level = 0

                match = re.match(
                    r"(\d+)\s+(.*?)\s+(\d+\s*(?:días|days))?\s*"
                    r"(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}/\d{1,2}/\d{4})",
                    line,
                )
                if not match:
                    match = re.match(
                        r"(.*?)\s+(\d+)\s+(\d+\s*(?:días|days))?\s*"
                        r"(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}/\d{1,2}/\d{4})",
                        line,
                    )

                if match and len(match.groups()) == 5:
                    if match.group(1).isdigit():
                        task_id = match.group(1)
                        task_name = match.group(2).strip()
                        start_date = match.group(4)
                        end_date = match.group(5)
                    else:
                        task_name = match.group(1).strip()
                        task_id = match.group(2)
                        start_date = match.group(4)
                        end_date = match.group(5)

                    # Calcular nivel de indentación por posición x en página
                    try:
                        chars = page.extract_words()
                        for char in chars:
                            if task_name in char.get("text", ""):
                                level = int(char["x0"] / 20)
                                break
                        else:
                            level = 0
                    except Exception as err:
                        logger.debug(
                            "Word position extraction failed, using indentation "
                            "fallback: %s",
                            err,
                        )
                        leading_spaces = len(line) - len(line.lstrip())
                        level = min(leading_spaces // 4, 10)

                    if task_id and task_name and start_date and end_date:
                        task: dict[str, Any] = {
                            "task_id": task_id,
                            "level": level,
                            "name": task_name,
                            "start_date": start_date,
                            "end_date": end_date,
                            "indentation": level,
                        }

                        if not is_start_end_task(task_name):
                            try:
                                start = datetime.strptime(start_date, "%d/%m/%Y")
                                end = datetime.strptime(end_date, "%d/%m/%Y")
                                if start != end:
                                    tasks.append(task)
                                    task_tree.append(TaskTreeNode(task))
                            except ValueError as err:
                                logger.debug(
                                    "Date parse error for task '%s' (%s / %s): %s"
                                    " — adding task anyway",
                                    task_name,
                                    start_date,
                                    end_date,
                                    err,
                                )
                                tasks.append(task)
                                task_tree.append(TaskTreeNode(task))

    # Construir jerarquía de tareas
    for i, node in enumerate(task_tree):
        if i > 0:
            for j in range(i - 1, -1, -1):
                potential_parent = task_tree[j]
                if potential_parent.task["level"] < node.task["level"]:
                    potential_parent.children.append(node)
                    break

    return tasks, task_tree


class PDFLoaderThread(QThread):
    # Signal emits (tasks list, task_tree list)
    tasks_extracted: Signal = Signal(list, list)

    def __init__(self, file_path: str) -> None:
        super().__init__()
        self.file_path = file_path

    def run(self) -> None:
        tasks, task_tree = extract_tasks(self.file_path)
        self.tasks_extracted.emit(tasks, task_tree)
