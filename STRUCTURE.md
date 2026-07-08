# Estructura del Proyecto - Baby Project Manager

Este documento detalla la jerarquía de archivos y carpetas del proyecto utilizando una representación visual de árbol para facilitar el control y mantenimiento.

## Árbol de Directorios

```plaintext
baby-project-manager/
├── assets/                     # Recursos estáticos (iconos, imágenes)
├── docs/                       # Documentación técnica y manuales
├── scratch/                    # Suite de pruebas (unit/integration/e2e) y herramientas de debug
├── src/                        # Código fuente de la aplicación
│   ├── main.py                 # Lanzador simplificado
│   ├── version.py              # Versión actual de la app
│   ├── core/                   # Lógica de negocio y datos (sin Qt)
│   │   ├── models.py           # Clase Task y Modelo de Tabla
│   │   ├── command_system.py   # Sistema para Undo/Redo
│   │   ├── alert_manager.py    # Lógica central de alertas
│   │   ├── mpp_extractor.py    # Extractor para Microsoft Project
│   │   ├── xlsx_extractor.py   # Extractor para Excel
│   │   ├── pdf_extractor.py    # Extractor para PDF
│   │   └── *_security_checker.py # Verificadores de seguridad y tipos
│   ├── ui/                     # Widgets, ventanas y diálogos (PySide6)
│   │   ├── main_window.py      # Ventana principal y orquestación
│   │   ├── task_operations_mixin.py # Operaciones avanzadas sobre tareas
│   │   ├── table_views.py      # Implementación de la tabla de tareas
│   │   ├── gantt_views.py      # Visualización del diagrama de Gantt
│   │   ├── calendar_view.py    # Vista de calendario (mes/año)
│   │   ├── delegates.py        # Renderizado de celdas y popup de calendario personalizados
│   │   ├── alerts_dialog.py    # Resumen de alertas activas
│   │   ├── global_alerts_dialog.py # Configuración global de alertas
│   │   ├── task_reminder_dialog.py # Recordatorios individuales por tarea
│   │   ├── about_dialog.py     # Ventana "Acerca de" rediseñada
│   │   ├── report_dialog.py    # Ventana de reporte de problemas (Dual)
│   │   ├── loading_animation_widget.py # Widget de animación de carga
│   │   ├── file_gui.py         # Interfaz de importación de archivos
│   │   └── hipervinculo.py     # Soporte para enlaces en notas
│   ├── utils/                  # Utilidades transversales (sin Qt/lógica de dominio)
│   │   ├── secrets_loader.py   # Carga segura de variables de entorno (.env)
│   │   ├── resource_helper.py  # Gestor de rutas para recursos (Assets/Bundling)
│   │   ├── config_manager.py   # Gestión de persistencia (.json)
│   │   ├── startup_manager.py  # Control de inicio con el sistema
│   │   ├── logger_config.py    # Configuración de logs
│   │   ├── jvm_manager.py      # Ciclo de vida de la JVM (Java)
│   │   └── filter_util.py      # Normalización y filtrado de texto
│   ├── templates/              # Assets no-Python
│   │   └── loading.html        # Animación de carga (web view)
│   └── updater/                # Sistema de actualizaciones automáticas
├── .env.example                # Plantilla para configuración de secretos
├── .env                        # Configuración local (ignorado por Git)
├── build_system/               # Scripts de construcción de ejecutables
│   ├── README.md               # Guía de construcción
│   ├── build_to_distribution.py # Asistente interactivo (compilador/modo)
│   ├── build_nuitka_windows.py
│   ├── build_pyinstaller_windows.py
│   ├── build_nuitka_linux.py
│   ├── build_pyinstaller_linux.py
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
- **gantt_views.py**: Dibuja las barras de Gantt, encabezados (años/meses/semanas con granularidad adaptativa al zoom), y línea "Hoy". Soporta zoom temporal (5 vistas escalables), desplazamiento horizontal sincronizado, e hit-testing preciso de barras independiente del scroll.
- **calendar_view.py**: Proporciona dos modos de vista del calendario (mes y año) con navegación sincronizada y persistencia del modo seleccionado. Muestra hitos de tareas (inicio/fin) como barras horizontales del ancho de la celda del día, apiladas una por fila, llenas para inicio y con contorno para fin. Indica tareas con notas mediante un punto amarillo en la barra. Resalta festivos colombianos con un tinte rojo suave y fines de semana con gris.
- **delegates.py**: Personaliza el renderizado de celdas de la tabla (LineEdit, SpinBox, botones de estado). El DateEditDelegate proporciona un popup de calendario con festivos colombianos destacados en rojo/negrita, primer día de semana configurado a lunes (consistente con la vista principal), y actualización dinámica de festivos al navegar entre meses y años.
- **table_views.py**: Configura las columnas y el comportamiento de la tabla de tareas, con scrollbar vertical sincronizado con el Gantt.

### Importación y Datos
- **file_gui.py**: Puente entre archivos externos (.mpp, .xlsx, .pdf) y el modelo interno.
- **jvm_manager.py**: Gestiona el entorno Java para el procesamiento de archivos de Project.
- **config_manager.py**: Persiste la configuración de la aplicación en un archivo INI, incluyendo: tamaño y posición de ventana, estado maximizado, nivel de zoom del Gantt, modo de calendario (mes/año), archivos recientes, y configuraciones de alertas.

### Utilidades y Otros
- **resource_helper.py**: Normaliza el acceso a archivos (assets, configs) tanto en desarrollo como en ejecutables empaquetados.
- **secrets_loader.py**: Implementa un parser ligero de `.env` para manejar secretos sin dependencias externas pesadas.
- **report_dialog.py**: Sistema de reporte de errores dual (GitHub + Discord).
- **updater/**: Gestiona la descarga e instalación de nuevas versiones desde GitHub.

---

*Última actualización: 2026-07-06 (src/ reorganizado en core/ui/utils/templates y tests/ renombrado a scratch/ con unit/integration/e2e, siguiendo la misma filosofía que el proyecto cad/Design Box)*
