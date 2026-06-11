"""Puertos (interfaces) de la arquitectura hexagonal.

El dominio y la capa de aplicación dependen solo de estas abstracciones;
los adaptadores (Strands/Bedrock, Twilio, browser, numpy) las implementan.
"""

from contextlib import AbstractAsyncContextManager
from typing import AsyncIterator, Protocol, runtime_checkable

from voicebot.domain.audio import AudioFrame
from voicebot.domain.events import ConversationEvent, TranscriptLine


@runtime_checkable
class ConversationSession(Protocol):
    """Sesión activa con el modelo speech-to-speech (puerto conducido)."""

    async def send_audio(self, frame: AudioFrame) -> None:
        """Envía audio del llamante al modelo."""
        ...

    def events(self) -> AsyncIterator[ConversationEvent]:
        """Itera los eventos producidos por el modelo hasta que la sesión termina."""
        ...


@runtime_checkable
class ConversationGateway(Protocol):
    """Fábrica de sesiones de conversación (puerto conducido)."""

    def open_session(self) -> AbstractAsyncContextManager[ConversationSession]: ...


@runtime_checkable
class CallTransport(Protocol):
    """Canal con el llamante: navegador, teléfono, micrófono local... (puerto conductor)."""

    def incoming_audio(self) -> AsyncIterator[AudioFrame]:
        """Itera el audio del llamante hasta que cuelga o se cierra el canal."""
        ...

    async def play_audio(self, frame: AudioFrame) -> None:
        """Reproduce voz del agente al llamante."""
        ...

    async def interrupt(self) -> None:
        """El llamante interrumpió al agente: descartar el audio aún no reproducido."""
        ...

    async def show_transcript(self, line: TranscriptLine) -> None:
        """Muestra/registra una transcripción (opcional según el canal)."""
        ...


@runtime_checkable
class AudioTranscoder(Protocol):
    """Conversión de formatos de audio (puerto conducido)."""

    def pcm16_to_mulaw(self, pcm: bytes) -> bytes: ...

    def mulaw_to_pcm16(self, mu: bytes) -> bytes: ...

    def resample(self, pcm: bytes, src_rate: int, dst_rate: int) -> bytes: ...
