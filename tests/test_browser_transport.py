import json

from voicebot.adapters.browser_transport import BrowserWebSocketTransport
from voicebot.domain.audio import AudioFrame
from voicebot.domain.events import TranscriptLine

from tests.fakes import FakeWebSocket


async def test_incoming_audio_yields_pcm16_16k_frames():
    chunk = b"\x01\x00" * 320
    ws = FakeWebSocket(
        incoming=[
            {"type": "websocket.receive", "bytes": chunk},
            {"type": "websocket.receive", "text": "ignorado"},  # sin bytes -> se ignora
            {"type": "websocket.disconnect"},
        ]
    )
    transport = BrowserWebSocketTransport(ws)

    frames = [frame async for frame in transport.incoming_audio()]

    assert len(frames) == 1
    assert frames[0].data == chunk
    assert frames[0].sample_rate == 16000


async def test_play_audio_sends_raw_bytes():
    ws = FakeWebSocket()
    transport = BrowserWebSocketTransport(ws)

    await transport.play_audio(AudioFrame(data=b"\x02\x00" * 10, sample_rate=24000))

    assert ws.sent_bytes == [b"\x02\x00" * 10]


async def test_interrupt_and_transcript_are_json_control_messages():
    ws = FakeWebSocket()
    transport = BrowserWebSocketTransport(ws)

    await transport.interrupt()
    await transport.show_transcript(TranscriptLine(role="user", text="hola"))

    assert json.loads(ws.sent_text[0]) == {"type": "interruption"}
    assert json.loads(ws.sent_text[1]) == {"type": "transcript", "role": "user", "text": "hola"}
