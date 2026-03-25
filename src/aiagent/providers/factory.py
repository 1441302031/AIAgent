from aiagent.config.settings import Settings
from aiagent.domain.errors import ConfigurationError

from aiagent.providers.mock import MockProvider


def create_provider(settings: Settings):
    if settings.provider == "mock":
        return MockProvider(mode=settings.mock_mode, scripted_response=settings.mock_response)
    raise ConfigurationError(f"Unsupported provider: {settings.provider}")
