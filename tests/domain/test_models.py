from aiagent.domain.errors import ConfigurationError
from aiagent.domain.models import (
    AgentRequest,
    AgentResponse,
    CompletionRequest,
    CompletionResponse,
    Message,
)


def test_message_defaults_metadata_to_empty_dict():
    message = Message(role="user", content="hello")
    assert message.metadata == {}


def test_completion_request_holds_messages_in_order():
    req = CompletionRequest(
        model="mock-model",
        messages=[Message(role="system", content="sys"), Message(role="user", content="hi")],
    )
    assert [m.role for m in req.messages] == ["system", "user"]


def test_completion_request_defaults_temperature_to_zero():
    req = CompletionRequest(model="mock-model", messages=[])
    assert req.temperature == 0.0


def test_completion_response_defaults_raw_to_empty_dict():
    response = CompletionResponse(model="mock-model", message=Message(role="assistant", content="ok"))
    assert response.raw == {}


def test_agent_request_defaults_optional_fields():
    req = AgentRequest(user_input="hello")
    assert req.task_id is None
    assert req.context == {}
    assert req.metadata == {}


def test_agent_response_exposes_final_text():
    response = AgentResponse(final_text="done")
    assert response.final_text == "done"


def test_agent_response_defaults_collection_fields():
    response = AgentResponse(final_text="done")
    assert response.messages == []
    assert response.artifacts == []
    assert response.handoffs == []


def test_configuration_error_is_application_exception():
    error = ConfigurationError("missing key")
    assert str(error) == "missing key"
