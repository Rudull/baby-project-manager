#!/usr/bin/env python3
"""
Script de prueba automático para comandos de deshacer/rehacer
Baby Project Manager - Termina automáticamente

    conda activate baby
    python scratch/e2e/test_auto.py
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
from PySide6.QtCore import QTimer, QDate
from PySide6.QtGui import QColor

from ui.main_window import MainWindow
from core.command_system import (
    AddTaskCommand, DuplicateTaskCommand, InsertTaskCommand,
    AddSubtaskCommand, ChangeColorCommand, ResetColorsCommand
)

class AutoTester:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.main_window = MainWindow()
        self.main_window.show()
        self.command_manager = self.main_window.command_manager

        self.test_results = []
        self.current_test = 0
        self.tests = [
            ("Duplicar Tarea", self.test_duplicate),
            ("Insertar Tarea", self.test_insert),
            ("Agregar Subtarea", self.test_subtask),
            ("Cambiar Color", self.test_color),
            ("Restablecer Colores", self.test_reset_colors)
        ]

        # Timer para ejecutar pruebas automáticamente
        self.timer = QTimer()
        self.timer.timeout.connect(self.run_next_test)
        self.timer.start(1000)  # 1 segundo entre pruebas

    def setup_basic_tasks(self):
        """Crea tareas básicas para las pruebas."""
        # Limpiar estado
        self.command_manager.clear()
        self.main_window.model.tasks.clear()
        self.main_window.model.update_visible_tasks()

        # Agregar 3 tareas básicas
        for i in range(3):
            cmd = AddTaskCommand(self.main_window)
            self.command_manager.execute_command(cmd)
            task = self.main_window.model.getTask(i)
            if task:
                task.name = f"Tarea Base {i+1}"

        return self.main_window.model.rowCount()

    def test_duplicate(self):
        """Prueba duplicar tarea."""
        print("\nPRUEBA: Duplicar Tarea")
        initial_count = self.setup_basic_tasks()

        # Duplicar primera tarea
        cmd = DuplicateTaskCommand(self.main_window, 0)
        self.command_manager.execute_command(cmd)

        after_duplicate = self.main_window.model.rowCount()
        duplicate_success = after_duplicate == initial_count + 1

        # Intentar deshacer
        undo_success = self.command_manager.undo()
        after_undo = self.main_window.model.rowCount()
        undo_correct = after_undo == initial_count

        result = duplicate_success and undo_success and undo_correct
        print(f"   Duplicación: {'OK' if duplicate_success else 'FAIL'}")
        print(f"   Deshacer: {'OK' if undo_success and undo_correct else 'FAIL'}")
        print(f"   Resultado: {'PASÓ' if result else 'FALLÓ'}")

        return result

    def test_insert(self):
        """Prueba insertar tarea."""
        print("\nPRUEBA: Insertar Tarea")
        initial_count = self.setup_basic_tasks()

        # Insertar tarea
        cmd = InsertTaskCommand(self.main_window, 1)
        self.command_manager.execute_command(cmd)

        after_insert = self.main_window.model.rowCount()
        insert_success = after_insert == initial_count + 1

        # Intentar deshacer
        undo_success = self.command_manager.undo()
        after_undo = self.main_window.model.rowCount()
        undo_correct = after_undo == initial_count

        result = insert_success and undo_success and undo_correct
        print(f"   Inserción: {'OK' if insert_success else 'FAIL'}")
        print(f"   Deshacer: {'OK' if undo_success and undo_correct else 'FAIL'}")
        print(f"   Resultado: {'PASÓ' if result else 'FALLÓ'}")

        return result

    def test_subtask(self):
        """Prueba agregar subtarea."""
        print("\nPRUEBA: Agregar Subtarea")
        initial_count = self.setup_basic_tasks()

        # Agregar subtarea
        cmd = AddSubtaskCommand(self.main_window, 0)
        self.command_manager.execute_command(cmd)

        after_subtask = self.main_window.model.rowCount()
        subtask_success = after_subtask == initial_count + 1

        # Verificar que es subtarea
        if subtask_success:
            subtask = None
            for task in self.main_window.model.tasks:
                if task.is_subtask:
                    subtask = task
                    break
            subtask_is_correct = subtask is not None
        else:
            subtask_is_correct = False

        # Intentar deshacer
        undo_success = self.command_manager.undo()
        after_undo = self.main_window.model.rowCount()
        undo_correct = after_undo == initial_count

        result = subtask_success and subtask_is_correct and undo_success and undo_correct
        print(f"   Agregación: {'OK' if subtask_success else 'FAIL'}")
        print(f"   Es subtarea: {'OK' if subtask_is_correct else 'FAIL'}")
        print(f"   Deshacer: {'OK' if undo_success and undo_correct else 'FAIL'}")
        print(f"   Resultado: {'PASÓ' if result else 'FALLÓ'}")

        return result

    def test_color(self):
        """Prueba cambiar color."""
        print("\nPRUEBA: Cambiar Color")
        self.setup_basic_tasks()

        task = self.main_window.model.getTask(0)
        if not task:
            print("   No se pudo obtener tarea para prueba")
            return False

        old_color = task.color
        new_color = QColor(255, 0, 0)

        # Cambiar color
        cmd = ChangeColorCommand(self.main_window, 0, old_color, new_color)
        self.command_manager.execute_command(cmd)

        color_changed = task.color.name() == new_color.name()

        # Intentar deshacer
        undo_success = self.command_manager.undo()
        color_restored = task.color.name() == old_color.name()

        result = color_changed and undo_success and color_restored
        print(f"   Cambio color: {'OK' if color_changed else 'FAIL'}")
        print(f"   Deshacer: {'OK' if undo_success and color_restored else 'FAIL'}")
        print(f"   Resultado: {'PASÓ' if result else 'FALLÓ'}")

        return result

    def test_reset_colors(self):
        """Prueba restablecer colores."""
        print("\nPRUEBA: Restablecer Colores")
        self.setup_basic_tasks()

        # Cambiar algunos colores
        for i, task in enumerate(self.main_window.model.tasks[:2]):
            task.color = QColor(255, i*100, 0)

        original_colors = [task.color.name() for task in self.main_window.model.tasks]

        # Restablecer colores
        cmd = ResetColorsCommand(self.main_window)
        self.command_manager.execute_command(cmd)

        default_color = QColor(34, 163, 159)
        colors_reset = all(task.color.name() == default_color.name()
                          for task in self.main_window.model.tasks)

        # Intentar deshacer
        undo_success = self.command_manager.undo()
        current_colors = [task.color.name() for task in self.main_window.model.tasks]
        colors_restored = current_colors == original_colors

        result = colors_reset and undo_success and colors_restored
        print(f"   Restablecer: {'OK' if colors_reset else 'FAIL'}")
        print(f"   Deshacer: {'OK' if undo_success and colors_restored else 'FAIL'}")
        print(f"   Resultado: {'PASÓ' if result else 'FALLÓ'}")

        return result

    def run_next_test(self):
        """Ejecuta la siguiente prueba."""
        if self.current_test < len(self.tests):
            test_name, test_func = self.tests[self.current_test]
            try:
                result = test_func()
                self.test_results.append((test_name, result))
            except Exception as e:
                print(f"Error en {test_name}: {e}")
                self.test_results.append((test_name, False))

            self.current_test += 1
        else:
            # Todas las pruebas completadas
            self.show_final_results()
            self.timer.stop()
            # Programar cierre automático
            QTimer.singleShot(3000, self.app.quit)  # Cerrar en 3 segundos

    def show_final_results(self):
        """Muestra los resultados finales."""
        print("\n" + "="*60)
        print("RESULTADOS FINALES")
        print("="*60)

        passed = 0
        total = len(self.test_results)

        for test_name, result in self.test_results:
            status = "PASÓ" if result else "FALLÓ"
            print(f"{status} {test_name}")
            if result:
                passed += 1

        print(f"\nResumen: {passed}/{total} pruebas pasaron")

        if passed == total:
            print("¡TODAS LAS PRUEBAS PASARON!")
        else:
            print("Algunas pruebas fallaron - revisar implementación")

        print("\nLa aplicación se cerrará automáticamente en 3 segundos...")

    def run(self):
        """Inicia las pruebas automáticas."""
        print("Baby Project Manager - Pruebas Automáticas de Comandos")
        print("="*60)
        print("Iniciando pruebas automáticas...")
        print("Las pruebas se ejecutarán cada segundo")
        print("La aplicación se cerrará automáticamente al finalizar")

        return self.app.exec()

def main():
    """Función principal."""
    tester = AutoTester()
    return tester.run()

if __name__ == "__main__":
    sys.exit(main())
