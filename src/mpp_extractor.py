#mpp_extractor.py
#7
import sys
import os
import jpype
import mpxj
from datetime import datetime

class MPPReader:
    def __init__(self):
        pass

    def format_outline_number(self, task):
        """Genera el número de esquema jerárquico para una tarea"""
        outline_number = task.getOutlineNumber()
        if outline_number is not None:
            return str(outline_number)
        return ''

    def format_date(self, date):
        """Convierte la fecha a formato dd/mm/yyyy"""
        if date is None:
            return ""
        try:
            # Para fechas tipo LocalDateTime
            if hasattr(date, 'getDayOfMonth'):
                day = str(date.getDayOfMonth()).zfill(2)
                month = str(date.getMonthValue()).zfill(2)
                year = date.getYear()
                return f"{day}/{month}/{year}"
            # Para fechas tipo Date (versiones antiguas de MPXJ)
            elif hasattr(date, 'getTime'):
                python_date = datetime.fromtimestamp(date.getTime() / 1000)
                return python_date.strftime("%d/%m/%Y")
            else:
                return str(date)
        except Exception as e:
            print(f"Error al formatear fecha: {str(e)}")
            return str(date)
