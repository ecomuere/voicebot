"""Herramientas del agente.

`get_order_status` sigue el patrón del ADR 0001: la regla de negocio vive en
una Lambda compartida (lambdas/order_status) que también invoca el AI agent de
Amazon Connect, de modo que ambos canales responden igual. El resto son
ejemplos a sustituir por llamadas reales a tus APIs/sistemas.
"""

import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from strands import tool


def _lambda_client():
    import boto3

    return boto3.client("lambda", region_name=os.getenv("VOICEBOT_REGION", "us-east-1"))


@tool
def get_order_status(order_id: str) -> str:
    """Consulta el estado de un pedido por su número.

    Args:
        order_id: Número del pedido, por ejemplo "1001".

    Returns:
        Estado del pedido y entrega estimada, o un mensaje de error.
    """
    function_name = os.getenv("VOICEBOT_ORDER_STATUS_FUNCTION", "")
    if not function_name:
        return "La consulta de pedidos no está disponible en este momento."

    response = _lambda_client().invoke(
        FunctionName=function_name,
        Payload=json.dumps({"order_id": order_id}).encode("utf-8"),
    )
    result = json.loads(response["Payload"].read())
    if result.get("encontrado") == "true":
        return (
            f"El pedido {result['pedido']} está {result['estado']}; "
            f"entrega estimada: {result['entrega_estimada']}."
        )
    return result.get("mensaje", "No he podido consultar el pedido.")


@tool
def get_current_time(timezone: str = "Europe/Madrid") -> str:
    """Obtiene la fecha y hora actual.

    Args:
        timezone: Zona horaria IANA, por ejemplo "Europe/Madrid" o "America/Mexico_City".

    Returns:
        Fecha y hora actual en formato legible.
    """
    now = datetime.now(ZoneInfo(timezone))
    return now.strftime("%A %d de %B de %Y, %H:%M")


@tool
def get_weather(location: str) -> str:
    """Obtiene el tiempo actual para una ubicación.

    Args:
        location: Ciudad o ubicación.

    Returns:
        Información meteorológica.
    """
    # Demo: en una aplicación real, llama a una API meteorológica.
    return f"En {location} hace sol y 22 grados."
