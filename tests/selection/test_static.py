from aiagent.selection.static import StaticSelectionPolicy


def test_static_selection_returns_explicit_provider():
    policy = StaticSelectionPolicy()

    assert policy.select_provider("moonshot") == "moonshot"


def test_static_selection_returns_default_mock_when_provider_missing():
    policy = StaticSelectionPolicy()

    assert policy.select_provider(None) == "mock"
