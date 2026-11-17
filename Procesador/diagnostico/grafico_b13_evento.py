#!/usr/bin/env python3
"""
Genera gráficos de evolución temporal a partir del CSV consolidado
del diagnóstico B13.

Gráficos:
1. Porcentaje del dominio con topes nubosos por debajo de:
   -53.15 °C
   -63.15 °C
   -73.15 °C

2. Temperatura mínima B13 por intervalo.

Uso:
    python Procesador/diagnostico/grafico_b13_evento.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# ============================================================
# Rutas
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_CSV = (
    BASE_DIR
    / "Procesador"
    / "data"
    / "output"
    / "diagnostico"
    / "diagnostico_b13_estadisticas.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "Procesador"
    / "data"
    / "output"
    / "diagnostico"
)


# ============================================================
# Configuración del evento
# ============================================================

EVENT_TITLE = "San Rafael, Mendoza - 11/01/2024"


# ============================================================
# Carga y preparación
# ============================================================


def load_data() -> pd.DataFrame:
    """
    Carga el CSV y prepara la columna temporal.
    """
    if not INPUT_CSV.is_file():
        raise FileNotFoundError(
            f"No se encontró el CSV de diagnóstico B13: {INPUT_CSV}"
        )

    df = pd.read_csv(INPUT_CSV)

    required_columns = [
        "interval",
        "temperature_min_c",
        "cumulative_below_53_percent",
        "cumulative_below_63_percent",
        "cumulative_below_73_percent",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Faltan columnas requeridas en el CSV: "
            f"{missing}"
        )

    df["datetime"] = pd.to_datetime(
        df["interval"],
        format="%Y-%m-%d_%H%M",
    )

    df = df.sort_values("datetime").reset_index(drop=True)

    df["hora_utc"] = df["datetime"].dt.strftime("%H:%M")

    return df


# ============================================================
# Gráfico 1
# ============================================================


def plot_cold_cloud_area(df: pd.DataFrame) -> Path:
    """
    Grafica la evolución del porcentaje del dominio con topes
    nubosos bajo distintos umbrales térmicos.
    """
    output_path = (
        OUTPUT_DIR
        / "evolucion_areas_frias_b13_mendoza_2024.png"
    )

    plt.figure(figsize=(9, 5.5))

    plt.plot(
        df["hora_utc"],
        df["cumulative_below_53_percent"],
        marker="o",
        linewidth=2,
        label="BT < -53.15 °C",
    )

    plt.plot(
        df["hora_utc"],
        df["cumulative_below_63_percent"],
        marker="o",
        linewidth=2,
        label="BT < -63.15 °C",
    )

    plt.plot(
        df["hora_utc"],
        df["cumulative_below_73_percent"],
        marker="o",
        linewidth=2,
        label="BT < -73.15 °C",
    )

    plt.xlabel("Hora UTC")
    plt.ylabel("Área del dominio (%)")

    plt.title(
        "Evolución de topes nubosos fríos - B13\n"
        f"{EVENT_TITLE}"
    )

    plt.grid(
        True,
        alpha=0.3,
    )

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

    return output_path


# ============================================================
# Gráfico 2
# ============================================================


def plot_min_temperature(df: pd.DataFrame) -> Path:
    """
    Grafica la temperatura mínima B13 de cada intervalo.
    """
    output_path = (
        OUTPUT_DIR
        / "temperatura_minima_b13_mendoza_2024.png"
    )

    plt.figure(figsize=(9, 5.5))

    plt.plot(
        df["hora_utc"],
        df["temperature_min_c"],
        marker="o",
        linewidth=2,
    )

    plt.xlabel("Hora UTC")
    plt.ylabel("Temperatura mínima B13 (°C)")

    plt.title(
        "Temperatura mínima del tope nuboso - B13\n"
        f"{EVENT_TITLE}"
    )

    plt.grid(
        True,
        alpha=0.3,
    )

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

    return output_path


# ============================================================
# Resumen por consola
# ============================================================


def print_summary(df: pd.DataFrame) -> None:
    """
    Muestra un resumen simple de los intervalos procesados.
    """
    print("\nResumen B13\n")

    for _, row in df.iterrows():
        print(
            f"{row['hora_utc']} UTC | "
            f"Tmin = {row['temperature_min_c']:.2f} °C | "
            f"< -53.15 °C = "
            f"{row['cumulative_below_53_percent']:.3f} % | "
            f"< -63.15 °C = "
            f"{row['cumulative_below_63_percent']:.3f} % | "
            f"< -73.15 °C = "
            f"{row['cumulative_below_73_percent']:.3f} %"
        )


# ============================================================
# Main
# ============================================================


def main() -> int:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = load_data()

    print_summary(df)

    cold_area_plot = plot_cold_cloud_area(df)
    min_temp_plot = plot_min_temperature(df)

    print("\nGráficos generados correctamente:\n")
    print(cold_area_plot)
    print(min_temp_plot)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())