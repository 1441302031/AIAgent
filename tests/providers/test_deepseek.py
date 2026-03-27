import json

import httpx
import pytest

from aiagent.domain.errors import AuthenticationError, ProviderError, TransportError
from aiagent.domain.models import CompletionRequest, Message
from aiagent.providers.deepseek import DeepSeekProvider


def test_deepseek_provider_sends_chat_completion_payload():
    sent = {}

    def handler(request: httpx.Request) -> httpx.Response:
        sent["url"] = str(request.url)
        sent["auth"] = request.headers["Authorization"]
        sent["body"] = request.read().decode()
        return httpx.Response(
            200,
            json={
                "model": "deepseek-chat",
                "choices": [{"message": {"role": "assistant", "content": "hello back"}}],
            },
        )

    provider = DeepSeekProvider(
        api_key="secret",
        model="deepseek-chat",
        base_url="https://api.deepseek.com",
        transport=httpx.MockTransport(handler),
    )

    response = provider.complete(
        CompletionRequest(
            model="deepseek-chat",
            messages=[Message(role="user", content="hello")],
            temperature=0.25,
        )
    )

    body = json.loads(sent["body"])
    assert sent["url"].endswith("/chat/completions")
    assert sent["auth"] == "Bearer secret"
    assert body["model"] == "deepseek-chat"
    assert body["messages"] == [{"role": "user", "content": "hello"}]
    assert body["temperature"] == 0.25
    assert response.message.content == "hello back"


def test_deepseek_provider_raises_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": "bad key"}})

    provider = DeepSeekProvider(
        api_key="secret",
        model="deepseek-chat",
        base_url="https://api.deepseek.com",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(AuthenticationError):
        provider.complete(
            CompletionRequest(model="deepseek-chat", messages=[Message(role="user", content="hello")])
        )


def test_deepseek_provider_uses_default_error_message_for_non_object_error_json():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json=["oops"])

    provider = DeepSeekProvider(
        api_key="secret",
        model="deepseek-chat",
        base_url="https://api.deepseek.com",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ProviderError, match="DeepSeek request failed with status 500."):
        provider.complete(
            CompletionRequest(model="deepseek-chat", messages=[Message(role="user", content="hello")])
        )


@pytest.mark.parametrize(
    ("status_code", "message"),
    [
        (500, "server exploded"),
        (429, "too many requests"),
    ],
)
def test_deepseek_provider_raises_provider_error_on_error_status(status_code: int, message: str):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json={"error": {"message": message}})

    provider = DeepSeekProvider(
        api_key="secret",
        model="deepseek-chat",
        base_url="https://api.deepseek.com",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ProviderError, match=message):
        provider.complete(
            CompletionRequest(model="deepseek-chat", messages=[Message(role="user", content="hello")])
        )


def test_deepseek_provider_raises_transport_error_on_http_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    provider = DeepSeekProvider(
        api_key="secret",
        model="deepseek-chat",
        base_url="https://api.deepseek.com",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(TransportError):
        provider.complete(
            CompletionRequest(model="deepseek-chat", messages=[Message(role="user", content="hello")])
        )


@pytest.mark.parametrize(
    ("response", "match"),
    [
        (httpx.Response(200, content=b"{"), "DeepSeek returned an invalid success response."),
        (httpx.Response(200, json={"model": "deepseek-chat"}), "DeepSeek returned an invalid success response."),
        (
            httpx.Response(200, json={"model": "deepseek-chat", "choices": []}),
            "DeepSeek returned an invalid success response.",
        ),
    ],
)
def test_deepseek_provider_raises_provider_error_on_malformed_success_response(
    response: httpx.Response, match: str
):
    def handler(request: httpx.Request) -> httpx.Response:
        return response

    provider = DeepSeekProvider(
        api_key="secret",
        model="deepseek-chat",
        base_url="https://api.deepseek.com",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ProviderError, match=match):
        provider.complete(
            CompletionRequest(model="deepseek-chat", messages=[Message(role="user", content="hello")])
        )
