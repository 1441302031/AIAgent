# aiagent

`aiagent` 是一个 `library-first + thin CLI` 的 Python agent 项目，当前支持：

- one-shot CLI
- REPL
- streaming 输出
- `mock / moonshot / deepseek` provider
- minimal multi-agent
- 本地文件上下文预处理

## 项目 SOP

本项目当前默认 SOP 为 **GSD**，旧流程不再作为项目默认流程。

- 当前 SOP 文档见 [`docs/gsd/project-sop.md`](./docs/gsd/project-sop.md)
- 仓库内不再新增旧流程目录文档

## 安装与运行

使用可编辑安装：

```bash
python -m pip install -e .
```

安装命令必须包含末尾的 `.`，也就是 `python -m pip install -e .`。

单次调用：

```bash
python -m aiagent "hello"
```

进入 REPL：

```bash
python -m aiagent --repl
```

多 agent 模式：

```bash
python -m aiagent --multi-agent "Please break this task into steps"
python -m aiagent --repl --multi-agent
```

显示当前选中 agent 路径的流式输出：

```bash
python -m aiagent --multi-agent --show-subagents "Please break this task into steps"
python -m aiagent --repl --multi-agent --show-subagents
```

退出 REPL：

- `quit`
- `exit`
- `Ctrl+C`
- `Ctrl+D`

## env 启动器

如果你不想手工设置一堆环境变量，可以直接使用启动器：

```bash
python tools/run_with_env.py mock --prompt "hello"
python tools/run_with_env.py mock --repl
python tools/run_with_env.py deepseek --prompt "hello"
python tools/run_with_env.py --env .env.deepseek --prompt "hello"
```

模板映射：

- `mock` -> `.env.mock`
- `deepseek` -> `.env.deepseek`
- `moonshot` -> `.env.moonshot`

真实密钥建议只保存在本地未跟踪的 env 文件中，不要提交进仓库。

## 文件上下文预处理

现在支持在发给模型前自动读取本地文件上下文。

支持两类输入：

1. 显式语法

```bash
python -m aiagent "请分析 @file(src/aiagent/agents/assistant.py)"
python -m aiagent "请概览 @dir(src/aiagent/agents)"
python -m aiagent "请比较 @glob(src/aiagent/providers/*.py)"
```

2. 轻量自然语言路径识别

```bash
python -m aiagent "请帮我分析 src/aiagent/agents/assistant.py 这个文件"
python -m aiagent "请分析 src/aiagent/providers 目录下的所有文件"
python -m aiagent "请比较 src/**/*.py 这些文件"
```

当前默认原则：

- 优先按项目根目录解析相对路径
- 支持绝对路径
- 只读取安全的文本文件
- 会忽略 `.git`、`__pycache__`、`node_modules`、`.venv`、`dist`、`build`
- 目录和 glob 读取会受到文件数、单文件大小、总注入大小限制

## 配置

通用环境变量：

- `AIAGENT_PROVIDER`
- `AIAGENT_MODEL`
- `AIAGENT_TEMPERATURE`

Mock provider：

- `AIAGENT_MOCK_MODE`
- `AIAGENT_MOCK_RESPONSE`

Moonshot provider：

- `AIAGENT_API_KEY`
- `AIAGENT_API_BASE`

DeepSeek provider：

- `AIAGENT_DEEPSEEK_API_KEY`
- `AIAGENT_DEEPSEEK_API_BASE`

DeepSeek 示例：

```bash
AIAGENT_PROVIDER=deepseek
AIAGENT_MODEL=deepseek-chat
AIAGENT_DEEPSEEK_API_KEY=your-key
AIAGENT_DEEPSEEK_API_BASE=https://api.deepseek.com
python -m aiagent "hello"
```

## 测试

运行全量测试：

```bash
python -B -m pytest -p no:cacheprovider -v
```

## 更多文档

- 完整使用与架构说明：[`docs/agent-guide.md`](./docs/agent-guide.md)
- 项目 SOP：[`docs/gsd/project-sop.md`](./docs/gsd/project-sop.md)

## 排错

如果 `python -m aiagent` 没有反映当前仓库代码，先检查 Python 实际导入的是哪个包：

```bash
python -c "import aiagent; print(aiagent.__file__)"
```

如果路径指向旧目录或旧 worktree，重新安装：

```bash
python -m pip uninstall -y aiagent
python -m pip install -e .
```
