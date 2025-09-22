# Sistema de Comandos - Deshacer/Rehacer

## Descripción General

Baby Project Manager incluye un sistema completo de comandos que permite deshacer (Ctrl+Z) y rehacer (Ctrl+Y) todas las operaciones realizadas con las tareas. Este sistema está basado en el patrón de diseño Command y proporciona una experiencia de usuario fluida y confiable.

## Características Principales

- **Deshacer/Rehacer Completo**: Todas las operaciones con tareas pueden ser deshechas y rehechas
- **Historial Inteligente**: Mantiene un historial de hasta 50 comandos
- **Integración Transparente**: Funciona automáticamente sin intervención del usuario
- **Preservación de Estado**: Restaura completamente el estado anterior de las tareas

## Operaciones Soportadas

### ✅ Operaciones Básicas de Tareas
- **Agregar Nueva Tarea**: Ctrl+Z deshace la creación de la tarea
- **Eliminar Tarea**: Ctrl+Z restaura la tarea eliminada con todas sus propiedades
- **Duplicar Tarea**: Ctrl+Z elimina la tarea duplicada
- **Insertar Tarea**: Ctrl+Z elimina la tarea insertada

### ✅ Operaciones de Edición
- **Cambiar Nombre**: Restaura el nombre anterior
- **Modificar Fechas**: Restaura fechas de inicio y fin
- **Cambiar Duración**: Restaura la duración anterior
- **Modificar Dedicación**: Restaura el porcentaje de dedicación

### ✅ Operaciones de Estructura
- **Mover Tarea Arriba/Abajo**: Restaura la posición original
- **Convertir a Subtarea**: Deshace la conversión
- **Convertir a Tarea Padre**: Restaura como subtarea
- **Agregar Subtarea**: Elimina la subtarea agregada

### ✅ Operaciones de Formato
- **Cambiar Color**: Restaura el color anterior
- **Restablecer Todos los Colores**: Restaura todos los colores originales
- **Editar Notas**: Restaura el contenido anterior de las notas
- **Modificar Hipervínculos**: Restaura los enlaces anteriores

## Atajos de Teclado

| Atajo | Acción | Descripción |
|-------|--------|-------------|
| `Ctrl+Z` | Deshacer | Deshace la última operación realizada |
| `Ctrl+Y` | Rehacer | Rehace la última operación deshecha |
| `Ctrl+S` | Guardar | Guarda el proyecto actual |
| `Escape` | Deseleccionar | Limpia la selección actual |

## Interfaz de Usuario

### Menú Principal
- **Deshacer**: Muestra el comando que se puede deshacer
- **Rehacer**: Muestra el comando que se puede rehacer
- Los elementos se habilitan/deshabilitan automáticamente

### Indicadores Visuales
- Los comandos disponibles se muestran en el menú
- El título de la ventana muestra "*" cuando hay cambios sin guardar

## Uso Básico

### Ejemplo 1: Deshacer Eliminación de Tarea
```
1. Seleccionar una tarea en la tabla
2. Hacer clic derecho → "Eliminar"
3. La tarea desaparece
4. Presionar Ctrl+Z
5. La tarea se restaura completamente
```

### Ejemplo 2: Deshacer Múltiples Operaciones
```
1. Agregar nueva tarea (Operación A)
2. Cambiar su color (Operación B)
3. Mover la tarea arriba (Operación C)
4. Presionar Ctrl+Z → Deshace C (movimiento)
5. Presionar Ctrl+Z → Deshace B (color)
6. Presionar Ctrl+Z → Deshace A (creación)
7. Presionar Ctrl+Y → Rehace A
8. Presionar Ctrl+Y → Rehace B
9. Presionar Ctrl+Y → Rehace C
```

## Limitaciones y Consideraciones

### Límites del Sistema
- **Historial Máximo**: 50 comandos (configurable)
- **Memoria**: Los comandos mantienen copias de los datos modificados
- **Persistencia**: El historial se limpia al cargar/crear un nuevo proyecto

### Operaciones No Incluidas
- **Guardado/Carga de Archivos**: No se pueden deshacer
- **Importación de Datos**: No se puede deshacer la importación
- **Cambios de Vista**: No afectan el historial de comandos
- **Configuraciones**: Los cambios en preferencias no se incluyen

### Comportamiento Especial
- **Carga de Proyecto**: Limpia automáticamente el historial
- **Nuevo Proyecto**: Reinicia el sistema de comandos
- **Cambios Múltiples**: Cada edición individual se registra por separado

## Implementación Técnica

### Arquitectura
El sistema utiliza el patrón Command con los siguientes componentes:

1. **CommandManager**: Gestor central del historial
2. **Command (Base)**: Clase abstracta para todos los comandos
3. **Comandos Específicos**: Implementaciones para cada operación
4. **Integración UI**: Conexión con la interfaz de usuario

### Comandos Disponibles
- `AddTaskCommand`: Agregar tareas
- `DeleteTaskCommand`: Eliminar tareas
- `MoveTaskCommand`: Mover tareas
- `EditTaskCommand`: Editar propiedades
- `ChangeColorCommand`: Cambiar colores
- `DuplicateTaskCommand`: Duplicar tareas
- `ConvertTaskCommand`: Convertir tipo de tarea
- `AddSubtaskCommand`: Agregar subtareas
- `InsertTaskCommand`: Insertar tareas
- `ResetColorsCommand`: Restablecer colores
- `EditNotesCommand`: Editar notas

### Flujo de Ejecución
```
1. Usuario realiza acción → UI captura evento
2. UI crea comando apropiado → Command object
3. CommandManager ejecuta comando → command.execute()
4. Comando se añade al historial → History updated
5. Usuario presiona Ctrl+Z → CommandManager.undo()
6. Comando se deshace → command.undo()
```

## Desarrollo y Extensión

### Agregar Nuevo Comando
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
1. **Estado Completo**: Guardar todo el estado necesario para deshacer
2. **Operaciones Atómicas**: Cada comando debe ser una operación completa
3. **Manejo de Errores**: Implementar manejo robusto de excepciones
4. **Descripción Clara**: Usar descripciones descriptivas para los comandos
5. **Eficiencia**: Minimizar el uso de memoria en comandos frecuentes

## Solución de Problemas

### Problemas Comunes

**Q: El comando deshacer no funciona**
- Verificar que la operación esté implementada como comando
- Comprobar que el CommandManager esté inicializado
- Revisar que no haya errores en la consola

**Q: Se pierde el historial inesperadamente**
- El historial se limpia al cargar nuevos proyectos
- Verificar el límite máximo de historial (50 comandos)

**Q: Operación parcialmente deshecha**
- Asegurar que el comando guarde todo el estado necesario
- Verificar que las relaciones entre objetos se restauren correctamente

### Debugging
Activar mensajes de debug agregando prints en:
- `CommandManager.execute_command()`
- `CommandManager.undo()`
- `CommandManager.redo()`

## Testing

Ejecutar las pruebas del sistema:
```bash
cd src
python test_commands.py
```

Las pruebas verifican:
- Funcionalidad básica de deshacer/rehacer
- Límites del historial
- Estado del CommandManager
- Comandos específicos
- Integridad de los datos

## Versión y Changelog

### v1.0 (Actual)
- Implementación inicial del sistema de comandos
- Soporte para todas las operaciones principales
- Integración completa con la UI
- Sistema de pruebas automatizadas

### Futuras Mejoras
- Compresión del historial para operaciones similares
- Persistencia del historial entre sesiones
- Comandos macro para operaciones múltiples
- API para plugins de terceros