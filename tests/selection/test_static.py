from aiagent.selection.static import StaticSelectionPolicy


def test_static_selection_returns_explicit_provider():
    policy = StaticSelectionPolicy()

    assert policy.select_provider("moonshot") == "moonshot"


def test_static_selection_returns_default_mock_when_provider_missing():
    policy = StaticSelectionPolicy()

    assert policy.select_provider(None) == "mock"


def test_static_selection_returns_default_provider_when_configured_provider_is_empty():
    policy = StaticSelectionPolicy()

    assert policy.select_provider("") == "mock"


def test_static_selection_returns_custom_default_provider_when_provider_missing():
    policy = StaticSelectionPolicy(default_provider="moonshot")

    assert policy.select_provider(None) == "moonshot"
