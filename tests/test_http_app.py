from starlette.testclient import TestClient

from voicebot.application.conversation import ConversationService
from voicebot.domain.audio import AudioFrame
from voicebot.domain.events import AgentSpoke
from voicebot.entrypoints.http.app import create_app

from tests.fakes import FakeConversationSession, FakeGateway


def _client(session: FakeConversationSession | None = None) -> TestClient:
    session = session or FakeConversationSession()
    service = ConversationService(FakeGateway(session))
    return TestClient(create_app(service))


def test_ping_health_check():
    response = _client().get("/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_twilio_webhook_returns_twiml_pointing_to_media_stream():
    response = _client().post("/twilio/voice")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert '<Stream url="wss://testserver/ws/twilio"/>' in response.text


def test_browser_websocket_streams_agent_audio():
    pcm = b"\x01\x00" * 240
    session = FakeConversationSession(
        events=[AgentSpoke(frame=AudioFrame(data=pcm, sample_rate=24000))]
    )
    client = _client(session)

    with client.websocket_connect("/ws") as ws:
        assert ws.receive_bytes() == pcm


def test_browser_websocket_alias_route():
    pcm = b"\x02\x00" * 240
    session = FakeConversationSession(
        events=[AgentSpoke(frame=AudioFrame(data=pcm, sample_rate=24000))]
    )
    client = _client(session)

    with client.websocket_connect("/ws/browser") as ws:
        assert ws.receive_bytes() == pcm
