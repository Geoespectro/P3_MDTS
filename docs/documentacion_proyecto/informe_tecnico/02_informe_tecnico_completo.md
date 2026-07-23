# Informe técnico completo — SSE-Goes16 / P3 MDTS

| Control documental | Valor |
|---|---|
| Título | Informe técnico completo — SSE-Goes16 / P3 MDTS |
| Proyecto | SSE-Goes16 |
| Rama | `documentacion-exposicion` |
| Commit inspeccionado | `d858d9a` |
| Fecha | 22 de julio de 2026 |
| Estado del documento | Segunda revisión técnica y editorial; apto como base documental, con evidencias experimentales pendientes |
| Alcance de la revisión | Inspección estática de código, configuración, pruebas y documentación; no se ejecutaron pruebas, descargas ni procesamiento científico |

## 1. Resumen y criterio de lectura

SSE-Goes16 implementa en Python una cadena por archivos que obtiene seis bandas del instrumento ABI de GOES-16, las armoniza espacial y físicamente, calcula el producto RGB P3 MDTS y define salidas NetCDF, PNG y GIF. El repositorio también incluye dos diagnósticos independientes y un orquestador capaz de conservar el avance entre ejecuciones. Esta descripción expresa capacidades verificadas por lectura del código, no resultados de una corrida.

La distinción es importante: **implementado** significa que existe una ruta de código y configuración coherente; **inspeccionado** significa que esa ruta fue revisada estáticamente; **ejecutado** exigiría una salida fechada del entorno; y **validado** requeriría criterios técnicos o científicos, datos de referencia y evidencia reproducible. En esta revisión no se eleva ninguna capacidad desde “inspeccionada” a “ejecutada” o “validada”.

El flujo resumido puede consultarse en el [SVG de flujo general](../diagramas/exportados/01_flujo_general.svg). La fuente técnica vigente es el [Mermaid homónimo](../diagramas/fuente_mermaid/01_flujo_general.mmd) y el archivo [Drawio](../diagramas/editables/01_flujo_general.drawio) se conserva como editable visual.

## 2. Propósito, alcance y límites

El objetivo funcional declarado es producir un “Mapa RGB de Tormentas Severas” a partir de observaciones multibanda. La solución cubre adquisición, organización temporal, validación de carpetas, remuestreo, conversión radiométrica, álgebra RGB, persistencia NetCDF, representación cartográfica y animación. La configuración permite procesar un intervalo particular o una secuencia de intervalos según el punto de entrada utilizado.

El alcance actual es local y orientado a filesystem. Los módulos intercambian archivos y reconocen intervalos por nombres `YYYY-MM-DD_HHMM`. No se observa una API web, una cola distribuida, almacenamiento compartido, coordinación horizontal ni monitoreo institucional. Esas ausencias no invalidan el diseño para una estación de trabajo o una ejecución controlada; sí delimitan qué afirmaciones de escalabilidad pueden realizarse.

Tampoco corresponde presentar el RGB como detector confirmado de tormentas severas. El código implementa una composición y rangos determinados, pero el repositorio no aporta referencias científicas suficientes para justificar cada elección ni una comparación con verdad terreno o producto autorizado. Esos puntos permanecen como **referencias y validación científica pendientes**.

## 3. Arquitectura actual

La arquitectura se organiza alrededor de cinco responsabilidades principales:

1. `descarga/goes16Download.py` consulta el repositorio remoto, selecciona archivos y mantiene el inventario `download_db.json`.
2. `run_all.py` coordina la descarga y el procesamiento, valida intervalos y persiste `pipeline_state.json`.
3. `Procesador/src/resampleo_alg_band.py` dirige el procesamiento de uno o varios intervalos.
4. `Procesador/src/helpers_resampleo.py` concentra validaciones numéricas, remuestreo, conversiones, álgebra y escritura NetCDF.
5. `Procesador/src/mapa_rgb.py` produce mapas PNG y reconstruye la animación GIF.

`Procesador/diagnostico/` forma una rama operativa separada. Sus scripts no son llamados por `run_all.py`: se ejecutan explícitamente cuando se desea analizar B13 o la secuencia de PNG. Las pruebas de `test/` verifican una parte de configuración y funciones del descargador/procesador, pero no constituyen una capa transversal completa.

El diagrama de [arquitectura de módulos](../diagramas/exportados/02_arquitectura_modulos.svg) separa pipeline, almacenamiento, configuración y pruebas. Su fuente [Mermaid](../diagramas/fuente_mermaid/02_arquitectura_modulos.mmd), su editable [Drawio](../diagramas/editables/02_arquitectura_modulos.drawio) y el SVG publicado se encuentran sincronizados.

Esta arquitectura ofrece trazabilidad directa: cada etapa deja una salida identificable. Como contrapartida, los contratos están distribuidos entre expresiones regulares, configuraciones y convenciones de nombres. La regla de “exactamente una banda requerida” no está centralizada, y los estados de descarga y orquestación poseen garantías de persistencia diferentes.

## 4. Adquisición de datos

La configuración `descarga/setup.json` selecciona el producto remoto `ABI-L1b-RadF`, las bandas 2, 5, 7, 8, 10 y 13, una ventana temporal y parámetros operativos. En el commit inspeccionado, la fecha y hora inicial/final apuntan al 19 de marzo de 2024 a las 21:00, `timeout` vale 120 segundos y `max_workers` vale 1. La presencia de esa fecha solo prueba una intención configurada; no prueba que el caso haya sido descargado o procesado.

El descargador crea `data`, `temp`, `db` y `logs`, configura `s3fs.S3FileSystem(anon=True)` y verifica la conexión mediante un listado del bucket. Ese chequeo usa un `while True` con espera fija de 60 segundos cuando falla. Luego determina el instante inicial: si `download_db.json` contiene un último intervalo cuya lista tiene tantos elementos como bandas configuradas, reanuda diez minutos después; de lo contrario comienza en la fecha configurada.

Para cada instante construye la ruta remota y filtra el listado por número de banda y prefijo temporal. El diccionario `filtered_files` conserva una ruta por número de banda. Cada archivo seleccionado se descarga primero a `descarga/temp/`. Si el temporal tiene tamaño mayor que cero, se mueve a `descarga/data/<intervalo>/`; si está vacío, se elimina. Una excepción individual se registra y no se propaga fuera de `download_file`.

Después del movimiento, el worker agrega la ruta remota a la estructura global `download_db` y llama a `helpers.writeJson`. Esta función abre directamente el archivo de destino y serializa el diccionario. Aunque la configuración actual usa un solo worker, el código admite valores mayores y no protege ni la mutación compartida ni la escritura. Por eso la posible carrera es un riesgo de diseño verificable, pero su impacto real no fue medido en esta revisión.

El descargador considera completa una carpeta si detecta presencia de todas las bandas requeridas en los nombres. No exige una única coincidencia por banda ni comprueba la estructura interna NetCDF. Si falta alguna banda, espera los 120 segundos configurados y vuelve a consultar el mismo intervalo. El bucle no establece un máximo de reintentos. El parámetro `--max-retries` de `run_all.py` no limita esos intentos internos: se aplica a fallos de procesamiento administrados por el orquestador.

## 5. Organización y validación de intervalos

La unidad de trabajo es una carpeta `descarga/data/YYYY-MM-DD_HHMM/`. El descargador deriva ese nombre desde año, día juliano, hora y minuto. `run_all.py` ignora directorios que no cumplan su expresión regular de intervalo, extrae bandas de los `.nc` mediante `M6C(\d{2})_` y agrupa las coincidencias.

Aquí el contrato es más estricto que en descarga: `is_folder_complete` exige que cada una de las seis bandas aparezca exactamente una vez. `get_folder_problem` diferencia faltantes y duplicados. Una carpeta incompleta puede estar todavía recibiendo archivos; una duplicada se informa como no procesable. No hay eliminación automática de duplicados.

Antes de entregar un intervalo al procesador, el orquestador calcula una firma compuesta por nombre, tamaño y `mtime_ns` de cada `.nc`. Espera `stability_seconds` y vuelve a calcularla; solo considera estable una firma idéntica, salvo que el operador solicite omitir esa espera. Los intervalos estables se recuerdan en `pipeline_state.json`. Esta es una comprobación operacional útil contra escrituras en curso, pero no valida que el NetCDF pueda abrirse ni que su contenido científico sea correcto.

El [diagrama de descarga, validación y estado](../diagramas/exportados/04_descarga_validacion_y_estado.svg) distingue las comprobaciones reales de cada módulo y separa explícitamente las mejoras propuestas. La fuente técnica vigente es el [Mermaid correspondiente](../diagramas/fuente_mermaid/04_descarga_validacion_y_estado.mmd). Esta separación evita presentar persistencia atómica, reintentos finitos o un validador compartido como capacidades existentes.

## 6. Persistencia y recuperación

Existen dos mecanismos de estado con objetivos diferentes. `descarga/db/download_db.json` es un inventario jerárquico por año, día juliano, hora y minuto. Permite omitir rutas ya registradas y elegir un punto de reanudación. Si el JSON no puede decodificarse al iniciar, el descargador lo reemplaza por una estructura vacía. Esa recuperación evita detenerse, pero descarta el inventario previo; los archivos físicos vuelven a contrastarse solo dentro del flujo posterior.

`pipeline_state.json`, administrado exclusivamente por `run_all.py`, registra intervalos procesados, mapeados, fallidos y estables; además guarda conteos de reintentos, firmas fallidas y últimos errores. `save_state` escribe un temporal, ejecuta `flush` y `fsync`, y luego reemplaza el archivo final. Por lectura, esta persistencia es atómica en el filesystem esperado.

El orquestador normaliza estados anteriores y tolera JSON inválido creando un estado nuevo. Si un intervalo falló y luego cambia su firma de archivos, limpia su historial de fallo y vuelve a habilitar intentos. Si ya existen productos no vacíos, puede omitir etapas; para el GIF también comprueba que sea al menos tan reciente como el PNG más nuevo. El valor predeterminado de reintentos de procesamiento es dos. No debe confundirse esta recuperación con una transacción global: un corte entre etapas puede dejar productos existentes y estado incompleto, situación que el siguiente arranque intenta reconciliar mediante validaciones de archivos.

La [secuencia por intervalo](../diagramas/exportados/03_secuencia_procesamiento_intervalo.svg) deja claro que el procesador y el mapa retornan control al orquestador. Su fuente técnica vigente es el [Mermaid correspondiente](../diagramas/fuente_mermaid/03_secuencia_procesamiento_intervalo.mmd). Solo después `run_all.py` valida productos y persiste el estado; ni `resampleo_alg_band.py` ni `mapa_rgb.py` escriben `pipeline_state.json`.

## 7. Procesamiento físico y remuestreo

`Procesador/data/conf/config_resampleo.json` declara las seis bandas con dos dígitos, B13 como referencia, interpolación `linear`, guardado de bandas remuestreadas desactivado y rangos de normalización. `process_single_interval` valida la carpeta, localiza la banda de referencia y abre su dataset para obtener coordenadas y metadatos.

Para cada banda, `resample_band` interpola la variable `Rad` a las coordenadas `x` e `y` de B13 mediante xarray. La decisión ofrece una grilla común necesaria para restar matrices compatibles. No se revisó empíricamente el error introducido por interpolación ni se compararon métodos alternativos. El procesador mantiene los resultados convertidos en un diccionario hasta completar el álgebra, lo que implica seis arreglos y temporales en memoria; el consumo no fue perfilado.

Las bandas B02 y B05 se convierten de radiancia a reflectancia usando `kappa0`. B07, B08, B10 y B13 se convierten a temperatura de brillo mediante constantes de Planck del dataset y luego de kelvin a grados Celsius. Las funciones verifican variables requeridas y condiciones inválidas. Las pruebas unitarias declaradas cubren ejemplos sintéticos de estas conversiones, pero no datos reales ni compatibilidad de metadatos entre productos.

La composición implementada es rojo `B08 - B10`, verde `B07 - B13` y azul `B05 - B02`. Los rangos configurados son `[-35, 5]`, `[-10, 90]` y `[-0.75, 0.5]`, respectivamente. Cada diferencia se transforma linealmente y se recorta a `[0,1]`. El código rechaza canales totalmente `NaN`. La fórmula y los rangos son hechos comprobados por lectura; su interpretación meteorológica y adecuación al caso de estudio continúan pendientes de referencia científica y validación.

## 8. Generación del NetCDF RGB

`save_rgb_to_netcdf` crea un `xarray.Dataset` con variables `Red`, `Green` y `Blue` sobre dimensiones `y` y `x`. Copia coordenadas, atributos globales y atributos de coordenadas desde B13, evita heredar codificaciones internas de enteros y agrega descripciones del procesamiento. Si están presentes, conserva variables geoespaciales como `goes_imager_projection`, extensión latitud/longitud, subpunto satelital y límites de imagen. Los tres canales reciben `grid_mapping` y rango válido `[0,1]` cuando existe la proyección.

La ruta prevista es `Procesador/data/rgb/<intervalo>/<intervalo>_rgb_result.nc`. `run_all.py` comprueba que el archivo esperado exista y no esté vacío antes de registrar el intervalo como procesado. Esa validación no reabre el dataset ni verifica dimensiones, variables o georreferencia: son comprobaciones recomendadas para una prueba de integración futura.

## 9. Cartografía y GIF

`mapa_rgb.py` localiza NetCDF RGB, valida nombres de variables configurados y compone un arreglo de imagen seguro. El recorte usa grillas auxiliares de latitud y longitud a 8 km, interpreta el atributo textual de resolución y calcula índices para la región. Luego crea una proyección geostacionaria con metadatos del dataset, agrega costas, límites, grilla, título, pie y logo, y guarda un PNG con prefijo configurable.

La salida esperada queda en `Procesador/data/output/png/`. El código depende de recursos bajo `Procesador/data`: grillas, logo y shapefiles. Su presencia fue inventariada, pero no se verificaron visualmente el recorte, la alineación, la legibilidad ni las licencias y atribuciones de los recursos.

Después del mapa, `main` reúne todos los PNG que coinciden con el prefijo en el directorio de salida. `build_gif` los abre, convierte a RGB y guarda una animación en bucle con duración configurada de 0,7 segundos por cuadro. No usa un manifiesto de corrida; por eso podría mezclar conjuntos si conviven imágenes compatibles de ejecuciones diferentes. Además, reconstruye el GIF completo y carga los frames, por lo que costo y memoria crecen con la colección.

## 10. Diagnósticos

`diagnostico_b13.py` consume específicamente el archivo NetCDF de B13 de cada intervalo de descarga. Localiza la banda con `find_band_file`, exige `Rad`, `x`, `y` y `goes_imager_projection`, convierte a temperatura de brillo, recorta y calcula máscaras térmicas exclusivas. Produce dos PNG por intervalo, un JSON de estadísticas y un CSV consolidado. Los umbrales codificados deben documentarse con fundamento científico antes de interpretar sus categorías como evidencia meteorológica.

`diagnostico_gif_rgb.py`, pese a su nombre histórico, **no abre el GIF**. Lee directamente los PNG cuyo nombre coincide con `CONAE_PRD_GOES16_ABI_MDTS_RGB_*.png`, los ordena, calcula estadísticas por frame y diferencias entre imágenes consecutivas, y escribe `diagnostico_temporal_rgb.csv`. Entre sus métricas están medias RGB, brillo, MAE, RMSE, percentil 95 y proporción de píxeles cuyo cambio supera 0,05. El [diagrama de entradas y salidas](../diagramas/exportados/05_entradas_y_salidas.svg) refleja estas entradas reales sin atribuirle el GIF; su fuente vigente es el [Mermaid correspondiente](../diagramas/fuente_mermaid/05_entradas_y_salidas.mmd).

Los diagnósticos son instrumentos de observación del producto, no pruebas automáticas ni validación científica. No se encontraron sus salidas en la evidencia inspeccionada.

## 11. Operación y control de fallos

`run_all.py` valida rutas requeridas, carga configuración de mapa y puede iniciar el descargador como subproceso. Procesa intervalos de manera secuencial mientras la descarga puede continuar en segundo plano. Cada etapa se invoca con el mismo intérprete Python; un código de salida no exitoso se transforma en fallo del intervalo.

El orquestador detiene el subproceso de descarga al finalizar o ante interrupción. Sus opciones permiten omitir descarga, omitir estabilidad, ajustar espera, reiniciar estado y configurar reintentos de procesamiento. La documentación operativa debe conservar la distinción entre comandos observados en código y comandos efectivamente ejecutados. Esta revisión no ejecutó ninguno.

El modelo de fallos sigue siendo heterogéneo. El descargador registra y continúa frente a varias excepciones; el procesador puede devolver resultados falsos o códigos no exitosos; el orquestador registra texto de error y reintenta. No hay una taxonomía compartida que diferencie entrada inválida, dependencia temporal y defecto permanente. Esa clasificación es parte del próximo trabajo recomendado.

## 12. Pruebas y evidencia

El recuento directo de métodos con nombre `test_*` da **27 pruebas declaradas**: 4 en `test/test_descarga.py` y 23 en `test/test_procesador.py`. Las primeras inspeccionan estructura, JSON y capacidad de importar helpers. Las segundas cubren configuraciones, completitud y selección de bandas, normalización, rangos, conversiones físicas y álgebra. El recuento no equivale a resultados aprobados: la suite no se ejecutó durante esta revisión.

No se observan pruebas de `run_all.py`, acceso S3 simulado, carrera de persistencia, remuestreo integral, escritura y reapertura del NetCDF final, cartografía, GIF o diagnósticos. Tampoco se observó una configuración de integración continua. Estas brechas justifican una suite determinista sin red antes de automatizar CI.

El repositorio aporta código, configuraciones, pruebas, documentación, grillas, logo y shapefiles. No se encontraron en el inventario compartido NetCDF RGB, PNG finales, GIF, diagnósticos, logs ni una salida de pruebas. Como varias rutas están ignoradas, su ausencia del repositorio no demuestra que nunca hayan existido; demuestra que no están disponibles como evidencia reproducible para esta revisión.

## 13. Riesgos y mantenimiento

Los riesgos de prioridad mayor son la escritura no sincronizada de `download_db.json`, los bucles de descarga sin límite y la divergencia entre validadores de banda. Luego aparecen la ausencia de integración, el uso de memoria sin medición, la fragilidad de recorte frente a metadatos inesperados, la reconstrucción global del GIF y una observabilidad limitada a mensajes y estados locales.

La escalabilidad horizontal no debe ser la primera respuesta. Distribuir una cadena cuyos contratos y garantías de idempotencia todavía no están unificados amplificaría los fallos. Primero conviene medir volumen, duración y memoria; asegurar estados; y obtener una prueba de extremo a extremo pequeña. Recién con demanda demostrada tendría sentido separar servicios o introducir coordinación compartida.

También existe riesgo de deriva documental. Nombres, rutas y valores configurables pueden cambiar sin actualizar los diagramas o la presentación. La organización revisada establece `.mmd` como fuente textual canónica, `.drawio` como editable visual y SVG como formato de lectura. Los seis diagramas fueron sincronizados después de esta revisión; cualquier modificación futura deberá replicarse en los tres formatos.

## 14. Referencias disponibles y pendientes

Las referencias internas disponibles son `README.md`, `docs/Readme_descarga.md`, `docs/Readme_procesador.md`, los tres JSON de configuración y los docstrings/comentarios del código. Permiten reconstruir intención, operación y fórmulas. No sustituyen publicaciones científicas externas ni especificaciones oficiales del producto.

Quedan marcadores pendientes para: origen científico de la composición; justificación de rangos de normalización; fundamento de umbrales B13; referencia oficial y condiciones de uso de los datos; atribución de grillas, logo y shapefiles; y método de validación geoespacial y meteorológica. Esta revisión no agrega citas inexistentes.

## 15. Recomendación y criterio de aceptación

El próximo trabajo concreto debe ser **robustez de descarga y contrato de intervalos**: unificar la regla de bandas, serializar y hacer atómica la persistencia de descarga, definir fallos recuperables/terminales, limitar reintentos con backoff y cubrir los escenarios con pruebas sin red. El alcance debe preservar fórmula RGB, referencia B13 y salidas actuales.

Después corresponde reunir una corrida reproducible: commit, entorno, configuración, manifiesto y checksums de entradas, resultados de pruebas, NetCDF reabierto y validado estructuralmente, PNG revisado geoespacialmente, GIF con frames declarados, diagnósticos y métricas básicas de tiempo/memoria. Solo con ese paquete podrá actualizarse la presentación desde “productos previstos” hacia “productos generados y verificados”.

## 16. Conclusión

SSE-Goes16 contiene una cadena técnicamente reconocible desde adquisición hasta visualización, con persistencia recuperable del orquestador y una composición RGB explícita. La lectura del repositorio permite afirmar que esas capacidades están implementadas; no permite afirmar que la corrida configurada haya ocurrido, que sus productos sean correctos o que el método esté científicamente validado.

El avance responsable no consiste en sumar complejidad, sino en cerrar la distancia entre código y evidencia: contratos únicos, fallos finitos, estado seguro, pruebas deterministas y una ejecución controlada. Ese orden protege la lógica científica existente y crea una base verificable para futuras mejoras operativas e institucionales.
