class StaticSelectionPolicy:
    def __init__(self, default_provider: str = "mock") -> None:
        self._default_provider = default_provider

    def select_provider(self, configured_provider: str | None) -> str:
        if configured_provider:
            return configured_provider
        return self._default_provider
