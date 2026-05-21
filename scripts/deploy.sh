#!/usr/bin/env bash
# Script de deploy para el VPS — Ecommerce Ciclismo.
# NO se ejecuta en el entorno de desarrollo: se corre EN el VPS, una vez que el
# .env de produccion (con secretos) este presente. Aqui solo se versiona.
set -euo pipefail

COMPOSE_FILE="docker-compose.prod.yml"

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  echo "ERROR: falta .env de produccion con los secretos (DB_PASS, JWT_SECRET, etc.)." >&2
  echo "Copia .env.example a .env y rellenalo en el VPS. Ver docs/deploy-vps.md." >&2
  exit 1
fi

echo ">> Validando configuracion de compose..."
docker compose -f "$COMPOSE_FILE" config -q

echo ">> Construyendo imagenes (medusa, storefront, bot)..."
docker compose -f "$COMPOSE_FILE" build

echo ">> Levantando base de datos y cache..."
docker compose -f "$COMPOSE_FILE" up -d postgres redis

echo ">> Levantando backend, storefront, bot y nginx..."
docker compose -f "$COMPOSE_FILE" up -d

echo ">> Estado:"
docker compose -f "$COMPOSE_FILE" ps

cat <<'NOTA'
Listo. Pasos posventa (solo la primera vez):
  - Sembrar inventario:   docker compose -f docker-compose.prod.yml exec medusa npx medusa exec ./src/scripts/seed-ciclismo.ts
  - Crear publishable key: docker compose -f docker-compose.prod.yml exec medusa npx medusa exec ./src/scripts/ensure-publishable-key.ts
  - Copiar la key a MEDUSA_PUBLISHABLE_KEY en .env y reiniciar storefront/bot.
NOTA
