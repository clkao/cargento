---
title: Pi live-worker attribution — feed live ensign names to session_workflows
status: implementation
source: captain directive — source of truth is the live ensigns
id: rj497exc44z5es90d7a2bg49
gates:
    version: 1
    records:
        - id: gate:rj497exc44z5es90d7a2bg49:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:rj497exc44z5es90d7a2bg49-backlog-1
              briefing:
                id: briefing:rj497exc44z5es90d7a2bg49:backlog:attempt-1:revision-1
                digest: sha256:9db6429b8f07c980562244070249df4d71499ce8505895ddc36a6db7d0f67bd7
                request-digest: sha256:87224cad04e08e0db3c2e9a9ef602df7ca2845e96a71b822abe1ca35eb1cc25e
                room-ref: ./review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:rj497exc44z5es90d7a2bg49:backlog:1
                briefing: briefing:rj497exc44z5es90d7a2bg49:backlog:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-21T08:42:27.761264687Z"
                decision: approve
                reason: 'conn granted: ''you have the conn to push to the forked repo and open PR''. Captain directive: ''source of truth should be we have 3 ensigns actively working.'' Root cause of this session showing workflows:[] despite 3 live ensigns — Pi collector hardcodes worker_names=[].'
              application:
                target-stage: ideation
                state: consumed
        - id: gate:rj497exc44z5es90d7a2bg49:ideation
          stage: ideation
          attempts:
            - id: gate-attempt:rj497exc44z5es90d7a2bg49-ideation-1
              briefing:
                id: briefing:rj497exc44z5es90d7a2bg49:ideation:attempt-1:revision-1
                digest: sha256:75fd9c81a0e79e8c7d94a0d58771bd852f3218a6a6141cbbdb1fa60805f4987d
                request-digest: sha256:1fda245eb3b62ec17bc44aadb05d529b1d68745b7e07738620c9e98ad9b4661b
                room-ref: ./review/ideation/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:rj497exc44z5es90d7a2bg49:ideation:1
                briefing: briefing:rj497exc44z5es90d7a2bg49:ideation:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-21T09:19:56.552011227Z"
                decision: approve
                reason: conn granted. Spike confirmed 21 dispatches parseable from FO transcript. attribute_worker extension in scope. Advancing to implementation.
              application:
                target-stage: implementation
                state: consumed
started: 2026-08-21T08:42:31Z
worktree: .worktrees/spacedock-ensign-pi-live-worker-attribution
---

The Pi collector passes an empty `worker_names` list to `session_workflows`, so the session view's "live workers first" source is always empty for Pi FO sessions — even when ensigns are actively running. The source of truth for "what is this session doing right now" is the live ensigns; the dashboard should reflect that.

## Problem

In `collectors/pi.py`, `session_spacedock` calls:

```python
runtime_spacedock.session_workflows(config, state, boot, [], now, window_sec)
```

The fourth argument (`worker_names`) is hardcoded `[]`. `session_workflows` already has the mechanism to use it — `attribute_worker(name, slugs, stages)` maps a live worker name to a slug/stage and marks the entity `live: True`, and the "live workers first" source is the freshest of three. But the Pi collector never extracts live worker/ensign names from the transcript, so that source is always empty.

Result: a Pi FO session with 3 ensigns actively working shows `workflows: []` (or a strip with no `live` entities), because the collector hands `session_workflows` nothing to attribute. The entity-state directory (the middle source) also yields nothing for our detached `.spacedock/dev` workflow (the boot envelopes don't resolve its entity_dir), so the session view is blank for the session that most needs it — this one.

The transcript carries the dispatch records: 60 `subagent` mentions and `"agent":"worker"` entries in this session's transcript alone. The data is there; the collector doesn't parse it into worker_names.

## Included scope

- Extract live worker/ensign names from the Pi session transcript: parse the subagent dispatch tool_use records (the `agent` field, and the dispatch file path or task text that carries the slug/stage) to build the `worker_names` list (or a richer `(name, slug, stage)` structure `attribute_worker` can consume).
- Pass the extracted list to `session_workflows` instead of `[]`.
- The session view should then show the 3 live ensigns as `live: True` entities on the workflow strip, sourced from real transcript activity — the ground truth of what this session is doing.
- Reuse `attribute_worker`'s existing slug-attribution; if the dispatch record carries the slug/stage directly (from the dispatch file path), use it rather than guessing from the worker name.
- Dogfood against THIS session (01a02216): it should show the 3 active ensigns (z4/zp/et implementation) as live entities.

## Excluded scope

- The detached-workflow boot/entity_dir resolution (separate concern — the live-worker source should work even when the entity_dir is empty, because `attribute_worker` only needs the roster for slug boundaries, and the dispatch file path can supply the slug directly).
- Rich per-entity metadata (owned by `rich-session-metadata`).
- Cross-session project overview (owned by `project-view-overview`).

## Proof needed to decide whether design should start

Whether the Pi transcript's subagent dispatch tool_use records carry enough structured data (agent name, dispatch file path, or task text with the slug) to attribute a live worker to an entity slug + stage without the entity-state roster, and whether the existing `attribute_worker` can consume a richer `(name, slug, stage)` input or needs a small extension.

## Ideation

### Approach

The live ensigns are attributed from the FO transcript's own dispatch records, not from
worker names. A Pi FO session dispatches ensigns via async `subagent` toolCalls whose
`arguments.workflowScript` is a `runs.all([...])` fan-out; each run entry carries an
`agent: "worker"` and a `task:` string that begins `Read /tmp/spacedock-dispatch/
spacedock-ensign-{slug}-{stage}.md ...`. The slug and stage are read directly off that
dispatch file name — the stage is the trailing token matched against the workflow's known
stages, the slug is the kebab between `spacedock-ensign-` and `-{stage}` — and fed to
`session_workflows` as pre-attributed `(slug, stage)` workers, bypassing `attribute_worker`'s
name-parse (which needs a known slug from the roster).

Liveness model: the live ensigns are the runs of the **most recent async ensign dispatch
batch** — the newest `subagent` toolCall whose `workflowScript` yields at least one
dispatch-file `(slug, stage)`. The ensign workflow dispatches one batch per gate and advances
only after the batch resolves, so the newest ensign dispatch is the in-flight work. Management
calls (`action: "list"/"status"`, `subagent_wait`) and non-ensign async dispatches (rebase
tasks with no dispatch file) carry no `(slug, stage)` and are skipped, so they cannot displace
the live ensign batch.

`session_workflows` gets a small, additive extension: a new `attributed_workers:
list[tuple[str, str, str]]` (slug, stage, cycle) parameter. Its emit loop runs **first**
(freshest source), emitting `{"slug", "stage", "cycle", "live": True}` per attributed worker,
deduped by slug into the existing `seen` set; the existing `worker_names`→`attribute_worker`
path, the roster, and the boot snapshot follow unchanged. The Pi collector passes
`attributed_workers`; the Claude collector keeps `worker_names` and passes `attributed_workers
= []` (default), so its behaviour is untouched.

In `collectors/pi.py`, the active-branch projection gains a `dispatches` field captured only on
async `subagent` toolCalls: the `(slug, stage)` pairs parsed from that call's `workflowScript`
tasks (empty for rebase/management calls). `_info` exposes `live_workers` = the dispatches of
the newest branch entry with a non-empty `dispatches` list. The collector (whose
`session_spacedock` and boot reading arrive on the `pi-agent-spacedock-state` branch) passes
`live_workers` as `attributed_workers`.

### Riskiest mechanism — spike evidence (exercised first)

Parsed session 01a02216's real transcript (1003 JSONL entries, 31 `subagent` toolCalls, 22 async
dispatches). Findings:

- The async dispatch `workflowScript` reliably carries `agent: "worker"` and one `task:` per run
  whose first path matches `spacedock-ensign-{slug}-{stage}.md`. A regex over the task text
  extracted **21 distinct `(slug, stage)` dispatches** with zero false matches; the two rebase
  tasks ("Rebase the … branch") correctly fail to match (no dispatch file).
- The stage splits unambiguously: the trailing token is matched against the workflow's stage
  vocabulary (`backlog/ideation/implementation/validation/done`, all single tokens), so
  `fix-spacedock-freshness-gate-ideation` → slug `fix-spacedock-freshness-gate`, stage `ideation`.
- The most-recent-ensign-batch at `2026-08-21T08:28:30Z` yields exactly the dogfood's three:
  `rich-session-metadata:implementation`, `group-sessions-by-project:implementation`,
  `workflow-important-info:implementation`.
- `attribute_worker` **cannot** consume this without extension: it requires the worker `name`
  to start with `spacedock-ensign-` AND the slug to be present in the `slugs` set (roster ∪
  boot). For a detached workflow whose roster/`booted` is empty it returns `None` for every
  worker, so a direct pre-attributed path is required. (Confirmed: with the
  `pi-agent-spacedock-state` boot fix applied, boot resolves `definition_dir`+`entity_dir` and
  the roster is non-empty — 10 entities — but that is not relied on; the pre-attributed path
  works with an empty roster too.)

### Simplest rejected alternative

**Notify-subtraction** (dispatched keys minus keys seen in `subagent-notify` completions) —
rejected because the `subagent-notify` `content` is **truncated**: a 4-run batch completion
(notify #17) carries the header "Workflow completed with 4 child run(s)" but its `content` body
lists only the first run's `"key"` before being cut off (~1108 chars). The other three keys are
absent from the record, so completion matching by key under-reports completion and over-reports
liveness (my prototype showed 6 "live" instead of 3, including stale ideation runs). The
most-recent-ensign-batch model needs no completion record and is robust to that truncation.

(Secondary rejected: synthesise names `spacedock-ensign-{slug}-{stage}` and seed the `slugs`
set from the dispatch paths so `attribute_worker` matches them. Rejected: it round-trips data we
already hold through a name-parse whose cycle-token and stage-token matching only re-derives
the `(slug, stage)` we parsed directly, adding fragility for no gain; the entity explicitly says
to use the dispatch slug/stage "rather than guessing from the worker name.")

### Expected surface and tolerance

- `cargento_runtime/spacedock.py`: add the `attributed_workers` parameter + a ~10-line emit-first
  loop in `session_workflows`. Tolerance: the loop may share the existing `seen`/dedup machinery;
  no change to `attribute_worker`, `workflow_dirs`, `read_workflow`, or the roster/boot paths.
- `cargento_runtime/collectors/pi.py`: add `dispatches` capture in `_projection` (async
  `subagent` toolCalls only) + `live_workers` derivation in `_info` + pass it through the
  `session_spacedock`/`session_workflows` call. Tolerance: ~30-45 lines; depends on the
  `pi-agent-spacedock-state` branch having landed `session_spacedock` + Pi boot reading first.
- Frontend: **unchanged** — the strip already renders `live: True` entities.

### no mock

no mock: {backend-only — the workflow strip already renders `live: True` entities; this task
extracts and feeds the data (collector + `session_workflows`), adding no new rendered surface}.

### Acceptance criteria

- **AC-1 (live workers appear from transcript dispatches):** A Pi FO session that has dispatched
  ensigns shows those entities as `live: True` on the workflow strip, sourced from the
  transcript's async `subagent` dispatch records — not an empty strip.
  *Verified by:* a unit test feeding a fixture Pi FO transcript containing an async `subagent`
  toolCall whose `workflowScript` task names `spacedock-ensign-{slug}-{stage}.md`, asserting
  `session_workflows(..., attributed_workers=[(slug,stage,"")])` returns a strip entity
  `{"slug": slug, "stage": stage, "live": True}`.
  *Falsifying edit:* pass `attributed_workers=[]` (or delete the emit-first loop) → the strip has
  no `live: True` entity for that slug.

- **AC-2 (attribution works without the roster):** The slug and stage come from the dispatch file
  path, so a live entity is attributed even when the entity-state roster is empty (entity_dir
  absent/empty and `booted` empty) — the detached-workflow case.
  *Verified by:* a test where `boot` resolves `workflow_dir`+stages but `read_entities` returns
  `[]` and `boot_entities` returns `{}`, asserting the dispatched `(slug, stage)` still appears
  `live: True`.
  *Falsifying edit:* route attributed workers through `attribute_worker` (which requires a known
  slug) → returns `None` → no live entity.

- **AC-3 (baseline unchanged — Claude + non-Spacedock):** the Claude live-worker path
  (`worker_names`→`attribute_worker`) and the non-Spacedock Pi session (no boot → no strip) are
  unchanged.
  *Verified by:* the existing `session_workflows`/collector tests pass without modification; a
  Pi session with no boot envelope still yields `spacedock: None`.
  *Falsifying edit:* make `attributed_workers` a required parameter (break the Claude call
  signature) → Claude collector tests fail.

- **AC-4 (dogfood, conditioned on a containment-passing workflow dir):** for session 01a02216
  against a workflow dir whose README passes `read_workflow`'s containment guard (the normal
  case; the local `.spacedock/dev` symlink is a pre-existing dev limitation handled separately),
  the strip shows the three active ensigns — `rich-session-metadata`,
  `group-sessions-by-project`, `workflow-important-info` — at `implementation` as `live: True`.
  *Verified by:* an integration test (or dashboard check) against the real transcript with a
  non-symlinked workflow dir, asserting exactly those three slugs at `implementation` with
  `live: True`.
  *Falsifying edit:* if the most-recent-ensign-batch selection picks a non-ensign batch (e.g. a
  rebase `NOSLUG` dispatch) as "newest", no live ensigns appear.

### Test plan

- `dispatch_file_slug_stage`: given `workflowScript` task strings, the parser returns the correct
  `(slug, stage)`; rejects rebase tasks and unknown trailing stages.
- `session_workflows_attributed_live`: with empty roster/booted and
  `attributed_workers=[(slug,stage,"")]`, the strip contains `{"slug","stage","live":True}`;
  dedup keeps one entity per slug.
- `session_workflows_attributed_first`: an attributed worker wins over a roster entry for the
  same slug (live, freshest source).
- `pi_live_workers_newest_batch`: a fixture Pi branch with several `subagent` dispatches yields
  `live_workers` = the newest non-empty dispatches batch; a trailing management call (no
  dispatches) does not reset it; a trailing rebase (empty dispatches) does not displace it.
- `pi_collect_live_ensigns`: end-to-end on a fixture FO transcript → the session's `spacedock`
  strip carries the dogfood three at `implementation`, `live: True`.
- Regression: existing Claude `session_workflows`/collector tests and the non-Spacedock Pi path
  unchanged.

### Dependencies and residual risks

- **Depends on `pi-agent-spacedock-state` landing first**: that branch adds `session_spacedock`
  to `collectors/pi.py` (calling `session_workflows(..., [], ...)`) and the Pi `toolResult`-role
  boot reading in `spacedock.py`. This entity replaces the `[]` with extracted workers and adds
  the `attributed_workers` extension; without the prior branch there is no `session_spacedock` to
  feed. (Confirmed against that worktree: boot resolves and the roster is non-empty once it lands.)
- **`read_workflow` symlink containment — separate entity (out of scope, FO-confirmed):** the
  local `.spacedock/dev/README.md` is a symlink to `../repo/README.md` which realpath-resolves
  outside the workflow dir, so `read_workflow` returns `None` and `session_workflows` yields `[]`
  regardless of workers. The containment guard is a SECURITY.md boundary and is not touched here;
  the dogfood AC is conditioned on a containment-passing workflow dir (the FO is unblocking
  locally with a real README; the relaxation gets its own entity).
- **Liveness precision:** most-recent-ensign-batch shows a just-completed batch as live until the
  next ensign dispatch (the same freshness compromise Claude's subagent-window makes). If
  per-run precision is later required, a subagent-artifact-transcript-freshness model (mirroring
  Claude's `agent_children`) is the robust upgrade path; noted, not built at ideation.

## Stage Report: ideation

- DONE: Approach names the simplest rejected alternative and why it cannot deliver the MVP value
  Notify-subtraction rejected: `subagent-notify` content is truncated (a 4-run completion lists only the first key), so key-matching under-reports completion and over-reports liveness (prototype showed 6 live, not 3).
- DONE: Riskiest mechanism exercised first — parse a real Pi session transcript's subagent dispatch tool_use records to confirm they carry agent name + dispatch file path (with slug) + stage
  Parsed session 01a02216: 22 async dispatches, 21 distinct `(slug, stage)` from `spacedock-ensign-{slug}-{stage}.md` task paths, zero false matches; `agent:"worker"` confirmed; most-recent ensign batch = the dogfood three at implementation.
- DONE: Each acceptance criterion carries an external Verified-by clause with the concrete falsifying edit
  AC-1..AC-4 each state a test/assertion and the specific edit that makes it fail (delete emit-first loop / route through attribute_worker / make param required / mis-pick the batch).
- DONE: Whether attribute_worker can consume a richer (name, slug, stage) input or needs a small extension
  Needs a small extension: attribute_worker requires a known slug from the roster and a `spacedock-ensign-`-prefixed name; a new `attributed_workers` (slug,stage,cycle) path in session_workflows emits live entities directly, bypassing the name-parse.

### Summary

The FO transcript's async `subagent` dispatch records carry `(slug, stage)` on the dispatch file path reliably enough to attribute live ensigns without the roster. `attribute_worker` cannot consume this directly (it needs a known slug), so the approach adds an additive `attributed_workers` emit-first path to `session_workflows` and a `dispatches` capture in the Pi collector's projection, taking the most-recent ensign dispatch batch as live. Two dependencies surfaced: the `pi-agent-spacedock-state` branch must land first (it adds `session_spacedock` + Pi boot reading), and the `read_workflow` symlink-containment guard blocks the local dev dogfood — confirmed out of scope (separate entity; FO unblocks locally with a real README).

## Stage Report: implementation

- DONE: Extract (slug, stage) from FO transcript subagent dispatch records (spacedock-ensign-{slug}-{stage}.md in workflowScript task paths)
  Added `dispatch_workers(workflow_script)` pure parser in spacedock.py: greedy regex `SD_DISPATCH_RE` extracts (slug, stage) from dispatch file paths, deduped. Falsifying: non-greedy slug → multi-word slugs split wrong.
- DONE: Pass extracted workers to session_workflows via an attributed_workers path (extension to attribute_worker or a pre-attributed input)
  Added `attributed_workers` keyword-only parameter (list[tuple[str,str,str]]) to `session_workflows`; emit-first loop renders pre-attributed workers as live entities, validated against declared stages, deduped by slug. `attribute_worker` unchanged.
- DONE: Pi collector passes extracted worker_names instead of [] to session_workflows
  `collectors/pi.py` `_projection` captures `dispatches` from async subagent toolCalls (via `_subagent_dispatches` helper); `_info` exposes `live_workers` (newest non-empty batch); `session_spacedock` passes `live_workers` as `attributed_workers`. Falsifying: delete the pass-through → strip empty.
- DONE: Session view shows live ensigns as live:True entities on the workflow strip
  Verified by `test_pi_collect_live_ensigns_from_fan_out_dispatch`: a 3-run fan-out dispatch yields three `live: True` entities at `implementation`. Frontend unchanged — strip already renders `live: True`.
- DONE: Pre-PR suite green
  ruff check, ruff format --check, mypy --strict, lint_embedded.py, validate_plugins.py, bump_version --current, coverage (89.3% > 73% threshold), full unittest suite (1190 passed, 1 skipped) all green.

### Summary

Merged the `pi-agent-spacedock-state` dependency branch (fast-forward), then added the `dispatch_workers` parser and `attributed_workers` emit-first path to `spacedock.py`, and the dispatches capture + live_workers derivation to `collectors/pi.py`. The Pi collector now feeds the most-recent ensign dispatch batch as pre-attributed `(slug, stage, cycle)` tuples to `session_workflows`, which emits them as `live: True` entities before the roster/boot sources. The Claude collector is unchanged (defaults to None). Six new tests cover the parser, the emit-first/dedup/stage-validation, the newest-batch selection, and the end-to-end fan-out. The `read_workflow` symlink-containment guard still blocks the local dev dogfood (separate entity, out of scope).
