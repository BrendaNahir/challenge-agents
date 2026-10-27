import sqlite3
from pathlib import Path
from contextlib import closing
from reservas.validacion import validar_reserva, ErrorValidacion
from reservas.superposicion import hay_superposicion

class ErrorSuperposicion(Exception):
    """Excepción propia para superposición de reservas."""
    pass

class ErrorCancelacion(Exception):
    """Excepción propia para errores al cancelar reservas."""
    pass

def _inicializar_bd(conexion):
    conexion.execute("""
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidad TEXT NOT NULL,
            solicitante TEXT NOT NULL,
            inicio TEXT NOT NULL,
            fin TEXT NOT NULL,
            estado TEXT NOT NULL
        )
    """)
    conexion.commit()

def listar_reservas(unidad=None, ruta_db="data/reservas.db"):
    """Devuelve todas las reservas (activas y canceladas), opcionalmente filtradas por unidad."""
    db_path = Path(ruta_db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        _inicializar_bd(conn)
        if unidad is not None:
            cursor = conn.execute(
                "SELECT id, unidad, solicitante, inicio, fin, estado FROM reservas WHERE unidad = ?",
                (unidad,)
            )
        else:
            cursor = conn.execute(
                "SELECT id, unidad, solicitante, inicio, fin, estado FROM reservas"
            )
        return [dict(row) for row in cursor.fetchall()]

def crear_reserva(unidad, solicitante, inicio, fin, ahora=None, ruta_db="data/reservas.db"):
    """Crea una reserva tras validar datos y comprobar que no haya superposición activa."""
    unidad_val, sol_val, inicio_dt, fin_dt = validar_reserva(unidad, solicitante, inicio, fin, ahora=ahora)
    
    db_path = Path(ruta_db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        _inicializar_bd(conn)
        
        reservas = [dict(row) for row in conn.execute("SELECT id, unidad, solicitante, inicio, fin, estado FROM reservas").fetchall()]
        
        if hay_superposicion(reservas, unidad_val, inicio_dt, fin_dt):
            raise ErrorSuperposicion(f"El intervalo {inicio} a {fin} para la unidad '{unidad}' se superpone con una reserva activa.")
        
        inicio_str = inicio_dt.strftime("%Y-%m-%d %H:%M")
        fin_str = fin_dt.strftime("%Y-%m-%d %H:%M")
        
        cursor = conn.execute(
            "INSERT INTO reservas (unidad, solicitante, inicio, fin, estado) VALUES (?, ?, ?, ?, ?)",
            (unidad_val, sol_val, inicio_str, fin_str, "activa")
        )
        conn.commit()
        nuevo_id = cursor.lastrowid
        
        return {
            "id": nuevo_id,
            "unidad": unidad_val,
            "solicitante": sol_val,
            "inicio": inicio_str,
            "fin": fin_str,
            "estado": "activa"
        }

def cancelar_reserva(id, ruta_db="data/reservas.db"):
    """Cambia el estado de una reserva a 'cancelada' sin borrarla ni modificar sus datos."""
    db_path = Path(ruta_db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        _inicializar_bd(conn)
        
        cursor = conn.execute(
            "SELECT id, estado FROM reservas WHERE id = ?",
            (id,)
        )
        reserva = cursor.fetchone()
        if not reserva:
            raise ErrorCancelacion(f"La reserva con ID {id} no existe.")
        
        if reserva["estado"] == "cancelada":
            raise ErrorCancelacion(f"La reserva con ID {id} ya está cancelada.")
        
        conn.execute(
            "UPDATE reservas SET estado = 'cancelada' WHERE id = ?",
            (id,)
        )
        conn.commit()

def consultar_disponibilidad(unidad, inicio, fin, ahora=None, ruta_db="data/reservas.db"):
    """Devuelve True si el intervalo se puede reservar (pasa validaciones y no hay superposición activa)."""
    try:
        unidad_val, _, inicio_dt, fin_dt = validar_reserva(unidad, "SolicitanteTemporal", inicio, fin, ahora=ahora)
        reservas = listar_reservas(unidad=unidad_val, ruta_db=ruta_db)
        if hay_superposicion(reservas, unidad_val, inicio_dt, fin_dt):
            return False
        return True
    except (ErrorValidacion, ErrorSuperposicion):
        return False

def reiniciar_base(ruta_db="data/reservas.db"):
    """Borra todas las reservas y reinicia el autoincremento de IDs."""
    db_path = Path(ruta_db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_path)) as conn:
        _inicializar_bd(conn)
        conn.execute("DELETE FROM reservas")
        conn.execute("DELETE FROM sqlite_sequence WHERE name='reservas'")
        conn.commit()
