# Baby Project Manager - Build Scripts Guide

This directory contains scripts to create standalone executables for Baby Project Manager on different operating systems.

## 📁 Available Scripts

- **Windows:**
  - `build_yt-dlp_executable_windows.py` - Creates Windows executable (.exe) with PyInstaller
  - `build_cx-freeze_executable_windows.py` - Creates Windows executable (.exe) with cx_Freeze (alternative)
  - `check_windows_deps.py` - Checks and fixes Windows dependencies
- **Linux/macOS:**
  - `build_yt-dlp_executable_linux.py` - Creates Linux/macOS executable
- **Distribution Packaging:**
  - `build_to_distribution.py` - Prepares complete distribution package for **Windows, Linux, and macOS**

## 🚀 Quick Start

### 1. Check Dependencies (Windows Only)

Before building on Windows, check dependencies:

```cmd
python check_windows_deps.py
```

To attempt automatic fixes:

```cmd
python check_windows_deps.py --fix
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Build Commands

#### Windows (PyInstaller - Recommended)

```cmd
python build_yt-dlp_executable_windows.py --clean
```

#### Windows (cx_Freeze - Alternative)

```cmd
python build_cx-freeze_executable_windows.py --clean
```

#### Linux/macOS

```bash
python build_yt-dlp_executable_linux.py --clean
```

### 4. Build Options

- `--clean` - Clean previous build files before compiling
- `--debug` - Create executable with debug output and console
- `--onedir` - Create one-directory bundle instead of one-file
- `--test` - Test the built executable after creation
- `--build-distribution` - Build for distribution directory

### 5. Complete Distribution Package

```bash
python build_to_distribution.py --clean --test
```

Options:
- `--platform windows|linux|auto` - Force specific platform (auto-detect by default)
- `--clean` - Clean previous builds
- `--debug` - Create debug executable
- `--onedir` - Create directory bundle instead of single file
- `--test` - Test executable after build

## 📦 Output

The executables will be created in:
- Individual builds: `dist/` directory
- Distribution package: `distribution/` directory (complete package ready for deployment)

## 🔧 Windows Dependencies

### Required Components
- **Visual C++ Redistributable 2015-2022**: Required for PyInstaller executables
- **Java JDK 8+**: Required for MPP file import functionality
- **Python 3.8+**: For building from source

### Common Issues and Solutions

#### DLL Errors
If you encounter DLL errors when running the built executable:

1. **Missing Visual C++ Redistributable**:
   - Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
   - Or run: `python check_windows_deps.py --fix`

2. **Missing Java DLLs**:
   - Install Java JDK (not just JRE)
   - Set JAVA_HOME environment variable
   - Add Java bin directory to PATH

3. **Missing Qt/PySide6 DLLs**:
   - Reinstall PySide6: `pip uninstall PySide6 && pip install PySide6`
   - Try building with `--onedir` instead of `--onefile`

#### Build Failures
- Run dependency checker: `python check_windows_deps.py`
- Clean previous builds: `--clean` option
- Check available disk space (minimum 2GB)
- Ensure antivirus is not blocking build process

## 🧪 Testing

To test the program from source code:

```bash
cd src
python main_window.py
```

To test built executable:
- Run with `--test` option during build
- Or manually execute the generated .exe file