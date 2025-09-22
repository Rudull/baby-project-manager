#!/usr/bin/env python3
"""
Baby Project Manager - Build Windows Executable

This script builds the Baby Project Manager application into a standalone Windows executable
using PyInstaller with all necessary dependencies and configurations.

Usage:
    python build_yt-dlp_executable_windows.py [options]

Options:
    --clean                 Clean previous build files before building
    --debug                 Create executable with debug output and console
    --onedir               Create one-directory bundle instead of one-file
    --test                 Test the built executable after creation
    --build-distribution   Build for distribution directory
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
    print("BABY PROJECT MANAGER - WINDOWS EXECUTABLE BUILD")
    print("=" * 80)
    print("Building standalone Windows executable with PyInstaller")
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

def check_platform():
    """Check if we're running on Windows"""
    if platform.system() != "Windows":
        print("WARNING: This script is designed for Windows but running on", platform.system())
        print("   The executable may not work properly on the target platform.")

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("ERROR: Python 3.8+ is required")
        sys.exit(1)

    print("Python version is compatible")

def check_windows_dlls():
    """Check for Windows-specific DLLs and dependencies"""
    print("Checking Windows DLLs and dependencies...")

    issues = []

    # Check for Visual C++ Redistributable
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

    # Check Java installation for JPype1
    java_home = os.environ.get("JAVA_HOME")
    if java_home and os.path.exists(java_home):
        print(f"   JAVA_HOME: {java_home}")

        # Check for jvm.dll
        jvm_paths = [
            Path(java_home) / "bin" / "server" / "jvm.dll",
            Path(java_home) / "bin" / "client" / "jvm.dll"
        ]

        jvm_found = None
        for path in jvm_paths:
            if path.exists():
                jvm_found = path
                break

        if jvm_found:
            print(f"   JVM DLL found: {jvm_found}")
        else:
            issues.append("JVM DLL not found")
            print("   ERROR: JVM DLL not found")
    else:
        issues.append("JAVA_HOME not set or invalid")
        print("   ERROR: JAVA_HOME not set or invalid")

    # Check for Qt/PySide6 DLLs
    try:
        import PySide6
        pyside6_path = Path(PySide6.__file__).parent
        qt_bin = pyside6_path / "Qt" / "bin"
        if qt_bin.exists():
            print(f"   Qt binaries found: {qt_bin}")
        else:
            issues.append("Qt binaries not found")
            print("   WARNING: Qt binaries location not standard")
    except ImportError:
        issues.append("PySide6 not installed")

    if issues:
        print("\nWARNING: Potential issues found:")
        for issue in issues:
            print(f"   - {issue}")
        print("\nRecommendations:")
        print("   - Install Visual C++ Redistributable 2015-2022")
        print("   - Install Java JDK and set JAVA_HOME")
        print("   - Ensure PySide6 is properly installed")
        print()

    return len(issues) == 0

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("[*] Checking dependencies...")

    required_packages = [
        'PyInstaller',
        'PySide6',
        'pandas',
        'openpyxl',
        'pdfplumber',
        'PyPDF2',
        'jpype1',
        'mpxj',
        'workalendar',
        'pathlib',
        'unicodedata'
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
        print("Please install them using:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False

    print("[OK] All dependencies are installed")
    return True

def check_source_files():
    """Check if all required source files exist"""
    print("[*] Checking source files...")

    project_root = find_project_root()
    src_dir = project_root / "src"

    required_files = [
        "main_window.py",
        "models.py",
        "table_views.py",
        "gantt_views.py",
        "delegates.py",
        "config_manager.py",
        "about_dialog.py",
        "file_gui.py",
        "filter_util.py",
        "pdf_extractor.py",
        "mpp_extractor.py",
        "xlsx_extractor.py",
        "pdf_security_checker.py",
        "xlsx_security_checker.py",
        "jvm_manager.py",
        "hipervinculo.py",
        "loading_animation_widget.py",
        "loading.html",
        "startup_manager.py",
        "command_system.py"
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
    """Clean previous build files"""
    print("[*] Cleaning previous build files...")

    project_root = find_project_root()

    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['*.spec']

    for dir_name in dirs_to_clean:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"   Removing {dir_name}/")
            shutil.rmtree(dir_path)

    # Clean spec files
    for spec_file in project_root.glob("*.spec"):
        print(f"   Removing {spec_file.name}")
        spec_file.unlink()

    # Clean pycache in src
    src_pycache = project_root / "src" / "__pycache__"
    if src_pycache.exists():
        print("   Removing src/__pycache__/")
        shutil.rmtree(src_pycache)

    print("[OK] Build files cleaned")

def create_main_entry_point():
    """Create the main entry point file"""
    project_root = find_project_root()
    src_dir = project_root / "src"

    main_content = '''#!/usr/bin/env python3
"""
Baby Project Manager - Main Entry Point
"""
import sys
import os

# Add src directory to Python path
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from PySide6.QtWidgets import QApplication
from main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(app.style().standardPalette())

    window = MainWindow()
    window.show()

    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
'''

    main_file = src_dir / "main.py"
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(main_content)

    return main_file

def get_pyside6_binaries():
    """Get PySide6 binary files for inclusion"""
    try:
        import PySide6
        pyside6_path = Path(PySide6.__file__).parent

        # Common Qt DLLs that need to be included
        qt_bin = pyside6_path / "Qt" / "bin"
        binaries = []

        if qt_bin.exists():
            # Essential Qt DLLs
            essential_dlls = [
                "Qt6Core.dll",
                "Qt6Gui.dll",
                "Qt6Widgets.dll",
                "Qt6WebEngineCore.dll",
                "Qt6WebEngineWidgets.dll",
                "Qt6Quick.dll",
                "Qt6Qml.dll",
                "Qt6Network.dll",
                "Qt6OpenGL.dll",
                "Qt6PrintSupport.dll"
            ]

            for dll in essential_dlls:
                dll_path = qt_bin / dll
                if dll_path.exists():
                    binaries.append((str(dll_path), "."))

        return binaries
    except ImportError:
        return []

def get_java_binaries():
    """Get Java binaries for inclusion"""
    java_home = os.environ.get("JAVA_HOME")
    if not java_home:
        return []

    binaries = []

    # Include jvm.dll
    jvm_paths = [
        Path(java_home) / "bin" / "server" / "jvm.dll",
        Path(java_home) / "bin" / "client" / "jvm.dll"
    ]

    for jvm_path in jvm_paths:
        if jvm_path.exists():
            binaries.append((str(jvm_path), "."))
            break

    # Include essential Java DLLs
    java_bin = Path(java_home) / "bin"
    if java_bin.exists():
        essential_java_dlls = [
            "java.dll",
            "verify.dll",
            "zip.dll",
            "net.dll",
            "nio.dll"
        ]

        for dll in essential_java_dlls:
            dll_path = java_bin / dll
            if dll_path.exists():
                binaries.append((str(dll_path), "."))

    return binaries

def create_spec_file(debug=False, onedir=False):
    """Create PyInstaller spec file"""
    print("[*] Creating PyInstaller spec file...")

    project_root = find_project_root()
    src_dir = project_root / "src"

    # Create main entry point
    main_file = create_main_entry_point()

    # Get additional binaries
    pyside6_binaries = get_pyside6_binaries()
    java_binaries = get_java_binaries()
    all_binaries = pyside6_binaries + java_binaries

    # Configure for onedir or onefile
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
    upx=True,
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

    # Build binaries list for spec file
    binaries_str = "[\n"
    for binary_path, dest in all_binaries:
        binaries_str += f"    (r'{binary_path}', '{dest}'),\n"
    binaries_str += "]"

    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(r"{src_dir}")
sys.path.insert(0, str(src_dir))

block_cipher = None

# Data files to include
datas = [
    (r"{src_dir / 'loading.html'}", "."),
]

# Binary files to include
binaries = {binaries_str}

# Hidden imports
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtWidgets',
    'PySide6.QtGui',
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebEngineCore',
    'PySide6.QtPrintSupport',
    'PySide6.QtNetwork',
    'PySide6.QtOpenGL',
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
    'winreg'
]

# Excluded modules
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
    'jupyter'
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
    debug=False if not debug else True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False if not debug else True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
){collect_block}
'''

    spec_file = project_root / "baby_project_manager.spec"
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print(f"[OK] Spec file created: {spec_file}")
    return spec_file

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
            error_message = f"Exit code {e.returncode}\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
        except Exception as e:
            error_occurred = True
            error_message = str(e)
        finally:
            done = True

    thread = threading.Thread(target=target)
    thread.start()

    i = 0
    while not done:
        sys.stdout.write(f"\r⏳ Build en progreso... {spinner[i % len(spinner)]}")
        sys.stdout.flush()
        time.sleep(0.2)
        i += 1

    if error_occurred:
        sys.stdout.write("\r❌ Build falló.                        \n")
        print(f"Error details:\n{error_message}")
        thread.join()
        raise subprocess.CalledProcessError(1, cmd)
    else:
        sys.stdout.write("\r[OK] Build finalizado.                      \n")

    thread.join()

def build_executable(spec_file, debug=False, build_distribution=False):
    """Build the executable using PyInstaller"""
    print("[*] Building executable...")

    project_root = find_project_root()

    # If building for distribution, set workpath and distpath inside distribution/
    if build_distribution:
        distribution_dir = project_root / "distribution"
        build_dir = distribution_dir / "build"
        dist_dir = distribution_dir / "dist"
        build_dir.mkdir(parents=True, exist_ok=True)
        dist_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            f"--workpath={build_dir}",
            f"--distpath={dist_dir}"
        ]
    else:
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm"
        ]

    if debug:
        cmd.append("--debug=all")

    cmd.append(str(spec_file))

    print(f"[*] Running: {' '.join(cmd[3:])}")
    print()

    try:
        run_with_spinner(cmd, cwd=str(project_root))
        print()
        print("[OK] Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print()
        print(f"[X] Build failed with exit code: {e.returncode}")
        return False

def test_executable():
    """Test the built executable"""
    print("🧪 Testing executable...")

    project_root = find_project_root()

    # Check for onedir vs onefile build
    exe_onefile = project_root / "dist" / "baby_project_manager.exe"
    exe_onedir = project_root / "dist" / "baby_project_manager" / "baby_project_manager.exe"

    exe_path = None
    if exe_onefile.exists():
        exe_path = exe_onefile
    elif exe_onedir.exists():
        exe_path = exe_onedir

    if not exe_path:
        print(f"❌ Executable not found in expected locations")
        return False

    print(f"📍 Executable location: {exe_path}")

    # Test basic execution (launch and close quickly)
    try:
        print("   Starting executable...")
        process = subprocess.Popen([str(exe_path)],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

        # Wait a moment for startup
        import time
        time.sleep(5)

        # Check if process is still running
        if process.poll() is None:
            print("   Application started successfully")
            # Terminate the process
            process.terminate()
            process.wait(timeout=10)
            print("✅ Executable test completed successfully")
            return True
        else:
            # Process exited, check output
            stdout, stderr = process.communicate()
            print(f"   Process exited with code: {process.returncode}")
            if stderr:
                print(f"   STDERR: {stderr.decode()}")
            return False

    except Exception as e:
        print(f"❌ Executable test failed: {e}")
        return False

def show_build_results(build_distribution=False):
    """Show build results and file information"""
    print("\n" + "=" * 80)
    print("🎉 BUILD COMPLETED!")
    print("=" * 80)

    project_root = find_project_root()
    if build_distribution:
        dist_dir = project_root / "distribution" / "dist"
    else:
        dist_dir = project_root / "dist"

    if not dist_dir.exists():
        print("❌ Dist directory not found!")
        return

    print(f"\n📁 Build Location: {dist_dir}")

    # Find executable
    exe_onefile = dist_dir / "baby_project_manager.exe"
    exe_onedir = dist_dir / "baby_project_manager" / "baby_project_manager.exe"

    exe_path = None
    bundle_type = None

    if exe_onefile.exists():
        exe_path = exe_onefile
        bundle_type = "One-file"
    elif exe_onedir.exists():
        exe_path = exe_onedir
        bundle_type = "One-directory"

    if exe_path:
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"🚀 Executable: {exe_path}")
        print(f"📦 Bundle Type: {bundle_type}")
        print(f"📏 Size: {size_mb:.1f} MB")

        # Show directory contents summary
        print(f"\n📦 Distribution Contents:")
        file_count = 0
        total_size = 0

        for item in dist_dir.rglob("*"):
            if item.is_file():
                file_count += 1
                total_size += item.stat().st_size

        total_size_mb = total_size / (1024 * 1024)
        print(f"   📄 Total files: {file_count}")
        print(f"   📏 Total size: {total_size_mb:.1f} MB")

    else:
        print("❌ Executable not found in dist directory")

    print(f"\n📋 Next Steps:")
    if exe_path:
        print(f"1. Test the executable: {exe_path}")
        print(f"2. The executable is standalone and portable")
        if bundle_type == "One-directory":
            print(f"3. Distribute the entire {exe_path.parent.name}/ folder")
        else:
            print(f"3. Distribute only the executable file")
        print(f"4. Ensure target systems have:")
        print(f"   - Visual C++ Redistributable 2015-2022")
        print(f"   - Java Runtime Environment (for MPP files)")

    print(f"\n✨ Baby Project Manager executable ready!")

def copy_to_dist():
    """Copy additional files to distribution directory if building for distribution"""
    # This function is now redundant since build/dist are created directly in distribution/
    # Kept for compatibility, but does nothing.
    pass

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Build Baby Project Manager Windows executable")
    parser.add_argument("--clean", action="store_true", help="Clean previous build files")
    parser.add_argument("--debug", action="store_true", help="Create executable with debug output")
    parser.add_argument("--onedir", action="store_true", help="Create one-directory bundle")
    parser.add_argument("--test", action="store_true", help="Test the built executable")
    parser.add_argument("--build-distribution", action="store_true", help="Build for distribution")

    args = parser.parse_args()

    print_banner()

    try:
        check_platform()
        check_python_version()

        # Find project root
        project_root = find_project_root()
        print(f"Project root: {project_root}")

        if not check_dependencies():
            sys.exit(1)

        # Check Windows-specific dependencies
        if not check_windows_dlls():
            print("WARNING: Windows dependency issues detected. Build may fail or executable may not work properly.")
            response = input("Continue anyway? (y/N): ").strip().lower()
            if response != 'y':
                print("Build cancelled.")
                sys.exit(1)

        if not check_source_files():
            sys.exit(1)

        if args.clean:
            clean_build_files()

        # Create spec file and build
        spec_file = create_spec_file(debug=args.debug, onedir=args.onedir)

        if not build_executable(spec_file, debug=args.debug, build_distribution=args.build_distribution):
            sys.exit(1)

        if args.test:
            if not test_executable():
                print("⚠️  Warning: Executable test failed, but build completed")

        # No need to copy_to_dist, as build/dist are created directly in distribution/
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
