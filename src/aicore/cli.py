from __future__ import annotations

import argparse
from pathlib import Path
import sys

from aicore.history_service import create_checkpoint, log_write
from aicore.ledger_service import confirm_ledger_entry
from aicore.state_machine import InvalidStateTransition
from aicore.status_service import build_status
from aicore.task_contract_service import build_contract_checklist, render_contract_checklist
from aicore.task_query_service import get_task, list_tasks
from aicore.task_service import approve_task, reject_task, review_task, start_task
from aicore.task_update_service import update_task
from aicore.task_views import render_task_detail, render_task_list, render_terminal_summary


def run_shortcut(command: str, argv: list[str] | None = None) -> int:
    return main([command, *(argv or [])])


def shortcut_start() -> int:
    return run_shortcut("start", sys.argv[1:])


def shortcut_list() -> int:
    return run_shortcut("list", sys.argv[1:])


def shortcut_show() -> int:
    return run_shortcut("show", sys.argv[1:])


def shortcut_checklist() -> int:
    return run_shortcut("checklist", sys.argv[1:])


def shortcut_update() -> int:
    return run_shortcut("update", sys.argv[1:])


def shortcut_approve() -> int:
    return run_shortcut("approve", sys.argv[1:])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aicore")
    subparsers = parser.add_subparsers(dest="command")

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("request")
    start_parser.add_argument("--supersedes")

    review_parser = subparsers.add_parser("review")
    review_parser.add_argument("task_id")

    subparsers.add_parser("list")

    show_parser = subparsers.add_parser("show")
    show_parser.add_argument("task_id")

    checklist_parser = subparsers.add_parser("checklist")
    checklist_parser.add_argument("task_id")

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("task_id")
    update_parser.add_argument("--main-entrypoint", dest="main_entrypoints", action="append")
    update_parser.add_argument("--compat-entrypoint", dest="compat_entrypoints", action="append")
    update_parser.add_argument("--allowed-file", dest="allowed_files", action="append")
    update_parser.add_argument("--baseline-ref", dest="baseline_refs", action="append")
    update_parser.add_argument("--success-criteria", dest="success_criteria", action="append")
    update_parser.add_argument("--assumption", dest="assumptions", action="append")
    update_parser.add_argument("--risk", dest="risks", action="append")
    update_parser.add_argument("--review-summary")
    update_parser.add_argument("--rollback-plan")
    update_parser.add_argument(
        "--dual-write-required",
        choices=["true", "false"],
    )
    update_parser.add_argument("--dual-write-reason")

    approve_parser = subparsers.add_parser("approve")
    approve_parser.add_argument("task_id")
    approve_parser.add_argument("--by", required=True)

    reject_parser = subparsers.add_parser("reject")
    reject_parser.add_argument("task_id")
    reject_parser.add_argument("--reason", required=True)

    log_write_parser = subparsers.add_parser("log-write")
    log_write_parser.add_argument("task_id")
    log_write_parser.add_argument("--session", required=True)
    log_write_parser.add_argument("--file", dest="files", action="append", required=True)
    log_write_parser.add_argument("--summary", required=True)

    checkpoint_parser = subparsers.add_parser("checkpoint")
    checkpoint_parser.add_argument("task_id")
    checkpoint_parser.add_argument("--event", dest="event_ids", action="append", required=True)
    checkpoint_parser.add_argument("--summary", required=True)

    subparsers.add_parser("status")

    ledger_confirm_parser = subparsers.add_parser("ledger-confirm")
    ledger_confirm_parser.add_argument("task_id")
    ledger_confirm_parser.add_argument("--event", dest="event_ref", required=True)
    ledger_confirm_parser.add_argument("--capability", required=True)
    ledger_confirm_parser.add_argument("--entrypoint", required=True)
    ledger_confirm_parser.add_argument("--limit", required=True)
    ledger_confirm_parser.add_argument("--compatibility", required=True)
    ledger_confirm_parser.add_argument("--risk", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    if args.command == "start":
        try:
            task = start_task(args.request, Path.cwd(), supersedes=args.supersedes)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

        print(task["id"])
        print("状态: draft")
        print(f"目录: {Path('.aicore') / 'tasks' / task['id']}")
        print(render_terminal_summary(task))
        print(f"下一步: aicore review {task['id']}")
        return 0
    if args.command == "review":
        try:
            task = review_task(args.task_id, Path.cwd())
        except FileNotFoundError:
            print(f"error: task not found: {args.task_id}", file=sys.stderr)
            return 1
        except InvalidStateTransition as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

        print(task["id"])
        print(f"状态: {task['status']}")
        print(render_terminal_summary(task))
        print(
            f"请查看 {Path('.aicore') / 'tasks' / task['id'] / 'brief.md'} 并完成人工确认后，再决定 approve 或 reject。"
        )
        return 0
    if args.command == "list":
        print(render_task_list(list_tasks(Path.cwd())))
        return 0
    if args.command == "show":
        try:
            task = get_task(args.task_id, Path.cwd())
        except FileNotFoundError:
            print(f"error: task not found: {args.task_id}", file=sys.stderr)
            return 1
        print(render_task_detail(task))
        return 0
    if args.command == "checklist":
        try:
            report = build_contract_checklist(args.task_id, Path.cwd())
        except FileNotFoundError:
            print(f"error: task not found: {args.task_id}", file=sys.stderr)
            return 1
        print(render_contract_checklist(report))
        return 0
    if args.command == "update":
        try:
            task = update_task(
                args.task_id,
                Path.cwd(),
                main_entrypoints=args.main_entrypoints,
                compat_entrypoints=args.compat_entrypoints,
                allowed_files=args.allowed_files,
                baseline_refs=args.baseline_refs,
                success_criteria=args.success_criteria,
                assumptions=args.assumptions,
                risks=args.risks,
                review_summary=args.review_summary,
                rollback_plan=args.rollback_plan,
                dual_write_required=(
                    None
                    if args.dual_write_required is None
                    else args.dual_write_required == "true"
                ),
                dual_write_reason=args.dual_write_reason,
            )
        except FileNotFoundError:
            print(f"error: task not found: {args.task_id}", file=sys.stderr)
            return 1
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(task["id"])
        print(f"状态: {task['status']}")
        print(render_terminal_summary(task))
        return 0
    if args.command == "approve":
        try:
            task = approve_task(args.task_id, args.by, Path.cwd())
        except FileNotFoundError:
            print(f"error: task not found: {args.task_id}", file=sys.stderr)
            return 1
        except InvalidStateTransition as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

        print(task["id"])
        print(f"状态: {task['status']}")
        print(render_terminal_summary(task))
        return 0
    if args.command == "reject":
        try:
            task = reject_task(args.task_id, args.reason, Path.cwd())
        except FileNotFoundError:
            print(f"error: task not found: {args.task_id}", file=sys.stderr)
            return 1
        except InvalidStateTransition as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

        print(task["id"])
        print(f"状态: {task['status']}")
        print(render_terminal_summary(task))
        return 0
    if args.command == "log-write":
        try:
            result = log_write(
                cwd=Path.cwd(),
                task_id=args.task_id,
                session_id=args.session,
                files=args.files,
                summary=args.summary,
            )
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(result["event"]["event_id"])
        print(result["event_path"])
        return 0
    if args.command == "checkpoint":
        try:
            result = create_checkpoint(
                cwd=Path.cwd(),
                task_id=args.task_id,
                event_ids=args.event_ids,
                summary=args.summary,
            )
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(result["checkpoint"]["checkpoint_id"])
        print(result["manifest_path"])
        return 0
    if args.command == "status":
        status = build_status(Path.cwd())
        print("Sessions")
        for session_id in status["sessions"]:
            print(f"- {session_id}")
        print("Pending Events")
        for event_id in status["pending_event_ids"]:
            print(f"- {event_id}")
        print("Multi-session File Risks")
        for risk in status["multi_session_file_risks"]:
            sessions = ", ".join(risk["sessions"])
            events = ", ".join(risk["event_ids"])
            print(f"- {risk['path']} | sessions: {sessions} | events: {events}")
        return 0
    if args.command == "ledger-confirm":
        try:
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
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(result["ledger_path"])
        return 0
    print(f"error: unknown command '{args.command}'", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
