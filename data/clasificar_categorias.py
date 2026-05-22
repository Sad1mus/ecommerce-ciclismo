#!/usr/bin/env python3
"""
Clasificador nombre -> tipo de compra para el catálogo de ciclismo.

Lee data/inventario.json (608 productos, fuente del admin) y DERIVA una categoría
de compra legible para el cliente a partir del NOMBRE del producto. Genera
data/categorias_map.json: external_id/product_id/handle -> {tipo, codigo_interno}.

ANTI-ALUCINACIÓN:
  - Solo se DERIVA el tipo desde el nombre con reglas explícitas. No se inventan
    datos, no se tocan precios ni stock. El código interno (1-RK, 6-CL, ...) NO se
    pierde: queda como codigo_interno para guardarlo luego en metadata del producto.
  - Lo que no cae con confianza en un tipo va a "Otros / por clasificar" y se LISTA
    para que el dueño decida (nunca se adivina el tipo).

Uso:
    python3 data/clasificar_categorias.py

El handle se calcula igual que el seed (slugify del nombre) para poder cruzar.
"""
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INVENTARIO = ROOT / "data" / "inventario.json"
OUT = ROOT / "data" / "categorias_map.json"

OTROS = "Otros / por clasificar"


def norm(s: str) -> str:
    """minúsculas sin acentos, para casar reglas de forma robusta."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower().strip()


def slugify(s: str) -> str:
    """Mismo slug que el seed (seed-ciclismo.ts) para cruzar por handle."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    s = s[:80]
    s = re.sub(r"-+$", "", s)
    return s


def has(n: str, *subs: str) -> bool:
    return any(sub in n for sub in subs)


def word(n: str, *words: str) -> bool:
    return any(re.search(r"\b" + re.escape(w) + r"\b", n) for w in words)


def clasificar(name: str) -> str:
    """Devuelve el tipo de compra. Reglas ordenadas: gana la primera que casa.

    El ORDEN importa (un nombre puede contener varias palabras clave):
    primero los tipos específicos, "luz"/"kit" quedan al final como red de
    arrastre, y lo dudoso cae a OTROS.
    """
    n = norm(name)

    # --- Sillines y tijas (antes que Luces: "Silla mtb luz incorp gel") ---
    if has(n, "sillin", "silla", "forro", "tija") or word(n, "cana"):
        return "Sillines y tijas"

    # --- Cascos (no confundir "biccasco" de las luces) ---
    if word(n, "casco"):
        return "Cascos"

    if has(n, "gafa"):
        return "Gafas"
    if has(n, "guante"):
        return "Guantes"
    if has(n, "candado"):
        return "Candados"

    # --- Pedales y calas (antes que Luces: "Pedal mtb luz recargable") ---
    if has(n, "pedal", "calapies", "chocles") or word(n, "cala", "calas"):
        return "Pedales y calas"

    if has(n, "guardabarro"):
        return "Guardabarros"
    if has(n, "suspension"):
        return "Suspensión"

    # --- Hidratación (caramañolas / termo) ---
    if has(n, "caramanola", "caramañola", "termo"):
        return "Hidratación"

    # --- Bolsos (antes que Kits: "Kit bolso ..."; antes que Luces) ---
    if has(n, "bolso", "hydropack", "vejiga", "portaherramienta", "portaheramienta", "alforja"):
        return "Bolsos"

    # --- Mangos y grips (antes que Frenos: "Mangos con protector freno") ---
    if has(n, "mango", "grips"):
        return "Mangos y grips"

    # --- Llantas, rines y aros (incl. válvulas, cintas de rin/tubeless, manzanas) ---
    if (word(n, "rin", "aro", "aros", "llanta", "neumatico", "manzana", "manzanas",
              "eje", "ejes", "nucleo", "radio", "radios")
            or has(n, "antipinchazos", "tubeless", "valvula")):
        return "Llantas, rines y aros"

    # --- Transmisión (cadena/coronilla/piñón/cassette/tensor/biela...) ---
    if has(n, "cadena", "cadenilla", "coronilla", "monoplato", "biplato", "pacha",
           "pinon", "descarrilador", "rodaja", "caja centro", "biela", "tensor",
           "cartucho", "pguaya", "pfunda"):
        # cartucho = eje/caja centro tipo cartucho; pguaya/pfunda = terminales de
        # guaya y funda (cableado de cambios/freno). Derivación, no invención.
        return "Transmisión"
    if has(n, "palanca") and (has(n, "vel", "integ")):
        return "Transmisión"

    # --- Frenos, pastillas y rotores ---
    if has(n, "pastilla", "zapatas", "rotor", "freno", "purga", "disco"):
        return "Frenos, pastillas y rotores"

    # --- Manubrios y potencias (codo = potencia/stem) ---
    # Accesorios de manubrio (cinta/tapones/timbre...) se resuelven después,
    # pero "manubrio"/"manilar"/"codo" como pieza van aquí. Los accesorios usan
    # palabras propias (cinta, timbre, espejo...) que se chequean luego, así que
    # excluimos explícitamente esos nombres aquí.
    if (has(n, "manubrio", "manilar", "codo")
            and not has(n, "cinta", "tapon", "accesorio", "timbre", "espejo", "retrovisor")):
        return "Manubrios y potencias"

    # --- Soportes y portacelular (antes que Luces/Bombas: "Soporte Pluz", "PInflador") ---
    if has(n, "soporte", "portacelular", "portacamara", "porta camara"):
        return "Soportes y portacelular"

    # --- Bombas e infladores ---
    if has(n, "bomba", "inflador"):
        return "Bombas e infladores"

    # --- Protección de cuadro (marco / downtube / puntas de marco) ---
    if has(n, "pmarco", "downtube", "neopreno", "punta de marco", "punta pmarco",
           "puntapmarco", "protecciones adhesivas"):
        return "Protección de cuadro"

    # --- Accesorios de manubrio (timbre, espejo, cinta, parlante, velocímetro...) ---
    if has(n, "campana", "timbre", "espejo", "retrovisor", "cinta", "parlante",
           "velocimetro", "pito", "corneta", "alarma") \
            or (has(n, "tapon", "tapones") and has(n, "manubrio")) \
            or (has(n, "accesorio") and has(n, "manubrio")):
        return "Accesorios de manubrio"

    # --- Luces (red de arrastre tardía: ya filtramos pedal/silla/bolso con "luz") ---
    if has(n, "luz", "luces", "luminic", "luminis"):
        return "Luces"

    # --- Kits y herramientas (red de arrastre final) ---
    if has(n, "kit", "herramienta", "cepillo", "limpieza", "despinche", "parche",
           "parches", "estacion de mantenimiento", "extractor") \
            or (has(n, "palanca") and has(n, "desmonte")):
        return "Kits y herramientas"

    return OTROS


def main():
    products = json.loads(INVENTARIO.read_text(encoding="utf-8"))
    total = len(products)

    mapping = {}
    by_tipo = Counter()
    otros = []
    used_handle = set()

    for p in products:
        name = p["name"]
        codigo = p["category"]
        pid = p["product_id"]
        external_id = f"{codigo}::{pid}::{name}"[:250]

        # handle único igual que el seed (slug + sufijo si choca)
        h = slugify(name) or pid.lower()
        base = h
        i = 1
        while h in used_handle:
            i += 1
            h = f"{base}-{i}"
        used_handle.add(h)

        tipo = clasificar(name)
        by_tipo[tipo] += 1
        if tipo == OTROS:
            otros.append((codigo, pid, name))

        mapping[external_id] = {
            "product_id": pid,
            "handle": h,
            "name": name,
            "tipo": tipo,
            "codigo_interno": codigo,
        }

    OUT.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")

    clasificados = total - by_tipo[OTROS]
    pct = 100 * clasificados / total

    print("=" * 64)
    print(f"CLASIFICADOR nombre->tipo  ({INVENTARIO.name} -> {OUT.name})")
    print("=" * 64)
    print(f"clasificados {clasificados}/{total}  ({pct:.1f}%)   umbral >=548 (>=90%)")
    print(f"en '{OTROS}': {by_tipo[OTROS]}")
    print("-" * 64)
    print("CONTEO POR TIPO:")
    for tipo, n in sorted(by_tipo.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {n:4d}  {tipo}")
    print("-" * 64)
    print(f"OTROS / POR CLASIFICAR (LISTA para el dueño, {len(otros)}):")
    for codigo, pid, name in sorted(otros):
        print(f"  [{codigo:>16}] {pid:>8}  {name}")
    print("=" * 64)

    ok = clasificados >= 548
    print(f"RESULTADO: {'OK' if ok else 'FALLA'} (>=548 clasificados) -> {clasificados}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
