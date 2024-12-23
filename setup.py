# setup.py
import sys
from cx_Freeze import setup, Executable
import os

build_exe_options = {
    "packages": [
        "os",
        "sys",
        "PySide6",
        "PySide6.QtWebEngineWidgets", 
        "PySide6.QtWebEngineCore",
        "workalendar",
        "gantt_views",
        "models",
        "table_views",
        "about_dialog"
    ],
    "include_files": [
        ("src/", "src/"),
        ("src/loading.html", "src/loading.html")
    ],
    "path": ["src/"] + sys.path
}

base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="BabyProjectManager",
    version="0.1.2",
    description="Gestor de Proyectos",
    options={"build_exe": build_exe_options},
    executables=[Executable(
        os.path.join("src", "main_window.py"),
        base=base,
        target_name="BabyProjectManager.exe"
    )]
)