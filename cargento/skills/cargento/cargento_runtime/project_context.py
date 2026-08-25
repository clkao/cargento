"""Read-only observer, gate, and captain-instruction context for one project."""

from __future__ import annotations

import json
import os
import re
import shlex
from typing import TYPE_CHECKING, Any

from . import io as runtime_io
from . import observer, records, spacedock

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from .config import RuntimeConfig
    from .state import RuntimeState

MAX_PROJECT_EVENTS = 100
MAX_PROJECT_OBSERVERS = 3
MAX_SEMANTIC_LINE = 112

_DIRECTIVE_PREFIX_RE = re.compile(
    r"^(?:please\s+|captain(?:\s+(?:says|asks|adds|clarifies|refines|clarification|refinement|correction))?\s*[:—-]\s*)+",
    re.IGNORECASE,
)
_DIRECTIVE_TAGS = (
    ("corrected", ("correction", "correct this", "fix the")),
    ("reframed", ("reframe", "refinement", "clarification", "change direction")),
    ("answered", ("answer to", "answered")),
    ("generated", ("new acceptance", "add a new", "create a new")),
)
_DISPATCH_BUILD_RE = re.compile(r"^\s*spacedock\s+dispatch\s+build(?:\s+(.*))?$", re.IGNORECASE)
_DISPATCH_VALUE_OPTIONS = {
    "--checklist-file",
    "--host",
    "--stage",
    "--stamp",
    "--workflow-dir",
}


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
    """One timestamped user-role message, excluding known tool/meta records."""
    if not isinstance(record, dict):
        return None
    message = observer.parse_message_record(record)
    if message is None or message.get("role") != "user":
        return None
    at = records.parse_ts(record.get("timestamp") or "")
    text = message["text"].strip()
    if at is None or not text:
        return None
    title = _semantic_line(text, min(MAX_SEMANTIC_LINE, config.observer_goal_cap_chars))
    if not title:
        return None
    event: dict[str, Any] = {
        "at": at,
        "kind": "steer",
        "phase": "user-role instruction",
        "title": title,
        "source": "timestamped non-meta user-role record",
        "harness": harness,
        "sid": sid,
    }
    lower = text.casefold()
    for tag, markers in _DIRECTIVE_TAGS:
        if any(marker in lower for marker in markers):
            event["steering_tag"] = tag
            event["tag_source"] = "explicit user-role wording"
            break
    return event


def _semantic_line(text: str, limit: int) -> str:
    """A short directive/task label from real text, without its envelope prose."""
    candidates: list[str] = []
    for raw in text.splitlines():
        line = raw.strip().lstrip("#*- ").strip()
        if not line or line.startswith(("<", "```", "Message Type:", "Task name:", "Sender:")):
            continue
        line = _DIRECTIVE_PREFIX_RE.sub("", line)
        if not line:
            continue
        candidates.append(line)
    if not candidates:
        return ""
    chosen = candidates[0]
    sentence = re.split(r"(?<=[.!?])\s+", chosen, maxsplit=1)[0]
    sentence = re.sub(r"\s+", " ", sentence).strip()
    return records.safe_text(sentence, limit)


def _record_timestamp(record: dict[str, Any]) -> float | None:
    message = record.get("message")
    message_ts = message.get("timestamp") if isinstance(message, dict) else None
    return records.parse_ts(record.get("timestamp") or message_ts or "")


def _dispatch_identity(command_line: str) -> tuple[str, str] | None:
    match = _DISPATCH_BUILD_RE.match(command_line)
    if match is None:
        return None
    try:
        tokens = shlex.split(match.group(1) or "")
    except ValueError:
        return None
    slug = ""
    stage = ""
    index = 0
    while index < len(tokens):
        part = tokens[index]
        if part in {"|", "&&", ";"} or part.startswith((">", "1>", "2>")):
            break
        if part in _DISPATCH_VALUE_OPTIONS:
            value = tokens[index + 1] if index + 1 < len(tokens) else ""
            if part == "--stage" and spacedock.SD_STAGE_RE.fullmatch(value):
                stage = value
            index += 2
            continue
        if part.startswith("-"):
            index += 1
            continue
        if not slug and spacedock.SD_STAGE_RE.fullmatch(part):
            slug = part
        index += 1
    return (slug, stage) if slug else None


def _subagent_tasks(arguments: dict[str, Any]) -> list[str]:
    tasks: list[str] = []
    task = arguments.get("task")
    if isinstance(task, str) and task.strip():
        tasks.append(task)
    batch = arguments.get("tasks")
    if isinstance(batch, list):
        for item in batch:
            if not isinstance(item, dict):
                continue
            value = item.get("task")
            if isinstance(value, str) and value.strip():
                tasks.append(value)
    return tasks


def _work_records(config: RuntimeConfig, transcript_path: str) -> list[dict[str, Any]]:
    transcript: list[dict[str, Any]] = []
    bounded = list(
        runtime_io.reverse_lines(
            config,
            transcript_path,
            max_bytes=config.turn_scan_max_bytes,
        )
    )
    for raw_bytes in reversed(bounded):
        raw = raw_bytes.decode("utf-8", "replace")
        if not raw or not raw.lstrip().startswith("{"):
            continue
        try:
            record = json.loads(raw)
        except (ValueError, json.JSONDecodeError, RecursionError):
            continue
        if isinstance(record, dict):
            transcript.append(record)
    return transcript


def _paired_results(transcript: list[dict[str, Any]]) -> dict[str, bool]:
    results: dict[str, bool] = {}
    for record in transcript:
        message = record.get("message")
        if not isinstance(message, dict) or message.get("role") != "toolResult":
            continue
        call_id = message.get("toolCallId")
        if isinstance(call_id, str):
            results[call_id] = message.get("isError") is not True
    return results


def _dispatch_events(
    command: str,
    *,
    at: float,
    succeeded: bool | None,
    harness: str,
    sid: str,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for command_line in command.splitlines():
        identity = _dispatch_identity(command_line)
        if identity is None:
            continue
        slug, stage = identity
        action = "Built" if succeeded is True else "Attempted"
        title = f"{action} dispatch package · {slug}"
        if stage:
            title += f" · {stage}"
        events.append(
            {
                "at": at,
                "kind": "work",
                "phase": "Spacedock dispatch build",
                "title": title,
                "source": "Pi bash tool call"
                + (" and paired result" if succeeded is not None else ""),
                "harness": harness,
                "sid": sid,
                "entity": slug,
            }
        )
    return events


def _subagent_event(
    arguments: dict[str, Any],
    *,
    at: float,
    succeeded: bool | None,
    harness: str,
    sid: str,
) -> dict[str, Any] | None:
    tasks = _subagent_tasks(arguments)
    if not tasks:
        return None
    if len(tasks) > 1:
        title = f"{len(tasks)} background tasks contributed"
    else:
        task = _semantic_line(tasks[0], MAX_SEMANTIC_LINE)
        if not task:
            return None
        if succeeded is None:
            title = f"Background task started · {task}"
        elif succeeded:
            title = f"Background task returned · {task}"
        else:
            title = f"Background task failed · {task}"
    return {
        "at": at,
        "kind": "outcome" if succeeded is not None else "work",
        "phase": "ordinary subagent task and paired result"
        if succeeded is not None
        else "ordinary subagent task",
        "title": title,
        "source": "Pi subagent tool call" + (" and paired result" if succeeded is not None else ""),
        "harness": harness,
        "sid": sid,
        "contributors": len(tasks),
    }


def _tool_call_events(
    block: dict[str, Any],
    *,
    at: float,
    results: dict[str, bool],
    harness: str,
    sid: str,
) -> list[dict[str, Any]]:
    call_id = block.get("id")
    call_key = call_id if isinstance(call_id, str) else ""
    arguments = block.get("arguments")
    args = arguments if isinstance(arguments, dict) else {}
    if block.get("name") == "bash":
        command = args.get("command")
        if not isinstance(command, str):
            return []
        return _dispatch_events(
            command,
            at=at,
            succeeded=results.get(call_key),
            harness=harness,
            sid=sid,
        )
    if block.get("name") != "subagent":
        return []
    event = _subagent_event(
        args,
        at=at,
        succeeded=results.get(call_key),
        harness=harness,
        sid=sid,
    )
    return [event] if event is not None else []


def work_events(
    config: RuntimeConfig,
    transcript_path: str,
    harness: str,
    sid: str,
) -> list[dict[str, Any]]:
    """Meaningful Pi tool work; lifecycle/status-only calls stay suppressed."""
    if harness != "pi":
        return []
    transcript = _work_records(config, transcript_path)
    results = _paired_results(transcript)

    events: list[dict[str, Any]] = []
    for record in transcript:
        message = record.get("message")
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        at = _record_timestamp(record)
        if at is None:
            continue
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "toolCall":
                continue
            events.extend(
                _tool_call_events(
                    block,
                    at=at,
                    results=results,
                    harness=harness,
                    sid=sid,
                )
            )
    return events


def instruction_events(
    config: RuntimeConfig,
    transcript_path: str,
    harness: str,
    sid: str,
) -> list[dict[str, Any]]:
    """Timestamped non-meta user-role messages from the bounded transcript tail."""
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
    focus: tuple[str, str] | None = None,
) -> dict[str, Any]:
    """Observer results and a real project event log for exact-label sessions."""
    selected = [
        session
        for session in sessions
        if str(session.get("project") or "") == project and session.get("active") is True
    ]
    selected.sort(key=lambda item: float(item.get("last_activity") or 0), reverse=True)
    if focus is None:
        analysis_sessions = selected[:MAX_PROJECT_OBSERVERS]
        omitted = selected[MAX_PROJECT_OBSERVERS:]
        scope = "selected project"
        surrounding_active = 0
    else:
        analysis_sessions = [
            session
            for session in selected
            if (
                str(session.get("harness") or ""),
                str(session.get("sid") or ""),
            )
            == focus
        ]
        omitted = []
        scope = "focused session"
        surrounding_active = len(selected) - len(analysis_sessions)
    observers: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    unavailable: list[dict[str, str]] = []
    briefings = 0
    omitted_rows = [
        {
            "harness": str(session.get("harness") or ""),
            "sid": str(session.get("sid") or ""),
            "reason": f"bounded to {MAX_PROJECT_OBSERVERS} newest active sessions",
        }
        for session in omitted
    ]
    for session in analysis_sessions:
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
        events.extend(work_events(config, transcript_path, harness, sid))
        gate_rows, prepared = _gate_context(config, state, transcript_path, harness, sid)
        events.extend(gate_rows)
        briefings += prepared

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
    work_count = sum(1 for event in timeline if event["kind"] in {"work", "outcome"})
    return {
        "project": project,
        "focus": {
            "harness": focus[0],
            "sid": focus[1],
            "observed": any(
                row.get("harness") == focus[0] and row.get("sid") == focus[1] for row in observers
            ),
        }
        if focus
        else None,
        "observers": observers,
        "events": timeline,
        "sources": {
            "scope": scope,
            "surrounding_active": surrounding_active,
            "observer": {
                "live": len(observers),
                "unavailable": unavailable,
                "omitted": omitted_rows,
            },
            "gate": {
                "live": gate_count,
                "untimestamped_prepare": briefings,
                "status_history": "unavailable",
            },
            "steer": {
                "live": steer_count,
                "unavailable": unavailable,
                "omitted": omitted_rows,
            },
            "work": {
                "live": work_count,
                "unavailable": unavailable,
                "omitted": omitted_rows,
            },
        },
    }
