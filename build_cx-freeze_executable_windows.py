#!/usr/bin/env python3
"""
Baby Project Manager - Build Windows Executable with cx_Freeze

This script builds the Baby Project Manager application into a standalone Windows executable
using cx_Freeze with all necessary dependencies and configurations.

Usage:
    python build_cx-freeze_executable_windows.py [options]

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
    print("🚀 BABY PROJECT MANAGER - WINDOWS EXECUTABLE BUILD (cx_Freeze)")
    print("=" * 80)
    print("Building standalone Windows executable with cx_Freeze")
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
        print("⚠️  Warning: This script is designed for Windows but running on", platform.system())
        print("   The executable may not work properly on the target platform.")

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)

    print("✅ Python version is compatible")

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("📦 Checking dependencies...")

    required_packages = [
        'cx_Freeze',
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
            if package == 'cx_Freeze':
                import cx_Freeze
                print(f"   ✅ {package}: {cx_Freeze.version}")
            elif package == 'PySide6':
                import PySide6
                print(f"   ✅ {package}: {PySide6.__version__}")
            elif package == 'pandas':
                import pandas
                print(f"   ✅ {package}: {pandas.__version__}")
            elif package == 'openpyxl':
                import openpyxl
                print(f"   ✅ {package}: {openpyxl.__version__}")
            elif package == 'pdfplumber':
                import pdfplumber
                print(f"   ✅ {package}: Found")
            elif package == 'PyPDF2':
                import PyPDF2
                print(f"   ✅ {package}: {PyPDF2.__version__}")
            elif package == 'jpype1':
                import jpype
                print(f"   ✅ {package}: {jpype.__version__}")
            elif package == 'mpxj':
                import mpxj
                print(f"   ✅ {package}: Found")
            elif package == 'workalendar':
                import workalendar
                print(f"   ✅ {package}: Found")
            else:
                __import__(package)
                print(f"   ✅ {package}: Found")
        except ImportError:
            print(f"   ❌ {package}: Not found")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Please install them using:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False

    print("✅ All dependencies are installed")
    return True

def check_source_files():
    """Check if all required source files exist"""
    print("📁 Checking source files...")

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
        "startup_manager.py"
    ]

    missing_files = []

    for file_name in required_files:
        file_path = src_dir / file_name
        if file_path.exists():
            print(f"   ✅ {file_name}")
        else:
            print(f"   ❌ {file_name}: Not found")
            missing_files.append(file_name)

    if missing_files:
        print(f"\n❌ Missing source files: {', '.join(missing_files)}")
        return False

    print("✅ All source files found")
    return True

def clean_build_files(build_dir=None, dist_dir=None):
    """Clean previous build files"""
    print("🧹 Cleaning previous build files...")

    project_root = find_project_root()

    # Determine which dirs to clean
    dirs_to_clean = []
    if build_dir is not None and dist_dir is not None:
        dirs_to_clean = [build_dir, dist_dir]
    else:
        dirs_to_clean = [project_root / 'build', project_root / 'dist', project_root / '__pycache__']

    for dir_path in dirs_to_clean:
        if isinstance(dir_path, str):
            dir_path = Path(dir_path)
        if dir_path.exists():
            print(f"   Removing {dir_path}/")
            shutil.rmtree(dir_path)

    # Clean setup files
    setup_file = project_root / "setup_cx_freeze.py"
    if setup_file.exists():
        print(f"   Removing {setup_file.name}")
        setup_file.unlink()

    # Clean pycache in src
    src_pycache = project_root / "src" / "__pycache__"
    if src_pycache.exists():
        print("   Removing src/__pycache__/")
        shutil.rmtree(src_pycache)

    print("✅ Build files cleaned")

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

def create_setup_file(debug=False, onedir=False, build_dir=None, dist_dir=None):
    """Create cx_Freeze setup file"""
    print("📄 Creating cx_Freeze setup file...")

    project_root = find_project_root()
    src_dir = project_root / "src"

    # Create main entry point
    main_file = create_main_entry_point()

    # Set build_exe path if provided
    build_exe_path = f'"{build_dir}"' if build_dir else 'None'

    setup_content = f'''#!/usr/bin/env python3
"""
cx_Freeze setup script for Baby Project Manager
"""

import sys
import os
from pathlib import Path
from cx_Freeze import setup, Executable

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Build options
build_options = {{
    "packages": [
        "PySide6.QtCore",
        "PySide6.QtWidgets",
        "PySide6.QtGui",
        "PySide6.QtWebEngineWidgets",
        "pandas",
        "openpyxl",
        "pdfplumber",
        "PyPDF2",
        "jpype1",
        "mpxj",
        "workalendar",
        "workalendar.america",
        "unicodedata",
        "ast",
        "configparser",
        "platform",
        "pathlib",
        "datetime",
        "math",
        "subprocess",
        "shutil",
        "re",
        "os",
        "sys"
    ],
    "excludes": [
        "tkinter",
        "unittest",
        "test",
        "distutils",
        "setuptools",
        "numpy.f2py",
        "numpy.distutils"
    ],
    "include_files": [
        (str(src_dir / "loading.html"), "loading.html"),
    ],
    "include_msvcrt": True,
    "optimize": 0 if {debug} else 2,
    "build_exe": {build_exe_path}
}}

# Base for executables
base = None
if sys.platform == "win32":
    base = "Console" if {debug} else "Win32GUI"

# Executable definition
executable = Executable(
    script=str(src_dir / "main.py"),
    base=base,
    target_name="baby_project_manager.exe",
    icon=None  # Add icon path here if available
)

# Setup configuration
setup(
    name="Baby Project Manager",
    version="1.0.0",
    description="Interactive Project Management Tool with Gantt Charts",
    author="Rafael Hernandez Bustamante",
    options={{"build_exe": build_options}},
    executables=[executable]
)
'''

    setup_file = project_root / "setup_cx_freeze.py"
    with open(setup_file, 'w', encoding='utf-8') as f:
        f.write(setup_content)

    print(f"✅ Setup file created: {setup_file}")
    return setup_file

def build_executable(setup_file, debug=False, build_dir=None):
    """Build the executable using cx_Freeze"""
    print("🔨 Building executable...")

    project_root = find_project_root()

    cmd = [
        sys.executable, str(setup_file), "build"
    ]

    if debug:
        cmd.extend(["--debug"])

    print(f"💻 Running: {' '.join(cmd)}")
    print()

    # Set environment variable for build_exe if needed
    env = os.environ.copy()
    if build_dir:
        env["CX_FREEZE_BUILD_EXE"] = str(build_dir)

    try:
        run_with_spinner(cmd, cwd=str(project_root))
        print()
        print("✅ Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print()
        print(f"❌ Build failed with exit code: {e.returncode}")
        return False

def test_executable():
    """Test the built executable"""
    print("🧪 Testing executable...")

    project_root = find_project_root()

    # cx_Freeze creates executable in build/exe.win-amd64-X.X/ directory
    build_dir = project_root / "build"
    if not build_dir.exists():
        print(f"❌ Build directory not found: {build_dir}")
        return False

    # Find the exe directory
    exe_dirs = list(build_dir.glob("exe.*"))
    if not exe_dirs:
        print(f"❌ No executable directory found in {build_dir}")
        return False

    exe_dir = exe_dirs[0]
    exe_path = exe_dir / "baby_project_manager.exe"

    if not exe_path.exists():
        print(f"❌ Executable not found: {exe_path}")
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
        time.sleep(3)

        # Terminate the process
        process.terminate()
        process.wait(timeout=5)

        print("✅ Executable test completed successfully")
        return True

    except Exception as e:
        print(f"❌ Executable test failed: {e}")
        return False

def show_build_results(build_dir=None):
    """Show build results and file information"""
    print("\n" + "=" * 80)
    print("🎉 BUILD COMPLETED!")
    print("=" * 80)

    project_root = find_project_root()
    build_dir = Path(build_dir) if build_dir else project_root / "build"

    if not build_dir.exists():
        print("❌ Build directory not found!")
        return

    print(f"\n📁 Build Location: {build_dir}")

    # Find executable directory
    exe_dirs = list(build_dir.glob("exe.*"))
    if not exe_dirs:
        print("❌ No executable directory found!")
        return

    exe_dir = exe_dirs[0]
    exe_path = exe_dir / "baby_project_manager.exe"

    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"🚀 Executable: {exe_path}")
        print(f"📏 Size: {size_mb:.1f} MB")

        # Show directory contents
        print(f"\n📦 Build Contents:")
        for item in sorted(exe_dir.rglob("*")):
            if item.is_file():
                rel_path = item.relative_to(exe_dir)
                size_kb = item.stat().st_size / 1024
                print(f"   📄 {rel_path} ({size_kb:.1f} KB)")
    else:
        print("❌ Executable not found in build directory")

    print(f"\n📋 Next Steps:")
    print(f"1. Test the executable: {exe_path}")
    print(f"2. The executable directory contains all dependencies")
    print(f"3. Distribute the entire exe directory")
    print(f"4. Ensure target systems have Visual C++ Redistributable")

    print(f"\n✨ Baby Project Manager executable ready!")

def copy_to_dist(build_dir=None, dist_dir=None):
    """Copy build results to distribution directory if building for distribution"""
    project_root = find_project_root()
    distribution_dir = project_root / "distribution"

    if not distribution_dir.exists():
        return

    print("📦 Copying to distribution directory...")

    build_dir = Path(build_dir) if build_dir else project_root / "build"
    exe_dirs = list(build_dir.glob("exe.*"))

    if not exe_dirs:
        print("❌ No executable directory found to copy")
        return

    exe_dir = exe_dirs[0]
    target_dist = distribution_dir / "dist"

    if target_dist.exists():
        shutil.rmtree(target_dist)

    shutil.copytree(exe_dir, target_dist)
    print(f"✅ Copied to: {target_dist}")

    # Copy build artifacts
    target_build = distribution_dir / "build"
    if target_build.exists():
        shutil.rmtree(target_build)
    shutil.copytree(build_dir, target_build)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Build Baby Project Manager Windows executable with cx_Freeze")
    parser.add_argument("--clean", action="store_true", help="Clean previous build files")
    parser.add_argument("--debug", action="store_true", help="Create executable with debug output")
    parser.add_argument("--onedir", action="store_true", help="Create one-directory bundle (cx_Freeze default)")
    parser.add_argument("--test", action="store_true", help="Test the built executable")
    parser.add_argument("--build-distribution", action="store_true", help="Build for distribution")

    args = parser.parse_args()

    print_banner()

    # Determine build/dist directories
    project_root = find_project_root()
    if args.build_distribution:
        distribution_dir = project_root / "distribution"
        build_dir = distribution_dir / "build"
        dist_dir = distribution_dir / "dist"
    else:
        build_dir = project_root / "build"
        dist_dir = project_root / "dist"

    try:
        check_platform()
        check_python_version()

        print(f"📁 Project root: {project_root}")

        if not check_dependencies():
            sys.exit(1)

        if not check_source_files():
            sys.exit(1)

        if args.clean:
            clean_build_files(build_dir=build_dir, dist_dir=dist_dir)

        # Create setup file and build
        setup_file = create_setup_file(debug=args.debug, onedir=args.onedir, build_dir=build_dir, dist_dir=dist_dir)

        if not build_executable(setup_file, debug=args.debug, build_dir=build_dir):
            sys.exit(1)

        if args.test:
            if not test_executable():
                print("⚠️  Warning: Executable test failed, but build completed")

        if args.build_distribution:
            copy_to_dist(build_dir=build_dir, dist_dir=dist_dir)

        show_build_results(build_dir=build_dir)

    except KeyboardInterrupt:
        print("\n❌ Build cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Build error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
