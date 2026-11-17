# Resumen ejecutivo

## Problema y objetivo

El proyecto aborda la obtención y transformación de observaciones multibanda del sensor ABI de los satélites **GOES-16 y GOES-19** en un producto RGB integrado que pueda visualizarse como mapa y animación.

El objetivo general es automatizar una cadena reproducible desde la descarga de datos hasta la generación del producto **P3 MDTS — Mapa RGB de Tormentas Severas**, conservando georreferencia y estado operativo.

El producto está orientado al análisis y seguimiento de **convección profunda e intensa y estructuras asociadas con posibles tormentas severas**.

## Solución desarrollada

La solución consiste en un pipeline Python modular que:

1. consulta los repositorios S3 públicos de NOAA para el producto `ABI-L1b-RadF`;
2. descarga las bandas B02, B05, B07, B08, B10 y B13 por intervalo;
3. valida que el intervalo esté completo y estable;
4. interpola las bandas a la grilla de referencia de B13;
5. convierte B02/B05 a reflectancia y B07/B08/B10/B13 a temperatura de brillo en °C;
6. calcula y normaliza los tres canales RGB;
7. guarda un NetCDF RGB georreferenciado;
8. produce mapas PNG y una animación GIF.

La composición implementada es:

```text
Red   = B08 - B10
Green = B07 - B13
Blue  = B05 - B02
```

El pipeline admite actualmente datos de:

```text
GOES-16
GOES-19
```

y reconoce archivos ABI correspondientes a:

```text
Mode 3
Mode 6
```

La selección del satélite se realiza mediante:

```text
descarga/setup.json
```

## Productos y estado actual

Los principales productos generados son:

```text
NetCDF RGB georreferenciado
mapas PNG
animación GIF
productos de diagnóstico B13
diagnósticos temporales RGB
```

`run_all.py` coordina la descarga y el procesamiento y mantiene el estado operativo mediante:

```text
pipeline_state.json
```

El pipeline fue ejecutado sobre datos reales correspondientes a diferentes períodos y configuraciones.

Se realizaron casos de estudio con:

```text
GOES-16 Mode 3
GOES-16 Mode 6
```

y pruebas funcionales con:

```text
GOES-19 Mode 6
```

Estas ejecuciones permitieron comprobar el funcionamiento integral de:

```text
descarga
→ validación
→ resampleo
→ conversiones físicas
→ composición RGB
→ NetCDF
→ mapa PNG
→ GIF
→ diagnósticos
```

Los casos de estudio también permitieron analizar conjuntamente el RGB, la temperatura de brillo B13 y la evolución temporal de los sistemas observados.

## Alcance de la validación

El estado actual permite considerar verificado el funcionamiento del pipeline y su compatibilidad operativa con GOES-16 y GOES-19.

Los casos estudiados aportan además evidencia de coherencia entre la evolución del producto y situaciones de convección intensa.

Sin embargo, esta evidencia no equivale a una **validación científica estadística completa**.

Una validación formal de mayor alcance requeriría:

```text
más eventos independientes
datos de radar
reportes georreferenciados
observaciones de superficie
métricas objetivas
análisis de falsos positivos y falsos negativos
```

Por este motivo no corresponde expresar actualmente el desempeño mediante porcentajes de precisión, sensibilidad o tasa de detección.

## Limitaciones principales

Entre los principales puntos de mejora técnica se encuentran:

- robustecer la persistencia de `download_db.json`;
- limitar y clasificar mejor los reintentos de descarga;
- centralizar las reglas de validación de intervalos;
- ampliar las pruebas de integración;
- medir tiempos de procesamiento y consumo de memoria;
- mejorar observabilidad y trazabilidad;
- ampliar la validación científica con fuentes independientes.

Estas limitaciones no impiden el funcionamiento actual del pipeline, pero representan oportunidades de mejora para una operación más robusta y reproducible.

## Próximos pasos

Las siguientes mejoras deberían concentrarse en:

1. robustecer descarga y persistencia;
2. ampliar las pruebas de integración;
3. mejorar la reproducibilidad de ejecuciones;
4. medir rendimiento y consumo de recursos;
5. ampliar la validación científica sobre una muestra mayor de eventos.

La evolución futura debe preservar la lógica científica y los productos actualmente implementados.

## Conclusión

P3 MDTS dispone actualmente de una cadena funcional que integra:

```text
adquisición
→ procesamiento
→ generación RGB
→ georreferencia
→ cartografía
→ animación
→ diagnóstico
```

El sistema soporta **GOES-16 y GOES-19**, así como archivos correspondientes a **Mode 3 y Mode 6**.

Las ejecuciones realizadas permiten afirmar que el pipeline funciona de extremo a extremo y genera los productos previstos.



