## Road Map

1. Mostrar 1 semana, 1 mes o 1 año en el diagrama de Gantt
2. Dibujar linea de separacion de acuerdo al periodo selecciodo
4. Fijar el desplazamento de el diagrama de Gantt con el derplazamiento de la lista de tareas
5. Oganizar automaticamente por fecha final o fecha de inicio y orden alfabetico (usar encabezado de table)
6. Alinear el Gantt con las tareas
7. Sombrear tarea seleccionada
8. Cambio de color tarea
9. Agregar nota en tarea de Gantt
10. colocar menu de tareas a barras de Gantt
11. Extender lineas vertivales da año al Gantt
12. Ajustar boton cambia de tamaño cuando se mueve arriba o abajo
13. Reineciar color por defecto Gantt
14. Implementar Ctr+S
15. Reescalar encabezado Gantt
16. Mostrar dias restantes en ventana de informacion de barras Gantt
17. Las tareas copiadas despues des ser colocadas en modo no edicion, si se colocan de nuevo en modo edicion, no permiten la edicion aunque si parpadea en rojo
18. Implementar arrastrar y soltar
19. Cuando el programa se ejecuta el diagrama de Gantt no ocupat todo el espacio poreble
20. Cuando la tarea se mueve abajo esta aparece en azul que indeca la no edicion pero realmente esta en modo edicion 




"encabezado" o "header"


¿Podemos establecer la convención de la aplicación con archivos de texto plano y usar nuestro propio formato inventado *.bpm para guardar y recuperar los datos de las tareas?
Dame las instrucciones detalladas con el código que se debe modificar y el que se debe agregar y donde se debe agregar.

Claro, podemos implementar un formato personalizado *.bpm (Baby Project Manager) para guardar y recuperar los datos de las tareas. Vamos a definir un formato simple que pueda manejar tareas anidadas y toda la información necesaria. Aquí están los pasos detallados:

1. Definir el formato *.bpm:
   ```
   [TASK]
   NAME: Nombre de la tarea
   START: DD/MM/YYYY
   END: DD/MM/YYYY
   DURATION: X
   DEDICATION: Y%
   LEVEL: Z
   [/TASK]
   ```
   Donde LEVEL indica el nivel de anidación (0 para tareas principales, 1 para subtareas, etc.)

2. Modificar la clase `Task` para incluir subtareas y nivel:

```python
class Task:
    def __init__(self, name, start_date, end_date, duration, dedication, level=0):
        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.duration = duration
        self.dedication = dedication
        self.level = level
        self.subtasks = []
```

3. Actualizar el método `save_tasks_to_file` en `TaskTableWidget`:

```python
def save_tasks_to_file(self, file_path):
    try:
        with open(file_path, 'w') as file:
            for row in range(self.task_table.rowCount()):
                task_name = self.task_table.item(row, 1).text()
                start_date = self.task_table.cellWidget(row, 2).date().toString("dd/MM/yyyy")
                end_date = self.task_table.cellWidget(row, 3).date().toString("dd/MM/yyyy")
                duration = self.task_table.cellWidget(row, 4).text()
                dedication = self.task_table.cellWidget(row, 5).text()
                level = self.get_task_level(row)  # Nuevo método para obtener el nivel

                file.write("[TASK]\n")
                file.write(f"NAME: {task_name}\n")
                file.write(f"START: {start_date}\n")
                file.write(f"END: {end_date}\n")
                file.write(f"DURATION: {duration}\n")
                file.write(f"DEDICATION: {dedication}\n")
                file.write(f"LEVEL: {level}\n")
                file.write("[/TASK]\n\n")

        self.current_file_path = file_path
        self.main_window.unsaved_changes = False
        print(f"Archivo guardado en: {file_path}")
    except Exception as e:
        print(f"Error al guardar el archivo: {e}")

def get_task_level(self, row):
    # Implementa la lógica para determinar el nivel de la tarea
    # Por ahora, asumiremos que todas las tareas son de nivel 0
    return 0
```

4. Actualizar el método `load_tasks_from_file` en `TaskTableWidget`:

```python
def load_tasks_from_file(self, file_path):
    try:
        self.task_table.setRowCount(0)  # Limpia la tabla actual
        with open(file_path, 'r') as file:
            task_data = {}
            for line in file:
                line = line.strip()
                if line == "[TASK]":
                    task_data = {}
                elif line == "[/TASK]":
                    self.add_task_to_table(task_data)
                elif ":" in line:
                    key, value = line.split(":", 1)
                    task_data[key.strip()] = value.strip()

        self.current_file_path = file_path
        self.main_window.unsaved_changes = False
        self.main_window.update_gantt_chart()
        print(f"Archivo cargado desde: {file_path}")
    except Exception as e:
        print(f"Error al cargar el archivo: {e}")

def add_task_to_table(self, task_data):
    row_position = self.task_table.rowCount()
    self.task_table.insertRow(row_position)

    # Botón de estado
    state_button = StateButton()
    self.task_table.setCellWidget(row_position, 0, state_button)

    # Nombre de la tarea
    self.task_table.setItem(row_position, 1, QTableWidgetItem(task_data['NAME']))

    # Fecha inicial
    start_date = QDateEdit()
    start_date.setDate(QDate.fromString(task_data['START'], "dd/MM/yyyy"))
    start_date.setCalendarPopup(True)
    start_date.setDisplayFormat("dd/MM/yyyy")
    self.task_table.setCellWidget(row_position, 2, start_date)

    # Fecha final
    end_date = QDateEdit()
    end_date.setDate(QDate.fromString(task_data['END'], "dd/MM/yyyy"))
    end_date.setCalendarPopup(True)
    end_date.setDisplayFormat("dd/MM/yyyy")
    self.task_table.setCellWidget(row_position, 3, end_date)

    # Duración
    duration = QLineEdit(task_data['DURATION'])
    self.task_table.setCellWidget(row_position, 4, duration)

    # Dedicación
    dedication = QLineEdit(task_data['DEDICATION'])
    self.task_table.setCellWidget(row_position, 5, dedication)

    # Conectar señales
    start_date.dateChanged.connect(lambda: self.main_window.validateAndCalculateDays(start_date, end_date, duration))
    end_date.dateChanged.connect(lambda: self.main_window.validateAndCalculateDays(start_date, end_date, duration))
    duration.textChanged.connect(lambda: self.main_window.calculateEndDateIfChanged(start_date, duration, end_date))

    self.task_table.setRowHeight(row_position, self.main_window.ROW_HEIGHT)

    # Aplicar indentación basada en el nivel
    level = int(task_data.get('LEVEL', 0))
    self.apply_task_indentation(row_position, level)

def apply_task_indentation(self, row, level):
    # Implementa la lógica para aplicar la indentación visual
    # Por ejemplo, puedes ajustar el margen izquierdo del QTableWidgetItem
    indent = level * 20  # 20 píxeles por nivel
    item = self.task_table.item(row, 1)
    if item:
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        item.setText(' ' * indent + item.text())
```

5. Actualizar los métodos de apertura y guardado de archivos para usar la extensión .bpm:

```python
def save_file_as(self):
    file_path, _ = QFileDialog.getSaveFileName(
        self,
        "Guardar como",
        "",
        "Archivos BPM (*.bpm);;Todos los archivos (*)"
    )
    if file_path:
        if not file_path.endswith('.bpm'):
            file_path += '.bpm'
        self.current_file_path = file_path
        self.save_tasks_to_file(file_path)

def open_file(self):
    file_path, _ = QFileDialog.getOpenFileName(
        self,
        "Abrir archivo",
        "",
        "Archivos BPM (*.bpm);;Todos los archivos (*)"
    )
    if file_path:
        self.load_tasks_from_file(file_path)
```

6. Actualizar el método `update_gantt_chart` en `MainWindow` para manejar los niveles de tarea:

```python
def update_gantt_chart(self):
    self.tasks = []
    for row in range(self.task_table_widget.task_table.rowCount()):
        name = self.task_table_widget.task_table.item(row, 1).text()
        start_date = self.task_table_widget.task_table.cellWidget(row, 2).date().toString("dd/MM/yyyy")
        end_date = self.task_table_widget.task_table.cellWidget(row, 3).date().toString("dd/MM/yyyy")
        duration = self.task_table_widget.task_table.cellWidget(row, 4).text()
        dedication = self.task_table_widget.task_table.cellWidget(row, 5).text()
        level = self.task_table_widget.get_task_level(row)
        task = Task(name, start_date, end_date, duration, dedication, level)
        self.tasks.append(task)

    # Actualizar la lógica del gráfico de Gantt para manejar niveles de tarea
    # ...
```

Estos cambios implementan un formato personalizado .bpm para guardar y cargar tareas, incluyendo información sobre su nivel de anidación. La interfaz de usuario ahora mostrará las tareas con indentación basada en su nivel.

Para completar la implementación, necesitarás:

1. Implementar la lógica para crear y manejar subtareas en la interfaz de usuario.
2. Actualizar el gráfico de Gantt para visualizar correctamente las tareas anidadas.
3. Mejorar el método `get_task_level` para determinar correctamente el nivel de cada tarea basado en tu lógica de interfaz de usuario.

Este es un buen punto de partida para implementar tu formato personalizado .bpm. Puedes expandir y ajustar estas funciones según las necesidades específicas de tu aplicación.
























Implementar arrastrar y soltar tareas en un programa de administración de tareas con una interfaz gráfica en PySide6 es completamente factible. Esto se puede lograr sobreescribiendo ciertos métodos de eventos en las clases del widget correspondiente. A continuación, desglosaré los pasos para implementar esta funcionalidad en el código que compartiste:

Pseudocódigo para implementar "Arrastrar y Soltar"
Habilitar el soporte de arrastre:

En la clase TaskTableWidget:
Habilitar el evento de arrastre para las filas.
Modificar el comportamiento al presionar el ratón para iniciar el arrastre.
Definir el evento de inicio de arrastre:

mousePressEvent: Registrar qué tarea se está arrastrando (el índice de la fila).
Definir el evento de movimiento del ratón:

mouseMoveEvent: Ejecutar el arrastre gráfico mientras el ratón se mueve si se mantiene presionado el botón izquierdo del ratón.
Definir el evento de finalización de arrastre:

dropEvent: Colocar la tarea en la nueva fila seleccionada.
Actualizar la tabla de tareas y el gráfico de Gantt.
Implementación en el código
A continuación se presenta la implementación de las partes relevantes en el código para habilitar la funcionalidad de "Arrastrar y Soltar". Solo se mostrarán las secciones que necesitan ser modificadas y agregadas para esta funcionalidad.

Modificaciones en TaskTableWidget
class TaskTableWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.current_drag_index = -1  # Para establecer el índice de arrastre

        # ... (resto del constructor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.current_drag_index = self.task_table.indexAt(event.pos()).row()  # Obtener índice de la tarea

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.current_drag_index >= 0:
            mime_data = QMimeData()
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            drag.setHotSpot(event.pos() - self.task_table.viewport().pos())
            drag.exec(Qt.MoveAction)

    def dropEvent(self, event):
        if event.source() == self:
            drop_index = self.task_table.indexAt(event.pos()).row()
            if drop_index != self.current_drag_index and self.current_drag_index >= 0:
                # Mover la tarea de un índice a otro
                task_data = self.retrieve_task_data(self.current_drag_index)
                self.task_table.removeRow(self.current_drag_index)  # Eliminar tarea original
                self.task_table.insertRow(drop_index)  # Insertar en la nueva posición
                self.add_task_to_table(task_data, editable=True)  # Agregar tarea de nuevo en la nueva ubicación

                self.unsaved_changes = True
                self.main_window.update_gantt_chart()  # Actualizar el gráfico de Gantt

        event.acceptProposedAction()
    
    def retrieve_task_data(self, row):
        return {
            'NAME': self.task_table.item(row, 1).text(),
            'START': self.task_table.cellWidget(row, 2).date().toString("dd/MM/yyyy"),
            'END': self.task_table.cellWidget(row, 3).date().toString("dd/MM/yyyy"),
            'DURATION': self.task_table.cellWidget(row, 4).text(),
            'DEDICATION': self.task_table.cellWidget(row, 5).text()
        }
Explicación de los cambios:
mousePressEvent: Captura cuál fila se ha comenzado a arrastrar.
mouseMoveEvent: Si se mantiene presionado el botón del ratón, se inicia el proceso de arrastre.
dropEvent: Maneja la lógica para mover la tarea del índice de la fila arrastrada al índice de la fila donde se suelta.