# Provider Registry / Config / Selection 实现规范

## 目标

在当前 `aiagent` 工程上，以最小改动演进 provider 框架，使后续新增 API 接入时更容易扩展、切换与继续演进，同时不破坏现有 `AssistantAgent` 主流程。

本规范首轮只覆盖三件事：

- `ProviderRegistry`：把 provider 构造从硬编码分支演进为可注册结构
- `ProviderConfig`：把公共配置与 provider 专属配置分层
- `SelectionPolicy`：为手动切换和后续动态切换预留明确挂载点

## 范围

本次实现规范仅覆盖以下代码边界：

- `src/aiagent/config/settings.py`
- `src/aiagent/config/provider_config.py`（新增）
- `src/aiagent/providers/base.py`
- `src/aiagent/providers/registry.py`（新增）
- `src/aiagent/providers/factory.py`
- `src/aiagent/providers/mock.py`
- `src/aiagent/providers/moonshot.py`
- `src/aiagent/selection/base.py`（新增）
- `src/aiagent/selection/static.py`（新增）
- 与上述模块直接相关的测试文件

## 非目标

本规范明确不包含以下内容：

- 不实现新的 provider
- 不修改 `AssistantAgent` 的核心调用协议
- 不实现动态权重选择
- 不实现自动 failover / retry / circuit breaker
- 不实现 provider 健康检查
- 不实现 streaming、tool calling、subagent 或 multi-agent
- 不重写 `CompletionRequest` / `CompletionResponse` 基础模型
- 不改变当前 CLI 的用户可见行为

## 设计概览

### 1. ProviderRegistry

新增 `ProviderRegistry`，负责维护：

- provider 名称
- provider 构造器
- provider 所需配置的绑定关系

首轮只要求支持静态注册与按名称构造，不要求插件系统或自动发现。

### 2. ProviderConfig

将配置拆成两层：

- 公共配置：如 `default_provider`、`model`、`temperature`
- provider 专属配置：如 `mock.mode`、`mock.response`、`moonshot.api_key`、`moonshot.api_base`

`settings.py` 仍是环境变量入口，但不继续把厂商字段无限堆平在一个数据结构里。

### 3. SelectionPolicy

新增 `SelectionPolicy` 抽象，首轮只提供 `StaticSelectionPolicy`。

首轮行为仍然是“按配置决定使用哪个 provider”，但需要把“选择谁”从“怎么构造”里拆开。这样后续如果要支持动态切换，只需要扩展策略层，而不是回头重构 factory。

## 模块职责

### `src/aiagent/config/settings.py`

- 保留环境变量读取入口
- 负责公共配置装配
- 负责调用 provider 配置解析逻辑
- 不再直接承担所有 provider 细节字段

### `src/aiagent/config/provider_config.py`

- 定义 provider 专属配置模型
- 提供从环境变量或 `Settings` 上下文解析 provider 配置的能力
- 让新增 provider 的配置边界独立可测试

### `src/aiagent/providers/registry.py`

- 提供 provider 注册接口
- 提供按 provider 名称构造实例的能力
- 对未知 provider 给出统一错误

### `src/aiagent/providers/factory.py`

- 继续作为统一 provider 创建入口
- 内部改为依赖 `SelectionPolicy + ProviderRegistry`
- 不再通过持续膨胀的 `if/elif` 承载所有构造逻辑

### `src/aiagent/selection/base.py`

- 定义 `SelectionPolicy` 协议

### `src/aiagent/selection/static.py`

- 提供首轮唯一实现：`StaticSelectionPolicy`
- 根据当前配置返回 provider 名称

## 数据流

首轮数据流应为：

1. 调用方或 CLI 加载 `Settings`
2. `Settings` 产出公共配置与 provider 选择输入
3. `SelectionPolicy` 决定 provider 名称
4. `factory.py` 调用 `ProviderRegistry`
5. `ProviderRegistry` 根据名称和对应配置构造 provider
6. `AssistantAgent` 继续按现有协议调用 `CompletionProvider.complete(...)`

## 行为约束

实现后应满足以下行为约束：

- 默认 provider 仍然是 `mock`
- `mock` 当前 one-shot / REPL 流程行为不变
- `moonshot` 当前配置校验和调用路径仍然成立
- `AssistantAgent` 不需要感知 provider 选择逻辑
- CLI 的命令格式与当前保持一致

## 测试要求

必须新增或更新以下测试：

- `tests/selection/test_static.py`
  - 验证静态策略能返回正确 provider 名称
- `tests/providers/test_registry.py`
  - 验证 provider 注册成功
  - 验证未知 provider 会抛出预期错误
- `tests/config/test_provider_config.py`
  - 验证公共配置与 provider 专属配置的解析边界
- `tests/providers/test_factory.py`
  - 验证 factory 通过 `SelectionPolicy + Registry` 构造 `mock` / `moonshot`
- 相关回归测试
  - `AssistantAgent` 既有测试继续通过
  - CLI 既有测试继续通过

## 实施顺序

推荐按以下顺序实施，并尽量遵循 TDD：

1. 先写 `StaticSelectionPolicy` 测试
2. 实现 `selection/base.py` 与 `selection/static.py`
3. 编写 `ProviderRegistry` 测试
4. 实现 `providers/registry.py`
5. 编写 `ProviderConfig` 测试
6. 实现 `config/provider_config.py`
7. 改造 `providers/factory.py`
8. 运行 provider/config 测试
9. 运行 agent / CLI 回归测试
10. 更新使用文档

## 风险与边界

### 已知风险

- 如果首轮把 `SelectionPolicy` 做得过重，容易提前引入过度设计
- 如果 `ProviderConfig` 分层不清晰，可能只是把复杂度从 `settings.py` 平移到新文件
- 如果 factory 改造时侵入 `AssistantAgent`，会破坏当前最稳定的边界

### 控制方式

- 首轮策略层只允许静态选择
- 首轮注册表只允许显式注册，不做插件化
- 首轮只整理配置边界，不扩大到 richer response 模型

## 完成标准

只有同时满足以下条件，本规范对应的实现才算完成：

1. 新增 provider 时，不再需要在 `factory.py` 中继续追加长链路 `if/elif`
2. 公共配置与 provider 专属配置具备清晰边界
3. `SelectionPolicy` 已成为独立挂载点
4. `AssistantAgent` 的对 provider 调用方式不变
5. 默认 `mock` 流程可继续运行
6. 相关新增测试与既有回归测试全部通过

## 验证

本规范文档完成时，需要满足以下验证条件：

1. 文件位于 `docs/specs/`
2. 文档明确写出目标、范围与非目标
3. 文档明确写出模块职责、数据流与行为约束
4. 文档明确写出测试要求与完成标准
5. 文档范围严格限制在 `registry + config + selection policy`
6. 文档内容为中文

## 后续工作

如果本规范通过评审，下一步应按当前项目 GSD SOP 拆成可执行的小任务计划。后续如需支持动态切换、fallback 或高可用，应另写下一阶段规范，不直接在本规范中扩张范围。
