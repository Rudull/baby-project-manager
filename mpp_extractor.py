#mpp_extractor.py
#6
import sys
import os
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

        # Ya no necesitamos iniciar la JVM aquí

    # Eliminamos el método start_jvm
    # def start_jvm(self):
    #     pass

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
                    level_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
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
        # Ya no cerramos la JVM aquí
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = ProjectManagerWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
