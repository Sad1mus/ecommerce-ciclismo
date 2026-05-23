# Plan de producción — Ecommerce Ciclismo

> Base: el producto está construido y verificado localmente (tienda + bot
> conversacional). Ya existen `docker-compose.prod.yml`, `nginx.conf`,
> `scripts/deploy.sh`, `src/payments/` (sandbox) y los docs de deploy/pagos.
> Este plan lista lo que falta para llevarlo a un servidor real.

## ⚠️ Cosas que cambiaron tras el bot conversacional
- `docs/deploy-vps.md` quedó parcialmente **desactualizado**: el bot ya NO usa
  `OPENAI_API_KEY` ni `MEDUSA_ADMIN_TOKEN`. Ahora usa **`GROQ_API_KEY` + `GROQ_MODEL`**
  (cerebro + voz), **`MEDUSA_ADMIN_EMAIL/PASSWORD`** (auto-login admin) y
  **`MEDUSA_SALES_CHANNEL_ID`** (crear pedidos). Ver tabla de secretos actualizada
  en `deploy-vps.md`.
- 🔧 **Gotcha técnico crítico:** en prod el contenedor Medusa usa `medusa start`
  (modo producción), que **exige el build del admin (`index.html`)** — justo lo
  que falló localmente (allí usamos `medusa develop`). **Verificar que `medusa build`
  en la imagen de prod genera el admin** o el contenedor no arranca. Probar ANTES
  del go-live.

## Fase 1 — Infraestructura (VPS + dominio + HTTPS)
- VPS **mínimo 4 GB RAM / 2 vCPU** (8 GB cómodo), SSD, Docker + `docker compose`.
- Dominio (A record al VPS), puertos 80/443 abiertos.
- HTTPS: el `nginx.conf` actual solo sirve HTTP → añadir Caddy/Traefik o certbot
  (TLS + redirección 80→443).
- `docker-compose.prod.yml` con `restart=always` → sobrevive reinicios (resuelve
  lo "frágil" de la demo local; ya no se relanza a mano).

## Fase 2 — Datos del dueño (catálogo 100% comprable) — no técnico, en paralelo
- 59 productos sin clasificar → categoría (`docs/pendientes-dueno.md`).
- 28 precios estimados → precio real. Hasta entonces siguen como borrador.

## Fase 3 — Imágenes persistentes
- Hoy en el `static/` local de Medusa. En prod → MinIO/S3 (robusto) o al menos
  volumen Docker, para que sobrevivan a los deploys. Re-subir con el script de
  catálogo desde `drive-download-*`.

## Fase 4 — Bot en producción
- **Groq Dev tier** (de pago, barato) → quita el techo de 100k tokens/día del free.
  Recomendado para uso diario con el modelo 70B (el 8b NO sirve: falla el tool-calling).
- **🔒 Control de acceso (ALTA prioridad):** en prod el bot OPERA el negocio
  (crea/factura/despacha). Restringir por `chat_id` (allowlist dueño/bodega) ANTES
  de exponerlo. Hoy el bot es abierto (se aplazó en la demo).
- Token de Telegram de producción (separado del de demo).
- Bot como servicio con `restart=always`.

## Fase 5 — Operaciones reales (decisión de alcance)
Lo que el bot hace hoy es demo-grade:
- **Facturación:** hoy comprobante interno en `metadata`. Producción CO puede exigir
  **factura electrónica DIAN** → integración regulada (proveedor autorizado +
  certificado digital). Workstream aparte y pesado.
- **Despacho:** hoy transportadora/guía en `metadata`. Decidir si se integra el
  fulfillment real de Medusa (captura de pago, guías reales).
- **Pagos:** cablear `src/payments/` (Wompi/ePayco) al módulo de pagos de Medusa +
  `ACTIVAR_PAGOS=true` + webhooks HTTPS (ver `docs/activar-pagos.md`).

## Fase 6 — Seguridad y operación
- Cambiar todos los secretos por defecto (`JWT_SECRET`, `COOKIE_SECRET` traen
  "cambia-esto-en-produccion").
- Backups automáticos: Postgres (catálogo + pedidos) e imágenes.
- Monitoreo: health checks, logs, alertas (bot caído = negocio parado).
- nginx con rate limiting; n8n (si se usa) aislado tras auth.
- Gestión de secretos del VPS (no `.env` plano si es posible; mínimo permisos 600 +
  rotación).

## Fase 7 — Prueba de accesibilidad real
- El dueño recorre el bot por VOZ en su dispositivo con su lector de pantalla.
- La mano derecha/clientes recorren la tienda visual.

## Orden recomendado
1. En paralelo ya: datos del dueño (Fase 2) + activar Groq Dev tier.
2. VPS + dominio + HTTPS + resolver el build del admin de Medusa (Fase 1).
3. Secretos de prod + imágenes a volumen/MinIO (Fases 1-3).
4. Bot auth por `chat_id` antes de exponerlo (Fase 4).
5. Pagos sandbox→prod + decisión DIAN/fulfillment (Fase 5).
6. Backups + monitoreo (Fase 6).
7. Prueba de accesibilidad real (Fase 7).

## Bloqueadores que dependen del dueño (no de código)
Servidor + dominio · llaves Wompi/ePayco de producción · decisión sobre DIAN ·
datos del dueño (59 + 28) · Groq Dev tier.
