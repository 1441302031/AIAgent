# Env 启动器 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为项目新增一个独立的 Python 启动器和多份 `.env` 模板，使用户可以通过 provider 名称或 env 文件路径一键切换 `mock`、`deepseek`、`moonshot`，并显式启动 one-shot 或 REPL。

**Architecture:** 这轮实现保持现有 `Settings.from_env()` 和 `python -m aiagent` 主运行路径不变，只在运行时外围新增 `tools/run_with_env.py`。启动器负责解析 `.env`、构造子进程环境变量，并通过 `subprocess` 调用当前 Python 解释器执行 `-m aiagent`；`.env` 模板仅提供占位配置，不保存真实 key。

**Tech Stack:** Python 3.14、pytest、subprocess、pathlib、现有 aiagent CLI 与环境变量配置模型

---

## 风险前置

- 当前项目没有内建 `.env` 读取能力，这轮必须把能力限制在启动器内，不能顺手改 `Settings.from_env()`。
- `.env` 模板文件极易诱导写入真实 key；模板必须只放占位值，真实使用建议复制为未跟踪私有文件。
- 启动器如果直接拼 shell 字符串，会有平台差异和转义风险；实现时必须使用 `subprocess` 和参数列表。
- 这轮只做“本地一键切换”，不做动态 provider 选择，不做 failover，不做主 CLI 协议变更。

## 文件结构图

- `docs/superpowers/specs/2026-03-27-env-launcher-design.md`
  - 本轮实现依据的设计 spec
- `tools/run_with_env.py`
  - 新增启动器，负责 env 文件解析、provider 映射、参数校验、子进程启动
- `tests/tools/test_run_with_env.py`
  - 新增启动器测试，覆盖解析、映射、模式校验、命令构造
- `.env.example`
  - 完整参考模板
- `.env.mock`
  - mock 快速启动模板
- `.env.deepseek`
  - DeepSeek 快速启动模板
- `.env.moonshot`
  - Moonshot 快速启动模板
- `README.md`
  - 增补启动器和 `.env` 使用说明
- `docs/agent-guide.md`
  - 增补启动器与 provider 切换说明

### Task 1: 为启动器编写最小失败测试

**Files:**
- Create: `tests/tools/test_run_with_env.py`
- Read: `src/aiagent/config/settings.py`
- Read: `src/aiagent/cli/main.py`

- [ ] **Step 1: 编写 `.env` 解析测试**

```python
from pathlib import Path

from tools.run_with_env import parse_env_file


def test_parse_env_file_ignores_comments_and_blank_lines(tmp_path: Path):
    env_file = tmp_path / ".env.test"
    env_file.write_text(
        "# comment\n\nAIAGENT_PROVIDER=deepseek\nAIAGENT_MODEL=deepseek-chat\n",
        encoding="utf-8",
    )

    result = parse_env_file(env_file)

    assert result == {
        "AIAGENT_PROVIDER": "deepseek",
        "AIAGENT_MODEL": "deepseek-chat",
    }
```

- [ ] **Step 2: 编写 provider 到 env 文件映射测试**

```python
from pathlib import Path

from tools.run_with_env import resolve_env_file


def test_resolve_env_file_supports_builtin_provider_names():
    project_root = Path("J:/Codex_Project/AIAgent")

    assert resolve_env_file(project_root, provider_name="mock", explicit_env=None).name == ".env.mock"
    assert resolve_env_file(project_root, provider_name="deepseek", explicit_env=None).name == ".env.deepseek"
    assert resolve_env_file(project_root, provider_name="moonshot", explicit_env=None).name == ".env.moonshot"
```

- [ ] **Step 3: 编写模式冲突与缺失校验测试**

```python
import pytest

from tools.run_with_env import build_runtime_mode


def test_build_runtime_mode_rejects_missing_mode():
    with pytest.raises(ValueError, match="prompt or repl"):
        build_runtime_mode(prompt=None, repl=False)


def test_build_runtime_mode_rejects_conflicting_modes():
    with pytest.raises(ValueError, match="choose exactly one"):
        build_runtime_mode(prompt="hi", repl=True)
```

- [ ] **Step 4: 编写 one-shot 与 REPL 命令构造测试**

```python
from tools.run_with_env import build_aiagent_command


def test_build_aiagent_command_for_prompt():
    command = build_aiagent_command("C:/Python314/python.exe", prompt="hello", repl=False)
    assert command == ["C:/Python314/python.exe", "-m", "aiagent", "hello"]


def test_build_aiagent_command_for_repl():
    command = build_aiagent_command("C:/Python314/python.exe", prompt=None, repl=True)
    assert command == ["C:/Python314/python.exe", "-m", "aiagent", "--repl"]
```

- [ ] **Step 5: 运行测试，确认红灯**

Run: `python -B -m pytest -p no:cacheprovider tests/tools/test_run_with_env.py -v`
Expected: FAIL，提示 `tools.run_with_env` 不存在或目标函数未定义

- [ ] **Step 6: 提交测试骨架**

```bash
git add tests/tools/test_run_with_env.py
git commit -m "test: add env launcher test coverage"
```

### Task 2: 实现启动器核心逻辑

**Files:**
- Create: `tools/run_with_env.py`
- Test: `tests/tools/test_run_with_env.py`

- [ ] **Step 1: 实现 `.env` 解析函数**

```python
def parse_env_file(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Invalid .env line: {raw_line}")
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result
```

- [ ] **Step 2: 实现 provider 到模板文件的映射**

```python
BUILTIN_ENV_FILES = {
    "mock": ".env.mock",
    "deepseek": ".env.deepseek",
    "moonshot": ".env.moonshot",
}


def resolve_env_file(project_root: Path, provider_name: str | None, explicit_env: str | None) -> Path:
    if explicit_env:
        return project_root / explicit_env
    if provider_name not in BUILTIN_ENV_FILES:
        raise ValueError(f"Unsupported provider: {provider_name}")
    return project_root / BUILTIN_ENV_FILES[provider_name]
```

- [ ] **Step 3: 实现模式校验与命令构造**

```python
def build_runtime_mode(prompt: str | None, repl: bool) -> str:
    if bool(prompt) == bool(repl):
        raise ValueError("Must choose exactly one of --prompt or --repl.")
    return "repl" if repl else "prompt"


def build_aiagent_command(python_executable: str, prompt: str | None, repl: bool) -> list[str]:
    if repl:
        return [python_executable, "-m", "aiagent", "--repl"]
    return [python_executable, "-m", "aiagent", prompt or ""]
```

- [ ] **Step 4: 实现 CLI 主入口**

```python
def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list:
        print("mock")
        print("deepseek")
        print("moonshot")
        return 0

    project_root = Path(__file__).resolve().parent.parent
    env_file = resolve_env_file(project_root, args.provider, args.env)
    env_values = parse_env_file(env_file)
    command = build_aiagent_command(sys.executable, args.prompt, args.repl)
    child_env = os.environ.copy()
    child_env.update(env_values)
    return subprocess.run(command, env=child_env, cwd=project_root).returncode
```

- [ ] **Step 5: 运行启动器测试，确认转绿**

Run: `python -B -m pytest -p no:cacheprovider tests/tools/test_run_with_env.py -v`
Expected: PASS

- [ ] **Step 6: 提交启动器实现**

```bash
git add tools/run_with_env.py tests/tools/test_run_with_env.py
git commit -m "feat: add env launcher"
```

### Task 3: 增加 `.env` 模板文件

**Files:**
- Create: `.env.example`
- Create: `.env.mock`
- Create: `.env.deepseek`
- Create: `.env.moonshot`

- [ ] **Step 1: 创建 `.env.example`**

```dotenv
# Common
AIAGENT_PROVIDER=mock
AIAGENT_MODEL=mock-model
AIAGENT_TEMPERATURE=0

# Mock
AIAGENT_MOCK_MODE=echo
AIAGENT_MOCK_RESPONSE=Mock response

# Moonshot
AIAGENT_API_KEY=
AIAGENT_API_BASE=https://api.moonshot.cn/v1

# DeepSeek
AIAGENT_DEEPSEEK_API_KEY=
AIAGENT_DEEPSEEK_API_BASE=https://api.deepseek.com
```

- [ ] **Step 2: 创建 `.env.mock`**

```dotenv
AIAGENT_PROVIDER=mock
AIAGENT_MODEL=mock-model
AIAGENT_TEMPERATURE=0
AIAGENT_MOCK_MODE=echo
AIAGENT_MOCK_RESPONSE=Mock response
```

- [ ] **Step 3: 创建 `.env.deepseek`**

```dotenv
AIAGENT_PROVIDER=deepseek
AIAGENT_MODEL=deepseek-chat
AIAGENT_TEMPERATURE=0
AIAGENT_DEEPSEEK_API_KEY=
AIAGENT_DEEPSEEK_API_BASE=https://api.deepseek.com
```

- [ ] **Step 4: 创建 `.env.moonshot`**

```dotenv
AIAGENT_PROVIDER=moonshot
AIAGENT_MODEL=moonshot-v1-8k
AIAGENT_TEMPERATURE=0
AIAGENT_API_KEY=
AIAGENT_API_BASE=https://api.moonshot.cn/v1
```

- [ ] **Step 5: 做模板完整性检查**

Run: `Get-Content .env.example, .env.mock, .env.deepseek, .env.moonshot`
Expected: 文件存在，且不包含真实 key

- [ ] **Step 6: 提交模板文件**

```bash
git add .env.example .env.mock .env.deepseek .env.moonshot
git commit -m "chore: add env launcher templates"
```

### Task 4: 更新使用文档

**Files:**
- Modify: `README.md`
- Modify: `docs/agent-guide.md`

- [ ] **Step 1: 在 README 中补启动器用法**

补充内容应包含：

- `python tools/run_with_env.py deepseek --prompt "你好"`
- `python tools/run_with_env.py deepseek --repl`
- `python tools/run_with_env.py --env .env.deepseek --prompt "你好"`
- 模板文件说明
- 真实 key 不要直接写进模板文件

- [ ] **Step 2: 在 Agent Guide 中补切换说明**

补充内容应包含：

- provider 名称映射
- `--prompt` / `--repl` 的显式模式设计
- 推荐把真实配置保存到本地未跟踪 env 文件

- [ ] **Step 3: 做文档自检**

Verification:
- 文档示例命令与启动器参数一致
- 没有写入真实 key
- 没有暗示主运行时已内建 `.env` 支持

- [ ] **Step 4: 提交文档**

```bash
git add README.md docs/agent-guide.md
git commit -m "docs: add env launcher usage"
```

### Task 5: 做本地 smoke test 与最终回归

**Files:**
- Read: `tools/run_with_env.py`
- Read: `.env.mock`
- Read: `.env.deepseek`

- [ ] **Step 1: 跑 mock one-shot smoke**

Run: `python tools/run_with_env.py mock --prompt "hello"`
Expected: 正常输出 mock 回复

- [ ] **Step 2: 跑 mock REPL smoke**

Run: `'quit' | python tools/run_with_env.py mock --repl`
Expected: 能进入 REPL 并正常退出

- [ ] **Step 3: 跑启动器测试与现有全量测试**

Run: `python -B -m pytest -p no:cacheprovider tests/tools/test_run_with_env.py -v`
Expected: PASS

Run: `python -B -m pytest -p no:cacheprovider -v`
Expected: PASS

- [ ] **Step 4: 如需验证 DeepSeek 模板，只允许本地临时覆盖**

示例：

```powershell
$env:AIAGENT_DEEPSEEK_API_KEY='<local-only>'
python tools/run_with_env.py --env .env.deepseek --prompt "请只回复 OK"
```

Verification:
- 不将真实 key 写回 `.env.deepseek`
- 仅把真实 key 作为当前 shell 的临时环境变量

- [ ] **Step 5: 最终提交**

```bash
git add .
git commit -m "test: verify env launcher workflow"
```

## 完成定义

满足以下条件才算本计划完成：

- 新增 `tools/run_with_env.py`
- 新增 `.env.example`、`.env.mock`、`.env.deepseek`、`.env.moonshot`
- 可通过 provider 名称或 `--env` 文件路径启动
- 必须显式指定 `--prompt` 或 `--repl`
- 启动器测试通过
- 现有 `python -m aiagent` 运行方式不受影响
- 至少完成一次本地 smoke test
- 模板文件中没有真实 key

## 执行备注

- 当前会话已有真实 DeepSeek key 暴露在聊天历史中；实施时不能把它写进模板、测试、文档或 git 历史。
- 若后续想让主运行时也支持 `.env` 自动加载，应单独开新 spec，不在本计划内顺手实现。
- 当前仓库里有 `.merge-backups/`、`__pycache__/` 等无关未跟踪噪音，实施时不要顺手清理，避免扩大范围。
