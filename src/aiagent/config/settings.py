from __future__ import annotations

import os
from dataclasses import dataclass
from collections.abc import Mapping

from aiagent.domain.errors import ConfigurationError


@dataclass(slots=True)
class Settings:
    provider: str = "mock"
    model: str = "mock-model"
    temperature: float = 0.0
    api_key: str | None = None
    api_base: str = "https://api.moonshot.cn/v1"
    mock_mode: str = "echo"
    mock_response: str = "Mock response"

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
            mock_mode=source.get("AIAGENT_MOCK_MODE", "echo"),
            mock_response=source.get("AIAGENT_MOCK_RESPONSE", "Mock response"),
        )
        if settings.provider == "moonshot" and not settings.api_key:
            raise ConfigurationError("Moonshot provider requires an API key.")
        return settings
