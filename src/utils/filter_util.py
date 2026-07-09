"""filter_util.py
Utility functions for normalizing and filtering task data.
"""
from __future__ import annotations

import unicodedata
from typing import Any


def normalize_string(s: str | None) -> str:
    """Normaliza una cadena eliminando acentos y convirtiéndola a minúsculas."""
    if s is None:
        return ""
    s = str(s)
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    ).lower()


def is_start_end_task(task_name: str | None) -> bool:
    """Determina si una tarea es una tarea de inicio o fin."""
    if task_name is None:
        return False
    task_name = str(task_name)
    normalized_name = normalize_string(task_name)
    start_end_keywords = ["inicio", "fin", "start", "end", "comienzo", "final"]
    return any(keyword in normalized_name for keyword in start_end_keywords)


def filter_tasks(
    tasks: list[dict[str, Any]],
    search_terms: list[str],
) -> list[dict[str, Any]]:
    """Filtra una lista de tareas según los términos de búsqueda."""
    filtered_tasks: list[dict[str, Any]] = []
    for task in tasks:
        task_name = task["name"]
        if is_start_end_task(task_name):
            continue
        normalized_task_name = normalize_string(task_name)
        if all(term in normalized_task_name for term in search_terms):
            filtered_tasks.append(task)
    return filtered_tasks
