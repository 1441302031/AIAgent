import pytest

from aiagent.domain.errors import ConfigurationError
from aiagent.providers.registry import ProviderRegistry


def test_provider_registry_builds_registered_provider():
    registry = ProviderRegistry()

    class DemoProvider:
        def __init__(self, label: str) -> None:
            self.label = label

    registry.register("demo", lambda config: DemoProvider(config))

    provider = registry.build("demo", "ready")

    assert isinstance(provider, DemoProvider)
    assert provider.label == "ready"


def test_provider_registry_raises_for_unknown_provider():
    registry = ProviderRegistry()

    with pytest.raises(ConfigurationError, match="Unsupported provider: missing"):
        registry.build("missing", object())
