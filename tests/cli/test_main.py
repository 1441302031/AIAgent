from importlib import import_module

from aiagent.cli.main import main
from aiagent.cli.repl import run_repl


def test_package_entrypoint_module_exists():
    module = import_module("aiagent.__main__")
    assert module is not None


def test_main_prints_one_shot_response(monkeypatch, capsys):
    monkeypatch.delenv("AIAGENT_PROVIDER", raising=False)
    monkeypatch.delenv("AIAGENT_API_KEY", raising=False)
    monkeypatch.delenv("AIAGENT_API_BASE", raising=False)
    monkeypatch.delenv("AIAGENT_MODEL", raising=False)
    monkeypatch.delenv("AIAGENT_TEMPERATURE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_MODE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_RESPONSE", raising=False)

    exit_code = main(["hello"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Mock echo: hello" in captured.out


def test_main_dispatches_to_repl(monkeypatch):
    monkeypatch.setattr("aiagent.cli.main.run_repl", lambda: 7)

    exit_code = main(["--repl"])

    assert exit_code == 7


def test_repl_exits_on_quit(monkeypatch, capsys):
    monkeypatch.delenv("AIAGENT_PROVIDER", raising=False)
    monkeypatch.delenv("AIAGENT_API_KEY", raising=False)
    monkeypatch.delenv("AIAGENT_API_BASE", raising=False)
    monkeypatch.delenv("AIAGENT_MODEL", raising=False)
    monkeypatch.delenv("AIAGENT_TEMPERATURE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_MODE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_RESPONSE", raising=False)
    inputs = iter(["hello", "quit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    exit_code = run_repl()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Mock echo: hello" in output
