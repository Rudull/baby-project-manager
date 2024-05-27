import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
QDateEdit, QLineEdit, QMenu, QSizePolicy, QScrollArea,
QLabel, QFrame, QSpacerItem)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QIntValidator, QPainter, QColor
from datetime import date, timedelta
from workalendar.america import Colombia

class ProgressBarCanvas(QWidget):
    def __init__(self, start_date, end_date, min_date, max_date, *args, **kwargs):
        super(ProgressBarCanvas, self).__init__(*args, **kwargs)
        self.start_date = start_date
        self.end_date = end_date
        self.min_date = min_date
        self.max_date = max_date

    def setDates(self, start_date, end_date, min_date, max_date):
        self.start_date = start_date
        self.end_date = end_date
        self.min_date = min_date
        self.max_date = max_date
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.start_date or not self.end_date or not self.min_date or not self.max_date:
            return
        painter = QPainter(self)
        total_days = (self.max_date - self.min_date).days + 1
        start_offset_days = (self.start_date - self.min_date).days
        end_offset_days = (self.end_date - self.min_date).days
        start_x = int((start_offset_days / total_days) * self.width())
        end_x = int((end_offset_days / total_days) * self.width())
        painter.setBrush(QColor(100, 200, 100))  # Green color
        painter.setPen(Qt.NoPen)
        painter.drawRect(start_x, 0, end_x - start_x, self.height())

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.min_date = QDate.currentDate().toPyDate()
        self.max_date = (QDate.currentDate().addYears(1)).toPyDate()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Baby Project Manager")
        self.setGeometry(0, 0, 1920, 1080)

        # Layout principal
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.setLayout(self.mainLayout)

        self.headerAndContentLayout = QVBoxLayout()
        self.mainLayout.addLayout(self.headerAndContentLayout)

        # Títulos de las columnas
        self.title_layout = QHBoxLayout()
        self.addTitleLabels(self.title_layout)
        self.headerAndContentLayout.addLayout(self.title_layout)

        # Área de desplazamiento horizontal
        self.horizontalScrollArea = QScrollArea(self)
        self.horizontalScrollArea.setWidgetResizable(True)
        self.horizontalScrollContent = QWidget()
        self.horizontalScrollLayout = QVBoxLayout(self.horizontalScrollContent)
        self.horizontalScrollContent.setLayout(self.horizontalScrollLayout)
        self.horizontalScrollArea.setWidget(self.horizontalScrollContent)
        self.headerAndContentLayout.addWidget(self.horizontalScrollArea)

        # Iniciar el layout de la línea de tiempo
        self.timelineLayout = QHBoxLayout()
        self.timelineFrame = QFrame()
        self.timelineContent = QHBoxLayout(self.timelineFrame)
        self.horizontalScrollLayout.addWidget(self.timelineFrame)

        # Área de desplazamiento vertical
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollContent = QWidget()
        self.scrollLayout = QVBoxLayout(self.scrollContent)
        self.scrollLayout.setContentsMargins(5, 20, 0, 5)
        self.scrollLayout.setSpacing(5)
        self.scrollContent.setLayout(self.scrollLayout)
        self.scrollContent.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.scrollArea.setWidget(self.scrollContent)
        self.horizontalScrollLayout.addWidget(self.scrollArea)

        # Contenedor de filas
        self.rowsContainer = QVBoxLayout()
        self.scrollLayout.addLayout(self.rowsContainer)

        # Botón para agregar filas
        self.addRowButton = QPushButton('+')
        self.addRowButton.setFixedSize(460, 30)
        self.addRowButton.setStyleSheet("background-color: lightgray; font-size: 18px;")
        self.addRowButton.clicked.connect(lambda: self.addRow())
        button_layout = QVBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.addRowButton)
        self.scrollLayout.addLayout(button_layout)

        # Agregar una fila por defecto al iniciar
        self.fixedRow = QHBoxLayout()
        self.populateRow(self.fixedRow)
        self.rowsContainer.addLayout(self.fixedRow)

        # Actualizar la línea de tiempo
        self.updateTimeline()

    def addTitleLabels(self, layout):
        labels = ["", "Nombre", "Fecha Inicial", "Fecha Final", "Días", "(%)"]
        widths = [20, 144, 108, 108, 39, 33]
        for label, width in zip(labels, widths):
            lbl = QLabel(label)
            lbl.setFixedWidth(width)
            layout.addWidget(lbl)
        self.timelineLayout = QHBoxLayout()
        self.timelineLayout.addStretch()
        layout.addLayout(self.timelineLayout)

    def addRow(self, data=None):
        row_layout = QHBoxLayout()
        self.populateRow(row_layout, data)
        self.rowsContainer.addLayout(row_layout)
        self.updateTimeline()

    def populateRow(self, row_layout, data=None):
        cell_height = 24
        reduced_height = int(cell_height * 0.8)
        date_width = 98
        days_width = 39
        dedication_width = 30
        circle_button = QPushButton()
        circle_button.setFixedSize(20, reduced_height)
        circle_button.setStyleSheet("background-color: blue;")
        circle_button.setContextMenuPolicy(Qt.CustomContextMenu)
        circle_button.customContextMenuRequested.connect(self.showContextMenu)
        row_layout.addWidget(circle_button)
        name_entry = QLineEdit()
        name_entry.setFixedSize(144, reduced_height)
        name_entry.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        if data:
            name_entry.setText(data["name"])
        row_layout.addWidget(name_entry)
        start_date_entry = QDateEdit()
        start_date_entry.setCalendarPopup(True)
        start_date_entry.setDisplayFormat("dd/MM/yyyy")
        start_date_entry.setDate(data["start_date"] if data else QDate.currentDate())
        start_date_entry.setFixedSize(date_width, reduced_height)
        start_date_entry.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row_layout.addWidget(start_date_entry)
        end_date_entry = QDateEdit()
        end_date_entry.setCalendarPopup(True)
        end_date_entry.setDisplayFormat("dd/MM/yyyy")
        end_date_entry.setDate(data["end_date"] if data else QDate.currentDate())
        end_date_entry.setFixedSize(date_width, reduced_height)
        end_date_entry.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row_layout.addWidget(end_date_entry)
        days_entry = QLineEdit()
        days_entry.setFixedSize(days_width, reduced_height)
        days_entry.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        if data:
            days_entry.setText(data["days"])
        row_layout.addWidget(days_entry)
        dedication_entry = QLineEdit()
        dedication_entry.setFixedSize(dedication_width, reduced_height)
        dedication_entry.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        dedication_entry.setText("100")
        dedication_entry.setValidator(QIntValidator(0, 100))
        if data:
            dedication_entry.setText(data["dedication"])
        row_layout.addWidget(dedication_entry)
        canvas = ProgressBarCanvas(
            start_date_entry.date().toPyDate(), end_date_entry.date().toPyDate(),
            self.min_date, self.max_date)
        canvas.setFixedHeight(reduced_height)
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_layout.addWidget(canvas)
        row_layout.addStretch()
        start_date_entry.dateChanged.connect(lambda: self.validateAndCalculateDays(start_date_entry, end_date_entry, days_entry))
        end_date_entry.dateChanged.connect(lambda: self.validateAndCalculateDays(start_date_entry, end_date_entry, days_entry))
        days_entry.editingFinished.connect(lambda: self.calculateEndDateIfChanged(start_date_entry, days_entry, end_date_entry))
        start_date_entry.dateChanged.connect(self.updateTimeline)
        end_date_entry.dateChanged.connect(self.updateTimeline)
        days_entry.editingFinished.connect(self.updateTimeline)

    def validateAndCalculateDays(self, start_entry, end_entry, days_entry):
        cal = Colombia()
        start_date = start_entry.date().toPyDate()
        end_date = end_entry.date().toPyDate()
        business_days = sum(1 for day in (start_date + timedelta(n) for n in range((end_date - start_date).days + 1)) if cal.is_working_day(day))
        days_entry.setText(str(business_days))

    def calculateEndDateIfChanged(self, start_entry, days_entry, end_entry):
        if not days_entry.text().isdigit():
            return
        cal = Colombia()
        start_date = start_entry.date().toPyDate()
        days = int(days_entry.text())
        end_date = start_date
        if cal.is_working_day(start_date):
            days -= 1
        while days > 0:
            end_date += timedelta(1)
            if cal.is_working_day(end_date):
                days -= 1
        end_entry.setDate(end_date)

    def showContextMenu(self, position):
        sender = self.sender()
        context_menu = QMenu()
        context_menu.addAction("Eliminar", lambda: self.deleteRow(sender))
        context_menu.addAction("Mover arriba", lambda: self.moveRowUp(sender))
        context_menu.addAction("Mover abajo", lambda: self.moveRowDown(sender))
        context_menu.addAction("Insertar fila", lambda: self.insertRow(sender))
        context_menu.addAction("Duplicar fila", lambda: self.duplicateRow(sender))
        context_menu.exec_(sender.mapToGlobal(position))

    def deleteRow(self, sender):
        for i in reversed(range(self.rowsContainer.count())):
            row_layout = self.rowsContainer.itemAt(i).layout()
            if row_layout and sender in [row_layout.itemAt(j).widget() for j in range(row_layout.count())]:
                self.clearLayout(row_layout)
                self.rowsContainer.removeItem(row_layout)
                break
        self.updateTimeline()

    def moveRowUp(self, sender):
        for i in range(1, self.rowsContainer.count()):
            row_layout = self.rowsContainer.itemAt(i).layout()
            if row_layout and sender in [row_layout.itemAt(j).widget() for j in range(row_layout.count())]:
                previous_row_layout = self.rowsContainer.itemAt(i - 1).layout()
                self.swapRowData(row_layout, previous_row_layout)
                break
        self.updateTimeline()

    def moveRowDown(self, sender):
        for i in range(self.rowsContainer.count() - 1):
            row_layout = self.rowsContainer.itemAt(i).layout()
            if row_layout and sender in [row_layout.itemAt(j).widget() for j in range(row_layout.count())]:
                next_row_layout = self.rowsContainer.itemAt(i + 1).layout()
                self.swapRowData(row_layout, next_row_layout)
                break
        self.updateTimeline()

    def insertRow(self, sender):
        for i in range(self.rowsContainer.count()):
            row_layout = self.rowsContainer.itemAt(i).layout()
            if row_layout and sender in [row_layout.itemAt(j).widget() for j in range(row_layout.count())]:
                new_row_layout = QHBoxLayout()
                self.populateRow(new_row_layout)
                self.rowsContainer.insertLayout(i + 1, new_row_layout)
                break
        self.updateTimeline()

    def duplicateRow(self, sender):
        for i in range(self.rowsContainer.count()):
            row_layout = self.rowsContainer.itemAt(i).layout()
            if row_layout and sender in [row_layout.itemAt(j).widget() for j in range(row_layout.count())]:
                data = self.getRowData(row_layout)
                new_row_layout = QHBoxLayout()
                self.populateRow(new_row_layout, data)
                self.rowsContainer.insertLayout(i + 1, new_row_layout)
                break
        self.updateTimeline()

    def getRowData(self, row_layout):
        data = {
            "name": row_layout.itemAt(1).widget().text(),
            "start_date": row_layout.itemAt(2).widget().date(),
            "end_date": row_layout.itemAt(3).widget().date(),
            "days": row_layout.itemAt(4).widget().text(),
            "dedication": row_layout.itemAt(5).widget().text(),
        }
        return data

    def swapRowData(self, row_layout1, row_layout2):
        data1 = self.getRowData(row_layout1)
        data2 = self.getRowData(row_layout2)
        self.setRowData(row_layout1, data2)
        self.setRowData(row_layout2, data1)
        self.updateTimeline()

    def setRowData(self, row_layout, data):
        row_layout.itemAt(1).widget().setText(data["name"])
        row_layout.itemAt(2).widget().setDate(data["start_date"])
        row_layout.itemAt(3).widget().setDate(data["end_date"])
        row_layout.itemAt(4).widget().setText(data["days"])
        row_layout.itemAt(5).widget().setText(data["dedication"])
        self.updateTimeline()

    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget() is not None:
                    child.widget().deleteLater()

    def updateTimeline(self):
        self.clearLayout(self.timelineContent)
        self.min_date, self.max_date = self.getMinMaxDates()
        if not self.min_date or not self.max_date:
            return
        pre_labels_width = 20 + 144 + 108 + 108 + 39 + 33
        spacer = QSpacerItem(pre_labels_width, 0, QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.timelineContent.addSpacerItem(spacer)
        current_date = self.min_date
        while current_date <= self.max_date:
            month_label = QLabel(current_date.strftime('%B %Y'))
            month_label.setFixedWidth(150)
            self.timelineContent.addWidget(month_label)
            current_date += timedelta(days=31)
            current_date = current_date.replace(day=1)
        for i in range(self.rowsContainer.count()):
            row_layout = self.rowsContainer.itemAt(i).layout()
            if row_layout:
                canvas = row_layout.itemAt(6).widget()
                start_date = row_layout.itemAt(2).widget().date().toPyDate()
                end_date = row_layout.itemAt(3).widget().date().toPyDate()
                canvas.setDates(start_date, end_date, self.min_date, self.max_date)

    def getMinMaxDates(self):
        min_date, max_date = None, None
        for i in range(self.rowsContainer.count()):
            row_layout = self.rowsContainer.itemAt(i).layout()
            start_date = row_layout.itemAt(2).widget().date().toPyDate()
            end_date = row_layout.itemAt(3).widget().date().toPyDate()
            if min_date is None or start_date < min_date:
                min_date = start_date
            if max_date is None or end_date > max_date:
                max_date = end_date
        if min_date and max_date:
            if (max_date - min_date).days < 365:
                max_date = min_date + timedelta(days=365)
            return min_date.replace(day=1), max_date.replace(day=1)
        return None, None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())