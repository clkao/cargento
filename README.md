---
commissioned-by: spacedock@0.27.0
entity-type: task
entity-label: task
entity-label-plural: tasks
id-style: sd-b32
state: .spacedock-state
stages:
  defaults:
    worktree: false
    concurrency: 2
  states:
    - name: backlog
      initial: true
      gate: true
    - name: ideation
      gate: true
    - name: implementation
      worktree: true
      context-sections:
        - Review-finding disposition
    - name: validation
      worktree: true
      fresh: true
      feedback-to: implementation
      gate: true
      context-sections:
        - Review-finding disposition
    - name: done
      terminal: true
---

# Drive Cargento dashboard development through spacedock

Each task ships a Cargento dashboard improvement through PR review: a captain-curated
backlog, design at ideation, a build in a dedicated worktree, independent validation
against external-proof acceptance criteria, and a merge to `main` tracked by the
`pr-merge` mod. Cargento is a passive reader of files other tools already wrote, so the
proof bar here is exercising behavior — a test, a command, a rendered page, or an
on-disk state a fresh agent reproduces — never a grep over this README or a skill body.

## File Naming

Each task lives as a flat markdown file `{slug}.md`. Slugs are lowercase, hyphens, no
spaces. Example: `pi-agent-spacedock-state.md`.

## Schema

Every task file has YAML frontmatter. Fields are documented below; see **Task Template**
for a copy-paste starter.

### Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier; SD-B32 stored ID, displayed/addressed by shortest unique prefix |
| `title` | string | Human-readable task name |
| `status` | enum | One of: backlog, ideation, implementation, validation, done |
| `source` | string | Where this task came from (issue, captain note, retrospective) |
| `started` | ISO 8601 | When active work began |
| `completed` | ISO 8601 | When the task reached terminal status |
| `verdict` | enum | PASSED or REJECTED — set at validation |
| `score` | number | Priority score, 0.0–1.0 (optional) |
| `worktree` | string | Worktree path while a dispatched agent is active, empty otherwise. Sticks across non-terminal advancements and clears at terminal merge. |
| `issue` | string | GitHub issue reference (e.g., `#42`) — optional cross-reference |
| `pr` | string | GitHub PR reference (e.g., `#57`) — set when a PR is opened for this task's branch |
| `mod-block` | string | Pending mod-declared blocking action, format `{lifecycle_point}:{mod_name}` |

## Stages

### `backlog`

A task enters backlog when it is first proposed: a seed description, no design work. The captain-curated holding stage — the gate decides which tasks advance to ideation.

- **Inputs:** The seed outcome (what the dashboard should show or do), the Cargento AGENTS.md quality-gate contract, and any reference artifact (a screenshot, a prior design doc under `docs/`).
- **Outputs:** A seed task body naming the end value (what a user sees or can do that they could not before), included and excluded scope, and the proof needed to decide whether design should start.
- **Good:** The seed names a user-facing end state, not a mechanism; it points at a concrete dashboard surface (a view, a collector, the API) it will change.
- **Bad:** A seed that names only a code change ("refactor `collectors/pi.py`") with no end value, or one that bundles two independent dashboard changes into one task.

- **Gate content:** Show the seed outcome, included and excluded scope, and the proof needed to decide whether design should start.

### `ideation`

The captain greenlights a task for design: flesh out the problem, propose an approach, define acceptance criteria as entity-level end-state properties with `Verified by:` clauses, and write a test plan that matches the AC's level of abstraction.

- **Inputs:** The backlog seed, the Cargento runtime architecture (`docs/design-runtime-architecture.md`), the relevant collector (`cargento_runtime/collectors/*.py`), and the frontend sources under `cargento_runtime/web/`.
- **Outputs:** A chosen approach with the simplest rejected alternative named and why it cannot deliver the value; risk evidence exercising the riskiest mechanism first (or `no spike needed: {proven mechanisms}`); expected surface + tolerance; acceptance criteria each with an external `Verified by:` clause and the concrete change that would make it fail; a test plan.
- **Good:** ACs measure end value (what the dashboard shows or a user can do) and at least one AC measures against a baseline that can move the wrong way; the riskiest path (a transcript parse, a new view's render, a collector's session classification) is exercised end-to-end before the gate.
- **Bad:** ACs whose only proof is review of the task's own prose; a "no spike needed" recorded against an unverified runtime handoff; an approach that touches the shipped skill body (`cargento/skills/cargento/SKILL.md`) without flagging the portability rules.

- **Gate content:** Show the selected approach, risk evidence, expected files and lines with tolerance, semantic changes, and proposed proof for each acceptance criterion.

### `implementation`

The design is approved and the deliverable is built in a dedicated worktree on a feature branch — minimal changes that satisfy the AC, self-contained for validation.

- **Inputs:** The ideation body, the worktree on a feature branch, and the Cargento pre-PR command list from `AGENTS.md`.
- **Outputs:** The code/fixture change satisfying the AC; a Stage Report naming what each new or changed test asserts and the change that would make it fail; findings routed through `## Review-finding disposition`.
- **Good:** Tests written first and watched fail for the right reason; changes scoped to the AC; the pre-PR suite (`ruff check`, `ruff format --check`, `mypy`, `lint_embedded.py`, `validate_plugins.py`, `coverage`) run green before claiming done.
- **Bad:** Skipping the detached adversarial audit on a high-stakes surface (the shipped skill body, the launcher, the status/HTTP mutation paths, the CI/release machinery); a prose-only proof; touching `SKILL.md` without re-running `validate_plugins.py`.

### `validation`

A `fresh` agent independently verifies the deliverable against the ideation AC, reproducing each `Verified by:` clause rather than trusting the implementation's self-report. The validator checks what was produced; it does not produce it. Either gate-approval to `done` or rejection back to `implementation` with concrete fixes.

- **Inputs:** The implementation worktree, the ideation ACs, and the Cargento pre-PR suite.
- **Outputs:** A validation report with non-empty Stage Report results, the checks run, evidence for each AC (test names, command output, rendered page, on-disk state), reviewer findings under workflow labels, and a `PASSED`/`REJECTED` recommendation.
- **Good:** Each AC's evidence names the falsifying edit; the small-change fast path scales checks to the diff's blast radius; a detached adversarial audit runs on any high-stakes surface.
- **Bad:** Re-running a stage's verification reflexively without a report showing the required check did not run green; trusting self-reported "all tests pass" without the suite output; an AC whose only proof is a grep over an instruction file.

- **Gate content:** Show non-empty Stage Report results, checks run, evidence for each acceptance criterion, reviewer findings under workflow labels, and whether delivery can proceed.

### `done`

Terminal state: the task's PR is merged (tracked via the `pr` field and the `pr-merge` mod), `completed` set, `verdict: PASSED`, entity archived. Reached via real merge, not a manual flag flip.

## Review-finding disposition

Every finding enters this checkpoint when it arrives during implementation, validation, a detached audit, consequential FO quick work, or a correction routed from a rejected gate.

1. The reviewer owns observation, not task ownership or authorization.
2. The worker preserves the finding, investigates without candidate mutation, records the four evidence fields, and proposes materiality, task ownership, and disposition separately. Its `actor:ensign` round Resolution is advisory.
3. The FO sends a distinct `fix`, `decline`, `hold`, or `route for decision` authorization through the runtime's addressable-worker boundary.
4. The validator recommends `PASSED` or `REJECTED`; a new finding re-enters step 1.
5. Only the captain changes approved scope, accepted value, thresholds, tolerance, or acceptance criteria.
6. After revise is selected, rejection routing transports the evidence, workflow classifications, authorized dispositions, and concrete assignment unchanged; it never re-triages.

Before FO authorization, candidate bytes and Git HEAD stay unchanged, no candidate commit is made, and no reviewer rerun starts. Read-only file/history inspection, non-mutating reproductions, existing tests, and adversarial work in a throwaway checkout are allowed. After authorization, perform only that disposition; `hold` and `route for decision` forbid mutation and rerun. Changed evidence re-enters the checkpoint, and an unobservable runtime authorization means hold and re-consult.

The four evidence fields are released user and normal workflow; observable harm; affected value AC or non-negotiable boundary; and trigger evidence. Field 3 uses `value-ac[AC-N]`, `captain-ruling[YYYY-MM-DD]`, or `contract[repo/relative/path#anchor]` plus a nonblank claim; `none:` plus a rationale cannot establish Material.

- **Material:** all four fields establish supported-workflow harm to a value AC or protected boundary.
- **Deferred risk:** the trigger is hypothetical, unsupported, unobserved, or outside current promises; record its promote-to-material condition.
- **Polish:** no current user-visible loss or protected boundary is at risk.
- **Needs decision:** the task cannot own the required scope, product, or compatibility decision.

Materiality and task ownership are independent. Owned Material is eligible for an FO-authorized fix; out-of-scope Material holds unchanged as Needs decision. Deferred risk or Polish may be declined only after FO authorization.

## Workflow-specific rules

The FO/ensign operating contract already governs generic stage semantics and proof discipline: prefer the cheapest check that can fail — a shipped guard's run, an existing mechanical check, a one-off falsifiable exercise recorded in the report, then the captain's judgment — with new standing enforcement as the last resort rather than the default; prove by exercising rather than re-reading; and reject any AC whose only proof is a review of its own prose. Tasks in this workflow inherit these rules from the contract their FO loads at boot; the rules below add only the Cargento dev-shape specifics.

- **Repo-mutation worktree layer.** `implementation` and `validation` run in a worktree against the Cargento codebase, and `validation` is `fresh` so an independent agent checks the AC. PR state lives on the `pr` field, managed by the `pr-merge` mod — there is no `pr_open` or `awaiting_merge` stage.
- **No prose-grep over instruction files.** A string match over an instruction file the model reads (this README, `SKILL.md`, a skill, `AGENTS.md`) never proves a behavioral claim. To settle a case, ask whether the expected value comes from outside the file under test; if it does not, the check is a tautology and is banned. A grep whose output is pasted into the validation report is legitimate external evidence for that run; the same grep committed as a test is banned.
- **Evidence must be able to fail.** Each AC's cited evidence names the concrete change that would flip it — the falsifying edit. An author who cannot name what would make the evidence fail has not shown it can fail, and the criterion does not count.
- **Opt-in proof disciplines (copy into the `validation` stage when commissioning).** Adopt the ones the mission needs by folding them into the `validation` stage's Outputs and Bad lists:
  - **Test-first authoring** — for a code or fixture deliverable, write the failing test first, watch it fail for the right reason, then write the minimum code to pass.
  - **External-proof acceptance criteria** — each AC's evidence must come from a check outside the task body (a test, a command's output or exit code, a file the change produces, on-disk state, a rendered dashboard page). Reject self-referential ACs whose only proof is review of the task's own prose.
  - **Detached adversarial audit** — for high-stakes surfaces (the shipped skill body `SKILL.md`, the launcher `server.py`, the status/HTTP mutation paths in `http_api.py`/`aggregate.py`, the CI/release machinery), run a read-only audit on a throwaway checkout that tries to refute the validation with an edit the deliverable's own tests should catch. `Material:` findings route back through the validation→implementation feedback flow; "refuted nothing material" is a valid recorded outcome.
  - **Live scenario for runtime claims** — when an AC's truth is what an agent or model *does* at runtime (a collector classifying a session, a view rendering live data), prove it with a scripted live scenario graded on durable before→after state plus observed output, with a negative case that reds the grade. Mark the AC `Verified by: live <ci-run:<id> | session:<path>>`.

## Workflow State

View the workflow overview:

```bash
spacedock status --workflow-dir spacedock/flow
```

Output columns: ID, SLUG, STATUS, TITLE, SCORE, SOURCE.

Find dispatchable tasks ready for their next stage:

```bash
spacedock status --workflow-dir spacedock/flow --next
```

## Task Template

```yaml
---
id:
title: Task title here
status: backlog
source:
started:
completed:
verdict:
score:
worktree:
issue:
pr:
mod-block:
---

Brief description of this task and what it aims to achieve.

## Problem

{What is broken or missing, why it matters now, and what a fix must cover. Backlog seeds it; ideation sharpens it.}

## Proposed approach

{Ideation: the direction chosen, and the simplest alternative rejected with the reason it cannot deliver the value. Concrete enough that a worker can start.}

## Risk evidence

{Backlog: the check, artifact, or observation that decides whether design should start.}
{Ideation: the riskiest unverified mechanism and what exercising it showed, or `no spike needed: {the proven mechanisms this relies on}`.}

## Expected surface and tolerance

Estimate: {+NNN} net LOC across {M} files, tolerance {±NN%}.
Semantics this may change: {command grammar, stored formats, authority, runtime behavior, or `none`}.

## Acceptance criteria

Each AC names a property of the finished task (not a stage action) and how it is verified. At least one measures the end-value against a baseline that can move the wrong way.

**AC-1 — {End-state property.}**
Verified by: {test name / command output or exit code / file the change produces / resulting on-disk state — something outside this task body that a future reader can reproduce and that can fail; name the concrete change that would make it fail.}

## Test plan

{What tests verify the implementation, estimated cost, whether E2E is needed.}

### Feedback Cycles

{First officer appends one `- Cycle {N}: ...` line per correction round; the validation gate reads reviewer findings from here.}

## Out of scope

{What this task deliberately does not address.}
```

## Commit Discipline

- Commit status changes at dispatch and merge boundaries
- Commit task body updates when substantive
- Implementation commits land on the worktree branch; merge to main happens via the `pr-merge` mod after PR review
