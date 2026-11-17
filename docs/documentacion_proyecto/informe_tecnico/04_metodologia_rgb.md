# Metodología RGB implementada

## Contrato de bandas

El código requiere B02, B05, B07, B08, B10 y B13.

B13 aporta la grilla de referencia: sus coordenadas `x` e `y` se utilizan para llevar las restantes bandas a una grilla común mediante `xarray.DataArray.interp()`, actualmente con método `linear`.

La metodología se aplica sobre datos ABI compatibles de **GOES-16 y GOES-19**.

El procesador reconoce archivos correspondientes tanto a **Mode 3** como a **Mode 6**, sin modificar la composición científica del producto.

## Conversión física

| Bandas | Conversión implementada | Unidad declarada |
|---|---|---|
| B02, B05 | `radiancia × kappa0` | reflectancia, sin dimensión |
| B07, B08, B10, B13 | fórmula con `fk1`, `fk2`, `bc1`, `bc2`; luego K − 273,15 | °C |

Las constantes se leen de variables escalares del NetCDF y se conservan durante el remuestreo.

El código verifica la presencia de las constantes requeridas y rechaza condiciones inválidas, como radiancias térmicas no positivas.

**Reflectancia** y **temperatura de brillo** no son magnitudes intercambiables: el canal azul resta dos reflectancias, mientras que rojo y verde restan temperaturas.

## Álgebra y normalización

```text
Rojo  = B08 - B10
Verde = B07 - B13
Azul  = B05 - B02
```

Los valores crudos se normalizan linealmente y se recortan a `[0,1]` con rangos fijos:

| Canal | Rango actual |
|---|---:|
| Rojo | −35,0 a 5,0 |
| Verde | −5,0 a 60,0 |
| Azul | −0,75 a 0,25 |

Los rangos se encuentran definidos en:

`Procesador/data/conf/config_resampleo.json`

El uso de límites fijos permite mantener el mismo criterio de representación entre intervalos y facilita la comparación temporal del producto.

Los mismos rangos se utilizan para el procesamiento compatible con GOES-16 y GOES-19.

## Construcción y georreferencia

El resultado se guarda con variables bidimensionales `Red`, `Green` y `Blue`, coordenadas `x/y`, atributos de B13 y las variables geoespaciales disponibles.

Si existe `goes_imager_projection`, se asigna como `grid_mapping` y cada canal declara rango válido `[0,1]`.

La salida se almacena en:

`Procesador/data/rgb/<intervalo>/<intervalo>_rgb_result.nc`

## Interpretación del producto

La composición RGB está orientada a resaltar características asociadas con:

- convección profunda;
- desarrollo convectivo intenso;
- topes nubosos fríos;
- estructuras potencialmente asociadas con tormentas severas.

La interpretación no debe realizarse a partir de un único color de forma aislada.

El producto puede analizarse conjuntamente con:

```text
RGB
+
temperatura de brillo B13
+
evolución temporal
+
información meteorológica complementaria
```

Los casos de estudio realizados permitieron observar coherencia espacial y temporal entre determinadas firmas del RGB y regiones de topes nubosos fríos identificadas mediante B13.

## Diagnóstico térmico B13

Como herramienta auxiliar, el proyecto utiliza la temperatura de brillo de B13 para estudiar la evolución térmica de los topes nubosos.

Los diagnósticos permiten calcular:

- temperatura mínima;
- área bajo distintos umbrales térmicos;
- distribución espacial de topes fríos;
- evolución temporal.

Los umbrales utilizados corresponden a categorías de temperatura de brillo.

Estos valores permiten caracterizar topes nubosos fríos, pero **no deben interpretarse de forma aislada como detección directa de granizo o severidad meteorológica**.

## Validación realizada

La metodología fue aplicada sobre datos ABI reales en distintos períodos y modos operativos.

Entre los casos utilizados se encuentran:

```text
GOES-16 Mode 3
GOES-16 Mode 6
```

También se realizaron pruebas funcionales con:

```text
GOES-19 Mode 6
```

Los casos estudiados permitieron verificar:

- compatibilidad de bandas;
- resampleo;
- conversiones físicas;
- composición RGB;
- georreferencia;
- generación de productos;
- continuidad temporal;
- coherencia entre RGB y B13.

La evidencia obtenida permite respaldar el funcionamiento de la metodología implementada y su uso como herramienta de análisis de convección intensa.

## Límites interpretativos

- El producto RGB no constituye por sí solo un detector automático de tormentas severas.
- Una tonalidad determinada no debe interpretarse de manera aislada como confirmación de granizo.
- Los umbrales B13 representan temperaturas de brillo y no categorías directas de severidad.
- Los casos analizados aportan evidencia funcional y meteorológica, pero no constituyen una validación estadística completa.
- Actualmente no se dispone de métricas generales de precisión, sensibilidad, falsos positivos o falsos negativos.
- Una validación científica formal requeriría una muestra mayor de eventos y fuentes independientes como radar, observaciones de superficie y reportes georreferenciados.

El nombre **Mapa RGB de Tormentas Severas** expresa la finalidad del producto como herramienta de apoyo al análisis y seguimiento de convección intensa, pero no implica una clasificación automática de severidad.
