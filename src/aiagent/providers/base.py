from typing import Protocol

from aiagent.domain.models import CompletionRequest, CompletionResponse


class CompletionProvider(Protocol):
    def complete(self, request: CompletionRequest) -> CompletionResponse: ...
