# Repository Guidelines

## Project SOP

This repository now uses **GSD** as the default project SOP.

- Do not require or reference legacy workflow systems in normal project work.
- Do not instruct future contributors to follow the previous repository-level workflow process as the default.
- If an older workflow document conflicts with the current project behavior, prefer the current codebase, this file, and the GSD project SOP document.
- The active project SOP lives in [`docs/gsd/project-sop.md`](./docs/gsd/project-sop.md).

## Project Structure & Module Organization

This project uses a `src` layout. Runtime code lives in [`src/aiagent`](./src/aiagent), with subpackages for `agents`, `cli`, `config`, `domain`, `providers`, `selection`, `session`, `prompts`, and `preprocess`. Tests live under [`tests/`](./tests) and mirror the package structure. Repository-level documentation and design notes live under [`docs/`](./docs).

## Build, Test, and Development Commands

- `python -m pip install -e .` installs the package in editable mode for local development.
- `python -m aiagent "hello"` runs a one-shot prompt through the CLI.
- `python -m aiagent --repl` starts the interactive REPL.
- `python -m aiagent --multi-agent "help me break this task into steps"` runs the minimal multi-agent mode.
- `python tools/run_with_env.py mock --prompt "hello"` runs the app with a local env template without manual export steps.
- `python -B -m pytest -p no:cacheprovider -v` runs the full test suite.

## Coding Style & Naming Conventions

Use Python 3.11+ with standard 4-space indentation and `from __future__ import annotations` where the surrounding module already uses it. Follow existing naming patterns: `snake_case` for functions, methods, modules, and test files; `PascalCase` for classes; `test_*.py` for tests. Keep code explicit and small; this codebase does not currently define a formatter or linter config, so match the local style in nearby files.

## Testing Guidelines

Use `pytest` for all tests. Place tests alongside the area they cover, such as `tests/config/test_settings.py` or `tests/providers/test_factory.py`. Prefer descriptive test names that state the behavior under test. When adding CLI, agent, preprocessing, or provider behavior, include regression coverage for success and failure cases.

## Commit & Pull Request Guidelines

Git history favors short conventional commits such as `feat:`, `fix:`, `docs:`, and `test:`. Keep subject lines imperative and specific. Pull requests should summarize the change, list the commands used to verify it, and call out any config or behavior changes.

## Security & Configuration Tips

Do not commit real API keys or private `.env` files. The launcher expects env templates such as `.env.mock` or `.env.deepseek`; keep sensitive values in untracked local files. When debugging imports, verify the active checkout with `python -c "import aiagent; print(aiagent.__file__)"`.
