#!/usr/bin/env bash
# smoke-categorias-storefront.sh
# Verifica que el storefront (:8000) muestra las categorías de COMPRA POR TIPO
# (legibles) de la Fase A y NINGÚN código interno (6-CL, 1-RK, ...) como etiqueta.
#
# No muta nada. Requiere el stack vivo (Medusa :9001 + storefront :8000).
# Uso:  bash scripts/smoke-categorias-storefront.sh
set -euo pipefail

SF="${SF_URL:-http://localhost:8000}"
CC="${COUNTRY:-co}"
CJ="$(mktemp)"
trap 'rm -f "$CJ" "$CJ".home "$CJ".cand' EXIT

echo ">> Storefront: $SF/$CC"

# El middleware redirige una vez para fijar la cookie _medusa_cache_id.
curl -s -c "$CJ" -o /dev/null "$SF/$CC"
curl -s -b "$CJ" -c "$CJ" -L -o "$CJ".home "$SF/$CC"

echo "== Categorías-tipo legibles presentes en la navegación =="
faltan=0
for t in "Bombas e infladores" "Cascos" "Candados" "Transmisión" "Sillines y tijas" "Luces"; do
  if grep -qF "\"name\":\"$t\"" "$CJ".home || grep -qF "\\\"name\\\":\\\"$t\\\"" "$CJ".home; then
    echo "   OK  $t"
  else
    echo "  FALTA $t"; faltan=$((faltan+1))
  fi
done

echo "== Ningún código interno como NOMBRE de categoría =="
codes='6-CL|1-RK|2-SPK|3-RR|4-BK|5-MT|1\.1-KL|PITILLOS|UÑAS|PASTILLAS|PREVENTA 2025|PRODUTOS TORNASOL|PRODUCTOS P 2025|GUANTES'
vis=$( { grep -oE "\\\\?\"name\\\\?\":\\\\?\"($codes)\\\\?\"" "$CJ".home || true; } | sort -u | wc -l)
echo "   códigos visibles como categoría: $vis (debe ser 0)"

echo "== Categoría Candados lista productos reales =="
curl -s -b "$CJ" -c "$CJ" -L -o "$CJ".cand "$SF/$CC/categories/candados"
nprod=$( { grep -oE "Candado[^\"<]{0,30}" "$CJ".cand || true; } | sort -u | wc -l)
echo "   títulos 'Candado*' distintos en la página: $nprod"

if [ "$faltan" -eq 0 ] && [ "$vis" -eq 0 ] && [ "$nprod" -ge 1 ]; then
  echo "SMOKE OK"
else
  echo "SMOKE FALLA (faltan=$faltan codigos=$vis productos=$nprod)"; exit 1
fi

cat <<'NOTE'

Accesibilidad (manual, requiere Chrome-for-Testing fuera del repo):
  CHROME=~/chrome/linux-*/chrome-linux64/chrome
  npx @axe-core/cli --chrome-path "$CHROME" \
    --chrome-options="no-sandbox,disable-dev-shm-usage" http://localhost:8000
  -> esperado: 0 violations
NOTE
