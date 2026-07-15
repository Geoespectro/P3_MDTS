#!/usr/bin/env python3

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import xarray as xr

# ============================================================
# Rutas del proyecto
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSOR_SRC = PROJECT_ROOT / "Procesador" / "src"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROCESSOR_SRC))


from helpers_resampleo import (  # noqa: E402
    band_algebra,
    convert_band_to_physical_units,
    find_band_file,
    is_folder_complete,
    load_config,
    normalize_band_fixed_range,
    radiance_to_brightness_temperature,
    radiance_to_reflectance,
    validate_rgb_ranges,
)


class TestProcesador(unittest.TestCase):
    def setUp(self):
        self.config_resampleo_path = (
            PROJECT_ROOT / "Procesador" / "data" / "conf" / "config_resampleo.json"
        )

        self.config_mapa_path = (
            PROJECT_ROOT / "Procesador" / "data" / "conf" / "config_mapa.json"
        )

        self.required_bands = ["02", "05", "07", "08", "10", "13"]

        self.rgb_ranges = {
            "red": [-35.0, 5.0],
            "green": [-10.0, 90.0],
            "blue": [-0.75, 0.50],
        }

    # ========================================================
    # Configuraciones
    # ========================================================

    def test_config_resampleo_existe_y_es_valida(self):
        """
        Verifica que config_resampleo.json exista y contenga
        las claves utilizadas actualmente por el procesador.
        """
        self.assertTrue(self.config_resampleo_path.is_file())

        config = load_config(self.config_resampleo_path)

        required_keys = [
            "bands_list",
            "reference_band",
            "resample_method",
            "save_resampled_bands",
            "rgb_ranges",
        ]

        for key in required_keys:
            self.assertIn(key, config)

        self.assertEqual(config["bands_list"], self.required_bands)
        self.assertEqual(config["reference_band"], "13")
        self.assertIn(config["resample_method"], ["linear", "nearest"])

        self.assertIsInstance(config["save_resampled_bands"], bool)

        validate_rgb_ranges(config["rgb_ranges"])

    def test_config_mapa_existe_y_es_valida(self):
        """
        Verifica que config_mapa.json exista y tenga las claves principales.
        """
        self.assertTrue(self.config_mapa_path.is_file())

        with open(self.config_mapa_path, "r", encoding="utf-8") as file:
            config = json.load(file)

        required_keys = [
            "product_name",
            "output_prefix",
            "region",
            "input_rgb_base_dir",
            "output_png_dir",
            "output_gif_dir",
            "grids_dir",
            "logo_path",
            "shp_dir",
            "map_title",
        ]

        for key in required_keys:
            self.assertIn(key, config)

    # ========================================================
    # Detección de bandas
    # ========================================================

    def test_is_folder_complete_true(self):
        """
        Una carpeta con las seis bandas requeridas debe considerarse completa.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            for band in self.required_bands:
                file_path = Path(tmpdir) / f"OR_ABI-L1b-RadF-M6C{band}_G16_test.nc"
                file_path.write_text("archivo de prueba", encoding="utf-8")

            self.assertTrue(is_folder_complete(tmpdir, self.required_bands))

    def test_is_folder_complete_false_si_falta_banda(self):
        """
        Una carpeta incompleta debe detectarse correctamente.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            for band in ["02", "05", "07"]:
                file_path = Path(tmpdir) / f"OR_ABI-L1b-RadF-M6C{band}_G16_test.nc"
                file_path.write_text("archivo de prueba", encoding="utf-8")

            self.assertFalse(is_folder_complete(tmpdir, self.required_bands))

    def test_find_band_file(self):
        """
        find_band_file debe devolver el único archivo de la banda pedida.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            expected_file = Path(tmpdir) / "OR_ABI-L1b-RadF-M6C13_G16_test.nc"
            expected_file.write_text(
                "archivo de prueba",
                encoding="utf-8",
            )

            found = find_band_file(tmpdir, "13")

            self.assertEqual(Path(found), expected_file)

    def test_find_band_file_error_si_no_existe(self):
        """
        Debe lanzar FileNotFoundError si la banda no existe.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(FileNotFoundError):
                find_band_file(tmpdir, "13")

    def test_find_band_file_error_si_hay_duplicados(self):
        """
        Debe lanzar ValueError si existen dos archivos para la misma banda.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            first = Path(tmpdir) / "OR_ABI-L1b-RadF-M6C13_G16_test_1.nc"
            second = Path(tmpdir) / "OR_ABI-L1b-RadF-M6C13_G16_test_2.nc"

            first.write_text("archivo uno", encoding="utf-8")
            second.write_text("archivo dos", encoding="utf-8")

            with self.assertRaises(ValueError):
                find_band_file(tmpdir, "13")

    # ========================================================
    # Normalización y rangos
    # ========================================================

    def test_normalize_band_fixed_range(self):
        """
        Verifica que la normalización fija lleve los valores a [0, 1]
        y recorte los que quedan fuera del rango.
        """
        data = np.array(
            [
                [-5.0, 0.0],
                [5.0, 15.0],
            ],
            dtype=float,
        )

        result = normalize_band_fixed_range(
            data,
            min_value=0.0,
            max_value=10.0,
            channel_name="canal de prueba",
        )

        expected = np.array(
            [
                [0.0, 0.0],
                [0.5, 1.0],
            ],
            dtype=float,
        )

        np.testing.assert_allclose(result, expected)

    def test_normalize_band_fixed_range_error_rango_nulo(self):
        """
        No debe aceptarse un rango con mínimo igual al máximo.
        """
        data = np.array([[1.0, 2.0]], dtype=float)

        with self.assertRaises(ValueError):
            normalize_band_fixed_range(
                data,
                min_value=1.0,
                max_value=1.0,
            )

    def test_normalize_band_fixed_range_error_todos_nan(self):
        """
        No debe normalizar una matriz compuesta únicamente por NaN.
        """
        data = np.full((2, 2), np.nan)

        with self.assertRaises(ValueError):
            normalize_band_fixed_range(
                data,
                min_value=0.0,
                max_value=1.0,
            )

    def test_validate_rgb_ranges_correctos(self):
        """
        La configuración válida de rangos no debe generar errores.
        """
        validate_rgb_ranges(self.rgb_ranges)

    def test_validate_rgb_ranges_error_si_falta_canal(self):
        """
        Debe fallar si falta alguno de los canales RGB.
        """
        invalid_ranges = {
            "red": [-35.0, 5.0],
            "green": [-10.0, 90.0],
        }

        with self.assertRaises(ValueError):
            validate_rgb_ranges(invalid_ranges)

    def test_validate_rgb_ranges_error_si_minimo_no_es_menor(self):
        """
        Debe fallar si mínimo >= máximo.
        """
        invalid_ranges = {
            "red": [5.0, -35.0],
            "green": [-10.0, 90.0],
            "blue": [-0.75, 0.50],
        }

        with self.assertRaises(ValueError):
            validate_rgb_ranges(invalid_ranges)

    # ========================================================
    # Conversión física
    # ========================================================

    def test_radiance_to_reflectance(self):
        """
        Verifica la conversión simple de radiancia a reflectancia con kappa0.
        """
        radiance = np.array(
            [[1.0, 2.0], [3.0, 4.0]],
            dtype=float,
        )

        dataset = xr.Dataset(
            data_vars={
                "kappa0": ([], 0.5),
            }
        )

        result = radiance_to_reflectance(radiance, dataset)
        expected = radiance * 0.5

        np.testing.assert_allclose(result, expected)

    def test_radiance_to_reflectance_error_sin_kappa0(self):
        """
        Debe fallar si el dataset no contiene kappa0.
        """
        dataset = xr.Dataset()

        with self.assertRaises(ValueError):
            radiance_to_reflectance(
                np.array([[1.0]], dtype=float),
                dataset,
            )

    def test_radiance_to_brightness_temperature(self):
        """
        Verifica que la conversión térmica devuelva una matriz válida.
        """
        radiance = np.array(
            [[10.0, 20.0], [30.0, 40.0]],
            dtype=float,
        )

        dataset = xr.Dataset(
            data_vars={
                "planck_fk1": ([], 1000.0),
                "planck_fk2": ([], 1500.0),
                "planck_bc1": ([], 0.0),
                "planck_bc2": ([], 1.0),
            }
        )

        result = radiance_to_brightness_temperature(
            radiance,
            dataset,
        )

        self.assertEqual(result.shape, radiance.shape)
        self.assertTrue(np.isfinite(result).all())

    def test_radiance_to_brightness_temperature_error_sin_constantes(self):
        """
        Debe fallar si faltan constantes de Planck.
        """
        dataset = xr.Dataset()

        with self.assertRaises(ValueError):
            radiance_to_brightness_temperature(
                np.array([[10.0]], dtype=float),
                dataset,
            )

    def test_convert_band_to_physical_units_reflectiva(self):
        """
        B02 debe convertirse a reflectancia.
        """
        dataset = xr.Dataset(
            data_vars={
                "Rad": (
                    ["y", "x"],
                    np.array(
                        [[1.0, 2.0], [3.0, 4.0]],
                        dtype=float,
                    ),
                ),
                "kappa0": ([], 0.5),
            }
        )

        data, unit = convert_band_to_physical_units(
            "02",
            dataset,
        )

        self.assertEqual(unit, "reflectance")
        np.testing.assert_allclose(
            data,
            dataset["Rad"].values * 0.5,
        )

    def test_convert_band_to_physical_units_termica(self):
        """
        B13 debe convertirse a temperatura de brillo en Celsius.
        """
        dataset = xr.Dataset(
            data_vars={
                "Rad": (
                    ["y", "x"],
                    np.array(
                        [[10.0, 20.0], [30.0, 40.0]],
                        dtype=float,
                    ),
                ),
                "planck_fk1": ([], 1000.0),
                "planck_fk2": ([], 1500.0),
                "planck_bc1": ([], 0.0),
                "planck_bc2": ([], 1.0),
            }
        )

        data, unit = convert_band_to_physical_units(
            "13",
            dataset,
        )

        self.assertEqual(
            unit,
            "brightness_temperature_celsius",
        )
        self.assertEqual(data.shape, (2, 2))
        self.assertTrue(np.isfinite(data).all())

    def test_convert_band_to_physical_units_error_banda_desconocida(self):
        """
        Debe fallar si la banda no está clasificada.
        """
        dataset = xr.Dataset(
            data_vars={
                "Rad": (
                    ["y", "x"],
                    np.array([[1.0]], dtype=float),
                ),
            }
        )

        with self.assertRaises(ValueError):
            convert_band_to_physical_units(
                "99",
                dataset,
            )

    # ========================================================
    # Álgebra RGB
    # ========================================================

    def test_band_algebra(self):
        """
        Verifica que el álgebra RGB genere tres canales normalizados.
        """
        bands_data = {
            "02": np.array(
                [[0.10, 0.20], [0.30, 0.40]],
                dtype=float,
            ),
            "05": np.array(
                [[0.20, 0.40], [0.60, 0.80]],
                dtype=float,
            ),
            "07": np.array(
                [[-20.0, -10.0], [0.0, 10.0]],
                dtype=float,
            ),
            "08": np.array(
                [[-30.0, -20.0], [-10.0, 0.0]],
                dtype=float,
            ),
            "10": np.array(
                [[-10.0, -5.0], [0.0, 5.0]],
                dtype=float,
            ),
            "13": np.array(
                [[-30.0, -20.0], [-10.0, 0.0]],
                dtype=float,
            ),
        }

        red, green, blue = band_algebra(
            bands_data,
            self.rgb_ranges,
        )

        for channel in [red, green, blue]:
            self.assertEqual(channel.shape, (2, 2))
            self.assertGreaterEqual(
                float(np.nanmin(channel)),
                0.0,
            )
            self.assertLessEqual(
                float(np.nanmax(channel)),
                1.0,
            )

    def test_band_algebra_error_si_falta_banda(self):
        """
        Debe fallar si falta una banda requerida.
        """
        bands_data = {
            "02": np.ones((2, 2)),
            "05": np.ones((2, 2)),
            "07": np.ones((2, 2)),
            "08": np.ones((2, 2)),
            "10": np.ones((2, 2)),
            # Falta B13.
        }

        with self.assertRaises(ValueError):
            band_algebra(
                bands_data,
                self.rgb_ranges,
            )

    def test_band_algebra_error_si_canal_todos_nan(self):
        """
        Debe fallar si el resultado de algún canal contiene solo NaN.
        """
        nan_data = np.full((2, 2), np.nan)

        bands_data = {
            "02": np.ones((2, 2)),
            "05": np.ones((2, 2)),
            "07": np.ones((2, 2)),
            "08": nan_data,
            "10": nan_data,
            "13": np.ones((2, 2)),
        }

        with self.assertRaises(ValueError):
            band_algebra(
                bands_data,
                self.rgb_ranges,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
