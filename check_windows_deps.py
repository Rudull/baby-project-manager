#!/usr/bin/env python3
"""
Windows Dependencies Checker for Baby Project Manager

This script checks for Windows-specific dependencies and provides
installation guidance for missing components.

Usage:
    python check_windows_deps.py [--fix]

Options:
    --fix    Attempt to automatically fix some issues
    --help   Show this help message

Author: Rafael Hernandez Bustamante
License: GPL-3.0
"""

import sys
import os
import platform
import subprocess
import argparse
from pathlib import Path
import urllib.request
import tempfile
import shutil

def print_banner():
    """Print the script banner"""
    print("=" * 70)
    print("🔍 BABY PROJECT MANAGER - WINDOWS DEPENDENCIES CHECKER")
    print("=" * 70)
    print("Checking Windows dependencies for building and running the application")
    print()

def check_windows():
    """Verify we're running on Windows"""
    if platform.system() != "Windows":
        print("❌ This script is designed for Windows only")
        print(f"   Current system: {platform.system()}")
        return False

    print(f"✅ Running on Windows {platform.release()}")
    return True

def check_python():
    """Check Python installation"""
    print("🐍 Checking Python installation...")

    version = sys.version_info
    print(f"   Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("   ❌ Python 3.8+ required")
        return False

    # Check if pip is available
    try:
        import pip
        print(f"   ✅ pip available")
    except ImportError:
        print("   ❌ pip not available")
        return False

    print("   ✅ Python installation OK")
    return True

def check_visual_cpp():
    """Check Visual C++ Redistributable"""
    print("🔧 Checking Visual C++ Redistributable...")

    try:
        import winreg

        # Check for different versions
        redistributables = [
            (r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64", "2015-2022 x64"),
            (r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x86", "2015-2022 x86"),
            (r"SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x64", "2015-2022 x64 (WOW64)"),
        ]

        found = False
        for reg_path, name in redistributables:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                version = winreg.QueryValueEx(key, "Version")[0]
                print(f"   ✅ Found {name}: {version}")
                winreg.CloseKey(key)
                found = True
            except (FileNotFoundError, OSError):
                continue

        if not found:
            print("   ❌ Visual C++ Redistributable 2015-2022 not found")
            print("   📥 Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe")
            return False

        return True

    except ImportError:
        print("   ❌ Cannot check registry (winreg not available)")
        return False

def check_java():
    """Check Java installation"""
    print("☕ Checking Java installation...")

    # Check JAVA_HOME
    java_home = os.environ.get("JAVA_HOME")
    if not java_home:
        print("   ❌ JAVA_HOME environment variable not set")

        # Try to find Java installation
        common_paths = [
            r"C:\Program Files\Java",
            r"C:\Program Files (x86)\Java",
            r"C:\Program Files\Eclipse Adoptium",
            r"C:\Program Files\Microsoft\jdk-*",
        ]

        java_found = False
        for path_pattern in common_paths:
            if '*' in path_pattern:
                # Handle wildcards
                import glob
                matches = glob.glob(path_pattern)
                if matches:
                    java_home = matches[0]
                    java_found = True
                    break
            else:
                path = Path(path_pattern)
                if path.exists():
                    # Find JDK directories
                    jdk_dirs = [d for d in path.iterdir() if d.is_dir() and 'jdk' in d.name.lower()]
                    if jdk_dirs:
                        java_home = str(jdk_dirs[0])
                        java_found = True
                        break

        if not java_found:
            print("   ❌ Java installation not found")
            print("   📥 Download from: https://adoptium.net/temurin/releases/")
            return False
        else:
            print(f"   ⚠️  Java found at: {java_home}")
            print("   ⚠️  Please set JAVA_HOME environment variable")
    else:
        print(f"   ✅ JAVA_HOME: {java_home}")

    # Check if JAVA_HOME path exists
    java_path = Path(java_home)
    if not java_path.exists():
        print(f"   ❌ JAVA_HOME path does not exist: {java_home}")
        return False

    # Check for jvm.dll
    jvm_paths = [
        java_path / "bin" / "server" / "jvm.dll",
        java_path / "bin" / "client" / "jvm.dll",
        java_path / "jre" / "bin" / "server" / "jvm.dll",
        java_path / "jre" / "bin" / "client" / "jvm.dll",
    ]

    jvm_found = None
    for jvm_path in jvm_paths:
        if jvm_path.exists():
            jvm_found = jvm_path
            break

    if jvm_found:
        print(f"   ✅ JVM DLL found: {jvm_found}")
    else:
        print("   ❌ JVM DLL not found")
        print("   💡 Make sure you have JDK (not just JRE) installed")
        return False

    # Check java command
    try:
        result = subprocess.run(['java', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stderr.split('\n')[0]
            print(f"   ✅ Java command available: {version_line}")
        else:
            print("   ❌ Java command not working")
            return False
    except FileNotFoundError:
        print("   ❌ Java command not found in PATH")
        print("   💡 Add Java bin directory to PATH")
        return False

    return True

def check_python_packages():
    """Check required Python packages"""
    print("📦 Checking Python packages...")

    required_packages = [
        'PySide6',
        'PyInstaller',
        'pandas',
        'openpyxl',
        'pdfplumber',
        'PyPDF2',
        'jpype1',
        'mpxj',
        'workalendar',
    ]

    missing_packages = []

    for package in required_packages:
        try:
            if package == 'PySide6':
                import PySide6
                print(f"   ✅ {package}: {PySide6.__version__}")

                # Check for Qt DLLs
                pyside6_path = Path(PySide6.__file__).parent
                qt_bin = pyside6_path / "Qt" / "bin"
                if qt_bin.exists():
                    print(f"      Qt binaries: {qt_bin}")
                else:
                    print(f"      ⚠️  Qt binaries not found")

            elif package == 'PyInstaller':
                import PyInstaller
                print(f"   ✅ {package}: {PyInstaller.__version__}")
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
        print(f"\n   Missing packages: {', '.join(missing_packages)}")
        print(f"   Install with: pip install {' '.join(missing_packages)}")
        return False

    print("   ✅ All required packages found")
    return True

def check_build_tools():
    """Check build tools availability"""
    print("🔨 Checking build tools...")

    # Check if we can import build modules
    build_tools = [
        ('PyInstaller', 'PyInstaller'),
        ('cx_Freeze', 'cx_Freeze'),
    ]

    available_tools = []

    for tool_name, module_name in build_tools:
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', 'Unknown')
            print(f"   ✅ {tool_name}: {version}")
            available_tools.append(tool_name)
        except ImportError:
            print(f"   ❌ {tool_name}: Not available")

    if not available_tools:
        print("   ❌ No build tools available")
        return False

    return True

def check_disk_space():
    """Check available disk space"""
    print("💾 Checking disk space...")

    try:
        import shutil
        free_bytes = shutil.disk_usage('.').free
        free_gb = free_bytes / (1024 ** 3)

        print(f"   Available space: {free_gb:.1f} GB")

        if free_gb < 2:
            print("   ❌ Insufficient disk space (need at least 2 GB)")
            return False
        elif free_gb < 5:
            print("   ⚠️  Low disk space (recommended: 5+ GB)")
        else:
            print("   ✅ Sufficient disk space")

        return True

    except Exception as e:
        print(f"   ❌ Cannot check disk space: {e}")
        return False

def try_fix_java_home():
    """Try to automatically set JAVA_HOME"""
    print("🔧 Attempting to fix JAVA_HOME...")

    # Search for Java installations
    search_paths = [
        r"C:\Program Files\Java",
        r"C:\Program Files (x86)\Java",
        r"C:\Program Files\Eclipse Adoptium",
        r"C:\Program Files\Microsoft",
    ]

    java_installations = []

    for search_path in search_paths:
        path = Path(search_path)
        if path.exists():
            for item in path.iterdir():
                if item.is_dir():
                    # Check if it looks like a JDK
                    if any(keyword in item.name.lower() for keyword in ['jdk', 'java']):
                        # Verify it has necessary files
                        jvm_paths = [
                            item / "bin" / "server" / "jvm.dll",
                            item / "bin" / "client" / "jvm.dll",
                        ]
                        if any(p.exists() for p in jvm_paths):
                            java_installations.append(item)

    if not java_installations:
        print("   ❌ No Java installations found")
        return False

    # Use the first (presumably newest) installation
    java_home = str(java_installations[0])
    print(f"   Found Java installation: {java_home}")

    # Set environment variable for current session
    os.environ['JAVA_HOME'] = java_home
    print(f"   ✅ JAVA_HOME set for current session: {java_home}")

    # Provide instructions for permanent setting
    print("   💡 To set permanently, run as administrator:")
    print(f'   setx JAVA_HOME "{java_home}" /M')

    return True

def download_and_install_vcredist():
    """Download and install Visual C++ Redistributable"""
    print("🔧 Downloading Visual C++ Redistributable...")

    url = "https://aka.ms/vs/17/release/vc_redist.x64.exe"

    try:
        # Download to temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            installer_path = Path(temp_dir) / "vc_redist.x64.exe"

            print("   Downloading...")
            urllib.request.urlretrieve(url, installer_path)
            print(f"   Downloaded to: {installer_path}")

            # Run installer
            print("   Running installer...")
            result = subprocess.run([str(installer_path), '/quiet'],
                                  capture_output=True, text=True)

            if result.returncode == 0:
                print("   ✅ Visual C++ Redistributable installed successfully")
                return True
            else:
                print(f"   ❌ Installation failed: {result.stderr}")
                print("   💡 Try running manually as administrator")
                return False

    except Exception as e:
        print(f"   ❌ Download/install failed: {e}")
        print("   💡 Download manually from: https://aka.ms/vs/17/release/vc_redist.x64.exe")
        return False

def generate_report(results):
    """Generate a summary report"""
    print("\n" + "=" * 70)
    print("📋 DEPENDENCY CHECK SUMMARY")
    print("=" * 70)

    categories = [
        ("Windows", results.get('windows', False)),
        ("Python", results.get('python', False)),
        ("Visual C++", results.get('visual_cpp', False)),
        ("Java", results.get('java', False)),
        ("Python Packages", results.get('packages', False)),
        ("Build Tools", results.get('build_tools', False)),
        ("Disk Space", results.get('disk_space', False)),
    ]

    all_good = True
    critical_issues = []
    warnings = []

    for category, status in categories:
        if status:
            print(f"✅ {category}: OK")
        else:
            print(f"❌ {category}: ISSUES")
            all_good = False
            if category in ['Windows', 'Python', 'Visual C++']:
                critical_issues.append(category)
            else:
                warnings.append(category)

    print()

    if all_good:
        print("🎉 All dependencies are satisfied!")
        print("You should be able to build and run Baby Project Manager successfully.")
    else:
        if critical_issues:
            print("❌ Critical issues found:")
            for issue in critical_issues:
                print(f"   - {issue}")

        if warnings:
            print("⚠️  Warnings:")
            for warning in warnings:
                print(f"   - {warning}")

        print("\n💡 Recommendations:")
        if 'Visual C++' in critical_issues:
            print("   1. Install Visual C++ Redistributable 2015-2022")
            print("      Download: https://aka.ms/vs/17/release/vc_redist.x64.exe")

        if 'Java' in warnings:
            print("   2. Install Java JDK and set JAVA_HOME")
            print("      Download: https://adoptium.net/temurin/releases/")

        if 'Python Packages' in warnings:
            print("   3. Install missing Python packages:")
            print("      pip install -r requirements.txt")

        print("   4. Re-run this script after fixing issues")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Check Windows dependencies for Baby Project Manager")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix some issues automatically")

    args = parser.parse_args()

    print_banner()

    results = {}

    # Run all checks
    results['windows'] = check_windows()
    if not results['windows']:
        generate_report(results)
        return 1

    results['python'] = check_python()
    results['visual_cpp'] = check_visual_cpp()
    results['java'] = check_java()
    results['packages'] = check_python_packages()
    results['build_tools'] = check_build_tools()
    results['disk_space'] = check_disk_space()

    # Try to fix issues if requested
    if args.fix:
        print("\n🔧 ATTEMPTING AUTOMATIC FIXES")
        print("=" * 40)

        if not results['java']:
            if try_fix_java_home():
                # Re-check Java
                results['java'] = check_java()

        if not results['visual_cpp']:
            print("\n⚠️  Visual C++ Redistributable installation requires administrator privileges")
            response = input("Attempt to download and install? (y/N): ").strip().lower()
            if response == 'y':
                if download_and_install_vcredist():
                    # Re-check Visual C++
                    results['visual_cpp'] = check_visual_cpp()

    # Generate final report
    generate_report(results)

    # Return appropriate exit code
    critical_failed = not all([
        results['windows'],
        results['python'],
        results['visual_cpp']
    ])

    return 1 if critical_failed else 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
