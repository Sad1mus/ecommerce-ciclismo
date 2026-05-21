"""Formato de respuestas APTO PARA LECTOR DE PANTALLA.

Reglas de accesibilidad del proyecto (admin no vidente + lector de pantalla):
 - Texto plano: sin emojis, sin iconos, sin arte ASCII.
 - Sin tablas ni columnas alineadas (un lector de pantalla las lee como ruido):
   nada de '|', tabuladores ni multiples espacios para alinear.
 - Respuestas cortas: maximo ~10 lineas.
 - Una idea por linea, con etiqueta explicita ("Stock:", "Precio:").
"""
from __future__ import annotations

MAX_LINES = 10
DATO_NO_DISPONIBLE = (
    "Dato no disponible en este momento. No fue posible consultar el inventario; "
    "intenta de nuevo mas tarde."
)

# Rango de emojis/simbolos pictograficos a rechazar.
_EMOJI_RANGES = [
    (0x1F300, 0x1FAFF),
    (0x2600, 0x27BF),
    (0x2190, 0x21FF),  # flechas decorativas
    (0xFE00, 0xFE0F),  # variation selectors
    (0x1F000, 0x1F0FF),
]


def has_emoji(text: str) -> bool:
    for ch in text:
        cp = ord(ch)
        for lo, hi in _EMOJI_RANGES:
            if lo <= cp <= hi:
                return True
    return False


def is_screen_reader_safe(text: str) -> bool:
    """True si el texto cumple las reglas: sin emojis, sin tablas, <= MAX_LINES."""
    if has_emoji(text):
        return False
    if "|" in text or "\t" in text:
        return False
    lines = text.splitlines()
    if len(lines) > MAX_LINES:
        return False
    return True


def clamp_lines(text: str) -> str:
    """Recorta a MAX_LINES lineas para no abrumar al lector de pantalla."""
    lines = text.splitlines()
    if len(lines) <= MAX_LINES:
        return text
    kept = lines[: MAX_LINES - 1]
    kept.append("Hay mas resultados; refina la busqueda.")
    return "\n".join(kept)


def format_cop(amount: int | None, currency: str = "COP") -> str:
    if amount is None:
        return "precio no disponible"
    # Separador de miles con punto (es-CO), sin decimales (COP sin subunidad).
    return f"${amount:,.0f}".replace(",", ".") + f" {currency}"
