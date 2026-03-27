import aiagent.domain as domain
from aiagent.domain.errors import (
    AiAgentError,
    AuthenticationError,
    ConfigurationError,
    ProviderError,
    TransportError,
)
from aiagent.domain.models import (
    AgentRequest,
    AgentResponse,
    CompletionEvent,
    CompletionRequest,
    CompletionResponse,
    Message,
)
from aiagent.providers.base import CompletionProvider


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


def test_completion_event_defaults_text_to_empty_string():
    event = CompletionEvent(kind="delta")
    assert event.kind == "delta"
    assert event.text == ""


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


def test_configuration_error_inherits_from_aiagent_error():
    assert issubclass(ConfigurationError, AiAgentError)


def test_provider_error_inherits_from_aiagent_error():
    assert issubclass(ProviderError, AiAgentError)


def test_authentication_error_inherits_from_provider_error():
    assert issubclass(AuthenticationError, ProviderError)


def test_transport_error_inherits_from_provider_error():
    assert issubclass(TransportError, ProviderError)


def test_domain_package_re_exports_public_types():
    assert domain.ConfigurationError is ConfigurationError
    assert domain.AgentRequest is AgentRequest
    assert domain.Message is Message


def test_completion_provider_exposes_stream_complete_protocol_method():
    assert hasattr(CompletionProvider, "stream_complete")
