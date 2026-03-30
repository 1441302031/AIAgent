# DeepSeek Provider 接入规范

## 目标

在当前 `aiagent` 的 provider 架构上新增 `DeepSeekProvider`，通过独立 provider 实现接入 DeepSeek 聊天补全 API，同时保持 `AssistantAgent`、CLI、session 与现有 provider 边界不变。

本次接入采用 `方案 B`：

- 使用 DeepSeek 专属环境变量承载认证与 base URL
- 不复用 `AIAGENT_API_KEY`
- 不在本轮引入通用 OpenAI-compatible provider 抽象层

## 范围

本次实现仅覆盖以下边界：

- `src/aiagent/config/settings.py`
- `src/aiagent/config/provider_config.py`
- `src/aiagent/providers/deepseek.py`（新增）
- `src/aiagent/providers/factory.py`
- `src/aiagent/providers/__init__.py`
- `tests/config/test_settings.py`
- `tests/config/test_provider_config.py`
- `tests/providers/test_deepseek.py`（新增）
- `tests/providers/test_factory.py`
- 与本次接入相关的最小文档更新

## 非目标

本规范明确不包含以下内容：

- 不重构 `MoonshotProvider`
- 不抽取通用 `OpenAICompatibleProvider`
- 不实现流式输出
- 不实现 tool calling
- 不实现 reasoning 专属字段
- 不实现多 provider 动态切换
- 不实现 failover、retry、健康检查
- 不修改 `AssistantAgent`、`SessionHistory` 或 CLI 主流程
- 不引入 DeepSeek 之外的新 provider

## 配置方案

### 通用环境变量

继续复用现有通用字段：

- `AIAGENT_PROVIDER`
- `AIAGENT_MODEL`
- `AIAGENT_TEMPERATURE`

### DeepSeek 专属环境变量

本次新增以下字段：

- `AIAGENT_DEEPSEEK_API_KEY`
- `AIAGENT_DEEPSEEK_API_BASE`

当 `AIAGENT_PROVIDER=deepseek` 时：

- 必须读取 `AIAGENT_DEEPSEEK_API_KEY`
- 必须使用 `AIAGENT_DEEPSEEK_API_BASE` 或其默认值
- 不应复用 Moonshot 的专属环境变量

## 设计概览

### 1. DeepSeekProvider

新增 `DeepSeekProvider`，保持与现有 `CompletionProvider` 边界一致：

- 输入 `CompletionRequest`
- 输出 `CompletionResponse`

它的职责仅限于：

- 构造 HTTP 请求
- 发送认证头
- 解析成功响应
- 将错误归一化为当前领域异常

### 2. DeepSeekProviderConfig

在 `provider_config.py` 中新增：

- `DeepSeekProviderConfig`

首版字段仅包含：

- `api_key: str | None`
- `api_base: str`

`model` 继续走通用 `Settings.model`，避免首轮过度拆分。

### 3. Factory 接入

在 `factory.py` 中通过现有：

- `ProviderRegistry`
- `StaticSelectionPolicy`

注册 `deepseek` provider。

对外入口仍然保持：

- `create_provider(settings)`

### 4. Settings 接入

`Settings` 继续是环境变量入口，但要新增 DeepSeek 配置来源：

- 读取 `AIAGENT_DEEPSEEK_API_KEY`
- 读取 `AIAGENT_DEEPSEEK_API_BASE`
- 当 `provider=deepseek` 且缺少 key 时，抛出 `ConfigurationError`

## 请求/响应边界

首版 DeepSeekProvider 应遵循与现有聊天 provider 一致的请求结构：

- 请求体包含：
  - `model`
  - `messages`
  - `temperature`
- 认证头使用：
  - `Authorization: Bearer <api_key>`

成功响应应被转换为：

- `CompletionResponse.model`
- `CompletionResponse.message`
- `CompletionResponse.raw`

## 错误处理

DeepSeekProvider 应沿用当前 provider 层错误语义：

- 401 -> `AuthenticationError`
- 其他 4xx / 5xx -> `ProviderError`
- 网络层异常 -> `TransportError`
- 成功响应结构非法 -> `ProviderError`

不应向 agent 层泄露原始 HTTP 库异常。

## 测试要求

必须新增或更新以下测试：

### `tests/config/test_provider_config.py`

- 验证能组装 `DeepSeekProviderConfig`
- 验证其 `api_key` 与 `api_base` 来源正确

### `tests/config/test_settings.py`

- 验证 `provider=deepseek` 时读取 DeepSeek 专属环境变量
- 验证缺失 `AIAGENT_DEEPSEEK_API_KEY` 时抛配置错误

### `tests/providers/test_deepseek.py`

至少覆盖：

- 正确发送 `model/messages/temperature`
- 401 -> `AuthenticationError`
- 5xx -> `ProviderError`
- HTTP 失败 -> `TransportError`
- 非法成功响应 -> `ProviderError`

### `tests/providers/test_factory.py`

- 验证 `create_provider()` 能构造 `DeepSeekProvider`
- 验证走的是现有 registry / selection 装配路径

### 回归要求

实现完成后，以下测试必须继续通过：

- `tests/providers/`
- `tests/config/`
- `tests/agents/`
- `tests/cli/test_main.py`

## 实施顺序

推荐按以下顺序实施，并优先遵循 TDD：

1. 扩展 `test_provider_config.py`
2. 扩展 `provider_config.py`
3. 扩展 `test_settings.py`
4. 扩展 `settings.py`
5. 新增 `test_deepseek.py`
6. 实现 `deepseek.py`
7. 扩展 `test_factory.py`
8. 修改 `factory.py`
9. 运行相关回归测试
10. 更新文档

## 成功标准

只有同时满足以下条件，本规范对应的实现才算完成：

1. `AIAGENT_PROVIDER=deepseek` 时可构造 `DeepSeekProvider`
2. 缺失 `AIAGENT_DEEPSEEK_API_KEY` 时会明确报配置错误
3. `DeepSeekProvider` 能按当前 completion 协议工作
4. 错误处理与现有 provider 语义一致
5. `AssistantAgent`、CLI、session 主流程无需修改
6. 现有 provider 行为无回归
7. 相关新增测试与既有回归测试全部通过

## 验证

本规范文档完成时，需要满足以下验证条件：

1. 文件位于 `docs/specs/`
2. 文档明确写出目标、范围与非目标
3. 文档明确写出配置方案、模块边界、错误处理与测试要求
4. 文档明确采用 `方案 B`，即 DeepSeek 专属环境变量
5. 文档明确排除通用兼容层重构
6. 文档内容为中文

## 后续工作

如果本规范通过评审，下一步应按当前项目 GSD SOP 拆成可执行的小步骤。若后续还要接入更多 OpenAI-compatible provider，应另写下一阶段规范，评估是否抽取通用兼容层，而不是在本规范中顺手扩展范围。
