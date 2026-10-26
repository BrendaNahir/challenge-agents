\# Especificación: Sistema de reservas de equipos de laboratorio



\## 1. Problema

La coordinación de un laboratorio registra pedidos en mensajes y una planilla.

A veces se confirma la misma unidad para horarios superpuestos, y a veces una

cancelación sigue bloqueando el horario. Se necesita consultar disponibilidad,

reservar y cancelar sin perder el historial.



\## 2. Alcance

Incluye:

\- Leer el inventario precargado (5 unidades, cada ID es una unidad física distinta).

\- Consultar disponibilidad de una unidad en un intervalo.

\- Crear reservas (una unidad por reserva).

\- Cancelar reservas conservando su registro.

\- Persistir reservas y estados para recuperarlos al reiniciar.



No incluye: administrar el inventario, autenticación y roles, notificaciones,

pagos, integraciones externas, interfaz gráfica, concurrencia distribuida.



\## 3. Inventario inicial

| ID de unidad | Equipo |

|---|---|

| MIC-01 | Microscopio digital |

| MIC-02 | Microscopio digital |

| OSC-01 | Osciloscopio |

| MUL-01 | Multímetro |

| FUE-01 | Fuente de alimentación |



\## 4. Reglas

\- R1. Una reserva activa ocupa el intervalo; una cancelada no bloquea.

\- R2. La unidad debe existir en el inventario.

\- R3. El solicitante no puede ser vacío ni contener solo espacios.

\- R4. Fecha y hora deben ser válidas y con el formato `AAAA-MM-DD HH:MM`.

\- R5. El inicio debe ser estrictamente anterior al fin.

\- R6. Se rechaza la superposición con reservas activas de la misma unidad.

\- R7. Se permiten límites consecutivos (el fin de una = el inicio de otra).

\- R8. Se permiten reservas simultáneas de unidades distintas.

\- R9. La consulta de disponibilidad aplica exactamente las mismas reglas.

\- R10. Cancelar conserva identificador y datos, cambia el estado a "cancelada"

&#x20; y libera el intervalo.

\- R11. Las reservas y sus estados persisten al cerrar y reabrir la aplicación.



\## 5. Supuestos

\- S1. Zona horaria única: Argentina (UTC-3, sin horario de verano). Las horas

&#x20; se ingresan y guardan como hora local, sin conversión.

\- S2. Formato de fecha y hora: `AAAA-MM-DD HH:MM`, sin segundos.

\- S3. No se permiten reservas con inicio anterior al momento actual.

\- S4. Duración máxima de una reserva: 8 horas.

\- S5. Anticipación máxima: el inicio no puede superar los 90 días desde ahora.

\- S6. No hay duración mínima más allá de inicio < fin.

\- S7. Cancelar una reserva ya cancelada devuelve un error claro y no cambia nada.

\- S8. Cancelar es posible mientras la reserva esté activa, aunque ya haya comenzado.

\- S9. Los solicitantes son ficticios; el texto se guarda sin espacios al inicio y al final.

\- S10. La consulta de disponibilidad también rechaza intervalos inválidos o

&#x20; fuera de los límites S3 a S5.



\## 6. Interfaz

Consola (CLI) con los comandos: `unidades`, `disponibilidad`, `reservar`,

`cancelar`, `listar`.



\## 7. Criterios de aceptación

\- CA1. Con MIC-01 reservado de 10:00 a 11:00, reservar MIC-01 de 10:30 a 11:30 se rechaza.

\- CA2. Con la misma reserva, reservar MIC-01 de 11:00 a 12:00 se acepta.

\- CA3. Con la misma reserva, reservar MIC-02 de 10:00 a 11:00 se acepta.

\- CA4. Reservar con unidad inexistente, solicitante vacío o solo espacios,

&#x20; fecha inválida, inicio >= fin, duración > 8 h, pasado o más de 90 días se rechaza.

\- CA5. Tras cancelar, la reserva sigue listada con estado "cancelada" y el

&#x20; mismo ID, y el horario vuelve a estar disponible.

\- CA6. Tras detener y reiniciar la aplicación, las reservas activas y

&#x20; canceladas siguen presentes.

\- CA7. La consulta de disponibilidad da el mismo resultado que el intento de

&#x20; reserva para el mismo intervalo.

