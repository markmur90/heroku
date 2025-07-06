# External API Integration Guide

This document provides a technical overview and implementation steps to connect an external API (`api.gpt4`) with the Django transfer simulator. It covers authentication, OTP challenge flow, transfer submission, configuration, and security.

## 1. Flow Overview

1. **Obtain JWT/OAuth Token**
   - POST `/api/token` or `/oidc/token` with credentials to receive a JWT.
   - Functions such as `obtener_token_desde_simulador` use this endpoint in `conexion_banco.py`【F:api/gpt4/conexion/conexion_banco.py†L152-L176】.
2. **Create OTP Challenge**
   - POST `/auth/challenges` (alias `/api/challenge`)
   - The helper `crear_challenge_mtan` builds the request with headers `Authorization`, `Correlation-Id`, and payload specifying the method (e.g., `MTAN`)【F:api/gpt4/utils.py†L1113-L1151】.
3. **Submit Transfer**
   - POST `/payments` or `/api/send-transfer` with transfer data and headers `Authorization`, `Otp`, `Idempotency-Id`, `Correlation-Id`【F:api/gpt4/utils.py†L724-L755】.
   - The response updates `auth_id` and `status` in `Transfer` models【F:api/gpt4/utils.py†L760-L771】.

All three steps must occur sequentially for each transfer to ensure real processing.

## 2. Required Code Updates

### `api/gpt4` Module

* Use the connection helpers in `api/gpt4/conexion/conexion_banco.py` for real requests. Ensure `enviar_transferencia_conexion` is called with the token and OTP from the challenge response.【F:api/gpt4/conexion/conexion_banco.py†L213-L276】
* Replace any usage of mock generators or hardcoded data with calls to the simulator via `hacer_request_banco` and related helpers.
* Verify that views like `send_transfer_gateway_view` call `crear_challenge_mtan` when OTP is required and then `enviar_transferencia_conexion` with the returned OTP value.【F:api/gpt4/views.py†L904-L963】
* Maintain CSRF exemptions on API endpoints such as `handle_notification` to allow simulator callbacks.【F:api/gpt4/views.py†L27-L83】

### Templates

Update forms located in `templates/api/GPT4` to include fields for manual token and OTP values. For example `send_transfer.html` already renders `manual_token` and `manual_otp` inputs; ensure these remain visible and correctly bound to the form【F:templates/api/GPT4/send_transfer.html†L32-L75】.

Provide user feedback for OTP challenge status (success/error) and show the PhotoTAN image when returned from the challenge endpoint, as already done in the template with `request.session.photo_tan_img`【F:templates/api/GPT4/send_transfer.html†L65-L70】.

### Dynamic Configuration

Use `ConfiguracionAPI` entries to store all external URLs and credentials. Keys referenced in `config/settings/configuracion_dinamica.py` include:
`TOKEN_URL`, `AUTHORIZE_URL`, `OTP_URL`, `AUTH_URL`, `API_URL`, `CLIENT_ID`, `CLIENT_SECRET`, and network settings such as `DNS_BANCO`, `DOMINIO_BANCO`, `RED_SEGURA_PREFIX`, `MOCK_PORT`【F:config/settings/configuración_dinamica.py†L4-L32】.
Ensure that these values are populated for the appropriate environment (production/sandbox/local) via the admin views in `api/configuraciones_api`.

## 3. Integration Steps

1. **Configure Environment**
   - Populate `ConfiguracionAPI` with simulator URLs and credentials (see `.env.local` for examples)【F:.env.local†L1-L37】.
   - Load these settings using `cargar_variables_entorno` at startup or when switching environment.
2. **Authentication**
   - From the external API, send credentials to `/api/token` (`obtener_token_desde_simulador`). Store the JWT for subsequent calls.
3. **OTP Challenge**
   - Call `/auth/challenges` using the token. Capture the returned `id` and await OTP input from the user (or push/phototan, depending on method).
4. **Transfer Submission**
   - Submit the SEPA transfer XML/JSON to `/payments` with headers `Authorization: Bearer <token>` and `Otp: <otp>`.
   - Use `enviar_transferencia_conexion` to log and process the response, updating the transfer status and generating XML/AML files.
5. **Handle OTP Verification**
   - If the API returns an `authId`, complete SCA by sending the OTP via `verify_mtan` or related helpers.
6. **Persist Results**
   - The simulator will respond with final transaction status. Save this in the `Transfer` model and display it in templates like `transfer_detail.html`.

## 4. Error Handling and Validation

* All request/response cycles are logged via `registrar_log`. Ensure errors from HTTP requests are captured and propagated to the caller.【F:api/gpt4/utils.py†L724-L781】
* Validate generated XML and AML files using `validar_xml_pain001` and `validar_aml_con_xsd` after a successful transfer submission.【F:api/gpt4/utils.py†L772-L783】
* Handle potential race conditions in OTP creation by checking for existing challenges and expiring them before requesting new ones.
* Implement timeouts from `TIMEOUT_REQUEST` to avoid hanging requests.
* Surfaces connection failures or invalid responses with meaningful HTTP status codes in the API views.

## 5. Security Considerations

* Use HTTPS for all connections to the simulator. The helper `hacer_request_seguro` resolves the simulator IP and enforces TLS when in the secure network.【F:api/gpt4/conexion/conexion_banco.py†L68-L98】
* JWTs and OTP values should never be logged in plain text; sensitive data is masked by logging filters such as `SensitiveFilter` in `conexion_banco_refactor.py`【F:api/gpt4_conexion/conexion_banco_refactor.py†L15-L41】.
* Ensure CSRF is disabled only on API endpoints that require it, e.g., `handle_notification` is decorated with `@csrf_exempt`【F:api/gpt4/views.py†L18-L25】.
* Store secret keys and client credentials in `ConfiguracionAPI` rather than the repository.

## 6. Route Compatibility

The simulator exposes both `/payments` and `/api/transferencias/entrantes/` as aliases. Ensure your URL mappings keep both paths functional. `enviar_transferencia_conexion` currently posts to `/api/transferencia`; adjust to `/payments` if required by the external API while keeping the original endpoint available for backward compatibility.【F:api/gpt4/conexion/conexion_banco.py†L213-L244】

---
This guide summarizes the necessary components to integrate an external API with the transfer simulator. Follow the steps above to authenticate, challenge for OTP, and process real transfers securely.