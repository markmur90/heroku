# from config.settings.configuración_dinamica import OAUTH2
from .base1 import *

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

USE_X_FORWARDED_HOST = True

# Configuraciones específicas del entorno local
USE_OAUTH2_UI = True

REDIRECT_URI = os.getenv("REDIRECT_URI", "https://api.coretransapi.com/oauth2/callback/")
ORIGIN = os.getenv("ORIGIN", "https://api.coretransapi..com")

OAUTH2.update({
    "REDIRECT_URI": REDIRECT_URI,
    "ORIGIN": ORIGIN,
})

# DATABASE_URL="postgres://u22qfesn1ol61g:p633435fd268a16298ff6b2b83e47e7091ae5cb79d80ad13e03a6aff1262cc2ae@c7pvjrnjs0e7al.cluster-czz5s0kz4scl.eu-west-1.rds.amazonaws.com:5432/ddo6kmmjfftuav"

DATABASE_URL="postgres://markmur88:Ptf8454Jd55@localhost:5432/mydatabase"

SIMULADOR_SECRET_KEY = "la_clave_del_simulador"  # O desde un .env
