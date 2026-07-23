# Guion oral de 10 minutos

Versión para **9 a 9:30 minutos** a 110–120 palabras por minuto, con margen para pausas y transiciones.

## 1 · Apertura (0:00–0:30)

“Presento SSE-Goes16, que implementa el producto P3 MDTS a partir de datos ABI de GOES-16. Explicaré el problema, la arquitectura, el procesamiento y el estado de la evidencia. Distinguiré entre lo implementado, lo inspeccionado y aquello que todavía debe ejecutarse o validarse.”

## 2 · Problema y motivación (0:30–1:15)

“La entrada no es una imagen terminada. Para cada instante llegan archivos independientes de distintas bandas. Antes de combinarlos hay que reunir el intervalo correcto, comprobar faltantes, armonizar coordenadas y transformar radiancias a magnitudes físicas comparables. Además, una operación puede recibir datos tarde, interrumpirse o encontrar duplicados. El desafío no es solo calcular tres canales: también es reconocer entradas utilizables, conservar avance y producir salidas trazables.”

## 3 · Objetivos y alcance (1:15–2:00)

“El objetivo del proyecto es automatizar el recorrido desde la adquisición hasta la visualización. La implementación prevé descargar seis bandas, generar un RGB georreferenciado, escribir un NetCDF, crear un mapa PNG y reconstruir una animación GIF. También conserva estado para retomar trabajo y ofrece diagnósticos separados. El alcance actual es un pipeline local o contenerizado, coordinado por archivos y procesos. No es una API web ni un servicio distribuido, y tampoco debe describirse todavía como un sistema operacional validado.”

## 4 · Datos y bandas (2:00–2:45)

“Las bandas configuradas son B02, B05, B07, B08, B10 y B13. La banda 13 cumple una función especial: aporta la grilla espacial de referencia. El procesador interpola las demás bandas hacia sus coordenadas para que las restas se realicen sobre arreglos compatibles. Tanto la lista como la referencia B13 están explícitas en configuración y código. En cambio, la justificación científica completa de la composición, los rangos y los umbrales todavía necesita bibliografía y una validación documentada.”

## 5 · Arquitectura (2:45–3:40)

“En el diagrama vemos responsabilidades separadas. Descarga consulta S3 y organiza NetCDF por intervalo. `run_all.py` inicia la descarga, inspecciona carpetas, ejecuta procesamiento y mapa, valida salidas y actualiza `pipeline_state.json`. `resampleo_alg_band.py` coordina el trabajo científico; `helpers_resampleo.py` implementa conversiones, remuestreo, álgebra y escritura; y `mapa_rgb.py` produce PNG y GIF. Los diagnósticos se ejecutan aparte. El flujo es comprensible, aunque sus contratos dependen de nombres, carpetas y configuraciones repetidas.”

## 6 · Flujo completo (3:40–4:40)

“Sigamos un intervalo. El descargador filtra el listado remoto por banda y tiempo, baja cada archivo a una carpeta temporal, verifica que no esté vacío y lo mueve a `descarga/data`. Después actualiza su inventario de descargas. El orquestador realiza una comprobación más estricta: exige exactamente un NetCDF por cada banda y compara una firma de nombres, tamaños y fechas de modificación antes y después de una espera. Solo entonces llama al procesador. Cuando este devuelve control, el orquestador valida el NetCDF y registra el intervalo como procesado. Luego ejecuta el mapa, comprueba PNG y GIF y lo registra como mapeado. Es importante: el procesador y el mapa no escriben `pipeline_state.json`; lo hace `run_all.py` después de cada validación.”

## 7 · Metodología RGB (4:40–5:45)

“En la etapa física, B02 y B05 se convierten a reflectancia usando el coeficiente `kappa0`. B07, B08, B10 y B13 se convierten a temperatura de brillo y luego a grados Celsius. Con las seis bandas ya sobre la grilla de B13, el canal rojo se calcula como B08 menos B10; el verde como B07 menos B13; y el azul como B05 menos B02. Cada resultado se normaliza con un rango fijo configurado y se recorta entre cero y uno. Podemos demostrar que esa fórmula y esas validaciones existen. No podemos afirmar todavía qué precisión meteorológica alcanza ni que una determinada apariencia confirme por sí sola una tormenta severa.”

## 8 · Productos previstos y evidencia disponible (5:45–6:35)

“La implementación prevé un NetCDF RGB con variables Red, Green y Blue, coordenadas y metadatos geoespaciales; un PNG regional con elementos cartográficos; y un GIF generado a partir de los PNG disponibles. También prevé mapas térmicos y estadísticas de B13, además de un CSV de cambios temporales RGB. Sin embargo, en el material compartido no se encontraron productos finales reproducibles ni logs de una corrida. Por eso esta diapositiva habla de productos previstos y evidencia disponible, no de resultados ya demostrados. Antes de una exposición final conviene incorporar una corrida identificada por commit, configuración y entradas.”

## 9 · Pruebas y diagnósticos (6:35–7:30)

“El recuento directo da 27 métodos de prueba declarados: cuatro en el archivo de descarga y veintitrés en el procesador. Cubren estructura y configuración, selección de bandas, rangos, normalización, conversiones físicas y álgebra. En esta revisión no se ejecutaron, así que la cifra describe existencia, no aprobación. Tampoco cubren todavía el orquestador, una descarga S3 simulada, cartografía, GIF o diagnósticos. El diagnóstico B13 consume específicamente el NetCDF de B13. El diagnóstico temporal, pese a su nombre, no lee el GIF: compara los PNG consecutivos. Y diagnóstico no equivale a validación científica; solamente calcula métricas definidas por el código.”

## 10 · Limitaciones y riesgos (7:30–8:25)

“Los riesgos prioritarios son operativos. Primero, los workers pueden modificar y reescribir `download_db.json` sin sincronización; hoy hay un solo worker configurado, pero el diseño admite más. Segundo, la conexión y los intervalos incompletos pueden reintentarse sin un límite interno. Tercero, descargador y orquestador no usan exactamente la misma regla para considerar completa una carpeta. Además, falta medir la memoria de las seis matrices, el recorte depende de grillas auxiliares y el GIF se reconstruye con todos los PNG coincidentes. Son riesgos corregibles sin cambiar de inmediato la fórmula RGB.”

## 11 · Roadmap (8:25–9:10)

“La mejora debe ser incremental. En el corto plazo propongo un validador único de intervalos, escritura serializada y atómica del estado de descarga, errores clasificados, reintentos finitos con backoff y pruebas de descarga sin red. En el mediano plazo: una integración pequeña con NetCDF sintético, mediciones de memoria y tiempo, un manifiesto de frames para el GIF, logging, métricas y CI. Solo después, si el volumen y los usuarios lo justifican, tendría sentido separar servicios, compartir almacenamiento o incorporar una cola de trabajo. Distribuir antes de estabilizar contratos agregaría complejidad sobre una base todavía no demostrada.”

## 12 · Cierre (9:10–9:30)

“En conclusión, SSE-Goes16 contiene una cadena completa en código y una arquitectura que puede explicarse y mantenerse. El próximo salto de calidad no es sumar funciones: es convertir esa implementación en evidencia reproducible. El trabajo concreto recomendado es robustecer descarga e intervalos y luego documentar una corrida controlada de extremo a extremo. Con esa base podremos hablar de resultados verificados y avanzar hacia una validación científica responsable.”
