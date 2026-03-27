from __future__ import annotations

import os
from dataclasses import dataclass
from collections.abc import Mapping

from aiagent.config.provider_config import ProviderConfigMap, build_provider_configs
from aiagent.domain.errors import ConfigurationError


@dataclass(slots=True)
class Settings:
    provider: str = "mock"
    model: str = "mock-model"
    temperature: float = 0.0
    api_key: str | None = None
    api_base: str = "https://api.moonshot.cn/v1"
    deepseek_api_key: str | None = None
    deepseek_api_base: str = "https://api.deepseek.com"
    mock_mode: str = "echo"
    mock_response: str = "Mock response"

    @property
    def provider_configs(self) -> ProviderConfigMap:
        return build_provider_configs(
            mock_mode=self.mock_mode,
            mock_response=self.mock_response,
            moonshot_api_key=self.api_key,
            moonshot_api_base=self.api_base,
            deepseek_api_key=self.deepseek_api_key,
            deepseek_api_base=self.deepseek_api_base,
        )

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        source = os.environ if env is None else env
        temperature_raw = source.get("AIAGENT_TEMPERATURE", 0.0)
        try:
            temperature = float(temperature_raw)
        except (TypeError, ValueError) as exc:
            raise ConfigurationError("Invalid AIAGENT_TEMPERATURE value.") from exc
        settings = cls(
            provider=source.get("AIAGENT_PROVIDER", "mock"),
            model=source.get("AIAGENT_MODEL", "mock-model"),
            temperature=temperature,
            api_key=source.get("AIAGENT_API_KEY"),
            api_base=source.get("AIAGENT_API_BASE", "https://api.moonshot.cn/v1"),
            deepseek_api_key=source.get("AIAGENT_DEEPSEEK_API_KEY"),
            deepseek_api_base=source.get(
                "AIAGENT_DEEPSEEK_API_BASE", "https://api.deepseek.com"
            ),
            mock_mode=source.get("AIAGENT_MOCK_MODE", "echo"),
            mock_response=source.get("AIAGENT_MOCK_RESPONSE", "Mock response"),
        )
        if settings.provider == "moonshot" and not settings.api_key:
            raise ConfigurationError("Moonshot provider requires an API key.")
        if settings.provider == "deepseek" and not settings.deepseek_api_key:
            raise ConfigurationError("DeepSeek provider requires an API key.")
        return settings
