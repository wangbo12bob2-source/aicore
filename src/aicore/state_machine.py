from __future__ import annotations


ALLOWED_TRANSITIONS = {
    "draft": {"reviewing", "approved", "rejected", "superseded"},
    "reviewing": {"approved", "rejected", "superseded"},
    "approved": {"superseded"},
    "rejected": set(),
    "superseded": set(),
}


class InvalidStateTransition(ValueError):
    pass


def transition(task: dict, next_status: str) -> dict:
    current_status = task["status"]
    allowed_statuses = ALLOWED_TRANSITIONS.get(current_status)
    if allowed_statuses is None or next_status not in allowed_statuses:
        raise InvalidStateTransition(
            f"invalid state transition: {current_status} -> {next_status}"
        )

    task["status"] = next_status
    return task
