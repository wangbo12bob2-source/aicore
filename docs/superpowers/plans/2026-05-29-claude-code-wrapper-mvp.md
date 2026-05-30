# Claude Code Wrapper MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal Claude Code project wrapper so Claude Code can follow the existing `aicore` task, history, checkpoint, and ledger workflow through project instructions, slash commands, and one guard agent.

**Architecture:** Keep `aicore` as the only stateful engine. The Claude Code layer is a thin project wrapper: `CLAUDE.md` defines timing rules, `.claude/commands/*.md` document deterministic CLI entrypoints, and `.claude/agents/aicore-guard.md` supervises workflow gaps without maintaining separate state.

**Tech Stack:** Markdown, Claude Code project files, Python 3.11 CLI commands from existing `aicore`

---

## File Structure

### New Files To Create

- Create: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/CLAUDE.md`
  Project-level Claude Code rules that bind Claude Code behavior to the existing `aicore` workflow.
- Create: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/.claude/commands/aicore-start.md`
  Slash command guidance for starting a task with `aicore start`.
- Create: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/.claude/commands/aicore-log-write.md`
  Slash command guidance for recording post-edit events and snapshots.
- Create: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/.claude/commands/aicore-checkpoint.md`
  Slash command guidance for turning one or more events into a checkpoint.
- Create: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/.claude/commands/aicore-ledger.md`
  Slash command guidance for confirming completed system facts into `system-ledger.md`.
- Create: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/.claude/agents/aicore-guard.md`
  Minimal guard agent instructions for supervising missed `aicore` workflow steps.
- Create: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/tests/test_claude_wrapper_files.py`
  Lightweight structural tests that verify the wrapper files exist and reference the correct `aicore` commands.

### Existing Files To Modify

- Modify: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/README.md`
  Add a short Claude Code usage section without duplicating every command body.

## Task 1: Add Project-Level CLAUDE.md

**Files:**
- Create: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/CLAUDE.md`
- Create: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/tests/test_claude_wrapper_files.py`

- [ ] **Step 1: Write the failing structural test**

```python
from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_project_claude_md_binds_claude_code_to_aicore_workflow():
    text = (PROJECT_ROOT / "CLAUDE.md").read_text(encoding="utf-8")

    assert "aicore" in text
    assert "python3.11 -m aicore.cli start" in text
    assert "python3.11 -m aicore.cli log-write" in text
    assert "python3.11 -m aicore.cli checkpoint" in text
    assert "python3.11 -m aicore.cli ledger-confirm" in text
    assert "不维护第二套状态" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3.11 -B -m pytest tests/test_claude_wrapper_files.py::test_project_claude_md_binds_claude_code_to_aicore_workflow -q
```

Expected: FAIL with `FileNotFoundError` for `CLAUDE.md`.

- [ ] **Step 3: Create the minimal project-level CLAUDE.md**

```markdown
# aicore Claude Code 工作流

## 项目规则

- 本项目使用 `aicore` 作为唯一任务、历史和完成态事实源。
- Claude Code 不维护第二套状态，不在 `.claude/` 中记录任务真相。
- 所有对话回答使用中文。
- 修改和设计必须兼容 macOS、Windows、Linux。

## 必须遵守的 aicore 顺序

1. 新任务开始前，先运行：

```bash
python3.11 -m aicore.cli start "<需求>"
```

2. 每轮 Agent 修改文件后，立即运行：

```bash
python3.11 -m aicore.cli log-write <task-id> --session <session-id> --file <path> --summary "<summary>"
```

3. 一轮相关修改达到稳定点后，运行：

```bash
python3.11 -m aicore.cli checkpoint <task-id> --event <event-id> --summary "<summary>"
```

4. 只有当某个变化已确认成为当前系统事实时，才运行：

```bash
python3.11 -m aicore.cli ledger-confirm <task-id> --event <event-id> --capability "<capability>" --entrypoint "<entrypoint>" --limit "<limit>" --compatibility "<compatibility>" --risk "<risk>"
```

## 行为边界

- 不要在未创建或未确认任务边界时直接改代码。
- 不要把临时试验写入 `system-ledger.md`。
- 不要自动批准任务、自动提交 Git 或自动扩大修改范围。
- 如果发现当前能力已经记录在 `.aicore/system-ledger.md`，优先复用或迁移，不要重复开发。
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python3.11 -B -m pytest tests/test_claude_wrapper_files.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md tests/test_claude_wrapper_files.py
git commit -m "feat: add claude code aicore project rules"
```

## Task 2: Add Four Claude Code Commands

**Files:**
- Create: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/.claude/commands/aicore-start.md`
- Create: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/.claude/commands/aicore-log-write.md`
- Create: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/.claude/commands/aicore-checkpoint.md`
- Create: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/.claude/commands/aicore-ledger.md`
- Modify: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/tests/test_claude_wrapper_files.py`

- [ ] **Step 1: Add failing tests for command files**

```python
def test_claude_commands_cover_the_four_aicore_entrypoints():
    commands = {
        "aicore-start.md": "python3.11 -m aicore.cli start",
        "aicore-log-write.md": "python3.11 -m aicore.cli log-write",
        "aicore-checkpoint.md": "python3.11 -m aicore.cli checkpoint",
        "aicore-ledger.md": "python3.11 -m aicore.cli ledger-confirm",
    }

    for filename, command_text in commands.items():
        text = (PROJECT_ROOT / ".claude" / "commands" / filename).read_text(
            encoding="utf-8"
        )
        assert command_text in text
        assert "何时使用" in text
        assert "输出" in text
        assert "不要" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3.11 -B -m pytest tests/test_claude_wrapper_files.py::test_claude_commands_cover_the_four_aicore_entrypoints -q
```

Expected: FAIL with `FileNotFoundError` for the first missing command file.

- [ ] **Step 3: Create `.claude/commands/aicore-start.md`**

```markdown
# /aicore-start

## 何时使用

在开始任何新的实现、修复、迁移或重构任务前使用。

## 执行动作

```bash
python3.11 -m aicore.cli start "<需求>"
```

## 输出

- 记录生成的 `task-id`
- 提醒用户查看 `.aicore/tasks/<task-id>/brief.md`
- 明确当前仍处于任务启动阶段

## 不要

- 不要在未生成任务草案前直接修改代码
- 不要在此命令中顺手执行实现
- 不要自动 approve
```

- [ ] **Step 4: Create `.claude/commands/aicore-log-write.md`**

```markdown
# /aicore-log-write

## 何时使用

在 Agent 完成一轮文件修改后立即使用。

## 执行动作

```bash
python3.11 -m aicore.cli log-write <task-id> --session <session-id> --file <path> --summary "<summary>"
```

可为多个文件重复传入 `--file`。

## 输出

- 第一行是 `event-id`
- 第二行是事件文件路径
- 提醒用户保留 `event-id`，后续 checkpoint 和 ledger 会引用它

## 不要

- 不要把未修改的文件写入事件
- 不要把临时失败试验当成完成态事实
- 不要在此命令中自动写 ledger
```

- [ ] **Step 5: Create `.claude/commands/aicore-checkpoint.md`**

```markdown
# /aicore-checkpoint

## 何时使用

在一轮相关修改达到稳定点后使用，例如测试通过、迁移阶段完成、或一个可恢复里程碑出现时。

## 执行动作

```bash
python3.11 -m aicore.cli checkpoint <task-id> --event <event-id> --summary "<summary>"
```

可为多个事件重复传入 `--event`。

## 输出

- 第一行是 `checkpoint-id`
- 第二行是 checkpoint manifest 路径

## 不要

- 不要引用不存在的 event
- 不要跨 task 混用 event
- 不要把 checkpoint 当作完成态账本
```

- [ ] **Step 6: Create `.claude/commands/aicore-ledger.md`**

```markdown
# /aicore-ledger

## 何时使用

只有当用户或验证结果确认某个变化已经成为当前系统事实时使用。

## 执行动作

```bash
python3.11 -m aicore.cli ledger-confirm <task-id> --event <event-id> --capability "<capability>" --entrypoint "<entrypoint>" --limit "<limit>" --compatibility "<compatibility>" --risk "<risk>"
```

## 输出

- `.aicore/system-ledger.md`
- 简要说明新增的完成态事实

## 不要

- 不要记录临时试验
- 不要记录尚未验证生效的推测
- 不要使用多行字段污染账本结构
```

- [ ] **Step 7: Run command tests**

Run:

```bash
python3.11 -B -m pytest tests/test_claude_wrapper_files.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add .claude/commands tests/test_claude_wrapper_files.py
git commit -m "feat: add claude code aicore commands"
```

## Task 3: Add Minimal aicore Guard Agent

**Files:**
- Create: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/.claude/agents/aicore-guard.md`
- Modify: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/tests/test_claude_wrapper_files.py`

- [ ] **Step 1: Add failing test for guard agent**

```python
def test_aicore_guard_agent_is_supervisory_not_autonomous():
    text = (PROJECT_ROOT / ".claude" / "agents" / "aicore-guard.md").read_text(
        encoding="utf-8"
    )

    assert "流程监督" in text
    assert "python3.11 -m aicore.cli" in text
    assert "不自动批准" in text
    assert "不维护第二套状态" in text
    assert "system-ledger.md" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3.11 -B -m pytest tests/test_claude_wrapper_files.py::test_aicore_guard_agent_is_supervisory_not_autonomous -q
```

Expected: FAIL with `FileNotFoundError` for `.claude/agents/aicore-guard.md`.

- [ ] **Step 3: Create `.claude/agents/aicore-guard.md`**

```markdown
---
name: aicore-guard
description: Use to supervise whether Claude Code is following the project aicore workflow: task start, post-edit history logging, checkpointing, and confirmed system ledger updates.
---

# aicore Guard

## 角色定位

你是 `aicore` 流程监督员，负责提醒 Claude Code 是否漏掉关键流程动作。

你辅助组织命令参数，但不维护第二套状态；项目事实只写入 `.aicore/`。

## 检查顺序

1. 如果当前任务还没有 task-id，提醒先运行：

```bash
python3.11 -m aicore.cli start "<需求>"
```

2. 如果本轮已经修改文件但还没有 event-id，提醒运行：

```bash
python3.11 -m aicore.cli log-write <task-id> --session <session-id> --file <path> --summary "<summary>"
```

3. 如果一组 event 已经达到稳定点，建议运行：

```bash
python3.11 -m aicore.cli checkpoint <task-id> --event <event-id> --summary "<summary>"
```

4. 如果某项能力已确认成为当前系统事实，建议运行：

```bash
python3.11 -m aicore.cli ledger-confirm <task-id> --event <event-id> --capability "<capability>" --entrypoint "<entrypoint>" --limit "<limit>" --compatibility "<compatibility>" --risk "<risk>"
```

## 禁止事项

- 不自动批准任务。
- 不自动提交 Git。
- 不自行扩大修改范围。
- 不把临时试验写入 `system-ledger.md`。
- 不维护第二套状态。
```

- [ ] **Step 4: Run tests**

Run:

```bash
python3.11 -B -m pytest tests/test_claude_wrapper_files.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .claude/agents/aicore-guard.md tests/test_claude_wrapper_files.py
git commit -m "feat: add claude code aicore guard agent"
```

## Task 4: Document Claude Code Usage And Verify

**Files:**
- Modify: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/README.md`
- Test: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/tests/test_claude_wrapper_files.py`

- [ ] **Step 1: Add failing README test**

```python
def test_readme_mentions_claude_code_wrapper_entrypoints():
    text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "Claude Code" in text
    assert "/aicore-start" in text
    assert "/aicore-log-write" in text
    assert "/aicore-checkpoint" in text
    assert "/aicore-ledger" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3.11 -B -m pytest tests/test_claude_wrapper_files.py::test_readme_mentions_claude_code_wrapper_entrypoints -q
```

Expected: FAIL because README does not yet mention Claude Code wrapper commands.

- [ ] **Step 3: Update README with a concise Claude Code section**

```markdown
## Claude Code 包装层

本项目提供项目级 Claude Code 包装层：

- `CLAUDE.md`：项目级 `aicore` 工作流规则
- `.claude/commands/aicore-start.md`：`/aicore-start`
- `.claude/commands/aicore-log-write.md`：`/aicore-log-write`
- `.claude/commands/aicore-checkpoint.md`：`/aicore-checkpoint`
- `.claude/commands/aicore-ledger.md`：`/aicore-ledger`
- `.claude/agents/aicore-guard.md`：流程监督 agent

推荐日常顺序：

1. `/aicore-start`
2. `/aicore-log-write`
3. `/aicore-checkpoint`
4. `/aicore-ledger`

Claude Code 包装层不维护第二套状态，所有事实仍写入 `.aicore/`。
```

- [ ] **Step 4: Run wrapper tests**

Run:

```bash
python3.11 -B -m pytest tests/test_claude_wrapper_files.py -q
```

Expected: PASS.

- [ ] **Step 5: Run full test suite**

Run:

```bash
python3.11 -B -m pytest -q
```

Expected: PASS.

- [ ] **Step 6: Manual structural verification**

Run:

```bash
find . -maxdepth 3 \( -name 'CLAUDE.md' -o -path './.claude/*' \) | sort
```

Expected output includes:

```text
./.claude/agents/aicore-guard.md
./.claude/commands/aicore-checkpoint.md
./.claude/commands/aicore-ledger.md
./.claude/commands/aicore-log-write.md
./.claude/commands/aicore-start.md
./CLAUDE.md
```

- [ ] **Step 7: Commit**

```bash
git add README.md tests/test_claude_wrapper_files.py CLAUDE.md .claude
git commit -m "docs: describe claude code aicore wrapper"
```

## Self-Review

- Spec coverage:
  - `CLAUDE.md` project rules: Task 1.
  - Four commands under `.claude/commands`: Task 2.
  - One supervisory guard agent: Task 3.
  - README usage and structural verification: Task 4.
  - No second state source: asserted in `CLAUDE.md`, guard agent, and tests.
- Placeholder scan:
  - The plan contains shell examples with angle-bracket placeholders because these are literal user-facing command templates in Markdown command files. They are not unfinished implementation placeholders.
  - No `TODO`, `TBD`, or unspecified implementation steps remain.
- Type consistency:
  - Command file names match spec: `aicore-start.md`, `aicore-log-write.md`, `aicore-checkpoint.md`, `aicore-ledger.md`.
  - Agent file name matches spec: `aicore-guard.md`.
  - CLI commands match existing `aicore.cli`: `start`, `log-write`, `checkpoint`, `ledger-confirm`.
