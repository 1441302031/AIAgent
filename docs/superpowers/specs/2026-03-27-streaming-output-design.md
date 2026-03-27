# 流式输出与 Thinking 状态设计

## 概述

当前项目的输出路径仍然是“provider 返回完整结果，agent 组装完整文本，CLI 一次性打印”。这使得 one-shot 和 REPL 在真实模型调用时都存在明显等待空窗，尤其是在 DeepSeek 这类已支持流式输出的 provider 上，交互体验不够自然。

本设计的目标是在保持现有 `agent -> provider -> cli` 责任边界清晰的前提下，引入统一的流式输出能力，并在模型尚未返回首个内容块时显示 `thinking + 计时` 状态。一旦收到首个内容块，CLI 应立即移除 `thinking` 提示，转而直接流式打印模型输出。

## 用户确认的设计决策

本轮已确认的边界如下：

- 首版目标覆盖所有现有 provider：`mock`、`deepseek`、`moonshot`
- 输出行为统一由 provider 抽象层支持流式，而不是只在 CLI 做假动画
- `thinking + 时间` 属于 CLI 渲染行为
- 流式输出完成后，agent 仍需保留完整文本并写入 history

## 目标

### 1. 为 provider 增加统一流式接口

现有 `CompletionProvider` 只有同步 `complete()`。本轮将扩展 provider 协议，使当前所有 provider 都支持流式接口：

- `MockProvider`
- `DeepSeekProvider`
- `MoonshotProvider`

### 2. 为 agent 增加流式执行路径

`AssistantAgent` 除了现有 `run()` 外，新增 `run_stream()`。该接口负责：

- 构造 `CompletionRequest`
- 消费 provider 的流式事件
- 累加完整 assistant 文本
- 在流式结束后将完整消息写入 history

### 3. 为 CLI 增加 thinking + 计时渲染

在 one-shot 与 REPL 两种模式下：

- 请求发出后立即显示 `thinking... <elapsed>` 状态
- 首个内容块到来后移除 thinking
- 后续直接流式打印模型正文
- 输出结束后补换行

### 4. 保持现有退出与中断行为

REPL 的 `quit` / `exit` / `Ctrl+C` / `Ctrl+D` 行为不应回归。

## 非目标

本轮明确不做以下事情：

- 不引入 tool calling
- 不引入 planner / executor
- 不实现并行 token 渲染
- 不实现复杂终端动画或光标控制库
- 不实现多 provider 竞速输出
- 不实现自动重试或 failover
- 不在本轮重构成统一 OpenAI-compatible streaming 基类

## 核心边界

### Provider 层

provider 负责：

- 调用模型接口
- 将底层流式数据解析为统一事件

provider 不负责：

- `thinking` 文案
- 计时显示
- history 写入

### Agent 层

agent 负责：

- 组装 prompt
- 转发流式事件
- 累加完整文本
- 流式结束后写入 history

agent 不负责：

- 终端渲染
- 计时刷新

### CLI 层

CLI 负责：

- 在等待首 token 时显示 `thinking + 时间`
- 首 token 到来后切换到正文打印
- 处理换行和终端显示细节

CLI 不负责：

- 解析 SSE
- 拼装 assistant 最终消息

## 文件结构建议

```text
src/aiagent/
  domain/
    models.py
  providers/
    base.py
    mock.py
    deepseek.py
    moonshot.py
  agents/
    assistant.py
  cli/
    main.py
    repl.py
    streaming.py
tests/
  domain/
  providers/
  agents/
  cli/
```

## 流式事件模型

建议在 `domain/models.py` 中新增一个最小流式事件对象：

```python
@dataclass(slots=True)
class CompletionEvent:
    kind: str  # "content" | "done"
    text: str = ""
```

本轮不做更复杂的状态枚举或事件总线。

## Provider 协议设计

建议把 provider 协议扩展为：

```python
class CompletionProvider(Protocol):
    def complete(self, request: CompletionRequest) -> CompletionResponse: ...
    def stream_complete(self, request: CompletionRequest) -> Iterator[CompletionEvent]: ...
```

### MockProvider

首版不要求真的异步输出，只需按字符或按词分块 yield。

### DeepSeekProvider

DeepSeek 官方文档支持 `stream: true` 的聊天补全 SSE 流。  
来源：[DeepSeek 对话补全接口](https://api-docs.deepseek.com/zh-cn/api/create-chat-completion/)

### MoonshotProvider

Moonshot 官方示例提供了兼容 OpenAI 风格的流式输出用法。  
来源：[Moonshot/Kimi Thinking 示例](https://platform.moonshot.cn/blog/posts/kimi-thinking)

## Agent 流式数据流

建议新增：

```python
def run_stream(self, request: AgentRequest) -> Iterator[CompletionEvent]:
    ...
```

执行流程：

1. 构造 `CompletionRequest`
2. 调用 `provider.stream_complete(...)`
3. 每收到一个 `content` 事件就向上游转发
4. 同时累加完整文本
5. 流式结束后构造完整 assistant message
6. 把 user / assistant message 写入 history

这样可以保证：

- CLI 有实时内容可渲染
- history 仍保持完整

## CLI 交互设计

### One-shot

执行：

```bash
python tools/run_with_env.py deepseek --prompt "你好"
```

建议行为：

1. 立即显示：

```text
thinking... 0.1s
```

2. 如果首 token 未到，持续刷新计时
3. 首 token 到来时，清掉 `thinking`
4. 继续流式打印正文
5. 结束后输出换行

### REPL

用户输入后：

- 先显示 `thinking`
- 再切换为正文流式输出
- 结束后回到 `aiagent>` 提示符

## 错误处理

### 首 token 前失败

- 停止 `thinking`
- 输出错误信息

### 流式中途失败

- 保留已输出正文
- 换行后输出错误信息

### KeyboardInterrupt

首版保持现有中断语义，不额外引入取消协议。

## 测试策略

### 1. provider 流式测试

至少覆盖：

- `mock` 按块返回内容
- `deepseek` 解析 SSE 内容块
- `moonshot` 解析 SSE 内容块
- `[DONE]` 正确结束
- 流式异常正确归一化

### 2. agent 流式测试

至少覆盖：

- `run_stream()` 会传出 token
- 流式结束后会写入完整 assistant message
- history 顺序不回归

### 3. CLI 流式测试

至少覆盖：

- one-shot 会先显示 `thinking`
- 收到首 token 后不再保留 `thinking`
- REPL 会流式输出正文
- 退出与中断行为不回归

## 风险与约束

### 1. Windows 终端渲染差异

同一行刷新在不同终端上的表现可能不完全一致，因此首版应使用尽量简单的 stdout 刷新策略，不引入复杂终端依赖。

### 2. Moonshot / DeepSeek 流式响应细节

虽然官方文档支持流式，但不同厂商 chunk 结构可能存在细微差异。实现时应以官方响应结构为准，而不是盲目复用同一段解析逻辑。

### 3. 文档噪音

当前 `docs/agent-guide.md` 已有较大 diff 历史，实施时文档改动应尽量克制，避免再次引入低价值格式漂移。

## 成功标准

本设计落地后，满足以下条件即可视为完成：

1. one-shot 输出为流式
2. REPL 输出为流式
3. 首 token 前显示 `thinking + 时间`
4. 首 token 到来后移除 `thinking`
5. `mock`、`deepseek`、`moonshot` 都支持统一流式接口
6. 流式完成后 history 正确写入
7. CLI 退出与中断行为不回归
8. 全量测试通过
9. 至少一次真实 DeepSeek 流式调用成功

## 实施建议

推荐后续实施顺序：

1. 先给 `domain/models.py` 增加流式事件模型测试
2. 再扩展 provider 协议
3. 先实现 `MockProvider.stream_complete()`
4. 再给 `AssistantAgent` 增加 `run_stream()`
5. 再实现 CLI streaming renderer
6. 再接 `main.py` 和 `repl.py`
7. 最后实现 `DeepSeekProvider.stream_complete()` 与 `MoonshotProvider.stream_complete()`
8. 跑全量回归并做真实 DeepSeek 流式 smoke test

这个顺序能先用最便宜的 `mock` 打通整条链路，再接真实 provider，定位问题也会更清晰。
