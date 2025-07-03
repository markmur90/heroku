#!/usr/bin/env bash
# login.sh — Obtiene token JWT del simulador

# Configuración
SIM_URL="http://localhost:3000/api/login/"
USER="493069k1"
PASS="bar1588623"

# Petición
echo "🔐 Obteniendo JWT..."
SIM_TOKEN=$(curl -s -X POST "$SIM_URL" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USER\",\"password\":\"$PASS\"}" \
  | jq -r '.token')

if [[ -z "$SIM_TOKEN" || "$SIM_TOKEN" == "null" ]]; then
  echo "❌ No se pudo obtener el token."
  exit 1
fi

echo "✅ Token obtenido: $SIM_TOKEN"
# Exportar para otros scripts
export SIM_TOKEN
