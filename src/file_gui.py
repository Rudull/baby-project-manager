#file_gui.py
#6
import sys
import os
import platform
import jpype
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
    QFileDialog, QTableWidget, QTableWidgetItem, QLineEdit, QLabel, QSizePolicy,
    QMessageBox, QColorDialog, QHeaderView
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor

from pdf_extractor import PDFLoaderThread, TaskTreeNode
from filter_util import normalize_string, is_start_end_task
import re
from loading_animation_widget import LoadingAnimationWidget
from jvm_manager import JVMManager

class MPPLoaderThread(QThread):
    tasks_extracted = Signal(list, list)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def format_outline_number(self, task):
        """Genera el número de esquema jerárquico para una tarea"""
        outline_number = task.getOutlineNumber()
        if outline_number is not None:
            return str(outline_number)
        return ''

    def run(self):
        try:
            from mpp_extractor import MPPReader
            mpp_reader = MPPReader()

            tasks = []
            task_tree = []

            from net.sf.mpxj.reader import UniversalProjectReader
            reader = UniversalProjectReader()
            project = reader.read(self.file_path)

            for task in project.getTasks():
                if task.getID() is None:
                    continue

                task_name = str(task.getName()) if task.getName() is not None else ''

                if is_start_end_task(task_name) or (task.getDuration() is not None and task.getDuration().getDuration() == 0):
                    continue

                outline_number = self.format_outline_number(task)

                task_dict = {
                    'task_id': str(task.getID()),
                    'level': outline_number,
                    'name': task_name,
                    'start_date': mpp_reader.format_date(task.getStart()),
                    'end_date': mpp_reader.format_date(task.getFinish()),
                    'indentation': task.getOutlineLevel() - 1,
                    'outline_level': task.getOutlineLevel() - 1
                }

                tasks.append(task_dict)
                task_tree.append(TaskTreeNode(task_dict))

            # Solo emitir los datos extraídos
            self.tasks_extracted.emit(tasks, task_tree)

        except Exception as e:
            print(f"Error al extraer tareas MPP: {e}")
            import traceback
            traceback.print_exc()
            self.tasks_extracted.emit([], [])

class XLSXLoaderThread(QThread):
    tasks_extracted = Signal(list, list)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            from xlsx_extractor import XLSXReader
            xlsx_reader = XLSXReader()
            tasks = xlsx_reader.read_xlsx(self.file_path)

            task_tree = []
            for task in tasks:
                if not is_start_end_task(task['name']):
                    task_tree.append(TaskTreeNode(task))

            # Solo emitir los datos extraídos
            self.tasks_extracted.emit(tasks, task_tree)

        except Exception as e:
            print(f"Error al extraer tareas XLSX: {e}")
            import traceback
            traceback.print_exc()
            self.tasks_extracted.emit([], [])

class MainWindow(QMainWindow):
    tasks_imported = Signal(list)

    # Constantes para anchos de columna
    COLUMN_WIDTHS = {
        'task_id': 50,    # Ancho de la columna "ID de Tarea"
        'level': 150,       # Ancho de la columna "Nivel"
        'name': 700,       # Ancho de la columna "Nombre de Tarea"
        'start_date': 100, # Ancho de la columna "Fecha Inicio"
        'end_date': 100,   # Ancho de la columna "Fecha Fin"
        'source': 200      # Ancho de la columna "Archivo Fuente"
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gantt Chart Extractor")
        self.setGeometry(100, 100, 1200, 600)

        # Inicializar atributos de color
        self.selected_color = None
        self.default_color = QColor(34, 163, 159)

        # Iniciar la JVM usando el manager
        self.jvm_manager = JVMManager()
        if not self.jvm_manager.start_jvm():
            QMessageBox.critical(
                self,
                "Error",
                "No se pudo iniciar la JVM. La funcionalidad de importación puede estar limitada."
            )

        # Inicializar botones
        self.init_buttons()

        # Layout principal
        main_layout = QVBoxLayout()

        # Crear un único layout horizontal para todos los botones
        all_buttons_layout = QHBoxLayout()

        # Agregar todos los botones al mismo layout horizontal
        all_buttons_layout.addWidget(self.load_pdf_button)
        all_buttons_layout.addWidget(self.load_mpp_button)
        all_buttons_layout.addWidget(self.load_xlsx_button)
        all_buttons_layout.addWidget(self.save_filter_button)
        all_buttons_layout.addWidget(self.load_filter_button)
        all_buttons_layout.addWidget(self.select_color_button)
        all_buttons_layout.addWidget(self.add_tasks_button)

        # Agregar el layout de botones al layout principal
        main_layout.addLayout(all_buttons_layout)

        # Barra de búsqueda y filtro
        search_title = QLabel("Buscador")
        main_layout.addWidget(search_title)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Buscar tareas (todas las palabras, separadas por comas)...")
        self.search_bar.textChanged.connect(self.filter_tasks)
        main_layout.addWidget(self.search_bar)

        filter_title = QLabel("Filtro")
        main_layout.addWidget(filter_title)

        # Entradas de filtro
        search_parent_layout = QVBoxLayout()
        labels_layout = QHBoxLayout()
        include_label = QLabel("Incluir palabras:")
        exclude_label = QLabel("Excluir palabras:")
        labels_layout.addWidget(include_label)
        labels_layout.addWidget(exclude_label)
        search_parent_layout.addLayout(labels_layout)

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
        self.task_counter = QLabel("Tareas encontradas: 0")
        search_parent_layout.addWidget(self.task_counter)

        main_layout.addLayout(search_parent_layout)

        # Tabla para mostrar tareas
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nivel", "Nombre de Tarea",
            "Fecha Inicio", "Fecha Fin", "Archivo Fuente"
        ])

        # Obtener el header horizontal
        header = self.table.horizontalHeader()

        # Establecer los anchos iniciales y el comportamiento de redimensionamiento
        # Columnas con ancho fijo
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Fixed)

        # Columna del nombre con redimensionamiento flexible
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        # Establecer los anchos iniciales
        self.table.setColumnWidth(0, self.COLUMN_WIDTHS['task_id'])
        self.table.setColumnWidth(1, self.COLUMN_WIDTHS['level'])
        # La columna 2 (nombre) se ajustará automáticamente
        self.table.setColumnWidth(3, self.COLUMN_WIDTHS['start_date'])
        self.table.setColumnWidth(4, self.COLUMN_WIDTHS['end_date'])
        self.table.setColumnWidth(5, self.COLUMN_WIDTHS['source'])

        main_layout.addWidget(self.table)

        # Animación de carga
        self.loading_animation = LoadingAnimationWidget()
        main_layout.addWidget(self.loading_animation)

        # Establece el widget central
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Variables de estado
        self.tasks = []
        self.task_tree = []
        self.source_file = ""
        self.loader_thread = None

    def init_buttons(self):
        """Inicializa todos los botones de la interfaz."""
        # Botones de carga y filtros
        self.load_pdf_button = QPushButton("Cargar PDF")
        self.load_mpp_button = QPushButton("Cargar MPP")
        self.load_xlsx_button = QPushButton("Cargar XLSX")
        self.save_filter_button = QPushButton("Guardar Filtro")
        self.load_filter_button = QPushButton("Cargar Filtro")

        # Botones de color y agregar tareas
        self.select_color_button = QPushButton("Seleccionar Color")
        self.add_tasks_button = QPushButton("Agregar Tareas al Canvas")

        # Conectar señales
        self.load_pdf_button.clicked.connect(self.load_pdf_file)
        self.load_mpp_button.clicked.connect(self.load_mpp_file)
        self.load_xlsx_button.clicked.connect(self.load_xlsx_file)
        self.save_filter_button.clicked.connect(self.save_filter)
        self.load_filter_button.clicked.connect(self.load_filter)
        self.select_color_button.clicked.connect(self.select_color)
        self.add_tasks_button.clicked.connect(self.add_tasks_to_canvas)

        # Configurar un tamaño mínimo uniforme para todos los botones
        min_button_width = 120
        for button in [self.load_pdf_button, self.load_mpp_button,
                      self.load_xlsx_button, self.save_filter_button,
                      self.load_filter_button, self.select_color_button,
                      self.add_tasks_button]:
            button.setMinimumWidth(min_button_width)
            button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

    def load_pdf_file(self):
        self.load_file(file_type='pdf')

    def load_mpp_file(self):
        self.load_file(file_type='mpp')

    def load_xlsx_file(self):
        self.load_file(file_type='xlsx')

    def load_file(self, file_type=None):
        if file_type == 'pdf':
            file_filter = "Archivos PDF (*.pdf)"
        elif file_type == 'mpp':
            file_filter = "Archivos MPP (*.mpp)"
        elif file_type == 'xlsx':
            file_filter = "Archivos Excel (*.xlsx)"
        else:
            file_filter = "Archivos (*.pdf *.mpp *.xlsx)"

        file_name, _ = QFileDialog.getOpenFileName(self, "Abrir Archivo", "", file_filter)
        if file_name:
            self.source_file = file_name
            self.reset_color_selection()
            self.show_loading(True)
            self.load_pdf_button.setEnabled(False)
            self.load_mpp_button.setEnabled(False)
            self.load_xlsx_button.setEnabled(False)

            if file_name.lower().endswith('.pdf'):
                self.loader_thread = PDFLoaderThread(file_name)
            elif file_name.lower().endswith('.mpp'):
                self.loader_thread = MPPLoaderThread(file_name)
            elif file_name.lower().endswith('.xlsx'):
                self.loader_thread = XLSXLoaderThread(file_name)
            else:
                QMessageBox.warning(self, "Archivo no soportado",
                                  "Por favor seleccione un archivo PDF, MPP o XLSX.")
                self.show_loading(False)
                self.load_pdf_button.setEnabled(True)
                self.load_mpp_button.setEnabled(True)
                self.load_xlsx_button.setEnabled(True)
                return

            self.loader_thread.tasks_extracted.connect(self.on_tasks_extracted)
            self.loader_thread.start()

    def on_tasks_extracted(self, tasks, task_tree):
        """Solo cargar las tareas en la tabla, sin emitir la señal de importación"""
        self.tasks = tasks
        self.task_tree = task_tree
        self.populate_table()
        self.show_loading(False)
        self.load_pdf_button.setEnabled(True)
        self.load_mpp_button.setEnabled(True)
        self.load_xlsx_button.setEnabled(True)

    def show_loading(self, show):
        if show:
            self.loading_animation.start()
        else:
            self.loading_animation.stop()

    def populate_table(self):
        self.table.setRowCount(len(self.tasks))
        for row, task in enumerate(self.tasks):
            try:
                # ID de Tarea
                self.table.setItem(row, 0, QTableWidgetItem(str(task.get('task_id', ''))))

                # Nivel
                self.table.setItem(row, 1, QTableWidgetItem(str(task.get('level', ''))))

                # Nombre de la tarea con indentación visual
                task_name = self.clean_task_name(task.get('name', ''))

                # Usamos outline_level para la indentación visual
                indentation = task.get('outline_level', 0)
                display_name = '    ' * indentation + task_name
                self.table.setItem(row, 2, QTableWidgetItem(display_name))

                # Fechas con verificación
                start_date = task.get('start_date', '')
                end_date = task.get('end_date', '')

                if not start_date:
                    start_date = "N/A"
                if not end_date:
                    end_date = "N/A"

                self.table.setItem(row, 3, QTableWidgetItem(str(start_date)))
                self.table.setItem(row, 4, QTableWidgetItem(str(end_date)))

                # Archivo fuente
                self.table.setItem(row, 5, QTableWidgetItem(self.source_file))

            except Exception as e:
                print(f"Error al procesar tarea {row}: {str(e)}")
                continue

        self.update_task_counter()

    def clean_task_name(self, name):
        """Limpia el nombre de la tarea, maneja casos donde name no es string."""
        if name is None:
            return ""

        # Convertir a string si no lo es
        name = str(name)

        cleaned_name = re.sub(r'^\d+[\.\-\s]+', '', name)
        return cleaned_name

    def filter_tasks(self):
        search_terms = [normalize_string(term.strip()) for term in self.search_bar.text().split(',') if term.strip()]
        include_terms = [normalize_string(term.strip()) for term in self.include_bar.text().split(',') if term.strip()]
        exclude_terms = [normalize_string(term.strip()) for term in self.exclude_bar.text().split(',') if term.strip()]
        visible_tasks = 0

        for row in range(self.table.rowCount()):
            task_name = self.table.item(row, 2).text()
            normalized_task_name = normalize_string(task_name)
            if self.table.item(row, 1).text() == "":  # Omitir si no hay ID
                self.table.setRowHidden(row, True)
                continue

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
        file_name, _ = QFileDialog.getSaveFileName(self, "Guardar Filtro", "", "Archivos de Filtro (*.ft)")
        if file_name:
            if not file_name.endswith('.ft'):
                file_name += '.ft'
            include_terms = self.include_bar.text()
            exclude_terms = self.exclude_bar.text()
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(f"Incluir:{include_terms}\n")
                f.write(f"Excluir:{exclude_terms}\n")

    def load_filter(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Cargar Filtro", "", "Archivos de Filtro (*.ft)")
        if file_name:
            with open(file_name, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                include_terms = ''
                exclude_terms = ''
                for line in lines:
                    if line.startswith("Incluir:"):
                        include_terms = line[len("Incluir:"):].strip()
                    elif line.startswith("Excluir:"):
                        exclude_terms = line[len("Excluir:"):].strip()
                self.include_bar.setText(include_terms)
                self.exclude_bar.setText(exclude_terms)
                self.filter_tasks()

    def closeEvent(self, event):
        # No cerrar la JVM aquí, se manejará al cerrar la aplicación principal
        event.accept()

    def select_color(self):
        color = QColorDialog.getColor(initial=self.default_color, parent=self)
        if color.isValid():
            self.selected_color = color
            # Cambiar el color de fondo del botón para indicar el color seleccionado
            self.select_color_button.setStyleSheet(
                        f"""
                        QPushButton {{
                            background-color: {color.name()};
                            color: {'white' if color.lightness() < 128 else 'black'};
                            border: 1px solid #666;
                            padding: 5px;
                        }}
                        QPushButton:hover {{
                            background-color: {color.lighter(110).name()};
                        }}
                        """
                    )

    def reset_color_selection(self):
        """Reinicia la selección de color cuando se carga un nuevo archivo."""
        self.selected_color = None
        self.select_color_button.setStyleSheet("")

    def add_tasks_to_canvas(self):
        if not hasattr(self, 'tasks') or not self.tasks:
            QMessageBox.warning(
                self,
                "Sin datos",
                "No hay tareas cargadas. Por favor, importe un archivo primero."
            )
            return

        visible_tasks_count = sum(1 for row in range(self.table.rowCount())
                                if not self.table.isRowHidden(row))

        if visible_tasks_count == 0:
            QMessageBox.warning(
                self,
                "Sin tareas",
                "No hay tareas visibles para agregar. Ajuste los filtros si es necesario."
            )
            return

        # Si no hay color seleccionado, mostrar diálogo
        if self.selected_color is None:
            reply = QMessageBox.question(
                self,
                "Color no seleccionado",
                "No ha seleccionado un color para las tareas. ¿Desea usar el color por defecto?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.selected_color = self.default_color
            else:
                self.select_color()
                return

        # Obtener solo las tareas visibles (no filtradas)
        visible_tasks = []
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                task_data = {
                    'name': self.table.item(row, 2).text().strip(),
                    'start_date': self.table.item(row, 3).text().strip(),
                    'end_date': self.table.item(row, 4).text().strip(),
                    'color': self.selected_color.name()
                }
                visible_tasks.append(task_data)

        # Emitir señal con las tareas visibles y el color seleccionado
        if visible_tasks:
                self.tasks_imported.emit(visible_tasks)
                QMessageBox.information(
                    self,
                    "Tareas agregadas",
                    f"Se han agregado {len(visible_tasks)} tareas al canvas."
                )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
