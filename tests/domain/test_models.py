from aiagent.domain.errors import ConfigurationError
from aiagent.domain.models import AgentResponse, CompletionRequest, Message


def test_message_defaults_metadata_to_empty_dict():
    message = Message(role="user", content="hello")
    assert message.metadata == {}


def test_completion_request_holds_messages_in_order():
    req = CompletionRequest(
        model="mock-model",
        messages=[Message(role="system", content="sys"), Message(role="user", content="hi")],
    )
    assert [m.role for m in req.messages] == ["system", "user"]


def test_agent_response_exposes_final_text():
    response = AgentResponse(final_text="done")
    assert response.final_text == "done"


def test_configuration_error_is_application_exception():
    error = ConfigurationError("missing key")
    assert str(error) == "missing key"
