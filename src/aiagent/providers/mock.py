from typing import Iterator

from aiagent.domain.errors import ConfigurationError
from aiagent.domain.models import CompletionEvent, CompletionRequest, CompletionResponse, Message


class MockProvider:
    def __init__(self, mode: str = "echo", scripted_response: str = "Mock response") -> None:
        if mode not in {"echo", "scripted"}:
            raise ConfigurationError(f"Unsupported mock mode: {mode}")
        self.mode = mode
        self.scripted_response = scripted_response

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        last_user_message = next(
            (message for message in reversed(request.messages) if message.role == "user"),
            None,
        )
        if self.mode == "scripted":
            content = self.scripted_response
        else:
            content = f"Mock echo: {last_user_message.content if last_user_message else ''}"
        return CompletionResponse(
            model=request.model,
            message=Message(role="assistant", content=content),
            raw={"provider": "mock", "mode": self.mode},
        )

    def stream_complete(self, request: CompletionRequest) -> Iterator[CompletionEvent]:
        if self.mode == "scripted":
            content = self.scripted_response
        else:
            last_user_message = next(
                (message for message in reversed(request.messages) if message.role == "user"),
                None,
            )
            content = f"Mock echo: {last_user_message.content if last_user_message else ''}"

        yield CompletionEvent(kind="content", text=content)
        yield CompletionEvent(kind="done")
