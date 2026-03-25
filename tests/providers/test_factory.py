from aiagent.config.settings import Settings
from aiagent.domain.errors import ConfigurationError
from aiagent.providers.factory import create_provider
from aiagent.providers.mock import MockProvider


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


def test_provider_factory_rejects_unsupported_provider():
    settings = Settings(provider="moonshot", model="mock-model")
    try:
        create_provider(settings)
    except ConfigurationError as exc:
        assert "Unsupported provider" in str(exc)
    else:
        raise AssertionError("Expected ConfigurationError")
