from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any


ACTION_GROUPS = (
    "to_build",
    "to_rebuild",
    "to_deprecate",
    "to_remove",
    "to_skip",
)

STATE_TO_ACTION = {
    "PAST_LIVE": "to_rebuild",
    "CANCELED_DEPRECATED": "to_deprecate",
    "INVALID_REMOVE": "to_remove",
}


def clean_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def classification_sessions(classification: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(classification, dict):
        return {}

    sessions = classification.get("sessions")
    if not isinstance(sessions, dict):
        return {}

    return {
        str(session_id): session
        for session_id, session in sessions.items()
        if isinstance(session, dict)
    }


def has_changed(session: dict[str, Any]) -> bool:
    current_state = clean_string(session.get("current_state"))
    previous_state = clean_string(session.get("previous_state"))

    if previous_state is None:
        return True

    if current_state != previous_state:
        return True

    if session.get("was_ever_published") is not True:
        return True

    if session.get("content_changed") is True:
        return True

    if session.get("source_changed") is True:
        return True

    if session.get("last_built_at") in (None, ""):
        return True

    return False


def action_for_session(session: dict[str, Any]) -> str:
    state = clean_string(session.get("current_state"))

    if state == "FUTURE_ACTIVE":
        return "to_build" if has_changed(session) else "to_skip"

    return STATE_TO_ACTION.get(state, "to_remove")


def plan_item(session_id: str, session: dict[str, Any], action: str) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "action": action,
        "current_state": session.get("current_state"),
        "previous_state": session.get("previous_state"),
        "state_reason": session.get("state_reason"),
        "confidence_level": session.get("confidence_level"),
        "is_currently_in_source": session.get("is_currently_in_source"),
        "was_ever_published": session.get("was_ever_published"),
        "last_known": deepcopy(session.get("last_known", {})),
    }


def summarize_reasons(items: list[dict[str, Any]]) -> dict[str, int]:
    reasons = Counter()

    for item in items:
        reason = clean_string(item.get("state_reason")) or "unknown"
        reasons[reason] += 1

    return dict(sorted(reasons.items()))


def empty_plan() -> dict[str, Any]:
    return {
        "to_build": [],
        "to_rebuild": [],
        "to_deprecate": [],
        "to_remove": [],
        "to_skip": [],
        "counts": {
            "to_build": 0,
            "to_rebuild": 0,
            "to_deprecate": 0,
            "to_remove": 0,
            "to_skip": 0,
            "total": 0,
        },
        "reason_summaries": {
            "to_build": {},
            "to_rebuild": {},
            "to_deprecate": {},
            "to_remove": {},
            "to_skip": {},
        },
    }


def generate_plan(classification: Any, context: Any | None = None) -> dict[str, Any]:
    plan = empty_plan()
    sessions = classification_sessions(classification)

    for session_id in sorted(sessions):
        session = sessions[session_id]
        action = action_for_session(session)
        item = plan_item(session_id, session, action)
        plan[action].append(item)

    for group in ACTION_GROUPS:
        plan["counts"][group] = len(plan[group])
        plan["reason_summaries"][group] = summarize_reasons(plan[group])

    plan["counts"]["total"] = sum(plan["counts"][group] for group in ACTION_GROUPS)

    if isinstance(classification, dict):
        plan["classification_as_of"] = classification.get("classification_as_of")
        plan["source_feed_suspect"] = classification.get("source_feed_suspect", False)
        plan["duplicate_conflicts"] = deepcopy(classification.get("duplicate_conflicts", []))

    if isinstance(context, dict):
        plan["context"] = {
            "repo_root": context.get("repo_root"),
            "paths": deepcopy(context.get("paths", {})),
        }

    return plan
