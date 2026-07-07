#!/usr/bin/env python3
"""
Baby Project Manager - Build to Distribution Directory

This script builds the Baby Project Manager executable and places all build artifacts
in the distribution directory for easy packaging and distribution.

Usage:
    python build_to_distribution.py [options]

Options:
    --platform PLATFORM    Target platform (windows, linux, auto) - default: auto
    --compiler COMPILER    Compiler backend: pyinstaller or nuitka (Windows only) - default: pyinstaller
    --clean                Clean previous build files before building
    --debug                Create executable with debug output
    --onedir               Create one-directory bundle instead of one-file
    --onefile              Create one-file executable
    --test                 Test the built executable after creation
    --interactive          Force interactive configuration menu
    --help                 Show this help message

Author: Rafael Hernandez Bustamante
License: GPL-3.0
"""

import sys
import argparse
import subprocess
import shutil
import platform
from pathlib import Path
from datetime import datetime


def print_banner():
    print("=" * 80)
    print("BABY PROJECT MANAGER - BUILD TO DISTRIBUTION")
    print("=" * 80)
    print("Build executable and place all artifacts in distribution directory")
    print()


def find_project_root():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    if (project_root / "src").exists():
        return project_root

    current_dir = Path.cwd()
    for parent in [current_dir] + list(current_dir.parents):
        if (parent / "src").exists() and (parent / "build_system").exists():
            return parent

    raise FileNotFoundError("Could not find project root directory")


def detect_platform():
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system in ["linux", "darwin"]:
        return "linux"
    return "unknown"


def get_build_script_path(target_platform, compiler="pyinstaller"):
    project_root = find_project_root()
    if target_platform == "windows":
        if compiler == "nuitka":
            return project_root / "build_system" / "build_nuitka_windows.py"
        return project_root / "build_system" / "build_pyinstaller_windows.py"
    else:
        return project_root / "build_system" / "build_pyinstaller_linux.py"


def check_windows_dependencies():
    if platform.system() != "Windows":
        return True
    print("[*] Checking Windows dependencies...")
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64")
        print("   [OK] Visual C++ Redistributable found")
        winreg.CloseKey(key)
    except (ImportError, FileNotFoundError, OSError):
        print("   [!] Visual C++ Redistributable may not be installed")
    return True


def prepare_distribution_directory():
    project_root = find_project_root()
    dist_dir = project_root / "distribution"
    dist_dir.mkdir(exist_ok=True)
    for subdir in ["dist", "build", "logs", "packages"]:
        (dist_dir / subdir).mkdir(exist_ok=True)
    build_info = {
        "build_date": datetime.now().isoformat(),
        "platform": platform.system(),
        "python_version": sys.version,
        "project_root": str(project_root),
        "distribution_dir": str(dist_dir),
    }
    with open(dist_dir / "build_info.txt", "w") as f:
        f.write("Baby Project Manager - Build Information\n")
        f.write("=" * 40 + "\n\n")
        for key, value in build_info.items():
            f.write(f"{key}: {value}\n")
    return dist_dir


def clean_distribution_directory():
    project_root = find_project_root()
    dist_dir = project_root / "distribution"
    if not dist_dir.exists():
        return
    print("[*] Cleaning distribution directory...")
    for subdir in ["dist", "build"]:
        subdir_path = dist_dir / subdir
        if subdir_path.exists():
            try:
                shutil.rmtree(subdir_path)
                import time
                time.sleep(0.5)
                subdir_path.mkdir()
            except PermissionError:
                print(f"\n[X] Error: Could not clean folder '{subdir}'.")
                print(f"    The executable may be open. Close it and try again.")
                sys.exit(1)
            except Exception as e:
                print(f"   [!] Unexpected error: {e}")
                sys.exit(1)
    print("[OK] Distribution directory cleaned")


def run_command_with_output(cmd, cwd=None):
    try:
        process = subprocess.run(cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError:
        raise
    except Exception as e:
        print(f"Error starting process: {e}")
        raise


def run_build_script(target_platform, args):
    if target_platform == "windows":
        check_windows_dependencies()

    build_script = get_build_script_path(target_platform, args.compiler)
    if not build_script.exists():
        raise FileNotFoundError(f"Build script not found: {build_script}")

    cmd = [sys.executable, str(build_script), "--build-distribution"]
    if args.clean:
        cmd.append("--clean")
    if args.debug:
        cmd.append("--debug")
    if args.onedir:
        cmd.append("--onedir")
    if hasattr(args, "onefile") and args.onefile:
        cmd.append("--onefile")
    if args.test:
        cmd.append("--test")

    print(f"[*] Running build script: {build_script.name}")
    print(f"[*] Command: {' '.join(cmd[2:])}")
    print()

    try:
        run_command_with_output(cmd, cwd=str(build_script.parent))
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[X] Build script failed with exit code: {e.returncode}")
        return False
    except Exception as e:
        print(f"\n[X] Unexpected error running build script: {e}")
        return False


def copy_additional_files():
    print("[*] Copying additional files...")
    project_root = find_project_root()
    dist_dir = project_root / "distribution"

    files_to_copy = ["LICENSE", "README.md", "COMMANDS.md", "ROADMAP.md", "requirements.txt"]
    copied = []
    for file_name in files_to_copy:
        src_file = project_root / file_name
        if src_file.exists():
            shutil.copy2(src_file, dist_dir / file_name)
            copied.append(file_name)
            print(f"   Copied: {file_name}")

    src_dir = project_root / "src"
    if src_dir.exists():
        dst_src = dist_dir / "src"
        if dst_src.exists():
            shutil.rmtree(dst_src)
        shutil.copytree(src_dir, dst_src)
        print(f"   Copied: src/ directory")

    scripts_dir = dist_dir / "build_scripts"
    scripts_dir.mkdir(exist_ok=True)
    for script in ["build_pyinstaller_windows.py", "build_pyinstaller_linux.py",
                   "build_nuitka_windows.py", "build_to_distribution.py"]:
        src_script = project_root / "build_system" / script
        if src_script.exists():
            shutil.copy2(src_script, scripts_dir / script)
            print(f"   Copied: {script}")

    print(f"[OK] Copied {len(copied)} additional files")


def create_distribution_readme():
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

## Building from Source

### Windows (Nuitka - Recommended)
```cmd
python build_scripts/build_nuitka_windows.py --clean
```

### Windows (PyInstaller - Alternative)
```cmd
python build_scripts/build_pyinstaller_windows.py --clean
```

### Linux/macOS
```bash
python build_scripts/build_pyinstaller_linux.py --clean
```

### Complete Distribution
```bash
python build_scripts/build_to_distribution.py
```

## System Requirements

### Windows
- Windows 10 or later (64-bit)
- Visual C++ Redistributable 2015-2022
- Java Runtime Environment (JRE) 8 or later (for MPP file support)
- 4 GB RAM minimum

### Linux
- Modern Linux distribution with GUI support (64-bit)
- X11 or Wayland display server
- Java Runtime Environment (JRE) 8 or later (for MPP file support)

## Troubleshooting

- **Antivirus blocking**: Add the executable to antivirus exclusions
- **DLL errors (Windows)**: Install Visual C++ Redistributable 2015-2022
- **Java errors**: Ensure JAVA_HOME environment variable is set correctly
- **Permission denied (Linux)**: `chmod +x baby_project_manager`

## License

GNU General Public License v3.0 (GPL-3.0)
"""
    with open(dist_dir / "README_DISTRIBUTION.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("[OK] Created distribution README")


def create_install_script():
    project_root = find_project_root()
    dist_dir = project_root / "distribution"
    if platform.system() != "Windows":
        return
    install_content = """@echo off
echo Installing Baby Project Manager...
echo.

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo This script requires administrator privileges.
    echo Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo Copying files...
if not exist "C:\\Program Files\\BabyProjectManager" mkdir "C:\\Program Files\\BabyProjectManager"
xcopy "dist\\*" "C:\\Program Files\\BabyProjectManager\\" /E /I /Y

echo Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('$env:USERPROFILE\\Desktop\\Baby Project Manager.lnk'); $Shortcut.TargetPath = 'C:\\Program Files\\BabyProjectManager\\baby_project_manager.exe'; $Shortcut.Save()"

echo.
echo Installation completed!
echo Run from: C:\\Program Files\\BabyProjectManager\\baby_project_manager.exe
echo.
pause
"""
    with open(dist_dir / "install_windows.bat", "w", encoding="utf-8") as f:
        f.write(install_content)
    print("[OK] Created Windows installation script")


def show_distribution_summary():
    project_root = find_project_root()
    dist_dir = project_root / "distribution"
    print("\n" + "=" * 80)
    print("DISTRIBUTION BUILD COMPLETED!")
    print("=" * 80)
    print(f"\n[*] Distribution Location: {dist_dir}")

    print("\n[*] Distribution Contents:")
    try:
        for item in sorted(dist_dir.iterdir()):
            if item.is_dir():
                file_count = len(list(item.rglob("*")))
                print(f"   [DIR]  {item.name}/ ({file_count} items)")
            else:
                size_kb = item.stat().st_size / 1024
                print(f"   [FILE] {item.name} ({size_kb:.1f} KB)")
    except Exception as e:
        print(f"   [!] Could not list contents: {e}")

    dist_dist_dir = dist_dir / "dist"
    if dist_dist_dir.exists():
        for item in dist_dist_dir.rglob("*"):
            if item.is_file() and "baby_project_manager" in item.name:
                size_mb = item.stat().st_size / (1024 * 1024)
                print(f"\n[*] Executable: {item}")
                print(f"[*] Size: {size_mb:.1f} MB")
                break

    print("\n[*] Next Steps:")
    print("1. Test the executable in the dist/ directory")
    print("2. Copy the distribution/ folder to target machines")
    print("3. See README_DISTRIBUTION.md for detailed instructions")
    if platform.system() == "Windows":
        print("4. For Windows: Use install_windows.bat for system-wide installation")
    print(f"\n[OK] Distribution package ready for deployment!")


def main():
    parser = argparse.ArgumentParser(description="Build Baby Project Manager to distribution directory")
    parser.add_argument("--platform", choices=["windows", "linux", "auto"], default="auto",
                        help="Target platform (auto detects current OS)")
    parser.add_argument("--compiler", choices=["pyinstaller", "nuitka"],
                        help="Compiler backend (Windows only; default: pyinstaller)")
    parser.add_argument("--clean", action="store_true", help="Clean before building")
    parser.add_argument("--debug", action="store_true", help="Build with debug output")
    parser.add_argument("--onedir", action="store_true", help="Build as a folder (one-directory)")
    parser.add_argument("--onefile", action="store_true", help="Build as a single file")
    parser.add_argument("--test", action="store_true", help="Test executable after build")
    parser.add_argument("--interactive", action="store_true", help="Force interactive menu")
    args = parser.parse_args()

    print_banner()

    target_platform = detect_platform() if args.platform == "auto" else args.platform
    print(f"[*] Detected Platform: {target_platform.capitalize()}")

    # Interactive menu when called with no arguments or --interactive
    if len(sys.argv) == 1 or args.interactive:
        print("\n" + "-" * 40)
        print(" INTERACTIVE BUILD CONFIGURATION")
        print("-" * 40)

        if not args.compiler and target_platform == "windows":
            print("\nSelect Compiler:")
            print("1. Nuitka (Recommended — fewer antivirus false positives)")
            print("2. PyInstaller (Alternative)")
            choice = input("Enter choice [1]: ").strip()
            args.compiler = "nuitka" if choice != "2" else "pyinstaller"
        elif not args.compiler:
            args.compiler = "pyinstaller"

        if not args.onedir and not args.onefile:
            print("\nSelect Output Type:")
            print("1. Single File (One-File) (Default)")
            print("2. Folder (One-Directory)")
            choice = input("Enter choice [1]: ").strip()
            if choice == "2":
                args.onedir = True
            else:
                args.onefile = True

        if not args.test:
            print("\nSelect Build Mode:")
            print("1. Normal (Distribution) (Default)")
            print("2. Test (Build & Run executable for 5 seconds)")
            choice = input("Enter choice [1]: ").strip()
            if choice == "2":
                args.test = True

        if not args.clean:
            print("\nClean previous build files? (Recommended)")
            print("1. Yes (Default)")
            print("2. No")
            choice = input("Enter choice [1]: ").strip()
            if choice != "2":
                args.clean = True

        print("-" * 40 + "\n")

    # Default compiler if still not set
    if not args.compiler:
        args.compiler = "pyinstaller"

    try:
        if args.clean:
            clean_distribution_directory()
        prepare_distribution_directory()
        if not run_build_script(target_platform, args):
            sys.exit(1)
        copy_additional_files()
        create_distribution_readme()
        create_install_script()
        show_distribution_summary()
    except KeyboardInterrupt:
        print("\nBuild cancelled by user")
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
