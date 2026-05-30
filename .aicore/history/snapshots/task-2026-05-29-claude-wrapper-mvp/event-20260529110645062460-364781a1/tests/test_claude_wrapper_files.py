from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_project_claude_instructions_define_aicore_state_contract():
    claude_file = PROJECT_ROOT / "CLAUDE.md"

    assert claude_file.exists()

    text = claude_file.read_text(encoding="utf-8")

    assert "aicore start" in text
    assert "log-write" in text
    assert "checkpoint" in text
    assert "ledger-confirm" in text
    assert "不维护第二套状态" in text


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
        assert "Python 3.11 启动器" in text
        assert "何时使用" in text
        assert "输出" in text
        assert "不要" in text


def test_aicore_guard_agent_is_supervisory_not_autonomous():
    text = (PROJECT_ROOT / ".claude" / "agents" / "aicore-guard.md").read_text(
        encoding="utf-8"
    )

    assert "流程监督" in text
    assert "python3.11 -m aicore.cli" in text
    assert "不自动批准" in text
    assert "不自动提交 Git" in text
    assert "不自行扩大修改范围" in text
    assert "不维护第二套状态" in text
    assert "system-ledger.md" in text


def test_readme_mentions_claude_code_wrapper_entrypoints():
    text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "Claude Code" in text
    assert "/aicore-start" in text
    assert "/aicore-log-write" in text
    assert "/aicore-checkpoint" in text
    assert "/aicore-ledger" in text
