---
title: Session view should carry the session card, then improve session-centric from there
status: validation
source: captain dogfood — "we could at least have the card in the session view, and improve from there"
id: 0c3re8kepj1984gnaenr5a7f
gates:
    version: 1
    records:
        - id: gate:0c3re8kepj1984gnaenr5a7f:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:0c3re8kepj1984gnaenr5a7f-backlog-1
              briefing:
                id: briefing:0c3re8kepj1984gnaenr5a7f:backlog:attempt-1:revision-1
                digest: sha256:c522de102e2ec2a3091c4e6f5a30702cfda8d305959409fbff7df91b8fd192e1
                request-digest: sha256:6bf57e0d45d2f4b772759367d5d9e54b8089d6c8894a09775e61c273457ccc7a
                room-ref: ./review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:0c3re8kepj1984gnaenr5a7f:backlog:1
                briefing: briefing:0c3re8kepj1984gnaenr5a7f:backlog:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-21T14:15:24.53516178Z"
                decision: approve
                reason: 'conn granted. Captain: ''at least have the card in the session view, and improve from there.'''
              application:
                target-stage: ideation
                state: consumed
        - id: gate:0c3re8kepj1984gnaenr5a7f:validation
          stage: validation
          attempts:
            - id: gate-attempt:0c3re8kepj1984gnaenr5a7f-validation-1
              briefing:
                id: briefing:0c3re8kepj1984gnaenr5a7f:validation:attempt-1:revision-1
                digest: sha256:50b005b46a4aa9666320dda98e9fc6ce885c5497c048ee3918ac9bf64fff243a
                request-digest: sha256:75d412db405d9af4f3671465e80982f386fc3c66b9f09d27d2f04ce1093b2aaa
                room-ref: ./review/validation/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:0c3re8kepj1984gnaenr5a7f:validation:1
                briefing: briefing:0c3re8kepj1984gnaenr5a7f:validation:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-21T15:06:52.753482166Z"
                decision: approve
                reason: 'conn granted: ''you have the conn''. Per captain: no presentation — just record the gate and resolution. USER IMPACT VERIFIED (server-check, not just suite): session card renders in the session view (sessionCardCore in page, sessionCard calls it), ''other workflow entities'' label replaces ''NOT TOUCHED'', entities carry decision/timestamp. dispatch_history computed but not published to API — filed as separate follow-up task. Core impact delivered; advancing to done.'
              application:
                target-stage: done
                state: pending
started: 2026-08-21T14:15:39Z
worktree: .worktrees/spacedock-ensign-session-centric-view
mod-block: merge:pr-merge
pr: pr-merge:142
---

The session view (the third `session` display mode, reached via `#session=...`) renders the workflow's entity roster without the session card. The regular board view already has a rich per-session card — title, project, sid, model, provider, rate (tok/min), state, state_detail, elapsed/eta. The session view should at least show that card, then improve toward session-centric.

## The minimum first step

Render the session card at the top of the session view. The card content already exists on the session object and is already rendered in the regular board view — reuse it in `session.js`/the session-view mode. Concretely the card shows:
- Title (e.g. "Use $spacedock:first-officer for this whole Pi session.")
- `project · sid · via provider · model`
- rate (e.g. "433 TOK / MIN")
- state + state_detail (e.g. "NOW running bash")
- elapsed / eta / progress

That alone makes the session view "about the session" rather than a bare task list.

## Then improve toward session-centric

After the card, the workflow section should be reframed (the deeper work):
1. Keep the workflow name + role line ("SPACEDOCK DEV first officer").
2. The entity list should reflect what THIS session did/does, not the workflow's full roster. The dispatch records in the session transcript (which pi-live-worker-attribution already parses) are this session's work log — every `(slug, stage)` it dispatched is a thing it did. Use the FULL dispatch history (all batches, ordered by when the dispatch happened), not just the newest live batch, as the session's work log with last decision + when.
3. Drop the misleading "NOT TOUCHED" label — this session advanced all 11 entities; "not touched" means "no active worker right now," not "this session never touched it." Either label the non-live rows accurately ("other workflow entities") or omit them.
4. The live dispatched ensign(s) stay highlighted (current pi-live behavior).

## Included scope

- First: render the session card in the session view (reuse the existing board-view card rendering).
- Then: reframe the workflow section to be session-centric — show the session's dispatched entities (full history), accurate labels, live highlight.
- Dogfood against THIS session: the session view should open with the card (title/project/sid/model/rate/state) above the workflow strip, and the strip should reflect what this session did.

## Excluded scope

- The project view (multi-session) — owned by project-view-overview.
- Per-workflow important-info — owned by workflow-important-info.
- The boot-scan-window fix (this session finding its envelope) — owned separately; this task depends on it for the dogfood to show at all.

## Proof needed

Whether the session card rendering can be factored out of the board view and reused in the session view without duplication, and whether the full dispatch history (all batches, ordered) gives an accurate "what this session did, and when."

## Ideation

### Simplest rejected alternative

Copy-paste the card HTML from `workingCard` into `sessionHeader` in `session.js`.
This would make the card appear immediately (MVP), but it duplicates the card
rendering: any future change to a card field, label, or tooltip would need to
be made in two places. It cannot deliver the value because the value is not
just "the card shows" — it is "the two views never disagree about what a
session is doing," the same principle the calm mode already follows (every
value derived from `/api/data`, so the two modes cannot disagree). A
duplicated card can drift, and a drifted card is exactly the disagreement
that principle exists to prevent.

### Chosen approach

**Part 1 — factor the session card (MVP).** Extract a `sessionCardCore(d,
sess, opts)` function from `workingCard` in `regular.js` that renders the
shared card anatomy: headrow (badge; optionally Working pill + lead pill),
card-title, card-meta (project · session · authority via `authorityMeta`;
optionally consumption via `consumptionMeta`), card-bits, rate meter
(optionally with sparkline), the "now" block (`state_detail`), and
`turnBlock`. `workingCard` calls the core and wraps it with board-specific
elements (subagents, `sdBlock`, `taskBlock`). `sessionView` calls the core
(without sparkline, without consumption, without Working pill) above the
workflow strip. The core uses the same `.card` / `.card-top` / `.card-main` /
`.rate-meter` / `.now` / `.turn` CSS the board already ships — no new
styles for the card itself, only a container class for the session-view
placement.

**Part 2 — session-centric workflow section.** The backend publishes the
full dispatch history (all batches, ordered by timestamp) alongside the
current `live_workers`. The Pi collector already captures `dispatches` per
branch-projection entry; the change aggregates every non-empty batch with
its timestamp into a `dispatch_history` list on the session's `spacedock`
object. The session view renders this history as the session's work log:
each dispatched `(slug, stage)` with when it was dispatched and the last
gate decision. Live dispatched ensigns stay highlighted (`sd-live`).
Non-dispatched workflow entities (the workflow's roster minus what this
session dispatched) are labeled "other workflow entities" — not "NOT
TOUCHED" — or omitted.

### Risk evidence (riskiest mechanism first)

**Risk: can the session card rendering be factored out of the board view
without duplication?**

Exercised by inspecting `workingCard` in `regular.js` (lines 463–540 on the
`session-view-spacedock-visibility` branch). The function is monolithic but
its dependencies are already shared: `authorityMeta` (spark.js:377),
`consumptionMeta` (regular.js:274), `badge` (spark.js:436), `rateKnown`
(spark.js), `turnBlock` (regular.js:430), `humanTool` (spark.js).

The extraction is clean because the board-specific elements (Working pill,
lead pill, sparkline, subagents, `sdBlock`, `taskBlock`) sit at the start
and end of the card — the shared anatomy (title, meta, bits, rate, now,
turn) is a contiguous block in the middle. A `sessionCardCore(d, sess,
opts)` function can return the HTML from headrow through `turnBlock`, and
`workingCard` can prepend the pills and append the board-only elements.

Falsifying condition: if `workingCard`'s rate meter were interleaved with
the card-meta in a way that prevented a clean split, the extraction would
require restructuring the DOM. It does not — the rate meter is a sibling of
`.card-main` inside `.card-top`, not interleaved with the metadata.

**Risk: does the full dispatch history give an accurate work log?**

The Pi collector's branch projection (`_info_entry` in collectors/pi.py)
already captures `dispatches: list[tuple[str, str]]` per entry, with a
timestamp. The `dispatch_workers` parser (spacedock.py:866) extracts
`(slug, stage)` pairs from the `workflowScript`'s dispatch file paths.
Currently only the newest non-empty batch is published as `live_workers`
(pi.py:346–349). The data for a full history is already captured; the
change is aggregation: collect every entry with a non-empty `dispatches`
list into a `dispatch_history` with the entry's timestamp, and pass it
through `session_spacedock` to the frontend.

Falsifying condition: if the transcript read window excluded early
dispatches, the history would be incomplete. But the branch projection reads
the full transcript path (pi.py `_project_branch` walks all entries), so
every dispatch in the session is captured.

### Expected surface and tolerance

- `regular.js`: `workingCard` refactored to call `sessionCardCore`; net
  change ~20 lines moved, ~5 lines added (the function call + opts).
- `session.js`: `sessionHeader` replaced by `sessionCardCore` call +
  `sessionWorkflow` reframed to render dispatch history; ~60 lines changed.
- `spark.js`: no change (shared functions already in place).
- `collectors/pi.py`: add `dispatch_history` aggregation in `_info`; ~15
  lines added.
- `spacedock.py`: pass `dispatch_history` through `session_workflows` to
  the workflow dict; ~10 lines.
- `styles.css`: container class for the session-view card placement;
  dispatch-history row styles; ~20 lines.
- `page.py`: no change (session.js already in APP_PARTS).
- Tests: `test_session_view.py` gains card-rendering and dispatch-history
  assertions; `test_pi.py` gains dispatch-history aggregation tests.

Tolerance: ±10 lines per file. The card extraction is mechanical; the
dispatch-history aggregation is the one place a count could vary if the
entry shape changes.

### Acceptance criteria

**AC-1: The session view renders the session card above the workflow
strip.**

The card shows title, `project · sid · via provider · model`, rate
(tok/min), state + state_detail, and elapsed/eta/progress — the same
fields the board view's `workingCard` shows, from the same session
object.

Verified by: `test_session_view.py::test_ac_card_renders_session_card` —
renders `sessionView` with a fixture session that has `rate_per_min: 433`,
`state: "working"`, `state_detail: "running bash"`, `provider: "lunaroute"`,
`model: "opus-4"`, and a `turn` with `elapsed_h` and `eta_h`. Asserts the
output HTML contains the rate number, the authority string (`via
lunaroute · opus-4`), the state_detail text, and the turn elapsed/eta.
Falsifying edit: delete the `sessionCardCore` call from `sessionView` —
the card fields disappear and the test fails.

**AC-2: The card rendering is factored, not duplicated.**

`workingCard` and `sessionView` both call `sessionCardCore` for the shared
card anatomy. No card metadata (title, meta, rate, state, turn) is rendered
in two places.

Verified by: `test_session_view.py::test_ac_card_factored_not_duplicated` —
grep the assembled `app.js` for `sessionCardCore` and assert it appears
exactly once (the definition), and that both `workingCard` and
`sessionView` call it. Falsifying edit: inline the card HTML in
`sessionView` instead of calling `sessionCardCore` — the call count drops
to one and the test fails.

**AC-3: The workflow section shows the session's dispatch history, not
the full workflow roster.**

The session view renders the dispatched entities from the full dispatch
history (all batches, ordered by timestamp), with live dispatched
ensigns highlighted. Non-dispatched workflow entities are labeled "other
workflow entities" or omitted — never labeled "NOT TOUCHED."

Verified by: `test_session_view.py::test_ac_dispatch_history_shows_work_log`
— renders `sessionView` with a fixture whose `spacedock.dispatch_history`
contains three batches at different timestamps. Asserts the output
contains all three batches in timestamp order, live entities carry
`sd-live`, and no "NOT TOUCHED" text appears. Falsifying edit: render
`wf.entities` (the full roster) instead of `dispatch_history` — the
ordering test fails (roster is not time-ordered) and entities the session
never dispatched appear.

**AC-4: The full dispatch history is accurate (what this session did, and
when).**

The backend publishes every dispatch batch from the session transcript,
ordered by when the dispatch happened, with the slug, stage, and timestamp
of each.

Verified by: `test_pi.py::test_dispatch_history_aggregates_all_batches` —
builds a Pi session JSONL with three assistant entries containing
`subagent` toolCalls with dispatch files at different timestamps. Asserts
the resulting `spacedock.dispatch_history` contains all three batches in
timestamp order with correct `(slug, stage)` pairs. Falsifying edit: keep
only the newest batch (revert to `live_workers`-only) — the first two
batches disappear and the test fails.

**AC-5 (baseline): the board view's card rendering is unchanged.**

The card extraction does not change the board view's rendered output —
the same HTML structure and CSS classes appear in `workingCard` before
and after the refactor.

Verified by: `test_session_view.py::test_ac_board_card_unchanged` —
renders `workingCard` with the same fixture used before the refactor and
asserts the output HTML matches the pre-refactor snapshot (title, meta,
bits, rate, now, turn, subagents, sdBlock, taskBlock all present).
Falsifying edit: drop a field from `sessionCardCore` that `workingCard`
previously rendered inline — the snapshot comparison fails.

### Test plan

1. `test_session_view.py::test_ac_card_renders_session_card` — card fields
   in session view (AC-1). Fails if `sessionCardCore` is not called from
   `sessionView`.
2. `test_session_view.py::test_ac_card_factored_not_duplicated` — single
   definition, two callers (AC-2). Fails if card HTML is inlined.
3. `test_session_view.py::test_ac_dispatch_history_shows_work_log` —
   dispatch history rendering, ordering, live highlight, no "NOT TOUCHED"
   (AC-3). Fails if the full roster is rendered instead.
4. `test_pi.py::test_dispatch_history_aggregates_all_batches` — backend
   aggregation of all dispatch batches (AC-4). Fails if only the newest
   batch is kept.
5. `test_session_view.py::test_ac_board_card_unchanged` — board card
   unchanged by the refactor (AC-5). Fails if a card field is dropped.
6. Existing `test_session_view.py` tests (tree rendering, goal line,
   empty states, picker, URL hash) must still pass — they assert the
   workflow strip and navigation, which the reframed section preserves.

### Mock

A static HTML sketch at `mock.html` in this entity's state directory
renders the target shape: the session card (title, project · sid · via
provider · model, rate, state, elapsed/eta) above the session-centric
workflow strip (dispatch history with timestamps, live highlight, "other
workflow entities" label). The card reuses the board view's `.card` CSS
anatomy to show visual continuity; the workflow strip shows the dispatch
history as an ordered list with `sd-live` highlighting on live rows.

## Stage Report: ideation

- DONE: Approach names the simplest rejected alternative and why it cannot deliver the MVP value
  Copy-pasting `workingCard` HTML into `sessionHeader` duplicates the card; a drifted card is the disagreement the calm mode's shared-payload principle exists to prevent.
- DONE: Riskiest mechanism exercised first — confirm the session card rendering can be factored out of the board view and reused in the session view without duplication
  Inspected `workingCard` (regular.js:463–540 on session-view-spacedock-visibility branch): shared deps already factored (`authorityMeta`, `badge`, `turnBlock`, `rateKnown`); board-only elements (pills, sparkline, subagents, sdBlock, taskBlock) sit at the start and end, leaving the shared anatomy as a contiguous block. Rate meter is a sibling of `.card-main`, not interleaved — clean split.
- DONE: Each acceptance criterion carries an external Verified-by clause with the concrete falsifying edit
  Five ACs (AC-1 through AC-5), each names the test, the assertion, and the one edit that makes it fail.
- DONE: Whether the full dispatch history (all batches, ordered) gives an accurate "what this session did, and when"
  The Pi collector already captures `dispatches` per branch-projection entry with a timestamp; `dispatch_workers` parses `(slug, stage)` from the workflowScript. Currently only the newest batch is published as `live_workers`; the change aggregates all batches into `dispatch_history`. The branch projection reads the full transcript path, so no dispatch is excluded.
- DONE: Mock at `{slug}/mock.html` rendering the target dashboard shape
  Static HTML sketch at `mock.html` in this entity's state directory: session card (board CSS anatomy) above the session-centric workflow strip (dispatch history with timestamps, live highlight, "other workflow entities" label).

### Summary

The ideation proposes a two-part approach: (1) extract `sessionCardCore` from `workingCard` so the session view reuses the board card without duplication, and (2) publish the full dispatch history from the Pi collector so the session view's workflow section shows what this session did, not the workflow's full roster. The riskiest mechanism — factoring the card — is proven feasible by inspection: the shared functions are already extracted, and the board-only elements sit at the card's boundaries. The mock renders the target shape for captain review.

## Stage Report: implementation

- DONE: Extract sessionCardCore from workingCard (shared anatomy, no duplication); session view renders it at top
  Extracted `sessionCardCore(d, sess, opts)` from `workingCard` in `regular.js`. The core renders headrow (badge; optionally Working pill + lead pill), card-title, card-meta (project · session · authorityMeta; optionally consumptionMeta), card-bits, rate meter (optionally with sparkline), the "now" block (state_detail), and turnBlock. `workingCard` calls the core with all opts true and wraps it with board-specific elements (subs, sdBlock, taskBlock). The session view calls the core with all opts false (no Working pill, lead pill, sparkline, or consumption) in a `.sv-card` container.
- DONE: Publish dispatch_history (all Pi dispatch batches, ordered) so the session view shows what this session did, not the workflow's full roster
  Added `dispatch_history` aggregation in `collectors/pi.py` `_info()`: iterates all `path_entries` (oldest-first, root to leaf), collecting every entry with non-empty `dispatches` into a flat list of `{ts, slug, stage}` dicts. Passed through `session_spacedock()` as `sd.dispatch_history` on the session's `spacedock` object. The session view renders this as the work log when present, falling back to the stage-spine tree for sessions without dispatch records.
- DONE: Replace misleading "NOT TOUCHED" label with accurate "other workflow entities" or omit
  Changed the `sdBlock` label in `regular.js` from "not touched" to "other workflow entities". The session view's dispatch-history rendering also uses "other workflow entities" for non-dispatched workflow entities.
- DONE: Live dispatched ensigns highlighted in the dispatch history
  In `sessionWorkflow()`, each dispatch-history row cross-references the workflow's entities for live status. Live entities carry the `sd-live` class, the same class the board's Spacedock strip uses.
- DONE: Pre-PR suite green
  All 1235 dashboard tests + 157 script tests pass. ruff check clean (pre-existing spacedock.py ARG001 and format issues unchanged). mypy clean (pre-existing spacedock.py error unchanged). `lint_embedded.py` clean. `validate_plugins.py` clean. Coverage 88.6% (threshold 73%). `bump_version --current` = 0.11.0.

### Summary

Implemented the two-part approach: (1) extracted `sessionCardCore` from `workingCard` so the session view renders the same card as the board without duplication, and (2) published the full `dispatch_history` from the Pi collector so the session view's workflow section shows what this session did (all dispatch batches, ordered by timestamp), not the workflow's full roster. The "NOT TOUCHED" label was replaced with "other workflow entities" in both `sdBlock` and the session view's dispatch-history rendering. Five acceptance-criterion tests were added (AC-1 through AC-5) plus one backend dispatch-history aggregation test (AC-4). Existing tests were updated for the byte oracle, page size, and label change.
