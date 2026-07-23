# Operación y ejecución

> Los comandos siguientes **no fueron ejecutados durante esta documentación**. Las etiquetas indican su origen.

## Requisitos e instalación

- Linux, Python 3.10+ y conexión para S3. `[DOCUMENTADO]`
- Docker usa Python 3.12 y paquetes del sistema para GEOS, PROJ, NetCDF/HDF5 e imágenes. `[DOCUMENTADO]`

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`[DOCUMENTADO]` en `README.md`. `[PENDIENTE DE VALIDACIÓN]` en el entorno actual.

## Configuraciones

Antes de operar, revisar:

- `descarga/setup.json`: ventana, producto, timeout, bandas y workers.
- `Procesador/data/conf/config_resampleo.json`: referencia, método y rangos.
- `Procesador/data/conf/config_mapa.json`: rutas, región, mapa y GIF.

La configuración actual limita la descarga a `2024-03-19 21:00`, con fin también a `21:00`; el ejemplo de `docs/Readme_descarga.md` muestra `21:20`, por lo que no debe confundirse ejemplo con estado actual.

## Descarga

```bash
python descarga/goes16Download.py
```

`[DOCUMENTADO]`. Genera datos bajo `descarga/data/`, temporales, logs y `download_db.json`. Requiere red y no se validó.

## Procesar un intervalo

```bash
python Procesador/src/resampleo_alg_band.py --interval 2024-03-19_2100
python Procesador/src/mapa_rgb.py --interval 2024-03-19_2100
```

`[DOCUMENTADO]`; el nombre se adaptó a la ventana actual. `[PENDIENTE DE VALIDACIÓN]` para existencia de ese intervalo y resultados.

## Orquestador

```bash
python run_all.py
python run_all.py --skip-download
python run_all.py --skip-download --once
python run_all.py --reset-state
```

Los dos primeros y `--reset-state` están `[DOCUMENTADO]`; `--once` está `[INFERIDO DEL CÓDIGO]`. También existen `--poll-seconds`, `--stability-seconds`, `--max-retries` y `--retry-delay`. No usar `--reset-state` sin comprender que elimina `pipeline_state.json`.

## Salidas esperadas

```text
descarga/data/<intervalo>/*.nc
Procesador/data/rgb/<intervalo>/<intervalo>_rgb_result.nc
Procesador/data/output/png/CONAE_PRD_GOES16_ABI_MDTS_RGB_<intervalo>.png
Procesador/data/output/gif/CONAE_PRD_GOES16_ABI_MDTS_RGB_animacion.gif
```

`[DOCUMENTADO]` y respaldado por configuración/código. No se encontraron ejemplos actuales.

## Diagnósticos

```bash
python Procesador/diagnostico/diagnostico_b13.py --interval 2024-03-19_2100
python Procesador/diagnostico/diagnostico_b13.py --all
python Procesador/diagnostico/diagnostico_gif_rgb.py
```

`[DOCUMENTADO]`, `[PENDIENTE DE VALIDACIÓN]`. B13 produce mapas, máscaras, JSON y CSV; el diagnóstico RGB produce un CSV temporal.

## Pruebas

```bash
python -m unittest discover -s test -p "test_*.py" -v
```

`[DOCUMENTADO]`, `[PENDIENTE DE VALIDACIÓN]`. Algunas pruebas crean directorios de trabajo o temporales; por restricción no fueron ejecutadas.

## Limpieza

```bash
python clean.py
```

`[DOCUMENTADO]`, pero **no ejecutar sin revisar el código**: `DRY_RUN = False` en el repositorio actual y todas las categorías están activadas, por lo que elimina contenidos generados. La documentación raíz dice revisar `DRY_RUN = True`; hoy no está activado. (Fuente: `clean.py:20-36`)

## Recuperación y errores conocidos

| Situación | Acción conservadora | Estado |
|---|---|---|
| Interrupción del orquestador | Reiniciar; lee `pipeline_state.json` y productos existentes | `[INFERIDO DEL CÓDIGO]` |
| JSON del orquestador corrupto | El código comienza con estado vacío | `[INFERIDO DEL CÓDIGO]` |
| Banda faltante/duplicada | Corregir la carpeta o esperar nueva descarga | `[INFERIDO DEL CÓDIGO]` |
| S3 inaccesible | Revisar red; el descargador espera y reintenta | `[DOCUMENTADO]` |
| Primer mapa sin caché Cartopy | Puede requerir recursos Natural Earth | `[DOCUMENTADO]` |
| Reintentos de proceso agotados | Corregir entrada; un cambio de firma rehabilita el intervalo | `[INFERIDO DEL CÓDIGO]` |
| Base de descarga inválida | No eliminar automáticamente: respaldar y revisar concurrencia | `[PENDIENTE DE VALIDACIÓN]` |
