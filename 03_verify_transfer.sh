#!/usr/bin/env bash
# verify_transfer.sh — Verifica OTP y confirma transferencia

# Requiere: SIM_TOKEN exportado
if [[ -z "$SIM_TOKEN" ]]; then
  echo "❌ Variable SIM_TOKEN no definida. Ejecuta primero ./login.sh"
  exit 1
fi

API_VERIFY="http://localhost:3000/api/transferencia/verify/"

read -p "🔢 Introduce PAYMENT_ID: " PAYMENT_ID
read -p "🔢 Repite el OTP: " OTP

echo "🔍 Verificando OTP para $PAYMENT_ID..."
curl -i -X POST "$API_VERIFY" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SIM_TOKEN" \
  -d "{\"payment_id\":\"$PAYMENT_ID\",\"otp\":\"$OTP\"}"

echo "✅ Proceso completado."
