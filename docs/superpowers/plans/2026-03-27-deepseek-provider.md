# DeepSeek Provider 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不破坏现有 `AssistantAgent`、CLI 与已有 provider 行为的前提下，新增 `DeepSeekProvider`，并通过 DeepSeek 专属环境变量完成配置、构造、测试与真实连通性验证。

**Architecture:** 本计划沿用现有 `ProviderRegistry + ProviderConfig + StaticSelectionPolicy + factory` 架构，不引入通用 OpenAI-compatible 抽象层。实现顺序采用 TDD，从 provider config 和 settings 边界开始，再实现 provider 本身，最后接入 factory、补回归测试并做真实 API smoke test。

**Tech Stack:** Python 3.14、pytest、httpx、现有 aiagent provider 架构、环境变量配置、git

---

## 风险前置

- 当前环境无法稳定在线读取 DeepSeek 官方文档，因此实现时不能依赖“临时浏览记忆”，必须以现有 spec 为准，并把真实联网验证放到最后一步。
- 用户已在会话中提供真实 API key。该 key 只能用于本地进程环境变量注入，不能写入代码、测试、文档、计划文件或 git 历史。
- `MoonshotProvider` 和 DeepSeek 很像，但这轮目标是独立 provider，不是顺手抽通用兼容层；如果实现时开始复制重构过多，说明范围在滑动。

控制策略：

- DeepSeek 首版只支持与现有 `CompletionRequest` / `CompletionResponse` 对齐的聊天补全路径。
- 所有真实 key 只在本地 smoke test 命令里临时注入，不落盘。
- 不改 `AssistantAgent`、CLI、session、prompt 结构。

## 文件结构图

- `docs/specs/2026-03-27-deepseek-provider-spec.md`
  - 本轮实施的源规范
- `src/aiagent/config/settings.py`
  - 环境变量入口，新增 DeepSeek 专属配置读取与校验
- `src/aiagent/config/provider_config.py`
  - 新增 `DeepSeekProviderConfig` 与配置组装逻辑
- `src/aiagent/providers/deepseek.py`
  - 新增 DeepSeek provider 实现
- `src/aiagent/providers/factory.py`
  - 通过 registry + static selection 注册并构造 `deepseek`
- `src/aiagent/providers/__init__.py`
  - 对外导出 `DeepSeekProvider`
- `tests/config/test_provider_config.py`
  - 补充 DeepSeek provider config 组装测试
- `tests/config/test_settings.py`
  - 补充 DeepSeek 环境变量读取与缺 key 错误测试
- `tests/providers/test_deepseek.py`
  - 新增 DeepSeek provider 行为测试
- `tests/providers/test_factory.py`
  - 补充通过 factory 构造 `DeepSeekProvider` 的测试
- `README.md`
  - 更新 DeepSeek 配置方式
- `docs/agent-guide.md`
  - 更新 provider 使用说明与 DeepSeek 示例

### Task 1: 扩展 ProviderConfig 支持 DeepSeek

**Goal:** 先把 DeepSeek 的 provider 专属配置边界加进现有配置分层，不触碰 provider 实现。

**Files:**
- Modify: `src/aiagent/config/provider_config.py`
- Test: `tests/config/test_provider_config.py`

- [ ] **Step 1: 写 DeepSeek provider config 的失败测试**

```python
from aiagent.config.provider_config import build_provider_configs


def test_build_provider_configs_returns_deepseek_settings():
    configs = build_provider_configs(
        mock_mode="echo",
        mock_response="hi",
        moonshot_api_key=None,
        moonshot_api_base="https://api.moonshot.cn/v1",
        deepseek_api_key="secret",
        deepseek_api_base="https://api.deepseek.com",
    )

    assert configs["deepseek"].api_key == "secret"
    assert configs["deepseek"].api_base == "https://api.deepseek.com"
```

- [ ] **Step 2: 运行测试，确认按预期红灯**

Run: `python -B -m pytest tests/config/test_provider_config.py -v`
Expected: FAIL，提示 `build_provider_configs()` 不接受 DeepSeek 参数或 `deepseek` 配置不存在

- [ ] **Step 3: 实现最小 DeepSeekProviderConfig**

```python
@dataclass(frozen=True, slots=True)
class DeepSeekProviderConfig:
    api_key: str | None
    api_base: str
```

并让 `build_provider_configs(...)` 返回 `deepseek` 配置项。

- [ ] **Step 4: 再跑配置测试确认转绿**

Run: `python -B -m pytest tests/config/test_provider_config.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/aiagent/config/provider_config.py tests/config/test_provider_config.py
git commit -m "feat: add deepseek provider config"
```

### Task 2: 扩展 Settings 读取 DeepSeek 专属环境变量

**Goal:** 让 `Settings` 能读取 `AIAGENT_DEEPSEEK_API_KEY` 与 `AIAGENT_DEEPSEEK_API_BASE`，并在选择 `deepseek` 且缺 key 时抛出配置错误。

**Files:**
- Modify: `src/aiagent/config/settings.py`
- Test: `tests/config/test_settings.py`

- [ ] **Step 1: 写失败测试，覆盖读取与缺 key 校验**

```python
def test_settings_load_deepseek_provider_from_env():
    settings = Settings.from_env(
        {
            "AIAGENT_PROVIDER": "deepseek",
            "AIAGENT_DEEPSEEK_API_KEY": "secret",
            "AIAGENT_DEEPSEEK_API_BASE": "https://api.deepseek.com",
            "AIAGENT_MODEL": "deepseek-chat",
        }
    )
    assert settings.provider == "deepseek"
    assert settings.provider_configs["deepseek"].api_key == "secret"


def test_settings_require_api_key_for_deepseek():
    with pytest.raises(ConfigurationError, match="DeepSeek"):
        Settings.from_env({"AIAGENT_PROVIDER": "deepseek"})
```

- [ ] **Step 2: 运行测试，确认红灯**

Run: `python -B -m pytest tests/config/test_settings.py -v`
Expected: FAIL，提示 DeepSeek 配置尚未接入

- [ ] **Step 3: 实现最小 Settings 扩展**

实现内容：
- 新增 DeepSeek 环境变量读取
- 将其传给 `build_provider_configs(...)`
- 在 `provider=deepseek` 且缺 `AIAGENT_DEEPSEEK_API_KEY` 时抛配置错误

- [ ] **Step 4: 跑 config 测试集**

Run: `python -B -m pytest tests/config -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/aiagent/config/settings.py tests/config/test_settings.py
git commit -m "feat: add deepseek settings support"
```

### Task 3: 新增 DeepSeekProvider 实现

**Goal:** 新增 DeepSeek provider，保持与现有 `MoonshotProvider` 同级、同协议，不抽通用兼容层。

**Files:**
- Create: `src/aiagent/providers/deepseek.py`
- Modify: `src/aiagent/providers/__init__.py`
- Test: `tests/providers/test_deepseek.py`

- [ ] **Step 1: 写失败测试，覆盖请求构造与错误归一化**

至少包含：

```python
def test_deepseek_provider_sends_chat_completion_payload(): ...
def test_deepseek_provider_raises_on_401(): ...
def test_deepseek_provider_raises_provider_error_on_500(): ...
def test_deepseek_provider_raises_transport_error_on_http_failure(): ...
def test_deepseek_provider_raises_provider_error_on_malformed_success_response(): ...
```

- [ ] **Step 2: 运行单测，确认红灯**

Run: `python -B -m pytest tests/providers/test_deepseek.py -v`
Expected: FAIL，提示 `DeepSeekProvider` 模块或类不存在

- [ ] **Step 3: 写最小实现**

实现要求：
- 构造参数：`api_key`、`model`、`base_url`、`transport=None`
- POST 到 `/chat/completions`
- `Authorization: Bearer <api_key>`
- request body 包含 `model/messages/temperature`
- 成功响应转换为 `CompletionResponse`
- 401/4xx/5xx/http failure/非法成功响应按现有 provider 语义归一化

- [ ] **Step 4: 跑 DeepSeek provider 测试**

Run: `python -B -m pytest tests/providers/test_deepseek.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/aiagent/providers/deepseek.py src/aiagent/providers/__init__.py tests/providers/test_deepseek.py
git commit -m "feat: add deepseek provider"
```

### Task 4: 通过 Factory 接入 DeepSeekProvider

**Goal:** 保持 `create_provider(settings)` 不变，通过现有 registry + static selection 装配 `deepseek`。

**Files:**
- Modify: `src/aiagent/providers/factory.py`
- Test: `tests/providers/test_factory.py`

- [ ] **Step 1: 先写失败测试**

```python
def test_provider_factory_builds_deepseek_provider():
    settings = Settings.from_env(
        {
            "AIAGENT_PROVIDER": "deepseek",
            "AIAGENT_DEEPSEEK_API_KEY": "secret",
            "AIAGENT_DEEPSEEK_API_BASE": "https://api.deepseek.com",
            "AIAGENT_MODEL": "deepseek-chat",
        }
    )
    provider = create_provider(settings)
    assert isinstance(provider, DeepSeekProvider)
```

如已有 factory 装配路径测试风格一致，也补一条 monkeypatch 路径断言。

- [ ] **Step 2: 跑 factory 测试确认红灯**

Run: `python -B -m pytest tests/providers/test_factory.py -v`
Expected: FAIL，提示 `deepseek` 尚未注册

- [ ] **Step 3: 在 factory 中注册 deepseek**

最小实现：
- `registry.register("deepseek", ...)`
- 从 `settings.provider_configs["deepseek"]` 取 `api_key/api_base`
- 缺 key 时抛 `ConfigurationError`

- [ ] **Step 4: 跑 provider/config/selection 相关测试**

Run: `python -B -m pytest tests/providers tests/config tests/selection -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/aiagent/providers/factory.py tests/providers/test_factory.py
git commit -m "feat: wire deepseek provider into factory"
```

### Task 5: 跑回归测试，确认 Agent 与 CLI 无回归

**Goal:** 证明 DeepSeek 接入没有影响现有 agent、CLI 与已有 provider。

**Files:**
- Read: `tests/agents/`
- Read: `tests/cli/test_main.py`
- Read: `tests/providers/`
- Read: `tests/config/`

- [ ] **Step 1: 跑 providers/config 回归**

Run: `python -B -m pytest -p no:cacheprovider tests/providers tests/config -v`
Expected: PASS

- [ ] **Step 2: 跑 agent 回归**

Run: `python -B -m pytest -p no:cacheprovider tests/agents -v`
Expected: PASS

- [ ] **Step 3: 跑 CLI 回归**

Run: `python -B -m pytest -p no:cacheprovider tests/cli/test_main.py -v`
Expected: PASS

- [ ] **Step 4: 若无缺口，不新增测试**

Verification:
- 明确记录“不需要补额外回归测试”的理由
- 避免为了凑任务增加低价值测试

### Task 6: 用真实 DeepSeek Key 做最小 Smoke Test

**Goal:** 在不把 key 落盘的前提下，验证 DeepSeek 接入能完成真实 one-shot 调用。

**Files:**
- No file changes required unless发现真实 API 兼容性缺陷

- [ ] **Step 1: 先跑一个本地 one-shot smoke**

Run（示意，实际在当前 shell 临时注入，不写入文件）：

```bash
$env:AIAGENT_PROVIDER='deepseek'
$env:AIAGENT_MODEL='deepseek-chat'
$env:AIAGENT_DEEPSEEK_API_KEY='<local-only>'
$env:AIAGENT_DEEPSEEK_API_BASE='https://api.deepseek.com'
python -m aiagent "hello"
```

Expected:
- 返回真实模型回复
- 不报配置错误

- [ ] **Step 2: 如果 one-shot 成功，再跑 REPL smoke**

Run（示意）：

```bash
'quit' | ForEach-Object {
  $env:AIAGENT_PROVIDER='deepseek'
  $env:AIAGENT_MODEL='deepseek-chat'
  $env:AIAGENT_DEEPSEEK_API_KEY='<local-only>'
  $env:AIAGENT_DEEPSEEK_API_BASE='https://api.deepseek.com'
  $_
} | python -m aiagent --repl
```

Expected:
- 能正常启动 REPL
- 能正常退出

- [ ] **Step 3: 若真实 smoke 暴露兼容性问题，先写回归测试再修**

Verification:
- 必须明确记录是配置问题、网络问题，还是响应格式问题
- 不允许直接热修不补测试

### Task 7: 更新文档并做最终验证

**Goal:** 同步 README / Agent Guide 中的配置说明，并做最终全量验证。

**Files:**
- Modify: `README.md`
- Modify: `docs/agent-guide.md`

- [ ] **Step 1: 更新 README**

补充：
- `AIAGENT_PROVIDER=deepseek`
- `AIAGENT_DEEPSEEK_API_KEY`
- `AIAGENT_DEEPSEEK_API_BASE`
- 当前 DeepSeek 是独立 provider，不是通用兼容层

- [ ] **Step 2: 更新 Agent Guide**

补充：
- DeepSeek provider 用法
- DeepSeek 在现有 registry/config/factory 中的位置
- 真实 key 只通过环境变量注入，不写入项目文件

- [ ] **Step 3: 跑最终全量测试**

Run: `python -B -m pytest -p no:cacheprovider -v`
Expected: PASS

- [ ] **Step 4: 最终提交**

```bash
git add README.md docs/agent-guide.md
git commit -m "docs: add deepseek provider usage"
```

## 完成定义

满足以下条件才算本计划执行完成：

- `AIAGENT_PROVIDER=deepseek` 时可构造 `DeepSeekProvider`
- 缺失 `AIAGENT_DEEPSEEK_API_KEY` 时明确报配置错误
- DeepSeek 请求/响应路径与现有 completion 协议对齐
- 401/5xx/传输异常/非法成功响应均有测试覆盖
- factory 已通过 registry + static selection 接入 `deepseek`
- 现有 `mock` / `moonshot` / `AssistantAgent` / CLI 行为无回归
- 本地全量测试通过
- 至少一次真实 DeepSeek one-shot smoke test 成功
- key 未写入仓库、文档或测试文件

## 执行备注

- 计划中提到的真实 key 只作为本地运行时输入，不应出现在提交记录中。
- 当前会话里用户给的 key 已暴露在聊天历史中；实现结束后应提醒用户自行轮换。
- 如果真实联网验证失败，先区分是文档差异、网络/TLS 问题，还是 provider 解析问题，再决定是否继续修改代码。
