"""Herramientas del agente (ejemplos).

Sustituye las implementaciones por llamadas reales a tus APIs/sistemas.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from strands import tool


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
