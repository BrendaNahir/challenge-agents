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

## Tarea 1: (entrada escrita por el agente)
- **Qué se hizo**: Se crearon las carpetas `reservas/` y `tests/` con sus respectivos archivos `__init__.py`, y el archivo `data/inventario.json` con las 5 unidades del inventario sin modificar los IDs.
- **Archivos que cambiaron**: `reservas/__init__.py`, `tests/__init__.py`, `data/inventario.json`, `PROGRESS.md`.
- **Comando de prueba ejecutado**: `python -c "import json; d = json.load(open('data/inventario.json', encoding='utf-8')); print(len(d)); assert len(d) == 5; print('OK')"` -> Resultado: `5 \n OK`.

## Tarea 1: (notas mías sobre el proceso)
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

