"""Tests de los agentes de ventas, logistica y reportes (Medusa MOCKEADO).

Verifican que los agentes usan SOLO datos de la API y que ante fallo no inventan.
"""
from agents import LogisticaAgent, ReportesAgent, VentasAgent
from formatting import DATO_NO_DISPONIBLE, has_emoji, is_screen_reader_safe
from testing_fakes import FailingClient, FakeClient


# ---------- Ventas ----------
def test_ventas_usa_precio_y_stock_de_la_api(productos_demo):
    agente = VentasAgent(FakeClient(productos=productos_demo))
    salida = agente.consultar("candado")
    assert "14.500" in salida
    assert "8 disponibles" in salida
    assert is_screen_reader_safe(salida)


def test_ventas_api_caida_no_inventa():
    agente = VentasAgent(FailingClient())
    salida = agente.consultar("candado")
    assert salida == DATO_NO_DISPONIBLE
    assert "$" not in salida


# ---------- Logistica ----------
def test_logistica_lista_estados_reales(pedidos_demo):
    agente = LogisticaAgent(FakeClient(pedidos=pedidos_demo))
    salida = agente.estado_pedidos()
    assert "Pedido 1001" in salida
    assert "completed" in salida
    assert "pending" in salida
    assert not has_emoji(salida)


def test_logistica_api_caida_no_inventa():
    assert LogisticaAgent(FailingClient()).estado_pedidos() == DATO_NO_DISPONIBLE


# ---------- Reportes ----------
def test_reportes_stock_bajo_calculado_de_la_api(productos_demo):
    agente = ReportesAgent(FakeClient(productos=productos_demo))
    salida = agente.stock_bajo("candado", umbral=5)
    # Candado clave (stock 2) <= 5 entra; Candado espiral (8) no.
    assert "Candado clave" in salida
    assert "Candado espiral" not in salida


def test_reportes_resumen_suma_unidades_reales(productos_demo):
    agente = ReportesAgent(FakeClient(productos=productos_demo))
    salida = agente.resumen("candado")
    # 8 + 2 = 10 unidades (el de stock None no suma).
    assert "Unidades totales en stock: 10" in salida
    assert "Con stock informado: 2" in salida


def test_reportes_api_caida_no_inventa():
    assert ReportesAgent(FailingClient()).resumen("x") == DATO_NO_DISPONIBLE
    assert ReportesAgent(FailingClient()).stock_bajo("x") == DATO_NO_DISPONIBLE
