import base64

from voicebot.adapters.strands_events import map_event
from voicebot.domain.events import AgentSpoke, Interrupted, TranscriptReady


def test_maps_audio_stream_with_base64_payload():
    pcm = b"\x01\x00" * 100
    event = map_event(
        {
            "type": "bidi_audio_stream",
            "audio": base64.b64encode(pcm).decode(),
            "format": "pcm",
            "sample_rate": 24000,
            "channels": 1,
        }
    )
    assert isinstance(event, AgentSpoke)
    assert event.frame.data == pcm
    assert event.frame.sample_rate == 24000


def test_maps_audio_stream_with_raw_bytes_payload():
    pcm = b"\x01\x00" * 100
    event = map_event({"type": "bidi_audio_stream", "audio": pcm, "sample_rate": 24000})
    assert isinstance(event, AgentSpoke)
    assert event.frame.data == pcm


def test_maps_interruption():
    event = map_event({"type": "bidi_interruption", "reason": "user_speech"})
    assert isinstance(event, Interrupted)
    assert event.reason == "user_speech"


def test_maps_final_transcript_only():
    final = map_event(
        {"type": "bidi_transcript_stream", "is_final": True, "role": "user", "text": "hola"}
    )
    partial = map_event(
        {"type": "bidi_transcript_stream", "is_final": False, "role": "user", "text": "ho"}
    )
    assert isinstance(final, TranscriptReady)
    assert final.line.text == "hola"
    assert partial is None


def test_unknown_events_are_ignored():
    assert map_event({"type": "bidi_response_complete", "stop_reason": "end_turn"}) is None
