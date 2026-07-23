# Matriz de trazabilidad

| Afirmación | Módulo | Fuente / función | Documento | Verificación |
|---|---|---|---|---|
| Bandas 02,05,07,08,10,13 | configuración | `descarga/setup.json`; `Procesador/data/conf/config_resampleo.json` | [metodología](../informe_tecnico/04_metodologia_rgb.md) | Verificada por lectura |
| B13 es referencia | procesamiento | `Procesador/src/resampleo_alg_band.py::process_single_interval`; `Procesador/src/helpers_resampleo.py::resample_band` | [metodología](../informe_tecnico/04_metodologia_rgb.md) | Verificada por lectura |
| Fórmulas RGB | procesamiento | `Procesador/src/helpers_resampleo.py::band_algebra` | [metodología](../informe_tecnico/04_metodologia_rgb.md) | Verificada por lectura |
| Conversiones físicas | procesamiento | `Procesador/src/helpers_resampleo.py::radiance_to_*`; `Procesador/src/helpers_resampleo.py::convert_band_to_physical_units` | [informe](../informe_tecnico/02_informe_tecnico_completo.md) | Verificada por lectura; no con datos reales |
| Salida NetCDF georreferenciada | procesamiento | `Procesador/src/helpers_resampleo.py::save_rgb_to_netcdf` | [informe](../informe_tecnico/02_informe_tecnico_completo.md) | Código verificado; archivo no encontrado |
| Generación de PNG | cartografía | `Procesador/src/mapa_rgb.py::process_rgb_file` | [arquitectura](../informe_tecnico/03_arquitectura_y_flujo.md) | Código verificado; archivo no encontrado |
| Creación de GIF | cartografía | `Procesador/src/mapa_rgb.py::build_gif`; `Procesador/src/mapa_rgb.py::main` | [arquitectura](../informe_tecnico/03_arquitectura_y_flujo.md) | Código verificado; archivo no encontrado |
| Estado atómico del orquestador | orquestación | `run_all.py::save_state` | [informe](../informe_tecnico/02_informe_tecnico_completo.md) | Verificada por lectura |
| Estado de descarga no atómico | descarga | `descarga/goes16Download.py::download_file`; `descarga/helpers.py::writeJson` | [limitaciones](../mejoras/01_limitaciones_actuales.md) | Inferencia técnica respaldada |
| Intervalo exige bandas únicas | orquestación | `run_all.py::is_folder_complete`; `run_all.py::get_folder_problem` | [arquitectura](../informe_tecnico/03_arquitectura_y_flujo.md) | Verificada por lectura |
| Pruebas existentes | pruebas | 27 métodos `test_*` en `test/test_descarga.py` y `test/test_procesador.py` | [pruebas](../informe_tecnico/06_pruebas_validacion_y_resultados.md) | Existencia verificada; ejecución pendiente |
| Diagnóstico B13 | diagnóstico | `Procesador/diagnostico/diagnostico_b13.py` | [pruebas](../informe_tecnico/06_pruebas_validacion_y_resultados.md) | Código verificado; resultados pendientes |
| Diagnóstico temporal | diagnóstico | `Procesador/diagnostico/diagnostico_gif_rgb.py` | [pruebas](../informe_tecnico/06_pruebas_validacion_y_resultados.md) | Código verificado; resultados pendientes |
| Caso 19-03-2024 | configuración | `descarga/setup.json` | [pruebas](../informe_tecnico/06_pruebas_validacion_y_resultados.md) | Solo fecha configurada; evidencia pendiente |
