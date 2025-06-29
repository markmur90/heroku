# api/utils/jwt_simulador.py
import jwt
import datetime
from django.conf import settings

def generar_token_simulador(username='493069k1'):
    now = datetime.datetime.utcnow()
    payload = {
        "username": username,
        "exp": now + datetime.timedelta(hours=1),
        "iat": now
    }
    secret_key = settings.SIMULADOR_SECRET_KEY
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token
