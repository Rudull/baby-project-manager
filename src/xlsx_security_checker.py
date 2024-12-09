# xlsx_security_checker.py

import openpyxl
from openpyxl.utils.exceptions import InvalidFileException

def check_xlsx_restrictions(file_path):
    """Verifica si el XLSX tiene contraseña o restricciones de lectura."""
    try:
        wb = openpyxl.load_workbook(file_path, read_only=False)
        wb.close()
        return None  # Sin restricciones
    except InvalidFileException as e:
        return f"Error al abrir el XLSX: {e}"
    except KeyError as e:
        if 'workbook.xml' in str(e):
            return "El XLSX está protegido o el archivo no es válido."
        else:
            return f"Error al abrir el XLSX: {e}"
    except Exception as e:
        if 'File is not a zip file' in str(e):
            return "El archivo no es un XLSX válido, está protegido con contraseña o está dañado."
        else:
            return f"Error al abrir el XLSX: {e}"
