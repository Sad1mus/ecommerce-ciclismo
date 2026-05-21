"""Proveedor Wompi (Colombia) — sandbox/mock. NO realiza cobros reales."""
from __future__ import annotations

import hashlib

from base import PaymentProvider, PaymentResult

# URLs oficiales (referencia; en sandbox NO se invocan por defecto).
SANDBOX_URL = "https://sandbox.wompi.co/v1"
PROD_URL = "https://production.wompi.co/v1"


class WompiProvider(PaymentProvider):
    name = "wompi"
    required_secrets = ("WOMPI_PUBLIC_KEY", "WOMPI_PRIVATE_KEY", "WOMPI_EVENTS_SECRET")

    def base_url(self) -> str:
        return SANDBOX_URL if self.sandbox else PROD_URL

    def build_payload(self, amount: int, currency: str, reference: str) -> dict:
        # Wompi maneja montos en centavos. COP no usa subunidad de uso comun,
        # pero la API espera "amount_in_cents".
        return {
            "amount_in_cents": int(amount) * 100,
            "currency": currency.upper(),
            "reference": reference,
            "redirect_url": "https://tienda.example/checkout/resultado",
        }

    def create_payment(self, amount: int, currency: str, reference: str) -> PaymentResult:
        self._refuse_real()
        payload = self.build_payload(amount, currency, reference)
        # MOCK determinista: aprueba salvo referencias marcadas para rechazo.
        approved = "decline" not in reference.lower()
        status = "sandbox_approved" if approved else "sandbox_declined"
        txn = "wompi_sbx_" + hashlib.sha1(reference.encode()).hexdigest()[:12]
        return PaymentResult(
            provider=self.name,
            reference=reference,
            amount=amount,
            currency=currency.upper(),
            status=status,
            real_charge=False,
            sandbox=True,
            detail="Cobro simulado (sandbox). Sin movimiento de dinero real.",
            raw={"transaction_id": txn, "payload": payload, "endpoint": self.base_url()},
        )
