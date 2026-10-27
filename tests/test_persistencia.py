import unittest
import tempfile
import subprocess
import sys
import os
from pathlib import Path

class TestPersistencia(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.ruta_db = str(Path(self.tmp_dir.name) / "test_persistencia.db")
        self.ahora = "2026-06-01 10:00"
        self.repo_root = str(Path(__file__).resolve().parent.parent)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def run_cmd(self, args, check=True):
        cmd = [sys.executable, "-m", "reservas", "--db", self.ruta_db] + args
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        result = subprocess.run(
            cmd,
            cwd=self.repo_root,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        if check and result.returncode != 0:
            raise RuntimeError(f"Comando falló {' '.join(cmd)}: {result.stderr or result.stdout}")
        return result

    def test_persistencia_activa_y_cancelada(self):
        """Comprueba que reservas activas y canceladas sobreviven al reinicio y operan correctamente."""
        # 1. Crear dos reservas con procesos separados
        res1 = self.run_cmd(["--ahora", self.ahora, "reservar", "MIC-01", "Dra. Gomez", "2026-06-01 11:00", "2026-06-01 12:00"])
        self.assertEqual(res1.returncode, 0)

        res2 = self.run_cmd(["--ahora", self.ahora, "reservar", "MIC-01", "Dr. Perez", "2026-06-01 13:00", "2026-06-01 14:00"])
        self.assertEqual(res2.returncode, 0)

        # 2. Cancelar la primera reserva (id 1) en otro proceso
        res_cancel = self.run_cmd(["cancelar", "1"])
        self.assertEqual(res_cancel.returncode, 0)

        # 3. Ejecutar "listar" en un proceso nuevo y comprobar ambas reservas con sus estados
        res_listar = self.run_cmd(["listar"])
        self.assertEqual(res_listar.returncode, 0)
        output = res_listar.stdout
        lineas = [l for l in output.splitlines() if l.strip()]
        self.assertEqual(len(lineas), 2)
        linea_1 = next((l for l in lineas if l.startswith("ID: 1")), None)
        self.assertIsNotNone(linea_1)
        self.assertIn("Dra. Gomez", linea_1)
        self.assertIn("2026-06-01 11:00", linea_1)
        self.assertIn("2026-06-01 12:00", linea_1)
        self.assertIn("cancelada", linea_1.lower())

        linea_2 = next((l for l in lineas if l.startswith("ID: 2")), None)
        self.assertIsNotNone(linea_2)
        self.assertIn("Dr. Perez", linea_2)
        self.assertIn("2026-06-01 13:00", linea_2)
        self.assertIn("2026-06-01 14:00", linea_2)
        self.assertIn("activa", linea_2.lower())

        # 4. Comprobar que reservar el mismo horario de la cancelada (11:00-12:00) funciona en otro proceso
        res_rebook_cancelada = self.run_cmd(["--ahora", self.ahora, "reservar", "MIC-01", "Dr. Nuevo", "2026-06-01 11:00", "2026-06-01 12:00"])
        self.assertEqual(res_rebook_cancelada.returncode, 0)

        # 5. Comprobar que reservar el de la activa (13:00-14:00) sigue fallando con código 1 en otro proceso
        res_rebook_activa = self.run_cmd(["--ahora", self.ahora, "reservar", "MIC-01", "Dr. Otro", "2026-06-01 13:00", "2026-06-01 14:00"], check=False)
        self.assertEqual(res_rebook_activa.returncode, 1)

if __name__ == "__main__":
    unittest.main()
