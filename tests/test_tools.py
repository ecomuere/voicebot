import io
import json

import pytest

strands = pytest.importorskip("strands", reason="requiere el SDK de strands instalado")

from voicebot.adapters import tools  # noqa: E402


class FakeLambdaClient:
    def __init__(self, response: dict):
        self._response = response
        self.invocations: list[dict] = []

    def invoke(self, FunctionName: str, Payload: bytes) -> dict:
        self.invocations.append({"FunctionName": FunctionName, "Payload": Payload})
        return {"Payload": io.BytesIO(json.dumps(self._response).encode())}


def test_order_status_unavailable_without_configuration(monkeypatch):
    monkeypatch.delenv("VOICEBOT_ORDER_STATUS_FUNCTION", raising=False)
    result = tools.get_order_status("1001")
    assert "no está disponible" in result


def test_order_status_invokes_shared_lambda(monkeypatch):
    monkeypatch.setenv("VOICEBOT_ORDER_STATUS_FUNCTION", "voicebot-order-status")
    fake = FakeLambdaClient(
        {"encontrado": "true", "pedido": "1001", "estado": "enviado", "entrega_estimada": "mañana"}
    )
    monkeypatch.setattr(tools, "_lambda_client", lambda: fake)

    result = tools.get_order_status("1001")

    assert "enviado" in result and "mañana" in result
    invocation = fake.invocations[0]
    assert invocation["FunctionName"] == "voicebot-order-status"
    assert json.loads(invocation["Payload"]) == {"order_id": "1001"}


def test_order_status_not_found(monkeypatch):
    monkeypatch.setenv("VOICEBOT_ORDER_STATUS_FUNCTION", "voicebot-order-status")
    fake = FakeLambdaClient({"encontrado": "false", "mensaje": "No existe ningún pedido 9999"})
    monkeypatch.setattr(tools, "_lambda_client", lambda: fake)

    assert "9999" in tools.get_order_status("9999")
