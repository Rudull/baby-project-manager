import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QFileDialog, QTableWidget, QTableWidgetItem,
    QLineEdit, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt
from pdf_extractor import PDFLoaderThread
from filter_util import normalize_string, is_start_end_task
import re
from loading_animation_widget import LoadingAnimationWidget  # Asegúrate de tener este módulo

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Gantt Chart Extractor")
        self.setGeometry(100, 100, 1200, 600)

        # Layout principal
        main_layout = QVBoxLayout()

        # Layout horizontal para los botones
        button_layout = QHBoxLayout()
        self.load_button = QPushButton("Cargar PDF")
        self.load_button.clicked.connect(self.load_pdf)
        self.load_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button_layout.addWidget(self.load_button)

        self.save_filter_button = QPushButton("Guardar Filtro")
        self.save_filter_button.clicked.connect(self.save_filter)
        self.save_filter_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button_layout.addWidget(self.save_filter_button)

        self.load_filter_button = QPushButton("Cargar Filtro")
        self.load_filter_button.clicked.connect(self.load_filter)
        self.load_filter_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button_layout.addWidget(self.load_filter_button)

        main_layout.addLayout(button_layout)

        # Título para el Buscador
        search_title = QLabel("Buscador")
        main_layout.addWidget(search_title)

        # Barra de búsqueda original con funcionalidad de palabras separadas por comas
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Buscar tareas (todas las palabras, separadas por comas)...")
        self.search_bar.textChanged.connect(self.filter_tasks)
        main_layout.addWidget(self.search_bar)

        # Título para el Filtro
        filter_title = QLabel("Filtro")
        main_layout.addWidget(filter_title)

        # Layout para las entradas de búsqueda y el contador de tareas
        search_parent_layout = QVBoxLayout()

        # Labels para las entradas de texto
        labels_layout = QHBoxLayout()
        include_label = QLabel("Incluir palabras:")
        exclude_label = QLabel("Excluir palabras:")
        labels_layout.addWidget(include_label)
        labels_layout.addWidget(exclude_label)
        search_parent_layout.addLayout(labels_layout)

        # Entradas de texto
        inputs_layout = QHBoxLayout()
        self.include_bar = QLineEdit()
        self.include_bar.setPlaceholderText("Palabras a incluir (separadas por comas)...")
        self.include_bar.textChanged.connect(self.filter_tasks)
        inputs_layout.addWidget(self.include_bar)

        self.exclude_bar = QLineEdit()
        self.exclude_bar.setPlaceholderText("Palabras a excluir (separadas por comas)...")
        self.exclude_bar.textChanged.connect(self.filter_tasks)
        inputs_layout.addWidget(self.exclude_bar)
        search_parent_layout.addLayout(inputs_layout)

        # Contador de tareas
        self.task_counter = QLabel("Tareas encontradas: 0")
        search_parent_layout.addWidget(self.task_counter)

        main_layout.addLayout(search_parent_layout)

        # Tabla para mostrar tareas
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID de Tarea", "Nivel", "Nombre de Tarea", "Fecha Inicio", "Fecha Fin", "Archivo Fuente"])
        main_layout.addWidget(self.table)

        # Animación de carga
        self.loading_animation = LoadingAnimationWidget()
        main_layout.addWidget(self.loading_animation)

        # Configurar widget central
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.tasks = []
        self.task_tree = []
        self.source_file = ""

        # Inicializar el hilo
        self.loader_thread = None

    def load_pdf(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Abrir Archivo PDF", "", "Archivos PDF (*.pdf)")
        if file_name:
            self.source_file = file_name
            self.show_loading(True)
            self.load_button.setEnabled(False)  # Desactivar el botón mientras carga

            # Iniciar el hilo de carga
            self.loader_thread = PDFLoaderThread(file_name)
            self.loader_thread.tasks_extracted.connect(self.on_tasks_extracted)
            self.loader_thread.start()

    def on_tasks_extracted(self, tasks, task_tree):
        self.tasks = tasks
        self.task_tree = task_tree
        self.populate_table()
        self.show_loading(False)
        self.load_button.setEnabled(True)  # Rehabilitar el botón

    def show_loading(self, show):
        if show:
            self.loading_animation.start()
        else:
            self.loading_animation.stop()

    def populate_table(self):
        self.table.setRowCount(len(self.tasks))
        for row, task in enumerate(self.tasks):
            # Establecer el ID de la tarea en la columna correspondiente
            self.table.setItem(row, 0, QTableWidgetItem(task['task_id']))
            self.table.setItem(row, 1, QTableWidgetItem(str(task['level'])))

            # Limpiar el nombre de la tarea para eliminar cualquier ID o prefijo no deseado
            task_name = self.clean_task_name(task['name'])

            # Construir el nombre de la tarea con la jerarquía adecuada
            if task['level'] > 0:
                for i in range(row-1, -1, -1):
                    if self.tasks[i]['level'] < task['level']:
                        parent_task = self.tasks[i]
                        parent_name = self.clean_task_name(parent_task['name'])
                        task_name = f"{parent_name} -> {task_name}"
                        break
            # Añadir indentación para reflejar el nivel de la tarea
            display_name = '  ' * task['level'] + task_name
            self.table.setItem(row, 2, QTableWidgetItem(display_name))

            # Establecer las fechas y el archivo fuente
            self.table.setItem(row, 3, QTableWidgetItem(task['start_date']))
            self.table.setItem(row, 4, QTableWidgetItem(task['end_date']))
            self.table.setItem(row, 5, QTableWidgetItem(self.source_file))

        self.table.resizeColumnsToContents()
        self.update_task_counter()

    def clean_task_name(self, name):
        """
        Limpia el nombre de la tarea eliminando cualquier prefijo numérico o de puntuación.
        Por ejemplo, convierte "1. Diseño" en "Diseño".
        """
        # Usa una expresión regular para eliminar números al inicio, puntos, guiones y espacios
        cleaned_name = re.sub(r'^\d+[\.\-\s]+', '', name)
        return cleaned_name

    def filter_tasks(self):
        # Procesar términos de búsqueda del filtro superior
        search_terms = [normalize_string(term.strip())
                        for term in self.search_bar.text().split(',')
                        if term.strip()]
        include_terms = [normalize_string(term.strip())
                         for term in self.include_bar.text().split(',')
                         if term.strip()]
        exclude_terms = [normalize_string(term.strip())
                         for term in self.exclude_bar.text().split(',')
                         if term.strip()]

        visible_tasks = 0
        for row in range(self.table.rowCount()):
            task_name = self.table.item(row, 2).text()
            normalized_task_name = normalize_string(task_name)

            if is_start_end_task(task_name):
                self.table.setRowHidden(row, True)
                continue

            # Verificar si la tarea cumple con los términos de búsqueda, inclusión y exclusión
            # Cambiado a 'all()' para que solo muestre tareas que contengan todas las palabras
            search_match = all(term in normalized_task_name for term in search_terms) if search_terms else True
            include_match = any(term in normalized_task_name for term in include_terms) if include_terms else True
            exclude_match = any(term in normalized_task_name for term in exclude_terms) if exclude_terms else False

            if search_match and include_match and not exclude_match:
                self.table.setRowHidden(row, False)
                visible_tasks += 1
            else:
                self.table.setRowHidden(row, True)

        self.update_task_counter(visible_tasks)

    def update_task_counter(self, count=None):
        if count is None:
            count = self.table.rowCount()
        self.task_counter.setText(f"Tareas encontradas: {count}")

    def save_filter(self):
        # Abrir diálogo para guardar archivo con extensión .ft
        file_name, _ = QFileDialog.getSaveFileName(self, "Guardar Filtro", "", "Archivos de Filtro (*.ft)")
        if file_name:
            # Asegurarse de que el archivo tenga la extensión .ft
            if not file_name.endswith('.ft'):
                file_name += '.ft'

            # Obtener los términos actuales de inclusión y exclusión
            include_terms = self.include_bar.text()
            exclude_terms = self.exclude_bar.text()

            # Guardar los términos en el archivo
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(f"Incluir:{include_terms}\n")
                f.write(f"Excluir:{exclude_terms}\n")

    def load_filter(self):
        # Abrir diálogo para seleccionar archivo de filtro con extensión .ft
        file_name, _ = QFileDialog.getOpenFileName(self, "Cargar Filtro", "", "Archivos de Filtro (*.ft)")
        if file_name:
            # Leer los términos de inclusión y exclusión del archivo
            with open(file_name, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            include_terms = ''
            exclude_terms = ''

            for line in lines:
                if line.startswith("Incluir:"):
                    include_terms = line[len("Incluir:"):].strip()
                elif line.startswith("Excluir:"):
                    exclude_terms = line[len("Excluir:"):].strip()

            # Establecer los términos en las cajas de texto correspondientes
            self.include_bar.setText(include_terms)
            self.exclude_bar.setText(exclude_terms)

            # Actualizar el filtrado
            self.filter_tasks()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
