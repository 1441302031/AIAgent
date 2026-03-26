# aiagent

`aiagent` is a minimal, library-first Python agent project with a thin command-line interface for one-shot prompts and an interactive REPL.

## Install and run

This repository uses a `src` layout. For a fresh checkout, use one of these supported approaches:

Install the project in editable mode, then run the module:

```bash
python -m pip install -e .
python -m aiagent "hello"
python -m aiagent --repl
```

Note: the install command must include the trailing `.`. `python -m pip install -e` is incomplete and will not install this checkout.

Or run directly from the checkout by setting `PYTHONPATH=src`:

```bash
PYTHONPATH=src python -m aiagent "hello"
PYTHONPATH=src python -m aiagent --repl
```

## Usage

After `python -m pip install -e .`, run a single prompt:

```bash
python -m aiagent "hello"
```

After `python -m pip install -e .`, start the interactive REPL:

```bash
python -m aiagent --repl
```

Exit the REPL with `quit`, `exit`, `Ctrl+C`, or `Ctrl+D` / EOF.

## Tests

Run the full test suite with:

```bash
python -B -m pytest -p no:cacheprovider -v
```

## Configuration

Set configuration through environment variables:

- `AIAGENT_PROVIDER`
- `AIAGENT_API_KEY`
- `AIAGENT_API_BASE`
- `AIAGENT_MODEL`

Optional variables used by the mock and runtime configuration include `AIAGENT_TEMPERATURE`, `AIAGENT_MOCK_MODE`, and `AIAGENT_MOCK_RESPONSE`.

## Provider 架构

当前的 provider 创建流程已经不再是单纯的硬编码分支，而是改成了 `registry + static selection` 的装配方式：

1. `Settings` 先把环境变量整理成运行时配置
2. `Settings.provider_configs` 会基于当前 `Settings` 字段动态构造各 provider 对应的配置，每次访问都会重新计算
3. `StaticSelectionPolicy` 只负责静态选择目标 provider
4. `ProviderRegistry` 根据 provider 名称和配置实例化具体 provider

默认 provider 仍然是 `mock`。当前这套流程只做静态选择，不包含动态切换、failover 或健康检查。

## More Documentation

For a fuller usage and architecture guide, including `subagent` / `multi-agent` expansion guidance, see `docs/agent-guide.md`.

## Troubleshooting

If `python -m aiagent` does not reflect the current checkout, verify which package Python is importing:

```bash
python -c "import aiagent; print(aiagent.__file__)"
```

If the printed path points at an older checkout or worktree, reinstall from the current repository:

```bash
python -m pip uninstall -y aiagent
python -m pip install -e .
```

Then verify again:

```bash
python -c "import aiagent; print(aiagent.__file__)"
```
