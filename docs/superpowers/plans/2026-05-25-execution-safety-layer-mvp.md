# Execution Safety Layer MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为现有 `aicore` 任务启动器补上最小执行安全层：Agent 写文件即留痕、可显式生成 checkpoint、人工确认后更新系统完成态账本。

**Architecture:** 在现有 `task_service + task_store + cli` 之上新增一条独立的数据链路。`history_store` 负责事件、快照和 checkpoint 持久化；`ledger_service` 负责把人工确认后的系统事实写入 `.aicore/system-ledger.md`；CLI 只增加最小命令面，不改变既有任务状态机语义。

**Tech Stack:** Python 3.11, argparse, pathlib, PyYAML, pytest

---

## File Structure

### Existing Files To Modify

- Modify: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/src/aicore/cli.py`
  Add `log-write`, `checkpoint`, `ledger-confirm` subcommands and consistent terminal output.
- Modify: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/src/aicore/task_views.py`
  Add helper rendering for ledger confirmation output if needed, without polluting existing task brief rendering.
- Modify: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/README.md`
  Document the new safety workflow and cross-platform commands.
- Modify: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/tests/test_cli_smoke.py`
  Expose the new subcommands in parser help text.

### New Files To Create

- Create: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/src/aicore/history_store.py`
  Store event files, file snapshots, and checkpoint manifests under `.aicore/history/`.
- Create: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/src/aicore/history_service.py`
  Validate inputs and orchestrate `log-write` / `checkpoint` flows.
- Create: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/src/aicore/ledger_service.py`
  Create and update `.aicore/system-ledger.md` from confirmed facts.
- Create: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/tests/test_history_commands.py`
  Cover event creation, snapshot persistence, and checkpoint behavior.
- Create: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/tests/test_ledger_commands.py`
  Cover ledger file creation, append semantics, and event/checkpoint references.

## Task 1: Add History Store Primitives

**Files:**
- Create: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/src/aicore/history_store.py`
- Test: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/tests/test_history_commands.py`

- [ ] **Step 1: Write the failing tests for event and snapshot persistence**

```python
from __future__ import annotations

import json
from pathlib import Path

from aicore.history_service import log_write


def test_log_write_persists_event_and_snapshots(workspace: Path):
    source_file = workspace / "src" / "auth" / "login.ts"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("export const login = 'ok';\n", encoding="utf-8")

    result = log_write(
        cwd=workspace,
        task_id="task-2026-05-25-001",
        session_id="session-1",
        files=["src/auth/login.ts"],
        summary="记录登录文件改动",
    )

    assert result["event"]["task_id"] == "task-2026-05-25-001"
    assert result["event"]["kind"] == "file_write"
    assert len(result["event"]["files"]) == 1

    event_path = workspace / result["event_path"]
    snapshot_path = workspace / result["event"]["files"][0]["snapshot_path"]

    assert event_path.exists()
    assert snapshot_path.exists()
    assert snapshot_path.read_text(encoding="utf-8") == "export const login = 'ok';\n"


def test_log_write_rejects_missing_files(workspace: Path):
    try:
        log_write(
            cwd=workspace,
            task_id="task-2026-05-25-001",
            session_id="session-1",
            files=["src/auth/missing.ts"],
            summary="文件不存在",
        )
    except FileNotFoundError as exc:
        assert "src/auth/missing.ts" in str(exc)
    else:
        raise AssertionError("expected FileNotFoundError")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3.11 -B -m pytest tests/test_history_commands.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'aicore.history_service'`

- [ ] **Step 3: Write the minimal history storage implementation**

```python
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import shutil


def history_root(cwd: Path) -> Path:
    return cwd / ".aicore" / "history"


def _sanitize_relative_path(path_text: str) -> str:
    return path_text.replace("\\", "__").replace("/", "__")


def create_event_record(
    cwd: Path,
    task_id: str,
    session_id: str,
    files: list[str],
    summary: str,
) -> dict:
    timestamp = datetime.now(timezone.utc)
    event_id = f"event-{timestamp.strftime('%Y%m%d%H%M%S')}"
    event_files = []

    for relative_path in files:
        source = cwd / relative_path
        if not source.exists():
            raise FileNotFoundError(relative_path)
        snapshot_dir = history_root(cwd) / "snapshots" / task_id / event_id
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_file = snapshot_dir / _sanitize_relative_path(relative_path)
        shutil.copy2(source, snapshot_file)
        event_files.append(
            {
                "path": relative_path,
                "change_type": "modified",
                "snapshot_path": str(snapshot_file.relative_to(cwd)),
            }
        )

    event = {
        "event_id": event_id,
        "task_id": task_id,
        "session_id": session_id,
        "timestamp": timestamp.isoformat(),
        "kind": "file_write",
        "files": event_files,
        "summary": summary,
    }
    events_dir = history_root(cwd) / "events"
    events_dir.mkdir(parents=True, exist_ok=True)
    event_path = events_dir / f"{event_id}.json"
    event_path.write_text(json.dumps(event, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"event": event, "event_path": str(event_path.relative_to(cwd))}
```

- [ ] **Step 4: Add the thin service wrapper**

```python
from __future__ import annotations

from pathlib import Path

from aicore.history_store import create_event_record


def log_write(
    cwd: Path,
    task_id: str,
    session_id: str,
    files: list[str],
    summary: str,
) -> dict:
    if not files:
        raise ValueError("files 不能为空")
    if not summary.strip():
        raise ValueError("summary 不能为空")
    return create_event_record(
        cwd=cwd,
        task_id=task_id,
        session_id=session_id,
        files=files,
        summary=summary.strip(),
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```bash
python3.11 -B -m pytest tests/test_history_commands.py -q
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/aicore/history_store.py src/aicore/history_service.py tests/test_history_commands.py
git commit -m "feat: add event and snapshot history storage"
```

## Task 2: Add Checkpoint Persistence

**Files:**
- Modify: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/src/aicore/history_store.py`
- Modify: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/src/aicore/history_service.py`
- Modify: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/tests/test_history_commands.py`

- [ ] **Step 1: Extend tests with checkpoint coverage**

```python
import json

from aicore.history_service import create_checkpoint, log_write


def test_create_checkpoint_writes_manifest_with_event_references(workspace: Path):
    source_file = workspace / "src" / "auth" / "login.ts"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("export const login = 'ok';\n", encoding="utf-8")

    event_result = log_write(
        cwd=workspace,
        task_id="task-2026-05-25-001",
        session_id="session-1",
        files=["src/auth/login.ts"],
        summary="记录登录文件改动",
    )

    checkpoint = create_checkpoint(
        cwd=workspace,
        task_id="task-2026-05-25-001",
        event_ids=[event_result["event"]["event_id"]],
        summary="登录逻辑达到阶段稳定点",
    )

    manifest_path = workspace / checkpoint["manifest_path"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert checkpoint["checkpoint_id"].startswith("checkpoint-")
    assert manifest["task_id"] == "task-2026-05-25-001"
    assert manifest["event_ids"] == [event_result["event"]["event_id"]]
    assert manifest["summary"] == "登录逻辑达到阶段稳定点"
```

- [ ] **Step 2: Run the focused tests to verify failure**

Run:

```bash
python3.11 -B -m pytest tests/test_history_commands.py::test_create_checkpoint_writes_manifest_with_event_references -q
```

Expected: FAIL with `ImportError` or `AttributeError` for `create_checkpoint`

- [ ] **Step 3: Implement checkpoint storage in the history layer**

```python
def create_checkpoint_manifest(
    cwd: Path,
    task_id: str,
    event_ids: list[str],
    summary: str,
) -> dict:
    timestamp = datetime.now(timezone.utc)
    checkpoint_id = f"checkpoint-{timestamp.strftime('%Y%m%d%H%M%S')}"
    checkpoint_dir = history_root(cwd) / "checkpoints" / task_id / checkpoint_id
    checkpoint_dir.mkdir(parents=True, exist_ok=False)
    manifest = {
        "checkpoint_id": checkpoint_id,
        "task_id": task_id,
        "timestamp": timestamp.isoformat(),
        "event_ids": event_ids,
        "summary": summary,
    }
    manifest_path = checkpoint_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {
        "checkpoint_id": checkpoint_id,
        "manifest_path": str(manifest_path.relative_to(cwd)),
    }
```

- [ ] **Step 4: Add the service validation wrapper**

```python
def create_checkpoint(
    cwd: Path,
    task_id: str,
    event_ids: list[str],
    summary: str,
) -> dict:
    if not event_ids:
        raise ValueError("event_ids 不能为空")
    if not summary.strip():
        raise ValueError("summary 不能为空")
    return create_checkpoint_manifest(
        cwd=cwd,
        task_id=task_id,
        event_ids=event_ids,
        summary=summary.strip(),
    )
```

- [ ] **Step 5: Run history tests**

Run:

```bash
python3.11 -B -m pytest tests/test_history_commands.py -q
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/aicore/history_store.py src/aicore/history_service.py tests/test_history_commands.py
git commit -m "feat: add task checkpoint manifests"
```

## Task 3: Add System Ledger Service

**Files:**
- Create: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/src/aicore/ledger_service.py`
- Create: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/tests/test_ledger_commands.py`

- [ ] **Step 1: Write the failing tests for ledger creation and append**

```python
from __future__ import annotations

from pathlib import Path

from aicore.ledger_service import confirm_ledger_entry


def test_confirm_ledger_entry_creates_system_ledger(workspace: Path):
    result = confirm_ledger_entry(
        cwd=workspace,
        task_id="task-2026-05-25-001",
        event_ref="event-001",
        capability="支持 JWT 登录",
        entrypoint="API: POST /auth/login",
        limit="暂不支持 refresh token",
        compatibility="支持 macOS / Windows / Linux",
        risk="异常路径回归待补齐",
    )

    ledger_path = workspace / result["ledger_path"]
    text = ledger_path.read_text(encoding="utf-8")

    assert ledger_path.exists()
    assert "## Current Capabilities" in text
    assert "- 支持 JWT 登录" in text
    assert "来源: task-2026-05-25-001 / event-001" in text


def test_confirm_ledger_entry_appends_instead_of_overwriting(workspace: Path):
    confirm_ledger_entry(
        cwd=workspace,
        task_id="task-2026-05-25-001",
        event_ref="event-001",
        capability="支持 JWT 登录",
        entrypoint="API: POST /auth/login",
        limit="暂不支持 refresh token",
        compatibility="支持 macOS / Windows / Linux",
        risk="异常路径回归待补齐",
    )
    confirm_ledger_entry(
        cwd=workspace,
        task_id="task-2026-05-25-002",
        event_ref="checkpoint-001",
        capability="支持管理员审核",
        entrypoint="CLI: aicore approve",
        limit="仅管理员可用",
        compatibility="不依赖系统专属路径",
        risk="角色边界待补测试",
    )

    ledger = (workspace / ".aicore" / "system-ledger.md").read_text(encoding="utf-8")
    assert ledger.count("## Current Capabilities") == 1
    assert "- 支持 JWT 登录" in ledger
    assert "- 支持管理员审核" in ledger
```

- [ ] **Step 2: Run the ledger tests to verify failure**

Run:

```bash
python3.11 -B -m pytest tests/test_ledger_commands.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'aicore.ledger_service'`

- [ ] **Step 3: Implement minimal ledger writing**

```python
from __future__ import annotations

from pathlib import Path


LEDGER_HEADER = """# System Ledger

## Current Capabilities

## Entrypoints

## Limits And Boundaries

## Compatibility

## Known Risks
"""


def confirm_ledger_entry(
    cwd: Path,
    task_id: str,
    event_ref: str,
    capability: str,
    entrypoint: str,
    limit: str,
    compatibility: str,
    risk: str,
) -> dict:
    ledger_path = cwd / ".aicore" / "system-ledger.md"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    if not ledger_path.exists():
        ledger_path.write_text(LEDGER_HEADER, encoding="utf-8")

    text = ledger_path.read_text(encoding="utf-8")
    source_line = f"来源: {task_id} / {event_ref}"
    sections = {
        "## Current Capabilities": f"- {capability}\n  - {source_line}\n",
        "## Entrypoints": f"- {entrypoint}\n  - {source_line}\n",
        "## Limits And Boundaries": f"- {limit}\n  - {source_line}\n",
        "## Compatibility": f"- {compatibility}\n  - {source_line}\n",
        "## Known Risks": f"- {risk}\n  - {source_line}\n",
    }

    for marker, block in sections.items():
        text = text.replace(marker, f"{marker}\n{block}", 1)

    ledger_path.write_text(text, encoding="utf-8")
    return {"ledger_path": str(ledger_path.relative_to(cwd))}
```

- [ ] **Step 4: Run ledger tests to verify pass**

Run:

```bash
python3.11 -B -m pytest tests/test_ledger_commands.py -q
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/aicore/ledger_service.py tests/test_ledger_commands.py
git commit -m "feat: add system ledger confirmation flow"
```

## Task 4: Expose Safety Commands Through the CLI

**Files:**
- Modify: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/src/aicore/cli.py`
- Modify: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/tests/test_cli_smoke.py`
- Modify: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/tests/test_history_commands.py`
- Modify: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/tests/test_ledger_commands.py`

- [ ] **Step 1: Add failing CLI tests**

```python
from aicore.cli import build_parser, main


def test_build_parser_exposes_safety_commands():
    parser = build_parser()
    help_text = parser.format_help()
    assert "log-write" in help_text
    assert "checkpoint" in help_text
    assert "ledger-confirm" in help_text
```

```python
def test_log_write_command_creates_event_and_snapshot(workspace: Path):
    source_file = workspace / "src" / "auth" / "login.ts"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("export const login = 'ok';\n", encoding="utf-8")

    exit_code = main(
        [
            "log-write",
            "--task-id",
            "task-2026-05-25-001",
            "--session-id",
            "session-1",
            "--file",
            "src/auth/login.ts",
            "--summary",
            "记录登录修改",
        ]
    )

    assert exit_code == 0
    assert any((workspace / ".aicore" / "history" / "events").iterdir())
```

- [ ] **Step 2: Run the focused CLI tests to verify failure**

Run:

```bash
python3.11 -B -m pytest tests/test_cli_smoke.py::test_build_parser_exposes_safety_commands -q
```

Expected: FAIL because the new subcommands are not yet registered

- [ ] **Step 3: Extend the parser and command execution**

```python
log_write_parser = subparsers.add_parser("log-write")
log_write_parser.add_argument("--task-id", required=True)
log_write_parser.add_argument("--session-id", required=True)
log_write_parser.add_argument("--file", dest="files", action="append", required=True)
log_write_parser.add_argument("--summary", required=True)

checkpoint_parser = subparsers.add_parser("checkpoint")
checkpoint_parser.add_argument("--task-id", required=True)
checkpoint_parser.add_argument("--event-id", dest="event_ids", action="append", required=True)
checkpoint_parser.add_argument("--summary", required=True)

ledger_parser = subparsers.add_parser("ledger-confirm")
ledger_parser.add_argument("--task-id", required=True)
ledger_parser.add_argument("--event-ref", required=True)
ledger_parser.add_argument("--capability", required=True)
ledger_parser.add_argument("--entrypoint", required=True)
ledger_parser.add_argument("--limit", required=True)
ledger_parser.add_argument("--compatibility", required=True)
ledger_parser.add_argument("--risk", required=True)
```

```python
if args.command == "log-write":
    result = log_write(
        cwd=Path.cwd(),
        task_id=args.task_id,
        session_id=args.session_id,
        files=args.files,
        summary=args.summary,
    )
    print(result["event"]["event_id"])
    print(result["event_path"])
    return 0
```

```python
if args.command == "checkpoint":
    result = create_checkpoint(
        cwd=Path.cwd(),
        task_id=args.task_id,
        event_ids=args.event_ids,
        summary=args.summary,
    )
    print(result["checkpoint_id"])
    print(result["manifest_path"])
    return 0
```

```python
if args.command == "ledger-confirm":
    result = confirm_ledger_entry(
        cwd=Path.cwd(),
        task_id=args.task_id,
        event_ref=args.event_ref,
        capability=args.capability,
        entrypoint=args.entrypoint,
        limit=args.limit,
        compatibility=args.compatibility,
        risk=args.risk,
    )
    print(result["ledger_path"])
    return 0
```

- [ ] **Step 4: Run the smoke and command tests**

Run:

```bash
python3.11 -B -m pytest tests/test_cli_smoke.py tests/test_history_commands.py tests/test_ledger_commands.py -q
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/aicore/cli.py tests/test_cli_smoke.py tests/test_history_commands.py tests/test_ledger_commands.py
git commit -m "feat: expose execution safety commands"
```

## Task 5: Update Docs And Run Full Verification

**Files:**
- Modify: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/README.md`
- Test: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/tests/test_start_command.py`
- Test: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/tests/test_state_commands.py`
- Test: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/tests/test_supersedes_flow.py`
- Test: `/Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding/tests/test_task_store.py`

- [ ] **Step 1: Update README with the new safety workflow**

```md
## 执行安全层

### 1. 记录 Agent 写入

macOS/Linux:

```bash
python3.11 -m aicore.cli log-write \
  --task-id task-2026-05-25-001 \
  --session-id session-1 \
  --file src/auth/login.ts \
  --summary "记录登录逻辑改动"
```

Windows PowerShell:

```powershell
py -3.11 -m aicore.cli log-write `
  --task-id task-2026-05-25-001 `
  --session-id session-1 `
  --file src/auth/login.ts `
  --summary "记录登录逻辑改动"
```

### 2. 生成阶段 checkpoint

### 3. 确认完成态并更新账本
```

- [ ] **Step 2: Run the full test suite**

Run:

```bash
python3.11 -B -m pytest -q
```

Expected: PASS

- [ ] **Step 3: Perform a manual smoke workflow**

Run:

```bash
python3.11 -m aicore.cli start "实现 JWT 登录"
python3.11 -m aicore.cli log-write --task-id task-2026-05-25-001 --session-id session-1 --file README.md --summary "记录示例修改"
python3.11 -m aicore.cli checkpoint --task-id task-2026-05-25-001 --event-id event-PLACEHOLDER --summary "示例阶段完成"
python3.11 -m aicore.cli ledger-confirm --task-id task-2026-05-25-001 --event-ref event-PLACEHOLDER --capability "支持 JWT 登录" --entrypoint "API: POST /auth/login" --limit "暂不支持 refresh token" --compatibility "支持 macOS / Windows / Linux" --risk "异常路径回归待补齐"
```

Expected:

- `.aicore/history/events/` 下出现事件文件
- `.aicore/history/snapshots/` 下出现快照文件
- `.aicore/history/checkpoints/` 下出现 manifest
- `.aicore/system-ledger.md` 被创建并包含能力条目

- [ ] **Step 4: Replace the smoke placeholders with real IDs after running the first command**

Use the actual `event_id` printed by `log-write` in both `checkpoint` and `ledger-confirm`, then re-run those two commands. Record the real example in `README.md` if the final wording changes.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: describe execution safety workflow"
```

## Self-Review

- Spec coverage:
  - 任务启动器保持不变，仅扩展安全层：Task 4 and Task 5 avoid touching `task_service` state semantics.
  - Agent 写入即留痕：Task 1 implements event + snapshot flow.
  - 阶段 checkpoint：Task 2 implements checkpoint manifests.
  - 完成态账本：Task 3 implements `system-ledger.md`.
  - CLI 最小命令面：Task 4 exposes `log-write`, `checkpoint`, `ledger-confirm`.
  - 跨平台说明：Task 5 updates README with macOS/Linux and Windows PowerShell commands.
- Placeholder scan:
  - The only intentional placeholders are `event-PLACEHOLDER` in the manual smoke workflow, and Step 4 explicitly requires replacing them with real runtime IDs before considering the task done.
  - No `TODO` / `TBD` / “implement later” placeholders remain in code tasks.
- Type consistency:
  - Service names are `log_write`, `create_checkpoint`, `confirm_ledger_entry`.
  - CLI command names are `log-write`, `checkpoint`, `ledger-confirm`.
  - Storage folders are consistently `.aicore/history/events`, `.aicore/history/snapshots`, `.aicore/history/checkpoints`, and `.aicore/system-ledger.md`.
