# Preguntas y respuestas

## Docentes y especialistas

**¿Por qué se usa B13 como referencia?**  
Porque `Procesador/data/conf/config_resampleo.json` la define como `reference_band` y el procesador toma de ella `x/y`. El repositorio no incluye una comparación científica con otras referencias.

**¿Por qué se remuestrea?**  
Las restas requieren arreglos sobre coordenadas compatibles. El código interpola `Rad` de cada banda a la grilla de B13.

**¿Qué representan los canales?**  
Representan diferencias normalizadas: R=B08−B10, G=B07−B13 y B=B05−B02. La interpretación meteorológica específica está pendiente de respaldo bibliográfico.

**¿Cuál es la precisión?**  
No hay métricas de precisión disponibles. Existen pruebas unitarias del cálculo, pero no una validación contra verdad terreno o producto de referencia.

**¿Está validado el caso del 19-03-2024?**  
No. La fecha está configurada, pero no se encontraron productos o informe de validación.

## Infraestructura

**¿Cuál es la fuente de datos?**  
El código usa acceso S3 anónimo para `ABI-L1b-RadF`; la documentación lo atribuye al repositorio NOAA.

**¿Qué ocurre ante una interrupción?**  
El orquestador persiste progreso atómicamente y reutiliza salidas existentes. La base de descarga también permite reanudar, aunque su escritura concurrente necesita robustecerse.

**¿Cómo escala?**  
La descarga admite workers; el procesamiento de intervalos es secuencial. No hay coordinación distribuida ni almacenamiento compartido implementados.

**¿Qué consumo de memoria tiene?**  
No fue medido. El procesador conserva seis bandas convertidas en `bands_data`, por lo que el riesgo debe cuantificarse antes de elegir optimizaciones.

## Desarrollo y mantenimiento

**¿Qué pruebas hay?**  
27 métodos declarados: cuatro de descarga/estructura y veintitrés del procesador. No cubren integración ni fueron ejecutados en esta documentación.

**¿Cómo maneja faltantes y duplicados?**  
El orquestador exige una única coincidencia por banda. El procesador detecta faltantes al validar y duplicados al seleccionar; esa separación motiva centralizar el contrato.

**¿Por qué no usar Dask o microservicios ahora?**  
Porque aún faltan mediciones y contratos probados. Introducir distribución antes de estabilizar estado y validación aumentaría complejidad sin evidencia de necesidad.

**¿Cuál es el próximo paso?**  
Persistencia de descarga segura, reintentos finitos, clasificación de fallos, validador único y pruebas sin red; luego una corrida reproducible con evidencia.

## Usuarios institucionales

**¿Puede operar continuamente?**  
La configuración acepta fin nulo y el descargador puede continuar, pero sus reintentos indefinidos y observabilidad actual impiden calificarlo como servicio institucional robusto.

**¿El RGB confirma una tormenta severa?**  
No debe afirmarse. El repositorio implementa una composición orientada a ese producto; falta validación científica y operacional.

**¿Qué limitaciones deben comunicarse?**  
Ausencia de resultados reproducibles adjuntos, referencias científicas pendientes, cobertura parcial de pruebas y riesgos operativos de descarga, memoria y GIF.
