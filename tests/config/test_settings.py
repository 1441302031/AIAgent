from aiagent.config.settings import Settings
from aiagent.domain.errors import ConfigurationError


def test_settings_default_to_mock_provider():
    settings = Settings.from_env({})
    assert settings.provider == "mock"


def test_settings_require_api_key_for_moonshot():
    try:
        Settings.from_env({"AIAGENT_PROVIDER": "moonshot"})
    except ConfigurationError as exc:
        assert "api key" in str(exc).lower()
    else:
        raise AssertionError("Expected configuration error")
