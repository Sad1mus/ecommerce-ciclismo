"""Tests de las herramientas de categorias (publicas + codigos internos del dueño)."""
from formatting import DATO_NO_DISPONIBLE
from medusa_client import ProductInfo
from testing_fakes import FailingClient, FakeClient
import tools

CATS = [
    {"name": "Cascos", "is_active": True},
    {"name": "Candados", "is_active": True},
    {"name": "6-CL", "is_active": False},
    {"name": "PITILLOS", "is_active": False},
]
PRODS = [ProductInfo(title="Casco MTB", sku="C1", price=80000, currency="COP", stock=4, variant_id="v1")]


def test_listar_categorias_separa_publicas_e_internas():
    out = tools.listar_categorias(FakeClient(categorias=CATS))
    assert "Categorias de la tienda (2)" in out and "Cascos" in out
    assert "Codigos internos del dueño (2)" in out and "6-CL" in out


def test_listar_categorias_api_caida():
    assert tools.listar_categorias(FailingClient()) == DATO_NO_DISPONIBLE


def test_productos_por_categoria_publica():
    out = tools.productos_por_categoria(FakeClient(categorias=CATS, productos=PRODS), "Cascos")
    assert "Categoria Cascos: 1 productos" in out and "Casco MTB" in out


def test_productos_por_categoria_inexistente():
    out = tools.productos_por_categoria(FakeClient(categorias=CATS, productos=PRODS), "Inexistente")
    assert "No existe la categoria" in out


def test_buscar_por_codigo_interno():
    c = FakeClient(por_codigo={"6-CL": ["Llavero bici", "Sticker reflectivo", "Tornillos lujo"]})
    out = tools.buscar_por_codigo_interno(c, "6-cl")  # minuscula -> normaliza
    assert "Codigo 6-CL: 3 productos" in out and "Llavero bici" in out


def test_buscar_por_codigo_sin_resultados():
    out = tools.buscar_por_codigo_interno(FakeClient(por_codigo={}), "ZZZ")
    assert "No hay productos con el codigo interno ZZZ" in out


def test_buscar_por_codigo_vacio():
    assert "Falta el codigo" in tools.buscar_por_codigo_interno(FakeClient(), "")


def test_registradas_en_spec_y_registry():
    nombres = {t["function"]["name"] for t in tools.TOOLS_SPEC}
    for n in ("listar_categorias", "productos_por_categoria", "buscar_por_codigo_interno"):
        assert n in nombres and n in tools.REGISTRY
