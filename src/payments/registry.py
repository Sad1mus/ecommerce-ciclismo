"""Registro de proveedores de pago. Todo arranca DESACTIVADO (solo sandbox)."""
from __future__ import annotations

from base import PaymentProvider
from epayco import EpaycoProvider
from wompi import WompiProvider

# Proveedores disponibles. sandbox=True por defecto: codigo listo, no activado.
_PROVIDERS = {
    "wompi": WompiProvider,
    "epayco": EpaycoProvider,
}


def get_provider(name: str, sandbox: bool = True) -> PaymentProvider:
    cls = _PROVIDERS.get(name.lower())
    if not cls:
        raise ValueError(f"Proveedor de pago desconocido: {name}")
    return cls(sandbox=sandbox)


def available_providers() -> list[str]:
    return sorted(_PROVIDERS)


def activation_status() -> dict[str, dict]:
    """Reporte de que falta para activar cada proveedor (secretos ausentes)."""
    status = {}
    for name in available_providers():
        p = get_provider(name)
        status[name] = {
            "sandbox": p.sandbox,
            "activatable": p.is_activatable(),
            "missing_secrets": p.missing_secrets(),
        }
    return status
