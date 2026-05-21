"""Fixtures compartidos por los tests del bot."""
import pytest

from medusa_client import OrderInfo, ProductInfo


@pytest.fixture
def productos_demo():
    return [
        ProductInfo(title="Candado espiral", sku="CL1", price=14500, currency="COP", stock=8),
        ProductInfo(title="Candado clave", sku="CL2", price=18500, currency="COP", stock=2),
        ProductInfo(title="Bomba mini", sku="B1", price=18500, currency="COP", stock=None),
    ]


@pytest.fixture
def pedidos_demo():
    return [
        OrderInfo(display_id=1001, status="completed", total=34000, currency="COP"),
        OrderInfo(display_id=1002, status="pending", total=52000, currency="COP"),
    ]
