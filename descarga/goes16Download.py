import datetime
import json
import logging
import os
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

# Leer el archivo de configuración
data = help.readJson(setup_file)

# Extraer configuraciones del archivo
main_path = os.path.dirname(os.path.abspath(__file__))
# image_path = os.path.join(main_path, '..', 'Procesador', 'inbox')
image_path = os.path.join(main_path, "data")
temp_path = os.path.join(main_path, "temp")
db_path = os.path.join(main_path, data["db_path"])
log_path = os.path.join(main_path, data["log_path"])
bands = data["bands"]
product = data["product"]
timeout = data["timeout"]
dates = data["dates"]
start_hour = data.get("start_hour", "00:00")
end_date = data.get("end_date", None)
end_hour = data.get("end_hour", None)
max_workers = data.get("max_workers", 1)

# Crear carpetas necesarias
for path in [image_path, temp_path, db_path, log_path]:
    if not os.path.exists(path):
        os.makedirs(path)

# Configurar el logger
logger, logfile = help.createLogger(__file__, log_path)

# Configurar las credenciales anónimas para S3
logger.info("Configurando credenciales de acceso al repositorio remoto.")
fs = s3fs.S3FileSystem(anon=True)

# Verificar conexión a S3
while True:
    try:
        fs.ls("s3://noaa-goes16/")
        logger.info("Conexión a S3 exitosa.")
        break
    except Exception as e:
        logger.error(f"Error en la conexión a S3: {str(e)}")
        time.sleep(60)

# Crear o leer la base de datos de descargas
db_file = os.path.join(db_path, "download_db.json")
if not os.path.exists(db_file):
    logger.info("Creando archivo de base de datos.")
    download_db = {}
    help.writeJson(db_file, download_db)
else:
    try:
        logger.info("Leyendo base de datos existente.")
        download_db = help.readJson(db_file)
    except json.JSONDecodeError:
        logger.error("Base de datos corrupta. Creando una nueva.")
        download_db = {}
        help.writeJson(db_file, download_db)


# Obtener última fecha y hora descargada
def get_last_downloaded_time():
    last_time = None
    for year in sorted(download_db.keys()):
        for day in sorted(download_db[year].keys()):
            for hour in sorted(download_db[year][day].keys()):
                for minute in sorted(download_db[year][day][hour].keys()):
                    if len(download_db[year][day][hour][minute]) == len(bands):
                        last_time = datetime.datetime.strptime(
                            f"{year}{day}{hour}{minute}", "%Y%j%H%M"
                        )
    return last_time


last_time = get_last_downloaded_time()
if last_time:
    logger.info(f"Reanudando desde la última descarga: {last_time}")
    current_datetime = last_time + datetime.timedelta(minutes=10)
else:
    logger.info("Iniciando desde el principio.")
    current_datetime = datetime.datetime.strptime(
        f"{dates[0]} {start_hour}", "%Y-%m-%d %H:%M"
    )

# Convertir la fecha y hora de fin si está disponible
if end_date and end_hour:
    end_datetime = datetime.datetime.strptime(
        f"{end_date} {end_hour}", "%Y-%m-%d %H:%M"
    )
else:
    end_datetime = None


# Función para descargar un archivo y organizarlo en carpetas
def download_file(f, temp_path, final_path, year, day, hour, minute):

    image_name = f.split("/")[-1]
    if not image_name.strip():
        logger.error("Nombre de archivo inválido. Omitiendo...")
        return

    # Crear carpeta para el intervalo actual (YYYY-MM-DD_HHMM)
    folder_name = f"{year}-{datetime.datetime.strptime(day, '%j').strftime('%m-%d')}_{hour}{minute}"
    interval_path = os.path.join(final_path, folder_name)

    if not os.path.exists(interval_path):
        os.makedirs(interval_path)

    # Definir rutas de descarga temporal y final
    temp_file_path = os.path.join(temp_path, image_name)
    final_file_path = os.path.join(interval_path, image_name)

    try:
        # Descargar el archivo
        logger.info(f"Descargando archivo: {image_name}")
        fs.get(f, temp_file_path)

        # Verificar integridad y moverlo
        if os.path.getsize(temp_file_path) > 0:
            shutil.move(temp_file_path, final_file_path)
            # logger.info(f'Archivo guardado en: {final_file_path}')

            # Actualizar base de datos
            if year not in download_db:
                download_db[year] = {}
            if day not in download_db[year]:
                download_db[year][day] = {}
            if hour not in download_db[year][day]:
                download_db[year][day][hour] = {}
            if minute not in download_db[year][day][hour]:
                download_db[year][day][hour][minute] = []
            download_db[year][day][hour][minute].append(f)
            help.writeJson(db_file, download_db)
        else:
            logger.error(f"Archivo incompleto: {image_name}")
            os.remove(temp_file_path)

    except Exception as e:
        logger.error(f"Error al descargar el archivo {image_name}: {str(e)}")


# Bucle principal
while True:
    if end_datetime and current_datetime > end_datetime:
        logger.info("Proceso completado.")
        print("Proceso completado.")
        break

    logger.info(f'Procesando: {current_datetime.strftime("%Y-%m-%d %H:%M")}')
    year, day, hour, minute = (
        current_datetime.strftime("%Y"),
        current_datetime.strftime("%j"),
        current_datetime.strftime("%H"),
        current_datetime.strftime("%M"),
    )
    remotePath, _, _, _ = help.getRemotePath(
        "s3://noaa-goes16/", product, current_datetime
    )

    if year not in download_db:
        download_db[year] = {}
    if day not in download_db[year]:
        download_db[year][day] = {}
    if hour not in download_db[year][day]:
        download_db[year][day][hour] = {}
    if minute not in download_db[year][day][hour]:
        download_db[year][day][hour][minute] = []

    if len(download_db[year][day][hour][minute]) == len(bands):
        logger.info(
            f'Todas las bandas ya descargadas para {current_datetime.strftime("%Y-%m-%d %H:%M")}.'
        )
        current_datetime += datetime.timedelta(minutes=10)
        continue

    try:
        currentFileList = fs.ls(remotePath, refresh=True)
        filtered_files = {}
        timestamp_prefix = (
            f"s{year}{day}{hour}{minute}"  # Prefijo específico para el intervalo actual
        )
        for f in currentFileList:
            try:
                band_number = int(f.split("_")[1].split("M6C")[-1])
                if band_number in bands and f.split("_")[3].startswith(
                    timestamp_prefix
                ):
                    filtered_files[band_number] = f
            except (IndexError, ValueError):
                continue

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(
                    download_file, f, temp_path, image_path, year, day, hour, minute
                )
                for band, f in filtered_files.items()
                if f not in download_db[year][day][hour][minute]
            ]
            for future in as_completed(futures):
                future.result()

        if len(download_db[year][day][hour][minute]) == len(bands):
            logger.info(
                f'Todas las bandas descargadas para {current_datetime.strftime("%Y-%m-%d %H:%M")}.'
            )
            current_datetime += datetime.timedelta(minutes=10)
        else:
            logger.info(
                f'Faltan bandas para completar el intervalo {current_datetime.strftime("%Y-%m-%d %H:%M")}. Reintentando...'
            )
            time.sleep(timeout)

    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        time.sleep(timeout)


# Función para verificar si una carpeta contiene todas las bandas requeridas
def is_folder_complete(folder_path, required_bands):

    if not os.path.exists(folder_path):
        return False

    existing_files = os.listdir(folder_path)
    # Extraer números de banda presentes en los nombres de archivo
    existing_bands = set(
        int(file.split("_")[1].split("M6C")[-1])
        for file in existing_files
        if "M6C" in file
    )

    return all(band in existing_bands for band in required_bands)


# Modificar el flujo principal para incluir la validación
while True:
    if end_datetime and current_datetime > end_datetime:
        logger.info("Proceso completado.")
        print("Proceso completado.")
        break

    logger.info(f'Procesando: {current_datetime.strftime("%Y-%m-%d %H:%M")}')
    year, day, hour, minute = (
        current_datetime.strftime("%Y"),
        current_datetime.strftime("%j"),
        current_datetime.strftime("%H"),
        current_datetime.strftime("%M"),
    )
    remotePath, _, _, _ = help.getRemotePath(
        "s3://noaa-goes16/", product, current_datetime
    )

    # Crear el nombre de la carpeta para el intervalo actual
    folder_name = f"{year}-{datetime.datetime.strptime(day, '%j').strftime('%m-%d')}_{hour}{minute}"
    interval_path = os.path.join(image_path, folder_name)

    if len(download_db[year][day][hour][minute]) == len(bands):
        # Verificar si la carpeta está completa
        if is_folder_complete(interval_path, bands):
            logger.info(
                f'Carpeta completa y validada para {current_datetime.strftime("%Y-%m-%d %H:%M")}.'
            )
            current_datetime += datetime.timedelta(minutes=10)
            continue
        else:
            logger.warning(
                f'Carpeta incompleta a pesar de base de datos. Reintentando descargas para {current_datetime.strftime("%Y-%m-%d %H:%M")}.'
            )
            download_db[year][day][hour][minute] = []

    try:
        currentFileList = fs.ls(remotePath, refresh=True)
        filtered_files = {}
        timestamp_prefix = (
            f"s{year}{day}{hour}{minute}"  # Prefijo específico para el intervalo actual
        )
        for f in currentFileList:
            try:
                band_number = int(f.split("_")[1].split("M6C")[-1])
                if band_number in bands and f.split("_")[3].startswith(
                    timestamp_prefix
                ):
                    filtered_files[band_number] = f
            except (IndexError, ValueError):
                continue

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(
                    download_file, f, temp_path, image_path, year, day, hour, minute
                )
                for band, f in filtered_files.items()
                if f not in download_db[year][day][hour][minute]
            ]
            for future in as_completed(futures):
                future.result()

        # Validar carpeta después de las descargas
        if is_folder_complete(interval_path, bands):
            logger.info(
                f'Carpeta validada y completa para {current_datetime.strftime("%Y-%m-%d %H:%M")}.'
            )
            current_datetime += datetime.timedelta(minutes=10)
        else:
            logger.warning(
                f'Faltan bandas para completar el intervalo {current_datetime.strftime("%Y-%m-%d %H:%M")}. Reintentando...'
            )
            time.sleep(timeout)

    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        time.sleep(timeout)

print("=" * 40 + "\nDESCARGA COMPLETADA\n" + "=" * 40)
