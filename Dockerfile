FROM python:3.12-slim

WORKDIR /app

# Dependencias del sistema necesarias para netCDF, cartopy, shapely, pyproj, matplotlib, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    libgeos-dev \
    libproj-dev \
    proj-data \
    proj-bin \
    libnetcdf-dev \
    libhdf5-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "run_all.py"]
