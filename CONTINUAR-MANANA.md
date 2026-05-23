# Continuar mañana — Ecommerce Ciclismo

Punto de control al cierre del 2026-05-22. Todo el código está en GitHub
(`develop`, sincronizado con `origin`).

## Dónde quedamos

El **bot conversacional** ("mano derecha" del dueño no vidente) está **construido
y verificado de punta a punta**:
- El dueño le habla NATURAL por voz o texto; un LLM (Groq, llama-3.3-70b-versatile)
  entiende e invoca herramientas. **Anti-alucinación**: los datos salen siempre de
  Medusa; el LLM nunca inventa cifras.
- **Consulta:** stock, precio, estado de un pedido, pedidos pendientes, reportes,
  **categorías** (las 22 públicas por tipo Y los códigos internos del dueño como
  6-CL, PITILLOS).
- **Operación con confirmación hablada:** crear pedido, confirmar, facturar
  (comprobante interno F-NNNNN), plantilla de empaque, marcar transportadora.
- Voz: Whisper vía Groq. 62 tests verdes; pipeline y conversación validados en vivo.
- Tienda (storefront) y admin de Medusa: funcionando, catálogo con imágenes reales.

> Estructura DUAL respetada: el público ve categorías por tipo legibles; el dueño
> conserva sus códigos (en `metadata.codigo_interno` + categorías inactivas).

## Cómo levantar todo mañana

```bash
cd ~/Documentos/Fof
./scripts/dev-up.sh        # Postgres+Redis, Medusa (develop, :9001), tienda (:8000),
                           # bot (cerebro 70B), keep-awake. Idempotente.
./scripts/demo-down.sh     # para apagar todo limpio
```
- Tienda: http://localhost:8000 · Admin: http://localhost:9001/app
  (admin@ciclismo.co / Ciclismo2026!)
- Bot: **@Ecommerceciclismobot** en Telegram (voz o texto). Pruebas:
  "¿cómo vamos de cascos?", "¿qué tengo en 6-CL?", "factúrame el pedido 3" → "sí".

> El bot/stack hay que correrlo en una terminal PROPIA (sobrevive al cerrar la
> sesión de Claude Code). Quedaron pedidos de prueba nº1, 2, 3 como data de demo.

## Secretos (.env local, gitignored — NO se commitea)
Ya están puestos: `GROQ_API_KEY`, `GROQ_MODEL=llama-3.3-70b-versatile`,
`TELEGRAM_BOT_TOKEN`, `MEDUSA_SALES_CHANNEL_ID`, `MEDUSA_ADMIN_EMAIL/PASSWORD`,
publishable key y región. (Las keys de demo se pueden rotar cuando quieras.)

## Gotchas aprendidos (importantes)
- Medusa local: usar **`medusa develop`**, NO `start` (start exige el build del
  admin y falla). En prod hay que resolver ese build (ver plan).
- Groq: **usar 70B**. El `8b-instant` FALLA el tool-calling (probado). Límite free
  ~12k tokens/min y **100k tokens/día por modelo**; se reinicia. Para uso diario sin
  techo: **Dev tier** de Groq.
- El cerebro reintenta ante rate-limit y degrada con "estoy con mucha demanda".

## Lo que sigue
- **Producción:** ver `docs/plan-produccion.md` (VPS, HTTPS, imágenes a MinIO/S3,
  pagos Wompi/ePayco, auth del bot por chat_id, DIAN, backups, accesibilidad real).
- **Datos del dueño:** `docs/pendientes-dueno.md` (59 sin clasificar + 28 precios).

## Estado git
Rama `develop` sincronizada con `origin` (github.com/Sad1mus/ecommerce-ciclismo).
Último hito: commit del bot conversacional (mano derecha, LLM + tools + voz).
