# Procesador P3 MDTS

## Propósito

El módulo `Procesador/` genera el producto **Mapa RGB de Tormentas Severas** a partir de intervalos completos de bandas GOES-16 ABI.

El procesamiento incluye resampleo espacial, conversión radiométrica, álgebra RGB, normalización fija, generación de un NetCDF georreferenciado, mapas PNG y un GIF animado.

## Requisitos

- Python 3.10 o superior.
- Dependencias instaladas desde `requirements.txt`.
- Grillas auxiliares de latitud y longitud.
- Logo institucional.
- Shapefiles opcionales para límites personalizados.

## Estructura

```text
Procesador/
├── data/
│   ├── conf/
│   │   ├── config_mapa.json
│   │   └── config_resampleo.json
│   ├── grids/
│   │   ├── g16_lats_8km.txt
│   │   └── g16_lons_8km.txt
│   ├── logo/
│   │   └── logo.png
│   ├── output/
│   │   ├── diagnostico/
│   │   ├── gif/
│   │   └── png/
│   ├── resampled/
│   ├── rgb/
│   └── shp/
├── diagnostico/
│   ├── diagnostico_b13.py
│   └── diagnostico_gif_rgb.py
└── src/
    ├── helpers_resampleo.py
    ├── mapa_rgb.py
    └── resampleo_alg_band.py
```

## Scripts principales

- `src/resampleo_alg_band.py`: procesa uno o todos los intervalos y genera NetCDF RGB.
- `src/helpers_resampleo.py`: validaciones, resampleo, conversiones físicas, álgebra RGB y guardado NetCDF.
- `src/mapa_rgb.py`: genera mapas PNG y reconstruye el GIF.
- `diagnostico/diagnostico_b13.py`: analiza temperatura de brillo B13 y núcleos fríos.
- `diagnostico/diagnostico_gif_rgb.py`: analiza continuidad temporal y cambios espaciales del RGB.

## Flujo

```text
descarga/data/<intervalo>/
→ validación de seis bandas
→ resampleo a la grilla de B13
→ conversión a unidades físicas
→ álgebra RGB
→ normalización fija
→ NetCDF RGB georreferenciado
→ recorte y representación cartográfica
→ PNG
→ GIF
```

## Configuración del resampleo

Archivo:

```text
Procesador/data/conf/config_resampleo.json
```

Configuración esperada:

```json
{
  "bands_list": ["02", "05", "07", "08", "10", "13"],
  "reference_band": "13",
  "resample_method": "linear",
  "save_resampled_bands": false,
  "rgb_ranges": {
    "red": [-35.0, 5.0],
    "green": [-10.0, 90.0],
    "blue": [-0.75, 0.50]
  }
}
```

- `bands_list`: bandas obligatorias.
- `reference_band`: banda cuya grilla `x/y` se usa como referencia.
- `resample_method`: método de interpolación usado por `xarray`.
- `save_resampled_bands`: controla si se guardan bandas intermedias.
- `rgb_ranges`: límites fijos usados para normalizar cada canal RGB.

Cuando `save_resampled_bands` es `false`, las bandas resampleadas permanecen en memoria. Cuando es `true`, se guardan en:

```text
Procesador/data/resampled/<intervalo>/
```

## Validación de entrada

La entrada debe existir en:

```text
descarga/data/<intervalo>/
```

Cada intervalo debe contener exactamente un archivo para cada banda:

```text
B02, B05, B07, B08, B10 y B13
```

Si falta una banda o existe más de un archivo coincidente para una misma banda, el intervalo no se procesa correctamente y se informa el error.

## Resampleo

Todas las bandas se interpolan a la grilla de B13 mediante:

```text
xarray.DataArray.interp()
```

El procesador resamplea `Rad` y conserva las variables de calibración necesarias para la conversión física.

## Conversión física

### Bandas reflectivas

```text
B02 y B05
```

Se convierten mediante:

```text
reflectancia = radiancia × kappa0
```

### Bandas térmicas

```text
B07, B08, B10 y B13
```

Se convierten a temperatura de brillo mediante las constantes de Planck del NetCDF y luego a grados Celsius.

## Composición RGB

```text
Red   = B08 - B10
Green = B07 - B13
Blue  = B05 - B02
```

Los canales se calculan después de convertir las bandas a sus unidades físicas.

## Normalización

Los canales se normalizan al rango `[0, 1]` usando los límites definidos en:

```text
Procesador/data/conf/config_resampleo.json
```

Configuración actual:

```text
Red   → -35.0 a 5.0
Green → -10.0 a 90.0
Blue  → -0.75 a 0.50
```

Los valores externos a cada rango se recortan a `0` o `1`.

## NetCDF RGB

Salida:

```text
Procesador/data/rgb/<intervalo>/<intervalo>_rgb_result.nc
```

Variables principales:

```text
Red
Green
Blue
x
y
goes_imager_projection
```

El archivo conserva la información geoespacial disponible en la banda de referencia y vincula los canales con `goes_imager_projection` mediante el atributo `grid_mapping`.

## Configuración del mapa

Archivo:

```text
Procesador/data/conf/config_mapa.json
```

Controla:

- región;
- rutas de entrada y salida;
- grillas auxiliares;
- shapefiles;
- logo;
- tamaño y resolución;
- título;
- duración de cada cuadro del GIF.

Los shapefiles son opcionales. Si no están presentes, el mapa puede generarse sin esos límites personalizados.

Cartopy puede requerir acceso a internet en la primera ejecución para descargar recursos Natural Earth si no están disponibles en su caché local.

## Mapa PNG

`mapa_rgb.py`:

1. abre el NetCDF RGB;
2. valida dimensiones;
3. calcula el recorte con las grillas auxiliares;
4. crea la proyección geostacionaria;
5. representa el RGB;
6. agrega costas, límites, grilla, título y logo;
7. guarda el PNG.

Salida:

```text
Procesador/data/output/png/
```

Nombre esperado:

```text
CONAE_PRD_GOES16_ABI_MDTS_RGB_<intervalo>.png
```

## GIF

Después de generar los mapas, `mapa_rgb.py` reúne los PNG existentes, los ordena por nombre y reconstruye:

```text
Procesador/data/output/gif/CONAE_PRD_GOES16_ABI_MDTS_RGB_animacion.gif
```

La duración de cada cuadro se define con `gif_frame_duration` en `config_mapa.json`.

## Ejecución

Desde la raíz del proyecto.

### Procesar todos los intervalos

```bash
python Procesador/src/resampleo_alg_band.py
```

### Procesar un intervalo

```bash
python Procesador/src/resampleo_alg_band.py --interval 2024-12-06_2300
```

### Generar todos los mapas y el GIF

```bash
python Procesador/src/mapa_rgb.py
```

### Generar un mapa y actualizar el GIF

```bash
python Procesador/src/mapa_rgb.py --interval 2024-12-06_2300
```

## Diagnósticos

### B13 para un intervalo

```bash
python Procesador/diagnostico/diagnostico_b13.py \
  --interval 2024-12-06_2300
```

### B13 para todos los intervalos

```bash
python Procesador/diagnostico/diagnostico_b13.py --all
```

También puede ejecutarse sin argumentos para procesar todos los intervalos encontrados:

```bash
python Procesador/diagnostico/diagnostico_b13.py
```

Genera:

```text
<intervalo>_B13_BT.png
<intervalo>_B13_mascaras.png
<intervalo>_B13_estadisticas.json
diagnostico_b13_estadisticas.csv
```

### Evolución temporal RGB

```bash
python Procesador/diagnostico/diagnostico_gif_rgb.py
```

Genera:

```text
diagnostico_temporal_rgb.csv
```

Incluye medias RGB, brillo, MAE, RMSE, percentil 95 y porcentaje de píxeles con cambios significativos.

## Pipeline completo

```bash
python run_all.py
```

Para procesar solamente intervalos ya descargados:

```bash
python run_all.py --skip-download
```

## Pruebas

Desde la raíz:

```bash
python test/test_procesador.py
```

O toda la suite:

```bash
python -m unittest discover -s test -p "test_*.py" -v
```

## Salidas generadas

```text
Procesador/data/
├── resampled/
├── rgb/
└── output/
    ├── diagnostico/
    ├── gif/
    └── png/
```

Estos productos no deben versionarse.
