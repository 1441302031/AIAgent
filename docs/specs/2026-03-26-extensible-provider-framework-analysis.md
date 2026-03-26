# 可扩展 Provider 框架分析

## 结论

最终建议：`做小幅框架调整`

基于当前代码结构，我不建议在新增更多 API 之前先做一轮“大而全”的 provider 框架重构；但我也不建议继续长期维持当前 `if/elif + 单层 Settings` 的模式不变。更合理的方向是，在保持 `CompletionProvider` 与 `AssistantAgent` 边界稳定的前提下，做一组小而明确的框架化调整，为后续新增 provider、手动切换、动态切换和故障转移预留稳定挂载点。

## 当前结构中应保持稳定的部分

以下部分已经是当前框架最有价值的稳定边界，不建议在下一轮扩展中轻易打破：

### 1. `CompletionProvider` 协议边界

当前 `src/aiagent/providers/base.py` 通过：

- `complete(request: CompletionRequest) -> CompletionResponse`

定义了一个非常小、非常清晰的 provider 契约。  
这条边界是当前框架可扩展性的核心，应继续保留。

### 2. `AssistantAgent` 对 provider 的解耦

`src/aiagent/agents/assistant.py` 只依赖：

- `CompletionProvider`
- `SessionHistory`
- `CompletionRequest`
- `CompletionResponse`

它并不感知具体厂商，也不分支处理 `mock` 或 `moonshot`。  
这意味着后续 provider 切换、动态选择或 fallback 的演进，原则上都不应要求修改 agent 主流程。

### 3. `CompletionRequest` / `CompletionResponse` 的基础聊天抽象

当前 `src/aiagent/domain/models.py` 的模型已经足以覆盖近期目标中的基础聊天类 API：

- `CompletionRequest.model`
- `CompletionRequest.messages`
- `CompletionRequest.temperature`
- `CompletionResponse.model`
- `CompletionResponse.message`
- `CompletionResponse.raw`

对接 2-3 个基础聊天 provider，这个抽象仍然成立。

## 当前结构的主要问题

### 1. provider 创建逻辑集中，但扩展方式偏脆弱

当前 `src/aiagent/providers/factory.py` 使用：

- `if settings.provider == "mock"`
- `if settings.provider == "moonshot"`

这种方式在 provider 数量很少时简单直接，但当 provider 继续增长时，会出现：

- 分支集中膨胀
- 构造逻辑难以统一审视
- 新增 provider 时容易把 factory 变成唯一热点文件

因此，当前工厂适合短期扩展，但不适合作为长期 provider 框架的最终形态。

### 2. `Settings` 仍然带有厂商偏向

当前 `src/aiagent/config/settings.py` 中的默认值和校验逻辑仍明显偏向 Moonshot：

- 默认 `api_base = "https://api.moonshot.cn/v1"`
- 错误信息直接写明 `Moonshot provider requires an API key.`

这说明配置层已经可以工作，但还不是中立的 provider 框架配置结构。  
如果继续增加 provider，这部分会越来越容易混杂。

### 3. 当前框架还没有 provider 选择策略层

现在“使用哪个 provider”完全由：

- `Settings.provider`
- `create_provider(settings)`

直接决定。  
这意味着：

- 手动切换只是一种配置分支
- 动态切换还没有独立挂载点
- fallback / failover 也没有独立挂载点

换句话说，当前有 provider 选择入口，但没有 provider 选择策略层。

### 4. 高可用相关能力还没有架构落点

从 `src/aiagent/providers/moonshot.py` 和对应测试可以看出，当前框架已经能区分：

- 认证错误
- 传输错误
- provider 错误
- malformed success response

这是一个好基础。  
但这些错误目前只是在 provider 实现内部被标准化，并没有进一步形成：

- fallback 决策点
- 重试策略挂载点
- provider 健康度判断边界

这意味着“高可用”现在只能作为未来架构方向，而不是当前框架自带能力。

## 对关键问题的回答

### 1. 当前 `CompletionProvider` 是否足以作为长期 provider 边界？

结论：`基本足够，短中期建议保留`

对于基础聊天 API，它已经足够稳定和清晰。  
如果未来引入 tool calling、streaming、usage 结构化读取、多候选响应等 richer API，这个边界可能需要扩展，但当前没有证据表明应先行打破它。

### 2. provider 创建方式是否应继续使用 `if/elif`？

结论：`短期可以，后续应演进为注册表或映射模型`

如果只新增 1 个 provider，继续使用当前方式成本仍然较低。  
但如果目标是“后续更容易扩展、切换和动态切换”，则 provider 创建逻辑应从硬编码分支逐步迁移到：

- provider 注册表
- 名称到构造器的映射
- 或等价的声明式选择结构

这里不需要一步到位做复杂框架，但应停止把工厂长期当作条件分支堆栈。

### 3. 什么样的配置结构更适合未来扩展？

结论：`应从单层通用配置，逐步演进到“公共配置 + provider 专属配置”结构`

当前 `Settings` 已经能工作，但会随着 provider 增长而持续累积厂商细节。  
更适合后续演进的方向是：

- 保留公共字段，如 provider、model、temperature
- 将 provider 专属字段显式分组
- 保持默认 mock 流程最小化

这会让未来新增 provider 时，配置边界更清楚，也更利于切换。

### 4. 支持手动切换 provider 的最小架构变化是什么？

结论：`最小变化是引入更清晰的 provider 注册/选择边界，而不是修改 agent`

手动切换的最小目标不是“多写几个 if”，而是让：

- provider 名称有统一注册点
- 选择入口保持单一
- `AssistantAgent` 完全不需要感知切换逻辑

这说明手动切换应仍然发生在 provider 选择层，而不是 agent 层。

### 5. 支持后续动态选择 provider 的最小架构变化是什么？

结论：`需要引入独立的 SelectionPolicy 挂载点`

动态切换的本质不是“把配置改成运行时变量”，而是让“选哪个 provider”这件事成为一个可替换策略。  
因此，最小必要变化不是重写 provider，而是新增一个清晰的策略挂载点，位于：

- provider registry / factory 之上
- agent 层之下或旁侧

这是一个架构推断，但与当前边界是一致的。

### 6. 支持后续 failover 的最小架构变化是什么？

结论：`需要在标准化错误边界之上增加 FallbackPolicy 挂载点`

当前 provider 层已经提供了较好的错误分类基础。  
这意味着未来 failover 最自然的挂载点不是 CLI，也不是 provider 内部，而是在：

- 标准化错误返回之后
- 真正调用 provider 的外层协调边界

也就是说，先有统一选择逻辑，再有 fallback 才是最自然的路径。

### 7. 哪些部分应在演进中保持稳定？

应优先保持稳定的部分：

- `CompletionProvider` 协议
- `AssistantAgent` 的 provider 无感知调用模式
- `CompletionRequest` / `CompletionResponse` 的基础聊天抽象
- `mock` 作为默认本地流程

## 推荐的最小框架方向

如果目标是“方便后续新增 API、切换、动态切换和面向高可用扩展”，我推荐的最小框架方向是：

### 1. 保留 provider 协议，不先动 agent

先把 provider 框架理顺，不要把问题扩散到 agent 层。  
当前 agent 层已经足够干净，重构收益低于风险。

### 2. 将工厂演进为注册式选择结构

不要求立刻引入复杂插件系统，但应逐步把：

- provider 名称
- provider 构造逻辑
- provider 所需配置

从 `if/elif` 迁移到更清晰的注册式或映射式结构。

### 3. 将设置分为“公共配置 + provider 专属配置”

这是后续易扩展的关键。  
如果不先解决配置边界，provider 增长很快会让 settings 成为新的耦合中心。

### 4. 为未来策略层预留独立挂载点

当前不需要实现动态切换或 failover，但从架构上应明确：

- 手动切换属于配置/选择层
- 动态切换属于 selection policy
- failover 属于 fallback policy

只有这样，后续新增能力时才不会回头侵入 agent 和 CLI。

## 保持当前结构不变的风险

- provider 数量增长后，`factory.py` 会迅速膨胀
- `Settings` 会越来越偏向具体厂商，降低可维护性
- 手动切换会继续停留在硬编码配置分支层面
- 动态切换和 failover 没有清晰挂载点，后续很容易演变为横向侵入

## 过早引入抽象框架的风险

- 当前 provider 数量还少，过重抽象会显著增加理解成本
- 如果过早设计复杂注册、策略、健康检查体系，mock 默认流程会变重
- 如果为了“高可用”提前引入过多概念，当前项目会在未解决真实问题前承担额外复杂度

## 最终建议

我不建议继续完全维持当前结构，也不建议在此刻引入一个完整 provider framework。  
最合理的建议是：

`做小幅框架调整`

这意味着：

- 保留当前 provider 协议和 agent 边界
- 对 provider 选择结构做最小框架化
- 对配置做最小中立化
- 明确为动态切换和 fallback 预留策略挂载点

这条路径最符合当前代码现状，也最能兼顾“易扩展”和“不过度设计”。

## 非实现说明

本分析严格基于当前仓库代码与既有 spec 完成，没有新增任何 provider，也没有修改任何运行时逻辑。
