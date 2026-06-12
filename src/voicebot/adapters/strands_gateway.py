"""Adaptador de ConversationGateway sobre Strands Agents + Amazon Nova Sonic.

Usa el streaming bidireccional experimental de Strands: el audio entra y sale
en tiempo real de Nova Sonic (Bedrock), sin pipeline STT->LLM->TTS.
"""

import base64
from contextlib import asynccontextmanager
from typing import AsyncIterator

from strands.experimental.bidi import BidiAgent
from strands.experimental.bidi.models import BidiNovaSonicModel
from strands.experimental.bidi.tools import stop_conversation
from strands.experimental.bidi.types.events import BidiAudioInputEvent

from voicebot.adapters.strands_events import map_event
from voicebot.adapters.tools import get_current_time, get_order_status, get_weather
from voicebot.config import Settings
from voicebot.domain.audio import AudioFrame
from voicebot.domain.events import ConversationEvent


class StrandsConversationSession:
    """Implementa el puerto ConversationSession sobre un BidiAgent activo."""

    def __init__(self, agent: BidiAgent) -> None:
        self._agent = agent

    async def send_audio(self, frame: AudioFrame) -> None:
        await self._agent.send(
            BidiAudioInputEvent(
                audio=base64.b64encode(frame.data).decode("ascii"),
                format="pcm",
                sample_rate=frame.sample_rate,
                channels=frame.channels,
            )
        )

    async def events(self) -> AsyncIterator[ConversationEvent]:
        async for raw_event in self._agent.receive():
            event = map_event(raw_event)
            if event is not None:
                yield event


class StrandsConversationGateway:
    """Implementa el puerto ConversationGateway creando agentes Strands por sesión."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def build_agent(self) -> BidiAgent:
        model = BidiNovaSonicModel(
            model_id=self._settings.model_id,
            provider_config={"audio": {"voice": self._settings.voice}},
            client_config={"region": self._settings.region},
        )
        return BidiAgent(
            model=model,
            system_prompt=self._settings.system_prompt,
            # stop_conversation permite al usuario terminar la sesión con la voz.
            tools=[get_current_time, get_order_status, get_weather, stop_conversation],
        )

    @asynccontextmanager
    async def open_session(self) -> AsyncIterator[StrandsConversationSession]:
        agent = self.build_agent()
        await agent.start()
        try:
            yield StrandsConversationSession(agent)
        finally:
            await agent.stop()
