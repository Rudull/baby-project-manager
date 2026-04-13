import sys
import math
from PySide6.QtWidgets import QApplication, QTableView, QVBoxLayout, QWidget, QScrollBar
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt

app = QApplication(sys.argv)
w = QWidget()
l = QVBoxLayout(w)
tv = QTableView()
tv.verticalHeader().setDefaultSectionSize(25)
tv.verticalHeader().setMinimumSectionSize(25)
tv.horizontalHeader().setFixedHeight(30)
model = QStandardItemModel(50, 1)
for i in range(50): model.setItem(i, 0, QStandardItem(f"Item {i}"))
tv.setModel(model)
l.addWidget(tv)

def on_scroll(val):
    print(f"Scrollbar value: {val}, verticalOffset(): {tv.verticalOffset()}, val*25: {val*25}")

tv.verticalScrollBar().valueChanged.connect(on_scroll)
w.resize(200, 260)
w.show()
tv.verticalScrollBar().setValue(39)
# Try simulating what the app does
