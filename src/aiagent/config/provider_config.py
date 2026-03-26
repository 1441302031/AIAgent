from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MockProviderConfig:
    mode: str
    response: str


@dataclass(frozen=True, slots=True)
class MoonshotProviderConfig:
    api_key: str | None
    api_base: str


ProviderConfigMap = dict[str, MockProviderConfig | MoonshotProviderConfig]


def build_provider_configs(
    *,
    mock_mode: str,
    mock_response: str,
    moonshot_api_key: str | None,
    moonshot_api_base: str,
) -> ProviderConfigMap:
    return {
        "mock": MockProviderConfig(mode=mock_mode, response=mock_response),
        "moonshot": MoonshotProviderConfig(
            api_key=moonshot_api_key,
            api_base=moonshot_api_base,
        ),
    }
