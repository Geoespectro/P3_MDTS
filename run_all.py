#!/usr/bin/env python3
"""
Orquestador general del pipeline P3 MDTS.

Flujo:
    descarga en segundo plano
    -> detección de intervalos completos y estables
    -> resampleo + generación RGB
    -> mapa PNG + actualización del GIF
    -> validación de productos

Características:
    - usa el mismo intérprete Python/entorno virtual;
    - procesa un intervalo a la vez para limitar el consumo de memoria;
    - descarga y procesamiento pueden ejecutarse simultáneamente;
    - reanuda ejecuciones interrumpidas usando los productos reales en disco;
    - limita reintentos para evitar ciclos infinitos;
    - guarda pipeline_state.json de forma atómica;
    - detecta productos vacíos o GIF desactualizado;
    - comprueba el código de salida del descargador.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent

# ============================================================
# Rutas de la estructura P3
# ============================================================

DESCARGA_SCRIPT = BASE_DIR / "descarga" / "goes16Download.py"
PROCESADOR_SCRIPT = BASE_DIR / "Procesador" / "src" / "resampleo_alg_band.py"
MAPA_SCRIPT = BASE_DIR / "Procesador" / "src" / "mapa_rgb.py"

RAW_DATA_DIR = BASE_DIR / "descarga" / "data"
RGB_DATA_DIR = BASE_DIR / "Procesador" / "data" / "rgb"
MAP_OUTPUT_DIR = BASE_DIR / "Procesador" / "data" / "output"

MAP_CONFIG_PATH = (
    BASE_DIR / "Procesador" / "data" / "conf" / "config_mapa.json"
)
STATE_PATH = BASE_DIR / "pipeline_state.json"

REQUIRED_BANDS = ["02", "05", "07", "08", "10", "13"]
INTERVAL_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{4}$")

DEFAULT_GIF_FILENAME = "CONAE_PRD_GOES16_ABI_MDTS_RGB_animacion.gif"


# ============================================================
# Logging
# ============================================================


def log(message: str) -> None:
    print(f"[PIPELINE] {message}", flush=True)


# ============================================================
# Configuración y validación inicial
# ============================================================


def validate_project_structure() -> None:
    """
    Verifica que existan los scripts y configuraciones esenciales.
    """
    required_files = [
        DESCARGA_SCRIPT,
        PROCESADOR_SCRIPT,
        MAPA_SCRIPT,
        MAP_CONFIG_PATH,
    ]

    missing = [str(path) for path in required_files if not path.is_file()]

    if missing:
        raise FileNotFoundError(
            "Faltan archivos requeridos por el pipeline:\n- "
            + "\n- ".join(missing)
        )

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    RGB_DATA_DIR.mkdir(parents=True, exist_ok=True)
    (MAP_OUTPUT_DIR / "png").mkdir(parents=True, exist_ok=True)
    (MAP_OUTPUT_DIR / "gif").mkdir(parents=True, exist_ok=True)


def load_map_config() -> dict[str, Any]:
    try:
        with open(MAP_CONFIG_PATH, "r", encoding="utf-8") as file:
            config = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"No se pudo leer la configuración del mapa: {MAP_CONFIG_PATH}"
        ) from exc

    if not isinstance(config, dict):
        raise ValueError("config_mapa.json debe contener un objeto JSON.")

    return config


def get_expected_gif_path() -> Path:
    config = load_map_config()
    gif_filename = config.get("gif_filename", DEFAULT_GIF_FILENAME)

    if not isinstance(gif_filename, str) or not gif_filename.strip():
        raise ValueError("'gif_filename' debe ser un texto no vacío.")

    # Se usa solamente el nombre para impedir que una configuración accidental
    # apunte fuera del directorio de salida del proyecto.
    safe_name = Path(gif_filename).name

    if safe_name != gif_filename:
        raise ValueError(
            "'gif_filename' debe contener solo el nombre del archivo, no una ruta."
        )

    return MAP_OUTPUT_DIR / "gif" / safe_name


# ============================================================
# Estado del pipeline
# ============================================================


def empty_state() -> dict[str, Any]:
    return {
        "processed_intervals": [],
        "mapped_intervals": [],
        "failed_intervals": [],
        "stable_intervals": [],
        "retry_counts": {},
        "failed_signatures": {},
        "last_errors": {},
    }


def normalize_state(state: Any) -> dict[str, Any]:
    """
    Normaliza estados anteriores para mantener compatibilidad.
    """
    normalized = empty_state()

    if not isinstance(state, dict):
        return normalized

    for key in [
        "processed_intervals",
        "mapped_intervals",
        "failed_intervals",
        "stable_intervals",
    ]:
        value = state.get(key, [])
        if isinstance(value, list):
            normalized[key] = sorted(
                {item for item in value if isinstance(item, str)}
            )

    for key in ["retry_counts", "failed_signatures", "last_errors"]:
        value = state.get(key, {})
        if isinstance(value, dict):
            normalized[key] = value

    # retry_counts debe contener enteros no negativos.
    normalized["retry_counts"] = {
        str(interval): max(0, int(count))
        for interval, count in normalized["retry_counts"].items()
        if isinstance(count, (int, float, str))
        and str(count).lstrip("-").isdigit()
    }

    normalized["failed_signatures"] = {
        str(interval): str(signature)
        for interval, signature in normalized["failed_signatures"].items()
    }

    normalized["last_errors"] = {
        str(interval): str(error)
        for interval, error in normalized["last_errors"].items()
    }

    return normalized


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return empty_state()

    try:
        with open(STATE_PATH, "r", encoding="utf-8") as file:
            return normalize_state(json.load(file))
    except (OSError, json.JSONDecodeError):
        log("pipeline_state.json corrupto o inválido. Se crea un estado nuevo.")
        return empty_state()


def save_state(state: dict[str, Any]) -> None:
    """
    Guarda el estado de forma atómica para evitar un JSON incompleto.
    """
    state = normalize_state(state)
    temp_path = STATE_PATH.with_suffix(".json.tmp")

    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump(state, file, indent=4, ensure_ascii=False)
        file.flush()
        os.fsync(file.fileno())

    temp_path.replace(STATE_PATH)


def add_to_state_list(
    state: dict[str, Any],
    key: str,
    interval: str,
) -> None:
    if interval not in state[key]:
        state[key].append(interval)
        state[key] = sorted(state[key])
        save_state(state)


def remove_from_state_list(
    state: dict[str, Any],
    key: str,
    interval: str,
) -> None:
    if interval in state[key]:
        state[key].remove(interval)
        save_state(state)


def clear_failure_state(state: dict[str, Any], interval: str) -> None:
    changed = False

    if interval in state["failed_intervals"]:
        state["failed_intervals"].remove(interval)
        changed = True

    for key in ["retry_counts", "failed_signatures", "last_errors"]:
        if interval in state[key]:
            del state[key][interval]
            changed = True

    if changed:
        save_state(state)


def register_failure(
    state: dict[str, Any],
    interval: str,
    error: Exception,
) -> int:
    count = int(state["retry_counts"].get(interval, 0)) + 1

    state["retry_counts"][interval] = count
    state["failed_signatures"][interval] = get_folder_signature(
        RAW_DATA_DIR / interval
    )
    state["last_errors"][interval] = str(error)

    if interval not in state["failed_intervals"]:
        state["failed_intervals"].append(interval)
        state["failed_intervals"] = sorted(state["failed_intervals"])

    save_state(state)
    return count


def print_status(state: dict[str, Any], max_retries: int) -> None:
    log("Estado actual:")
    log(
        f"Procesados RGB: {len(state['processed_intervals'])} "
        f"-> {state['processed_intervals']}"
    )
    log(
        f"Mapeados PNG/GIF: {len(state['mapped_intervals'])} "
        f"-> {state['mapped_intervals']}"
    )
    log(
        f"Fallidos: {len(state['failed_intervals'])} "
        f"-> {state['failed_intervals']}"
    )

    exhausted = [
        interval
        for interval, attempts in state["retry_counts"].items()
        if int(attempts) >= max_retries
    ]

    if exhausted:
        log(
            f"Sin más reintentos automáticos ({max_retries}): "
            f"{sorted(exhausted)}"
        )


# ============================================================
# Detección de carpetas completas
# ============================================================


def get_band_from_filename(filename: str) -> str | None:
    """
    Extrae la banda desde nombres como:
    OR_ABI-L1b-RadF-M6C13_G16_...
    """
    match = re.search(r"M6C(\d{2})_", filename)
    return match.group(1) if match else None


def get_interval_folders() -> list[Path]:
    if not RAW_DATA_DIR.exists():
        return []

    folders = []

    for item in RAW_DATA_DIR.iterdir():
        if not item.is_dir():
            continue

        if not INTERVAL_PATTERN.fullmatch(item.name):
            log(f"Se omite carpeta con nombre de intervalo inválido: {item.name}")
            continue

        folders.append(item)

    return sorted(folders, key=lambda path: path.name)


def get_band_files(folder: Path) -> dict[str, list[Path]]:
    band_files: dict[str, list[Path]] = {}

    for file in folder.glob("*.nc"):
        band = get_band_from_filename(file.name)

        if band:
            band_files.setdefault(band, []).append(file)

    return band_files


def is_folder_complete(folder: Path) -> bool:
    band_files = get_band_files(folder)

    return all(
        band in band_files and len(band_files[band]) == 1
        for band in REQUIRED_BANDS
    )


def get_folder_problem(folder: Path) -> str | None:
    """
    Informa bandas faltantes o duplicadas.
    """
    band_files = get_band_files(folder)

    missing = [band for band in REQUIRED_BANDS if band not in band_files]
    duplicated = [
        band
        for band in REQUIRED_BANDS
        if len(band_files.get(band, [])) > 1
    ]

    problems = []

    if missing:
        problems.append(f"faltan bandas {missing}")

    if duplicated:
        problems.append(f"bandas duplicadas {duplicated}")

    return "; ".join(problems) if problems else None


def get_total_nc_size(folder: Path) -> int:
    total = 0

    for file in folder.glob("*.nc"):
        try:
            total += file.stat().st_size
        except FileNotFoundError:
            pass

    return total


def get_folder_signature(folder: Path) -> str:
    """
    Firma simple para detectar cambios después de un fallo.
    """
    if not folder.exists():
        return "missing"

    parts = []

    for file in sorted(folder.glob("*.nc"), key=lambda path: path.name):
        try:
            stat = file.stat()
            parts.append(f"{file.name}:{stat.st_size}:{stat.st_mtime_ns}")
        except FileNotFoundError:
            continue

    return "|".join(parts)


def is_folder_stable(folder: Path, wait_seconds: float) -> bool:
    """
    Comprueba cantidad de archivos, tamaño y fecha de modificación.
    """
    signature_1 = get_folder_signature(folder)

    if not signature_1:
        return False

    time.sleep(wait_seconds)
    signature_2 = get_folder_signature(folder)

    return signature_1 == signature_2


def refresh_retry_if_folder_changed(
    state: dict[str, Any],
    interval: str,
) -> None:
    """
    Si los archivos cambiaron desde el último fallo, habilita nuevos intentos.
    """
    old_signature = state["failed_signatures"].get(interval)

    if old_signature is None:
        return

    new_signature = get_folder_signature(RAW_DATA_DIR / interval)

    if new_signature != old_signature:
        log(
            f"Los archivos de {interval} cambiaron desde el último fallo. "
            "Se reinician sus reintentos."
        )
        clear_failure_state(state, interval)


def get_complete_intervals_ready(
    *,
    skip_stability: bool,
    stability_seconds: float,
    state: dict[str, Any],
) -> list[str]:
    """
    Busca intervalos completos que todavía necesiten RGB, PNG o GIF.
    """
    ready: list[str] = []
    stable_intervals = set(state.get("stable_intervals", []))

    for folder in get_interval_folders():
        interval = folder.name

        refresh_retry_if_folder_changed(state, interval)

        if interval_products_complete(interval):
            continue

        problem = get_folder_problem(folder)

        if problem:
            # Una carpeta incompleta puede estar todavía descargándose.
            # Las duplicadas se informan porque no se resolverán solas normalmente.
            if "duplicadas" in problem:
                log(f"Carpeta {interval} no procesable: {problem}.")
            continue

        if interval in stable_intervals:
            ready.append(interval)
            continue

        if skip_stability:
            log(f"Carpeta completa detectada: {interval}. Se asume estable.")
            add_to_state_list(state, "stable_intervals", interval)
            ready.append(interval)
            continue

        log(f"Carpeta completa detectada: {interval}. Verificando estabilidad...")

        if is_folder_stable(folder, stability_seconds):
            add_to_state_list(state, "stable_intervals", interval)
            ready.append(interval)
        else:
            log(
                f"Carpeta {interval} todavía parece estar en escritura. "
                "Se revisará luego."
            )

    return sorted(ready)


# ============================================================
# Validaciones de productos
# ============================================================


def is_nonempty_file(path: Path) -> bool:
    try:
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


def get_rgb_path(interval: str) -> Path:
    return RGB_DATA_DIR / interval / f"{interval}_rgb_result.nc"


def get_png_matches(interval: str) -> list[Path]:
    png_dir = MAP_OUTPUT_DIR / "png"

    if not png_dir.exists():
        return []

    return sorted(
        [
            path
            for path in png_dir.glob(f"*{interval}.png")
            if is_nonempty_file(path)
        ]
    )


def get_png_path(interval: str) -> Path | None:
    matches = get_png_matches(interval)
    return matches[0] if matches else None


def rgb_exists(interval: str) -> bool:
    return is_nonempty_file(get_rgb_path(interval))


def png_exists(interval: str) -> bool:
    return get_png_path(interval) is not None


def gif_exists() -> bool:
    return is_nonempty_file(get_expected_gif_path())


def gif_is_current() -> bool:
    """
    El GIF se considera vigente si es posterior al PNG más nuevo.
    """
    gif_path = get_expected_gif_path()

    if not is_nonempty_file(gif_path):
        return False

    png_dir = MAP_OUTPUT_DIR / "png"
    pngs = [
        path
        for path in png_dir.glob("*.png")
        if is_nonempty_file(path)
    ]

    if not pngs:
        return False

    newest_png_mtime = max(path.stat().st_mtime_ns for path in pngs)
    return gif_path.stat().st_mtime_ns >= newest_png_mtime


def interval_products_complete(interval: str) -> bool:
    return rgb_exists(interval) and png_exists(interval) and gif_is_current()


def validate_rgb(interval: str) -> Path:
    rgb_path = get_rgb_path(interval)

    if not is_nonempty_file(rgb_path):
        raise FileNotFoundError(
            f"No se generó un RGB válido o está vacío: {rgb_path}"
        )

    return rgb_path


def validate_png(interval: str) -> Path:
    png_path = get_png_path(interval)

    if png_path is None:
        raise FileNotFoundError(
            f"No se generó un PNG válido para el intervalo: {interval}"
        )

    return png_path


def validate_gif() -> Path:
    gif_path = get_expected_gif_path()

    if not is_nonempty_file(gif_path):
        raise FileNotFoundError(
            f"No se generó el GIF esperado o está vacío: {gif_path}"
        )

    if not gif_is_current():
        raise RuntimeError(
            f"El GIF está desactualizado respecto de los PNG: {gif_path}"
        )

    return gif_path


# ============================================================
# Ejecución de pasos
# ============================================================


def run_step(command: list[str], step_name: str) -> None:
    log(f"Iniciando {step_name}")
    log(" ".join(command))

    result = subprocess.run(
        command,
        cwd=BASE_DIR,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Falló {step_name} con código {result.returncode}"
        )

    log(f"{step_name} finalizado OK")


def process_interval(interval: str, state: dict[str, Any]) -> None:
    """
    Procesa un intervalo completo de forma recuperable.
    """
    log(f"Procesando intervalo nuevo o pendiente: {interval}")

    if rgb_exists(interval):
        log(f"RGB ya existe para {interval}. No se repite resampleo.")
    else:
        run_step(
            [
                sys.executable,
                str(PROCESADOR_SCRIPT),
                "--interval",
                interval,
            ],
            f"resampleo + álgebra RGB del intervalo {interval}",
        )

    rgb_path = validate_rgb(interval)
    log(f"RGB validado: {rgb_path}")
    add_to_state_list(state, "processed_intervals", interval)

    # mapa_rgb.py reconstruye el GIF con todos los PNG existentes.
    # Se ejecuta si falta el PNG o si el GIF no existe/está desactualizado.
    if png_exists(interval) and gif_is_current():
        log(
            f"PNG y GIF vigente ya existen para {interval}. "
            "No se repite mapa."
        )
    else:
        run_step(
            [
                sys.executable,
                str(MAPA_SCRIPT),
                "--interval",
                interval,
            ],
            f"mapa + GIF del intervalo {interval}",
        )

    png_path = validate_png(interval)
    gif_path = validate_gif()

    log(f"PNG validado: {png_path}")
    log(f"GIF validado: {gif_path}")

    add_to_state_list(state, "mapped_intervals", interval)
    clear_failure_state(state, interval)

    log(f"Intervalo {interval} completado.")


# ============================================================
# Descarga
# ============================================================


def launch_downloader() -> subprocess.Popen[Any]:
    log("Lanzando descarga en segundo plano...")

    process = subprocess.Popen(
        [sys.executable, str(DESCARGA_SCRIPT)],
        cwd=BASE_DIR,
    )

    log(f"Descarga iniciada con PID {process.pid}")
    return process


def stop_process(process: subprocess.Popen[Any] | None) -> None:
    if process is None or process.poll() is not None:
        return

    log("Deteniendo proceso de descarga...")

    try:
        process.send_signal(signal.SIGINT)
        process.wait(timeout=10)
        return
    except subprocess.TimeoutExpired:
        log("La descarga no respondió a SIGINT. Se envía terminate().")
    except OSError:
        return

    try:
        process.terminate()
        process.wait(timeout=5)
        return
    except subprocess.TimeoutExpired:
        log("La descarga no respondió a terminate(). Se envía kill().")
    except OSError:
        return

    try:
        process.kill()
        process.wait(timeout=5)
    except OSError:
        pass


def downloader_status(
    process: subprocess.Popen[Any] | None,
) -> tuple[bool, int | None]:
    """
    Retorna:
        terminado, código_de_salida
    """
    if process is None:
        return True, 0

    returncode = process.poll()
    return returncode is not None, returncode


# ============================================================
# Selección y reintentos
# ============================================================


def retry_exhausted(
    interval: str,
    state: dict[str, Any],
    max_retries: int,
) -> bool:
    return int(state["retry_counts"].get(interval, 0)) >= max_retries


def select_next_interval(
    ready_intervals: list[str],
    state: dict[str, Any],
    max_retries: int,
) -> str | None:
    """
    Prioriza completar productos parciales antes de iniciar nuevos RGB.
    """
    candidates = [
        interval
        for interval in ready_intervals
        if not retry_exhausted(interval, state, max_retries)
    ]

    # Prioridad 1: ya tiene RGB; falta PNG o actualizar GIF.
    for interval in candidates:
        if rgb_exists(interval) and (
            not png_exists(interval) or not gif_is_current()
        ):
            return interval

    # Prioridad 2: falta la etapa RGB.
    for interval in candidates:
        if not rgb_exists(interval):
            return interval

    return None


def get_unresolved_failures(
    state: dict[str, Any],
    max_retries: int,
) -> list[str]:
    return sorted(
        [
            interval
            for interval in state["failed_intervals"]
            if int(state["retry_counts"].get(interval, 0)) >= max_retries
        ]
    )


# ============================================================
# Main
# ============================================================


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Pipeline P3 MDTS: descarga, detección de carpetas completas, "
            "resampleo, álgebra RGB, mapa y GIF."
        )
    )

    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="No lanza la descarga. Procesa carpetas ya existentes.",
    )

    parser.add_argument(
        "--poll-seconds",
        type=float,
        default=10.0,
        help="Segundos entre revisiones cuando no hay trabajo listo.",
    )

    parser.add_argument(
        "--stability-seconds",
        type=float,
        default=3.0,
        help="Segundos usados para comprobar que una carpeta dejó de cambiar.",
    )

    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="Cantidad máxima de intentos automáticos por intervalo.",
    )

    parser.add_argument(
        "--retry-delay",
        type=float,
        default=5.0,
        help="Espera después de un fallo antes de continuar.",
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help="Procesa como máximo un intervalo y termina.",
    )

    parser.add_argument(
        "--reset-state",
        action="store_true",
        help="Elimina pipeline_state.json antes de iniciar.",
    )

    return parser


def validate_args(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> None:
    if args.poll_seconds <= 0:
        parser.error("--poll-seconds debe ser mayor que cero.")

    if args.stability_seconds < 0:
        parser.error("--stability-seconds no puede ser negativo.")

    if args.max_retries < 1:
        parser.error("--max-retries debe ser al menos 1.")

    if args.retry_delay < 0:
        parser.error("--retry-delay no puede ser negativo.")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    validate_args(parser, args)

    validate_project_structure()

    if args.reset_state and STATE_PATH.exists():
        STATE_PATH.unlink()
        log("Estado anterior eliminado.")

    state = load_state()
    downloader_process: subprocess.Popen[Any] | None = None

    try:
        if not args.skip_download:
            downloader_process = launch_downloader()
        else:
            log("Descarga omitida por parámetro --skip-download.")

        while True:
            state = load_state()

            ready_intervals = get_complete_intervals_ready(
                skip_stability=args.skip_download,
                stability_seconds=args.stability_seconds,
                state=state,
            )

            if ready_intervals:
                log(f"Intervalos completos listos: {ready_intervals}")
            else:
                log("No hay intervalos completos nuevos por ahora.")

            interval_to_process = select_next_interval(
                ready_intervals,
                state,
                args.max_retries,
            )

            if interval_to_process is not None:
                try:
                    process_interval(interval_to_process, state)

                except Exception as error:
                    state = load_state()
                    attempt = register_failure(
                        state,
                        interval_to_process,
                        error,
                    )

                    log(
                        f"ERROR procesando {interval_to_process} "
                        f"(intento {attempt}/{args.max_retries}): {error}"
                    )

                    if attempt >= args.max_retries:
                        log(
                            f"{interval_to_process} alcanzó el máximo de "
                            "reintentos. Se continuará con otros intervalos."
                        )

                    if args.retry_delay > 0:
                        time.sleep(args.retry_delay)

                print_status(load_state(), args.max_retries)

                if args.once:
                    log("Modo --once activo. Finalizando.")
                    break

                # Si hay más intervalos listos, se revisan inmediatamente.
                continue

            log("No hay intervalos pendientes que puedan procesarse ahora.")
            print_status(load_state(), args.max_retries)

            if args.once:
                log("Modo --once activo. Finalizando.")
                break

            download_done, download_returncode = downloader_status(
                downloader_process
            )

            if download_done:
                if download_returncode not in (None, 0):
                    log(
                        "ERROR: la descarga terminó con código "
                        f"{download_returncode}."
                    )
                    return 1

                unresolved = get_unresolved_failures(
                    load_state(),
                    args.max_retries,
                )

                if unresolved:
                    log(
                        "La descarga terminó, pero quedaron intervalos "
                        f"fallidos sin resolver: {unresolved}"
                    )
                    return 2

                log(
                    "La descarga terminó y no quedan intervalos pendientes. "
                    "Pipeline completado."
                )
                break

            log(f"Esperando {args.poll_seconds} segundos...")
            time.sleep(args.poll_seconds)

    except KeyboardInterrupt:
        log("Interrupción manual recibida.")
        return 130

    finally:
        stop_process(downloader_process)
        log("Pipeline finalizado.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
