import os
from netCDF4 import Dataset

def inspect_nc_file(file_path):
    try:
        print(f"\n=== Inspeccionando archivo: {file_path} ===")
        dataset = Dataset(file_path, 'r')
        print("Dimensiones:")
        for dim_name, dim in dataset.dimensions.items():
            print(f"  {dim_name}: {len(dim)}")

        print("\nVariables:")
        for var_name, var in dataset.variables.items():
            print(f"  {var_name}: {var.dimensions}")
            for attr_name in var.ncattrs():
                print(f"    - {attr_name}: {getattr(var, attr_name)}")

        print("\nAtributos globales:")
        for attr_name in dataset.ncattrs():
            print(f"  {attr_name}: {getattr(dataset, attr_name)}")

        dataset.close()
    except Exception as e:
        print(f"Error al inspeccionar el archivo {file_path}: {e}")

if __name__ == "__main__":
    # Cambia esta ruta al directorio que contiene tus archivos NetCDF
    nc_directory = "/home/usuario/Escritorio/P3_TS/1_descarga/data"
    for root, _, files in os.walk(nc_directory):
        for file in files:
            if file.endswith(".nc"):
                file_path = os.path.join(root, file)
                inspect_nc_file(file_path)
