#!/usr/bin/env python3
"""
Script de prueba simple para comandos específicos sin dependencias problemáticas
"""

import sys
import os
from pathlib import Path

# Agregar el directorio src al path
BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDate
from PySide6.QtGui import QColor

# Importar solo lo esencial
from models import Task, TaskTableModel
from command_system import (
    CommandManager, AddTaskCommand, DuplicateTaskCommand,
    InsertTaskCommand, AddSubtaskCommand, ChangeColorCommand,
    ResetColorsCommand
)

class SimpleMainWindow:
    """Clase simplificada que simula MainWindow para pruebas."""

    def __init__(self):
        self.model = TaskTableModel()
        self.command_manager = CommandManager()
        self.tasks = []
        self._loading_file = False

        # Crear algunas tareas de prueba
        self.setup_test_data()

    def setup_test_data(self):
        """Crea tareas de prueba básicas."""
        print("🔧 Configurando datos de prueba...")

        # Agregar 3 tareas directamente al modelo
        for i in range(3):
            task = Task(
                name=f"Tarea {i+1}",
                start_date=QDate.currentDate().toString("dd/MM/yyyy"),
                end_date=QDate.currentDate().addDays(1).toString("dd/MM/yyyy"),
                duration="1",
                dedication="40",
                color=QColor(34, 163, 159)
            )
            self.model.tasks.append(task)
            self.tasks.append(task)

        self.model.update_visible_tasks()
        print(f"✅ Creadas {len(self.tasks)} tareas de prueba")
        self.show_state()

    def show_state(self):
        """Muestra el estado actual."""
        print(f"\n📊 ESTADO ACTUAL:")
        print(f"   - Tareas: {self.model.rowCount()}")
        print(f"   - Puede deshacer: {self.command_manager.can_undo()}")
        print(f"   - Puede rehacer: {self.command_manager.can_redo()}")
        for i, task in enumerate(self.tasks):
            print(f"   - [{i}] {task.name} (Color: {task.color.name()})")

    def count_subtasks(self, actual_row):
        """Cuenta subtareas de una tarea padre."""
        count = 0
        for i in range(actual_row + 1, len(self.model.tasks)):
            task = self.model.tasks[i]
            if task.is_subtask:
                count += 1
            else:
                break
        return count

    def update_gantt_chart(self):
        """Método dummy para compatibilidad."""
        pass

    def set_unsaved_changes(self, value):
        """Método dummy para compatibilidad."""
        pass

    def _duplicate_task_internal(self, row):
        """Simulación de duplicación interna."""
        print(f"🔄 _duplicate_task_internal: row={row}")
        if 0 <= row < len(self.tasks):
            original_task = self.tasks[row]
            duplicated_task = Task(
                name=original_task.name + " (copia)",
                start_date=original_task.start_date,
                end_date=original_task.end_date,
                duration=original_task.duration,
                dedication=original_task.dedication,
                color=original_task.color
            )
            self.model.tasks.append(duplicated_task)
            self.tasks.append(duplicated_task)
            self.model.update_visible_tasks()
            print(f"✅ Tarea duplicada: {duplicated_task.name}")

    def _add_subtask_internal(self, parent_index):
        """Simulación de agregar subtarea."""
        print(f"🔄 _add_subtask_internal: parent_index={parent_index}")
        if 0 <= parent_index < len(self.tasks):
            parent_task = self.tasks[parent_index]
            subtask = Task(
                name=f"Subtarea de {parent_task.name}",
                start_date=parent_task.start_date,
                end_date=parent_task.end_date,
                duration=parent_task.duration,
                dedication=parent_task.dedication,
                color=parent_task.color
            )
            subtask.is_subtask = True
            subtask.parent_task = parent_task
            parent_task.subtasks.append(subtask)

            self.model.tasks.append(subtask)
            self.tasks.append(subtask)
            self.model.update_visible_tasks()
            print(f"✅ Subtarea agregada: {subtask.name}")

    def _insert_task_internal(self, row):
        """Simulación de insertar tarea."""
        print(f"🔄 _insert_task_internal: row={row}")
        new_task = Task(
            name="Tarea Insertada",
            start_date=QDate.currentDate().toString("dd/MM/yyyy"),
            end_date=QDate.currentDate().addDays(1).toString("dd/MM/yyyy"),
            duration="1",
            dedication="40",
            color=QColor(34, 163, 159)
        )

        # Insertar en la posición especificada
        insert_pos = min(row + 1, len(self.model.tasks))
        self.model.tasks.insert(insert_pos, new_task)
        self.tasks.insert(insert_pos, new_task)
        self.model.update_visible_tasks()
        print(f"✅ Tarea insertada: {new_task.name}")

    def _delete_task_internal(self, row):
        """Simulación de eliminar tarea."""
        print(f"🔄 _delete_task_internal: row={row}")
        if 0 <= row < len(self.tasks):
            task = self.tasks[row]
            print(f"🗑️ Eliminando tarea: {task.name}")
            self.model.tasks.remove(task)
            self.tasks.remove(task)
            self.model.update_visible_tasks()

    def _update_task_color_internal(self, task_index, color):
        """Simulación de cambio de color."""
        print(f"🔄 _update_task_color_internal: task_index={task_index}, color={color.name()}")
        if 0 <= task_index < len(self.tasks):
            self.tasks[task_index].color = color
            print(f"🎨 Color actualizado para {self.tasks[task_index].name}")

def test_duplicate():
    """Prueba duplicar tarea."""
    print("\n" + "="*50)
    print("PRUEBA: DUPLICAR TAREA")
    print("="*50)

    window = SimpleMainWindow()

    print("\nEstado inicial:")
    window.show_state()

    print("\n🔧 Ejecutando DuplicateTaskCommand...")
    cmd = DuplicateTaskCommand(window, 0)
    window.command_manager.execute_command(cmd)

    print("\nEstado después de duplicar:")
    window.show_state()

    print("\n↩️ Intentando deshacer...")
    result = window.command_manager.undo()
    print(f"Resultado: {result}")

    print("\nEstado después de deshacer:")
    window.show_state()

    return result

def test_add_subtask():
    """Prueba agregar subtarea."""
    print("\n" + "="*50)
    print("PRUEBA: AGREGAR SUBTAREA")
    print("="*50)

    window = SimpleMainWindow()

    print("\nEstado inicial:")
    window.show_state()

    print("\n🔧 Ejecutando AddSubtaskCommand...")
    cmd = AddSubtaskCommand(window, 0)
    window.command_manager.execute_command(cmd)

    print("\nEstado después de agregar subtarea:")
    window.show_state()

    print("\n↩️ Intentando deshacer...")
    result = window.command_manager.undo()
    print(f"Resultado: {result}")

    print("\nEstado después de deshacer:")
    window.show_state()

    return result

def test_insert_task():
    """Prueba insertar tarea."""
    print("\n" + "="*50)
    print("PRUEBA: INSERTAR TAREA")
    print("="*50)

    window = SimpleMainWindow()

    print("\nEstado inicial:")
    window.show_state()

    print("\n🔧 Ejecutando InsertTaskCommand...")
    cmd = InsertTaskCommand(window, 1)
    window.command_manager.execute_command(cmd)

    print("\nEstado después de insertar:")
    window.show_state()

    print("\n↩️ Intentando deshacer...")
    result = window.command_manager.undo()
    print(f"Resultado: {result}")

    print("\nEstado después de deshacer:")
    window.show_state()

    return result

def test_change_color():
    """Prueba cambiar color."""
    print("\n" + "="*50)
    print("PRUEBA: CAMBIAR COLOR")
    print("="*50)

    window = SimpleMainWindow()

    print("\nEstado inicial:")
    window.show_state()

    old_color = window.tasks[0].color
    new_color = QColor(255, 0, 0)  # Rojo

    print(f"\n🔧 Ejecutando ChangeColorCommand (de {old_color.name()} a {new_color.name()})...")
    cmd = ChangeColorCommand(window, 0, old_color, new_color)
    window.command_manager.execute_command(cmd)

    print("\nEstado después de cambiar color:")
    window.show_state()

    print("\n↩️ Intentando deshacer...")
    result = window.command_manager.undo()
    print(f"Resultado: {result}")

    print("\nEstado después de deshacer:")
    window.show_state()

    return result

def test_reset_colors():
    """Prueba restablecer colores."""
    print("\n" + "="*50)
    print("PRUEBA: RESTABLECER COLORES")
    print("="*50)

    window = SimpleMainWindow()

    # Cambiar algunos colores primero
    window.tasks[0].color = QColor(255, 0, 0)
    window.tasks[1].color = QColor(0, 255, 0)

    print("\nEstado inicial (con colores modificados):")
    window.show_state()

    print("\n🔧 Ejecutando ResetColorsCommand...")
    cmd = ResetColorsCommand(window)
    window.command_manager.execute_command(cmd)

    print("\nEstado después de restablecer colores:")
    window.show_state()

    print("\n↩️ Intentando deshacer...")
    result = window.command_manager.undo()
    print(f"Resultado: {result}")

    print("\nEstado después de deshacer:")
    window.show_state()

    return result

def main():
    """Función principal."""
    print("Baby Project Manager - Prueba Simple de Comandos")
    print("=" * 60)

    app = QApplication(sys.argv)

    tests = [
        ("Duplicar Tarea", test_duplicate),
        ("Agregar Subtarea", test_add_subtask),
        ("Insertar Tarea", test_insert_task),
        ("Cambiar Color", test_change_color),
        ("Restablecer Colores", test_reset_colors),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Error en {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    print("\n" + "="*60)
    print("RESUMEN DE RESULTADOS")
    print("="*60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print(f"\nResultado: {passed}/{total} pruebas pasaron")

    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron!")
    else:
        print("🔍 Revisar las pruebas fallidas")

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
