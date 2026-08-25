"""Codex rollout collection."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Any

# Absolute on the canonical top-level package: a sub-package cannot use
# parent-relative imports without tripping the repository's own TID252 rule.
from cargento_runtime import io as runtime_io
from cargento_runtime import records, sessions, transcripts, turns

if TYPE_CHECKING:
    from cargento_runtime.config import RuntimeConfig
    from cargento_runtime.sessions import Session
    from cargento_runtime.state import RuntimeState


def discover(config: RuntimeConfig, _state: RuntimeState) -> bool:
    """Whether a Codex sessions store is present."""
    return runtime_io.any_store_dir(config, "codex.sessions")


# Rollout tails examined for a quota snapshot, newest mtime first. Token
# events are frequent, so the snapshot is almost always in the newest file;
# the rest of the budget covers a file that was only just created.
_USAGE_FILE_CAP = 8
_CHILD_LIFECYCLE_FILE_CAP = 24
_CHILD_LIFECYCLE_BYTES = 128 * 1024
_CHILD_LIFECYCLE_EVENT_CAP = 12


def _usage_window(now: float, raw: Any) -> tuple[str, dict[str, Any]] | None:
    """One rate_limits window mapped onto the payload contract, or nothing."""
    win = records.as_dict(raw)
    pct = win.get("used_percent")
    minutes = win.get("window_minutes")
    if not isinstance(pct, (int, float)) or isinstance(pct, bool):
        return None
    if not isinstance(minutes, (int, float)) or isinstance(minutes, bool):
        return None
    # Codex names no windows, only durations: 300 minutes is the 5-hour
    # window, 10080 the weekly. Classify by length so a plan that carries
    # only one of them (prolite writes just the weekly) still maps.
    key = "fiveH" if minutes < 1440 else "week"
    shaped: dict[str, Any] = {"pct": max(0, min(100, round(pct)))}
    resets = win.get("resets_at")
    if isinstance(resets, (int, float)) and not isinstance(resets, bool) and resets > 0:
        shaped.update(sessions.reset_fields(now, resets))
    return key, shaped


def usage(
    config: RuntimeConfig,
    state: RuntimeState,
    now: float,
    window_hours: float,
) -> list[dict[str, Any]]:
    """The newest quota snapshot Codex left on disk, as one usage entry.

    Codex writes ``rate_limits`` beside every token count, so this is a read
    of what is already there: no network, no credential, and a snapshot only
    as fresh as the last active turn, which is why the entry carries ``asOf``.
    One entry for the whole store — the CLI reports account quota, not
    per-session quota.
    """
    del state
    files: list[tuple[float, str]] = []
    for fp in runtime_io.glob_stores(
        config,
        "codex.sessions",
        "*",
        "*",
        "*",
        "rollout-*.jsonl",
    ):
        try:
            files.append((os.path.getmtime(fp), fp))
        except OSError:
            continue
    best: tuple[float, dict[str, Any]] | None = None
    for _, fp in sorted(files, reverse=True)[:_USAGE_FILE_CAP]:
        snap = transcripts.analyze_codex_transcript(config, fp)["rate_limits"]
        if snap and (best is None or snap[0] > best[0]):
            best = snap
    # A snapshot older than the dashboard's own activity window describes
    # quota windows that have themselves reset; the band's empty state is
    # more honest than a number that old.
    if not best or not sessions.is_fresh(config, now, best[0], window_hours * 3600):
        return []
    epoch, limits = best
    entry: dict[str, Any] = {"harness": "codex", "state": "ok", "asOf": int(epoch)}
    for raw in (limits.get("primary"), limits.get("secondary")):
        mapped = _usage_window(now, raw)
        if mapped:
            entry.setdefault(mapped[0], mapped[1])
    if "fiveH" not in entry and "week" not in entry:
        return []
    return [entry]


def _subagent_rate(
    config: RuntimeConfig,
    path: str,
    now: float,
    scan: dict[str, Any] | None,
) -> int:
    """Recent Codex subagent output after its own task_started boundary.

    Takes the scan rather than making it: the caller needs the same scan for
    the child's model, and one child file must not be walked twice in a pass.
    """
    start = scan.get("last_start") if scan else None
    if not start:
        return 0
    info = transcripts.analyze_codex_transcript(config, path)
    recent: float = sum(
        tokens
        for epoch, tokens in info["usage_events"]
        if epoch >= start and sessions.is_fresh(config, now, epoch, config.rate_window_sec)
    )
    return round(recent / (config.rate_window_sec / 60))


def _child_lineage(
    sid: str,
    parent_sid: str,
    top_level: dict[str, tuple[float, str]],
    meta_by_sid: dict[str, dict[str, Any]],
) -> tuple[str, int, str | None]:
    """Resolve a child root, depth, and immediate named parent from recorded links."""
    immediate_parent = parent_sid
    depth = 1
    seen = {sid}
    while parent_sid not in top_level:
        parent_meta = meta_by_sid.get(parent_sid)
        next_parent = parent_meta.get("parent_session_id") if parent_meta is not None else None
        if not next_parent or next_parent in seen:
            break
        seen.add(parent_sid)
        parent_sid = next_parent
        depth += 1
    immediate_meta = meta_by_sid.get(immediate_parent)
    parent_name = (
        records.safe_text(immediate_meta.get("agent_label") or "subagent", 70)
        if depth > 1 and immediate_meta is not None
        else None
    )
    return parent_sid, depth, parent_name


def _child_lifecycle(
    config: RuntimeConfig,
    path: str,
    name: str,
    model: Any,
    depth: int,
    parent_name: str | None,
) -> list[dict[str, Any]]:
    """Bounded lifecycle signals written by one real Codex child rollout."""
    kinds = {
        "task_started": "subagent_task_started",
        "task_complete": "subagent_complete",
        "turn_aborted": "subagent_interrupted",
    }
    events: list[dict[str, Any]] = []
    for raw in runtime_io.reverse_lines(
        config,
        path,
        max_bytes=_CHILD_LIFECYCLE_BYTES,
        contains=b'"type"',
    ):
        try:
            row = records.as_dict(json.loads(raw))
        except (UnicodeDecodeError, ValueError):
            continue
        payload = records.as_dict(row.get("payload"))
        payload_type = payload.get("type")
        kind = (
            kinds.get(payload_type)
            if row.get("type") == "event_msg" and isinstance(payload_type, str)
            else None
        )
        at = records.parse_ts(row.get("timestamp"))
        if kind is None or at is None:
            continue
        events.append(
            {
                "at": at,
                "kind": kind,
                "name": name,
                "model": model,
                "depth": depth,
                "parent_name": parent_name,
                "source": "Codex child rollout lifecycle",
            }
        )
        if len(events) >= _CHILD_LIFECYCLE_EVENT_CAP:
            break
    return list(reversed(events))


def _rollouts(
    config: RuntimeConfig,
    state: RuntimeState,
) -> tuple[
    dict[str, tuple[float, str]],
    list[tuple[str, float, str, dict[str, Any]]],
    dict[str, dict[str, Any]],
]:
    """Read Codex rollout identity once and separate dashboard roots."""
    found: dict[str, tuple[float, str]] = {}
    rollouts: list[tuple[str, float, str, dict[str, Any]]] = []
    meta_by_sid: dict[str, dict[str, Any]] = {}
    for fp in runtime_io.glob_stores(
        config,
        "codex.sessions",
        "*",
        "*",
        "*",
        "rollout-*.jsonl",
    ):
        try:
            mtime = os.path.getmtime(fp)
        except OSError:
            continue
        meta = transcripts.codex_meta(config, state, fp)
        session_sid = meta.get("session_id") or os.path.basename(fp)[: -len(".jsonl")][-36:]
        sid = (meta.get("thread_id") or session_sid) if meta.get("subagent") else session_sid
        rollouts.append((sid, mtime, fp, meta))
        meta_by_sid[sid] = meta
        if not meta.get("subagent") and (session_sid not in found or mtime > found[session_sid][0]):
            found[session_sid] = (mtime, fp)
    return found, rollouts, meta_by_sid


def collect(
    config: RuntimeConfig,
    state: RuntimeState,
    now: float,
    window_hours: float,
    show_all: bool,
) -> list[Session]:
    # Resumes and subagent threads each write their own rollout file, so group
    # by the session_meta session_id rather than by file.
    # parent session_id -> running agents, recent child activity, and rate
    agent_data: dict[str, dict[str, Any]] = {}
    found, rollouts, meta_by_sid = _rollouts(config, state)
    lifecycle_paths = set(
        [
            fp
            for _, _, fp, meta in sorted(rollouts, key=lambda row: -row[1])
            if meta.get("subagent")
        ][:_CHILD_LIFECYCLE_FILE_CAP]
    )

    for sid, mtime, fp, meta in rollouts:
        if meta.get("subagent"):
            parent_sid = meta.get("parent_session_id") or sid
            # Codex nests worker threads. Only top-level sessions are dashboard
            # rows, so walk the recorded parent links and attach each descendant
            # to the real row that owns it. The previous direct-parent lookup
            # orphaned depth-2 rollouts even though both links were on disk.
            parent_sid, depth, parent_name = _child_lineage(
                sid,
                parent_sid,
                found,
                meta_by_sid,
            )
            data = agent_data.setdefault(
                parent_sid,
                {"agents": [], "activity": [], "rate": 0, "lifecycle": []},
            )
            # One scan, above both branches. The rate window is wider than the
            # working window today, so the rate branch happens to have scanned
            # every child the second branch renders — but that is two config
            # numbers agreeing, not an invariant, and a child's model must not
            # rest on it. Still gated on a child being inside one window or the
            # other, so a store full of finished threads is not re-walked.
            charged = sessions.is_fresh(config, now, mtime, config.rate_window_sec)
            rendered = sessions.is_fresh(config, now, mtime, config.working_threshold_sec)
            scan = turns.scan_turns(config, state, fp, "codex") if charged or rendered else None
            name = records.safe_text(meta.get("agent_label") or "subagent", 70)
            data["activity"].extend(
                [mtime] if sessions.is_fresh(config, now, mtime, window_hours * 3600) else []
            )
            if fp in lifecycle_paths and sessions.is_fresh(
                config,
                now,
                mtime,
                window_hours * 3600,
            ):
                data["lifecycle"].extend(
                    _child_lifecycle(
                        config,
                        fp,
                        name,
                        (scan or {}).get("model"),
                        depth,
                        parent_name,
                    )
                )
            if charged:
                data["rate"] += _subagent_rate(config, fp, now, scan)
            if rendered and scan and scan.get("turn_start") is not None:
                # The child's own rollout declares its own model; the page, not
                # the collector, decides whether it differs from the parent's.
                # Membership is present lifecycle, not mtime inference: Codex
                # writes task_complete/turn_aborted and scan_turns retires the
                # active turn on either boundary.
                data["agents"].append(
                    (
                        name,
                        mtime,
                        (scan or {}).get("model"),
                        turns.started_at(scan),
                        depth,
                        parent_name,
                    )
                )
            continue

    out: list[Session] = []
    for sid, (mtime, fp) in found.items():
        data = agent_data.get(sid) or {
            "agents": [],
            "activity": [],
            "rate": 0,
            "lifecycle": [],
        }
        agents = sorted(data["agents"], key=lambda a: -a[1])
        activity_sources = (mtime, *data["activity"])
        last_activity = sessions.newest_plausible(config, now, activity_sources)
        active = sessions.is_fresh(config, now, last_activity, window_hours * 3600)
        if not (active or show_all):
            continue
        info = transcripts.analyze_codex_transcript(config, fp) if active else None
        # Hoisted above `subagents` because the model is published beside them,
        # and kept behind the `if info` guard so a stale `?all=1` row still pays
        # for no scan. Such a row reports no model rather than an old one: the
        # collector has not read it this pass, and that is the honest reading.
        scan = turns.scan_turns(config, state, fp, "codex") if info else None
        last_event_sources = (info["last_event_ts"] if info else 0, *activity_sources)
        subagents = [
            {"name": label, "model": model, "started_at": started_at}
            for label, _, model, started_at, _, _ in agents
        ]
        hierarchy = [
            {
                "name": label,
                "model": model,
                "started_at": started_at,
                "depth": depth,
                "parent_name": parent_name,
            }
            for label, _, model, started_at, depth, parent_name in sorted(
                agents,
                key=lambda agent: (agent[4], -agent[1], agent[0]),
            )
        ]
        lifecycle = sorted(data["lifecycle"], key=lambda event: event["at"])[-48:]
        session_state, state_detail = "idle", "awaiting your message"
        if sessions.is_fresh(
            config,
            now,
            sessions.newest_plausible(config, now, last_event_sources),
            config.working_threshold_sec,
        ):
            session_state = "working"
            state_detail = sessions.working_detail(info, subagents)

        s = sessions.base_session(
            "codex",
            sid,
            sessions.project_from_cwd(
                config,
                transcripts.codex_meta(config, state, fp).get("cwd") or "",
            )
            or "codex",
        )
        s.update(
            {
                "title": (info or {}).get("title"),
                "last_prompt": ((info or {}).get("last_prompt") or "")[:140],
                "state": session_state,
                "state_detail": state_detail,
                "active": active,
                "last_activity": last_activity,
                # What retires a gate this session already answered. Codex reports
                # a gate through the event overlay, and the reducer only lets a
                # wait lapse when the session's OWN activity outruns it -- so
                # without this the row stayed red from the approval to the turn's
                # `Stop`, which is DRC-4097 on a second harness.
                #
                # The rollout's own newest record, not its mtime and not
                # `last_activity`: the latter folds in subagent files, and a child
                # writing says nothing about whether the human answered. Measured
                # on 0.149.0 rather than assumed, because the whole value of the
                # signal is that it stays put while a person is being asked: with
                # a real approval prompt standing open the rollout held at 13
                # lines and one timestamp across 25 seconds, then advanced to 27
                # once the gate was answered. A tail with no timestamp reports 0,
                # which leaves the wait standing -- the safe direction, and the
                # one an unreported value already takes in the reducer.
                "own_activity": (info or {}).get("last_event_ts") or 0,
                "started_at": turns.started_at(scan),
                "rate_per_min": sessions.rate_from(info, now, config) + data["rate"],
                "session_output_tokens": (scan.get("session_output_tokens") if scan else None),
                "turn_output_tokens": scan.get("turn_output_tokens") if scan else None,
                "turn": turns.turn_progress(scan, session_state, now, config),
                # `provider` stays None: no Codex record carries one, and
                # reading "openai" off the harness name would be inference.
                "model": scan.get("model") if scan else None,
                "subagents": subagents,
                "subagent_hierarchy": hierarchy,
                "subagent_events": lifecycle,
            }
        )
        out.append(s)
    return out
