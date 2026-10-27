import json
from datetime import datetime, timedelta
from pathlib import Path

class ErrorValidacion(Exception):
    """Excepción propia para errores de validación de reservas."""
    pass

def _cargar_inventario():
    inventario_path = Path(__file__).parent.parent / "data" / "inventario.json"
    if not inventario_path.exists():
        inventario_path = Path("data/inventario.json")
    with open(inventario_path, "r", encoding="utf-8") as f:
        return json.load(f)

def validar_reserva(unidad, solicitante, inicio, fin, ahora=None):
    """Valida los datos de una reserva según las reglas R2-R5 y supuestos S2-S5.

    Parámetros:
    - unidad: str (ID de unidad)
    - solicitante: str
    - inicio: str ("AAAA-MM-DD HH:MM")
    - fin: str ("AAAA-MM-DD HH:MM")
    - ahora: datetime o str opcional ("AAAA-MM-DD HH:MM"), por defecto datetime.now()

    Retorna:
    - (unidad, solicitante_limpio, inicio_dt, fin_dt) si es válido.
    - Lanza ErrorValidacion si algo es inválido.
    """
    # 1. Validar Unidad (R2)
    inventario = _cargar_inventario()
    ids_validos = {item["id"] for item in inventario}
    if not unidad or unidad not in ids_validos:
        raise ErrorValidacion(f"Unidad inválida o inexistente: '{unidad}'.")

    # 2. Validar Solicitante (R3, S9)
    if not solicitante or not isinstance(solicitante, str) or not solicitante.strip():
        raise ErrorValidacion("El solicitante no puede estar vacío ni contener solo espacios.")
    solicitante_limpio = solicitante.strip()

    # 3. Procesar "ahora"
    if ahora is None:
        ahora_dt = datetime.now()
    elif isinstance(ahora, str):
        try:
            ahora_dt = datetime.strptime(ahora, "%Y-%m-%d %H:%M")
        except ValueError:
            raise ErrorValidacion(f"Formato o valor inválido para 'ahora': '{ahora}'. Use AAAA-MM-DD HH:MM.")
    elif isinstance(ahora, datetime):
        ahora_dt = ahora
    else:
        raise ErrorValidacion("El parámetro 'ahora' debe ser una cadena o un objeto datetime.")

    # 4. Validar formato y valores de Fechas (R4, S2)
    try:
        inicio_dt = datetime.strptime(inicio, "%Y-%m-%d %H:%M")
    except ValueError:
        raise ErrorValidacion(f"Fecha de inicio inválida o con formato incorrecto: '{inicio}'. Use AAAA-MM-DD HH:MM.")

    try:
        fin_dt = datetime.strptime(fin, "%Y-%m-%d %H:%M")
    except ValueError:
        raise ErrorValidacion(f"Fecha de fin inválida o con formato incorrecto: '{fin}'. Use AAAA-MM-DD HH:MM.")

    # 5. Inicio estrictamente anterior al fin (R5)
    if inicio_dt >= fin_dt:
        raise ErrorValidacion("El inicio debe ser estrictamente anterior al fin.")

    # 6. Duración máxima 8 horas (S4)
    if (fin_dt - inicio_dt) > timedelta(hours=8):
        raise ErrorValidacion("La duración máxima de una reserva es de 8 horas.")

    # 7. Inicio no anterior a "ahora" (S3)
    if inicio_dt < ahora_dt:
        raise ErrorValidacion("El inicio no puede ser anterior al momento actual.")

    # 8. Anticipación máxima 90 días (S5)
    if inicio_dt > ahora_dt + timedelta(days=90):
        raise ErrorValidacion("El inicio no puede superar los 90 días desde ahora.")

    return unidad, solicitante_limpio, inicio_dt, fin_dt
