"""Read-only observer, gate, and captain-instruction context for one project."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
from typing import TYPE_CHECKING, Any

from . import io as runtime_io
from . import observer, records, spacedock

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence

    from .config import RuntimeConfig
    from .state import RuntimeState

MAX_PROJECT_EVENTS = 100
MAX_PROJECT_OBSERVERS = 3
MAX_ACTIVE_CHILD_OBSERVERS = 3
MAX_SEMANTIC_LINE = 112
SEMANTIC_CURRENT_HORIZON_SEC = 15 * 60
SEMANTIC_BURST_EPSILON_SEC = 2
MAX_PRIMARY_ACTIVITY_NODES = 5

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
_TASK_DIRECTIVE_RE = re.compile(
    r"^(?:add|append|build|compare|create|design|diagnose|fix|implement|inspect|make|"
    r"prepare|remove|replace|review|revise|run|test|update|verify|write)\b",
    re.IGNORECASE,
)
_SEMANTIC_FACT_TYPES = {
    "steer": "user_message",
    "prepared_dispatch": "prepared_dispatch",
    "task_started": "work_birth",
    "task_result": "work_result",
    "outcome": "result",
    "gate": "gate_decision",
    "checkpoint": "result",
    "decision": "decision",
    "test_result": "result",
    "ask_resolution": "decision",
}
_DISPATCH_BUILD_RE = re.compile(r"^\s*spacedock\s+dispatch\s+build(?:\s+(.*))?$", re.IGNORECASE)
# This is transcript grammar from the dispatch contract, not a location we create or write.
_DISPATCH_DIRECTORY = "/tmp/spacedock-dispatch"  # noqa: S108
_DISPATCH_FILE_PREFIX = f"{_DISPATCH_DIRECTORY}/spacedock-ensign-"
_DISPATCH_ARTIFACT_RE = re.compile(
    re.escape(_DISPATCH_FILE_PREFIX) + r"[A-Za-z0-9][A-Za-z0-9._-]*\.md"
)
_DISPATCH_VALUE_OPTIONS = {
    "--checklist-file",
    "--host",
    "--stage",
    "--stamp",
    "--workflow-dir",
}


def _semantic_id(prefix: str, *parts: object) -> str:
    payload = "\x1f".join(str(part) for part in parts).encode("utf-8", "replace")
    return f"{prefix}:{hashlib.sha256(payload).hexdigest()[:16]}"


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
    child_activity_fallback: bool = False,
) -> dict[str, Any] | None:
    signature = _transcript_signature(transcript_path)
    cached = observer.read_sidecar(config, harness, sid)
    cached_payload = cached if isinstance(cached, dict) else {}
    raw_cached_model = cached_payload.get("model")
    cached_model = raw_cached_model if isinstance(raw_cached_model, dict) else {}
    if not refresh:
        observed_at = cached_payload.get("observed_at")
        goal = cached_payload.get("goal")
        if not isinstance(observed_at, (int, float)) or not isinstance(goal, str):
            return None
        model_metadata = dict(cached_model)
        model_metadata["status"] = (
            "cached" if cached_payload.get("transcript") == signature else "cached-stale"
        )
        return {
            "goal": goal,
            "stage": cached_payload.get("stage"),
            "block": cached_payload.get("block"),
            "reason": cached_payload.get("reason"),
            "model": model_metadata,
            "observed_at": observed_at,
            "snapshot_status": model_metadata["status"],
        }

    caller = observer.CodexGoalModel(config, child_assignment=child_activity_fallback)
    result = observer.analyze(
        config,
        state,
        transcript_path,
        now=now,
        window_sec=config.window_hours * 3600,
        model=caller,
    )
    if child_activity_fallback and result.get("goal") == observer.NO_GOAL:
        result["goal"] = observer.derive_child_assignment(config, transcript_path, caller)
        if result["goal"] != observer.NO_GOAL:
            result["reason"] = "derived-from-readable-child-activity"
    model_metadata = caller.metadata()
    sidecar = {
        **result,
        "model": model_metadata,
        "transcript": signature,
        "observed_at": now,
    }
    observer.write_sidecar(config, harness, sid, sidecar)
    return {
        **result,
        "model": model_metadata,
        "observed_at": now,
        "snapshot_status": "refreshed",
    }


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
        "intent_promotable": _intent_promotable(text, title),
    }
    lower = text.casefold()
    for tag, markers in _DIRECTIVE_TAGS:
        if any(marker in lower for marker in markers):
            event["steering_tag"] = tag
            event["tag_source"] = "explicit user-role wording"
            break
    return event


def _intent_promotable(text: str, title: str) -> bool:
    """Reject rows that cannot stand alone as a useful semantic directive."""
    normalized = re.sub(r"[^a-z0-9]+", " ", title.casefold()).strip()
    if normalized in {
        "continue",
        "do it",
        "go ahead",
        "no",
        "ok",
        "okay",
        "why do we need that",
        "why do we need this",
        "yes",
    }:
        return False
    lowered = text.lstrip().casefold()
    stripped_title = title.strip()
    looks_like_non_intent = (
        re.match(r"^[,.;:)}\]]", stripped_title) is not None
        or re.match(
            r"^(?:raise\s+[a-z_][a-z0-9_]*\s*\(|(?:find|ls|cat|sed|rg)\s+(?:~?/|\.\.?/))",
            stripped_title,
            re.IGNORECASE,
        )
        is not None
        or re.match(r"^(?:saved|wrote|written|created)\b.*\s(?:to|at)\s+/", lowered) is not None
    )
    if looks_like_non_intent:
        return False
    if lowered.startswith(
        (
            "command failed",
            "error:",
            "exception:",
            "fatal:",
            "traceback (most recent call last)",
        )
    ):
        return False
    if re.match(
        r"^(?:\.?\.?/|\.venv/|python(?:3)?\s|uv\s+run\s|npm\s|pytest(?:\s|$))",
        lowered,
    ):
        return False
    words = re.findall(r"[a-z0-9]+", normalized)
    return len(words) >= 3 and len(normalized) >= 12


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


def _task_assignment(text: str, artifact: str) -> str:
    """Select the current task directive, not a preceding status sentence."""
    if artifact:
        return ""
    candidates: list[tuple[int, int, str]] = []
    for index, raw in enumerate(text.splitlines()):
        line = raw.strip().lstrip("#*- ").strip()
        if not line or line.startswith(("```", "Message Type:", "Task name:", "Sender:")):
            continue
        task_match = re.match(r"^Task:\s*(.+)$", line, re.IGNORECASE)
        if task_match:
            candidates.append((4, index, task_match.group(1)))
            continue
        if _TASK_DIRECTIVE_RE.match(line):
            priority = 5 if "stage report" in line.casefold() else 3
            candidates.append((priority, index, line))
    if candidates:
        _priority, _index, chosen = max(candidates, key=lambda item: (item[0], -item[1]))
        return _semantic_line(chosen, MAX_SEMANTIC_LINE)
    return _semantic_line(text, MAX_SEMANTIC_LINE)


def _record_timestamp(record: dict[str, Any]) -> float | None:
    message = record.get("message")
    message_ts = message.get("timestamp") if isinstance(message, dict) else None
    return records.parse_ts(record.get("timestamp") or message_ts or "")


def _dispatch_identity(command_line: str) -> tuple[str, str, str] | None:
    match = _DISPATCH_BUILD_RE.match(command_line)
    if match is None:
        return None
    try:
        tokens = shlex.split(match.group(1) or "")
    except ValueError:
        return None
    slug = ""
    stage = ""
    workflow_binding = ""
    index = 0
    while index < len(tokens):
        part = tokens[index]
        if part in {"|", "&&", ";"} or part.startswith((">", "1>", "2>")):
            break
        if part in _DISPATCH_VALUE_OPTIONS:
            value = tokens[index + 1] if index + 1 < len(tokens) else ""
            if part == "--stage" and spacedock.SD_STAGE_RE.fullmatch(value):
                stage = value
            elif part == "--workflow-dir":
                workflow_binding = value
            index += 2
            continue
        if part.startswith("-"):
            index += 1
            continue
        if not slug and spacedock.SD_STAGE_RE.fullmatch(part):
            slug = part
        index += 1
    return (workflow_binding, slug, stage) if slug else None


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


def _dispatch_artifact(text: str) -> str:
    match = _DISPATCH_ARTIFACT_RE.search(text)
    return match.group(0) if match is not None else ""


def _dispatch_artifact_identity(artifact: str) -> tuple[str, str] | None:
    if not artifact.startswith(_DISPATCH_FILE_PREFIX) or not artifact.endswith(".md"):
        return None
    name = artifact[len(_DISPATCH_FILE_PREFIX) : -len(".md")]
    slug, separator, stage = name.rpartition("-")
    if not separator or not spacedock.SD_STAGE_RE.fullmatch(slug):
        return None
    if not spacedock.SD_STAGE_RE.fullmatch(stage):
        return None
    return slug, stage


def _dispatch_file_assignment(artifact: str) -> str:
    """Read the bounded human work title from one exact dispatch artifact."""
    if _dispatch_artifact_identity(artifact) is None:
        return ""
    prefix = "You are working on:"
    for raw in runtime_io.iter_bounded_text_lines(
        artifact,
        max_lines=40,
        per_line_bytes=2048,
    ):
        line = raw.strip()
        if line.startswith(prefix):
            return records.safe_text(line[len(prefix) :].strip(), MAX_SEMANTIC_LINE)
    return ""


def _subagent_specs(arguments: dict[str, Any]) -> list[tuple[str, str, str, str]]:
    specs: list[tuple[str, str, str, str]] = []
    task = arguments.get("task")
    if isinstance(task, str) and task.strip():
        contributor = arguments.get("agent") or arguments.get("name") or ""
        binding = arguments.get("work_item") or arguments.get("task_id") or ""
        specs.append((task, str(contributor), str(binding), _dispatch_artifact(task)))
    batch = arguments.get("tasks")
    if isinstance(batch, list):
        for item in batch:
            if not isinstance(item, dict):
                continue
            value = item.get("task")
            if not isinstance(value, str) or not value.strip():
                continue
            contributor = item.get("agent") or item.get("name") or ""
            binding = item.get("work_item") or item.get("task_id") or ""
            specs.append((value, str(contributor), str(binding), _dispatch_artifact(value)))
    return specs


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


def _result_text(message: dict[str, Any]) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return records.safe_text(content, 16_000)
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and isinstance(block.get("text"), str):
            parts.append(block["text"])
    return records.safe_text("\n".join(parts), 16_000)


def _paired_results(transcript: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for record in transcript:
        message = record.get("message")
        if not isinstance(message, dict) or message.get("role") != "toolResult":
            continue
        call_id = message.get("toolCallId")
        if isinstance(call_id, str):
            results[call_id] = {
                "succeeded": message.get("isError") is not True,
                "text": _result_text(message),
                "at": _record_timestamp(record),
            }
    return results


def _dispatch_count(command: str) -> int:
    return sum(_dispatch_identity(line) is not None for line in command.splitlines())


def _dispatch_events(
    command: str,
    *,
    at: float,
    result: dict[str, Any] | None,
    harness: str,
    sid: str,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for command_line in command.splitlines():
        identity = _dispatch_identity(command_line)
        if identity is None:
            continue
        workflow_binding, slug, stage = identity
        title = slug + (f" → {stage}" if stage else " dispatched")
        events.append(
            {
                "at": at,
                "kind": "prepared_dispatch",
                "phase": "Spacedock dispatch preparation",
                "title": title,
                "source": "Pi bash tool call"
                + (" and paired result" if result is not None else ""),
                "harness": harness,
                "sid": sid,
                "entity": slug,
                "workflow_binding": workflow_binding,
                "stage": stage,
                "dispatch_artifact": (f"{_DISPATCH_FILE_PREFIX}{slug}-{stage}.md" if stage else ""),
                "dispatch_artifact_prefix": f"{_DISPATCH_FILE_PREFIX}{slug}-",
                "succeeded": result.get("succeeded") if result is not None else None,
            }
        )
    return events


def _validation_event(
    result: dict[str, Any] | None,
    *,
    at: float,
    harness: str,
    sid: str,
) -> dict[str, Any] | None:
    if not result or result.get("succeeded") is not True:
        return None
    match = re.search(r"(?<!\d)(\d+)\s+passed(?:\s+in\s+[\d.]+s)?", str(result.get("text", "")))
    if match is None:
        return None
    count = int(match.group(1))
    return {
        "at": at,
        "kind": "outcome",
        "phase": "validation result",
        "title": f"{count} validation checks passed",
        "source": "Pi bash tool call and paired successful result",
        "harness": harness,
        "sid": sid,
        "checks_passed": count,
    }


def _subagent_category(combined: str) -> str:
    if re.match(r"^(?:review|inspect)\b", combined):
        return (
            "Implementation review completed"
            if "implementation" in combined
            else "Technical review completed"
        )
    if re.match(r"^implement\b", combined):
        return "Implementation pass completed"
    if re.match(r"^(?:design|write\b.*\bdesign)\b", combined):
        return "Design result produced"
    if re.match(r"^(?:perform\s+)?(?:independent\s+)?acceptance\b", combined):
        return "Independent acceptance completed"
    return ""


def _subagent_result_counts(text: str, tasks: list[str]) -> tuple[int, int]:
    completed = re.search(r"(?:children|tasks?):\s*(\d+)\s+completed", text, re.IGNORECASE)
    failed = re.search(r"(\d+)\s+failed", text, re.IGNORECASE)
    completed_count = int(completed.group(1)) if completed else len(tasks)
    failed_count = int(failed.group(1)) if failed else 0
    return completed_count, failed_count


def _subagent_result_title(tasks: list[str], result: dict[str, Any]) -> str:
    if _subagent_result_pending(result):
        return ""
    text = str(result.get("text", ""))
    lowered = text.casefold()
    if "acceptance cannot be requested explicitly" in lowered or (
        "cannot supply" in lowered and "reviewer result" in lowered
    ):
        return ""
    combined = " ".join(tasks).casefold()
    if result.get("succeeded") is not True:
        return "Independent acceptance was unavailable" if "acceptance" in combined else ""
    title = _subagent_category(combined)
    if not title:
        return ""
    contributors, failures = _subagent_result_counts(text, tasks)
    if contributors > 1:
        title += f" by {contributors} contributors"
    if failures:
        title += f" with {failures} contributor failure"
        if failures != 1:
            title += "s"
    return title


def _subagent_result_pending(result: dict[str, Any]) -> bool:
    text = str(result.get("text", "")).casefold()
    return any(marker in text for marker in ("detached", "running in the background"))


def _subagent_events(
    arguments: dict[str, Any],
    *,
    call_key: str,
    at: float,
    result: dict[str, Any] | None,
    harness: str,
    sid: str,
) -> list[dict[str, Any]]:
    specs = _subagent_specs(arguments)
    tasks = [spec[0] for spec in specs]
    if not specs:
        return []
    rows: list[dict[str, Any]] = []
    for index, (task, contributor, binding, artifact) in enumerate(specs):
        assignment = _task_assignment(task, artifact)
        title = assignment or _semantic_line(task, MAX_SEMANTIC_LINE)
        if not title:
            continue
        rows.append(
            {
                "at": at,
                "kind": "task_started",
                "phase": "ordinary subagent task",
                "title": title,
                "source": "Pi subagent task label",
                "harness": harness,
                "sid": sid,
                "lineage": f"{call_key}:{index}",
                "work_item_binding": binding,
                "contributor_ref": contributor,
                "dispatch_artifact": artifact,
                "assignment": assignment,
                "worker_kind": "ensign" if artifact else "subagent",
                "stage": "started",
            }
        )
    if result is None or _subagent_result_pending(result):
        return rows
    result_title = _subagent_result_title(tasks, result)
    result_at = result.get("at")
    outcome_at = float(result_at) if isinstance(result_at, (int, float)) else at
    text = str(result.get("text", ""))
    completed = re.search(r"(?:children|tasks?):\s*(\d+)\s+completed", text, re.IGNORECASE)
    failed = re.search(r"(\d+)\s+failed", text, re.IGNORECASE)
    complete_count = int(completed.group(1)) if completed else len(tasks)
    failure_count = int(failed.group(1)) if failed else 0
    if len(tasks) == 1 or (complete_count == len(tasks) and failure_count == 0):
        for index, (task, contributor, binding, artifact) in enumerate(specs):
            item_title = result_title or _subagent_result_title([task], result)
            if not item_title and artifact and result.get("succeeded") is True:
                item_title = "Dispatch result returned"
            if not item_title:
                continue
            rows.append(
                {
                    "at": outcome_at,
                    "kind": "task_result",
                    "phase": "ordinary subagent result",
                    "title": item_title,
                    "source": "Pi subagent task label and paired result",
                    "harness": harness,
                    "sid": sid,
                    "lineage": f"{call_key}:{index}",
                    "work_item_binding": binding,
                    "contributor_ref": contributor,
                    "dispatch_artifact": artifact,
                    "assignment": _task_assignment(task, artifact),
                    "worker_kind": "ensign" if artifact else "subagent",
                    "stage": "completed",
                }
            )
    elif result_title:
        rows.append(
            {
                "at": outcome_at,
                "kind": "outcome",
                "phase": "ordinary subagent batch result",
                "title": result_title,
                "source": "Pi subagent batch call and paired result",
                "harness": harness,
                "sid": sid,
                "contributors": len(tasks),
            }
        )
    return rows


def _tool_call_events(
    block: dict[str, Any],
    *,
    at: float,
    results: dict[str, dict[str, Any]],
    harness: str,
    sid: str,
) -> list[dict[str, Any]]:
    call_id = block.get("id")
    call_key = call_id if isinstance(call_id, str) else ""
    arguments = block.get("arguments")
    args = arguments if isinstance(arguments, dict) else {}
    result = results.get(call_key)
    if block.get("name") == "bash":
        command = args.get("command")
        dispatches = _dispatch_events(
            command if isinstance(command, str) else "",
            at=at,
            result=result,
            harness=harness,
            sid=sid,
        )
        validation = _validation_event(result, at=at, harness=harness, sid=sid)
        return dispatches + ([validation] if validation is not None else [])
    if block.get("name") != "subagent":
        return []
    return _subagent_events(
        args,
        call_key=call_key,
        at=at,
        result=result,
        harness=harness,
        sid=sid,
    )


def _tool_support(
    block: dict[str, Any], results: dict[str, dict[str, Any]]
) -> dict[str, int] | None:
    name = block.get("name")
    if name not in {"bash", "subagent"}:
        return None
    support = {"tool_calls": 1, "dispatch_builds": 0, "subagent_calls": 0, "pending_subagents": 0}
    arguments = block.get("arguments")
    args = arguments if isinstance(arguments, dict) else {}
    if name == "bash" and isinstance(args.get("command"), str):
        support["dispatch_builds"] = _dispatch_count(args["command"])
    if name != "subagent" or not _subagent_tasks(args):
        return support
    support["subagent_calls"] = 1
    call_id = block.get("id")
    pair = results.get(call_id) if isinstance(call_id, str) else None
    pending = pair is None or _subagent_result_pending(pair)
    support["pending_subagents"] = int(pending)
    return support


def _assistant_tool_calls(
    transcript: list[dict[str, Any]],
) -> Iterator[tuple[float, dict[str, Any]]]:
    for record in transcript:
        message = record.get("message")
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        content = message.get("content")
        at = _record_timestamp(record)
        if not isinstance(content, list) or at is None:
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "toolCall":
                yield at, block


def _work_evidence(
    config: RuntimeConfig,
    transcript_path: str,
    harness: str,
    sid: str,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Demonstrated Pi results plus counts for suppressed supporting telemetry."""
    stats = {
        "tool_calls": 0,
        "dispatch_builds": 0,
        "subagent_calls": 0,
        "pending_subagents": 0,
        "suppressed_tool_calls": 0,
        "collapsed_contributors": 0,
    }
    if harness != "pi":
        return [], stats
    transcript = _work_records(config, transcript_path)
    results = _paired_results(transcript)

    events: list[dict[str, Any]] = []
    for at, block in _assistant_tool_calls(transcript):
        support = _tool_support(block, results)
        if support is None:
            continue
        for key, value in support.items():
            stats[key] += value
        found = _tool_call_events(
            block,
            at=at,
            results=results,
            harness=harness,
            sid=sid,
        )
        for event in found:
            artifact = str(event.get("dispatch_artifact") or "")
            assignment = _dispatch_file_assignment(artifact)
            if assignment:
                event["assignment"] = assignment
                event["source"] = (
                    str(event.get("source") or "") + " and bounded dispatch artifact title"
                )
        events.extend(found)
        if not found:
            stats["suppressed_tool_calls"] += 1
        for event in found:
            stats["collapsed_contributors"] += max(0, int(event.get("contributors", 1)) - 1)
    return events, stats


def work_events(
    config: RuntimeConfig,
    transcript_path: str,
    harness: str,
    sid: str,
) -> list[dict[str, Any]]:
    """Demonstrated Pi results; supporting tool and lifecycle facts stay suppressed."""
    return _work_evidence(config, transcript_path, harness, sid)[0]


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
    workflow_binding: str,
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
        "workflow_binding": workflow_binding,
        "entity": slug,
        "decision": decision,
        "by": current.get("by", ""),
        "target_stage": current.get("target_stage", ""),
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
    elif block == "application" and body.startswith("target-stage:"):
        current["target_stage"] = body[len("target-stage:") :].strip().strip("\"'")
    return gate_stage


def gate_events(
    config: RuntimeConfig,
    lines: list[str],
    slug: str,
    workflow: str,
    harness: str,
    sid: str,
    *,
    workflow_binding: str | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """All timestamped gate decisions and the untimestamped briefing count."""
    events: list[dict[str, Any]] = []
    current: dict[str, str] = {}
    block = ""
    gate_stage = ""
    briefings = 0

    def flush() -> None:
        event = _gate_event(
            config,
            current,
            slug,
            workflow,
            workflow_binding or workflow,
            harness,
            sid,
        )
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
            found, prepared = gate_events(
                config,
                lines,
                slug,
                str(workflow["name"]),
                harness,
                sid,
                workflow_binding=str(workflow_dir),
            )
            events.extend(found)
            briefings += prepared
    return events, briefings


def _prepared_dispatches(events: list[dict[str, Any]]) -> list[tuple[str, str, str, str, str]]:
    prepared: list[tuple[str, str, str, str, str]] = []
    for event in events:
        if event.get("kind") != "prepared_dispatch":
            continue
        artifact = str(event.get("dispatch_artifact") or "")
        prefix = str(event.get("dispatch_artifact_prefix") or "")
        workflow = str(event.get("workflow_binding") or "")
        entity = str(event.get("entity") or "")
        stage = str(event.get("stage") or "")
        if workflow and entity and (artifact or prefix):
            prepared.append((artifact, prefix, workflow, entity, stage))
    return prepared


def _artifact_bindings(
    artifact: str, prepared: list[tuple[str, str, str, str, str]]
) -> set[tuple[str, str, str]]:
    bindings: set[tuple[str, str, str]] = set()
    for exact, prefix, workflow, entity, prepared_stage in prepared:
        if exact and artifact == exact:
            bindings.add((workflow, entity, prepared_stage))
            continue
        if not artifact.startswith(prefix) or not artifact.endswith(".md"):
            continue
        stage = artifact[len(prefix) : -len(".md")]
        if stage and spacedock.SD_STAGE_RE.fullmatch(stage):
            bindings.add((workflow, entity, stage))
    return bindings


def _bind_dispatch_artifacts(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Bind a consumed dispatch file only to its exact prepared artifact."""
    prepared = _prepared_dispatches(events)

    normalized: list[dict[str, Any]] = []
    for source_event in events:
        event = dict(source_event)
        artifact = str(event.get("dispatch_artifact") or "")
        identity = _dispatch_artifact_identity(artifact)
        if event.get("kind") in {"task_started", "task_result"} and identity is not None:
            entity, stage = identity
            event.update(
                {
                    "entity": entity,
                    "stage": stage,
                    "title": (
                        f"{entity} · {stage} result returned"
                        if event.get("kind") == "task_result"
                        else f"{entity} · {stage} dispatched"
                    ),
                    "source": str(event.get("source") or "")
                    + " and structured dispatch artifact path",
                }
            )
        bindings = _artifact_bindings(artifact, prepared)
        if event.get("kind") in {"task_started", "task_result"} and len(bindings) == 1:
            workflow, entity, stage = next(iter(bindings))
            event.update(
                {
                    "workflow_binding": workflow,
                    "entity": entity,
                    "stage": stage,
                    "title": (
                        f"{entity} · {stage} result returned"
                        if event.get("kind") == "task_result"
                        else f"{entity} · {stage} dispatched"
                    ),
                    "source": str(event.get("source") or "") + " and exact prepared-dispatch match",
                }
            )
        normalized.append(event)
    return normalized


def _semantic_work_identity(
    source_event: dict[str, Any], raw_kind: str
) -> tuple[str, str, str, str]:
    binding = str(source_event.get("work_item_binding") or "")
    if raw_kind in {"task_started", "task_result"} and source_event.get("entity"):
        workflow_binding = str(source_event.get("workflow_binding") or "")
        artifact = str(source_event.get("dispatch_artifact") or "")
        work_item_id = (
            _semantic_id("workflow-item", workflow_binding, source_event["entity"])
            if workflow_binding
            else _semantic_id("workflow-item-artifact", artifact)
        )
        label = str(source_event["entity"])
        if source_event.get("stage"):
            label += f" · {source_event['stage']}"
        return work_item_id, "workflow_item", label, binding
    if raw_kind in {"prepared_dispatch", "gate"} and source_event.get("entity"):
        workflow_binding = str(source_event.get("workflow_binding") or "unbound-workflow")
        return (
            _semantic_id("workflow-item", workflow_binding, source_event["entity"]),
            "workflow_item",
            str(source_event["entity"]),
            binding,
        )
    if raw_kind not in {"task_started", "task_result"} or not source_event.get("lineage"):
        return "", "unknown", "", binding
    work_item_id = (
        _semantic_id("work-item", "bound", binding)
        if binding
        else _semantic_id("work-item", "one-off", source_event["lineage"])
    )
    return (
        work_item_id,
        "unknown" if binding else "one_off",
        str(source_event.get("title") or "one-off work"),
        binding,
    )


def _semantic_actor_claim(source_event: dict[str, Any], raw_kind: str) -> str:
    if raw_kind == "steer":
        return "timestamped non-meta user-role record"
    if raw_kind in {"prepared_dispatch", "task_started", "task_result", "outcome"}:
        return "session assistant/tool exchange"
    if raw_kind == "gate":
        return str(source_event.get("by") or "decision author unavailable")
    return ""


def _semantic_fact_from_event(
    source_event: dict[str, Any], raw_kind: str, fact_type: str, work_item_id: str
) -> dict[str, Any]:
    fact_id = _semantic_id(
        "fact",
        raw_kind,
        source_event.get("harness"),
        source_event.get("sid"),
        source_event.get("at"),
        source_event.get("workflow_binding"),
        source_event.get("entity"),
        source_event.get("lineage"),
        source_event.get("title"),
    )
    fact: dict[str, Any] = {
        "fact_id": fact_id,
        "at": source_event.get("at"),
        "type": fact_type,
        "summary": source_event.get("title"),
        "scope": "workflow" if raw_kind == "gate" else "session",
        "actor_claim": _semantic_actor_claim(source_event, raw_kind),
        "work_item_id": work_item_id or None,
        "evidence": {"source": source_event.get("source"), "confidence": "exact"},
    }
    for key in ("stage", "decision", "by", "target_stage", "assignment", "worker_kind"):
        if source_event.get(key) not in (None, ""):
            fact[key] = source_event[key]
    lineage = str(source_event.get("lineage") or "")
    if lineage:
        call_key = lineage.rsplit(":", 1)[0]
        fact["batch_id"] = _semantic_id(
            "batch", source_event.get("harness"), source_event.get("sid"), call_key
        )
    return fact


def _semantic_intent(fact: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    projection_id = _semantic_id("intent", fact["fact_id"])
    projection = {
        "projection_id": projection_id,
        "at": fact["at"],
        "kind": "operator_intent",
        "summary": fact["summary"],
        "derived_from": fact["fact_id"],
        "confidence": "derived-deterministic",
    }
    relation = {
        "from": projection_id,
        "to": fact["fact_id"],
        "type": "derived_from",
        "confidence": "exact",
        "provenance": "bounded semantic-line extraction",
    }
    return projection, relation


def _append_semantic_intent(
    fact: dict[str, Any],
    intent_summaries: set[str],
    intent_projections: list[dict[str, Any]],
    relations: list[dict[str, Any]],
) -> None:
    projection, relation = _semantic_intent(fact)
    summary_key = str(projection["summary"]).casefold().strip()
    if summary_key in intent_summaries:
        return
    intent_summaries.add(summary_key)
    intent_projections.append(projection)
    relations.append(relation)


def _semantic_source_binding(
    source_event: dict[str, Any], work_item_kind: str, binding: str
) -> dict[str, str]:
    if binding:
        return {"source": "explicit task binding", "value": binding}
    if source_event.get("dispatch_artifact"):
        return {
            "source": "structured Spacedock dispatch artifact",
            "value": str(source_event["dispatch_artifact"]),
        }
    if work_item_kind != "workflow_item":
        return {"source": "Pi subagent call", "value": str(source_event.get("lineage") or "")}
    value = (
        str(source_event.get("workflow_binding") or "unbound-workflow")
        + ":"
        + str(source_event.get("entity") or "")
    )
    return {"source": "Spacedock entity slug", "value": value}


def _semantic_work_relation(
    source_event: dict[str, Any], raw_kind: str, fact_id: str, work_item_id: str
) -> dict[str, Any] | None:
    relation_type = {
        "prepared_dispatch": "binds_to",
        "task_started": "binds_to",
        "task_result": "progresses",
        "gate": "decides",
    }.get(raw_kind)
    if relation_type is None:
        return None
    return {
        "from": fact_id,
        "to": work_item_id,
        "type": relation_type,
        "confidence": "structural" if raw_kind in {"prepared_dispatch", "gate"} else "exact",
        "provenance": source_event.get("source"),
    }


def _semantic_observer_facts(observers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    for observer_row in observers:
        observed_at = observer_row.get("observed_at")
        goal = observer_row.get("goal")
        if not isinstance(observed_at, (int, float)) or not isinstance(goal, str):
            continue
        facts.append(
            {
                "fact_id": _semantic_id(
                    "observer",
                    observer_row.get("harness"),
                    observer_row.get("sid"),
                    observed_at,
                    goal,
                ),
                "at": observed_at,
                "type": "observer_snapshot",
                "summary": goal,
                "scope": "session",
                "actor_claim": "model-derived observer snapshot",
                "work_item_id": None,
                "evidence": {
                    "source": observer_row.get("source"),
                    "confidence": "derived",
                    "snapshot_status": observer_row.get("snapshot_status"),
                },
            }
        )
    return facts


def _semantic_trail_heads(
    fact_by_work_item: dict[str, list[dict[str, Any]]], facts: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    heads: list[dict[str, Any]] = []
    for work_item_id, item_facts in fact_by_work_item.items():
        newest = max(item_facts, key=lambda fact: float(fact.get("at") or 0))
        status = {
            "prepared_dispatch": "prepared",
            "work_birth": "requested",
            "work_result": "outcome",
            "gate_decision": "decision",
        }.get(str(newest.get("type")), "latest")
        heads.append(
            {
                "work_item_id": work_item_id,
                "status": status,
                "latest_meaningful_event": newest["fact_id"],
            }
        )
    at_by_id = {fact["fact_id"]: float(fact.get("at") or 0) for fact in facts}
    return sorted(
        heads,
        key=lambda head: at_by_id.get(str(head["latest_meaningful_event"]), 0),
        reverse=True,
    )


def _semantic_assignments(
    fact_by_work_item: dict[str, list[dict[str, Any]]],
    work_items: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    assignments: list[dict[str, Any]] = []
    for work_item_id, item_facts in fact_by_work_item.items():
        births = [fact for fact in item_facts if fact.get("type") == "work_birth"]
        if not births:
            continue
        birth = max(births, key=lambda fact: float(fact.get("at") or 0))
        latest = max(item_facts, key=lambda fact: float(fact.get("at") or 0))
        completed = latest.get("type") == "work_result"
        work_item = work_items[work_item_id]
        assignments.append(
            {
                "projection_id": _semantic_id("assignment", work_item_id, birth["fact_id"]),
                "work_item_id": work_item_id,
                "assignment_fact": birth["fact_id"],
                "state_fact": latest["fact_id"],
                "at": latest.get("at"),
                "state": "completed" if completed else "awaiting_result",
                "worker_kind": birth.get("worker_kind") or "subagent",
                "assignment": birth.get("assignment") or work_item.get("label"),
                "contributor_refs": list(work_item.get("contributor_refs") or []),
            }
        )
    return sorted(assignments, key=lambda row: float(row.get("at") or 0), reverse=True)


def _activity_nodes(representatives: list[dict[str, Any]]) -> list[dict[str, Any]]:
    clusters: list[list[dict[str, Any]]] = []
    for representative in sorted(representatives, key=lambda row: float(row.get("at") or 0)):
        if not clusters:
            clusters.append([representative])
            continue
        cluster = clusters[-1]
        first = cluster[0]
        same_batch = bool(representative.get("batch_id")) and representative.get(
            "batch_id"
        ) == first.get("batch_id")
        near = (
            float(representative.get("at") or 0) - float(first.get("at") or 0)
            <= SEMANTIC_BURST_EPSILON_SEC
        )
        if not (same_batch or near):
            cluster = []
            clusters.append(cluster)
        cluster.append(representative)

    nodes: list[dict[str, Any]] = []
    for cluster in clusters:
        cluster.sort(key=lambda row: float(row.get("at") or 0), reverse=True)
        work_item_ids = [
            work_item_id for member in cluster for work_item_id in member["work_item_ids"]
        ]
        if len(cluster) == 1:
            node = dict(cluster[0])
            node["kind"] = "work"
        else:
            node = {
                "kind": "burst",
                "at": cluster[0].get("at"),
                "count": len(cluster),
                "work_item_ids": work_item_ids,
                "latest_event": cluster[0].get("latest_event"),
                "retry_count": sum(int(member.get("retry_count") or 0) for member in cluster),
            }
        nodes.append(node)
    return sorted(nodes, key=lambda row: float(row.get("at") or 0), reverse=True)[
        :MAX_PRIMARY_ACTIVITY_NODES
    ]


def _semantic_activity_projection(
    work_items: dict[str, dict[str, Any]],
    trail_heads: list[dict[str, Any]],
    facts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Bound the primary graph without turning old requests into current state."""
    if not facts:
        return {"nodes": [], "historical_unresolved": 0}
    fact_by_id = {str(fact["fact_id"]): fact for fact in facts}
    head_facts = [
        fact_by_id[str(head["latest_meaningful_event"])]
        for head in trail_heads
        if str(head.get("latest_meaningful_event")) in fact_by_id
    ]
    newest_work_at = max((float(fact.get("at") or 0) for fact in head_facts), default=0)
    current_after = newest_work_at - SEMANTIC_CURRENT_HORIZON_SEC

    def label_key(work_item_id: str) -> str:
        label = str(work_items.get(work_item_id, {}).get("label") or "")
        return re.sub(r"[^a-z0-9]+", " ", label.casefold()).strip()

    current: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for head in trail_heads:
        latest = fact_by_id.get(str(head.get("latest_meaningful_event")))
        if latest is None or float(latest.get("at") or 0) < current_after:
            continue
        if head.get("status") not in {"prepared", "requested", "outcome", "decision"}:
            continue
        current.append((head, latest))

    # An exact repeated assignment is one work lane with retry history, not a
    # new primary node each time the orchestrator redispatches it.
    grouped: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {}
    for head, latest in current:
        key = label_key(str(head["work_item_id"])) or str(head["work_item_id"])
        grouped.setdefault(key, []).append((head, latest))
    representatives: list[dict[str, Any]] = []
    for members in grouped.values():
        members.sort(key=lambda pair: float(pair[1].get("at") or 0), reverse=True)
        head, latest = members[0]
        representatives.append(
            {
                "at": latest.get("at"),
                "batch_id": latest.get("batch_id"),
                "status": head.get("status"),
                "work_item_ids": [str(pair[0]["work_item_id"]) for pair in members],
                "latest_event": latest["fact_id"],
                "retry_count": len(members) - 1,
            }
        )
    nodes = _activity_nodes(representatives)

    represented_keys = {
        label_key(work_item_id) for node in nodes for work_item_id in node.get("work_item_ids", [])
    }
    historical_keys = {
        label_key(str(head["work_item_id"]))
        for head in trail_heads
        if head.get("status") == "requested"
        and label_key(str(head["work_item_id"])) not in represented_keys
    }
    return {
        "nodes": nodes,
        "historical_unresolved": len(historical_keys),
        "current_after": current_after,
    }


def _semantic_model(
    events: list[dict[str, Any]], observers: list[dict[str, Any]]
) -> dict[str, Any]:
    """Immutable source facts, explicit relations, and replaceable projections."""
    ordered = sorted(
        _bind_dispatch_artifacts(events), key=lambda event: float(event.get("at") or 0)
    )
    facts: list[dict[str, Any]] = []
    work_items: dict[str, dict[str, Any]] = {}
    contributors: dict[str, dict[str, Any]] = {}
    relations: list[dict[str, Any]] = []
    intent_projections: list[dict[str, Any]] = []
    intent_summaries: set[str] = set()
    fact_by_work_item: dict[str, list[dict[str, Any]]] = {}
    for source_event in ordered:
        raw_kind = str(source_event.get("kind") or "")
        fact_type = _SEMANTIC_FACT_TYPES.get(raw_kind)
        if fact_type is None:
            continue
        work_item_id, work_item_kind, work_item_label, binding = _semantic_work_identity(
            source_event, raw_kind
        )
        fact = _semantic_fact_from_event(source_event, raw_kind, fact_type, work_item_id)
        fact_id = str(fact["fact_id"])
        facts.append(fact)
        if raw_kind == "steer" and source_event.get("intent_promotable") is True:
            _append_semantic_intent(fact, intent_summaries, intent_projections, relations)
        if not work_item_id:
            continue
        work_item = work_items.setdefault(
            work_item_id,
            {
                "work_item_id": work_item_id,
                "label": work_item_label,
                "kind": work_item_kind,
                "source_bindings": [],
                "contributor_refs": [],
            },
        )
        if raw_kind in {"task_started", "task_result"} and source_event.get("dispatch_artifact"):
            work_item["label"] = work_item_label
        source_binding = _semantic_source_binding(source_event, work_item_kind, binding)
        if source_binding not in work_item["source_bindings"]:
            work_item["source_bindings"].append(source_binding)
        fact_by_work_item.setdefault(work_item_id, []).append(fact)
        work_relation = _semantic_work_relation(source_event, raw_kind, fact_id, work_item_id)
        if work_relation is not None:
            relations.append(work_relation)
        contributor_ref = str(source_event.get("contributor_ref") or "")
        if contributor_ref:
            contributor_id = _semantic_id("contributor", contributor_ref)
            contributors.setdefault(
                contributor_id,
                {
                    "contributor_id": contributor_id,
                    "source_label": contributor_ref,
                    "identity_status": "unverified source label",
                },
            )
            if contributor_id not in work_item["contributor_refs"]:
                work_item["contributor_refs"].append(contributor_id)
            relations.append(
                {
                    "from": contributor_id,
                    "to": work_item_id,
                    "type": "contributes_to",
                    "confidence": "source-labeled",
                    "provenance": source_event.get("source"),
                }
            )

    facts.extend(_semantic_observer_facts(observers))
    facts.sort(key=lambda fact: float(fact.get("at") or 0), reverse=True)
    trail_heads = _semantic_trail_heads(fact_by_work_item, facts)
    assignments = _semantic_assignments(fact_by_work_item, work_items)
    activity = _semantic_activity_projection(work_items, trail_heads, facts)
    return {
        "facts": facts,
        "work_items": list(work_items.values()),
        "contributors": list(contributors.values()),
        "relations": relations,
        "projections": {
            "operator_intents": intent_projections,
            "trail_heads": trail_heads,
            "assignments": assignments,
            "activity": activity,
            "steering_episodes": [],
            "candidate_goal_shifts": [],
        },
    }


def _active_child_assignments(
    config: RuntimeConfig,
    state: RuntimeState,
    session: Mapping[str, Any],
    *,
    now: float,
    refresh: bool,
) -> list[dict[str, Any]]:
    hierarchy = session.get("subagent_hierarchy")
    if not isinstance(hierarchy, list):
        return []
    assignments: list[dict[str, Any]] = []
    for raw_child in hierarchy[:MAX_ACTIVE_CHILD_OBSERVERS]:
        if not isinstance(raw_child, dict):
            continue
        child = records.as_dict(raw_child)
        row: dict[str, Any] = {
            "name": records.safe_text(child.get("name") or "subagent", 70),
            "depth": child.get("depth"),
            "parent_name": child.get("parent_name"),
            "observer_sid": child.get("observer_sid"),
        }
        workflow_entity = child.get("workflow_entity")
        workflow_stage = child.get("workflow_stage")
        if isinstance(workflow_entity, str) and isinstance(workflow_stage, str):
            row.update(
                {
                    "workflow_entity": workflow_entity,
                    "workflow_stage": workflow_stage,
                }
            )
        exact = child.get("assignment")
        if isinstance(exact, str) and exact:
            assignments.append(
                {
                    **row,
                    "assignment": exact,
                    "confidence": "exact",
                    "source": child.get("assignment_status") or "exact parent dispatch",
                }
            )
            continue
        child_sid = child.get("observer_sid")
        if not isinstance(child_sid, str) or not child_sid:
            assignments.append({**row, "assignment": None, "confidence": "unavailable"})
            continue
        transcript_path = observer.resolve_transcript(config, state, "codex", child_sid)
        if transcript_path is None:
            assignments.append({**row, "assignment": None, "confidence": "unavailable"})
            continue
        observed = _observe_session(
            config,
            state,
            transcript_path,
            "codex",
            child_sid,
            now=now,
            refresh=refresh,
            child_activity_fallback=True,
        )
        if observed is None:
            assignments.append({**row, "assignment": None, "confidence": "unavailable"})
            continue
        goal = observed.get("goal")
        if not isinstance(goal, str) or not goal or goal == observer.NO_GOAL:
            assignments.append({**row, "assignment": None, "confidence": "unavailable"})
            continue
        assignments.append(
            {
                **row,
                "assignment": goal,
                "confidence": "derived",
                "source": (
                    "bounded child observer snapshot"
                    if observed.get("snapshot_status") == "refreshed"
                    else "cached child observer snapshot"
                ),
                "observed_at": observed.get("observed_at"),
                "snapshot_status": observed.get("snapshot_status"),
            }
        )
    return assignments


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
    child_assignments: list[dict[str, Any]] = []
    support_totals = {
        "tool_calls": 0,
        "dispatch_builds": 0,
        "subagent_calls": 0,
        "pending_subagents": 0,
        "suppressed_tool_calls": 0,
        "collapsed_contributors": 0,
    }
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
        if focus is not None and harness == "codex":
            child_assignments = _active_child_assignments(
                config,
                state,
                session,
                now=now,
                refresh=refresh,
            )
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
            refresh=refresh and focus is not None,
        )
        if result is not None:
            observers.append(
                {
                    **identity,
                    **result,
                    "source": "cached observer snapshot"
                    if str(result.get("snapshot_status", "")).startswith("cached")
                    else "bounded transcript and entity state",
                }
            )
        events.extend(instruction_events(config, transcript_path, harness, sid))
        work_rows, work_support = _work_evidence(config, transcript_path, harness, sid)
        events.extend(work_rows)
        for support_key in support_totals:
            support_totals[support_key] += work_support[support_key]
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
            event.get("lineage"),
            event.get("work_item_binding"),
        )
        deduped.setdefault(key, event)
    timeline = sorted(deduped.values(), key=lambda event: float(event["at"]), reverse=True)
    timeline = timeline[:MAX_PROJECT_EVENTS]
    gate_count = sum(1 for event in timeline if event["kind"] == "gate")
    steer_count = sum(1 for event in timeline if event["kind"] == "steer")
    work_count = sum(
        1
        for event in timeline
        if event["kind"] in {"prepared_dispatch", "task_started", "task_result", "outcome"}
    )
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
        "semantic": _semantic_model(timeline, observers),
        "child_assignments": child_assignments,
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
                "support": support_totals,
                "unavailable": unavailable,
                "omitted": omitted_rows,
            },
        },
    }
