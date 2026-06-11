"""Composition root: aquí (y solo aquí) se cablean adaptadores con casos de uso."""

from voicebot.application.conversation import ConversationService
from voicebot.config import Settings


def build_conversation_service(settings: Settings | None = None) -> ConversationService:
    # Import local para que los módulos testables no arrastren la dependencia de strands.
    from voicebot.adapters.strands_gateway import StrandsConversationGateway

    settings = settings or Settings.from_env()
    return ConversationService(gateway=StrandsConversationGateway(settings))
