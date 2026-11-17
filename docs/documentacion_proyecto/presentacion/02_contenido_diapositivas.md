# Contenido propuesto de diapositivas

## 1. P3 MDTS
**Mapa RGB de Tormentas Severas** · Pipeline GOES-16 y GOES-19 · Estado técnico actual.<br>
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
GOES-16 y GOES-19 · ABI Mode 3 (`M3Cxx`) y Mode 6 (`M6Cxx`).<br>
Selección del satélite: `descarga/setup.json`. B13 = grilla de referencia.<br>
Cadencia de referencia: GOES-16 histórico Mode 3, 15 min; Mode 6 de GOES-16 y GOES-19, 10 min.<br>
Información pendiente: referencias científicas y validación estadística.

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
- Rangos RGB: R `[-35.0, 5.0]`; G `[-5.0, 60.0]`; B `[-0.75, 0.25]`
- Normalización y recorte a `[0,1]`

Pie: `Procesador/src/helpers_resampleo.py`.  
Pendiente: fundamento y validación científica de rangos.

## 8. Resultados funcionales y evidencia disponible
- Ya hubo ejecuciones reales: existen NetCDF RGB, PNG, GIF y diagnósticos.
- Casos de estudio: GOES-16 Mode 3 y Mode 6.
- Prueba funcional: GOES-19 Mode 6.

Estos resultados no constituyen validación científica estadística completa.

## 9. Calidad actual
- 27 métodos de prueba declarados: 4 de descarga y 23 del procesador.
- Pruebas de configuración, conversiones y álgebra.
- Existen resultados funcionales y diagnósticos separados del pipeline.
- No se afirma que la suite automatizada haya sido ejecutada.
- Validación científica estadística: pendiente.

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
**La cadena ya tuvo ejecuciones reales y produjo resultados funcionales.**<br>
El próximo paso es documentar la evidencia y completar la validación científica estadística.
