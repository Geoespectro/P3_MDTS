# Limitaciones actuales

**Hecho** describe comportamiento visible. **Inferencia** anticipa un riesgo técnico; debe probarse antes de cuantificar impacto.

## Críticas

### Escritura concurrente de `download_db.json`

- **Hecho:** `download_file` modifica el diccionario global y llama `writeJson` desde tareas de `ThreadPoolExecutor`; `writeJson` sobrescribe directamente el archivo. (`descarga/goes16Download.py:51-95,265-281`; `descarga/helpers.py:6-9`)
- **Inferencia:** con `max_workers > 1` puede haber carreras, pérdida de actualizaciones o JSON parcial. Hoy la configuración usa 1, lo que reduce, pero no elimina el defecto de diseño.

### Esperas/reintentos sin límite en descarga

- **Hecho:** conexión y bucle temporal usan `while True`; ante errores S3 se duerme `timeout` y continúa. Intervalos incompletos también vuelven a consultarse. (`goes16Download.py:151-164,199-297`)
- **Inferencia:** una dependencia degradada o un intervalo permanentemente incompleto puede impedir una finalización clara. El límite de `run_all.py --max-retries` aplica al procesamiento, no a esos bucles internos.

## Altas

### Clasificación insuficiente de fallos

- **Hecho:** varias excepciones de descarga se registran y continúan; el procesador devuelve `False` para causas heterogéneas.
- **Inferencia:** no se distingue de forma estable entre fallo recuperable, entrada inválida y defecto permanente.

### Contrato duplicado de bandas

- **Hecho:** descargador, helpers y orquestador implementan validaciones propias. El orquestador exige una coincidencia; `Procesador/src/helpers_resampleo.py::is_folder_complete` comprueba presencia y `find_band_file` detecta duplicado después. (`run_all.py:344-386`; `Procesador/src/helpers_resampleo.py:27-70`)
- **Inferencia:** mensajes/decisiones pueden divergir y aumentar mantenimiento.

### Cobertura y CI

- **Hecho:** hay 27 métodos de prueba declarados —4 en `test/test_descarga.py` y 23 en `test/test_procesador.py`—; no cubren orquestador, S3, mapa, GIF o diagnósticos. No se observó workflow de CI. El recuento fue realizado por inspección; las pruebas no se ejecutaron en esta revisión.
- **Inferencia:** regresiones integrales pueden llegar sin detección automática.

## Medias

### Consumo de memoria

- **Hecho:** cada banda remuestreada se convierte a un arreglo NumPy y queda en `bands_data` hasta terminar el intervalo. (`Procesador/src/resampleo_alg_band.py:77-158`)
- **Inferencia:** seis grillas completas más temporales pueden limitar archivos grandes. Falta medición.

### Grillas auxiliares y robustez cartográfica

- **Hecho:** el recorte carga matrices de 8 km, interpreta `spatial_resolution` como texto y calcula un factor entero. (`Procesador/src/mapa_rgb.py:70-195`)
- **Inferencia:** resoluciones no divisibles, metadatos inesperados o grillas incompatibles pueden producir error o recorte incorrecto.

### Reconstrucción completa del GIF

- **Hecho:** `Procesador/src/mapa_rgb.py::main` obtiene todos los PNG y `build_gif` los carga en memoria antes de guardar. (`Procesador/src/mapa_rgb.py:449-457,576-686`)
- **Inferencia:** costo y memoria crecen con la historia; PNG de corridas distintas pueden mezclarse.

### Observabilidad

- **Hecho:** hay logging/prints y JSON de estado, pero no métricas, correlación de corrida ni formato centralizado.
- **Inferencia:** diagnóstico operacional y capacidad serán difíciles a escala.

## Bajas

### Mantenibilidad y deriva documental

- **Hecho:** rutas/contratos se repiten y `docs/Readme_descarga.md` ejemplifica fin 21:20 mientras `setup.json` actual termina 21:00. `clean.py` tiene `DRY_RUN=False`, aunque la guía pide revisarlo.
- **Inferencia:** cambios parciales pueden confundir operación.

### Escalabilidad arquitectónica

- **Hecho:** procesamiento secuencial y coordinación por filesystem/JSON local.
- **Inferencia:** no escala horizontalmente sin control de concurrencia, almacenamiento compartido e idempotencia. Esto no es defecto si el volumen actual no lo exige.
