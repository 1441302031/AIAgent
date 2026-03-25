import json

import httpx
import pytest

from aiagent.domain.errors import AuthenticationError, ProviderError, TransportError
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
        CompletionRequest(
            model="moonshot-v1-8k",
            messages=[Message(role="user", content="hello")],
            temperature=0.25,
        )
    )

    body = json.loads(sent["body"])
    assert sent["url"].endswith("/chat/completions")
    assert sent["auth"] == "Bearer secret"
    assert body["model"] == "moonshot-v1-8k"
    assert body["messages"] == [{"role": "user", "content": "hello"}]
    assert body["temperature"] == 0.25
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


def test_moonshot_provider_raises_provider_error_on_500():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": {"message": "server exploded"}})

    provider = MoonshotProvider(
        api_key="secret",
        model="moonshot-v1-8k",
        base_url="https://api.moonshot.cn/v1",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ProviderError, match="server exploded"):
        provider.complete(
            CompletionRequest(model="moonshot-v1-8k", messages=[Message(role="user", content="hello")])
        )


def test_moonshot_provider_raises_transport_error_on_http_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    provider = MoonshotProvider(
        api_key="secret",
        model="moonshot-v1-8k",
        base_url="https://api.moonshot.cn/v1",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(TransportError):
        provider.complete(
            CompletionRequest(model="moonshot-v1-8k", messages=[Message(role="user", content="hello")])
        )


@pytest.mark.parametrize(
    ("response", "match"),
    [
        (httpx.Response(200, content=b"{"), "Moonshot returned an invalid success response."),
        (httpx.Response(200, json={"model": "moonshot-v1-8k"}), "Moonshot returned an invalid success response."),
        (
            httpx.Response(200, json={"model": "moonshot-v1-8k", "choices": []}),
            "Moonshot returned an invalid success response.",
        ),
    ],
)
def test_moonshot_provider_raises_provider_error_on_malformed_success_response(
    response: httpx.Response, match: str
):
    def handler(request: httpx.Request) -> httpx.Response:
        return response

    provider = MoonshotProvider(
        api_key="secret",
        model="moonshot-v1-8k",
        base_url="https://api.moonshot.cn/v1",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ProviderError, match=match):
        provider.complete(
            CompletionRequest(model="moonshot-v1-8k", messages=[Message(role="user", content="hello")])
        )
