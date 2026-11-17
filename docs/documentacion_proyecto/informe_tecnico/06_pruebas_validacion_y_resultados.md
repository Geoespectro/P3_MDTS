# Pruebas, validación y resultados

## Criterio de lectura

La documentación distingue entre:

- **pruebas automatizadas**: verificaciones implementadas mediante `unittest`;
- **validación funcional**: ejecución real del pipeline y comprobación de sus productos;
- **casos de estudio**: análisis de eventos reales con apoyo de diagnósticos;
- **validación científica formal**: evaluación sistemática mediante una muestra amplia, fuentes independientes y métricas objetivas.

Los casos realizados permiten verificar el funcionamiento del pipeline y analizar la coherencia meteorológica de los productos, pero no constituyen por sí solos una validación científica estadística completa.

---

## A. Pruebas automatizadas existentes

| Grupo | Objetivo / entrada | Comprobación y salida | Alcance |
|---|---|---|---|
| Descarga (`test/test_descarga.py`) | Árbol, `descarga/setup.json`, carpetas, importación | Aserciones `unittest` | Verifica estructura y funciones básicas del módulo de descarga |
| Procesador (`test/test_procesador.py`) | JSON reales y datos sintéticos | Configuración, bandas, normalización, conversiones y álgebra | Verifica funciones principales del procesamiento |
| Detección de bandas | Archivos temporales sintéticos | Completo, faltante, selección, inexistencia y duplicado | Comprueba la lógica de identificación de bandas |
| Normalización/rangos | Arreglos NumPy | Valores, recorte y errores | Comprueba el comportamiento de la normalización |
| Conversiones | Datasets sintéticos xarray | Reflectancia, temperatura y errores | Comprueba las conversiones físicas implementadas |
| Álgebra RGB | Seis arreglos sintéticos | Fórmulas, rangos, faltantes y NaN | Comprueba la composición RGB |

Las pruebas automatizadas cubren principalmente componentes individuales.

No sustituyen las pruebas de integración ni la validación mediante datos reales.

---

## B. Validación funcional del pipeline

El pipeline fue ejecutado sobre datos ABI reales correspondientes a distintos períodos y modos operativos.

Se verificó el flujo:

```text
descarga
→ validación de intervalos
→ detección de bandas
→ resampleo
→ conversión física
→ composición RGB
→ NetCDF georreferenciado
→ mapa PNG
→ GIF
```

También se verificó la compatibilidad con:

```text
GOES-16
GOES-19
```

y con archivos correspondientes a:

```text
Mode 3
Mode 6
```

La identificación de bandas utiliza nomenclatura compatible con:

```text
M3Cxx
M6Cxx
```

---

## C. Casos de estudio

### Córdoba — 08/02/2018

Configuración principal:

```text
Satélite: GOES-16
Modo: Mode 3
Cadencia: 15 minutos
```

Este caso permitió comprobar el procesamiento de datos históricos GOES-16 y la compatibilidad con nomenclatura `M3`.

Se generaron los productos principales del pipeline:

```text
NetCDF RGB
mapas PNG
GIF
diagnóstico B13
```

El análisis temporal de B13 mostró una intensificación progresiva de la convección durante el período estudiado, con descenso de la temperatura mínima de brillo y aumento del área ocupada por topes nubosos fríos.

El caso se utilizó como apoyo para verificar la coherencia entre:

```text
evolución temporal
+
RGB
+
temperatura de brillo B13
+
evento meteorológico documentado
```

---

### San Rafael / Mendoza — 11/01/2024

Configuración principal:

```text
Satélite: GOES-16
Modo: Mode 6
Cadencia: 10 minutos
```

El pipeline fue ejecutado sobre una secuencia temporal correspondiente al evento.

Se generaron:

```text
NetCDF RGB
mapas PNG
GIF
diagnósticos B13
comparaciones RGB/B13
```

El análisis mostró una región persistente de topes nubosos fríos y núcleos con temperaturas inferiores a aproximadamente `-63 °C` durante la evolución del sistema.

La firma amarilla observada en el RGB presentó correspondencia espacial con regiones de topes fríos en B13, incluyendo núcleos térmicamente más intensos.

Este comportamiento refuerza la interpretación del producto como herramienta para identificar y seguir convección profunda e intensa.

---

### GOES-19

También se realizaron pruebas funcionales con:

```text
Satélite: GOES-19
Modo: Mode 6
```

Estas pruebas permitieron comprobar:

```text
selección dinámica del satélite
descarga desde el bucket correspondiente
procesamiento de las bandas
generación del RGB
generación de mapas
nombres y títulos correspondientes al satélite configurado
```

El objetivo de esta prueba fue verificar compatibilidad operativa con GOES-19.

No se utilizó como caso principal de validación meteorológica.

---

## D. Diagnósticos

### Diagnóstico B13

Script:

```text
Procesador/diagnostico/diagnostico_b13.py
```

Trabaja directamente sobre la banda B13 y genera:

```text
<intervalo>_B13_BT.png
<intervalo>_B13_mascaras.png
<intervalo>_B13_estadisticas.json
diagnostico_b13_estadisticas.csv
```

El diagnóstico permite estudiar:

```text
temperatura mínima de brillo
distribución espacial de topes fríos
porcentaje de área bajo distintos umbrales térmicos
evolución temporal
```

Los umbrales utilizados deben interpretarse como categorías de temperatura de brillo.

No representan por sí mismos una detección directa de granizo o severidad.

---

### Diagnóstico temporal RGB

Script:

```text
Procesador/diagnostico/diagnostico_gif_rgb.py
```

Analiza la secuencia de imágenes RGB y genera:

```text
diagnostico_temporal_rgb.csv
```

Incluye métricas como:

```text
medias RGB
brillo
MAE
RMSE
percentil 95
porcentaje de píxeles con cambios significativos
```

Estas métricas permiten analizar continuidad y variación temporal del producto.

No constituyen una clasificación automática de severidad meteorológica.

---

## E. Evidencias disponibles

Las ejecuciones realizadas permitieron obtener evidencia de:

```text
descarga de datos ABI
compatibilidad GOES-16 / GOES-19
compatibilidad Mode 3 / Mode 6
detección de las seis bandas requeridas
resampleo
conversiones radiométricas
composición RGB
NetCDF georreferenciado
mapas PNG
GIF
diagnósticos B13
evolución temporal del producto
```

El repositorio conserva principalmente:

```text
código
configuraciones
pruebas
documentación
scripts de diagnóstico
grillas
logo
shapefiles
```

Los datos descargados y productos generados se consideran archivos de trabajo y no forman parte del contenido que debe versionarse de manera permanente.

---

## F. Alcance de la validación actual

La validación realizada permite afirmar que el pipeline:

```text
funciona de extremo a extremo
procesa datos ABI reales
admite GOES-16 y GOES-19
admite Mode 3 y Mode 6
genera los productos previstos
mantiene coherencia temporal entre intervalos
permite analizar conjuntamente RGB y B13
```

Los casos de Córdoba y Mendoza muestran además coherencia entre la evolución del producto y situaciones meteorológicas severas documentadas.

Sin embargo, el número de eventos analizados no permite calcular métricas estadísticas generales de desempeño.

Por lo tanto, no corresponde expresar los resultados como:

```text
porcentaje de precisión
accuracy
sensibilidad
tasa de detección
tasa de falsos positivos
```

mientras no exista una validación formal con una muestra representativa y una fuente de verdad independiente.

---

## G. Validación científica a futuro

Para ampliar la validación científica del producto sería conveniente incorporar:

1. una mayor cantidad de eventos severos y no severos;
2. datos de radar meteorológico;
3. reportes georreferenciados de superficie;
4. información temporal precisa de granizo y otros fenómenos;
5. criterios objetivos de coincidencia espacial y temporal;
6. métricas de falsos positivos y falsos negativos;
7. análisis sistemático de sensibilidad de los rangos RGB y umbrales B13.

Esto permitiría pasar de una validación funcional y mediante casos de estudio a una evaluación científica cuantitativa del producto.

---

## Conclusión

Las pruebas y ejecuciones realizadas muestran que **P3 MDTS funciona como pipeline completo de adquisición, procesamiento y representación de datos ABI**.

Se comprobó su funcionamiento con:

```text
GOES-16 Mode 3
GOES-16 Mode 6
GOES-19 Mode 6
```

y se utilizaron casos reales para analizar la coherencia del RGB con la evolución térmica observada mediante B13.

El estado actual proporciona evidencia suficiente para considerar verificado funcionalmente el pipeline y su compatibilidad operativa.

La validación científica formal queda como una etapa posterior que requiere una muestra mayor, fuentes independientes de referencia y métricas objetivas.
