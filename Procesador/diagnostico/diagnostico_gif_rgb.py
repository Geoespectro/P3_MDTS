#!/usr/bin/env python3
"""
Diagnóstico temporal de los PNG RGB del producto P3 MDTS.

Calcula por frame:
    - medias RGB;
    - brillo medio;
    - cambios de medias respecto del frame anterior;
    - MAE espacial;
    - RMSE espacial;
    - percentil 95 del cambio;
    - porcentaje de píxeles con cambio mayor a 0.05;
    - porcentaje de píxeles válidos analizados.

Genera:
    Procesador/data/output/diagnostico/diagnostico_temporal_rgb.csv

Uso:
    python Procesador/diagnostico/diagnostico_gif_rgb.py
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

BASE_DIR = Path(__file__).resolve().parents[2]
PNG_DIR = BASE_DIR / "Procesador" / "data" / "output" / "png"
OUTPUT_DIR = (
    BASE_DIR
    / "Procesador"
    / "data"
    / "output"
    / "diagnostico"
)

PNG_PATTERN = "CONAE_PRD_GOES16_ABI_MDTS_RGB_*.png"
INTERVAL_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2}_\d{4})")

WHITE_THRESHOLD = 0.95
SPATIAL_CHANGE_THRESHOLD = 0.05


def load_image_rgb(path: Path) -> np.ndarray:
    """
    Abre un PNG, lo convierte a RGB y normaliza sus valores entre 0 y 1.
    """
    try:
        with Image.open(path) as image:
            rgb_image = image.convert("RGB")
            array = np.asarray(rgb_image, dtype=np.float32) / 255.0
    except Exception as error:
        raise RuntimeError(f"No se pudo abrir la imagen: {path}") from error

    if array.ndim != 3 or array.shape[2] != 3:
        raise ValueError(
            f"La imagen no tiene formato RGB válido: {path} -> {array.shape}"
        )

    return array


def build_valid_mask(array: np.ndarray) -> np.ndarray:
    """
    Excluye zonas casi blancas como encabezados, márgenes y fondo exterior.

    Devuelve una máscara 2D de píxeles válidos.
    """
    if array.ndim != 3 or array.shape[2] != 3:
        raise ValueError("La imagen debe tener forma filas x columnas x 3.")

    mean_rgb = np.mean(array, axis=2)

    return (
        np.isfinite(mean_rgb)
        & (mean_rgb < WHITE_THRESHOLD)
    )


def extract_interval(filename: str) -> str:
    match = INTERVAL_PATTERN.search(filename)
    return match.group(1) if match else ""


def calculate_frame_statistics(
    array: np.ndarray,
    valid_mask: np.ndarray,
) -> dict[str, float]:
    valid_pixels = array[valid_mask]

    if valid_pixels.size == 0:
        raise ValueError("La imagen no contiene píxeles válidos.")

    mean_rgb = np.mean(valid_pixels, axis=0)
    brightness = float(np.mean(mean_rgb))

    return {
        "mean_R": float(mean_rgb[0]),
        "mean_G": float(mean_rgb[1]),
        "mean_B": float(mean_rgb[2]),
        "brightness_mean": brightness,
        "valid_pixel_count": int(valid_pixels.shape[0]),
        "valid_pixel_percent": float(
            valid_pixels.shape[0]
            / (array.shape[0] * array.shape[1])
            * 100.0
        ),
    }


def calculate_temporal_statistics(
    current_array: np.ndarray,
    current_mask: np.ndarray,
    previous_array: np.ndarray | None,
    previous_mask: np.ndarray | None,
    current_mean: np.ndarray,
    previous_mean: np.ndarray | None,
) -> dict[str, float]:
    """
    Calcula cambios globales y espaciales respecto del frame anterior.
    """
    if previous_array is None or previous_mask is None or previous_mean is None:
        return {
            "delta_R": 0.0,
            "delta_G": 0.0,
            "delta_B": 0.0,
            "delta_total": 0.0,
            "spatial_mae": 0.0,
            "spatial_rmse": 0.0,
            "spatial_p95": 0.0,
            "pixels_change_gt_005_percent": 0.0,
            "common_valid_pixels": 0,
        }

    if current_array.shape != previous_array.shape:
        raise ValueError(
            "Los frames consecutivos no tienen la misma dimensión: "
            f"anterior={previous_array.shape}, actual={current_array.shape}"
        )

    delta_mean = current_mean - previous_mean
    delta_total = float(np.linalg.norm(delta_mean))

    common_mask = current_mask & previous_mask
    common_count = int(np.count_nonzero(common_mask))

    if common_count == 0:
        raise ValueError(
            "No existen píxeles válidos comunes entre frames consecutivos."
        )

    difference = np.abs(
        current_array[common_mask] - previous_array[common_mask]
    )

    per_pixel_change = np.mean(difference, axis=1)

    mae = float(np.mean(per_pixel_change))
    rmse = float(np.sqrt(np.mean(np.square(per_pixel_change))))
    p95 = float(np.percentile(per_pixel_change, 95))
    changed_percent = float(
        np.count_nonzero(per_pixel_change > SPATIAL_CHANGE_THRESHOLD)
        / common_count
        * 100.0
    )

    return {
        "delta_R": float(delta_mean[0]),
        "delta_G": float(delta_mean[1]),
        "delta_B": float(delta_mean[2]),
        "delta_total": delta_total,
        "spatial_mae": mae,
        "spatial_rmse": rmse,
        "spatial_p95": p95,
        "pixels_change_gt_005_percent": changed_percent,
        "common_valid_pixels": common_count,
    }


def validate_png_files(png_files: list[Path]) -> None:
    if not png_files:
        raise FileNotFoundError(
            f"No se encontraron PNG con patrón {PNG_PATTERN} en: {PNG_DIR}"
        )

    empty_files = [
        str(path)
        for path in png_files
        if not path.is_file() or path.stat().st_size == 0
    ]

    if empty_files:
        raise ValueError(
            "Se encontraron PNG vacíos o inválidos:\n- "
            + "\n- ".join(empty_files)
        )


def save_csv(rows: list[dict[str, object]], output_path: Path) -> None:
    if not rows:
        raise ValueError("No hay resultados para guardar.")

    fieldnames = [
        "interval",
        "filename",
        "mean_R",
        "mean_G",
        "mean_B",
        "brightness_mean",
        "valid_pixel_count",
        "valid_pixel_percent",
        "delta_R",
        "delta_G",
        "delta_B",
        "delta_total",
        "spatial_mae",
        "spatial_rmse",
        "spatial_p95",
        "pixels_change_gt_005_percent",
        "common_valid_pixels",
    ]

    with open(output_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    png_files = sorted(PNG_DIR.glob(PNG_PATTERN))
    validate_png_files(png_files)

    print("\nDiagnóstico temporal RGB del GIF\n")
    print(f"Carpeta PNG: {PNG_DIR}")
    print(f"Cantidad de frames: {len(png_files)}\n")

    rows: list[dict[str, object]] = []

    previous_array: np.ndarray | None = None
    previous_mask: np.ndarray | None = None
    previous_mean: np.ndarray | None = None

    for png_path in png_files:
        array = load_image_rgb(png_path)
        valid_mask = build_valid_mask(array)

        frame_stats = calculate_frame_statistics(array, valid_mask)

        current_mean = np.array(
            [
                frame_stats["mean_R"],
                frame_stats["mean_G"],
                frame_stats["mean_B"],
            ],
            dtype=np.float32,
        )

        temporal_stats = calculate_temporal_statistics(
            current_array=array,
            current_mask=valid_mask,
            previous_array=previous_array,
            previous_mask=previous_mask,
            current_mean=current_mean,
            previous_mean=previous_mean,
        )

        interval = extract_interval(png_path.name)

        row = {
            "interval": interval,
            "filename": png_path.name,
            **frame_stats,
            **temporal_stats,
        }

        rows.append(row)

        print(f"Archivo: {png_path.name}")
        print(f"  Intervalo: {interval or 'no detectado'}")
        print(f"  R medio: {frame_stats['mean_R']:.4f}")
        print(f"  G medio: {frame_stats['mean_G']:.4f}")
        print(f"  B medio: {frame_stats['mean_B']:.4f}")
        print(f"  Brillo medio: {frame_stats['brightness_mean']:.4f}")
        print(
            "  Píxeles válidos: "
            f"{frame_stats['valid_pixel_count']} "
            f"({frame_stats['valid_pixel_percent']:.2f} %)"
        )
        print(
            "  Cambio de medias vs frame anterior: "
            f"{temporal_stats['delta_total']:.4f}"
        )
        print(
            "  MAE espacial vs frame anterior: "
            f"{temporal_stats['spatial_mae']:.4f}"
        )
        print(
            "  RMSE espacial vs frame anterior: "
            f"{temporal_stats['spatial_rmse']:.4f}"
        )
        print(
            "  Percentil 95 del cambio: "
            f"{temporal_stats['spatial_p95']:.4f}"
        )
        print(
            "  Píxeles con cambio > 0.05: "
            f"{temporal_stats['pixels_change_gt_005_percent']:.2f} %"
        )
        print("")

        previous_array = array
        previous_mask = valid_mask
        previous_mean = current_mean

    output_csv = OUTPUT_DIR / "diagnostico_temporal_rgb.csv"
    save_csv(rows, output_csv)

    print(f"CSV guardado en: {output_csv}")
    print("Diagnóstico temporal finalizado correctamente.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
