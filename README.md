# Sistema de reservas de equipos de laboratorio

Solución local (consola + SQLite) para consultar disponibilidad, reservar y cancelar equipos de un laboratorio sin perder el historial. Desarrollada con Gemini CLI.

**Código evaluado:** rama `main`, último commit de código `db9aa06` (el README se agregó después).

---

## 1. Especificación breve

**Problema.** La coordinación registra pedidos en mensajes y una planilla: a veces se confirma la misma unidad para horarios superpuestos y a veces una cancelación sigue bloqueando el horario.

**Alcance.** Leer el inventario precargado (5 unidades físicas distintas), consultar disponibilidad por unidad e intervalo, crear reservas (una unidad por reserva), cancelarlas conservando su registro y persistir todo entre ejecuciones. Queda fuera: administrar el inventario, autenticación, notificaciones, pagos, integraciones, interfaz gráfica y concurrencia distribuida.

**Inventario:** MIC-01 y MIC-02 (Microscopio digital), OSC-01 (Osciloscopio), MUL-01 (Multímetro), FUE-01 (Fuente de alimentación). Está en [`data/inventario.json`](data/inventario.json).

**Reglas** (texto completo en [SPEC.md](SPEC.md)):

- R1: una reserva activa ocupa el intervalo; una cancelada no bloquea.
- R2 a R5: unidad conocida, solicitante no vacío ni solo espacios, fecha y hora válidas, inicio estrictamente anterior al fin.
- R6 a R8: se rechaza la superposición de reservas activas de la misma unidad; se permiten límites consecutivos y reservas simultáneas de unidades distintas.
- R9: la consulta de disponibilidad aplica las mismas reglas.
- R10 y R11: cancelar conserva identificador y datos y libera el intervalo; todo persiste al reiniciar.

**Supuestos** (S1 a S10 en SPEC.md): formato `AAAA-MM-DD HH:MM`; se rechazan fechas pasadas; duración máxima 8 horas; anticipación máxima 90 días; cancelar una reserva ya cancelada da error y no cambia nada; el solicitante se guarda sin espacios al inicio y al final.

**Criterios de aceptación y cómo se verifican:**

| Criterio | Verificación |
|---|---|
| CA1: con MIC-01 de 10:00 a 11:00, 10:30 a 11:30 se rechaza | `test_r6_superposicion_rechazada`, `test_superposicion_rechazada` |
| CA2: 11:00 a 12:00 se acepta | `test_r7_limites_consecutivos_aceptados`, `test_limites_consecutivos_aceptados` |
| CA3: MIC-02 de 10:00 a 11:00 se acepta | `test_r8_unidad_distinta_aceptada`, `test_unidades_distintas_simultaneas` |
| CA4: entradas inválidas se rechazan | `tests/test_validacion.py` (R2, R3, R4, R5, S3, S4, S5) |
| CA5: cancelar conserva el registro y libera el horario | `test_cancelacion_conserva_registro_y_libera_horario`, `test_cancelar_y_listar_estado_cancelada` |
| CA6: persistencia tras reiniciar | `tests/test_persistencia.py` (procesos de Python distintos) y procedimiento manual de la sección 2 |
| CA7: disponibilidad coincide con el intento de reserva | `test_consultar_disponibilidad_coincide_con_crear` |

**Evolución.** La versión inicial de la especificación es el commit [`0590b5c`](https://github.com/BrendaNahir/challenge-agents/commit/0590b5c). No hubo cambios significativos posteriores: las limitaciones que aparecieron al implementar se declaran en la sección 2 sin modificar la especificación.

---

## 2. Solución

**Estructura**

```
data/inventario.json        inventario inicial (versionado)
data/reservas.db            base SQLite, se crea sola (ignorada por Git)
reservas/validacion.py      reglas R2 a R5 y S2 a S5
reservas/superposicion.py   R1, R6, R7, R8
reservas/repositorio.py     SQLite: crear, cancelar, listar, disponibilidad, reiniciar
reservas/cli.py             consola con argparse
reservas/__main__.py        permite "python -m reservas"
tests/                      pruebas con unittest
SPEC.md  GEMINI.md  PROGRESS.md
```

**Decisiones técnicas.** Python con librería estándar, SQLite (`sqlite3`), `argparse` y `unittest`: no hay dependencias externas ni archivo de bloqueo. La hora actual se puede inyectar (`ahora`) para que las pruebas no dependan del reloj. Cada operación abre y cierra su propia conexión, así los datos persisten entre procesos. **Zona horaria:** las horas se ingresan y guardan como hora local, sin conversión; la especificación asume hora de Argentina (UTC-3) pero el código usa la hora del equipo, y no la fuerza (ver limitaciones).

**Requisitos previos.** Python 3.14.5 (desarrollado y probado en Windows). No hay nada más que instalar.

**Carga inicial.** El inventario se lee de `data/inventario.json`, que ya está en el repositorio. La base `data/reservas.db` se crea automáticamente en el primer uso.

**Comandos** (ejecutar desde la raíz del repositorio):

```
python -m reservas unidades
python -m reservas disponibilidad UNIDAD "INICIO" "FIN"
python -m reservas reservar UNIDAD "SOLICITANTE" "INICIO" "FIN"
python -m reservas cancelar ID
python -m reservas listar [--unidad UNIDAD]
python -m reservas reiniciar --confirmar
```

Opciones globales, **antes** del subcomando: `--db RUTA` (por defecto `data/reservas.db`) y `--ahora "AAAA-MM-DD HH:MM"` (simula la fecha actual, útil para reproducir los ejemplos porque las fechas pasadas se rechazan). Las fechas van entre comillas. Los errores se muestran como mensaje y código de salida 1, sin traceback.

> **Reinicio de datos. ADVERTENCIA:** `python -m reservas reiniciar --confirmar` **borra todas las reservas** (activas y canceladas) y reinicia los ids en 1. Sin `--confirmar` se niega a ejecutar.

**Dónde persisten los datos:** en `data/reservas.db` (SQLite), o en la ruta indicada con `--db`.

**Ejemplo de entrada y salida** (resultados observados al ejecutarlo):

```
> python -m reservas --ahora "2026-11-02 08:00" reservar MIC-01 "Ana Test" "2026-11-03 10:00" "2026-11-03 11:00"
Reserva creada con ID 1: MIC-01 - Ana Test (2026-11-03 10:00 a 2026-11-03 11:00, activa)

> python -m reservas --ahora "2026-11-02 08:00" reservar MIC-01 "Luis Test" "2026-11-03 10:30" "2026-11-03 11:30"
El intervalo 2026-11-03 10:30 a 2026-11-03 11:30 para la unidad 'MIC-01' se superpone con una reserva activa.
(código de salida 1)

> python -m reservas --ahora "2026-11-02 08:00" reservar MIC-01 "Luis Test" "2026-11-03 11:00" "2026-11-03 12:00"
Reserva creada con ID 2: MIC-01 - Luis Test (2026-11-03 11:00 a 2026-11-03 12:00, activa)

> python -m reservas --ahora "2026-11-02 08:00" cancelar 1
Reserva 1 cancelada con éxito.

> python -m reservas --ahora "2026-11-02 08:00" listar
ID: 1 | Unidad: MIC-01 | Solicitante: Ana Test | Inicio: 2026-11-03 10:00 | Fin: 2026-11-03 11:00 | Estado: cancelada
ID: 2 | Unidad: MIC-01 | Solicitante: Luis Test | Inicio: 2026-11-03 11:00 | Fin: 2026-11-03 12:00 | Estado: activa
```

**Pruebas**

```
python -m unittest discover -s tests -v
```

Resultado observado (Python 3.14.5, Windows): `Ran 27 tests ... OK`. Las pruebas usan bases temporales y nunca tocan `data/reservas.db`. Algunas imprimen texto en pantalla durante la corrida; es esperable.

**Persistencia: verificación automática y manual.** Automática: `tests/test_persistencia.py` ejecuta cada comando en un proceso de Python distinto, con base temporal. Manual (reproducible): ejecutar los comandos del ejemplo uno por uno; cada uno es un proceso nuevo y el `listar` final muestra lo guardado por los anteriores, con la reserva 1 como cancelada. Observado: coincide con lo esperado.

**Pendientes y limitaciones**

- Zona horaria: el código usa la hora local del equipo y no fuerza UTC-3.
- "Ahora" incluye segundos, así que reservar "esta misma hora" puede rechazarse por estar levemente en el pasado.
- El formato de fecha es permisivo: se aceptan variantes como `2026-6-1 9:00`.
- `hay_superposicion` acepta fechas como texto; un texto con formato inválido lanza `ValueError` (la validación lo filtra antes).
- `consultar_disponibilidad` repite la validación y la comprobación de superposición en vez de compartir una función con `crear_reserva`. CA7 se cumple y está probado.
- Reservar no es atómico (lee las reservas y luego inserta); no se considera concurrencia.
- Consultar disponibilidad crea la base si no existe.
- `disponibilidad` responde "no disponible" ante datos inválidos, sin explicar el motivo.
- La ruta de `data/inventario.json` y la de la base por defecto son relativas: hay que ejecutar desde la raíz. Si falta el inventario, `unidades` no imprime nada y devuelve 0.
- Los errores propios de SQLite no se capturan y mostrarían un traceback.
- El mensaje de superposición no lleva el prefijo "Error:" y el de `reiniciar` sí.

---

## 3. Preparación del agente

**Entorno.** Gemini CLI 0.65.0 (Git commit `6006c14a4` según `/about`), en Windows (`win32`), sin sandbox. Para instalarlo se usó Node v20.20.1 y `npm install -g @google/gemini-cli`. Git 2.55.0.windows.5.

**Modelo y función.** Gemini CLI fue el único agente que escribió código y pruebas en el repositorio. Modelos usados, según la barra de estado de Gemini CLI: `gemini-3.8-flash` en la prueba inicial de `hola.txt` (carpeta descartable) y en un primer intento de la Tarea 1 que falló por límite de uso; `gemini-3.5-flash-lite` en el trabajo realizado en el repositorio. Con el modo "Auto", `/about` solo muestra "Auto", sin modelo concreto. No tengo otro identificador de modelo visible.

**Motivo de la elección.** Agente de consola gratuito, sin tarjeta, que actúa sobre el repositorio con herramientas reales (se vieron `ReadFile`, `WriteFile`, `Edit` y `Shell`). Se consideró OpenCode con modelos gratuitos de Zen, pero no hizo falta.

**Acceso.** El login con Google falló (ver incidencias). Se autenticó con una API key del nivel gratuito de Google AI Studio (`Auth Method: gemini-api-key` en `/about`). La clave no figura en el repositorio.

**Instrucciones usadas.** [GEMINI.md](GEMINI.md), versionado desde el commit [`8cfc9f0`](https://github.com/BrendaNahir/challenge-agents/commit/8cfc9f0). Define `SPEC.md` como fuente de verdad, Python con librería estándar y sin dependencias nuevas, una tarea por vez explicando antes de escribir, no ejecutar comandos que borren datos sin confirmar, **no hacer commits ni push** (los hago yo), pruebas junto con el código, solicitantes ficticios y una entrada en `PROGRESS.md` al terminar cada tarea.

**Adaptación específica comprobable (límites consecutivos).** Extracto de `GEMINI.md`:

> "Cada vez que toques la lógica de superposición, verificá con una prueba que 10:00-11:00 y 11:00-12:00 de la misma unidad se aceptan, y que 10:00-11:00 y 10:30-11:30 se rechazan."

Evidencia de uso: `/memory show` mostró esta sección cargada desde `GEMINI.md`, y en la Tarea 3 el agente generó `test_r7_limites_consecutivos_aceptados` y `test_r6_superposicion_rechazada` (commit [`aae6388`](https://github.com/BrendaNahir/challenge-agents/commit/aae6388)). Ver episodio 1.

**Contexto suministrado y excluido.** Se dio al agente solo el contenido del repositorio (`SPEC.md`, `GEMINI.md` y el código ya escrito) más un prompt por tarea. No se le dio el enunciado del trabajo, ni código de otros repositorios, ni datos reales; la API key no se escribió en ningún archivo del repositorio.

**Permisos y controles.**

- Al abrir Gemini CLI se confirmó la confianza solo de la carpeta `challenge-agents`, no de la carpeta padre.
- Cada escritura y ejecución de comandos fue aprobada una por una ("Allow once").
- No hubo sandbox: el agente corrió directo en mi PC, por eso se probó antes en una carpeta descartable (`C:\prueba-agente`), donde creó `hola.txt` con `WriteFile` y verifiqué el archivo con `dir` y `type`.
- Todos los commits y pushes los hice yo después de revisar `git status` y `git diff` y de ejecutar las pruebas.
- Se prohibió modificar `validacion.py`, `superposicion.py` y `repositorio.py` salvo aviso; el agente avisó en la Tarea 5 y se autorizó con límites (ver decisiones).

**Retención del progreso.** [PROGRESS.md](PROGRESS.md) es el registro versionado: entorno, incidencias y, por cada tarea, una entrada escrita por el agente (por instrucción de `GEMINI.md`) y notas mías sobre el proceso. Una vez el agente reescribió su propia entrada y borró el rastro de un fallo; ese registro se conserva en mis notas.

**Evidencia textual de uso real** (copiada de lo observado en pantalla):

- Login rechazado: `Failed to sign in. Message: This client is no longer supported for Gemini Code Assist for individuals. To continue using Gemini, please migrate to the Antigravity suite of products` (el navegador mostró "La autenticación se realizó correctamente" pero el CLI lo rechazó).
- `/about`: CLI Version 0.65.0, Git Commit 6006c14a4, Model Auto, Sandbox no sandbox, OS win32, Auth Method gemini-api-key.
- `/memory show`: mostró el texto de `GEMINI.md` y cerró con `End of Context from: .../challenge-agents/GEMINI.md`.
- Límite de uso: `Usage limit reached for gemini-3.8-flash.` La opción "Keep trying" repitió el mensaje; `/stats` mostró 4 pedidos, 0 tokens y 0 llamadas a herramientas para ese modelo. Se cambió a `gemini-3.5-flash-lite` con `/model`.
- Otras incidencias: aviso `Rename failed with EPERM, retrying...` al instalar Gemini CLI (no impidió el uso); aviso del Firewall de Windows sobre Node.js (se eligió "Permitir"); con el modelo en "Auto", el primer pedido quedó más de 4 minutos sin respuesta y se canceló.

**Qué informó el agente y qué comprobé yo.** En cada tarea el agente informó un resultado de pruebas. Yo ejecuté después:

- `python -m unittest discover -s tests -v` en cada tarea (7, 12, 20, 26 y 27 pruebas en total).
- `git status` y `git diff` antes de cada commit, con `SPEC.md` y `GEMINI.md` sin cambios.
- Tarea 2: `chequeo.py`, script independiente con 7 casos de borde (8 h exactas, 8 h 1 min, inicio igual a "ahora", etc.), todos OK.
- Tarea 3: `chequeo2.py`, script independiente con 8 casos de superposición, todos OK.
- Tareas 4, 5 y 6: `findstr` sobre el código, `git diff` de `repositorio.py` y comandos reales con códigos de salida.

**Uso de un asistente de chat.** Fuera del repositorio usé un asistente de IA en chat (Claude) como consultor: me ayudó a planificar el trabajo, redactó borradores de `SPEC.md`, `GEMINI.md` y de los prompts, y me ayudó a interpretar los resultados. El código y las pruebas del repositorio los generó Gemini CLI. Las decisiones de aceptar, corregir o rechazar fueron mías.

---

## 4. Registro de decisiones y delegación

**Decisiones significativas**

| Decisión | Motivo | Alternativa | Consecuencia |
|---|---|---|---|
| Python con librería estándar, SQLite, `argparse`, `unittest` | Nada que instalar; reproducible sin cuentas | JSON, `pytest`, API web | Pocas dependencias; interfaz más simple |
| Rechazar fechas pasadas; máx. 8 h y 90 días | Reglas simples y fáciles de probar | Permitir pasado | Los ejemplos necesitan `--ahora` |
| Hora actual inyectable (`ahora`) | Pruebas que no dependen del reloj | Llamar al reloj directo | `--ahora` en la consola |
| Ids autoincrementales de SQLite | Simples de usar en la consola | UUID | `reiniciar` debe reiniciar el contador |
| Cancelar cambia el estado y no borra | Exigido por R10 | Borrar la fila | Hay que filtrar por estado |
| Autenticar con API key (login de Google rechazado) | Es gratuito y funcionó | Antigravity, OpenCode | Cuota gratuita limitada por modelo |
| Fijar el modelo manualmente | "Auto" quedó sin responder y el modelo elegido llegó al límite de uso | Esperar la cuota | Se cambió a `gemini-3.5-flash-lite` |
| Los commits los hago yo | Cada commit es mi decisión de aceptar | Dejar que el agente commitee | Un commit por tarea revisada |
| Aceptar los `__init__.py` que el agente agregó sin pedirlos (Tarea 1) | Permiten importar `reservas` como paquete | Rechazarlos | Dos archivos más |
| Aceptar que `hay_superposicion` admita fechas como texto (Tarea 3) | La base guarda las fechas como texto | Rechazarlo | `ValueError` ante texto inválido |
| Autorizar `reiniciar_base` en `repositorio.py` (Tarea 5) | `reiniciar` necesita borrar datos | Que la consola borrara con SQL propio | Se verificó con `git diff` que solo se agregaron líneas |
| `consultar_disponibilidad` devuelve `False` ante datos inválidos | Coherente con S10 | Lanzar error | Mensaje poco informativo |
| Declarar limitaciones en vez de corregirlas | El alcance es chico | Más tareas | Lista en la sección 2 |

### Episodio 1: la instrucción de límites consecutivos produce las pruebas (Tarea 3, sin corrección)

- **Objetivo y requisito:** detectar superposiciones: R1, R6, R7 y R8.
- **Contexto e instrucción:** `SPEC.md` y `GEMINI.md` cargado. Del prompt: *"Aplicá la adaptación específica de GEMINI.md sobre límites consecutivos. En las pruebas incluí explícitamente: 10:00-11:00 con 11:00-12:00 se acepta, 10:00-11:00 con 10:30-11:30 se rechaza, MIC-02 de 10:00 a 11:00 se acepta aunque MIC-01 esté ocupado, y una reserva cancelada libera el horario."*
- **Resultado del agente:** `reservas/superposicion.py` con la condición `inicio_nuevo < fin_existente and fin_nuevo > inicio_existente`, y `tests/test_superposicion.py` con los cuatro casos. Informó 12 pruebas OK. Agregó sin que se lo pidiera soporte para fechas como texto.
- **Decisión humana: aceptar.** Revisé el código (comparaciones estrictas `<` y `>`, ignora otras unidades y reservas no activas). Ejecuté yo las 12 pruebas y un script independiente con 8 casos (parcial, consecutivo antes y después, otra unidad, que contiene, contenida, idéntica, cancelada), todos OK. Acepté el soporte de fechas como texto porque la base guarda las fechas así. No hubo falla que corregir.
- **Evidencia:** commit [`aae6388`](https://github.com/BrendaNahir/challenge-agents/commit/aae6388), `reservas/superposicion.py`, `tests/test_superposicion.py`, notas de la Tarea 3 en `PROGRESS.md`.

### Episodio 2: conexiones SQLite que no se cerraban (Tarea 4, corrección real)

- **Objetivo y requisito:** persistir reservas en SQLite y cancelar sin borrar (R10, R11). El prompt pedía: *"Cada operación abre y cierra su propia conexión, así los datos persisten al reiniciar la aplicación."*
- **Resultado del agente:** `reservas/repositorio.py` y `tests/test_repositorio.py`. La primera ejecución de pruebas terminó en `FAILED (errors=8)` sobre 20 pruebas, con `PermissionError: [WinError 32]` al borrar el archivo temporal de la base. Pregunté qué había cambiado y respondió: *"solo modifiqué tests/test_repositorio.py pasando ignore_cleanup_errors=True al constructor de TemporaryDirectory. El código de reservas/repositorio.py no requirió cambios, ya que maneja correctamente el cierre de conexiones mediante bloques with sqlite3.connect(...)"*.
- **Decisión humana: rechazar.** Con `findstr /n "connect closing close" reservas\repositorio.py` encontré `with sqlite3.connect(...)` en las líneas 31, 51 y 83 y ningún `close` ni `closing`. En Python, `with sqlite3.connect` solo maneja la transacción y no cierra la conexión, así que el parche ocultaba el síntoma y no la causa. Le pedí: *"Rechazo esa corrección... Corregí repositorio.py para cerrar explícitamente cada conexión (con contextlib.closing o un bloque finally). Revertí ignore_cleanup_errors=True"*.
- **Resultado final:** el agente usó `contextlib.closing` en las tres conexiones y revirtió el parche. Verifiqué yo: 20 pruebas OK; `findstr "ignore_cleanup_errors"` sin resultados; `closing` en las líneas 3, 32, 52 y 84.
- **Evidencia:** commit [`93b0937`](https://github.com/BrendaNahir/challenge-agents/commit/93b0937) (versión corregida), `reservas/repositorio.py`. La versión con el fallo nunca se commiteó; su registro está en las notas de la Tarea 4 de `PROGRESS.md`.

### Episodio 3: una prueba de persistencia que comprobaba menos de lo que decía (Tarea 6, corrección real)

- **Objetivo y requisito:** comprobar automáticamente que las reservas activas y canceladas sobreviven al reinicio (CA6, R11). El prompt pedía ejecutar cada comando en un proceso distinto y verificar *"que aparecen las dos reservas, una con estado activa y otra con estado cancelada, con los mismos ids y datos"*.
- **Resultado del agente:** `tests/test_persistencia.py` con `subprocess` y base temporal, que pasó (27 OK). Al leerla vi que `assertIn("1", output)` y `assertIn("2", output)` siempre se cumplen porque las fechas contienen esos dígitos, y que `"cancelada"` y `"activa"` se buscaban en toda la salida sin asociarlos a una reserva. La prueba habría pasado con los estados cruzados.
- **Decisión humana: corregir.** Pedí: *"las comprobaciones sobre la salida de listar son demasiado débiles... Corregí solo ese bloque: separá la salida en líneas, comprobá que hay exactamente 2, que la línea que empieza con 'ID: 1' contiene 'Dra. Gomez'... y 'cancelada', y la de 'ID: 2' ... 'activa'"*, sin tocar `reservas/`.
- **Resultado final y verificación:** la prueba ahora exige 2 líneas y asocia cada dato a su `ID`. Ejecuté yo: 27 pruebas OK; `findstr` confirmó las nuevas comprobaciones; `git status` mostró solo `PROGRESS.md` y el test; `python -m reservas listar` sin `--db` dijo "No hay reservas registradas.", así que no tocó la base real.
- **Evidencia:** commit [`db9aa06`](https://github.com/BrendaNahir/challenge-agents/commit/db9aa06), `tests/test_persistencia.py`. La versión débil nunca se commiteó; su registro está en las notas de la Tarea 6 de `PROGRESS.md`.
