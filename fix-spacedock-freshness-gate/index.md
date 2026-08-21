---
title: Fix Spacedock entity-state freshness gate (mtime staleness blanks the workflow strip)
status: implementation
source: captain dogfood feedback
id: tzrvnebvdb10fddfr40szvtm
gates:
    version: 1
    records:
        - id: gate:tzrvnebvdb10fddfr40szvtm:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:tzrvnebvdb10fddfr40szvtm-backlog-1
              briefing:
                id: briefing:tzrvnebvdb10fddfr40szvtm:backlog:attempt-1:revision-1
                digest: sha256:dcc36568f0e286ebec8cd255fb4e498078cc37ae00d8e4e30277bd769226699a
                request-digest: sha256:58bd5b698c28c45a4c3f880b662a9c7b7934ec4911dce85aff57207fc42b62f9
                room-ref: ./review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:tzrvnebvdb10fddfr40szvtm:backlog:1
                briefing: briefing:tzrvnebvdb10fddfr40szvtm:backlog:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-21T07:28:23.355151244Z"
                decision: approve
                reason: 'FO autonomous approval (conn granted: ''you have the conn to push to the forked repo and open PR''; reinforced: ''when you have the conn, you should still do gate attempt and record your autonomous approval as resolution''). Backlog seed names a user-facing end value and a concrete dashboard surface; proof-needed well-scoped. Advancing to ideation.'
              application:
                target-stage: ideation
                state: consumed
        - id: gate:tzrvnebvdb10fddfr40szvtm:ideation
          stage: ideation
          attempts:
            - id: gate-attempt:tzrvnebvdb10fddfr40szvtm-ideation-1
              briefing:
                id: briefing:tzrvnebvdb10fddfr40szvtm:ideation:attempt-1:revision-1
                digest: sha256:9ddeb5f2daa951ef7764ee64b28af2ec7cea1605d0a7b78f57519c687a52af08
                request-digest: sha256:07d5eb205b859a0836ec793237f571b7fc1fb76079b8108eac2316884dba7e17
                room-ref: ./review/ideation/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:tzrvnebvdb10fddfr40szvtm:ideation:1
                briefing: briefing:tzrvnebvdb10fddfr40szvtm:ideation:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-21T07:55:37.343186712Z"
                decision: approve
                reason: 'conn granted: ''you have the conn to push to the forked repo and open PR''; reinforced: ''when you have the conn, you should still do gate attempt and record your autonomous approval as resolution''. Ideation is sound: drop the mtime gate (the 4 other gates suffice); git-commit-time and frontmatter started: correctly rejected. 4 ACs with falsifying edits. Advancing to implementation.'
              application:
                target-stage: implementation
                state: consumed
started: 2026-08-21T07:28:35Z
worktree: .worktrees/spacedock-ensign-fix-spacedock-freshness-gate
---

A long-running first-officer session that has been driving a workflow for hours
shows `workflows: []` on the dashboard — no strip, no entities — even though it
is classified as a first officer and the entity state is committed and current.

## Problem

`spacedock.read_entities` gates every entity file by `is_fresh(config, now,
info.st_mtime, window_sec)` — the file's **mtime** must be within the freshness
window (default 1 hour). But Spacedock entity state is committed via git; a file's
mtime reflects the last checkout/write, not the last logical change. A session
that committed entity state 2 hours ago and has been doing PR review since has
stale mtime → `read_entities` returns `[]` → `workflows: []` → the strip blanks.

Measured: this session (a Pi FO driving the `dev` workflow for hours) shows
`spacedock: {"role": "first-officer", "workflows": []}` on the dashboard. The
entity dir exists, the boot envelope resolves, the entity files are committed
and current — but their mtime is hours old, so `read_entities` filters them out.

## Included scope

- Replace or supplement the mtime freshness gate in `read_entities` with a signal
  that reflects actual workflow activity: the git commit time of the entity file,
  or the entity file's frontmatter `started`/`completed` timestamps, or drop the
  freshness gate for Spacedock state entirely (the boot envelope's
  `entity_dir_present` already proves the workflow is live).
- Keep the "don't show retired workflows" intent — but gate on workflow
  activity (boot envelope recency, entity dir presence), not file mtime.

## Excluded scope

- Changing the session freshness window for non-Spacedock collectors.
- The session view's rendering of the empty state (owned by
  `session-view-spacedock-visibility`).

## Proof needed to decide whether design should start

Whether `read_entities` is the only mtime-gated path, and whether git commit time
(or frontmatter timestamps) is reachable read-only without a git dependency.

## Approach

Drop the mtime freshness gate in `read_entities`. The `is_fresh(config, now,
info.st_mtime, window_sec)` check filters entity files by filesystem mtime,
but Spacedock entity state is committed via git — mtime reflects the last
checkout/write, not the last logical change. A long-running first officer
whose entity files were committed hours ago has stale mtime and the strip
blanks.

The session's own freshness (transcript mtime within the window) already
gates whether the session appears on the dashboard at all. The boot envelope
(read from the transcript) names the `entity_dir` — a retired workflow would
not be booted. The `resting` filter in `session_workflows` already excludes
entities on initial/terminal stages. The `status`-in-declared-stages check
in `read_entities` handles per-file discrimination. These are the real gates;
the mtime gate is a false negative on long-running sessions.

### Simplest rejected alternative

Replace mtime with the frontmatter `started:` timestamp. Why it cannot
deliver the MVP value:

1. `started:` is not universally present — 4 of 9 entity files in the live
   `.spacedock-state` checkout lack it (entities seeded and advanced without
   the field).
2. Even when present, `started:` records when the entity *entered* the
   current stage — which can be hours old for an actively-worked entity,
   reproducing the same staleness bug.
3. It would require a fallback to mtime for files without `started:`, which
   means the original bug persists for those files.
4. It is more complex (ISO timestamp parsing, missing-field handling,
   fallback logic) for a gate that adds no value over the session-level
   freshness already in place.

## Riskiest mechanism exercised first

Spike: confirm whether git commit time (or frontmatter timestamps) is
reachable read-only without a git dependency, vs. dropping the mtime gate.

- **Git commit time**: NOT reachable without a git dependency. No `import git`
  or `subprocess.*git` exists anywhere in `cargento_runtime/`. Adding
  `subprocess` git calls would introduce an external dependency (git must be
  installed), a cross-platform risk (git may not be available on all
  platforms), and would violate the "pure parsers" design (D-4 in
  `docs/design-cross-platform.md`). REJECTED.
- **Frontmatter `started:`**: Parseable via the existing `scalar()` function
  + `datetime.fromisoformat()` (Python 3.11+ handles the `Z` suffix natively,
  verified on the project's 3.12 runtime). But not universally present (4 of
  9 entity files lack it), and even when present it is a logical stage-entry
  timestamp that can be hours old — the same staleness as mtime. Does not
  solve the core problem.
- **Dropping the mtime gate**: The session-level freshness (transcript mtime
  within `window_sec`) already gates the session. The boot envelope proves
  the workflow is live for that session. The `resting` and
  `status`-in-declared-stages filters handle the "don't show retired"
  intent. SIMPLEST and MOST CORRECT.

`read_entities` is the only mtime-gated path in `spacedock.py` — confirmed
by grep: `is_fresh` is called exactly once in the module, inside
`read_entities`. No other Spacedock code path gates entity visibility by
file mtime.

## Expected surface + tolerance

One function in `cargento_runtime/spacedock.py`:

- `read_entities`: remove the `is_fresh(config, now, info.st_mtime, window_sec)`
  check (currently lines 575-576). The `now` and `window_sec` parameters
  become unused; remove them from the signature and update the call site in
  `session_workflows` (line 643) accordingly.
- Tolerance: ±5 lines. The change is the removal of one `if` branch and its
  parameters; no new logic is added.

No changes to `cargento/skills/cargento/SKILL.md` (no portability-rule
exposure). No changes to frontend sources.

## Acceptance criteria

**AC1**: A first-officer session whose entity state files have mtime older
than the freshness window still shows its workflow strip on the dashboard.
- Verified by: `read_entities` returns `[(slug, stage)]` for entity files
  whose `status` is a declared stage, regardless of `st_mtime`. The existing
  test `test_entity_state_older_than_the_window_is_history_not_work` is
  updated to assert the entity IS returned (was `[]`, now `[(slug, stage)]`).
  Falsifying edit: re-add the `is_fresh` check in `read_entities` → the test
  fails (returns `[]`).

**AC2**: Entities resting on initial or terminal stages are still excluded
from the strip (the "don't show retired workflows" intent is preserved).
- Verified by: `session_workflows` still filters entities on `resting`
  stages. The existing test
  `test_session_workflows_places_entities_on_the_spine` still passes.
  Falsifying edit: remove the `if stage in resting` check in
  `session_workflows` → the test fails (resting entities appear).

**AC3**: Entity files whose `status` is not a declared stage are still
excluded.
- Verified by: `read_entities` still checks `stage in declared`. The
  existing test `test_entity_state_refuses_everything_that_is_not_an_entity`
  still passes. Falsifying edit: remove the `stage in declared` check → the
  test fails (undeclared stages appear).

**AC4**: No git dependency is introduced.
- Verified by: `grep -rn 'import git\|subprocess.*git\|from git'
  cargento/skills/cargento/cargento_runtime/` returns no results after the
  change. Falsifying edit: add a `subprocess.run(["git", ...])` call → the
  grep returns a result.

## no mock: {not a user-facing surface}

This is a backend-only change to `spacedock.py`'s `read_entities` collector.
The dashboard rendering is unchanged — the fix makes the existing workflow
strip appear when it should, rather than blanking it. No new view, card, or
rendered panel is introduced.

## Test plan

1. Update `test_entity_state_older_than_the_window_is_history_not_work` to
   assert that a stale-mtime entity with a valid stage IS returned (was:
   `[]`, now: `[(slug, stage)]`).
2. Add a test: `read_entities` returns entities regardless of mtime — a file
   with mtime hours in the past and a file with mtime now both appear, as long
   as their `status` is a declared stage.
3. Existing tests for `resting` exclusion, `status`-in-declared-stages,
   symlink refusal, cache invalidation, and newest-first ordering continue
   to pass unchanged (they do not depend on the mtime gate).
4. Remove `now`/`window_sec` from `read_entities` test call-sites if the
   signature is cleaned up; the existing tests that pass these arguments
   are updated to match.

## Stage Report: ideation

- DONE: Approach names the simplest rejected alternative and why it cannot deliver the MVP value
  Frontmatter `started:` rejected: not universally present (4/9 files lack it), records stage-entry time (hours old for active entities), needs mtime fallback that preserves the bug, adds complexity for no value over session-level freshness.
- DONE: Riskiest mechanism exercised first: confirm whether git commit time (or frontmatter timestamps) is reachable read-only without a git dependency, vs. dropping the mtime gate
  Git commit time: no git dependency in cargento_runtime/, subprocess git adds external dep + cross-platform risk, violates pure-parser design D-4. Frontmatter `started:`: parseable via scalar() + fromisoformat() (3.11+ handles Z), but not universal and equally stale. Dropping the mtime gate is simplest and correct — session freshness, boot envelope, resting filter, and status-in-declared already gate correctly.
- DONE: Each AC carries an external Verified-by clause with the concrete falsifying edit
  AC1 verified by updated stale-mtime test (falsified by re-adding is_fresh). AC2 verified by existing resting-filter test (falsified by removing the resting check). AC3 verified by existing undeclared-stage test (falsified by removing the declared check). AC4 verified by grep for git imports (falsified by adding a subprocess git call).
- DONE: Backend-only task (spacedock.py collector change, no user-facing rendered surface): record no mock: {not a user-facing surface} in the body
  Recorded in the body above: "no mock: {not a user-facing surface}" — collector change, no new view/card/panel.

### Summary

The mtime freshness gate in `read_entities` is a false negative for
long-running Spacedock first-officer sessions: git-committed entity state
has stale mtime even when the workflow is active. The spike confirmed git
commit time is unreachable without a new dependency (rejected), and
frontmatter `started:` is not universal and equally stale (rejected). The
approach is to drop the mtime gate entirely — the session's own freshness,
the boot envelope's `entity_dir`, the `resting` filter, and the
`status`-in-declared-stages check are the real gates that preserve the
"don't show retired workflows" intent. One function changes in
`spacedock.py`; the existing stale-mtime test is inverted, one new test
added, and the rest of the suite passes unchanged.

## Stage Report: implementation

- DONE: Change satisfies the ideation ACs: drop the mtime freshness gate in read_entities; session freshness + boot entity_dir + resting filter + status-in-declared already gate correctly
  Removed `sessions.is_fresh(config, now, info.st_mtime, window_sec)` from `read_entities` and dropped its `now`/`window_sec` params. Falsifying edit: re-adding the `is_fresh` check makes the inverted stale-mtime test fail (returns `[]`).
- DONE: Tests written first and watched fail for the right reason: existing stale-mtime test inverted (now asserts entities show despite stale mtime), one new test for the no-mtime path
  `test_entity_state_older_than_the_window_is_history_not_work` now asserts `[("drc-1","review")]` for a stale-mtime file (was `[]`); new `test_entity_state_shows_regardless_of_mtime_when_stage_is_declared` asserts both a stale-mtime and a fresh-mtime entity appear. Falsified by re-adding `is_fresh`.
- DONE: No git dependency introduced (subprocess git rejected); pure-parser design preserved
  `grep -rn 'import git\|subprocess.*git\|from git' cargento/skills/cargento/cargento_runtime/` returns no results. The `from cargento_runtime import sessions` import was removed (no longer needed); no subprocess/git added.
- DONE: Pre-PR suite run green: ruff check, ruff format --check, mypy, lint_embedded.py, validate_plugins.py, coverage
  ruff check . / format --check . pass; mypy --strict clean (80 files); lint_embedded.py clean; validate_plugins.py validated 1 skill; bump_version --current 0.11.0; coverage TOTAL 89.3% (fail_under=73). Full unittest discover OK (skipped=1). The import-graph allowlist was updated to drop `cargento_runtime.sessions` from `spacedock` (mechanical consequence of the removed import).

### Summary

Dropped the mtime freshness gate from `read_entities` in `cargento_runtime/spacedock.py`: the `is_fresh(config, now, info.st_mtime, window_sec)` check and its `now`/`window_sec` parameters are gone, and the now-unused `from cargento_runtime import sessions` import was removed. `session_workflows` keeps its `now`/`window_sec` signature (the render API contract the collector and tests call) but stops forwarding them, marking them unused with the codebase's `del` idiom. The stale-mtime test is inverted and a new no-mtime-path test added; the import-graph allowlist in `test_contracts.py` drops the `sessions` dependency. One pre-existing flaky wall-clock linearity test (`test_reverse_lines_stays_linear_on_one_long_record` in `test_transcripts.py`) intermittently fails under VM scheduling jitter both with and without this change — unrelated to Spacedock. Commit `2bfff08` on `spacedock-ensign/fix-spacedock-freshness-gate`.
