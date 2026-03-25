# AIAgent Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first runnable version of `aiagent` with a reusable Python library core, a default mock provider, a Moonshot-compatible provider adapter, and both one-shot and REPL CLI entrypoints.

**Architecture:** The implementation follows a layered design: stable domain models and errors at the bottom, configuration and provider selection above that, prompt/session utilities in the middle, a single assistant agent for orchestration, and a thin CLI at the edge. The default runtime uses a deterministic mock provider so the full flow works without credentials, while the Moonshot adapter is implemented and validated behind configuration for later activation.

**Tech Stack:** Python 3.11+, `pytest`, `httpx`, standard library `argparse`, `dataclasses`, and `typing`

---

## File Structure Map

- `pyproject.toml`: package metadata, dependencies, pytest configuration, console entry metadata
- `README.md`: usage, configuration, and local development instructions
- `src/aiagent/__init__.py`: package export surface
- `src/aiagent/__main__.py`: `python -m aiagent` entrypoint
- `src/aiagent/config/settings.py`: load and validate env-based settings
- `src/aiagent/domain/models.py`: message, completion, and agent dataclasses
- `src/aiagent/domain/errors.py`: normalized application exceptions
- `src/aiagent/prompts/system.py`: default assistant system prompt
- `src/aiagent/prompts/templates.py`: prompt assembly helpers
- `src/aiagent/providers/base.py`: provider protocol / interface
- `src/aiagent/providers/factory.py`: choose provider from settings
- `src/aiagent/providers/mock.py`: deterministic local mock provider
- `src/aiagent/providers/moonshot.py`: Moonshot-compatible HTTP adapter
- `src/aiagent/session/history.py`: in-memory conversation history
- `src/aiagent/agents/base.py`: agent interface
- `src/aiagent/agents/assistant.py`: single assistant agent orchestration
- `src/aiagent/cli/main.py`: argument parsing and one-shot/repl dispatch
- `src/aiagent/cli/repl.py`: REPL loop
- `tests/domain/test_models.py`: domain model behavior tests
- `tests/config/test_settings.py`: settings validation tests
- `tests/providers/test_factory.py`: provider selection tests
- `tests/providers/test_mock.py`: mock provider tests
- `tests/providers/test_moonshot.py`: Moonshot adapter tests
- `tests/prompts/test_templates.py`: prompt assembly tests
- `tests/session/test_history.py`: history management tests
- `tests/agents/test_assistant.py`: assistant agent orchestration tests
- `tests/cli/test_main.py`: CLI integration tests

### Task 1: Project Skeleton and Tooling

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/aiagent/__init__.py`
- Create: `src/aiagent/__main__.py`
- Create: `src/aiagent/cli/main.py`
- Create: `src/aiagent/config/__init__.py`
- Create: `src/aiagent/domain/__init__.py`
- Create: `src/aiagent/prompts/__init__.py`
- Create: `src/aiagent/providers/__init__.py`
- Create: `src/aiagent/session/__init__.py`
- Create: `src/aiagent/agents/__init__.py`
- Create: `src/aiagent/cli/__init__.py`
- Create: `tests/__init__.py`
- Test: `tests/cli/test_main.py`

- [ ] **Step 1: Write the failing smoke test for module startup**

```python
from importlib import import_module


def test_package_entrypoint_module_exists():
    module = import_module("aiagent.__main__")
    assert module is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/cli/test_main.py::test_package_entrypoint_module_exists -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'aiagent'`

- [ ] **Step 3: Write minimal packaging and package files**

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "aiagent"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["httpx>=0.27,<1.0"]

[project.optional-dependencies]
dev = ["pytest>=8.0,<9.0"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

```python
# src/aiagent/__main__.py
from aiagent.cli.main import main


if __name__ == "__main__":
    raise SystemExit(main())
```

```python
# src/aiagent/cli/main.py
def main(argv: list[str] | None = None) -> int:
    return 0
```

- [ ] **Step 4: Run the smoke test to verify it passes**

Run: `python -m pytest tests/cli/test_main.py::test_package_entrypoint_module_exists -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml README.md src tests
git commit -m "chore: bootstrap aiagent package skeleton"
```

### Task 2: Domain Models and Normalized Errors

**Files:**
- Create: `src/aiagent/domain/models.py`
- Create: `src/aiagent/domain/errors.py`
- Modify: `src/aiagent/domain/__init__.py`
- Test: `tests/domain/test_models.py`

- [ ] **Step 1: Write the failing tests for core dataclasses and errors**

```python
from aiagent.domain.errors import ConfigurationError
from aiagent.domain.models import AgentResponse, CompletionRequest, Message


def test_message_defaults_metadata_to_empty_dict():
    message = Message(role="user", content="hello")
    assert message.metadata == {}


def test_completion_request_holds_messages_in_order():
    req = CompletionRequest(
        model="mock-model",
        messages=[Message(role="system", content="sys"), Message(role="user", content="hi")],
    )
    assert [m.role for m in req.messages] == ["system", "user"]


def test_agent_response_exposes_final_text():
    response = AgentResponse(final_text="done")
    assert response.final_text == "done"


def test_configuration_error_is_application_exception():
    error = ConfigurationError("missing key")
    assert str(error) == "missing key"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/domain/test_models.py -v`
Expected: FAIL because `aiagent.domain.models` and `aiagent.domain.errors` do not exist yet

- [ ] **Step 3: Write minimal dataclasses and errors**

```python
from dataclasses import dataclass, field


@dataclass(slots=True)
class Message:
    role: str
    content: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class CompletionRequest:
    model: str
    messages: list[Message]
    temperature: float = 0.0


@dataclass(slots=True)
class CompletionResponse:
    model: str
    message: Message
    raw: dict = field(default_factory=dict)


@dataclass(slots=True)
class AgentRequest:
    user_input: str
    task_id: str | None = None
    context: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


@dataclass(slots=True)
class AgentResponse:
    final_text: str
    messages: list[Message] = field(default_factory=list)
    artifacts: list[dict] = field(default_factory=list)
    handoffs: list[dict] = field(default_factory=list)
```

```python
class AiAgentError(Exception):
    """Base application exception."""


class ConfigurationError(AiAgentError):
    pass


class ProviderError(AiAgentError):
    pass


class AuthenticationError(ProviderError):
    pass


class TransportError(ProviderError):
    pass


class AgentError(AiAgentError):
    pass
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/domain/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/aiagent/domain tests/domain/test_models.py
git commit -m "feat: add core domain models and errors"
```

### Task 3: Settings Loading and Provider Factory

**Files:**
- Create: `src/aiagent/config/settings.py`
- Create: `src/aiagent/providers/base.py`
- Modify: `src/aiagent/config/__init__.py`
- Test: `tests/config/test_settings.py`

- [ ] **Step 1: Write the failing tests for settings defaults and credential validation**

```python
from aiagent.config.settings import Settings


def test_settings_default_to_mock_provider():
    settings = Settings.from_env({})
    assert settings.provider == "mock"


def test_settings_require_api_key_for_moonshot():
    try:
        Settings.from_env({"AIAGENT_PROVIDER": "moonshot"})
    except Exception as exc:
        assert "api key" in str(exc).lower()
    else:
        raise AssertionError("Expected configuration error")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/config/test_settings.py -v`
Expected: FAIL because settings are not implemented

- [ ] **Step 3: Write minimal settings model and factory**

```python
from dataclasses import dataclass
import os

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
    def from_env(cls, env: dict[str, str] | None = None) -> "Settings":
        source = env or os.environ
        settings = cls(
            provider=source.get("AIAGENT_PROVIDER", "mock"),
            model=source.get("AIAGENT_MODEL", "mock-model"),
            temperature=float(source.get("AIAGENT_TEMPERATURE", "0.0")),
            api_key=source.get("AIAGENT_API_KEY"),
            api_base=source.get("AIAGENT_API_BASE", "https://api.moonshot.cn/v1"),
            mock_mode=source.get("AIAGENT_MOCK_MODE", "echo"),
            mock_response=source.get("AIAGENT_MOCK_RESPONSE", "Mock response"),
        )
        if settings.provider == "moonshot" and not settings.api_key:
            raise ConfigurationError("Moonshot provider requires an API key.")
        return settings
```

```python
from typing import Protocol

from aiagent.domain.models import CompletionRequest, CompletionResponse


class CompletionProvider(Protocol):
    def complete(self, request: CompletionRequest) -> CompletionResponse: ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/config/test_settings.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/aiagent/config src/aiagent/providers/base.py tests/config/test_settings.py
git commit -m "feat: add settings loader and provider protocol"
```

### Task 4: Mock Provider

**Files:**
- Create: `src/aiagent/providers/mock.py`
- Create: `src/aiagent/providers/factory.py`
- Modify: `src/aiagent/providers/__init__.py`
- Test: `tests/providers/test_mock.py`
- Test: `tests/providers/test_factory.py`

- [ ] **Step 1: Write the failing tests for mock behavior and provider selection**

```python
from aiagent.config.settings import Settings
from aiagent.domain.models import CompletionRequest, Message
from aiagent.providers.factory import create_provider
from aiagent.providers.mock import MockProvider


def test_mock_provider_echoes_last_user_message():
    provider = MockProvider(mode="echo", scripted_response="ignored")
    response = provider.complete(
        CompletionRequest(
            model="mock-model",
            messages=[Message(role="user", content="hello world")],
        )
    )
    assert response.message.content == "Mock echo: hello world"


def test_mock_provider_returns_scripted_response():
    provider = MockProvider(mode="scripted", scripted_response="ready")
    response = provider.complete(
        CompletionRequest(
            model="mock-model",
            messages=[Message(role="user", content="ignored")],
        )
    )
    assert response.message.content == "ready"


def test_provider_factory_returns_mock_provider_by_default():
    settings = Settings.from_env({})
    provider = create_provider(settings)
    assert isinstance(provider, MockProvider)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/providers/test_mock.py tests/providers/test_factory.py -v`
Expected: FAIL because `MockProvider` is not implemented

- [ ] **Step 3: Write minimal mock provider**

```python
from aiagent.domain.models import CompletionRequest, CompletionResponse, Message


class MockProvider:
    def __init__(self, mode: str = "echo", scripted_response: str = "Mock response") -> None:
        self._mode = mode
        self._scripted_response = scripted_response

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        last_user = next(
            (message for message in reversed(request.messages) if message.role == "user"),
            Message(role="user", content=""),
        )
        content = (
            self._scripted_response
            if self._mode == "scripted"
            else f"Mock echo: {last_user.content}"
        )
        return CompletionResponse(
            model=request.model,
            message=Message(role="assistant", content=content),
            raw={"provider": "mock", "mode": self._mode},
        )
```

```python
from aiagent.domain.errors import ConfigurationError
from aiagent.providers.mock import MockProvider


def create_provider(settings):
    if settings.provider == "mock":
        return MockProvider(mode=settings.mock_mode, scripted_response=settings.mock_response)
    raise ConfigurationError(f"Unsupported provider: {settings.provider}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/providers/test_mock.py tests/providers/test_factory.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/aiagent/providers tests/providers
git commit -m "feat: add deterministic mock provider"
```

### Task 5: Moonshot-Compatible Provider

**Files:**
- Create: `src/aiagent/providers/moonshot.py`
- Modify: `src/aiagent/providers/factory.py`
- Modify: `src/aiagent/providers/__init__.py`
- Test: `tests/providers/test_moonshot.py`
- Test: `tests/providers/test_factory.py`

- [ ] **Step 1: Write the failing tests for Moonshot request shaping and missing credentials**

```python
import httpx
import pytest

from aiagent.domain.errors import AuthenticationError
from aiagent.domain.models import CompletionRequest, Message
from aiagent.config.settings import Settings
from aiagent.providers.factory import create_provider
from aiagent.providers.moonshot import MoonshotProvider


def test_moonshot_provider_sends_chat_completion_payload():
    sent = {}

    def handler(request: httpx.Request) -> httpx.Response:
        sent["url"] = str(request.url)
        sent["auth"] = request.headers["Authorization"]
        sent["body"] = request.read().decode()
        return httpx.Response(
            200,
            json={
                "model": "moonshot-v1-8k",
                "choices": [{"message": {"role": "assistant", "content": "hello back"}}],
            },
        )

    transport = httpx.MockTransport(handler)
    provider = MoonshotProvider(
        api_key="secret",
        model="moonshot-v1-8k",
        base_url="https://api.moonshot.cn/v1",
        transport=transport,
    )

    response = provider.complete(
        CompletionRequest(model="moonshot-v1-8k", messages=[Message(role="user", content="hello")])
    )

    assert sent["url"].endswith("/chat/completions")
    assert sent["auth"] == "Bearer secret"
    assert response.message.content == "hello back"


def test_moonshot_provider_raises_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": "bad key"}})

    provider = MoonshotProvider(
        api_key="secret",
        model="moonshot-v1-8k",
        base_url="https://api.moonshot.cn/v1",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(AuthenticationError):
        provider.complete(
            CompletionRequest(model="moonshot-v1-8k", messages=[Message(role="user", content="hello")])
        )


def test_provider_factory_builds_moonshot_provider():
    settings = Settings.from_env(
        {
            "AIAGENT_PROVIDER": "moonshot",
            "AIAGENT_API_KEY": "secret",
            "AIAGENT_MODEL": "moonshot-v1-8k",
        }
    )
    provider = create_provider(settings)
    assert isinstance(provider, MoonshotProvider)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/providers/test_moonshot.py -v`
Expected: FAIL because `MoonshotProvider` is not implemented

- [ ] **Step 3: Write minimal Moonshot provider**

```python
import httpx

from aiagent.domain.errors import AuthenticationError, ProviderError, TransportError
from aiagent.domain.models import CompletionRequest, CompletionResponse, Message


class MoonshotProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._client = httpx.Client(base_url=base_url.rstrip("/"), transport=transport, timeout=30.0)

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        payload = {
            "model": request.model or self._model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
        }
        try:
            response = self._client.post(
                "/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json=payload,
            )
        except httpx.HTTPError as exc:
            raise TransportError(str(exc)) from exc
        if response.status_code == 401:
            raise AuthenticationError("Moonshot authentication failed.")
        if response.status_code >= 400:
            raise ProviderError(f"Moonshot request failed with status {response.status_code}.")
        data = response.json()
        message = data["choices"][0]["message"]
        return CompletionResponse(
            model=data.get("model", request.model),
            message=Message(role=message["role"], content=message["content"]),
            raw=data,
        )
```

```python
from aiagent.domain.errors import ConfigurationError
from aiagent.providers.mock import MockProvider
from aiagent.providers.moonshot import MoonshotProvider


def create_provider(settings):
    if settings.provider == "mock":
        return MockProvider(mode=settings.mock_mode, scripted_response=settings.mock_response)
    if settings.provider == "moonshot":
        return MoonshotProvider(
            api_key=settings.api_key,
            model=settings.model,
            base_url=settings.api_base,
        )
    raise ConfigurationError(f"Unsupported provider: {settings.provider}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/providers/test_moonshot.py tests/providers/test_factory.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/aiagent/providers tests/providers
git commit -m "feat: add moonshot compatible provider"
```

### Task 6: Prompt Assembly and Session History

**Files:**
- Create: `src/aiagent/prompts/system.py`
- Create: `src/aiagent/prompts/templates.py`
- Create: `src/aiagent/session/history.py`
- Modify: `src/aiagent/prompts/__init__.py`
- Modify: `src/aiagent/session/__init__.py`
- Test: `tests/prompts/test_templates.py`
- Test: `tests/session/test_history.py`

- [ ] **Step 1: Write the failing tests for history management and prompt assembly**

```python
from aiagent.domain.models import Message
from aiagent.prompts.templates import build_messages
from aiagent.session.history import SessionHistory


def test_session_history_appends_messages_in_order():
    history = SessionHistory()
    history.add(Message(role="user", content="hello"))
    history.add(Message(role="assistant", content="hi"))
    assert [m.role for m in history.all()] == ["user", "assistant"]


def test_build_messages_prepends_system_prompt():
    history = SessionHistory()
    history.add(Message(role="assistant", content="earlier"))
    messages = build_messages("system text", history.all(), "next user input")
    assert messages[0].role == "system"
    assert messages[-1].content == "next user input"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/prompts/test_templates.py tests/session/test_history.py -v`
Expected: FAIL because history and prompt helpers are not implemented

- [ ] **Step 3: Write minimal history and prompt helpers**

```python
# src/aiagent/session/history.py
from aiagent.domain.models import Message


class SessionHistory:
    def __init__(self) -> None:
        self._messages: list[Message] = []

    def add(self, message: Message) -> None:
        self._messages.append(message)

    def all(self) -> list[Message]:
        return list(self._messages)
```

```python
# src/aiagent/prompts/system.py
DEFAULT_SYSTEM_PROMPT = "You are a helpful AI assistant."
```

```python
# src/aiagent/prompts/templates.py
from aiagent.domain.models import Message


def build_messages(system_prompt: str, history: list[Message], user_input: str) -> list[Message]:
    return [Message(role="system", content=system_prompt), *history, Message(role="user", content=user_input)]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/prompts/test_templates.py tests/session/test_history.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/aiagent/prompts src/aiagent/session tests/prompts tests/session
git commit -m "feat: add prompt builder and session history"
```

### Task 7: Assistant Agent Orchestration

**Files:**
- Create: `src/aiagent/agents/base.py`
- Create: `src/aiagent/agents/assistant.py`
- Modify: `src/aiagent/agents/__init__.py`
- Test: `tests/agents/test_assistant.py`

- [ ] **Step 1: Write the failing tests for assistant agent request flow**

```python
from aiagent.agents.assistant import AssistantAgent
from aiagent.domain.models import AgentRequest, Message
from aiagent.providers.mock import MockProvider
from aiagent.session.history import SessionHistory


def test_assistant_agent_adds_user_and_assistant_messages_to_history():
    history = SessionHistory()
    agent = AssistantAgent(
        provider=MockProvider(mode="scripted", scripted_response="done"),
        history=history,
        model="mock-model",
    )

    response = agent.run(AgentRequest(user_input="help me"))

    assert response.final_text == "done"
    assert [m.role for m in history.all()] == ["user", "assistant"]


def test_assistant_agent_includes_prior_history_in_provider_request():
    history = SessionHistory()
    history.add(Message(role="assistant", content="prior"))
    agent = AssistantAgent(provider=MockProvider(mode="echo"), history=history, model="mock-model")

    response = agent.run(AgentRequest(user_input="hello"))

    assert response.final_text == "Mock echo: hello"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/agents/test_assistant.py -v`
Expected: FAIL because `AssistantAgent` is not implemented

- [ ] **Step 3: Write minimal agent interface and assistant implementation**

```python
from typing import Protocol

from aiagent.domain.models import AgentRequest, AgentResponse


class Agent(Protocol):
    def run(self, request: AgentRequest) -> AgentResponse: ...
```

```python
from aiagent.domain.models import AgentRequest, AgentResponse, CompletionRequest, Message
from aiagent.prompts.system import DEFAULT_SYSTEM_PROMPT
from aiagent.prompts.templates import build_messages


class AssistantAgent:
    def __init__(
        self,
        provider,
        history,
        model: str,
        temperature: float = 0.0,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        self._provider = provider
        self._history = history
        self._model = model
        self._temperature = temperature
        self._system_prompt = system_prompt

    def run(self, request: AgentRequest) -> AgentResponse:
        messages = build_messages(self._system_prompt, self._history.all(), request.user_input)
        completion = self._provider.complete(
            CompletionRequest(model=self._model, messages=messages, temperature=self._temperature)
        )
        user_message = Message(role="user", content=request.user_input)
        self._history.add(user_message)
        self._history.add(completion.message)
        return AgentResponse(final_text=completion.message.content, messages=[user_message, completion.message])
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/agents/test_assistant.py tests/prompts/test_templates.py tests/session/test_history.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/aiagent/agents tests/agents
git commit -m "feat: add single assistant agent orchestration"
```

### Task 8: One-Shot CLI

**Files:**
- Modify: `src/aiagent/cli/main.py`
- Modify: `src/aiagent/__main__.py`
- Test: `tests/cli/test_main.py`

- [ ] **Step 1: Write the failing tests for one-shot command execution**

```python
from aiagent.cli.main import main


def test_main_prints_one_shot_response(capsys):
    exit_code = main(["hello"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Mock echo: hello" in captured.out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/cli/test_main.py::test_main_prints_one_shot_response -v`
Expected: FAIL because `main()` is not implemented

- [ ] **Step 3: Write minimal CLI dispatcher**

```python
import argparse

from aiagent.agents.assistant import AssistantAgent
from aiagent.config.settings import Settings
from aiagent.domain.models import AgentRequest
from aiagent.providers.factory import create_provider
from aiagent.session.history import SessionHistory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aiagent")
    parser.add_argument("prompt", nargs="?")
    parser.add_argument("--repl", action="store_true")
    args = parser.parse_args(argv)

    if args.repl:
        from aiagent.cli.repl import run_repl

        return run_repl()

    if not args.prompt:
        parser.error("prompt is required unless --repl is used")

    settings = Settings.from_env()
    provider = create_provider(settings)
    agent = AssistantAgent(
        provider=provider,
        history=SessionHistory(),
        model=settings.model,
        temperature=settings.temperature,
    )
    response = agent.run(AgentRequest(user_input=args.prompt))
    print(response.final_text)
    return 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/cli/test_main.py::test_main_prints_one_shot_response -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/aiagent/cli src/aiagent/__main__.py tests/cli/test_main.py
git commit -m "feat: add one-shot cli entrypoint"
```

### Task 9: REPL CLI and Documentation

**Files:**
- Create: `src/aiagent/cli/repl.py`
- Modify: `src/aiagent/cli/main.py`
- Modify: `README.md`
- Test: `tests/cli/test_main.py`

- [ ] **Step 1: Write the failing tests for REPL mode**

```python
from aiagent.cli.repl import run_repl


def test_repl_exits_on_quit(monkeypatch, capsys):
    inputs = iter(["hello", "quit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    exit_code = run_repl()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Mock echo: hello" in output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/cli/test_main.py::test_repl_exits_on_quit -v`
Expected: FAIL because `run_repl()` is not implemented

- [ ] **Step 3: Write minimal REPL loop and update README**

```python
from aiagent.agents.assistant import AssistantAgent
from aiagent.config.settings import Settings
from aiagent.domain.models import AgentRequest
from aiagent.providers.factory import create_provider
from aiagent.session.history import SessionHistory


def run_repl() -> int:
    settings = Settings.from_env()
    provider = create_provider(settings)
    agent = AssistantAgent(
        provider=provider,
        history=SessionHistory(),
        model=settings.model,
        temperature=settings.temperature,
    )

    while True:
        user_input = input("aiagent> ").strip()
        if user_input.lower() in {"quit", "exit"}:
            return 0
        if not user_input:
            continue
        response = agent.run(AgentRequest(user_input=user_input))
        print(response.final_text)
```

```md
## Usage

python -m aiagent "hello"
python -m aiagent --repl

## Configuration

- `AIAGENT_PROVIDER=mock|moonshot`
- `AIAGENT_API_KEY=...`
- `AIAGENT_API_BASE=https://api.moonshot.cn/v1`
- `AIAGENT_MODEL=moonshot-v1-8k`
```

- [ ] **Step 4: Run the full test suite to verify it passes**

Run: `python -m pytest -v`
Expected: PASS for all tests

- [ ] **Step 5: Run a manual smoke check**

Run: `python -m aiagent "hello"`
Expected: prints `Mock echo: hello`

- [ ] **Step 6: Commit**

```bash
git add src/aiagent/cli README.md tests/cli/test_main.py
git commit -m "feat: add repl cli and usage docs"
```

## Final Verification Checklist

- [ ] Run `python -m pytest -v`
- [ ] Run `python -m aiagent "hello"`
- [ ] Run `python -m aiagent --repl`
- [ ] Confirm default provider is mock without any env vars
- [ ] Confirm `Settings.from_env({"AIAGENT_PROVIDER": "moonshot"})` raises a configuration error
- [ ] Confirm Moonshot provider tests use mocked HTTP only

## Notes for the Implementer

- Keep the CLI thin. If logic starts growing there, move it into `agents`, `providers`, or `session`.
- Do not add tool-calling, file actions, streaming, or multi-agent orchestration in this plan.
- Keep `AgentRequest` and `AgentResponse` structured even though the first implementation is a single-agent flow.
- Use the mock provider in all CLI and agent tests unless the test is explicitly about Moonshot request shaping.
- Prefer standard library solutions unless a dependency clearly reduces complexity.
