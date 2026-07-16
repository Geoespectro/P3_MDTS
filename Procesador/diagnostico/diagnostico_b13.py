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

import cartopy.crs as ccrs
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
from mapa_rgb import (  # noqa: E402
    get_crop_indexes as get_map_crop_indexes,
)
from mapa_rgb import (
    get_plot_object,
)

DOWNLOAD_DATA_DIR = PROJECT_DIR / "descarga" / "data"
CONF_PATH = PROJECT_DIR / "Procesador" / "data" / "conf" / "config_mapa.json"
OUTPUT_DIR = PROJECT_DIR / "Procesador" / "data" / "output" / "diagnostico"

INTERVAL_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{4}$")

THRESHOLD_YELLOW = -53.15  # 220 K
THRESHOLD_ORANGE = -63.15  # 210 K
THRESHOLD_RED = -73.15  # 200 K


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
    required = [CONF_PATH]
    missing = [str(path) for path in required if not path.is_file()]

    if missing:
        raise FileNotFoundError(
            "Faltan archivos requeridos:\n- " + "\n- ".join(missing)
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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

    yellow = valid & (bt_crop <= THRESHOLD_YELLOW) & (bt_crop > THRESHOLD_ORANGE)
    orange = valid & (bt_crop <= THRESHOLD_ORANGE) & (bt_crop > THRESHOLD_RED)
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
    img_extent: tuple[float, float, float, float],
    map_extent: list[float],
    satellite_crs: ccrs.Geostationary,
    conf: dict[str, Any],
    output_path: Path,
) -> None:
    dpi = conf.get("figure_resolution_dpi", 200)
    fig_width = conf.get("figure_length_inches", 8)
    fig_height = conf.get("figure_high_inches", 5)

    figure = plt.figure(clear=True)
    figure.set_size_inches(fig_width, fig_height)

    axis = get_plot_object(conf, map_extent)

    image = axis.imshow(
        bt_crop,
        transform=satellite_crs,
        extent=img_extent,
        origin="upper",
        cmap="gray_r",
        vmin=-90,
        vmax=30,
        interpolation="nearest",
        aspect="auto",
        zorder=1,
    )

    colorbar = figure.colorbar(
        image,
        ax=axis,
        orientation="vertical",
        pad=0.03,
        shrink=0.85,
    )
    colorbar.set_label("Temperatura de brillo B13 [°C]")

    axis.set_title(
        f"B13 Temperatura de brillo - {interval}",
        fontsize=10,
        pad=8,
    )

    figure.savefig(output_path, dpi=dpi)
    plt.close(figure)


def save_mask_png(
    interval: str,
    bt_crop: np.ndarray,
    masks: np.ndarray,
    img_extent: tuple[float, float, float, float],
    map_extent: list[float],
    satellite_crs: ccrs.Geostationary,
    conf: dict[str, Any],
    output_path: Path,
) -> None:
    dpi = conf.get("figure_resolution_dpi", 200)
    fig_width = conf.get("figure_length_inches", 8)
    fig_height = conf.get("figure_high_inches", 5)

    cmap = ListedColormap(
        [
            (0.0, 0.0, 0.0, 0.0),
            (1.0, 1.0, 0.0, 0.85),
            (1.0, 0.65, 0.0, 0.90),
            (1.0, 0.0, 0.0, 0.95),
        ]
    )

    figure = plt.figure(clear=True)
    figure.set_size_inches(fig_width, fig_height)

    axis = get_plot_object(conf, map_extent)

    # Fondo térmico B13
    axis.imshow(
        bt_crop,
        transform=satellite_crs,
        extent=img_extent,
        origin="upper",
        cmap="gray_r",
        vmin=-90,
        vmax=30,
        interpolation="nearest",
        aspect="auto",
        zorder=1,
    )

    # Máscaras severas superpuestas
    axis.imshow(
        masks,
        transform=satellite_crs,
        extent=img_extent,
        origin="upper",
        cmap=cmap,
        vmin=0,
        vmax=3,
        interpolation="nearest",
        aspect="auto",
        zorder=2,
    )

    axis.set_title(
        f"Máscaras térmicas B13 - {interval}\n"
        "amarillo: -63.15 a -53.15 °C | "
        "naranja: -73.15 a -63.15 °C | "
        "rojo: ≤ -73.15 °C",
        fontsize=8,
        pad=8,
    )

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
        bbox_to_anchor=(0.5, -0.16),
        ncol=3,
        frameon=True,
        fontsize=7,
    )

    figure.savefig(
        output_path,
        dpi=dpi,
        bbox_inches="tight",
    )

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
) -> dict[str, Any]:
    input_dir = DOWNLOAD_DATA_DIR / interval

    if not input_dir.is_dir():
        raise FileNotFoundError(f"No existe la carpeta del intervalo: {input_dir}")

    b13_path = Path(find_band_file(str(input_dir), "13"))

    print("\n" + "=" * 70)
    print(f"Diagnóstico B13: {interval}")
    print("=" * 70)
    print(f"Leyendo B13: {b13_path}")

    with xr.open_dataset(b13_path) as dataset:
        required = [
            "Rad",
            "x",
            "y",
            "goes_imager_projection",
        ]

        for variable in required:
            if variable not in dataset.variables and variable not in dataset.coords:
                raise KeyError(f"No existe '{variable}' en: {b13_path}")

        bt_celsius = radiance_to_brightness_temperature(
            dataset["Rad"].values,
            dataset,
        )
        bt_celsius = np.asarray(bt_celsius, dtype=np.float32)

        if bt_celsius.ndim != 2:
            raise ValueError(
                "B13 debe ser bidimensional. " f"Forma recibida: {bt_celsius.shape}"
            )

        img_extent, img_indexes, map_extent = get_map_crop_indexes(dataset, conf)

        (
            min_lon_idx,
            max_lon_idx,
            min_lat_idx,
            max_lat_idx,
        ) = img_indexes

        bt_crop = bt_celsius[
            min_lat_idx:max_lat_idx,
            min_lon_idx:max_lon_idx,
        ]

        projection = dataset["goes_imager_projection"]

        satellite_crs = ccrs.Geostationary(
            central_longitude=(projection.longitude_of_projection_origin),
            satellite_height=(projection.perspective_point_height),
        )

    if bt_crop.size == 0:
        raise ValueError(f"El recorte quedó vacío para {interval}.")

    if not np.any(np.isfinite(bt_crop)):
        raise ValueError(f"El recorte de {interval} no contiene datos válidos.")

    masks = build_exclusive_masks(bt_crop)
    statistics = calculate_statistics(interval, bt_crop, masks)

    out_bt = OUTPUT_DIR / f"{interval}_B13_BT.png"
    out_mask = OUTPUT_DIR / f"{interval}_B13_mascaras.png"

    save_bt_png(
        interval,
        bt_crop,
        img_extent,
        map_extent,
        satellite_crs,
        conf,
        out_bt,
    )
    save_mask_png(
        interval,
        bt_crop,
        masks,
        img_extent,
        map_extent,
        satellite_crs,
        conf,
        out_mask,
    )
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

    if args.interval:
        if not INTERVAL_PATTERN.fullmatch(args.interval):
            parser.error("--interval debe tener formato YYYY-MM-DD_HHMM.")
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
            successful.append(process_interval(interval, conf))
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
