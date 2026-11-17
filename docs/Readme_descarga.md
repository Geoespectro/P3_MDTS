# Lógica de Descarga de Datos GOES

## Propósito

El módulo `descarga/` automatiza la descarga de datos ABI de los satélites **GOES-16 y GOES-19** desde los repositorios S3 públicos de NOAA.

Los archivos se organizan por intervalos temporales y bandas espectrales. La descarga utiliza una carpeta temporal, una base JSON local y logs de ejecución.

La selección del satélite se realiza desde:

```text
descarga/setup.json
```

Valores soportados:

```json
"satellite": "goes16"
```

o:

```json
"satellite": "goes19"
```

El sistema selecciona automáticamente el bucket correspondiente:

```text
goes16 → s3://noaa-goes16/
goes19 → s3://noaa-goes19/
```

---

## Requisitos

- Python 3.10 o superior.
- Conexión a internet.
- Dependencia `s3fs` instalada mediante `requirements.txt`.

---

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

---

## Archivos principales

- `goes16Download.py`: flujo principal de descarga para GOES-16 y GOES-19.
- `helpers.py`: lectura y escritura de JSON, creación de logs y funciones auxiliares.
- `inspect_bands.py`: herramienta de inspección.
- `setup.json`: configuración del satélite, producto, bandas y ventana temporal.

> Nota: el archivo principal conserva el nombre histórico `goes16Download.py`, aunque actualmente soporta tanto GOES-16 como GOES-19.

---

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
    "ventana_temporal": "Configura: \"dates\": [\"AAAA-MM-DD\"], \"start_hour\": \"HH:MM\", \"end_date\": \"AAAA-MM-DD\", \"end_hour\": \"HH:MM\".",
    "interval_minutes": "Cadencia Full Disk: usar 15 minutos para GOES-16 histórico en Mode 3 (antes del 02/04/2019) y 10 minutos para Mode 6 (desde el 02/04/2019) y GOES-19."
  },
  "db_path": "db/",
  "log_path": "logs/",
  "satellite": "goes16",
  "product": "ABI-L1b-RadF",
  "timeout": 120,
  "bands": [2, 5, 7, 8, 10, 13],
  "dates": ["2024-03-19"],
  "start_hour": "21:00",
  "interval_minutes": 10,
  "max_workers": 1,
  "end_date": "2024-03-19",
  "end_hour": "21:20"
}
```

---

## Parámetros

- `satellite`: satélite a utilizar. Valores soportados:
  - `goes16`
  - `goes19`
- `product`: producto ABI a descargar.
- `bands`: bandas requeridas.
- `dates`: fecha inicial.
- `start_hour`: hora inicial.
- `interval_minutes`: separación temporal entre intervalos a descargar.
- `end_date`: fecha final opcional.
- `end_hour`: hora final opcional.
- `timeout`: espera entre intentos de reconexión.
- `max_workers`: cantidad máxima de descargas concurrentes.
- `db_path`: carpeta de la base JSON local.
- `log_path`: carpeta de logs.

Las rutas principales del módulo se resuelven de manera relativa a `descarga/`, lo que permite mover el proyecto a otra computadora sin modificar rutas absolutas.

---

## Cadencia temporal Full Disk

La cadencia configurada mediante:

```json
"interval_minutes": 10
```

debe corresponder al período que se quiera procesar.

Regla práctica:

```text
GOES-16 antes del 02/04/2019  → 15 minutos
GOES-16 desde el 02/04/2019   → 10 minutos
GOES-19                       → 10 minutos
```

### GOES-16 histórico — Mode 3

Para eventos anteriores al cambio operacional de 2019:

```json
"satellite": "goes16",
"interval_minutes": 15
```

Ejemplo:

```text
2018-02-08_1730
2018-02-08_1745
2018-02-08_1800
```

Los archivos pueden presentar nomenclatura:

```text
M3C02
M3C05
M3C07
...
```

### GOES-16 / GOES-19 — Mode 6

Para períodos modernos:

```json
"interval_minutes": 10
```

Ejemplo:

```text
2024-01-11_1900
2024-01-11_1910
2024-01-11_1920
```

Los archivos presentan normalmente nomenclatura:

```text
M6C02
M6C05
M6C07
...
```

El módulo reconoce de forma compatible:

```text
M3Cxx
M6Cxx
```

---

## Modos de descarga

### Ventana temporal

Para descargar un período definido:

```json
"dates": ["2024-03-19"],
"start_hour": "21:00",
"end_date": "2024-03-19",
"end_hour": "22:00"
```

La separación entre intervalos se define mediante:

```json
"interval_minutes": 10
```

---

### Descarga continua

Para continuar sin fecha final:

```json
"dates": ["2024-03-19"],
"start_hour": "21:00",
"end_date": null,
"end_hour": null
```

En este modo el proceso continúa buscando nuevos intervalos según la cadencia configurada.

---

## Flujo

```text
lectura de setup.json
→ selección del satélite
→ construcción del bucket NOAA correspondiente
→ conexión anónima a S3
→ selección de archivos por producto, fecha, hora y banda
→ identificación de bandas M3/M6
→ descarga en descarga/temp/
→ movimiento a descarga/data/<intervalo>/
→ actualización de descarga/db/download_db.json
→ validación de las bandas del intervalo
```

Los archivos se descargan primero en:

```text
descarga/temp/
```

y se mueven a su carpeta final cuando la transferencia termina.

---

## Organización de datos

### Ejemplo GOES-16 Mode 6

```text
descarga/data/
├── 2024-01-11_1900/
│   ├── OR_ABI-L1b-RadF-M6C02_G16_....nc
│   ├── OR_ABI-L1b-RadF-M6C05_G16_....nc
│   ├── OR_ABI-L1b-RadF-M6C07_G16_....nc
│   ├── OR_ABI-L1b-RadF-M6C08_G16_....nc
│   ├── OR_ABI-L1b-RadF-M6C10_G16_....nc
│   └── OR_ABI-L1b-RadF-M6C13_G16_....nc
└── 2024-01-11_1910/
```

### Ejemplo GOES-16 histórico Mode 3

```text
descarga/data/
└── 2018-02-08_1730/
    ├── OR_ABI-L1b-RadF-M3C02_G16_....nc
    ├── OR_ABI-L1b-RadF-M3C05_G16_....nc
    ├── OR_ABI-L1b-RadF-M3C07_G16_....nc
    ├── OR_ABI-L1b-RadF-M3C08_G16_....nc
    ├── OR_ABI-L1b-RadF-M3C10_G16_....nc
    └── OR_ABI-L1b-RadF-M3C13_G16_....nc
```

### Ejemplo GOES-19 Mode 6

```text
descarga/data/
└── 2026-09-28_0700/
    ├── OR_ABI-L1b-RadF-M6C02_G19_....nc
    ├── OR_ABI-L1b-RadF-M6C05_G19_....nc
    ├── OR_ABI-L1b-RadF-M6C07_G19_....nc
    ├── OR_ABI-L1b-RadF-M6C08_G19_....nc
    ├── OR_ABI-L1b-RadF-M6C10_G19_....nc
    └── OR_ABI-L1b-RadF-M6C13_G19_....nc
```

---

## Validación de intervalos

Una carpeta se considera completa cuando contiene las seis bandas requeridas:

```text
B02
B05
B07
B08
B10
B13
```

La detección de bandas admite tanto:

```text
M3Cxx
```

como:

```text
M6Cxx
```

por lo que el mismo flujo puede utilizarse con datos históricos y modernos.

---

## Base de datos local

Archivo:

```text
descarga/db/download_db.json
```

Registra los archivos descargados y permite reanudar la ejecución sin repetir transferencias ya completadas.

La lógica de reanudación se limita a la ventana temporal configurada para evitar que registros antiguos interfieran con una nueva ejecución.

La base es un registro local de trabajo y no debe versionarse.

---

## Logs

Se guardan en:

```text
descarga/logs/
```

Incluyen información sobre:

```text
satélite configurado
conexión al bucket NOAA
intervalos procesados
bandas detectadas
archivos descargados
reintentos
errores
```

---

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

---

## Verificación rápida

Antes de ejecutar puede comprobarse el satélite configurado en:

```text
descarga/setup.json
```

Por ejemplo:

```json
"satellite": "goes16"
```

o:

```json
"satellite": "goes19"
```

También debe verificarse que:

```json
"interval_minutes"
```

corresponda al período seleccionado.

---

## Pruebas

Para ejecutar las pruebas del módulo desde la raíz:

```bash
python test/test_descarga.py
```

O toda la suite:

```bash
python -m unittest discover -s test -p "test_*.py" -v
```

---

## Errores comunes

### Satélite no soportado

Solo se admiten actualmente:

```text
goes16
goes19
```

Revisar:

```text
descarga/setup.json
```

---

### Cadencia temporal incorrecta

Si se configura:

```json
"interval_minutes": 10
```

para un período histórico de GOES-16 que operaba en Mode 3, algunos horarios solicitados pueden no existir.

Para GOES-16 anterior al 02/04/2019 utilizar como referencia:

```json
"interval_minutes": 15
```

---

### Fallo de conexión S3

Verificar:

- conexión a internet;
- disponibilidad del repositorio NOAA;
- valor de `satellite`;
- instalación de `s3fs`.

---

### Carpeta incompleta

Revisar:

- log de descarga;
- espacio libre;
- permisos de escritura;
- rango temporal configurado;
- `interval_minutes`;
- disponibilidad de las seis bandas.

---

### Base JSON inválida

El archivo puede eliminarse para reiniciar el registro local:

```bash
rm descarga/db/download_db.json
```

La próxima ejecución volverá a crearlo.

También puede utilizarse la herramienta general:

```bash
python clean.py
```

si se desea limpiar completamente el estado temporal del proyecto.
```

Con eso reemplazás directamente `docs/Readme_descarga.md`.


