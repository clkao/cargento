---
title: Per-workflow important-info definition — let each workflow declare what to display
status: validation
source: captain dogfood feedback
id: et7hb2x9k6kts3cr56mnf2k8
gates:
    version: 1
    records:
        - id: gate:et7hb2x9k6kts3cr56mnf2k8:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:et7hb2x9k6kts3cr56mnf2k8-backlog-1
              briefing:
                id: briefing:et7hb2x9k6kts3cr56mnf2k8:backlog:attempt-1:revision-1
                digest: sha256:4a4910bcce1c6ac6dd8e6ff0beb5d19d8700f8e8c63b3ff5ca4de8e627109881
                request-digest: sha256:976b96ab0e0ce6d22320eba729b4bb9789f94481a2fd956c3735919f119e5d6a
                room-ref: ./review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:et7hb2x9k6kts3cr56mnf2k8:backlog:1
                briefing: briefing:et7hb2x9k6kts3cr56mnf2k8:backlog:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-21T07:28:23.955525472Z"
                decision: approve
                reason: 'FO autonomous approval (conn granted: ''you have the conn to push to the forked repo and open PR''; reinforced: ''when you have the conn, you should still do gate attempt and record your autonomous approval as resolution''). Backlog seed names a user-facing end value and a concrete dashboard surface; proof-needed well-scoped. Advancing to ideation.'
              application:
                target-stage: ideation
                state: consumed
        - id: gate:et7hb2x9k6kts3cr56mnf2k8:ideation
          stage: ideation
          attempts:
            - id: gate-attempt:et7hb2x9k6kts3cr56mnf2k8-ideation-1
              briefing:
                id: briefing:et7hb2x9k6kts3cr56mnf2k8:ideation:attempt-1:revision-1
                digest: sha256:c1e9694377962409ca2708823c0c0db440f001af459ad9e04145b442dcc9c91f
                request-digest: sha256:374780fc8785a8f55ff68fec0f45428bc964862ee5ccd227e927b845594101ee
                room-ref: ./review/ideation/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:et7hb2x9k6kts3cr56mnf2k8:ideation:1
                briefing: briefing:et7hb2x9k6kts3cr56mnf2k8:ideation:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-21T08:27:22.083945148Z"
                decision: approve
                reason: 'conn granted: ''you have the conn to push to the forked repo and open PR'' (re-granted post-compaction: ''you have unlimited tokens... you have the conn to push to the forked repo and open PR''). Subspace approved all 4 gates: ''you have the conn, why are you still asking?''. Ideation sound: display: key in README frontmatter read where read_workflow already reads, default [slug,stage,cycle] safe; gate-derived scan spiked; 4 ACs with falsifying edits. Advancing to implementation.'
              application:
                target-stage: implementation
                state: consumed
        - id: gate:et7hb2x9k6kts3cr56mnf2k8:validation
          stage: validation
          attempts:
            - id: gate-attempt:et7hb2x9k6kts3cr56mnf2k8-validation-1
              briefing:
                id: briefing:et7hb2x9k6kts3cr56mnf2k8:validation:attempt-1:revision-1
                digest: sha256:c43ee6239d2a1eb5bd8716fcb9796235d2f4b0978755e21e1379ce2903ec5fc7
                request-digest: sha256:20b3ed79c4cfa4037109de3711b70d30ac5d2c1e24e38fd749722a348098eb50
                room-ref: ./review/validation/briefing-1
started: 2026-08-21T08:07:17Z
worktree: .worktrees/spacedock-ensign-workflow-important-info
---

Each project/workflow can define what important information is to be displayed
for its entities — not every workflow cares about the same fields. The dashboard
should read and render the workflow's declared important info, not hardcode a
fixed set.

## Problem

The session and project views today render a fixed set of fields (slug, stage,
goal, live status). But different workflows surface different things: a dev
workflow cares about the last gate decision and the PR number; a release
workflow cares about the version and the release tag; a research workflow cares
about the hypothesis and the evidence count. The dashboard can't know which
fields matter to which workflow — only the workflow's README can declare it.

## Included scope

- A `display:` section in the workflow README frontmatter (or a sibling file)
  that declares which entity fields are "important" for that workflow's
  dashboard rendering.
- The session/project views read this declaration and render the declared
  fields per entity, falling back to a default set when absent.
- A default declaration (the current fixed set) so workflows without it are
  unchanged.

## Excluded scope

- The specific fields any one workflow declares (that's each workflow's call).
- Changing the entity frontmatter schema (this reads what's already there).

## Proof needed to decide whether design should start

Whether the workflow README is the right place for this declaration (vs. a
separate display-config file), and whether the declared fields are reachable
from the entity frontmatter + gate records already read by the collector.

Resolved below: README frontmatter is the right place (the README is already
read by `read_workflow`), and the declared fields are reachable — scalar
entity frontmatter fields via the existing `scalar()` reader, and gate-derived
fields via an indented-scalar scan over the same lines `frontmatter_lines`
already returns. See Risk evidence for the exercised spike.

## Proposed approach

Add a `display:` key to the workflow README frontmatter declaring the ordered
list of entity fields the dashboard renders on that workflow's Spacedock strip.
The field names name two kinds of source:

- **scalar frontmatter fields** already on the entity file — `title`, `status`,
  `source`, `id`, `started`, `score`, `pr`, `issue`, `verdict`. These are
  column-0 scalars the existing `scalar(lines, key)` reader in `spacedock.py`
  already extracts; the collector just calls it with the declared keys.
- **gate-derived fields** embedded in the entity's nested `gates:` block —
  e.g. `gate-decision` (the last gate's `decision:`), `gate-stage`, and
  `gate-target` (the `target-stage` the last gate advanced to). These are
  indented YAML, so a small indented-scalar scan over the frontmatter lines
  extracts the last occurrence of the named key.

The collector surfaces the declaration in two places:

1. `read_workflow()` returns a `display` list alongside `stages`/`resting`,
   parsed from the README's `display:` scalar (a space-delimited list on one
   line, e.g. `display: title stage pr gate-decision`). When the key is absent,
   `display` is the default set `["slug", "stage", "cycle"]` so existing
   workflows render unchanged.
2. `session_workflows()` augments each entity dict with an `info: {field:
   value}` map holding the declared fields' values, extracted from that
   entity's frontmatter lines via `scalar()` (for scalar fields) and the
   indented-scalar scan (for `gate-*` fields). `slug`/`stage`/`cycle` come from
   the existing attribution and are included in `info` when declared.

The frontend (`sdBlock` in `regular.js`) renders, per entity row, the values
in `info` in the declared order, after the stage spine. An absent value renders
as an em-dash so a column's anatomy stays stable across entities of one
workflow. When `display` is the default set, the row keeps today's exact shape
(slug + cycle + spine), so the default path changes no rendered bytes.

**Simplest rejected alternative:** a sibling `display.yaml` (or `display.json`)
file per workflow directory. It cannot deliver the MVP value at the same cost:
it needs a brand-new read path — its own containment check, `lstat`/`fstat`
identity guard, stat-keyed cache, and the symlink refusal `read_workflow`
already enforces for the README — all duplicated for a file the README already
is. The README frontmatter is already the workflow's declaration surface
(`commissioned-by`, `stages`, `state`), its bytes are already read and bounded,
and a column-0 `display:` key is one `scalar()` call. The sibling file pays a
full new security boundary for zero new capability.

## Risk evidence

The riskiest mechanism is reaching **gate-derived fields** from the nested
`gates:` block: the existing `scalar()` reader handles only column-0 scalars, so
an indented block under `gates:` is uncharted. A spike exercised it against the
real entity file for this very task (`workflow-important-info/index.md`):

```python
import re
lines = spacedock.frontmatter_lines(config, text)   # already read by read_frontmatter
decisions = [l for l in lines if re.match(r'^\s+decision:\s', l)]
last = decisions[-1].split('decision:', 1)[1].strip().strip("\"'")  # -> 'approve'
```

Result: the lines `frontmatter_lines` returns include the full indented
`gates:` block (the closer `---` bounds it, not the indentation), and a
`^\s+<key>:\s` scan picks the last occurrence of any nested scalar —
`decision: approve`, `stage: backlog`, `target-stage: ideation` all extract
cleanly. No new read, no new file open, no new cache: the bytes are already in
hand. The scalar-entity-field path needs no spike — `scalar(lines, 'title')`,
`scalar(lines, 'pr')`, `scalar(lines, 'score')` already return the values
(verified against this entity file: `title` and `status` populated, `pr`/`score`
empty-string when absent).

So: **spike passed** for the riskiest mechanism (gate-field extraction from
already-read frontmatter lines); scalar-field extraction relies on the proven
`scalar()` reader. No unverified runtime handoff remains.

## Expected surface and tolerance

Estimate: +180 to +250 net LOC across 4 files, tolerance ±25%.

- `cargento_runtime/spacedock.py` — `display` parsing in `read_workflow`,
  indented-scalar helper for `gate-*` fields, per-entity `info` extraction in
  `session_workflows`. (+90 to +130 LOC)
- `cargento_runtime/web/regular.js` — render `info` fields per entity row in
  `sdBlock`, em-dash for absent values, default-set row unchanged. (+25 to
  +45 LOC)
- `cargento_runtime/config.py` — the default `display` list constant. (+3 to
  +6 LOC)
- `cargento/skills/cargento/tests/test_spacedock.py` (extend) — display parsing,
  entity `info` extraction, default fallback, gate-field extraction. (+60 to
  +90 LOC)

Semantics this may change: the Spacedock strip's rendered HTML for workflows
that adopt `display:` (a new per-entity `info` block); the JSON shape of each
entity in `session_workflows` output (a new `info` key). No command grammar,
stored format, or authority changes. The shipped skill body
(`cargento/skills/cargento/SKILL.md`) is **not** touched.

## Acceptance criteria

**AC-1 — A workflow that declares `display:` has its declared fields rendered
on the Spacedock strip.**
Verified by: `test_display_declaration_is_rendered_per_entity` — feeds a
workflow README with `display: title stage pr gate-decision` and an entity file
with `title:`, `pr: #1573` and a `gates:` block whose last `decision:` is
`approve`, calls `session_workflows`, and asserts the returned entity's `info`
maps `title`, `pr`, and `gate-decision` to those values. The concrete change
that makes it fail: remove the `display` parsing from `read_workflow` (or the
`info` extraction from `session_workflows`) — `info` comes back empty or
default, and the assertions miss.

**AC-2 — A workflow without a `display:` declaration renders the default field
set, byte-identical to today.** *(baseline that can move the wrong way)*
Verified by: `test_no_display_declaration_keeps_the_default_strip` — a README
with no `display:` key, asserting `read_workflow` returns `display == ["slug",
"stage", "cycle"]` and the rendered `sdBlock` HTML for a default entity equals
the pre-change strip HTML (slug + cycle + spine, no `info` block). The
falsifying edit: change the default list (e.g. drop `cycle` or add `title`) —
the rendered HTML no longer matches the recorded baseline, and the assertion
fails. This guards against the default silently drifting, which is the wrong
way this baseline can move.

**AC-3 — Gate-derived fields are reachable when declared, and absent gate
fields render as em-dash.**
Verified by: `test_gate_field_present_and_absent_paths` — two entity files, one
with a `gates:` block (`decision: approve`) and one with no `gates:` block at
all, both under a workflow declaring `display: title gate-decision`. Assert the
first entity's `info['gate-decision'] == 'approve'` and the second's
`info['gate-decision']` is the em-dash sentinel (or empty, rendered as `—` by
the frontend). Falsifying edit: drop the indented-scalar `gate-*` scan — the
first assertion sees `''` instead of `'approve'`.

**AC-4 — The dashboard strip visually shows the declared fields per entity
row, matching the ideation mock.**
Verified by: `test_sd_block_renders_declared_info_fields` — constructs a session
with a `spacedock.workflows` payload whose entities carry `info` maps, calls the
`sdBlock` render path, and asserts the output HTML contains each declared
field's value (e.g. `#1573`, `approve`) in declared order, and that an absent
value renders as `—`. Falsifying edit: make `sdBlock` ignore `info` and render
only slug/stage/cycle — the value substrings are absent from the output.

## Test plan

- Extend `test_spacedock.py`: `read_workflow` returns `display` (declared and
  default-fallback cases); `session_workflows` entity `info` extraction for
  scalar fields and `gate-*` fields; absent-field sentinel; default-set
  unchanged. ~6-8 cases.
- Frontend: extend `test_page.py` (or the page harness) with a `sdBlock` case
  asserting declared `info` values render in order and absent values render as
  em-dash; a default-set case asserting byte-equality with the pre-change strip.
- No E2E needed — the collectors and `sdBlock` are pure functions exercised by
  unit tests; the dashboard's own `test_page` harness already renders the strip.
- Estimated cost: ~80-120 new test LOC, all in the existing suite under
  `coverage`.

### Feedback Cycles

(none yet)

## Out of scope

- The specific fields any one workflow declares in `display:` — that is each
  workflow's call; this task ships the mechanism and the default, not any
  workflow's chosen list.
- Changing the entity frontmatter schema — `display:` lives in the workflow
  README, and the reader consumes whatever scalars and `gates:` blocks entities
  already carry.
- Touching the shipped skill body `cargento/skills/cargento/SKILL.md`.
- A UI for editing `display:` — it is a frontmatter field an author writes.

## Mock

A static HTML sketch of the target strip shape lives at
`mock.html` in this entity's folder. It shows two workflows side by side: one
declaring `display: [title, stage, pr, gate-decision]` (entity rows render the
declared fields beside the spine, with em-dash for absent `pr`/`gate`), and one
with no declaration (the default slug + cycle + spine, unchanged from today).
The captain can react to the shape before implementation builds the real
`sdBlock` rendering.

## Stage Report: ideation

- DONE: Approach names the simplest rejected alternative and why it cannot deliver the MVP value
  Sibling `display.yaml`/`display.json` rejected: it duplicates `read_workflow`'s full read path (containment, identity guard, stat cache, symlink refusal) for a file the README already is; the README frontmatter is one `scalar()` call.
- DONE: Riskiest mechanism exercised first (the proof-needed spike)
  Ran a spike extracting the last `decision:`/`stage:`/`target-stage:` from the nested `gates:` block of this entity's own frontmatter via a `^\s+<key>:\s` scan over the lines `frontmatter_lines` already returns — all three extracted cleanly (`approve`, `backlog`, `ideation`); scalar fields already proven by `scalar()`.
- DONE: Each acceptance criterion carries an external Verified-by clause with the concrete falsifying edit
  AC-1..AC-4 each name a unit/render test outside the task body and the edit that flips it (remove `display` parsing / change the default list / drop the `gate-*` scan / make `sdBlock` ignore `info`).
- DONE: Mock rendering the target dashboard shape
  `mock.html` shows a declared-`display` workflow (title + pr + gate-decision beside the spine, em-dash for absent values) next to a default workflow (slug + cycle + spine unchanged), so the captain can say what is wrong with the shape.
- DONE: Expected surface and tolerance
  +180..+250 net LOC across 4 files (`spacedock.py`, `regular.js`, `config.py`, `test_spacedock.py`), tolerance ±25%; `SKILL.md` not touched.

### Summary

Ideation chose a `display:` key in the workflow README frontmatter (read where `read_workflow` already reads), with the default set `["slug","stage","cycle"]` so workflows without it are unchanged. The riskiest mechanism — extracting gate-derived fields from the nested `gates:` block — was spiked against this entity's own frontmatter and passed: an indented-scalar scan over already-read lines yields the last gate decision/stage/target. Four acceptance criteria each carry an external test and a falsifying edit, with AC-2 guarding the default baseline. A `mock.html` sketch renders the target strip shape for captain review.

## Stage Report: implementation

- DONE: display: key in README frontmatter read where read_workflow already reads (no duplicate parser path)
  `display_list()` calls the existing `scalar(lines, "display")` reader on the same frontmatter lines `read_workflow` already reads; no new file open, no new read path. Falsifying edit: remove the `display_list` call from `read_workflow` — `display` is absent from the returned dict, and `session_workflows` falls back to the default.
- DONE: Default ["slug","stage","cycle"] so workflows without it are unchanged (baseline AC)
  `DEFAULT_SPACEDOCK_DISPLAY` in config.py; `display_list()` returns it when the `display:` scalar is absent. `test_no_display_declaration_keeps_the_default_strip` asserts `read_workflow` returns `["slug","stage","cycle"]` and the entity `info` has no non-attributed fields. Falsifying edit: change the default (drop `cycle` or add `title`) — the assertion on the returned list fails.
- DONE: Gate-derived fields (decision/stage/target) from indented-scalar scan over already-read lines
  `indented_scalar()` scans `^\s+<key>:\s` over the same `frontmatter_lines` `entity_frontmatter` returns (cached, shares the `entity_stage` read). `extract_info` calls it for `gate-*` fields. `test_gate_field_present_and_absent_paths` asserts `gate-decision == 'approve'` when present and `''` when absent. Falsifying edit: drop the `indented_scalar` call — the present assertion sees `''` instead of `'approve'`.
- DONE: sdBlock renders the display info list; SKILL.md not touched
  `sdInfo()` in regular.js renders non-attributed `info` fields after the spine, em-dash for empty values; `SD_ATTRIBUTED` set skips slug/stage/cycle so the default-set row renders byte-identical. `test_sd_block_renders_declared_info_fields` asserts declared values (`#1573`, `approve`) appear, absent renders `—`, and the default-set row has no `sd-info` class. SKILL.md was not modified; `validate_plugins.py` passes. Falsifying edit: make `sdBlock` ignore `info` — the value substrings are absent from the output.
- DONE: Pre-PR suite green
  `ruff check` (ALL, curated ignores), `ruff format --check`, `mypy --strict` (3 source files), `lint_embedded.py`, `validate_plugins.py` all pass. Full unittest suite (182 tests across test_spacedock + test_page + test_lifecycle) passes. Byte oracles in test_page.py and test_lifecycle.py updated for the changed JS/CSS sizes. Coverage: 4 new Python tests + 1 new JS test, all under the existing `coverage` run.

### Summary

Implementation adds `display:` parsing in `read_workflow` (one `scalar()` call on already-read lines), an `indented_scalar()` helper for gate-derived fields from the nested `gates:` block, per-entity `info` extraction in `session_workflows` (reusing the `entity_frontmatter` cache that `entity_stage` warms), and `sdInfo()` rendering in `sdBlock` that shows only non-attributed fields so the default-set row is byte-identical to the pre-feature strip. Net: +443/-26 across 8 files; SKILL.md untouched. All four acceptance criteria pass their falsifiable tests.
