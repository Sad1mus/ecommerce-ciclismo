# Goal Queue — Ecommerce Ciclismo (Fases 1–5)

estado: activa
current: 1
turn_cap_por_item: 40

<!--
Estados por tarea: [pending] -> [in-progress] -> [done] | [blocked]
Reglas:
- Solo UNA tarea [in-progress] a la vez. No empezar la siguiente hasta que la
  actual esté [done] o [blocked].
- "Check" debe CORRERSE y su resultado quedar VISIBLE en la conversación
  (el evaluador de /goal no lee este archivo, solo ve el transcript).
- Cada fase termina con commit en rama `develop` + push a origin (NUNCA a main:
  el modo auto bloquea push a main; trabajamos siempre en develop).
- Reglas permanentes del proyecto:
  * ANTI-ALUCINACIÓN: precios y stock SIEMPRE desde la DB/API de Medusa, jamás
    inventados ni hardcodeados.
  * Accesibilidad primero (admin no vidente + lector de pantalla).
  * Puertos locales: Postgres 5433, Redis 6380, Medusa 9001 (coexisten con etherlabx).
  * NO commitear node_modules, .env, ni secretos reales.
-->

## [done] 1. Git + repositorio privado en GitHub (Sad1mus)
**Condición:** `/home/sadimus/Documentos/Fof` es un repo git con un commit inicial
que incluye TODO el trabajo de Fase 0 (docker-compose, data/, src/medusa código —
sin node_modules), autor Sad1mus, conectado a un repo PRIVADO
`github.com/Sad1mus/ecommerce-ciclismo`, con la rama `develop` pusheada. Ningún
`.git` anidado en src/medusa.
**Check (imprimir en el transcript):**
- `git -C /home/sadimus/Documentos/Fof log --oneline -1` muestra el commit (autor Sad1mus)
- `git -C /home/sadimus/Documentos/Fof status --porcelain` vacío (limpio)
- `git -C /home/sadimus/Documentos/Fof ls-files | grep -c node_modules` == 0
- `gh repo view Sad1mus/ecommerce-ciclismo --json visibility,isPrivate -q '.isPrivate'` == true
- `git -C /home/sadimus/Documentos/Fof ls-remote --heads origin develop` no vacío
**No tocar:** no pushear a `main`; no trackear node_modules/.env/data/inventario.json;
no borrar los documentos ni el CSV existentes; no exponer tokens.
**Evidencia:** Commit inicial dfefe97 (autor Sad1mus <jordycapital@gmail.com>), 43 archivos sin node_modules/.env/inventario.json. Repo privado github.com/Sad1mus/ecommerce-ciclismo (isPrivate=true), rama develop pusheada (ls-remote OK). Sin .git anidado en src/medusa. status limpio.

## [done] 2. Fase 1 — Storefront Next.js accesible
**Condición:** `src/storefront` (Next.js) lista el catálogo real consumiendo la
Store API de Medusa (con publishable key creada y ligada al sales channel), es
accesible (navegación por teclado, roles/labels ARIA, contraste AA), y compila.
Los precios/stock vienen de la API (no hardcode). Commit en develop + push.
**Check (imprimir):**
- `cd src/storefront && npm run build` termina con exit 0
- humo: arrancar el storefront en background, `curl -s localhost:<puerto>` devuelve
  HTTP 200 y el HTML contiene al menos un nombre de producto real del inventario
- lint a11y: `npx eslint .` (con eslint-plugin-jsx-a11y configurado) exit 0
- `git -C . log --oneline -1` muestra el commit de Fase 1 pusheado a develop
**No tocar:** no romper el backend Medusa de Fase 0; no hardcodear precios/stock;
solo añadir a src/medusa lo mínimo (publishable key / CORS).
**Evidencia:** Commit 7cd123b en develop (pusheado, ls-remote OK). `npm run build` exit 0 (ruta `/` dinámica ƒ). Smoke: storefront en :8000 devuelve HTTP 200 y HTML con productos reales ("Candado manguera espiral" $14.500, 8 en stock; "Forro gel MTB antipros" $19.500, 43 en stock) — precios y stock servidos por la Store API de Medusa (publishable key pk_1e37… ligada al sales channel "Tienda Ciclismo", region COP), nunca hardcode. `npx eslint .` exit 0 con eslint-plugin-jsx-a11y (34 reglas activas).

## [done] 3. Fase 2 — Bot Telegram texto (anti-alucinación)
**Condición:** `src/bot` (Python) con comandos `/stock`, `/precio`, `/pedidos` que
consultan SIEMPRE la API/DB de Medusa (nunca inventan); respuestas texto-only aptas
para lector de pantalla (sin emojis ni tablas, máx ~10 líneas); si la API falla,
responde "dato no disponible" en vez de inventar. Tests pasan. Commit en develop + push.
**Check (imprimir):**
- `cd src/bot && python -m pytest -q` exit 0
- los tests (con Medusa mockeado) prueban: (a) `/stock` devuelve el stock que da la
  API, (b) ante fallo de API el bot NO inventa, (c) salida sin emojis/tablas
- `git log --oneline -1` muestra el commit de Fase 2 en develop
**No tocar:** no requiere TELEGRAM_BOT_TOKEN real para los tests; anti-alucinación
obligatoria; sin secretos en el repo.
**Evidencia:** Commit d534c1f en develop (pusheado). `python -m pytest -q` → 9 passed, exit 0. Tests con Medusa mockeado prueban: (a) /stock refleja el stock de la API ("8 unidades"), (b) FailingClient → "dato no disponible" sin dígitos inventados, (c) salida sin emojis/tablas y ≤10 líneas. Demo real contra Medusa: /stock candado y /precio bomba devuelven stock y precios reales de la API. Token Telegram solo por env (import de telegram diferido); .venv no commiteado.

## [done] 4. Fase 3 — Voz (Whisper) + agentes ventas/logística/reportes
**Condición:** handler de voz que transcribe audio→texto→comando (Whisper) integrado
al bot, más los agentes de ventas, logística y reportes. Pipeline de voz con STT
mockeado y lógica de agentes cubiertos por tests. Tests pasan. Commit en develop + push.
**Check (imprimir):**
- `cd src/bot && python -m pytest -q` exit 0 incluyendo tests del pipeline de voz
  (Whisper/STT mockeado) y de los 3 agentes nuevos
- `git log --oneline -1` muestra el commit de Fase 3 en develop
**No tocar:** OPENAI_API_KEY no requerido (STT mockeado en tests); sin llamadas
reales a pagos; anti-alucinación.
**Evidencia:** Commit 65b60ba en develop (pusheado). `python -m pytest -q` → 26 passed, exit 0. Incluye test_voice.py (pipeline audio→texto→comando con STT/Whisper mockeado: routing, datos reales vía cliente, STT caído → "no entendí el audio" sin inventar) y test_agents.py (VentasAgent/LogisticaAgent/ReportesAgent: precio+stock reales, suma de unidades calculada de la API, anti-alucinación ante fallo). voice.py usa WhisperTranscriber con import diferido (OPENAI_API_KEY solo runtime); bot.py integra MessageHandler de voz + /ventas /logistica /reportes.

## [in-progress] 5. Fase 4 — Pagos Wompi/ePayco (CÓDIGO LISTO, NO ACTIVADO)
**Condición:** integración de pagos colombianos (Wompi + ePayco) programada como
proveedor en sandbox/mock, con build y tests verdes, y un documento de activación
que lista los secretos que faltan. NO se ejecutan cobros reales ni hay llaves reales
en el repo. Commit en develop + push.
**Check (imprimir):**
- build/tests afectados terminan exit 0 (`npm run build` y/o `pytest -q`)
- `test -f docs/activar-pagos.md && echo OK` imprime OK
- no hay llaves reales commiteadas: `git grep -nE "WOMPI_PRIVATE|EPAYCO_PRIVATE" -- '*.env' || echo "sin llaves reales"`
- `git log --oneline -1` muestra el commit de Fase 4 en develop
**No tocar:** NO cobros reales, NO llaves reales en git, todo en modo sandbox/desactivado.
**Evidencia:**

## [pending] 6. Fase 5 — Deploy Docker para VPS (CÓDIGO LISTO, NO DESPLEGADO)
**Condición:** `docker-compose.prod.yml` + Dockerfiles (medusa, bot, storefront) +
`nginx.conf` + script de deploy + `docker-compose.prod.yml` válido y las imágenes
construyen localmente. Documento de deploy a VPS. NO se despliega a ningún servidor real.
**Check (imprimir):**
- `docker compose -f docker-compose.prod.yml config -q` exit 0
- `docker build` de cada Dockerfile (medusa/bot/storefront) exit 0
- `test -f docs/deploy-vps.md && echo OK` imprime OK
- `git log --oneline -1` muestra el commit de Fase 5 en develop
**No tocar:** NO conectar a VPS real, NO secretos reales; solo validar/buildear localmente.
**Evidencia:**
