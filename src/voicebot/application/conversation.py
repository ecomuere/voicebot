"""Caso de uso: atender una llamada de voz.

Orquesta el flujo bidireccional entre un transporte (browser, teléfono...) y
una sesión speech-to-speech, sin conocer los detalles de ninguno de los dos.
"""

import asyncio

from voicebot.domain.events import AgentSpoke, Interrupted, TranscriptReady
from voicebot.domain.ports import CallTransport, ConversationGateway, ConversationSession


class ConversationService:
    """Atiende llamadas conectando un CallTransport con una ConversationSession."""

    def __init__(self, gateway: ConversationGateway) -> None:
        self._gateway = gateway

    async def attend_call(self, transport: CallTransport) -> None:
        async with self._gateway.open_session() as session:
            caller_task = asyncio.create_task(
                self._pump_caller(transport, session), name="pump-caller"
            )
            agent_task = asyncio.create_task(
                self._pump_agent(transport, session), name="pump-agent"
            )
            done, pending = await asyncio.wait(
                {caller_task, agent_task}, return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            for task in done:
                task.result()  # propaga errores reales

    @staticmethod
    async def _pump_caller(transport: CallTransport, session: ConversationSession) -> None:
        async for frame in transport.incoming_audio():
            await session.send_audio(frame)

    @staticmethod
    async def _pump_agent(transport: CallTransport, session: ConversationSession) -> None:
        async for event in session.events():
            if isinstance(event, AgentSpoke):
                await transport.play_audio(event.frame)
            elif isinstance(event, Interrupted):
                await transport.interrupt()
            elif isinstance(event, TranscriptReady):
                await transport.show_transcript(event.line)
