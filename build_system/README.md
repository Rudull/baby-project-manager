# Baby Project Manager - Build Scripts Guide

This directory contains scripts to create standalone executables for Baby Project Manager on different operating systems.

## Available Scripts

- **Windows:**
  - `build_nuitka_windows.py` — Creates Windows executable with Nuitka **(Recommended)**
  - `build_pyinstaller_windows.py` — Creates Windows executable with PyInstaller (Alternative)
  - `check_windows_deps.py` — Checks and fixes Windows dependencies
- **Linux/macOS:**
  - `build_nuitka_linux.py` — Creates Linux/macOS executable with Nuitka **(Recommended)**
  - `build_pyinstaller_linux.py` — Creates Linux/macOS executable with PyInstaller (Alternative)
- **Distribution Packaging:**
  - `build_to_distribution.py` — Prepares complete distribution package (interactive orchestrator)

## Quick Start

### 1. Check Dependencies (Windows Only)

```cmd
python check_windows_deps.py
```

To attempt automatic fixes:

```cmd
python check_windows_deps.py --fix
```

### 2. Build Commands

#### Windows (Nuitka — Recommended)

```cmd
python build_nuitka_windows.py --clean
```

#### Windows (PyInstaller — Alternative)

```cmd
python build_pyinstaller_windows.py --clean
```

#### Linux/macOS (Nuitka — Recommended)

```bash
conda activate baby
python build_nuitka_linux.py --clean
```

#### Linux/macOS (PyInstaller — Alternative)

```bash
conda activate baby
python build_pyinstaller_linux.py --clean
```

### 3. Complete Distribution Package

**Interactive Mode (Recommended):**

```powershell
python build_to_distribution.py
```

The script detects your OS, then asks you to choose compiler (Nuitka/PyInstaller), output type, test mode, and whether to clean — step by step.

**With arguments:**

```powershell
python build_to_distribution.py --compiler nuitka --onefile --clean --test
```

## Build Options

- `--clean` — Clean previous build files before compiling
- `--debug` — Show the console in the executable (diagnose errors)
- `--onedir` — Create one-directory bundle instead of one-file
- `--onefile` — Create a single executable file
- `--test` — Automatically launch the application for 5 seconds after build
- `--compiler nuitka|pyinstaller` — Select compiler backend (`build_to_distribution.py` only)

## Output

- Individual builds: `dist/` directory in project root
- Distribution package: `distribution/` directory (complete package ready for deployment)

## Windows Dependencies

### Required Components
- **Visual C++ Redistributable 2015-2022** — Required for all Windows executables
- **Java JDK 8+** — Required for MPP file import functionality
- **Python 3.8+** — For building from source
- **Nuitka packages** — `nuitka>=2.4.4`, `ordered-set>=4.1.0`, `zstandard>=0.21.0`

Install all Python build dependencies:

```cmd
pip install -r ../requirements.txt
```

## Troubleshooting

### Nuitka
- **Version**: Ensure you have `nuitka>=2.4.4`. Older versions may fail post-processing.
- **Icon error (OSError: Invalid argument)**: The `.ico` file may be a renamed PNG. Install `Pillow` — Nuitka detects and converts it automatically.
- **Missing ordered-set / zstandard**: Run `pip install ordered-set zstandard`.
- **Antivirus false positives**: Nuitka compiles to real C, so false positives are rarer than PyInstaller. Use `--onedir` instead of `--onefile` to reduce alerts further.

### PyInstaller
- **DLL errors**: Install Visual C++ Redistributable 2015-2022.
- **Missing Qt/PySide6 DLLs**: Reinstall PySide6 or try `--onedir` instead of `--onefile`.
- **Java errors**: Ensure `JAVA_HOME` is set and points to a JDK (not just JRE).

### Linux/macOS
- **Conda SSL or Expat errors**: Ensure your Conda environment is active (`conda activate baby`) before building. Both Linux scripts bundle critical libs from `$CONDA_PREFIX` automatically.
- **Missing system libraries**: `sudo apt install libxcb-cursor0 libnss3 libatk-bridge2.0-0`
- **Permission denied on executable**: `chmod +x baby_project_manager`
