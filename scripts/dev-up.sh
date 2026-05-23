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

# Evita que el equipo se suspenda durante la demo. Reversible: scripts/demo-down.sh
# o kill del PID en .devlogs/keepawake.pid. No cambia ajustes persistentes.
if command -v systemd-inhibit >/dev/null 2>&1 \
   && ! pgrep -f "systemd-inhibit.*ciclismo-demo" >/dev/null 2>&1; then
  setsid systemd-inhibit --what=sleep:idle --who="ciclismo-demo" \
    --why="Demo ecommerce en curso" --mode=block sleep infinity \
    >/dev/null 2>&1 < /dev/null &
  echo $! >"$LOGDIR/keepawake.pid"
  echo ">> keep-awake activado (no se suspendera mientras corra la demo)"
fi

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
  # 'medusa develop' (no 'start'): start exige el admin build (index.html) y aquí
  # falla; develop sirve el admin al vuelo. PORT=9001 explícito (default sería 9000).
  ( cd src/medusa/apps/backend
    PORT=9001 nohup npx medusa develop >"$LOGDIR/medusa.log" 2>&1 &
    echo $! >"$LOGDIR/medusa.pid" )
  wait_http http://localhost:9001/health Medusa 120 200
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
  # Idempotente: Telegram solo permite UN getUpdates; no relanzar si ya corre
  # (un segundo bot daría "Conflict: terminated by other getUpdates request").
  if pgrep -f "[p]ython bot.py" >/dev/null 2>&1; then
    echo "  bot ya está corriendo (no relanzo)"
  else
    ( cd src/bot
      # El .venv puede venir sin deps: instalar si falta python-telegram-bot.
      [ -x .venv/bin/python ] || python3 -m venv .venv
      .venv/bin/python -c "import telegram" 2>/dev/null \
        || .venv/bin/pip install -q -r requirements.txt
      nohup ./.venv/bin/python bot.py >"$LOGDIR/bot.log" 2>&1 &
      echo $! >"$LOGDIR/bot.pid" )
    echo "  bot lanzado (TELEGRAM_BOT_TOKEN presente) — log en .devlogs/bot.log"
  fi
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
