from __future__ import annotations

import httpx

from aiagent.domain.errors import AuthenticationError, ProviderError, TransportError
from aiagent.domain.models import CompletionRequest, CompletionResponse, Message


class MoonshotProvider:
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
        payload = {
            "model": request.model or self.model,
            "messages": [{"role": message.role, "content": message.content} for message in request.messages],
            "temperature": request.temperature,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            response = self.client.post("/chat/completions", headers=headers, json=payload)
        except httpx.HTTPError as exc:
            raise TransportError("Moonshot request failed.") from exc

        if response.status_code == 401:
            raise AuthenticationError(_error_message(response, "Moonshot authentication failed."))
        if 400 <= response.status_code:
            raise ProviderError(_error_message(response, f"Moonshot request failed with status {response.status_code}."))

        body = _parse_success_response(response)
        choice = body["choices"][0]["message"]
        return CompletionResponse(
            model=body.get("model", request.model or self.model),
            message=Message(role=choice["role"], content=choice["content"]),
            raw=body,
        )


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
        raise ProviderError("Moonshot returned an invalid success response.") from exc

    if not isinstance(body, dict) or not isinstance(choices, list):
        raise ProviderError("Moonshot returned an invalid success response.")
    if not isinstance(choice, dict) or not isinstance(message, dict):
        raise ProviderError("Moonshot returned an invalid success response.")
    if not isinstance(role, str) or not isinstance(content, str):
        raise ProviderError("Moonshot returned an invalid success response.")
    return body
