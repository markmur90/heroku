Evaluación del código actual

    En api/gpt4/conexion/conexion_banco.py se observan funciones que replican de forma local servicios del simulador. Por ejemplo, obtener_token_desde_simulador usa ssh_request para generar un token localmente en vez de consumir la ruta oficial del simulador

.

En la vista send_transfer_gateway_view se definen rutas internas para token, challenge y envío de transferencias (bank_sim_token, bank_sim_challenge, etc.) que vuelven a usar esos servicios locales en lugar de las APIs del simulador

.

Los templates hacen llamadas AJAX a estas rutas internas (bank_sim_token, bank_sim_challenge, bank_sim_send_transfer) como se ve en transfer_send_conexion.html

.

Las variables de entorno apuntan a la infraestructura local (IP, puerto y rutas internas) en lugar de usar la URL externa https://simulador.ejemplo.com

    .

Esta combinación implica que la aplicación está recreando parte de la lógica del simulador (token, challenge y envío) en lugar de consumir las rutas oficiales indicadas.

Arquitectura de integración corregida

    Único punto de acceso
    Configurar BASE_URL=https://simulador.ejemplo.com y construir las rutas mediante esa base (TOKEN_PATH, AUTH_PATH, API_PATH). No se debe usar ssh_request ni puertos locales.

    Servicios externos

        /api/token o /oidc/token para obtener JWT.

        /api/challenge o /auth/challenges para solicitar el challenge OTP.

        /api/send-transfer o /payments para enviar la transferencia.

    Modo fake
    La variable ALLOW_FAKE_BANK mantiene un flujo alternativo solo cuando esté habilitado. Si está en True, se podrá seguir utilizando el modo fake (sin llamadas al simulador) para pruebas aisladas.

El diagrama de llamadas quedaría:

Cliente (navegador) → Django (api/gpt4) → Simulador
                             └─ modo fake (sin llamadas) si ALLOW_FAKE_BANK=True

Implementación paso a paso

    Autenticación JWT

def obtener_token():
    url = settings.BASE_URL + settings.TOKEN_PATH  # /api/token u /oidc/token
    data = {'grant_type': 'client_credentials', 'scope': settings.SCOPE}
    resp = requests.post(url, data=data, auth=(settings.CLIENT_ID, settings.CLIENT_SECRET),
                         timeout=settings.TIMEOUT_REQUEST)
    resp.raise_for_status()
    return resp.json()['access_token']

Challenge OTP

def crear_challenge(payment_id, token):
    url = settings.BASE_URL + settings.AUTH_PATH  # /api/challenge
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    body = {'payment_id': payment_id}
    r = requests.post(url, json=body, headers=headers, timeout=settings.TIMEOUT_REQUEST)
    r.raise_for_status()
    data = r.json()
    return data['challenge_id'], data['otp']       # OTP en respuesta 202

Transferencia

    def enviar_transferencia(transfer, token, otp, totp):
        url = settings.BASE_URL + settings.API_PATH   # /payments o /api/send-transfer
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Otp': otp,
            'Totp': totp,
            'Idempotency-Id': transfer.payment_id,
            'Correlation-Id': transfer.payment_id
        }
        body = transfer.to_schema_data()
        r = requests.post(url, json=body, headers=headers, timeout=settings.TIMEOUT_REQUEST)
        r.raise_for_status()
        return r.json()

    Flujo completo

token = obtener_token()
challenge_id, otp = crear_challenge(transfer.payment_id, token)
totp = generar_codigo_totp()     # función auxiliar TOTP
resultado = enviar_transferencia(transfer, token, otp, totp)

Código refactorizado

    Eliminar las vistas bank_sim_token, bank_sim_challenge, bank_sim_send_transfer y bank_sim_status_transfer

    .

    Simplificar send_transfer_gateway_view para que, en modo normal, use el flujo de arriba (token → challenge → transferencia). El modo fake se conserva:

@requiere_conexion_banco
def send_transfer_gateway_view(request, payment_id):
    transfer = get_object_or_404(Transfer, payment_id=payment_id)

    if request.GET.get('mode') == 'fake' and get_settings()['ALLOW_FAKE_BANK']:
        if request.method == 'POST':
            transfer.status = 'ACSP'
            transfer.save()
            return JsonResponse({'status': transfer.status})
        return render(request, 'api/GPT4/transfer_send_fake.html', {'transfer': transfer})

    if request.method == 'POST':
        try:
            token = obtener_token()
            challenge_id, otp = crear_challenge(transfer.payment_id, token)
            totp = request.POST.get('totp')  # ingresado por el usuario
            enviar_transferencia(transfer, token, otp, totp)
            messages.success(request, 'Transferencia enviada correctamente')
        except Exception as exc:
            messages.error(request, str(exc))
        return redirect('transfer_detailGPT4', payment_id=payment_id)

    return render(request, 'api/GPT4/transfer_send.html', {'transfer': transfer})

    Actualizar las URL correspondientes eliminando las rutas bank_sim_* de api/gpt4/urls.py.

    Revisar los templates para reemplazar las llamadas AJAX a bank_sim_* por un formulario estándar que ejecute la vista anterior. El template transfer_send_conexion.html se simplifica a un botón de “Enviar” que envía el formulario.

Configuración técnica

    Variables de entorno:

BASE_URL=https://simulador.ejemplo.com
TOKEN_PATH=/oidc/token
AUTH_PATH=/auth/challenges
API_PATH=/payments

    Ajustar settings.py o ConfiguracionAPI para que get_settings() lea estas nuevas variables.

    Mantener ALLOW_FAKE_BANK en el modelo de configuración para conservar el modo simulado en la vista de gateway.

Plan de testing

    Pruebas unitarias de utilidades

        Verificar generación de JWT y TOTP.

        Mockear las peticiones HTTP (token, challenge, transferencia).

    Pruebas de integración

        Configurar un entorno de staging que apunte al Simulador.

        Ejecutar el flujo completo (JWT → OTP → transferencia) con valores reales y comprobar respuestas 200/202/201.

    Pruebas de duplicación

        Intentar enviar dos transferencias con el mismo payment_id para validar el manejo de idempotencia.

    Modo fake

        Con ALLOW_FAKE_BANK=True, probar que la vista send_transfer_gateway_view permita finalizar transferencias sin llamadas externas.

    Manejo de fallos

        Simular expiración de TOTP y OTP para comprobar mensajes de error.

        Probar timeouts y respuestas 4xx/5xx del simulador para confirmar que se registren adecuadamente y se muestren al usuario.

De esta forma se elimina la lógica redundante que generaba servicios de token y challenge de manera local y se asegura que todas las operaciones pasen directamente por las rutas oficiales del simulador con el flujo JWT → Challenge OTP → Transferencia, manteniendo opcionalmente el modo fake mediante ALLOW_FAKE_BANK. This ensures consistent integration while preserving the option to perform local tests.