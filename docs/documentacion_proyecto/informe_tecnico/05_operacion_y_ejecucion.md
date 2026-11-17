# Operación y ejecución

## Requisitos e instalación

- Linux.
- Python 3.10 o superior.
- Conexión a internet para la descarga desde NOAA.
- Dependencias definidas en `requirements.txt`.

El contenedor Docker utiliza Python 3.12 e incluye dependencias del sistema necesarias para GEOS, PROJ, NetCDF/HDF5 e imágenes.

Instalación local:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Configuraciones

Antes de ejecutar el pipeline deben revisarse los siguientes archivos:

```text
descarga/setup.json
Procesador/data/conf/config_resampleo.json
Procesador/data/conf/config_mapa.json
```

### Descarga

`descarga/setup.json` define:

```text
satélite
producto
bandas
fecha inicial
hora inicial
fecha final
hora final
cadencia temporal
timeout
cantidad de workers
```

Los satélites soportados son:

```json
"satellite": "goes16"
```

o:

```json
"satellite": "goes19"
```

La cadencia se configura mediante:

```json
"interval_minutes": 10
```

Como referencia:

```text
GOES-16 histórico Mode 3  → 15 minutos
GOES-16 Mode 6            → 10 minutos
GOES-19 Mode 6            → 10 minutos
```

### Procesamiento

`Procesador/data/conf/config_resampleo.json` define:

```text
bandas requeridas
banda de referencia
método de resampleo
persistencia de bandas intermedias
rangos RGB
```

Los rangos actuales son:

```text
Red   → -35.0 a 5.0
Green → -5.0 a 60.0
Blue  → -0.75 a 0.25
```

### Mapa

`Procesador/data/conf/config_mapa.json` define:

```text
rutas
región
recursos cartográficos
tamaño y resolución
título
duración del GIF
```

El satélite utilizado se toma de `descarga/setup.json`, por lo que no es necesario configurarlo nuevamente en el archivo del mapa.

---

## Descarga

Desde la raíz del proyecto:

```bash
python descarga/goes16Download.py
```

Aunque el archivo conserva el nombre histórico `goes16Download.py`, actualmente permite descargar datos de:

```text
GOES-16
GOES-19
```

Los archivos descargados se almacenan en:

```text
descarga/data/<intervalo>/
```

Durante la descarga también se utilizan:

```text
descarga/temp/
descarga/logs/
descarga/db/download_db.json
```

---

## Procesar un intervalo

Ejemplo:

```bash
python Procesador/src/resampleo_alg_band.py --interval 2024-01-11_1900
python Procesador/src/mapa_rgb.py --interval 2024-01-11_1900
```

El primer comando genera el NetCDF RGB correspondiente al intervalo.

El segundo genera el mapa PNG y actualiza la animación GIF.

---

## Procesar todos los intervalos disponibles

Procesamiento RGB:

```bash
python Procesador/src/resampleo_alg_band.py
```

Generación de mapas y GIF:

```bash
python Procesador/src/mapa_rgb.py
```

---

## Orquestador

El pipeline completo se ejecuta mediante:

```bash
python run_all.py
```

El orquestador coordina:

```text
descarga
→ validación de intervalos
→ procesamiento RGB
→ mapa PNG
→ GIF
```

La descarga puede continuar en segundo plano mientras los intervalos completos y estables son procesados.

### Procesar datos ya descargados

```bash
python run_all.py --skip-download
```

### Ejecutar una única revisión

```bash
python run_all.py --skip-download --once
```

### Reiniciar el estado del pipeline

```bash
python run_all.py --reset-state
```

Este último comando elimina el estado almacenado en:

```text
pipeline_state.json
```

por lo que debe utilizarse cuando se desea comenzar nuevamente el seguimiento de los intervalos.

El orquestador también dispone de opciones para controlar:

```text
--poll-seconds
--stability-seconds
--max-retries
--retry-delay
```

---

## Salidas

### Datos descargados

```text
descarga/data/<intervalo>/*.nc
```

### NetCDF RGB

```text
Procesador/data/rgb/<intervalo>/<intervalo>_rgb_result.nc
```

### Mapas PNG

Según el satélite configurado:

```text
Procesador/data/output/png/CONAE_PRD_GOES16_ABI_MDTS_RGB_<intervalo>.png
```

o:

```text
Procesador/data/output/png/CONAE_PRD_GOES19_ABI_MDTS_RGB_<intervalo>.png
```

### GIF

Según el satélite configurado:

```text
Procesador/data/output/gif/CONAE_PRD_GOES16_ABI_MDTS_RGB_animacion.gif
```

o:

```text
Procesador/data/output/gif/CONAE_PRD_GOES19_ABI_MDTS_RGB_animacion.gif
```

Los nombres se generan automáticamente a partir del satélite configurado en:

```text
descarga/setup.json
```

---

## Diagnósticos

### B13 para un intervalo

```bash
python Procesador/diagnostico/diagnostico_b13.py \
  --interval 2024-01-11_1900
```

### B13 para todos los intervalos

```bash
python Procesador/diagnostico/diagnostico_b13.py --all
```

También puede ejecutarse sin argumentos:

```bash
python Procesador/diagnostico/diagnostico_b13.py
```

Las salidas incluyen:

```text
<intervalo>_B13_BT.png
<intervalo>_B13_mascaras.png
<intervalo>_B13_estadisticas.json
diagnostico_b13_estadisticas.csv
```

### Diagnóstico temporal RGB

```bash
python Procesador/diagnostico/diagnostico_gif_rgb.py
```

Genera:

```text
diagnostico_temporal_rgb.csv
```

con métricas de continuidad y cambio temporal del producto.

---

## Pruebas

Desde la raíz del proyecto:

```bash
python -m unittest discover -s test -p "test_*.py" -v
```

También pueden ejecutarse por módulo:

```bash
python test/test_descarga.py
```

```bash
python test/test_procesador.py
```

Las pruebas automatizadas complementan las ejecuciones funcionales realizadas sobre datos reales.

---

## Limpieza

Para eliminar datos temporales y productos generados:

```bash
python clean.py
```

Antes de ejecutarlo debe revisarse:

```python
DRY_RUN = False
```

Con este valor la limpieza se realiza efectivamente.

Para comprobar previamente qué elementos serían eliminados puede configurarse:

```python
DRY_RUN = True
```

El script mantiene la estructura principal del proyecto y elimina únicamente las categorías configuradas para limpieza.

---

## Recuperación y errores conocidos

| Situación | Acción recomendada |
|---|---|
| Interrupción del orquestador | Reiniciar el pipeline; `run_all.py` recupera el estado desde `pipeline_state.json` y los productos existentes |
| Estado del pipeline inválido | Puede reiniciarse mediante `--reset-state` |
| Banda faltante | Esperar la descarga o revisar el intervalo |
| Banda duplicada | Corregir el contenido de la carpeta antes de procesar |
| S3 inaccesible | Revisar conexión a internet y disponibilidad del repositorio NOAA |
| Cadencia incorrecta | Revisar `interval_minutes` según fecha y modo operativo |
| Satélite incorrecto | Revisar `satellite` en `descarga/setup.json` |
| Primer mapa sin caché Cartopy | Puede requerir descarga de recursos Natural Earth |
| Reintentos de procesamiento agotados | Revisar los archivos del intervalo y ejecutar nuevamente |
| Base de descarga inválida | Respaldar y revisar `descarga/db/download_db.json`; puede regenerarse si es necesario |

---

## Flujo operativo recomendado

Antes de una ejecución:

```text
1. Revisar descarga/setup.json
2. Verificar satellite
3. Verificar fechas y horarios
4. Verificar interval_minutes
5. Activar el entorno virtual
6. Ejecutar run_all.py
7. Revisar logs y productos generados
```

Para una ejecución limpia puede utilizarse previamente:

```bash
python clean.py
```

si se desea eliminar productos y estados de ejecuciones anteriores.
