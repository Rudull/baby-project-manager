#pdf_extractor.py
#3

import re
import pdfplumber
from PySide6.QtCore import QThread, Signal
from filter_util import normalize_string, is_start_end_task

class TaskTreeNode:
    def __init__(self, task):
        self.task = task
        self.children = []

def extract_tasks(file_path):
    """Extrae tareas y construye un árbol de tareas desde un archivo PDF."""
    tasks = []
    task_tree = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split('\n')
            for line in lines:
                # Inicializar variables con valores por defecto
                task_id = None
                task_name = None
                start_date = None
                end_date = None
                level = 0

                # Intentar los patrones de coincidencia
                match = re.match(
                    r'(\d+)\s+(.*?)\s+(\d+\s*(?:días|days))?\s*(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}/\d{1,2}/\d{4})',
                    line
                )
                if not match:
                    match = re.match(
                        r'(.*?)\s+(\d+)\s+(\d+\s*(?:días|days))?\s*(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}/\d{1,2}/\d{4})',
                        line
                    )

                if match:
                    if len(match.groups()) == 5:
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

                        # Calcular nivel de indentación
                        try:
                            chars = page.extract_words()
                            for char in chars:
                                if task_name in char.get('text', ''):
                                    x0 = char['x0']
                                    level = int(x0 / 20)
                                    break
                            else:
                                level = 0
                        except:
                            leading_spaces = len(line) - len(line.lstrip())
                            level = leading_spaces // 4
                            if level > 10:
                                level = 0

                        if task_id and task_name and start_date and end_date:
                            task = {
                                'task_id': task_id,
                                'level': level,
                                'name': task_name,
                                'start_date': start_date,
                                'end_date': end_date,
                                'indentation': level
                            }

                            if not is_start_end_task(task_name):
                                tasks.append(task)
                                task_tree.append(TaskTreeNode(task))

    # Construir jerarquía de tareas
    for i in range(len(task_tree)):
        node = task_tree[i]
        if i > 0:
            for j in range(i-1, -1, -1):
                potential_parent = task_tree[j]
                if potential_parent.task['level'] < node.task['level']:
                    potential_parent.children.append(node)
                    break

    return tasks, task_tree

class PDFLoaderThread(QThread):
    tasks_extracted = Signal(list, list)  # Señal para enviar tareas y árbol de tareas

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        tasks, task_tree = extract_tasks(self.file_path)
        self.tasks_extracted.emit(tasks, task_tree)
