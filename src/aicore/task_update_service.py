from __future__ import annotations

from datetime import datetime
from pathlib import Path, PurePosixPath, PureWindowsPath

from aicore.task_contract_service import validate_task_contract
from aicore.task_store import load_task, overwrite_task


def _resolve_current_time(now: datetime | None) -> datetime:
    current_time = now if now is not None else datetime.now()
    if current_time.tzinfo is None:
        return current_time.astimezone()
    return current_time


def _validate_non_empty_items(values: list[str], field_name: str) -> list[str]:
    normalized_values = [value.strip() for value in values if value.strip()]
    if not normalized_values:
        raise ValueError(f"{field_name} 不能为空")
    return normalized_values


def _normalize_workspace_relative_path(path_text: str) -> str:
    normalized = path_text.strip()
    if not normalized:
        raise ValueError("allowed_files 不能为空")
    if PureWindowsPath(normalized).is_absolute() or PureWindowsPath(normalized).drive:
        raise ValueError("allowed_files 必须位于当前工作区内")

    pure_path = PurePosixPath(normalized.replace("\\", "/"))
    if pure_path.is_absolute() or ".." in pure_path.parts:
        raise ValueError("allowed_files 必须位于当前工作区内")
    return PurePosixPath(*pure_path.parts).as_posix()


def update_task(
    task_id: str,
    cwd: Path,
    *,
    main_entrypoints: list[str] | None = None,
    compat_entrypoints: list[str] | None = None,
    allowed_files: list[str] | None = None,
    baseline_refs: list[str] | None = None,
    success_criteria: list[str] | None = None,
    assumptions: list[str] | None = None,
    risks: list[str] | None = None,
    review_summary: str | None = None,
    rollback_plan: str | None = None,
    dual_write_required: bool | None = None,
    dual_write_reason: str | None = None,
    now: datetime | None = None,
) -> dict:
    task = load_task(cwd, task_id)

    if main_entrypoints is not None:
        task["entrypoints"]["main"] = _validate_non_empty_items(
            main_entrypoints, "entrypoints.main"
        )
    if compat_entrypoints is not None:
        task["entrypoints"]["compat"] = [value.strip() for value in compat_entrypoints if value.strip()]
    if allowed_files is not None:
        normalized_paths = [
            _normalize_workspace_relative_path(path_text) for path_text in allowed_files
        ]
        if not normalized_paths:
            raise ValueError("change_scope.allowed_files 不能为空")
        task["change_scope"]["allowed_files"] = normalized_paths
    if baseline_refs is not None:
        task["acceptance"]["baseline_refs"] = _validate_non_empty_items(
            baseline_refs, "acceptance.baseline_refs"
        )
    if success_criteria is not None:
        task["acceptance"]["success_criteria"] = _validate_non_empty_items(
            success_criteria, "acceptance.success_criteria"
        )
    if assumptions is not None:
        task["context"]["assumptions"] = _validate_non_empty_items(
            assumptions, "context.assumptions"
        )
    if risks is not None:
        task["context"]["risks"] = _validate_non_empty_items(risks, "context.risks")
    if review_summary is not None:
        normalized_summary = review_summary.strip()
        if not normalized_summary:
            raise ValueError("review.summary 不能为空")
        task["review"]["summary"] = normalized_summary
    if rollback_plan is not None:
        normalized_rollback = rollback_plan.strip()
        if not normalized_rollback:
            raise ValueError("context.rollback_plan 不能为空")
        task["context"]["rollback_plan"] = normalized_rollback
    if dual_write_required is not None:
        task["implementation"]["dual_write_required"] = dual_write_required
    if dual_write_reason is not None:
        normalized_reason = dual_write_reason.strip()
        if not normalized_reason:
            raise ValueError("implementation.dual_write_reason 不能为空")
        task["implementation"]["dual_write_reason"] = normalized_reason

    task["history"]["updated_at"] = _resolve_current_time(now).isoformat()
    overwrite_task(cwd, task)
    return task


def validate_task_for_approval(task_id: str, cwd: Path) -> dict:
    return validate_task_contract(task_id, cwd)
