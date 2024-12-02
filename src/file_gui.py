#file_gui.py
#
import sys
import os
import platform
import jpype
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
    QFileDialog, QTableWidget, QTableWidgetItem, QLineEdit, QLabel, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from pdf_extractor import PDFLoaderThread, TaskTreeNode
from filter_util import normalize_string, is_start_end_task
import re
from loading_animation_widget import LoadingAnimationWidget

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
            from filter_util import is_start_end_task

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

            # Construir jerarquía
            for i in range(len(task_tree)):
                node = task_tree[i]
                if i > 0:
                    for j in range(i - 1, -1, -1):
                        potential_parent = task_tree[j]
                        if potential_parent.task['outline_level'] < node.task['outline_level']:
                            potential_parent.children.append(node)
                            break

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
            from filter_util import is_start_end_task

            xlsx_reader = XLSXReader()
            tasks = xlsx_reader.read_xlsx(self.file_path)

            task_tree = []
            for task in tasks:
                if not is_start_end_task(task['name']):
                    task_tree.append(TaskTreeNode(task))

            # Construir jerarquía
            for i in range(len(task_tree)):
                node = task_tree[i]
                if i > 0:
                    for j in range(i - 1, -1, -1):
                        potential_parent = task_tree[j]
                        if potential_parent.task['outline_level'] < node.task['outline_level']:
                            potential_parent.children.append(node)
                            break

            self.tasks_extracted.emit(tasks, task_tree)

        except Exception as e:
            print(f"Error al extraer tareas XLSX: {e}")
            import traceback
            traceback.print_exc()
            self.tasks_extracted.emit([], [])

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gantt Chart Extractor")
        self.setGeometry(100, 100, 1200, 600)

        # Iniciar la JVM en el hilo principal
        self.start_jvm()

        # Layout principal
        main_layout = QVBoxLayout()

        # Layout horizontal para botones
        button_layout = QHBoxLayout()

        # Botón para cargar archivo PDF
        self.load_pdf_button = QPushButton("Cargar PDF")
        self.load_pdf_button.clicked.connect(self.load_pdf_file)
        self.load_pdf_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button_layout.addWidget(self.load_pdf_button)

        # Botón para cargar archivo MPP
        self.load_mpp_button = QPushButton("Cargar MPP")
        self.load_mpp_button.clicked.connect(self.load_mpp_file)
        self.load_mpp_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button_layout.addWidget(self.load_mpp_button)

        # Botón para cargar archivo XLSX
        self.load_xlsx_button = QPushButton("Cargar XLSX")
        self.load_xlsx_button.clicked.connect(self.load_xlsx_file)
        self.load_xlsx_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button_layout.addWidget(self.load_xlsx_button)

        # Botón para guardar filtro
        self.save_filter_button = QPushButton("Guardar Filtro")
        self.save_filter_button.clicked.connect(self.save_filter)
        self.save_filter_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button_layout.addWidget(self.save_filter_button)

        # Botón para cargar filtro
        self.load_filter_button = QPushButton("Cargar Filtro")
        self.load_filter_button.clicked.connect(self.load_filter)
        self.load_filter_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button_layout.addWidget(self.load_filter_button)

        main_layout.addLayout(button_layout)

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
        self.table.setHorizontalHeaderLabels(["ID de Tarea", "Nivel", "Nombre de Tarea", "Fecha Inicio", "Fecha Fin", "Archivo Fuente"])
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

    def start_jvm(self):
        if jpype.isJVMStarted():
            print("JVM ya iniciada.")
            return
        system = platform.system()

        # Agregar las propiedades para deshabilitar el registro de Log4j2
        jvm_args = [
            "-Dlog4j2.loggerContextFactory=org.apache.logging.log4j.simple.SimpleLoggerContextFactory",
            "-Dorg.apache.logging.log4j.simplelog.StatusLogger.level=OFF",
            "-Dlog4j2.level=OFF"
        ]

        try:
            if system == "Windows":
                # Obtener JAVA_HOME
                java_home = os.environ.get("JAVA_HOME")
                if not java_home:
                    raise EnvironmentError(
                        "La variable de entorno JAVA_HOME no está configurada. "
                        "Por favor, configúrala apuntando al directorio de instalación del JDK."
                    )

                # Construir la ruta a jvm.dll
                jvm_path = os.path.join(java_home, "bin", "server", "jvm.dll")
                if not os.path.exists(jvm_path):
                    # Intentar con 'client' si 'server' no existe
                    jvm_path = os.path.join(java_home, "bin", "client", "jvm.dll")
                    if not os.path.exists(jvm_path):
                        raise FileNotFoundError(
                            f"No se encontró jvm.dll en las rutas:\n"
                            f" - {os.path.join(java_home, 'bin', 'server', 'jvm.dll')}\n"
                            f" - {os.path.join(java_home, 'bin', 'client', 'jvm.dll')}"
                        )

                # Iniciar la JVM con la ruta especificada y argumentos
                jpype.startJVM(
                    jvm_path,
                    *jvm_args
                )
            else:
                # Otros sistemas operativos (Linux, macOS, etc.)
                jpype.startJVM(
                    jpype.getDefaultJVMPath(),
                    *jvm_args
                )
            print("JVM iniciada correctamente.")
        except Exception as e:
            print(f"Error al iniciar la JVM: {e}")
            sys.exit(1)

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

        self.table.resizeColumnsToContents()
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
        try:
            if jpype.isJVMStarted():
                jpype.shutdownJVM()
        except Exception as e:
            print(f"Error al cerrar la JVM: {e}")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
