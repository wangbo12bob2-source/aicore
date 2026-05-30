from __future__ import annotations

from pathlib import Path


_LEDGER_PATH = Path(".aicore") / "system-ledger.md"
_SECTION_TITLES = [
    "## Current Capabilities",
    "## Entrypoints",
    "## Limits And Boundaries",
    "## Compatibility",
    "## Known Risks",
]


def _parse_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {title: [] for title in _SECTION_TITLES}
    current_title: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line in sections:
            current_title = line
            continue
        if current_title is None:
            continue
        sections[current_title].append(line)

    missing = [title for title in _SECTION_TITLES if title not in sections]
    if missing:
        raise ValueError(f"缺少固定区块: {missing[0]}")
    return sections


def _render_sections(sections: dict[str, list[str]]) -> str:
    blocks: list[str] = []
    for title in _SECTION_TITLES:
        blocks.append(title)
        blocks.extend(sections[title])
        blocks.append("")
    return "\n".join(blocks).rstrip() + "\n"


def _validate_single_line(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} 不能为空")
    if "\n" in normalized or "\r" in normalized:
        raise ValueError(f"{field_name} 必须是单行文本")
    return normalized


def _initial_ledger_text() -> str:
    return _render_sections({title: [] for title in _SECTION_TITLES})


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
    ledger_path = cwd / _LEDGER_PATH
    ledger_path.parent.mkdir(parents=True, exist_ok=True)

    capability_text = _validate_single_line(capability, "capability")
    entrypoint_text = _validate_single_line(entrypoint, "entrypoint")
    limit_text = _validate_single_line(limit, "limit")
    compatibility_text = _validate_single_line(compatibility, "compatibility")
    risk_text = _validate_single_line(risk, "risk")

    ledger_text = (
        ledger_path.read_text(encoding="utf-8")
        if ledger_path.exists()
        else _initial_ledger_text()
    )
    source = f"来源: {task_id} / {event_ref}"
    sections = _parse_sections(ledger_text)
    sections["## Current Capabilities"].append(f"- {capability_text} ({source})")
    sections["## Entrypoints"].append(f"- {entrypoint_text} ({source})")
    sections["## Limits And Boundaries"].append(f"- {limit_text} ({source})")
    sections["## Compatibility"].append(f"- {compatibility_text} ({source})")
    sections["## Known Risks"].append(f"- {risk_text} ({source})")

    ledger_path.write_text(_render_sections(sections), encoding="utf-8")
    return {"ledger_path": _LEDGER_PATH.as_posix()}
