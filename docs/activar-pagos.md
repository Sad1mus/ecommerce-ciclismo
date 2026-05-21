# Activación de pagos (Wompi / ePayco) — Colombia

> Estado actual: **CÓDIGO LISTO, NO ACTIVADO**. Los proveedores corren en
> `sandbox`/mock: **no se ejecutan cobros reales** ni hay llaves reales en el
> repositorio. Esta guía lista lo que falta para activar producción.

El código vive en `src/payments/` (`base.py`, `wompi.py`, `epayco.py`,
`registry.py`). Por defecto `sandbox=True` y `ACTIVAR_PAGOS` está apagado, así
que cualquier intento de cobro real es rechazado por la salvaguarda
`_refuse_real()`.

## 1. Secretos que faltan

Ninguno de estos valores está (ni debe estar) en el repositorio. Se cargan por
variables de entorno (`.env`, gestor de secretos del VPS, etc.).

### Wompi
| Variable | Descripción | Dónde se obtiene |
|---|---|---|
| `WOMPI_PUBLIC_KEY` | Llave pública (`pub_prod_...`) | Dashboard Wompi → Desarrolladores |
| `WOMPI_PRIVATE_KEY` | Llave privada (`prv_prod_...`) | Dashboard Wompi → Desarrolladores |
| `WOMPI_EVENTS_SECRET` | Secreto para validar webhooks | Dashboard Wompi → Eventos |

### ePayco
| Variable | Descripción | Dónde se obtiene |
|---|---|---|
| `EPAYCO_PUBLIC_KEY` | `PUBLIC_KEY` del comercio | Dashboard ePayco → Integraciones |
| `EPAYCO_PRIVATE_KEY` | `PRIVATE_KEY` del comercio | Dashboard ePayco → Integraciones |
| `EPAYCO_P_CUST_ID` | `P_CUST_ID_CLIENTE` | Dashboard ePayco |
| `EPAYCO_P_KEY` | `P_KEY` (firma de confirmación) | Dashboard ePayco |

### Bandera global
| Variable | Valor para activar |
|---|---|
| `ACTIVAR_PAGOS` | `true` (cualquier otro valor = solo sandbox) |

## 2. Pasos de activación

1. Crear/validar las cuentas de comercio en Wompi y ePayco (modo producción).
2. Cargar los secretos de arriba en el entorno del backend (NUNCA en git).
3. Poner `ACTIVAR_PAGOS=true`.
4. Instanciar el proveedor con `sandbox=False`:
   `get_provider("wompi", sandbox=False)`.
5. Configurar las URLs de webhook/confirmación públicas (HTTPS del VPS).
6. Hacer una compra de prueba de bajo monto y validar la firma del webhook
   antes de abrir al público.

## 3. Verificación previa (sin tocar producción)

```bash
cd src/payments
python -c "from registry import activation_status; import json; print(json.dumps(activation_status(), indent=2))"
```

Mientras falten secretos, cada proveedor reporta `activatable: false` y lista
`missing_secrets`. Esa es la confirmación de que **no** está activado.

## 4. Integración con Medusa (pendiente de activación)

`src/payments/` es la capa portable de proveedores. Para conectarla a Medusa se
registra como `payment_provider` del módulo de pagos de Medusa, mapeando
`create_payment`/estado a las sesiones de pago del checkout. Esa conexión solo
se cablea una vez que existan los secretos de producción.

## 5. Reglas de seguridad

- Nunca commitear llaves reales (`WOMPI_PRIVATE_KEY`, `EPAYCO_PRIVATE_KEY`, etc.).
- `.env` está en `.gitignore`; solo `.env.example` (con valores vacíos) se versiona.
- Todo cobro real exige `ACTIVAR_PAGOS=true` + secretos presentes; de lo
  contrario el código se mantiene en sandbox por diseño.
