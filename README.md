# Ecommerce Ciclismo — administrado por un dueño no vidente

Tienda de productos de ciclismo (Colombia). La particularidad central:
**el dueño/administrador es no vidente y opera toda la tienda por un bot de
Telegram (texto + voz)**, mientras que su mano derecha y los clientes usan la
tienda visual normal.

> Filosofía: **adaptamos el software a él, no al revés.** Su forma de etiquetar
> el inventario es la verdad; el sistema se acomoda para minimizar fricción.

## Estado: Fases 0–2 cerradas · Fase 3 (voz + agentes) en curso

Enfoque **lean**: construimos el producto directo (sin la "fábrica" JARVIS/
LiteLLM/Ollama por ahora). Esa capa se puede añadir luego para abaratar costos.
El producto está construido y verificado localmente (tienda + bot
conversacional); lo que falta para el servidor real vive en
`docs/plan-produccion.md`.

| Fase | Qué entrega | Estado |
|------|-------------|--------|
| 0 | Repo + Docker (Postgres+Redis) + inventario normalizado + MedusaJS | ✅ |
| 1 | Storefront Next.js accesible (catálogo visual, español/COP) | ✅ |
| 2 | Bot Telegram conversacional (Groq/Llama tool-calling, anti-alucinación) | ✅ |
| 3 | Voz (Whisper vía Groq) + agentes ventas/logística/reportes | 🔧 en curso |
| 4 | Pagos Wompi/ePayco | ⏳ módulos listos, sin activar |
| 5 | Deploy Docker en VPS + monitor | ⏳ |

## Regla de oro: anti-alucinación

Stock y precios salen **siempre** de la base de datos (MedusaJS/Postgres),
**nunca** de un LLM. El LLM solo interpreta lenguaje natural; los datos son la
fuente única de verdad. Verificado con tests E2E
(`src/bot/test_anti_alucinacion.py`, `src/bot/test_e2e_storefront_bot.py`).

## Inventario

- Fuente: `inventario_FINAL_con_stock_simulado.csv` (679 filas, 608 productos).
- `data/normalize_inventory.py` → normaliza a `data/inventario.json` (productos
  con variantes por color/talla).
- `data/price_fixes.csv` → correcciones editables de precio para las variantes
  que venían en $0 (4 recuperadas del nombre, 28 estimadas a confirmar).
- Pendientes del dueño (no de código): **59 productos sin categoría asignada** y
  **28 precios estimados** siguen como borrador (no comprables) hasta que el dueño
  los confirme. Detalle en `docs/pendientes-dueno.md`.

Re-generar inventario tras cambiar el CSV o los precios:

```bash
python3 data/normalize_inventory.py
```

## Capa de datos (Fase 0)

```bash
cp .env.example .env        # ya hay un .env de dev
docker compose up -d        # postgres + redis
docker compose ps           # verificar healthy
```

## Estructura

```
Fof/
├── docker-compose.yml      # lean: postgres + redis
├── .env / .env.example
├── data/
│   ├── normalize_inventory.py
│   ├── price_fixes.csv
│   └── inventario.json     # generado
├── src/
│   ├── medusa/             # backend ecommerce (Fase 0)
│   ├── storefront/         # Next.js (Fase 1)
│   ├── bot/                # Telegram conversacional + voz (Fases 2-3)
│   └── payments/           # Wompi/ePayco (Fase 4, sandbox / sin activar)
└── *.md / *.docx           # documentos de arquitectura (JARVIS, ciclismo)
```
