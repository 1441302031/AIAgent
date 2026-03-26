# Provider Registry / Config / Selection 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不改变 `AssistantAgent` 与 CLI 外部行为的前提下，为当前工程补齐 `ProviderRegistry`、`ProviderConfig` 和 `StaticSelectionPolicy` 三个边界，使后续新增 provider 时更容易扩展与切换。

**Architecture:** 本计划采用“小步重构 + 测试先行”的方式推进。先从最轻的 `SelectionPolicy` 挂载点开始，再引入 `ProviderRegistry`，随后拆分 provider 配置边界，最后只在 `factory.py` 做最小装配改造，并用现有 agent/CLI 回归测试兜底。

**Tech Stack:** Python 3.14、pytest、现有 `aiagent` provider/agent 架构、Markdown 文档、git

---

## 风险前置

- 当前 `settings.py` 已经承载公共配置和厂商细节，如果 `ProviderConfig` 拆分不彻底，复杂度只会横向移动，不会真正下降。
- `factory.py` 是当前 provider 创建热区，如果一次性把注册、配置、选择都揉进去，容易引入隐含行为变化。
- `AssistantAgent` 是现有最稳定边界，这轮如果反向侵入 agent 层，会明显超出 spec 范围。

控制策略：

- 每次只引入一个新边界，并立即用测试验证。
- 所有 provider 选择逻辑都留在 provider 框架层，不移动到 agent 层。
- 默认 `mock` 行为必须在每个阶段都能保持可运行。

## 文件结构图

- `docs/specs/2026-03-26-provider-registry-config-selection-spec.md`
  - 本轮实施的源规范
- `src/aiagent/config/settings.py`
  - 当前环境变量读取与应用配置入口
- `src/aiagent/config/provider_config.py`
  - 新增，承载公共配置之外的 provider 专属配置模型与解析逻辑
- `src/aiagent/providers/base.py`
  - 保持不变的 `CompletionProvider` 协议边界
- `src/aiagent/providers/registry.py`
  - 新增，承载 provider 注册与构造
- `src/aiagent/providers/factory.py`
  - 从硬编码分支演进为 `SelectionPolicy + Registry` 装配点
- `src/aiagent/providers/mock.py`
  - 当前默认 provider，作为行为回归基线
- `src/aiagent/providers/moonshot.py`
  - 当前真实 provider 适配实现，作为 registry/config 装配目标
- `src/aiagent/selection/base.py`
  - 新增，定义 `SelectionPolicy` 协议
- `src/aiagent/selection/static.py`
  - 新增，提供静态策略实现
- `tests/selection/test_static.py`
  - 新增，验证静态选择策略
- `tests/providers/test_registry.py`
  - 新增，验证 provider 注册与未知 provider 错误
- `tests/config/test_provider_config.py`
  - 新增，验证配置分层边界
- `tests/providers/test_factory.py`
  - 修改，验证 factory 通过策略与注册表构造 provider
- `tests/agents/`
  - 回归验证 `AssistantAgent` 不受影响
- `tests/cli/test_main.py`
  - 回归验证 CLI 行为不变

### Task 1: 建立 SelectionPolicy 最小边界

**目标:** 先把“选择哪个 provider”从 factory 的构造逻辑里拆出来，但首轮只支持静态选择。

**涉及文件:**
- Create: `src/aiagent/selection/base.py`
- Create: `src/aiagent/selection/static.py`
- Create: `tests/selection/test_static.py`

**预期改动:**
- 新增 `SelectionPolicy` 协议
- 新增 `StaticSelectionPolicy`
- 增加静态选择策略测试，覆盖默认 provider 与显式 provider 选择

- [ ] **Step 1: 写 `StaticSelectionPolicy` 的失败测试**

```python
from aiagent.selection.static import StaticSelectionPolicy


def test_static_selection_returns_explicit_provider():
    policy = StaticSelectionPolicy()
    assert policy.select_provider("moonshot") == "moonshot"


def test_static_selection_returns_mock_when_provider_missing():
    policy = StaticSelectionPolicy(default_provider="mock")
    assert policy.select_provider(None) == "mock"
```

**验证方式:**
- 运行：`python -B -m pytest tests/selection/test_static.py -v`
- 预期：失败，提示 `aiagent.selection` 或相关类尚不存在

- [ ] **Step 2: 实现最小协议与静态策略**

```python
from typing import Protocol


class SelectionPolicy(Protocol):
    def select_provider(self, configured_provider: str | None) -> str: ...
```

```python
class StaticSelectionPolicy:
    def __init__(self, default_provider: str = "mock") -> None:
        self._default_provider = default_provider

    def select_provider(self, configured_provider: str | None) -> str:
        return configured_provider or self._default_provider
```

**验证方式:**
- 运行：`python -B -m pytest tests/selection/test_static.py -v`
- 预期：`2 passed`

- [ ] **Step 3: 做一次小提交**

```bash
git add src/aiagent/selection/base.py src/aiagent/selection/static.py tests/selection/test_static.py
git commit -m "feat: add static provider selection policy"
```

**验证方式:**
- 运行：`git show --stat --oneline -1`
- 预期：只包含 selection 相关文件

### Task 2: 建立 ProviderRegistry 边界

**目标:** 把 provider 构造能力从 `factory.py` 的硬编码分支中拆成注册表。

**涉及文件:**
- Create: `src/aiagent/providers/registry.py`
- Create: `tests/providers/test_registry.py`
- Modify: `src/aiagent/providers/__init__.py`

**预期改动:**
- 新增显式注册/构造 API
- 对未知 provider 统一报错
- 不引入插件化与自动发现

- [ ] **Step 1: 写 `ProviderRegistry` 的失败测试**

```python
import pytest

from aiagent.providers.registry import ProviderRegistry


def test_registry_builds_registered_provider():
    registry = ProviderRegistry()
    registry.register("demo", lambda _: object())
    assert registry.build("demo", object()).__class__ is object


def test_registry_raises_for_unknown_provider():
    registry = ProviderRegistry()
    with pytest.raises(KeyError):
        registry.build("missing", object())
```

**验证方式:**
- 运行：`python -B -m pytest tests/providers/test_registry.py -v`
- 预期：失败，提示 `ProviderRegistry` 尚不存在

- [ ] **Step 2: 实现最小注册表**

```python
class ProviderRegistry:
    def __init__(self) -> None:
        self._builders: dict[str, object] = {}

    def register(self, name: str, builder) -> None:
        self._builders[name] = builder

    def build(self, name: str, config):
        try:
            builder = self._builders[name]
        except KeyError as exc:
            raise KeyError(f"Unknown provider: {name}") from exc
        return builder(config)
```

**验证方式:**
- 运行：`python -B -m pytest tests/providers/test_registry.py -v`
- 预期：`2 passed`

- [ ] **Step 3: 暴露注册表导出并提交**

```bash
git add src/aiagent/providers/registry.py src/aiagent/providers/__init__.py tests/providers/test_registry.py
git commit -m "feat: add provider registry"
```

**验证方式:**
- 运行：`git show --stat --oneline -1`
- 预期：只包含 registry 相关文件

### Task 3: 拆分 ProviderConfig 配置边界

**目标:** 把公共配置与 provider 专属配置分层，停止在 `settings.py` 里持续堆平厂商字段。

**涉及文件:**
- Create: `src/aiagent/config/provider_config.py`
- Create: `tests/config/test_provider_config.py`
- Modify: `src/aiagent/config/settings.py`
- Modify: `src/aiagent/config/__init__.py`

**预期改动:**
- 新增 provider 配置模型
- `settings.py` 继续作为环境变量入口，但把 provider 专属配置解析委托给新模块
- 保持当前 `mock` / `moonshot` 环境变量兼容

- [ ] **Step 1: 写 provider 配置解析失败测试**

```python
from aiagent.config.provider_config import build_provider_configs


def test_build_provider_configs_returns_mock_settings():
    configs = build_provider_configs(
        mock_mode="echo",
        mock_response="hi",
        moonshot_api_key=None,
        moonshot_api_base="https://api.moonshot.cn/v1",
    )
    assert configs["mock"].mode == "echo"
    assert configs["mock"].response == "hi"


def test_build_provider_configs_returns_moonshot_settings():
    configs = build_provider_configs(
        mock_mode="echo",
        mock_response="hi",
        moonshot_api_key="secret",
        moonshot_api_base="https://api.moonshot.cn/v1",
    )
    assert configs["moonshot"].api_key == "secret"
```

**验证方式:**
- 运行：`python -B -m pytest tests/config/test_provider_config.py -v`
- 预期：失败，提示 `provider_config` 尚不存在

- [ ] **Step 2: 实现最小配置模型与解析函数**

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class MockProviderConfig:
    mode: str
    response: str


@dataclass(frozen=True)
class MoonshotProviderConfig:
    api_key: str | None
    api_base: str
```

**验证方式:**
- 运行：`python -B -m pytest tests/config/test_provider_config.py -v`
- 预期：`2 passed`

- [ ] **Step 3: 让 `Settings` 暴露分层配置而不改现有外部行为**

```python
provider_configs = build_provider_configs(
    mock_mode=self.mock_mode,
    mock_response=self.mock_response,
    moonshot_api_key=self.api_key,
    moonshot_api_base=self.api_base,
)
```

**验证方式:**
- 运行：`python -B -m pytest tests/config/test_provider_config.py tests/config -v`
- 预期：provider config 测试通过，既有 config 测试无新增失败

- [ ] **Step 4: 小提交**

```bash
git add src/aiagent/config/provider_config.py src/aiagent/config/settings.py src/aiagent/config/__init__.py tests/config/test_provider_config.py
git commit -m "feat: split provider configuration"
```

**验证方式:**
- 运行：`git show --stat --oneline -1`
- 预期：只包含 config 分层相关文件

### Task 4: 改造 factory 接入策略层与注册表

**目标:** 在不改变外部创建入口的情况下，让 `factory.py` 通过 `SelectionPolicy + ProviderRegistry` 构造 provider。

**涉及文件:**
- Modify: `src/aiagent/providers/factory.py`
- Modify: `tests/providers/test_factory.py`
- Reference: `src/aiagent/providers/mock.py`
- Reference: `src/aiagent/providers/moonshot.py`
- Reference: `src/aiagent/selection/static.py`
- Reference: `src/aiagent/providers/registry.py`

**预期改动:**
- `create_provider(settings)` 仍保留
- 内部先选择 provider，再通过 registry 构造
- 不改变 `mock` 与 `moonshot` 的外部可见行为

- [ ] **Step 1: 先更新 factory 测试，让它表达新装配方式**

```python
def test_create_provider_builds_mock_via_registry():
    settings = Settings(provider="mock")
    provider = create_provider(settings)
    assert provider.__class__.__name__ == "MockProvider"


def test_create_provider_builds_moonshot_via_registry():
    settings = Settings(provider="moonshot", api_key="secret")
    provider = create_provider(settings)
    assert provider.__class__.__name__ == "MoonshotProvider"
```

**验证方式:**
- 运行：`python -B -m pytest tests/providers/test_factory.py -v`
- 预期：先失败，反映旧实现与新测试不匹配

- [ ] **Step 2: 实现默认注册表装配**

```python
registry = ProviderRegistry()
registry.register("mock", lambda config: MockProvider(mode=config.mode, response=config.response))
registry.register(
    "moonshot",
    lambda config: MoonshotProvider(api_key=config.api_key, api_base=config.api_base),
)
```

**验证方式:**
- 运行：`python -B -m pytest tests/providers/test_factory.py -v`
- 预期：factory 测试通过

- [ ] **Step 3: 接入 `StaticSelectionPolicy`**

```python
policy = StaticSelectionPolicy(default_provider=settings.provider)
provider_name = policy.select_provider(settings.provider)
provider = registry.build(provider_name, settings.provider_configs[provider_name])
```

**验证方式:**
- 运行：`python -B -m pytest tests/providers/test_factory.py tests/providers/test_registry.py tests/selection/test_static.py -v`
- 预期：全部通过

- [ ] **Step 4: 小提交**

```bash
git add src/aiagent/providers/factory.py tests/providers/test_factory.py
git commit -m "refactor: route provider creation through registry and selection policy"
```

**验证方式:**
- 运行：`git show --stat --oneline -1`
- 预期：只包含 factory 与对应测试改动

### Task 5: 运行回归测试，确认 agent 与 CLI 无行为回归

**目标:** 证明这轮框架层调整没有侵入 `AssistantAgent` 与 CLI 外部行为。

**涉及文件:**
- Read: `tests/agents/`
- Read: `tests/cli/test_main.py`
- Read: `tests/providers/`
- Read: `tests/config/`
- Read: `tests/selection/`

**预期改动:**
- 本任务不新增实现代码
- 只在发现测试缺口时补最小回归测试

- [ ] **Step 1: 跑 provider/config/selection 测试集合**

运行：

```bash
python -B -m pytest tests/providers tests/config tests/selection -v
```

**验证方式:**
- 预期：全部通过

- [ ] **Step 2: 跑 agent 回归测试**

运行：

```bash
python -B -m pytest tests/agents -v
```

**验证方式:**
- 预期：全部通过

- [ ] **Step 3: 跑 CLI 回归测试**

运行：

```bash
python -B -m pytest tests/cli/test_main.py -v
```

**验证方式:**
- 预期：全部通过

- [ ] **Step 4: 如果需要，补一条最小集成测试**

建议补的最小测试：

```python
def test_create_provider_keeps_mock_as_default_when_no_provider_is_set():
    settings = Settings(provider=None)
    provider = create_provider(settings)
    assert provider.__class__.__name__ == "MockProvider"
```

**验证方式:**
- 运行：对应单测 + `tests/providers/test_factory.py`
- 预期：通过

- [ ] **Step 5: 小提交**

```bash
git add tests/providers tests/config tests/selection tests/agents tests/cli/test_main.py
git commit -m "test: add provider framework regression coverage"
```

**验证方式:**
- 运行：`git show --stat --oneline -1`
- 预期：只包含测试相关改动

### Task 6: 更新文档并做最终验证

**目标:** 让使用文档与实现结果保持一致，并在结束前完成一次完整验证。

**涉及文件:**
- Modify: `README.md`
- Modify: `docs/agent-guide.md`
- Reference: `docs/specs/2026-03-26-provider-registry-config-selection-spec.md`

**预期改动:**
- 补充 provider 构造机制已演进为注册/策略装配
- 说明当前仍是静态选择，不包含动态切换与 failover
- 不扩展到超出本轮范围的功能说明

- [ ] **Step 1: 更新 README 的 provider 架构说明**

补充内容：
- 当前 provider 选择路径
- 默认仍然是 `mock`
- 动态切换尚未实现

**验证方式:**
- 人工检查 `README.md` 是否与实现一致

- [ ] **Step 2: 更新 `docs/agent-guide.md` 的扩展说明**

补充内容：
- registry / config / static selection 的当前边界
- 后续如何在此基础上继续做动态切换

**验证方式:**
- 人工检查文档是否与 spec、代码一致

- [ ] **Step 3: 跑最终完整测试**

运行：

```bash
python -B -m pytest -p no:cacheprovider -v
```

**验证方式:**
- 预期：全量测试通过

- [ ] **Step 4: 做最终提交**

```bash
git add README.md docs/agent-guide.md
git commit -m "docs: document provider registry and selection architecture"
```

**验证方式:**
- 运行：`git status --short`
- 预期：只剩无关未跟踪噪音，当前任务相关文件均已提交

## 完成定义

满足以下条件才算本计划执行完成：

- `SelectionPolicy` 已成为独立挂载点
- `ProviderRegistry` 已接管 provider 构造
- `ProviderConfig` 已明确拆出 provider 专属配置边界
- `create_provider(settings)` 对外入口保留不变
- 默认 `mock` 行为不变
- `AssistantAgent` 与 CLI 回归测试全部通过
- README 与 `docs/agent-guide.md` 已更新到当前架构

## 执行备注

- 严格按 TDD 顺序推进，不要跳过“先失败测试”的步骤。
- 每个任务完成后立即运行对应验证，不要把多个风险点堆到最后一起排查。
- 如果任一阶段出现行为异常，先使用 `systematic-debugging` 定位根因，再决定是否修改实现。
