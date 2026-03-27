# Agent Guide

## Overview

`aiagent` currently provides a single-agent baseline built around a reusable Python library core plus a thin CLI shell. The default runtime uses a deterministic mock provider so the full request -> prompt assembly -> provider -> response flow works without any API key.

This guide serves two audiences:

- Users who want to run the current agent from the command line
- Developers who want to evolve the project toward `subagent` and `multi-agent` behavior

## Current Scope

The current implementation includes:

- One-shot CLI execution
- Interactive REPL mode
- A structured `AssistantAgent`
- In-memory session history
- A mock provider for local development
- A Moonshot-compatible provider adapter for later activation
- A DeepSeek provider adapter for real chat-completion calls

The current implementation does not yet include:

- Tool calling
- Planner / executor loops
- File editing tools
- Long-term memory
- Real subagent orchestration
- Multi-agent routing and aggregation

## Quick Start

Install in editable mode:

```bash
python -m pip install -e .
```

The install command must include the trailing `.`. `python -m pip install -e` is incomplete and will not install this checkout.

Run a single prompt:

```bash
python -m aiagent "Summarize this requirement"
```

Start the interactive REPL:

```bash
python -m aiagent --repl
```

Exit the REPL with:

- `quit`
- `exit`
- `Ctrl+C`
- `Ctrl+D`

Run directly from source without installing:

```bash
PYTHONPATH=src python -m aiagent "hello"
PYTHONPATH=src python -m aiagent --repl
```

## Configuration

Configuration is loaded from environment variables in `Settings`.

Required and commonly used variables:

```bash
AIAGENT_PROVIDER=mock
AIAGENT_MODEL=mock-model
AIAGENT_TEMPERATURE=0
AIAGENT_MOCK_MODE=echo
AIAGENT_MOCK_RESPONSE=Mock response
AIAGENT_API_KEY=
AIAGENT_API_BASE=https://api.moonshot.cn/v1
```

### Mock Mode

Default behavior is `mock + echo`.

Example:

```bash
python -m aiagent "hello"
```

Typical output:

```text
Mock echo: hello
```

To force a deterministic scripted response:

```bash
AIAGENT_PROVIDER=mock
AIAGENT_MOCK_MODE=scripted
AIAGENT_MOCK_RESPONSE=This is a fixed reply
```

### Moonshot Mode

The Moonshot adapter is already implemented, but it is only activated when `AIAGENT_PROVIDER=moonshot`.

Example:

```bash
AIAGENT_PROVIDER=moonshot
AIAGENT_API_KEY=your-key
AIAGENT_API_BASE=https://api.moonshot.cn/v1
AIAGENT_MODEL=moonshot-v1-8k
python -m aiagent "hello"
```

If `moonshot` is selected without an API key, the runtime raises a configuration error immediately instead of silently falling back to `mock`.

### DeepSeek 模式

DeepSeek adapter 现在已经接入，启用时使用 DeepSeek 专属环境变量，而不是复用 Moonshot 的配置键。

示例：

```bash
AIAGENT_PROVIDER=deepseek
AIAGENT_MODEL=deepseek-chat
AIAGENT_DEEPSEEK_API_KEY=your-key
AIAGENT_DEEPSEEK_API_BASE=https://api.deepseek.com
python -m aiagent "hello"
```

如果选择了 `deepseek` 但没有提供 `AIAGENT_DEEPSEEK_API_KEY`，运行时会立即抛出配置错误，不会静默回退到 `mock`。

当前 DeepSeek 接入范围：

- 通过 `Settings` 读取专属环境变量
- 通过 `ProviderRegistry + StaticSelectionPolicy + factory` 完成装配
- 通过 `DeepSeekProvider` 调用 `/chat/completions`
- 支持 one-shot CLI 与 REPL 复用同一套 provider 装配逻辑

## Provider 装配与选择

当前 provider 运行链路已经从早期的硬编码分支，演进为 `registry + static selection` 的装配方式，但仍然是静态选择，不是动态调度。

相关概念如下：

- `ProviderConfig`
- `provider_configs`
- `StaticSelectionPolicy`
- `ProviderRegistry`

### `ProviderConfig` 与 `provider_configs`

`Settings.from_env()` 会先读取环境变量，再在 `Settings` 上下文中组装出 `provider_configs`。

`provider_configs` 是 `Settings.provider_configs` 的动态计算结果，会基于当前 `Settings` 字段构造每个 provider 的配置对象：

- `mock` 由当前 `Settings` 上下文派生为 `MockProviderConfig`
- `moonshot` 由当前 `Settings` 上下文派生为 `MoonshotProviderConfig`

这一步只负责把配置整理好，不负责决定最终运行哪个 provider。

### `StaticSelectionPolicy`

`StaticSelectionPolicy` 只负责静态选择 provider 名称。

- 如果用户显式配置了 `AIAGENT_PROVIDER`，就使用该值
- 如果没有配置，则默认返回 `mock`

它不是动态路由器，也不做运行时切换、fallback、健康检查或 failover。

### `ProviderRegistry`

`ProviderRegistry` 负责把 provider 名称映射到具体构造器，再用对应配置实例化 provider。

当前注册的 provider 仍然只有：

- `mock`
- `moonshot`

如果名称未注册，registry 会抛出配置错误。

## Current Runtime Flow

当前运行链路可以理解为：

1. CLI parses arguments
2. `Settings` loads runtime configuration
3. `Settings.provider_configs` 基于当前字段派生配置
4. `StaticSelectionPolicy` 选择 provider 名称，默认是 `mock`
5. `ProviderRegistry` 按名称和配置创建 provider 实例
6. `SessionHistory` 提供内存中的会话状态
7. `AssistantAgent` 组装 prompt 并调用 provider
8. 最终文本被打印或返回

这条链路和早期“直接在工厂里硬编码分支”的方式相比，已经把 provider 选择和 provider 构造拆开了，但它仍然只是单次静态选择。

The key code paths are:

- `src/aiagent/cli/main.py`
- `src/aiagent/cli/repl.py`
- `src/aiagent/config/settings.py`
- `src/aiagent/providers/factory.py`
- `src/aiagent/providers/registry.py`
- `src/aiagent/selection/static.py`
- `src/aiagent/agents/assistant.py`
- `src/aiagent/session/history.py`

## Core Architecture

### Domain Layer

The domain layer defines the stable data contracts:

- `Message`
- `CompletionRequest`
- `CompletionResponse`
- `AgentRequest`
- `AgentResponse`

This is the right place to preserve long-lived interfaces while the runtime grows.

### Provider Layer

Providers only know how to transform a completion request into a completion response.

Current providers:

- `MockProvider`
- `MoonshotProvider`

This separation is important because later agent changes should not require rewriting transport code.

### Session Layer

`SessionHistory` stores the current conversation in memory and returns ordered messages. REPL mode keeps one history instance alive across turns; one-shot mode creates a fresh history for each request.

### Agent Layer

`AssistantAgent` is the current orchestration layer. It:

- converts `AgentRequest` into prompt messages
- adds the default system prompt
- calls the selected provider
- appends user and assistant messages into history
- returns `AgentResponse`

This is the layer that should grow into `subagent` and `multi-agent` behavior.

## Using the Agent from Python

The minimal library-first usage looks like this:

```python
from aiagent.agents.assistant import AssistantAgent
from aiagent.config.settings import Settings
from aiagent.domain.models import AgentRequest
from aiagent.providers.factory import create_provider
from aiagent.session.history import SessionHistory

settings = Settings.from_env()
provider = create_provider(settings)
history = SessionHistory()

agent = AssistantAgent(
    provider=provider,
    history=history,
    model=settings.model,
    temperature=settings.temperature,
)

response = agent.run(AgentRequest(user_input="Break this task into steps"))
print(response.final_text)
```

This pattern is the recommended entrypoint for future orchestration work because it keeps the CLI thin and the core reusable.

## Subagent Design Guide

### What a Subagent Should Mean in This Project

In this codebase, a subagent should not be a special provider. It should be another agent implementation that shares the same structured request / response contract as the main agent.

A good first definition is:

- Main agent receives a user task
- Main agent decides part of the task should be delegated
- Main agent calls a subagent with a narrowed `AgentRequest`
- Subagent returns a normal `AgentResponse`
- Main agent records the handoff and integrates the result

### Recommended Boundaries

Keep these boundaries:

- `providers/` remain transport adapters only
- `session/` remains history storage only
- `agents/` owns orchestration logic
- `domain/models.py` remains the shared contract surface

Avoid putting delegation logic into the CLI or provider layer.

### Recommended First Subagent Shape

Suggested additions:

- `src/aiagent/agents/subagent.py`
- `src/aiagent/agents/router.py`

Suggested responsibilities:

- `SubAgent`: a focused assistant with its own system prompt and optionally its own provider settings
- `TaskRouter`: decides whether a request stays local or is delegated

### Suggested Data Flow

1. Main agent receives `AgentRequest`
2. Router classifies the task
3. If delegation is needed, create a narrowed request
4. Call the chosen subagent
5. Convert the returned result into a handoff record
6. Return a merged `AgentResponse`

### Reusing Existing Domain Fields

You already have useful extension points in `AgentRequest` and `AgentResponse`:

- `AgentRequest.task_id`
- `AgentRequest.context`
- `AgentRequest.metadata`
- `AgentResponse.artifacts`
- `AgentResponse.handoffs`

Use these before adding new global abstractions.

### Minimal Handoff Pattern

A practical first handoff record can look like:

```python
{
    "agent": "research",
    "reason": "task_router",
    "input_summary": "Summarize the requirements",
    "result_summary": "Returned structured bullets",
}
```

This can live in `AgentResponse.handoffs` without forcing a larger schema too early.

## Multi-Agent Design Guide

### What Multi-Agent Should Mean Here

For this project, `multi-agent` should mean coordinated orchestration of several agents with distinct responsibilities, not several providers racing to answer the same prompt.

A good early model is:

- `CoordinatorAgent` receives the top-level request
- It decides which specialist agents to call
- Each specialist returns a normal `AgentResponse`
- The coordinator merges results into a final answer

### Recommended Specialist Roles

A practical first set of specialists is:

- `ResearchAgent`: extracts facts, summaries, requirements
- `PlannerAgent`: converts goals into steps
- `WriterAgent`: turns structured output into final user-facing text

Later, if tool calling is added:

- `ToolAgent`: owns tool execution and normalization
- `ReviewAgent`: validates or critiques another agent result

### Recommended Files

Suggested first additions:

- `src/aiagent/agents/coordinator.py`
- `src/aiagent/agents/subagent.py`
- `src/aiagent/agents/router.py`

Possible second-stage additions:

- `src/aiagent/agents/research.py`
- `src/aiagent/agents/planner.py`
- `src/aiagent/agents/writer.py`

### Coordinator Responsibilities

The coordinator should own:

- task decomposition
- subagent selection
- result aggregation
- failure handling
- final response formatting

The coordinator should not own:

- HTTP transport details
- CLI rendering
- low-level history storage

### Aggregation Strategy

Keep aggregation simple at first:

1. Call subagents sequentially
2. Store each result in memory
3. Produce one merged summary
4. Attach handoff metadata into the final `AgentResponse`

Do not begin with parallel execution, retries, or dynamic graphs unless the single-path version is already stable.

## Recommended Implementation Order

To grow from the current single-agent baseline toward Cursor-like orchestration, use this order:

1. Add `TaskRouter` for classification
2. Add one focused `SubAgent`
3. Record handoffs in `AgentResponse`
4. Add `CoordinatorAgent`
5. Support two specialist subagents
6. Add structured aggregation
7. Only then consider tool calling
8. Add multi-agent reviews or retries after the above is stable

This order minimizes rework because it preserves the existing `AgentRequest -> AgentResponse` contract.

## Testing Strategy for Subagent and Multi-Agent Work

Recommended test progression:

1. Unit-test the router classification rules
2. Unit-test each subagent with `MockProvider`
3. Unit-test coordinator aggregation using fake subagents
4. Add a small integration test for the full multi-agent flow
5. Keep Moonshot transport tests isolated and mocked

When possible, keep subagent tests deterministic by using scripted mock responses.

## Known Risks and Design Constraints

- `main.py` and `repl.py` still duplicate some bootstrap wiring
- current history is in-memory only
- no streaming support exists yet
- no cancellation, retry, or timeout policy exists above the provider layer
- no structured planner or tool protocol exists yet

These are normal constraints for a first baseline. The current architecture is good enough to support the next step, but the next step should be added incrementally rather than introducing a full agent runtime all at once.

## Recommended Next Step

If the next milestone is `subagent / multi-agent`, the most valuable immediate implementation target is:

1. add a `TaskRouter`
2. add one `SubAgent`
3. add a `CoordinatorAgent`
4. verify the whole flow with `MockProvider`

Once that works, Moonshot can be enabled by configuration instead of by redesign.

下一阶段如果要继续演进 provider 能力，应该是动态切换或更复杂的策略层；但那仍然属于后续阶段，不是当前实现。

## Troubleshooting

If `python -m aiagent` appears to do nothing or does not reflect this checkout, check which `aiagent` package Python is importing:

```bash
python -c "import aiagent; print(aiagent.__file__)"
```

If the path points to an older checkout or a stale worktree, reinstall from the current repository:

```bash
python -m pip uninstall -y aiagent
python -m pip install -e .
```

For a direct source-based fallback, bypass installation entirely:

```bash
PYTHONPATH=src python -m aiagent "hello"
PYTHONPATH=src python -m aiagent --repl
```
