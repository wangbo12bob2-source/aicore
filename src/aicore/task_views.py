from __future__ import annotations

from pathlib import Path


def _render_dual_write_required(task: dict) -> str:
    return "是" if task["implementation"]["dual_write_required"] else "否"


def render_confirm_lines(task: dict) -> list[str]:
    confirm_items = [
        ("主入口", ", ".join(task["entrypoints"]["main"]) or "待确认"),
        ("兼容入口", ", ".join(task["entrypoints"]["compat"]) or "待确认"),
        ("是否需要双改", _render_dual_write_required(task)),
        ("双改原因", task["implementation"]["dual_write_reason"] or "待确认"),
        ("允许修改文件", ", ".join(task["change_scope"]["allowed_files"]) or "待确认"),
        ("禁止修改范围", ", ".join(task["change_scope"]["protected_areas"]) or "待确认"),
        ("验收依据", ", ".join(task["acceptance"]["baseline_refs"]) or "待确认"),
        ("回退方案", task["context"]["rollback_plan"] or "待确认"),
    ]
    return [f"{label}: {value}" for label, value in confirm_items]


def render_terminal_summary(task: dict) -> str:
    lines = [
        f"项目类型: {task['project']['type']}",
        *render_confirm_lines(task),
    ]
    return "\n".join(lines)


def render_task_list(tasks: list[dict]) -> str:
    if not tasks:
        return "暂无任务"

    lines = []
    for task in tasks:
        lines.append(
            f"- {task['id']} | 状态: {task['status']} | 模块: {task['scope']['module']} | 需求: {task['request']['raw']}"
        )
    return "\n".join(lines)


def render_task_detail(task: dict) -> str:
    lines = [
        task["id"],
        f"状态: {task['status']}",
        render_terminal_summary(task),
        f"原始需求: {task['request']['raw']}",
        f"模块范围: {task['scope']['module']}",
        f"任务目录: {Path('.aicore') / 'tasks' / task['id']}",
        f"简报文件: {Path('.aicore') / 'tasks' / task['id'] / 'brief.md'}",
    ]
    return "\n".join(lines)


def render_brief(task: dict) -> str:
    lines = [
        f"# {task['id']}",
        "",
        "> 该草案仅用于人工确认边界与约束，需要人工确认后再进入下一步。",
        "> 在明确批准前，工具不会自动进入实现阶段。",
        "",
        f"- 状态: `{task['status']}`",
        f"- 原始需求: {task['request']['raw']}",
        f"- 项目类型: {task['project']['type']}",
        f"- 模块范围: {task['scope']['module']}",
        f"- 前置假设: {'; '.join(task['context']['assumptions'])}",
        f"- 主要风险: {'; '.join(task['context']['risks'])}",
        "",
        "## 人工确认清单",
        "",
        "确认以下信息后，再执行 `review / approve / reject`：",
    ]
    lines.extend(f"- {line}" for line in render_confirm_lines(task))
    return "\n".join(lines) + "\n"
