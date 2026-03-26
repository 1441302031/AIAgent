import aiagent.config as config

from aiagent.config.settings import Settings
from aiagent.domain.errors import ConfigurationError


def test_settings_default_to_mock_provider():
    settings = Settings.from_env({})
    assert settings.provider == "mock"
    assert settings.model == "mock-model"
    assert settings.temperature == 0.0
    assert settings.api_base == "https://api.moonshot.cn/v1"
    assert settings.mock_mode == "echo"
    assert settings.mock_response == "Mock response"
    assert settings.provider_configs["mock"].mode == "echo"
    assert settings.provider_configs["mock"].response == "Mock response"
    assert settings.provider_configs["moonshot"].api_key is None
    assert settings.provider_configs["moonshot"].api_base == "https://api.moonshot.cn/v1"


def test_settings_require_api_key_for_moonshot():
    try:
        Settings.from_env({"AIAGENT_PROVIDER": "moonshot"})
    except ConfigurationError as exc:
        assert "api key" in str(exc).lower()
    else:
        raise AssertionError("Expected configuration error")


def test_settings_re_exported_from_config_package():
    assert config.Settings is Settings


def test_settings_rejects_invalid_temperature():
    try:
        Settings.from_env({"AIAGENT_TEMPERATURE": "hot"})
    except ConfigurationError as exc:
        assert "temperature" in str(exc).lower()
    else:
        raise AssertionError("Expected configuration error")
