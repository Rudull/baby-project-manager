import os
import sys
from pathlib import Path

def get_resource_path(relative_path: str) -> Path:
    """
    Get the absolute path to a resource, works for dev and for PyInstaller.
    
    Args:
        relative_path: Path relative to the project root (e.g., 'assets/logo.png')
                      or src directory if running from source.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
    except Exception:
        # If not bundled, use the folder containing this script's parent (project root)
        # Assuming this script is in project_root/src/
        base_path = Path(os.path.dirname(os.path.abspath(__file__))).parent

    return base_path / relative_path

def is_frozen() -> bool:
    """Check if the application is running as a bundled executable."""
    return getattr(sys, 'frozen', False)
