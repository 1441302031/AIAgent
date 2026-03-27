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

Or run the env launcher directly from the checkout without installing:

```bash
python tools/run_with_env.py mock --prompt "hello"
python tools/run_with_env.py mock --repl
python tools/run_with_env.py --env .env.deepseek --prompt "hello"
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

## Env 启动器

如果你想从本地 `.env` 模板启动，而不是手动把配置写进当前 shell，请使用 `tools/run_with_env.py`。这个启动器负责读取模板文件、把环境变量注入子进程，然后再调用 `python -m aiagent`；主运行时本身不会自动加载 `.env`。

常用命令：

```bash
python tools/run_with_env.py deepseek --prompt "你好"
python tools/run_with_env.py deepseek --repl
python tools/run_with_env.py --env .env.deepseek --prompt "你好"
```

模板文件说明：

- `deepseek` 默认对应 `.env.deepseek`
- `moonshot` 默认对应 `.env.moonshot`
- `mock` 默认对应 `.env.mock`
- 也可以用 `--env` 显式指定任意本地文件；相对路径会按项目根目录解析，而不是按当前 `cwd`

模板文件只应该保留占位符和示例值，真实 key 不要直接写进模板文件。推荐把真实配置放到本地未跟踪的 env 文件里，例如复制一份模板后改成你自己的私有文件，并确保它不会被提交。

## Tests

Run the full test suite with:

```bash
python -B -m pytest -p no:cacheprovider -v
```

## Configuration

通过环境变量配置运行时行为：

- 通用变量：
  - `AIAGENT_PROVIDER`
  - `AIAGENT_MODEL`
  - `AIAGENT_TEMPERATURE`
- Mock provider：
  - `AIAGENT_MOCK_MODE`
  - `AIAGENT_MOCK_RESPONSE`
- Moonshot provider：
  - `AIAGENT_API_KEY`
  - `AIAGENT_API_BASE`
- DeepSeek provider：
  - `AIAGENT_DEEPSEEK_API_KEY`
  - `AIAGENT_DEEPSEEK_API_BASE`

其中 `AIAGENT_PROVIDER` 默认是 `mock`。当前 `moonshot` 与 `deepseek` 都使用各自专属的 API 配置，不会静默共用同一组 key。

### DeepSeek 配置示例

```bash
AIAGENT_PROVIDER=deepseek
AIAGENT_MODEL=deepseek-chat
AIAGENT_DEEPSEEK_API_KEY=your-key
AIAGENT_DEEPSEEK_API_BASE=https://api.deepseek.com
python -m aiagent "hello"
```

如果你不想安装项目，也可以直接从源码目录运行：

```bash
PYTHONPATH=src AIAGENT_PROVIDER=deepseek AIAGENT_MODEL=deepseek-chat AIAGENT_DEEPSEEK_API_KEY=your-key AIAGENT_DEEPSEEK_API_BASE=https://api.deepseek.com python -m aiagent "hello"
```

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
