#!/usr/bin/env python3
"""
Baby Project Manager - Build Windows Executable (PyInstaller)

This script builds the Baby Project Manager application into a standalone Windows executable
using PyInstaller with all necessary dependencies and configurations.

Usage:
    python build_pyinstaller_windows.py [options]

Options:
    --clean                 Clean previous build files before building
    --debug                 Create executable with debug output and console
    --onedir               Create one-directory bundle instead of one-file
    --onefile              Create one-file executable (default)
    --test                  Test the built executable after creation
    --build-distribution   Build for distribution directory
    --help                  Show this help message

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
    print("=" * 80)
    print("BABY PROJECT MANAGER - WINDOWS EXECUTABLE BUILD (PYINSTALLER)")
    print("=" * 80)
    print("Building standalone Windows executable with PyInstaller")
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


def check_platform():
    if platform.system() != "Windows":
        print("WARNING: This script is designed for Windows but running on", platform.system())
        print("   The executable may not work properly on the target platform.")


def check_python_version():
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("ERROR: Python 3.8+ is required")
        sys.exit(1)
    print("Python version is compatible")


def check_windows_dlls():
    print("Checking Windows DLLs and dependencies...")
    issues = []

    try:
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64")
            print("   Visual C++ Redistributable found")
            winreg.CloseKey(key)
        except FileNotFoundError:
            issues.append("Visual C++ Redistributable 2015-2022 not found")
            print("   WARNING: Visual C++ Redistributable 2015-2022 not found")
    except ImportError:
        issues.append("Cannot check Visual C++ Redistributable")

    java_home = os.environ.get("JAVA_HOME")
    if java_home and os.path.exists(java_home):
        print(f"   JAVA_HOME: {java_home}")
        jvm_paths = [
            Path(java_home) / "bin" / "server" / "jvm.dll",
            Path(java_home) / "bin" / "client" / "jvm.dll",
        ]
        jvm_found = any(p.exists() for p in jvm_paths)
        if jvm_found:
            print(f"   JVM DLL found")
        else:
            issues.append("JVM DLL not found")
            print("   ERROR: JVM DLL not found")
    else:
        issues.append("JAVA_HOME not set or invalid")
        print("   ERROR: JAVA_HOME not set or invalid")

    try:
        import PySide6
        pyside6_path = Path(PySide6.__file__).parent
        possible_qt_bins = [
            pyside6_path / "Qt" / "bin",
            pyside6_path,
            Path(sys.prefix) / "Library" / "bin",
            Path(sys.prefix) / "bin",
        ]
        qt_bin = None
        for path in possible_qt_bins:
            if path.exists() and (path / "Qt6Core.dll").exists():
                qt_bin = path
                break
        if not qt_bin:
            dlls = list(pyside6_path.glob("**/Qt6Core.dll"))
            if dlls:
                qt_bin = dlls[0].parent
        if qt_bin:
            print(f"   Qt binaries found: {qt_bin}")
        else:
            issues.append("Qt binaries not found")
            print("   WARNING: Qt binaries location not found")
    except ImportError:
        issues.append("PySide6 not installed")

    if issues:
        print("\nWARNING: Potential issues found:")
        for issue in issues:
            print(f"   - {issue}")
        print()

    return len(issues) == 0


def check_dependencies():
    print("[*] Checking dependencies...")
    required_packages = [
        'PyInstaller', 'PySide6', 'pandas', 'openpyxl',
        'pdfplumber', 'PyPDF2', 'jpype1', 'mpxj', 'workalendar',
    ]
    missing_packages = []
    for package in required_packages:
        try:
            if package == 'PyInstaller':
                import PyInstaller
                print(f"   [OK] {package}: {PyInstaller.__version__}")
            elif package == 'PySide6':
                import PySide6
                print(f"   [OK] {package}: {PySide6.__version__}")
            elif package == 'pandas':
                import pandas
                print(f"   [OK] {package}: {pandas.__version__}")
            elif package == 'openpyxl':
                import openpyxl
                print(f"   [OK] {package}: {openpyxl.__version__}")
            elif package == 'pdfplumber':
                import pdfplumber
                print(f"   [OK] {package}: Found")
            elif package == 'PyPDF2':
                import PyPDF2
                print(f"   [OK] {package}: {PyPDF2.__version__}")
            elif package == 'jpype1':
                import jpype
                print(f"   [OK] {package}: {jpype.__version__}")
            elif package == 'mpxj':
                import mpxj
                print(f"   [OK] {package}: Found")
            elif package == 'workalendar':
                import workalendar
                print(f"   [OK] {package}: Found")
            else:
                __import__(package)
                print(f"   [OK] {package}: Found")
        except ImportError:
            print(f"   [X] {package}: Not found")
            missing_packages.append(package)
    if missing_packages:
        print(f"\n[X] Missing packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install " + " ".join(missing_packages))
        return False
    print("[OK] All dependencies are installed")
    return True


def check_source_files():
    print("[*] Checking source files...")
    project_root = find_project_root()
    src_dir = project_root / "src"
    required_files = [
        "main.py", "version.py",
        "ui/main_window.py", "core/models.py", "ui/table_views.py",
        "ui/gantt_views.py", "ui/delegates.py", "utils/config_manager.py", "ui/about_dialog.py",
        "ui/file_gui.py", "utils/filter_util.py", "core/pdf_extractor.py", "core/mpp_extractor.py",
        "core/xlsx_extractor.py", "core/pdf_security_checker.py", "core/xlsx_security_checker.py",
        "utils/jvm_manager.py", "ui/hipervinculo.py", "ui/loading_animation_widget.py",
        "templates/loading.html", "utils/startup_manager.py", "core/command_system.py",
    ]
    missing_files = []
    for file_name in required_files:
        file_path = src_dir / file_name
        if file_path.exists():
            print(f"   [OK] {file_name}")
        else:
            print(f"   [X] {file_name}: Not found")
            missing_files.append(file_name)
    if missing_files:
        print(f"\n[X] Missing source files: {', '.join(missing_files)}")
        return False
    print("[OK] All source files found")
    return True


def clean_build_files():
    print("[*] Cleaning previous build files...")
    project_root = find_project_root()

    def handle_remove_readonly(func, path, exc):
        import stat
        if not os.access(path, os.W_OK):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        else:
            raise

    for dir_name in ["build", "dist", "__pycache__"]:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"   Removing {dir_name}/")
            try:
                shutil.rmtree(dir_path, onerror=handle_remove_readonly)
            except PermissionError:
                print(f"\n[!] ERROR: Could not remove {dir_name}/. Permission denied.")
                print(f"    The executable may be running. Close it and try again.")
                sys.exit(1)
            except Exception as e:
                print(f"   [!] Warning: Could not remove {dir_name}/: {e}")

    for spec_file in project_root.glob("*.spec"):
        print(f"   Removing {spec_file.name}")
        try:
            spec_file.unlink()
        except Exception as e:
            print(f"   [!] Warning: Could not remove {spec_file.name}: {e}")

    src_pycache = project_root / "src" / "__pycache__"
    if src_pycache.exists():
        print("   Removing src/__pycache__/")
        try:
            shutil.rmtree(src_pycache, onerror=handle_remove_readonly)
        except Exception:
            pass

    print("[OK] Build files cleaned")


def get_pyside6_binaries():
    try:
        import PySide6
        pyside6_path = Path(PySide6.__file__).parent
        possible_qt_bins = [
            pyside6_path / "Qt" / "bin",
            pyside6_path,
            Path(sys.prefix) / "Library" / "bin",
            Path(sys.prefix) / "bin",
        ]
        qt_bin = None
        for path in possible_qt_bins:
            if path.exists() and (path / "Qt6Core.dll").exists():
                qt_bin = path
                break
        if not qt_bin:
            dlls = list(pyside6_path.glob("**/Qt6Core.dll"))
            if dlls:
                qt_bin = dlls[0].parent
        binaries = []
        if qt_bin:
            for dll in ["Qt6Core.dll", "Qt6Gui.dll", "Qt6Widgets.dll",
                        "Qt6WebEngineCore.dll", "Qt6WebEngineWidgets.dll",
                        "Qt6Network.dll", "Qt6PrintSupport.dll"]:
                dll_path = qt_bin / dll
                if dll_path.exists():
                    binaries.append((str(dll_path), "."))
        return binaries
    except ImportError:
        return []


def get_java_binaries():
    java_home = os.environ.get("JAVA_HOME")
    if not java_home:
        return []
    binaries = []
    for jvm_path in [Path(java_home) / "bin" / "server" / "jvm.dll",
                     Path(java_home) / "bin" / "client" / "jvm.dll"]:
        if jvm_path.exists():
            binaries.append((str(jvm_path), "."))
            break
    java_bin = Path(java_home) / "bin"
    if java_bin.exists():
        for dll in ["java.dll", "verify.dll", "zip.dll", "net.dll", "nio.dll"]:
            dll_path = java_bin / dll
            if dll_path.exists():
                binaries.append((str(dll_path), "."))
    return binaries


def create_spec_file(debug=False, onedir=False):
    print("[*] Creating PyInstaller spec file...")
    project_root = find_project_root()
    src_dir = project_root / "src"
    main_file = src_dir / "main.py"

    pyside6_binaries = get_pyside6_binaries()
    java_binaries = get_java_binaries()
    all_binaries = pyside6_binaries + java_binaries

    if onedir:
        exclude_binaries = "True"
        onefile_config = ""
        collect_block = """
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='baby_project_manager',
)"""
    else:
        exclude_binaries = "False"
        onefile_config = """
    a.binaries,
    a.zipfiles,
    a.datas,
    [],"""
        collect_block = ""

    binaries_str = "[\n"
    for binary_path, dest in all_binaries:
        binaries_str += f"    (r'{binary_path}', '{dest}'),\n"
    binaries_str += "]"

    env_file = project_root / ".env"
    datas_env = f'    (r"{env_file}", "."),\n' if env_file.exists() else ""

    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

src_dir = Path(r"{src_dir}")
sys.path.insert(0, str(src_dir))

block_cipher = None

datas = [
    (r"{src_dir / 'templates' / 'loading.html'}", "templates"),
    (r"{project_root / 'assets'}", "assets"),
{datas_env}]

binaries = {binaries_str}

hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtWidgets',
    'PySide6.QtGui',
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebEngineCore',
    'PySide6.QtPrintSupport',
    'PySide6.QtNetwork',
    'pandas',
    'openpyxl',
    'pdfplumber',
    'PyPDF2',
    'jpype',
    'jpype._core',
    'jpype._jclass',
    'jpype._jarray',
    'jpype._jproxy',
    'mpxj',
    'workalendar',
    'workalendar.america',
    'unicodedata',
    'ast',
    'configparser',
    'platform',
    'pathlib',
    'datetime',
    'math',
    'subprocess',
    'shutil',
    're',
    'os',
    'sys',
    'winreg',
    'requests',
    'urllib3',
    'charset_normalizer',
    'idna',
    'certifi',
    'ssl',
]

excludes = [
    'tkinter',
    'unittest',
    'test',
    'distutils',
    'setuptools',
    'numpy.f2py',
    'numpy.distutils',
    'matplotlib',
    'scipy',
    'IPython',
    'jupyter',
]

a = Analysis(
    [r"{main_file}"],
    pathex=[r"{src_dir}"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,{onefile_config}
    exclude_binaries={exclude_binaries},
    name='baby_project_manager',
    debug={debug},
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console={debug},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=r"{project_root / 'assets' / 'icono.ico'}",
)
{collect_block}
'''

    spec_file = project_root / "baby_project_manager.spec"
    with open(spec_file, "w", encoding="utf-8") as f:
        f.write(spec_content)
    print(f"[OK] Spec file created: {spec_file}")
    return spec_file


def run_command_with_output(cmd, cwd=None):
    try:
        process = subprocess.run(cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError:
        raise
    except Exception as e:
        print(f"Error starting process: {e}")
        raise


def build_executable(spec_file, debug=False, build_distribution=False):
    print("[*] Building executable with PyInstaller...")
    project_root = find_project_root()

    if build_distribution:
        distribution_dir = project_root / "distribution"
        build_dir = distribution_dir / "build"
        dist_dir = distribution_dir / "dist"
        build_dir.mkdir(parents=True, exist_ok=True)
        dist_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean", "--noconfirm",
            f"--workpath={build_dir}",
            f"--distpath={dist_dir}",
        ]
    else:
        cmd = [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm"]

    if debug:
        cmd.append("--debug=all")

    cmd.append(str(spec_file))
    print(f"[*] Running: {' '.join(cmd[3:])}")
    print()

    try:
        run_command_with_output(cmd, cwd=str(project_root))
        print()
        print("[OK] Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print()
        print(f"[X] Build failed with exit code: {e.returncode}")
        return False


def test_executable(build_distribution=False):
    print("Testing executable...")
    project_root = find_project_root()

    if build_distribution:
        dist_dir = project_root / "distribution" / "dist"
    else:
        dist_dir = project_root / "dist"

    exe_onefile = dist_dir / "baby_project_manager.exe"
    exe_onedir = dist_dir / "baby_project_manager" / "baby_project_manager.exe"

    exe_path = None
    if exe_onefile.exists():
        exe_path = exe_onefile
    elif exe_onedir.exists():
        exe_path = exe_onedir

    if not exe_path:
        print(f"Executable not found in expected locations: {dist_dir}")
        return False

    print(f"Executable location: {exe_path}")

    try:
        print("   Starting executable...")
        process = subprocess.Popen([str(exe_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        import time
        time.sleep(5)
        if process.poll() is None:
            print("   Application started successfully")
            process.terminate()
            process.wait(timeout=10)
            print("Executable test completed successfully")
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"   Process exited with code: {process.returncode}")
            if stderr:
                print(f"   STDERR: {stderr.decode()}")
            return False
    except Exception as e:
        print(f"Executable test failed: {e}")
        return False


def show_build_results(build_distribution=False):
    print("\n" + "=" * 80)
    print("BUILD COMPLETED!")
    print("=" * 80)

    project_root = find_project_root()
    dist_dir = project_root / "distribution" / "dist" if build_distribution else project_root / "dist"

    if not dist_dir.exists():
        print("Dist directory not found!")
        return

    print(f"\nBuild Location: {dist_dir}")

    exe_onefile = dist_dir / "baby_project_manager.exe"
    exe_onedir = dist_dir / "baby_project_manager" / "baby_project_manager.exe"

    exe_path = None
    bundle_type = None
    if exe_onefile.exists():
        exe_path, bundle_type = exe_onefile, "One-file"
    elif exe_onedir.exists():
        exe_path, bundle_type = exe_onedir, "One-directory"

    if exe_path:
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"Executable: {exe_path}")
        print(f"Bundle Type: {bundle_type}")
        print(f"Size: {size_mb:.1f} MB")
    else:
        print("Executable not found in dist directory")


def main():
    parser = argparse.ArgumentParser(description="Build Baby Project Manager Windows executable (PyInstaller)")
    parser.add_argument("--clean", action="store_true", help="Clean previous build files")
    parser.add_argument("--debug", action="store_true", help="Create executable with debug output")
    parser.add_argument("--onedir", action="store_true", help="Create one-directory bundle")
    parser.add_argument("--onefile", action="store_true", help="Create one-file executable (default)")
    parser.add_argument("--test", action="store_true", help="Test the built executable")
    parser.add_argument("--build-distribution", action="store_true", help="Build for distribution")
    args = parser.parse_args()

    print_banner()

    try:
        check_platform()
        check_python_version()

        project_root = find_project_root()
        print(f"Project root: {project_root}")

        if not check_dependencies():
            sys.exit(1)

        if not check_windows_dlls():
            print("WARNING: Windows dependency issues detected. Build may fail.")
            response = input("Continue anyway? (y/N): ").strip().lower()
            if response != "y":
                print("Build cancelled.")
                sys.exit(1)

        if not check_source_files():
            sys.exit(1)

        if args.clean:
            clean_build_files()

        spec_file = create_spec_file(debug=args.debug, onedir=args.onedir)

        if not build_executable(spec_file, debug=args.debug, build_distribution=args.build_distribution):
            sys.exit(1)

        if args.test:
            if not test_executable(build_distribution=args.build_distribution):
                print("Warning: Executable test failed, but build completed")

        show_build_results(build_distribution=args.build_distribution)

    except KeyboardInterrupt:
        print("\nBuild cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Build error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
