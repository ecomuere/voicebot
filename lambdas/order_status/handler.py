"""Herramienta de negocio compartida: consulta del estado de un pedido.

Única implementación de la regla de negocio (ADR 0001), servida como Lambda e
invocada por los dos canales:
  - Amazon Connect (teléfono): acción del AI agent / bloque Invoke Lambda.
  - Agente Strands (web): tool `get_order_status` en adapters/tools.py.

Connect exige como respuesta un mapa plano clave->valor de strings, así que ese
es el contrato de salida para ambos llamantes.
"""

from typing import Any

# Demo: sustituir por la consulta real (DynamoDB, ERP, API interna...).
_FAKE_ORDERS: dict[str, dict[str, str]] = {
    "1001": {"estado": "enviado", "entrega_estimada": "mañana"},
    "1002": {"estado": "en preparación", "entrega_estimada": "en 2 días"},
    "1003": {"estado": "entregado", "entrega_estimada": "ya entregado"},
}


def lookup_order(order_id: str) -> dict[str, str]:
    """Regla de negocio: estado de un pedido a partir de su identificador."""
    order = _FAKE_ORDERS.get(order_id.strip())
    if order is None:
        return {
            "encontrado": "false",
            "mensaje": f"No existe ningún pedido con el número {order_id}",
        }
    return {"encontrado": "true", "pedido": order_id.strip(), **order}


def _extract_parameters(event: Any) -> dict[str, Any]:
    """Normaliza el evento: formato de Amazon Connect o invocación directa.

    Connect envuelve los parámetros en {"Details": {"Parameters": {...}}};
    la invocación directa (boto3) envía el JSON plano.
    """
    if isinstance(event, dict) and "Details" in event:
        return event["Details"].get("Parameters") or {}
    return event if isinstance(event, dict) else {}


def lambda_handler(event: Any, context: Any = None) -> dict[str, str]:
    params = _extract_parameters(event)
    order_id = str(params.get("order_id", "")).strip()
    if not order_id:
        return {"encontrado": "false", "mensaje": "Falta el parámetro order_id"}
    return lookup_order(order_id)
