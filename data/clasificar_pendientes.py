#!/usr/bin/env python3
"""Clasificacion BEST-EFFORT de los pendientes del catalogo + auditoria.

Contexto (decision consciente del dueño): cerrar el catalogo sin esperar sus datos,
asignando "lo mas cercano segun el contexto" a lo que quedo sin categoria, y dejando
los precios estimados como BORRADOR NO COMPRABLE. TODO lo derivado se AUDITA en
data/catalogo_provisional.json para que el update de inventario posterior sea
quirurgico. Habra un update de inventario obligatorio despues.

Este script es OFFLINE y REVERSIBLE: solo lee archivos locales y escribe el JSON de
auditoria. NO toca Medusa (esa es la parte B, que muta el catalogo real y corre
aparte con el stack vivo).

Fuentes (no se inventan datos, se DERIVAN):
  - data/categorias_map.json : los que quedaron en "Otros / por clasificar" (los 59).
  - data/price_fixes.csv     : las filas source=estimado (los 28 precios a confirmar).

Uso:  python3 data/clasificar_pendientes.py
"""
import csv
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATEGORIAS_MAP = ROOT / "data" / "categorias_map.json"
PRICE_FIXES = ROOT / "data" / "price_fixes.csv"
OUT = ROOT / "data" / "catalogo_provisional.json"

OTROS = "Otros / por clasificar"


def norm(s: str) -> str:
    """minusculas sin acentos, para casar reglas de forma robusta."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower().strip()


# Reglas best-effort para los pendientes. Orden: gana la primera que casa. Cada una
# lleva la CONFIANZA (alta/media/baja) y el motivo, que quedan auditados. Lo que no
# casa con ninguna se marca 'revisar' y se LISTA (no se fuerza un tipo inventado).
def clasificar_pendiente(name: str, codigo_interno: str):
    """Devuelve (tipo, confianza, motivo). tipo=None -> queda en 'Otros' (revisar)."""
    n = norm(name)
    cod = (codigo_interno or "").strip().upper()

    # Pitillos (accesorio de rueda por color). Los colores sueltos ("1 Gris"...) no
    # dicen "pitillo" en el nombre, pero su codigo interno es PITILLOS.
    if "pitillo" in n or cod == "PITILLOS":
        return "Llantas, rines y aros", "baja", "pitillos de rueda por color (codigo PITILLOS), a confirmar"

    if "espaciador" in n:
        return "Manubrios y potencias", "alta", "espaciador de direccion (va en la espiga/steerer)"
    if "espiga" in n:
        return "Manubrios y potencias", "media", "espiga de direccion"
    if "paral" in n:
        return "Soportes y portacelular", "alta", "paral lateral = pata de apoyo (kickstand)"
    if "abrazadera" in n:
        return "Sillines y tijas", "baja", "abrazadera de sillin/tija (clamp), a confirmar"
    if "tornillo" in n:
        return "Kits y herramientas", "media", "tornilleria / herrajes"
    if "cubierta" in n:
        return "Llantas, rines y aros", "baja", "'cubierta' suele ser neumatico exterior, a confirmar"

    # Sin señal suficiente: mascaras/tapabocas, llaveros, bicis de exhibicion,
    # stickers, pila, 'pets', capa, accesorio multiproposito -> se LISTAN para revisar.
    return None, "revisar", "sin señal clara en el nombre; requiere decision del dueño"


def cargar_otros() -> list[dict]:
    data = json.loads(CATEGORIAS_MAP.read_text(encoding="utf-8"))
    otros = []
    for entry in data.values():
        if entry.get("tipo") == OTROS:
            otros.append(entry)
    return otros


def cargar_estimados() -> list[dict]:
    filas = []
    with PRICE_FIXES.open(encoding="utf-8") as fh:
        for row in csv.DictReader(l for l in fh if not l.startswith("#")):
            if (row.get("source") or "").strip() == "estimado":
                filas.append(row)
    return filas


def main() -> int:
    otros = cargar_otros()
    estimados = cargar_estimados()

    derivadas = []
    conf = Counter()
    revisar = []
    for e in sorted(otros, key=lambda x: (x.get("codigo_interno", ""), x.get("name", ""))):
        tipo, confianza, motivo = clasificar_pendiente(e.get("name", ""), e.get("codigo_interno", ""))
        conf[confianza] += 1
        registro = {
            "product_id": e.get("product_id", ""),
            "name": e.get("name", ""),
            "codigo_interno": e.get("codigo_interno", ""),
            "tipo_asignado": tipo,          # None => sigue en "Otros"
            "confianza": confianza,
            "motivo": motivo,
        }
        derivadas.append(registro)
        if tipo is None:
            revisar.append(e.get("name", ""))

    precios = [
        {
            "match_nombre": r.get("match_nombre", ""),
            "precio_estimado_cop": int(r.get("precio_cop") or 0),
            "accion": "borrador (status=draft en Medusa, NO comprable)",
            "nota": r.get("nota", ""),
        }
        for r in estimados
    ]

    auditoria = {
        "generado_por": "data/clasificar_pendientes.py",
        "advertencia": (
            "BEST-EFFORT consciente. Categorias derivadas por contexto (no confirmadas "
            "por el dueño); precios estimados quedan NO comprables. Requiere un update "
            "de inventario y la confirmacion del dueño."
        ),
        "categorias_derivadas": derivadas,
        "precios_estimados_borrador": precios,
    }
    OUT.write_text(json.dumps(auditoria, ensure_ascii=False, indent=2), encoding="utf-8")

    con_tipo = sum(1 for d in derivadas if d["tipo_asignado"])
    print("=" * 64)
    print("CATALOGO BEST-EFFORT — clasificacion de pendientes + auditoria")
    print("=" * 64)
    print(f"categorizados {len(derivadas)}/{len(derivadas)} procesados "
          f"(con tipo best-effort: {con_tipo}, a revisar: {len(revisar)})")
    for c in ("alta", "media", "baja", "revisar"):
        if conf[c]:
            print(f"    confianza {c:<7}: {conf[c]}")
    print("-" * 64)
    print(f"precios en borrador {len(precios)}/{len(precios)} (draft, NO comprables)")
    print("-" * 64)
    if revisar:
        print(f"A REVISAR (sin tipo forzado, {len(revisar)}):")
        for name in sorted(revisar):
            print(f"    - {name}")
    print("-" * 64)
    print(f"auditoria -> {OUT.relative_to(ROOT)}")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
