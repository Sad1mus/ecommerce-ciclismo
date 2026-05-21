"""Logica de los comandos del bot: /stock, /precio, /pedidos.

Cada handler es una funcion PURA (recibe el cliente Medusa y los argumentos,
devuelve un string). Esto las hace testeables sin Telegram ni red real.

ANTI-ALUCINACION: si el cliente lanza cualquier excepcion (API caida, timeout,
auth), el handler devuelve DATO_NO_DISPONIBLE. Jamas se inventan cifras.
"""
from __future__ import annotations

from formatting import DATO_NO_DISPONIBLE, clamp_lines, format_cop
from medusa_client import MedusaClient


def handle_stock(client: MedusaClient, query: str) -> str:
    query = (query or "").strip()
    if not query:
        return "Indica que producto consultar. Ejemplo: /stock candado"
    try:
        productos = client.search_products(query)
    except Exception:
        return DATO_NO_DISPONIBLE
    if not productos:
        return f"Sin resultados para: {query}"
    lineas = [f"Stock para: {query}"]
    for p in productos:
        if p.stock is None:
            lineas.append(f"{p.title}: stock no disponible")
        else:
            lineas.append(f"{p.title}: {p.stock} unidades")
    return clamp_lines("\n".join(lineas))


def handle_precio(client: MedusaClient, query: str) -> str:
    query = (query or "").strip()
    if not query:
        return "Indica que producto consultar. Ejemplo: /precio candado"
    try:
        productos = client.search_products(query)
    except Exception:
        return DATO_NO_DISPONIBLE
    if not productos:
        return f"Sin resultados para: {query}"
    lineas = [f"Precio para: {query}"]
    for p in productos:
        lineas.append(f"{p.title}: {format_cop(p.price, p.currency)}")
    return clamp_lines("\n".join(lineas))


def handle_pedidos(client: MedusaClient, limit: int = 5) -> str:
    try:
        pedidos = client.list_orders(limit=limit)
    except Exception:
        return DATO_NO_DISPONIBLE
    if not pedidos:
        return "No hay pedidos registrados."
    lineas = ["Ultimos pedidos:"]
    for o in pedidos:
        lineas.append(
            f"Pedido {o.display_id}: {o.status}, {format_cop(o.total, o.currency)}"
        )
    return clamp_lines("\n".join(lineas))
