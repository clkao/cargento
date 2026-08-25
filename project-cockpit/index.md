---
title: Project cockpit and remembered goal
status: breadboard
source: commission seed
started: 2026-08-25T03:31:15Z
completed:
verdict:
score: 0.95
worktree: .worktrees/spacedock-ensign-project-cockpit
issue:
pr:
parent:
budget: three review cycles
integration-base: e2fdaffc10ac31da5e5d39361bb2e95e3ca4c1a7
integration-checkpoint:
development-task:
id: yehhw3jcrd6j7eb2zazad25s
gates:
    version: 1
    records:
        - id: gate:yehhw3jcrd6j7eb2zazad25s:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:yehhw3jcrd6j7eb2zazad25s-backlog-1
              briefing:
                id: briefing:yehhw3jcrd6j7eb2zazad25s:backlog:attempt-1:revision-1
                digest: sha256:76c0e0637e107bd0c8abcc4d162a0f212c26c8fe2f6f901a8fd8409c6c2fa128
                request-digest: sha256:5cf0904e646d1bfd47405c97004ebeca5cc33b758947a326015ba3ffb5a40ea0
                room-ref: ./review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:yehhw3jcrd6j7eb2zazad25s:backlog:1
                briefing: briefing:yehhw3jcrd6j7eb2zazad25s:backlog:attempt-1:revision-1
                by: person:captain
                at: "2026-08-25T03:30:45.588978Z"
                decision: approve
                reason: Captain approved the bounded project-cockpit probe direction and learning spend.
              application:
                target-stage: breadboard
                state: consumed
---

Discover the by-project cockpit that restores operator context before an active session asks for attention.

## Question

Which by-project overview lets the captain immediately recover what each project is working toward, what sessions are active, and which session needs a decision?

## Boundaries and budget

The first breadboard covers active sessions grouped by project, a free-form operator goal persisted in browser storage, and outstanding Cargento asks shown beside that goal. It does not add server-side goal persistence, a real steering transport, or production integration. Use at most three review cycles and begin from the mirror-view prototype at the recorded integration baseline.

## Candidate directions

Compare at least two concrete project-overview shapes. Treat the existing session mirror as reusable evidence and a possible drill-down, not as the predetermined primary view.

## Evidence

The baseline branch already composes project grouping, a session mirror, observer output, causal history, and needs-you metadata. A focused local run of its observer and session-view modules passed 30 tests. Its steering and consistency panels are mocked, its goal is session-derived rather than operator-owned, and its internal model gateway is prototype-only.

## Decision criterion

Shaping must record the criterion that emerges from operating the variants. The intended value is that the captain can recover the project goal, current activity, and the reason attention is needed without reconstructing context from individual transcripts.

## Direct captain communication

Use the existing Cargento ask lane for small bounded choices. Use an artifact review for concrete visual variants. Bring scope, persistence ownership, and gate decisions to the first-officer conversation.

## Development handoff

No development task exists until review passes the demonstrated approach.

## Acceptance criteria

**AC-1 — A captain can recover one project context and locate the session needing attention from one project-level surface.**
Verified by: a live or scripted scenario containing at least two projects, multiple active sessions, and one outstanding ask; changing the ask to the other project must move the needs-you signal to that project.

**AC-2 — The operator-written project goal survives a page reload and is never overwritten by inferred session text.**
Verified by: a page-harness exercise that writes a goal, reloads the page, then publishes a conflicting observer-derived goal and confirms the operator text remains authoritative.

**AC-3 — The review distinguishes demonstrated project behavior from mocked mirror content.**
Verified by: the review inventory names every live data source and labels or removes every mocked section; replacing a live source with a fixture-only constant must fail the inventory exercise.

### Feedback Cycles

## Stage Report: breadboard

- DONE: Produce at least two inspectable project-overview shapes that make the project goal, active sessions, and the session needing attention recoverable from one surface.
  Commit `7be2c8c` adds a project deck and attention ledger over one shared scenario; removing either renderer makes the shape exercise fail.
- DONE: Exercise the riskiest paths end to end: move an outstanding ask between two projects, and reload an operator-written browser goal while conflicting observer text is published.
  `node --test docs/breadboards/project-cockpit/app.test.js` fires the page handlers, moves the visible ask and signal, reconstructs the page over the same storage, and rejects observer overwrite; bypassing either reducer or precedence rule fails.
- DONE: Inventory live versus mocked data, observed failure modes, and the choices that still matter without adding production integration.
  The artifact and README classify every source, record three observed failures and four open choices; labeling a fixture-only source live makes the inventory audit fail.

### Summary

Built a standalone, disposable project cockpit from mirror baseline `e2fdaff`, leaving shipped runtime bytes untouched. The deck favors bounded project-context recovery; the ledger favors cross-project scanning, and both preserve the attention reason after ask reassignment. The page served successfully and all executable checks passed, but browser automation was unavailable, so visual inspection remains an honest review action rather than claimed evidence.

## Stage Report: shaping

- DONE: Record the evidence-derived decision criterion and a side-by-side comparison whose costs and tradeoffs explain which variant best restores operator context.
  `docs/breadboards/project-cockpit/README.md` selects the deck by whether one bounded region restores goal, work, asking session, and question; its six-row comparison names the ledger's scan advantage and both variants' costs.
- DONE: Integrate the selected checkpoint through the single-writer proto/operator-cockpit lane while preserving operator-authored goal precedence.
  Exercised commit `45711064de8389bda0e0d42c88b4880516565365` rebases the checkpoint onto `e2fdaff`; 3 cockpit and 30 baseline tests passed, including reload-plus-conflict precedence, and `clkao/proto/operator-cockpit` resolves to that SHA.
- DONE: Name the exact exercised integration commit and provide a reproducible viewing procedure that lets the captain experience or falsify the recommendation.
  Fetch `https://github.com/clkao/cargento.git` branch `proto/operator-cockpit`, verify HEAD is `45711064de8389bda0e0d42c88b4880516565365`, run `node --test docs/breadboards/project-cockpit/app.test.js`, then serve that directory on `127.0.0.1:8765`; move the ask, write/reload a goal, publish the conflict, and switch to the ledger.

### Summary

The recommended checkpoint makes the project deck primary because it preserves the context boundary the operator is trying to recover; the ledger remains a falsifiable alternate for dense comparison. The single-writer lane was initialized only on the authorized `clkao` remote, its remote SHA matches the tested local head, and the exact served checkpoint preserved operator-authored goal precedence.

## Stage Report: review

- DONE: Independently reproduce every acceptance-criterion path on exact checkpoint `45711064de8389bda0e0d42c88b4880516565365`, including ask reassignment, goal reload under conflicting observer text, and the live-versus-mocked inventory.
  Local HEAD and `clkao/proto/operator-cockpit` both resolved to the checkpoint; the 3 cockpit checks and 30 observer/session-view checks passed, and the page plus both assets served on `127.0.0.1:8765`.
- DONE: Reproduce AC-1 ask reassignment across two projects and multiple sessions.
  The page harness moved `ask-1`, the highlighted project, question, and session id from `cockpit` to `launch-notes`; hard-coding the target to `launch-notes` is the mutation that would expose the path's missing reverse-direction coverage.
- DONE: Reproduce AC-2 goal reload under conflicting observer text.
  The page harness submitted `Keep projects legible at a glance.`, reconstructed the page over the same storage, published conflicting observer text, and kept the operator value authoritative; removing storage lookup or precedence makes this check fail.
- FAILED: Reproduce AC-3's required live-versus-mocked falsification.
  Replacing the live ask reassignment `ask.projectId = projectId` with fixture-only constant `ask.projectId = "launch-notes"` left all 3 cockpit tests green; the audit validates prose labels, not the live implementation it claims to inventory.
- DONE: Compare the selected project deck with the ledger alternative, classify remaining unknowns, and name the fact that would reverse the recommendation.
  The deck keeps goal, active work, asking session, and question inside one boundary and owns inline editing; the ledger is denser and faster to compare across projects but requires three-column joining and has no editor in this checkpoint.
- DONE: Classify remaining unknowns as implementation detail or approach-changing risk.
  Implementation details: storage-key versioning, session-mirror drill-down placement, responsive polish, and adapting the existing grouped response without changing its read-only collectors.
  Approach-changing risks: the inventory proof is uncoupled from behavior; ask-project ownership is unresolved when the asking session remains in another project; and no connected browser was available to inspect whether real project counts reverse the deck's scan advantage.
- DONE: Name the recommendation-reversal fact.
  Reverse the deck recommendation if representative operators recover goal, active work, asking session, and question faster or with fewer wrong joins in the ledger at realistic project counts; reverse this rejection when a fixture-only replacement of each claimed-live mechanism fails a targeted inventory exercise.
- SKIPPED: Complete visual inspection in a controllable browser.
  The in-app browser runtime reported no available browser; static serving and executable page behavior were verified, but no screenshot or visual judgment is claimed.
- DONE: Issue PASSED or REJECTED and, only if PASSED, provide an exact development seed that leaves no product or architecture choice for development to settle.
  **REJECTED.** Do not issue a development seed: AC-3 is not demonstrated, and development would still have to choose the authoritative ask-to-project rule for cross-project reassignment.

### Summary

Recommend **REJECTED** at checkpoint `45711064de8389bda0e0d42c88b4880516565365`. AC-1 and AC-2 reproduce, the deck is the stronger bounded-context default on the available evidence, and the baseline remains green; however, the required AC-3 mutation survives the full cockpit suite, so the review cannot distinguish an exercised live channel from a fixture-shaped constant at its stated evidence bar.

## Stage Report: breadboard (cycle 2)

- DONE: Make AC-3 behaviorally falsifiable: replacing every claimed-live mechanism with a fixture-only constant must fail a targeted exercise, including ask reassignment in both directions.
  Commit `938271f6f75fccbd3d361f90acd5b21784164be8` binds both live inventory rows to probes; its mutation exercise catches the reviewer's exact hard-coded ask destination and a constant browser-goal write, while routing `cockpit → launch-notes → cockpit`.
- DONE: Select and exercise the authoritative ask-to-project ownership rule when an asking session remains in its original project while the ask is reassigned.
  The ask envelope's `projectId` owns attention; the session stays under `cockpit`, while both deck and ledger render its full question and `codex:8f21` under reassigned project `launch-notes`.
- DONE: Preserve the passing goal-persistence and bounded-context paths, record the corrected exact checkpoint, and keep all rolling-branch pushes restricted to clkao/cargento after the FO grants the lane.
  After lane grant, 9 combined cockpit checks and 30 observer/session tests passed, all three static assets served, and only `git push clkao HEAD:proto/operator-cockpit` was used; the remote ref matches exact checkpoint `938271f6f75fccbd3d361f90acd5b21784164be8`.

### Summary

The correction closes the rejected evidence gap by making each live inventory claim mutation-tested rather than prose-audited. It also chooses ask-envelope ownership without relocating the session, preserving bounded context and operator-goal precedence alongside the interaction-origin probe suite. The inherited `e2fdaff` prototype still has its pre-existing Ruff, format, and mypy findings outside this docs-only checkpoint; applicable behavior, frontend, plugin, and serving checks passed.
