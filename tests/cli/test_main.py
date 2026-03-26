from importlib import import_module

import pytest

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


def test_repl_exits_cleanly_on_keyboard_interrupt(monkeypatch, capsys):
    monkeypatch.delenv("AIAGENT_PROVIDER", raising=False)
    monkeypatch.delenv("AIAGENT_API_KEY", raising=False)
    monkeypatch.delenv("AIAGENT_API_BASE", raising=False)
    monkeypatch.delenv("AIAGENT_MODEL", raising=False)
    monkeypatch.delenv("AIAGENT_TEMPERATURE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_MODE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_RESPONSE", raising=False)
    monkeypatch.setattr("builtins.input", lambda _: (_ for _ in ()).throw(KeyboardInterrupt()))

    exit_code = run_repl()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert output == "\n"


def test_repl_exits_cleanly_on_keyboard_interrupt_during_agent_run(monkeypatch, capsys):
    monkeypatch.delenv("AIAGENT_PROVIDER", raising=False)
    monkeypatch.delenv("AIAGENT_API_KEY", raising=False)
    monkeypatch.delenv("AIAGENT_API_BASE", raising=False)
    monkeypatch.delenv("AIAGENT_MODEL", raising=False)
    monkeypatch.delenv("AIAGENT_TEMPERATURE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_MODE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_RESPONSE", raising=False)
    monkeypatch.setattr("builtins.input", lambda _: "hello")
    monkeypatch.setattr(
        "aiagent.cli.repl.AssistantAgent.run",
        lambda self, request: (_ for _ in ()).throw(KeyboardInterrupt()),
    )

    exit_code = run_repl()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert output == "\n"


def test_repl_exits_on_whitespace_padded_exit_command(monkeypatch):
    monkeypatch.delenv("AIAGENT_PROVIDER", raising=False)
    monkeypatch.delenv("AIAGENT_API_KEY", raising=False)
    monkeypatch.delenv("AIAGENT_API_BASE", raising=False)
    monkeypatch.delenv("AIAGENT_MODEL", raising=False)
    monkeypatch.delenv("AIAGENT_TEMPERATURE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_MODE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_RESPONSE", raising=False)
    monkeypatch.setattr("builtins.input", lambda _: " exit ")
    monkeypatch.setattr(
        "aiagent.cli.repl.AssistantAgent.run",
        lambda self, request: pytest.fail("agent.run should not be called for a padded exit command"),
    )

    exit_code = run_repl()

    assert exit_code == 0
