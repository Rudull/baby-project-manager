# Sistema de Alertas de Hitos y Recordatorios

Baby Project Manager incluye un sistema de alertas avanzado diseñado para mantener al usuario informado sobre el progreso del proyecto y tareas críticas sin causar saturación.

## Descripción General

El sistema monitoriza automáticamente las fechas de vencimiento de las tareas y permite configurar recordatorios independientes. Utiliza un esquema de "una notificación al día" para evitar interrupciones constantes, mientras mantiene una vigilancia en segundo plano si la aplicación permanece abierta durante largos periodos.

## Características Principales

- **Alertas de Próximo Vencimiento**: Notifica tareas que vencen pronto según un umbral configurable.
- **Detección de Tareas Vencidas**: Muestra un resumen de tareas que ya han pasado su fecha final.
- **Recordatorios Independientes**: Permite añadir notas personalizadas con fechas y frecuencias específicas por tarea.
- **Frecuencias Periódicas**: Soporte para recordatorios únicos, diarios, semanales y mensuales.
- **Sistema Anti-Saturación**:
  - Máximo un resumen visual al día al iniciar.
  - Tareas vencidas colapsadas por defecto para reducir ruido visual.
  - Opción de "Posponer" (Snooze) y "No molestar" (Silenciar) por tarea.

---

## Configuración Global

Accesible desde el menú principal **Configuración -> Alertas...**.

| Parámetro | Descripción |
|-----------|-------------|
| **Habilitar sistema** | Activa o desactiva todas las notificaciones de la app. |
| **Mostrar al arrancar** | Controla si aparece el diálogo de resumen al abrir la aplicación. |
| **Umbral global** | Días de anticipación por defecto para considerar una tarea "Próxima". |
| **Hora de chequeo** | Hora en la que se realiza la validación automática si la app sigue abierta. |

---

## Recordatorios por Tarea

Haciendo clic derecho sobre cualquier tarea -> **Recordatorios...**.

### Umbral Personalizado
Permite anular la configuración global para una tarea específica o silenciarla completamente si no requiere seguimiento visual.

### Recordatorios Adicionales
Ideal para hitos internos que no afectan el diagrama de Gantt (ej: "Enviar correo solicitando equipos").
- **Comentario**: Descripción del recordatorio.
- **Fecha**: Cuándo debe sonar la alerta.
- **Frecuencia**:
  - **Una vez**: Alerta única.
  - **Diario**: Se repite cada día desde la fecha elegida.
  - **Semanal**: Se repite el mismo día de la semana.
  - **Mensual**: Se repite el mismo día del mes.

---

## Diálogo de Resumen (Startup)

Cuando el sistema detecta alertas activas al iniciar:
1. **Próximas**: Listado de tareas críticas con botones de acción rápida.
2. **Recordatorios**: Muestra el comentario personalizado y la fecha.
3. **Vencidas**: Sección contraíble al final para referencia histórica.

### Acciones por Alerta
- **Posponer**: Oculta la alerta por 1, 3 o 7 días.
- **Silenciar**: Marca la tarea como "No molestar" permanentemente.

---

## Funcionamiento Técnico

### Persistencia
La configuración se guarda en el archivo .bpm de cada proyecto dentro de los campos:
- `ALERT_THRESHOLD`: Umbral específico.
- `ALERT_SNOOZED`: Fecha de posposición o "never".
- `REMINDERS`: Lista de diccionarios con comentarios, fechas y frecuencias.

### Lógica de Segundo Plano
Si la aplicación permanece abierta por días, un QTimer calcula el tiempo hasta la próxima "Hora de chequeo". Al cumplirse:
- Se actualizan las alertas internamente.
- Se resetea el flag de "visto hoy" para que el usuario reciba el resumen actualizado.

---

## Solución de Problemas

**Q: No recibo alertas al arrancar**
- Verifique que estén habilitadas en la configuración global.
- Compruebe que las tareas tengan fechas finales válidas (dd/MM/yyyy).
- Revise si ya se mostró un diálogo ese mismo día (el sistema lo bloquea hasta mañana).

**Q: Una tarea silenciada vuelve a aparecer**
- Al cambiar el umbral de una tarea de "Silenciar" a "Global" o "Personalizado", el estado de silencio se elimina automáticamente.
