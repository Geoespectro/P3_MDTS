# Roadmap de mejoras

Todo lo listado corresponde a **mejoras propuestas** sobre el estado actual de P3 MDTS.

El pipeline ya dispone de funcionamiento extremo a extremo, soporte para GOES-16 y GOES-19, compatibilidad con Mode 3 y Mode 6, generación de NetCDF RGB, mapas PNG, GIF y herramientas de diagnóstico.

Las mejoras siguientes están orientadas a robustez, reproducibilidad, automatización, observabilidad y futura operación institucional.

## Corto plazo — asegurar el contrato operativo

1. Crear un validador único de intervalos y bandas compartido por descargador, procesador y orquestador.
2. Serializar las actualizaciones de `download_db.json` y utilizar escritura mediante archivo temporal + reemplazo atómico.
3. Definir una clasificación común de errores:
   - recuperables;
   - entrada inválida;
   - dependencia temporal;
   - terminales.
4. Agregar reintentos finitos y estrategia de backoff para las esperas del módulo de descarga.
5. Incorporar pruebas de descarga sin red para escenarios como:
   - listado correcto;
   - descarga exitosa;
   - descarga parcial;
   - banda faltante;
   - banda duplicada;
   - timeout;
   - JSON corrupto.
6. Mantener alineados código, configuraciones, README y documentación técnica.
7. Revisar periódicamente que los scripts auxiliares y diagnósticos no dependan de nombres o patrones específicos de un único satélite.

**Resultado esperado:** el pipeline falla de manera predecible y recuperable, mantiene contratos consistentes y preserva la lógica RGB existente.

## Mediano plazo — demostrar calidad y capacidad

1. Incorporar pruebas de integración con un conjunto NetCDF pequeño y controlado.
2. Implementar una prueba completa:

```text
descarga simulada
→ validación
→ procesamiento
→ NetCDF RGB
→ PNG
→ GIF
```

3. Verificar estructuralmente el NetCDF generado:
   - variables;
   - dimensiones;
   - coordenadas;
   - proyección;
   - rangos válidos.
4. Medir memoria y tiempo de procesamiento por intervalo.
5. Evaluar liberación de intermedios, chunking o procesamiento por bloques únicamente si las mediciones lo justifican.
6. Incorporar un manifiesto de corrida que identifique:
   - satélite;
   - período;
   - intervalos;
   - productos generados;
   - configuración utilizada.
7. Asociar explícitamente los frames del GIF a una corrida para evitar mezcla accidental de productos.
8. Implementar logging estructurado con identificador de corrida e intervalo.
9. Incorporar integración continua para:
   - pruebas;
   - lint;
   - comprobaciones básicas de calidad;
   - cobertura acordada.
10. Registrar métricas operativas como:
    - cantidad de intervalos;
    - duración por etapa;
    - reintentos;
    - fallos;
    - consumo de memoria.

**Resultado esperado:** comportamiento reproducible, medible y revisable de extremo a extremo.

## Mediano plazo — ampliar validación científica

1. Incorporar más eventos severos y no severos.
2. Incorporar datos de radar meteorológico cuando estén disponibles.
3. Incorporar reportes georreferenciados de superficie.
4. Definir criterios objetivos de coincidencia espacial y temporal.
5. Evaluar falsos positivos y falsos negativos.
6. Analizar sensibilidad de:
   - rangos RGB;
   - umbrales térmicos B13;
   - ventana temporal.
7. Documentar formalmente referencias científicas para:
   - composición RGB;
   - bandas utilizadas;
   - interpretación meteorológica;
   - umbrales B13.

**Resultado esperado:** avanzar desde validación funcional y casos de estudio hacia una evaluación científica cuantitativa del producto.

## Largo plazo — operación institucional

1. Separar, si el volumen lo justifica, componentes de:
   - descarga;
   - procesamiento;
   - publicación.
2. Introducir almacenamiento compartido y coordinación idempotente.
3. Exponer estado y productos mediante un servicio web autorizado.
4. Habilitar múltiples procesadores mediante cola o mecanismo de bloqueo de intervalos.
5. Definir políticas institucionales de:
   - despliegue;
   - retención;
   - respaldo;
   - seguridad;
   - auditoría.
6. Implementar monitoreo y alertas operativas.
7. Definir objetivos de servicio y recuperación.
8. Evaluar automatización de publicación o integración con otros sistemas institucionales.

**Condición previa:** el volumen de datos, cantidad de usuarios y necesidades operativas deben justificar la complejidad adicional.

## Criterio general de evolución

Las mejoras futuras deben preservar:

```text
composición RGB
banda B13 como referencia
georreferencia
formatos de salida
compatibilidad GOES-16 / GOES-19
compatibilidad Mode 3 / Mode 6
```

salvo que exista evidencia técnica o científica suficiente para justificar un cambio.

La prioridad debe mantenerse en este orden:

```text
robustez
→ reproducibilidad
→ medición
→ validación
→ escalabilidad
```
```

