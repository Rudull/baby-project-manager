# Baby Project Manager

## Description

Baby Project Manager is a simple and effective project management application designed to help users manage tasks and create Gantt charts. It allows users to organize, visualize, and schedule tasks in an intuitive and easy-to-use manner.  It supports importing and exporting data from various file formats, including `.bpm`, `.xlsx`, and `.pdf`.

## Features

- **Task Management**: Create, edit, delete, and duplicate tasks, including subtasks.  Tasks can be visually organized with hierarchical indentation and customizable colors.
- **Gantt Charts**: Interactive Gantt chart visualization of scheduled tasks with support for zooming and scrolling.
- **File Support**: Import and export tasks from and to `.bpm`, `.xlsx`, and `.pdf` files.  The application uses a custom `.bpm` format for efficient data storage.
- **Filtering and Search**: Filter and search tasks by keywords, including and excluding specific terms.
- **Drag and Drop**: Drag and drop functionality for reordering tasks.
- **User-Friendly Interface**: Intuitive graphical interface based on PySide6.
- **Hyperlink Support**: Add and manage hyperlinks within task notes.
- **Holiday and Weekend Handling**: Accurately calculates task durations considering holidays and weekends in Colombia.

## Requirements

- Python 3.7+
- Java JDK 8+ (required for processing MPP files - ensure JAVA_HOME is set. See `docs/Configuracion de entorno virtual de Java.txt` for setup instructions)
- Python libraries (install via `pip install -r requirements.txt`):
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
pip install -r requirements.txt
```

  **Option 1 - Direct Installation:**
  ```bash
  pip install PySide6 pdfplumber jpype1 mpxj pandas openpyxl workalendar
  ```
  **Option 2 - Using requirements.txt:**
  ```bash
  pip install -r requirements.txt
  ```

## File Structure

```plaintext
baby-project-manager/
├── docs/                  # Documentation
├── src/                   # Source code of the application
├── tests/                 # Test files
└── ...
```

## Usage

1. **Run the program**: Navigate to the project directory and run:
   ```bash
   python src/baby.py
   ```

2. **Add Tasks**: Use the "Add New Task" button or the context menu to add tasks and set start and end dates.

3. **View in Gantt Chart**: Tasks appear automatically in the Gantt chart. Use the mouse wheel to zoom in/out (Ctrl + mouse wheel).

4. **Import and Export Data**: Use the menu options to import/export tasks.

5. **Filter Tasks**: Use the search and filter functions to locate specific tasks.

## Roadmap (See `ROADMAP.md`)

## Contribution

Contributions are welcome!  Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## Contact

For inquiries or more information about the project, you can open an issue in the repository or contact the authors directly.

---

I hope this guide helps you get started with Baby Project Manager. Enjoy managing your projects!
