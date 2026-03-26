from typing import Protocol


class SelectionPolicy(Protocol):
    def select_provider(self, configured_provider: str | None) -> str: ...
