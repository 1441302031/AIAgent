from aiagent.config.settings import Settings
from aiagent.domain.errors import ConfigurationError

from aiagent.providers.mock import MockProvider
from aiagent.providers.moonshot import MoonshotProvider


def create_provider(settings: Settings):
    if settings.provider == "mock":
        return MockProvider(mode=settings.mock_mode, scripted_response=settings.mock_response)
    if settings.provider == "moonshot":
        if not settings.api_key:
            raise ConfigurationError("Moonshot provider requires an API key.")
        return MoonshotProvider(
            api_key=settings.api_key,
            model=settings.model,
            base_url=settings.api_base,
        )
    raise ConfigurationError(f"Unsupported provider: {settings.provider}")
