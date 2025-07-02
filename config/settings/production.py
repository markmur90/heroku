from .base1 import *
from pathlib import Path
import os

# Cargamos primero el .env production
from dotenv import load_dotenv
load_dotenv(Path(BASE_DIR) / '.env.production')

# …tu configuración existente…
USE_OAUTH2_UI = True

# Clave del simulador: ahora **lee** de la variable de entorno
SIMULADOR_SECRET_KEY = os.getenv("SIMULADOR_SECRET_KEY", "")
if not SIMULADOR_SECRET_KEY:
    raise ImproperlyConfigured("Falta SIMULADOR_SECRET_KEY en .env.production")
