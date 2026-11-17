# P3 MDTS — Mapa RGB de Tormentas Severas

## Descripción

Este proyecto implementa un pipeline para generar el producto **P3 MDTS — Mapa RGB de Tormentas Severas** a partir de datos del sensor ABI de los satélites **GOES-16 y GOES-19**.

El flujo general es:

```text
descarga de bandas
→ validación de intervalos completos
→ resampleo a una grilla común
→ conversión a unidades físicas
→ composición y normalización RGB
→ NetCDF RGB georreferenciado
→ mapa PNG
→ GIF animado
```

El producto busca resaltar características asociadas con convección profunda y posibles tormentas severas.

La selección del satélite se realiza desde:

```text
descarga/setup.json
```

---

## Requisitos

- Linux.
- Python 3.10 o superior.
- Conexión a internet para la descarga desde NOAA.
- Dependencias listadas en `requirements.txt`.

La primera generación cartográfica puede requerir acceso a internet si Cartopy todavía no dispone de los recursos Natural Earth en su caché local.

---

## Estructura del proyecto

```text
P3_MDTS/
├── descarga/
│   ├── data/
│   ├── db/
│   ├── logs/
│   ├── temp/
│   ├── goes16Download.py
│   ├── helpers.py
│   ├── inspect_bands.py
│   └── setup.json
├── docs/
│   ├── documentacion_proyecto/
│   ├── Readme_descarga.md
│   └── Readme_procesador.md
├── Procesador/
│   ├── data/
│   │   ├── conf/
│   │   ├── diagnostico/
│   │   ├── grids/
│   │   ├── logo/
│   │   ├── output/
│   │   ├── resampled/
│   │   ├── rgb/
│   │   └── shp/
│   ├── diagnostico/
│   │   ├── comparacion_evento_cordoba_2018.py
│   │   ├── comparacion_evento_mendoza_2024.py
│   │   ├── diagnostico_b13.py
│   │   └── diagnostico_gif_rgb.py
│   └── src/
│       ├── helpers_resampleo.py
│       ├── mapa_rgb.py
│       └── resampleo_alg_band.py
├── test/
│   ├── test_descarga.py
│   └── test_procesador.py
├── clean.py
├── Dockerfile
├── requirements.txt
├── run_all.py
└── README.md
```

Durante la ejecución, `run_all.py` crea `pipeline_state.json` en la raíz del proyecto. Es un archivo temporal de control y no debe versionarse.

---

## Componentes

### Descarga

El módulo `descarga/` obtiene las bandas ABI desde NOAA, organiza los archivos por intervalo temporal y registra el estado de las descargas.

Soporta:

```text
GOES-16
GOES-19
```

Configuración:

```text
descarga/setup.json
```

Salida:

```text
descarga/data/<intervalo>/
```

Documentación específica:

```text
docs/Readme_descarga.md
```

---

### Procesador

El módulo `Procesador/` valida los intervalos completos, procesa las bandas ABI, genera el RGB georreferenciado y produce los mapas PNG y la animación GIF.

Entrada:

```text
descarga/data/<intervalo>/
```

Salidas principales:

```text
Procesador/data/rgb/
Procesador/data/output/png/
Procesador/data/output/gif/
```

El procesador admite archivos correspondientes a **Mode 3 y Mode 6**.

Documentación específica:

```text
docs/Readme_procesador.md
```

---

### Orquestador

`run_all.py` coordina el pipeline completo:

```text
descarga
→ procesamiento
→ NetCDF RGB
→ mapa PNG
→ GIF
```

La descarga se ejecuta en segundo plano y el procesamiento comienza cuando se detecta un intervalo completo y estable.

También permite procesar datos ya descargados:

```bash
python run_all.py --skip-download
```

---

### Limpieza

`clean.py` elimina datos temporales y productos generados sin borrar el código, las configuraciones ni los recursos principales del proyecto.

Para ejecutar una limpieza:

```bash
python clean.py
```

Puede configurarse:

```python
DRY_RUN = True
```

para simular qué archivos serían eliminados sin realizar cambios.

---

## Bandas utilizadas

```text
B02, B05, B07, B08, B10 y B13
```

La banda B13 se utiliza como referencia espacial.

La composición aplicada es:

```text
Red   = B08 - B10
Green = B07 - B13
Blue  = B05 - B02
```

Antes del álgebra:

```text
B02 y B05           → reflectancia
B07, B08, B10 y B13 → temperatura de brillo en °C
```

Los detalles del procesamiento y los rangos de normalización se encuentran en:

```text
docs/Readme_procesador.md
```

---

## Instalación

Desde la raíz del proyecto:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Ejecución

### Pipeline completo

```bash
python run_all.py
```

### Sin ejecutar la descarga

```bash
python run_all.py --skip-download
```

### Reiniciar el estado del pipeline

```bash
python run_all.py --reset-state
```

### Procesar un intervalo manualmente

```bash
python Procesador/src/resampleo_alg_band.py --interval 2024-12-06_2300
python Procesador/src/mapa_rgb.py --interval 2024-12-06_2300
```

### Ejecutar diagnósticos

B13 para un intervalo:

```bash
python Procesador/diagnostico/diagnostico_b13.py \
  --interval 2024-12-06_2300
```

B13 para todos los intervalos:

```bash
python Procesador/diagnostico/diagnostico_b13.py --all
```

Diagnóstico temporal RGB:

```bash
python Procesador/diagnostico/diagnostico_gif_rgb.py
```

### Limpiar datos y productos generados

```bash
python clean.py
```

---

## Pruebas

Desde la raíz:

```bash
python -m unittest discover -s test -p "test_*.py" -v
```

---

## Documentación

La documentación operativa específica se encuentra en:

```text
docs/Readme_descarga.md
docs/Readme_procesador.md
```

La documentación ampliada del proyecto se encuentra en:

```text
docs/documentacion_proyecto/
```

---

## Archivos generados

Los siguientes archivos y directorios corresponden a datos temporales o productos generados y no deben versionarse:

```text
descarga/data/
descarga/temp/
descarga/logs/
descarga/db/

Procesador/data/resampled/
Procesador/data/rgb/
Procesador/data/output/png/
Procesador/data/output/gif/
Procesador/data/output/diagnostico/
Procesador/data/diagnostico/

pipeline_state.json
pipeline_state.json.tmp

__pycache__/
*.pyc
```

Los recursos necesarios para ejecutar el proyecto deben conservarse:

```text
Procesador/data/conf/
Procesador/data/grids/
Procesador/data/logo/
Procesador/data/shp/
```
```


