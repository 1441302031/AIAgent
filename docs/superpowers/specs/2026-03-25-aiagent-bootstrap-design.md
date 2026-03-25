# AIAgent Bootstrap Design

## Overview

Build the first usable version of a Python-based agent framework with a reusable library core and a very thin CLI. The first milestone must run end-to-end without an API key by default, while already including a Moonshot-compatible provider adapter that can be enabled later through configuration only.

This phase intentionally focuses on the smallest meaningful vertical slice:

- library-first architecture
- single-agent completion flow
- default mock provider
- Moonshot-compatible provider scaffold
- one-shot CLI command
- interactive REPL CLI

The design must leave clear extension points for later `subagent` and `multi-agent` orchestration, but those orchestration behaviors are not part of the first implementation slice.

## Goals

- Provide a clean Python project structure for future agent work.
- Make the default experience runnable with no API key.
- Support both one-shot CLI usage and a REPL using the same session model.
- Separate provider, prompt, session, domain, agent, and CLI concerns.
- Allow future switch from `mock` to `moonshot` by configuration rather than code changes.
- Keep the first implementation small enough to plan and test rigorously.

## Non-Goals

- Real tool calling or tool execution.
- File editing, shell execution, or Cursor-like tool actions.
- Multi-agent runtime coordination in this phase.
- Long-term memory, vector storage, or retrieval.
- Streaming output, cancellation, or advanced terminal UX.
- Full prompt library migration from external references in this phase.

## External References

- Moonshot documentation is used as the basis for a compatible provider shape, especially around chat completion style requests.
- The CL4R1T4S `CURSOR` reference is treated as prompt and behavior inspiration, not as architecture to copy directly.

## Target User Experience

The user can run a single prompt from the command line:

```bash
python -m aiagent "Hello"
```

And can also start an interactive chat session:

```bash
python -m aiagent --repl
```

With default settings, both modes use the mock provider and return deterministic, testable responses. Once Moonshot credentials are added later, the user can switch provider mode through configuration only.

## Architecture Summary

The first version uses a layered architecture:

1. `domain`: stable request/response models and shared errors
2. `config`: application settings and provider selection inputs
3. `prompts`: system prompt and prompt assembly helpers
4. `providers`: completion backends (`mock`, `moonshot`)
5. `session`: in-memory message history
6. `agents`: single assistant agent orchestration
7. `cli`: thin entrypoints for one-shot and REPL execution

The CLI must not contain business logic. The agent must not know about terminal behavior. Providers must only care about completion requests and responses.

## Proposed Project Structure

```text
aiagent/
  pyproject.toml
  README.md
  src/aiagent/
    __init__.py
    config/
      __init__.py
      settings.py
    domain/
      __init__.py
      models.py
      errors.py
    prompts/
      __init__.py
      system.py
      templates.py
    providers/
      __init__.py
      base.py
      mock.py
      moonshot.py
      factory.py
    session/
      __init__.py
      history.py
    agents/
      __init__.py
      base.py
      assistant.py
    cli/
      __init__.py
      main.py
      repl.py
  tests/
    config/
    providers/
    session/
    agents/
    cli/
```

## Module Responsibilities

### `domain`

Owns the most stable data contracts:

- `Message`
- `CompletionRequest`
- `CompletionResponse`
- `AgentRequest`
- `AgentResponse`

Also owns normalized exceptions:

- `ConfigurationError`
- `ProviderError`
- `AuthenticationError`
- `TransportError`
- `AgentError`

This layer is the contract boundary between the rest of the system.

### `config`

Loads and validates runtime configuration such as:

- provider name
- model name
- base URL
- API key
- temperature
- mock behavior mode

This ensures provider selection and environment setup stay outside the agent logic.

### `prompts`

Provides the initial system prompt and prompt assembly helpers. The first phase only needs:

- default assistant system prompt
- conversion of system prompt + session history + latest user input into provider-ready messages

This is where later Cursor-inspired prompt variants can be introduced.

### `providers`

Defines the provider abstraction and implementations:

- `base.py`: provider interface
- `mock.py`: deterministic mock backend
- `moonshot.py`: Moonshot-compatible chat completion adapter
- `factory.py`: select provider from settings

The provider interface should be structured and model-oriented, not raw string-in/string-out, so that later agent variants can share it safely.

### `session`

Maintains in-memory conversation history for both REPL and future agent workflows. It is intentionally separate from the CLI so that any future interface can reuse it.

### `agents`

Contains the single assistant agent used in phase one. The assistant agent:

- accepts structured agent input
- builds prompt messages
- calls the selected provider
- returns structured agent output

This boundary is where future subagents and multi-agent coordinators will plug in.

### `cli`

Contains argument handling, terminal IO, and the REPL loop only. It should delegate all useful work to the library core.

## Core Data Flow

### One-shot mode

1. CLI reads the user prompt.
2. Settings are loaded.
3. Provider factory creates the configured provider.
4. A session history object is created.
5. The assistant agent assembles:
   - system prompt
   - session history
   - current user message
6. The provider receives a `CompletionRequest`.
7. The provider returns a `CompletionResponse`.
8. The agent returns an `AgentResponse`.
9. CLI prints the final text and exits.

### REPL mode

1. CLI initializes settings, provider, agent, and one long-lived session.
2. Each user input is appended through the same agent flow.
3. Assistant replies are written back into session history.
4. The loop continues until the user exits.

Both modes reuse the same session model and assistant agent.

## Provider Strategy

### Default Mock Provider

The application default must be `mock`.

The first phase mock provider should support:

- `echo` mode: deterministic transformation based on user input
- `scripted` mode: return a configured canned response

This makes behavior easy to test and easy to demo before real credentials are available.

### Moonshot-Compatible Provider

The Moonshot adapter should be present in the first phase, but not required for normal development. It should:

- accept configuration for base URL, model, and API key
- construct chat-completion style HTTP requests
- map transport/authentication failures into normalized domain errors

If the configured provider is `moonshot` but required credentials are missing, the application should fail clearly rather than silently falling back to mock. Silent fallback would create false confidence.

## Prompt Strategy

The first phase prompt system should be intentionally small:

- one default assistant system prompt
- one message assembly path

It should still be structured so that later prompt families can be added without changing agent logic.

The CL4R1T4S `CURSOR` reference should inform future prompt tone and safety conventions, but the first phase should not block on reproducing that prompt set in full.

## Error Handling

Errors should be normalized before they reach the CLI:

- config validation issues become `ConfigurationError`
- auth issues become `AuthenticationError`
- transport and HTTP failures become `TransportError` or `ProviderError`
- malformed provider results or orchestration failures become `AgentError`

The CLI should convert normalized errors into concise user-facing messages and non-zero exits. The CLI should not inspect low-level HTTP exceptions directly.

## Extension Points for Future Subagents and Multi-Agent

The first phase will only implement a single assistant agent, but the data model should already support structured orchestration later.

`AgentRequest` should reserve fields such as:

- `task_id`
- `context`
- `metadata`

`AgentResponse` should reserve fields such as:

- `messages`
- `final_text`
- `artifacts`
- `handoffs`

With those contracts in place:

- a subagent can implement the same agent interface
- a future coordinator can compose multiple agents and merge responses without changing provider contracts

## Testing Strategy

The first phase should emphasize unit tests around boundaries that are stable and easy to reason about:

- settings loading and validation
- provider factory selection
- mock provider behavior
- Moonshot provider request construction and validation
- session history behavior
- assistant agent orchestration

CLI tests should stay light and prove:

- one-shot mode prints a response
- REPL mode loops and exits correctly

Moonshot tests should not depend on a live API key. They should use HTTP mocking or request-construction assertions only.

## TDD Expectations

Implementation should proceed bottom-up with small red-green-refactor steps:

1. domain models and errors
2. settings
3. provider factory
4. mock provider
5. Moonshot provider validation/request shaping
6. session history
7. assistant agent
8. one-shot CLI
9. REPL CLI

Each component should be introduced by a failing test before implementation.

## Phase-One Success Criteria

Phase one is complete when all of the following are true:

- the project can run locally without API credentials
- the default provider is mock
- one-shot CLI mode works
- REPL mode works
- assistant/session/provider boundaries are explicit and test-covered
- Moonshot-compatible provider is present and configurable
- switching to Moonshot later requires configuration changes, not library rewrites

## Risks and Mitigations

### Risk: Over-engineering the first phase

Mitigation: exclude tools, planning runtimes, streaming, and orchestration behavior from the first milestone.

### Risk: CLI leaks into core logic

Mitigation: keep `cli` as a terminal adapter only; route all real behavior through agent and provider interfaces.

### Risk: Future multi-agent support becomes awkward

Mitigation: use structured agent request/response types from the start, even for the single-agent implementation.

### Risk: Moonshot support becomes misleading without credentials

Mitigation: implement the adapter now, but fail explicitly if selected without required configuration.

## Implementation Readiness

This scope is intentionally narrow enough for a single implementation plan. It contains one vertical slice with clear extension points rather than multiple independent subsystems.
