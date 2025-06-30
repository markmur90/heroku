## 1. Evaluación del código actual

* **Endpoints locales duplicados**: Se han definido rutas internas que replican los servicios del simulador en `api/gpt4/urls.py` y/o `api/gpt4/conexion/conexion_banco.py`:

  ```python
  path("api/bank_sim/token", views.bank_sim_token, name="bank_sim_token"),
  path("api/bank_sim/challenge", views.bank_sim_challenge, name="bank_sim_challenge"),
  path("api/bank_sim/send-transfer", views.bank_sim_send_transfer, name="bank_sim_send_transfer"),
  path("api/bank_sim/status-transfer", views.bank_sim_status_transfer, name="bank_sim_status_transfer"),
  ```
* **Vistas y funciones**:

  * `bank_sim_token(request)`, `bank_sim_challenge(request)`, `bank_sim_send_transfer(request)`, `bank_sim_status_transfer(request)` implementan localmente la lógica de autenticación, OTP y transferencia.
  * En la plantilla `transfer_send_conexion.html` (y otras) se consumen estas rutas mediante llamadas AJAX, evitando invocar el simulador real.
* **Variables de entorno** apuntan a la infraestructura local (IP, puertos internos) en lugar de a la URL oficial `https://simulador.ejemplo.com`. Por ejemplo:

  ```bash
  BANK_SIM_BASE_URL=http://80.78.30.242:9181
  TOKEN_PATH=/oidc/token
  AUTH_PATH=/auth/challenges
  SEND_PATH=/payments
  STATUS_PATH=/payments/status
  TIMEOUT_REQUEST=10  # segundos
  ALLOW_FAKE_BANK=True
  ```

## 2. Plan de testing

1. **Pruebas unitarias**:

   * `obtener_token`, `solicitar_otp`, `enviar_transferencia`, `consultar_estado` usando `requests_mock`.
   * Validar respuesta esperada y manejo de códigos de error del simulador.
2. **Pruebas de integración** en entorno de staging contra el simulador real:

   * Flujo completo JWT → OTP → Transferencia.
   * Verificar cambios de estado y respuesta final.
3. **Casos de borde**:

   * Expiración de JWT u OTP.
   * Envío duplicado (`payment_id` repetido) y código de error de idempotencia (6506).
   * Timeouts y respuestas 4xx/5xx: confirmar logging y mensajes de usuario.
4. **Modo fake** (`ALLOW_FAKE_BANK=True`): las funciones deben redirigir al mock interno, sin llamadas externas.
5. **QA manual**: comprobar que desaparecen las invocaciones AJAX a rutas locales en templates cuando se usa el simulador real.

## 3. Refactorización propuesta

1. **Eliminar duplicados**:

   * Quitar las vistas `bank_sim_*` de `views.py`.
   * Remover sus rutas de `urls.py`.
   * Limpiar cualquier llamada AJAX en templates.
2. **Unificar flujo** en una única vista (por ejemplo, `send_transfer_view` o `send_transfer_gateway_view`):

   ```python
   def send_transfer_view(request, payment_id):
       transfer = get_object_or_404(Transfer, payment_id=payment_id)
       if request.method == "POST":
           form = SendTransferForm(request.POST, instance=transfer)
           if form.is_valid():
               token = obtener_token()
               challenge_id = solicitar_otp(token, payment_id)
               otp = form.cleaned_data.get("otp")
               respuesta_envio = enviar_transferencia(token, payment_id, otp)
               estado_final = esperar_estado_final(token, payment_id)
               # Mostrar resultado al usuario
   ```
3. **Funciones auxiliares**:

   ```python
   def obtener_token() -> str:
       url = f"{settings.BANK_SIM_BASE_URL}{settings.TOKEN_PATH}"
       r = requests.post(url, json={"username": settings.USER, "password": settings.PASS}, timeout=settings.TIMEOUT_REQUEST)
       r.raise_for_status()
       return r.json()["access_token"]

   def solicitar_otp(token: str, payment_id: str) -> str:
       url = f"{settings.BANK_SIM_BASE_URL}{settings.AUTH_PATH}"
       headers = {"Authorization": f"Bearer {token}"}
       r = requests.post(url, json={"payment_id": payment_id}, headers=headers, timeout=settings.TIMEOUT_REQUEST)
       r.raise_for_status()
       return r.json()["challenge_id"]

   def enviar_transferencia(token: str, payment_id: str, otp: str) -> dict:
       url = f"{settings.BANK_SIM_BASE_URL}{settings.SEND_PATH}"
       headers = {"Authorization": f"Bearer {token}"}
       body = {"payment_id": payment_id, "otp": otp, /* resto de campos */}
       r = requests.post(url, json=body, headers=headers, timeout=settings.TIMEOUT_REQUEST)
       r.raise_for_status()
       return r.json()

   def esperar_estado_final(token: str, payment_id: str) -> str:
       url = f"{settings.BANK_SIM_BASE_URL}{settings.STATUS_PATH}/{payment_id}"
       headers = {"Authorization": f"Bearer {token}"}
       # Loop con sleep y retries hasta estado terminal
   ```

## 4. Configuración técnica

* Variables de entorno centralizadas en `settings.py` o similar.
* Uso de `ALLOW_FAKE_BANK` para alternar entre mock interno y simulador real.
* Timeouts, rutas y credenciales parametrizables.

## 5. Manejo de casos de fallo y logging

* Capturar y registrar errores 4xx/5xx antes de `raise_for_status()`.
* Retries configurables ante timeouts.
* Mensajes de usuario claros en plantillas.
* Pruebas automáticas y cobertura mínima del 80% sobre las nuevas funciones.

---

**Mejor opción**: El contenido de la versión **R2** aporta la estructura más clara y ejemplos de rutas concretas; sin embargo, hemos combinado su claridad con las indicaciones de R1/R4 sobre variables de entorno y con el ejemplo de código detallado de R3. Este documento unificado es la versión más completa y coherente para guiar la refactorización.
