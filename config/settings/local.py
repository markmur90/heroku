from .base1 import *
from pathlib import Path
import os

# Cargamos primero el .env local
from dotenv import load_dotenv
load_dotenv(Path(BASE_DIR) / '.env.local')

# …tu configuración existente…
USE_OAUTH2_UI = True

# La clave del simulador ya se carga en ``base1`` mediante ``env_vars``