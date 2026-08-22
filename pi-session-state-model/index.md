---
title: Pi session state-detection mislabels long-running tools and thinking as idle/awaiting
status: backlog
source: captain seed
id: c8ex5x308ssq305b62n3szxm
gates:
    version: 1
    records:
        - id: gate:c8ex5x308ssq305b62n3szxm:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:c8ex5x308ssq305b62n3szxm-backlog-1
              briefing:
                id: briefing:c8ex5x308ssq305b62n3szxm:backlog:attempt-1:revision-1
                digest: sha256:542d08d7790eb21d52dc775a9b632105bf7b255098d8860df4536b53cf0105e1
                request-digest: sha256:9bb40bf77ee7af16cd0a1bc4aefff46e544f719ab48e2d74c7fda28bb84a7d26
                room-ref: ./review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:c8ex5x308ssq305b62n3szxm:backlog:1
                briefing: briefing:c8ex5x308ssq305b62n3szxm:backlog:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-22T05:53:01.653842444Z"
                decision: approve
                reason: 'Conn: captain granted ''you have the conn to push to the forked repo and open PR; when you have the conn, you should still do gate attempt and record your autonomous approval as resolution'' (session 01a02216, reaffirmed ''just do some'' this session). Evidence: seed reviewed in full — 4 falsifiable ACs against live /api/data (AC-1 in-flight tool reads working/running regardless of age; AC-2 thinking block reads working/thinking; AC-3 genuine-awaiting preserved; AC-4 suite green), root-cause collector scope (pi.py+sessions.py), not UI. Ideation owes the detection design.'
              application:
                target-stage: ideation
                state: pending
---
# Pi session state-detection mislabels long-running tools and thinking as idle/awaiting

## Problem
The Pi collector (`cargento_runtime/collectors/pi.py` + `sessions.working_detail`)
computes session state by *recency of transcript events* (`is_fresh` + the 90s
`working_threshold_sec`), not by *what the last event is*. Two mislabels result:

1. **A session running a long tool reads as `idle / awaiting your message`.**
   While a tool is in flight (an open `toolCall` with no matching `toolResult`),
   there are no new transcript events, so `last_event_ts` goes stale past the
   90s threshold, and the session flips to idle even though it's actively
   working. The spacedock session (01a02221) showed this: mid-bash (last record
   is an `assistant` with `toolCall`, no `toolResult` yet — the bash is still
   running), reported `idle / awaiting your message`.

2. **`running bash` shown during a thinking block.** `working_detail` returns
   `f"running {info['last_tool']}"` from the last tool call, but during a
   thinking block there IS no active tool — `last_tool` is stale from a prior
   turn. The cargento session (01a02216) showed this: I was in a thinking
   block, reported "running bash."

## Acceptance criteria
- **AC-1**: A Pi session whose last transcript record is an `assistant` message
  containing a `toolCall` with no subsequent `toolResult` (the tool is in
  flight) reports `state: working`, `state_detail: running <tool>` — regardless
  of how long ago the last event was. Verify: the spacedock session
  (`01a02221`) mid-bash shows `working / running bash`, not
  `idle / awaiting your message`.
- **AC-2**: A Pi session whose last transcript record is an `assistant`
  message with text/thinking content and no `toolCall` (a thinking block)
  reports `state: working`, `state_detail: thinking` — not
  `running <stale-tool>`. Verify: the cargento session (`01a02216`) during a
  thinking block shows `working / thinking`, not `running bash`.
- **AC-3**: A Pi session whose last record is a `toolResult` followed by a
  user message (genuinely awaiting) reports `idle / awaiting your message`
  as before (the in-flight-tool + thinking detection must not break the
  genuine-awaiting case).
- **AC-4**: The full unittest suite passes (this is a collector change with
  test surface; the state-detection logic in `pi.py` + `sessions.py` likely
  has existing tests that pin the current behavior — update them to the new
  behavior, don't break unrelated tests).

## Scope notes
- The fix is in the Pi collector (`collectors/pi.py`) — `scan_pi_session` should
  surface whether the last tool is in-flight (open `toolCall`, no matching
  `toolResult`) and whether the session is in a thinking block (last record is
  assistant text, no toolCall). Then the state decision in the `pi_sessions`
  function (~line 544) uses that, not just `is_fresh`.
- `sessions.working_detail` (~line 369) needs a "thinking" case.
- This is the collector's data model, not the session-view UI. The UI renders
  whatever `state_detail` the collector gives it; fixing the collector fixes
  the UI's lie for free.
- A user-impact gate (not just suite-green): dogfood on the live integration
  server — the spacedock session running bash shows `working / running bash`,
  and the cargento session during a thinking block shows `working / thinking`,
  verified via `/api/data` (or a screenshot).

## Why it matters
The activity row (piece 2 of the 3-glancable-pieces) lies to the captain about
what the session is doing. A captain skimming to decide whether to intervene
sees "awaiting your message" for a session that's actually running a long
bash, or "running bash" for a session that's thinking. The mirror is
supposed to show what's happening *now*; the state model can't distinguish
"blocked on a long tool" from "genuinely idle" or "thinking" from "running."
Fixing the collector is the root; the UI is a symptom.
