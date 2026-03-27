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


def test_moonshot_provider_uses_default_error_message_for_non_object_error_json():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json=["oops"])

    provider = MoonshotProvider(
        api_key="secret",
        model="moonshot-v1-8k",
        base_url="https://api.moonshot.cn/v1",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ProviderError, match="Moonshot request failed with status 500."):
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


def test_moonshot_provider_streams_sse_content_and_done_events():
    sent = {}

    def handler(request: httpx.Request) -> httpx.Response:
        sent["body"] = request.read().decode()
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=(
                b'data: {"model":"moonshot-v1-8k","choices":[{"delta":{"content":"Hel"}}]}\n\n'
                b'data: {"model":"moonshot-v1-8k","choices":[{"delta":{"content":"lo"}}]}\n\n'
                b"data: [DONE]\n\n"
            ),
        )

    provider = MoonshotProvider(
        api_key="secret",
        model="moonshot-v1-8k",
        base_url="https://api.moonshot.cn/v1",
        transport=httpx.MockTransport(handler),
    )

    events = list(
        provider.stream_complete(
            CompletionRequest(
                model="moonshot-v1-8k",
                messages=[Message(role="user", content="hello")],
                temperature=0.25,
            )
        )
    )

    body = json.loads(sent["body"])
    assert body["stream"] is True
    assert [event.kind for event in events] == ["content", "content", "done"]
    assert [event.text for event in events if event.kind == "content"] == ["Hel", "lo"]


def test_moonshot_provider_ignores_reasoning_content_and_usage_only_stream_chunks():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=(
                b'data: {"model":"moonshot-v1-8k","choices":[{"delta":{"reasoning_content":"thinking","content":null}}]}\n\n'
                b'data: {"model":"moonshot-v1-8k","choices":[],"usage":{"prompt_tokens":1,"completion_tokens":1}}\n\n'
                b'data: {"model":"moonshot-v1-8k","choices":[{"delta":{"content":"Answer"}}]}\n\n'
                b"data: [DONE]\n\n"
            ),
        )

    provider = MoonshotProvider(
        api_key="secret",
        model="moonshot-v1-8k",
        base_url="https://api.moonshot.cn/v1",
        transport=httpx.MockTransport(handler),
    )

    events = list(
        provider.stream_complete(
            CompletionRequest(
                model="moonshot-v1-8k",
                messages=[Message(role="user", content="hello")],
            )
        )
    )

    assert [event.kind for event in events] == ["content", "done"]
    assert [event.text for event in events if event.kind == "content"] == ["Answer"]


def test_moonshot_provider_raises_provider_error_when_stream_ends_before_done():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=b'data: {"model":"moonshot-v1-8k","choices":[{"delta":{"content":"Hel"}}]}\n\n',
        )

    provider = MoonshotProvider(
        api_key="secret",
        model="moonshot-v1-8k",
        base_url="https://api.moonshot.cn/v1",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ProviderError, match="Moonshot streaming response ended before \\[DONE\\]."):
        list(
            provider.stream_complete(
                CompletionRequest(model="moonshot-v1-8k", messages=[Message(role="user", content="hello")])
            )
        )


def test_moonshot_provider_raises_provider_error_on_malformed_stream_chunk():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=b'data: {"model":"moonshot-v1-8k","choices":[{"delta":123}]}\n\n',
        )

    provider = MoonshotProvider(
        api_key="secret",
        model="moonshot-v1-8k",
        base_url="https://api.moonshot.cn/v1",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ProviderError, match="Moonshot returned an invalid streaming response."):
        list(
            provider.stream_complete(
                CompletionRequest(model="moonshot-v1-8k", messages=[Message(role="user", content="hello")])
            )
        )


def test_moonshot_provider_raises_transport_error_on_stream_failure():
    class FailingStream(httpx.SyncByteStream):
        def __iter__(self):
            yield b'data: {"model":"moonshot-v1-8k","choices":[{"delta":{"content":"Hel"}}]}\n\n'
            raise httpx.ReadError("boom", request=httpx.Request("POST", "https://api.moonshot.cn/v1/chat/completions"))

        def close(self) -> None:
            pass

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, stream=FailingStream())

    provider = MoonshotProvider(
        api_key="secret",
        model="moonshot-v1-8k",
        base_url="https://api.moonshot.cn/v1",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(TransportError):
        list(
            provider.stream_complete(
                CompletionRequest(model="moonshot-v1-8k", messages=[Message(role="user", content="hello")])
            )
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
