"""Read-only observer, gate, and captain-instruction context for one project."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Any

from . import io as runtime_io
from . import observer, records, spacedock

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from .config import RuntimeConfig
    from .state import RuntimeState

MAX_PROJECT_EVENTS = 100
MAX_PROJECT_OBSERVERS = 3


def _transcript_signature(transcript_path: str) -> dict[str, int] | None:
    try:
        info = os.stat(transcript_path)
    except OSError:
        return None
    return {"size": info.st_size, "mtime_ns": info.st_mtime_ns}


def _observe_session(
    config: RuntimeConfig,
    state: RuntimeState,
    transcript_path: str,
    harness: str,
    sid: str,
    *,
    now: float,
    refresh: bool,
) -> dict[str, Any]:
    signature = _transcript_signature(transcript_path)
    cached = observer.read_sidecar(config, harness, sid)
    cached_payload = cached if isinstance(cached, dict) else {}
    raw_cached_model = cached_payload.get("model")
    cached_model = raw_cached_model if isinstance(raw_cached_model, dict) else {}
    expected_model = {
        "provider": "codex-cli",
        "model": observer.OBSERVER_MODEL,
        "reasoning_effort": observer.OBSERVER_MODEL_REASONING_EFFORT,
    }
    reuse = (
        not refresh
        and signature is not None
        and cached_payload.get("transcript") == signature
        and cached_model
        and all(cached_model.get(key) == value for key, value in expected_model.items())
    )
    model: observer.ModelCaller | Callable[[str, str], str | None] | None
    caller: observer.CodexGoalModel | None = None
    if (
        reuse
        and cached_model.get("status") in {"used", "cached"}
        and isinstance(cached_payload.get("goal"), str)
    ):
        cached_goal = str(cached_payload["goal"])

        def cached_caller(_recent: str, _stage: str) -> str:
            return cached_goal

        model = cached_caller
        model_metadata = dict(cached_model)
        model_metadata["status"] = "cached"
    elif reuse:
        model = None
        model_metadata = dict(cached_model)
        model_metadata["status"] = "cached-fallback"
    else:
        caller = observer.CodexGoalModel(config)
        model = caller
        model_metadata = caller.metadata()
    result = observer.analyze(
        config,
        state,
        transcript_path,
        now=now,
        window_sec=config.window_hours * 3600,
        model=model,
    )
    if caller is not None:
        model_metadata = caller.metadata()
    sidecar = {
        **result,
        "model": model_metadata,
        "transcript": signature,
        "observed_at": now,
    }
    observer.write_sidecar(config, harness, sid, sidecar)
    return {**result, "model": model_metadata, "observed_at": now}


def _instruction_event(
    config: RuntimeConfig,
    record: Any,
    harness: str,
    sid: str,
) -> dict[str, Any] | None:
    """One timestamped external user message, excluding tool and meta records."""
    if not isinstance(record, dict) or record.get("isMeta") is True:
        return None
    message = records.message_dict(record)
    if message.get("role") != "user":
        return None
    record_type = record.get("type")
    if record_type not in {"message", "user"}:
        return None
    content = message.get("content")
    if isinstance(content, list) and any(
        isinstance(block, dict) and block.get("type") == "tool_result" for block in content
    ):
        return None
    at = records.parse_ts(record.get("timestamp") or "")
    text = records.extract_text(content).strip()
    if at is None or not text:
        return None
    title = records.safe_text(text.splitlines()[0], config.observer_goal_cap_chars)
    return {
        "at": at,
        "kind": "steer",
        "phase": "captain instruction",
        "title": title,
        "detail": f"{harness}:{sid}",
        "source": "transcript user message",
        "harness": harness,
        "sid": sid,
    }


def instruction_events(
    config: RuntimeConfig,
    transcript_path: str,
    harness: str,
    sid: str,
) -> list[dict[str, Any]]:
    """Timestamped user instructions from the bounded transcript tail."""
    events: list[dict[str, Any]] = []
    seen: set[tuple[float, str]] = set()
    for raw in runtime_io.read_tail(config, transcript_path):
        if not raw or not raw.lstrip().startswith("{"):
            continue
        try:
            record = json.loads(raw)
        except (ValueError, json.JSONDecodeError, RecursionError):
            continue
        event = _instruction_event(config, record, harness, sid)
        if event is None:
            continue
        key = (event["at"], event["title"])
        if key in seen:
            continue
        seen.add(key)
        events.append(event)
    return events


def _gate_event(
    config: RuntimeConfig,
    current: dict[str, str],
    slug: str,
    workflow: str,
    harness: str,
    sid: str,
) -> dict[str, Any] | None:
    at = records.parse_ts(current.get("at", ""))
    decision = current.get("decision", "")
    if at is None or not decision:
        return None
    stage = current.get("stage", "unknown stage")
    application = current.get("application", "")
    phase = "gate decision" + (f" · application {application}" if application else "")
    reason = records.safe_text(current.get("reason", ""), config.observer_block_cap_chars)
    detail = f"{workflow} · {harness}:{sid}"
    if reason:
        detail += f" · {reason}"
    return {
        "at": at,
        "kind": "gate",
        "phase": phase,
        "title": f"{slug} · {stage} · {decision}",
        "detail": detail,
        "source": "Spacedock entity gate frontmatter",
        "harness": harness,
        "sid": sid,
        "workflow": workflow,
        "entity": slug,
    }


def _gate_field(body: str, block: str, current: dict[str, str], gate_stage: str) -> str:
    if body.startswith("stage:") and block == "gate":
        gate_stage = body[len("stage:") :].strip().strip("\"'")
        current["stage"] = gate_stage
    elif block == "resolution":
        for key in ("at", "decision", "by", "reason"):
            if body.startswith(key + ":"):
                current[key] = body[len(key) + 1 :].strip().strip("\"'")
                break
    elif block == "application" and body.startswith("state:"):
        current["application"] = body[len("state:") :].strip().strip("\"'")
    return gate_stage


def gate_events(
    config: RuntimeConfig,
    lines: list[str],
    slug: str,
    workflow: str,
    harness: str,
    sid: str,
) -> tuple[list[dict[str, Any]], int]:
    """All timestamped gate decisions and the untimestamped briefing count."""
    events: list[dict[str, Any]] = []
    current: dict[str, str] = {}
    block = ""
    gate_stage = ""
    briefings = 0

    def flush() -> None:
        event = _gate_event(config, current, slug, workflow, harness, sid)
        if event is not None:
            events.append(event)

    for raw in lines:
        body = raw.strip()
        if body.startswith("- id: gate:"):
            flush()
            current = {}
            gate_stage = ""
            block = "gate"
        elif body.startswith("- id: gate-attempt:"):
            flush()
            current = {"stage": gate_stage} if gate_stage else {}
            block = "attempt"
        elif body == "briefing:":
            briefings += 1
            block = "briefing"
        elif body == "resolution:":
            block = "resolution"
        elif body == "application:":
            block = "application"
        else:
            gate_stage = _gate_field(body, block, current, gate_stage)
    flush()
    return events, briefings


def _gate_context(
    config: RuntimeConfig,
    state: RuntimeState,
    transcript_path: str,
    harness: str,
    sid: str,
) -> tuple[list[dict[str, Any]], int]:
    events: list[dict[str, Any]] = []
    briefings = 0
    boot = spacedock.transcript_boot(config, state, transcript_path)
    for workflow_dir in spacedock.workflow_dirs(config, boot):
        workflow = spacedock.read_workflow(config, state, workflow_dir)
        entity_dir = spacedock.boot_entity_dir(boot, workflow_dir)
        if workflow is None or not entity_dir:
            continue
        for slug, path, info in spacedock.entity_files(config, entity_dir):
            try:
                lines = spacedock.read_frontmatter(
                    config, path, config.spacedock_entity_bytes, info
                )
            except spacedock.SdMismatchError:
                continue
            found, prepared = gate_events(config, lines, slug, str(workflow["name"]), harness, sid)
            events.extend(found)
            briefings += prepared
    return events, briefings


def collect(
    config: RuntimeConfig,
    state: RuntimeState,
    sessions: Sequence[Mapping[str, Any]],
    project: str,
    *,
    now: float,
    refresh: bool = False,
) -> dict[str, Any]:
    """Observer results and a real project event log for exact-label sessions."""
    selected = [
        session
        for session in sessions
        if str(session.get("project") or "") == project and session.get("active") is True
    ]
    selected.sort(key=lambda item: float(item.get("last_activity") or 0), reverse=True)
    observers: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    unavailable: list[dict[str, str]] = []
    briefings = 0
    omitted = selected[MAX_PROJECT_OBSERVERS:]
    for session in selected[:MAX_PROJECT_OBSERVERS]:
        harness = str(session.get("harness") or "")
        sid = str(session.get("sid") or "")
        identity = {"harness": harness, "sid": sid}
        transcript_path = observer.resolve_transcript(config, state, harness, sid)
        if transcript_path is None:
            unavailable.append({**identity, "reason": "transcript reader unavailable"})
            continue
        result = _observe_session(
            config,
            state,
            transcript_path,
            harness,
            sid,
            now=now,
            refresh=refresh,
        )
        observers.append({**identity, **result, "source": "bounded transcript and entity state"})
        events.extend(instruction_events(config, transcript_path, harness, sid))
        gate_rows, prepared = _gate_context(config, state, transcript_path, harness, sid)
        events.extend(gate_rows)
        briefings += prepared
    unavailable.extend(
        {
            "harness": str(session.get("harness") or ""),
            "sid": str(session.get("sid") or ""),
            "reason": f"bounded to {MAX_PROJECT_OBSERVERS} newest active sessions",
        }
        for session in omitted
    )

    deduped: dict[tuple[object, ...], dict[str, Any]] = {}
    for event in events:
        key = (
            event.get("kind"),
            event.get("at"),
            event.get("title"),
            event.get("workflow"),
            event.get("entity"),
        )
        deduped.setdefault(key, event)
    timeline = sorted(deduped.values(), key=lambda event: float(event["at"]), reverse=True)
    timeline = timeline[:MAX_PROJECT_EVENTS]
    gate_count = sum(1 for event in timeline if event["kind"] == "gate")
    steer_count = sum(1 for event in timeline if event["kind"] == "steer")
    return {
        "project": project,
        "observers": observers,
        "events": timeline,
        "sources": {
            "observer": {"live": len(observers), "unavailable": unavailable},
            "gate": {
                "live": gate_count,
                "untimestamped_prepare": briefings,
                "status_history": "unavailable",
            },
            "steer": {"live": steer_count, "unavailable": unavailable},
        },
    }
