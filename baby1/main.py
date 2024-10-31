# main.py
import sys
from PySide6.QtWidgets import QApplication
from main_window import MainWindow

def main():
    # Crear la aplicación de Qt
    app = QApplication(sys.argv)

    # Configurar el estilo de la aplicación
    app.setStyle("Fusion")

    # Aplicar la paleta de colores estándar del sistema
    app.setPalette(app.style().standardPalette())

    # Crear la ventana principal
    window = MainWindow()

    # Mostrar la ventana principal
    window.show()

    # Ejecutar el bucle de eventos de la aplicación
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
