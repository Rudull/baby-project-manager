# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main_window.py'],
    pathex=[],
    binaries=[('C:\\Program Files\\Java\\jdk-23\\bin\\server\\jvm.dll', '.')],
    datas=[('src/loading.html', '.')],
    hiddenimports=[
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6-WebEngine',
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
    name='BabyProjectManager',
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
    icon=['assets/icono.ico'],
)