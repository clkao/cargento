---
title: Group and filter the session list by project
status: validation
source: captain dogfood feedback
id: zp7z36m3am49jyqrp685nhz9
gates:
    version: 1
    records:
        - id: gate:zp7z36m3am49jyqrp685nhz9:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:zp7z36m3am49jyqrp685nhz9-backlog-1
              briefing:
                id: briefing:zp7z36m3am49jyqrp685nhz9:backlog:attempt-1:revision-1
                digest: sha256:68fa4cb3effa8122696f1f000bcff806ca965d6db554fb50c212d8c506fbaf78
                request-digest: sha256:39c3dfaaa1ea1469b26014559e550636b79beaa0e91b4357348dc82039367df0
                room-ref: ./review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:zp7z36m3am49jyqrp685nhz9:backlog:1
                briefing: briefing:zp7z36m3am49jyqrp685nhz9:backlog:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-21T07:28:23.625094496Z"
                decision: approve
                reason: 'FO autonomous approval (conn granted: ''you have the conn to push to the forked repo and open PR''; reinforced: ''when you have the conn, you should still do gate attempt and record your autonomous approval as resolution''). Backlog seed names a user-facing end value and a concrete dashboard surface; proof-needed well-scoped. Advancing to ideation.'
              application:
                target-stage: ideation
                state: consumed
        - id: gate:zp7z36m3am49jyqrp685nhz9:ideation
          stage: ideation
          attempts:
            - id: gate-attempt:zp7z36m3am49jyqrp685nhz9-ideation-1
              briefing:
                id: briefing:zp7z36m3am49jyqrp685nhz9:ideation:attempt-1:revision-1
                digest: sha256:1c7d233ef25d2cbcf8fc87ae5f58cf4ab058f16fd777cb976294c199d23878b2
                request-digest: sha256:6d48708dcdbbcdb3fa65233e8bda84606a6b320f09122b2872c0729490d136a0
                room-ref: ./review/ideation/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:zp7z36m3am49jyqrp685nhz9:ideation:1
                briefing: briefing:zp7z36m3am49jyqrp685nhz9:ideation:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-21T08:27:18.561150962Z"
                decision: approve
                reason: 'conn granted: ''you have the conn to push to the forked repo and open PR'' (re-granted post-compaction: ''you have unlimited tokens... you have the conn to push to the forked repo and open PR''). Subspace approved all 4 gates: ''you have the conn, why are you still asking?''. Ideation sound: client-side project filter + grouping, no backend change, reuses existing segmented-control + calm repo-sort; 5 ACs with page-JS falsifying edits. Advancing to implementation.'
              application:
                target-stage: implementation
                state: consumed
        - id: gate:zp7z36m3am49jyqrp685nhz9:validation
          stage: validation
          attempts:
            - id: gate-attempt:zp7z36m3am49jyqrp685nhz9-validation-1
              briefing:
                id: briefing:zp7z36m3am49jyqrp685nhz9:validation:attempt-1:revision-1
                digest: sha256:d0002c0ab509d38615d599845e682b30333cd70432f86f8f2fed5d89468c15ff
                request-digest: sha256:1ef1a96b6e3f801103c9bb7466a83efcd0735e9f5f22ec32d4dba3daaf914109
                room-ref: ./review/validation/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:zp7z36m3am49jyqrp685nhz9:validation:1
                briefing: briefing:zp7z36m3am49jyqrp685nhz9:validation:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-21T09:02:21.917925728Z"
                decision: approve
                reason: 'conn granted: ''you have the conn to push to the forked repo and open PR'' (re-granted post-compaction). Per captain: when you have the conn, you do not need to present — just record the gate and resolution.. Implementation verified: all checklist items DONE, suite green (independently confirmed for z4), commit landed. Delivery proceeds to done.'
              application:
                target-stage: done
                state: pending
started: 2026-08-21T08:07:14Z
worktree: .worktrees/spacedock-ensign-group-sessions-by-project
mod-block: merge:pr-merge
---

With 18 sessions across cargento, subspace-ssh, subspace-v0, tycho, spacedock,
and tmp, the flat session list is hard to navigate. An operator wants to group by
or filter by project to find the sessions they care about.

## Problem

The dashboard's session list is a flat list of all sessions across all
projects. There is no way to group by project, filter to one project, or
collapse projects you don't care about. Finding the cargento sessions among 18
total requires scanning every row.

## Included scope

- A project grouping/filter control in the session list (regular and calm
  views): group sessions by project, or filter to a single project.
- The project is already derived per session (`session.project`); this is a
  display/navigation change, not a new data source.
- Persisted preference (like display mode) so a reload keeps the grouping.

## Excluded scope

- The per-session view itself (owned by `session-view-spacedock-visibility`).
- Cross-session entity state overview within a project (owned by a separate
  task).

## Proof needed to decide whether design should start

Whether `session.project` is reliably populated across all harnesses, and
whether the grouping control can reuse the existing mode-bar pattern.

## Approach

Client-side project filter and grouping, frontend-only.

A `projectFilter` state variable (persisted in `localStorage`, the same way
`displayMode` is) holds either `null` (all projects) or a specific project
string. A project selector bar renders above the session list in both views
when two or more distinct projects are present. Selecting a project narrows
the rows shown to that project's sessions; selecting "all" restores the full
list.

In the regular view, sessions within each section (Working, Idle) are grouped
under project-header dividers — the same divider pattern calm mode's "repo"
sort already uses (`.cm-div` in calm, a new `.pg-head` in regular). When a
filter is active, only the matching project's group renders.

In calm mode, the existing "repo" sort already groups by project with dividers.
The project filter narrows the rows calm passes through `calmFilter`; the
sort and filter are independent — a reader can filter to one project under any
sort, and the "repo" sort groups within an unfiltered list.

No backend changes. The project set is derived from `d.sessions` on each
render — `Array.from(new Set(d.sessions.map(s => s.project)))` — so it tracks
the payload without a server round-trip.

### Simplest rejected alternative

Server-side project filtering via a query parameter (e.g. `?project=cargento`).

Cannot deliver the MVP value because:

1. Switching projects requires a full page reload, killing the SSE stream and
   losing scroll position and cursor state. The existing controls (mode
   switch, sort, filter) all update in place without a reload; a reload-based
   filter would be the only one that doesn't, and it would feel broken beside
   them.
2. Grouping (seeing all projects organized at once) is impossible when the
   server returns only one project's rows. The entity scope names both group
   and filter; a server filter can do one but not both.
3. The data is already all client-side — every session row is already in
   `d.sessions`. There is no data-fetching cost to filtering client-side, so
   the reload buys nothing.

### Risk evidence (proof-needed)

**`session.project` is reliably populated across all harnesses — confirmed.**

All ten collectors call `sessions.base_session(harness, sid, project)` with a
non-empty project string. Each derives it from `sessions.project_from_cwd`
and falls back to either the harness name (cursor, codex, copilot, goose,
opencode, antigravity, pi) or a label from the store path (claude, droid,
gemini) when the cwd is absent or empty. `project_from_cwd` returns
`<parent>/<basename>` — two segments, not a bare basename, so sibling
worktrees under the same repository name stay distinguishable. The project is
never `None` or `""`; the worst case is a single-segment harness-name fallback,
which still groups meaningfully.

Confirmed by reading every `base_session(` call site in
`cargento_runtime/collectors/*.py` — all ten pass a third argument with an
`or "<harness>"` or `or project_label(...)` fallback.

**The grouping control reuses the existing control-bar pattern — confirmed.**

Calm mode already has a segmented sort control (`.cm-seg` / `.cm-segb` in
`calm.js` / `styles.css`) that includes a "repo" sort grouping sessions by
project under dividers. The mode bar (`modeBar()` in `controls.js`) uses the
same segmented-button pattern. A project filter bar follows the same shape:
a label, a segmented group of chips, persisted to `localStorage` exactly as
`DISPLAY_MODE_KEY` is. No new UI primitive is needed.

No spike needed: both mechanisms (`session.project` population, the
segmented-control + localStorage pattern) are proven by existing code.

### Expected surface and tolerance

| File | Change | Lines (est.) |
|---|---|---|
| `web/mode.js` | `projectFilter` state + `localStorage` key + `setProjectFilter()` | ~15 |
| `web/controls.js` | `projectBar()` rendering the chip group, inserted into `modeBar()` output | ~25 |
| `web/regular.js` | Project-group dividers in `workingCard` / `idleRow` sections in `render()` | ~30 |
| `web/calm.js` | `calmFilter` respects `projectFilter`; existing "repo" sort unchanged | ~5 |
| `web/main.js` | `render()` calls `projectBar()` and applies `projectFilter` to session lists | ~15 |
| `web/styles.css` | `.projbar`, `.proj-seg`, `.proj-chip`, `.pg-head` styles | ~25 |
| `tests/test_page.py` | New test: project filter narrows regular view; persistence | ~40 |
| `tests/test_page_calm.py` | New test: project filter narrows calm view | ~30 |

Total: ~185 lines, ±50. Frontend-only; no Python backend, no collector, no
schema change.

### Mock

`mock.html` — a static HTML sketch of the regular view with the project bar
and project-group dividers. Open in a browser to see the target shape:

- The project bar sits between the mode bar and the session list, showing a
  chip per project with session counts.
- "all" is selected by default; clicking a project narrows the list.
- Working and Idle sections gain `.pg-head` project dividers.

### Acceptance criteria

**AC-1: A project filter narrows the session list to one project in both
regular and calm views.**

Verified by: a page-JS test that renders a payload with sessions across three
projects, sets the filter to one project via `setProjectFilter("cargento")`,
and asserts that only `cargento` sessions appear in the rendered `#app`
innerHTML (regular) and `cm-body` (calm). Falsifying edit: remove the
`projectFilter` check from `calmFilter` — the test fails because non-cargento
rows still render.

**AC-2: The filter persists across reloads.**

Verified by: a page-JS test that sets `localStorage` to
`{"cargento.projectFilter":"cargento"}` in the prelude, renders the page, and
asserts that the `cargento` chip has `class="proj-chip on"` and non-cargento
sessions are absent. Falsifying edit: remove the `localStorage.getItem` call
in `mode.js` — the test fails because the filter defaults to "all".

**AC-3: The project bar appears only when two or more distinct projects are
present.**

Verified by: a page-JS test that renders a payload where all sessions share
one project, and asserts `projectBar()` output is empty (no `.projbar` in the
DOM). Falsifying edit: remove the `>= 2` guard — the test fails because the
bar renders for a single project.

**AC-4: With no filter selected, the regular view groups sessions under
project dividers.**

Verified by: a page-JS test that renders a multi-project payload with
`projectFilter` unset and asserts `.pg-head` dividers appear in the Working
and Idle sections, each carrying the correct project name. Falsifying edit:
remove the divider emission from `render()` — the test fails because no
`.pg-head` elements exist.

**AC-5: The filter does not regress the session count or the needs-input
gate.**

Verified by: a page-JS test that filters to a project with no needs-input
sessions and asserts the gate band is empty (`needs.length === 0`), and that
filtering to a project with needs-input sessions still renders the band.
Falsifying edit: filter the `gateQueue` input but not the rendered sessions —
the test fails because the band shows sessions from other projects.

### Test plan

All tests are page-JS tests under the existing `PageJsHarness` (node + DOM
stub), matching the pattern in `test_page.py` and `test_page_calm.py`:

1. **Filter narrows rows (regular):** payload with 3 projects, set filter,
   assert only matching project's sessions in `#app`. (AC-1)
2. **Filter narrows rows (calm):** same payload, switch to calm, set filter,
   assert only matching rows in `cm-body`. (AC-1)
3. **Persistence:** prelude sets `localStorage`, render, assert chip state and
   row filtering match the saved filter. (AC-2)
4. **Bar hidden for single project:** payload with one project, assert no
   `.projbar` in DOM. (AC-3)
5. **Group dividers render (regular):** multi-project payload, no filter,
   assert `.pg-head` dividers with correct labels in Working and Idle. (AC-4)
6. **Gate band respects filter:** filter to project with no blocked sessions,
   assert empty band; filter to project with blocked sessions, assert band
   renders. (AC-5)

Each test asserts on rendered DOM output (behaviour), not on string
substring matches in source — per the page-test discipline in
`page_harness.py`.

## Stage Report: ideation

- DONE: Approach names the simplest rejected alternative and why it cannot deliver the MVP value
  Server-side `?project=` query-param filter — needs a full reload (kills SSE/scroll), can't group (scope requires both), and the data is already client-side so the reload buys nothing.
- DONE: Riskiest mechanism exercised first (the proof-needed spike)
  No spike needed — both mechanisms proven by reading existing code: all 10 collectors populate `session.project` with a non-empty fallback; calm's `.cm-seg`/`cm-div` "repo" sort and `modeBar()`'s segmented pattern + `localStorage` prove the control reuses an existing primitive.
- DONE: Each acceptance criterion carries an external Verified-by clause with the concrete falsifying edit
  AC-1 through AC-5 each name a page-JS test, the rendered DOM assertion, and the specific code removal that makes it fail.
- DONE: Whether
  Confirmed: `session.project` is never `None` or `""` across all ten collectors; the control-bar pattern is already in `calm.js` and `controls.js`.

### Summary

Proposed a client-side project filter and grouping: a `projectFilter` preference persisted in `localStorage` (like `displayMode`), a project chip bar reusing the existing segmented-control pattern, and project-group dividers in the regular view. The calm "repo" sort already groups by project, so calm only needs the filter wired into `calmFilter`. No backend changes — the project set is derived from `d.sessions` per render. A static HTML mock (`mock.html`) renders the target shape. All five ACs have page-JS falsifying edits.

## Stage Report: implementation

- DONE: projectFilter persisted in localStorage (like displayMode); project chip bar reuses segmented-control pattern
  `PROJECT_FILTER_KEY` in mode.js mirrors `DISPLAY_MODE_KEY`; `projectBar()` in controls.js emits `.proj-chip` buttons in a `.proj-seg` group, the same shape as `modeBar()`'s `.modeseg` and calm's `.cm-seg`.
- DONE: Project-group dividers in regular view; calm repo-sort already groups, only needs filter wired into calmFilter
  `groupedByProject()` in regular.js emits `.pg-head` dividers when the board has 2+ projects; `calmFilter()` gained a `projectFilter` predicate; calm's existing "repo" sort is unchanged.
- DONE: No backend changes — project set derived from d.sessions per render
  `Array.from(new Set(d.sessions.map(s => s.project)))` in `projectBar()`; no Python, collector, or schema change.
- DONE: session.project never None/"" (all 10 collectors populate it)
  Verified by reading all ten collector call sites in the ideation stage; no change needed.
- DONE: Pre-PR suite green
  ruff check, ruff format --check, mypy --strict, lint_embedded.py, validate_plugins.py, bump_version --current, coverage (89.2% > 73 threshold), and 1334 unittests all pass.

### Summary

Implemented client-side project filtering and grouping across both dashboard views. mode.js gained `projectFilter` state persisted via `localStorage` (mirroring `displayMode`). controls.js gained `projectBar()` — a chip bar reusing the existing segmented-control pattern, shown only when 2+ distinct projects are present. regular.js gained `groupedByProject()` emitting `.pg-head` dividers. calm.js's `calmFilter()` gained the `projectFilter` predicate, and `calmAction()` routes the "project" action through `setProjectFilter()`. main.js's `render()` applies the filter to `needs`, `working`, and `idle`, and inserts `projectBar(d)` in both views. styles.css gained `.projbar`/`.proj-chip`/`.pg-head` styles. Six new page-JS tests cover all five ACs. Commit: b3af387.
