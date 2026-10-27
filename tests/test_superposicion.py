import unittest
from datetime import datetime
from reservas.superposicion import hay_superposicion

class TestSuperposicion(unittest.TestCase):

    def test_r7_limites_consecutivos_aceptados(self):
        """R7 & GEMINI.md: 10:00-11:00 y 11:00-12:00 de la misma unidad se aceptan (sin superposición)."""
        reservas = [
            {
                "id": "R01",
                "unidad": "MIC-01",
                "solicitante": "Dr. Gomez",
                "inicio": datetime(2026, 6, 1, 10, 0),
                "fin": datetime(2026, 6, 1, 11, 0),
                "estado": "activa"
            }
        ]
        # Intervalo consecutivo posterior (11:00 a 12:00)
        self.assertFalse(
            hay_superposicion(reservas, "MIC-01", datetime(2026, 6, 1, 11, 0), datetime(2026, 6, 1, 12, 0))
        )
        # Intervalo consecutivo anterior (09:00 a 10:00)
        self.assertFalse(
            hay_superposicion(reservas, "MIC-01", datetime(2026, 6, 1, 9, 0), datetime(2026, 6, 1, 10, 0))
        )

    def test_r6_superposicion_rechazada(self):
        """R6 & GEMINI.md: 10:00-11:00 y 10:30-11:30 de la misma unidad se rechazan (superposición)."""
        reservas = [
            {
                "id": "R01",
                "unidad": "MIC-01",
                "solicitante": "Dr. Gomez",
                "inicio": datetime(2026, 6, 1, 10, 0),
                "fin": datetime(2026, 6, 1, 11, 0),
                "estado": "activa"
            }
        ]
        self.assertTrue(
            hay_superposicion(reservas, "MIC-01", datetime(2026, 6, 1, 10, 30), datetime(2026, 6, 1, 11, 30))
        )

    def test_r8_unidad_distinta_aceptada(self):
        """R8 & GEMINI.md: MIC-02 de 10:00 a 11:00 se acepta aunque MIC-01 esté ocupado."""
        reservas = [
            {
                "id": "R01",
                "unidad": "MIC-01",
                "solicitante": "Dr. Gomez",
                "inicio": datetime(2026, 6, 1, 10, 0),
                "fin": datetime(2026, 6, 1, 11, 0),
                "estado": "activa"
            }
        ]
        self.assertFalse(
            hay_superposicion(reservas, "MIC-02", datetime(2026, 6, 1, 10, 0), datetime(2026, 6, 1, 11, 0))
        )

    def test_r1_reserva_cancelada_libera_horario(self):
        """R1 & GEMINI.md: Una reserva cancelada libera el horario (no bloquea)."""
        reservas = [
            {
                "id": "R01",
                "unidad": "MIC-01",
                "solicitante": "Dr. Gomez",
                "inicio": datetime(2026, 6, 1, 10, 0),
                "fin": datetime(2026, 6, 1, 11, 0),
                "estado": "cancelada"
            }
        ]
        self.assertFalse(
            hay_superposicion(reservas, "MIC-01", datetime(2026, 6, 1, 10, 30), datetime(2026, 6, 1, 11, 30))
        )

    def test_cadenas_fechas_compatibles(self):
        """Verifica que acepte cadenas 'AAAA-MM-DD HH:MM' además de datetime."""
        reservas = [
            {
                "id": "R01",
                "unidad": "MIC-01",
                "solicitante": "Dr. Gomez",
                "inicio": "2026-06-01 10:00",
                "fin": "2026-06-01 11:00",
                "estado": "activa"
            }
        ]
        self.assertTrue(
            hay_superposicion(reservas, "MIC-01", "2026-06-01 10:30", "2026-06-01 11:30")
        )
        self.assertFalse(
            hay_superposicion(reservas, "MIC-01", "2026-06-01 11:00", "2026-06-01 12:00")
        )


if __name__ == "__main__":
    unittest.main()
