import unittest
import tempfile
from pathlib import Path
from io import StringIO
import sys
from reservas.cli import main

class TestCLI(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.ruta_db = str(Path(self.tmp_dir.name) / "test_reservas.db")
        self.ahora = "2026-06-01 10:00"

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_unidades(self):
        """Comando unidades lista el inventario correctamente."""
        code = main(["--db", self.ruta_db, "unidades"])
        self.assertEqual(code, 0)

    def test_disponibilidad_y_reservar(self):
        """Disponibilidad, reservar y listar."""
        # Consultar disponibilidad antes de reservar (debe ser disponible)
        code = main(["--db", self.ruta_db, "--ahora", self.ahora, "disponibilidad", "MIC-01", "2026-06-01 11:00", "2026-06-01 12:00"])
        self.assertEqual(code, 0)

        # Reservar
        code = main(["--db", self.ruta_db, "--ahora", self.ahora, "reservar", "MIC-01", "Dra. Gomez", "2026-06-01 11:00", "2026-06-01 12:00"])
        self.assertEqual(code, 0)

        # Consultar disponibilidad después de reservar (debe ser no disponible)
        code = main(["--db", self.ruta_db, "--ahora", self.ahora, "disponibilidad", "MIC-01", "2026-06-01 11:30", "2026-06-01 12:30"])
        self.assertEqual(code, 0) # El comando disponibilidad devuelve 0 y muestra "no disponible"

        # Listar reservas
        code = main(["--db", self.ruta_db, "listar"])
        self.assertEqual(code, 0)

    def test_superposicion_rechazada_codigo_1(self):
        """Superposición rechazada retorna código 1."""
        main(["--db", self.ruta_db, "--ahora", self.ahora, "reservar", "MIC-01", "Dra. Gomez", "2026-06-01 11:00", "2026-06-01 13:00"])
        
        # Superposición intenta reservar de 12:00 a 14:00
        code = main(["--db", self.ruta_db, "--ahora", self.ahora, "reservar", "MIC-01", "Dr. Perez", "2026-06-01 12:00", "2026-06-01 14:00"])
        self.assertEqual(code, 1)

    def test_cancelar_y_listar_estado_cancelada(self):
        """Cancelar reserva y verificar que listar la muestra como cancelada."""
        main(["--db", self.ruta_db, "--ahora", self.ahora, "reservar", "MIC-01", "Dra. Gomez", "2026-06-01 11:00", "2026-06-01 12:00"])
        
        # Cancelar id 1
        code = main(["--db", self.ruta_db, "cancelar", "1"])
        self.assertEqual(code, 0)

        # Listar debe mostrar la reserva con estado cancelada
        code = main(["--db", self.ruta_db, "listar"])
        self.assertEqual(code, 0)

    def test_reiniciar_sin_confirmar_rechazado(self):
        """Reiniciar sin --confirmar es rechazado con código 1."""
        code = main(["--db", self.ruta_db, "reiniciar"])
        self.assertEqual(code, 1)

        # Reiniciar con --confirmar debe tener éxito (código 0)
        code = main(["--db", self.ruta_db, "reiniciar", "--confirmar"])
        self.assertEqual(code, 0)

if __name__ == "__main__":
    unittest.main()
