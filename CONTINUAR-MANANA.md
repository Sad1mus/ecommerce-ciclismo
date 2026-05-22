# Continuar mañana — Ecommerce Ciclismo

Punto de control al cierre de hoy. Todo el código está en GitHub (`develop`).

## Dónde quedamos

El producto está **construido y verificado** de punta a punta:
- Backend Medusa con **608 productos**, stock real, **22 categorías legibles**,
  **608/608 con foto**.
- Storefront profesional **deportivo**, español/COP, accesible (axe 0 violaciones).
- Bot Telegram (texto + voz) conectado a Medusa **real** (sin mocks).
- Pagos Wompi/ePayco (sandbox) y deploy Docker: **código listo, no activado**.
- CI en GitHub Actions: **verde**.

## Cómo levantar todo mañana (en orden)

```bash
cd ~/Documentos/Fof
docker compose up -d                 # Postgres (5433) + Redis (6380)
# Backend Medusa (admin + API) en :9001
cd src/medusa/apps/backend && npx medusa develop
# En otra terminal: storefront en :8000
cd ~/Documentos/Fof/src/storefront && npm run start -- -p 8000
```
O usar el atajo que dejó el endurecimiento: `scripts/dev-up.sh`.

- Tienda:  http://localhost:8000
- Admin:   http://localhost:9001/app   (admin@ciclismo.co / Ciclismo2026!)

> Puertos remapeados para no chocar con el stack etherlabx: PG **5433**,
> Redis **6380**, Medusa **9001**, storefront **8000**.

## Lo que sigue (3 frentes)

### A) Datos del dueño  → ver `docs/pendientes-dueno.md`
- **59 productos** "por clasificar" (no se adivinaron).
- **28 precios estimados** a confirmar (siguen como borrador, no comprables).

### B) Puesta en marcha (necesita secretos + servidor)
- Token de Telegram (@BotFather), llaves **Wompi/ePayco**, llave **OpenAI** (voz).
- VPS + dominio.
- **Imágenes:** hoy viven en el `static/` local de Medusa. En la VPS deben ir a un
  **volumen Docker** (simple) o **MinIO/S3** (robusto) para que sobrevivan a las
  actualizaciones. (Las imágenes NO están en git: se re-suben con el script de
  catálogo desde la carpeta `drive-download-*`.)

### C) Prueba de accesibilidad real
- Que el dueño recorra tienda + bot con su **lector de pantalla en dispositivo real**.

## Colas de goals disponibles (en `.claude/`)
Todas las fases hechas se completaron vía `/goal`. Si se necesitan nuevas, se crean
con la skill `goal-queue`. (Los `.md` de colas ya completadas son artefactos locales.)

## Estado git
Rama de trabajo: `develop` (todo pusheado a github.com/Sad1mus/ecommerce-ciclismo,
privado). Commits firmados como Sad1mus <sad1mus@etherlabx.com>.
