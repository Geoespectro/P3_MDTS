import json
import os

import numpy as np
import xarray as xr

# ============================================================
# Utilidades generales
# ============================================================


def create_directory(path):
    """
    Crea un directorio si no existe.
    """
    os.makedirs(path, exist_ok=True)


def load_config(config_path):
    """
    Lee un archivo de configuración JSON.
    """
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_folder_complete(folder_path, required_bands):
    """
    Verifica si una carpeta contiene todos los archivos de las bandas requeridas.
    """
    if not os.path.exists(folder_path):
        return False

    existing_files = os.listdir(folder_path)

    existing_bands = set(
        file.split("M6C")[-1].split("_")[0]
        for file in existing_files
        if "M6C" in file and file.endswith(".nc")
    )

    return all(band in existing_bands for band in required_bands)


def find_band_file(folder_path, band):
    """
    Encuentra un único archivo NetCDF correspondiente a una banda específica.

    Si no existe ningún archivo para la banda, lanza FileNotFoundError.
    Si existe más de uno, lanza ValueError para evitar seleccionar un
    archivo de forma ambigua.
    """
    matches = sorted(
        file
        for file in os.listdir(folder_path)
        if f"M6C{band}" in file and file.endswith(".nc")
    )

    if not matches:
        raise FileNotFoundError(
            f"No se encontró el archivo para la banda {band} en {folder_path}"
        )

    if len(matches) > 1:
        raise ValueError(
            f"Se encontraron varios archivos para la banda {band} "
            f"en {folder_path}: {matches}"
        )

    return os.path.join(folder_path, matches[0])


# ============================================================
# Referencia espacial
# ============================================================


def get_reference_nc(ref_path):
    """
    Abre el NetCDF de referencia espacial.

    En este procesador usamos la banda 13 como referencia, porque contiene
    la grilla x/y y la información de proyección GOES necesaria para que el
    RGB final quede georreferenciado.
    """
    print(f"Obteniendo referencia de {ref_path}...")

    ds_ref = xr.open_dataset(ref_path)

    if "x" not in ds_ref or "y" not in ds_ref:
        ds_ref.close()
        raise ValueError(f"'x' o 'y' coordenadas no encontradas en {ref_path}")

    if "goes_imager_projection" not in ds_ref.variables:
        ds_ref.close()
        raise ValueError(
            f"'goes_imager_projection' no encontrada en la banda de referencia {ref_path}"
        )

    return ds_ref


# ============================================================
# Calibración física
# ============================================================


def copy_calibration_variables(ds_in, ds_out):
    """
    Copia variables de calibración necesarias para convertir radiancia
    a temperatura de brillo o reflectancia.

    Bandas térmicas:
        usan planck_fk1, planck_fk2, planck_bc1, planck_bc2.

    Bandas reflectivas:
        usan kappa0.
    """
    calibration_vars = [
        "planck_fk1",
        "planck_fk2",
        "planck_bc1",
        "planck_bc2",
        "kappa0",
        "esun",
    ]

    for var in calibration_vars:
        if var in ds_in.variables:
            ds_out[var] = ds_in[var]


def radiance_to_brightness_temperature(radiance, ds):
    """
    Convierte radiancia a temperatura de brillo en grados Celsius.

    Se aplica a bandas térmicas/emisivas:
        07, 08, 10, 13
    """
    required_vars = ["planck_fk1", "planck_fk2", "planck_bc1", "planck_bc2"]

    missing_vars = [var for var in required_vars if var not in ds.variables]

    if missing_vars:
        raise ValueError(
            "Constantes de Planck no disponibles en el dataset "
            f"para convertir a temperatura de brillo. Faltan: {missing_vars}"
        )

    fk1 = ds["planck_fk1"].values
    fk2 = ds["planck_fk2"].values
    bc1 = ds["planck_bc1"].values
    bc2 = ds["planck_bc2"].values

    radiance_safe = np.where(radiance <= 0, np.nan, radiance)

    brightness_temperature_kelvin = (
        fk2 / np.log((fk1 / radiance_safe) + 1) - bc1
    ) / bc2

    brightness_temperature_celsius = brightness_temperature_kelvin - 273.15

    return brightness_temperature_celsius


def radiance_to_reflectance(radiance, ds):
    """
    Convierte radiancia a reflectancia para bandas reflectivas GOES ABI.

    Se aplica a bandas:
        02, 05

    GOES ABI L1b incluye la variable kappa0, que permite realizar
    esta conversión.
    """
    if "kappa0" not in ds.variables:
        raise ValueError(
            "Variable kappa0 no disponible para convertir radiancia a reflectancia."
        )

    kappa0 = ds["kappa0"].values

    reflectance = radiance * kappa0

    return reflectance


def convert_band_to_physical_units(band, ds_resampled):
    """
    Convierte cada banda a la unidad física correcta antes del álgebra RGB.

    Bandas reflectivas:
        02, 05 -> reflectancia

    Bandas térmicas/emisivas:
        07, 08, 10, 13 -> temperatura de brillo en °C

    Retorna:
        data_convertida, nombre_unidad
    """
    if "Rad" not in ds_resampled.variables:
        raise ValueError("Variable 'Rad' no encontrada en banda resampleada.")

    radiance = ds_resampled["Rad"].values

    reflective_bands = ["02", "05"]
    thermal_bands = ["07", "08", "10", "13"]

    if band in reflective_bands:
        data = radiance_to_reflectance(radiance, ds_resampled)
        unit = "reflectance"

    elif band in thermal_bands:
        data = radiance_to_brightness_temperature(radiance, ds_resampled)
        unit = "brightness_temperature_celsius"

    else:
        raise ValueError(f"Banda {band} no clasificada para conversión física.")

    return data, unit


# ============================================================
# Resampleo
# ============================================================


def resample_band(
    input_path, output_path=None, ref_x=None, ref_y=None, method="linear"
):
    """
    Resamplea la variable Rad de una banda a la grilla de referencia.

    La grilla de referencia viene de la banda 13.

    Si output_path tiene una ruta, guarda la banda resampleada en disco.
    Si output_path es None, trabaja solo en memoria y no guarda archivo intermedio.
    """
    print(f"Resampleando {input_path}...")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Archivo {input_path} no encontrado.")

    if ref_x is None or ref_y is None:
        raise ValueError("ref_x y ref_y son requeridos para el resampleo.")

    ds = xr.open_dataset(input_path)

    try:
        if "Rad" not in ds.variables:
            raise ValueError(f"'Rad' variable no encontrada en {input_path}.")

        resampled_data = ds["Rad"].interp(
            x=ref_x,
            y=ref_y,
            method=method,
        )

        ds_out = xr.Dataset({"Rad": resampled_data})

        ds_out["Rad"].attrs = ds["Rad"].attrs.copy()

        copy_calibration_variables(ds, ds_out)

        if output_path is not None:
            ds_out.to_netcdf(output_path)
            print(f"Banda resampleada guardada en: {output_path}")
        else:
            print("Banda resampleada en memoria. No se guardó archivo intermedio.")

        return ds_out

    finally:
        ds.close()


# ============================================================
# Álgebra RGB
# ============================================================


def normalize_band_fixed_range(band, min_value, max_value, channel_name="canal"):
    """
    Normaliza una banda usando un rango físico fijo.

    Ventaja:
        Mantiene colores comparables entre imágenes sucesivas.

    Si un valor cae fuera del rango, se recorta a [0, 1].
    """
    if max_value == min_value:
        raise ValueError(
            f"El rango de normalización de {channel_name} no puede tener "
            "min_value == max_value."
        )

    if np.all(np.isnan(band)):
        raise ValueError(
            f"No se puede normalizar {channel_name}: todos los valores son NaN."
        )

    normalized = (band - min_value) / (max_value - min_value)
    normalized = np.clip(normalized, 0.0, 1.0)

    print(
        f"Normalizando {channel_name} con rango fijo: "
        f"min_fijo={min_value}, max_fijo={max_value}, "
        f"min_result={np.nanmin(normalized)}, max_result={np.nanmax(normalized)}"
    )

    return normalized


def validate_rgb_ranges(rgb_ranges):
    """
    Valida la estructura de rangos RGB recibida desde la configuración.
    """
    required_channels = ["red", "green", "blue"]

    if not isinstance(rgb_ranges, dict):
        raise ValueError("'rgb_ranges' debe ser un objeto JSON.")

    for channel in required_channels:
        if channel not in rgb_ranges:
            raise ValueError(f"Falta el rango del canal '{channel}' en 'rgb_ranges'.")

        channel_range = rgb_ranges[channel]

        if not isinstance(channel_range, list) or len(channel_range) != 2:
            raise ValueError(
                f"El rango de '{channel}' debe ser una lista [mínimo, máximo]."
            )

        min_value, max_value = channel_range

        if not isinstance(min_value, (int, float)) or not isinstance(
            max_value, (int, float)
        ):
            raise ValueError(
                f"Los valores del rango de '{channel}' deben ser numéricos."
            )

        if min_value >= max_value:
            raise ValueError(f"El rango de '{channel}' debe cumplir mínimo < máximo.")


def band_algebra(bands_data, rgb_ranges):
    """
    Aplica el álgebra de bandas para generar el RGB de tormentas severas.

    Adaptación GOES-16 del RGB severo tipo SEVIRI:

        Red   = B08 - B10
        Green = B07 - B13
        Blue  = B05 - B02

    Importante:
        bands_data ya debe venir convertido a unidades físicas correctas.

        B08, B10, B07, B13 -> temperatura de brillo en °C
        B05, B02           -> reflectancia

    Los rangos de normalización se reciben desde config_resampleo.json.
    """
    required_bands = ["02", "05", "07", "08", "10", "13"]

    for band in required_bands:
        if band not in bands_data:
            raise ValueError(f"Falta la banda {band} para aplicar álgebra RGB.")

    validate_rgb_ranges(rgb_ranges)

    red_raw = bands_data["08"] - bands_data["10"]
    green_raw = bands_data["07"] - bands_data["13"]
    blue_raw = bands_data["05"] - bands_data["02"]

    if np.all(np.isnan(red_raw)):
        raise ValueError("El canal rojo resultante contiene únicamente valores NaN.")

    if np.all(np.isnan(green_raw)):
        raise ValueError("El canal verde resultante contiene únicamente valores NaN.")

    if np.all(np.isnan(blue_raw)):
        raise ValueError("El canal azul resultante contiene únicamente valores NaN.")

    print(
        "Rangos crudos del álgebra RGB: "
        f"R min={np.nanmin(red_raw)}, max={np.nanmax(red_raw)}, "
        f"G min={np.nanmin(green_raw)}, max={np.nanmax(green_raw)}, "
        f"B min={np.nanmin(blue_raw)}, max={np.nanmax(blue_raw)}"
    )

    red = normalize_band_fixed_range(
        red_raw,
        min_value=rgb_ranges["red"][0],
        max_value=rgb_ranges["red"][1],
        channel_name="canal rojo",
    )

    green = normalize_band_fixed_range(
        green_raw,
        min_value=rgb_ranges["green"][0],
        max_value=rgb_ranges["green"][1],
        channel_name="canal verde",
    )

    blue = normalize_band_fixed_range(
        blue_raw,
        min_value=rgb_ranges["blue"][0],
        max_value=rgb_ranges["blue"][1],
        channel_name="canal azul",
    )

    print(
        "Álgebra de bandas con rangos fijos configurados: "
        f"R={np.nanmean(red)}, "
        f"G={np.nanmean(green)}, "
        f"B={np.nanmean(blue)}"
    )

    return red, green, blue


# ============================================================
# Guardado NetCDF RGB georreferenciado
# ============================================================


def save_rgb_to_netcdf(red, green, blue, output_path, interval_name, ds_ref):
    """
    Guarda los canales RGB en un archivo NetCDF conservando la georreferencia
    de la banda de referencia.

    Esto corrige el problema de tener una imagen RGB sin ubicación espacial.
    """
    print(f"Guardando resultado RGB con georreferencia en: {output_path}")

    ds = xr.Dataset(
        data_vars={
            "Red": (["y", "x"], red),
            "Green": (["y", "x"], green),
            "Blue": (["y", "x"], blue),
        },
        coords={
            # Se copian los valores sin heredar la codificación interna
            # del NetCDF original.
            "y": ("y", ds_ref["y"].values.copy()),
            "x": ("x", ds_ref["x"].values.copy()),
        },
        attrs=ds_ref.attrs.copy(),
    )

    # Conserva los atributos geoespaciales de las coordenadas.
    ds["x"].attrs = ds_ref["x"].attrs.copy()
    ds["y"].attrs = ds_ref["y"].attrs.copy()

    # Evita heredar codificaciones enteras con scale_factor/add_offset.
    ds["x"].encoding.clear()
    ds["y"].encoding.clear()

    ds.attrs["interval_name"] = interval_name
    ds.attrs["rgb_processing"] = (
        "RGB severo GOES-16. "
        "Bandas térmicas convertidas a temperatura de brillo, "
        "bandas reflectivas convertidas a reflectancia, "
        "resampleadas a grilla de banda 13 y guardadas con georreferencia."
    )

    ds.attrs["rgb_red"] = "B08 - B10 usando temperatura de brillo en Celsius"
    ds.attrs["rgb_green"] = "B07 - B13 usando temperatura de brillo en Celsius"
    ds.attrs["rgb_blue"] = "B05 - B02 usando reflectancia"

    variables_geo = [
        "goes_imager_projection",
        "geospatial_lat_lon_extent",
        "nominal_satellite_subpoint_lat",
        "nominal_satellite_subpoint_lon",
        "nominal_satellite_height",
        "x_image",
        "y_image",
        "x_image_bounds",
        "y_image_bounds",
    ]

    for var in variables_geo:
        if var in ds_ref.variables:
            ds[var] = ds_ref[var]

    if "goes_imager_projection" in ds.variables:
        for channel in ["Red", "Green", "Blue"]:
            ds[channel].attrs["grid_mapping"] = "goes_imager_projection"
            ds[channel].attrs["valid_range"] = [0.0, 1.0]

    ds["Red"].attrs["description"] = "Canal rojo normalizado: B08 - B10"
    ds["Green"].attrs["description"] = "Canal verde normalizado: B07 - B13"
    ds["Blue"].attrs["description"] = "Canal azul normalizado: B05 - B02"

    ds.to_netcdf(output_path)

    print(f"Archivo RGB guardado exitosamente en: {output_path}")
