"""Tests de las herramientas de consulta (lectura) con Medusa MOCKEADO."""
from formatting import DATO_NO_DISPONIBLE, is_screen_reader_safe
from medusa_client import OrderDetail, OrderInfo, OrderLine, ProductInfo
from testing_fakes import FailingClient, FakeClient
import tools

PRODS = [
    ProductInfo(title="Candado espiral", sku="CL1", price=14500, currency="COP", stock=8),
    ProductInfo(title="Candado clave", sku="CL2", price=11500, currency="COP", stock=2),
]


def test_consultar_producto_da_stock_y_precio():
    out = tools.consultar_producto(FakeClient(productos=PRODS), "candado")
    assert "Candado espiral" in out and "14.500" in out and "8 disponibles" in out
    assert is_screen_reader_safe(out)


def test_consultar_producto_sin_resultados():
    assert "Sin resultados" in tools.consultar_producto(FakeClient(productos=[]), "xyz")


def test_consultar_producto_api_caida_no_inventa():
    assert tools.consultar_producto(FailingClient(), "candado") == DATO_NO_DISPONIBLE


def test_consultar_pedido_detalle():
    det = OrderDetail(
        id="order_1", display_id=1001, status="pending", payment_status="captured",
        fulfillment_status="not_fulfilled", total=26000, currency="COP",
        items=[OrderLine(title="Candado espiral", quantity=2)],
        metadata={"factura_numero": "F-001"},
    )
    out = tools.consultar_pedido(FakeClient(detalles={1001: det}), 1001)
    assert "Pedido 1001" in out and "2 x Candado espiral" in out and "F-001" in out
    assert is_screen_reader_safe(out)


def test_consultar_pedido_inexistente():
    out = tools.consultar_pedido(FakeClient(detalles={}), 9999)
    assert "9999" in out and "no" in out.lower()


def test_listar_pedidos_pendientes():
    peds = [OrderInfo(display_id=1001, status="pending", total=26000, currency="COP")]
    out = tools.listar_pedidos_pendientes(FakeClient(pedidos=peds))
    assert "1001" in out and is_screen_reader_safe(out)


def test_reporte_stock_bajo():
    out = tools.reporte_stock_bajo(FakeClient(productos=PRODS), "candado", umbral=5)
    assert "Candado clave" in out and "Candado espiral" not in out  # solo el de stock 2


def test_execute_tool_desconocida():
    assert "desconocida" in tools.execute_tool("no_existe", {}, FakeClient()).lower()


def test_execute_tool_envuelve_errores():
    # API caida a traves del despachador -> dato no disponible (anti-alucinacion)
    assert tools.execute_tool("consultar_producto", {"consulta": "x"}, FailingClient()) == DATO_NO_DISPONIBLE
