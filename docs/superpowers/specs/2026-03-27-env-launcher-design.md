# Env 启动器与 .env 模板设计

## 概述

当前项目的运行配置由 `Settings.from_env()` 读取进程环境变量完成，尚未内建 `.env` 文件加载能力。为了让本地开发和多 provider 切换更高效，本设计在不修改主运行时配置模型的前提下，新增一个独立的 Python 启动器和一组 `.env` 模板文件。

本设计的目标是：

- 提供一份清晰可用的 `.env` 启动模板
- 提供一个 Python 启动器，支持通过 provider 名称或 `.env` 文件路径启动
- 支持 one-shot 和 REPL 两种显式运行模式
- 保持现有 `python -m aiagent` 直接运行方式不变

## 用户确认的设计决策

本轮已确认的边界如下：

- 启动器形式：`Python 启动器`
- 切换方式：同时支持 `provider 名称` 和 `--env 文件路径`
- 运行模式：必须显式指定 `--prompt` 或 `--repl`
- `.env` 组织方式：一个总模板加多个 provider 模板

## 目标

### 1. 提供多份 `.env` 模板文件

新增以下文件：

- `.env.example`
- `.env.mock`
- `.env.deepseek`
- `.env.moonshot`

这些文件只提供模板，不写入真实 key。

### 2. 提供独立启动器

新增：

- `tools/run_with_env.py`

该启动器负责：

- 解析 `.env` 文件
- 将解析结果注入子进程环境
- 调用现有 `python -m aiagent`
- 支持 provider 名称和显式 `--env` 路径两种入口

### 3. 支持显式模式运行

启动器必须要求用户明确指定一种模式：

- `--prompt "..."`：one-shot
- `--repl`：交互式 REPL

不允许默认进入某个模式，以避免误触。

## 非目标

本轮明确不做以下事情：

- 不把 `.env` 加载能力塞进 `Settings.from_env()`
- 不修改现有 CLI 参数协议
- 不引入 `python-dotenv`
- 不实现动态 provider 选择、fallback 或高可用策略
- 不自动写入或保存真实 API key
- 不处理 GUI、TUI 或其他交互外壳

## 文件结构

```text
.env.example
.env.mock
.env.deepseek
.env.moonshot
tools/
  run_with_env.py
tests/
  tools/
    test_run_with_env.py
```

## 启动器职责边界

### `tools/run_with_env.py`

负责以下事情：

- 接收 provider 名称或 `--env` 文件路径
- 解析 `.env` 文件中的 `KEY=value`
- 构造一份新的子进程环境变量字典
- 通过 `subprocess` 调用当前 Python 解释器执行 `-m aiagent`

不负责以下事情：

- 不负责 provider 的业务校验
- 不负责 model / key 的语义校验
- 不负责主运行时配置解析
- 不直接改写当前 shell 的环境变量

也就是说，启动器负责“加载和启动”，现有系统继续负责“配置校验和执行”。

## `.env` 模板设计

### `.env.example`

作为完整参考模板，包含：

- 通用变量
- mock 配置
- moonshot 配置
- deepseek 配置

### `.env.mock`

默认本地开发模板，示例内容应偏向：

- `AIAGENT_PROVIDER=mock`
- `AIAGENT_MODEL=mock-model`
- `AIAGENT_MOCK_MODE=echo`

### `.env.deepseek`

DeepSeek 启动模板，示例内容应偏向：

- `AIAGENT_PROVIDER=deepseek`
- `AIAGENT_MODEL=deepseek-chat`
- `AIAGENT_DEEPSEEK_API_BASE=https://api.deepseek.com`
- `AIAGENT_DEEPSEEK_API_KEY=`

### `.env.moonshot`

Moonshot 启动模板，示例内容应偏向：

- `AIAGENT_PROVIDER=moonshot`
- `AIAGENT_MODEL=moonshot-v1-8k`
- `AIAGENT_API_BASE=https://api.moonshot.cn/v1`
- `AIAGENT_API_KEY=`

## 命令设计

### 通过 provider 名称启动

one-shot：

```bash
python tools/run_with_env.py deepseek --prompt "你好"
```

REPL：

```bash
python tools/run_with_env.py deepseek --repl
```

### 通过 env 文件路径启动

one-shot：

```bash
python tools/run_with_env.py --env .env.deepseek --prompt "你好"
```

REPL：

```bash
python tools/run_with_env.py --env .env.deepseek --repl
```

### 辅助命令

列出支持的 provider 模板：

```bash
python tools/run_with_env.py --list
```

可选调试输出：

```bash
python tools/run_with_env.py deepseek --prompt "你好" --verbose
```

`--verbose` 只允许打印所选 env 文件、provider 名称和将执行的模式，不允许打印敏感值。

## provider 名称映射

启动器内置以下映射：

- `mock` -> `.env.mock`
- `deepseek` -> `.env.deepseek`
- `moonshot` -> `.env.moonshot`

若用户传入 `--env`，则直接以显式文件路径为准，不再走内置映射。

## 数据流

启动流程如下：

1. 解析命令行参数
2. 确认使用 provider 名称还是 `--env` 文件路径
3. 解析目标 `.env` 文件
4. 将 `.env` 中的键值对叠加到子进程环境变量
5. 构造 `python -m aiagent ...` 命令
6. 根据 `--prompt` 或 `--repl` 启动子进程
7. 将子进程退出码透传给调用方

## 错误处理

启动器首版需要明确报出以下错误：

- provider 名称不支持
- `--env` 指向的文件不存在
- 同时缺少 `--prompt` 和 `--repl`
- 同时提供了 `--prompt` 和 `--repl`
- `.env` 文件存在非法行

以下错误由现有 `aiagent` 运行时继续负责：

- 缺少必要 API key
- provider 配置错误
- provider 调用失败

## 测试策略

新增：

- `tests/tools/test_run_with_env.py`

首版至少覆盖：

- `.env` 解析成功
- 空行与注释忽略
- provider 到 `.env` 文件映射
- 不支持的 provider 报错
- `--prompt` / `--repl` 冲突报错
- 缺少运行模式报错
- one-shot 命令构造
- REPL 命令构造

首版测试只覆盖启动器本身，不覆盖真实 provider 联网。

## 风险与约束

### 1. 真实 key 泄露风险

模板文件不能包含真实 key。推荐实际使用时：

- 保留仓库内的模板文件
- 用户本地复制为未跟踪的私有 `.env` 文件

### 2. 平台差异

为避免 shell 字符串差异，启动器应使用 `subprocess` 和当前 Python 解释器，而不是拼接平台相关 shell 命令。

### 3. 与主运行时解耦

本设计故意不把 `.env` 支持写进 `Settings`，这样可以保持现有运行时边界稳定。代价是 `.env` 能力只在启动器路径下可用，但这是本轮可接受的折中。

## 成功标准

本设计落地后，满足以下条件即可视为完成：

1. 可以通过 provider 名称启动：
   - `python tools/run_with_env.py deepseek --prompt "你好"`
   - `python tools/run_with_env.py deepseek --repl`
2. 可以通过文件路径启动：
   - `python tools/run_with_env.py --env .env.deepseek --prompt "你好"`
3. `.env.example`、`.env.mock`、`.env.deepseek`、`.env.moonshot` 均存在
4. 启动器不会打印敏感值
5. 现有 `python -m aiagent` 运行方式不受影响
6. 启动器测试通过
7. 至少完成一次本地 smoke test

## 实施建议

推荐后续实施顺序：

1. 先写 `tests/tools/test_run_with_env.py`
2. 再实现 `.env` 解析
3. 再实现 provider -> 模板映射
4. 再实现参数校验与命令构造
5. 最后补 `.env` 模板文件与 smoke test

这个顺序可以保持 TDD，也能把启动器的行为边界控制在一个很小的范围里。
