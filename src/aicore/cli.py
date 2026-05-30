from __future__ import annotations

import argparse
from pathlib import Path
import sys

from aicore.history_service import create_checkpoint, log_write
from aicore.ledger_service import confirm_ledger_entry
from aicore.state_machine import InvalidStateTransition
from aicore.task_service import approve_task, reject_task, review_task, start_task
from aicore.task_views import render_terminal_summary


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

    log_write_parser = subparsers.add_parser("log-write")
    log_write_parser.add_argument("task_id")
    log_write_parser.add_argument("--session", required=True)
    log_write_parser.add_argument("--file", dest="files", action="append", required=True)
    log_write_parser.add_argument("--summary", required=True)

    checkpoint_parser = subparsers.add_parser("checkpoint")
    checkpoint_parser.add_argument("task_id")
    checkpoint_parser.add_argument("--event", dest="event_ids", action="append", required=True)
    checkpoint_parser.add_argument("--summary", required=True)

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
    if args.command == "approve":
        try:
            task = approve_task(args.task_id, args.by, Path.cwd())
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
