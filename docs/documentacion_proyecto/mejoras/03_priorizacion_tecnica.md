# Priorización técnica

Escalas cualitativas; el esfuerzo debe estimarse con el equipo.

| Mejora | Problema resuelto | Impacto | Esfuerzo | Riesgo de cambio | Dependencias | Prioridad | Criterio de finalización |
|---|---|---|---|---|---|---:|---|
| Persistencia atómica/serializada de descarga | carrera y corrupción JSON | Muy alto | Medio | Medio | pruebas de concurrencia | 1 | prueba demuestra actualizaciones completas y JSON siempre válido |
| Contrato único de intervalos | divergencia faltante/duplicado | Alto | Medio | Bajo | inventario de consumidores | 2 | todos los módulos comparten una regla y errores consistentes |
| Fallos + reintentos finitos/backoff | bloqueo indefinido | Muy alto | Medio | Medio | taxonomía de errores | 3 | cada escenario termina o reintenta dentro de límites configurados |
| Pruebas de descarga sin red | cambios no verificables | Alto | Medio | Bajo | adaptador/mocks S3 | 4 | casos de éxito, parcial, duplicado y timeout automatizados |
| Integración sintética | ausencia de prueba E2E | Alto | Alto | Bajo | fixtures NetCDF y recursos cartográficos | 5 | producto mínimo reproducible validado automáticamente |
| Manifiesto de GIF | mezcla y reconstrucción global | Medio | Medio | Bajo | definición de corrida | 6 | GIF usa solo frames declarados y ordenados |
| Perfilado/gestión de memoria | riesgo no cuantificado | Medio | Medio | Medio | dataset de referencia | 7 | presupuesto medido y umbral automatizado |
| Logging y métricas | baja observabilidad | Medio | Medio | Bajo | esquema de eventos | 8 | una corrida puede trazarse por intervalo y etapa |
| CI | regresiones tardías | Alto | Medio | Bajo | suite determinista | 9 | checks obligatorios reproducibles sin datos externos |
| Arquitectura distribuida | límite horizontal futuro | Variable | Muy alto | Alto | contratos, métricas y demanda | 10 | solo iniciar con requisito institucional aprobado |

## Orden recomendado

Las prioridades 1–4 forman una sola unidad de trabajo: arreglar estado y reintentos sin pruebas mantendría el riesgo oculto. Después, la integración crea la línea base para mejorar GIF, memoria y observabilidad. CI debe activarse cuando la suite sea determinista; distribuir antes sería construir sobre contratos todavía inestables.
