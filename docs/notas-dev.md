# Notas de desarrollo

Apuntes sueltos movidos desde [ROADMAP.md](../ROADMAP.md).

## Instalación manual de dependencias (pip)

```sh
pip install --upgrade pip
pip install pdfplumber
pip install PySide6
pip install workalendar
pip install mpxj
pip install JPype1
pip install pycryptodome
pip install PyPDF2
pip install openpyxl
pip install pandas
pip install pywin32  # Solo Windows
```

## Paletas de colores

- https://paletadecolores.online/oscuros/
- https://colorhunt.co/
- https://colorhunt.co/palette/f3efe043424222222222a39f

## Apuntes de color (Qt)

```python
self.setStyleSheet("background-color: rgb("

task.color = name_item.data(Qt.UserRole) or QColor(119, 41, 83)
Color(34, 163, 159)

# 72 en hexadecimal = 114 en decimal
# ab en hexadecimal = 171 en decimal
# e6 en hexadecimal = 230 en decimal

self.color = color or QColor("#72abe6")
self.color = color or QColor(114, 171, 230)

color = QColor(119, 33, 111)
# O también
color = QColor("#77216F")
```
