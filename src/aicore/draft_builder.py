from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


MULTI_SYSTEM_KEYWORD_GROUPS = (
    ("聊天", "chat"),
    ("支付", "payment", "billing"),
    ("文件存储", "storage"),
    ("报表", "report", "analytics"),
)

MULTI_ENTRYPOINT_RISK_GROUPS = (
    ("spa", "html"),
    ("web", "electron"),
    ("本地驱动", "远程 api"),
)

MULTI_ENTRYPOINT_RISK_KEYWORDS = (
    "双前端",
    "嵌入式 html",
)


@dataclass(frozen=True)
class DraftContext:
    request: str
    task_id: str
    now: datetime
    cwd: Path
    supersedes: str | None = None


def validate_request_scope(request: str) -> None:
    lowered = request.lower()
    matched = sum(
        any(keyword in lowered for keyword in keywords)
        for keywords in MULTI_SYSTEM_KEYWORD_GROUPS
    )
    if matched >= 3:
        raise ValueError("需求范围过大，包含多个独立子系统，请先拆分。")


def validate_entrypoint_risk(request: str) -> None:
    lowered = request.lower()
    has_risk_group = any(
        all(keyword in lowered for keyword in keywords)
        for keywords in MULTI_ENTRYPOINT_RISK_GROUPS
    )
    has_risk_keyword = any(keyword in lowered for keyword in MULTI_ENTRYPOINT_RISK_KEYWORDS)

    if has_risk_group or has_risk_keyword:
        raise ValueError("请求暴露明显多入口或双实现联动风险，当前无法确认主入口或双改策略，请先拆分或明确入口。")


def infer_project_type(request: str) -> str:
    if any(keyword in request for keyword in ("逆向", "还原", "反编译")):
        return "reverse-engineering"
    if any(keyword in request for keyword in ("迁移", "桥接", "替代旧系统")):
        return "hybrid-migration"
    return "product-delivery"


def infer_scope_module(request: str) -> str:
    lowered = request.lower()
    if "jwt" in lowered or "登录" in request or "auth" in lowered:
        return "auth-login"
    if "支付" in request or "payment" in lowered:
        return "payment"
    raise ValueError("无法稳定判断该请求归属的单一逻辑模块，请先明确任务边界。")


def build_draft(context: DraftContext) -> dict:
    validate_request_scope(context.request)
    validate_entrypoint_risk(context.request)
    scope_module = infer_scope_module(context.request)

    now_text = context.now.isoformat()
    return {
        "id": context.task_id,
        "version": 1,
        "status": "draft",
        "request": {"raw": context.request},
        "project": {"type": infer_project_type(context.request)},
        "scope": {
            "module": scope_module,
            "goal": context.request,
            "in_scope": ["待从需求中确认的核心动作"],
            "out_of_scope": ["未在当前请求中明确提出的扩展能力"],
        },
        "entrypoints": {"main": [], "compat": []},
        "implementation": {
            "dual_write_required": False,
            "dual_write_reason": "待确认是否存在兼容入口或双实现。",
        },
        "change_scope": {
            "allowed_files": [],
            "protected_areas": [
                "未在当前任务请求中点名的模块默认禁止修改。",
                "执行阶段入口和发布链路在本阶段禁止修改，原因：当前仅任务启动。",
            ],
        },
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
            "assumptions": ["项目类型由关键词初步推断，待人工确认。"],
            "risks": ["主入口、允许修改文件、验收依据尚未确认，不得进入执行。"],
            "rollback_plan": "若草案边界或约束判断有误，直接 reject 当前任务草案并重新 start，不进入执行阶段。",
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
