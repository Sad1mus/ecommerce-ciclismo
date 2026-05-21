"""Proveedor ePayco (Colombia) — sandbox/mock. NO realiza cobros reales."""
from __future__ import annotations

import hashlib

from base import PaymentProvider, PaymentResult

SANDBOX_URL = "https://apify.epayco.co"  # con test=true
PROD_URL = "https://apify.epayco.co"     # con test=false


class EpaycoProvider(PaymentProvider):
    name = "epayco"
    required_secrets = (
        "EPAYCO_PUBLIC_KEY",
        "EPAYCO_PRIVATE_KEY",
        "EPAYCO_P_CUST_ID",
        "EPAYCO_P_KEY",
    )

    def build_payload(self, amount: int, currency: str, reference: str) -> dict:
        # ePayco maneja el monto en unidades de la moneda (COP en pesos enteros).
        return {
            "value": int(amount),
            "currency": currency.lower(),
            "invoice": reference,
            "test": "true" if self.sandbox else "false",
            "response": "https://tienda.example/checkout/resultado",
        }

    def create_payment(self, amount: int, currency: str, reference: str) -> PaymentResult:
        self._refuse_real()
        payload = self.build_payload(amount, currency, reference)
        approved = "decline" not in reference.lower()
        status = "sandbox_approved" if approved else "sandbox_declined"
        txn = "epayco_sbx_" + hashlib.sha1(reference.encode()).hexdigest()[:12]
        return PaymentResult(
            provider=self.name,
            reference=reference,
            amount=amount,
            currency=currency.upper(),
            status=status,
            real_charge=False,
            sandbox=True,
            detail="Cobro simulado (sandbox, test=true). Sin dinero real.",
            raw={"ref_payco": txn, "payload": payload},
        )
