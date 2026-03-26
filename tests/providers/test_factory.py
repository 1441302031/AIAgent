import pytest

from aiagent.config.settings import Settings
from aiagent.domain.errors import ConfigurationError
from aiagent.providers import factory
from aiagent.providers.factory import create_provider
from aiagent.providers.mock import MockProvider
from aiagent.providers.moonshot import MoonshotProvider


def test_provider_factory_returns_mock_provider_by_default():
    settings = Settings(
        provider="mock",
        model="mock-model",
        mock_mode="scripted",
        mock_response="factory response",
    )
    provider = create_provider(settings)
    assert isinstance(provider, MockProvider)
    assert provider.mode == "scripted"
    assert provider.scripted_response == "factory response"


def test_provider_factory_routes_mock_creation_through_selection_and_registry(monkeypatch: pytest.MonkeyPatch):
    settings = Settings(
        provider="mock",
        model="mock-model",
        mock_mode="scripted",
        mock_response="factory response",
    )
    selected: list[str | None] = []
    built: list[tuple[str, object]] = []

    class FakeSelectionPolicy:
        def select_provider(self, configured_provider: str | None) -> str:
            selected.append(configured_provider)
            return "mock"

    class FakeRegistry:
        def __init__(self) -> None:
            self._builders: dict[str, object] = {}

        def register(self, name: str, builder: object) -> None:
            self._builders[name] = builder

        def build(self, name: str, config: object) -> object:
            built.append((name, config))
            return self._builders[name](config)

    monkeypatch.setattr(factory, "StaticSelectionPolicy", FakeSelectionPolicy)
    monkeypatch.setattr(factory, "ProviderRegistry", FakeRegistry)

    provider = create_provider(settings)

    assert isinstance(provider, MockProvider)
    assert provider.mode == "scripted"
    assert provider.scripted_response == "factory response"
    assert selected == ["mock"]
    assert built == [("mock", settings.provider_configs["mock"])]


def test_provider_factory_rejects_unsupported_provider():
    settings = Settings(provider="unknown", model="mock-model")
    try:
        create_provider(settings)
    except ConfigurationError as exc:
        assert "Unsupported provider" in str(exc)
    else:
        raise AssertionError("Expected ConfigurationError")


def test_provider_factory_builds_moonshot_provider():
    settings = Settings.from_env(
        {
            "AIAGENT_PROVIDER": "moonshot",
            "AIAGENT_API_KEY": "secret",
            "AIAGENT_MODEL": "moonshot-v1-8k",
        }
    )
    provider = create_provider(settings)
    assert isinstance(provider, MoonshotProvider)


def test_provider_factory_routes_moonshot_creation_through_selection_and_registry(
    monkeypatch: pytest.MonkeyPatch,
):
    settings = Settings.from_env(
        {
            "AIAGENT_PROVIDER": "moonshot",
            "AIAGENT_API_KEY": "secret",
            "AIAGENT_MODEL": "moonshot-v1-8k",
        }
    )
    selected: list[str | None] = []
    built: list[tuple[str, object]] = []

    class FakeSelectionPolicy:
        def select_provider(self, configured_provider: str | None) -> str:
            selected.append(configured_provider)
            return "moonshot"

    class FakeRegistry:
        def __init__(self) -> None:
            self._builders: dict[str, object] = {}

        def register(self, name: str, builder: object) -> None:
            self._builders[name] = builder

        def build(self, name: str, config: object) -> object:
            built.append((name, config))
            return self._builders[name](config)

    monkeypatch.setattr(factory, "StaticSelectionPolicy", FakeSelectionPolicy)
    monkeypatch.setattr(factory, "ProviderRegistry", FakeRegistry)

    provider = create_provider(settings)

    assert isinstance(provider, MoonshotProvider)
    assert provider.api_key == "secret"
    assert provider.model == "moonshot-v1-8k"
    assert selected == ["moonshot"]
    assert built == [("moonshot", settings.provider_configs["moonshot"])]


def test_provider_factory_rejects_empty_provider_string():
    settings = Settings(provider="", model="mock-model")

    with pytest.raises(ConfigurationError, match="Unsupported provider"):
        create_provider(settings)
