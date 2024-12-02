# Baby Project Manager

## Description

Baby Project Manager is a simple and effective project management application designed to help users manage tasks and create Gantt charts. It allows users to organize, visualize, and schedule tasks in an intuitive and easy-to-use manner.

## Features

- **Task Management**: Create, edit, delete, and duplicate tasks, as well as add subtasks.
- **Gantt Charts**: Visualization of scheduled tasks in an interactive Gantt chart.
- **File Support**: Import and export tasks from and to `.bpm`, `.xlsx`, and `PDF` files.
- **Filtering and Search**: Search tasks by keywords and include/exclude certain terms.
- **Visual Organization**: Organize tasks with hierarchical indentation and customizable colors.
- **User-Friendly Interface**: Intuitive graphical interface based on PySide6.

## Requirements

- Python 3.7+
- Java JDK 8+ (required for processing MPP files - ensure JAVA_HOME is set)
- Python libraries (install via `pip install -r requirements.txt`):
    - PySide6
    - pdfplumber
    - jpype1
    - mpxj
    - openpyxl
    - pandas
    - workalendar

## Installation

- **Clone the repository:**
   ```bash
   git clone https://github.com/Rudull/baby-project-manag
   ```

- **Install dependencies:**

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
3.Proyectos_de_Software/
├── baby-project-manager/
│   ├── docs/                  # Documentation
│   ├── src/                   # Source code of the application
│   ├── tests/                 # Test files
│   └── ...
├── .gitignore                 # Files to be ignored by Git
├── ROADMAP.md                 # Project roadmap
└── ...                        # Other configuration files
```

## Usage

1. **Run the program**:
   - Navigate to the project folder and run the main file.

   ```bash
   python src/baby.py
   ```

2. **Add Tasks**:
   - Use the "Add New Task" button to enter tasks and set start and end dates.

3. **View in Gantt Chart**:
   - Tasks will automatically appear in the Gantt chart once they are created.

4. **Import and Export Data**:
   - Use menu options to import/export tasks to compatible files.

5. **Filter Tasks**:
   - You can use the search and filter functions to find specific tasks in your list.

## Roadmap

The project follows a roadmap with a list of tasks and planned improvements. Some of these include:

- Fix issues with hyperlinks.
- Add drag and drop task option.
- Improve integration with other file formats.

## Contribution

Contributions are welcome! If you wish to contribute to the project, please fork the repository and submit a pull request with your enhancements.

## License

This project is licensed under the MIT License. Please refer to the `LICENSE` file for more details.

## Contact

For inquiries or more information about the project, you can open an issue in the repository or contact the authors directly.

---

I hope this guide helps you get started with Baby Project Manager. Enjoy managing your projects!
