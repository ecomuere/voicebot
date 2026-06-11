"""Configuración del voicebot (leída del entorno en el composition root)."""

import os
from dataclasses import dataclass, field

DEFAULT_SYSTEM_PROMPT = """\
Eres un asistente de voz amable y eficiente. Responde siempre en español,
salvo que el usuario te hable en otro idioma.

Reglas para conversación por voz:
- Respuestas cortas y naturales (1-3 frases), como en una conversación hablada.
- Nada de listas, markdown ni símbolos: solo texto hablable.
- Si necesitas datos (hora, tiempo, etc.), usa tus herramientas.
- Si el usuario quiere terminar, despídete brevemente y finaliza la conversación.
"""


@dataclass(frozen=True)
class Settings:
    # Nova Sonic está disponible en us-east-1, eu-north-1 y ap-northeast-1.
    model_id: str = "amazon.nova-sonic-v1:0"
    region: str = "us-east-1"
    voice: str = "tiffany"
    system_prompt: str = field(default=DEFAULT_SYSTEM_PROMPT)
    host: str = "0.0.0.0"
    port: int = 8000

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            model_id=os.getenv("VOICEBOT_MODEL_ID", cls.model_id),
            region=os.getenv("VOICEBOT_REGION", cls.region),
            voice=os.getenv("VOICEBOT_VOICE", cls.voice),
            system_prompt=os.getenv("VOICEBOT_SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT),
            host=os.getenv("VOICEBOT_HOST", cls.host),
            port=int(os.getenv("VOICEBOT_PORT", str(cls.port))),
        )
