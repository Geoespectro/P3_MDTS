# Guion oral de 10 minutos

Versión para **9 a 9:30 minutos** a 110–120 palabras por minuto, con margen para pausas y transiciones.

## 1 · Apertura (0:00–0:30)

“Presento P3 MDTS, Mapa RGB de Tormentas Severas, que procesa datos ABI de GOES-16 y GOES-19. Explicaré el problema, la arquitectura, el procesamiento y los resultados funcionales disponibles. Distinguiré esas ejecuciones de una validación científica estadística completa.”

## 2 · Problema y motivación (0:30–1:15)

“La entrada no es una imagen terminada. Para cada instante llegan archivos independientes de distintas bandas. Antes de combinarlos hay que reunir el intervalo correcto, comprobar faltantes, armonizar coordenadas y transformar radiancias a magnitudes físicas comparables. Además, una operación puede recibir datos tarde, interrumpirse o encontrar duplicados. El desafío no es solo calcular tres canales: también es reconocer entradas utilizables, conservar avance y producir salidas trazables.”

## 3 · Objetivos y alcance (1:15–2:00)

“El objetivo del proyecto es automatizar el recorrido desde la adquisición hasta la visualización. La implementación prevé descargar seis bandas, generar un RGB georreferenciado, escribir un NetCDF, crear un mapa PNG y reconstruir una animación GIF. También conserva estado para retomar trabajo y ofrece diagnósticos separados. El alcance actual es un pipeline local o contenerizado, coordinado por archivos y procesos. No es una API web ni un servicio distribuido, y tampoco debe describirse todavía como un sistema operacional validado.”

## 4 · Datos y bandas (2:00–2:45)

“Las bandas configuradas son B02, B05, B07, B08, B10 y B13. Se admiten archivos ABI Mode 3, identificados como M3Cxx, y Mode 6, identificados como M6Cxx; el satélite se selecciona en `descarga/setup.json`. La referencia histórica para GOES-16 Mode 3 es de 15 minutos; GOES-16 Mode 6 y GOES-19 Mode 6 usan 10 minutos. La banda 13 aporta la grilla espacial de referencia. La composición tiene rangos RGB configurados: rojo de −35 a 5, verde de −5 a 60 y azul de −0,75 a 0,25. La justificación científica completa de esos rangos y su validación estadística siguen pendientes.”

## 5 · Arquitectura (2:45–3:40)

“En el diagrama vemos responsabilidades separadas. Descarga consulta S3 y organiza NetCDF por intervalo. `run_all.py` inicia la descarga, inspecciona carpetas, ejecuta procesamiento y mapa, valida salidas y actualiza `pipeline_state.json`. `resampleo_alg_band.py` coordina el trabajo científico; `helpers_resampleo.py` implementa conversiones, remuestreo, álgebra y escritura; y `mapa_rgb.py` produce PNG y GIF. Los diagnósticos se ejecutan aparte. El flujo es comprensible, aunque sus contratos dependen de nombres, carpetas y configuraciones repetidas.”

## 6 · Flujo completo (3:40–4:40)

“Sigamos un intervalo. El descargador filtra el listado remoto por banda y tiempo, baja cada archivo a una carpeta temporal, verifica que no esté vacío y lo mueve a `descarga/data`. Después actualiza su inventario de descargas. El orquestador realiza una comprobación más estricta: exige exactamente un NetCDF por cada banda y compara una firma de nombres, tamaños y fechas de modificación antes y después de una espera. Solo entonces llama al procesador. Cuando este devuelve control, el orquestador valida el NetCDF y registra el intervalo como procesado. Luego ejecuta el mapa, comprueba PNG y GIF y lo registra como mapeado. Es importante: el procesador y el mapa no escriben `pipeline_state.json`; lo hace `run_all.py` después de cada validación.”

## 7 · Metodología RGB (4:40–5:45)

“En la etapa física, B02 y B05 se convierten a reflectancia usando el coeficiente `kappa0`. B07, B08, B10 y B13 se convierten a temperatura de brillo y luego a grados Celsius. Con las seis bandas ya sobre la grilla de B13, el canal rojo se calcula como B08 menos B10; el verde como B07 menos B13; y el azul como B05 menos B02. Los rangos actuales son R de −35 a 5, G de −5 a 60 y B de −0,75 a 0,25; los resultados se normalizan y recortan entre cero y uno. Las ejecuciones comprueban el funcionamiento en los casos realizados, pero no permiten afirmar una precisión meteorológica ni que una determinada apariencia confirme por sí sola una tormenta severa.”

## 8 · Productos previstos y evidencia disponible (5:45–6:35)

“Ya hubo ejecuciones reales del pipeline y existen resultados funcionales: NetCDF RGB, PNG, GIF y diagnósticos. Se realizaron casos de estudio con GOES-16 Mode 3 y Mode 6, además de una prueba funcional con GOES-19 Mode 6. Esto demuestra funcionamiento en esos casos, no una validación científica estadística completa. La evidencia que se presente debe identificar la corrida, su configuración y sus entradas, sin atribuirle resultados que no estén documentados.”

## 9 · Pruebas y diagnósticos (6:35–7:30)

“El inventario registra 27 métodos de prueba declarados: cuatro en el archivo de descarga y veintitrés en el procesador. Cubren estructura y configuración, selección de bandas, rangos, normalización, conversiones físicas y álgebra. No hay constancia explícita aquí de que la suite automatizada se haya ejecutado, por lo que la cifra describe métodos declarados, no aprobación. El diagnóstico B13 consume específicamente el NetCDF de B13. El diagnóstico temporal, pese a su nombre, no lee el GIF: compara los PNG consecutivos. Los diagnósticos funcionales tampoco equivalen a validación científica estadística.”

## 10 · Limitaciones y riesgos (7:30–8:25)

“Los riesgos prioritarios son operativos. Primero, los workers pueden modificar y reescribir `download_db.json` sin sincronización; hoy hay un solo worker configurado, pero el diseño admite más. Segundo, la conexión y los intervalos incompletos pueden reintentarse sin un límite interno. Tercero, descargador y orquestador no usan exactamente la misma regla para considerar completa una carpeta. Además, falta medir la memoria de las seis matrices, el recorte depende de grillas auxiliares y el GIF se reconstruye con todos los PNG coincidentes. Son riesgos corregibles sin cambiar de inmediato la fórmula RGB.”

## 11 · Roadmap (8:25–9:10)

“La mejora debe ser incremental. En el corto plazo propongo un validador único de intervalos, escritura serializada y atómica del estado de descarga, errores clasificados, reintentos finitos con backoff y pruebas de descarga sin red. En el mediano plazo: una integración pequeña con NetCDF sintético, mediciones de memoria y tiempo, un manifiesto de frames para el GIF, logging, métricas y CI. Solo después, si el volumen y los usuarios lo justifican, tendría sentido separar servicios, compartir almacenamiento o incorporar una cola de trabajo. Distribuir antes de estabilizar contratos agregaría complejidad sobre una base todavía no demostrada.”

## 12 · Cierre (9:10–9:30)

“En conclusión, P3 MDTS ya tuvo ejecuciones reales y produjo resultados funcionales para los casos indicados. El próximo paso es documentar esa evidencia de forma reproducible y completar una validación científica estadística con referencias adecuadas. Los resultados funcionales son una base para ese trabajo, no su sustituto.”
