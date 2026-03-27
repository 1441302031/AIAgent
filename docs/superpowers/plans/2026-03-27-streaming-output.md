# 流式输出与 Thinking 状态 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为当前 `aiagent` 项目增加统一的流式输出能力，使 one-shot 与 REPL 在模型尚未返回首个内容块前显示 `thinking + 时间`，在首个内容块到来后切换为正文流式输出，并在流式结束后保持完整 history 写入。

**Architecture:** 本轮实现从 provider 抽象层向上扩展流式接口，在 `domain -> providers -> agents -> cli` 这条链上逐层增加最小能力。CLI 的 `thinking + 时间` 是渲染层职责，provider 只负责产出统一流式事件，agent 负责累加完整文本并在结束后写入 history。

**Tech Stack:** Python 3.14、pytest、httpx、现有 aiagent provider/agent/cli 架构、stdout 渲染

---

## 风险前置

- 当前输出链路是一次性返回，一旦把流式能力塞进 CLI 而不改 provider / agent，会变成假流式并造成后续返工，因此必须按协议层推进。
- Windows 终端对同一行刷新行为可能和其他终端不一致，CLI renderer 必须保持简单，不引入复杂光标控制依赖。
- `docs/agent-guide.md` 当前已有较大 diff 历史，后续文档变更应尽量小。
- `DeepSeek` 和 `Moonshot` 的流式响应虽然都兼容类似 SSE 结构，但解析时不能盲目共用未验证逻辑。

## 文件结构图

- `docs/superpowers/specs/2026-03-27-streaming-output-design.md`
  - 本轮实施依据的设计 spec
- `src/aiagent/domain/models.py`
  - 新增最小流式事件模型
- `src/aiagent/providers/base.py`
  - 扩展 provider 协议，增加流式接口
- `src/aiagent/providers/mock.py`
  - 实现 mock 流式输出
- `src/aiagent/providers/deepseek.py`
  - 实现 DeepSeek 流式解析
- `src/aiagent/providers/moonshot.py`
  - 实现 Moonshot 流式解析
- `src/aiagent/agents/assistant.py`
  - 增加 `run_stream()`，负责转发事件并累加完整文本
- `src/aiagent/cli/streaming.py`
  - 新增 CLI thinking/计时/流式渲染器
- `src/aiagent/cli/main.py`
  - one-shot 接入流式渲染
- `src/aiagent/cli/repl.py`
  - REPL 接入流式渲染
- `tests/domain/test_models.py`
  - 增加流式事件模型测试
- `tests/providers/test_mock.py`
  - 增加 mock 流式测试
- `tests/providers/test_deepseek.py`
  - 增加 DeepSeek 流式测试
- `tests/providers/test_moonshot.py`
  - 增加 Moonshot 流式测试
- `tests/agents/test_assistant.py`
  - 增加 agent 流式测试
- `tests/cli/test_main.py`
  - 增加 one-shot / REPL 流式渲染测试
- `tests/cli/test_streaming.py`
  - 新增 CLI 渲染器测试

### Task 1: 增加最小流式事件模型与 provider 协议

**Files:**
- Modify: `src/aiagent/domain/models.py`
- Modify: `src/aiagent/providers/base.py`
- Test: `tests/domain/test_models.py`

- [ ] **Step 1: 编写流式事件模型失败测试**

```python
from aiagent.domain.models import CompletionEvent


def test_completion_event_defaults_to_empty_text():
    event = CompletionEvent(kind="done")
    assert event.kind == "done"
    assert event.text == ""
```

- [ ] **Step 2: 运行单测，确认红灯**

Run: `python -B -m pytest -p no:cacheprovider tests/domain/test_models.py::test_completion_event_defaults_to_empty_text -v`
Expected: FAIL，提示 `CompletionEvent` 不存在

- [ ] **Step 3: 在 `models.py` 中实现最小事件模型**

```python
@dataclass(slots=True)
class CompletionEvent:
    kind: str
    text: str = ""
```

- [ ] **Step 4: 扩展 `CompletionProvider` 协议**

```python
class CompletionProvider(Protocol):
    def complete(self, request: CompletionRequest) -> CompletionResponse: ...
    def stream_complete(self, request: CompletionRequest) -> Iterator[CompletionEvent]: ...
```

- [ ] **Step 5: 运行 domain 测试**

Run: `python -B -m pytest -p no:cacheprovider tests/domain/test_models.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add src/aiagent/domain/models.py src/aiagent/providers/base.py tests/domain/test_models.py
git commit -m "feat: add streaming completion event model"
```

### Task 2: 为 MockProvider 增加流式输出

**Files:**
- Modify: `src/aiagent/providers/mock.py`
- Test: `tests/providers/test_mock.py`

- [ ] **Step 1: 编写 mock 流式失败测试**

```python
from aiagent.domain.models import CompletionRequest, Message
from aiagent.providers.mock import MockProvider


def test_mock_provider_streams_scripted_response():
    provider = MockProvider(mode="scripted", scripted_response="hello")
    events = list(
        provider.stream_complete(
            CompletionRequest(model="mock-model", messages=[Message(role="user", content="hi")])
        )
    )
    assert [event.kind for event in events] == ["content", "done"]
    assert "".join(event.text for event in events if event.kind == "content") == "hello"
```

- [ ] **Step 2: 运行单测，确认红灯**

Run: `python -B -m pytest -p no:cacheprovider tests/providers/test_mock.py::test_mock_provider_streams_scripted_response -v`
Expected: FAIL，提示 `stream_complete` 不存在

- [ ] **Step 3: 实现最小 `stream_complete()`**

建议首版：
- `scripted` 模式直接按字符或单块输出
- `echo` 模式对最终文本做同样处理
- 最后补一个 `done` 事件

- [ ] **Step 4: 运行 mock provider 测试**

Run: `python -B -m pytest -p no:cacheprovider tests/providers/test_mock.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/aiagent/providers/mock.py tests/providers/test_mock.py
git commit -m "feat: add mock streaming provider support"
```

### Task 3: 为 AssistantAgent 增加流式执行路径

**Files:**
- Modify: `src/aiagent/agents/assistant.py`
- Test: `tests/agents/test_assistant.py`

- [ ] **Step 1: 编写 `run_stream()` 失败测试**

```python
def test_assistant_agent_streams_content_and_persists_history():
    ...
```

测试至少断言：
- agent 会转发 provider 的流式内容
- 流式结束后 history 包含 user / assistant 两条消息
- assistant 最终内容是所有 content 事件拼接结果

- [ ] **Step 2: 运行单测，确认红灯**

Run: `python -B -m pytest -p no:cacheprovider tests/agents/test_assistant.py::test_assistant_agent_streams_content_and_persists_history -v`
Expected: FAIL，提示 `run_stream` 不存在

- [ ] **Step 3: 实现最小 `run_stream()`**

执行逻辑：
- 生成 `CompletionRequest`
- 调 `provider.stream_complete(...)`
- 遇到 `content` 事件时累计文本并向上游 yield
- 流结束后写 history

- [ ] **Step 4: 运行 agent 测试**

Run: `python -B -m pytest -p no:cacheprovider tests/agents/test_assistant.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/aiagent/agents/assistant.py tests/agents/test_assistant.py
git commit -m "feat: add assistant streaming flow"
```

### Task 4: 新增 CLI 流式渲染器

**Files:**
- Create: `src/aiagent/cli/streaming.py`
- Create: `tests/cli/test_streaming.py`

- [ ] **Step 1: 编写 thinking 渲染失败测试**

测试至少覆盖：
- 首 token 前显示 `thinking`
- 收到首 token 后不再保留 `thinking`
- 结束时输出换行

- [ ] **Step 2: 运行单测，确认红灯**

Run: `python -B -m pytest -p no:cacheprovider tests/cli/test_streaming.py -v`
Expected: FAIL，提示模块或函数不存在

- [ ] **Step 3: 实现最小流式渲染器**

建议提供一个函数，例如：

```python
def render_stream(events: Iterable[CompletionEvent], writer: TextIO, time_fn: Callable[[], float]) -> str:
    ...
```

要求：
- 首 token 前输出 `thinking... <elapsed>s`
- 首 token 后清除 thinking 并继续流式打印正文
- 返回最终完整文本

- [ ] **Step 4: 运行 CLI renderer 测试**

Run: `python -B -m pytest -p no:cacheprovider tests/cli/test_streaming.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/aiagent/cli/streaming.py tests/cli/test_streaming.py
git commit -m "feat: add cli streaming renderer"
```

### Task 5: 接入 one-shot 与 REPL 流式输出

**Files:**
- Modify: `src/aiagent/cli/main.py`
- Modify: `src/aiagent/cli/repl.py`
- Modify: `tests/cli/test_main.py`

- [ ] **Step 1: 编写 one-shot 流式输出失败测试**

至少覆盖：
- `main(["hello"])` 输出包含最终文本
- 流式路径不再依赖一次性 `print(response.final_text)`

- [ ] **Step 2: 编写 REPL 流式输出失败测试**

至少覆盖：
- 用户输入后输出通过流式路径渲染
- `quit` / `exit` / `KeyboardInterrupt` 行为不回归

- [ ] **Step 3: 运行 CLI 测试，确认红灯**

Run: `python -B -m pytest -p no:cacheprovider tests/cli/test_main.py -v`
Expected: FAIL，提示旧输出假设不再满足

- [ ] **Step 4: 实现最小接入**

要求：
- one-shot 使用 `agent.run_stream()` + CLI renderer
- REPL 使用 `agent.run_stream()` + CLI renderer
- 保持退出行为不变

- [ ] **Step 5: 运行 CLI 测试**

Run: `python -B -m pytest -p no:cacheprovider tests/cli/test_main.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add src/aiagent/cli/main.py src/aiagent/cli/repl.py tests/cli/test_main.py
git commit -m "feat: enable streaming cli output"
```

### Task 6: 为 DeepSeekProvider 增加真实流式解析

**Files:**
- Modify: `src/aiagent/providers/deepseek.py`
- Modify: `tests/providers/test_deepseek.py`

- [ ] **Step 1: 编写 DeepSeek 流式失败测试**

测试至少覆盖：
- SSE 内容块解析
- `[DONE]` 正确结束
- 错误 chunk 或传输异常归一化

- [ ] **Step 2: 运行单测，确认红灯**

Run: `python -B -m pytest -p no:cacheprovider tests/providers/test_deepseek.py -v`
Expected: FAIL，提示 `stream_complete` 不存在或测试不通过

- [ ] **Step 3: 实现最小 `stream_complete()`**

要求：
- 发送 `stream: true`
- 解析 SSE `data:` 行
- 提取内容 delta
- 结束时产出 `done`

- [ ] **Step 4: 运行 DeepSeek provider 测试**

Run: `python -B -m pytest -p no:cacheprovider tests/providers/test_deepseek.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/aiagent/providers/deepseek.py tests/providers/test_deepseek.py
git commit -m "feat: add deepseek streaming provider"
```

### Task 7: 为 MoonshotProvider 增加真实流式解析

**Files:**
- Modify: `src/aiagent/providers/moonshot.py`
- Modify: `tests/providers/test_moonshot.py`

- [ ] **Step 1: 编写 Moonshot 流式失败测试**

覆盖点与 DeepSeek 类似：
- SSE 内容块解析
- `[DONE]` 结束
- 错误归一化

- [ ] **Step 2: 运行单测，确认红灯**

Run: `python -B -m pytest -p no:cacheprovider tests/providers/test_moonshot.py -v`
Expected: FAIL

- [ ] **Step 3: 实现最小 `stream_complete()`**

要求与 DeepSeek 类似，但错误文案保留 Moonshot 语义。

- [ ] **Step 4: 运行 Moonshot provider 测试**

Run: `python -B -m pytest -p no:cacheprovider tests/providers/test_moonshot.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/aiagent/providers/moonshot.py tests/providers/test_moonshot.py
git commit -m "feat: add moonshot streaming provider"
```

### Task 8: 最终回归与真实 DeepSeek 流式 smoke test

**Files:**
- Read: `tools/run_with_env.py`
- Read: `.env.deepseek`

- [ ] **Step 1: 跑 CLI 流式专项测试**

Run: `python -B -m pytest -p no:cacheprovider tests/cli/test_streaming.py tests/cli/test_main.py -v`
Expected: PASS

- [ ] **Step 2: 跑 provider / agent / domain 回归**

Run: `python -B -m pytest -p no:cacheprovider tests/providers tests/agents tests/domain -v`
Expected: PASS

- [ ] **Step 3: 跑全量测试**

Run: `python -B -m pytest -p no:cacheprovider -v`
Expected: PASS

- [ ] **Step 4: 做真实 DeepSeek one-shot 流式 smoke**

Run: `python tools/run_with_env.py deepseek --prompt "请只回复 OK"`
Expected:
- 先看到 `thinking...`
- 再流式输出正文
- 最终返回 `OK`

- [ ] **Step 5: 做真实 DeepSeek REPL 流式 smoke**

Run: `'quit' | python tools/run_with_env.py deepseek --repl`
Expected:
- 进入 REPL
- 输入内容后出现 `thinking...`
- 能正常退出

- [ ] **Step 6: 提交**

```bash
git add .
git commit -m "test: verify streaming output workflow"
```

## 完成定义

满足以下条件才算本计划完成：

- one-shot 输出改为流式
- REPL 输出改为流式
- 首 token 前显示 `thinking + 时间`
- 首 token 到来后移除 `thinking`
- `mock`、`deepseek`、`moonshot` 都支持统一流式接口
- 流式完成后 history 正确写入
- CLI 退出与中断行为不回归
- 全量测试通过
- 至少一次真实 DeepSeek 流式调用成功

## 执行备注

- 真实 DeepSeek key 已在本地 `.env.deepseek` 中存在，但不应再额外写入文档或测试。
- 当前仓库仍有 `.merge-backups/`、`__pycache__/` 等无关未跟踪噪音，实施时不要顺手清理。
- 如果真实终端上的同一行刷新行为与测试表现有差异，应优先保持功能正确，再做小范围渲染兼容调整。
