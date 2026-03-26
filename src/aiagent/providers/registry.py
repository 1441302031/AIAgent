from collections.abc import Callable

from aiagent.domain.errors import ConfigurationError


class ProviderRegistry:
    def __init__(self) -> None:
        self._builders: dict[str, Callable[[object], object]] = {}

    def register(self, name: str, builder: Callable[[object], object]) -> None:
        self._builders[name] = builder

    def build(self, name: str, config: object) -> object:
        try:
            builder = self._builders[name]
        except KeyError as exc:
            raise ConfigurationError(f"Unsupported provider: {name}") from exc
        return builder(config)
