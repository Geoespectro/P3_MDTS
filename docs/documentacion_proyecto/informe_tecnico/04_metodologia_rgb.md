# Metodología RGB implementada

## Contrato de bandas

El código requiere B02, B05, B07, B08, B10 y B13. B13 aporta la grilla de referencia: sus coordenadas `x` e `y` se pasan a `xarray.DataArray.interp`, actualmente con método `linear`. (Fuentes: `Procesador/data/conf/config_resampleo.json`; `Procesador/src/resampleo_alg_band.py:21-126`; `Procesador/src/helpers_resampleo.py:228-271`)

## Conversión física

| Bandas | Conversión implementada | Unidad declarada |
|---|---|---|
| B02, B05 | `radiancia × kappa0` | reflectancia, sin dimensión |
| B07, B08, B10, B13 | fórmula con `fk1`, `fk2`, `bc1`, `bc2`; luego K − 273,15 | °C |

Las constantes se leen de variables escalares del NetCDF y se copian al dataset remuestreado. El código rechaza radiancias térmicas no positivas y constantes ausentes. (Fuente: `Procesador/src/helpers_resampleo.py:108-225`)

**Reflectancia** y **temperatura de brillo** no son magnitudes intercambiables: el canal azul resta dos reflectancias, mientras rojo y verde restan temperaturas. La justificación científica de qué fenómenos resaltan específicamente estas diferencias no está demostrada dentro del código: **[FUNDAMENTO CIENTÍFICO PENDIENTE DE REFERENCIA]**.

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
| Verde | −10,0 a 90,0 |
| Azul | −0,75 a 0,50 |

Los rangos fijos favorecen comparabilidad temporal según el comentario del código. Su procedencia y validación científica no están citadas: **[FUNDAMENTO CIENTÍFICO PENDIENTE DE REFERENCIA]**. (Fuentes: `Procesador/data/conf/config_resampleo.json`; `Procesador/src/helpers_resampleo.py:282-427`)

## Construcción y georreferencia

El resultado se guarda con variables bidimensionales `Red`, `Green`, `Blue`, coordenadas `x/y`, atributos de B13 y variables geoespaciales disponibles. Si existe `goes_imager_projection`, se asigna como `grid_mapping` y cada canal declara rango válido `[0,1]`. (Fuente: `Procesador/src/helpers_resampleo.py:429-500`)

## Límites interpretativos

- La inspección confirma el algoritmo, no la exactitud del producto.
- No hay evidencia disponible de comparación con observaciones terrestres, otros productos o expertos.
- No se encontraron métricas de detección, falsos positivos o incertidumbre.
- El diagnóstico B13 aplica umbrales codificados, pero su fundamento requiere referencia: **[FUNDAMENTO CIENTÍFICO PENDIENTE DE REFERENCIA]**.
- El nombre “Mapa RGB de Tormentas Severas” expresa la finalidad del producto; no autoriza por sí solo a declarar presencia o severidad de una tormenta.
