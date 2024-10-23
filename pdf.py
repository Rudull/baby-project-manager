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
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Mode ID", "Task ID", "Level", "Task Name", "Start Date", "End Date", "Source File"])
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

    def extract_tasks(self, file_path):
        self.tasks = []
        self.task_tree = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                lines = text.split('\n')
                for line in lines:
                    # This regex pattern now captures both ID numbers
                    match = re.match(r'(\d+)\s+(\d+)\s+(.*?)\s+(\d+\s+días)\s+(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}/\d{1,2}/\d{4})', line)
                    if match:
                        mode_id, task_id, task_name, _, start_date, end_date = match.groups()
                        indentation = len(line) - len(line.lstrip())
                        level = indentation // 8  # Assuming 8 spaces per indentation level
                        task = {
                            'mode_id': mode_id,
                            'task_id': task_id,
                            'level': level,
                            'name': task_name,
                            'start_date': start_date,
                            'end_date': end_date,
                            'indentation': indentation
                        }
                        self.tasks.append(task)
                        self.task_tree.append(TaskTreeNode(task))

        # Creamos la jerarquía de tareas
        for i in range(len(self.task_tree)):
            node = self.task_tree[i]
            if i > 0:
                prev_node = self.task_tree[i-1]
                if node.task['level'] > prev_node.task['level']:
                    prev_node.children.append(node)

    def populate_table(self):
        self.table.setRowCount(len(self.tasks))
        for row, task in enumerate(self.tasks):
            self.table.setItem(row, 0, QTableWidgetItem(task['mode_id']))
            self.table.setItem(row, 1, QTableWidgetItem(task['task_id']))
            self.table.setItem(row, 2, QTableWidgetItem(str(task['level'])))
            if task['level'] > 0:
                parent_task = self.task_tree[row-1].task
                self.table.setItem(row, 3, QTableWidgetItem(f"{parent_task['name']} -> {task['name']}"))
            else:
                self.table.setItem(row, 3, QTableWidgetItem('  ' * task['level'] + task['name']))
            self.table.setItem(row, 4, QTableWidgetItem(task['start_date']))
            self.table.setItem(row, 5, QTableWidgetItem(task['end_date']))
            self.table.setItem(row, 6, QTableWidgetItem(self.source_file))
        self.table.resizeColumnsToContents()
        self.update_task_counter()

    def normalize_string(self, s):
        return ''.join(c for c in unicodedata.normalize('NFD', s)
                       if unicodedata.category(c) != 'Mn').lower()

    def filter_tasks(self):
        search_terms = [self.normalize_string(term.strip()) for term in self.search_bar.text().split(',') if term.strip()]
        
        visible_tasks = 0
        for row in range(self.table.rowCount()):
            task_name = self.normalize_string(self.table.item(row, 3).text())
            
            # If all search terms are in the task name (regardless of order), show the row
            if all(term in task_name for term in search_terms):
                self.table.setRowHidden(row, False)
                visible_tasks += 1
            else:
                self.table.setRowHidden(row, True)
        
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
