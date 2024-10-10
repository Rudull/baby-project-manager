import os
from mpxj import ProjectReader

def read_project_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"El archivo {file_path} no existe.")
    
    project = ProjectReader().read(file_path)
    
    # Extraer tareas
    tasks = project.getTasks()
    
    for task in tasks:
        if task is not None:  # Verificar si la tarea no es None
            name = task.getName()
            start = task.getStart()
            end = task.getFinish()
            print(f"Tarea: {name}, Inicio: {start}, Fin: {end}")

if __name__ == "__main__":
    file_path = "ruta/del/archivo.mpp"  # Cambia esto a la ruta real de tu archivo
    try:
        read_project_file(file_path)
    except Exception as e:
        print(f"Error: {e}")