# Limitaciones actuales

**Hecho** describe comportamiento visible en el código o en la operación actual. **Inferencia** anticipa un riesgo técnico; su impacto debe medirse antes de cuantificarse.

## Críticas

### Escritura concurrente de `download_db.json`

- **Hecho:** `download_file` modifica una estructura global de estado y llama a `writeJson` desde tareas gestionadas por `ThreadPoolExecutor`.
- **Hecho:** `writeJson` sobrescribe directamente el archivo JSON de destino.
- **Inferencia:** con `max_workers > 1` pueden producirse carreras de escritura, pérdida de actualizaciones o un archivo JSON parcial.
- La configuración habitual utiliza actualmente un único worker, lo que reduce la probabilidad de este problema, pero no elimina la limitación de diseño.

### Esperas y reintentos sin límite en descarga

- **Hecho:** la conexión y distintas etapas del flujo de descarga utilizan bucles de reintento que continúan mientras persista la condición de error.
- **Hecho:** los intervalos incompletos pueden volver a consultarse repetidamente.
- **Hecho:** `run_all.py --max-retries` limita reintentos de procesamiento, no todos los reintentos internos del descargador.
- **Inferencia:** una dependencia degradada, un archivo inexistente o un intervalo permanentemente incompleto pueden impedir una finalización clara del proceso de descarga.

## Altas

### Clasificación insuficiente de fallos

- **Hecho:** distintas excepciones de descarga se registran y permiten continuar la ejecución.
- **Hecho:** el procesador y el orquestador manejan causas de error diferentes mediante mecanismos distintos.
- **Inferencia:** no existe una clasificación única y explícita que diferencie de manera uniforme entre:
  - fallo recuperable;
  - entrada inválida;
  - dependencia temporal;
  - defecto permanente.

Una taxonomía común simplificaría la recuperación, los reintentos y el diagnóstico operacional.

### Contrato distribuido de bandas

- **Hecho:** descargador, helpers y orquestador realizan validaciones propias sobre las bandas requeridas.
- **Hecho:** el sistema debe reconocer exactamente las bandas:

```text
B02
B05
B07
B08
B10
B13
```

- **Hecho:** actualmente se admite nomenclatura compatible con:

```text
M3Cxx
M6Cxx
```

- **Inferencia:** mantener reglas similares en distintos módulos aumenta el riesgo de divergencia futura en mensajes, validaciones o decisiones operativas.

Centralizar este contrato reduciría mantenimiento y posibles inconsistencias.

### Cobertura de integración y CI

- **Hecho:** el proyecto dispone de pruebas automatizadas para componentes del descargador y del procesador.
- **Hecho:** además se realizaron ejecuciones funcionales sobre datos reales.
- **Hecho:** las pruebas unitarias no cubren de forma integral:
  - `run_all.py`;
  - acceso S3 simulado;
  - persistencia concurrente;
  - flujo completo de resampleo;
  - generación y reapertura del NetCDF final;
  - cartografía;
  - GIF;
  - diagnósticos.
- **Hecho:** no se observa actualmente un flujo de integración continua que ejecute automáticamente toda la suite.
- **Inferencia:** regresiones que involucren la interacción entre varios módulos pueden no detectarse mediante las pruebas unitarias actuales.

## Medias

### Consumo de memoria

- **Hecho:** cada banda remuestreada y convertida permanece disponible durante el procesamiento del intervalo.
- **Hecho:** el cálculo RGB requiere mantener varias matrices de tamaño completo y crear arreglos temporales.
- **Inferencia:** el consumo de memoria puede crecer significativamente con productos de mayor resolución o al ampliar el procesamiento.

Actualmente falta una medición sistemática de memoria y tiempo de ejecución.

### Grillas auxiliares y robustez cartográfica

- **Hecho:** el recorte cartográfico utiliza grillas auxiliares almacenadas en:

```text
Procesador/data/grids/
```

- **Hecho:** el módulo calcula índices de recorte en función de la información de resolución y las grillas disponibles.
- **Inferencia:** metadatos inesperados, resoluciones no contempladas o incompatibilidad entre grillas pueden provocar errores o recortes incorrectos.

La robustez frente a nuevos productos o resoluciones debería comprobarse antes de ampliar el alcance del procesador.

### Reconstrucción completa del GIF

- **Hecho:** la generación del GIF reúne los PNG disponibles correspondientes al producto y reconstruye la animación.
- **Hecho:** los frames se cargan para crear el GIF final.
- **Inferencia:** tiempo de procesamiento y consumo de memoria aumentan con la cantidad de imágenes disponibles.

Una estrategia incremental o basada en manifiestos de corrida podría resultar conveniente si aumenta la cantidad de intervalos procesados.

### Separación entre corridas

- **Hecho:** los productos se almacenan en directorios comunes de salida.
- **Inferencia:** si se conservan resultados de distintas ejecuciones compatibles dentro del mismo directorio, determinadas herramientas pueden incorporar productos de más de una corrida.

El uso de limpieza previa, directorios por corrida o manifiestos explícitos permitiría aislar mejor las ejecuciones.

### Observabilidad

- **Hecho:** el proyecto dispone de logs, mensajes de consola y archivos JSON de estado.
- **Hecho:** se conserva información suficiente para seguir el estado básico de descarga y procesamiento.
- **Inferencia:** para una operación de mayor escala podrían resultar insuficientes la correlación entre etapas, las métricas de rendimiento y la identificación de una corrida completa.

Una observabilidad más estructurada podría incluir:

```text
identificador de corrida
tiempos por etapa
uso de memoria
cantidad de intervalos
errores clasificados
resumen final de ejecución
```

## Bajas

### Mantenibilidad y deriva documental

- **Hecho:** configuraciones, rutas, nombres de archivos y criterios operativos aparecen en distintos documentos y módulos.
- **Hecho:** el proyecto dispone de README específicos y documentación técnica separada.
- **Inferencia:** un cambio parcial puede dejar documentación, ejemplos o diagramas desalineados respecto del código.

La actualización actual de la documentación reduce este riesgo, pero será necesario mantener sincronizados:

```text
README.md
docs/Readme_descarga.md
docs/Readme_procesador.md
docs/documentacion_proyecto/
diagramas
configuraciones
```

### Nombre histórico del descargador

- **Hecho:** el archivo principal de descarga conserva el nombre:

```text
goes16Download.py
```

aunque actualmente soporta:

```text
GOES-16
GOES-19
```

- **Inferencia:** el nombre puede inducir a pensar que el módulo solo admite GOES-16.

No afecta el funcionamiento y no requiere corrección inmediata, pero podría evaluarse un nombre más genérico en una futura refactorización.

### Escalabilidad arquitectónica

- **Hecho:** el procesamiento es principalmente secuencial y la coordinación utiliza filesystem y archivos JSON locales.
- **Inferencia:** el diseño actual no está orientado a escalabilidad horizontal distribuida.

Esto no constituye un defecto mientras el volumen operativo pueda resolverse adecuadamente en una estación de trabajo o entorno controlado.

Antes de introducir servicios distribuidos conviene medir:

```text
volumen de datos
tiempo por intervalo
uso de memoria
cantidad de intervalos por corrida
necesidad real de concurrencia
```

## Consideración general

Las limitaciones identificadas no invalidan el funcionamiento actual de P3 MDTS.

El pipeline ya permite:

```text
descargar datos ABI
procesar GOES-16 y GOES-19
trabajar con Mode 3 y Mode 6
generar NetCDF RGB
producir mapas PNG
crear GIF
ejecutar diagnósticos
```

Las mejoras propuestas están orientadas principalmente a aumentar:

```text
robustez
mantenibilidad
reproducibilidad
observabilidad
cobertura de integración
escalabilidad futura
```

sin modificar innecesariamente la lógica científica actualmente implementada.
