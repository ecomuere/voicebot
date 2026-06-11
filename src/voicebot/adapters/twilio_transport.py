"""Adaptador de CallTransport para llamadas telefónicas vía Twilio Media Streams.

Protocolo: https://www.twilio.com/docs/voice/media-streams
- Twilio envía JSON por WebSocket con eventos "start", "media" (μ-law 8 kHz
  base64), "stop".
- El servidor responde con eventos "media" (μ-law 8 kHz base64) y "clear"
  (descartar el audio en cola tras una interrupción).
"""

import base64
import json
from typing import Any, AsyncIterator, Optional

from voicebot.adapters.browser_transport import WebSocketLike
from voicebot.domain.audio import (
    AGENT_INPUT_SAMPLE_RATE,
    TELEPHONY_SAMPLE_RATE,
    AudioFrame,
)
from voicebot.domain.events import TranscriptLine
from voicebot.domain.ports import AudioTranscoder


class TwilioWebSocketTransport:
    def __init__(self, websocket: WebSocketLike, transcoder: AudioTranscoder) -> None:
        self._ws = websocket
        self._transcoder = transcoder
        self._stream_sid: Optional[str] = None

    async def incoming_audio(self) -> AsyncIterator[AudioFrame]:
        while True:
            message = await self._ws.receive()
            if message.get("type") == "websocket.disconnect":
                return
            text = message.get("text")
            if not text:
                continue
            payload: dict[str, Any] = json.loads(text)
            event = payload.get("event")

            if event == "start":
                self._stream_sid = payload["start"]["streamSid"]
            elif event == "media":
                mulaw = base64.b64decode(payload["media"]["payload"])
                pcm_8k = self._transcoder.mulaw_to_pcm16(mulaw)
                pcm_16k = self._transcoder.resample(
                    pcm_8k, TELEPHONY_SAMPLE_RATE, AGENT_INPUT_SAMPLE_RATE
                )
                yield AudioFrame(data=pcm_16k, sample_rate=AGENT_INPUT_SAMPLE_RATE, channels=1)
            elif event == "stop":
                return

    async def play_audio(self, frame: AudioFrame) -> None:
        if self._stream_sid is None:
            return  # aún no ha llegado el evento "start"
        pcm_8k = self._transcoder.resample(frame.data, frame.sample_rate, TELEPHONY_SAMPLE_RATE)
        mulaw = self._transcoder.pcm16_to_mulaw(pcm_8k)
        await self._ws.send_text(
            json.dumps(
                {
                    "event": "media",
                    "streamSid": self._stream_sid,
                    "media": {"payload": base64.b64encode(mulaw).decode("ascii")},
                }
            )
        )

    async def interrupt(self) -> None:
        if self._stream_sid is None:
            return
        await self._ws.send_text(json.dumps({"event": "clear", "streamSid": self._stream_sid}))

    async def show_transcript(self, line: TranscriptLine) -> None:
        # En una llamada telefónica no hay dónde mostrar texto; punto de extensión
        # natural para logging/analítica.
        return None


def build_stream_twiml(websocket_url: str) -> str:
    """TwiML que conecta la llamada entrante al WebSocket de Media Streams."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f'<Connect><Stream url="{websocket_url}"/></Connect>'
        "</Response>"
    )
