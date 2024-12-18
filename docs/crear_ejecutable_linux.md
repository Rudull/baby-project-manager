# Crear Ejecutable en Linux

## 1. Preparación del Entorno

```bash
# Instalar dependencias necesarias
pip install --upgrade pip
pip install pyinstaller
pip install -r requirements.txt
```

## 2. Configurar el Archivo Spec

1. Crear el archivo spec:
```bash
pyi-makespec --onefile --windowed --add-data "src/loading.gif:." src/main_window.py
```

2. Editar `main_window.spec` para incluir todas las dependencias:
```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main_window.py'],
    pathex=[],
    binaries=[],
    datas=[('src/loading.gif', '.')],
    hiddenimports=[
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'workalendar',
        'workalendar.america',
        'jpype1',
        'mpxj',
        'pdfplumber',
        'openpyxl',
        'pandas',
        'PyPDF2',
        'pycryptodome',
        'Crypto',
        'Crypto.Cipher',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='baby-project-manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

## 3. Crear el Ejecutable

```bash
pyinstaller main_window.spec
```

El ejecutable se generará en la carpeta `dist/`.

## 4. Verificación

1. Probar el ejecutable:
```bash
./dist/baby-project-manager
```

2. Si hay errores con Java:
- Asegurarse de tener instalado OpenJDK
- Configurar JAVA_HOME correctamente

## 5. Distribución

- Copiar la carpeta `dist/` completa
- Asegurarse de que el archivo `loading.gif` está incluido
- El usuario final necesitará tener Java instalado
```
