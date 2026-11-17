# Glosario

Las definiciones describen el uso de los términos dentro de este proyecto.

| Término | Definición en el proyecto |
|---|---|
| ABI | Instrumento Advanced Baseline Imager utilizado por los satélites GOES-16 y GOES-19 y asociado a los archivos procesados por el proyecto. |
| GOES-16 | Satélite utilizado como fuente de datos ABI para distintos períodos históricos y actuales. |
| GOES-19 | Satélite soportado por el pipeline como fuente de datos ABI. |
| Mode 3 | Modo operativo histórico de GOES-16 asociado a archivos con nomenclatura `M3Cxx`. |
| Mode 6 | Modo operativo asociado a archivos con nomenclatura `M6Cxx`, utilizado en períodos posteriores y por GOES-19. |
| Banda | Canal numerado del producto ABI; en este proyecto: 02, 05, 07, 08, 10 y 13. |
| Reflectancia | Magnitud calculada como `Rad × kappa0` para B02 y B05; el código la trata como adimensional. |
| Temperatura de brillo | Magnitud derivada de radiancia y constantes de Planck; el código la convierte de K a °C. |
| Remuestreo | Interpolación de `Rad` a coordenadas comunes mediante `xarray.interp`. |
| Grilla de referencia | Conjunto de coordenadas `x/y` tomado de B13 al que se llevan las otras bandas. |
| B13 | Banda 13, utilizada como referencia espacial y como una de las bandas térmicas del cálculo del canal verde. |
| RGB | Imagen compuesta por tres canales normalizados: rojo, verde y azul. |
| NetCDF | Formato utilizado tanto para las bandas de entrada como para la salida RGB georreferenciada. |
| PNG | Formato utilizado para cada mapa estático generado. |
| GIF | Animación construida a partir de los PNG ordenados temporalmente. |
| Intervalo | Carpeta o instante de trabajo identificado con formato `AAAA-MM-DD_HHMM`. |
| S3 | Almacenamiento remoto consultado de forma anónima mediante `s3fs`. |
| NOAA | Organismo proveedor de los repositorios públicos utilizados para la descarga de datos GOES. |
| Cartopy | Biblioteca utilizada para proyección y elementos cartográficos. |
| Shapefile | Conjunto de archivos vectoriales opcionales utilizados para representar límites personalizados. |
| Diagnóstico | Análisis auxiliar separado del pipeline principal, como B13 o continuidad temporal del RGB. |
| Orquestador | `run_all.py`, encargado de coordinar descarga, detección de intervalos, procesamiento, generación cartográfica y estado. |
| Estado persistente | Información almacenada en archivos JSON que permite recuperar progreso entre ejecuciones. |
| `download_db.json` | Registro local de archivos descargados utilizado por el módulo de descarga. |
| `pipeline_state.json` | Estado operativo mantenido por `run_all.py` para registrar intervalos procesados, mapeados, fallidos y estables. |
| Reintento | Nuevo intento después de un fallo. El orquestador limita los reintentos de procesamiento, mientras que algunas esperas del descargador pueden continuar hasta que la condición cambie. |
| Backoff | Estrategia de aumento progresivo de la espera entre reintentos; actualmente se considera una posible mejora de robustez. |
| P3 MDTS | Producto **Mapa RGB de Tormentas Severas** generado por el pipeline a partir de las seis bandas ABI configuradas. |