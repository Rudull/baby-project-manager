# Estructura del Proyecto - Baby Project Manager

Este documento detalla la jerarquía de archivos y carpetas del proyecto utilizando una representación visual de árbol para facilitar el control y mantenimiento.

## Árbol de Directorios

```plaintext
baby-project-manager/
├── assets/                     # Recursos estáticos (iconos, imágenes)
├── docs/                       # Documentación técnica y manuales
├── tests/                      # Suite de pruebas unitarias
├── src/                        # Código fuente de la aplicación
│   ├── updater/                # Sistema de actualizaciones automáticas
│   ├── main_window.py          # Ventana principal y orquestación
│   ├── main.py                 # Lanzador simplificado
│   ├── models.py               # Clase Task y Modelo de Tabla
│   ├── command_system.py       # Sistema para Undo/Redo
│   ├── task_operations_mixin.py # Operaciones avanzadas sobre tareas
│   ├── table_views.py          # Implementación de la tabla de tareas
│   ├── gantt_views.py          # Visualización del diagrama de Gantt
│   ├── delegates.py            # Renderizado de celdas personalizadas
│   ├── alert_manager.py        # Lógica central de alertas
│   ├── alerts_dialog.py        # Resumen de alertas activas
│   ├── global_alerts_dialog.py  # Configuración global de alertas
│   ├── task_reminder_dialog.py # Recordatorios individuales por tarea
│   ├── about_dialog.py         # Ventana "Acerca de" rediseñada
│   ├── report_dialog.py        # Ventana de reporte de problemas (Dual)
│   ├── secrets_loader.py       # Carga segura de variables de entorno (.env)
│   ├── resource_helper.py      # Gestor de rutas para recursos (Assets/Bundling)
│   ├── loading_animation_widget.py # Widget de animación de carga
│   ├── file_gui.py             # Interfaz de importación de archivos
│   ├── mpp_extractor.py        # Extractor para Microsoft Project
│   ├── xlsx_extractor.py       # Extractor para Excel
│   ├── pdf_extractor.py        # Extractor para PDF
│   ├── *_security_checker.py   # Verificadores de seguridad y tipos
│   ├── config_manager.py       # Gestión de persistencia (.json)
│   ├── startup_manager.py      # Control de inicio con el sistema
│   ├── logger_config.py        # Configuración de logs
│   ├── jvm_manager.py          # Ciclo de vida de la JVM (Java)
│   ├── hipervinculo.py         # Soporte para enlaces en notas
│   └── loading.html            # Animación de carga (web view)
├── .env.example                # Plantilla para configuración de secretos
├── .env                        # Configuración local (ignorado por Git)
├── build_system/               # Scripts de construcción de ejecutables
│   ├── README.md               # Guía de construcción
│   ├── build_linux_executable.py
│   ├── build_windows_executable.py
│   ├── build_cx-freeze_executable_windows.py
│   ├── build_to_distribution.py
│   └── check_windows_deps.py
├── README.md                   # Guía de inicio rápido
├── STRUCTURE.md                # (Este archivo) Control de estructura
├── requirements.txt            # Dependencias de Python
└── environment_*.yaml          # Entornos de Conda/Anaconda
```

---

## Descripción de Componentes

### Núcleo (Core)
- **main_window.py**: Gestiona el ciclo de vida de la interfaz y conecta los módulos.
- **models.py**: Define la estructura de datos Task y la comunicación modelo-vista.
- **command_system.py**: Implementa el patrón Command para permitir acciones reversibles.

### Visualización (Views)
- **gantt_views.py**: Encargado de dibujar las barras de Gantt y manejar el zoom.
- **table_views.py**: Configura las columnas y el comportamiento de la tabla de tareas.

### Importación y Datos
- **file_gui.py**: Puente entre archivos externos (.mpp, .xlsx, .pdf) y el modelo interno.
- **jvm_manager.py**: Gestiona el entorno Java para el procesamiento de archivos de Project.

### Utilidades y Otros
- **resource_helper.py**: Normaliza el acceso a archivos (assets, configs) tanto en desarrollo como en ejecutables empaquetados.
- **secrets_loader.py**: Implementa un parser ligero de `.env` para manejar secretos sin dependencias externas pesadas.
- **report_dialog.py**: Sistema de reporte de errores dual (GitHub + Discord).
- **updater/**: Gestiona la descarga e instalación de nuevas versiones desde GitHub.

---

*Última actualización: 2026-04-12*
