import requests
from config import settings

def get_simulator_token(username: str, password: str) -> str:
    url = settings.TOKEN_ENDPOINT
    payload = {"username": username, "password": password}
    resp = requests.post(url, json=payload, headers={"Content-Type":"application/json"})
    resp.raise_for_status()
    return resp.json().get("token")
