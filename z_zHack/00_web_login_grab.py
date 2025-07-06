import requests
from bs4 import BeautifulSoup

# === URLs ===
LOGIN_WEB = "http://80.78.30.242:9181"  # Web interna donde se carga el login
TOKEN_ENDPOINT = "http://80.78.30.242:9181/api/login/"  # Endpoint de login de API

# === Credenciales ===
USERNAME = "493069k1"
PASSWORD = "bar1588623"

# === Headers internos ===
session = requests.Session()
session.headers.update({
    "Host": "api.coretransapi.com",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0 (InternalBrowser)",
    "Accept": "text/xml,application/xml,application/xhtml+xml,text/html,application/json",
    "Accept-Language": "es-ES,es;q=0.8,en;q=0.5",
    "Referer": "http://80.78.30.242:9181", 
    "X-Origin-IP": "192.168.1.10",
    "X-Forwarded-For": "192.168.1.10",
    "X-Location": "OFICINA-CENTRAL-ES-9181",
    "X-Requested-With": "XMLHttpRequest",
    "Accept-Encoding": "gzip, deflate",
    "Sec-Ch-Ua": '"Google Chrome";v="115", "Not=A?Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Linux"'
})

# === Paso 1: Obtener csrftoken desde web interna (DEBUG=on) ===
login_web_response = session.get(LOGIN_WEB)
csrftoken = session.cookies.get("csrftoken")

if not csrftoken:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(login_web_response.text, "html.parser")
        csrf_input = soup.find("input", {"name": "csrfmiddlewaretoken"})
        if csrf_input:
            csrftoken = csrf_input.get("value")
            print("[+] Token CSRF obtenido desde el formulario interno:", csrftoken)
        else:
            print("[-] Token CSRF no encontrado en HTML ni en cookies. Probando con token dummy.")
            csrftoken = "dummycsrf"
    except:
        csrftoken = "dummycsrf"
else:
    print("[+] Token CSRF desde cookie:", csrftoken)

# === Paso 2: Login con headers == gerente real ===
session.post(TOKEN_ENDPOINT, data={
    "username": USERNAME,
    "password": PASSWORD,
    "csrfmiddlewaretoken": csrftoken,
})

print("Cookies tras login:", session.cookies.get_dict())