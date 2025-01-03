# Baby Project Manager

## Description

Baby Project Manager is a simple and effective project management application designed to help users manage tasks and create Gantt charts. It allows organizing, visualizing, and scheduling tasks in an intuitive and user-friendly way. It supports data import and export from various file formats, including `.bpm`, `.xlsx`, `.mpp`, and `.pdf`.

## Features

- **Task Management**: Create, edit, delete, and duplicate tasks, including subtasks.  Tasks can be visually organized with hierarchical indentation and customizable colors.
- **Gantt Charts**: Interactive Gantt chart visualization of scheduled tasks with support for zooming and scrolling.
- **File Support**: Import and export tasks from and to `.mpp`, `.xlsx`, and `.pdf` files.  The application uses a custom `.bpm` format for efficient data storage.
- **Filtering and Search**: Filter and search tasks by keywords, including and excluding specific terms.
- **Drag and Drop**: Drag and drop functionality for reordering tasks.
- **User-Friendly Interface**: Intuitive graphical interface based on PySide6.
- **Hyperlink Support**: Add and manage hyperlinks within task notes.
- **Holiday and Weekend Handling**: Accurately calculates task durations considering holidays and weekends in Colombia.

## Features

- **Task Management**:
  - Create, edit, delete, and duplicate tasks and subtasks
  - Visual organization with hierarchical indentation
  - Customizable colors
  - Support for notes with hyperlinks
  - Automatic duration calculation considering working days

- **Gantt Chart**:
  - Interactive schedule visualization
  - Mouse wheel zoom
  - Full, yearly, semi-annual, quarterly, and monthly views
  - Highlighted "today" line
  - Synchronization with Colombian calendar

- **File Support**:
  - Native `.bpm` format for efficient storage
  - Import from `.mpp`, `.xlsx`, and `.pdf`
  - Export to various formats
  - File security verification

- **Intuitive Interface**:
  - PySide6-based design
  - Light/dark themes
  - Context menus
  - Keyboard shortcuts
  - Multi-language support

## Requirements

- Python 3.7+
- Java JDK 8+ (required for processing MPP files - ensure JAVA_HOME is set. See `docs/Configuracion de entorno virtual de Java.txt` for setup instructions)
- Python libraries (install via `pip install -r requirements_linux.txt`o `pip install -r requirements_windows.txt`):
    - PySide6
    - pdfplumber
    - jpype1
    - mpxj
    - openpyxl
    - pandas
    - workalendar
    - pycryptodome
    - PyPDF2

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Rudull/baby-project-manager
   ```

2. **Install dependencies:**  It's recommended to use a virtual environment.
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate  # Windows
pip install -r requirements_linux.txt
pip install -r requirements_windows.txt
```

  **Option 1 - Direct Installation:**
  En Linux:
  ```bash
  pip install PySide6 pdfplumber jpype1 mpxj pandas openpyxl workalendar pycryptodome PyPDF2
  ```
  En Windows:
  ```bash
  pip install PySide6 pdfplumber jpype1 mpxj pandas openpyxl workalendar pycryptodome PyPDF2 pywin32
  ```

  **Option 2 - Using requirements.txt:**
  En Linux:
  ```bash
  pip install -r requirements_linux.txt
  ```
  En Windows:
  ```bash
  pip install -r requirements_windows.txt
  ```

## File Structure

```plaintext
├── main_window.py
│   └── MainWindow: "Ventana principal de la aplicación."
├── startup_manager.py
│   ├── StartupManager: "Manejador de inicio automatico de la aplicación."
├── config_manager.py
│   ├── ConfigManager: "Maneja la recuurrencia de la aplicación."
├── about_dialog.py
│   ├── AboutDialog(QDialog): "Maneja la ventana de información de la aplicación."
├── delegates.py
│   ├── LineEditDelegate: "Delegate para editar celdas con QLineEdit."
│   ├── DateEditDelegate: "Delegate para editar celdas con QDateEdit."
│   ├── SpinBoxDelegate: "Delegate para editar celdas con QSpinBox."
│   └── StateButtonDelegate: "Delegate para mostrar botones de estado en celdas."
├── gantt_views.py
│   ├── GanttHeaderView: "Vista del encabezado del diagrama de Gantt."
│   ├── GanttChart: "Widget que dibuja el gráfico de Gantt."
│   ├── GanttWidget: "Widget contenedor del encabezado y el gráfico de Gantt."
│   └── FloatingTaskMenu: "Menú flotante para editar notas de una tarea."
├── models.py
│   ├── Task: "Clase que representa una tarea."
│   └── TaskTableModel: "Modelo para la tabla de tareas."
├── hipervinculo.py
│   ├── HyperlinkTextEdit: "QTextEdit que maneja hipervínculos."
│   └── NotesApp: "Aplicación de ejemplo que usa HyperlinkTextEdit."
├── file_gui.py
│   ├── MPPLoaderThread: "Hilo para cargar y extraer tareas de archivos MPP."
│   ├── XLSXLoaderThread: "Hilo para cargar y extraer tareas de archivos XLSX."
│   └── MainWindow: "Ventana principal para la carga y filtro de archivos."
├── loading_animation_widget.py
│   └── LoadingAnimationWidget: "Widget para mostrar una animación de carga."
├── loading.html
│   └── "Archivo HTML para mostrar una animación de carga."
├── filter_util.py
│   ├── normalize_string: "Función para normalizar strings (quitar acentos y minúsculas)."
│   ├── is_start_end_task: "Función para identificar tareas de inicio o fin."
│   └── filter_tasks: "Función para filtrar una lista de tareas por términos."
├── jvm_manager.py
│   └── JVMManager: "Clase singleton para gestionar el ciclo de vida de la JVM."
├── table_views.py
│   └── TaskTableWidget: "Widget para la tabla de tareas."
├── mpp_extractor.py
│   └── MPPReader: "Clase para extraer datos de archivos MPP."
├── pdf_extractor.py
│   ├── TaskTreeNode: "Clase para representar un nodo en el árbol de tareas."
│   └── PDFLoaderThread: "Hilo para cargar y extraer tareas de archivos PDF."
├── pdf_security_checker.py
│   └── check_pdf_restrictions: "Función para verificar restricciones de seguridad en PDFs."
├── xlsx_extractor.py
│   └── XLSXReader: "Clase para extraer datos de archivos XLSX."
└── xlsx_security_checker.py
    └── check_xlsx_restrictions: "Función para verificar restricciones de seguridad en archivos XLSX."
  ```

## Usage

1. **Run the program**: Navigate to the project directory and run:
   ```bash
   python src/baby.py
   ```

2. Task Management:
   - Use "Add New Task" or context menu
   - Set start/end dates
   - Organize with subtasks
   - Customize colors
   - Add notes and hyperlinks

3. Gantt Chart:
   - Zoom with Ctrl + mouse wheel
   - Drag tasks
   - Change time view
   - Expand/collapse groups

4. Files:
   - Save in .bpm format
   - Import from other formats
   - Export data

## Roadmap (See `ROADMAP.md`)

## Contribution

Contributions are welcome!  Please fork the repository and submit a pull request.

## Créditos

Developed by Rafael Hernández Bustamante

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## Contact

For inquiries or more information about the project, you can open an issue in the repository or contact the authors directly.

---

I hope this guide helps you get started with Baby Project Manager. Enjoy managing your projects!
