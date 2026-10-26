\# Instrucciones para el agente



\## Proyecto

Sistema de reservas de equipos de laboratorio. La especificación está en

`SPEC.md` y es la fuente de verdad: no cambiar reglas ni supuestos sin que

yo lo apruebe.



\## Tecnología

\- Python 3.14, solo librería estándar. No agregar dependencias sin preguntar.

\- SQLite (módulo `sqlite3`) para persistir reservas.

\- Interfaz de consola con `argparse`.

\- Pruebas con `unittest`.



\## Estructura esperada

\- `reservas/` : código de la aplicación

\- `tests/` : pruebas automáticas

\- `data/inventario.json` : inventario inicial (no modificar los IDs)



\## Forma de trabajo

\- Una tarea por vez. Antes de escribir código, explicar brevemente qué vas a hacer.

\- No ejecutar comandos que borren archivos ni datos sin pedir confirmación.

\- No hacer commits ni push: los hago yo.

\- Escribir las pruebas junto con el código de cada tarea.

\- Usar solicitantes ficticios en ejemplos y pruebas. Nada de datos reales ni secretos.



\## Adaptación específica: límites consecutivos

Un intervalo \[inicio, fin) no se superpone con otro si fin == inicio del otro.

La condición de superposición es: `inicio\\\_nuevo < fin\\\_existente AND fin\\\_nuevo > inicio\\\_existente`.

Cada vez que toques la lógica de superposición, verificá con una prueba que

10:00-11:00 y 11:00-12:00 de la misma unidad se aceptan, y que

10:00-11:00 y 10:30-11:30 se rechazan.



\## Al terminar cada tarea

Agregar una entrada breve en `PROGRESS.md`: qué se hizo, qué archivos cambiaron

y qué comando de prueba se ejecutó con su resultado.

