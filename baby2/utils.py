import os
from datetime import datetime, timedelta
from PySide6.QtCore import QDate
from PySide6.QtGui import QColor
from workalendar.america import Colombia

class DateCalculator:
    """Utilidades para cálculos de fechas."""
    
    def __init__(self):
        self.calendar = Colombia()

    def calculate_business_days(self, start_date: QDate, end_date: QDate) -> int:
        """
        Calcula los días laborables entre dos fechas.
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha final
            
        Returns:
            int: Número de días laborables
        """
        if not start_date.isValid() or not end_date.isValid():
            return 0

        start = start_date.toPython()
        end = end_date.toPython()
        
        if end < start:
            return 0

        business_days = 0
        current_date = start
        
        while current_date <= end:
            if self.calendar.is_working_day(current_date):
                business_days += 1
            current_date += timedelta(days=1)
            
        return business_days

    def calculate_end_date(self, start_date: QDate, business_days: int) -> QDate:
        """
        Calcula la fecha final dado un número de días laborables.
        
        Args:
            start_date: Fecha de inicio
            business_days: Número de días laborables deseados
            
        Returns:
            QDate: Fecha final calculada
        """
        if not start_date.isValid() or business_days < 1:
            return start_date

        current_date = start_date.toPython()
        days_counted = 0
        
        while days_counted < business_days:
            if self.calendar.is_working_day(current_date):
                days_counted += 1
            if days_counted < business_days:
                current_date += timedelta(days=1)
                
        return QDate(current_date.year, current_date.month, current_date.day)

    def calculate_working_days_left(self, end_date: QDate) -> int:
        """
        Calcula los días laborables restantes hasta una fecha.
        
        Args:
            end_date: Fecha final
            
        Returns:
            int: Número de días laborables restantes
        """
        if not end_date.isValid():
            return 0

        today = datetime.now().date()
        end = end_date.toPython()
        
        if end < today:
            return 0

        return self.calculate_business_days(QDate(today), end_date)

class ColorManager:
    """Gestión de colores y temas."""
    
    DEFAULT_TASK_COLOR = QColor(34, 163, 159)
    DEFAULT_HIGHLIGHT_COLOR = QColor(200, 200, 255, 50)
    TODAY_LINE_COLOR = QColor(242, 211, 136)

    @staticmethod
    def is_light_theme(background_color: QColor) -> bool:
        """
        Determina si un color de fondo corresponde a un tema claro.
        
        Args:
            background_color: Color de fondo a evaluar
            
        Returns:
            bool: True si es tema claro, False si es oscuro
        """
        return background_color.lightness() > 128

    @staticmethod
    def get_theme_colors(is_light: bool) -> dict:
        """
        Obtiene los colores correspondientes al tema.
        
        Args:
            is_light: True para tema claro, False para oscuro
            
        Returns:
            dict: Diccionario con los colores del tema
        """
        if is_light:
            return {
                'year_color': QColor(80, 80, 80),
                'year_separator': QColor(120, 120, 120),
                'month_color': QColor(100, 100, 100),
                'month_separator': QColor(150, 150, 150),
                'week_color': QColor(120, 120, 120),
                'week_separator': QColor(180, 180, 180)
            }
        else:
            return {
                'year_color': QColor(200, 200, 200),
                'year_separator': QColor(160, 160, 160),
                'month_color': QColor(180, 180, 180),
                'month_separator': QColor(130, 130, 130),
                'week_color': QColor(150, 150, 150),
                'week_separator': QColor(110, 110, 110)
            }

class FileManager:
    """Gestión de archivos y rutas."""
    
    @staticmethod
    def normalize_path(file_path: str) -> str:
        """
        Normaliza una ruta de archivo.
        
        Args:
            file_path: Ruta a normalizar
            
        Returns:
            str: Ruta normalizada
        """
        return os.path.normpath(file_path)

    @staticmethod
    def get_file_name(file_path: str) -> str:
        """
        Obtiene el nombre de un archivo de una ruta.
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            str: Nombre del archivo
        """
        return os.path.basename(file_path)

    @staticmethod
    def ensure_extension(file_path: str, extension: str) -> str:
        """
        Asegura que un archivo tenga la extensión correcta.
        
        Args:
            file_path: Ruta del archivo
            extension: Extensión deseada (sin el punto)
            
        Returns:
            str: Ruta con la extensión correcta
        """
        if not file_path.lower().endswith(f'.{extension.lower()}'):
            return f"{file_path}.{extension}"
        return file_path

class ViewCalculator:
    """Cálculos relacionados con las vistas."""
    
    @staticmethod
    def calculate_pixels_per_day(width: int, total_days: int, min_pixels: float = 0.1) -> float:
        """
        Calcula los píxeles por día para el diagrama de Gantt.
        
        Args:
            width: Ancho disponible en píxeles
            total_days: Número total de días
            min_pixels: Mínimo de píxeles por día
            
        Returns:
            float: Píxeles por día
        """
        return max(min_pixels, width / total_days)

    @staticmethod
    def calculate_visible_tasks(viewport_height: int, row_height: int) -> int:
        """
        Calcula el número de tareas visibles en la vista.
        
        Args:
            viewport_height: Altura del viewport
            row_height: Altura de cada fila
            
        Returns:
            int: Número de tareas visibles
        """
        return max(1, viewport_height // row_height)

class Constants:
    """Constantes utilizadas en la aplicación."""
    
    # Dimensiones
    DEFAULT_ROW_HEIGHT = 25
    DEFAULT_HEADER_HEIGHT = 20
    MIN_WINDOW_WIDTH = 800
    MIN_WINDOW_HEIGHT = 600
    DEFAULT_WINDOW_WIDTH = 1200
    DEFAULT_WINDOW_HEIGHT = 800
    
    # Períodos de tiempo
    ONE_MONTH = 30
    THREE_MONTHS = 90
    SIX_MONTHS = 180
    ONE_YEAR = 365
    
    # Formatos de fecha
    DATE_FORMAT = "dd/MM/yyyy"
    
    # Nombres de archivo
    DEFAULT_FILE_EXTENSION = "bpm"
    
    # Valores por defecto
    DEFAULT_DEDICATION = 40
    DEFAULT_DURATION = 1
    
    # Configuración de zoom
    WHEEL_THRESHOLD = 100

class TaskValidator:
    """Validación de datos de tareas."""
    
    @staticmethod
    def validate_dates(start_date: QDate, end_date: QDate) -> bool:
        """
        Valida que las fechas sean correctas.
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha final
            
        Returns:
            bool: True si las fechas son válidas
        """
        return (start_date.isValid() and 
                end_date.isValid() and 
                end_date >= start_date)

    @staticmethod
    def validate_dedication(dedication: int) -> bool:
        """
        Valida que el porcentaje de dedicación sea correcto.
        
        Args:
            dedication: Porcentaje de dedicación
            
        Returns:
            bool: True si la dedicación es válida
        """
        return 0 <= dedication <= 100

    @staticmethod
    def validate_duration(duration: int) -> bool:
        """
        Valida que la duración sea correcta.
        
        Args:
            duration: Duración en días
            
        Returns:
            bool: True si la duración es válida
        """
        return duration > 0

class ErrorHandler:
    """Manejo de errores comunes."""
    
    @staticmethod
    def format_error_message(error: Exception) -> str:
        """
        Formatea un mensaje de error para mostrar al usuario.
        
        Args:
            error: Excepción a formatear
            
        Returns:
            str: Mensaje de error formateado
        """
        return f"Error: {str(error)}"

    @staticmethod
    def is_critical_error(error: Exception) -> bool:
        """
        Determina si un error es crítico.
        
        Args:
            error: Excepción a evaluar
            
        Returns:
            bool: True si el error es crítico
        """
        critical_types = (OSError, IOError, PermissionError)
        return isinstance(error, critical_types)