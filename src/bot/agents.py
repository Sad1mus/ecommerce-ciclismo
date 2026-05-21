"""Agentes de negocio: ventas, logistica y reportes.

Cada agente trabaja SOLO con datos de Medusa (via MedusaClient). Nunca inventan
cifras: si la API falla, devuelven "dato no disponible". La salida respeta las
reglas de accesibilidad (texto plano, sin emojis ni tablas, corto).
"""
from __future__ import annotations

from formatting import DATO_NO_DISPONIBLE, clamp_lines, format_cop
from medusa_client import MedusaClient

UMBRAL_STOCK_BAJO = 5


class VentasAgent:
    """Responde disponibilidad y precio para apoyar una venta."""

    def __init__(self, client: MedusaClient) -> None:
        self.client = client

    def consultar(self, query: str) -> str:
        query = (query or "").strip()
        if not query:
            return "Indica el producto a cotizar."
        try:
            productos = self.client.search_products(query)
        except Exception:
            return DATO_NO_DISPONIBLE
        if not productos:
            return f"Sin resultados para: {query}"
        lineas = [f"Disponibilidad y precio para: {query}"]
        for p in productos:
            stock = "sin dato" if p.stock is None else (
                "agotado" if p.stock <= 0 else f"{p.stock} disponibles"
            )
            lineas.append(f"{p.title}: {format_cop(p.price, p.currency)}, {stock}")
        return clamp_lines("\n".join(lineas))


class LogisticaAgent:
    """Resume el estado de los pedidos para la bodega."""

    def __init__(self, client: MedusaClient) -> None:
        self.client = client

    def estado_pedidos(self, limit: int = 5) -> str:
        try:
            pedidos = self.client.list_orders(limit=limit)
        except Exception:
            return DATO_NO_DISPONIBLE
        if not pedidos:
            return "No hay pedidos para despachar."
        lineas = ["Estado de pedidos:"]
        for o in pedidos:
            lineas.append(f"Pedido {o.display_id}: {o.status}")
        return clamp_lines("\n".join(lineas))


class ReportesAgent:
    """Genera reportes simples calculados SOLO con datos reales de la API."""

    def __init__(self, client: MedusaClient) -> None:
        self.client = client

    def stock_bajo(self, query: str, umbral: int = UMBRAL_STOCK_BAJO) -> str:
        try:
            productos = self.client.search_products(query, limit=20)
        except Exception:
            return DATO_NO_DISPONIBLE
        bajos = [p for p in productos if isinstance(p.stock, int) and p.stock <= umbral]
        if not bajos:
            return f"Sin productos con stock menor o igual a {umbral} para: {query}"
        lineas = [f"Stock bajo (<= {umbral}) para: {query}"]
        for p in bajos:
            lineas.append(f"{p.title}: {p.stock} unidades")
        return clamp_lines("\n".join(lineas))

    def resumen(self, query: str) -> str:
        try:
            productos = self.client.search_products(query, limit=50)
        except Exception:
            return DATO_NO_DISPONIBLE
        con_stock = [p for p in productos if isinstance(p.stock, int)]
        total_unidades = sum(p.stock for p in con_stock)
        lineas = [
            f"Resumen para: {query}",
            f"Productos encontrados: {len(productos)}",
            f"Con stock informado: {len(con_stock)}",
            f"Unidades totales en stock: {total_unidades}",
        ]
        return clamp_lines("\n".join(lineas))
