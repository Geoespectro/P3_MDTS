# Documentación integral de P3 MDTS

Paquete documental del proyecto **P3 MDTS — Mapa RGB de Tormentas Severas**.

Esta documentación describe la arquitectura, operación, metodología, evidencias, resultados de validación funcional y líneas de mejora del pipeline.

## Ruta rápida

1. Lea el [resumen ejecutivo](informe_tecnico/01_resumen_ejecutivo.md).
2. Recorra la [arquitectura y el flujo](informe_tecnico/03_arquitectura_y_flujo.md).
3. Consulte el [informe completo](informe_tecnico/02_informe_tecnico_completo.md).
4. Para exponer, use la [estructura de presentación](presentacion/01_estructura_presentacion.md) y el [guion oral](presentacion/03_guion_oral_10_minutos.md).
5. Consulte la sección de [evidencias](evidencias/01_inventario_evidencias.md) para revisar la trazabilidad del proyecto.

## Qué es el proyecto

P3 MDTS implementa en Python un pipeline que obtiene seis bandas ABI de los satélites **GOES-16 y GOES-19**, las lleva a una grilla común de referencia, aplica conversiones físicas y genera el producto RGB **Mapa de Tormentas Severas**.

El flujo produce:

```text
NetCDF RGB georreferenciado
mapas PNG
animación GIF
productos de diagnóstico
```

El sistema admite datos ABI correspondientes a **Mode 3 y Mode 6**, lo que permite trabajar tanto con períodos históricos como actuales.

El producto está orientado al análisis de **convección profunda e intensa** y al seguimiento de estructuras asociadas con posibles tormentas severas.

La documentación distingue entre la validación funcional del pipeline y una validación científica formal, que puede ampliarse mediante nuevos eventos, observaciones de superficie, radar y métricas objetivas.

## Índice completo

### Informe técnico

- [01 · Resumen ejecutivo](informe_tecnico/01_resumen_ejecutivo.md)
- [02 · Informe técnico completo](informe_tecnico/02_informe_tecnico_completo.md)
- [03 · Arquitectura y flujo](informe_tecnico/03_arquitectura_y_flujo.md)
- [04 · Metodología RGB](informe_tecnico/04_metodologia_rgb.md)
- [05 · Operación y ejecución](informe_tecnico/05_operacion_y_ejecucion.md)
- [06 · Pruebas, validación y resultados](informe_tecnico/06_pruebas_validacion_y_resultados.md)
- [07 · Glosario](informe_tecnico/07_glosario.md)

### Diagramas

Consulte primero la [guía de formatos y actualización](diagramas/README.md).

Para lectura se utilizan los SVG, mientras que los archivos Drawio se conservan como editables visuales.

- [01 · Flujo general (SVG)](diagramas/exportados/01_flujo_general.svg) · [editable](diagramas/editables/01_flujo_general.drawio)
- [02 · Arquitectura de módulos (SVG)](diagramas/exportados/02_arquitectura_modulos.svg) · [editable](diagramas/editables/02_arquitectura_modulos.drawio)
- [03 · Secuencia de un intervalo (SVG)](diagramas/exportados/03_secuencia_procesamiento_intervalo.svg) · [editable](diagramas/editables/03_secuencia_procesamiento_intervalo.drawio)
- [04 · Descarga, validación y estado (SVG)](diagramas/exportados/04_descarga_validacion_y_estado.svg) · [editable](diagramas/editables/04_descarga_validacion_y_estado.drawio)
- [05 · Entradas y salidas (SVG)](diagramas/exportados/05_entradas_y_salidas.svg) · [editable](diagramas/editables/05_entradas_y_salidas.drawio)
- [06 · Roadmap (SVG)](diagramas/exportados/06_roadmap_mejoras.svg) · [editable](diagramas/editables/06_roadmap_mejoras.drawio)

Los seis diagramas se mantienen en sus formatos Mermaid, Drawio y SVG.

Mermaid se conserva como fuente técnica, Drawio como editable visual y SVG como formato de publicación.

### Presentación

- [01 · Estructura de presentación](presentacion/01_estructura_presentacion.md)
- [02 · Contenido de diapositivas](presentacion/02_contenido_diapositivas.md)
- [03 · Guion oral de 10 minutos](presentacion/03_guion_oral_10_minutos.md)
- [04 · Preguntas y respuestas](presentacion/04_preguntas_y_respuestas.md)

### Evidencias

- [01 · Inventario](evidencias/01_inventario_evidencias.md)
- [02 · Matriz de trazabilidad](evidencias/02_matriz_trazabilidad.md)
- [03 · Evidencias pendientes](evidencias/03_evidencias_pendientes.md)

### Limitaciones y mejoras

- [01 · Limitaciones actuales](mejoras/01_limitaciones_actuales.md)
- [02 · Roadmap de mejoras](mejoras/02_roadmap_mejoras.md)
- [03 · Priorización técnica](mejoras/03_priorizacion_tecnica.md)

## Estado actual

El repositorio contiene:

```text
código fuente
configuraciones
pruebas
grillas auxiliares
logo
shapefiles
documentación técnica
herramientas de diagnóstico
```

El pipeline fue ejecutado sobre distintos períodos y configuraciones, incluyendo datos históricos y actuales.

Se verificaron:

```text
descarga de bandas ABI
compatibilidad GOES-16 / GOES-19
compatibilidad Mode 3 / Mode 6
validación de intervalos completos
resampleo
conversión física
generación del RGB
NetCDF georreferenciado
mapas PNG
animación GIF
diagnósticos B13
```

También se realizaron casos de estudio específicos utilizados como apoyo para la validación funcional y meteorológica del producto.

La validación científica formal puede ampliarse incorporando una mayor cantidad de eventos, datos de radar, reportes georreferenciados y métricas cuantitativas de desempeño.

## Mantenimiento de la documentación

Esta documentación debe revisarse cuando cambien:

```text
la lógica de descarga
las bandas utilizadas
la metodología RGB
los parámetros de configuración
los formatos de salida
la arquitectura del pipeline
los criterios de validación
```

Los README operativos principales se encuentran en:

```text
docs/Readme_descarga.md
docs/Readme_procesador.md
```

y deben mantenerse alineados con esta documentación integral.
