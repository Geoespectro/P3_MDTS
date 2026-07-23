# Glosario

Las definiciones describen el uso de los términos en este repositorio. Cuando exceden lo demostrable por código se marca la necesidad de referencia.

| Término | Definición en el proyecto |
|---|---|
| ABI | Instrumento/sensor asociado a los archivos GOES-16 usados por el proyecto. `[FUNDAMENTO CIENTÍFICO PENDIENTE DE REFERENCIA]` |
| GOES-16 | Satélite identificado como fuente de los archivos procesados. `[FUNDAMENTO CIENTÍFICO PENDIENTE DE REFERENCIA]` |
| Banda | Canal numerado del producto ABI; aquí: 02, 05, 07, 08, 10 y 13. |
| Reflectancia | Magnitud calculada como `Rad × kappa0` para B02 y B05; el código la declara adimensional. |
| Temperatura de brillo | Magnitud derivada de radiancia y constantes de Planck; el código la convierte de K a °C. |
| Remuestreo | Interpolación de `Rad` a coordenadas comunes mediante `xarray.interp`. |
| Grilla de referencia | Conjunto `x/y` tomado de B13 al que se llevan las otras bandas. |
| B13 | Banda 13, referencia espacial y una de las bandas térmicas del cálculo verde. |
| RGB | Imagen de tres canales normalizados: rojo, verde y azul. |
| NetCDF | Formato de entrada de bandas y salida del RGB georreferenciado. |
| PNG | Formato de cada mapa estático. |
| GIF | Animación construida con los PNG ordenados. |
| Intervalo | Carpeta/momento con formato `AAAA-MM-DD_HHMM`. |
| S3 | Almacenamiento consultado de forma anónima por `s3fs`. |
| NOAA | Organismo nombrado en la documentación como proveedor del repositorio S3. `[REFERENCIA INSTITUCIONAL PENDIENTE]` |
| Cartopy | Biblioteca usada para proyección y elementos cartográficos. |
| Shapefile | Conjunto de archivos vectoriales opcionales para límites personalizados. |
| Diagnóstico | Análisis separado del pipeline: B13 o continuidad temporal de PNG. |
| Orquestador | `run_all.py`, coordinador de descarga, detección, procesamiento y estado. |
| Estado persistente | JSON que permite recuperar progreso entre ejecuciones. |
| Reintento | Nuevo intento después de un fallo; el orquestador limita procesamiento, el descargador no limita todas sus esperas. |
| Backoff | Aumento progresivo de la espera entre reintentos; es una mejora propuesta, no implementada. |
