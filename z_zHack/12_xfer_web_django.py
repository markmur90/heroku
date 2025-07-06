import requests

# === URLs ===
login_web_url = "http://80.78.30.242:9181"  # Web interna de login
transferencia_web_url = "http://80.78.30.242:9181/api/transferencia"

# Credenciales
auth_data = {
    "username": "markmur88",
    "password": "Ptf8454Jd55"
}

# === Sesión desde navegador interno del banco ===
session = requests.Session()
session.headers.update({
    "Host": "80.78.30.242",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0 (InternalBrowser)",
    "Accept": "text/xml,application/xml,application/xhtml+xml,text/html",
    "Accept-Language": "es-ES;q=0.9,en-US;q=0.8",
    "X-Origin-IP": "192.168.1.10",
    "X-Location": "OFICINA-ES-MADRID",
    "X-Session-Type": "BANCO-INTERNAL",
})

# === Paso 1: Acceder a web interna del gerente para obtener csrftoken ===
web_login = session.get(login_web_url, allow_redirects=False)
cookies = session.cookies.get_dict()
print("Cookies tras GET interno:", cookies)
csrftoken = cookies.get("csrftoken", "dummycsrf")

# === Paso 2: Iniciar sesión vía web (no solo API), esto activa sessionid ===
login_response = session.post(login_web_url, data=auth_data)

# Ver cookies tras login vía web
print("Cookies tras login web:", session.cookies.get_dict())

# === Paso 3: Enviar transferencia con sesión Django web real ===
if "sessionid" in session.cookies.get_dict():
    session.headers.update({
        "Referer": "http://80.78.30.242:9181/api/login",
        "X-CSRFToken": csrftoken,
        "Cookie": f"sessionid={session.cookies.get('sessionid')}; csrftoken={csrftoken}"
    })

    transfer_data = {
        "debtor_account": 1,  # ID interno de cuenta del banco (obligatorio)
        "creditor_account": 1,
        "instructed_amount": "120.00",
        "currency": "EUR",
        "requested_execution_date": "2025-07-06",
        "remittance_information_unstructured": "PAGO-PROVEEDOR",
        "status": "PDNG"
    }

    transfer_response = session.post(transferencia_web_url, data=transfer_data)
    print("Estado:", transfer_response.status_code)
    print("Respuesta:", transfer_response.text)
else:
    print("[-] No hay sessionid. No estamos dentro del stack web del banco.")