#!/usr/bin/env python3
"""
Script de prueba manual simple para comandos de deshacer/rehacer
Baby Project Manager - Se cierra automáticamente después de 2 minutos

    conda activate baby
    python scratch/e2e/test_manual.py
"""

import sys
import os
from pathlib import Path

# Agregar el directorio src al path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtWidgets import QApplication, QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import QTimer, QDate
from PySide6.QtGui import QFont, QColor

from ui.main_window import MainWindow
from core.command_system import AddTaskCommand

class InstructionsDialog(QDialog):
    """Ventana con instrucciones de prueba."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Instrucciones de Prueba - Baby Project Manager")
        self.setFixedSize(600, 500)

        layout = QVBoxLayout()

        # Título
        title = QLabel("🧪 PRUEBAS MANUALES DE DESHACER/REHACER")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Instrucciones
        instructions = """
⏰ TIEMPO LÍMITE: Esta ventana se cerrará automáticamente en 2 minutos

✅ QUÉ PROBAR (cada operación seguida de Ctrl+Z):

1. 🔄 DUPLICAR TAREA:
   • Clic derecho en cualquier tarea → "Duplicar"
   • Verificar que aparece "(copia)"
   • Presionar Ctrl+Z
   • ¿Se eliminó solo la copia? ✅

2. ➕ INSERTAR TAREA:
   • Clic derecho en cualquier tarea → "Insertar"
   • Verificar que aparece nueva tarea
   • Presionar Ctrl+Z
   • ¿Se eliminó solo la tarea insertada? ✅

3. 👶 AGREGAR SUBTAREA:
   • Clic derecho en tarea padre → "Agregar subtarea"
   • Verificar que aparece subtarea indentada
   • Presionar Ctrl+Z
   • ¿Se eliminó solo la subtarea? ✅

4. 🎨 CAMBIAR COLOR:
   • Doble clic en barra del Gantt
   • Cambiar color en el diálogo
   • Presionar Ctrl+Z
   • ¿Se restauró el color original? ✅

5. 🎨 RESTABLECER COLORES:
   • Menú ☰ → "Restablecer colores"
   • Presionar Ctrl+Z
   • ¿Se restauraron los colores anteriores? ✅

6. 📝 EDITAR NOTAS:
   • Clic en barra del Gantt (abre notas)
   • Escribir texto en las notas
   • CERRAR ventana de notas (importante!)
   • Presionar Ctrl+Z
   • ¿Se deshicieron los cambios? ✅

📋 CONTROLES:
• Ctrl+Z: Deshacer última operación
• Ctrl+Y: Rehacer operación deshecha
• Escape: Limpiar selección

⚠️  IMPORTANTE: Para notas, CERRAR la ventana antes de Ctrl+Z
        """

        instructions_label = QLabel(instructions)
        instructions_label.setWordWrap(True)
        layout.addWidget(instructions_label)

        # Botón para cerrar
        close_button = QPushButton("Entendido - Comenzar Pruebas")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        self.setLayout(layout)

class ManualTester:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.main_window = MainWindow()
        self.main_window.show()

        # Crear tareas de prueba
        self.setup_test_data()

        # Mostrar instrucciones
        self.show_instructions()

        # Timer para cerrar automáticamente (2 minutos)
        self.auto_close_timer = QTimer()
        self.auto_close_timer.timeout.connect(self.auto_close)
        self.auto_close_timer.start(120000)  # 2 minutos

        # Timer para recordatorios cada 30 segundos
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self.show_reminder)
        self.reminder_timer.start(30000)  # 30 segundos
        self.reminder_count = 0

    def setup_test_data(self):
        """Crea tareas de prueba con diferentes colores."""
        print("Configurando tareas de prueba...")

        # Limpiar historial de comandos
        self.main_window.command_manager.clear()

        # Crear 4 tareas de prueba
        task_names = ["Tarea Roja", "Tarea Verde", "Tarea Azul", "Tarea Principal"]
        colors = ["#ff0000", "#00ff00", "#0000ff", "#22a39f"]

        for i, (name, color) in enumerate(zip(task_names, colors)):
            cmd = AddTaskCommand(self.main_window)
            self.main_window.command_manager.execute_command(cmd)

            # Personalizar la tarea
            task = self.main_window.model.getTask(i)
            if task:
                task.name = name
                task.color = QColor(color)

        # Limpiar historial después de configurar
        self.main_window.command_manager.clear()

        print(f"Creadas {self.main_window.model.rowCount()} tareas de prueba")

    def show_instructions(self):
        """Muestra el diálogo de instrucciones."""
        dialog = InstructionsDialog(self.main_window)
        dialog.exec()

    def show_reminder(self):
        """Muestra recordatorios periódicos."""
        self.reminder_count += 1

        reminders = [
            "💡 Recuerda: Ctrl+Z para deshacer, Ctrl+Y para rehacer",
            "⚠️  Para notas: escribir → CERRAR ventana → Ctrl+Z",
            "🎯 Prueba duplicar, insertar, agregar subtarea, cambiar colores",
            "⏰ La aplicación se cerrará automáticamente pronto"
        ]

        if self.reminder_count <= len(reminders):
            reminder = reminders[self.reminder_count - 1]
            # Crear notificación no-modal
            msg = QMessageBox(self.main_window)
            msg.setWindowTitle("Recordatorio")
            msg.setText(reminder)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.setModal(False)
            msg.show()

            # Auto-cerrar después de 3 segundos
            QTimer.singleShot(3000, msg.close)

    def auto_close(self):
        """Cierra la aplicación automáticamente."""
        msg = QMessageBox(self.main_window)
        msg.setWindowTitle("Tiempo Completado")
        msg.setText("""
⏰ Tiempo de prueba completado

¿Todas las operaciones funcionaron correctamente?

✅ Duplicar tarea → Ctrl+Z
✅ Insertar tarea → Ctrl+Z
✅ Agregar subtarea → Ctrl+Z
✅ Cambiar color → Ctrl+Z
✅ Restablecer colores → Ctrl+Z
✅ Editar notas → Ctrl+Z

La aplicación se cerrará en 5 segundos.
        """)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.show()

        # Cerrar después de 5 segundos
        QTimer.singleShot(5000, self.app.quit)

    def run(self):
        """Inicia la aplicación de pruebas."""
        print("Baby Project Manager - Prueba Manual Simple")
        print("=" * 50)
        print("Aplicación iniciada con tareas de prueba")
        print("Ventana de instrucciones mostrada")
        print("Se cerrará automáticamente en 2 minutos")
        print("Prueba todas las operaciones seguidas de Ctrl+Z")
        print()

        return self.app.exec()

def main():
    """Función principal."""
    tester = ManualTester()
    return tester.run()

if __name__ == "__main__":
    sys.exit(main())
