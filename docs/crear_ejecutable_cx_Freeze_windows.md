# Crear Ejecutable en Windows

## 1. Preparación del Entorno

1. Instalar dependencias:
```cmd
pip install --upgrade pip
pip install cx_Freeze
pip install -r requirements.txt
```

proyecto/
├── src/
│   ├── main_window.py
│   ├── gantt_views.py
│   ├── models.py
│   ├── table_views.py
│   ├── about_dialog.py
│   └── loading.html
└── setup.py

2. Verificar Java:
- Instalar JDK si no está instalado
- Configurar JAVA_HOME en variables de entorno

## 2. Crear setup.py

```python
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
```

## 3. Crear el Ejecutable

# Desde la raíz del proyecto
```cmd
python setup.py build
```

El ejecutable se generará en:
```
proyecto/
└── build/
    └── exe.win-amd64-3.11/  # La versión puede variar
        └── BabyProjectManager.exe
```

## 4. Distribución

1. Copiar toda la carpeta `exe.win-amd64-3.11/`
2. Incluir todos los archivos generados
3. El usuario final necesita:
- Java instalado
- JAVA_HOME configurado

## 5. Verificación

1. Probar el ejecutable haciendo doble clic
2. Verificar que:
- La interfaz se carga correctamente
- Las funciones de importación funcionan
- La animación de carga se muestra

## Nota
- Es recomendable usar un entorno virtual limpio
- Usar Python 3.7+ de 64 bits
- Incluir todos los recursos necesarios
```
