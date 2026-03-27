from importlib import import_module

import pytest

from aiagent.domain.models import CompletionEvent
from aiagent.cli.main import main
from aiagent.cli.repl import run_repl


def test_package_entrypoint_module_exists():
    module = import_module("aiagent.__main__")
    assert module is not None


def test_main_prints_one_shot_response_via_streaming_renderer(monkeypatch, capsys):
    monkeypatch.delenv("AIAGENT_PROVIDER", raising=False)
    monkeypatch.delenv("AIAGENT_API_KEY", raising=False)
    monkeypatch.delenv("AIAGENT_API_BASE", raising=False)
    monkeypatch.delenv("AIAGENT_MODEL", raising=False)
    monkeypatch.delenv("AIAGENT_TEMPERATURE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_MODE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_RESPONSE", raising=False)
    monkeypatch.setattr(
        "aiagent.cli.main.AssistantAgent.run",
        lambda self, request: pytest.fail("main should use run_stream for one-shot prompts"),
    )
    monkeypatch.setattr(
        "aiagent.cli.main.AssistantAgent.run_stream",
        lambda self, request: iter(
            [
                CompletionEvent(kind="content", text="Mock streamed: hello"),
                CompletionEvent(kind="done"),
            ]
        ),
    )
    renderer_calls = {}

    def fake_renderer(events, **kwargs):
        renderer_calls["called"] = True
        materialized = list(events)
        assert [event.kind for event in materialized] == ["content", "done"]
        kwargs["writer"].write("Mock streamed: hello")
        return "Mock streamed: hello"

    monkeypatch.setattr("aiagent.cli.main.render_streaming_completion", fake_renderer)

    exit_code = main(["hello"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert renderer_calls["called"] is True
    assert "Mock streamed: hello" in captured.out


def test_main_dispatches_to_repl(monkeypatch):
    monkeypatch.setattr("aiagent.cli.main.run_repl", lambda: 7)

    exit_code = main(["--repl"])

    assert exit_code == 7


def test_main_dispatches_multi_agent_flag_to_repl(monkeypatch):
    calls = {}

    def fake_run_repl(*, multi_agent: bool = False):
        calls["multi_agent"] = multi_agent
        return 11

    monkeypatch.setattr("aiagent.cli.main.run_repl", fake_run_repl)

    exit_code = main(["--repl", "--multi-agent"])

    assert exit_code == 11
    assert calls["multi_agent"] is True


def test_main_dispatches_show_subagents_flag_to_repl(monkeypatch):
    calls = {}

    def fake_run_repl(*, multi_agent: bool = False, show_subagents: bool = False):
        calls["multi_agent"] = multi_agent
        calls["show_subagents"] = show_subagents
        return 13

    monkeypatch.setattr("aiagent.cli.main.run_repl", fake_run_repl)

    exit_code = main(["--repl", "--multi-agent", "--show-subagents"])

    assert exit_code == 13
    assert calls["multi_agent"] is True
    assert calls["show_subagents"] is True


def test_repl_prints_streamed_response_and_exits_on_quit(monkeypatch, capsys):
    monkeypatch.delenv("AIAGENT_PROVIDER", raising=False)
    monkeypatch.delenv("AIAGENT_API_KEY", raising=False)
    monkeypatch.delenv("AIAGENT_API_BASE", raising=False)
    monkeypatch.delenv("AIAGENT_MODEL", raising=False)
    monkeypatch.delenv("AIAGENT_TEMPERATURE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_MODE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_RESPONSE", raising=False)
    monkeypatch.setattr(
        "aiagent.cli.repl.AssistantAgent.run",
        lambda self, request: pytest.fail("repl should use run_stream for normal prompts"),
    )
    monkeypatch.setattr(
        "aiagent.cli.repl.AssistantAgent.run_stream",
        lambda self, request: iter(
            [
                CompletionEvent(kind="content", text="Mock streamed: hello"),
                CompletionEvent(kind="done"),
            ]
        ),
    )
    renderer_calls = {}

    def fake_renderer(events, **kwargs):
        renderer_calls["called"] = True
        materialized = list(events)
        assert [event.kind for event in materialized] == ["content", "done"]
        kwargs["writer"].write("Mock streamed: hello")
        return "Mock streamed: hello"

    monkeypatch.setattr("aiagent.cli.repl.render_streaming_completion", fake_renderer)
    inputs = iter(["hello", "quit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    exit_code = run_repl()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert renderer_calls["called"] is True
    assert "Mock streamed: hello" in output


def test_main_uses_coordinator_agent_when_multi_agent_flag_is_set(monkeypatch, capsys):
    monkeypatch.delenv("AIAGENT_PROVIDER", raising=False)
    monkeypatch.delenv("AIAGENT_API_KEY", raising=False)
    monkeypatch.delenv("AIAGENT_API_BASE", raising=False)
    monkeypatch.delenv("AIAGENT_MODEL", raising=False)
    monkeypatch.delenv("AIAGENT_TEMPERATURE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_MODE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_RESPONSE", raising=False)
    monkeypatch.setattr(
        "aiagent.cli.main.AssistantAgent.run_stream",
        lambda self, request: pytest.fail("main should not stream directly from AssistantAgent in multi-agent mode"),
    )
    monkeypatch.setattr(
        "aiagent.cli.main.CoordinatorAgent.run_stream",
        lambda self, request: iter(
            [
                CompletionEvent(kind="content", text="Coordinator streamed: hello"),
                CompletionEvent(kind="done"),
            ]
        ),
    )
    monkeypatch.setattr("aiagent.cli.main.render_streaming_completion", lambda events, **kwargs: "done")

    exit_code = main(["--multi-agent", "hello"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""


def test_main_uses_show_subagents_flag_when_multi_agent_is_enabled(monkeypatch):
    monkeypatch.delenv("AIAGENT_PROVIDER", raising=False)
    monkeypatch.delenv("AIAGENT_API_KEY", raising=False)
    monkeypatch.delenv("AIAGENT_API_BASE", raising=False)
    monkeypatch.delenv("AIAGENT_MODEL", raising=False)
    monkeypatch.delenv("AIAGENT_TEMPERATURE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_MODE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_RESPONSE", raising=False)
    calls = {}

    class FakeCoordinator:
        def __init__(self, *args, **kwargs):
            calls["show_subagents"] = kwargs["show_subagents"]

        def run_stream(self, request):
            return iter([CompletionEvent(kind="content", text="[planner]\n"), CompletionEvent(kind="done")])

    monkeypatch.setattr("aiagent.cli.main.CoordinatorAgent", FakeCoordinator)
    monkeypatch.setattr("aiagent.cli.main.render_streaming_completion", lambda events, **kwargs: "done")

    exit_code = main(["--multi-agent", "--show-subagents", "hello"])

    assert exit_code == 0
    assert calls["show_subagents"] is True


def test_repl_uses_coordinator_agent_when_multi_agent_mode_is_enabled(monkeypatch, capsys):
    monkeypatch.delenv("AIAGENT_PROVIDER", raising=False)
    monkeypatch.delenv("AIAGENT_API_KEY", raising=False)
    monkeypatch.delenv("AIAGENT_API_BASE", raising=False)
    monkeypatch.delenv("AIAGENT_MODEL", raising=False)
    monkeypatch.delenv("AIAGENT_TEMPERATURE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_MODE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_RESPONSE", raising=False)
    monkeypatch.setattr(
        "aiagent.cli.repl.AssistantAgent.run_stream",
        lambda self, request: pytest.fail("repl should not stream directly from AssistantAgent in multi-agent mode"),
    )
    monkeypatch.setattr(
        "aiagent.cli.repl.CoordinatorAgent.run_stream",
        lambda self, request: iter(
            [
                CompletionEvent(kind="content", text="Coordinator streamed: hello"),
                CompletionEvent(kind="done"),
            ]
        ),
    )
    monkeypatch.setattr("aiagent.cli.repl.render_streaming_completion", lambda events, **kwargs: "done")
    inputs = iter(["hello", "quit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    exit_code = run_repl(multi_agent=True)
    output = capsys.readouterr().out

    assert exit_code == 0
    assert output == ""


def test_repl_uses_show_subagents_flag_when_enabled(monkeypatch):
    monkeypatch.delenv("AIAGENT_PROVIDER", raising=False)
    monkeypatch.delenv("AIAGENT_API_KEY", raising=False)
    monkeypatch.delenv("AIAGENT_API_BASE", raising=False)
    monkeypatch.delenv("AIAGENT_MODEL", raising=False)
    monkeypatch.delenv("AIAGENT_TEMPERATURE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_MODE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_RESPONSE", raising=False)
    calls = {}

    class FakeCoordinator:
        def __init__(self, *args, **kwargs):
            calls["show_subagents"] = kwargs["show_subagents"]

        def run_stream(self, request):
            return iter([CompletionEvent(kind="content", text="[planner]\n"), CompletionEvent(kind="done")])

    monkeypatch.setattr("aiagent.cli.repl.CoordinatorAgent", FakeCoordinator)
    monkeypatch.setattr("aiagent.cli.repl.render_streaming_completion", lambda events, **kwargs: "done")
    inputs = iter(["hello", "quit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    exit_code = run_repl(multi_agent=True, show_subagents=True)

    assert exit_code == 0
    assert calls["show_subagents"] is True


def test_repl_exits_cleanly_on_keyboard_interrupt(monkeypatch, capsys):
    monkeypatch.delenv("AIAGENT_PROVIDER", raising=False)
    monkeypatch.delenv("AIAGENT_API_KEY", raising=False)
    monkeypatch.delenv("AIAGENT_API_BASE", raising=False)
    monkeypatch.delenv("AIAGENT_MODEL", raising=False)
    monkeypatch.delenv("AIAGENT_TEMPERATURE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_MODE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_RESPONSE", raising=False)
    monkeypatch.setattr(
        "builtins.input",
        lambda _: (_ for _ in ()).throw(KeyboardInterrupt()),
    )

    exit_code = run_repl()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert output == "\n"


def test_repl_exits_cleanly_on_eof(monkeypatch, capsys):
    monkeypatch.delenv("AIAGENT_PROVIDER", raising=False)
    monkeypatch.delenv("AIAGENT_API_KEY", raising=False)
    monkeypatch.delenv("AIAGENT_API_BASE", raising=False)
    monkeypatch.delenv("AIAGENT_MODEL", raising=False)
    monkeypatch.delenv("AIAGENT_TEMPERATURE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_MODE", raising=False)
    monkeypatch.delenv("AIAGENT_MOCK_RESPONSE", raising=False)
    monkeypatch.setattr(
        "builtins.input",
        lambda _: (_ for _ in ()).throw(EOFError()),
    )

    exit_code = run_repl()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert output == ""


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
        lambda self, request: pytest.fail("repl should use run_stream when handling interrupts"),
    )
    monkeypatch.setattr(
        "aiagent.cli.repl.AssistantAgent.run_stream",
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
