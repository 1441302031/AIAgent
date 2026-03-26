# API Integration Feasibility Spec

## Goal

在不实现任何新 provider 的前提下，分析当前 `aiagent` 框架是否已经具备“继续扩展更多模型 API 接入”的基础能力，并明确：

- 哪些结构已经足够支持新增 API
- 哪些地方会成为扩展阻力
- 是否可以以“新增 provider”为主完成后续扩展
- 如果不够，缺口最小落在哪里

本 spec 只约束分析工作本身，不约束任何后续实现。

## Scope

本次分析只覆盖当前单 agent 基线下，与新增 API 接入直接相关的层：

- `src/aiagent/config/settings.py`
- `src/aiagent/providers/base.py`
- `src/aiagent/providers/factory.py`
- `src/aiagent/providers/mock.py`
- `src/aiagent/providers/moonshot.py`
- `src/aiagent/agents/assistant.py`
- `src/aiagent/domain/models.py`
- `docs/agent-guide.md`

分析重点是“provider 扩展路径”是否成立，而不是更广义的 agent runtime 演进。

## Non-Goals

以下内容明确不在本次范围内：

- 不新增任何 provider
- 不接入 DeepSeek、OpenAI 或其他真实模型
- 不修改 CLI、agent、session 或 prompt 行为
- 不实现 tool calling、subagent、multi-agent
- 不做性能、并发、流式输出或重试机制改造
- 不产出完整重构方案或实现计划

## Questions To Answer

分析结果必须明确回答以下问题：

1. 当前 `CompletionProvider` 协议是否足以承载新增 API 接入？
2. 当前 `Settings` 结构是否允许在不明显破坏兼容性的前提下继续增加 provider 配置？
3. 当前 `create_provider()` 工厂是否适合作为新增 provider 的统一接入点？
4. 当前 `AssistantAgent` 是否已经与具体 provider 解耦到足以复用？
5. Moonshot 的实现是“特定厂商适配”，还是已经接近“可复用的 OpenAI-compatible 模式”？
6. 如果未来继续接 2-3 个 API，最可能先出现的结构性问题是什么？

## Analysis Approach

本次分析应按下面顺序完成：

1. 读取当前 provider 协议、工厂、配置和 agent 调用链
2. 识别新增 provider 的最小接入面
3. 判断新增一个“与 Moonshot 相似”的聊天模型 API 时，是否主要只需：
   - 新增 provider 文件
   - 扩展 settings 字段
   - 在 factory 中增加分支
4. 判断新增一个“与 Moonshot 不完全兼容”的 API 时，现有边界是否仍然可承载
5. 总结“当前已足够”“需要小改”“需要先重构”这三种结论中哪一种最符合现状

## Decision Criteria

只有同时满足以下条件，才能下结论为“现有框架基本足以扩展更多 API 接入”：

- provider 层有明确稳定接口
- agent 层不依赖具体厂商实现
- 配置层可以按 provider 扩展而不破坏默认 mock 流程
- factory 层能承担 provider 选择职责
- 至少可以清晰描述“新增一个 provider”所需改动点，并且改动点集中

如果以下任一情况成立，则不能给出“基本足够”的结论：

- 新增 provider 需要改动 agent 主流程
- provider 差异无法被现有 `CompletionRequest` / `CompletionResponse` 表达
- 配置结构已经明显耦合到 Moonshot 命名
- factory 扩展会快速演变成不可维护的条件分支

## Deliverable

分析完成后应产出一份简短结论，至少包含：

- 结论等级：`足够扩展` / `小幅调整后可扩展` / `需要先重构`
- 支持该结论的 3-5 条核心证据
- 当前最明显的 1-3 个扩展阻力
- 对后续新增 provider 的最小建议边界

该结论应优先面向“下一步是否值得直接继续接更多 API”这个决策。

## Constraints

- 结论必须基于当前仓库代码，不依赖假设中的未来结构
- 不得把“未来可能这样设计”当作“当前已经支持”
- 不得在分析阶段顺手修改代码
- 如果某个判断是推断而不是代码直接证明，必须明确标注为“推断”

## Verification

本 spec 被视为完成，必须满足以下可检查条件：

1. spec 文件位于 `docs/specs/`
2. 明确写出范围边界和非目标
3. 明确列出待回答问题
4. 明确列出结论判定标准
5. 明确规定分析产出物的形式
6. 明确说明本阶段不做任何实现

## Out Of Scope Follow-Up

如果分析结论认为“可以扩展”或“需要小幅调整后可扩展”，后续才可以进入下一份实现型 spec 或 plan。那将是独立工作，不属于本 spec。
