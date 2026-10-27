\# Registro de progreso



\## Entorno (datos reales, 26/10/2026)

\- Sistema operativo: Windows

\- Node.js: v20.20.1

\- Gemini CLI: 0.65.0 (instalado con `npm install -g @google/gemini-cli`)

\- Git: 2.55.0.windows.5

\- Python: 3.14.5

\- Incidencia: al ejecutar `gemini --version` apareció

&#x20; `Rename failed with EPERM, retrying in 50ms (attempt 1/5)...`.

&#x20; No impidió el funcionamiento.



\## Hitos

\- Especificación inicial: commit `0590b5c` (`SPEC.md`).

\## Tareas con el agente

(Se completa a medida que se avanza.)

## Permisos y controles
- Al abrir Gemini CLI por primera vez pidió confirmar la confianza de la
  carpeta. Elegí "Trust folder (challenge-agents)" y no la carpeta padre,
  para limitar el alcance del agente a este repositorio.
- Los commits y pushes los hago yo después de revisar `git status` y `git diff`.
- Sandbox: ninguno (el agente corre directo en mi PC).
- Permisos: ante la escritura de `hola.txt`, Gemini pidió confirmación y la
  aprobé yo manualmente (opción elegida: "Allow once").

## Incidencias de acceso (26/10/2026)
- Al iniciar sesión con Google apareció un aviso del Firewall de Windows
  sobre Node.js. Elegí "Permitir".
- El login "Sign in with Google" terminó en: "Failed to sign in. Message:
  This client is no longer supported for Gemini Code Assist for
  individuals..." (el navegador mostró "La autenticación se realizó
  correctamente", pero el CLI la rechazó).
- Decisión: autenticar con API key de Google AI Studio (nivel gratuito).
  Para crearla hizo falta crear un proyecto nuevo.

## Acceso al agente (26/10/2026)
- Gemini CLI 0.65.0 (commit 6006c14a4), autenticación `gemini-api-key`
  (confirmado con `/about`).
- Con el modelo en "Auto", el primer pedido quedó más de 4 minutos sin
  respuesta y lo cancelé. Fijé manualmente `gemini-3.8-flash` con `/model`.
- Prueba en carpeta descartable (C:\prueba-agente): el agente creó
  `hola.txt` con la herramienta WriteFile. Verifiqué el archivo con `dir`
  y `type`.

## Tarea 1 (entrada escrita por el agente)
- **Qué se hizo**: Se crearon las carpetas `reservas/` y `tests/` con sus respectivos archivos `__init__.py`, y el archivo `data/inventario.json` con las 5 unidades del inventario sin modificar los IDs.
- **Archivos que cambiaron**: `reservas/__init__.py`, `tests/__init__.py`, `data/inventario.json`, `PROGRESS.md`.
- **Comando de prueba ejecutado**: `python -c "import json; d = json.load(open('data/inventario.json', encoding='utf-8')); print(len(d)); assert len(d) == 5; print('OK')"` -> Resultado: `5 \n OK`.

## Tarea 1 (notas mías sobre el proceso)
- Con `gemini-3.8-flash`, el pedido falló: "Usage limit reached for
  gemini-3.8-flash". La opción "Keep trying" repitió el mensaje.
  `/stats` mostró 4 pedidos, 0 tokens y 0 llamadas a herramientas en esa sesión.
- Cambié el modelo con `/model` a `gemini-3.5-flash-lite` y el pedido
  se procesó.
- Gemini leyó `SPEC.md` y, antes de crear nada, explicó su plan: carpetas
  `reservas/` y `tests/` con `__init__.py` e `data/inventario.json`.
  Los `__init__.py` no los había pedido.
- Decisión sobre `__init__.py`: los acepté, aunque no los pedí, porque
  permiten importar `reservas` como paquete desde las pruebas.
- Revisión humana: `git status` mostró solo `PROGRESS.md` modificado y las
  carpetas nuevas; `SPEC.md` y `GEMINI.md` no cambiaron. La prueba del
  agente solo verificó que hubiera 5 elementos, así que comprobé yo los IDs
  y los nombres con acento con un comando de Python. Resultado: IDs
  correctos y nombres correctos (True, True).
- Observación: `type data\inventario.json` en PowerShell mostró los acentos
  rotos ("MultÃ­metro"). Era un problema de visualización de la consola,
  no del archivo.
- Permisos: las escrituras y ediciones de esta tarea las aprobé yo
  ("Allow once").

## Tarea 2 (entrada escrita por el agente)
- **Qué se hizo**: Se implementó la validación de los datos de una reserva en `reservas/validacion.py` según las reglas R2 a R5 y los supuestos S2 a S5 de SPEC.md (verificación de unidad existente en inventario, solicitante no vacío con espacios limpios, formato de fecha AAAA-MM-DD HH:MM, inicio anterior al fin, duración máxima de 8 horas, inicio no anterior a "ahora" y anticipación máxima de 90 días, con soporte para el parámetro opcional "ahora"). Se escribieron pruebas unitarias exhaustivas con `unittest` en `tests/test_validacion.py` (una prueba por regla/supuesto).
- **Archivos que cambiaron**: `reservas/validacion.py`, `tests/test_validacion.py`, `PROGRESS.md`.
- **Comando de prueba ejecutado**: `python -m unittest tests/test_validacion.py` -> Resultado: `Ran 7 tests in 0.049s - OK`.

## Tarea 2 (notas mías sobre el proceso)
- Pedí la validación (R2 a R5, S2 a S5) con el parámetro "ahora"
  inyectable, para que las pruebas no dependan del reloj.
- Verificación propia 1: `python -m unittest discover -s tests -v`
  -> 7 tests OK (los corrí yo, además de lo que informó el agente).
- Verificación propia 2: revisé `reservas/validacion.py` y comprobé que
  no tiene caracteres rotos (el conteo de "Ã" dio 0; lo que vi en la
  consola era un problema de visualización).
- Verificación propia 3: script independiente fuera del repo con 7 casos
  de borde (8 h exactas, 8 h 1 min, inicio igual a "ahora", inicio 1 min
  antes, solo espacios, fecha imposible, unidad inexistente). Resultado:
  los 7 dieron OK.
- Python generó carpetas `__pycache__`; agregué un `.gitignore` para
  no versionarlas.
- Limitaciones detectadas al revisar el código (declaradas, sin corregir):
  usa la hora de la PC y no fuerza UTC-3; "ahora" incluye segundos;
  `strptime` acepta formatos como `2026-6-1 9:00`.

## Tarea 3 (entrada escrita por el agente)
- **Qué se hizo**: Se implementó la detección de superposición de reservas en `reservas/superposicion.py` aplicando las reglas R1 (canceladas no bloquean), R6 (superposición rechazada en misma unidad), R7 (límites consecutivos permitidos donde fin == inicio del otro se acepta) y R8 (unidades distintas simultáneas permitidas), junto con la fórmula exacta de superposición (`inicio_nuevo < fin_existente AND fin_nuevo > inicio_existente`). Se escribieron pruebas unitarias en `tests/test_superposicion.py` cubriendo límites consecutivos (10:00-11:00 y 11:00-12:00 aceptados, 10:00-11:00 y 10:30-11:30 rechazados), unidades distintas (MIC-02 aceptado aunque MIC-01 esté ocupado) y liberación por reserva cancelada.
- **Archivos que cambiaron**: `reservas/superposicion.py`, `tests/test_superposicion.py`, `PROGRESS.md`.
- **Comando de prueba ejecutado**: `python -m unittest tests/test_validacion.py tests/test_superposicion.py` -> Resultado: `Ran 12 tests in 0.115s - OK`.

## Tarea 3 (notas mías sobre el proceso)
- Pedí la detección de superposición aplicando la adaptación de
  `GEMINI.md` (límites consecutivos), con cuatro pruebas explícitas:
  consecutivos aceptados, superposición rechazada, unidad distinta
  aceptada y reserva cancelada que libera el horario.
- Verificación propia 1: `python -m unittest discover -s tests -v`
  -> 12 tests OK (los corrí yo).
- Verificación propia 2: revisé `reservas/superposicion.py`. La condición
  usa `<` y `>` estrictos, ignora otras unidades y reservas no activas.
- Verificación propia 3: script independiente fuera del repo con 8 casos
  (superposición parcial, consecutivo después y antes, otra unidad,
  que contiene a la otra, contenida, idéntica y cancelada). Resultado:
  los 8 dieron OK.
- Evidencia de la adaptación específica: las pruebas
  `test_r7_limites_consecutivos_aceptados` y
  `test_r6_superposicion_rechazada` salieron de la instrucción de
  `GEMINI.md` sobre límites consecutivos.
- Gemini agregó, sin que lo pidiera, soporte para fechas como texto.
  Decisión: lo acepté, porque al guardar en SQLite las fechas se leerán
  como texto. Limitación: un texto con formato inválido lanza
  `ValueError`; la validación de la Tarea 2 lo filtra antes.
- Observación: al revisar `PROGRESS.md` aparecieron entradas del agente
  duplicadas (Tareas 1 y 2) y mezcladas con mis notas. Lo ordené y
  deduplicé a mano.