"""Objetos de valor del dominio relacionados con audio."""

from dataclasses import dataclass

# Frecuencias de muestreo del dominio de una llamada de voz.
TELEPHONY_SAMPLE_RATE = 8000  # G.711 (Twilio Media Streams)
AGENT_INPUT_SAMPLE_RATE = 16000  # entrada esperada por el agente speech-to-speech
AGENT_OUTPUT_SAMPLE_RATE = 24000  # salida producida por el agente


@dataclass(frozen=True, slots=True)
class AudioFrame:
    """Fragmento de audio PCM16 little-endian mono/estéreo."""

    data: bytes
    sample_rate: int
    channels: int = 1

    def __post_init__(self) -> None:
        if self.sample_rate <= 0:
            raise ValueError("sample_rate debe ser positivo")
        if self.channels < 1:
            raise ValueError("channels debe ser >= 1")
        if len(self.data) % 2 != 0:
            raise ValueError("PCM16 requiere un número par de bytes")

    @property
    def duration_seconds(self) -> float:
        samples = len(self.data) // 2 // self.channels
        return samples / self.sample_rate
