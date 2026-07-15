#!/usr/bin/env python3
"""
Diagnóstico de Banda 13 para el producto P3 MDTS.

Genera, por intervalo:
    1. Temperatura de brillo B13 recortada a la ROI.
    2. Máscara térmica con categorías exclusivas.
    3. Estadísticas en JSON.

Además, genera un CSV consolidado con todos los intervalos procesados.

Uso:
    python Procesador/diagnostico/diagnostico_b13.py --interval 2024-03-20_2100
    python Procesador/diagnostico/diagnostico_b13.py --all

Si no se indica ninguna opción, procesa todos los intervalos completos.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch


# ============================================================
# Rutas del proyecto
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_DIR / "Procesador" / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from helpers_resampleo import (  # noqa: E402
    find_band_file,
    radiance_to_brightness_temperature,
)


DOWNLOAD_DATA_DIR = PROJECT_DIR / "descarga" / "data"
CONF_PATH = (
    PROJECT_DIR
    / "Procesador"
    / "data"
    / "conf"
    / "config_mapa.json"
)
LATS_PATH = (
    PROJECT_DIR
    / "Procesador"
    / "data"
    / "grids"
    / "g16_lats_8km.txt"
)
LONS_PATH = (
    PROJECT_DIR
    / "Procesador"
    / "data"
    / "grids"
    / "g16_lons_8km.txt"
)
OUTPUT_DIR = (
    PROJECT_DIR
    / "Procesador"
    / "data"
    / "output"
    / "diagnostico"
)

INTERVAL_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{4}$")

THRESHOLD_YELLOW = -53.15  # 220 K
THRESHOLD_ORANGE = -63.15  # 210 K
THRESHOLD_RED = -73.15     # 200 K


# ============================================================
# Utilidades
# ============================================================


def load_json(path: Path) -> dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"No existe el archivo requerido: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON inválido: {path}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"El archivo debe contener un objeto JSON: {path}")

    return data


def validate_required_files() -> None:
    required = [CONF_PATH, LATS_PATH, LONS_PATH]
    missing = [str(path) for path in required if not path.is_file()]

    if missing:
        raise FileNotFoundError(
            "Faltan archivos requeridos:\n- " + "\n- ".join(missing)
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_crop_indexes(
    lats: np.ndarray,
    lons: np.ndarray,
    conf: dict[str, Any],
) -> tuple[int, int, int, int]:
    lon_w = float(conf["argentina_lon_W"]) + float(
        conf.get("delta_lon_W_for_graph", 0.0)
    )
    lon_e = float(conf["argentina_lon_E"])
    lat_s = float(conf["argentina_lat_S"]) + float(
        conf.get("delta_lat_S_for_graph", 0.0)
    )
    lat_n = float(conf["argentina_lat_N"]) + float(
        conf.get("delta_lat_N_for_graph", 0.0)
    )

    mask = (
        np.isfinite(lats)
        & np.isfinite(lons)
        & (lons >= lon_w)
        & (lons <= lon_e)
        & (lats >= lat_s)
        & (lats <= lat_n)
    )

    rows, cols = np.where(mask)

    if rows.size == 0 or cols.size == 0:
        raise ValueError(
            "No se pudo calcular el recorte para la ROI configurada."
        )

    return int(rows.min()), int(rows.max()), int(cols.min()), int(cols.max())


def reduce_to_grid(
    data: np.ndarray,
    target_shape: tuple[int, int],
) -> np.ndarray:
    """
    Reduce una matriz por promedio de bloques para igualar la grilla auxiliar.
    """
    if data.shape == target_shape:
        return data

    target_rows, target_cols = target_shape
    source_rows, source_cols = data.shape

    if source_rows % target_rows != 0 or source_cols % target_cols != 0:
        raise ValueError(
            "No se puede reducir B13 automáticamente. "
            f"B13={data.shape}, grilla={target_shape}"
        )

    factor_y = source_rows // target_rows
    factor_x = source_cols // target_cols

    if factor_y != factor_x:
        raise ValueError(
            "La reducción requerida no es uniforme: "
            f"factor_y={factor_y}, factor_x={factor_x}"
        )

    print(
        f"Reduciendo B13 por bloques {factor_y}x{factor_x} "
        "para igualar la grilla auxiliar."
    )

    reduced = np.nanmean(
        data.reshape(
            target_rows,
            factor_y,
            target_cols,
            factor_x,
        ),
        axis=(1, 3),
    )

    print(f"Nueva forma B13 reducida: {reduced.shape}")
    return reduced


def get_available_intervals() -> list[str]:
    if not DOWNLOAD_DATA_DIR.exists():
        return []

    intervals = []

    for folder in DOWNLOAD_DATA_DIR.iterdir():
        if folder.is_dir() and INTERVAL_PATTERN.fullmatch(folder.name):
            intervals.append(folder.name)

    return sorted(intervals)


def build_exclusive_masks(bt_crop: np.ndarray) -> np.ndarray:
    """
    Categorías exclusivas:
        0: sin máscara
        1: -63.15 < T <= -53.15
        2: -73.15 < T <= -63.15
        3: T <= -73.15
    """
    masks = np.zeros(bt_crop.shape, dtype=np.uint8)

    valid = np.isfinite(bt_crop)

    yellow = (
        valid
        & (bt_crop <= THRESHOLD_YELLOW)
        & (bt_crop > THRESHOLD_ORANGE)
    )
    orange = (
        valid
        & (bt_crop <= THRESHOLD_ORANGE)
        & (bt_crop > THRESHOLD_RED)
    )
    red = valid & (bt_crop <= THRESHOLD_RED)

    masks[yellow] = 1
    masks[orange] = 2
    masks[red] = 3

    return masks


def safe_percentage(count: int, total: int) -> float:
    return (count / total * 100.0) if total > 0 else 0.0


def calculate_statistics(
    interval: str,
    bt_crop: np.ndarray,
    masks: np.ndarray,
) -> dict[str, Any]:
    valid = np.isfinite(bt_crop)
    valid_count = int(np.count_nonzero(valid))

    yellow_count = int(np.count_nonzero(masks == 1))
    orange_count = int(np.count_nonzero(masks == 2))
    red_count = int(np.count_nonzero(masks == 3))

    below_53 = int(np.count_nonzero(valid & (bt_crop <= THRESHOLD_YELLOW)))
    below_63 = int(np.count_nonzero(valid & (bt_crop <= THRESHOLD_ORANGE)))
    below_73 = int(np.count_nonzero(valid & (bt_crop <= THRESHOLD_RED)))

    if valid_count == 0:
        raise ValueError(f"El recorte de {interval} no contiene datos válidos.")

    return {
        "interval": interval,
        "shape_rows": int(bt_crop.shape[0]),
        "shape_cols": int(bt_crop.shape[1]),
        "valid_pixels": valid_count,
        "temperature_min_c": float(np.nanmin(bt_crop)),
        "temperature_max_c": float(np.nanmax(bt_crop)),
        "temperature_mean_c": float(np.nanmean(bt_crop)),
        "temperature_median_c": float(np.nanmedian(bt_crop)),
        "temperature_std_c": float(np.nanstd(bt_crop)),
        "exclusive_yellow_count": yellow_count,
        "exclusive_yellow_percent": safe_percentage(yellow_count, valid_count),
        "exclusive_orange_count": orange_count,
        "exclusive_orange_percent": safe_percentage(orange_count, valid_count),
        "exclusive_red_count": red_count,
        "exclusive_red_percent": safe_percentage(red_count, valid_count),
        "cumulative_below_53_count": below_53,
        "cumulative_below_53_percent": safe_percentage(below_53, valid_count),
        "cumulative_below_63_count": below_63,
        "cumulative_below_63_percent": safe_percentage(below_63, valid_count),
        "cumulative_below_73_count": below_73,
        "cumulative_below_73_percent": safe_percentage(below_73, valid_count),
    }


def save_bt_png(
    interval: str,
    bt_crop: np.ndarray,
    output_path: Path,
) -> None:
    figure, axis = plt.subplots(figsize=(11, 7))

    image = axis.imshow(
        bt_crop,
        cmap="gray_r",
        vmin=-90,
        vmax=30,
    )

    colorbar = figure.colorbar(image, ax=axis)
    colorbar.set_label("Temperatura de brillo B13 [°C]")

    axis.set_title(f"B13 Temperatura de brillo - {interval}")
    axis.axis("off")

    figure.tight_layout()
    figure.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(figure)


def save_mask_png(
    interval: str,
    masks: np.ndarray,
    output_path: Path,
) -> None:
    cmap = ListedColormap(["black", "yellow", "orange", "red"])

    figure, axis = plt.subplots(figsize=(11, 7))

    axis.imshow(
        masks,
        cmap=cmap,
        vmin=0,
        vmax=3,
        interpolation="nearest",
    )

    axis.set_title(
        f"Máscaras B13 - {interval}\n"
        "amarillo: -63.15 a -53.15 °C | "
        "naranja: -73.15 a -63.15 °C | "
        "rojo: ≤ -73.15 °C"
    )
    axis.axis("off")

    legend_elements = [
        Patch(
            facecolor="yellow",
            edgecolor="black",
            label="-63.15 < T ≤ -53.15 °C",
        ),
        Patch(
            facecolor="orange",
            edgecolor="black",
            label="-73.15 < T ≤ -63.15 °C",
        ),
        Patch(
            facecolor="red",
            edgecolor="black",
            label="T ≤ -73.15 °C",
        ),
    ]

    axis.legend(
        handles=legend_elements,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.08),
        ncol=3,
        frameon=True,
    )

    figure.tight_layout()
    figure.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(figure)


def save_interval_json(
    interval: str,
    statistics: dict[str, Any],
) -> Path:
    output_path = OUTPUT_DIR / f"{interval}_B13_estadisticas.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(statistics, file, indent=4, ensure_ascii=False)

    return output_path


def print_statistics(statistics: dict[str, Any]) -> None:
    print("\nEstadísticas B13:")
    print(
        "  Temperatura [°C]: "
        f"min={statistics['temperature_min_c']:.2f}, "
        f"max={statistics['temperature_max_c']:.2f}, "
        f"media={statistics['temperature_mean_c']:.2f}, "
        f"mediana={statistics['temperature_median_c']:.2f}, "
        f"desvío={statistics['temperature_std_c']:.2f}"
    )

    print("  Categorías exclusivas:")
    print(
        "    Amarillo (-63.15, -53.15]: "
        f"{statistics['exclusive_yellow_count']} píxeles "
        f"({statistics['exclusive_yellow_percent']:.3f} %)"
    )
    print(
        "    Naranja (-73.15, -63.15]: "
        f"{statistics['exclusive_orange_count']} píxeles "
        f"({statistics['exclusive_orange_percent']:.3f} %)"
    )
    print(
        "    Rojo (≤ -73.15): "
        f"{statistics['exclusive_red_count']} píxeles "
        f"({statistics['exclusive_red_percent']:.3f} %)"
    )

    print("  Umbrales acumulativos:")
    print(
        "    T ≤ -53.15 °C: "
        f"{statistics['cumulative_below_53_count']} "
        f"({statistics['cumulative_below_53_percent']:.3f} %)"
    )
    print(
        "    T ≤ -63.15 °C: "
        f"{statistics['cumulative_below_63_count']} "
        f"({statistics['cumulative_below_63_percent']:.3f} %)"
    )
    print(
        "    T ≤ -73.15 °C: "
        f"{statistics['cumulative_below_73_count']} "
        f"({statistics['cumulative_below_73_percent']:.3f} %)"
    )


# ============================================================
# Procesamiento
# ============================================================


def process_interval(
    interval: str,
    conf: dict[str, Any],
    lats: np.ndarray,
    lons: np.ndarray,
) -> dict[str, Any]:
    input_dir = DOWNLOAD_DATA_DIR / interval

    if not input_dir.is_dir():
        raise FileNotFoundError(
            f"No existe la carpeta del intervalo: {input_dir}"
        )

    b13_path = Path(find_band_file(str(input_dir), "13"))

    print("\n" + "=" * 70)
    print(f"Diagnóstico B13: {interval}")
    print("=" * 70)
    print(f"Leyendo B13: {b13_path}")

    with xr.open_dataset(b13_path) as dataset:
        if "Rad" not in dataset:
            raise KeyError(f"La variable 'Rad' no existe en: {b13_path}")

        bt_celsius = radiance_to_brightness_temperature(
            dataset["Rad"].values,
            dataset,
        )

    bt_celsius = np.asarray(bt_celsius, dtype=np.float32)

    if bt_celsius.ndim != 2:
        raise ValueError(
            f"B13 debe ser bidimensional. Forma recibida: {bt_celsius.shape}"
        )

    bt_celsius = reduce_to_grid(bt_celsius, lats.shape)

    if lons.shape != lats.shape:
        raise ValueError(
            f"Las grillas lat/lon no coinciden: "
            f"lats={lats.shape}, lons={lons.shape}"
        )

    r0, r1, c0, c1 = get_crop_indexes(lats, lons, conf)
    bt_crop = bt_celsius[r0 : r1 + 1, c0 : c1 + 1]

    if bt_crop.size == 0:
        raise ValueError(f"El recorte quedó vacío para {interval}.")

    masks = build_exclusive_masks(bt_crop)
    statistics = calculate_statistics(interval, bt_crop, masks)

    out_bt = OUTPUT_DIR / f"{interval}_B13_BT.png"
    out_mask = OUTPUT_DIR / f"{interval}_B13_mascaras.png"

    save_bt_png(interval, bt_crop, out_bt)
    save_mask_png(interval, masks, out_mask)
    out_json = save_interval_json(interval, statistics)

    print_statistics(statistics)
    print(f"\nPNG B13 generado: {out_bt}")
    print(f"PNG máscaras generado: {out_mask}")
    print(f"JSON estadísticas generado: {out_json}")

    return statistics


def save_consolidated_csv(
    rows: list[dict[str, Any]],
) -> Path:
    output_path = OUTPUT_DIR / "diagnostico_b13_estadisticas.csv"

    if not rows:
        return output_path

    fieldnames = list(rows[0].keys())

    with open(output_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return output_path


# ============================================================
# CLI
# ============================================================


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Diagnóstico B13 del producto P3 MDTS. "
            "Genera mapas y estadísticas térmicas."
        )
    )

    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        "--interval",
        help="Intervalo a diagnosticar. Ejemplo: 2024-03-20_2100",
    )

    group.add_argument(
        "--all",
        action="store_true",
        help="Procesa todos los intervalos disponibles.",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    validate_required_files()

    conf = load_json(CONF_PATH)
    lats = np.loadtxt(LATS_PATH)
    lons = np.loadtxt(LONS_PATH)

    if lats.ndim != 2 or lons.ndim != 2:
        raise ValueError(
            f"Las grillas deben ser bidimensionales: "
            f"lats={lats.shape}, lons={lons.shape}"
        )

    if args.interval:
        if not INTERVAL_PATTERN.fullmatch(args.interval):
            parser.error(
                "--interval debe tener formato YYYY-MM-DD_HHMM."
            )
        intervals = [args.interval]
    else:
        intervals = get_available_intervals()

    if not intervals:
        print("No se encontraron intervalos para diagnosticar.")
        return 1

    print(f"Intervalos seleccionados: {intervals}")

    successful: list[dict[str, Any]] = []
    failed: list[tuple[str, str]] = []

    for interval in intervals:
        try:
            successful.append(
                process_interval(interval, conf, lats, lons)
            )
        except Exception as error:
            failed.append((interval, str(error)))
            print(f"\nERROR en {interval}: {error}", file=sys.stderr)

    csv_path = save_consolidated_csv(successful)

    print("\n" + "=" * 70)
    print("RESUMEN DEL DIAGNÓSTICO B13")
    print("=" * 70)
    print(f"Intervalos correctos: {len(successful)}")
    print(f"Intervalos con error: {len(failed)}")

    if successful:
        print(f"CSV consolidado: {csv_path}")

    if failed:
        print("Errores:")
        for interval, error in failed:
            print(f"  {interval}: {error}")

    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())