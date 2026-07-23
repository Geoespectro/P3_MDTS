# Roadmap de mejoras

Todo lo listado es **propuesta**, no funcionalidad implementada.

## Corto plazo — asegurar el contrato operativo

1. Crear un validador único de intervalos y bandas.
2. Serializar actualizaciones de descarga y escribir JSON con temporal + reemplazo atómico.
3. Definir errores recuperables/terminales.
4. Agregar reintentos finitos, backoff y salida explícita.
5. Probar descarga sin red: listado, éxito, parcial, duplicado, timeout y corrupción.
6. Alinear documentación/configuración y hacer limpieza segura por defecto.

**Resultado esperado:** el pipeline falla de manera predecible y recuperable sin alterar la lógica RGB.

## Mediano plazo — demostrar calidad y capacidad

1. Pruebas de integración con NetCDF sintético pequeño.
2. Prueba completa descarga simulada → NetCDF → PNG → GIF.
3. Perfilado de memoria/tiempo; liberar intermedios o aplicar chunking solo con evidencia.
4. Manifiesto de frames por corrida para el GIF.
5. Logging estructurado con identificador de corrida/intervalo.
6. CI con pruebas, lint, tipos graduales y cobertura acordada.
7. Métricas de intervalos, latencias, reintentos, fallos y memoria.

**Resultado esperado:** comportamiento reproducible, medible y revisable.

## Largo plazo — operación institucional

1. Separar contenedores de descarga, procesamiento y publicación.
2. Introducir almacenamiento compartido y coordinación idempotente.
3. Exponer estado/productos mediante servicio web autorizado.
4. Habilitar múltiples procesadores con bloqueo/cola de intervalos.
5. Definir despliegue, retención, respaldo y seguridad institucional.
6. Implementar monitoreo, alertas y objetivos de servicio.

**Condición previa:** volumen, usuarios y acuerdos operativos deben justificar la complejidad.
