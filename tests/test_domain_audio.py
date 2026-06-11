import pytest

from voicebot.domain.audio import AudioFrame


def test_valid_frame():
    frame = AudioFrame(data=b"\x00\x00" * 160, sample_rate=16000)
    assert frame.channels == 1
    assert frame.duration_seconds == pytest.approx(0.01)


def test_rejects_odd_byte_count():
    with pytest.raises(ValueError):
        AudioFrame(data=b"\x00", sample_rate=16000)


def test_rejects_invalid_sample_rate():
    with pytest.raises(ValueError):
        AudioFrame(data=b"\x00\x00", sample_rate=0)


def test_rejects_invalid_channels():
    with pytest.raises(ValueError):
        AudioFrame(data=b"\x00\x00", sample_rate=16000, channels=0)
