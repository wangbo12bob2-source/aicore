from __future__ import annotations

import inspect
from pathlib import Path

from aicore.ledger_service import confirm_ledger_entry


def test_confirm_ledger_entry_creates_ledger_with_fixed_sections(workspace: Path):
    result = confirm_ledger_entry(
        cwd=workspace,
        task_id="task-2026-05-26-001",
        event_ref="event-001",
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
        "- 支持完成态账本记录 (来源: task-2026-05-26-001 / event-001)\n"
        "\n"
        "## Entrypoints\n"
        "- confirm_ledger_entry (来源: task-2026-05-26-001 / event-001)\n"
        "\n"
        "## Limits And Boundaries\n"
        "- 当前仅支持单文件账本 (来源: task-2026-05-26-001 / event-001)\n"
        "\n"
        "## Compatibility\n"
        "- 兼容 macOS、Windows、Linux (来源: task-2026-05-26-001 / event-001)\n"
        "\n"
        "## Known Risks\n"
        "- 重复确认会持续追加 (来源: task-2026-05-26-001 / event-001)\n"
    )


def test_confirm_ledger_entry_appends_to_each_section_without_reordering(workspace: Path):
    confirm_ledger_entry(
        cwd=workspace,
        task_id="task-2026-05-26-001",
        event_ref="event-001",
        capability="支持完成态账本记录",
        entrypoint="confirm_ledger_entry",
        limit="当前仅支持单文件账本",
        compatibility="兼容 macOS、Windows、Linux",
        risk="重复确认会持续追加",
    )

    confirm_ledger_entry(
        cwd=workspace,
        task_id="task-2026-05-26-002",
        event_ref="event-002",
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
        "- 支持完成态账本记录 (来源: task-2026-05-26-001 / event-001)\n"
        "- 支持第二次确认追加 (来源: task-2026-05-26-002 / event-002)\n"
        "\n"
        "## Entrypoints\n"
        "- confirm_ledger_entry (来源: task-2026-05-26-001 / event-001)\n"
        "- 后续调用继续写入 (来源: task-2026-05-26-002 / event-002)\n"
        "\n"
        "## Limits And Boundaries\n"
        "- 当前仅支持单文件账本 (来源: task-2026-05-26-001 / event-001)\n"
        "- 不做去重 (来源: task-2026-05-26-002 / event-002)\n"
        "\n"
        "## Compatibility\n"
        "- 兼容 macOS、Windows、Linux (来源: task-2026-05-26-001 / event-001)\n"
        "- 路径写入保持跨平台 (来源: task-2026-05-26-002 / event-002)\n"
        "\n"
        "## Known Risks\n"
        "- 重复确认会持续追加 (来源: task-2026-05-26-001 / event-001)\n"
        "- 内容增长依赖人工维护 (来源: task-2026-05-26-002 / event-002)\n"
    )


def test_confirm_ledger_entry_accepts_existing_crlf_ledger(workspace: Path):
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
        event_ref="event-003",
        capability="支持处理 CRLF 账本",
        entrypoint="ledger-confirm",
        limit="仍然只支持固定区块",
        compatibility="兼容 CRLF 文本输入",
        risk="人工维护仍可能造成语义重复",
    )

    ledger_text = ledger_path.read_text(encoding="utf-8")
    assert "- 已有能力 (来源: task-old / event-old)" in ledger_text
    assert "- 支持处理 CRLF 账本 (来源: task-2026-05-26-003 / event-003)" in ledger_text
    assert ledger_text.count("## Current Capabilities") == 1
    assert "\r\n" not in ledger_text


def test_confirm_ledger_entry_rejects_multiline_values(workspace: Path):
    try:
        confirm_ledger_entry(
            cwd=workspace,
            task_id="task-2026-05-26-004",
            event_ref="event-004",
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
