"""Herramientas (tools) que el cerebro conversacional puede invocar.

Cada herramienta:
 - Lee/escribe SOLO via MedusaClient (la verdad es Medusa; nunca se inventa).
 - Devuelve texto APTO PARA LECTOR DE PANTALLA (ver formatting.py).
 - Ante cualquier excepcion devuelve DATO_NO_DISPONIBLE (anti-alucinacion).

Las herramientas de ESCRITURA (crear/confirmar/facturar/empaque/despachar) exigen
`confirmado=True`. Si llega sin confirmar, NO mutan: devuelven una frase de
confirmacion para que el agente se la lea al dueño y solo ejecute tras un "sí".

El esquema (TOOLS_SPEC) sigue el formato de function-calling de OpenAI/Groq.
"""
from __future__ import annotations

from typing import Callable, Dict

from formatting import DATO_NO_DISPONIBLE, clamp_lines, format_cop
from medusa_client import MedusaClient

UMBRAL_STOCK_BAJO = 5


# --------------------------------------------------------------------------
# Lectura
# --------------------------------------------------------------------------
def consultar_producto(client: MedusaClient, consulta: str) -> str:
    """Stock y precio de los productos que coinciden con la consulta."""
    consulta = (consulta or "").strip()
    if not consulta:
        return "Falta indicar el producto a consultar."
    try:
        productos = client.search_products(consulta)
    except Exception:
        return DATO_NO_DISPONIBLE
    if not productos:
        return f"Sin resultados para: {consulta}"
    lineas = [f"Resultados para: {consulta}"]
    for p in productos:
        stock = "sin dato de stock" if p.stock is None else (
            "agotado" if p.stock <= 0 else f"{p.stock} disponibles"
        )
        lineas.append(f"{p.title}: {format_cop(p.price, p.currency)}, {stock}")
    return clamp_lines("\n".join(lineas))


def consultar_pedido(client: MedusaClient, numero: int) -> str:
    """Estado y contenido de un pedido por su numero (display_id)."""
    try:
        pedido = client.get_order(int(numero))
    except Exception:
        return DATO_NO_DISPONIBLE
    if pedido is None:
        return f"No encontre el pedido numero {numero} entre los recientes."
    lineas = [
        f"Pedido {pedido.display_id}: {pedido.status}",
        f"Pago: {pedido.payment_status or 'sin dato'}. Envio: {pedido.fulfillment_status or 'sin dato'}.",
        f"Total: {format_cop(pedido.total, pedido.currency)}",
    ]
    for it in pedido.items:
        lineas.append(f"{it.quantity} x {it.title}")
    factura = pedido.metadata.get("factura_numero")
    if factura:
        lineas.append(f"Factura: {factura}")
    transportadora = pedido.metadata.get("transportadora")
    if transportadora:
        guia = pedido.metadata.get("guia", "sin guia")
        lineas.append(f"Transportadora: {transportadora}, guia {guia}")
    return clamp_lines("\n".join(lineas))


def listar_pedidos_pendientes(client: MedusaClient, limite: int = 5) -> str:
    """Ultimos pedidos registrados, para revisar que hay por atender."""
    try:
        pedidos = client.list_orders(limit=int(limite))
    except Exception:
        return DATO_NO_DISPONIBLE
    if not pedidos:
        return "No hay pedidos registrados."
    lineas = ["Ultimos pedidos:"]
    for o in pedidos:
        lineas.append(f"Pedido {o.display_id}: {o.status}, {format_cop(o.total, o.currency)}")
    return clamp_lines("\n".join(lineas))


def reporte_stock_bajo(client: MedusaClient, consulta: str, umbral: int = UMBRAL_STOCK_BAJO) -> str:
    """Productos con stock menor o igual a un umbral, para reponer."""
    consulta = (consulta or "").strip()
    if not consulta:
        return "Falta indicar sobre que productos revisar el stock bajo."
    try:
        productos = client.search_products(consulta, limit=20)
    except Exception:
        return DATO_NO_DISPONIBLE
    bajos = [p for p in productos if isinstance(p.stock, int) and p.stock <= int(umbral)]
    if not bajos:
        return f"Sin productos con stock menor o igual a {umbral} para: {consulta}"
    lineas = [f"Stock bajo (<= {umbral}) para: {consulta}"]
    for p in bajos:
        lineas.append(f"{p.title}: {p.stock} unidades")
    return clamp_lines("\n".join(lineas))


def listar_categorias(client: MedusaClient) -> str:
    """Categorias publicas (lo que ve el cliente) y codigos internos del dueño."""
    try:
        cats = client.list_categories()
    except Exception:
        return DATO_NO_DISPONIBLE
    activas = sorted(c["name"] for c in cats if c["is_active"])
    internas = [c["name"] for c in cats if not c["is_active"]]
    partes = []
    if activas:
        partes.append(f"Categorias de la tienda ({len(activas)}): " + ", ".join(activas) + ".")
    if internas:
        partes.append(f"Codigos internos del dueño ({len(internas)}): " + ", ".join(internas) + ".")
    return "\n".join(partes) if partes else "No hay categorias registradas."


def productos_por_categoria(client: MedusaClient, categoria: str) -> str:
    """Productos de una categoria PUBLICA (por tipo), por su nombre."""
    categoria = (categoria or "").strip()
    if not categoria:
        return "Falta el nombre de la categoria."
    try:
        prods = client.products_in_category(categoria, limit=30)
    except Exception:
        return DATO_NO_DISPONIBLE
    if prods is None:
        return f"No existe la categoria publica '{categoria}'. Mira listar_categorias para ver las disponibles."
    if not prods:
        return f"La categoria '{categoria}' no tiene productos."
    nombres = [p.title for p in prods]
    extra = "..." if len(nombres) >= 30 else ""
    return f"Categoria {categoria}: {len(nombres)} productos. " + "; ".join(nombres[:20]) + extra


def buscar_por_codigo_interno(client: MedusaClient, codigo: str) -> str:
    """Productos por el CODIGO INTERNO del dueño (1-RK, 6-CL, PITILLOS...)."""
    codigo = (codigo or "").strip()
    if not codigo:
        return "Falta el codigo interno del dueño, por ejemplo 6-CL o PITILLOS."
    try:
        titulos = client.products_by_codigo(codigo)
    except Exception:
        return DATO_NO_DISPONIBLE
    if not titulos:
        return f"No hay productos con el codigo interno {codigo.upper()}."
    extra = f" (y {len(titulos) - 20} mas)" if len(titulos) > 20 else ""
    return f"Codigo {codigo.upper()}: {len(titulos)} productos. " + "; ".join(titulos[:20]) + extra


# --------------------------------------------------------------------------
# Escritura (operacion). Exigen confirmado=True; si no, NO mutan: devuelven una
# frase de confirmacion para que el agente la lea y solo ejecute tras un "sí".
# --------------------------------------------------------------------------
def _confirmacion(texto: str) -> str:
    return f"CONFIRMACION REQUERIDA: {texto} Pregunta al dueño si confirma y solo ejecuta si dice que sí."


def crear_pedido(client: MedusaClient, producto: str, cantidad: int = 1, confirmado: bool = False) -> str:
    """Crea un pedido para un producto (p.ej. cliente que llama). Pide confirmacion."""
    producto = (producto or "").strip()
    if not producto:
        return "Falta el producto para crear el pedido."
    cantidad = max(1, int(cantidad or 1))
    try:
        prods = client.search_products(producto)
    except Exception:
        return DATO_NO_DISPONIBLE
    if not prods:
        return f"Sin resultados para: {producto}. No cree ningun pedido."
    p = prods[0]
    if not p.variant_id:
        return f"No pude identificar una variante de '{p.title}' para el pedido."
    # Anti-sobreventa: si conocemos el stock y no alcanza, NO creamos el pedido.
    # (Si el stock es desconocido no bloqueamos: Medusa lo validara al crear.)
    if p.stock is not None and p.stock < cantidad:
        disp = "agotado" if p.stock <= 0 else f"solo {p.stock} disponibles"
        return (
            f"No cree el pedido: de '{p.title}' hay {disp} y pediste {cantidad}. "
            "Ajusta la cantidad o confirma que aun asi lo quieres."
        )
    if not confirmado:
        aviso = ""
        if p.variant_count > 1:
            # No elegimos la variante en silencio: avisamos cual va (SKU) para que el
            # dueño confirme a conciencia y pida otra presentacion si hace falta.
            ref = p.sku or "principal"
            aviso = (
                f" Ojo: '{p.title}' tiene {p.variant_count} presentaciones "
                f"(color o talla); voy a pedir la variante {ref}. Si necesitas otra, dime cual."
            )
        return _confirmacion(
            f"crear un pedido de {cantidad} x {p.title} a {format_cop(p.price, p.currency)} cada uno." + aviso
        )
    try:
        det = client.create_order([{"variant_id": p.variant_id, "quantity": cantidad}])
    except Exception:
        return DATO_NO_DISPONIBLE
    if det is None:
        return "Cree el pedido pero no pude releer su numero. Revisa los pedidos recientes."
    return f"Pedido {det.display_id} creado: {cantidad} x {p.title}. Estado: {det.status}."


def confirmar_pedido(client: MedusaClient, numero: int, confirmado: bool = False) -> str:
    """Marca un pedido como confirmado por el dueño. Pide confirmacion."""
    try:
        det = client.get_order(int(numero))
    except Exception:
        return DATO_NO_DISPONIBLE
    if det is None:
        return f"No encontre el pedido {numero}."
    if not confirmado:
        resumen = ", ".join(f"{it.quantity} x {it.title}" for it in det.items) or "sin items"
        return _confirmacion(f"confirmar el pedido {numero} ({resumen}), total {format_cop(det.total, det.currency)}.")
    try:
        client.update_order_metadata(det.id, {"estado_operativo": "confirmado"}, det.metadata)
    except Exception:
        return DATO_NO_DISPONIBLE
    return f"Pedido {numero} confirmado."


def facturar_pedido(client: MedusaClient, numero: int, confirmado: bool = False) -> str:
    """Genera un comprobante interno (numero + total) para un pedido. Pide confirmacion."""
    try:
        det = client.get_order(int(numero))
    except Exception:
        return DATO_NO_DISPONIBLE
    if det is None:
        return f"No encontre el pedido {numero}."
    ya = det.metadata.get("factura_numero")
    if ya:
        return f"El pedido {numero} ya tiene factura {ya}."
    if not confirmado:
        return _confirmacion(f"facturar el pedido {numero} por {format_cop(det.total, det.currency)}.")
    numero_factura = f"F-{int(det.display_id):05d}"
    try:
        client.update_order_metadata(
            det.id,
            {"factura_numero": numero_factura, "factura_total": det.total},
            det.metadata,
        )
    except Exception:
        return DATO_NO_DISPONIBLE
    return f"Pedido {numero} facturado. Factura {numero_factura} por {format_cop(det.total, det.currency)}."


def plantilla_empaque(client: MedusaClient, numero: int) -> str:
    """Lista de empaque (que y cuanto) de un pedido, para bodega. Solo lectura."""
    try:
        det = client.get_order(int(numero))
    except Exception:
        return DATO_NO_DISPONIBLE
    if det is None:
        return f"No encontre el pedido {numero}."
    if not det.items:
        return f"El pedido {numero} no tiene items para empacar."
    lineas = [f"Empaque del pedido {numero}:"]
    for it in det.items:
        lineas.append(f"{it.quantity} x {it.title}")
    lineas.append("Verifica cantidades antes de cerrar la caja.")
    return clamp_lines("\n".join(lineas))


def marcar_transportadora(
    client: MedusaClient, numero: int, empresa: str, guia: str = "", confirmado: bool = False
) -> str:
    """Marca un pedido como despachado con transportadora y guia. Pide confirmacion."""
    empresa = (empresa or "").strip()
    if not empresa:
        return "¿Por cual transportadora se despacha el pedido?"
    try:
        det = client.get_order(int(numero))
    except Exception:
        return DATO_NO_DISPONIBLE
    if det is None:
        return f"No encontre el pedido {numero}."
    guia = (guia or "").strip()
    if not confirmado:
        return _confirmacion(
            f"marcar el pedido {numero} como despachado por {empresa}, guia {guia or 'sin guia'}."
        )
    try:
        client.update_order_metadata(
            det.id,
            {"transportadora": empresa, "guia": guia, "estado_operativo": "despachado"},
            det.metadata,
        )
    except Exception:
        return DATO_NO_DISPONIBLE
    return f"Pedido {numero} despachado por {empresa}, guia {guia or 'sin guia'}."


# --------------------------------------------------------------------------
# Registro: nombre -> funcion.
# --------------------------------------------------------------------------
REGISTRY: Dict[str, Callable[..., str]] = {
    # lectura
    "consultar_producto": consultar_producto,
    "consultar_pedido": consultar_pedido,
    "listar_pedidos_pendientes": listar_pedidos_pendientes,
    "reporte_stock_bajo": reporte_stock_bajo,
    "listar_categorias": listar_categorias,
    "productos_por_categoria": productos_por_categoria,
    "buscar_por_codigo_interno": buscar_por_codigo_interno,
    # escritura (con confirmacion)
    "crear_pedido": crear_pedido,
    "confirmar_pedido": confirmar_pedido,
    "facturar_pedido": facturar_pedido,
    "plantilla_empaque": plantilla_empaque,
    "marcar_transportadora": marcar_transportadora,
}

TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "consultar_producto",
            "description": "Stock y precio de productos que coinciden con un texto. Usar siempre que el dueño pregunte por disponibilidad, existencias o precio de algo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "consulta": {"type": "string", "description": "Nombre o palabra del producto, p.ej. 'candado' o 'casco rojo'."}
                },
                "required": ["consulta"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_pedido",
            "description": "Estado, total y contenido de un pedido por su numero. Usar cuando pregunte '¿qué pasó con el pedido X?' o por el estado de un pedido.",
            "parameters": {
                "type": "object",
                "properties": {
                    "numero": {"type": "integer", "description": "Numero visible del pedido (display_id)."}
                },
                "required": ["numero"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listar_pedidos_pendientes",
            "description": "Lista los ultimos pedidos para revisar que hay por atender o despachar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limite": {"type": "integer", "description": "Cuantos pedidos listar (por defecto 5)."}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reporte_stock_bajo",
            "description": "Productos con stock bajo (<= umbral) para saber qué reponer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "consulta": {"type": "string", "description": "Familia o palabra de producto a revisar."},
                    "umbral": {"type": "integer", "description": "Umbral de stock bajo (por defecto 5)."},
                },
                "required": ["consulta"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listar_categorias",
            "description": "Lista las categorias de la tienda (lo que ve el cliente, por tipo) y los codigos internos del dueño. Usar cuando pregunte '¿qué categorías tengo/manejo?'.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "productos_por_categoria",
            "description": "Lista los productos de una categoria PUBLICA por su nombre (p.ej. Cascos, Candados, Luces).",
            "parameters": {
                "type": "object",
                "properties": {
                    "categoria": {"type": "string", "description": "Nombre de la categoria publica."}
                },
                "required": ["categoria"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_por_codigo_interno",
            "description": "Lista productos por el CODIGO INTERNO del dueño (como 1-RK, 6-CL, PITILLOS). Usar cuando el dueño hable en SUS codigos/categorias propias.",
            "parameters": {
                "type": "object",
                "properties": {
                    "codigo": {"type": "string", "description": "Codigo interno del dueño, p.ej. 6-CL o PITILLOS."}
                },
                "required": ["codigo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crear_pedido",
            "description": "Crea un pedido para un producto (p.ej. un cliente que llama). SIEMPRE confirma con el dueño antes; pasa confirmado=true solo tras un 'sí' explicito.",
            "parameters": {
                "type": "object",
                "properties": {
                    "producto": {"type": "string", "description": "Nombre o palabra del producto a pedir."},
                    "cantidad": {"type": "integer", "description": "Unidades (por defecto 1)."},
                    "confirmado": {"type": "boolean", "description": "true solo cuando el dueño ya dijo que sí."},
                },
                "required": ["producto"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "confirmar_pedido",
            "description": "Marca un pedido como confirmado por el dueño. Confirma antes; confirmado=true solo tras el sí.",
            "parameters": {
                "type": "object",
                "properties": {
                    "numero": {"type": "integer", "description": "Numero del pedido (display_id)."},
                    "confirmado": {"type": "boolean", "description": "true solo tras el sí del dueño."},
                },
                "required": ["numero"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "facturar_pedido",
            "description": "Genera el comprobante interno (numero + total) de un pedido. Confirma antes; confirmado=true solo tras el sí.",
            "parameters": {
                "type": "object",
                "properties": {
                    "numero": {"type": "integer", "description": "Numero del pedido (display_id)."},
                    "confirmado": {"type": "boolean", "description": "true solo tras el sí del dueño."},
                },
                "required": ["numero"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "plantilla_empaque",
            "description": "Lista de empaque (que y cuanto) de un pedido, para bodega. Solo lectura, no requiere confirmacion.",
            "parameters": {
                "type": "object",
                "properties": {
                    "numero": {"type": "integer", "description": "Numero del pedido (display_id)."}
                },
                "required": ["numero"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "marcar_transportadora",
            "description": "Marca un pedido como despachado con su transportadora y guia. Confirma antes; confirmado=true solo tras el sí.",
            "parameters": {
                "type": "object",
                "properties": {
                    "numero": {"type": "integer", "description": "Numero del pedido (display_id)."},
                    "empresa": {"type": "string", "description": "Transportadora, p.ej. Servientrega, Interrapidisimo."},
                    "guia": {"type": "string", "description": "Numero de guia (si lo hay)."},
                    "confirmado": {"type": "boolean", "description": "true solo tras el sí del dueño."},
                },
                "required": ["numero", "empresa"],
            },
        },
    },
]


def execute_tool(name: str, args: dict, client: MedusaClient) -> str:
    """Ejecuta una herramienta por nombre. Anti-alucinacion: errores -> dato no disponible."""
    fn = REGISTRY.get(name)
    if fn is None:
        return f"Herramienta desconocida: {name}"
    try:
        return fn(client, **(args or {}))
    except TypeError as e:
        return f"No pude ejecutar {name}: argumentos invalidos ({e})."
    except Exception:
        return DATO_NO_DISPONIBLE
