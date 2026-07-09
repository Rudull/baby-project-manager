#!/usr/bin/env python3
"""
Baby Project Manager - Build Linux Executable (PyInstaller)

This script builds the Baby Project Manager application into a standalone Linux executable
using PyInstaller with all necessary dependencies and configurations.

Usage:
    python build_pyinstaller_linux.py [options]

Options:
    --clean                 Clean previous build files before building
    --debug                 Create executable with debug output and console
    --onedir               Create one-directory bundle instead of one-file
    --onefile              Create one-file executable (default)
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


def print_banner():
    print("=" * 80)
    print("BABY PROJECT MANAGER - LINUX EXECUTABLE BUILD (PYINSTALLER)")
    print("=" * 80)
    print("Building standalone Linux executable with PyInstaller")
    print()


def check_platform():
    if platform.system().lower() not in ["linux", "darwin"]:
        print(f"Warning: This script is designed for Linux/macOS but running on {platform.system()}")


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


def check_python_version():
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("Python 3.8+ is required")
        sys.exit(1)
    print("Python version is compatible")


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
        "templates/loading.html", "utils/startup_manager.py",
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
            shutil.rmtree(src_pycache)
        except Exception:
            pass

    print("[OK] Build files cleaned")


def get_conda_binaries():
    """Bundle critical libs from Conda environment to avoid symbol mismatches."""
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if not conda_prefix or platform.system().lower() != "linux":
        return []
    conda_lib_path = Path(conda_prefix) / "lib"
    binaries = []
    for lib_name in ["libexpat.so.1", "libssl.so.3", "libcrypto.so.3"]:
        lib_path = conda_lib_path / lib_name
        if lib_path.exists():
            print(f"   Found Conda {lib_name}: {lib_path}")
            binaries.append((str(lib_path), "."))
    return binaries


def create_spec_file(debug=False, onedir=False):
    print("[*] Creating PyInstaller spec file...")
    project_root = find_project_root()
    src_dir = project_root / "src"
    main_file = src_dir / "main.py"

    binaries = get_conda_binaries()
    binaries_str = "[\n"
    for binary_path, dest in binaries:
        binaries_str += f"    (r'{binary_path}', '{dest}'),\n"
    binaries_str += "]"

    env_file = project_root / ".env"
    datas_env = f'    (r"{env_file}", "."),\n' if env_file.exists() else ""

    if onedir:
        exe_block = """
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
""".format(debug=debug)
    else:
        exe_block = """
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
""".format(debug=debug)

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
    'pkg_resources',
    'ssl',
    'hashlib',
    'socket',
    'requests',
    'urllib3',
]

excludes = [
    'tkinter',
    'unittest',
    'test',
    'matplotlib',
    'scipy',
    'IPython',
    'jupyter',
]
# NOTE: Do NOT exclude 'setuptools' / 'distutils' on Linux.
# pkg_resources (pulled in via hiddenimports and the pyi_rth_pkgres runtime
# hook) imports jaraco.text, which lives in setuptools._vendor.jaraco.
# Excluding setuptools strips that vendored jaraco, causing a startup crash:
#   ModuleNotFoundError: No module named 'jaraco'
# The app never opens (silent failure on double-click).

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
{exe_block}'''

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

    exe_onefile = dist_dir / "baby_project_manager"
    exe_onedir = dist_dir / "baby_project_manager" / "baby_project_manager"

    exe_path = None
    if exe_onefile.exists() and exe_onefile.is_file():
        exe_path = exe_onefile
    elif exe_onedir.exists():
        exe_path = exe_onedir

    if not exe_path:
        print(f"Executable not found in expected locations: {dist_dir}")
        return False

    print(f"Executable location: {exe_path}")
    os.chmod(exe_path, 0o755)

    try:
        print("   Starting executable...")
        process = subprocess.Popen([str(exe_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        import time
        time.sleep(3)
        process.terminate()
        process.wait(timeout=5)
        print("Executable test completed successfully")
        return True
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

    exe_onefile = dist_dir / "baby_project_manager"
    exe_onedir = dist_dir / "baby_project_manager" / "baby_project_manager"

    exe_path = None
    bundle_type = None
    if exe_onefile.exists() and exe_onefile.is_file():
        exe_path, bundle_type = exe_onefile, "One-file"
    elif exe_onedir.exists():
        exe_path, bundle_type = exe_onedir, "One-directory"

    if exe_path:
        os.chmod(exe_path, 0o755)
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"Executable: {exe_path}")
        print(f"Bundle Type: {bundle_type}")
        print(f"Size: {size_mb:.1f} MB")
    else:
        print("Executable not found in dist directory")


def main():
    parser = argparse.ArgumentParser(description="Build Baby Project Manager Linux executable (PyInstaller)")
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

        # Package a onedir build into a .tar.gz release asset for the auto-updater.
        if args.onedir:
            try:
                sys.path.insert(0, str(Path(__file__).resolve().parent))
                from release_packaging import package_onedir
                dist_dir = (project_root / "distribution" / "dist"
                            if args.build_distribution else project_root / "dist")
                package_onedir(dist_dir, project_root)
            except Exception as e:
                print(f"[!] Release packaging failed (build is fine): {e}")

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
