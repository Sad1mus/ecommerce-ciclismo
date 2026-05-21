# Deploy a VPS — Ecommerce Ciclismo

> Estado: **CÓDIGO LISTO, NO DESPLEGADO**. Los Dockerfiles y el
> `docker-compose.prod.yml` se validan y construyen localmente; **no** se ha
> desplegado a ningún servidor real ni hay secretos reales en el repo.

## Componentes

| Servicio | Imagen / build | Puerto interno | Expuesto |
|---|---|---|---|
| postgres | `postgres:15-alpine` | 5432 | no |
| redis | `redis:7-alpine` | 6379 | no |
| medusa | build `./src/medusa` | 9001 | vía nginx |
| storefront | build `./src/storefront` | 8000 | vía nginx |
| bot | build `./src/bot` | — | no (sale a Telegram) |
| nginx | `nginx:1.27-alpine` | 80 | 80 (público) |

Enrutado de `nginx.conf`: `/store`, `/admin`, `/auth`, `/app`, `/health` →
Medusa; el resto → storefront.

## Requisitos del VPS

- Docker Engine + plugin `docker compose`.
- Dominio apuntando al VPS (para HTTPS con Let's Encrypt — ver más abajo).
- Puertos 80/443 abiertos.

## Secretos (NO van en git)

Copiar `.env.example` a `.env` en el VPS y rellenar:

| Variable | Uso |
|---|---|
| `DB_PASS` | contraseña de Postgres (obligatoria) |
| `JWT_SECRET`, `COOKIE_SECRET` | secretos de Medusa (obligatorios) |
| `STORE_CORS`, `ADMIN_CORS`, `AUTH_CORS` | orígenes permitidos (tu dominio) |
| `MEDUSA_PUBLISHABLE_KEY`, `MEDUSA_REGION_ID` | storefront y bot |
| `MEDUSA_ADMIN_TOKEN` | bot, comando `/pedidos` |
| `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY` | bot y voz (Whisper) |

## Pasos

```bash
# en el VPS, dentro del repo
cp .env.example .env && nano .env        # rellenar secretos
docker compose -f docker-compose.prod.yml config -q   # validar
bash scripts/deploy.sh                    # build + up -d + estado
```

Primera vez (sembrar datos y generar la publishable key):

```bash
docker compose -f docker-compose.prod.yml exec medusa \
  npx medusa exec ./src/scripts/seed-ciclismo.ts
docker compose -f docker-compose.prod.yml exec medusa \
  npx medusa exec ./src/scripts/ensure-publishable-key.ts
# copiar el token impreso a MEDUSA_PUBLISHABLE_KEY en .env y:
docker compose -f docker-compose.prod.yml up -d storefront bot
```

## HTTPS (recomendado)

Añadir un contenedor `certbot` o terminar TLS en un proxy externo (Caddy,
Traefik) y redirigir 80→443. El `nginx.conf` incluido sirve HTTP; para
producción real, montar certificados y un `server` en el puerto 443.

## Validación local realizada (sin desplegar)

- `docker compose -f docker-compose.prod.yml config -q` → exit 0.
- `docker build` de `src/medusa`, `src/storefront` y `src/bot` → exit 0.

## Reglas

- No desplegar a un servidor real desde este repo de desarrollo.
- No commitear `.env` ni secretos; solo `.env.example` con valores vacíos.
- Los precios/stock siempre desde la DB/API de Medusa (anti-alucinación).
