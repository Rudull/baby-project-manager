#!/usr/bin/env python3
"""
Baby Project Manager - Build to Distribution Directory

This script builds the Baby Project Manager executable and places all build artifacts
in the distribution directory for easy packaging and distribution.

Usage:
    python build_to_distribution.py [options]

Options:
    --platform PLATFORM    Target platform (windows, linux, auto) - default: auto
    --clean                 Clean previous build files before building
    --debug                 Create executable with debug output
    --onedir               Create one-directory bundle instead of one-file
    --test                 Test the built executable after creation
    --help                 Show this help message

Author: Rafael Hernandez Bustamante
License: GPL-3.0
"""

import sys
import os
import argparse
import subprocess
import shutil
import platform
from pathlib import Path
from datetime import datetime

def print_banner():
    """Print the build script banner"""
    print("=" * 80)
    print("BABY PROJECT MANAGER - BUILD TO DISTRIBUTION")
    print("=" * 80)
    print("Build executable and place all artifacts in distribution directory")
    print("for easy packaging and distribution")
    print()

def find_project_root():
    """Find the correct project root directory"""
    # Start from script location
    script_dir = Path(__file__).parent

    # Should be in baby-project-manager directory
    if script_dir.name == "baby-project-manager":
        return script_dir

    # Search upwards for baby-project-manager directory
    current_dir = Path.cwd()
    for parent in [current_dir] + list(current_dir.parents):
        baby_pm_dir = parent / "baby-project-manager"
        if baby_pm_dir.exists() and (baby_pm_dir / "src").exists():
            return baby_pm_dir

    raise FileNotFoundError("Could not find baby-project-manager project root directory")

def detect_platform():
    """Detect the current platform"""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system in ["linux", "darwin"]:
        return "linux"
    else:
        return "unknown"

def get_build_script_path(target_platform):
    """Get the appropriate build script for the platform"""
    project_root = find_project_root()

    if target_platform == "windows":
        return project_root / "build_yt-dlp_executable_windows.py"
    else:
        return project_root / "build_yt-dlp_executable_linux.py"

def check_windows_dependencies():
    """Check Windows-specific dependencies"""
    if platform.system() != "Windows":
        return True

    print("[*] Checking Windows dependencies...")

    # Check for Visual C++ Redistributable
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                           r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64")
        print("   [OK] Visual C++ Redistributable found")
        winreg.CloseKey(key)
    except (ImportError, FileNotFoundError, OSError):
        print("   [!] Visual C++ Redistributable may not be installed")

    # Check Java installation
    java_home = os.environ.get("JAVA_HOME")
    if java_home and os.path.exists(java_home):
        print(f"   [OK] JAVA_HOME found: {java_home}")

        # Check for jvm.dll
        jvm_paths = [
            Path(java_home) / "bin" / "server" / "jvm.dll",
            Path(java_home) / "bin" / "client" / "jvm.dll"
        ]

        jvm_found = any(path.exists() for path in jvm_paths)
        if jvm_found:
            print("   [OK] JVM DLL found")
        else:
            print("   [X] JVM DLL not found")
            return False
    else:
        print("   [X] JAVA_HOME not set or invalid")
        return False

    return True

def prepare_distribution_directory():
    """Prepare the distribution directory"""
    project_root = find_project_root()
    dist_dir = project_root / "distribution"

    print(f"[*] Distribution directory: {dist_dir}")

    # Create distribution directory if it doesn't exist
    dist_dir.mkdir(exist_ok=True)

    # Create subdirectories
    subdirs = ['dist', 'build', 'logs', 'packages']
    for subdir in subdirs:
        (dist_dir / subdir).mkdir(exist_ok=True)
        print(f"   Created: {subdir}/")

    # Create build info file
    build_info = {
        'build_date': datetime.now().isoformat(),
        'platform': platform.system(),
        'python_version': sys.version,
        'project_root': str(project_root),
        'distribution_dir': str(dist_dir)
    }

    build_info_file = dist_dir / "build_info.txt"
    with open(build_info_file, 'w') as f:
        f.write("Baby Project Manager - Build Information\n")
        f.write("=" * 40 + "\n\n")
        for key, value in build_info.items():
            f.write(f"{key}: {value}\n")

    print(f"[OK] Distribution directory prepared")
    return dist_dir

def clean_distribution_directory():
    """Clean the distribution directory"""
    project_root = find_project_root()
    dist_dir = project_root / "distribution"

    if not dist_dir.exists():
        return

    print("[*] Cleaning distribution directory...")

    # Clean subdirectories but keep the structure
    subdirs_to_clean = ['dist', 'build']
    for subdir in subdirs_to_clean:
        subdir_path = dist_dir / subdir
        if subdir_path.exists():
            print(f"   Cleaning {subdir}/")
            shutil.rmtree(subdir_path)
            subdir_path.mkdir()

    print("[OK] Distribution directory cleaned")

import threading
import time

def run_with_spinner(cmd, cwd=None):
    spinner = ['|', '/', '-', '\\']
    done = False
    error_occurred = False
    error_message = ""

    def target():
        nonlocal done, error_occurred, error_message
        try:
            result = subprocess.run(cmd, cwd=cwd, check=True,
                                  capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            error_occurred = True
            error_message = f"Exit code {e.returncode}: {e.stderr}"
        except Exception as e:
            error_occurred = True
            error_message = str(e)
        finally:
            done = True

    thread = threading.Thread(target=target)
    thread.start()

    i = 0
    while not done:
        sys.stdout.write(f"\r[*] Build en progreso... {spinner[i % len(spinner)]}")
        sys.stdout.flush()
        time.sleep(0.2)
        i += 1

    if error_occurred:
        sys.stdout.write("\r[X] Build falló.                        \n")
        print(f"Error: {error_message}")
        thread.join()
        raise subprocess.CalledProcessError(1, cmd)
    else:
        sys.stdout.write("\r[OK] Build finalizado.                      \n")

    thread.join()

def run_build_script(target_platform, args):
    """Run the appropriate build script"""
    print(f"[*] Starting build for platform: {target_platform}")

    # Check platform-specific dependencies
    if target_platform == "windows":
        if not check_windows_dependencies():
            print("[X] Windows dependencies check failed")
            return False

    build_script = get_build_script_path(target_platform)

    if not build_script.exists():
        raise FileNotFoundError(f"Build script not found: {build_script}")

    print(f"[*] Using build script: {build_script.name}")

    # Construct command
    cmd = [sys.executable, str(build_script), "--build-distribution"]

    if args.clean:
        cmd.append("--clean")
    if args.debug:
        cmd.append("--debug")
    if args.onedir:
        cmd.append("--onedir")
    if args.test:
        cmd.append("--test")

    print(f"[*] Running: {' '.join(cmd[1:])}")
    print()

    # Run the build script
    try:
        run_with_spinner(cmd, cwd=str(build_script.parent))
        print()
        print("✅ Build script completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print()
        print(f"❌ Build script failed with exit code: {e.returncode}")
        return False

def copy_additional_files():
    """Copy additional files to distribution directory"""
    print("[*] Copying additional files...")

    project_root = find_project_root()
    dist_dir = project_root / "distribution"

    # Files to copy from root
    files_to_copy = [
        'LICENSE',
        'README.md',
        'README_BUILD.md',
        'COMMANDS.md',
        'ROADMAP.md',
        'requirements.txt'
    ]

    copied_files = []
    for file_name in files_to_copy:
        src_file = project_root / file_name
        if src_file.exists():
            dst_file = dist_dir / file_name
            shutil.copy2(src_file, dst_file)
            copied_files.append(file_name)
            print(f"   Copied: {file_name}")

    # Copy src directory (for reference)
    src_dir = project_root / "src"
    if src_dir.exists():
        dst_src = dist_dir / "src"
        if dst_src.exists():
            shutil.rmtree(dst_src)
        shutil.copytree(src_dir, dst_src)
        print(f"   Copied: src/ directory")

    # Copy build scripts
    build_scripts = [
        'build_yt-dlp_executable_windows.py',
        'build_yt-dlp_executable_linux.py',
        'build_cx-freeze_executable_windows.py',
        'build_to_distribution.py'
    ]

    scripts_dir = dist_dir / "build_scripts"
    scripts_dir.mkdir(exist_ok=True)

    for script in build_scripts:
        src_script = project_root / script
        if src_script.exists():
            dst_script = scripts_dir / script
            shutil.copy2(src_script, dst_script)
            print(f"   Copied: {script}")

    print(f"[OK] Copied {len(copied_files)} additional files")

def create_distribution_readme():
    """Create a README file for the distribution"""
    project_root = find_project_root()
    dist_dir = project_root / "distribution"

    readme_content = """# Baby Project Manager - Distribution Package

This directory contains the built executable and all necessary files for distributing the Baby Project Manager application.

## Contents

- `dist/` - Built executable and dependencies
- `build/` - Build artifacts (for debugging)
- `src/` - Source code (for reference)
- `build_scripts/` - Build scripts for creating executables
- `logs/` - Build logs and information
- `*.md` - Documentation files
- `requirements.txt` - Python dependencies

## Running the Application

### Windows
1. Navigate to `dist/` directory
2. Run `baby_project_manager.exe`

### Linux/macOS
1. Navigate to `dist/` directory
2. Run `./baby_project_manager`
3. If permission denied, run: `chmod +x baby_project_manager`

## Features

Baby Project Manager is a powerful project management tool that includes:

- Interactive Gantt chart visualization
- Task management with subtasks
- Import from PDF, MPP, and XLSX files
- Rich text notes with hyperlinks
- Multiple view modes (complete, year, month views)
- Color-coded task organization
- Working days calculation (Colombian calendar)
- Export/import project files (.bpm format)
- Complete undo/redo system (Ctrl+Z/Ctrl+Y)

## System Requirements

### Windows
- Windows 10 or later (64-bit)
- Visual C++ Redistributable 2015-2022
- Java Runtime Environment (JRE) 8 or later (for MPP file support)
- 4 GB RAM minimum, 8 GB recommended
- 500 MB free disk space

### Linux
- Modern Linux distribution with GUI support (64-bit)
- X11 or Wayland display server
- glibc 2.17 or later
- Java Runtime Environment (JRE) 8 or later (for MPP file support)
- 4 GB RAM minimum, 8 GB recommended
- 500 MB free disk space

### macOS
- macOS 10.14 or later (64-bit)
- Java Runtime Environment (JRE) 8 or later (for MPP file support)
- 4 GB RAM minimum, 8 GB recommended
- 500 MB free disk space

## Building from Source

If you need to rebuild the application:

### Prerequisites
```bash
pip install -r requirements.txt
```

### Windows
```bash
python build_scripts/build_yt-dlp_executable_windows.py --clean
```

### Linux/macOS
```bash
python build_scripts/build_yt-dlp_executable_linux.py --clean
```

### Complete Distribution
```bash
python build_scripts/build_to_distribution.py --clean --test
```

## File Formats Supported

- **Import**:
  - PDF (Gantt charts from project management software)
  - MPP (Microsoft Project files)
  - XLSX (Excel files with project data)
- **Export**:
  - BPM (Baby Project Manager native format)

## Configuration

The application creates configuration files in:
- **Windows**: `%APPDATA%\\BabyProjectManager\\`
- **Linux/macOS**: `~/.baby-project-manager/`

Configuration includes:
- Window size and position
- Recent files
- Theme preferences
- Default colors
- View preferences

## Troubleshooting

### Windows
- **Antivirus blocking**: Add the executable to antivirus exclusions
- **DLL errors**: Install Visual C++ Redistributable 2015-2022
- **Java errors**: Ensure JAVA_HOME environment variable is set correctly
- **File access issues**: Run as administrator if needed

### Linux
- **Permission denied**: `chmod +x baby_project_manager`
- **Missing libraries**: Install required system libraries:
  ```bash
  sudo apt-get install libxcb-xinerama0 libxcb-cursor0
  ```
- **Java not found**: Install OpenJDK:
  ```bash
  sudo apt-get install openjdk-11-jre
  ```

### macOS
- **Security warning**: Right-click the app and select "Open" to bypass Gatekeeper
- **Java not found**: Install Java from https://adoptium.net/

### General Issues
- **Port 5000 in use**: Close applications using port 5000
- **Insufficient memory**: Close other applications to free up RAM
- **Temporary files**: Ensure sufficient disk space for temporary files

## Support

For issues and documentation:
- GitHub Repository: https://github.com/Rudull/baby-project-manager
- Documentation: See included README.md files
- Commands Reference: COMMANDS.md

## License

GNU General Public License v3.0 (GPL-3.0)
See LICENSE file for full license text.

## Development

Baby Project Manager is built with:
- Python 3.8+
- PySide6 (Qt for Python)
- PyInstaller (for executable creation)
- Specialized libraries for file format support

### Development Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set JAVA_HOME environment variable
4. Run from source: `python src/main_window.py`

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly (including build scripts)
5. Submit a pull request

---

Thank you for using Baby Project Manager!
"""

    readme_file = dist_dir / "README_DISTRIBUTION.md"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print("[OK] Created distribution README")

def create_requirements_file():
    """Create requirements.txt file for the distribution"""
    project_root = find_project_root()
    dist_dir = project_root / "distribution"

    requirements_content = """# Baby Project Manager - Requirements
# Install with: pip install -r requirements.txt

# Core GUI Framework
PySide6>=6.4.0

# Data processing
pandas>=1.5.0
openpyxl>=3.0.10

# PDF processing
pdfplumber>=0.7.0
PyPDF2>=3.0.0

# Java integration for MPP files
jpype1>=1.4.0

# Microsoft Project file support
mpxj>=10.0.0

# Calendar calculations
workalendar>=16.0.0

# Build tools (for development)
PyInstaller>=5.7.0
cx_Freeze>=6.13.0

# Windows-specific (for startup management)
pywin32>=306; sys_platform == "win32"

# Optional: Enhanced file format support
# python-docx>=0.8.11
# xlsxwriter>=3.0.0
"""

    requirements_file = dist_dir / "requirements.txt"
    with open(requirements_file, 'w', encoding='utf-8') as f:
        f.write(requirements_content)

    print("[OK] Created requirements.txt")

def create_install_script():
    """Create installation script for Windows"""
    project_root = find_project_root()
    dist_dir = project_root / "distribution"

    if platform.system() == "Windows":
        install_script = dist_dir / "install_windows.bat"
        install_content = """@echo off
echo Installing Baby Project Manager...
echo.

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo This script requires administrator privileges.
    echo Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

:: Copy files to Program Files
echo Copying files...
if not exist "C:\\Program Files\\BabyProjectManager" mkdir "C:\\Program Files\\BabyProjectManager"
xcopy "dist\\*" "C:\\Program Files\\BabyProjectManager\\" /E /I /Y

:: Create desktop shortcut
echo Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('$env:USERPROFILE\\Desktop\\Baby Project Manager.lnk'); $Shortcut.TargetPath = 'C:\\Program Files\\BabyProjectManager\\baby_project_manager.exe'; $Shortcut.Save()"

:: Create start menu entry
echo Creating start menu entry...
if not exist "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Baby Project Manager" mkdir "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Baby Project Manager"
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Baby Project Manager\\Baby Project Manager.lnk'); $Shortcut.TargetPath = 'C:\\Program Files\\BabyProjectManager\\baby_project_manager.exe'; $Shortcut.Save()"

echo.
echo Installation completed successfully!
echo You can now run Baby Project Manager from:
echo - Desktop shortcut
echo - Start menu
echo - C:\\Program Files\\BabyProjectManager\\baby_project_manager.exe
echo.
pause
"""
        with open(install_script, 'w', encoding='utf-8') as f:
            f.write(install_content)
        print("[OK] Created Windows installation script")

def show_distribution_summary():
    """Show summary of the distribution build"""
    project_root = find_project_root()
    dist_dir = project_root / "distribution"

    print("\n" + "=" * 80)
    print("DISTRIBUTION BUILD COMPLETED!")
    print("=" * 80)

    print(f"\n[*] Distribution Location: {dist_dir}")

    # Show directory structure
    print("\n[*] Distribution Contents:")
    try:
        for item in sorted(dist_dir.iterdir()):
            if item.is_dir():
                file_count = len(list(item.rglob("*"))) if item.exists() else 0
                print(f"   [DIR] {item.name}/ ({file_count} items)")
            else:
                size_kb = item.stat().st_size / 1024
                print(f"   [FILE] {item.name} ({size_kb:.1f} KB)")
    except Exception as e:
        print(f"   [!] Could not list contents: {e}")

    # Find executable
    dist_dist_dir = dist_dir / "dist"
    executable = None
    if dist_dist_dir.exists():
        for item in dist_dist_dir.rglob("*"):
            if item.is_file() and ("baby_project_manager" in item.name):
                executable = item
                break

    if executable:
        size_mb = executable.stat().st_size / (1024 * 1024)
        print(f"\n[*] Executable: {executable}")
        print(f"[*] Size: {size_mb:.1f} MB")

    print("\n[*] Next Steps:")
    print("1. Test the executable in the dist/ directory")
    print("2. Copy the entire distribution/ folder to target machines")
    print("3. Run the executable directly or use installation script")
    print("4. See README_DISTRIBUTION.md for detailed instructions")

    if platform.system() == "Windows":
        print("5. For Windows: Use install_windows.bat for system-wide installation")

    print(f"\n[OK] Distribution package ready for deployment!")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Build Baby Project Manager to distribution directory")
    parser.add_argument("--platform", choices=["windows", "linux", "auto"], default="auto",
                       help="Target platform (default: auto-detect)")
    parser.add_argument("--clean", action="store_true", help="Clean previous build files")
    parser.add_argument("--debug", action="store_true", help="Create executable with debug output")
    parser.add_argument("--onedir", action="store_true", help="Create one-directory bundle")
    parser.add_argument("--test", action="store_true", help="Test the built executable")

    args = parser.parse_args()

    print_banner()

    try:
        # Detect platform if auto
        if args.platform == "auto":
            target_platform = detect_platform()
            if target_platform == "unknown":
                print("❌ Could not detect platform. Please specify with --platform")
                sys.exit(1)
        else:
            target_platform = args.platform

        print(f"[*] Target platform: {target_platform}")
        print(f"[*] Current platform: {platform.system()}")

        if target_platform == "windows" and platform.system() != "Windows":
            print("[!] Warning: Building Windows executable on non-Windows platform")

        # Find project root
        project_root = find_project_root()
        print(f"[*] Project root: {project_root}")

        # Clean if requested
        if args.clean:
            clean_distribution_directory()

        # Prepare distribution directory
        dist_dir = prepare_distribution_directory()

        # Run the build script
        if not run_build_script(target_platform, args):
            print("❌ Build failed!")
            sys.exit(1)

        # Copy additional files
        copy_additional_files()

        # Create distribution README
        create_distribution_readme()

        # Create requirements file
        create_requirements_file()

        # Create installation script if on Windows
        create_install_script()

        # Show summary
        show_distribution_summary()

    except KeyboardInterrupt:
        print("\n[X] Build cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"[X] Build error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
