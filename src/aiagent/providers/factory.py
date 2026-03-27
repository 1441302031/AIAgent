from aiagent.config.settings import Settings
from aiagent.domain.errors import ConfigurationError

from aiagent.providers.deepseek import DeepSeekProvider
from aiagent.providers.mock import MockProvider
from aiagent.providers.moonshot import MoonshotProvider
from aiagent.providers.registry import ProviderRegistry
from aiagent.selection.static import StaticSelectionPolicy


def create_provider(settings: Settings):
    registry = ProviderRegistry()
    registry.register(
        "mock",
        lambda config: MockProvider(mode=config.mode, scripted_response=config.response),
    )
    registry.register("moonshot", lambda config: _build_moonshot_provider(settings, config))
    registry.register("deepseek", lambda config: _build_deepseek_provider(settings, config))

    provider_name = StaticSelectionPolicy().select_provider(settings.provider)
    provider_config = settings.provider_configs.get(provider_name)
    if provider_name in {"mock", "moonshot"} and provider_config is None:
        raise ConfigurationError(f"Missing configuration for provider: {provider_name}")
    return registry.build(provider_name, provider_config)


def _build_moonshot_provider(settings: Settings, config: object) -> MoonshotProvider:
    api_key = getattr(config, "api_key", None)
    if not api_key:
        raise ConfigurationError("Moonshot provider requires an API key.")
    return MoonshotProvider(
        api_key=api_key,
        model=settings.model,
        base_url=getattr(config, "api_base"),
    )


def _build_deepseek_provider(settings: Settings, config: object) -> DeepSeekProvider:
    api_key = getattr(config, "api_key", None)
    if not api_key:
        raise ConfigurationError("DeepSeek provider requires an API key.")
    return DeepSeekProvider(
        api_key=api_key,
        model=settings.model,
        base_url=getattr(config, "api_base"),
    )
