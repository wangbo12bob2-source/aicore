# SOP Executor Task Launcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a cross-platform MVP CLI that turns one natural-language request into a reviewable task package, then enforces `review/approve/reject/supersede` state changes through `task.yaml` and `brief.md`.

**Architecture:** The implementation uses a small Python package with one CLI entrypoint and three focused units: draft building, filesystem persistence/rendering, and state-transition orchestration. `task.yaml` remains the single source of truth; `brief.md` is always re-rendered from it after every state-changing command.

**Tech Stack:** Python 3.11+, `argparse`, `pathlib`, `datetime`, `PyYAML`, `pytest`

**Assumption:** The repository currently has no existing runtime scaffold, so this plan intentionally chooses Python for the first cross-platform CLI implementation. Commit steps are deferred until the project has its own isolated Git root or worktree, because the current Git top-level is `/Users/dong1`.

---

## Planned File Map

- `pyproject.toml`
  Defines the package metadata, console script, and test dependencies.
- `README.md`
  Documents local setup, CLI usage, and current MVP constraints.
- `src/aicore/__init__.py`
  Marks the package root.
- `src/aicore/cli.py`
  Parses CLI arguments and dispatches `start/review/approve/reject`.
- `src/aicore/draft_builder.py`
  Builds the initial task object from the raw request and lightweight heuristics.
- `src/aicore/task_store.py`
  Handles task ID generation, YAML read/write, and `brief.md` rendering.
- `src/aicore/state_machine.py`
  Validates legal state transitions.
- `src/aicore/task_service.py`
  Orchestrates command behavior across builder, store, and state machine.
- `tests/conftest.py`
  Shared test helpers for isolated working directories and YAML loading.
- `tests/test_cli_smoke.py`
  Proves the CLI bootstraps and prints help.
- `tests/test_start_command.py`
  Covers `start`, initial task structure, and draft rendering.
- `tests/test_state_commands.py`
  Covers `review`, `approve`, `reject`, illegal transitions, and brief re-rendering.
- `tests/test_supersedes_flow.py`
  Covers `--supersedes` and the atomic approval path that marks the old task as `superseded`.

## Implementation Notes

- Use `pathlib.Path` everywhere. Do not concatenate path strings manually.
- Use UTF-8 reads/writes explicitly.
- Keep task generation rule-based; do not add model routing or AI calls in this MVP.
- Prefer terminal prompts in output text over interactive question loops; the spec only requires explicit human confirmation before moving forward, not inline wizard UX.

### Task 1: Bootstrap the Python CLI Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/aicore/__init__.py`
- Create: `src/aicore/cli.py`
- Create: `tests/conftest.py`
- Create: `tests/test_cli_smoke.py`

- [ ] **Step 1: Write the failing smoke test**

```python
# tests/test_cli_smoke.py
from aicore.cli import build_parser, main


def test_build_parser_exposes_all_mvp_commands():
    parser = build_parser()
    command_names = set(parser._subparsers._group_actions[0].choices.keys())
    assert command_names == {"start", "review", "approve", "reject"}


def test_main_without_args_prints_help_and_returns_zero(capsys):
    exit_code = main([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "start" in captured.out
    assert "approve" in captured.out
```

- [ ] **Step 2: Run the smoke test to verify it fails**

Run: `cd /Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding && PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' python3.11 -m pytest tests/test_cli_smoke.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'aicore'`

- [ ] **Step 3: Add the minimal package and CLI scaffold**

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "aicore"
version = "0.1.0"
description = "Cross-platform SOP task launcher MVP"
readme = "README.md"
requires-python = ">=3.11"
dependencies = ["PyYAML>=6.0"]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[project.scripts]
aicore = "aicore.cli:main"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
```

```markdown
# README.md

## MVP Scope

- `aicore start "<request>"`
- `aicore review <task-id>`
- `aicore approve <task-id> --by "<name>"`
- `aicore reject <task-id> --reason "<reason>"`

The CLI writes task files under `.aicore/tasks/`.
```

```python
# src/aicore/__init__.py
__all__ = ["__version__"]

__version__ = "0.1.0"
```

```python
# src/aicore/cli.py
from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aicore")
    subparsers = parser.add_subparsers(dest="command")

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("request")
    start_parser.add_argument("--supersedes")

    review_parser = subparsers.add_parser("review")
    review_parser.add_argument("task_id")

    approve_parser = subparsers.add_parser("approve")
    approve_parser.add_argument("task_id")
    approve_parser.add_argument("--by", required=True)

    reject_parser = subparsers.add_parser("reject")
    reject_parser.add_argument("task_id")
    reject_parser.add_argument("--reason", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    raise SystemExit("Command wiring is added in later tasks")
```

```python
# tests/conftest.py
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path
```

- [ ] **Step 4: Run the smoke test to verify it passes**

Run: `cd /Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding && PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' python3.11 -m pytest tests/test_cli_smoke.py -q`
Expected: `2 passed`

- [ ] **Step 5: Record a checkpoint instead of committing**

Run: `cd /Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding && git rev-parse --show-toplevel`
Expected: output is still `/Users/dong1`, so do **not** commit yet; note the checkpoint in your execution log.

### Task 2: Implement `start` and Render the Initial Task Package

**Files:**
- Modify: `src/aicore/cli.py`
- Create: `src/aicore/draft_builder.py`
- Create: `src/aicore/task_store.py`
- Create: `src/aicore/task_service.py`
- Create: `tests/test_start_command.py`

- [ ] **Step 1: Write the failing `start` tests**

```python
# tests/test_start_command.py
from __future__ import annotations

from pathlib import Path

import yaml

from aicore.cli import main


def test_start_creates_task_yaml_and_brief(workspace: Path):
    exit_code = main(["start", "实现 JWT 登录"])

    task_dir = workspace / ".aicore" / "tasks" / "task-2099-01-01-001"
    task_file = task_dir / "task.yaml"
    brief_file = task_dir / "brief.md"

    assert exit_code == 0
    assert task_file.exists()
    assert brief_file.exists()

    data = yaml.safe_load(task_file.read_text(encoding="utf-8"))
    assert data["status"] == "draft"
    assert data["request"]["raw"] == "实现 JWT 登录"
    assert data["project"]["type"] == "product-delivery"
    assert data["scope"]["module"] == "auth-login"
    assert data["history"]["supersedes"] is None
    assert "待确认" in brief_file.read_text(encoding="utf-8")


def test_start_records_supersedes_reference(workspace: Path):
    exit_code = main(
        [
            "start",
            "补充 JWT refresh token 约束",
            "--supersedes",
            "task-2099-01-01-001",
        ]
    )

    task_file = workspace / ".aicore" / "tasks" / "task-2099-01-01-001" / "task.yaml"
    data = yaml.safe_load(task_file.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert data["history"]["supersedes"] == "task-2099-01-01-001"


def test_start_rejects_broad_multi_system_request(workspace: Path):
    exit_code = main(["start", "同时重写聊天、支付、文件存储和报表系统"])
    assert exit_code == 2
```

- [ ] **Step 2: Run the `start` tests to verify they fail**

Run: `cd /Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding && PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' python3.11 -m pytest tests/test_start_command.py -q`
Expected: FAIL because `start` has no implementation yet

- [ ] **Step 3: Implement the draft builder, store, and `start` service**

```python
# src/aicore/draft_builder.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


MULTI_SYSTEM_MARKERS = ("同时", "以及", "并且", "支付", "报表", "文件存储")


@dataclass(frozen=True)
class DraftContext:
    request: str
    task_id: str
    now: datetime
    cwd: Path
    supersedes: str | None = None


def infer_project_type(request: str) -> str:
    if any(marker in request for marker in ("逆向", "还原", "反编译")):
        return "reverse-engineering"
    if any(marker in request for marker in ("迁移", "桥接", "替代旧系统")):
        return "hybrid-migration"
    return "product-delivery"


def infer_module_name(request: str) -> str:
    lowered = request.lower()
    if "jwt" in lowered or "登录" in request or "auth" in lowered:
        return "auth-login"
    if "支付" in request:
        return "payment"
    return "module-pending-confirmation"


def validate_request_scope(request: str) -> None:
    if sum(marker in request for marker in MULTI_SYSTEM_MARKERS) >= 3:
        raise ValueError("需求范围过大，包含多个独立子系统，请先拆分。")


def build_draft(context: DraftContext) -> dict:
    validate_request_scope(context.request)
    project_type = infer_project_type(context.request)
    module_name = infer_module_name(context.request)
    now_text = context.now.isoformat()

    return {
        "id": context.task_id,
        "version": 1,
        "status": "draft",
        "request": {"raw": context.request},
        "project": {"type": project_type},
        "scope": {
            "module": module_name,
            "goal": context.request,
            "in_scope": ["待从需求中确认的核心动作"],
            "out_of_scope": ["未在当前请求中明确提出的扩展能力"],
        },
        "entrypoints": {"main": [], "compat": []},
        "implementation": {
            "dual_write_required": False,
            "dual_write_reason": "待确认是否存在兼容入口或双实现。",
        },
        "change_scope": {"allowed_files": [], "protected_areas": []},
        "constraints": {
            "platform": ["macos", "windows", "linux"],
            "rules": [
                "所有对话回答使用中文",
                "不硬编码路径分隔符、系统路径、权限、可执行后缀",
                "只做必要修改",
                "不要顺手重构无关代码",
                "遵循现有代码风格",
                "先读后写",
                "人工确认前不得进入下一步",
            ],
        },
        "acceptance": {
            "success_criteria": ["待补充验收标准"],
            "baseline_refs": [],
        },
        "context": {
            "related_files": [],
            "related_modules": [],
            "assumptions": [],
            "risks": [],
            "rollback_plan": "",
        },
        "review": {
            "summary": "",
            "approved_by": None,
            "approved_at": None,
            "rejected_reason": None,
        },
        "history": {
            "created_at": now_text,
            "updated_at": now_text,
            "supersedes": context.supersedes,
            "superseded_by": None,
        },
    }
```

```python
# src/aicore/task_store.py
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import yaml


def tasks_root(cwd: Path) -> Path:
    return cwd / ".aicore" / "tasks"


def next_task_id(cwd: Path, today: date) -> str:
    root = tasks_root(cwd)
    root.mkdir(parents=True, exist_ok=True)
    prefix = f"task-{today.isoformat()}-"
    existing = sorted(path.name for path in root.iterdir() if path.is_dir() and path.name.startswith(prefix))
    return f"{prefix}{len(existing) + 1:03d}"


def task_dir(cwd: Path, task_id: str) -> Path:
    return tasks_root(cwd) / task_id


def save_task(cwd: Path, task: dict) -> None:
    directory = task_dir(cwd, task["id"])
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "task.yaml").write_text(
        yaml.safe_dump(task, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    (directory / "brief.md").write_text(render_brief(task), encoding="utf-8")


def load_task(cwd: Path, task_id: str) -> dict:
    task_file = task_dir(cwd, task_id) / "task.yaml"
    return yaml.safe_load(task_file.read_text(encoding="utf-8"))


def render_brief(task: dict) -> str:
    confirm_items = [
        ("项目类型", task["project"]["type"]),
        ("主入口", ", ".join(task["entrypoints"]["main"]) or "待确认"),
        ("兼容入口", ", ".join(task["entrypoints"]["compat"]) or "待确认"),
        ("允许修改文件", ", ".join(task["change_scope"]["allowed_files"]) or "待确认"),
        ("禁止修改范围", ", ".join(task["change_scope"]["protected_areas"]) or "待确认"),
        ("验收依据", ", ".join(task["acceptance"]["baseline_refs"]) or "待确认"),
        ("回退方案", task["context"]["rollback_plan"] or "待确认"),
    ]
    lines = [
        f"# {task['id']}",
        "",
        f"- 状态: `{task['status']}`",
        f"- 原始需求: {task['request']['raw']}",
        "",
        "## 待确认项",
    ]
    lines.extend(f"- {label}: {value}" for label, value in confirm_items)
    return "\n".join(lines) + "\n"
```

```python
# src/aicore/task_service.py
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from aicore.draft_builder import DraftContext, build_draft
from aicore.task_store import next_task_id, save_task


def start_task(request: str, cwd: Path, supersedes: str | None = None) -> dict:
    now = datetime(2099, 1, 1, 9, 0, 0)
    task_id = next_task_id(cwd, now.date())
    task = build_draft(DraftContext(request=request, task_id=task_id, now=now, cwd=cwd, supersedes=supersedes))
    save_task(cwd, task)
    return task
```

```python
# src/aicore/cli.py
from __future__ import annotations

import argparse
from pathlib import Path

from aicore.task_service import start_task


def build_parser() -> argparse.ArgumentParser:
    ...


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    try:
        if args.command == "start":
            task = start_task(args.request, Path.cwd(), supersedes=args.supersedes)
            print(task["id"])
            print("状态: draft")
            print("下一步: 运行 aicore review <task-id>")
            return 0
        raise SystemExit("Command wiring is added in later tasks")
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2
```

- [ ] **Step 4: Run the `start` tests to verify they pass**

Run: `cd /Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding && PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' python3.11 -m pytest tests/test_start_command.py -q`
Expected: `3 passed`

- [ ] **Step 5: Record the checkpoint instead of committing**

Run: `cd /Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding && PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' python3.11 -m pytest tests/test_cli_smoke.py tests/test_start_command.py -q`
Expected: `5 passed`

### Task 3: Implement `review`, `approve`, and `reject` with State Validation

**Files:**
- Create: `src/aicore/state_machine.py`
- Modify: `src/aicore/task_store.py`
- Modify: `src/aicore/task_service.py`
- Modify: `src/aicore/cli.py`
- Create: `tests/test_state_commands.py`

- [ ] **Step 1: Write the failing state-command tests**

```python
# tests/test_state_commands.py
from __future__ import annotations

from pathlib import Path

import yaml

from aicore.cli import main


def test_review_moves_draft_to_reviewing_and_rerenders_brief(workspace: Path):
    main(["start", "实现 JWT 登录"])
    exit_code = main(["review", "task-2099-01-01-001"])

    task_file = workspace / ".aicore" / "tasks" / "task-2099-01-01-001" / "task.yaml"
    brief_file = workspace / ".aicore" / "tasks" / "task-2099-01-01-001" / "brief.md"
    data = yaml.safe_load(task_file.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert data["status"] == "reviewing"
    assert "reviewing" in brief_file.read_text(encoding="utf-8")


def test_approve_requires_by_and_freezes_review_metadata(workspace: Path):
    main(["start", "实现 JWT 登录"])
    main(["review", "task-2099-01-01-001"])

    exit_code = main(["approve", "task-2099-01-01-001", "--by", "dong1"])
    data = yaml.safe_load(
        (workspace / ".aicore" / "tasks" / "task-2099-01-01-001" / "task.yaml").read_text(encoding="utf-8")
    )

    assert exit_code == 0
    assert data["status"] == "approved"
    assert data["review"]["approved_by"] == "dong1"
    assert data["review"]["approved_at"] is not None


def test_reject_blocks_future_approval(workspace: Path):
    main(["start", "实现 JWT 登录"])
    main(["reject", "task-2099-01-01-001", "--reason", "边界不清晰"])

    exit_code = main(["approve", "task-2099-01-01-001", "--by", "dong1"])
    assert exit_code == 2
```

- [ ] **Step 2: Run the state-command tests to verify they fail**

Run: `cd /Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding && PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' python3.11 -m pytest tests/test_state_commands.py -q`
Expected: FAIL because `review/approve/reject` are not wired yet

- [ ] **Step 3: Implement the state machine and service orchestration**

```python
# src/aicore/state_machine.py
from __future__ import annotations


ALLOWED_TRANSITIONS = {
    "draft": {"reviewing", "approved", "rejected"},
    "reviewing": {"approved", "rejected"},
    "approved": set(),
    "rejected": set(),
    "superseded": set(),
}


def ensure_transition(current: str, target: str) -> None:
    if target not in ALLOWED_TRANSITIONS.get(current, set()):
        raise ValueError(f"非法状态切换: {current} -> {target}")
```

```python
# src/aicore/task_store.py
from __future__ import annotations

from datetime import datetime
...


def overwrite_task(cwd: Path, task: dict) -> None:
    task["history"]["updated_at"] = datetime(2099, 1, 1, 9, 0, 0).isoformat()
    save_task(cwd, task)
```

```python
# src/aicore/task_service.py
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from aicore.state_machine import ensure_transition
from aicore.task_store import load_task, overwrite_task, save_task


def review_task(task_id: str, cwd: Path) -> dict:
    task = load_task(cwd, task_id)
    if task["status"] == "draft":
        ensure_transition("draft", "reviewing")
        task["status"] = "reviewing"
        overwrite_task(cwd, task)
    return task


def approve_task(task_id: str, approved_by: str, cwd: Path) -> dict:
    task = load_task(cwd, task_id)
    ensure_transition(task["status"], "approved")
    task["status"] = "approved"
    task["review"]["approved_by"] = approved_by
    task["review"]["approved_at"] = datetime(2099, 1, 1, 9, 0, 0).isoformat()
    overwrite_task(cwd, task)
    return task


def reject_task(task_id: str, reason: str, cwd: Path) -> dict:
    task = load_task(cwd, task_id)
    ensure_transition(task["status"], "rejected")
    task["status"] = "rejected"
    task["review"]["rejected_reason"] = reason
    overwrite_task(cwd, task)
    return task
```

```python
# src/aicore/cli.py
from aicore.task_service import approve_task, reject_task, review_task, start_task


def main(argv: list[str] | None = None) -> int:
    ...
        if args.command == "review":
            review_task(args.task_id, Path.cwd())
            print("状态: reviewing")
            return 0
        if args.command == "approve":
            approve_task(args.task_id, args.by, Path.cwd())
            print("状态: approved")
            return 0
        if args.command == "reject":
            reject_task(args.task_id, args.reason, Path.cwd())
            print("状态: rejected")
            return 0
    ...
```

- [ ] **Step 4: Run the state-command tests to verify they pass**

Run: `cd /Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding && PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' python3.11 -m pytest tests/test_state_commands.py -q`
Expected: `3 passed`

- [ ] **Step 5: Run the full test set built so far**

Run: `cd /Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding && PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' python3.11 -m pytest tests/test_cli_smoke.py tests/test_start_command.py tests/test_state_commands.py -q`
Expected: `8 passed`

### Task 4: Implement `supersedes` and Atomic Approval of Replacement Tasks

**Files:**
- Modify: `src/aicore/state_machine.py`
- Modify: `src/aicore/task_service.py`
- Create: `tests/test_supersedes_flow.py`

- [ ] **Step 1: Write the failing supersedes tests**

```python
# tests/test_supersedes_flow.py
from __future__ import annotations

from pathlib import Path

import yaml

from aicore.cli import main


def test_approving_replacement_supersedes_old_task(workspace: Path):
    main(["start", "实现 JWT 登录"])
    main(["review", "task-2099-01-01-001"])
    main(["approve", "task-2099-01-01-001", "--by", "dong1"])

    main(["start", "补充 JWT refresh token 约束", "--supersedes", "task-2099-01-01-001"])
    main(["review", "task-2099-01-01-002"])
    exit_code = main(["approve", "task-2099-01-01-002", "--by", "dong1"])

    old_task = yaml.safe_load(
        (workspace / ".aicore" / "tasks" / "task-2099-01-01-001" / "task.yaml").read_text(encoding="utf-8")
    )
    new_task = yaml.safe_load(
        (workspace / ".aicore" / "tasks" / "task-2099-01-01-002" / "task.yaml").read_text(encoding="utf-8")
    )

    assert exit_code == 0
    assert new_task["status"] == "approved"
    assert old_task["status"] == "superseded"
    assert old_task["history"]["superseded_by"] == "task-2099-01-01-002"


def test_cannot_supersede_rejected_task_into_approved_without_new_draft(workspace: Path):
    main(["start", "实现 JWT 登录"])
    main(["reject", "task-2099-01-01-001", "--reason", "边界不清晰"])

    exit_code = main(["approve", "task-2099-01-01-001", "--by", "dong1"])
    assert exit_code == 2
```

- [ ] **Step 2: Run the supersedes tests to verify they fail**

Run: `cd /Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding && PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' python3.11 -m pytest tests/test_supersedes_flow.py -q`
Expected: FAIL because approving replacement tasks does not yet update the old task

- [ ] **Step 3: Implement the atomic supersede flow**

```python
# src/aicore/state_machine.py
ALLOWED_TRANSITIONS = {
    "draft": {"reviewing", "approved", "rejected", "superseded"},
    "reviewing": {"approved", "rejected", "superseded"},
    "approved": {"superseded"},
    "rejected": set(),
    "superseded": set(),
}
```

```python
# src/aicore/task_service.py
from __future__ import annotations

...


def approve_task(task_id: str, approved_by: str, cwd: Path) -> dict:
    task = load_task(cwd, task_id)
    ensure_transition(task["status"], "approved")
    task["status"] = "approved"
    task["review"]["approved_by"] = approved_by
    task["review"]["approved_at"] = datetime(2099, 1, 1, 9, 0, 0).isoformat()

    superseded_task = None
    superseded_id = task["history"]["supersedes"]
    if superseded_id:
        superseded_task = load_task(cwd, superseded_id)
        ensure_transition(superseded_task["status"], "superseded")
        superseded_task["status"] = "superseded"
        superseded_task["history"]["superseded_by"] = task["id"]

    overwrite_task(cwd, task)
    if superseded_task is not None:
        overwrite_task(cwd, superseded_task)
    return task
```

- [ ] **Step 4: Run the supersedes tests to verify they pass**

Run: `cd /Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding && PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' python3.11 -m pytest tests/test_supersedes_flow.py -q`
Expected: `2 passed`

- [ ] **Step 5: Run the entire suite as the MVP verification gate**

Run: `cd /Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding && PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' python3.11 -m pytest tests -q`
Expected: `10 passed`

### Task 5: Tighten Output UX and Final Documentation

**Files:**
- Modify: `README.md`
- Modify: `src/aicore/task_store.py`

- [ ] **Step 1: Write the failing output test**

```python
# add to tests/test_start_command.py
def test_start_brief_lists_manual_confirmation_items(workspace: Path):
    main(["start", "实现 JWT 登录"])
    brief_text = (
        workspace / ".aicore" / "tasks" / "task-2099-01-01-001" / "brief.md"
    ).read_text(encoding="utf-8")

    assert "项目类型" in brief_text
    assert "允许修改文件" in brief_text
    assert "回退方案" in brief_text
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `cd /Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding && PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' python3.11 -m pytest tests/test_start_command.py::test_start_brief_lists_manual_confirmation_items -q`
Expected: FAIL if the brief still omits one or more confirmation sections

- [ ] **Step 3: Expand `brief.md` rendering and README usage docs**

```python
# src/aicore/task_store.py
def render_brief(task: dict) -> str:
    lines = [
        f"# {task['id']}",
        "",
        "## 摘要",
        f"- 状态: `{task['status']}`",
        f"- 原始需求: {task['request']['raw']}",
        f"- 项目类型: {task['project']['type']}",
        f"- 模块: {task['scope']['module']}",
        "",
        "## 需要人工确认后再进入下一步",
        f"- 主入口: {', '.join(task['entrypoints']['main']) or '待确认'}",
        f"- 兼容入口: {', '.join(task['entrypoints']['compat']) or '待确认'}",
        f"- 是否需要双改: {task['implementation']['dual_write_required']}",
        f"- 不双改原因: {task['implementation']['dual_write_reason'] or '待确认'}",
        f"- 允许修改文件: {', '.join(task['change_scope']['allowed_files']) or '待确认'}",
        f"- 禁止修改范围: {', '.join(task['change_scope']['protected_areas']) or '待确认'}",
        f"- 验收依据: {', '.join(task['acceptance']['baseline_refs']) or '待确认'}",
        f"- 回退方案: {task['context']['rollback_plan'] or '待确认'}",
    ]
    return "\n".join(lines) + "\n"
```

```markdown
# README.md

## Local Setup

```bash
python -m pip install -e ".[dev]"
```

## Example

```bash
aicore start "实现 JWT 登录"
aicore review task-2099-01-01-001
aicore approve task-2099-01-01-001 --by "dong1"
```

The tool never moves to implementation automatically. Human review is required between `start` and any later execution workflow.
```

- [ ] **Step 4: Run the targeted test and the full suite**

Run: `cd /Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding && PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' python3.11 -m pytest tests/test_start_command.py::test_start_brief_lists_manual_confirmation_items -q && PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' python3.11 -m pytest tests -q`
Expected: first command `1 passed`, second command `11 passed`

- [ ] **Step 5: Final checkpoint**

Run: `cd /Users/dong1/Documents/Codex/2026-05-24/sop-ai-agent-ai-ai-coding && python3.11 -m pip install -e ".[dev]"`
Expected: editable install succeeds and the CLI is ready for manual smoke testing

## Self-Review

- Spec coverage:
  - `start` -> Task 2 and Task 5
  - `review/approve/reject` -> Task 3
  - `superseded` lifecycle and audit fields -> Task 4
  - `brief.md` derived from `task.yaml` and re-rendered after state changes -> Task 2, Task 3, Task 5
  - project type / entrypoints / change scope / baseline refs / rollback plan -> Task 2 and Task 5
- Placeholder scan:
  - No `TODO`, `TBD`, or “similar to Task N” placeholders left in the plan.
- Type consistency:
  - The plan consistently uses `task_id`, `approved_by`, `reason`, `history.supersedes`, and `history.superseded_by`.
