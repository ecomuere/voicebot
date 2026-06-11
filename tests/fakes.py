"""Dobles de prueba que implementan los puertos del dominio."""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator, Iterable

from voicebot.domain.audio import AudioFrame
from voicebot.domain.events import ConversationEvent, TranscriptLine


class FakeConversationSession:
    """Sesión que emite una lista fija de eventos y registra el audio recibido."""

    def __init__(self, events: Iterable[ConversationEvent] = (), hang_forever: bool = False):
        self._events = list(events)
        self._hang_forever = hang_forever
        self.sent_frames: list[AudioFrame] = []

    async def send_audio(self, frame: AudioFrame) -> None:
        self.sent_frames.append(frame)

    async def events(self) -> AsyncIterator[ConversationEvent]:
        for event in self._events:
            yield event
        if self._hang_forever:
            await asyncio.Event().wait()


class FakeGateway:
    def __init__(self, session: FakeConversationSession):
        self.session = session
        self.closed = False

    @asynccontextmanager
    async def open_session(self):
        try:
            yield self.session
        finally:
            self.closed = True


class FakeTransport:
    """Transporte que entrega frames fijos y registra lo que el agente le envía."""

    def __init__(self, frames: Iterable[AudioFrame] = (), hang_forever: bool = False):
        self._frames = list(frames)
        self._hang_forever = hang_forever
        self.played: list[AudioFrame] = []
        self.interruptions = 0
        self.transcripts: list[TranscriptLine] = []

    async def incoming_audio(self) -> AsyncIterator[AudioFrame]:
        for frame in self._frames:
            yield frame
        if self._hang_forever:
            await asyncio.Event().wait()

    async def play_audio(self, frame: AudioFrame) -> None:
        self.played.append(frame)

    async def interrupt(self) -> None:
        self.interruptions += 1

    async def show_transcript(self, line: TranscriptLine) -> None:
        self.transcripts.append(line)


class FakeWebSocket:
    """Imita el subconjunto de starlette.websockets.WebSocket usado por los adaptadores."""

    def __init__(self, incoming: Iterable[dict] = ()):
        self._incoming = list(incoming)
        self.sent_bytes: list[bytes] = []
        self.sent_text: list[str] = []

    async def receive(self) -> dict:
        if self._incoming:
            return self._incoming.pop(0)
        return {"type": "websocket.disconnect"}

    async def send_bytes(self, data: bytes) -> None:
        self.sent_bytes.append(data)

    async def send_text(self, data: str) -> None:
        self.sent_text.append(data)
