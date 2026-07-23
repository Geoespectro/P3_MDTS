# Contenido propuesto de diapositivas

## 1. SSE-Goes16 / P3 MDTS
**Mapa RGB de Tormentas Severas** · Pipeline GOES-16 · Estado técnico actual.  
Imagen: logo existente. Pie: `Procesador/data/logo/logo.png`.

## 2. Problema
- Seis bandas llegan como archivos independientes.
- Sus datos deben alinearse y convertirse antes de combinarse.
- La operación debe tolerar intervalos incompletos e interrupciones.

## 3. Objetivos
- Descargar y organizar bandas.
- Generar RGB georreferenciado.
- Producir NetCDF, PNG y GIF.
- Conservar estado recuperable.

## 4. Datos y bandas
**B02 · B05 · B07 · B08 · B10 · B13**  
B13 = grilla de referencia.  
Fuente: configuraciones del repositorio.  
Información pendiente: referencia científica del producto.

## 5. Arquitectura
Descarga → Procesamiento → Cartografía → Diagnóstico  
Orquestación y estado conectan las etapas.  
Diagrama: [arquitectura de módulos en SVG](../diagramas/exportados/02_arquitectura_modulos.svg). Editable: [Drawio](../diagramas/editables/02_arquitectura_modulos.drawio).

## 6. Flujo
S3 → bandas → validación → B13 → conversiones → RGB → NetCDF → PNG → GIF.  
Diagrama: [flujo general en SVG](../diagramas/exportados/01_flujo_general.svg). Editable: [Drawio](../diagramas/editables/01_flujo_general.drawio).

## 7. Metodología RGB
- R = B08 − B10
- G = B07 − B13
- B = B05 − B02
- Normalización fija a `[0,1]`

Pie: `Procesador/src/helpers_resampleo.py`.  
Pendiente: fundamento y validación científica de rangos.

## 8. Productos previstos y evidencia disponible
- NetCDF RGB georreferenciado.
- Mapa PNG regional.
- Animación GIF.
- Diagnósticos B13 y temporales.

Evidencia visual: **pendiente de una corrida reproducible**.

## 9. Calidad actual
- 27 métodos de prueba declarados: 4 de descarga y 23 del procesador.
- Pruebas de configuración, conversiones y álgebra.
- Diagnósticos separados del pipeline.
- Integración y resultados: pendientes.

## 10. Limitaciones
- Estado de descarga no sincronizado.
- Esperas del descargador sin límite.
- Contrato de bandas duplicado.
- Memoria, cartografía y GIF requieren robustez.

## 11. Roadmap
**Ahora:** descarga robusta + pruebas sin red.  
**Después:** integración, memoria, CI y métricas.  
**A futuro:** despliegue coordinado y monitoreo.  
Diagrama: [roadmap en SVG](../diagramas/exportados/06_roadmap_mejoras.svg). Editable: [Drawio](../diagramas/editables/06_roadmap_mejoras.drawio).

## 12. Conclusión
**La cadena está implementada en código.**  
El próximo salto de calidad es hacerla verificable, robusta y científicamente respaldada.
