"""Abstraccion de proveedores de pago colombianos (Wompi, ePayco).

CODIGO LISTO, NO ACTIVADO. Por defecto los proveedores operan en modo
SANDBOX/MOCK: no se realizan cobros reales ni se llama a la red. La activacion
exige secretos reales que NO viven en el repo (ver docs/activar-pagos.md).

Estados de un pago en sandbox:
  - "sandbox_approved": cobro simulado aprobado (real_charge=False).
  - "sandbox_declined": cobro simulado rechazado.
Nunca se devuelve un estado real sin activacion explicita + secretos.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class PaymentResult:
    provider: str
    reference: str
    amount: int
    currency: str
    status: str
    real_charge: bool
    sandbox: bool
    detail: str = ""
    raw: dict = field(default_factory=dict)


class PaymentProvider(ABC):
    """Contrato comun. Implementaciones: WompiProvider, EpaycoProvider."""

    name = "base"
    # Variables de entorno requeridas para activar el modo real.
    required_secrets: tuple[str, ...] = ()

    def __init__(self, sandbox: bool = True) -> None:
        # Por seguridad el default es sandbox. Solo se desactiva si ademas
        # estan presentes los secretos y la bandera global de activacion.
        self.sandbox = sandbox

    def missing_secrets(self) -> list[str]:
        return [s for s in self.required_secrets if not os.getenv(s)]

    def is_activatable(self) -> bool:
        """True solo si hay secretos y la activacion global esta encendida."""
        flag = os.getenv("ACTIVAR_PAGOS", "false").lower() in ("1", "true", "yes")
        return flag and not self.missing_secrets()

    @abstractmethod
    def create_payment(self, amount: int, currency: str, reference: str) -> PaymentResult:
        ...

    def _refuse_real(self) -> None:
        """Salvaguarda: jamas cobrar de verdad sin activacion + secretos."""
        if not self.sandbox and not self.is_activatable():
            faltan = ", ".join(self.missing_secrets()) or "ACTIVAR_PAGOS"
            raise RuntimeError(
                f"Pagos NO activados para {self.name}. Faltan: {faltan}. "
                "Ver docs/activar-pagos.md. Operando solo en sandbox."
            )
