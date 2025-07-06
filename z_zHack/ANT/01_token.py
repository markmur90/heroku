import requests

# Datos del gerente que tienes
username = "493069k1"
password = "bar1588623"

# Endpoint de login de la API del banco
# login_url = "http://80.78.30.242:9181/api/login"
login_url = "http://80.78.30.242:9181"

# Cabecera para fingir que eres un dispositivo interno si hay control por navegador o IP
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; BancoInterno)",
    # "Host": "api.banco.com",
    "Host": "80.78.30.242",
    "Content-Type": "application/json",
    "X-Origin-IP": "192.168.x.x"  # IP interna del banco (o inventamos una si no la tienes)
}

# Datos de autenticación
data = {
    "username": username,
    "password": password
}

# Iniciar sesión y capturar el token o cookie
session = requests.Session()
response = session.post(login_url, json=data, headers=headers)

# Guardar el token o cookie para usar en la transferencia SEPA
if response.status_code == 200:
    print("Login exitoso. Datos de sesión:")
    print("Headers:", response.headers)
    print("Cookies:", session.cookies.get_dict())
    print("Body:", response.text)
else:
    print("Error al loguearse.")
    print("Estado HTTP:", response.status_code)
    print("Respuesta:", response.text)