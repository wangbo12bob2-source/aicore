from __future__ import annotations

from pathlib import Path

from aicore.task_store import load_task


_DEFAULT_SUCCESS_CRITERION = "待补充验收标准"
_DEFAULT_DUAL_WRITE_REASON = "待确认是否存在兼容入口或双实现。"
_DEFAULT_RISK = "主入口、允许修改文件、验收依据尚未确认，不得进入执行。"


def _non_empty(values: list[str]) -> bool:
    return any(value.strip() for value in values)


def build_contract_checklist(task_id: str, cwd: Path) -> dict:
    task = load_task(cwd, task_id)

    items = [
        {
            "key": "main_entrypoints",
            "title": "主入口已确认",
            "ok": _non_empty(task["entrypoints"]["main"]),
            "hint": "请补充 --main-entrypoint，明确这次到底改哪个入口。",
        },
        {
            "key": "architecture_assumptions",
            "title": "任务级架构假设已说明",
            "ok": _non_empty(task["context"]["assumptions"]),
            "hint": "请补充 --assumption，说明当前模块职责、入口归属或关键设计前提。",
        },
        {
            "key": "dual_write_strategy",
            "title": "双改策略已确认",
            "ok": task["implementation"]["dual_write_reason"].strip()
            not in {"", _DEFAULT_DUAL_WRITE_REASON},
            "hint": "请补充 --dual-write-reason，说明是否需要兼容入口或双改。",
        },
        {
            "key": "allowed_files",
            "title": "允许修改文件已冻结",
            "ok": _non_empty(task["change_scope"]["allowed_files"]),
            "hint": "请补充 --allowed-file，明确这次允许改哪些文件。",
        },
        {
            "key": "baseline_refs",
            "title": "验收依据已确认",
            "ok": _non_empty(task["acceptance"]["baseline_refs"]),
            "hint": "请补充 --baseline-ref，明确用什么命令、测试或页面验收。",
        },
        {
            "key": "success_criteria",
            "title": "成功标准已写清",
            "ok": _non_empty(task["acceptance"]["success_criteria"])
            and all(
                criterion.strip() != _DEFAULT_SUCCESS_CRITERION
                for criterion in task["acceptance"]["success_criteria"]
            ),
            "hint": "请补充 --success-criteria，不要保留“待补充验收标准”。",
        },
        {
            "key": "risks",
            "title": "风险与未覆盖项已说明",
            "ok": _non_empty(task["context"]["risks"])
            and all(risk.strip() != _DEFAULT_RISK for risk in task["context"]["risks"]),
            "hint": "请补充 --risk，写清本轮没覆盖什么风险。",
        },
        {
            "key": "review_summary",
            "title": "任务边界摘要已确认",
            "ok": bool(task["review"]["summary"].strip()),
            "hint": "请补充 --review-summary，用一句话说明本轮边界已经冻结。",
        },
        {
            "key": "rollback_plan",
            "title": "回退方案已存在",
            "ok": bool(task["context"]["rollback_plan"].strip()),
            "hint": "请补充 --rollback-plan，明确改坏后怎么撤回。",
        },
    ]

    failed_items = [item for item in items if not item["ok"]]
    return {
        "task": task,
        "items": items,
        "ready": not failed_items,
        "failed_items": failed_items,
    }


def render_contract_checklist(report: dict) -> str:
    lines = [
        report["task"]["id"],
        f"状态: {report['task']['status']}",
        "任务级架构与审批检查",
    ]
    for item in report["items"]:
        prefix = "[OK]" if item["ok"] else "[ ]"
        lines.append(f"- {prefix} {item['title']}：{item['hint']}")

    if report["ready"]:
        lines.append("结论: 当前任务已完成任务级架构审核，可以继续 approve。")
    else:
        lines.append("结论: 当前任务还没完成任务级架构审核，请先运行 aicore update 补齐未满足项。")
    return "\n".join(lines)


def validate_task_contract(task_id: str, cwd: Path) -> dict:
    report = build_contract_checklist(task_id, cwd)
    if not report["ready"]:
        missing_titles = "、".join(item["title"] for item in report["failed_items"])
        raise ValueError(
            "任务尚未完成任务级架构审核，请先运行 "
            f"`aicore checklist {task_id}` 查看未完成项。当前缺少: {missing_titles}"
        )
    return report["task"]
