---
title: Session view with Spacedock visibility
status: validation
source: captain seed
id: 6s6ft835wwg0q9hb8505rkz6
gates:
    version: 1
    records:
        - id: gate:6s6ft835wwg0q9hb8505rkz6:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:6s6ft835wwg0q9hb8505rkz6-backlog-1
              briefing:
                id: briefing:6s6ft835wwg0q9hb8505rkz6:backlog:attempt-1:revision-1
                digest: sha256:46a4904f685b2000c4a33adec4d49526c94a8907a88043939273cea15d585c95
                request-digest: sha256:0948043d557687115d613668a97634a54efa7a854af164a7befb03c8f210e65f
                room-ref: ./session-view-spacedock-visibility/review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:6s6ft835wwg0q9hb8505rkz6:backlog:1
                briefing: briefing:6s6ft835wwg0q9hb8505rkz6:backlog:attempt-1:revision-1
                by: person:captain
                at: "2026-08-21T02:50:24.961909245Z"
                decision: approve
                reason: captain directs the backlog seed to advance to ideation for design
              application:
                target-stage: ideation
                state: consumed
        - id: gate:6s6ft835wwg0q9hb8505rkz6:ideation
          stage: ideation
          attempts:
            - id: gate-attempt:6s6ft835wwg0q9hb8505rkz6-ideation-1
              briefing:
                id: briefing:6s6ft835wwg0q9hb8505rkz6:ideation:attempt-1:revision-1
                digest: sha256:2966d5abe5eb11ec405b76bc581ce408b8c9ba628e5da1c3dab0d171030121dc
                request-digest: sha256:32443893ba6225f08deec112c8f17f407e323088ae8c454c10d2779c35dc4d1a
                room-ref: ./session-view-spacedock-visibility/review/ideation/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:6s6ft835wwg0q9hb8505rkz6:ideation:1
                briefing: briefing:6s6ft835wwg0q9hb8505rkz6:ideation:attempt-1:revision-1
                by: person:captain
                at: "2026-08-21T06:24:06.520801102Z"
                decision: approve
                reason: Captain approved the 6s ideation via Subspace (binding resolution, decision approve, no annotations).
              application:
                target-stage: implementation
                state: consumed
        - id: gate:6s6ft835wwg0q9hb8505rkz6:validation
          stage: validation
          attempts:
            - id: gate-attempt:6s6ft835wwg0q9hb8505rkz6-validation-1
              briefing:
                id: briefing:6s6ft835wwg0q9hb8505rkz6:validation:attempt-1:revision-1
                digest: sha256:db989bcceec2e3a3f345776a349ab472df649829e4e2c556cb1a69ab3b9ddbf9
                request-digest: sha256:dddf5c39cfbfcd762144f36de7bc57d3a22d5d9897b5064edcb681a52b1cc8b3
                room-ref: ./session-view-spacedock-visibility/review/validation/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:6s6ft835wwg0q9hb8505rkz6:validation:1
                briefing: briefing:6s6ft835wwg0q9hb8505rkz6:validation:attempt-1:revision-1
                by: person:captain
                at: "2026-08-21T06:49:33.917450744Z"
                decision: approve
                reason: Captain approved validation via Subspace (binding resolution, decision approve, no annotations). All 3 ACs independently reproduced with falsifying edits, no-goal baseline guard confirmed, overviews unchanged, pre-PR suite green. Delivery can proceed to done.
              application:
                target-stage: done
                state: superseded
            - id: gate-attempt:6s6ft835wwg0q9hb8505rkz6-validation-2
              briefing:
                id: briefing:6s6ft835wwg0q9hb8505rkz6:validation:attempt-2:revision-1
                digest: sha256:32e05f5b5476f483626b0273aad9316393354d41e1ad191e02e70dee0328aff7
                request-digest: sha256:74f7dd9c03caeaa6f87a0805e1c615e63229adcac5771a4264b931037298c392
                room-ref: ./session-view-spacedock-visibility/review/validation/briefing-2
              resolution:
                type: Resolution
                id: resolution:spacedock:6s6ft835wwg0q9hb8505rkz6:validation:2
                briefing: briefing:6s6ft835wwg0q9hb8505rkz6:validation:attempt-2:revision-1
                by: agent:first-officer
                at: "2026-08-21T07:55:40.848007092Z"
                decision: approve
                reason: 'conn granted: ''you have the conn to push to the forked repo and open PR''; reinforced: ''when you have the conn, you should still do gate attempt and record your autonomous approval as resolution''. Rework addresses all 3 dogfood bugs: URL hash routing navigable from calm view, 4 distinct empty/loading states, dogfooded against this session and the non-Spacedock Review handoff session. Suite green. Delivery can proceed to done.'
              application:
                target-stage: done
                state: pending
started: 2026-08-21T02:50:26Z
worktree: .worktrees/spacedock-ensign-session-view-spacedock-visibility
mod-block:
pr:
---

Cargento's dashboard has two overview modes — `regular` and `calm` — that summarize all sessions. There is no per-session view. The reference (`/private/tmp/image (1).png`) shows a "Task Map": a dispatch tree of work items connected by dependency edges with stage-colored nodes, plus panels for recent completions, active claims, available, and blocked. A session view should render that dispatch tree for one session and add a high-level goal — a sprint or stated objective — if the session carries one (stated in its workflow/roadmap context, or derived from the entities it is driving).

## Problem

An operator watching one active session cannot see, for that session alone, the dispatch tree of what it is working or the high-level goal it is pursuing. The overview modes aggregate all sessions and do not render per-session dependency trees. This task adds a session view without touching the existing `regular`/`calm` overviews or any other dashboard surface.

## Proposed approach

A third display mode — `session` — selectable alongside `regular` and `calm` via the existing mode bar in `web/controls.js`. Entering it requires a target session: clicking a session card or row (either overview) stores the session's `(harness, sid)` key and calls `setDisplayMode("session")`. The mode bar gains a third button; the existing two-mode switch in `web/mode.js` (`setDisplayMode`, the `localStorage` persistence) is widened additively — `displayMode` accepts `"session"` and the saved value round-trips like the other two. The render branch in `web/main.js` gains an `else if (displayMode === "session")` arm before the regular default; `regular` and `calm` are untouched.

The session view renders two things from the same `/api/data` payload both overviews already consume — no new endpoint, no new collector, no cross-session scan:

1. **Dispatch tree.** The session's `spacedock.workflows` array (already published by `collectors/claude.py` → `session_spacedock` → `spacedock.session_workflows`) carries `{workflow, stages, entities: [{slug, stage, cycle, live}]}`. The view renders each workflow as a tree: stage-colored entity nodes positioned along the workflow's ordered `stages` spine, with live workers (entities whose `live` flag is set) highlighted. This reuses the exact `sdBlock` / `sdWindow` spine logic already in `web/regular.js` for the existing Spacedock strip, generalized from a horizontal strip to a vertical tree layout matching the reference image's Task Map shape.

2. **Goal line.** A one-line header above the tree showing the high-level goal. The goal is derived, not inferred: when the session is a first officer (`spacedock.role === "first-officer"`), the workflow README's frontmatter `title` scalar (already read by `spacedock.read_workflow` via `scalar(lines, "title")` — currently discarded after extracting `commissioned-by`) is published as `workflow.goal` alongside each workflow's `stages` and `entities`. When the workflow frontmatter carries no `title`, no goal line renders — the view shows the tree alone, never a fabricated objective.

### Simplest rejected alternative

A dedicated `/api/session?id=<harness>:<sid>` endpoint that returns a single session's full payload on demand, rendered in a separate page or component. It cannot deliver the MVP because the data the dispatch tree needs — `spacedock.workflows` — is already in every `/api/data` response for every session. A second endpoint doubles the server surface (a new route, a new query path, a new cache key) for zero new data, and it introduces a second read path that can disagree with the overview about what a session is doing. The mode-switch approach reads from the same payload the overviews already trust, so the session view and the overview cannot diverge.

## Risk evidence

The riskiest mechanism is whether a third mode can be hosted additively in `web/mode.js` without disturbing the existing two, and whether the entity-state data for a per-session dispatch tree is reachable from a single session id without a cross-session scan. Both are confirmed by reading the code:

- `setDisplayMode` in `mode.js` rejects anything that is not `"calm"` or `"regular"` and persists the value to `localStorage`. Widening the guard to accept `"session"` is a one-line change; the round-trip and the `render(lastData)` re-render call are mode-agnostic. The `modeBar()` in `controls.js` builds its button group from two `btn()` calls — a third is additive.
- `render()` in `main.js` branches on `displayMode === "calm"` and falls through to regular. An `else if (displayMode === "session")` arm before the fall-through is additive; the regular path is untouched.
- The `spacedock` field on each session row is already populated by `collectors/claude.py` → `session_spacedock()`. It is keyed to a single session's transcript boot output and subagent names — no cross-session scan. A session selected by `(harness, sid)` is found in the existing `d.sessions` array by the same `sessKey()` identity the page already uses for deduplication and notification state.
- The `title` scalar in workflow frontmatter is already parsed by `spacedock.frontmatter_lines` + `scalar(lines, "title")` in `read_workflow`; only the extraction target changes (add `"goal": title` to the returned dict), not the read path.

No spike needed: all mechanisms are proven by existing code paths that already read, parse, and publish this data.

## Risk evidence

The riskiest mechanism is whether a third mode can be hosted additively in `web/mode.js` without disturbing the existing two, and whether the entity-state data for a per-session dispatch tree is reachable from a single session id without a cross-session scan. Both are confirmed by reading the code (see Proposed approach above for the full evidence). No spike needed: all mechanisms are proven by existing code paths that already read, parse, and publish this data.

## Expected surface and tolerance

Estimate: ~120–180 lines of new JS in `web/session.js` (the view renderer), ~10 lines changed in `web/mode.js` (accept `"session"`), ~5 lines in `web/controls.js` (third mode button), ~15 lines in `web/main.js` (render branch + session-key state), ~5 lines in `web/page.py` (`APP_PARTS` gains `session.js`), ~10 lines in `cargento_runtime/spacedock.py` (publish `goal` from `title` scalar), and ~50 lines of new CSS in `web/styles.css` for the tree layout. No new Python module, no new collector, no new HTTP route.

Tolerance: the JS line count may grow to ~250 if the tree layout needs edge-drawing logic (SVG connectors between nodes). The Python change is tightly bounded — one `scalar` call and one dict key. If the `title` scalar proves insufficient for the goal line (e.g., the workflow README carries the goal in a body heading instead of frontmatter), the fallback is to show no goal rather than to widen the read — staying within the out-of-scope LLM-summarization boundary.

Semantics this may change:
- `displayMode` gains a third value (`"session"`) and a second piece of session-selection state (`sessionViewKey`). `localStorage` persists the mode but not the key (selecting a stale session on reload falls back to the overview — a dead session in a named mode is worse than a fresh start).
- `spacedock.read_workflow` returns one new key (`goal`) in its result dict. `session_workflows` passes it through. The session row's `spacedock.workflows` entries gain a `goal` field. No existing consumer of `workflows` (`sdBlock` in `regular.js`, the calm-mode `sdBlock`) reads `goal`, so they are unaffected.
- `APP_PARTS` in `web/page.py` gains one entry. The assembled page hash changes, which is the self-proving property the refactor test checks — the test that asserts the assembled page hash must be updated to the new hash.

## Acceptance criteria

### AC-1: Session view renders the dispatch tree for a known first-officer session

Selecting the session view for a session whose `spacedock.role` is `first-officer` and whose `spacedock.workflows` is non-empty renders one tree per workflow, with entity nodes colored by their `stage` and positioned along the workflow's ordered `stages` spine. Live workers (`live: true`) are visually distinct from parked entities. The entity slugs, stages, and cycle labels match the `/api/data` payload for that session.

**Verified by:** a unit test that feeds a fixture `/api/data` payload (one FO session with two workflows, three entities at different stages) into the session-view renderer function and asserts the rendered HTML contains each entity slug, each stage name, and the `live` class on the live entity. The test fails if any entity slug is missing from the output, if a stage name is absent, or if a `live` entity is not marked with the `sd-live` class.

**Falsifying edit:** remove the `goal` passthrough from `spacedock.read_workflow` — the test for AC-1 does not assert on `goal`, so it still passes, proving AC-1 is independent of the goal line. Conversely, delete the tree-rendering branch and AC-1 fails.

### AC-2: Goal line shows a stated goal and shows nothing when no goal exists

When the session's workflow frontmatter carries a `title` scalar, the session view renders it as a one-line goal header above the tree. When no `title` is present, no goal line renders — the tree stands alone, with no fabricated or placeholder text.

**Verified by:** two unit tests against the same renderer: (a) a fixture whose workflow frontmatter `title` is `"Ship session view"` — the rendered HTML contains that string in the goal header element; (b) a fixture with no `title` — the rendered HTML contains no goal header element. Test (a) fails if the `goal` field is dropped from the payload. Test (b) fails if the renderer emits a goal element when `goal` is null or empty.

**Falsifying edit:** hardcode a goal string in the renderer (e.g., `"Current sprint"`) as a fallback when `goal` is absent — test (b) fails, which is the baseline moving the wrong way: a session with no goal would show a fabricated one.

### AC-3: Existing overviews are unchanged

The `regular` and `calm` modes render identically to before this change: no new DOM elements, no removed elements, no changed class names.

**Verified by:** the existing `test_page.py` assembled-page hash test is updated to the new hash (since `APP_PARTS` gains `session.js`), but the regular and calm renderer tests (`test_regular.js` / `test_calm.js` equivalents in the Python test suite that feed fixtures through `render()`) assert the same output as before. The test fails if the regular or calm render branch gains or loses any element.

**Falsifying edit:** add a `session` class to the mode bar's regular button — the overview test fails.

## Test plan

1. **Session-view renderer unit tests** (new file `tests/test_session_view.py` or additions to the existing web-renderer test module). Feed a fixture payload through the session-view render function and assert:
   - AC-1: every entity slug, stage name, and `live` class is present in the rendered HTML.
   - AC-2a: the goal header element contains the workflow `title` when present.
   - AC-2b: no goal header element when `title` is absent.
   - AC-3: the regular and calm renderers produce unchanged output.
2. **`spacedock.read_workflow` goal passthrough test** (addition to `tests/test_spacedock.py`). A workflow README fixture with `title: Ship session view` in its frontmatter produces `goal: "Ship session view"` in the returned dict. A fixture without `title` produces `goal: ""`. Fails if the `scalar(lines, "title")` call is removed.
3. **`APP_PARTS` / assembled-page hash test** (`test_page.py`). Update the expected hash to include `session.js`. The test self-proves the part list is complete and ordered.
4. **`mode.js` acceptance test** (addition to the JS-renderer test suite). `setDisplayMode("session")` sets `displayMode` to `"session"`, persists to `localStorage`, and triggers `render(lastData)`. `setDisplayMode("invalid")` is a no-op. Fails if the guard is not widened.

All tests run on every runner (pure functions / fixtures, no filesystem or network).

### Feedback Cycles

## Out of scope

- Changing the `regular` or `calm` overviews — this task is additive only.
- A new cross-session data source: the dispatch tree reuses existing `spacedock.py`/`sessions.py` reads.
- LLM-summarized goal inference beyond stated/derived-from-workflow-context for this task.

## Stage Report: ideation

- DONE: Approach names the simplest rejected alternative and why it cannot deliver the MVP value
  A dedicated `/api/session?id=…` endpoint was rejected: the dispatch-tree data is already in every `/api/data` response, so a second endpoint doubles the server surface for zero new data and introduces a second read path that can disagree with the overview.
- DONE: Riskiest mechanism exercised first (or no-spike-needed with proven mechanisms named)
  No spike needed: `setDisplayMode` in `mode.js` is a guarded one-liner widened additively; `render()` in `main.js` gains an `else if` arm; `spacedock.workflows` is already published per session by `collectors/claude.py` → `session_spacedock()`; `scalar(lines, "title")` is already parsed by `read_workflow` and only needs to be passed through as `goal`.
- DONE: Each AC carries an external Verified-by clause with the concrete falsifying edit
  AC-1 verified by a renderer unit test asserting entity slugs, stage names, and `sd-live` classes are present; fails if the tree branch is deleted. AC-2 verified by two tests (goal present / goal absent); the absent-goal test fails if a hardcoded fallback is added. AC-3 verified by unchanged overview renderer tests; fails if the mode bar gains a session class on the regular button.

### Summary

Filled all ideation placeholders: a third `session` display mode reusing the existing `/api/data` payload and `spacedock.workflows` data, a goal line from the workflow frontmatter `title` scalar, three acceptance criteria with falsifying edits, and a test plan. A static HTML mock at `session-view-spacedock-visibility/mock.html` renders the target tree shape (stage-colored nodes along the workflow spine, live-worker highlighting, goal header, and the no-goal and ensign variants).

## Stage Report: implementation

- DONE: Change satisfies the ideation ACs: session view renders dispatch tree (AC1), goal line present/absent (AC2), overviews unchanged (AC3)
  `test_session_view.py` feeds a fixture /api/data payload (one FO session, two workflows, three entities at different stages) through `sessionView()` and asserts every entity slug, stage name, and `sd-live` class is present (AC-1); asserts goal header element present when `goal` is non-empty and absent when empty (AC-2a/AC-2b); asserts no hardcoded fallback goal string (AC-2 falsifying edit); `test_page_calm.py` and `test_page.py` existing renderer tests pass unchanged (AC-3); deleting the tree-rendering branch in `session.js` makes AC-1 fail, hardcoding a goal fallback makes AC-2 fail, adding a `session` class to the regular button makes AC-3 fail.
- DONE: Tests written first and watched fail for the right reason (tree-render, goal present/absent, overview regression)
  Tests written in `test_session_view.py` (6 tests: AC-1 tree render, AC-2a goal present, AC-2b goal absent, AC-2 no-hardcoded-fallback, picker, mode switch) and `test_spacedock.py` (2 tests: goal passthrough through `read_workflow` and `session_workflows`). All watched fail before implementation; all pass after.
- DONE: Third "session" display mode reuses existing /api/data payload and spacedock.workflows (no new endpoint); goal from frontmatter title scalar
  `sessionView(d)` in `session.js` reads from the same `d.sessions[].spacedock.workflows` the overview `sdBlock` already reads — no new endpoint, no new collector. `spacedock.read_workflow` publishes `goal: scalar(lines, "title")` and `session_workflows` passes it through as `workflow.goal`.
- DONE: Pre-PR suite run green: ruff check, ruff format --check, mypy, lint_embedded.py, validate_plugins.py, coverage
  ruff check: All checks passed. ruff format --check: 110 files already formatted. mypy: Success, no issues in 81 source files. lint_embedded.py: Frontend assets clean. validate_plugins.py: Validated 1 skills. coverage: 89.2% (threshold 73%). Full unittest suite: 1185 tests OK (1 skipped).

### Summary

Implemented a third `session` display mode that renders one session's Spacedock dispatch tree from the existing `/api/data` payload. The view reuses `spacedock.workflows` data already published per session — no new endpoint or collector. Each workflow renders as a vertical tree of stage-colored entity nodes along the ordered stages spine, with live workers highlighted via the existing `sd-live` class. A one-line goal header from the workflow frontmatter `title` scalar renders above the tree when present; no goal line renders when absent. The mode is selected via a third button in the mode bar, and clicking a session card or idle row in the regular view enters session mode with that session. `spacedock.read_workflow` was widened by one `scalar` call and one dict key; `session_workflows` passes the `goal` field through. The change is additive: `regular` and `calm` render branches are untouched except for `data-calm` attributes on existing card/row elements (no new DOM elements, no class changes). 14 files changed, 440 insertions, 20 deletions. Commit `72cdc8a`.

## Stage Report: validation

- DONE: Each AC's Verified-by reproduced independently (not trusting self-report): AC1 tree renders, AC2 goal present/absent, AC3 overviews unchanged
  AC-1: deleted the tree-rendering branch in `session.js` → `test_ac1_session_view_renders_dispatch_tree` fails (entity slugs all absent). AC-2a: `test_ac2a_goal_line_shows_stated_goal` passes with the goal present. AC-2b: `test_ac2b_no_goal_line_when_title_absent` passes — no `sv-goal` element when `goal` is empty. AC-3: added a `session` class to the regular button in `controls.js` → `test_load_page_preserves_all_three_byte_oracles` fails (asset hash and assembled-page size mismatch). Independence confirmed: removing the `goal` passthrough from `spacedock.read_workflow` leaves `test_ac1` passing (AC-1 does not assert on `goal`) while `test_workflow_goal_passes_through_the_frontmatter_title` fails (KeyError: 'goal').
- DONE: Goal line absent when no title (no hardcoded fallback) — independent check of the baseline-wrong-way guard
  Hardcoded a `"Current sprint"` fallback in `sessionWorkflow()` when `goal` is empty → both `test_ac2_no_hardcoded_goal_fallback` and `test_ac2b_no_goal_line_when_title_absent` fail ("a hardcoded goal fallback was rendered" / "a goal was fabricated for a workflow with no title"). Reverted; both pass clean.
- DONE: Regular/calm overview renderer tests pass unchanged — independent check that existing surfaces are untouched
  `test_page.py` (91 tests) and `test_page_calm.py` (49 tests) pass unchanged with the implementation's updated asset hashes and page-size assertions. The only regular.js change is additive `data-calm` attributes on `workingCard` and `idleRow` (no new elements, no class changes); calm.js gains a `session` action handler but no calm-renderer DOM changes.
- DONE: Pre-PR suite re-run green from the validation lane: ruff, mypy, lint_embedded, validate_plugins, coverage
  ruff check: All checks passed. ruff format --check: 110 files already formatted. mypy: Success, no issues in 81 source files. lint_embedded.py: Frontend assets clean. validate_plugins.py: Validated 1 skills. coverage: 89.2% (threshold 73%). Full unittest suite: 1185 tests OK (1 skipped) + 157 script tests OK. Version parity: `bump_version.py --current` → 0.11.0; no version fields moved since merge-base.
- DONE: Reviewer findings recorded under workflow labels with a PASSED/REJECTED recommendation
  No reviewer findings arrived during this validation lane. The implementation diff (commit `72cdc8a`, 14 files, +440/-20) was inspected for scope creep, dependency ordering, and XSS surface; all `data-arg` values pass through `esc()`, `sdSlug` and `sessKey` are defined in earlier-loaded parts, and `sessionViewKey` is intentionally not persisted. Recommendation: PASSED.

### Summary

Independently reproduced all three ACs via their falsifying edits and the full pre-PR suite. AC-1 tree rendering fails when the branch is deleted; AC-2 baseline-wrong-way guard fails when a hardcoded fallback is added; AC-3 hash test fails when the regular button gains an extraneous class. AC-1/AC-2 independence confirmed by removing the goal passthrough. Pre-PR suite green: ruff, mypy, lint_embedded, validate_plugins, coverage 89.2%. No reviewer findings. Recommendation: PASSED.

## Stage Report: implementation (cycle 2)

- DONE: Routable URL with session id (URL hash), navigable from calm view and back
  mode.js reads `location.hash` (`#session=<harness>:<sid>`) on init to restore session mode + key; `syncSessionHash()` updates the hash when entering/leaving; `hashchange` listener handles browser back/forward. A "← overview" back button (`data-calm="mode" data-arg="regular"`) in session.js returns to the overview. The calm expansion panel gains a "view" button (`data-calm="session"`) that enters session mode for that row. `calmAction("session")` now re-renders when already in session mode (previously a no-op from the picker). Tests: `test_url_hash_restores_session_on_init`, `test_url_hash_synced_on_session_enter`, `test_url_hash_cleared_on_leave`, `test_hashchange_navigates_back`, `test_back_button_in_session_view`, `test_calm_expansion_has_view_button`, `test_calm_view_button_enters_session_mode`. Falsifying edit: remove `syncSessionHash()` call from `setDisplayMode` → `test_url_hash_synced_on_session_enter` fails.
- DONE: Distinct empty/loading states: loading, not-a-spacedock-session (spacedock null), fo-no-entities, non-fo-spacedock
  `sessionView()` in session.js now distinguishes four cases: (a) loading — session key set but not in current data → `sv-loading` with "Looking for session …"; (b) `spacedock: null` → "Not a Spacedock session"; (c) FO with empty workflows → "First officer with no in-flight entities" (mentions freshness-gate); (d) non-FO Spacedock → role + "session". The old generic "This session has no Spacedock workflows" is removed. Tests: `test_loading_state_when_session_not_found`, `test_empty_state_not_a_spacedock_session`, `test_empty_state_fo_no_entities`, `test_empty_state_worker_session`. Falsifying edit: revert `sessionEmptyState` to the old generic message → `test_empty_state_not_a_spacedock_session` fails (old message still shown).
- DONE: Dogfooded against this session (01a02216, Pi FO) and Review handoff (4971fdd9, non-Spacedock) — single session page works well for this session
  The 01a02216 session (Pi FO, empty workflows due to freshness gate) hits the `test_empty_state_fo_no_entities` path: "First officer with no in-flight entities" with a freshness-gate pointer instead of a blank panel. The 4971fdd9 session (spacedock: null) hits `test_empty_state_not_a_spacedock_session`: "Not a Spacedock session" instead of the confusing "no workflows" message. Both have a back button to the overview.
- DONE: Pre-PR suite green: ruff, mypy, lint_embedded, validate_plugins, coverage
  ruff check: All checks passed. ruff format --check: 111 files already formatted. mypy: Success, no issues in 81 source files. lint_embedded.py: Frontend assets clean. validate_plugins.py: Validated 1 skills. coverage: 89.3% (threshold 73%). Full unittest suite: 1200 tests OK (1 skipped) + 157 script tests OK. Version parity: 0.12.0; no version fields moved.

### Summary

Implemented the three rework items from captain dogfood feedback: (1) URL hash routing (`#session=<key>`) makes the session view navigable by URL, with a hashchange listener for browser back/forward, a back button in the view, and a "view" button in the calm expansion panel; (2) four distinct empty/loading states replace the generic "no workflows" message; (3) the FO-no-entities and not-a-Spacedock states are dogfooded against the captain's two test sessions. 8 files changed, +369/-28, commit `0ef6b7c`. The freshness gate itself is NOT fixed (separate task).
