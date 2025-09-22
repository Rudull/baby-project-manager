#!/usr/bin/env python3
"""
Script de debug simple para probar comandos específicos de Baby Project Manager
Uso: python debug_commands.py
"""

import sys
import os
from pathlib import Path

# Agregar el directorio src al path
BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QDate
from PySide6.QtGui import QColor

from main_window import MainWindow
from command_system import *

class CommandDebugger:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.main_window = MainWindow()
        self.command_manager = self.main_window.command_manager

        # Agregar algunas tareas de prueba
        self.setup_test_data()

    def setup_test_data(self):
        """Configura datos de prueba."""
        print("🔧 Configurando datos de prueba...")

        # Limpiar y agregar tareas básicas
        self.command_manager.clear()
        self.main_window.model.tasks.clear()
        self.main_window.model.update_visible_tasks()

        # Agregar 3 tareas de prueba
        for i in range(3):
            cmd = AddTaskCommand(self.main_window)
            self.command_manager.execute_command(cmd)
            task = self.main_window.model.getTask(i)
            if task:
                task.name = f"Tarea {i+1}"

        print(f"✅ Configurados {self.main_window.model.rowCount()} tareas de prueba")
        self.show_current_state()

    def show_current_state(self):
        """Muestra el estado actual."""
        print("\n📊 ESTADO ACTUAL:")
        print(f"   - Tareas totales: {self.main_window.model.rowCount()}")
        print(f"   - Puede deshacer: {self.command_manager.can_undo()}")
        print(f"   - Puede rehacer: {self.command_manager.can_redo()}")
        print(f"   - Historial: {len(self.command_manager.command_history)} comandos")

        for i in range(self.main_window.model.rowCount()):
            task = self.main_window.model.getTask(i)
            if task:
                print(f"   - [{i}] {task.name} (Color: {task.color.name()})")
        print()

    def test_insert_task(self):
        """Prueba insertar tarea."""
        print("🧪 PROBANDO: Insertar tarea")
        print("Estado inicial:")
        self.show_current_state()

        # Insertar tarea en posición 1
        print("Insertando tarea en posición 1...")
        cmd = InsertTaskCommand(self.main_window, 1)
        self.command_manager.execute_command(cmd)

        print("Estado después de insertar:")
        self.show_current_state()

        # Intentar deshacer
        print("Intentando deshacer...")
        result = self.command_manager.undo()
        print(f"Resultado de deshacer: {result}")

        print("Estado después de deshacer:")
        self.show_current_state()

    def test_duplicate_task(self):
        """Prueba duplicar tarea."""
        print("🧪 PROBANDO: Duplicar tarea")
        print("Estado inicial:")
        self.show_current_state()

        # Duplicar primera tarea
        print("Duplicando tarea 0...")
        cmd = DuplicateTaskCommand(self.main_window, 0)
        self.command_manager.execute_command(cmd)

        print("Estado después de duplicar:")
        self.show_current_state()

        # Intentar deshacer
        print("Intentando deshacer...")
        result = self.command_manager.undo()
        print(f"Resultado de deshacer: {result}")

        print("Estado después de deshacer:")
        self.show_current_state()

    def test_add_subtask(self):
        """Prueba agregar subtarea."""
        print("🧪 PROBANDO: Agregar subtarea")
        print("Estado inicial:")
        self.show_current_state()

        # Agregar subtarea a primera tarea
        print("Agregando subtarea a tarea 0...")
        cmd = AddSubtaskCommand(self.main_window, 0)
        self.command_manager.execute_command(cmd)

        print("Estado después de agregar subtarea:")
        self.show_current_state()

        # Intentar deshacer
        print("Intentando deshacer...")
        result = self.command_manager.undo()
        print(f"Resultado de deshacer: {result}")

        print("Estado después de deshacer:")
        self.show_current_state()

    def test_change_color(self):
        """Prueba cambiar color."""
        print("🧪 PROBANDO: Cambiar color")
        print("Estado inicial:")
        self.show_current_state()

        # Cambiar color de primera tarea
        task = self.main_window.model.getTask(0)
        if task:
            old_color = task.color
            new_color = QColor(255, 0, 0)  # Rojo

            print(f"Cambiando color de '{task.name}' de {old_color.name()} a {new_color.name()}...")
            cmd = ChangeColorCommand(self.main_window, 0, old_color, new_color)
            self.command_manager.execute_command(cmd)

            print("Estado después de cambiar color:")
            self.show_current_state()

            # Intentar deshacer
            print("Intentando deshacer...")
            result = self.command_manager.undo()
            print(f"Resultado de deshacer: {result}")

            print("Estado después de deshacer:")
            self.show_current_state()

    def test_reset_colors(self):
        """Prueba restablecer colores."""
        print("🧪 PROBANDO: Restablecer colores")

        # Primero cambiar algunos colores
        for i in range(2):
            task = self.main_window.model.getTask(i)
            if task:
                task.color = QColor(255, i*100, 0)

        print("Estado inicial (con colores cambiados):")
        self.show_current_state()

        # Restablecer colores
        print("Restableciendo todos los colores...")
        cmd = ResetColorsCommand(self.main_window)
        self.command_manager.execute_command(cmd)

        print("Estado después de restablecer colores:")
        self.show_current_state()

        # Intentar deshacer
        print("Intentando deshacer...")
        result = self.command_manager.undo()
        print(f"Resultado de deshacer: {result}")

        print("Estado después de deshacer:")
        self.show_current_state()

    def test_edit_notes(self):
        """Prueba editar notas."""
        print("🧪 PROBANDO: Editar notas")
        print("Estado inicial:")
        self.show_current_state()

        # Editar notas de primera tarea
        task = self.main_window.model.getTask(0)
        if task:
            old_notes = task.notes_html
            new_notes = "Esta es una nota de prueba"

            print(f"Cambiando notas de '{task.name}'...")
            print(f"  Notas anteriores: '{old_notes}'")
            print(f"  Notas nuevas: '{new_notes}'")

            cmd = EditNotesCommand(self.main_window, task, old_notes, new_notes, {}, {})
            self.command_manager.execute_command(cmd)

            print("Estado después de cambiar notas:")
            print(f"  Notas actuales: '{task.notes_html}'")
            print(f"  Tiene notas: {task.has_notes}")

            # Intentar deshacer
            print("Intentando deshacer...")
            result = self.command_manager.undo()
            print(f"Resultado de deshacer: {result}")

            print("Estado después de deshacer:")
            print(f"  Notas actuales: '{task.notes_html}'")
            print(f"  Tiene notas: {task.has_notes}")

    def run_interactive_test(self):
        """Ejecuta pruebas interactivas."""
        while True:
            print("\n" + "="*50)
            print("MENU DE PRUEBAS")
            print("="*50)
            print("1. Probar Insertar Tarea")
            print("2. Probar Duplicar Tarea")
            print("3. Probar Agregar Subtarea")
            print("4. Probar Cambiar Color")
            print("5. Probar Restablecer Colores")
            print("6. Probar Editar Notas")
            print("7. Resetear datos de prueba")
            print("8. Mostrar estado actual")
            print("9. Probar Deshacer manual")
            print("10. Probar Rehacer manual")
            print("0. Salir")

            try:
                choice = input("\nSelecciona una opción: ").strip()

                if choice == "0":
                    break
                elif choice == "1":
                    self.test_insert_task()
                elif choice == "2":
                    self.test_duplicate_task()
                elif choice == "3":
                    self.test_add_subtask()
                elif choice == "4":
                    self.test_change_color()
                elif choice == "5":
                    self.test_reset_colors()
                elif choice == "6":
                    self.test_edit_notes()
                elif choice == "7":
                    self.setup_test_data()
                elif choice == "8":
                    self.show_current_state()
                elif choice == "9":
                    result = self.command_manager.undo()
                    print(f"Resultado de deshacer: {result}")
                    self.show_current_state()
                elif choice == "10":
                    result = self.command_manager.redo()
                    print(f"Resultado de rehacer: {result}")
                    self.show_current_state()
                else:
                    print("Opción no válida")

                input("\nPresiona Enter para continuar...")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()

def main():
    print("Baby Project Manager - Debugger de Comandos")
    print("=" * 60)

    debugger = CommandDebugger()
    debugger.run_interactive_test()

    print("\n👋 Debug finalizado")
    return 0

if __name__ == "__main__":
    sys.exit(main())
