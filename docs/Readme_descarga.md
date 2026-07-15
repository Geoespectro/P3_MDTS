# Lógica de Descarga de Datos GOES-16

## Propósito

El módulo `descarga/` automatiza la descarga de datos ABI del satélite GOES-16 desde el repositorio S3 de NOAA.

Los archivos se organizan por intervalos temporales y bandas espectrales. La descarga utiliza una carpeta temporal, una base JSON local y logs de ejecución.

## Requisitos

- Python 3.10 o superior.
- Conexión a internet.
- Dependencia `s3fs` instalada mediante `requirements.txt`.

## Estructura

```text
descarga/
├── data/
├── db/
├── logs/
├── temp/
├── goes16Download.py
├── helpers.py
├── inspect_bands.py
└── setup.json
```

## Archivos principales

- `goes16Download.py`: flujo principal de descarga.
- `helpers.py`: lectura y escritura de JSON, creación de logs y funciones auxiliares.
- `inspect_bands.py`: herramienta de inspección.
- `setup.json`: configuración temporal, bandas y producto.

## Configuración

Archivo:

```text
descarga/setup.json
```

Ejemplo:

```json
{
  "_comment": {
    "descarga_continua": "Configura: \"dates\": [\"AAAA-MM-DD\"], \"start_hour\": \"HH:MM\", \"end_date\": null, \"end_hour\": null.",
    "ventana_temporal": "Configura: \"dates\": [\"AAAA-MM-DD\"], \"start_hour\": \"HH:MM\", \"end_date\": \"AAAA-MM-DD\", \"end_hour\": \"HH:MM\"."
  },
  "db_path": "db/",
  "log_path": "logs/",
  "product": "ABI-L1b-RadF",
  "timeout": 120,
  "bands": [2, 5, 7, 8, 10, 13],
  "dates": ["2024-03-19"],
  "start_hour": "21:00",
  "max_workers": 1,
  "end_date": "2024-03-19",
  "end_hour": "21:20"
}
```

### Parámetros

- `product`: producto GOES-16.
- `bands`: bandas requeridas.
- `dates`: fecha inicial.
- `start_hour`: hora inicial.
- `end_date`: fecha final opcional.
- `end_hour`: hora final opcional.
- `timeout`: espera entre intentos de reconexión.
- `max_workers`: cantidad máxima de descargas concurrentes.
- `db_path`: carpeta de la base JSON local.
- `log_path`: carpeta de logs.

Las rutas principales del módulo se resuelven de manera relativa a `descarga/`, lo que permite mover el proyecto a otra computadora sin modificar rutas absolutas.

## Modos de descarga

### Ventana temporal

Para descargar un período definido:

```json
"dates": ["2024-03-19"],
"start_hour": "21:00",
"end_date": "2024-03-19",
"end_hour": "22:00"
```

### Descarga continua

Para continuar sin fecha final:

```json
"dates": ["2024-03-19"],
"start_hour": "21:00",
"end_date": null,
"end_hour": null
```

## Flujo

```text
lectura de setup.json
→ conexión anónima a S3
→ selección de archivos por producto, fecha, hora y banda
→ descarga en descarga/temp/
→ movimiento a descarga/data/<intervalo>/
→ actualización de descarga/db/download_db.json
→ validación de las bandas del intervalo
```

Los archivos se descargan primero en `temp/` y se mueven a su carpeta final cuando la transferencia termina.

## Organización de datos

```text
descarga/data/
├── 2024-12-06_2300/
│   ├── OR_ABI-L1b-RadF-M6C02_G16_....nc
│   ├── OR_ABI-L1b-RadF-M6C05_G16_....nc
│   ├── OR_ABI-L1b-RadF-M6C07_G16_....nc
│   ├── OR_ABI-L1b-RadF-M6C08_G16_....nc
│   ├── OR_ABI-L1b-RadF-M6C10_G16_....nc
│   └── OR_ABI-L1b-RadF-M6C13_G16_....nc
└── 2024-12-06_2310/
```

## Base de datos local

Archivo:

```text
descarga/db/download_db.json
```

Registra los archivos descargados y permite reanudar la ejecución sin repetir transferencias ya completadas.

La base es un registro local de trabajo y no debe versionarse.

## Logs

Se guardan en:

```text
descarga/logs/
```

Incluyen conexión, intervalos, archivos descargados, reintentos y errores.

## Ejecución

Desde la raíz del proyecto:

```bash
python descarga/goes16Download.py
```

También puede ejecutarse desde `descarga/`:

```bash
cd descarga
python goes16Download.py
```

## Verificación

Una carpeta completa debe contener las bandas:

```text
B02, B05, B07, B08, B10 y B13
```

Para ejecutar las pruebas del módulo desde la raíz:

```bash
python test/test_descarga.py
```

O toda la suite:

```bash
python -m unittest discover -s test -p "test_*.py" -v
```

## Errores comunes

### Fallo de conexión S3

Verificar:

- conexión a internet;
- disponibilidad del repositorio NOAA;
- instalación de `s3fs`.

### Carpeta incompleta

Revisar:

- log de descarga;
- espacio libre;
- permisos de escritura;
- rango temporal configurado;
- disponibilidad de las seis bandas.

### Base JSON inválida

El archivo puede eliminarse para reiniciar el registro local:

```bash
rm descarga/db/download_db.json
```

La próxima ejecución volverá a crearlo.


