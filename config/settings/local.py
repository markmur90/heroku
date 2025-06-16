# from config.settings.configuración_dinamica import OAUTH2
from .base1 import *

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Configuraciones específicas del entorno local
USE_OAUTH2_UI = True

REDIRECT_URI = os.getenv("REDIRECT_URI", "https://api.coretransapi.com/oauth2/callback/")
ORIGIN = os.getenv("ORIGIN", "https://api.coretransapi..com")

OAUTH2.update({
    "REDIRECT_URI": REDIRECT_URI,
    "ORIGIN": ORIGIN,
})

SIMULADOR_SECRET_KEY = "la_clave_del_simulador"  # O desde un .env
