#!/usr/bin/env python3
"""
Test script para el sistema de comandos de Baby Project Manager
Verifica que todas las operaciones de deshacer/rehacer funcionen correctamente.

    conda activate baby
    python scratch/integration/test_commands.py
"""

import sys
import os
from pathlib import Path

# Agregar el directorio src al path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDate
from PySide6.QtGui import QColor

from ui.main_window import MainWindow
from core.command_system import (
    CommandManager, AddTaskCommand, DeleteTaskCommand,
    MoveTaskCommand, ChangeColorCommand, DuplicateTaskCommand,
    EditTaskCommand, ConvertTaskCommand, AddSubtaskCommand
)

class CommandTester:
    """Clase para probar el sistema de comandos."""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.main_window = MainWindow()
        self.command_manager = self.main_window.command_manager
        self.passed_tests = 0
        self.total_tests = 0

    def assert_equal(self, actual, expected, test_name):
        """Verifica que dos valores sean iguales."""
        self.total_tests += 1
        if actual == expected:
            print(f"{test_name}: PASSED")
            self.passed_tests += 1
        else:
            print(f"{test_name}: FAILED - Expected {expected}, got {actual}")

    def assert_true(self, condition, test_name):
        """Verifica que una condición sea verdadera."""
        self.total_tests += 1
        if condition:
            print(f"{test_name}: PASSED")
            self.passed_tests += 1
        else:
            print(f"{test_name}: FAILED - Condition was false")

    def test_add_task_command(self):
        """Prueba el comando de agregar tarea."""
        print("\n=== Probando AddTaskCommand ===")

        initial_count = self.main_window.model.rowCount()

        # Ejecutar comando de agregar tarea
        command = AddTaskCommand(self.main_window)
        self.command_manager.execute_command(command)

        new_count = self.main_window.model.rowCount()
        self.assert_equal(new_count, initial_count + 1, "Tarea agregada correctamente")

        # Verificar que se puede deshacer
        self.assert_true(self.command_manager.can_undo(), "Puede deshacer después de agregar")

        # Deshacer
        self.command_manager.undo()
        undone_count = self.main_window.model.rowCount()
        self.assert_equal(undone_count, initial_count, "Tarea eliminada correctamente al deshacer")

        # Verificar que se puede rehacer
        self.assert_true(self.command_manager.can_redo(), "Puede rehacer después de deshacer")

        # Rehacer
        self.command_manager.redo()
        redone_count = self.main_window.model.rowCount()
        self.assert_equal(redone_count, initial_count + 1, "Tarea re-agregada correctamente al rehacer")

    def test_delete_task_command(self):
        """Prueba el comando de eliminar tarea."""
        print("\n=== Probando DeleteTaskCommand ===")

        # Primero agregar una tarea para eliminar
        add_command = AddTaskCommand(self.main_window)
        self.command_manager.execute_command(add_command)

        initial_count = self.main_window.model.rowCount()

        # Obtener la tarea antes de eliminar
        task_to_delete = self.main_window.model.getTask(0)
        task_name = task_to_delete.name if task_to_delete else ""

        # Eliminar la primera tarea
        delete_command = DeleteTaskCommand(self.main_window, 0)
        self.command_manager.execute_command(delete_command)

        new_count = self.main_window.model.rowCount()
        self.assert_equal(new_count, initial_count - 1, "Tarea eliminada correctamente")

        # Deshacer eliminación
        self.command_manager.undo()
        restored_count = self.main_window.model.rowCount()
        self.assert_equal(restored_count, initial_count, "Tarea restaurada correctamente")

        # Verificar que la tarea restaurada tiene el mismo nombre
        restored_task = self.main_window.model.getTask(0)
        restored_name = restored_task.name if restored_task else ""
        self.assert_equal(restored_name, task_name, "Nombre de tarea restaurada correctamente")

    def test_move_task_command(self):
        """Prueba los comandos de mover tarea."""
        print("\n=== Probando MoveTaskCommand ===")

        # Agregar dos tareas
        self.command_manager.execute_command(AddTaskCommand(self.main_window))
        self.command_manager.execute_command(AddTaskCommand(self.main_window))

        # Obtener nombres de las tareas
        task1 = self.main_window.model.getTask(0)
        task2 = self.main_window.model.getTask(1)
        name1 = task1.name if task1 else ""
        name2 = task2.name if task2 else ""

        # Mover la segunda tarea hacia arriba
        move_command = MoveTaskCommand(self.main_window, 1, "up")
        self.command_manager.execute_command(move_command)

        # Verificar que las tareas cambiaron de posición
        moved_task1 = self.main_window.model.getTask(0)
        moved_task2 = self.main_window.model.getTask(1)
        moved_name1 = moved_task1.name if moved_task1 else ""
        moved_name2 = moved_task2.name if moved_task2 else ""

        self.assert_equal(moved_name1, name2, "Segunda tarea movida a primera posición")
        self.assert_equal(moved_name2, name1, "Primera tarea movida a segunda posición")

        # Deshacer movimiento
        self.command_manager.undo()
        restored_task1 = self.main_window.model.getTask(0)
        restored_task2 = self.main_window.model.getTask(1)
        restored_name1 = restored_task1.name if restored_task1 else ""
        restored_name2 = restored_task2.name if restored_task2 else ""

        self.assert_equal(restored_name1, name1, "Orden original restaurado después de deshacer")
        self.assert_equal(restored_name2, name2, "Orden original restaurado después de deshacer")

    def test_color_change_command(self):
        """Prueba el comando de cambio de color."""
        print("\n=== Probando ChangeColorCommand ===")

        # Agregar una tarea
        self.command_manager.execute_command(AddTaskCommand(self.main_window))

        task = self.main_window.model.getTask(0)
        if task:
            original_color = task.color
            new_color = QColor(255, 0, 0)  # Rojo

            # Cambiar color
            color_command = ChangeColorCommand(self.main_window, 0, original_color, new_color)
            self.command_manager.execute_command(color_command)

            # Verificar que el color cambió
            self.assert_equal(task.color.name(), new_color.name(), "Color cambiado correctamente")

            # Deshacer cambio de color
            self.command_manager.undo()
            self.assert_equal(task.color.name(), original_color.name(), "Color restaurado correctamente")

    def test_duplicate_task_command(self):
        """Prueba el comando de duplicar tarea."""
        print("\n=== Probando DuplicateTaskCommand ===")

        # Agregar una tarea
        self.command_manager.execute_command(AddTaskCommand(self.main_window))
        initial_count = self.main_window.model.rowCount()

        # Duplicar la tarea
        duplicate_command = DuplicateTaskCommand(self.main_window, 0)
        self.command_manager.execute_command(duplicate_command)

        new_count = self.main_window.model.rowCount()
        self.assert_equal(new_count, initial_count + 1, "Tarea duplicada correctamente")

        # Verificar que la tarea duplicada tiene "(copia)" en el nombre
        duplicated_task = self.main_window.model.getTask(1)
        if duplicated_task:
            self.assert_true("(copia)" in duplicated_task.name, "Tarea duplicada tiene '(copia)' en el nombre")

        # Deshacer duplicación
        self.command_manager.undo()
        undone_count = self.main_window.model.rowCount()
        self.assert_equal(undone_count, initial_count, "Duplicación deshecha correctamente")

    def test_command_history_limit(self):
        """Prueba el límite del historial de comandos."""
        print("\n=== Probando límite del historial ===")

        # Limpiar historial
        self.command_manager.clear()

        # Ejecutar más comandos que el límite
        max_history = self.command_manager.max_history
        for i in range(max_history + 5):
            self.command_manager.execute_command(AddTaskCommand(self.main_window))

        # Verificar que el historial no excede el límite
        history_length = len(self.command_manager.command_history)
        self.assert_true(history_length <= max_history, f"Historial limitado a {max_history} comandos")

    def test_command_manager_state(self):
        """Prueba el estado del gestor de comandos."""
        print("\n=== Probando estado del CommandManager ===")

        # Limpiar historial
        self.command_manager.clear()

        # Estado inicial
        self.assert_true(not self.command_manager.can_undo(), "No puede deshacer inicialmente")
        self.assert_true(not self.command_manager.can_redo(), "No puede rehacer inicialmente")

        # Ejecutar un comando
        self.command_manager.execute_command(AddTaskCommand(self.main_window))

        self.assert_true(self.command_manager.can_undo(), "Puede deshacer después de ejecutar comando")
        self.assert_true(not self.command_manager.can_redo(), "No puede rehacer después de ejecutar comando")

        # Deshacer
        self.command_manager.undo()

        self.assert_true(not self.command_manager.can_undo(), "No puede deshacer después de deshacer todo")
        self.assert_true(self.command_manager.can_redo(), "Puede rehacer después de deshacer")

        # Rehacer
        self.command_manager.redo()

        self.assert_true(self.command_manager.can_undo(), "Puede deshacer después de rehacer")
        self.assert_true(not self.command_manager.can_redo(), "No puede rehacer después de rehacer todo")

    def test_subtask_commands(self):
        """Prueba los comandos relacionados con subtareas."""
        print("\n=== Probando comandos de subtareas ===")

        # Agregar una tarea padre
        self.command_manager.execute_command(AddTaskCommand(self.main_window))
        initial_count = self.main_window.model.rowCount()

        # Agregar subtarea
        subtask_command = AddSubtaskCommand(self.main_window, 0)
        self.command_manager.execute_command(subtask_command)

        new_count = self.main_window.model.rowCount()
        self.assert_equal(new_count, initial_count + 1, "Subtarea agregada correctamente")

        # Verificar que la nueva tarea es una subtarea
        subtask = self.main_window.model.getTask(1)
        if subtask:
            self.assert_true(subtask.is_subtask, "Nueva tarea es efectivamente una subtarea")

        # Deshacer agregar subtarea
        self.command_manager.undo()
        undone_count = self.main_window.model.rowCount()
        self.assert_equal(undone_count, initial_count, "Subtarea eliminada correctamente al deshacer")

    def run_all_tests(self):
        """Ejecuta todas las pruebas."""
        print("Iniciando pruebas del sistema de comandos...")
        print("=" * 50)

        try:
            self.test_command_manager_state()
            self.test_add_task_command()
            self.test_delete_task_command()
            self.test_move_task_command()
            self.test_color_change_command()
            self.test_duplicate_task_command()
            self.test_subtask_commands()
            self.test_command_history_limit()
        except Exception as e:
            print(f"Error durante las pruebas: {e}")
            import traceback
            traceback.print_exc()

        print("\n" + "=" * 50)
        print(f"Pruebas completadas: {self.passed_tests}/{self.total_tests} pasaron")

        if self.passed_tests == self.total_tests:
            print("¡Todas las pruebas pasaron exitosamente!")
            return True
        else:
            print("Algunas pruebas fallaron.")
            return False

def main():
    """Función principal para ejecutar las pruebas."""
    print("Baby Project Manager - Test del Sistema de Comandos")
    print("=" * 60)

    tester = CommandTester()
    success = tester.run_all_tests()

    if success:
        print("\nSistema de comandos funcionando correctamente.")
        print("Puedes usar Ctrl+Z para deshacer y Ctrl+Y para rehacer en la aplicación.")
    else:
        print("\nSe encontraron problemas en el sistema de comandos.")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
