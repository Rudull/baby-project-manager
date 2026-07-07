#!/usr/bin/env python3
"""
Baby Project Manager - Build Windows Executable (Nuitka)

This script builds the Baby Project Manager application into a standalone Windows executable
using Nuitka with all necessary dependencies and configurations.

Usage:
    python build_nuitka_windows.py [options]

Options:
    --clean                 Clean previous build files before building
    --debug                 Create executable with debug output and console
    --onedir                Create one-directory bundle (default)
    --onefile               Create one-file executable
    --test                  Test the built executable after creation
    --build-distribution    Build for distribution directory
    --help                  Show this help message

Author: Rafael Hernandez Bustamante
License: GPL-3.0
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def print_banner():
    print("=" * 80)
    print("BABY PROJECT MANAGER - WINDOWS EXECUTABLE BUILD (NUITKA)")
    print("=" * 80)
    print("Building standalone Windows executable with Nuitka")
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


def check_dependencies():
    print("[*] Checking dependencies...")
    required_packages = [
        "nuitka",
        "ordered_set",
        "zstandard",
        "PySide6",
        "pandas",
        "openpyxl",
        "pdfplumber",
        "PyPDF2",
        "jpype1",
        "mpxj",
        "workalendar",
        "pathlib",
    ]
    missing_packages = []
    for package in required_packages:
        try:
            if package == "nuitka":
                import nuitka
                try:
                    import importlib.metadata
                    version = importlib.metadata.version("nuitka")
                except ImportError:
                    version = "Found"
                print(f"   [OK] {package}: {version}")
            elif package == "PySide6":
                import PySide6
                print(f"   [OK] {package}: {PySide6.__version__}")
            elif package == "pandas":
                import pandas
                print(f"   [OK] {package}: {pandas.__version__}")
            elif package == "openpyxl":
                import openpyxl
                print(f"   [OK] {package}: {openpyxl.__version__}")
            elif package == "pdfplumber":
                import pdfplumber
                print(f"   [OK] {package}: Found")
            elif package == "PyPDF2":
                import PyPDF2
                print(f"   [OK] {package}: {PyPDF2.__version__}")
            elif package == "jpype1":
                import jpype
                print(f"   [OK] {package}: {jpype.__version__}")
            elif package == "mpxj":
                import mpxj
                print(f"   [OK] {package}: Found")
            elif package == "workalendar":
                import workalendar
                print(f"   [OK] {package}: Found")
            else:
                __import__(package)
                print(f"   [OK] {package}: Found")
        except ImportError:
            print(f"   [X] {package}: Not found")
            missing_packages.append(package.replace("_", "-"))

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
    required_files = ["main.py", "version.py", "ui/main_window.py"]
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

    dirs_to_clean = [
        "build", "dist", "__pycache__",
        "main.build", "main.dist", "main.onefile-build",
        "baby_project_manager.build", "baby_project_manager.dist",
        "baby_project_manager.onefile-build",
    ]

    for dir_name in dirs_to_clean:
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

    for file_ext in ["*.spec", "*.cmd"]:
        for file_to_clean in project_root.glob(file_ext):
            print(f"   Removing {file_to_clean.name}")
            try:
                file_to_clean.unlink()
            except Exception as e:
                print(f"   [!] Warning: Could not remove {file_to_clean.name}: {e}")

    src_pycache = project_root / "src" / "__pycache__"
    if src_pycache.exists():
        print("   Removing src/__pycache__/")
        try:
            shutil.rmtree(src_pycache, onerror=handle_remove_readonly)
        except Exception:
            pass

    print("[OK] Build files cleaned")


def get_java_include_args():
    """Build Nuitka --include-data-files args for Java JVM DLLs."""
    java_home = os.environ.get("JAVA_HOME")
    if not java_home:
        return []
    args = []
    java_home_path = Path(java_home)
    for jvm_rel in ["bin/server/jvm.dll", "bin/client/jvm.dll"]:
        jvm_path = java_home_path / jvm_rel
        if jvm_path.exists():
            args.append(f"--include-data-files={jvm_path}=jvm.dll")
            break
    java_bin = java_home_path / "bin"
    if java_bin.exists():
        for dll in ["java.dll", "verify.dll", "zip.dll", "net.dll", "nio.dll"]:
            dll_path = java_bin / dll
            if dll_path.exists():
                args.append(f"--include-data-files={dll_path}={dll}")
    return args


def run_command_with_output(cmd, cwd=None):
    try:
        process = subprocess.run(cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError:
        raise
    except Exception as e:
        print(f"Error starting process: {e}")
        raise


def build_executable(debug=False, onedir=True, onefile=False, build_distribution=False):
    print("[*] Building executable with Nuitka...")
    project_root = find_project_root()
    src_dir = project_root / "src"
    main_file = src_dir / "main.py"

    if build_distribution:
        distribution_dir = project_root / "distribution"
        build_dir = distribution_dir / "build"
        dist_dir = distribution_dir / "dist"
        build_dir.mkdir(parents=True, exist_ok=True)
        dist_dir.mkdir(parents=True, exist_ok=True)
        output_dir = dist_dir
    else:
        output_dir = project_root / "dist"
        output_dir.mkdir(parents=True, exist_ok=True)

    env_file = project_root / ".env"

    cmd = [
        sys.executable, "-m", "nuitka",
        "--onefile" if onefile and not onedir else "--standalone",
        "--output-filename=baby_project_manager.exe",
        f"--windows-icon-from-ico={project_root / 'assets' / 'icono.ico'}",
        "--windows-company-name=Rafael Hernandez Bustamante",
        "--windows-product-name=Baby Project Manager",
        "--windows-product-version=1.0.0",
        # Data
        f"--include-data-dir={project_root / 'assets'}=assets",
        f"--include-data-files={src_dir / 'templates' / 'loading.html'}=templates/loading.html",
        # Modules
        "--include-module=PySide6.QtCore",
        "--include-module=PySide6.QtWidgets",
        "--include-module=PySide6.QtGui",
        "--include-module=PySide6.QtWebEngineWidgets",
        "--include-module=PySide6.QtWebEngineCore",
        "--include-module=PySide6.QtPrintSupport",
        "--include-module=PySide6.QtNetwork",
        "--include-package=pandas",
        "--include-package=openpyxl",
        "--include-package=pdfplumber",
        "--include-package=PyPDF2",
        "--include-package=jpype",
        "--include-package=mpxj",
        "--include-package=workalendar",
        "--include-package=requests",
        "--include-package=urllib3",
        # Plugins
        "--enable-plugin=pyside6",
        # Excludes
        "--nofollow-import-to=tkinter",
        "--nofollow-import-to=distutils",
        "--nofollow-import-to=setuptools",
        "--nofollow-import-to=IPython",
        "--nofollow-import-to=jupyter",
        "--nofollow-import-to=matplotlib",
        "--nofollow-import-to=scipy",
        "--nofollow-import-to=PySide6.Qt3DCore",
        "--nofollow-import-to=PySide6.Qt3DRender",
        "--nofollow-import-to=PySide6.QtMultimedia",
        "--nofollow-import-to=PySide6.QtQuick",
        "--nofollow-import-to=PySide6.QtQml",
        "--nofollow-import-to=PySide6.QtOpenGL",
        "--nofollow-import-to=http.server",
        "--nofollow-import-to=xmlrpc",
        # Output
        f"--output-dir={output_dir}",
        "--assume-yes-for-downloads",
    ]

    # Include .env if present
    if env_file.exists():
        cmd.append(f"--include-data-files={env_file}=.env")

    # Include Java JVM DLLs
    cmd.extend(get_java_include_args())

    if not debug:
        cmd.append("--windows-console-mode=disable")

    cmd.append(str(main_file))

    print(f"[*] Running Nuitka build...")
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

    # Nuitka standalone creates baby_project_manager.dist/ or main.dist/
    exe_onefile = dist_dir / "baby_project_manager.exe"
    exe_standalone = dist_dir / "baby_project_manager.dist" / "baby_project_manager.exe"
    exe_standalone_alt = dist_dir / "main.dist" / "baby_project_manager.exe"

    exe_path = None
    if exe_onefile.exists():
        exe_path = exe_onefile
    elif exe_standalone.exists():
        exe_path = exe_standalone
    elif exe_standalone_alt.exists():
        exe_path = exe_standalone_alt

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
    exe_standalone = dist_dir / "baby_project_manager.dist" / "baby_project_manager.exe"
    exe_standalone_alt = dist_dir / "main.dist" / "baby_project_manager.exe"

    exe_path = None
    bundle_type = None
    if exe_onefile.exists():
        exe_path, bundle_type = exe_onefile, "One-file"
    elif exe_standalone.exists():
        exe_path, bundle_type = exe_standalone, "One-directory"
    elif exe_standalone_alt.exists():
        exe_path, bundle_type = exe_standalone_alt, "One-directory"

    if exe_path:
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"Executable: {exe_path}")
        print(f"Bundle Type: {bundle_type}")
        print(f"Size: {size_mb:.1f} MB")
    else:
        print("Executable not found in dist directory")
        print("Tip: Nuitka may have created a .dist subfolder — check the dist/ directory.")


def main():
    parser = argparse.ArgumentParser(description="Build Baby Project Manager Windows executable with Nuitka")
    parser.add_argument("--clean", action="store_true", help="Clean previous build files")
    parser.add_argument("--debug", action="store_true", help="Create executable with debug output")
    parser.add_argument("--onedir", action="store_true", help="Create one-directory bundle (default unless --onefile)")
    parser.add_argument("--onefile", action="store_true", help="Create one-file bundle")
    parser.add_argument("--test", action="store_true", help="Test the built executable")
    parser.add_argument("--build-distribution", action="store_true", help="Build for distribution")
    args = parser.parse_args()

    # Nuitka defaults to standalone (onedir) if not onefile
    onedir = not args.onefile

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

        if not build_executable(
            debug=args.debug,
            onedir=onedir,
            onefile=args.onefile,
            build_distribution=args.build_distribution,
        ):
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
