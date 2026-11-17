# Informe técnico completo — P3 MDTS

| Control documental | Valor |
|---|---|
| Título | Informe técnico completo — P3 MDTS |
| Proyecto | P3 MDTS — Mapa RGB de Tormentas Severas |
| Fecha de actualización | 21 de octubre de 2026 |
| Estado del documento | Documento técnico actualizado |
| Alcance | Arquitectura, adquisición, procesamiento, productos, operación, pruebas y validación funcional |

## 1. Resumen y criterio de lectura

P3 MDTS implementa en Python una cadena de procesamiento que obtiene seis bandas del instrumento ABI de los satélites **GOES-16 y GOES-19**, las armoniza espacial y físicamente, calcula el producto RGB Mapa de Tormentas Severas y genera salidas NetCDF, PNG y GIF.

El repositorio también incluye herramientas de diagnóstico y un orquestador capaz de coordinar descarga, procesamiento y generación cartográfica conservando el avance entre ejecuciones.

El pipeline ha sido ejecutado sobre datos reales correspondientes a distintos períodos y modos operativos. Se realizaron casos de estudio con GOES-16 y pruebas funcionales con GOES-19.

La validación realizada permite verificar el funcionamiento integral del pipeline y analizar la coherencia de sus productos. Esto debe distinguirse de una **validación científica formal**, que requeriría una muestra mayor de eventos, datos de radar, observaciones georreferenciadas y métricas objetivas de desempeño.

El flujo resumido puede consultarse en el [SVG de flujo general](../diagramas/exportados/01_flujo_general.svg). La fuente técnica se conserva en el [Mermaid homónimo](../diagramas/fuente_mermaid/01_flujo_general.mmd) y el archivo [Drawio](../diagramas/editables/01_flujo_general.drawio) se mantiene como editable visual.

---

## 2. Propósito, alcance y límites

El objetivo funcional es producir un **Mapa RGB de Tormentas Severas** a partir de observaciones multibanda del instrumento ABI.

La solución cubre:

```text
adquisición
→ organización temporal
→ validación de intervalos
→ remuestreo
→ conversión radiométrica
→ álgebra RGB
→ normalización
→ persistencia NetCDF
→ representación cartográfica
→ animación
```

La configuración permite procesar un intervalo particular o una secuencia de intervalos según el punto de entrada utilizado.

El alcance actual es local y orientado a filesystem. Los módulos intercambian archivos y reconocen intervalos por nombres:

```text
YYYY-MM-DD_HHMM
```

No se implementa actualmente una API web, cola distribuida, almacenamiento compartido ni coordinación horizontal. Estas características no son necesarias para el funcionamiento actual en una estación de trabajo o entorno controlado, aunque podrían evaluarse ante futuras necesidades de escalabilidad.

El RGB debe interpretarse como una herramienta de apoyo para identificar y seguir **convección profunda e intensa y estructuras asociadas con posibles tormentas severas**.

No constituye por sí solo un detector directo de granizo ni una clasificación meteorológica definitiva.

---

## 3. Arquitectura actual

La arquitectura se organiza alrededor de cinco responsabilidades principales:

1. `descarga/goes16Download.py` consulta el repositorio remoto, selecciona archivos y mantiene el inventario `download_db.json`.
2. `run_all.py` coordina la descarga y el procesamiento, valida intervalos y persiste `pipeline_state.json`.
3. `Procesador/src/resampleo_alg_band.py` dirige el procesamiento de uno o varios intervalos.
4. `Procesador/src/helpers_resampleo.py` concentra validaciones, remuestreo, conversiones físicas, álgebra RGB y escritura NetCDF.
5. `Procesador/src/mapa_rgb.py` produce mapas PNG y reconstruye la animación GIF.

Aunque el descargador conserva el nombre histórico:

```text
goes16Download.py
```

actualmente admite:

```text
GOES-16
GOES-19
```

La selección del satélite se realiza mediante:

```text
descarga/setup.json
```

`Procesador/diagnostico/` constituye una rama auxiliar. Sus herramientas no son llamadas automáticamente por `run_all.py`, sino que se ejecutan cuando se requiere analizar B13 o la evolución temporal del RGB.

El diagrama de [arquitectura de módulos](../diagramas/exportados/02_arquitectura_modulos.svg) separa pipeline, almacenamiento, configuración y pruebas.

La arquitectura mantiene una trazabilidad directa: cada etapa genera una salida identificable que puede utilizarse como entrada o evidencia para la etapa siguiente.

---

## 4. Adquisición de datos

La configuración:

```text
descarga/setup.json
```

define:

```text
satélite
producto
bandas
fecha y hora inicial
fecha y hora final
cadencia temporal
timeout
cantidad de workers
```

Los satélites actualmente soportados son:

```json
"satellite": "goes16"
```

y:

```json
"satellite": "goes19"
```

El producto utilizado es:

```text
ABI-L1b-RadF
```

y las bandas requeridas son:

```text
B02
B05
B07
B08
B10
B13
```

El descargador selecciona automáticamente el bucket NOAA correspondiente al satélite configurado.

La cadencia de descarga se controla mediante:

```json
"interval_minutes": 10
```

Como referencia operativa:

```text
GOES-16 histórico Mode 3  → 15 minutos
GOES-16 Mode 6            → 10 minutos
GOES-19 Mode 6            → 10 minutos
```

Para GOES-16, los archivos históricos anteriores al cambio operacional de 2019 pueden presentar nomenclatura Mode 3.

El sistema reconoce tanto:

```text
M3Cxx
```

como:

```text
M6Cxx
```

Los archivos seleccionados se descargan inicialmente en:

```text
descarga/temp/
```

y, una vez completada la transferencia, se mueven a:

```text
descarga/data/<intervalo>/
```

La base local:

```text
descarga/db/download_db.json
```

registra los archivos descargados y permite recuperar el estado de trabajo.

---

## 5. Organización y validación de intervalos

La unidad de trabajo es una carpeta:

```text
descarga/data/YYYY-MM-DD_HHMM/
```

Cada intervalo debe contener las seis bandas requeridas:

```text
02
05
07
08
10
13
```

La detección de bandas admite:

```text
M3C02
M3C05
...
```

y:

```text
M6C02
M6C05
...
```

`run_all.py` utiliza un patrón compatible con ambos modos:

```text
M[36]Cxx
```

El orquestador verifica que cada banda requerida aparezca exactamente una vez.

Una carpeta con bandas faltantes se considera incompleta. Una carpeta con duplicados se informa como no procesable hasta corregir la entrada.

Antes de entregar un intervalo al procesador, el orquestador calcula una firma basada en:

```text
nombre
tamaño
mtime
```

de los archivos NetCDF.

Luego espera el tiempo de estabilidad configurado y vuelve a calcularla. Solo procesa el intervalo cuando la firma permanece estable.

Esta comprobación reduce el riesgo de comenzar a procesar archivos todavía en escritura.

El [diagrama de descarga, validación y estado](../diagramas/exportados/04_descarga_validacion_y_estado.svg) representa este flujo.

---

## 6. Persistencia y recuperación

Existen dos mecanismos de estado con objetivos diferentes.

### Estado de descarga

```text
descarga/db/download_db.json
```

mantiene el inventario de archivos descargados.

Permite evitar transferencias repetidas y recuperar el avance dentro de la ventana temporal configurada.

### Estado del pipeline

```text
pipeline_state.json
```

es administrado por `run_all.py`.

Registra información sobre:

```text
intervalos procesados
intervalos mapeados
intervalos fallidos
intervalos estables
reintentos
firmas
últimos errores
```

La escritura del estado utiliza un archivo temporal seguido de reemplazo del archivo definitivo, reduciendo el riesgo de dejar un JSON parcialmente escrito.

Si un intervalo falló y posteriormente cambia su firma de archivos, el orquestador puede volver a habilitar su procesamiento.

Si determinados productos ya existen y son válidos, el pipeline puede evitar repetir etapas innecesarias.

La [secuencia por intervalo](../diagramas/exportados/03_secuencia_procesamiento_intervalo.svg) representa la interacción entre orquestador, procesador y generación cartográfica.

---

## 7. Procesamiento físico y remuestreo

La configuración:

```text
Procesador/data/conf/config_resampleo.json
```

define:

```text
bandas requeridas
banda de referencia
método de interpolación
persistencia de bandas intermedias
rangos de normalización RGB
```

La banda:

```text
B13
```

se utiliza como referencia espacial.

Para cada banda, `resample_band` interpola la variable:

```text
Rad
```

a las coordenadas `x` e `y` de B13 mediante `xarray`.

Esto permite obtener matrices espacialmente compatibles antes de realizar las diferencias utilizadas por el RGB.

### Bandas reflectivas

```text
B02
B05
```

se convierten de radiancia a reflectancia mediante:

```text
reflectancia = radiancia × kappa0
```

### Bandas térmicas

```text
B07
B08
B10
B13
```

se convierten a temperatura de brillo utilizando las constantes de Planck almacenadas en los NetCDF y posteriormente se expresan en grados Celsius.

### Composición RGB

La composición implementada es:

```text
Red   = B08 - B10
Green = B07 - B13
Blue  = B05 - B02
```

Los rangos actuales de normalización son:

```text
Red   → -35.0 a 5.0
Green → -5.0 a 60.0
Blue  → -0.75 a 0.25
```

Cada diferencia se transforma linealmente y se recorta al rango:

```text
[0, 1]
```

Los mismos parámetros se utilizan para el procesamiento compatible con GOES-16 y GOES-19.

---

## 8. Generación del NetCDF RGB

`save_rgb_to_netcdf` crea un `xarray.Dataset` con las variables:

```text
Red
Green
Blue
```

sobre las dimensiones:

```text
y
x
```

El archivo conserva las coordenadas y la información geoespacial disponible en la banda de referencia.

Cuando están presentes, también se preservan variables como:

```text
goes_imager_projection
extensión geográfica
subpunto satelital
límites de imagen
```

Los tres canales se vinculan con:

```text
goes_imager_projection
```

mediante el atributo:

```text
grid_mapping
```

La salida se guarda en:

```text
Procesador/data/rgb/<intervalo>/<intervalo>_rgb_result.nc
```

`run_all.py` comprueba la existencia del producto antes de registrar el intervalo como procesado.

---

## 9. Cartografía y GIF

`mapa_rgb.py` localiza el NetCDF RGB, valida las variables requeridas y construye la imagen RGB.

El recorte utiliza las grillas auxiliares disponibles en:

```text
Procesador/data/grids/
```

El mapa utiliza la proyección geostacionaria disponible en los metadatos y agrega:

```text
costas
límites
grilla
título
pie
logo
```

Las salidas PNG se guardan en:

```text
Procesador/data/output/png/
```

El satélite utilizado se obtiene de:

```text
descarga/setup.json
```

Los nombres y títulos del producto se generan automáticamente de acuerdo con esa configuración.

Ejemplos de nombres:

```text
CONAE_PRD_GOES16_ABI_MDTS_RGB_<intervalo>.png
CONAE_PRD_GOES19_ABI_MDTS_RGB_<intervalo>.png
```

Después de generar los mapas, `mapa_rgb.py` ordena los PNG correspondientes y reconstruye la animación.

Las salidas se almacenan en:

```text
Procesador/data/output/gif/
```

con nombres correspondientes al satélite configurado.

La duración de cada cuadro se controla mediante:

```text
gif_frame_duration
```

en:

```text
Procesador/data/conf/config_mapa.json
```

---

## 10. Diagnósticos

### Diagnóstico B13

`diagnostico_b13.py` procesa la banda B13 de cada intervalo.

Convierte la radiancia a temperatura de brillo y genera productos destinados a analizar topes nubosos fríos.

Las salidas incluyen:

```text
<intervalo>_B13_BT.png
<intervalo>_B13_mascaras.png
<intervalo>_B13_estadisticas.json
diagnostico_b13_estadisticas.csv
```

Los umbrales utilizados permiten separar distintos rangos de temperatura de brillo.

Estas categorías deben interpretarse como indicadores de temperatura de los topes nubosos y no como detección directa de granizo u otro fenómeno específico.

### Diagnóstico temporal RGB

`diagnostico_gif_rgb.py` analiza la secuencia temporal de imágenes PNG.

Calcula, entre otras métricas:

```text
medias RGB
brillo
MAE
RMSE
percentil 95
proporción de píxeles con cambios significativos
```

y genera:

```text
diagnostico_temporal_rgb.csv
```

Los diagnósticos constituyen herramientas auxiliares para analizar el comportamiento del producto y no forman parte del procesamiento científico principal.

---

## 11. Operación y control de fallos

El punto de entrada principal es:

```bash
python run_all.py
```

`run_all.py` valida rutas requeridas, carga configuraciones y puede iniciar el descargador como subproceso.

La descarga puede continuar en segundo plano mientras el procesamiento se ejecuta secuencialmente sobre intervalos completos y estables.

También puede procesarse información ya descargada:

```bash
python run_all.py --skip-download
```

El estado puede reiniciarse mediante:

```bash
python run_all.py --reset-state
```

Cada etapa se ejecuta utilizando el mismo intérprete Python.

Un código de salida no exitoso es tratado por el orquestador como fallo del intervalo y puede activar el mecanismo de reintentos configurado.

La gestión de errores se mantiene distribuida entre descargador, procesador y orquestador. Una futura mejora puede unificar la clasificación de fallos recuperables, entradas inválidas y errores permanentes.

---

## 12. Pruebas y evidencia

El repositorio incluye:

```text
test/test_descarga.py
test/test_procesador.py
```

con pruebas destinadas a funciones y configuraciones del descargador y del procesador.

Además de las pruebas automatizadas disponibles, se realizaron ejecuciones reales del pipeline sobre diferentes períodos y configuraciones.

### Casos de estudio

Se utilizaron, entre otros, los siguientes eventos:

```text
Córdoba — 08/02/2018
GOES-16
Mode 3
cadencia de 15 minutos
```

y:

```text
San Rafael / Mendoza — 11/01/2024
GOES-16
Mode 6
cadencia de 10 minutos
```

Estos casos permitieron verificar:

```text
descarga
detección de bandas
compatibilidad M3/M6
resampleo
conversiones físicas
generación RGB
NetCDF
mapas PNG
GIF
diagnóstico B13
evolución temporal
```

También se realizaron pruebas funcionales con:

```text
GOES-19
Mode 6
```

para comprobar la compatibilidad del pipeline con el segundo satélite soportado.

Estas ejecuciones constituyen evidencia de funcionamiento y casos de estudio del producto.

No deben interpretarse como una validación científica estadística completa.

---

## 13. Riesgos y mantenimiento

Los principales puntos de mejora técnica identificados incluyen:

```text
persistencia concurrente de download_db.json
reintentos de descarga
unificación de validadores
mayor cobertura de integración
medición de memoria y tiempos
observabilidad
validación estructural del NetCDF final
```

La escalabilidad horizontal no constituye actualmente la prioridad principal.

Antes de distribuir el procesamiento conviene mantener contratos de entrada y salida claros, asegurar estados reproducibles y medir el comportamiento del pipeline bajo las cargas reales previstas.

También existe riesgo de deriva documental.

Cambios en:

```text
nombres
rutas
configuraciones
satélites
bandas
rangos RGB
formatos de salida
```

deben reflejarse en README, documentación técnica y diagramas.

---

## 14. Referencias disponibles y pendientes

Las referencias internas principales son:

```text
README.md
docs/Readme_descarga.md
docs/Readme_procesador.md
Procesador/data/conf/config_resampleo.json
Procesador/data/conf/config_mapa.json
descarga/setup.json
```

Estas fuentes permiten reconstruir la operación y configuración actual del pipeline.

Para una validación científica formal conviene ampliar la documentación externa relacionada con:

```text
fundamento de la composición RGB
rangos de normalización
umbrales térmicos B13
especificaciones ABI
datos NOAA
métodos de validación meteorológica
```

También deben mantenerse documentadas las fuentes y condiciones de uso de:

```text
grillas
shapefiles
logo
recursos cartográficos
```

---

## 15. Recomendaciones de evolución

El proyecto dispone actualmente de un pipeline funcional desde la adquisición hasta la representación cartográfica.

Las mejoras futuras deberían priorizar:

```text
robustez de descarga
persistencia segura
validaciones centralizadas
pruebas de integración
reproducibilidad de ejecuciones
métricas de rendimiento
ampliación de la validación científica
```

Para una validación científica de mayor alcance sería conveniente incorporar:

```text
más eventos independientes
datos de radar
reportes georreferenciados
observaciones de superficie
métricas objetivas
análisis de falsos positivos y falsos negativos
```

Estas mejoras pueden realizarse preservando la lógica científica y las salidas actualmente implementadas.

---

## 16. Conclusión

P3 MDTS contiene una cadena funcional que integra:

```text
adquisición
→ validación
→ remuestreo
→ conversión física
→ composición RGB
→ NetCDF
→ cartografía
→ animación
→ diagnóstico
```

El pipeline admite actualmente datos ABI de:

```text
GOES-16
GOES-19
```

y reconoce archivos correspondientes a:

```text
Mode 3
Mode 6
```

La ejecución sobre casos reales permitió comprobar el funcionamiento del flujo completo y analizar la coherencia temporal y térmica de los productos obtenidos.

Los casos estudiados aportan evidencia funcional y meteorológica útil, pero no sustituyen una validación científica formal basada en una muestra amplia y fuentes de verdad independientes.

El estado actual proporciona una base técnica reproducible sobre la cual pueden incorporarse mejoras de robustez, automatización, observabilidad y validación sin modificar innecesariamente la lógica científica ya implementada.
