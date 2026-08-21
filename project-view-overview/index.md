---
title: Project view — multi-session entity state overview across sessions
status: ideation
source: captain dogfood feedback
id: 5semdnyk5x3w5gh8vkjxfqxw
gates:
    version: 1
    records:
        - id: gate:5semdnyk5x3w5gh8vkjxfqxw:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:5semdnyk5x3w5gh8vkjxfqxw-backlog-1
              briefing:
                id: briefing:5semdnyk5x3w5gh8vkjxfqxw:backlog:attempt-1:revision-1
                digest: sha256:8648661b2b61037f98090c248689c5ebbd7ac16bf3d4262032b4914d7fc3c5a8
                request-digest: sha256:6342b6256f817feb0f7c335a522c0524157bc1a620d502b7a29d962adf063cb1
                room-ref: ./review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:5semdnyk5x3w5gh8vkjxfqxw:backlog:1
                briefing: briefing:5semdnyk5x3w5gh8vkjxfqxw:backlog:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-21T07:28:23.818279884Z"
                decision: approve
                reason: 'FO autonomous approval (conn granted: ''you have the conn to push to the forked repo and open PR''; reinforced: ''when you have the conn, you should still do gate attempt and record your autonomous approval as resolution''). Backlog seed names a user-facing end value and a concrete dashboard surface; proof-needed well-scoped. Advancing to ideation.'
              application:
                target-stage: ideation
                state: consumed
started: 2026-08-21T08:07:15Z
---

In a project with multiple sessions (e.g. cargento has this FO session plus two
dispatched ensign workers), the dashboard should show the overview entity state
across all the project's sessions — which session is driving which entity, and
the aggregate state of the workflow across the project's active sessions.

## Problem

The session view shows one session's dispatch tree. But a project's workflow is
driven by multiple sessions: a first officer and its dispatched ensigns. An
operator cannot see, for one project, the aggregate picture — which entities are
being worked by which session, what's blocked, what's dispatchable — across all
the project's sessions in one view.

## Included scope

- A project-level view (selectable when grouping by project) that shows, for
  one project's workflow, the entity state aggregated across all the project's
  active sessions: each entity with its current stage, which session is driving
  it, and the workflow's overall progress.
- Reuse `spacedock.workflows` data already published per session; aggregate by
  slug across the project's sessions.

## Excluded scope

- Per-session detail view (owned by `session-view-spacedock-visibility`).
- Per-workflow important-info definition (owned by a separate task).

## Proof needed to decide whether design should start

Whether entity slugs are unique across sessions in a project (so aggregation by
slug is well-defined), and whether the project view can be built from the
existing `/api/data` payload without a new endpoint.

## Proof resolution

**Entity slugs are unique within a workflow across sessions in a project.** An
entity slug is a filename in a shared entity-state directory (`entity_dir`),
which the boot envelope names absolutely. Every FO session for the same
project boots the same workflow and reads the same `entity_dir`, so the slugs
are identical across sessions — they are filenames in one directory, and a
directory cannot hold two files of the same name. `spacedock.session_workflows`
already groups entities by workflow (`workflow_dir`), so aggregation is
well-defined by `(workflow, slug)`, not by slug alone: two workflows in the same
project could declare entities with colliding slugs (they have separate
`entity_dir`s), but the workflow grouping keeps them apart. Confirmed by reading
`spacedock.py:entity_files` (one `scandir` of the entity-state directory, slug =
filename) and `spacedock.py:session_workflows` (entities collected per
`workflow_dir`).

**The project view can be built from the existing `/api/data` payload without a
new endpoint.** The payload already carries everything the project view needs:
`session.project` (a string on every row), `session.spacedock` (role +
`workflows[]` on FO sessions), and `session.harness` / `session.session` (the
session identity). The frontend already groups sessions by project client-side
(`calm.js` `repo` sort, `calmEntries` groups by `r.project`). The project view
repeats the same grouping and, for each project group, collects
`spacedock.workflows` from FO sessions, deduplicates entities by `(workflow,
slug)`, and renders the aggregate tree — all from the same `d.sessions` array the
overviews already consume. No new endpoint, no new collector, no server-side
cross-session scan.

## Proposed approach

A `project` display mode, selectable alongside `regular` and `calm` via the
existing mode bar in `web/controls.js`. Entering it requires no target session:
the mode renders one project panel per distinct `session.project` value in the
payload, each showing the aggregate Spacedock workflow state for that project.

Each project panel is built entirely from the existing `/api/data` payload:

1. **Group.** Partition `d.sessions` by `session.project`. The same grouping
   `calmEntries`' `repo` sort already performs, lifted into its own mode.

2. **Collect workflow data.** For each project group, find sessions whose
   `spacedock.workflows` is non-empty (FO sessions — both Claude and Pi, after
   `pi-agent-spacedock-state` landed). These carry `{workflow, stages, entities:
   [{slug, stage, cycle, live}]}` per workflow.

3. **Merge by (workflow, slug).** FO sessions for the same project read the same
   entity-state directory, so their workflow data agrees. Merge by workflow
   name, deduplicating entities by slug — the first FO session's data wins, and
   a second FO session (if present) can only add a workflow the first did not
   boot. This is a union, not a conflict resolution: one FO session per workflow
   is the common case.

4. **Render.** For each workflow, render a tree: entity nodes positioned along
   the workflow's ordered `stages` spine, reusing the existing `sdWindow` /
   `sdSlug` spine and elision logic from `web/regular.js`. Each entity shows its
   slug, stage, cycle label, and `live` flag. A per-entity session attribution
   line names the FO session (harness + display id) carrying the workflow data
   that published it. The panel header shows the project name and a compact
   progress summary: `N entities · M live · K at gate`.

5. **Non-Spacedock sessions.** Projects with no FO session render a plain
   session list (the same rows `calm` or `regular` would show), so the mode does
   not go blank for a project that has sessions but no Spacedock workflow.

### Simplest rejected alternative

A server-side `/api/project?name=<project>` endpoint that aggregates workflow
state across sessions server-side, with a per-project cache key and collection
pass. It cannot deliver the MVP value because every datum the project view needs
— `session.project`, `session.spacedock.workflows`, `session.harness`,
`session.session` — is already in every `/api/data` response. A second endpoint
doubles the server surface (a new route, a new query path, a new cache key, and a
cross-session collection pass that the per-session collector architecture
forbids: `R-2` in `docs/design-runtime-architecture.md` states a collector may
not import another collector or `aggregate`, so no single collector can read
two sessions' `spacedock` data). The frontend-mode approach reads from the same
payload the overviews already trust, so the project view and the overview cannot
diverge about what an entity's stage is.

## Risk evidence

The riskiest mechanism is whether `spacedock.workflows` from FO sessions can be
merged client-side by `(workflow, slug)` across sessions in the same project,
without a server-side cross-session scan, and whether the result is stable
across the 5-second poll. Both are confirmed by reading the code:

- `session.project` is a string on every session row (`sessions.base_session`).
  The calm view's `repo` sort (`calm.js:calmEntries`) already groups by it
  client-side, proving the grouping is stable and cheap.
- `spacedock.workflows` is published per FO session by `collectors/claude.py` →
  `session_spacedock()` and (after `pi-agent-spacedock-state`) by
  `collectors/pi.py` → `session_spacedock()`. Both call the same
  `spacedock.session_workflows`, which returns entities keyed by `(workflow,
  slug)`. The frontend reads `sess.spacedock.workflows` without knowing which
  harness produced it — `sdBlock` in `regular.js` already does this.
- Merging by `(workflow, slug)` is a union: each FO session contributes its
  workflows; entities within a workflow are deduplicated by slug (the first FO's
  data wins, since all FOs for the same project read the same entity-state
  directory and produce identical data). The merge is idempotent and
  order-independent, so it is stable across polls.
- `setDisplayMode` in `mode.js` is a guarded one-liner widened additively (the
  same pattern `session-view-spacedock-visibility` proposed for its `session`
  mode). `render()` in `main.js` gains an `else if (displayMode === "project")`
  arm; the regular and calm paths are untouched.

No spike needed: all mechanisms are proven by existing code paths that already
group by project, publish workflow data, and render it. The merge is a
client-side union of data already in the payload.

## Expected surface and tolerance

Estimate: ~150–200 lines of new JS in `web/project.js` (the view renderer:
grouping, merge, tree rendering, session attribution), ~10 lines changed in
`web/mode.js` (accept `"project"`), ~5 lines in `web/controls.js` (mode button),
~15 lines in `web/main.js` (render branch), ~5 lines in `web/page.py` (`APP_PARTS`
gains `project.js`), and ~60 lines of new CSS in `web/styles.css` for the
project panel and tree layout. No new Python module, no new collector, no new
HTTP route.

Tolerance: the JS may grow to ~250 if the tree layout needs edge-drawing logic
(SVG connectors between nodes). The Python change is tightly bounded — one
`APP_PARTS` entry. If the merge proves to need conflict resolution (two FO
sessions disagreeing about an entity's stage), the fallback is to show the
freshest (highest `last_activity`) FO's data and flag the conflict — but this is
not expected, because all FOs read the same entity-state directory.

Semantics this may change:
- `displayMode` gains a fourth value (`"project"`). `localStorage` persists it
  like the other modes. The mode bar gains a fourth button.
- `APP_PARTS` in `web/page.py` gains one entry. The assembled page hash changes,
  which is the self-proving property `test_page.py` checks — that test must be
  updated to the new hash.
- No Python runtime module changes. No payload shape changes. The project view
  reads `d.sessions` and `d.generated` from the same payload the overviews use.

## Acceptance criteria

### AC-1: Project view renders the aggregate workflow entity state for a project with an FO session

Selecting the project mode for a payload containing one or more FO sessions in
the same project renders one tree per workflow, with entity nodes colored by
their `stage` and positioned along the workflow's ordered `stages` spine. Live
workers (`live: true`) are visually distinct from parked entities. The entity
slugs, stages, and cycle labels match the `/api/data` payload for those
sessions. Multiple FO sessions in the same project contribute workflows that are
merged by workflow name without duplicating entities.

**Verified by:** a unit test that feeds a fixture `/api/data` payload (two FO
sessions in the same project, each booting a different workflow, with entities
at different stages) into the project-view renderer function and asserts the
rendered HTML contains each entity slug, each stage name, and the `live` class
on live entities. The test also asserts that a workflow published by only one
FO session appears, and that entities shared by both FO sessions (same workflow,
same slug) appear once, not twice.

**Falsifying edit:** delete the merge-by-`(workflow, slug)` deduplication —
shared entities appear twice, and the test asserting single-occurrence fails.

### AC-2: Session attribution names which session is driving each entity

Each entity in the project view carries a session attribution line naming the
FO session (harness + display id) whose `spacedock.workflows` data published
that entity. Live entities (`live: true`) are attributed to the session that
marked them live; parked entities are attributed to the session whose workflow
data carried them.

**Verified by:** the same renderer unit test asserting the rendered HTML
contains the FO session's harness and display id beside each entity it
published. The test fails if the attribution line is removed from the renderer.

**Falsifying edit:** remove the session attribution line from the renderer —
the test asserting the FO session's harness and display id appear fails.

### AC-3: Existing overviews are unchanged

The `regular` and `calm` modes render identically to before this change: no new
DOM elements, no removed elements, no changed class names.

**Verified by:** the existing `test_page.py` assembled-page hash test is updated
to the new hash (since `APP_PARTS` gains `project.js`), but the regular and calm
renderer tests assert the same output as before. The test fails if the regular
or calm render branch gains or loses any element.

**Falsifying edit:** add a `project` class to the mode bar's regular button — the
overview test fails.

## Test plan

1. **Project-view renderer unit tests** (new file `tests/test_project_view.py` or
   additions to the existing web-renderer test module). Feed a fixture payload
   through the project-view render function and assert:
   - AC-1: every entity slug, stage name, and `live` class is present; shared
     entities appear once.
   - AC-2: the FO session's harness and display id appear beside its entities.
   - AC-3: the regular and calm renderers produce unchanged output.
2. **Merge-by-`(workflow, slug)` unit test** (in the same test module). Two FO
   sessions in the same project, same workflow, same entity slug — the renderer
   outputs one entity node, not two. Fails if deduplication is removed.
3. **`APP_PARTS` / assembled-page hash test** (`test_page.py`). Update the
   expected hash to include `project.js`. The test self-proves the part list is
   complete and ordered.
4. **`mode.js` acceptance test** (addition to the JS-renderer test suite).
   `setDisplayMode("project")` sets `displayMode` to `"project"`, persists to
   `localStorage`, and triggers `render(lastData)`. `setDisplayMode("invalid")`
   is a no-op. Fails if the guard is not widened.

All tests run on every runner (pure functions / fixtures, no filesystem or
network).

## Out of scope

- Changing the `regular` or `calm` overviews — this task is additive only.
- A new cross-session data source: the project view reuses existing
  `spacedock.workflows` data already in the payload.
- Per-session detail view (owned by `session-view-spacedock-visibility`).
- Per-workflow important-info definition (owned by a separate task).
- Live-worker attribution for Pi ensign subagents (owned by a follow-up to
  `pi-agent-spacedock-state`, which passes empty `worker_names`). The project
  view shows the `live` flag as published; enriching it with Pi subagent names
  is a separate task.
- A project grouping/filter control for the session list (owned by
  `group-sessions-by-project`). The project mode implements its own grouping;
  it does not depend on that task.
