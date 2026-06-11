"""Adaptador de AudioTranscoder con numpy: G.711 μ-law y remuestreo PCM16.

Twilio Media Streams usa μ-law mono a 8 kHz; el agente espera PCM16 a 16 kHz
de entrada y produce PCM16 a 24 kHz de salida.
"""

import numpy as np

_BIAS = 0x84
_CLIP = 32635


class NumpyAudioTranscoder:
    def pcm16_to_mulaw(self, pcm: bytes) -> bytes:
        """Codifica PCM16 little-endian a G.711 μ-law."""
        if not pcm:
            return b""
        x = np.frombuffer(pcm, dtype="<i2").astype(np.int32)
        sign = (x < 0).astype(np.int32)
        mag = np.minimum(np.abs(x), _CLIP) + _BIAS
        exponent = np.floor(np.log2(mag)).astype(np.int32) - 7
        mantissa = (mag >> (exponent + 3)) & 0x0F
        mu = ~((sign << 7) | (exponent << 4) | mantissa) & 0xFF
        return mu.astype(np.uint8).tobytes()

    def mulaw_to_pcm16(self, mu: bytes) -> bytes:
        """Decodifica G.711 μ-law a PCM16 little-endian."""
        if not mu:
            return b""
        u = (~np.frombuffer(mu, dtype=np.uint8)) & 0xFF
        sign = (u & 0x80) != 0
        exponent = ((u >> 4) & 0x07).astype(np.int32)
        mantissa = (u & 0x0F).astype(np.int32)
        x = (((mantissa << 3) + _BIAS) << exponent) - _BIAS
        x = np.where(sign, -x, x)
        return x.astype("<i2").tobytes()

    def resample(self, pcm: bytes, src_rate: int, dst_rate: int) -> bytes:
        """Remuestrea PCM16 mono por interpolación lineal (suficiente para voz)."""
        if not pcm or src_rate == dst_rate:
            return pcm
        x = np.frombuffer(pcm, dtype="<i2").astype(np.float32)
        n_out = int(round(len(x) * dst_rate / src_rate))
        if n_out <= 0:
            return b""
        positions = np.linspace(0, len(x) - 1, n_out)
        y = np.interp(positions, np.arange(len(x)), x)
        return np.clip(y, -32768, 32767).astype("<i2").tobytes()
