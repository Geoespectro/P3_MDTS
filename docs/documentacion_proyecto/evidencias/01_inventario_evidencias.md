# Inventario de evidencias existentes

Inspección estática del 22-07-2026. No se copiaron binarios. Las fechas son metadatos del sistema de archivos y no prueban fecha de generación científica.

| Ruta / conjunto | Tipo / tamaño | Qué demuestra | Diapositiva | Uso |
|---|---|---|---:|---|
| `README.md` | Markdown, 5.002 B | alcance y comandos declarados | 2–3 | Listo; contrastado con código |
| `docs/Readme_descarga.md` | Markdown, 4.631 B | operación declarada de descarga | 5–6 | Revisar: ejemplo horario difiere de config |
| `docs/Readme_procesador.md` | Markdown, 7.573 B | procesamiento y salidas declaradas | 6–9 | Listo con cautela |
| `descarga/setup.json` | JSON, 553 B | bandas/producto/ventana actual | 4 | Listo |
| `Procesador/data/conf/config_resampleo.json` | JSON, 248 B | B13, método y rangos | 4, 7 | Listo |
| `Procesador/data/conf/config_mapa.json` | JSON, 1.334 B | nombres, rutas, región y estilo | 8 | Listo |
| `test/test_descarga.py` | código de prueba | 4 métodos declarados | 9 | Requiere ejecución |
| `test/test_procesador.py` | código de prueba | 23 métodos declarados | 9 | Requiere ejecución |
| `Procesador/diagnostico/*.py` | código diagnóstico | salidas/métricas previstas | 9 | Requiere ejecución y revisión científica |
| `Procesador/data/logo/logo.png` | PNG, 4.310 B | activo gráfico institucional | 1 | Revisar autorización/legibilidad |
| `Procesador/data/grids/g16_lats_8km.txt`, `g16_lons_8km.txt` | grillas de texto | insumos del recorte | 5–6 | Listos como insumo, no visual |
| `Procesador/data/shp/limite_internacional2/*` | shapefile; `.shp` 8.878.808 B | límites personalizados disponibles | 8 | Revisar licencia/atribución |
| `Procesador/data/shp/limite_interprovincial2/*` | shapefile; `.shp` 4.196.992 B | límites provinciales disponibles | 8 | Revisar licencia/atribución |
| `Procesador/data/shp/shapefiles/natural_earth/physical/*` | 3 shapefiles; `.shp` 6.812.812, 1.046.728 y 89.652 B | costas en varias escalas | 8 | Revisar atribución |
| `Dockerfile`, `requirements.txt` | configuración | entorno previsto y dependencias | 5 | Listos; no se construyó imagen |

## Productos no encontrados

No se encontraron, fuera de ubicaciones excluidas de la inspección, NetCDF `.nc`, PNG de salida, GIF, CSV/JSON diagnósticos, logs o `pipeline_state.json`. Estas rutas están ignoradas por `.gitignore`, por lo que podrían existir localmente en otra copia sin formar parte del repositorio compartido.
