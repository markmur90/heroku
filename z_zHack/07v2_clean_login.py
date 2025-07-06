import requests

# === HOST ===
base_url = "http://80.78.30.242:9181"
login_url = f"{base_url}/api/login/"

# === Credenciales ===
USERNAME = "markmur88"
PASSWORD = "Ptf8454Jd55"

# === Headers internos del gerente ===
headers = {
    "Host": "80.78.30.242",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0 (InternalBrowser)",
    "Accept": "application/json,text/xml;q=0.9",
    "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Content-Type": "application/json",
    "X-Origin-IP": "192.168.1.10",     # Usado como seguridad por IP origen interna
    "X-Location": "OFICINA-CENTRAL-ES" # Verificación de geolocalización interna
}

# === Realizar login y obtener token ===
session = requests.Session()
session.headers.update(headers)

payload = {
    "username": USERNAME,
    "password": PASSWORD,
}

token_response = session.post(login_url, json=payload)
token_json = token_response.json()

if token_response.status_code == 200:
    access_token = token_json.get("token")
    print("[+] ¡Login exitoso! Token JWT obtenido:")
    print(access_token)
    print("Guardado en archivo interno_token.txt")

    with open("interno_token.txt", "w") as tokfile:
        tokfile.write(access_token)
else:
    print("[-] Hubo un error en el login.")
    print(token_response.status_code)
    print(token_response.text)