# Sistema de Comandos - Deshacer/Rehacer

## Descripción General

Baby Project Manager incluye un sistema completo de comandos que permite deshacer (Ctrl+Z) y rehacer (Ctrl+Y) todas las operaciones realizadas con las tareas. Este sistema está basado en el patrón de diseño Command y proporciona una experiencia de usuario fluida y confiable.

## Características Principales

- **Deshacer/Rehacer Completo**: Todas las operaciones con tareas pueden ser deshechas y rehechas.
- **Historial Inteligente**: Mantiene un historial de hasta 50 comandos.
- **Integración Transparente**: Funciona automáticamente sin intervención del usuario.
- **Preservación de Estado**: Restaura completamente el estado anterior de las tareas.

## Operaciones Soportadas

### Operaciones Básicas de Tareas
- **Agregar Nueva Tarea**: Ctrl+Z deshace la creación de la tarea.
- **Eliminar Tarea**: Ctrl+Z restaura la tarea eliminada con todas sus propiedades.
- **Duplicar Tarea**: Ctrl+Z elimina la tarea duplicada.
- **Insertar Tarea**: Ctrl+Z elimina la tarea insertada.

### Operaciones de Edición
- **Cambiar Nombre**: Restaura el nombre anterior.
- **Modificar Fechas**: Restaura fechas de inicio y fin.
- **Cambiar Duración**: Restaura la duración anterior.
- **Modificar Dedicación**: Restaura el porcentaje de dedicación.

### Operaciones de Estructura
- **Mover Tarea Arriba/Abajo**: Restaura la posición original.
- **Convertir a Subtarea**: Deshace la conversión.
- **Convertir a Tarea Padre**: Restaura como subtarea.
- **Agregar Subtarea**: Elimina la subtarea agregada.

### Operaciones de Formato
- **Cambiar Color**: Restaura el color anterior.
- **Restablecer Todos los Colores**: Restaura todos los colores originales.
- **Editar Notas**: Restaura el contenido anterior de las notas.
- **Modificar Hipervínculos**: Restaura los enlaces anteriores.

## Atajos de Teclado

| Atajo | Acción | Descripción |
|-------|--------|-------------|
| `Ctrl+Z` | Deshacer | Deshace la última operación realizada |
| `Ctrl+Y` | Rehacer | Rehace la última operación deshecha |
| `Ctrl+S` | Guardar | Guarda el proyecto actual |
| `Escape` | Deseleccionar | Limpia la selección actual |
| `Ctrl+Rueda` | Zoom del Gantt | Acerca/aleja la escala de tiempo (Completa → Año → 6M → 3M → 1M). La línea "Hoy" se ancla en la pantalla durante el zoom |
| `Shift+Rueda` | Scroll horizontal | Desplaza la vista del Gantt horizontalmente para navegar proyectos largos |

## Interfaz de Usuario

### Menú Principal
- **Deshacer**: Muestra el comando que se puede deshacer.
- **Rehacer**: Muestra el comando que se puede rehacer.
- Los elementos se habilitan/deshabilitan automáticamente.

### Indicadores Visuales
- Los comandos disponibles se muestran en el menú.
- El título de la ventana muestra "*" cuando hay cambios sin guardar.

## Interacción con el Diagrama de Gantt

### Zoom y Navegación
- **Zoom temporal (Ctrl+Scroll)**: Cambia la escala de tiempo entre cinco vistas:
  - **Completa**: Ajusta todo el proyecto al ancho del viewport.
  - **Año**: Muestra ~365 días por viewport.
  - **6 Meses**: Muestra ~183 días por viewport.
  - **3 Meses**: Muestra ~91 días por viewport.
  - **1 Mes**: Muestra ~31 días por viewport.

- **Línea "Hoy" anclada**: La línea roja que marca el día actual permanece en la misma posición horizontal de la pantalla al cambiar de zoom, garantizando una referencia visual estable. Al abrir un proyecto, la línea "Hoy" se posiciona donde aparecería en la vista "Completa", independientemente del zoom anterior.

- **Zoom persistente**: El nivel de zoom se guarda automáticamente y se restaura al iniciar la aplicación, sin necesidad de ajustarlo cada vez.

- **Scroll horizontal (Shift+Scroll o barra de desplazamiento)**: Navega proyectos largos que no caben en el viewport. En vista "Completa" el scroll está deshabilitado (todo el proyecto visible).

- **Scroll vertical (Scroll)**: Desplaza la lista de tareas sincronizadamente con el diagrama de Gantt.

### Vista de Calendario
- **Modo Mes/Año**: Los botones "Mes" y "Año" permiten alternar entre dos vistas del calendario.
- **Modo persistente**: La aplicación recuerda si estabas en vista de mes o año y la restaura al iniciar.

### Estado de Ventana
- **Posición y tamaño**: Cuando cierras la aplicación con la ventana en modo normal (no maximizada), la posición y tamaño se guardan y se restauran exactamente en la siguiente sesión.
- **Estado maximizado**: Si cierras la aplicación con la ventana maximizada, se abre maximizada nuevamente, correctamente alineada con la pantalla.

### Interacción con Barras
- **Clic en barra**: Selecciona la tarea en la tabla.
- **Doble clic en barra**: Abre el selector de color para personalizar el color de la tarea.
- **Clic derecho en barra**: Abre menú contextual (Duplicar, Mover, Eliminar, etc.).
- **Hover sobre barra**: Cambia el cursor a "mano" para indicar interactividad.

## Uso Básico

### Ejemplo 1: Deshacer Eliminación de Tarea
```
1. Seleccionar una tarea en la tabla
2. Hacer clic derecho -> "Eliminar"
3. La tarea desaparece
4. Presionar Ctrl+Z
5. La tarea se restaura completamente
```

### Ejemplo 2: Deshacer Múltiples Operaciones
```
1. Agregar nueva tarea (Operación A)
2. Cambiar su color (Operación B)
3. Mover la tarea arriba (Operación C)
4. Presionar Ctrl+Z -> Deshace C (movimiento)
5. Presionar Ctrl+Z -> Deshace B (color)
6. Presionar Ctrl+Z -> Deshace A (creación)
7. Presionar Ctrl+Y -> Rehace A
8. Presionar Ctrl+Y -> Rehace B
9. Presionar Ctrl+Y -> Rehace C
```

## Limitaciones y Consideraciones

### Límites del Sistema
- **Historial Máximo**: 50 comandos (configurable).
- **Memoria**: Los comandos mantienen copias de los datos modificados.
- **Persistencia**: El historial se limpia al cargar/crear un nuevo proyecto.

### Operaciones No Incluidas
- **Guardado/Carga de Archivos**: No se pueden deshacer.
- **Importación de Datos**: No se puede deshacer la importación.
- **Cambios de Vista**: No afectan el historial de comandos.
- **Configuraciones**: Los cambios en preferencias no se incluyen.

## Implementación Técnica

### Arquitectura
El sistema utiliza el patrón Command con los siguientes componentes:
1. **CommandManager**: Gestor central del historial.
2. **Command (Base)**: Clase abstracta para todos los comandos.
3. **Comandos Específicos**: Implementaciones para cada operación.

### Comandos Disponibles

- `AddTaskCommand`: Agregar tareas.
- `DeleteTaskCommand`: Eliminar tareas.
- `MoveTaskCommand`: Mover tareas.
- `EditTaskCommand`: Editar propiedades de las tareas.
- `ChangeColorCommand`: Cambiar colores de las tareas.
- `DuplicateTaskCommand`: Duplicar tareas existentes.
- `ConvertTaskCommand`: Convertir tipo de tarea (Padre/Subtarea).
- `AddSubtaskCommand`: Agregar subtareas.
- `InsertTaskCommand`: Insertar tareas en posiciones específicas.
- `ResetColorsCommand`: Restablecer colores originales.
- `EditNotesCommand`: Editar contenido de las notas.

## Desarrollo y Extensión

Para añadir una nueva operación al sistema:

```python
class MiNuevoCommand(Command):
    def __init__(self, main_window, parametros):
        super().__init__("descripción del comando")
        self.main_window = main_window
        # Guardar estado necesario
        
    def execute(self):
        # Implementar la operación
        pass
        
    def undo(self):
        # Implementar la operación inversa
        pass
```

### Mejores Prácticas
1. **Estado Completo**: Guardar todo el estado necesario para deshacer.
2. **Operaciones Atómicas**: Cada comando debe ser una operación completa.
3. **Manejo de Errores**: Implementar manejo robusto de excepciones.

## Solución de Problemas

**Q: El comando deshacer no funciona**
- Verificar que la operación esté implementada como comando.
- Comprobar que el CommandManager esté inicializado.

**Q: Se pierde el historial inesperadamente**
- El historial se limpia al cargar nuevos proyectos.
- Verificar el límite máximo de historial (50 comandos).

## Testing

Ejecutar las pruebas del sistema:
```bash
cd src
python test_commands.py
```
Las pruebas verifican la funcionalidad básica, límites del historial e integridad de los datos.

## Versión y Changelog

### v1.0 (Actual)
- Implementación inicial del sistema de comandos.
- Soporte para todas las operaciones principales e integración con UI.

---

*Última actualización: 2026-07-03*