import os
import sys
from pathlib import Path


def _is_nuitka_compiled() -> bool:
    """Check if running as a Nuitka-compiled program (Nuitka injects this name into every compiled module)."""
    return "__compiled__" in globals()

def get_resource_path(relative_path: str) -> Path:
    """
    Get the absolute path to a resource, works for dev, PyInstaller and Nuitka.

    Args:
        relative_path: Path relative to the project root (e.g., 'assets/logo.png')
                      or src directory if running from source.
    """
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
    elif _is_nuitka_compiled():
        # Nuitka places included data (assets/, templates/, ...) directly next to the
        # compiled package folders (ui/, utils/, core/, ...), i.e. one level above
        # this module's own directory - not two, as in the source tree layout.
        base_path = Path(os.path.dirname(os.path.abspath(__file__))).parent
    else:
        # If not bundled, use the folder containing this script's parent (project root)
        # Assuming this script is in project_root/src/utils/
        base_path = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent

    return base_path / relative_path

def is_frozen() -> bool:
    """Check if the application is running as a bundled executable (PyInstaller or Nuitka)."""
    return getattr(sys, 'frozen', False) or _is_nuitka_compiled()
