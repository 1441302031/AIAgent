from typing import Iterator, Protocol

from aiagent.domain.models import CompletionEvent, CompletionRequest, CompletionResponse


class CompletionProvider(Protocol):
    def complete(self, request: CompletionRequest) -> CompletionResponse: ...

    def stream_complete(self, request: CompletionRequest) -> Iterator[CompletionEvent]: ...
