## Road Map

0*. Oganizar automaticamente por fecha final o fecha de inicio y orden alfabetico (usar encabezado de table)

1. Implementar forma de identificar el archivo *.bpm de tareas sobre el que se esta trabajando
2. Implementar division de semanas
3. Implementar subtareas
4. Implementar importasion de archivos *.ppm
5. Implementar rodar tarea
6. Sombrear tarea seleccionada
7. Implementar animacion cuando se cambia de periodo con la rueda del mouse
8. Dibujar linea de separacion de acuerdo al periodo selecciodo
9. Fijar el desplazamento de el diagrama de Gantt con el derplazamiento de la lista de tareas
10. Extender lineas vertivales da año al Gantt
11. Implementar arrastrar y soltar
12. Implementar que el panel de la lista de tareas se pueda contraer a la izquierda y el diagram de Gantt se reescale al espacio disponible

10. Revisar def scrollTo(self, value):


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








Cuando el usuario haga clic derecho sobre una tarea padre (haciendo clic derecho sobre la columna 0 en la celda donde está el botón de cada fila
), debe alternar entre colapsar las tareas hijo y expandir las tareas hijo.
Dame las instrucciones detalladas con el código que se debe modificar y el que se debe agregar y donde se debe agregar.


Para implementar la funcionalidad de colapsar y expandir subtareas al hacer clic derecho en una tarea padre, necesitaremos hacer varios cambios en el código existente. Aquí están las instrucciones detalladas:

1. Modificar la clase `Task`:

Añade un nuevo atributo `collapsed` a la clase `Task`:

```python
class Task:
    def __init__(self, name, start_date, end_date, duration, dedication, color=None, notes=""):
        # ... (código existente) ...
        self.collapsed = False  # Nuevo atributo
```

2. Modificar la clase `StateButton`:

Añade un nuevo método para manejar el clic derecho:

```python
class StateButton(QPushButton):
    def __init__(self, parent=None):
        # ... (código existente) ...
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, position):
        task = self.parent().item(self.parent().row(self), 1).data(Qt.UserRole + 1)
        if task.subtasks:
            menu = QMenu(self)
            action = menu.addAction("Colapsar" if not task.collapsed else "Expandir")
            action.triggered.connect(self.toggle_collapse)
            menu.exec_(self.mapToGlobal(position))

    def toggle_collapse(self):
        task = self.parent().item(self.parent().row(self), 1).data(Qt.UserRole + 1)
        task.collapsed = not task.collapsed
        self.parent().parent().parent().update_task_visibility()
```

3. Modificar la clase `TaskTableWidget`:

Añade un nuevo método para actualizar la visibilidad de las tareas:

```python
class TaskTableWidget(QWidget):
    def __init__(self, parent=None):
        # ... (código existente) ...

    def update_task_visibility(self):
        for row in range(self.task_table.rowCount()):
            item = self.task_table.item(row, 1)
            if item:
                task = item.data(Qt.UserRole + 1)
                visible = True
                parent = task.parent
                while parent:
                    if parent.collapsed:
                        visible = False
                        break
                    parent = parent.parent
                self.task_table.setRowHidden(row, not visible)
        self.main_window.update_gantt_chart()
```

4. Modificar el método `add_task_to_table` en `TaskTableWidget`:

Modifica la creación del `StateButton`:

```python
def add_task_to_table(self, task_data, editable=False, row=None):
    # ... (código existente) ...
    state_button = StateButton()
    state_button.setParent(self.task_table)  # Establece el padre del botón
    # ... (resto del código existente) ...
```

5. Modificar la clase `MainWindow`:

Añade un nuevo método para actualizar la visibilidad de las tareas en el gráfico de Gantt:

```python
class MainWindow(QMainWindow):
    def __init__(self):
        # ... (código existente) ...

    def update_gantt_chart(self):
        self.tasks = []
        for row in range(self.task_table_widget.task_table.rowCount()):
            if not self.task_table_widget.task_table.isRowHidden(row):
                name_item = self.task_table_widget.task_table.item(row, 1)
                task = name_item.data(Qt.UserRole + 1)
                if task:
                    # ... (resto del código existente para actualizar las tareas) ...
                    self.tasks.append(task)

        # ... (resto del código existente para actualizar el gráfico de Gantt) ...
```

6. Conectar la señal de actualización:

En el constructor de `MainWindow`, añade:

```python
self.task_table_widget.task_table.itemChanged.connect(self.update_gantt_chart)
```

Estos cambios permitirán colapsar y expandir subtareas al hacer clic derecho en el botón de estado de una tarea padre. Cuando se colapsa una tarea, todas sus subtareas se ocultarán tanto en la tabla como en el gráfico de Gantt. Al expandirla, las subtareas volverán a ser visibles.

Recuerda manejar correctamente los casos en que las tareas padre estén colapsadas al cargar o guardar proyectos, para mantener el estado de colapso/expansión entre sesiones si es necesario.














python3 baby.py
Traceback (most recent call last):
  File "/mnt/007358280B6294C8/1. Rafael/3.Proyectos_de_Software/baby-project-manager/baby.py", line 1030, in show_context_menu
    self.add_subtask()
  File "/mnt/007358280B6294C8/1. Rafael/3.Proyectos_de_Software/baby-project-manager/baby.py", line 1099, in add_subtask
    state_button.set_is_subtask(True)
AttributeError: 'StateButton' object has no attribute 'set_is_subtask'. Did you mean: 'set_has_subtasks'?
Traceback (most recent call last):
  File "/mnt/007358280B6294C8/1. Rafael/3.Proyectos_de_Software/baby-project-manager/baby.py", line 1030, in show_context_menu
    self.add_subtask()
  File "/mnt/007358280B6294C8/1. Rafael/3.Proyectos_de_Software/baby-project-manager/baby.py", line 1099, in add_subtask
    state_button.set_is_subtask(True)
AttributeError: 'StateButton' object has no attribute 'set_is_subtask'. Did you mean: 'set_has_subtasks'?
Archivo cargado desde: /mnt/007358280B6294C8/1. Rafael/3.Proyectos_de_Software/baby-project-manager/proyectos_prueba.bpm
Acción seleccionada: Abrir
Traceback (most recent call last):
  File "/mnt/007358280B6294C8/1. Rafael/3.Proyectos_de_Software/baby-project-manager/baby.py", line 1030, in show_context_menu
    self.add_subtask()
  File "/mnt/007358280B6294C8/1. Rafael/3.Proyectos_de_Software/baby-project-manager/baby.py", line 1099, in add_subtask
    state_button.set_is_subtask(True)
AttributeError: 'StateButton' object has no attribute 'set_is_subtask'. Did you mean: 'set_has_subtasks'?
Traceback (most recent call last):
  File "/mnt/007358280B6294C8/1. Rafael/3.Proyectos_de_Software/baby-project-manager/baby.py", line 1030, in show_context_menu
    self.add_subtask()
  File "/mnt/007358280B6294C8/1. Rafael/3.Proyectos_de_Software/baby-project-manager/baby.py", line 1099, in add_subtask
    state_button.set_is_subtask(True)
AttributeError: 'StateButton' object has no attribute 'set_is_subtask'. Did you mean: 'set_has_subtasks'?
