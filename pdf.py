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

    def extract_tasks(self, file_path):
        self.tasks = []
        self.task_tree = []
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                # Extract text and tables
                text = page.extract_text()
                tables = page.extract_tables()
                
                # Process each line of text
                lines = text.split('\n')
                for line in lines:
                    # Try different patterns to find task information
                    # Pattern 1: Look for ID at the start
                    match = re.match(r'(\d+)\s+(.*?)\s+(\d+\s*(?:días|days))?\s*(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}/\d{1,2}/\d{4})', line)
                    if not match:
                        # Pattern 2: Look for ID after task name
                        match = re.match(r'(.*?)\s+(\d+)\s+(\d+\s*(?:días|days))?\s*(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}/\d{1,2}/\d{4})', line)
                    
                    if match:
                        # Extract components based on which pattern matched
                        if len(match.groups()) == 5:
                            if match.group(1).isdigit():
                                # Pattern 1 matched
                                task_id = match.group(1)
                                task_name = match.group(2).strip()
                                start_date = match.group(4)
                                end_date = match.group(5)
                            else:
                                # Pattern 2 matched
                                task_name = match.group(1).strip()
                                task_id = match.group(2)
                                start_date = match.group(4)
                                end_date = match.group(5)

                        # Calculate indentation level
                        # First try to get visual indentation from the PDF
                        try:
                            chars = page.extract_words()
                            for char in chars:
                                if task_name in char.get('text', ''):
                                    x0 = char['x0']
                                    # Convert x0 position to indentation level (assuming 20 units per level)
                                    level = int(x0 / 20)
                                    break
                            else:
                                level = 0
                        except:
                            # If visual indentation fails, try to determine by leading spaces
                            leading_spaces = len(line) - len(line.lstrip())
                            level = leading_spaces // 4  # Assuming 4 spaces per indentation level
                            if level > 10:  # Sanity check
                                level = 0

                        task = {
                            'task_id': task_id,
                            'level': level,
                            'name': task_name,
                            'start_date': start_date,
                            'end_date': end_date,
                            'indentation': level
                        }
                        
                        self.tasks.append(task)
                        self.task_tree.append(TaskTreeNode(task))

        # Build task hierarchy
        for i in range(len(self.task_tree)):
            node = self.task_tree[i]
            if i > 0:
                # Look for the nearest parent (task with lower level)
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
            
            # Format task name with indentation and parent information
            task_name = task['name']
            if task['level'] > 0:
                # Find parent task
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
        search_terms = [self.normalize_string(term.strip()) for term in self.search_bar.text().split(',') if term.strip()]

        visible_tasks = 0
        for row in range(self.table.rowCount()):
            task_name = self.normalize_string(self.table.item(row, 2).text())

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