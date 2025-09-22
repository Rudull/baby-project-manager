# pdf_security_checker.py

import PyPDF2

def check_pdf_restrictions(file_path):
    """Verifica si el PDF tiene contraseña o restricciones de extracción de contenido."""
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            if reader.is_encrypted:
                return "El PDF está protegido con contraseña."

            # Verificar si hay un diccionario de encriptación
            encrypt_dict = reader.trailer.get('/Encrypt')
            if encrypt_dict:
                permissions = encrypt_dict.get('/P')
                if permissions is not None:
                    # Convertir el entero de permisos a 32 bits sin signo
                    permissions = permissions + (1 << 32) if permissions < 0 else permissions
                    # Comprobar si el permiso de extracción está permitido
                    can_extract = permissions & 16 == 16
                    if not can_extract:
                        return "El PDF tiene restricciones de extracción de contenido."
            return None  # Sin restricciones
    except PyPDF2.errors.PdfReadError as e:
        return f"Error al leer el PDF: {e}"
    except Exception as e:
        return f"Error al abrir el PDF: {e}"
