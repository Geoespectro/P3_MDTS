import json
import os
import sys
import unittest
from pathlib import Path

# Agrega la raíz del proyecto al PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


class TestDescarga(unittest.TestCase):
    def setUp(self):
        self.descarga_dir = PROJECT_ROOT / "descarga"
        self.setup_path = self.descarga_dir / "setup.json"
        self.data_dir = self.descarga_dir / "data"
        self.temp_dir = self.descarga_dir / "temp"
        self.logs_dir = self.descarga_dir / "logs"
        self.db_dir = self.descarga_dir / "db"

    def test_estructura_descarga_existe(self):
        """
        Verifica que exista la estructura principal de descarga.
        """
        self.assertTrue(self.descarga_dir.exists())
        self.assertTrue((self.descarga_dir / "goes16Download.py").exists())
        self.assertTrue((self.descarga_dir / "helpers.py").exists())

    def test_setup_json_existe_y_es_valido(self):
        """
        Verifica que setup.json exista y sea un JSON válido.
        """
        self.assertTrue(self.setup_path.exists())

        with open(self.setup_path, "r") as f:
            config = json.load(f)

        self.assertIsInstance(config, dict)

    def test_carpetas_de_trabajo_existen_o_pueden_crearse(self):
        """
        Verifica que las carpetas de trabajo de descarga existan o puedan crearse.
        """
        for folder in [self.data_dir, self.temp_dir, self.logs_dir, self.db_dir]:
            folder.mkdir(parents=True, exist_ok=True)
            self.assertTrue(folder.exists())

    def test_helpers_descarga_importable(self):
        """
        Verifica que el módulo helpers.py de descarga pueda importarse.
        """
        try:
            import descarga.helpers  # noqa: F401
        except Exception as e:
            self.fail(f"No se pudo importar descarga.helpers: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
