# Build System Guide

Baby Project Manager uses a modern build system with support for Nuitka (recommended) and PyInstaller compilers.

## Quick Start

### Interactive Build (Recommended)

```powershell
conda activate baby
python build_system/build_to_distribution.py
```

The script will ask you to choose:
1. **Compiler**: Nuitka (recommended, fewer antivirus false positives) or PyInstaller
2. **Output Type**: Single file or folder bundle
3. **Build Mode**: Normal or Test (runs for 5 seconds after build)
4. **Clean**: Remove previous builds

### Windows-Specific (Nuitka)

```powershell
conda activate baby
python build_system/build_nuitka_windows.py --clean
```

### Windows-Specific (PyInstaller)

```powershell
conda activate baby
python build_system/build_pyinstaller_windows.py --clean
```

### Linux/macOS

```bash
conda activate baby
python build_system/build_pyinstaller_linux.py --clean
```

## Build Options

- `--clean` — Remove previous build artifacts
- `--debug` — Include console output for debugging
- `--onedir` — Create folder bundle (default)
- `--onefile` — Create single executable file
- `--test` — Auto-launch executable for 5 seconds after build
- `--compiler nuitka|pyinstaller` — Choose compiler (Windows, `build_to_distribution.py` only)

## Output

- **Individual builds**: `dist/` folder in project root
- **Distribution package**: `distribution/` folder (ready to deploy)

## Requirements

### Windows
- Visual C++ Redistributable 2015-2022
- Java JDK 8+ (for MPP file support)
- Python 3.8+

### Linux/macOS
- Java JDK 8+ (for MPP file support)
- Python 3.8+

## Troubleshooting

### Nuitka
- **Missing packages**: `pip install nuitka ordered-set zstandard`
- **Icon error**: Ensure `.ico` file is valid (not renamed PNG)
- **Antivirus**: Nuitka produces fewer false positives than PyInstaller

### PyInstaller
- **DLL errors (Windows)**: Install Visual C++ Redistributable
- **Java errors**: Set `JAVA_HOME` environment variable

### Linux
- **Permission denied**: `chmod +x baby_project_manager`
- **Missing libraries**: `sudo apt install libxcb-cursor0 libnss3 libatk-bridge2.0-0`

## Compiler Comparison

| Feature | Nuitka | PyInstaller |
|---------|--------|-------------|
| Speed | Faster | Standard |
| File Size | Medium | Large |
| Antivirus FP | Lower | Higher |
| Support | Recommended | Alternative |

## Files

- [build_system/README.md](build_system/README.md) — Detailed build documentation
- [requirements.txt](requirements.txt) — Python dependencies
