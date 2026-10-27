import unittest
from datetime import datetime, timedelta
from reservas.validacion import validar_reserva, ErrorValidacion

class TestValidacionReserva(unittest.TestCase):

    def setUp(self):
        # Hora fija de referencia para pruebas sin depender del reloj
        self.ahora = "2026-06-01 10:00"

    def test_r2_unidad_existente(self):
        """R2: La unidad debe existir en el inventario."""
        # Unidad existente debe pasar
        unidad, solicitante, inicio, fin = validar_reserva(
            "MIC-01", "Dra. Gomez", "2026-06-01 11:00", "2026-06-01 12:00", ahora=self.ahora
        )
        self.assertEqual(unidad, "MIC-01")

        # Unidad inexistente debe lanzar ErrorValidacion
        with self.assertRaises(ErrorValidacion):
            validar_reserva("MIC-99", "Dra. Gomez", "2026-06-01 11:00", "2026-06-01 12:00", ahora=self.ahora)

    def test_r3_solicitante_valido(self):
        """R3 & S9: Solicitante no vacío ni solo espacios; se limpia al inicio y final."""
        # Solicitante con espacios alrededor debe ser limpiado (S9)
        _, solicitante_limpio, _, _ = validar_reserva(
            "MIC-01", "  Dr. Perez  ", "2026-06-01 11:00", "2026-06-01 12:00", ahora=self.ahora
        )
        self.assertEqual(solicitante_limpio, "Dr. Perez")

        # Solicitante vacío
        with self.assertRaises(ErrorValidacion):
            validar_reserva("MIC-01", "", "2026-06-01 11:00", "2026-06-01 12:00", ahora=self.ahora)

        # Solicitante con solo espacios
        with self.assertRaises(ErrorValidacion):
            validar_reserva("MIC-01", "   ", "2026-06-01 11:00", "2026-06-01 12:00", ahora=self.ahora)

    def test_r4_s2_formato_fechas(self):
        """R4 & S2: Formato y valores de fecha válidos (AAAA-MM-DD HH:MM)."""
        # Formato inválido
        with self.assertRaises(ErrorValidacion):
            validar_reserva("MIC-01", "Dr. Perez", "01-06-2026 11:00", "2026-06-01 12:00", ahora=self.ahora)

        # Valores inválidos (ej. febrero 30)
        with self.assertRaises(ErrorValidacion):
            validar_reserva("MIC-01", "Dr. Perez", "2026-02-30 11:00", "2026-02-30 12:00", ahora="2026-02-01 10:00")

    def test_r5_inicio_anterior_fin(self):
        """R5: El inicio debe ser estrictamente anterior al fin."""
        # Inicio igual al fin
        with self.assertRaises(ErrorValidacion):
            validar_reserva("MIC-01", "Dr. Perez", "2026-06-01 11:00", "2026-06-01 11:00", ahora=self.ahora)

        # Inicio posterior al fin
        with self.assertRaises(ErrorValidacion):
            validar_reserva("MIC-01", "Dr. Perez", "2026-06-01 12:00", "2026-06-01 11:00", ahora=self.ahora)

    def test_s4_duracion_maxima(self):
        """S4: Duración máxima de una reserva: 8 horas."""
        # Exactamente 8 horas debe aceptarse
        validar_reserva("MIC-01", "Dr. Perez", "2026-06-01 11:00", "2026-06-01 19:00", ahora=self.ahora)

        # Más de 8 horas (ej. 8h 1m) debe rechazarse
        with self.assertRaises(ErrorValidacion):
            validar_reserva("MIC-01", "Dr. Perez", "2026-06-01 11:00", "2026-06-01 19:01", ahora=self.ahora)

    def test_s3_inicio_no_anterior_ahora(self):
        """S3: No se permiten reservas con inicio anterior al momento actual."""
        # Inicio en el pasado respecto a "ahora"
        with self.assertRaises(ErrorValidacion):
            validar_reserva("MIC-01", "Dr. Perez", "2026-06-01 09:59", "2026-06-01 11:00", ahora=self.ahora)

        # Inicio igual a "ahora" debe aceptarse
        validar_reserva("MIC-01", "Dr. Perez", "2026-06-01 10:00", "2026-06-01 11:00", ahora=self.ahora)

    def test_s5_anticipacion_maxima(self):
        """S5: Anticipación máxima: el inicio no puede superar los 90 días desde ahora."""
        ahora_dt = datetime.strptime(self.ahora, "%Y-%m-%d %H:%M")
        
        # Exactamente 90 días después debe aceptarse
        inicio_90d = (ahora_dt + timedelta(days=90)).strftime("%Y-%m-%d %H:%M")
        fin_90d = (ahora_dt + timedelta(days=90, hours=1)).strftime("%Y-%m-%d %H:%M")
        validar_reserva("MIC-01", "Dr. Perez", inicio_90d, fin_90d, ahora=self.ahora)

        # 90 días y 1 minuto después debe rechazarse
        inicio_mas_90d = (ahora_dt + timedelta(days=90, minutes=1)).strftime("%Y-%m-%d %H:%M")
        fin_mas_90d = (ahora_dt + timedelta(days=90, hours=2)).strftime("%Y-%m-%d %H:%M")
        with self.assertRaises(ErrorValidacion):
            validar_reserva("MIC-01", "Dr. Perez", inicio_mas_90d, fin_mas_90d, ahora=self.ahora)


if __name__ == "__main__":
    unittest.main()
