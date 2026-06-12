from __future__ import annotations

import inspect
from pathlib import Path

from aicore.history_service import log_write
from aicore.ledger_service import confirm_ledger_entry


def _create_event(workspace: Path, task_id: str, path_text: str = "src/app.py") -> str:
    source_file = workspace / path_text
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("print('ok')\n", encoding="utf-8")
    result = log_write(
        cwd=workspace,
        task_id=task_id,
        session_id="session-1",
        files=[path_text],
        summary="记录完成态来源事件",
    )
    return result["event"]["event_id"]


def test_confirm_ledger_entry_creates_ledger_with_fixed_sections(workspace: Path):
    event_id = _create_event(workspace, "task-2026-05-26-001")
    result = confirm_ledger_entry(
        cwd=workspace,
        task_id="task-2026-05-26-001",
        event_ref=event_id,
        capability="支持完成态账本记录",
        entrypoint="confirm_ledger_entry",
        limit="当前仅支持单文件账本",
        compatibility="兼容 macOS、Windows、Linux",
        risk="重复确认会持续追加",
    )

    assert result == {"ledger_path": ".aicore/system-ledger.md"}

    ledger_path = workspace / ".aicore" / "system-ledger.md"
    assert ledger_path.exists()
    assert ledger_path.read_text(encoding="utf-8") == (
        "## Current Capabilities\n"
        f"- 支持完成态账本记录 (来源: task-2026-05-26-001 / {event_id})\n"
        "\n"
        "## Entrypoints\n"
        f"- confirm_ledger_entry (来源: task-2026-05-26-001 / {event_id})\n"
        "\n"
        "## Limits And Boundaries\n"
        f"- 当前仅支持单文件账本 (来源: task-2026-05-26-001 / {event_id})\n"
        "\n"
        "## Compatibility\n"
        f"- 兼容 macOS、Windows、Linux (来源: task-2026-05-26-001 / {event_id})\n"
        "\n"
        "## Known Risks\n"
        f"- 重复确认会持续追加 (来源: task-2026-05-26-001 / {event_id})\n"
    )


def test_confirm_ledger_entry_appends_to_each_section_without_reordering(workspace: Path):
    first_event_id = _create_event(workspace, "task-2026-05-26-001", "src/first.py")
    confirm_ledger_entry(
        cwd=workspace,
        task_id="task-2026-05-26-001",
        event_ref=first_event_id,
        capability="支持完成态账本记录",
        entrypoint="confirm_ledger_entry",
        limit="当前仅支持单文件账本",
        compatibility="兼容 macOS、Windows、Linux",
        risk="重复确认会持续追加",
    )

    second_event_id = _create_event(workspace, "task-2026-05-26-002", "src/second.py")
    confirm_ledger_entry(
        cwd=workspace,
        task_id="task-2026-05-26-002",
        event_ref=second_event_id,
        capability="支持第二次确认追加",
        entrypoint="后续调用继续写入",
        limit="不做去重",
        compatibility="路径写入保持跨平台",
        risk="内容增长依赖人工维护",
    )

    ledger_text = (workspace / ".aicore" / "system-ledger.md").read_text(
        encoding="utf-8"
    )

    assert ledger_text == (
        "## Current Capabilities\n"
        f"- 支持完成态账本记录 (来源: task-2026-05-26-001 / {first_event_id})\n"
        f"- 支持第二次确认追加 (来源: task-2026-05-26-002 / {second_event_id})\n"
        "\n"
        "## Entrypoints\n"
        f"- confirm_ledger_entry (来源: task-2026-05-26-001 / {first_event_id})\n"
        f"- 后续调用继续写入 (来源: task-2026-05-26-002 / {second_event_id})\n"
        "\n"
        "## Limits And Boundaries\n"
        f"- 当前仅支持单文件账本 (来源: task-2026-05-26-001 / {first_event_id})\n"
        f"- 不做去重 (来源: task-2026-05-26-002 / {second_event_id})\n"
        "\n"
        "## Compatibility\n"
        f"- 兼容 macOS、Windows、Linux (来源: task-2026-05-26-001 / {first_event_id})\n"
        f"- 路径写入保持跨平台 (来源: task-2026-05-26-002 / {second_event_id})\n"
        "\n"
        "## Known Risks\n"
        f"- 重复确认会持续追加 (来源: task-2026-05-26-001 / {first_event_id})\n"
        f"- 内容增长依赖人工维护 (来源: task-2026-05-26-002 / {second_event_id})\n"
    )


def test_confirm_ledger_entry_accepts_existing_crlf_ledger(workspace: Path):
    event_id = _create_event(workspace, "task-2026-05-26-003")
    ledger_path = workspace / ".aicore" / "system-ledger.md"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        "## Current Capabilities\r\n"
        "- 已有能力 (来源: task-old / event-old)\r\n"
        "\r\n"
        "## Entrypoints\r\n"
        "- 已有入口 (来源: task-old / event-old)\r\n"
        "\r\n"
        "## Limits And Boundaries\r\n"
        "- 已有限制 (来源: task-old / event-old)\r\n"
        "\r\n"
        "## Compatibility\r\n"
        "- 已有兼容性 (来源: task-old / event-old)\r\n"
        "\r\n"
        "## Known Risks\r\n"
        "- 已有风险 (来源: task-old / event-old)\r\n",
        encoding="utf-8",
    )

    confirm_ledger_entry(
        cwd=workspace,
        task_id="task-2026-05-26-003",
        event_ref=event_id,
        capability="支持处理 CRLF 账本",
        entrypoint="ledger-confirm",
        limit="仍然只支持固定区块",
        compatibility="兼容 CRLF 文本输入",
        risk="人工维护仍可能造成语义重复",
    )

    ledger_text = ledger_path.read_text(encoding="utf-8")
    assert "- 已有能力 (来源: task-old / event-old)" in ledger_text
    assert f"- 支持处理 CRLF 账本 (来源: task-2026-05-26-003 / {event_id})" in ledger_text
    assert ledger_text.count("## Current Capabilities") == 1
    assert "\r\n" not in ledger_text


def test_confirm_ledger_entry_rejects_multiline_values(workspace: Path):
    event_id = _create_event(workspace, "task-2026-05-26-004")
    try:
        confirm_ledger_entry(
            cwd=workspace,
            task_id="task-2026-05-26-004",
            event_ref=event_id,
            capability="第一行\n第二行",
            entrypoint="ledger-confirm",
            limit="限制",
            compatibility="兼容性",
            risk="风险",
        )
    except ValueError as exc:
        assert "单行" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_confirm_ledger_entry_rejects_unknown_event_reference(workspace: Path):
    try:
        confirm_ledger_entry(
            cwd=workspace,
            task_id="task-2026-05-26-005",
            event_ref="event-missing",
            capability="能力",
            entrypoint="ledger-confirm",
            limit="限制",
            compatibility="兼容性",
            risk="风险",
        )
    except ValueError as exc:
        assert "event 不存在" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_confirm_ledger_entry_rejects_event_reference_from_other_task(workspace: Path):
    event_id = _create_event(workspace, "task-2026-05-26-006")
    try:
        confirm_ledger_entry(
            cwd=workspace,
            task_id="task-2026-05-26-007",
            event_ref=event_id,
            capability="能力",
            entrypoint="ledger-confirm",
            limit="限制",
            compatibility="兼容性",
            risk="风险",
        )
    except ValueError as exc:
        assert event_id in str(exc)
        assert "task-2026-05-26-006" in str(exc)
        assert "task-2026-05-26-007" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_cli_ledger_confirm_function_signature_matches_expected_entrypoint():
    assert list(inspect.signature(confirm_ledger_entry).parameters) == [
        "cwd",
        "task_id",
        "event_ref",
        "capability",
        "entrypoint",
        "limit",
        "compatibility",
        "risk",
    ]
