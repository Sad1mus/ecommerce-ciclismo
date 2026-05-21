"""Tests de los proveedores de pago: TODO en sandbox, sin cobros reales."""
import os

import pytest

from base import PaymentProvider
from epayco import EpaycoProvider
from registry import activation_status, available_providers, get_provider
from wompi import WompiProvider


@pytest.mark.parametrize("name", ["wompi", "epayco"])
def test_sandbox_no_cobra_de_verdad(name):
    prov = get_provider(name, sandbox=True)
    res = prov.create_payment(amount=14500, currency="COP", reference="ORD-1")
    assert res.sandbox is True
    assert res.real_charge is False
    assert res.status == "sandbox_approved"
    assert res.amount == 14500


@pytest.mark.parametrize("name", ["wompi", "epayco"])
def test_referencia_decline_simula_rechazo(name):
    res = get_provider(name).create_payment(1000, "COP", "ORD-decline-2")
    assert res.status == "sandbox_declined"
    assert res.real_charge is False


def test_wompi_monto_en_centavos():
    payload = WompiProvider().build_payload(14500, "COP", "ORD-9")
    assert payload["amount_in_cents"] == 1450000  # 14500 * 100


def test_epayco_test_true_en_sandbox():
    payload = EpaycoProvider(sandbox=True).build_payload(14500, "COP", "ORD-9")
    assert payload["test"] == "true"


def test_no_activable_sin_secretos(monkeypatch):
    # Sin secretos ni bandera global => no activable.
    for k in (
        "ACTIVAR_PAGOS",
        "WOMPI_PRIVATE_KEY",
        "WOMPI_PUBLIC_KEY",
        "WOMPI_EVENTS_SECRET",
    ):
        monkeypatch.delenv(k, raising=False)
    prov = WompiProvider()
    assert prov.is_activatable() is False
    assert "WOMPI_PRIVATE_KEY" in prov.missing_secrets()


def test_modo_real_sin_secretos_se_rehusa(monkeypatch):
    # Intentar cobro real sin activacion debe LANZAR, nunca cobrar.
    monkeypatch.delenv("ACTIVAR_PAGOS", raising=False)
    prov = WompiProvider(sandbox=False)
    with pytest.raises(RuntimeError):
        prov.create_payment(1000, "COP", "ORD-3")


def test_activation_status_reporta_faltantes(monkeypatch):
    monkeypatch.delenv("ACTIVAR_PAGOS", raising=False)
    st = activation_status()
    assert set(st) == {"epayco", "wompi"}
    assert st["wompi"]["activatable"] is False
    assert st["wompi"]["missing_secrets"]  # lista no vacia


def test_proveedores_disponibles():
    assert available_providers() == ["epayco", "wompi"]
    assert isinstance(get_provider("wompi"), PaymentProvider)
