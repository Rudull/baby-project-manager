#!/usr/bin/env python3
"""
Baby Project Manager - Build Linux Executable

This script builds the Baby Project Manager application into a standalone Linux executable
using PyInstaller with all necessary dependencies and configurations.

Usage:
    python build_executable_linux.py [options]

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
    print("🚀 BABY PROJECT MANAGER - LINUX EXECUTABLE BUILD")
    print("=" * 80)
    print("Building standalone Linux executable with PyInstaller")
    print()

def check_platform():
    import platform
    if platform.system().lower() not in ["linux", "darwin"]:
        print(f"⚠️  Warning: This script is designed for Linux/macOS but running on {platform.system()}")

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
                print(f"   ✅ {package}: {PyInstaller.__version__}")
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

def clean_build_files():
    """Clean previous build files"""
    print("🧹 Cleaning previous build files...")

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

    print("✅ Build files cleaned")

def ensure_clean_dist():
    """Ensure dist directory is clean"""
    project_root = find_project_root()
    dist_dir = project_root / "dist"

    if dist_dir.exists():
        print("🧹 Cleaning existing dist directory...")
        shutil.rmtree(dist_dir)

    dist_dir.mkdir(exist_ok=True)
    print("✅ Dist directory prepared")

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

def create_spec_file(debug=False, onedir=False):
    """Create PyInstaller spec file"""
    print("📄 Creating PyInstaller spec file...")

    project_root = find_project_root()
    src_dir = project_root / "src"

    # Create main entry point
    main_file = create_main_entry_point()

    # Different configuration for one-file vs one-dir
    if onedir:
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

# Hidden imports
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtWidgets',
    'PySide6.QtGui',
    'PySide6.QtWebEngineWidgets',
    'pandas',
    'openpyxl',
    'pdfplumber',
    'PyPDF2',
    'jpype1',
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
    'sys'
]

a = Analysis(
    [r"{main_file}"],
    pathex=[r"{src_dir}"],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='baby_project_manager',
    debug={debug},
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console={debug},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='baby_project_manager',
)
'''
    else:
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

# Hidden imports
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtWidgets',
    'PySide6.QtGui',
    'PySide6.QtWebEngineWidgets',
    'pandas',
    'openpyxl',
    'pdfplumber',
    'PyPDF2',
    'jpype1',
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
    'sys'
]

a = Analysis(
    [r"{main_file}"],
    pathex=[r"{src_dir}"],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='baby_project_manager',
    debug={debug},
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console={debug},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''

    spec_file = project_root / "baby_project_manager.spec"
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print(f"✅ Spec file created: {spec_file}")
    return spec_file

import threading
import time

def run_with_spinner(cmd, cwd=None):
    spinner = ['|', '/', '-', '\\']
    done = False

    def target():
        nonlocal done
        try:
            subprocess.run(cmd, cwd=cwd, check=True)
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
    sys.stdout.write("\r✅ Build finalizado.                      \n")
    thread.join()

def build_executable(spec_file, debug=False, build_dir=None, dist_dir=None):
    """Build the executable using PyInstaller"""
    print("🔨 Building executable...")

    project_root = find_project_root()

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm"
    ]

    # Add custom build/dist dirs if provided
    if build_dir:
        cmd += ["--workpath", str(build_dir)]
    if dist_dir:
        cmd += ["--distpath", str(dist_dir)]

    if debug:
        cmd.append("--debug=all")

    cmd.append(str(spec_file))

    print(f"💻 Running: {' '.join(cmd[3:])}")
    print()

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

    # Check for both possible locations
    exe_path_onefile = project_root / "dist" / "baby_project_manager"
    exe_path_onedir = project_root / "dist" / "baby_project_manager" / "baby_project_manager"

    exe_path = None
    if exe_path_onefile.exists():
        exe_path = exe_path_onefile
    elif exe_path_onedir.exists():
        exe_path = exe_path_onedir

    if not exe_path:
        print(f"❌ Executable not found in expected locations")
        return False

    print(f"📍 Executable location: {exe_path}")

    # Make executable
    os.chmod(exe_path, 0o755)

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

def show_build_results():
    """Show build results and file information"""
    print("\n" + "=" * 80)
    print("🎉 BUILD COMPLETED!")
    print("=" * 80)

    project_root = find_project_root()
    dist_dir = project_root / "dist"

    if not dist_dir.exists():
        print("❌ Dist directory not found!")
        return

    print(f"\n📁 Build Location: {dist_dir}")

    # Find executable
    exe_path_onefile = dist_dir / "baby_project_manager"
    exe_path_onedir = dist_dir / "baby_project_manager" / "baby_project_manager"

    exe_path = None
    if exe_path_onefile.exists():
        exe_path = exe_path_onefile
        bundle_type = "One-file"
    elif exe_path_onedir.exists():
        exe_path = exe_path_onedir
        bundle_type = "One-directory"

    if exe_path:
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"🚀 Executable: {exe_path}")
        print(f"📦 Bundle Type: {bundle_type}")
        print(f"📏 Size: {size_mb:.1f} MB")

        # Make executable
        os.chmod(exe_path, 0o755)
        print("✅ Executable permissions set")

        # Show directory contents
        print(f"\n📦 Distribution Contents:")
        for item in sorted(dist_dir.rglob("*")):
            if item.is_file():
                rel_path = item.relative_to(dist_dir)
                size_kb = item.stat().st_size / 1024
                print(f"   📄 {rel_path} ({size_kb:.1f} KB)")
    else:
        print("❌ Executable not found in dist directory")

    print(f"\n📋 Next Steps:")
    if exe_path:
        print(f"1. Test the executable: {exe_path}")
        print(f"2. The executable is standalone and portable")
        if bundle_type == "One-directory":
            print(f"3. Distribute the entire dist/baby_project_manager/ folder")
        else:
            print(f"3. Distribute only the executable file")
        print(f"4. Ensure target systems have required system libraries")

    print(f"\n✨ Baby Project Manager executable ready!")

def copy_to_dist():
    """Copy additional files to distribution directory if building for distribution"""
    project_root = find_project_root()
    distribution_dir = project_root / "distribution"

    if not distribution_dir.exists():
        return

    print("📦 Copying to distribution directory...")

    dist_dir = project_root / "dist"
    target_dist = distribution_dir / "dist"

    if target_dist.exists():
        shutil.rmtree(target_dist)

    shutil.copytree(dist_dir, target_dist)
    print(f"✅ Copied to: {target_dist}")

    # Copy build artifacts
    build_dir = project_root / "build"
    if build_dir.exists():
        target_build = distribution_dir / "build"
        if target_build.exists():
            shutil.rmtree(target_build)
        shutil.copytree(build_dir, target_build)

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
        print(f"📁 Project root: {project_root}")

        if not check_dependencies():
            sys.exit(1)

        if not check_source_files():
            sys.exit(1)

        if args.clean:
            clean_build_files()

        # Determine build/dist output directories
        if args.build_distribution:
            distribution_dir = project_root / "distribution"
            build_dir = distribution_dir / "build"
            dist_dir = distribution_dir / "dist"
            # Ensure directories exist
            build_dir.mkdir(parents=True, exist_ok=True)
            dist_dir.mkdir(parents=True, exist_ok=True)
        else:
            build_dir = None
            dist_dir = None

        # Create spec file and build
        spec_file = create_spec_file(debug=args.debug, onedir=args.onedir)

        if not build_executable(spec_file, debug=args.debug, build_dir=build_dir, dist_dir=dist_dir):
            sys.exit(1)

        if args.test:
            if not test_executable():
                print("⚠️  Warning: Executable test failed, but build completed")

        if args.build_distribution:
            # No need to copy, already built in distribution/
            pass

        show_build_results()

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
