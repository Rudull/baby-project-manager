#xlsx_extractor.py
#
import pandas as pd
from datetime import datetime
import re
import unicodedata
from filter_util import is_start_end_task

class XLSXReader:
    def __init__(self):
        self.column_mappings = {
            'task_id': ['id', 'task id', 'taskid', '#', 'código', 'codigo'],
            'name': ['name', 'task name', 'taskname', 'activity', 'description',
                     'nombre', 'tarea', 'actividad', 'descripcion', 'descripción'],
            'start_date': [
                'start', 'start date', 'startdate', 'begin date',
                'fecha inicio', 'inicio', 'fecha de inicio', 'fecha_inicio',
                'fecha inicio', 'start_date', 'fecha de comienzo', 'comienzo'
            ],
            'end_date': [
                'end', 'finish', 'end date', 'enddate', 'finish date',
                'fecha fin', 'fin', 'fecha de fin', 'fecha final', 'fecha_fin',
                'fecha terminación', 'terminación'
            ],
            'level': ['level', 'outline level', 'wbs', 'hierarchy',
                      'nivel', 'jerarquía', 'jerarquia', 'nivel_']
        }

    def normalize_column_name(self, name):
        """Elimina acentos y caracteres especiales, y convierte a minúsculas."""
        name = ''.join(
            c for c in unicodedata.normalize('NFD', name)
            if unicodedata.category(c) != 'Mn'
        )
        return name.lower().strip()

    def identify_columns(self, df):
        identified_columns = {}
        # Normalizar los nombres de columnas
        df.columns = [self.normalize_column_name(str(col)) for col in df.columns]

        for key, possible_names in self.column_mappings.items():
            for col in df.columns:
                # Normalizar los nombres posibles
                normalized_possible = [self.normalize_column_name(name) for name in possible_names]
                # Verificar coincidencia exacta o si la columna contiene alguno de los nombres posibles
                if col in normalized_possible or any(name in col for name in normalized_possible):
                    identified_columns[key] = col
                    break

        # Fallback para fechas en caso de no identificar columnas por nombre
        date_columns = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
        if 'start_date' not in identified_columns and date_columns:
            identified_columns['start_date'] = date_columns[0]
        if 'end_date' not in identified_columns and len(date_columns) > 1:
            identified_columns['end_date'] = date_columns[1]

        return identified_columns

    def format_date(self, date_value):
        if pd.isna(date_value):
            return ""

        try:
            # Si es un número (fecha de Excel), convertir a datetime
            if isinstance(date_value, (int, float)):
                return pd.Timestamp.fromordinal(
                    datetime(1900, 1, 1).toordinal() + int(date_value) - 2
                ).strftime('%d/%m/%Y')

            # Si ya es datetime o Timestamp
            if isinstance(date_value, (datetime, pd.Timestamp)):
                return date_value.strftime('%d/%m/%Y')

            # Si es string, intentar varios formatos
            if isinstance(date_value, str):
                date_value = date_value.strip()
                for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y'):
                    try:
                        return datetime.strptime(date_value, fmt).strftime('%d/%m/%Y')
                    except ValueError:
                        continue

            return str(date_value)
        except Exception:
            return str(date_value)

    def compare_dates(self, date1, date2):
        """Compara dos fechas en formato string dd/mm/yyyy"""
        if not date1 or not date2:
            return False
        try:
            date1_obj = datetime.strptime(date1, '%d/%m/%Y')
            date2_obj = datetime.strptime(date2, '%d/%m/%Y')
            return date1_obj == date2_obj
        except:
            return False

    def determine_outline_level(self, row, columns, text):
        """Determina el nivel jerárquico de una tarea"""
        # Primero intentar usar el valor de la columna nivel si existe
        if 'level' in columns:
            try:
                level_value = row[columns['level']]
                if not pd.isna(level_value):
                    if isinstance(level_value, (int, float)):
                        return int(level_value)
                    elif isinstance(level_value, str):
                        # Limpiar la cadena y convertir a entero
                        level_str = re.sub(r'[^\d]', '', level_value)
                        if level_str:
                            return int(level_str)
            except (ValueError, TypeError):
                pass

        # Si no se pudo obtener el nivel de la columna, usar la indentación
        leading_spaces = len(text) - len(text.lstrip())
        return leading_spaces // 2 if leading_spaces > 0 else 0

    def read_xlsx(self, file_path):
        try:
            # Leer las dos primeras filas para detectar encabezados
            df_head = pd.read_excel(file_path, nrows=2, header=None)  # header=None para leer sin encabezados predeterminados

            # Analizar si la primera fila parece un encabezado
            first_row_is_header = self._is_header_row(df_head.iloc[0])

            # Leer el archivo completo con el header correcto
            header_row = 0 if first_row_is_header else 1
            df = pd.read_excel(file_path, header=header_row)

            columns = self.identify_columns(df)
            if not columns:
                raise ValueError("No se pudieron identificar las columnas necesarias")

            tasks = []
            for idx, row in df.iterrows():
                try:
                    if 'name' not in columns:
                        continue

                    task_name = str(row[columns['name']]).strip()
                    if pd.isna(task_name) or not task_name:
                        continue

                    # Obtener fechas primero
                    start_date = ''
                    end_date = ''
                    if 'start_date' in columns:
                        start_date = self.format_date(row[columns['start_date']])
                    if 'end_date' in columns:
                        end_date = self.format_date(row[columns['end_date']])

                    # Verificar si es una tarea hito o tiene misma fecha inicio/fin
                    if is_start_end_task(task_name) or self.compare_dates(start_date, end_date):
                        continue

                    # Obtener el nivel
                    outline_level = self.determine_outline_level(row, columns, task_name)

                    # Task ID
                    task_id = ''
                    if 'task_id' in columns and not pd.isna(row[columns['task_id']]):
                        task_id = str(row[columns['task_id']])


                    task = {
                        'task_id': task_id,
                        'name': task_name,
                        'start_date': start_date,
                        'end_date': end_date,
                        'level': str(outline_level),
                        'outline_level': outline_level,
                        'indentation': outline_level
                    }
                    tasks.append(task)

                except Exception:
                    continue

            return tasks

        except Exception:
            return []

    def _is_header_row(self, row):
        """Verifica si una fila parece un encabezado de columna."""
        #Criterios simples:
        # - Si la mayoría de las celdas no son números y tienen longitud > 3 (heurística)
        # - Si alguna celda contiene texto como "ID", "Nombre", "Fecha", etc (case insensitive)
        non_numeric_count = 0
        for cell in row:
            cell_str = str(cell).strip()
            if not cell_str.isdigit() and len(cell_str) > 3:
                non_numeric_count +=1
            elif any(keyword in cell_str.lower() for keyword in ["id", "nombre", "name", "fecha", "start", "end", "nivel", "level"]):
                return True
        return non_numeric_count >= len(row)/2
