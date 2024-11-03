#mpp_extractor.py
#3
import sys
import os
import platform
import jpype
import mpxj
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog
)
from PySide6.QtCore import Qt


class ProjectManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Baby Project Manager")
        self.setMinimumSize(1000, 600)

        # Crear widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Crear layout vertical
        layout = QVBoxLayout(central_widget)

        # Crear botón para seleccionar archivo
        self.select_button = QPushButton("Seleccionar archivo .mpp")
        self.select_button.clicked.connect(self.select_file)
        layout.addWidget(self.select_button)

        # Crear tabla
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            'ID',
            'Nivel',
            'Tarea',
            'Fecha de Inicio',
            'Fecha de Fin',
            'Archivo Fuente'
        ])
        layout.addWidget(self.table)

        # Iniciar la JVM según el sistema operativo
        self.start_jvm()

    def start_jvm(self):
        """
        Inicia la JVM dependiendo del sistema operativo.
        En Windows, especifica la ruta a jvm.dll.
        En otros sistemas operativos, usa la configuración predeterminada.
        """
        system = platform.system()
        jvm_args = ["-Dorg.apache.logging.log4j.simplelog.StatusLogger.level=OFF"]

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
                    # Intentar con client si server no existe (para versiones antiguas de JDK)
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

    def format_outline_number(self, task):
        """Genera el número de esquema jerárquico para una tarea"""
        outline_number = task.getOutlineNumber()
        if outline_number is not None:
            return str(outline_number)
        else:
            return ''

    def format_date(self, date):
        """Convierte la fecha a formato dd/mm/yyyy"""
        if date is None:
            return ""
        try:
            # Para fechas tipo LocalDateTime
            if hasattr(date, 'getDayOfMonth'):
                day = str(date.getDayOfMonth()).zfill(2)
                month = str(date.getMonthValue()).zfill(2)
                year = date.getYear()
                return f"{day}/{month}/{year}"
            # Para fechas tipo Date (versiones antiguas de MPXJ)
            elif hasattr(date, 'getTime'):
                python_date = datetime.fromtimestamp(date.getTime() / 1000)
                return python_date.strftime("%d/%m/%Y")
            else:
                return str(date)
        except Exception as e:
            print(f"Error al formatear fecha: {str(e)}")
            return str(date)

    def select_file(self):
        file_dialog = QFileDialog(self)
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Seleccionar archivo MPP",
            "",
            "Archivos de Project (*.mpp)"
        )

        if file_path:
            self.load_project_data(file_path)

    def load_project_data(self, file_path):
        try:
            from net.sf.mpxj.reader import UniversalProjectReader

            reader = UniversalProjectReader()
            project = reader.read(file_path)
            tasks = list(project.getTasks())

            self.table.setRowCount(len(tasks))

            for row, task in enumerate(tasks):
                if task.getID() is None:
                    continue

                # ID
                self.table.setItem(row, 0, QTableWidgetItem(str(task.getID())))

                # Nivel jerárquico
                outline_number = self.format_outline_number(task)
                if outline_number:
                    level_item = QTableWidgetItem(outline_number)
                    level_item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, 1, level_item)

                # Nombre de tarea con indentación
                if task.getName() is not None:
                    indent = "    " * (task.getOutlineLevel() - 1)
                    self.table.setItem(row, 2, QTableWidgetItem(f"{indent}{task.getName()}"))

                # Fechas
                self.table.setItem(row, 3, QTableWidgetItem(self.format_date(task.getStart())))
                self.table.setItem(row, 4, QTableWidgetItem(self.format_date(task.getFinish())))

                # Archivo fuente
                self.table.setItem(row, 5, QTableWidgetItem(file_path))

            self.table.resizeColumnsToContents()

        except Exception as e:
            print(f"Error al cargar el archivo: {str(e)}")

    def closeEvent(self, event):
        jpype.shutdownJVM()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = ProjectManagerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
