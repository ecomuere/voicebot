"""Eventos de dominio emitidos durante una conversación de voz."""

from dataclasses import dataclass
from typing import Union

from voicebot.domain.audio import AudioFrame


@dataclass(frozen=True, slots=True)
class TranscriptLine:
    """Una intervención transcrita de la conversación."""

    role: str  # "user" | "assistant"
    text: str


@dataclass(frozen=True, slots=True)
class AgentSpoke:
    """El agente ha producido un fragmento de voz."""

    frame: AudioFrame


@dataclass(frozen=True, slots=True)
class Interrupted:
    """El usuario ha interrumpido al agente (barge-in); descartar audio pendiente."""

    reason: str = "user_speech"


@dataclass(frozen=True, slots=True)
class TranscriptReady:
    """Hay disponible una transcripción final de una intervención."""

    line: TranscriptLine


ConversationEvent = Union[AgentSpoke, Interrupted, TranscriptReady]
