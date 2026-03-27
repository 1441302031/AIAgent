from aiagent.config.provider_config import build_provider_configs


def test_build_provider_configs_returns_mock_settings():
    configs = build_provider_configs(
        mock_mode="echo",
        mock_response="hi",
        moonshot_api_key=None,
        moonshot_api_base="https://api.moonshot.cn/v1",
    )

    assert configs["mock"].mode == "echo"
    assert configs["mock"].response == "hi"


def test_build_provider_configs_returns_deepseek_settings():
    configs = build_provider_configs(
        mock_mode="echo",
        mock_response="hi",
        moonshot_api_key=None,
        moonshot_api_base="https://api.moonshot.cn/v1",
        deepseek_api_key="secret",
        deepseek_api_base="https://api.deepseek.com",
    )

    assert configs["deepseek"].api_key == "secret"
    assert configs["deepseek"].api_base == "https://api.deepseek.com"


def test_build_provider_configs_returns_moonshot_settings():
    configs = build_provider_configs(
        mock_mode="echo",
        mock_response="hi",
        moonshot_api_key="secret",
        moonshot_api_base="https://api.moonshot.cn/v1",
    )

    assert configs["moonshot"].api_key == "secret"
    assert configs["moonshot"].api_base == "https://api.moonshot.cn/v1"
