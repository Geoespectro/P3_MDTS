# Resumen ejecutivo

## Problema y objetivo

El proyecto aborda la obtención y transformación de observaciones multibanda del sensor ABI de GOES-16 en un producto RGB integrado que pueda visualizarse como mapa y animación. Su objetivo general es automatizar una cadena reproducible desde la descarga de datos hasta la generación del producto P3 MDTS, conservando georreferencia y estado operativo. (Fuentes: `README.md`; `run_all.py`)

## Solución desarrollada

La solución es un pipeline Python modular:

1. consulta el repositorio S3 público configurado para el producto `ABI-L1b-RadF`;
2. descarga B02, B05, B07, B08, B10 y B13 por intervalo;
3. valida que el intervalo esté completo y estable;
4. interpola las bandas a la grilla de B13;
5. convierte B02/B05 a reflectancia y B07/B08/B10/B13 a temperatura de brillo en °C;
6. calcula y normaliza tres diferencias de bandas;
7. guarda un NetCDF RGB georreferenciado;
8. produce un mapa PNG y reconstruye un GIF. (Fuentes: `descarga/setup.json`; `Procesador/src/resampleo_alg_band.py`; `Procesador/src/helpers_resampleo.py`; `Procesador/src/mapa_rgb.py`)

La composición implementada es:

- rojo = B08 − B10;
- verde = B07 − B13;
- azul = B05 − B02. (Fuente: `Procesador/src/helpers_resampleo.py`, función `band_algebra`)

## Productos y estado actual

El código define como productos un NetCDF por intervalo, un PNG cartográfico por intervalo, un GIF global y diagnósticos B13/RGB. `run_all.py` mantiene `pipeline_state.json`, evita repetir productos válidos y limita a dos los reintentos de **procesamiento** por defecto. (Fuentes: `Procesador/data/conf/config_mapa.json`; `run_all.py`, funciones `process_interval`, `save_state` y `build_parser`)

Son resultados comprobables por inspección: la existencia del flujo, las fórmulas, configuraciones, validaciones y 27 métodos de prueba declarados. No se ejecutaron pruebas y no se encontraron productos finales o reportes de ejecución en el inventario actual; por eso no se afirma rendimiento, exactitud ni validez científica.

## Limitaciones principales

- La base `download_db.json` puede ser actualizada por workers concurrentes sin bloqueo ni escritura atómica.
- La reconexión S3 y la espera por intervalos incompletos no tienen un máximo explícito dentro del descargador.
- La validación de duplicados no es uniforme entre descargador, procesador y orquestador.
- El procesamiento conserva las seis matrices convertidas en memoria.
- El recorte depende de grillas auxiliares de 8 km y de interpretar un atributo textual de resolución.
- Cada actualización del mapa reconstruye el GIF con todos los PNG del directorio.
- Las pruebas no cubren integración S3, orquestación, cartografía, GIF ni diagnósticos; no se observó configuración de CI. (Fuentes: código citado en [limitaciones](../mejoras/01_limitaciones_actuales.md))

## Próximos pasos

La acción prioritaria es robustecer descarga y contrato de intervalos: serializar y hacer atómica la persistencia de descarga, clasificar fallos, aplicar reintentos finitos con backoff y centralizar la regla “exactamente un archivo por banda”. Debe acompañarse con pruebas sin red. Luego corresponde generar una corrida reproducible y reunir NetCDF, PNG, GIF, diagnósticos y resultados de pruebas para validar el caso de estudio.

## Conclusión

El repositorio contiene una cadena técnica completa en términos de código, con separación reconocible entre descarga, procesamiento, cartografía, diagnóstico y orquestación. Su madurez documental y operativa depende ahora de convertir esa implementación en evidencia reproducible, reforzar los puntos de fallo y respaldar científicamente las decisiones del producto.
