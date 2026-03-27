from __future__ import annotations

import json
from typing import Iterator

import httpx

from aiagent.domain.errors import AuthenticationError, ProviderError, TransportError
from aiagent.domain.models import CompletionEvent, CompletionRequest, CompletionResponse, Message


class DeepSeekProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.client = httpx.Client(
            base_url=base_url.rstrip("/"),
            transport=transport,
            timeout=30.0,
        )

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        payload = self._payload(request)
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            response = self.client.post("/chat/completions", headers=headers, json=payload)
        except httpx.HTTPError as exc:
            raise TransportError("DeepSeek request failed.") from exc

        if response.status_code == 401:
            raise AuthenticationError(_error_message(response, "DeepSeek authentication failed."))
        if 400 <= response.status_code:
            raise ProviderError(_error_message(response, f"DeepSeek request failed with status {response.status_code}."))

        body = _parse_success_response(response)
        choice = body["choices"][0]["message"]
        return CompletionResponse(
            model=body.get("model", request.model or self.model),
            message=Message(role=choice["role"], content=choice["content"]),
            raw=body,
        )

    def stream_complete(self, request: CompletionRequest) -> Iterator[CompletionEvent]:
        payload = self._payload(request)
        payload["stream"] = True
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            with self.client.stream("POST", "/chat/completions", headers=headers, json=payload) as response:
                if response.status_code == 401:
                    raise AuthenticationError(_error_message(response, "DeepSeek authentication failed."))
                if 400 <= response.status_code:
                    raise ProviderError(
                        _error_message(response, f"DeepSeek request failed with status {response.status_code}.")
                    )

                try:
                    saw_done = False
                    for line in response.iter_lines():
                        if not line:
                            continue
                        if line.startswith(":"):
                            continue
                        if not line.startswith("data:"):
                            raise ProviderError("DeepSeek returned an invalid streaming response.")
                        data = line.removeprefix("data:").strip()
                        if not data:
                            continue
                        if data == "[DONE]":
                            saw_done = True
                            break
                        event = _parse_stream_event(data)
                        if event is not None:
                            yield event
                except httpx.HTTPError as exc:
                    raise TransportError("DeepSeek stream failed.") from exc

                if not saw_done:
                    raise ProviderError("DeepSeek streaming response ended before [DONE].")
                yield CompletionEvent(kind="done")
        except httpx.HTTPError as exc:
            raise TransportError("DeepSeek stream failed.") from exc

    def _payload(self, request: CompletionRequest) -> dict:
        return {
            "model": request.model or self.model,
            "messages": [{"role": message.role, "content": message.content} for message in request.messages],
            "temperature": request.temperature,
        }


def _error_message(response: httpx.Response, default: str) -> str:
    try:
        body = response.json()
    except ValueError:
        return default
    if not isinstance(body, dict):
        return default
    error = body.get("error")
    if isinstance(error, dict):
        message = error.get("message")
        if isinstance(message, str) and message:
            return message
    return default


def _parse_success_response(response: httpx.Response) -> dict:
    try:
        body = response.json()
        choices = body["choices"]
        choice = choices[0]
        message = choice["message"]
        role = message["role"]
        content = message["content"]
    except (ValueError, TypeError, KeyError, IndexError) as exc:
        raise ProviderError("DeepSeek returned an invalid success response.") from exc

    if not isinstance(body, dict) or not isinstance(choices, list):
        raise ProviderError("DeepSeek returned an invalid success response.")
    if not isinstance(choice, dict) or not isinstance(message, dict):
        raise ProviderError("DeepSeek returned an invalid success response.")
    if not isinstance(role, str) or not isinstance(content, str):
        raise ProviderError("DeepSeek returned an invalid success response.")
    return body


def _parse_stream_event(data: str) -> CompletionEvent | None:
    try:
        body = json.loads(data)
        choices = body["choices"]
    except (ValueError, TypeError, KeyError) as exc:
        raise ProviderError("DeepSeek returned an invalid streaming response.") from exc

    if not isinstance(body, dict) or not isinstance(choices, list):
        raise ProviderError("DeepSeek returned an invalid streaming response.")

    # `stream_options.include_usage` sends a final usage-only chunk with empty choices.
    if not choices:
        return None

    try:
        choice = choices[0]
        delta = choice["delta"]
    except (TypeError, KeyError, IndexError) as exc:
        raise ProviderError("DeepSeek returned an invalid streaming response.") from exc

    if not isinstance(choice, dict) or not isinstance(delta, dict):
        raise ProviderError("DeepSeek returned an invalid streaming response.")

    reasoning_content = delta.get("reasoning_content")
    if reasoning_content is not None and not isinstance(reasoning_content, str):
        raise ProviderError("DeepSeek returned an invalid streaming response.")

    content = delta.get("content")
    if content is None:
        return None
    if not isinstance(content, str):
        raise ProviderError("DeepSeek returned an invalid streaming response.")
    if not content:
        return None
    return CompletionEvent(kind="content", text=content)
