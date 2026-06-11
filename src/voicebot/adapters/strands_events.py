"""Traducción de eventos del SDK de Strands a eventos de dominio.

Módulo sin dependencia de strands para poder testearlo de forma aislada:
los eventos bidi de Strands se comportan como diccionarios.
"""

import base64
from typing import Any, Mapping, Optional

from voicebot.domain.audio import AudioFrame
from voicebot.domain.events import (
    AgentSpoke,
    ConversationEvent,
    Interrupted,
    TranscriptLine,
    TranscriptReady,
)


def _decode_audio_payload(audio: Any) -> bytes:
    if isinstance(audio, (bytes, bytearray)):
        return bytes(audio)
    return base64.b64decode(audio)


def map_event(event: Mapping[str, Any]) -> Optional[ConversationEvent]:
    """Convierte un evento bidi de Strands en un evento de dominio (o None si no aplica)."""
    event_type = event.get("type")

    if event_type == "bidi_audio_stream":
        return AgentSpoke(
            frame=AudioFrame(
                data=_decode_audio_payload(event["audio"]),
                sample_rate=event.get("sample_rate", 24000),
                channels=event.get("channels", 1),
            )
        )

    if event_type == "bidi_interruption":
        return Interrupted(reason=event.get("reason", "user_speech"))

    if event_type == "bidi_transcript_stream" and event.get("is_final"):
        return TranscriptReady(
            line=TranscriptLine(role=event.get("role", "assistant"), text=event.get("text", ""))
        )

    return None
