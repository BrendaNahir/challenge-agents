from datetime import datetime

def _asegurar_datetime(val):
    if isinstance(val, str):
        return datetime.strptime(val, "%Y-%m-%d %H:%M")
    return val

def hay_superposicion(reservas, unidad, inicio, fin):
    """Verifica si el intervalo [inicio, fin) se superpone con alguna reserva ACTIVA
    de la misma unidad.

    Reglas aplicadas:
    - R1: Una reserva activa ocupa el intervalo; una cancelada no bloquea.
    - R6: Se rechaza la superposición con reservas activas de la misma unidad.
    - R7: Se permiten límites consecutivos (el fin de una = el inicio de otra).
    - R8: Se permiten reservas simultáneas de unidades distintas.
    - Adaptación GEMINI.md: fin == inicio del otro se acepta.
      Condición de superposición: inicio_nuevo < fin_existente AND fin_nuevo > inicio_existente.

    Parámetros:
    - reservas: list[dict]
    - unidad: str
    - inicio: datetime o str ("AAAA-MM-DD HH:MM")
    - fin: datetime o str ("AAAA-MM-DD HH:MM")

    Retorna:
    - True si hay superposición con reserva activa de la misma unidad, False en caso contrario.
    """
    inicio_nuevo = _asegurar_datetime(inicio)
    fin_nuevo = _asegurar_datetime(fin)

    for r in reservas:
        # Solo evaluar la misma unidad (R8) y reservas activas (R1)
        if r.get("unidad") != unidad:
            continue
        if r.get("estado") != "activa":
            continue

        inicio_existente = _asegurar_datetime(r["inicio"])
        fin_existente = _asegurar_datetime(r["fin"])

        # Condición de superposición:
        # inicio_nuevo < fin_existente AND fin_nuevo > inicio_existente
        if inicio_nuevo < fin_existente and fin_nuevo > inicio_existente:
            return True

    return False
