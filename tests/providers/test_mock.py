from aiagent.domain.models import CompletionRequest, Message
from aiagent.providers.mock import MockProvider


def test_mock_provider_echoes_last_user_message():
    provider = MockProvider(mode="echo", scripted_response="ignored")
    response = provider.complete(
        CompletionRequest(
            model="mock-model",
            messages=[Message(role="user", content="hello world")],
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
