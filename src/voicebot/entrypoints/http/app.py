"""Servidor HTTP/WebSocket: cliente web y telefonía (Twilio).

Endpoints:
  GET  /              Cliente web para llamar desde el navegador.
  GET  /ping          Health check (contrato de Bedrock AgentCore Runtime).
  WS   /ws            Audio bidireccional (ruta del contrato de AgentCore).
  WS   /ws/browser    Alias de /ws para despliegues self-hosted.
  POST /twilio/voice  Webhook de voz de Twilio (devuelve TwiML).
  WS   /ws/twilio     Twilio Media Streams.
"""

import logging
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response

from voicebot.adapters.browser_transport import BrowserWebSocketTransport
from voicebot.adapters.numpy_transcoder import NumpyAudioTranscoder
from voicebot.adapters.twilio_transport import TwilioWebSocketTransport, build_stream_twiml
from voicebot.application.conversation import ConversationService
from voicebot.config import Settings

logger = logging.getLogger(__name__)

_STATIC_DIR = Path(__file__).parent / "static"


def public_websocket_url(request: Request, path: str) -> str:
    """URL wss pública del servidor, respetando proxies (ngrok, ALB...)."""
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
    return f"wss://{host}{path}"


def create_app(service: ConversationService) -> FastAPI:
    app = FastAPI(title="voicebot")
    transcoder = NumpyAudioTranscoder()

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(_STATIC_DIR / "index.html")

    @app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"status": "healthy"}

    @app.websocket("/ws")
    @app.websocket("/ws/browser")
    async def ws_browser(websocket: WebSocket) -> None:
        await websocket.accept()
        transport = BrowserWebSocketTransport(websocket)
        try:
            await service.attend_call(transport)
        except WebSocketDisconnect:
            pass
        finally:
            logger.info("Llamada de navegador finalizada")

    @app.api_route("/twilio/voice", methods=["GET", "POST"])
    async def twilio_voice(request: Request) -> Response:
        twiml = build_stream_twiml(public_websocket_url(request, "/ws/twilio"))
        return Response(content=twiml, media_type="application/xml")

    @app.websocket("/ws/twilio")
    async def ws_twilio(websocket: WebSocket) -> None:
        await websocket.accept()
        transport = TwilioWebSocketTransport(websocket, transcoder)
        try:
            await service.attend_call(transport)
        except WebSocketDisconnect:
            pass
        finally:
            logger.info("Llamada telefónica finalizada")

    return app


def create_default_app() -> FastAPI:
    """Factoría para uvicorn: construye la app con el cableado de producción."""
    from voicebot.bootstrap import build_conversation_service

    return create_app(build_conversation_service())


def run() -> None:
    import uvicorn

    settings = Settings.from_env()
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(
        "voicebot.entrypoints.http.app:create_default_app",
        factory=True,
        host=settings.host,
        port=settings.port,
    )


if __name__ == "__main__":
    run()
