"""Adaptador de CallTransport para el cliente web (WebSocket).

Protocolo con el navegador:
- Entrada (browser -> servidor): frames binarios PCM16 mono a 16 kHz.
- Salida (servidor -> browser):
    * frames binarios PCM16 mono a 24 kHz (voz del agente)
    * mensajes JSON de control: {"type": "interruption"} y
      {"type": "transcript", "role": ..., "text": ...}
"""

import json
from typing import Any, AsyncIterator, Protocol

from voicebot.domain.audio import AGENT_INPUT_SAMPLE_RATE, AudioFrame
from voicebot.domain.events import TranscriptLine


class WebSocketLike(Protocol):
    """Subconjunto de la interfaz de starlette.websockets.WebSocket que usamos."""

    async def receive(self) -> dict[str, Any]: ...

    async def send_bytes(self, data: bytes) -> None: ...

    async def send_text(self, data: str) -> None: ...


class BrowserWebSocketTransport:
    def __init__(self, websocket: WebSocketLike) -> None:
        self._ws = websocket

    async def incoming_audio(self) -> AsyncIterator[AudioFrame]:
        while True:
            message = await self._ws.receive()
            if message.get("type") == "websocket.disconnect":
                return
            data = message.get("bytes")
            if data:
                yield AudioFrame(data=data, sample_rate=AGENT_INPUT_SAMPLE_RATE, channels=1)

    async def play_audio(self, frame: AudioFrame) -> None:
        await self._ws.send_bytes(frame.data)

    async def interrupt(self) -> None:
        await self._ws.send_text(json.dumps({"type": "interruption"}))

    async def show_transcript(self, line: TranscriptLine) -> None:
        await self._ws.send_text(
            json.dumps({"type": "transcript", "role": line.role, "text": line.text})
        )
