#!/usr/bin/env python3
"""
Mapeo imagen -> producto para el catálogo de ciclismo.

Recorre la carpeta drive-download (NO se commitea: binarios) y asocia cada imagen
con un producto de data/inventario.json. Genera data/imagenes_map.json.

Cómo cruza (DERIVACIÓN, sin inventar nada):
  1. Patrón "<Nombre> mod <ID> Precio<n> [(<variación>)].<ext>": se extrae el <ID>
     y se cruza contra product_id (único). La (<variación>) se guarda como metadato
     (para ordenar la galería); el Precio<n> del nombre NO altera precios.
  2. Las imágenes SIN ese patrón (productos SIN_ID y nombres con IDs embebidos) se
     cruzan por NOMBRE + categoría (carpeta) contra el title del producto.

La categoría de la imagen = carpeta contenedora (1-RK, 6-CL, PITILLOS, UÑAS, ...),
que coincide 1:1 con inventario.category.

Lo que no cruza con confianza se LISTA para el dueño (no se adivina).

Uso:  python3 data/mapear_imagenes.py
"""
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INVENTARIO = ROOT / "data" / "inventario.json"
DRIVE = ROOT / "drive-download-20250611T144345Z-1-001"
OUT = ROOT / "data" / "imagenes_map.json"

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}
MOD_RE = re.compile(r"\bmod\.?\s+([A-Za-z0-9][A-Za-z0-9.\-]*)", re.IGNORECASE)


def strip_accents(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def slugify(s: str) -> str:
    s = strip_accents(s).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)[:80]
    return re.sub(r"-+$", "", s)


def norm_name(s: str) -> str:
    """Normaliza un nombre para cruce difuso (sin precio, sin paréntesis, sin
    puntuación). Solo deriva, no inventa."""
    s = strip_accents(s).lower()
    s = re.sub(r"\bprecios?\s*aprox\s*\d+", " ", s)
    s = re.sub(r"\bprecio\s*\d+", " ", s)
    s = re.sub(r"\$\s*\d+", " ", s)
    s = re.sub(r"\([^)]*\)", " ", s)            # quita variación / anotaciones
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def extract_variacion(stem: str) -> str:
    m = re.findall(r"\(([^)]*)\)", stem)
    return m[-1].strip() if m else ""


def main():
    products = json.loads(INVENTARIO.read_text(encoding="utf-8"))

    # índices
    by_id = {}              # PRODUCT_ID(upper) -> producto (único, sin SIN_ID)
    by_cat_norm = {}        # categoria -> [(norm_name, producto)]
    used_handle = set()
    for p in products:
        if p["product_id"] != "SIN_ID":
            by_id[p["product_id"].upper()] = p
        by_cat_norm.setdefault(p["category"], []).append((norm_name(p["name"]), p))
        # handle idéntico al seed (para exponerlo en el map)
        h = slugify(p["name"]) or p["product_id"].lower()
        base, i = h, 1
        while h in used_handle:
            i += 1
            h = f"{base}-{i}"
        used_handle.add(h)
        p["_handle"] = h

    images = sorted(
        [f for f in DRIVE.rglob("*") if f.is_file() and f.suffix.lower() in IMG_EXT]
    )
    total = len(images)

    mapping = {}
    unmapped = []
    by_method = Counter()

    for img in images:
        rel = str(img.relative_to(ROOT))
        categoria = img.parent.name          # carpeta = código interno
        stem = img.stem
        prod = None
        method = None

        # 1) cruce por ID (patrón "mod <ID>")
        m = MOD_RE.search(stem)
        if m:
            pid = m.group(1).rstrip(".-").upper()
            prod = by_id.get(pid)
            if prod:
                method = "id"

        # 2) cruce por nombre + categoría
        if not prod:
            fn = norm_name(stem)
            best, best_len = None, 0
            for nm, cand in by_cat_norm.get(categoria, []):
                if not nm:
                    continue
                if fn == nm or fn.startswith(nm) or nm.startswith(fn):
                    if len(nm) > best_len:
                        best, best_len = cand, len(nm)
            if best:
                prod, method = best, "nombre"

        if not prod:
            unmapped.append(rel)
            continue

        by_method[method] += 1
        mapping[rel] = {
            "product_id": prod["product_id"],
            "handle": prod["_handle"],
            "name": prod["name"],
            "codigo_interno": prod["category"],
            "variacion": extract_variacion(stem),
            "match": method,
        }

    OUT.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")

    mapeadas = len(mapping)
    pct = 100 * mapeadas / total
    productos_con_img = len({v["product_id"] + "::" + v["codigo_interno"] for v in mapping.values()})

    print("=" * 64)
    print(f"MAPEO imagen->producto  (drive-download -> {OUT.name})")
    print("=" * 64)
    print(f"mapeadas {mapeadas}/{total}  ({pct:.1f}%)   umbral >=646 (>=95%)")
    print(f"  por ID (mod <ID>):     {by_method['id']}")
    print(f"  por nombre+categoría:  {by_method['nombre']}")
    print(f"  productos distintos con >=1 imagen: {productos_con_img}")
    print("-" * 64)
    print(f"NO MAPEADAS (LISTA para el dueño, {len(unmapped)}):")
    for rel in unmapped:
        print(f"  {rel}")
    print("=" * 64)

    ok = mapeadas >= 646
    print(f"RESULTADO: {'OK' if ok else 'FALLA'} (>=646 mapeadas) -> {mapeadas}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
