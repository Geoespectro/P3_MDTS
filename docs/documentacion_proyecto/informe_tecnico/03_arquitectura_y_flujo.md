# Arquitectura y flujo

## Vista por módulos

![Arquitectura de módulos](../diagramas/exportados/02_arquitectura_modulos.svg)

> El SVG es el formato destinado a lectura. La fuente Mermaid, el editable Drawio y el SVG publicado fueron sincronizados después de la revisión técnica.

| Módulo | Responsabilidad | Entrada | Salida / estado |
|---|---|---|---|
| `descarga/` | Consultar S3, seleccionar y descargar archivos | `setup.json`, S3/NOAA | `data/<intervalo>/*.nc`, `download_db.json`, logs |
| `Procesador/src/resampleo_alg_band.py` | Coordinar validación, remuestreo, conversión y RGB | seis NetCDF de banda | NetCDF RGB por intervalo |
| `Procesador/src/helpers_resampleo.py` | Implementar operaciones numéricas y persistencia NetCDF | radiancia, calibración y configuración | matrices físicas/normalizadas |
| `Procesador/src/mapa_rgb.py` | Recortar, cartografiar y animar | NetCDF RGB, grillas, logo, shapefiles | PNG y GIF |
| `Procesador/diagnostico/` | Analizar B13 y continuidad temporal RGB | bandas B13 o PNG | PNG/JSON/CSV diagnósticos |
| `run_all.py` | Superponer descarga y procesamiento recuperable | configuraciones y carpetas | productos y `pipeline_state.json` |
| `test/` | Pruebas unitarias de configuración y funciones | fixtures temporales/arreglos | aserciones; no productos persistentes previstos |

## Dependencias y configuración

`descarga/setup.json` selecciona producto, ventana temporal, timeout, workers y bandas. `Procesador/data/conf/config_resampleo.json` define bandas, B13, interpolación lineal y rangos RGB. `Procesador/data/conf/config_mapa.json` define rutas, región, extensión, recursos gráficos y nombre del GIF. Las rutas de mapa son relativas a la raíz y `run_all.py` valida la estructura antes de comenzar. (Fuentes: los tres JSON citados; `run_all.py:75-137`)

## Flujo entre componentes

1. El orquestador inicia el descargador como subproceso, salvo `--skip-download`.
2. El descargador consulta por bloques temporales, descarga primero a `descarga/temp/` y mueve archivos no vacíos a `descarga/data/<AAAA-MM-DD_HHMM>/`.
3. El orquestador exige exactamente un NetCDF por banda y comprueba estabilidad por firma de nombres, tamaños y tiempos de modificación.
4. El procesador toma `x` e `y` de B13, interpola `Rad` y conserva variables de calibración.
5. Convierte unidades, aplica álgebra y normalización, y escribe el NetCDF.
6. El módulo cartográfico recorta, arma la imagen RGB, agrega elementos de mapa, guarda PNG y reconstruye el GIF.
7. El orquestador valida archivos no vacíos y persiste listas de intervalos procesados, mapeados y fallidos.
8. Los diagnósticos se ejecutan aparte; no forman parte de `process_interval`. (Fuentes: `run_all.py:420-507,628-735`; `Procesador/src/*.py`)

## Estado y recuperación

Hay dos estados distintos:

- `descarga/db/download_db.json`: inventario de archivos descargados. Se escribe directamente y permite retomar desde el último intervalo completo. (Fuente: `descarga/goes16Download.py:20-30,166-181`)
- `pipeline_state.json`: estado del orquestador. Se normaliza por compatibilidad y se guarda mediante temporal, `flush`, `fsync` y reemplazo atómico. Registra procesados, mapeados, fallidos, estables, intentos, firmas y errores. (Fuente: `run_all.py:139-280`)

Si un producto ya existe y es no vacío, el orquestador evita repetir esa etapa. Si cambia la firma de una carpeta fallida, rehabilita sus reintentos. La opción `--reset-state` elimina únicamente el estado del orquestador, no los productos. (Fuente: `run_all.py:435-454,646-694,895-909`)

## Estructura relevante

```text
descarga/data/<intervalo>/             # seis bandas de entrada
Procesador/data/resampled/<intervalo>/ # opcional
Procesador/data/rgb/<intervalo>/       # NetCDF RGB
Procesador/data/output/png/            # mapas
Procesador/data/output/gif/            # animación
Procesador/data/output/diagnostico/    # diagnósticos
```

## Diagramas relacionados

- [Flujo general (SVG)](../diagramas/exportados/01_flujo_general.svg) · [editable](../diagramas/editables/01_flujo_general.drawio)
- [Arquitectura de módulos (SVG)](../diagramas/exportados/02_arquitectura_modulos.svg) · [editable](../diagramas/editables/02_arquitectura_modulos.drawio)
- [Secuencia por intervalo (SVG)](../diagramas/exportados/03_secuencia_procesamiento_intervalo.svg) · [editable](../diagramas/editables/03_secuencia_procesamiento_intervalo.drawio)
- [Descarga, validación y estado (SVG)](../diagramas/exportados/04_descarga_validacion_y_estado.svg) · [editable](../diagramas/editables/04_descarga_validacion_y_estado.drawio)
- [Entradas y salidas (SVG)](../diagramas/exportados/05_entradas_y_salidas.svg) · [editable](../diagramas/editables/05_entradas_y_salidas.drawio)
- [Roadmap (SVG)](../diagramas/exportados/06_roadmap_mejoras.svg) · [editable](../diagramas/editables/06_roadmap_mejoras.drawio)
