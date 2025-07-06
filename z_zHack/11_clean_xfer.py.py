import requests
import uuid
from datetime import datetime

# === URLs ===
login_url = "http://80.78.30.242:9181/api/login/"
transfer_url = "http://80.78.30.242:9181/api/send-transfer"

# === Datos reales desde la cuenta interna ===
session = requests.Session()
session.headers.update({
    "Host": "80.78.30.242",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0 (InternalBrowser)",
    "Accept": "text/xml,application/xml,application/xhtml+xml,application/json",
    "Accept-Language": "es-ES;q=0.9,en;q=0.8",
    "X-Origin-IP": "192.68.1.10",
    "X-Location": "OFICINA-CENTRAL-ES",
    "X-Requested-With": "XMLHttpRequest",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
})

# === Paso 1: Login JWT desde Django interno ===
session.post(login_url, json={
    "username": "markmur88",
    "password": "Ptf8454Jd55"
})

# === Paso 2: Cargar token desde header o desde cookie de sesión Django ===
jwt_token = session.cookies.get("sessionid") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx"
session.headers.update({
    "Authorization": f"Bearer {jwt_token}",
    "X-Session-Token": jwt_token,
})

# === Paso 3: Generar payment_id único ===
payment_id = str(uuid.uuid4())

# === Datos de transferencia ajustados a campos ORM válidos ===
transfer_data = {
    # Campos obligatorios ORM
    "payment_id": payment_id,

    "debtor_account_id": 1,
    "creditor_account_id": 2,

    "instructed_amount": "100.00",
    "currency": "EUR",
    "requested_execution_date": datetime.today().strftime("%Y-%m-%d"),

    "remittance_information_unstructured": "Operación entre cuentas internas autorizada",
    "status": "PDNG",  # Pendiente hasta que el backend lo actualice
    
    "purpose_code": "GDSV",  # Si lo validan
    "payment_identification": {
        "instruction_id": f"INST-{payment_id}",
        "end_to_end_id": f"E2E-{payment_id}"
    }
}

# === Enviar la transferencia desde sesión completa ===
response = session.post(transfer_url, json=transfer_data)

print("[+] Resultado de transferencia final:")
print("Status:", response.status_code)
print("Respuesta del sistema:", response.text)

if response.status_code == 201:
    print("\n[+] 💸 ¡Transferencia SEPA ejecutada con éxito!")
elif response.status_code == 403:
    print("\n[-] ¡Token de sesión no aceptado!")
elif response.status_code == 400:
    print("\n[-] Campos inválidos. ¿La API espera otro formato exacto y realista?")