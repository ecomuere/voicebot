import numpy as np
import pytest

from voicebot.adapters.numpy_transcoder import NumpyAudioTranscoder


@pytest.fixture
def transcoder() -> NumpyAudioTranscoder:
    return NumpyAudioTranscoder()


def _sine_pcm16(rate: int, freq: float = 440.0, seconds: float = 0.1, amplitude: float = 0.8):
    t = np.arange(int(rate * seconds)) / rate
    return (np.sin(2 * np.pi * freq * t) * amplitude * 32767).astype("<i2")


def test_mulaw_silence_is_0xff(transcoder):
    assert transcoder.pcm16_to_mulaw(b"\x00\x00") == b"\xff"
    assert transcoder.mulaw_to_pcm16(b"\xff") == b"\x00\x00"


def test_mulaw_is_self_inverse_on_codewords(transcoder):
    # decode -> encode debe devolver el mismo byte para todos los códigos
    # (excepto 0x7f, el "cero negativo", que se normaliza a 0xff).
    codes = bytes(b for b in range(256) if b != 0x7F)
    decoded = transcoder.mulaw_to_pcm16(codes)
    assert transcoder.pcm16_to_mulaw(decoded) == codes


def test_mulaw_roundtrip_snr(transcoder):
    original = _sine_pcm16(8000)
    roundtrip = transcoder.mulaw_to_pcm16(transcoder.pcm16_to_mulaw(original.tobytes()))
    recovered = np.frombuffer(roundtrip, dtype="<i2").astype(np.float64)
    signal = original.astype(np.float64)
    noise = signal - recovered
    snr_db = 10 * np.log10(np.sum(signal**2) / np.sum(noise**2))
    assert snr_db > 30  # G.711 ofrece ~38 dB para señal de voz a buen nivel


def test_resample_changes_length_proportionally(transcoder):
    pcm = _sine_pcm16(8000).tobytes()
    upsampled = transcoder.resample(pcm, 8000, 16000)
    assert len(upsampled) == 2 * len(pcm)
    downsampled = transcoder.resample(upsampled, 24000, 8000)
    assert len(downsampled) == len(upsampled) // 3


def test_resample_same_rate_is_identity(transcoder):
    pcm = _sine_pcm16(16000).tobytes()
    assert transcoder.resample(pcm, 16000, 16000) == pcm


def test_resample_preserves_constant_signal(transcoder):
    pcm = (np.full(800, 1000, dtype="<i2")).tobytes()
    out = np.frombuffer(transcoder.resample(pcm, 8000, 16000), dtype="<i2")
    assert np.all(out == 1000)


def test_empty_input(transcoder):
    assert transcoder.pcm16_to_mulaw(b"") == b""
    assert transcoder.mulaw_to_pcm16(b"") == b""
    assert transcoder.resample(b"", 8000, 16000) == b""
