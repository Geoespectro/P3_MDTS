import datetime
import json
import logging
import os
import re
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import helpers as help
import s3fs


# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)


# Obtiene la ruta absoluta al directorio del script
script_dir = os.path.dirname(os.path.abspath(__file__))
setup_file = os.path.join(script_dir, "setup.json")


def build_interval_folder_name(
    year: str,
    day: str,
    hour: str,
    minute: str,
) -> str:
    """
    Convierte año + día juliano + hora/minuto al formato:

        YYYY-MM-DD_HHMM
    """

    interval_datetime = datetime.datetime.strptime(
        f"{year}{day}{hour}{minute}",
        "%Y%j%H%M",
    )

    return interval_datetime.strftime("%Y-%m-%d_%H%M")


def extract_band_number(filename):
    """
    Extrae el número de banda ABI tanto para Mode 3 como Mode 6.

    Ejemplos:

        ...M3C13_G16... -> 13
        ...M6C13_G19... -> 13

    Retorna None si el nombre no corresponde a una banda ABI válida.
    """

    match = re.search(
        r"M[36]C(\d{2})",
        os.path.basename(filename),
    )

    if match:
        return int(match.group(1))

    return None


def is_folder_complete(folder_path, required_bands):
    """
    Verifica que una carpeta contenga todas las bandas requeridas.

    Compatible con archivos M3Cxx y M6Cxx.
    """

    if not os.path.exists(folder_path):
        return False

    existing_files = os.listdir(folder_path)

    existing_bands = {
        band
        for file in existing_files
        if (band := extract_band_number(file)) is not None
    }

    return all(
        band in existing_bands
        for band in required_bands
    )


def get_last_downloaded_time(
    start_datetime,
    end_datetime=None,
):
    """
    Busca el último intervalo completo registrado en la base de datos,
    pero solamente dentro de la ventana temporal configurada.

    Esto evita que datos anteriores, por ejemplo de 2026,
    provoquen que una corrida de 2018 continúe desde una fecha incorrecta.
    """

    last_time = None

    for year in sorted(download_db.keys()):
        for day in sorted(download_db[year].keys()):
            for hour in sorted(download_db[year][day].keys()):
                for minute in sorted(
                    download_db[year][day][hour].keys()
                ):

                    try:
                        interval_datetime = datetime.datetime.strptime(
                            f"{year}{day}{hour}{minute}",
                            "%Y%j%H%M",
                        )
                    except ValueError:
                        continue

                    # Ignorar registros anteriores a la ventana actual
                    if interval_datetime < start_datetime:
                        continue

                    # Ignorar registros posteriores a la ventana actual
                    if (
                        end_datetime is not None
                        and interval_datetime > end_datetime
                    ):
                        continue

                    downloaded_files = (
                        download_db[year][day][hour][minute]
                    )

                    if len(downloaded_files) == len(bands):
                        if (
                            last_time is None
                            or interval_datetime > last_time
                        ):
                            last_time = interval_datetime

    return last_time


def download_file(
    f,
    temp_path,
    final_path,
    year,
    day,
    hour,
    minute,
):
    """
    Descarga un archivo y lo organiza dentro de la carpeta
    correspondiente al intervalo YYYY-MM-DD_HHMM.
    """

    image_name = f.split("/")[-1]

    if not image_name.strip():
        logger.error(
            "Nombre de archivo inválido. Omitiendo..."
        )
        return

    folder_name = build_interval_folder_name(
        year,
        day,
        hour,
        minute,
    )

    interval_path = os.path.join(
        final_path,
        folder_name,
    )

    if not os.path.exists(interval_path):
        os.makedirs(interval_path)

    temp_file_path = os.path.join(
        temp_path,
        image_name,
    )

    final_file_path = os.path.join(
        interval_path,
        image_name,
    )

    try:
        logger.info(
            f"Descargando archivo: {image_name}"
        )

        fs.get(
            f,
            temp_file_path,
        )

        # Verificar que el archivo descargado no esté vacío
        if os.path.getsize(temp_file_path) > 0:

            shutil.move(
                temp_file_path,
                final_file_path,
            )

            # Actualizar base de datos
            if year not in download_db:
                download_db[year] = {}

            if day not in download_db[year]:
                download_db[year][day] = {}

            if hour not in download_db[year][day]:
                download_db[year][day][hour] = {}

            if minute not in download_db[year][day][hour]:
                download_db[year][day][hour][minute] = []

            if (
                f
                not in download_db[year][day][hour][minute]
            ):
                download_db[year][day][hour][minute].append(f)

            help.writeJson(
                db_file,
                download_db,
            )

        else:
            logger.error(
                f"Archivo incompleto: {image_name}"
            )

            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    except Exception as e:
        logger.error(
            f"Error al descargar el archivo "
            f"{image_name}: {str(e)}"
        )


def main():
    global bands
    global db_file
    global download_db
    global fs
    global logger

    # ---------------------------------------------------------
    # Leer configuración
    # ---------------------------------------------------------

    data = help.readJson(setup_file)

    main_path = os.path.dirname(
        os.path.abspath(__file__)
    )

    image_path = os.path.join(
        main_path,
        "data",
    )

    temp_path = os.path.join(
        main_path,
        "temp",
    )

    db_path = os.path.join(
        main_path,
        data["db_path"],
    )

    log_path = os.path.join(
        main_path,
        data["log_path"],
    )

    bands = data["bands"]

    product = data["product"]

    timeout = data["timeout"]

    dates = data["dates"]

    start_hour = data.get(
        "start_hour",
        "00:00",
    )

    end_date = data.get(
        "end_date",
        None,
    )

    end_hour = data.get(
        "end_hour",
        None,
    )

    max_workers = data.get(
        "max_workers",
        1,
    )

    # ---------------------------------------------------------
    # Satélite
    # ---------------------------------------------------------

    satellite = data.get(
        "satellite",
        "goes16",
    ).lower()

    if satellite not in (
        "goes16",
        "goes19",
    ):
        raise ValueError(
            "Satélite inválido en setup.json. "
            "Use 'goes16' o 'goes19'."
        )

    bucket_url = (
        f"s3://noaa-{satellite}/"
    )

    # ---------------------------------------------------------
    # Cadencia temporal
    # ---------------------------------------------------------

    interval_minutes = data.get(
        "interval_minutes",
        10,
    )

    if (
        not isinstance(interval_minutes, int)
        or interval_minutes <= 0
    ):
        raise ValueError(
            "'interval_minutes' debe ser "
            "un número entero mayor que 0."
        )

    # ---------------------------------------------------------
    # Ventana temporal
    # ---------------------------------------------------------

    start_datetime = datetime.datetime.strptime(
        f"{dates[0]} {start_hour}",
        "%Y-%m-%d %H:%M",
    )

    if end_date and end_hour:

        end_datetime = datetime.datetime.strptime(
            f"{end_date} {end_hour}",
            "%Y-%m-%d %H:%M",
        )

    else:
        end_datetime = None

    # ---------------------------------------------------------
    # Crear carpetas necesarias
    # ---------------------------------------------------------

    for path in [
        image_path,
        temp_path,
        db_path,
        log_path,
    ]:
        if not os.path.exists(path):
            os.makedirs(path)

    # ---------------------------------------------------------
    # Logger
    # ---------------------------------------------------------

    logger, logfile = help.createLogger(
        __file__,
        log_path,
    )

    logger.info(
        f"Satélite seleccionado: {satellite}"
    )

    logger.info(
        f"Bucket seleccionado: {bucket_url}"
    )

    logger.info(
        f"Producto: {product}"
    )

    logger.info(
        f"Bandas requeridas: {bands}"
    )

    logger.info(
        f"Cadencia configurada: "
        f"{interval_minutes} minutos"
    )

    logger.info(
        f"Inicio: {start_datetime}"
    )

    if end_datetime:
        logger.info(
            f"Fin: {end_datetime}"
        )

    # ---------------------------------------------------------
    # Acceso S3
    # ---------------------------------------------------------

    logger.info(
        "Configurando credenciales de acceso "
        "al repositorio remoto."
    )

    fs = s3fs.S3FileSystem(
        anon=True
    )

    # ---------------------------------------------------------
    # Verificar conexión
    # ---------------------------------------------------------

    while True:

        try:

            fs.ls(
                bucket_url
            )

            logger.info(
                f"Conexión a S3 exitosa: "
                f"{satellite}."
            )

            break

        except Exception as e:

            logger.error(
                f"Error en la conexión a S3: "
                f"{str(e)}"
            )

            time.sleep(60)

    # ---------------------------------------------------------
    # Crear o cargar base de datos
    # ---------------------------------------------------------

    db_file = os.path.join(
        db_path,
        "download_db.json",
    )

    if not os.path.exists(db_file):

        logger.info(
            "Creando archivo de base de datos."
        )

        download_db = {}

        help.writeJson(
            db_file,
            download_db,
        )

    else:

        try:

            logger.info(
                "Leyendo base de datos existente."
            )

            download_db = help.readJson(
                db_file
            )

        except json.JSONDecodeError:

            logger.error(
                "Base de datos corrupta. "
                "Creando una nueva."
            )

            download_db = {}

            help.writeJson(
                db_file,
                download_db,
            )

    # ---------------------------------------------------------
    # Determinar desde dónde continuar
    # ---------------------------------------------------------

    last_time = get_last_downloaded_time(
        start_datetime,
        end_datetime,
    )

    if last_time:

        logger.info(
            f"Reanudando desde la última descarga "
            f"de esta ventana: {last_time}"
        )

        current_datetime = (
            last_time
            + datetime.timedelta(
                minutes=interval_minutes
            )
        )

    else:

        logger.info(
            "Iniciando desde el principio "
            "de la ventana configurada."
        )

        current_datetime = start_datetime

    # ---------------------------------------------------------
    # Flujo principal
    # ---------------------------------------------------------

    while True:

        # Finalización de ventana temporal
        if (
            end_datetime
            and current_datetime > end_datetime
        ):

            logger.info(
                "Proceso completado."
            )

            print(
                "Proceso completado."
            )

            break

        logger.info(
            f"Procesando: "
            f"{current_datetime.strftime('%Y-%m-%d %H:%M')}"
        )

        year = current_datetime.strftime("%Y")
        day = current_datetime.strftime("%j")
        hour = current_datetime.strftime("%H")
        minute = current_datetime.strftime("%M")

        # -----------------------------------------------------
        # Ruta remota NOAA
        # -----------------------------------------------------

        remotePath, _, _, _ = help.getRemotePath(
            bucket_url,
            product,
            current_datetime,
        )

        # -----------------------------------------------------
        # Carpeta local del intervalo
        # -----------------------------------------------------

        folder_name = build_interval_folder_name(
            year,
            day,
            hour,
            minute,
        )

        interval_path = os.path.join(
            image_path,
            folder_name,
        )

        # -----------------------------------------------------
        # Inicializar estructura de DB
        # -----------------------------------------------------

        if year not in download_db:
            download_db[year] = {}

        if day not in download_db[year]:
            download_db[year][day] = {}

        if hour not in download_db[year][day]:
            download_db[year][day][hour] = {}

        if minute not in download_db[year][day][hour]:
            download_db[year][day][hour][minute] = []

        # -----------------------------------------------------
        # Verificar intervalo previamente descargado
        # -----------------------------------------------------

        if (
            len(
                download_db[year][day][hour][minute]
            )
            == len(bands)
        ):

            if is_folder_complete(
                interval_path,
                bands,
            ):

                logger.info(
                    f"Carpeta completa y validada para "
                    f"{current_datetime.strftime('%Y-%m-%d %H:%M')}."
                )

                current_datetime += datetime.timedelta(
                    minutes=interval_minutes
                )

                continue

            else:

                logger.warning(
                    f"Carpeta incompleta a pesar de "
                    f"base de datos. Reintentando descargas "
                    f"para "
                    f"{current_datetime.strftime('%Y-%m-%d %H:%M')}."
                )

                download_db[year][day][hour][minute] = []

                help.writeJson(
                    db_file,
                    download_db,
                )

        # -----------------------------------------------------
        # Buscar archivos en S3
        # -----------------------------------------------------

        try:

            currentFileList = fs.ls(
                remotePath,
                refresh=True,
            )

            filtered_files = {}

            timestamp_prefix = (
                f"s{year}{day}{hour}{minute}"
            )

            # -------------------------------------------------
            # Filtrar bandas requeridas
            # Compatible con M3 y M6
            # -------------------------------------------------

            for f in currentFileList:

                try:

                    band_number = extract_band_number(
                        f
                    )

                    if band_number is None:
                        continue

                    filename_parts = f.split("_")

                    if len(filename_parts) < 4:
                        continue

                    if (
                        band_number in bands
                        and filename_parts[3].startswith(
                            timestamp_prefix
                        )
                    ):
                        filtered_files[
                            band_number
                        ] = f

                except (
                    IndexError,
                    ValueError,
                ):
                    continue

            # Mostrar qué bandas se encontraron
            found_bands = sorted(
                filtered_files.keys()
            )

            logger.info(
                f"Bandas encontradas para "
                f"{current_datetime.strftime('%Y-%m-%d %H:%M')}: "
                f"{found_bands}"
            )

            # -------------------------------------------------
            # Descargar
            # -------------------------------------------------

            with ThreadPoolExecutor(
                max_workers=max_workers
            ) as executor:

                futures = [

                    executor.submit(
                        download_file,
                        f,
                        temp_path,
                        image_path,
                        year,
                        day,
                        hour,
                        minute,
                    )

                    for band, f
                    in filtered_files.items()

                    if (
                        f
                        not in
                        download_db[
                            year
                        ][
                            day
                        ][
                            hour
                        ][
                            minute
                        ]
                    )
                ]

                for future in as_completed(
                    futures
                ):
                    future.result()

            # -------------------------------------------------
            # Validar carpeta
            # -------------------------------------------------

            if is_folder_complete(
                interval_path,
                bands,
            ):

                logger.info(
                    f"Carpeta validada y completa para "
                    f"{current_datetime.strftime('%Y-%m-%d %H:%M')}."
                )

                current_datetime += datetime.timedelta(
                    minutes=interval_minutes
                )

            else:

                logger.warning(
                    f"Faltan bandas para completar "
                    f"el intervalo "
                    f"{current_datetime.strftime('%Y-%m-%d %H:%M')}. "
                    f"Reintentando..."
                )

                time.sleep(
                    timeout
                )

        except Exception as e:

            logger.error(
                f"Error inesperado: {str(e)}"
            )

            time.sleep(
                timeout
            )

    print(
        "=" * 40
        + "\nDESCARGA COMPLETADA\n"
        + "=" * 40
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
