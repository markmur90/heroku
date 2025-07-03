#!/usr/bin/env bash
set -euo pipefail

# Configuración
API_LOGIN="http://localhost:3000/api/login/"
API_URL="http://localhost:3000/api/transferencia/"
USER="493069k1"
PASS="bar1588623"
IDEMP_ID="206df230-f289-4d27-a2a5-27131ee68d72"
TRANSFER_FILE="02_transfer.json"

# 0️⃣ Obtener token automáticamente
echo "🔐 Obteniendo JWT..."
SIM_TOKEN=$(curl --silent --fail -X POST "$API_LOGIN" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USER\",\"password\":\"$PASS\"}" \
  | jq -r '.token')

if [[ -z "$SIM_TOKEN" || "$SIM_TOKEN" == "null" ]]; then
  echo "❌ No se pudo obtener el token."
  exit 1
fi
echo "✅ Token obtenido: $SIM_TOKEN"

# 1️⃣ Verificar que exista el JSON de la transferencia
if [[ ! -f "$TRANSFER_FILE" ]]; then
  echo "❌ No se encontró '$TRANSFER_FILE'."
  exit 1
fi

# 2️⃣ Pedir al usuario el OTP generado por el simulador
read -p "🔢 Introduce el OTP para la transferencia $IDEMP_ID: " OTP

# 3️⃣ Enviar la transferencia
echo "✉️ Enviando transferencia..."
RESPONSE=$(curl --silent --show-error --write-out "\n%{http_code}" \
  --request POST "$API_URL" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer $SIM_TOKEN" \
  --header "Idempotency-Id: $IDEMP_ID" \
  --header "Correlation-Id: $IDEMP_ID" \
  --header "Otp: $OTP" \
  --data-binary @"$TRANSFER_FILE")

# 4️⃣ Separar cuerpo y código HTTP
HTTP_BODY=$(echo "$RESPONSE" | sed '$d')
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [[ "$HTTP_CODE" != "200" && "$HTTP_CODE" != "202" ]]; then
  echo "❌ Error al enviar transferencia (HTTP $HTTP_CODE):"
  echo "$HTTP_BODY"
  exit 1
fi

echo "✅ Transferencia iniciada (HTTP $HTTP_CODE):"
echo "$HTTP_BODY"
