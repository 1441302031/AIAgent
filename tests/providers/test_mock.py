from aiagent.domain.models import CompletionRequest, Message
from aiagent.domain.errors import ConfigurationError
from aiagent.providers.mock import MockProvider


def test_mock_provider_echoes_last_user_message():
    provider = MockProvider(mode="echo", scripted_response="ignored")
    response = provider.complete(
        CompletionRequest(
            model="mock-model",
            messages=[
                Message(role="system", content="be brief"),
                Message(role="user", content="first"),
                Message(role="assistant", content="ack"),
                Message(role="user", content="hello world"),
            ],
        )
    )
    assert response.message.content == "Mock echo: hello world"


def test_mock_provider_returns_scripted_response():
    provider = MockProvider(mode="scripted", scripted_response="ready")
    response = provider.complete(
        CompletionRequest(
            model="mock-model",
            messages=[Message(role="user", content="ignored")],
        )
    )
    assert response.message.content == "ready"


def test_mock_provider_rejects_invalid_mode():
    try:
        MockProvider(mode="unsupported", scripted_response="ignored")
    except ConfigurationError as exc:
        assert "unsupported" in str(exc).lower()
    else:
        raise AssertionError("Expected ConfigurationError")
