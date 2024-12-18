# setup.py
import sys
from cx_Freeze import setup, Executable
import os

build_exe_options = {
    "packages": [
        "os", 
        "sys",
        "PySide6",
        "workalendar",
        "gantt_views",
        "models",
        "table_views",
        "about_dialog"
    ],
    "include_files": [
        ("src/", "src/"),
        ("src/loading.gif", "src/loading.gif")
    ],
    "path": ["src/"] + sys.path
}

base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="BabyProjectManager",
    version="1.0",
    description="Gestor de Proyectos",
    options={"build_exe": build_exe_options},
    executables=[Executable(
        os.path.join("src", "main_window.py"),
        base=base,
        target_name="BabyProjectManager.exe"
    )]
)