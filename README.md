# aicore

`aicore` 是一个最小可跑的任务草案 CLI，用来先生成任务边界、确认修改范围，再决定是否进入下一步。

## 核心原则

- `start` 只会生成 `task.yaml` 和 `brief.md` 草案。
- 工具不会自动进入实现阶段，必须由人工确认后，再执行 `review`、`approve` 或 `reject`。
- `brief.md` 的确认信息全部派生自同目录下的 `task.yaml`，没有额外状态源。

## 本地安装

macOS/Linux:

```bash
python3.11 -m pip install -e '.[dev]'
```

Windows PowerShell:

```powershell
py -3.11 -m pip install -e ".[dev]"
```

## Smoke Test

macOS/Linux:

```bash
python3.11 -B -m pytest -p no:cacheprovider tests/test_cli_smoke.py -q
```

Windows PowerShell:

```powershell
py -3.11 -B -m pytest -p no:cacheprovider tests/test_cli_smoke.py -q
```

## MVP 命令流

CLI 会把任务文件写到当前工作目录下的 `.aicore/tasks/`。

### 1. 生成草案

macOS/Linux:

```bash
python3.11 -m aicore.cli start "实现 JWT 登录"
```

Windows PowerShell:

```powershell
py -3.11 -m aicore.cli start "实现 JWT 登录"
```

运行后会生成：

- `.aicore/tasks/<task-id>/task.yaml`
- `.aicore/tasks/<task-id>/brief.md`

此时只是在准备人工确认材料，不会自动进入实现阶段。

### 2. 进入人工复核

macOS/Linux:

```bash
python3.11 -m aicore.cli review task-2026-05-25-001
```

Windows PowerShell:

```powershell
py -3.11 -m aicore.cli review task-2026-05-25-001
```

建议先阅读 `brief.md`，重点确认这些信息：

- 主入口
- 兼容入口
- 是否需要双改
- 双改原因
- 允许修改文件
- 禁止修改范围
- 验收依据
- 回退方案

### 3. 人工批准

macOS/Linux:

```bash
python3.11 -m aicore.cli approve task-2026-05-25-001 --by "alice"
```

Windows PowerShell:

```powershell
py -3.11 -m aicore.cli approve task-2026-05-25-001 --by "alice"
```

`approve` 只记录该草案已经被人工确认，不代表工具自动开始实现。

### 4. 人工驳回

macOS/Linux:

```bash
python3.11 -m aicore.cli reject task-2026-05-25-001 --reason "主入口未确认"
```

Windows PowerShell:

```powershell
py -3.11 -m aicore.cli reject task-2026-05-25-001 --reason "主入口未确认"
```

当边界、风险或回退方案不清晰时，应先 `reject`，而不是继续往下推进。

## 当前边界

- 当前 MVP 是任务启动闸机，不是自动实现器。
- `entrypoints`、`allowed_files`、`baseline_refs` 等关键字段仍以人工补全和人工确认为主。
- 如果主入口、双改策略、修改范围或验收依据还不稳定，就应该停在 `review` / `reject`，而不是继续推进。
- 如果当前 Git 顶层不是本项目目录，应先隔离到独立仓库或 worktree，再执行 commit。

## 执行安全层

执行安全层只解决两件事：

- Agent 改完文件后，立刻留下可恢复版本
- 你确认某个变化已经成为“当前系统事实”后，把它写进总账本

这层不会替代 Git，也不会自动判断模型是否降智。

### 1. 记录一次 Agent 写入

macOS/Linux:

```bash
python3.11 -m aicore.cli log-write task-2026-05-26-001 \
  --session session-1 \
  --file src/auth/login.ts \
  --summary "记录登录逻辑改动"
```

Windows PowerShell:

```powershell
py -3.11 -m aicore.cli log-write task-2026-05-26-001 `
  --session session-1 `
  --file src/auth/login.ts `
  --summary "记录登录逻辑改动"
```

输出：

- 第一行：`event_id`
- 第二行：事件文件路径

落盘结果：

- `.aicore/history/events/<event-id>.json`
- `.aicore/history/snapshots/<task-id>/<event-id>/...`

### 2. 为一轮修改生成 checkpoint

拿到 `log-write` 打印的 `event_id` 后，再显式生成阶段 checkpoint。

macOS/Linux:

```bash
python3.11 -m aicore.cli checkpoint task-2026-05-26-001 \
  --event event-20260526000000000000-example \
  --summary "登录逻辑达到阶段稳定点"
```

Windows PowerShell:

```powershell
py -3.11 -m aicore.cli checkpoint task-2026-05-26-001 `
  --event event-20260526000000000000-example `
  --summary "登录逻辑达到阶段稳定点"
```

输出：

- 第一行：`checkpoint_id`
- 第二行：manifest 路径

落盘结果：

- `.aicore/history/checkpoints/<task-id>/<checkpoint-id>/manifest.json`

约束：

- `--event` 可以重复传入多次
- 所有 `event_id` 都必须真实存在
- 所有 `event_id` 都必须属于同一个 `task_id`

### 3. 确认完成态并更新账本

当你确认某个变化已经成为当前系统事实时，再写入账本。

macOS/Linux:

```bash
python3.11 -m aicore.cli ledger-confirm task-2026-05-26-001 \
  --event event-20260526000000000000-example \
  --capability "支持 JWT 登录" \
  --entrypoint "API: POST /auth/login" \
  --limit "暂不支持 refresh token" \
  --compatibility "支持 macOS、Windows、Linux" \
  --risk "异常路径回归待补齐"
```

Windows PowerShell:

```powershell
py -3.11 -m aicore.cli ledger-confirm task-2026-05-26-001 `
  --event event-20260526000000000000-example `
  --capability "支持 JWT 登录" `
  --entrypoint "API: POST /auth/login" `
  --limit "暂不支持 refresh token" `
  --compatibility "支持 macOS、Windows、Linux" `
  --risk "异常路径回归待补齐"
```

输出：

- `.aicore/system-ledger.md`

落盘结果：

- 账本会更新这 5 个固定区块：
  - `Current Capabilities`
  - `Entrypoints`
  - `Limits And Boundaries`
  - `Compatibility`
  - `Known Risks`

约束：

- `capability`、`entrypoint`、`limit`、`compatibility`、`risk` 都必须是单行文本
- 账本记录的是“当前已确认事实”，不是所有实现过程

### 一个最小工作流

1. `start`：先冻结任务边界
2. `log-write`：每次 Agent 写文件后留痕
3. `checkpoint`：一轮修改达到稳定点后打 checkpoint
4. `ledger-confirm`：确认完成态已经成立，再更新账本

如果你只是试验某个改动，还没有确认它已经成为系统真实能力，就只做 `log-write` / `checkpoint`，不要提前写账本。

## Claude Code 包装层

本项目提供项目级 Claude Code 包装层：

- `CLAUDE.md`：项目级 `aicore` 工作流规则
- `.claude/commands/aicore-start.md`：`/aicore-start`
- `.claude/commands/aicore-save.md`：`/aicore-save`
- `.claude/commands/aicore-log-write.md`：`/aicore-log-write`
- `.claude/commands/aicore-checkpoint.md`：`/aicore-checkpoint`
- `.claude/commands/aicore-ledger.md`：`/aicore-ledger`
- `.claude/agents/aicore-guard.md`：流程监督 agent
- `.claude/settings.json`：`PostToolUse` 主动保存提醒 hook

默认 hook 命令使用项目当前约定的 `python3.11` 启动器；如果当前系统使用 Windows 原生 Python Launcher，可以只把 `.claude/settings.json` 里的启动器替换为 `py -3.11`，不要改变 hook 脚本路径和 `aicore` 参数语义。

推荐日常顺序：

1. `/aicore-start`
2. Claude Code 修改文件后，`PostToolUse` hook 会主动提醒运行 `/aicore-save`
3. `/aicore-save` 一次完成 `log-write` 和 `checkpoint`
4. 已批准 plan 或 brief 中的计划项完成并验证通过后，再运行 `/aicore-ledger`

Claude Code 包装层不维护第二套状态，所有事实仍写入 `.aicore/`。
