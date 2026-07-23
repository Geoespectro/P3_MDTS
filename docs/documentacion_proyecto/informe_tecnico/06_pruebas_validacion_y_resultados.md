# Pruebas, validación y resultados

## Criterio de lectura

`Comprobado por inspección` significa que el código/archivo existe y fue leído. **No significa que fue ejecutado**.

## A. Pruebas automatizadas existentes

| Grupo | Objetivo / entrada | Comprobación y salida | Estado / limitación |
|---|---|---|---|
| Descarga (`test/test_descarga.py`, 4 métodos) | Árbol, `descarga/setup.json`, carpetas, importación | Aserciones `unittest` | Comprobado por inspección; una prueba crea carpetas; sin S3 |
| Procesador (`test/test_procesador.py`, 23 métodos) | JSON reales y datos sintéticos | configuración, bandas, normalización, conversiones y álgebra | Comprobado por inspección; no prueba compatibilidad ambiental ni integración |
| Detección de bandas | archivos temporales sintéticos | completo, faltante, selección, inexistencia, duplicado | Comprobado por inspección; no usa NetCDF reales |
| Normalización/rangos | arreglos NumPy | valores, recorte y errores | Comprobado por inspección |
| Conversiones | datasets sintéticos xarray | reflectancia, temperatura y errores | Comprobado por inspección; no contrasta valores de un producto real |
| Álgebra RGB | seis arreglos sintéticos | fórmulas, rangos, faltante y NaN | Comprobado por inspección; no genera NetCDF/PNG |

La suite suma **27 métodos** declarados: 4 en `test/test_descarga.py` y 23 en `test/test_procesador.py`. No cubre `run_all.py`, descarga real/simulada de S3, persistencia concurrente, `resample_band`, escritura/lectura NetCDF final, mapa, GIF ni diagnósticos.

## B. Diagnósticos científicos

| Diagnóstico | Entrada | Comprobación / salida prevista | Estado y limitaciones |
|---|---|---|---|
| `Procesador/diagnostico/diagnostico_b13.py` | B13 por intervalo y configuración de mapa | BT, máscaras, estadísticas por intervalo y CSV consolidado | Código inspeccionado; no ejecutado; umbrales sin referencia incluida |
| `Procesador/diagnostico/diagnostico_gif_rgb.py` | PNG que coinciden con el patrón fijo `CONAE_PRD_GOES16_ABI_MDTS_RGB_*.png` (`PNG_PATTERN` en el script) | CSV de medias, brillo, MAE, RMSE, p95 y cambio >0,05 | Código inspeccionado; no ejecutado; mide cambios de imagen, no severidad meteorológica |

## C. Verificaciones manuales recomendadas

- Confirmar seis archivos no vacíos y únicos por intervalo.
- Inspeccionar metadatos/calibración y dimensiones del NetCDF.
- Confirmar valores finitos y rango `[0,1]` de canales.
- Verificar georreferencia y recorte contra una referencia autorizada.
- Revisar orden temporal del GIF y separación entre corridas.
- Comparar diagnósticos con un caso documentado por especialistas.

Estado: **pendientes**.

## D. Evidencias disponibles

- Código y configuraciones que definen el algoritmo.
- Documentación operativa existente.
- Pruebas unitarias declaradas.
- Grillas, logo y shapefiles usados por cartografía.

No se encontraron resultados de pruebas, NetCDF RGB, PNG finales, GIF, CSV/JSON de diagnóstico o logs. Véase [inventario](../evidencias/01_inventario_evidencias.md).

## E. Validaciones pendientes

1. Ejecutar la suite en un entorno controlado y conservar salida/versiones.
2. Probar descarga sin red con un adaptador o mock de S3.
3. Ejecutar un intervalo con fixture NetCDF pequeño.
4. Validar recuperación ante interrupción y JSON corrupto/concurrente.
5. Comparar georreferencia, valores y representación con criterios de aceptación.
6. Medir tiempo y memoria con un conjunto definido.
7. Obtener revisión científica y referencias para composición, rangos y umbrales.

Aunque `descarga/setup.json` menciona el 19 de marzo de 2024, no hay productos o informe asociado visibles: **[EVIDENCIA PENDIENTE: caso 19-03-2024]**.
