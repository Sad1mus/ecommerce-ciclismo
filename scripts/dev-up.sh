#!/usr/bin/env bash
# ===========================================================================
# dev-up.sh — Levanta TODO el stack LOCAL del ecommerce de ciclismo, junto y de
# forma reproducible:  Postgres + Redis (docker) -> Medusa (:9001) ->
# Storefront (:8000) -> Bot (conectividad).
#
# Idempotente: si un servicio ya responde, NO lo reinicia. Sin mocks: todo
# golpea el stack real. Puertos: Postgres 5433, Redis 6380, Medusa 9001,
# Storefront 8000.  Logs en .devlogs/.
# ===========================================================================
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
LOGDIR="$ROOT/.devlogs"; mkdir -p "$LOGDIR"

# Carga .env local (PK, region, credenciales admin del E2E) si existe.
if [ -f .env ]; then set -a; . ./.env; set +a; fi

http_code() { curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$1" 2>/dev/null || echo 000; }

wait_http() { # url name max_intentos codigos_ok...
  local url="$1" name="$2" tries="$3"; shift 3
  local ok=("$@")
  for ((i=1; i<=tries; i++)); do
    local code; code="$(http_code "$url")"
    for c in "${ok[@]}"; do
      if [ "$code" = "$c" ]; then echo "  $name OK ($code)"; return 0; fi
    done
    sleep 2
  done
  echo "  ERROR: $name no respondio (último=$code) en $url"; return 1
}

echo ">> 1/4  Postgres + Redis (docker compose)"
docker compose up -d postgres redis >/dev/null
pg=none; rd=none
for ((i=1; i<=30; i++)); do
  pg="$(docker inspect -f '{{.State.Health.Status}}' ciclismo-postgres 2>/dev/null || echo none)"
  rd="$(docker inspect -f '{{.State.Health.Status}}' ciclismo-redis 2>/dev/null || echo none)"
  [ "$pg" = healthy ] && [ "$rd" = healthy ] && break
  sleep 2
done
echo "  postgres=$pg  redis=$rd"
[ "$pg" = healthy ] && [ "$rd" = healthy ] || { echo "  ERROR: db/cache no healthy"; exit 1; }

echo ">> 2/4  Medusa (:9001)"
if [ "$(http_code http://localhost:9001/health)" = "200" ]; then
  echo "  ya está arriba"
else
  ( cd src/medusa/apps/backend
    [ -d .medusa/server ] || npx medusa build
    nohup npx medusa start >"$LOGDIR/medusa.log" 2>&1 &
    echo $! >"$LOGDIR/medusa.pid" )
  wait_http http://localhost:9001/health Medusa 90 200
fi

echo ">> 3/4  Storefront (:8000)"
# /co responde 307 (redirección que fija la cookie _medusa_cache_id): eso ya es "arriba".
sf_code="$(http_code http://localhost:8000/co)"
if [ "$sf_code" = "200" ] || [ "$sf_code" = "307" ]; then
  echo "  ya está arriba ($sf_code)"
else
  ( cd src/storefront
    [ -d .next ] || npm run build
    nohup npm run start >"$LOGDIR/storefront.log" 2>&1 &
    echo $! >"$LOGDIR/storefront.pid" )
  wait_http http://localhost:8000/co Storefront 90 200 307
fi

echo ">> 4/4  Bot -> Medusa (conectividad real, sin mocks)"
if [ -n "${TELEGRAM_BOT_TOKEN:-}" ]; then
  ( cd src/bot
    nohup ./.venv/bin/python bot.py >"$LOGDIR/bot.log" 2>&1 &
    echo $! >"$LOGDIR/bot.pid" )
  echo "  bot lanzado (TELEGRAM_BOT_TOKEN presente) — log en .devlogs/bot.log"
else
  echo "  sin TELEGRAM_BOT_TOKEN: no se arranca el daemon. Verifico que el bot"
  echo "  alcanza el Medusa real y lee datos (no inventa):"
  ( cd src/bot && ./.venv/bin/python - <<'PY'
import handlers
from medusa_client import MedusaClient
c = MedusaClient()
prods = c.search_products("candado", limit=1)
if prods:
    p = prods[0]
    print(f"    bot OK: '{p.title}' sku={p.sku} stock={p.stock} precio={p.price} {p.currency}")
else:
    print("    bot conecta pero la búsqueda no devolvió productos")
PY
  )
fi

echo ""
echo ">> Estado docker:"
docker compose ps
echo ""
echo ">> Endpoints:"
echo "   Medusa /health : $(http_code http://localhost:9001/health)"
echo "   Storefront /co : $(http_code http://localhost:8000/co)"
echo ""
echo "Stack arriba. E2E:  cd src/bot && ./.venv/bin/python -m pytest -q -m integration"
