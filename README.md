# Ecommerce Ciclismo — administrado por un dueño no vidente

Tienda de productos de ciclismo (Colombia). La particularidad central:
**el dueño/administrador es no vidente y opera toda la tienda por un bot de
Telegram (texto + voz)**, mientras que su mano derecha y los clientes usan la
tienda visual normal.

> Filosofía: **adaptamos el software a él, no al revés.** Su forma de etiquetar
> el inventario es la verdad; el sistema se acomoda para minimizar fricción.

## Estado: Fase 0 (en curso)

Enfoque **lean**: construimos el producto directo (sin la "fábrica" JARVIS/
LiteLLM/Ollama por ahora). Esa capa se puede añadir luego para abaratar costos.

| Fase | Qué entrega | Estado |
|------|-------------|--------|
| 0 | Repo + Docker (Postgres+Redis) + inventario normalizado + MedusaJS | 🔧 en curso |
| 1 | Storefront Next.js accesible (catálogo visual) | ⏳ |
| 2 | Bot Telegram texto: /stock, /precio, /pedidos (anti-alucinación) | ⏳ |
| 3 | Voz (Whisper) + agentes ventas/logística/reportes | ⏳ |
| 4 | Pagos Wompi/ePayco | ⏳ |
| 5 | Deploy Docker en VPS + monitor | ⏳ |

## Regla de oro: anti-alucinación

Stock y precios salen **siempre** de la base de datos (MedusaJS/Postgres),
**nunca** de un LLM. El LLM solo interpreta lenguaje natural; los datos son la
fuente única de verdad.

## Inventario

- Fuente: `inventario_FINAL_con_stock_simulado.csv` (679 filas, 608 productos).
- `data/normalize_inventory.py` → normaliza a `data/inventario.json` (productos
  con variantes por color/talla).
- `data/price_fixes.csv` → correcciones editables de precio para las variantes
  que venían en $0 (4 recuperadas del nombre, 28 estimadas a confirmar).

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
│   └── bot/                # Telegram (Fase 2)
└── *.md / *.docx           # documentos de arquitectura (JARVIS, ciclismo)
```
