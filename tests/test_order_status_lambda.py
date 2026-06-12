from order_status.handler import lambda_handler


def test_direct_invocation_with_known_order():
    result = lambda_handler({"order_id": "1001"})
    assert result["encontrado"] == "true"
    assert result["estado"] == "enviado"


def test_connect_event_shape():
    event = {
        "Details": {
            "ContactData": {"ContactId": "abc"},
            "Parameters": {"order_id": "1002"},
        },
        "Name": "ContactFlowEvent",
    }
    result = lambda_handler(event)
    assert result["encontrado"] == "true"
    assert result["estado"] == "en preparación"


def test_unknown_order():
    result = lambda_handler({"order_id": "9999"})
    assert result["encontrado"] == "false"
    assert "9999" in result["mensaje"]


def test_missing_order_id():
    assert lambda_handler({})["encontrado"] == "false"
    assert lambda_handler({"Details": {"Parameters": {}}})["encontrado"] == "false"


def test_response_is_flat_string_map():
    # Contrato exigido por Amazon Connect: mapa plano de strings.
    for event in ({"order_id": "1001"}, {"order_id": "nope"}, {}):
        result = lambda_handler(event)
        assert all(isinstance(k, str) and isinstance(v, str) for k, v in result.items())
