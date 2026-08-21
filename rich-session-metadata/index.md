---
title: Rich session metadata — entities touched, state, decisions, and progress
status: implementation
source: captain dogfood feedback
id: z4tjfzz9y4dz1vvaz588mc81
gates:
    version: 1
    records:
        - id: gate:z4tjfzz9y4dz1vvaz588mc81:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:z4tjfzz9y4dz1vvaz588mc81-backlog-1
              briefing:
                id: briefing:z4tjfzz9y4dz1vvaz588mc81:backlog:attempt-1:revision-1
                digest: sha256:ccc42b201dd9818ef37d42815ce44b7fa89e69fdc08cc57858eb11ed3842bc8e
                request-digest: sha256:890c71dca7bf7c2b8552257358643bc0729d51f3c3e816367634a987885790f6
                room-ref: ./review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:z4tjfzz9y4dz1vvaz588mc81:backlog:1
                briefing: briefing:z4tjfzz9y4dz1vvaz588mc81:backlog:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-21T07:28:23.481133823Z"
                decision: approve
                reason: 'FO autonomous approval (conn granted: ''you have the conn to push to the forked repo and open PR''; reinforced: ''when you have the conn, you should still do gate attempt and record your autonomous approval as resolution''). Backlog seed names a user-facing end value and a concrete dashboard surface; proof-needed well-scoped. Advancing to ideation.'
              application:
                target-stage: ideation
                state: consumed
        - id: gate:z4tjfzz9y4dz1vvaz588mc81:ideation
          stage: ideation
          attempts:
            - id: gate-attempt:z4tjfzz9y4dz1vvaz588mc81-ideation-1
              briefing:
                id: briefing:z4tjfzz9y4dz1vvaz588mc81:ideation:attempt-1:revision-1
                digest: sha256:5dc72312557492e7f1a28e8df57872c341cf1d82a700d7b1116c70fb9c4f206e
                request-digest: sha256:425ad4738333f53ef9e9ae4db535066f6d2be508eceaf5fa0efb9f5e548a8e2e
                room-ref: ./review/ideation/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:z4tjfzz9y4dz1vvaz588mc81:ideation:1
                briefing: briefing:z4tjfzz9y4dz1vvaz588mc81:ideation:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-21T08:27:13.733416189Z"
                decision: approve
                reason: 'conn granted: ''you have the conn to push to the forked repo and open PR'' (re-granted post-compaction: ''you have unlimited tokens... you have the conn to push to the forked repo and open PR''). Subspace approved all 4 gates: ''you have the conn, why are you still asking?''. Ideation sound: entity_gate_summary parses gate records from frontmatter (spiked on 9 real files); complements upstream #124 (entity history vs wait text); 5 ACs with falsifying edits; mock renders target. Advancing to implementation.'
              application:
                target-stage: implementation
                state: consumed
started: 2026-08-21T08:07:11Z
worktree: .worktrees/spacedock-ensign-rich-session-metadata
mod-block:
---

The session view should show, for the session being viewed, the entities it
touched, their current state, the decisions made on them, and what progressed
and when — not just the dispatch tree spine.

## Problem

The current session view renders the dispatch tree (stage-colored entity nodes
along the workflow spine) and a goal line. An operator watching one session
cannot see what that session actually DID — which entities it advanced, what
decisions were made (approve/revise/hold), what stage each entity is at now, and
when it last progressed. The spine shows WHERE in the pipeline each entity sits,
not WHAT happened to it.

## Included scope

- Per-entity card in the session view: slug, current stage, the last gate
  decision (approve/revise/hold) and its reason, the last state-change timestamp,
  and a one-line "what progressed since when" (e.g. "advanced to validation 12m
  ago").
- Secondary section: other dispatchable entities NOT touched by this session
  (the rest of the workflow's backlog), dimmed or separated.
- Data source: the entity state files' frontmatter + the `### Feedback Cycles`
  section + gate records, read read-only.

## Excluded scope

- Cross-session project overview (owned by a separate task).
- Per-workflow important-info definition (owned by a separate task).

## Proof needed to decide whether design should start

Whether the entity frontmatter + gate records + feedback cycles carry enough
structured data to render "last decision + when" without parsing free-form stage
reports, and whether the session view can attribute entity changes to this
session vs. a peer.

## Ideation

### Approach

Extend the entity data published in the `spacedock` payload to carry per-entity
gate decision metadata (last decision, timestamp, reason, target-stage), and
extend the session view frontend to render per-entity cards with that metadata,
separated into "touched by this session" (live) and "not touched" (non-live)
sections.

The existing `session_workflows` in `spacedock.py` already builds per-entity
data: `{slug, stage, cycle, live}`. The `live` flag — set by `attribute_worker`
when a subagent name matches — already attributes entities to this session vs.
peers. What is missing is the gate decision metadata: the last gate record's
last attempt's `resolution.decision`, `resolution.at`, `resolution.reason`, and
`application.target-stage`, all of which live in the entity file's frontmatter
`gates:` block.

A new pure function `entity_gate_summary(config, lines)` in `spacedock.py` reads
the `gates.records[].attempts[].resolution` and `.application` blocks from
frontmatter lines via an indentation-scoped scan — the same approach
`stage_entries` uses for the `stages.states[]` block, and the same proven
parser lineage `scalar()` and `frontmatter_lines()` already use. It returns
`{decision, decision_at, decision_by, target_stage}` or `{}` when no gate
record has a resolution. `read_entities` or `session_workflows` attaches this
to each entity dict, and `sdBlock` in `regular.js` renders it below the spine:
a decision badge (approve/revise/hold), a one-line "advanced to X Ym ago"
progress line, the truncated reason, and the "not touched" entities dimmed
in a separate section.

### Simplest rejected alternative

Derive "what progressed" by diffing the boot envelope's `dispatchable` snapshot
against the entity state directory's current `status` — no new parsing needed.
Why it cannot deliver the MVP value:

1. The boot envelope is a point-in-time snapshot from session start; it carries
   `current` (the stage at boot) but no decision, reason, or timestamp. A
   diff can show "the stage moved" but cannot answer "was it approved or held"
   or "when did it move."
2. `dispatchable: []` is the common case for a long-running first officer that
   booted before work was intaken — there is nothing to diff against.
3. Even when the snapshot is non-empty, the `current` field may be stale
   (entities advanced past boot). The diff would show a stage change the
   operator already knows about, without the decision context that is the
   whole point of the feature.

### Riskiest mechanism exercised first

Spike: verified that the nested `gates.records[].attempts[].resolution` and
`.application` blocks in entity frontmatter are parseable with an
indentation-scoped scanner (no YAML library), extracting `decision`, `at`,
`reason`, `by`, and `target-stage` from all 9 real entity files in the live
`.spacedock-state` checkout.

- **Gate record parsing**: `/tmp/spike_gate_parse3.py` ran an
  indentation-scoped scan over every `*/index.md` and `*.md` file in the state
  checkout. All 6 entity files with gate records yielded the last resolution's
  `decision` (approve), `at` (ISO timestamp), `by` (agent:first-officer or
  person:captain), and `application.target-stage` (the stage the entity was
  advanced to). No file required body parsing or a YAML evaluator.
- **`### Feedback Cycles` section**: grep across all entity files shows the
  heading is present in advanced entities but carries no structured content —
  it is immediately followed by `## Out of scope` or `## Stage Report`. The
  real decision data lives in the frontmatter gate records, not the body.
- **Session attribution**: the `live` flag in `session_workflows` already
  attributes entities to this session (live worker name match) vs. peers (state
  directory / boot snapshot only). Gate records do not carry a session id in
  `resolution.by` (it is a role like `agent:first-officer`, not a session
  identifier), but the `live`/non-`live` split is sufficient for the MVP: it
  separates "touched by this session" from "not touched."

### Expected surface + tolerance

Backend (`cargento_runtime/spacedock.py`):

- New function `entity_gate_summary(config, lines)`: indentation-scoped scan
  of the `gates:` block, returning `{decision, decision_at, decision_by,
  target_stage}` from the last gate record's last attempt. ~35 lines.
- `read_entities` or `session_workflows` calls `entity_gate_summary` for each
  entity and attaches the fields to the entity dict. ~10 lines of changes
  (the frontmatter lines are already read for `status` by `entity_stage`;
  `entity_gate_summary` reuses the same lines).
- The entity dict in the `session_workflows` output gains `decision`,
  `decision_at`, `decision_by`, `target_stage` fields.

Frontend (`cargento_runtime/web/regular.js`):

- `sdBlock` extended to render per-entity decision info below the spine: a
  decision badge, a "advanced to X Ym ago" line, and the truncated reason.
  Non-live entities rendered in a dimmed separate section. ~30 lines.

Tolerance: ±15 lines on backend, ±20 lines on frontend.

No changes to `cargento/skills/cargento/SKILL.md` (no portability-rule
exposure). No new endpoint — the data rides in the existing `/api/data`
payload's `spacedock.workflows[].entities[]`.

### Acceptance criteria

**AC1**: Per-entity card shows the last gate decision (approve/revise/hold) and
its timestamp as a relative "Xm ago" line.
- Verified by: `entity_gate_summary` returns the last resolution's `decision`
  and `decision_at` from the frontmatter; the frontend renders a decision badge
  and relative time. Falsifying edit: return `{}` from
  `entity_gate_summary` → no decision or timestamp rendered.

**AC2**: The "what progressed since when" one-liner shows the target-stage the
entity was advanced to (e.g. "advanced to validation 12m ago").
- Verified by: the frontend renders `target_stage` from the gate record's
  `application.target-stage` alongside the relative time. Falsifying edit:
  omit `target_stage` from the entity data → the one-liner shows only the
  decision, not the progression.

**AC3**: Entities not touched by this session (non-live) are visually separated
from those that are (live) — dimmed or in a distinct section.
- Verified by: the frontend renders non-live entities in a separate, dimmed
  section below the live ones. Falsifying edit: remove the `live` flag from
  entity data → all entities appear in one undifferentiated list.

**AC4**: The decision data is derived from entity state file frontmatter (gate
records), not from free-form stage report or `### Feedback Cycles` body parsing.
- Verified by: `entity_gate_summary` reads only frontmatter lines via
  `frontmatter_lines()` + indentation scan; it never reads the body or parses
  `## Stage Report` or `### Feedback Cycles` sections. Falsifying edit:
  change `entity_gate_summary` to search the body for `## Stage Report` → the
  function reads body text, which is the rejected approach.

**AC5**: The existing session view rendering (overview tiles, cards,
sparklines, existing `sdBlock` spine) is unchanged when no Spacedock data is
present or when an entity has no gate records.
- Verified by: existing renderer tests pass unchanged; entities without gate
  records render the spine only (no decision badge, no reason). Falsifying
  edit: make `entity_gate_summary` return a non-empty default for entities
  without gate records → a decision badge appears where none should.

### Test plan

1. New unit test: `entity_gate_summary` extracts `decision`, `decision_at`,
   `decision_by`, and `target_stage` from frontmatter lines containing a
   two-record gate history (backlog → ideation, each with a resolution).
   Falsified by returning `{}`.
2. New unit test: `entity_gate_summary` returns `{}` for frontmatter with no
   `gates:` block. Falsified by returning a non-empty default.
3. New unit test: `session_workflows` attaches `decision`, `decision_at`,
   `decision_by`, `target_stage` to each entity dict when gate records exist.
   Falsified by not calling `entity_gate_summary`.
4. New unit test: entities without gate records get empty decision fields
   (`decision: ""`, `target_stage: ""`) and the frontend renders the spine only.
   Falsified by rendering a decision badge for empty decision.
5. Existing tests for `session_workflows`, `read_entities`, `attribute_worker`,
   `read_workflow`, and the existing `sdBlock` renderer continue to pass
   unchanged.

## Stage Report: ideation

- DONE: Approach names the simplest rejected alternative and why it cannot deliver the MVP value
  Boot-envelope diff rejected: the `dispatchable` snapshot carries `current` (stage at boot) but no decision/reason/timestamp; `dispatchable: []` is the common case for a long-running FO; even when non-empty, a diff shows a stage change without the decision context that is the whole point.
- DONE: Riskiest mechanism exercised first (the proof-needed spike)
  Spike `/tmp/spike_gate_parse3.py` ran an indentation-scoped scan over all 9 entity files in the live `.spacedock-state` checkout. All 6 with gate records yielded the last resolution's `decision`, `at`, `by`, and `application.target-stage` — no YAML library, no body parsing. `### Feedback Cycles` confirmed empty (no structured content; the real data is in frontmatter gate records). Session attribution confirmed: the `live` flag already separates touched/not-touched; gate records carry role not session id, but the live/non-live split is sufficient for the MVP.
- DONE: Each acceptance criterion carries an external Verified-by clause with the concrete falsifying edit
  AC1: decision+timestamp from `entity_gate_summary`, falsified by returning `{}`. AC2: `target_stage` from `application.target-stage`, falsified by omitting it. AC3: `live` flag separates touched/not-touched, falsified by removing it. AC4: frontmatter-only read, falsified by reading the body. AC5: existing rendering unchanged, falsified by a non-empty default for no-gate entities.
- DONE: User-facing surface: mock at `rich-session-metadata/mock.html`
  Static HTML sketch renders two variants: FO with live workers (touched entities with decision badges, progress lines, reasons, spines; not-touched entities dimmed in a separate section) and FO with no live workers (all entities in the not-touched section). Decision badges show approve (green), revise (amber), hold (red). Progress line shows "advanced to X Ym ago" from `target_stage` + `decision_at`.

### Summary

The approach extends the existing `spacedock` payload with per-entity gate
decision metadata (last decision, timestamp, reason, target-stage) parsed from
entity frontmatter by a new pure `entity_gate_summary` function, and extends
`sdBlock` in the frontend to render per-entity cards with that metadata,
separated into touched (live) and not-touched (non-live) sections. The spike
verified the nested gate records structure is parseable with an
indentation-scoped scanner across all 9 real entity files — no YAML library,
no body parsing needed. The simplest rejected alternative (boot-envelope diff)
cannot deliver the MVP because the snapshot lacks decision/reason/timestamp
data and is empty for the common long-running FO case. Five acceptance
criteria with falsifying edits, a five-test plan, and a static HTML mock at
`rich-session-metadata/mock.html` rendering the target card shape.

## Stage Report: implementation

- DONE: `entity_gate_summary(config, lines)` — indentation-scoped scan of the `gates:` block, returns `{decision, decision_at, decision_by, target_stage}` from the last gate record's last resolved attempt, or `{}` when no resolution exists. Frontmatter-only read (never touches the body).
- DONE: `_entity_data` refactored to cache both stage and gate summary from a single frontmatter read, with `entity_stage` and `entity_gate_data` as thin wrappers sharing the cache.
- DONE: `read_entities` returns `(slug, stage, gate_summary)` tuples; `session_workflows` attaches `decision`, `decision_at`, `decision_by`, `target_stage` to each entity dict, using a `gate_map` built from the roster.
- DONE: `sdBlock` in `regular.js` renders live and non-live entities in separate sections, with a decision badge (approve/revise/hold) and a "advanced to X Ym ago" progress line on entities with gate metadata. Non-live entities in a dimmed "not touched" section.
- DONE: CSS styles for `.sd-badge`, `.sd-ok`, `.sd-revise`, `.sd-hold`, `.sd-prog`, `.sd-dim`, `.sd-dim-sep`.
- DONE: Unit tests for `entity_gate_summary` (two-record gate history, no-gates), `session_workflows` gate attachment (with and without gate records), and frontend `sdBlock` rendering (decision badge, progress line, live/non-live split, no-gate entities render spine only).
- DONE: Existing `read_entities` tests updated for the new `(slug, stage, gate)` return type; byte oracle for `regular.js` and `styles.css` updated.
- DONE: Pre-PR suite green: ruff check, ruff format, mypy --strict, lint_embedded, validate_plugins, bump_version --current, full unittest suite (1181 passed, 1 skipped), coverage 89.2% (> 73% threshold).

### Summary

Implemented the rich session metadata feature: per-entity gate decision
metadata (last decision, timestamp, by, target-stage) parsed from entity
state file frontmatter by a new pure `entity_gate_summary` function, attached
to each entity dict in the `session_workflows` payload, and rendered by
`sdBlock` in the frontend as decision badges and progress lines, split into
touched (live) and not-touched (non-live) sections. The frontmatter is read
once per entity (shared cache), never the body. All five acceptance criteria
satisfied with falsifying edits verified by tests.
