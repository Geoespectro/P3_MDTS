#!/usr/bin/env python3
"""
Herramienta de limpieza para P3_MDTS_en_desarrollo.

Elimina datos y productos generados sin borrar la estructura de carpetas
ni los archivos fuente del proyecto.
"""

from __future__ import annotations

import shutil
from pathlib import Path


# ============================================================
# CONFIGURACIÓN
# ============================================================

# True: muestra qué eliminaría, pero no borra nada.
# False: realiza la limpieza.
DRY_RUN = False

CLEAN_CONFIG = {
    "descargas": True,
    "base_datos": True,
    "logs_descarga": True,
    "temporales_descarga": True,
    "rgb": True,
    "bandas_resampleadas": True,
    "mapas_png": True,
    "gif": True,
    "diagnosticos_generados": True,
    "pipeline_state": True,
}


# ============================================================
# RUTAS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

PATHS = {
    "descargas": PROJECT_ROOT / "descarga" / "data",
    "base_datos": PROJECT_ROOT / "descarga" / "db",
    "logs_descarga": PROJECT_ROOT / "descarga" / "logs",
    "temporales_descarga": PROJECT_ROOT / "descarga" / "temp",
    "rgb": PROJECT_ROOT / "Procesador" / "data" / "rgb",
    "bandas_resampleadas": PROJECT_ROOT / "Procesador" / "data" / "resampled",
    "mapas_png": PROJECT_ROOT / "Procesador" / "data" / "output" / "png",
    "gif": PROJECT_ROOT / "Procesador" / "data" / "output" / "gif",
    "diagnosticos_generados": (
        PROJECT_ROOT / "Procesador" / "data" / "output" / "diagnostico"
    ),
    "pipeline_state": PROJECT_ROOT / "pipeline_state.json",
}


def is_inside_project(path: Path) -> bool:
    try:
        path.resolve().relative_to(PROJECT_ROOT.resolve())
        return True
    except ValueError:
        return False


def validate_target(path: Path) -> None:
    resolved = path.resolve()

    if not is_inside_project(resolved):
        raise ValueError(f"Ruta fuera del proyecto: {resolved}")

    if resolved == PROJECT_ROOT.resolve():
        raise ValueError("No se permite eliminar la raíz completa del proyecto.")


def remove_path(path: Path) -> int:
    validate_target(path)

    if not path.exists() and not path.is_symlink():
        return 0

    if DRY_RUN:
        print(f"  [SIMULACIÓN] Se eliminaría: {path}")
        return 1

    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)

    print(f"  [ELIMINADO] {path}")
    return 1


def clean_directory_contents(directory: Path) -> int:
    validate_target(directory)

    if not directory.exists():
        if DRY_RUN:
            print(f"  [NO EXISTE] {directory}")
        else:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"  [CREADO VACÍO] {directory}")
        return 0

    if not directory.is_dir():
        raise ValueError(f"La ruta esperada no es un directorio: {directory}")

    removed = 0

    for item in directory.iterdir():
        removed += remove_path(item)

    if removed == 0:
        print(f"  [YA ESTABA VACÍO] {directory}")

    return removed


def clean_selected_item(key: str, path: Path) -> int:
    print(f"\n{key}:")

    if key == "pipeline_state":
        removed = remove_path(path)
        if removed == 0:
            print(f"  [NO EXISTE] {path}")
        return removed

    return clean_directory_contents(path)


def main() -> None:
    print("=" * 60)
    print("LIMPIEZA DEL PROYECTO P3 MDTS")
    print("=" * 60)
    print(f"Raíz del proyecto: {PROJECT_ROOT}")
    print(f"Modo simulación: {'ACTIVADO' if DRY_RUN else 'DESACTIVADO'}")

    total_removed = 0
    enabled_count = 0

    for key, enabled in CLEAN_CONFIG.items():
        if not enabled:
            print(f"\n{key}:")
            print("  [OMITIDO POR CONFIGURACIÓN]")
            continue

        enabled_count += 1
        total_removed += clean_selected_item(key, PATHS[key])

    print("\n" + "=" * 60)

    if enabled_count == 0:
        print("No había ninguna opción de limpieza activada.")
    elif DRY_RUN:
        print(f"Simulación finalizada. Elementos detectados: {total_removed}")
        print("No se eliminó ningún archivo.")
    else:
        print(f"Limpieza finalizada. Elementos eliminados: {total_removed}")

    print("=" * 60)


if __name__ == "__main__":
    main()