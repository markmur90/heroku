# api/utils/jwt_simulador.py
import jwt
import requests
import datetime

from config.settings import base1

# def generar_token_simulador(username='493069k1'):
#     now = datetime.datetime.utcnow()
#     payload = {
#         "username": username,
#         "exp": now + datetime.timedelta(hours=1),
#         "iat": now
#     }
#     secret_key = settings.SIMULADOR_SECRET_KEY
#     token = jwt.encode(payload, secret_key, algorithm='HS256')
#     return token

def obtener_token_simulador(username=None, password=None):
    """
    Llama al endpoint /api/login/ del simulador para obtener un JWT válido.
    """
    url = base1.SIMULADOR_LOGIN_URL
    payload = {
        'username': username or base1.SIMULADOR_USERNAME,
        'password': password or base1.SIMULADOR_PASSWORD
    }
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()['token']