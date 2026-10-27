import unittest
import tempfile
from pathlib import Path
from reservas.repositorio import (
    crear_reserva,
    cancelar_reserva,
    listar_reservas,
    consultar_disponibilidad,
    reiniciar_base,
    ErrorSuperposicion,
    ErrorCancelacion
)
from reservas.validacion import ErrorValidacion

class TestRepositorio(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.ruta_db = str(Path(self.tmp_dir.name) / "test_reservas.db")
        self.ahora = "2026-06-01 10:00"

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_crear_reserva_valida(self):
        """Creación válida de una reserva."""
        reserva = crear_reserva(
            "MIC-01", "Dra. Gomez", "2026-06-01 11:00", "2026-06-01 12:00",
            ahora=self.ahora, ruta_db=self.ruta_db
        )
        self.assertEqual(reserva["id"], 1)
        self.assertEqual(reserva["unidad"], "MIC-01")
        self.assertEqual(reserva["solicitante"], "Dra. Gomez")
        self.assertEqual(reserva["inicio"], "2026-06-01 11:00")
        self.assertEqual(reserva["fin"], "2026-06-01 12:00")
        self.assertEqual(reserva["estado"], "activa")

        reservas = listar_reservas(ruta_db=self.ruta_db)
        self.assertEqual(len(reservas), 1)

    def test_superposicion_rechazada(self):
        """Superposición con reserva activa rechazada con ErrorSuperposicion."""
        crear_reserva(
            "MIC-01", "Dra. Gomez", "2026-06-01 11:00", "2026-06-01 13:00",
            ahora=self.ahora, ruta_db=self.ruta_db
        )
        # Superposición parcial (12:00-14:00)
        with self.assertRaises(ErrorSuperposicion):
            crear_reserva(
                "MIC-01", "Dr. Perez", "2026-06-01 12:00", "2026-06-01 14:00",
                ahora=self.ahora, ruta_db=self.ruta_db
            )

    def test_limites_consecutivos_aceptados(self):
        """Límites consecutivos aceptados (fin de una == inicio de otra)."""
        crear_reserva(
            "MIC-01", "Dra. Gomez", "2026-06-01 10:00", "2026-06-01 11:00",
            ahora=self.ahora, ruta_db=self.ruta_db
        )
        # 11:00-12:00 debe aceptarse (consecutivo)
        reserva2 = crear_reserva(
            "MIC-01", "Dr. Perez", "2026-06-01 11:00", "2026-06-01 12:00",
            ahora=self.ahora, ruta_db=self.ruta_db
        )
        self.assertEqual(reserva2["id"], 2)

    def test_unidades_distintas_simultaneas(self):
        """Unidades distintas simultáneas permitidas."""
        crear_reserva(
            "MIC-01", "Dra. Gomez", "2026-06-01 11:00", "2026-06-01 12:00",
            ahora=self.ahora, ruta_db=self.ruta_db
        )
        # MIC-02 en el mismo horario debe aceptarse
        reserva2 = crear_reserva(
            "MIC-02", "Dr. Perez", "2026-06-01 11:00", "2026-06-01 12:00",
            ahora=self.ahora, ruta_db=self.ruta_db
        )
        self.assertEqual(reserva2["unidad"], "MIC-02")

    def test_cancelacion_conserva_registro_y_libera_horario(self):
        """Cancelar conserva el registro, cambia estado a 'cancelada' y libera el horario."""
        r1 = crear_reserva(
            "MIC-01", "Dra. Gomez", "2026-06-01 11:00", "2026-06-01 12:00",
            ahora=self.ahora, ruta_db=self.ruta_db
        )
        
        cancelar_reserva(r1["id"], ruta_db=self.ruta_db)

        # Verificar que el registro sigue enlistar_reservas con estado 'cancelada'
        reservas = listar_reservas(ruta_db=self.ruta_db)
        self.assertEqual(len(reservas), 1)
        self.assertEqual(reservas[0]["estado"], "cancelada")

        # Verificar que el horario queda libre para otra reserva
        r2 = crear_reserva(
            "MIC-01", "Dr. Perez", "2026-06-01 11:00", "2026-06-01 12:00",
            ahora=self.ahora, ruta_db=self.ruta_db
        )
        self.assertEqual(r2["id"], 2)

    def test_cancelar_dos_veces(self):
        """Cancelar una reserva ya cancelada lanza ErrorCancelacion."""
        r1 = crear_reserva(
            "MIC-01", "Dra. Gomez", "2026-06-01 11:00", "2026-06-01 12:00",
            ahora=self.ahora, ruta_db=self.ruta_db
        )
        cancelar_reserva(r1["id"], ruta_db=self.ruta_db)

        with self.assertRaises(ErrorCancelacion):
            cancelar_reserva(r1["id"], ruta_db=self.ruta_db)

    def test_cancelar_id_inexistente(self):
        """Cancelar un ID inexistente lanza ErrorCancelacion."""
        with self.assertRaises(ErrorCancelacion):
            cancelar_reserva(999, ruta_db=self.ruta_db)

    def test_consultar_disponibilidad_coincide_con_crear(self):
        """consultar_disponibilidad coincide exactamente con si crear_reserva puede tener éxito."""
        # Inicialmente disponible
        self.assertTrue(consultar_disponibilidad("MIC-01", "2026-06-01 11:00", "2026-06-01 12:00", ahora=self.ahora, ruta_db=self.ruta_db))

        crear_reserva(
            "MIC-01", "Dra. Gomez", "2026-06-01 11:00", "2026-06-01 12:00",
            ahora=self.ahora, ruta_db=self.ruta_db
        )

        # Ahora no disponible (superposición)
        self.assertFalse(consultar_disponibilidad("MIC-01", "2026-06-01 11:30", "2026-06-01 12:30", ahora=self.ahora, ruta_db=self.ruta_db))

        # Parámetros inválidos (ej. unidad inexistente) deben retornar False en disponibilidad
        self.assertFalse(consultar_disponibilidad("MIC-99", "2026-06-01 11:00", "2026-06-01 12:00", ahora=self.ahora, ruta_db=self.ruta_db))

    def test_reiniciar_base(self):
        """reiniciar_base borra todas las reservas y reinicia el autoincremento de IDs."""
        r1 = crear_reserva(
            "MIC-01", "Dra. Gomez", "2026-06-01 11:00", "2026-06-01 12:00",
            ahora=self.ahora, ruta_db=self.ruta_db
        )
        self.assertEqual(r1["id"], 1)

        reiniciar_base(ruta_db=self.ruta_db)
        reservas = listar_reservas(ruta_db=self.ruta_db)
        self.assertEqual(len(reservas), 0)

        # Verificar que el siguiente id vuelve a ser 1
        r2 = crear_reserva(
            "MIC-02", "Dr. Perez", "2026-06-01 11:00", "2026-06-01 12:00",
            ahora=self.ahora, ruta_db=self.ruta_db
        )
        self.assertEqual(r2["id"], 1)


if __name__ == "__main__":
    unittest.main()
