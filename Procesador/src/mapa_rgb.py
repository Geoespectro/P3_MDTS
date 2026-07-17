import argparse
import glob
import json
import logging
import os
from datetime import datetime

import matplotlib
import numpy as np
import xarray as xr

matplotlib.use("Agg")

import cartopy
import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


PROCESSOR_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_PATH = os.path.join(
    PROCESSOR_DIR,
    "data",
    "conf",
    "config_mapa.json",
)


def load_config(config_path):
    """
    Lee el archivo JSON de configuración del mapa.
    """
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_directory(path):
    """
    Crea un directorio si no existe.
    """
    os.makedirs(path, exist_ok=True)


def get_rgb_files(input_rgb_base_dir, target_interval=None):
    """
    Obtiene los archivos RGB NetCDF disponibles.

    Si target_interval tiene un valor, busca únicamente ese intervalo.
    """
    if target_interval:
        pattern = os.path.join(
            input_rgb_base_dir,
            target_interval,
            f"{target_interval}_rgb_result.nc",
        )
    else:
        pattern = os.path.join(input_rgb_base_dir, "*", "*_rgb_result.nc")

    return sorted(glob.glob(pattern))


def get_crop_indexes(ds, conf):
    """
    Calcula los índices de recorte usando la lógica de P1/P2.

    Importante:
    - Para recortar la imagen se usan los deltas.
    - Para dibujar el mapa se usa el extent base de Argentina/Sudamérica.

    Esto evita que el mapa del P3 quede visualmente más amplio y con el
    continente más chico.
    """
    grids_dir = conf["grids_dir"]

    lons_path = os.path.join(grids_dir, "g16_lons_8km.txt")
    lats_path = os.path.join(grids_dir, "g16_lats_8km.txt")

    if not os.path.exists(lons_path):
        raise FileNotFoundError(f"No se encontró la grilla de longitudes: {lons_path}")

    if not os.path.exists(lats_path):
        raise FileNotFoundError(f"No se encontró la grilla de latitudes: {lats_path}")

    lons = np.loadtxt(lons_path)
    lats = np.loadtxt(lats_path)

    if lons.shape != lats.shape:
        raise ValueError(
            "Las grillas de latitud y longitud no tienen la misma dimensión: "
            f"lons={lons.shape}, lats={lats.shape}"
        )

    if lons.ndim != 2 or lats.ndim != 2:
        raise ValueError("Las grillas auxiliares deben ser matrices bidimensionales.")

    region = conf.get("region", "ARG")

    if region == "ARG":
        map_min_lon = conf["argentina_lon_W"]
        map_max_lon = conf["argentina_lon_E"]
        map_min_lat = conf["argentina_lat_S"]
        map_max_lat = conf["argentina_lat_N"]

        min_lon = map_min_lon + conf["delta_lon_W_for_graph"]
        max_lon = map_max_lon
        min_lat = map_min_lat + conf["delta_lat_S_for_graph"]
        max_lat = map_max_lat + conf["delta_lat_N_for_graph"]

    elif region == "SuA":
        map_min_lon = conf["sudamerica_lon_W"]
        map_max_lon = conf["sudamerica_lon_E"]
        map_min_lat = conf["sudamerica_lat_S"]
        map_max_lat = conf["sudamerica_lat_N"]

        min_lon = map_min_lon
        max_lon = map_max_lon
        min_lat = map_min_lat
        max_lat = map_max_lat

    else:
        raise ValueError("Región no soportada. Usar ARG o SuA.")

    spatial_resolution = ds.attrs.get("spatial_resolution", "2km at nadir")

    try:
        band_resolution_km = float(str(spatial_resolution).split("km")[0])
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "No se pudo interpretar el atributo spatial_resolution: "
            f"{spatial_resolution}"
        ) from exc

    if band_resolution_km <= 0:
        raise ValueError(f"Resolución espacial inválida: {band_resolution_km} km")

    ref_grid_resolution_km = 8
    frac = int(ref_grid_resolution_km / band_resolution_km)

    if frac <= 0:
        raise ValueError(
            "La relación entre la grilla auxiliar y la resolución del RGB "
            f"no es válida: {ref_grid_resolution_km}/{band_resolution_km}"
        )

    half = int(lons.shape[0] / 2)

    min_lon_idx = np.abs(lons - min_lon)[half, :].argmin()
    max_lon_idx = np.abs(lons - max_lon)[half, :].argmin()
    max_lat_idx = np.abs(lats - min_lat)[:, half].argmin()
    min_lat_idx = np.abs(lats - max_lat)[:, half].argmin()

    min_lon_idx *= frac
    max_lon_idx *= frac
    min_lat_idx *= frac
    max_lat_idx *= frac

    x_size = ds.sizes["x"]
    y_size = ds.sizes["y"]

    if not 0 <= min_lon_idx < max_lon_idx <= x_size:
        raise ValueError(
            "Índices longitudinales de recorte inválidos: "
            f"{min_lon_idx}:{max_lon_idx}, tamaño x={x_size}"
        )

    if not 0 <= min_lat_idx < max_lat_idx <= y_size:
        raise ValueError(
            "Índices latitudinales de recorte inválidos: "
            f"{min_lat_idx}:{max_lat_idx}, tamaño y={y_size}"
        )

    sat_h = ds["goes_imager_projection"].perspective_point_height

    x = ds["x"].values[min_lon_idx:max_lon_idx] * sat_h
    y = ds["y"].values[min_lat_idx:max_lat_idx] * sat_h

    if x.size == 0 or y.size == 0:
        raise ValueError(
            "El recorte calculado quedó vacío. Revisar límites y deltas del mapa."
        )

    img_extent = (x.min(), x.max(), y.min(), y.max())
    img_indexes = [min_lon_idx, max_lon_idx, min_lat_idx, max_lat_idx]

    map_extent = [map_min_lon, map_max_lon, map_min_lat, map_max_lat]

    return img_extent, img_indexes, map_extent


def get_plot_object(conf, map_extent):
    """
    Crea el mapa con estilo similar a P1/P2:
    costa, grilla, límites internacionales y límites provinciales.
    """
    shp_dir = conf["shp_dir"]

    cartopy.config["pre_existing_data_dir"] = shp_dir

    ax = plt.axes(projection=ccrs.PlateCarree())

    map_extent = [
        map_extent[0],
        map_extent[1],
        map_extent[2] - 1.0,
        map_extent[3],
    ]

    ax.set_extent(map_extent, ccrs.PlateCarree())  # type: ignore[attr-defined]

    ax.coastlines(  # type: ignore[attr-defined]
        "10m",
        lw=conf.get("line_width_inches_for_coast", 0.2),
        color="black",
    )

    grid_step = conf.get("grid_step_degrees", 10.0)

    if grid_step <= 0:
        raise ValueError("'grid_step_degrees' debe ser mayor que cero.")

    xlocs = np.arange(
        np.floor(map_extent[0] / grid_step) * grid_step,
        np.ceil(map_extent[1] / grid_step) * grid_step + grid_step,
        grid_step,
    )

    ylocs = np.arange(
        np.floor(map_extent[2] / grid_step) * grid_step,
        np.ceil(map_extent[3] / grid_step) * grid_step + grid_step,
        grid_step,
    )

    gl = ax.gridlines(  # type: ignore[attr-defined]
        xlocs=xlocs,
        ylocs=ylocs,
        linestyle="--",
        color="black",
        draw_labels=True,
        linewidth=conf.get("line_width_inches_for_gridlines", 0.3),
    )

    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {"size": 4}
    gl.ylabel_style = {"size": 4}

    shp_internacional = os.path.join(
        shp_dir,
        "limite_internacional2",
        "ne_10m_admin_0_map_units_PLATE.shp",
    )

    shp_provincial = os.path.join(
        shp_dir,
        "limite_interprovincial2",
        "008b_limites_provinciales_linea_PLATE.shp",
    )

    if os.path.exists(shp_internacional):
        paises = list(shpreader.Reader(shp_internacional).geometries())
        for pais in paises:
            ax.add_geometries(  # type: ignore[attr-defined]
                [pais],
                ccrs.PlateCarree(),
                edgecolor="black",
                facecolor="none",
                linewidth=conf.get(
                    "line_width_inches_for_nation_limits",
                    0.2,
                ),
            )
    else:
        logging.warning(
            "No se encontró shapefile internacional: %s",
            shp_internacional,
        )

    if os.path.exists(shp_provincial):
        provincias = list(shpreader.Reader(shp_provincial).geometries())
        for provincia in provincias:
            ax.add_geometries(  # type: ignore[attr-defined]
                [provincia],
                ccrs.PlateCarree(),
                edgecolor="black",
                facecolor="none",
                linewidth=conf.get(
                    "line_width_inches_for_province_limits",
                    0.3,
                ),
            )
    else:
        logging.warning(
            "No se encontró shapefile provincial: %s",
            shp_provincial,
        )

    return ax


def add_image_foot(ax, title, institution=None, size=8.0):
    """
    Añade la banda blanca superior con el título.
    """
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    width = xlim[1] - xlim[0]

    # Franja superior un poco más alta para contener correctamente el logo.
    banner_height = 0.065 * (ylim[1] - ylim[0])

    ax.add_patch(
        Rectangle(
            (xlim[0], ylim[1] - banner_height),
            width,
            banner_height,
            alpha=1,
            zorder=20,
            facecolor="white",
            edgecolor="none",
        )
    )

    ax.text(
        xlim[0] + 0.002 * width,
        ylim[1] - banner_height / 1.55,
        title,
        horizontalalignment="left",
        verticalalignment="center",
        color="black",
        size=size,
        zorder=21,
    )

    if institution:
        ax.text(
            xlim[1] - 0.05 * width,
            ylim[1] - banner_height / 2,
            institution,
            horizontalalignment="right",
            verticalalignment="center",
            color="black",
            size=size,
            zorder=21,
        )


def add_logo(ax, logo_path):
    """
    Añade el logo dentro de la franja blanca superior.
    """
    if not os.path.exists(logo_path):
        logging.warning("No se encontró logo: %s", logo_path)
        return

    logo_img = plt.imread(logo_path)

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    axis_width = xlim[1] - xlim[0]
    axis_height = ylim[1] - ylim[0]

    banner_height = 0.065 * axis_height

    # El logo ocupa como máximo el 8 % del ancho del mapa.
    logo_width = 0.08 * axis_width
    logo_height = logo_width * logo_img.shape[0] / logo_img.shape[1]

    # Evita que el logo sea más alto que la franja blanca.
    max_logo_height = 0.80 * banner_height

    if logo_height > max_logo_height:
        logo_height = max_logo_height
        logo_width = logo_height * logo_img.shape[1] / logo_img.shape[0]

    right_margin = 0.01 * axis_width

    logo_x = xlim[1] - right_margin - logo_width

    # Centrado vertical dentro de la franja.
    banner_bottom = ylim[1] - banner_height
    logo_y = banner_bottom + (banner_height - logo_height) / 2

    ax.imshow(
        logo_img,
        extent=(
            logo_x,
            logo_x + logo_width,
            logo_y,
            logo_y + logo_height,
        ),
        aspect="auto",
        zorder=25,
    )

def safe_rgb(red, green, blue):
    """
    Asegura que los canales queden en rango 0-1 y reemplaza valores inválidos.
    """
    red = np.nan_to_num(red, nan=0.0, posinf=1.0, neginf=0.0)
    green = np.nan_to_num(green, nan=0.0, posinf=1.0, neginf=0.0)
    blue = np.nan_to_num(blue, nan=0.0, posinf=1.0, neginf=0.0)

    red = np.clip(red, 0.0, 1.0)
    green = np.clip(green, 0.0, 1.0)
    blue = np.clip(blue, 0.0, 1.0)

    return np.dstack((red, green, blue))


def get_timestamp_label(ds, interval_name):
    """
    Intenta obtener fecha/hora desde atributos GOES.
    Si no puede, usa el nombre del intervalo.
    """
    timestamp = ds.attrs.get("time_coverage_start")

    if not timestamp:
        return interval_name

    try:
        if "." in timestamp:
            timestamp = timestamp.split(".")[0] + "Z"

        return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").strftime(
            "%d/%m/%Y - %H:%M UTC"
        )
    except (TypeError, ValueError):
        return interval_name


def build_output_name(conf, interval_name):
    """
    Construye el nombre del archivo PNG de salida.
    """
    prefix = conf.get("output_prefix", "CONAE_PRD_GOES16_ABI_MDTS_RGB")
    return f"{prefix}_{interval_name}.png"


def get_existing_pngs(conf):
    """
    Obtiene todos los PNG existentes en el directorio configurado.
    """
    output_png_dir = conf["output_png_dir"]
    pattern = os.path.join(output_png_dir, "*.png")
    return sorted(glob.glob(pattern))


def process_rgb_file(rgb_file, conf):
    """
    Genera un mapa PNG a partir de un RGB NetCDF georreferenciado.
    """
    logging.info("Procesando RGB: %s", rgb_file)

    ds = xr.open_dataset(rgb_file)
    fig = None

    try:
        required_vars = [
            "Red",
            "Green",
            "Blue",
            "x",
            "y",
            "goes_imager_projection",
        ]

        for var in required_vars:
            if var not in ds.variables and var not in ds.coords:
                raise ValueError(
                    f"El archivo no contiene la variable/coordenada requerida: {var}"
                )

        interval_name = ds.attrs.get(
            "interval_name",
            os.path.basename(os.path.dirname(rgb_file)),
        )

        img_extent, img_indexes, map_extent = get_crop_indexes(ds, conf)

        min_lon_idx, max_lon_idx, min_lat_idx, max_lat_idx = img_indexes

        red = ds["Red"].values[
            min_lat_idx:max_lat_idx,
            min_lon_idx:max_lon_idx,
        ]
        green = ds["Green"].values[
            min_lat_idx:max_lat_idx,
            min_lon_idx:max_lon_idx,
        ]
        blue = ds["Blue"].values[
            min_lat_idx:max_lat_idx,
            min_lon_idx:max_lon_idx,
        ]

        if red.size == 0 or green.size == 0 or blue.size == 0:
            raise ValueError(
                "Uno o más canales RGB quedaron vacíos después del recorte."
            )

        if not (red.shape == green.shape == blue.shape):
            raise ValueError(
                "Los canales RGB no tienen las mismas dimensiones después "
                f"del recorte: R={red.shape}, G={green.shape}, B={blue.shape}"
            )

        rgb_image = safe_rgb(red, green, blue)

        projection = ds["goes_imager_projection"]

        sat_crs = ccrs.Geostationary(
            central_longitude=projection.longitude_of_projection_origin,
            satellite_height=projection.perspective_point_height,
        )

        dpi = conf.get("figure_resolution_dpi", 200)
        fig_width = conf.get("figure_length_inches", 8)
        fig_height = conf.get("figure_high_inches", 5)

        fig = plt.figure(clear=True)
        fig.set_size_inches(fig_width, fig_height)

        ax = get_plot_object(conf, map_extent)

        ax.imshow(
            rgb_image,
            transform=sat_crs,
            extent=img_extent,
            origin="upper",
            aspect="auto",
        )

        timestamp_label = get_timestamp_label(ds, interval_name)

        title = (
            f"{conf.get('map_title', 'GOES-16 ABI - MDTS RGB')} - " f"{timestamp_label}"
        )

        add_image_foot(
            ax,
            title,
            size=conf.get("font_size_title", 8.0),
        )

        add_logo(ax, conf["logo_path"])

        output_png_dir = conf["output_png_dir"]
        ensure_directory(output_png_dir)

        output_name = build_output_name(conf, interval_name)
        output_path = os.path.join(output_png_dir, output_name)

        # Igual que P1/P2: sin bbox_inches="tight" para no alterar proporciones.
        fig.savefig(output_path, dpi=dpi)

        logging.info("PNG generado: %s", output_path)

        return output_path

    finally:
        if fig is not None:
            plt.close(fig)

        ds.close()


def build_gif(image_paths, conf):
    """
    Genera o reconstruye el GIF usando los PNG recibidos.
    """
    if not image_paths:
        logging.warning("No hay imágenes PNG para generar GIF.")
        return None

    output_gif_dir = conf["output_gif_dir"]
    ensure_directory(output_gif_dir)

    gif_path = os.path.join(output_gif_dir, conf["gif_filename"])

    frame_duration = conf.get("gif_frame_duration", 0.7)

    if frame_duration <= 0:
        raise ValueError("'gif_frame_duration' debe ser mayor que cero.")

    frame_duration_ms = int(frame_duration * 1000)

    frames = []

    try:
        for image_path in image_paths:
            with Image.open(image_path) as image:
                frames.append(image.convert("RGB").copy())

        frames[0].save(
            gif_path,
            save_all=True,
            append_images=frames[1:],
            duration=frame_duration_ms,
            loop=0,
        )

    finally:
        for frame in frames:
            frame.close()

    logging.info("GIF generado: %s", gif_path)

    return gif_path


def main():
    parser = argparse.ArgumentParser(
        description="Generador de mapa y GIF para RGB georreferenciado P3 MDTS."
    )

    parser.add_argument(
        "--interval",
        type=str,
        default=None,
        help="Nombre del intervalo a mapear. Ejemplo: 2024-12-06_2300",
    )

    args = parser.parse_args()

    conf = load_config(CONFIG_PATH)

    ensure_directory(conf["output_png_dir"])
    ensure_directory(conf["output_gif_dir"])

    rgb_files = get_rgb_files(
        conf["input_rgb_base_dir"],
        target_interval=args.interval,
    )

    if not rgb_files:
        if args.interval:
            logging.warning(
                "No se encontró RGB para el intervalo %s en %s",
                args.interval,
                conf["input_rgb_base_dir"],
            )
            return 1
        else:
            logging.warning(
                "No se encontraron RGB en: %s",
                conf["input_rgb_base_dir"],
            )
            return 0

    if args.interval:
        logging.info(
            "Procesando mapa solo para intervalo: %s",
            args.interval,
        )
    else:
        logging.info("RGB encontrados: %s", len(rgb_files))

    generated_pngs = []
    had_errors = False

    for rgb_file in rgb_files:
        try:
            png_path = process_rgb_file(rgb_file, conf)
            generated_pngs.append(png_path)
        except Exception as e:
            had_errors = True
            logging.error("Error procesando %s: %s", rgb_file, e)

    all_pngs = get_existing_pngs(conf)

    if not all_pngs:
        all_pngs = sorted(generated_pngs)

    build_gif(all_pngs, conf)

    logging.info("Proceso de mapa y GIF finalizado.")
    return 1 if had_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
