## Road Map

1. Cuaando se selecciona una tarea que tiene hipervinculos, se pierde el formato de y dejan de fuecionar
2. Las notas deberias podersne copiar facilmente a una barra de tareas diferente
3. Implementar filtro al diagrama de Gantt
4. Una tarea deberia poderse convestir en subtarea
5. Colocar posibilidad de una fila adicional que permita ingrezar otro campo como nombre del responsable
6. fecha inicio y fin de una tarea, cuando tiene subtareas debe ser la primer fecha de inicio de las subtareas, y la ultima fecha final de las subtareas
7. Implementar que la tarea padre sea la superoposicion de las subtareas
8. Implementar dias de escepsion
9. Implementar forma de identificar el archivo *.bpm de tareas sobre el que se esta trabajando (Pestañas)
10. El scroll debe poder fuecionar sobre el diagrama de Gantt
11. Implementar rodar tarea
12. Implementar animacion cuando se cambia de periodo con la rueda del mouse
13. Dibujar linea de separacion de acuerdo al periodo selecciodo (Extender lineas vertivales da año al Gantt)
14. Fijar el desplazamento de el diagrama de Gantt con el derplazamiento de la lista de tareas (Solo falta un pequeño ajurte cundo se baja al maximo)
15. Implementar arrastrar y soltar
16. Implementar que el panel de la lista de tareas se pueda contraer a la izquierda y el diagram de Gantt se reescale al espacio disponible
17. Implementar CTR+Z y CTR+Y
19. Dividir baby.py en partes mas pequeñas

QTableWidget por QAbstractTableModel junto con QTableView


↳

0. https://paletadecolores.online/oscuros/
0. https://colorhunt.co/
0. https://colorhunt.co/palette/f3efe043424222222222a39f

self.setStyleSheet("background-color: rgb(

task.color = name_item.data(Qt.UserRole) or QColor(119,41,83)
Color(34,163,159)
- 72 en hexadecimal = 114 en decimal
- ab en hexadecimal = 171 en decimal
- e6 en hexadecimal = 230 en decimal
self.color = color or QColor("#72abe6")
self.color = color or QColor(114, 171, 230)

color = QColor(119, 33, 111)
# O también
color = QColor("#77216F")

pip install --upgrade pip
pip install pdfplumber
pip install PySide6
pip install workalendar
pip install mpxj
pip install JPype1
pip install pycryptodome
pip install PyPDF2

Estructura de Archivos Propuesta:

    main.py (Programa principal)
    models.py (Contiene las clases Task y TaskTableModel)
    delegates.py (Contiene las clases delegadas personalizadas)
    gantt.py (Contiene las clases relacionadas con el diagrama de Gantt)
    task_table_widget.py (Contiene la clase TaskTableWidget)
    floating_menu.py (Contiene la clase FloatingTaskMenu)
    hyperlink_text_edit.py (Contiene la clase HyperlinkTextEdit)
    main_window.py


    Analizando el código proporcionado, sugiero dividirlo en los siguientes módulos principales:

    1. **Módulo de Modelos (models.py)**
       - Clase Task (modelo de datos para tareas)
       - Clase TaskTableModel (modelo para la tabla de tareas)

    2. **Módulo de Delegados (delegates.py)**
       - LineEditDelegate
       - DateEditDelegate
       - SpinBoxDelegate
       - StateButtonDelegate

    3. **Módulo de Vistas Gantt (gantt_views.py)**
       - GanttHeaderView
       - GanttChart
       - FloatingTaskMenu
       - GanttWidget

    4. **Módulo de Vistas de Tabla (table_views.py)**
       - TaskTableWidget

    5. **Módulo de Ventana Principal (main_window.py)**
       - MainWindow

    6. **Módulo de Utilidades (utils.py)**
       - Funciones helper para cálculos de fechas
       - Funciones para manejo de archivos
       - Constantes compartidas

    7. **Módulo de Hipervínculos (hipervinculo.py)** - Ya existente
       - HyperlinkTextEdit
       - NotesApp

    8. **Módulo Principal (main.py)**
       - Punto de entrada de la aplicación
       - Configuración inicial
