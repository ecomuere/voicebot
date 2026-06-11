import base64
import json

from voicebot.adapters.numpy_transcoder import NumpyAudioTranscoder
from voicebot.adapters.twilio_transport import TwilioWebSocketTransport, build_stream_twiml
from voicebot.domain.audio import AudioFrame

from tests.fakes import FakeWebSocket


def _twilio_messages(mulaw_payload: bytes) -> list[dict]:
    return [
        {
            "type": "websocket.receive",
            "text": json.dumps({"event": "start", "start": {"streamSid": "MZ123"}}),
        },
        {
            "type": "websocket.receive",
            "text": json.dumps(
                {
                    "event": "media",
                    "media": {"payload": base64.b64encode(mulaw_payload).decode()},
                }
            ),
        },
        {"type": "websocket.receive", "text": json.dumps({"event": "stop"})},
    ]


async def test_incoming_audio_decodes_mulaw_and_resamples_to_16k():
    mulaw = b"\xff" * 160  # 20 ms de silencio a 8 kHz
    ws = FakeWebSocket(incoming=_twilio_messages(mulaw))
    transport = TwilioWebSocketTransport(ws, NumpyAudioTranscoder())

    frames = [frame async for frame in transport.incoming_audio()]

    assert len(frames) == 1
    assert frames[0].sample_rate == 16000
    # 160 muestras a 8 kHz -> 320 muestras a 16 kHz -> 640 bytes PCM16
    assert len(frames[0].data) == 640


async def test_play_audio_sends_mulaw_8k_media_message():
    ws = FakeWebSocket(incoming=_twilio_messages(b"\xff" * 160))
    transport = TwilioWebSocketTransport(ws, NumpyAudioTranscoder())
    async for _ in transport.incoming_audio():  # procesa "start" para capturar streamSid
        pass

    # 240 muestras a 24 kHz (10 ms) -> 80 muestras a 8 kHz
    await transport.play_audio(AudioFrame(data=b"\x00\x00" * 240, sample_rate=24000))

    message = json.loads(ws.sent_text[0])
    assert message["event"] == "media"
    assert message["streamSid"] == "MZ123"
    assert len(base64.b64decode(message["media"]["payload"])) == 80


async def test_play_audio_before_start_is_dropped():
    ws = FakeWebSocket()
    transport = TwilioWebSocketTransport(ws, NumpyAudioTranscoder())

    await transport.play_audio(AudioFrame(data=b"\x00\x00" * 240, sample_rate=24000))

    assert ws.sent_text == []


async def test_interrupt_sends_clear_event():
    ws = FakeWebSocket(incoming=_twilio_messages(b"\xff" * 160))
    transport = TwilioWebSocketTransport(ws, NumpyAudioTranscoder())
    async for _ in transport.incoming_audio():
        pass

    await transport.interrupt()

    assert json.loads(ws.sent_text[-1]) == {"event": "clear", "streamSid": "MZ123"}


def test_build_stream_twiml():
    twiml = build_stream_twiml("wss://example.com/ws/twilio")
    assert "<Connect>" in twiml
    assert '<Stream url="wss://example.com/ws/twilio"/>' in twiml
