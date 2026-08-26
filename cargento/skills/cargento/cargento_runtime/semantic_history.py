"""Restart-safe, bounded semantic work history for the project cockpit."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
from typing import TYPE_CHECKING, Any

from . import records

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from .config import RuntimeConfig
    from .state import RuntimeState

SCHEMA_VERSION = 1
MAX_PROJECTS = 20
MAX_EVENTS_PER_PROJECT = 64
STORE_NAME = "semantic-work-history.json"

_FACT_EVENT_TYPES = {
    "user_message": "operator_direction",
    "observer_snapshot": "observed_goal",
    "prepared_dispatch": "assignment",
    "work_birth": "assignment",
    "work_result": "progress_head",
    "gate_decision": "gate_decision",
    "decision": "gate_decision",
    "result": "result",
}


def workflow_work_item_id(workflow: str, entity: str) -> str:
    """Return the durable task identity shared by assignments and projections."""
    workflow_digest = hashlib.blake2b(workflow.encode(), digest_size=10).hexdigest()
    return f"workflow:{workflow_digest}:{entity}"


def store_path(config: RuntimeConfig) -> str:
    return os.path.join(config.state_home, STORE_NAME)


def _read(config: RuntimeConfig) -> dict[str, Any]:
    try:
        with open(store_path(config), "rb") as handle:
            raw = handle.read(config.state_read_cap_bytes + 1)
        if len(raw) > config.state_read_cap_bytes:
            return {"v": SCHEMA_VERSION, "projects": {}}
        value = json.loads(raw)
    except (OSError, ValueError, RecursionError):
        return {"v": SCHEMA_VERSION, "projects": {}}
    if not isinstance(value, dict) or not isinstance(value.get("projects"), dict):
        return {"v": SCHEMA_VERSION, "projects": {}}
    return value


def _write(config: RuntimeConfig, payload: dict[str, Any]) -> bool:
    target = store_path(config)
    tmp = f"{target}.{os.getpid()}.tmp"
    try:
        os.makedirs(config.state_home, mode=0o700, exist_ok=True)
        handle_fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(handle_fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, separators=(",", ":"))
        os.replace(tmp, target)
    except (OSError, ValueError):
        with contextlib.suppress(OSError, ValueError):
            os.unlink(tmp)
        return False
    return True


def _source_identity(fact: Mapping[str, Any]) -> str:
    branch = fact.get("branch")
    if isinstance(branch, dict):
        harness = records.safe_text(branch.get("harness"), 32)
        sid = records.safe_text(branch.get("sid"), 128)
        if harness and sid:
            return f"{harness}:{sid}"
    evidence = fact.get("evidence")
    source = evidence.get("source") if isinstance(evidence, dict) else ""
    return records.safe_text(source, 160) or "source unavailable"


def _event_from_fact(
    fact: Mapping[str, Any],
    work_items: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any] | None:
    fact_type = str(fact.get("type") or "")
    source_kind = str(fact.get("source_kind") or "")
    event_type = "checkpoint" if source_kind == "checkpoint" else _FACT_EVENT_TYPES.get(fact_type)
    if event_type is None:
        return None
    fact_id = records.safe_text(fact.get("fact_id"), 160)
    summary = records.safe_text(fact.get("summary"), 240)
    at = fact.get("at")
    if not fact_id or not summary or not isinstance(at, (int, float)):
        return None
    work_item_id = records.safe_text(fact.get("work_item_id"), 160)
    item = work_items.get(work_item_id, {}) if work_item_id else {}
    branch = fact.get("branch")
    evidence = fact.get("evidence")
    normalized_fact = {
        key: value
        for key, value in fact.items()
        if key
        in {
            "fact_id",
            "at",
            "type",
            "source_kind",
            "summary",
            "scope",
            "actor_claim",
            "work_item_id",
            "stage",
            "decision",
            "target_stage",
            "assignment",
            "worker_kind",
            "batch_id",
        }
    }
    if isinstance(branch, dict):
        normalized_fact["branch"] = dict(branch)
    if isinstance(evidence, dict):
        normalized_fact["evidence"] = dict(evidence)
    return {
        "event_id": fact_id,
        "event_type": event_type,
        "at": float(at),
        "source_identity": _source_identity(fact),
        "source_ref": fact_id,
        "work_binding": work_item_id or None,
        "summary": summary,
        "fact": normalized_fact,
        "work_item": dict(item) if item else None,
    }


def _final_output_events(sessions: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for session in sessions:
        output = session.get("last_output")
        if session.get("state") == "working" or not isinstance(output, str) or not output.strip():
            continue
        harness = records.safe_text(session.get("harness"), 32)
        sid = records.safe_text(session.get("sid"), 128)
        at = session.get("last_activity")
        if not harness or not sid or not isinstance(at, (int, float)):
            continue
        exact = "\n".join(records.safe_text(line, 4096) for line in output.splitlines())[:4096]
        summary = records.safe_text(" ".join(exact.split()), 112)
        event_id = f"final:{harness}:{sid}:{float(at):.6f}"
        work_item_id = f"session:{harness}:{sid}"
        fact = {
            "fact_id": event_id,
            "at": float(at),
            "type": "result",
            "summary": summary,
            "scope": "session",
            "actor_claim": "assistant final-answer record",
            "work_item_id": work_item_id,
            "evidence": {
                "source": "assistant final_answer followed by terminal turn state",
                "confidence": "exact",
            },
            "detail": exact,
        }
        found.append(
            {
                "event_id": event_id,
                "event_type": "final_output",
                "at": float(at),
                "source_identity": f"{harness}:{sid}",
                "source_ref": event_id,
                "work_binding": work_item_id,
                "summary": summary,
                "fact": fact,
                "work_item": {
                    "work_item_id": work_item_id,
                    "label": records.safe_text(session.get("title"), 112) or "Last output",
                    "kind": "session_result",
                    "source_bindings": [
                        {"source": "session identity", "value": f"{harness}:{sid}"}
                    ],
                    "contributor_refs": [],
                },
            }
        )
    return found


def _assignment_events(
    assignments: Iterable[Mapping[str, Any]], *, observed_at: float
) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for assignment in assignments:
        summary = records.safe_text(assignment.get("assignment"), 240)
        if assignment.get("confidence") != "exact" or not summary:
            continue
        observer_sid = records.safe_text(assignment.get("observer_sid"), 128)
        worker = records.safe_text(assignment.get("name"), 70) or "subagent"
        entity = records.safe_text(assignment.get("workflow_entity"), 112)
        stage = records.safe_text(assignment.get("workflow_stage"), 70)
        workflow = records.safe_text(assignment.get("workflow_binding"), 1024)
        identity = f"{observer_sid}\0{worker}\0{workflow}\0{entity}\0{stage}\0{summary}"
        digest = hashlib.blake2b(identity.encode(), digest_size=12).hexdigest()
        event_id = f"assignment:{digest}"
        work_item_id = (
            workflow_work_item_id(workflow, entity)
            if entity and workflow
            else (f"workflow-unbound:{entity}" if entity else f"assignment:{digest}")
        )
        fact: dict[str, Any] = {
            "fact_id": event_id,
            "at": observed_at,
            "type": "prepared_dispatch",
            "source_kind": "child_assignment",
            "summary": summary,
            "scope": "session",
            "actor_claim": "current structured child assignment",
            "work_item_id": work_item_id,
            "assignment": summary,
            "evidence": {
                "source": records.safe_text(assignment.get("source"), 160),
                "confidence": "exact",
            },
        }
        if stage:
            fact["stage"] = stage
        if workflow:
            fact["workflow_binding"] = workflow
            fact["workflow_entity"] = entity
        source_identity = f"codex:{observer_sid}" if observer_sid else f"worker:{worker}"
        found.append(
            {
                "event_id": event_id,
                "event_type": "assignment",
                "at": observed_at,
                "source_identity": source_identity,
                "source_ref": event_id,
                "work_binding": work_item_id,
                "summary": summary,
                "fact": fact,
                "work_item": {
                    "work_item_id": work_item_id,
                    "label": entity.replace("-", " ").capitalize() if entity else summary,
                    "kind": "workflow_item" if entity else "one_off",
                    "source_bindings": [
                        {
                            "source": "structured child assignment",
                            "value": (
                                f"{workflow}:{entity}" if workflow and entity else entity or summary
                            ),
                        }
                    ],
                    "contributor_refs": [],
                },
            }
        )
    return found


def _merge(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {
        str(event.get("event_id")): event
        for event in existing
        if isinstance(event, dict) and event.get("event_id")
    }
    for event in sorted(incoming, key=lambda row: float(row.get("at") or 0)):
        merged_event = dict(event)
        event_type = merged_event["event_type"]
        source_identity = merged_event["source_identity"]
        work_binding = merged_event.get("work_binding")
        if event_type == "progress_head" and work_binding:
            by_id = {
                key: prior
                for key, prior in by_id.items()
                if not (
                    prior.get("event_type") == "progress_head"
                    and prior.get("work_binding") == work_binding
                )
            }
        if event_type == "assignment" and work_binding:
            fact = merged_event.get("fact")
            entity = fact.get("workflow_entity") if isinstance(fact, dict) else None
            if entity and str(work_binding).startswith("workflow:"):
                legacy_binding = f"workflow:{entity}"
                by_id = {
                    key: prior
                    for key, prior in by_id.items()
                    if not (
                        prior.get("event_type") == "assignment"
                        and prior.get("source_identity") == source_identity
                        and prior.get("work_binding") == legacy_binding
                    )
                }
        if event_type == "observed_goal":
            same_source = [
                prior
                for prior in by_id.values()
                if prior.get("event_type") in {"observed_goal", "goal_shift"}
                and prior.get("source_identity") == source_identity
            ]
            newest = max(same_source, key=lambda row: float(row.get("at") or 0), default=None)
            if newest and newest.get("summary") == event.get("summary"):
                by_id.pop(str(newest.get("event_id")), None)
            elif newest:
                merged_event["event_type"] = "goal_shift"
        by_id[merged_event["event_id"]] = merged_event
    return sorted(by_id.values(), key=lambda row: float(row.get("at") or 0), reverse=True)[
        :MAX_EVENTS_PER_PROJECT
    ]


def update(
    config: RuntimeConfig,
    state: RuntimeState,
    project: str,
    semantic: Mapping[str, Any],
    sessions: Iterable[Mapping[str, Any]],
    assignments: Iterable[Mapping[str, Any]] = (),
    *,
    now: float | None = None,
) -> dict[str, Any]:
    """Merge current source-backed meaning into the durable bounded history."""
    facts = semantic.get("facts")
    work_rows = semantic.get("work_items")
    work_items = (
        {
            str(row.get("work_item_id")): row
            for row in work_rows
            if isinstance(row, dict) and row.get("work_item_id")
        }
        if isinstance(work_rows, list)
        else {}
    )
    incoming = (
        [
            event
            for event in (
                _event_from_fact(fact, work_items) for fact in facts if isinstance(fact, dict)
            )
            if event is not None
        ]
        if isinstance(facts, list)
        else []
    )
    incoming.extend(_final_output_events(sessions))
    if isinstance(now, (int, float)):
        incoming.extend(_assignment_events(assignments, observed_at=float(now)))
    with state.semantic_history_lock:
        payload = _read(config)
        projects = payload["projects"]
        prior = projects.get(project)
        existing = prior.get("events", []) if isinstance(prior, dict) else []
        merged = _merge(existing if isinstance(existing, list) else [], incoming)
        cursors: dict[str, dict[str, Any]] = {}
        for event in merged:
            source = str(event.get("source_identity") or "source unavailable")
            cursor = cursors.get(source)
            if cursor is None or float(event.get("at") or 0) > float(cursor.get("at") or 0):
                cursors[source] = {
                    "at": event.get("at"),
                    "event_id": event.get("event_id"),
                }
        projects[project] = {"events": merged, "cursors": cursors}
        if len(projects) > MAX_PROJECTS:
            ranked = sorted(
                projects,
                key=lambda key: max(
                    (float(row.get("at") or 0) for row in projects[key].get("events", [])),
                    default=0,
                ),
                reverse=True,
            )[:MAX_PROJECTS]
            payload["projects"] = {key: projects[key] for key in ranked}
        persisted = _write(config, payload)
    return {"events": merged, "cursors": cursors, "persisted": persisted}
