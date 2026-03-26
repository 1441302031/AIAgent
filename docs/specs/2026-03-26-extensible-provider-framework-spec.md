# 可扩展 Provider 框架规范

## 目标

产出一份精简、可执行的分析型规范，用于评估如何将当前 `aiagent` 的 provider 架构演进为一个具备以下特征的框架：

- 更容易扩展新 API
- 更容易在不同 provider 之间切换
- 后续能够支持动态选择 provider
- 在架构层面考虑高可用能力

本规范仅用于分析与设计，不授权任何实现工作。

## 范围

本次工作只分析当前框架中的以下内容：

- `docs/specs/2026-03-26-api-integration-feasibility-analysis.md`
- `src/aiagent/providers/base.py`
- `src/aiagent/providers/factory.py`
- `src/aiagent/providers/mock.py`
- `src/aiagent/providers/moonshot.py`
- `src/aiagent/config/settings.py`
- `src/aiagent/agents/assistant.py`
- `src/aiagent/domain/models.py`

分析重点仅限于 provider 框架演进，不扩展到更广义的 agent 架构。

## 期望产出

分析结果需要回答：项目是否应演进为一个具备以下能力的 provider 框架：

- provider 注册表或映射模型
- provider 专属配置边界
- 显式的 provider 选择策略
- 可选的 fallback / failover 策略
- 在不重写 agent 代码的前提下支持后续动态切换的路径

## 非目标

本规范明确不包括以下内容：

- 不实现任何新的 provider
- 不重构现有代码
- 不增加运行时 failover 行为
- 不增加 retry、circuit breaker 或 load balancing
- 不增加 tool calling、subagent 或 multi-agent 行为
- 不增加流式输出支持
- 不编写实现计划
- 不修改测试或生产代码

## 待回答问题

基于本规范产出的分析文档，必须回答以下问题：

1. 当前 `CompletionProvider` 契约是否足以作为长期 provider 边界？
2. provider 创建方式是否应继续使用 `if/elif` 分支，还是应迁移到注册表模型？
3. 什么样的配置结构能让未来新增 provider 更容易，同时避免硬编码厂商假设？
4. 支持“手动切换 provider”的最小架构变化是什么？
5. 支持“后续动态选择 provider”的最小架构变化是什么？
6. 支持“后续 provider 间故障转移”的最小架构变化是什么？
7. 在这一演进过程中，当前代码中哪些部分应保持稳定不动？

## 分析方向

分析应将当前设计与一个精简目标框架进行对照。目标框架仅作为概念模型，包含：

- `ProviderProtocol`：稳定的请求/响应边界
- `ProviderRegistry`：将 provider 名称映射到构造器或描述对象
- `ProviderConfig`：将公共配置与 provider 专属配置分离
- `SelectionPolicy`：决定应使用哪个 provider
- `FallbackPolicy`：定义 provider 失败时的处理方式

这种对照仅限概念分析，不编写任何代码。

## 判定标准

只有在未来框架方向同时改善以下各项时，才应推荐引入：

- 新增 provider 时需要改动的集中化文件更少
- 切换 provider 不需要修改 agent 层代码
- 配置结构更中立，不偏向特定厂商
- 后续 fallback 行为有清晰的挂载点
- 默认 mock 流程仍然保持简单

如果某个方向会在尚未解决真实扩展问题之前，明显提高当前项目复杂度，则应判定为过度设计并拒绝。

## 交付物

基于本规范的后续分析，应产出一份简短决策文档，至少包含：

- 推荐的架构方向
- 最小必要的边界变化
- 应保持稳定不变的部分
- 继续维持当前模型的风险
- 过早引入更抽象框架的风险
- 在以下结论中的最终推荐：
  - `保持当前结构`
  - `做小幅框架调整`
  - `在新增更多 API 前先引入 provider 框架`

## 约束

- 所有结论都必须基于当前仓库代码
- 将高可用视为架构议题，而不是实现任务
- 不假设存在分布式系统、并发调度或 service mesh 能力
- 不为“无限数量 provider”设计，只为近期增长优化
- 优先采用最小且真正有用的抽象

## 验证

只有满足以下所有条件，本规范才算完成：

1. 文件保存在 `docs/specs/` 下
2. 目标明确为“仅分析”，而不是实现
3. 非目标已被明确列出
4. 待回答问题已明确列出
5. 判定标准已明确列出
6. 交付物形式已明确列出
7. 高可用与动态切换已被明确纳入分析主题

## 超出范围的后续工作

如果后续分析认为有必要做框架层调整，那么下一步必须另写一份面向实现的独立规范。那部分工作不属于本文件范围。
