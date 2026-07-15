import argparse
import os

import numpy as np
from helpers_resampleo import (
    band_algebra,
    convert_band_to_physical_units,
    create_directory,
    find_band_file,
    get_reference_nc,
    is_folder_complete,
    load_config,
    resample_band,
    save_rgb_to_netcdf,
)

PROCESSOR_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.dirname(PROCESSOR_DIR)


def process_single_interval(
    interval,
    input_base_dir,
    resampled_base_dir,
    rgb_base_dir,
    config,
):
    """
    Procesa un único intervalo:

    1. Valida que la carpeta tenga las 6 bandas requeridas.
    2. Toma la banda 13 como referencia espacial.
    3. Resamplea todas las bandas a la grilla de la banda 13.
    4. Convierte cada banda a su unidad física correspondiente:
        - B02 y B05 -> reflectancia
        - B07, B08, B10 y B13 -> temperatura de brillo en °C
    5. Aplica el álgebra RGB.
    6. Guarda el RGB final en NetCDF con georreferencia.

    Si save_resampled_bands=false en el JSON, no guarda las bandas
    resampleadas intermedias y trabaja en memoria.
    """
    bands = config["bands_list"]
    reference_band = config["reference_band"]
    method = config["resample_method"]
    rgb_ranges = config["rgb_ranges"]

    save_resampled_bands = config.get("save_resampled_bands", True)

    interval_path = os.path.join(input_base_dir, interval)

    if not os.path.isdir(interval_path):
        print(f"Intervalo {interval} no existe en {input_base_dir}. Omitiendo...")
        return False

    if not is_folder_complete(interval_path, bands):
        print(f"Intervalo {interval} incompleto. Omitiendo...")
        return False

    resampled_interval_dir = os.path.join(resampled_base_dir, interval)
    rgb_interval_dir = os.path.join(rgb_base_dir, interval)

    if save_resampled_bands:
        create_directory(resampled_interval_dir)

    create_directory(rgb_interval_dir)

    try:
        ref_path = find_band_file(interval_path, reference_band)
        ds_ref = get_reference_nc(ref_path)
        ref_x = ds_ref["x"].values
        ref_y = ds_ref["y"].values
    except Exception as e:
        print(f"Error al obtener referencia espacial del intervalo {interval}: {e}")
        return False

    bands_data = {}
    bands_units = {}

    try:
        for band in bands:
            try:
                input_band_path = find_band_file(interval_path, band)

                original_file_name = os.path.basename(input_band_path)

                if save_resampled_bands:
                    output_band_path = os.path.join(
                        resampled_interval_dir,
                        original_file_name,
                    )
                else:
                    output_band_path = None

                ds_resampled = resample_band(
                    input_path=input_band_path,
                    output_path=output_band_path,
                    ref_x=ref_x,
                    ref_y=ref_y,
                    method=method,
                )

                try:
                    band_data, band_unit = convert_band_to_physical_units(
                        band,
                        ds_resampled,
                    )

                    bands_data[band] = band_data
                    bands_units[band] = band_unit

                    print(
                        f"Banda {band} convertida a {band_unit}: "
                        f"min={np.nanmin(bands_data[band])}, "
                        f"max={np.nanmax(bands_data[band])}, "
                        f"mean={np.nanmean(bands_data[band])}"
                    )

                finally:
                    ds_resampled.close()

            except Exception as e:
                print(f"Error procesando banda {band} del intervalo {interval}: {e}")
                return False

        print(f"Unidades físicas usadas para el intervalo {interval}: {bands_units}")

        red, green, blue = band_algebra(
            bands_data=bands_data,
            rgb_ranges=rgb_ranges,
        )

        rgb_output_path = os.path.join(
            rgb_interval_dir,
            f"{interval}_rgb_result.nc",
        )

        save_rgb_to_netcdf(
            red=red,
            green=green,
            blue=blue,
            output_path=rgb_output_path,
            interval_name=interval,
            ds_ref=ds_ref,
        )

        print(f"Intervalo {interval} procesado correctamente.")
        return True

    except Exception as e:
        print(f"Error al aplicar álgebra RGB para {interval}: {e}")
        return False

    finally:
        try:
            ds_ref.close()
        except Exception:
            pass


def process_intervals(
    input_base_dir,
    resampled_base_dir,
    rgb_base_dir,
    config,
    target_interval=None,
):
    """
    Procesa todos los intervalos disponibles o solo uno si se pasa --interval.
    """
    if target_interval:
        intervals = [target_interval]
        print(f"Procesando únicamente el intervalo solicitado: {target_interval}")
    else:
        intervals = sorted(os.listdir(input_base_dir))
        print("Procesando todos los intervalos disponibles.")

    processed_count = 0
    skipped_count = 0

    for interval in intervals:
        success = process_single_interval(
            interval=interval,
            input_base_dir=input_base_dir,
            resampled_base_dir=resampled_base_dir,
            rgb_base_dir=rgb_base_dir,
            config=config,
        )

        if success:
            processed_count += 1
        else:
            skipped_count += 1

    print("Proceso de resampleo completado.")
    print(f"Intervalos procesados correctamente: {processed_count}")
    print(f"Intervalos omitidos o con error: {skipped_count}")


def main():
    parser = argparse.ArgumentParser(
        description="Procesador P3 MDTS: resampleo de bandas y generación de RGB georreferenciado."
    )

    parser.add_argument(
        "--interval",
        type=str,
        default=None,
        help="Nombre del intervalo a procesar. Ejemplo: 2024-12-06_2300",
    )

    args = parser.parse_args()

    config_path = os.path.join(
        PROCESSOR_DIR,
        "data",
        "conf",
        "config_resampleo.json",
    )

    config = load_config(config_path)

    input_base_directory = os.path.join(PROJECT_DIR, "descarga", "data")
    resampled_base_directory = os.path.join(PROCESSOR_DIR, "data", "resampled")
    rgb_base_directory = os.path.join(PROCESSOR_DIR, "data", "rgb")

    process_intervals(
        input_base_dir=input_base_directory,
        resampled_base_dir=resampled_base_directory,
        rgb_base_dir=rgb_base_directory,
        config=config,
        target_interval=args.interval,
    )


if __name__ == "__main__":
    main()
