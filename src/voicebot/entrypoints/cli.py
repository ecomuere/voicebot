"""Modo local: conversación por micrófono y altavoces del equipo.

Uso:
    voicebot-local

Requiere PyAudio (PortAudio instalado en el sistema) y credenciales AWS.
Este modo usa el IO de audio propio de Strands en lugar de un CallTransport,
ya que BidiAudioIO ya resuelve captura/reproducción e interrupciones locales.
"""

import asyncio

from voicebot.config import Settings


async def main() -> None:
    from strands.experimental.bidi.io import BidiAudioIO, BidiTextIO

    from voicebot.adapters.strands_gateway import StrandsConversationGateway

    gateway = StrandsConversationGateway(Settings.from_env())
    agent = gateway.build_agent()  # mismo cableado que el servidor

    audio_io = BidiAudioIO()  # micrófono + altavoces por defecto
    text_io = BidiTextIO()  # transcripción de la conversación por consola

    print("🎙️  Voicebot listo. Habla por el micrófono (Ctrl+C para salir).")
    await agent.run(
        inputs=[audio_io.input()],
        outputs=[audio_io.output(), text_io.output()],
    )


def run() -> None:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Conversación terminada.")


if __name__ == "__main__":
    run()
