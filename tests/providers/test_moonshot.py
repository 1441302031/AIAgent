import httpx
import pytest

from aiagent.domain.errors import AuthenticationError
from aiagent.domain.models import CompletionRequest, Message
from aiagent.providers.moonshot import MoonshotProvider


def test_moonshot_provider_sends_chat_completion_payload():
    sent = {}

    def handler(request: httpx.Request) -> httpx.Response:
        sent["url"] = str(request.url)
        sent["auth"] = request.headers["Authorization"]
        sent["body"] = request.read().decode()
        return httpx.Response(
            200,
            json={
                "model": "moonshot-v1-8k",
                "choices": [{"message": {"role": "assistant", "content": "hello back"}}],
            },
        )

    transport = httpx.MockTransport(handler)
    provider = MoonshotProvider(
        api_key="secret",
        model="moonshot-v1-8k",
        base_url="https://api.moonshot.cn/v1",
        transport=transport,
    )

    response = provider.complete(
        CompletionRequest(model="moonshot-v1-8k", messages=[Message(role="user", content="hello")])
    )

    assert sent["url"].endswith("/chat/completions")
    assert sent["auth"] == "Bearer secret"
    assert response.message.content == "hello back"


def test_moonshot_provider_raises_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": "bad key"}})

    provider = MoonshotProvider(
        api_key="secret",
        model="moonshot-v1-8k",
        base_url="https://api.moonshot.cn/v1",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(AuthenticationError):
        provider.complete(
            CompletionRequest(model="moonshot-v1-8k", messages=[Message(role="user", content="hello")])
        )
