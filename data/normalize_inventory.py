#!/usr/bin/env python3
"""
Normaliza el CSV de inventario de ciclismo a un JSON limpio listo para
sembrar en MedusaJS v2.

Regla de oro del proyecto (anti-alucinacion): el stock y los precios son la
fuente unica de verdad y vienen SIEMPRE del inventario / DB, nunca de un LLM.
Este script solo reordena los datos del CSV, no inventa ni modifica valores.

Entrada : inventario_FINAL_con_stock_simulado.csv
          columnas: Categoria, ID_Producto, Nombre_Producto, Variacion,
                    Precio_Venta, Stock
Salida  : data/inventario.json
          [
            {
              "category": "1-RK",
              "product_id": "GB30C",
              "name": "Guante mtb corto",
              "variants": [
                {"variation": "Azul", "price_cop": 34500, "stock": 34},
                ...
              ]
            },
            ...
          ]

Productos con una sola fila y Variacion vacia -> una variante "default".
Productos con varias filas (mismo ID_Producto) -> una variante por color/talla.
"""
import csv
import json
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "inventario_FINAL_con_stock_simulado.csv"
FIXES_PATH = ROOT / "data" / "price_fixes.csv"
OUT_PATH = ROOT / "data" / "inventario.json"


def load_price_fixes() -> list[dict]:
    """Carga data/price_fixes.csv (ignora lineas que empiezan con #)."""
    if not FIXES_PATH.exists():
        return []
    with FIXES_PATH.open(encoding="utf-8", newline="") as fh:
        lines = [ln for ln in fh if not ln.lstrip().startswith("#")]
    fixes = []
    for r in csv.DictReader(lines):
        fixes.append({
            "match": r["match_nombre"].strip().lower(),
            "price": int(r["precio_cop"]),
            "source": r["source"].strip(),
        })
    return fixes


def apply_price_fix(name: str, fixes: list[dict]):
    """Devuelve (precio, source) de la primera regla cuyo patron este en name."""
    low = name.lower()
    for f in fixes:
        if f["match"] and f["match"] in low:
            return f["price"], f["source"]
    return None, None


def parse_int(value: str, field: str, row_num: int) -> int:
    value = (value or "").strip()
    if value == "":
        raise ValueError(f"fila {row_num}: campo '{field}' vacio")
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"fila {row_num}: '{field}'='{value}' no es entero")


def main() -> int:
    if not CSV_PATH.exists():
        print(f"ERROR: no existe {CSV_PATH}", file=sys.stderr)
        return 1

    fixes = load_price_fixes()
    products: "OrderedDict[str, dict]" = OrderedDict()
    name_conflicts: list[str] = []
    errors: list[str] = []
    fixes_applied: list[str] = []
    rows_read = 0

    with CSV_PATH.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        expected = ["Categoria", "ID_Producto", "Nombre_Producto",
                    "Variacion", "Precio_Venta", "Stock"]
        if reader.fieldnames != expected:
            print(f"ERROR: cabecera inesperada.\n  esperado={expected}\n"
                  f"  encontrado={reader.fieldnames}", file=sys.stderr)
            return 1

        for i, row in enumerate(reader, start=2):  # fila 1 = cabecera
            rows_read += 1
            pid = (row["ID_Producto"] or "").strip()
            name = (row["Nombre_Producto"] or "").strip()
            category = (row["Categoria"] or "").strip()
            variation = (row["Variacion"] or "").strip()

            if not pid:
                errors.append(f"fila {i}: ID_Producto vacio")
                continue

            # Productos SIN SKU real ("SIN_ID"): cada fila es un producto
            # distinto, NO variantes del mismo. Le damos una clave sintetica
            # unica por fila para no fusionarlos por error.
            group_key = pid if pid != "SIN_ID" else f"SIN_ID__row{i}"

            try:
                price = parse_int(row["Precio_Venta"], "Precio_Venta", i)
                stock = parse_int(row["Stock"], "Stock", i)
            except ValueError as e:
                errors.append(str(e))
                continue

            if group_key not in products:
                products[group_key] = {
                    "category": category,
                    "product_id": pid,
                    "name": name,
                    "variants": [],
                }
            else:
                # mismo ID con nombre distinto -> lo anotamos pero conservamos el primero
                if products[group_key]["name"] != name:
                    name_conflicts.append(
                        f"{pid}: '{products[group_key]['name']}' vs '{name}' (fila {i})"
                    )

            price_source = "csv"
            if price == 0:
                fixed_price, src = apply_price_fix(name, fixes)
                if fixed_price is not None:
                    price = fixed_price
                    price_source = src  # "recuperado" o "estimado"
                    fixes_applied.append(f"{src}: {name[:50]} -> {price:,}")

            products[group_key]["variants"].append({
                "variation": variation if variation else "Unica",
                "price_cop": price,
                "price_source": price_source,
                "stock": stock,
                # vendible solo si tiene precio confirmado (no estimado, no 0)
                "sellable": price > 0 and price_source != "estimado",
            })

    if errors:
        print("ERRORES (filas descartadas):", file=sys.stderr)
        for e in errors:
            print("  -", e, file=sys.stderr)

    product_list = list(products.values())
    total_variants = sum(len(p["variants"]) for p in product_list)
    total_units = sum(v["stock"] for p in product_list for v in p["variants"])
    all_prices = [v["price_cop"] for p in product_list for v in p["variants"]]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(product_list, fh, ensure_ascii=False, indent=2)

    # Resumen por categoria
    by_cat: "OrderedDict[str, int]" = OrderedDict()
    for p in product_list:
        by_cat[p["category"]] = by_cat.get(p["category"], 0) + 1

    print("=== RESUMEN NORMALIZACION ===")
    print(f"Filas leidas (sin cabecera) : {rows_read}")
    print(f"Productos unicos            : {len(product_list)}")
    print(f"Variantes totales           : {total_variants}")
    print(f"Unidades en stock (suma)    : {total_units}")
    if all_prices:
        print(f"Precio min / max (COP)      : {min(all_prices):,} / {max(all_prices):,}")
    print(f"Categorias                  : {len(by_cat)}")
    for cat, n in by_cat.items():
        print(f"    {cat:<22} {n} productos")
    # --- Calidad de datos: a revisar antes de vender ---
    still_zero = [v for p in product_list for v in p["variants"] if v["price_cop"] == 0]
    recuperado = [v for p in product_list for v in p["variants"] if v["price_source"] == "recuperado"]
    estimado = [v for p in product_list for v in p["variants"] if v["price_source"] == "estimado"]
    not_sellable = [v for p in product_list for v in p["variants"] if not v["sellable"]]
    sin_id = [p for p in product_list if p["product_id"] == "SIN_ID"]

    print("\n=== CALIDAD DE DATOS ===")
    print(f"Precios recuperados del nombre : {len(recuperado)}")
    print(f"Precios estimados (CONFIRMAR)  : {len(estimado)}")
    print(f"Variantes aun en $0            : {len(still_zero)}")
    print(f"NO vendibles (draft en tienda) : {len(not_sellable)}  (precio 0 o estimado)")
    print(f"Productos sin SKU real (SIN_ID): {len(sin_id)}  -> SKU sintetico al sembrar")
    if name_conflicts:
        print(f"IDs con nombre inconsistente   : {len(name_conflicts)} (se conservo el primero)")

    print(f"\nEscrito -> {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
