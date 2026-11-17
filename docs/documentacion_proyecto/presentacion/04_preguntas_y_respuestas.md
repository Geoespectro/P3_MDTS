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

**¿Qué satélites y modos admite?**

GOES-16 y GOES-19, con archivos ABI Mode 3 (`M3Cxx`) y Mode 6 (`M6Cxx`). La selección del satélite se realiza en `descarga/setup.json`. La referencia temporal es 15 minutos para GOES-16 histórico Mode 3 y 10 minutos para GOES-16 Mode 6 y GOES-19 Mode 6.

**¿Está validado el caso del 19-03-2024?**  
La fecha figura en la configuración, pero aquí no está confirmado a qué caso de estudio corresponde ni qué resultados se asocian a ella. No debe presentarse como caso validado.

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
Persistencia de descarga segura, reintentos finitos, clasificación de fallos, validador único y pruebas sin red; además, documentar una ejecución existente con su configuración, entradas y salidas.

## Usuarios institucionales

**¿Puede operar continuamente?**  
La configuración acepta fin nulo y el descargador puede continuar, pero sus reintentos indefinidos y observabilidad actual impiden calificarlo como servicio institucional robusto.

**¿El RGB confirma una tormenta severa?**  
No debe afirmarse. El repositorio implementa una composición orientada a ese producto; falta validación científica y operacional.

**¿Qué limitaciones deben comunicarse?**  
Hay resultados funcionales disponibles, pero no equivalen a una validación científica estadística completa. También deben comunicarse las referencias científicas pendientes, la cobertura parcial de pruebas y los riesgos operativos de descarga, memoria y GIF.
