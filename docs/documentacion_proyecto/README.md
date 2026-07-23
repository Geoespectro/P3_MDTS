# Documentación integral de SSE-Goes16 / P3 MDTS

Paquete documental generado el **22 de julio de 2026** a partir de la inspección estática del repositorio actual. Describe qué hace el pipeline, cómo se opera y qué evidencia falta reunir. No acredita una ejecución exitosa ni una validación científica.

## Ruta rápida

1. Lea el [resumen ejecutivo](informe_tecnico/01_resumen_ejecutivo.md).
2. Recorra la [arquitectura y el flujo](informe_tecnico/03_arquitectura_y_flujo.md).
3. Consulte el [informe completo](informe_tecnico/02_informe_tecnico_completo.md).
4. Para exponer, use la [estructura de presentación](presentacion/01_estructura_presentacion.md) y el [guion oral](presentacion/03_guion_oral_10_minutos.md).
5. Antes de presentar resultados, cierre las [evidencias pendientes](evidencias/03_evidencias_pendientes.md).

## Qué es el proyecto

SSE-Goes16 implementa en Python un pipeline que obtiene seis bandas ABI de GOES-16, las lleva a la grilla de B13, aplica conversiones físicas y genera el producto RGB P3 MDTS, un NetCDF georreferenciado, mapas PNG y una animación GIF. La finalidad declarada es representar tormentas severas; la interpretación y validación científica todavía requieren referencias y evidencia experimental.

## Índice completo

### Informe técnico — base para informe Word

- [01 · Resumen ejecutivo](informe_tecnico/01_resumen_ejecutivo.md)
- [02 · Informe técnico completo](informe_tecnico/02_informe_tecnico_completo.md)
- [03 · Arquitectura y flujo](informe_tecnico/03_arquitectura_y_flujo.md)
- [04 · Metodología RGB](informe_tecnico/04_metodologia_rgb.md)
- [05 · Operación y ejecución](informe_tecnico/05_operacion_y_ejecucion.md)
- [06 · Pruebas, validación y resultados](informe_tecnico/06_pruebas_validacion_y_resultados.md)
- [07 · Glosario](informe_tecnico/07_glosario.md)

### Diagramas

Consulte primero la [guía de formatos y actualización](diagramas/README.md). Para lectura se enlazan los SVG; el editable visual está disponible como recurso secundario.

- [01 · Flujo general (SVG)](diagramas/exportados/01_flujo_general.svg) · [editable](diagramas/editables/01_flujo_general.drawio)
- [02 · Arquitectura de módulos (SVG)](diagramas/exportados/02_arquitectura_modulos.svg) · [editable](diagramas/editables/02_arquitectura_modulos.drawio)
- [03 · Secuencia de un intervalo (SVG)](diagramas/exportados/03_secuencia_procesamiento_intervalo.svg) · [editable](diagramas/editables/03_secuencia_procesamiento_intervalo.drawio)
- [04 · Descarga, validación y estado (SVG)](diagramas/exportados/04_descarga_validacion_y_estado.svg) · [editable](diagramas/editables/04_descarga_validacion_y_estado.drawio)
- [05 · Entradas y salidas (SVG)](diagramas/exportados/05_entradas_y_salidas.svg) · [editable](diagramas/editables/05_entradas_y_salidas.drawio)
- [06 · Roadmap (SVG)](diagramas/exportados/06_roadmap_mejoras.svg) · [editable](diagramas/editables/06_roadmap_mejoras.drawio)

> Los seis diagramas fueron sincronizados en sus formatos Mermaid, Drawio y SVG. Mermaid se conserva como fuente técnica canónica, Drawio como editable visual y SVG como formato de publicación.

### Presentación — base para PowerPoint y exposición

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

## Estado de la evidencia

El repositorio contiene código, configuración, documentación, pruebas unitarias, grillas, logo y shapefiles. En la inspección no se encontraron NetCDF, PNG, GIF, CSV, JSON de diagnósticos ni logs de ejecución versionados o visibles fuera de rutas ignoradas. En consecuencia, se documentan **capacidades implementadas y comprobables por lectura**, no resultados de una corrida.

> Esta documentación refleja el contenido observado en la rama `documentacion-exposicion` el 22-07-2026. Si cambia el código o la configuración, debe revisarse la trazabilidad.
