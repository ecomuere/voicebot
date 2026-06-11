from voicebot.application.conversation import ConversationService
from voicebot.domain.audio import AudioFrame
from voicebot.domain.events import AgentSpoke, Interrupted, TranscriptLine, TranscriptReady

from tests.fakes import FakeConversationSession, FakeGateway, FakeTransport


def _frame(rate: int = 16000) -> AudioFrame:
    return AudioFrame(data=b"\x01\x00" * 160, sample_rate=rate)


async def test_forwards_caller_audio_to_session():
    session = FakeConversationSession()
    transport = FakeTransport(frames=[_frame(), _frame()])
    service = ConversationService(FakeGateway(session))

    await service.attend_call(transport)

    assert len(session.sent_frames) == 2
    assert all(f.sample_rate == 16000 for f in session.sent_frames)


async def test_delivers_agent_events_to_transport():
    line = TranscriptLine(role="assistant", text="hola")
    session = FakeConversationSession(
        events=[AgentSpoke(frame=_frame(24000)), Interrupted(), TranscriptReady(line=line)]
    )
    transport = FakeTransport(hang_forever=True)
    service = ConversationService(FakeGateway(session))

    await service.attend_call(transport)

    assert len(transport.played) == 1
    assert transport.played[0].sample_rate == 24000
    assert transport.interruptions == 1
    assert transport.transcripts == [line]


async def test_finishes_when_caller_hangs_up_even_if_session_is_open():
    session = FakeConversationSession(hang_forever=True)
    transport = FakeTransport(frames=[_frame()])
    gateway = FakeGateway(session)
    service = ConversationService(gateway)

    await service.attend_call(transport)  # no debe colgarse

    assert session.sent_frames  # se llegó a enviar el audio del llamante
    assert gateway.closed  # la sesión se cierra siempre


async def test_finishes_when_session_ends_even_if_caller_is_silent():
    session = FakeConversationSession(events=[AgentSpoke(frame=_frame(24000))])
    transport = FakeTransport(hang_forever=True)
    gateway = FakeGateway(session)
    service = ConversationService(gateway)

    await service.attend_call(transport)  # no debe colgarse

    assert transport.played
    assert gateway.closed
