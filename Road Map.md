a## Road Map

1. Cundo se abre otro proyecto no se pregunta si se desean guardas los cambios
10. colocar menu de tareas a barras de Gantt
1. Mostrar 1 semana, 1 mes o 1 año en el diagrama de Gantt
2. Dibujar linea de separacion de acuerdo al periodo selecciodo
4. Fijar el desplazamento de el diagrama de Gantt con el derplazamiento de la lista de tareas
5. Oganizar automaticamente por fecha final o fecha de inicio y orden alfabetico (usar encabezado de table)
7. Sombrear tarea seleccionada
11. Extender lineas vertivales da año al Gantt
13. Reineciar color por defecto Gantt
14. Implementar Ctr+S
15. Reescalar encabezado Gantt
16. Mostrar dias restantes en ventana de informacion de barras Gantt
18. Implementar arrastrar y soltar
20.


- 72 en hexadecimal = 114 en decimal
- ab en hexadecimal = 171 en decimal
- e6 en hexadecimal = 230 en decimal
self.color = color or QColor("#72abe6")
self.color = color or QColor(114, 171, 230)




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
