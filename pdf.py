# pdf 1
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QFileDialog, QTableWidget, QTableWidgetItem, QLineEdit, QLabel
from PySide6.QtCore import Qt
import pdfplumber
import re
from datetime import datetime
import unicodedata

class TaskTreeNode:
    def __init__(self, task):
        self.task = task
        self.children = []

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Gantt Chart Extractor")
        self.setGeometry(100, 100, 1200, 600)

        # Main layout
        main_layout = QVBoxLayout()

        # Button to load PDF
        self.load_button = QPushButton("Load PDF")
        self.load_button.clicked.connect(self.load_pdf)
        main_layout.addWidget(self.load_button)

        # Search bar and task counter
        search_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search tasks (comma-separated for multiple terms)...")
        self.search_bar.textChanged.connect(self.filter_tasks)
        search_layout.addWidget(self.search_bar)

        self.task_counter = QLabel("Tasks found: 0")
        search_layout.addWidget(self.task_counter)

        main_layout.addLayout(search_layout)

        # Table to display tasks
        self.table = QTableWidget()
        self.table.setColumnCount(6)  # Removed one ID column
        self.table.setHorizontalHeaderLabels(["Task ID", "Level", "Task Name", "Start Date", "End Date", "Source File"])
        main_layout.addWidget(self.table)

        # Set the central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.tasks = []
        self.task_tree = []
        self.source_file = ""

    def load_pdf(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open PDF File", "", "PDF Files (*.pdf)")
        if file_name:
            self.source_file = file_name
            self.extract_tasks(file_name)
            self.populate_table()

    def is_start_end_task(self, task_name):
        normalized_name = self.normalize_string(task_name)
        start_end_keywords = ['inicio', 'fin', 'start', 'end', 'comienzo', 'final']
        return any(keyword in normalized_name for keyword in start_end_keywords)

    def extract_tasks(self, file_path):
        self.tasks = []
        self.task_tree = []

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                lines = text.split('\n')
                for line in lines:
                    # Inicializar variables con valores por defecto
                    task_id = None
                    task_name = None
                    start_date = None
                    end_date = None
                    level = 0

                    # Intentar los patrones de coincidencia
                    match = re.match(r'(\d+)\s+(.*?)\s+(\d+\s*(?:días|days))?\s*(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}/\d{1,2}/\d{4})', line)
                    if not match:
                        match = re.match(r'(.*?)\s+(\d+)\s+(\d+\s*(?:días|days))?\s*(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}/\d{1,2}/\d{4})', line)

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

                            # Calculate indentation level
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

                                if not self.is_start_end_task(task_name):
                                    self.tasks.append(task)
                                    self.task_tree.append(TaskTreeNode(task))

        # Build task hierarchy
        for i in range(len(self.task_tree)):
            node = self.task_tree[i]
            if i > 0:
                for j in range(i-1, -1, -1):
                    potential_parent = self.task_tree[j]
                    if potential_parent.task['level'] < node.task['level']:
                        potential_parent.children.append(node)
                        break

    def populate_table(self):
        self.table.setRowCount(len(self.tasks))
        for row, task in enumerate(self.tasks):
            self.table.setItem(row, 0, QTableWidgetItem(task['task_id']))
            self.table.setItem(row, 1, QTableWidgetItem(str(task['level'])))

            task_name = task['name']
            if task['level'] > 0:
                parent_found = False
                for i in range(row-1, -1, -1):
                    if self.tasks[i]['level'] < task['level']:
                        parent_task = self.tasks[i]
                        task_name = f"{parent_task['name']} -> {task_name}"
                        parent_found = True
                        break

            self.table.setItem(row, 2, QTableWidgetItem('  ' * task['level'] + task_name))
            self.table.setItem(row, 3, QTableWidgetItem(task['start_date']))
            self.table.setItem(row, 4, QTableWidgetItem(task['end_date']))
            self.table.setItem(row, 5, QTableWidgetItem(self.source_file))

        self.table.resizeColumnsToContents()
        self.update_task_counter()

    def normalize_string(self, s):
        return ''.join(c for c in unicodedata.normalize('NFD', s)
                       if unicodedata.category(c) != 'Mn').lower()

    def filter_tasks(self):
        search_terms = [self.normalize_string(term.strip())
                       for term in self.search_bar.text().split(',')
                       if term.strip()]

        visible_tasks = 0
        for row in range(self.table.rowCount()):
            task_name = self.table.item(row, 2).text()
            normalized_task_name = self.normalize_string(task_name)

            if self.is_start_end_task(task_name):
                self.table.setRowHidden(row, True)
                continue

            if search_terms:
                if all(term in normalized_task_name for term in search_terms):
                    self.table.setRowHidden(row, False)
                    visible_tasks += 1
                else:
                    self.table.setRowHidden(row, True)
            else:
                self.table.setRowHidden(row, False)
                visible_tasks += 1

        self.update_task_counter(visible_tasks)

    def update_task_counter(self, count=None):
        if count is None:
            count = self.table.rowCount()
        self.task_counter.setText(f"Tasks found: {count}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
