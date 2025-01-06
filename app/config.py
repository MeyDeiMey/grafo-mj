# app/config.py

import os

# Obtener la ruta absoluta del directorio actual (app/)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Definir PROJECT_ROOT como el directorio padre de app/
PROJECT_ROOT = os.path.dirname(current_dir)

# Definir las rutas hacia datalake y datamart
DATA_LAKE_PATH = os.path.join(PROJECT_ROOT, "datalake")
DATA_MART_PATH = os.path.join(PROJECT_ROOT, "datamart")