# Baby Project Manager

[![Versión](https://img.shields.io/badge/version-0.4.3-blue.svg)](https://github.com/Rudull/baby-project-manager/releases)
[![Licencia](https://img.shields.io/badge/license-GPL--3.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)

**Baby Project Manager** es una herramienta para la gestión de proyectos y creación de diagramas de Gantt. Diseñada para ofrecer una experiencia intuitiva, permite organizar, visualizar y programar tareas de manera profesional sin complicaciones.

---

## Propuesta de Valor

Baby Project Manager se destaca por su ligereza y enfoque en lo esencial:
- **Claridad Visual**: Diagramas de Gantt interactivos sincronizados con la lista de tareas.
- **Interoperabilidad**: Importación desde Microsoft Project (.mpp), Excel (.xlsx) y PDF.
- **Control Total**: Sistema completo de Deshacer/Rehacer (Undo/Redo) y alertas de hitos.
- **Localización**: Soporte nativo para el calendario de festivos de Colombia.

---

## Vista Previa

### Interfaz Principal
![Baby Project Manager - Pantalla Principal](assets/1_baby_project_manager_0-4-3.png)

### Importación de Cronogramas
![Ventana de Importación](assets/2_import_0-4-3.png)

---

## Características Principales

- **Gestión Jerárquica**: Creación de tareas y subtareas con niveles de indentación.
- **Diagramas de Gantt Dinámicos**: Zoom, arrastrar y soltar, y vistas personalizadas.
- **Formatos Soportados**:
  - **Nativo**: .bpm (eficiente).
  - **Importación**: .mpp, .xlsx, .pdf.
  - **Exportación**: Excel y PDF.
- **Sistema de Alertas**: Recordatorios por tarea y alertas globales de vencimiento.
- **Personalización**: Colores por tarea, notas con hipervínculos y temas claro/oscuro.
- **Productividad**: Atajos de teclado y menús contextuales rápidos.

---

## Instalación y Configuración

### 1. Clona el repositorio
```bash
git clone https://github.com/Rudull/baby-project-manager
```

### 2. Configura el entorno (Recomendado: Conda/Anaconda)
Este proyecto utiliza librerías de Java y Qt, por lo que Conda es la forma más sencilla de gestionar todas las dependencias:

```bash
# Crear el entorno desde el archivo de configuración
conda env create -f environment_windows.yaml

# Activar el entorno
conda activate baby
```

*Nota: La configuración de Conda ya incluye el JDK de Java necesario para desarrollo.*

### 3. Configura los secretos
- Copia `.env.example` como `.env` y añade tu URL de Webhook de Discord para habilitar los reportes directos desde la app. Esto es necesario tanto para desarrollo como para que el ejecutable compilado tenga soporte de reportes.

### 4. Ejecuta la aplicación
```bash
python src/main.py
```

---

## Generación del Ejecutable (Build)

Para crear una versión distribuible (.exe) en Windows:

```bash
# Limpiar y generar distribución completa (Súper rápido - sin UPX)
python build_system/build_to_distribution.py --clean
```

**Importante para el Usuario Final:**
Para que el archivo `.exe` generado pueda abrir archivos de Microsoft Project (.mpp), el usuario debe tener **Java instalado en su sistema Windows** y configurado en el `PATH`. Consulta [docs/Configuracion de entorno virtual de Java.txt](docs/Configuracion de entorno virtual de Java.txt) para más detalles.

---

## Reporte de Problemas

La aplicación incluye un sistema dual para reportar errores:
- **GitHub Issues**: Para usuarios con cuenta de GitHub.
- **Reporte Directo (Discord)**: Envío de reportes anónimos directamente desde la aplicación (requiere que el `.env` esté presente al momento de compilar).

---

## Requisitos del Sistema

- **Python 3.11+** (Recomendado)
- **Java JDK 17+** 
  - Para desarrollo: Incluido en el entorno Conda.
  - Para el Ejecutable: Instalación global en Windows requerida.
- **Bibliotecas principales**: PySide6, pandas, openpyxl, mpxj, jpype1, workalendar.

---

## Estructura del Proyecto

Para consultar la arquitectura detallada de archivos y carpetas, vea:

[STRUCTURE.md](STRUCTURE.md)

---

## Contribuciones

Las contribuciones son bienvenidas. Si desea mejorar la aplicación o añadir formatos de importación, puede abrir un Pull Request o un Issue.

---

## Licencia

Este proyecto está bajo la licencia **GNU General Public License v3.0**. Ver el archivo [LICENSE](LICENSE) para más detalles.

---

**Desarrollado por [Rafael Hernández Bustamante](https://www.linkedin.com/in/rafaelhernandezbustamante)**
