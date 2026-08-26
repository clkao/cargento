---
title: Project cockpit and remembered goal
status: shaping
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

## Stage Report: breadboard (cycle 3)

- DONE: Inventory every proposed project-cockpit datum and interaction mechanism against current Cargento: source, availability, freshness, project/session identity mapping, persistence owner, and trust boundary.
  Commit `4f98613fa814a210b1a36c7f9ab4758b03542d5a` adds a sanitized substrate measurement and inventory covering project labels, `(harness, sid)` session identity, active state, ask envelopes, observer output, browser storage, and every proposed project-level write; it distinguishes observed, observed-empty, inferred, unavailable, and historical fixture evidence.
- DONE: Exercise the real local sources for project grouping, active sessions, outstanding asks, observer output, and browser-owned goal persistence; record missing mechanisms and failure modes without substituting fixtures.
  The read-only probe measured 13 active sessions across 7 non-empty project labels with no identity collisions, an `ask:true` live registry with zero pending asks, and deterministic goal plus open-block output from a real Pi transcript; shipped browser JavaScript declared 8 local-storage keys but no project-goal key, schema, writer, or conflict rule. A non-empty ask was not synthesized because that would mutate the live registry, so registration, attribution, notification, answer, and withdrawal behavior remain explicitly unexercised rather than fixture-substituted.
- DONE: Recommend the smallest demonstrated substrate that shaping may build on, with every inferred, unavailable, or fixture-only input explicitly classified.
  `docs/probes/project-cockpit/SUBSTRATE.md` limits shaping to a read-only grouping over live `/api/data sessions[]`, treats `project` as a fallible display label and `(harness, sid)` as the session key, and permits ask display only for real `asks[]` entries; project goals, ask reassignment, project-level synthesis, and steering remain unavailable pending identity, persistence, conflict, and trust rules. The earlier `docs/breadboards/project-cockpit/` mock is classified as historical fixture evidence only.

### Summary

The corrected breadboard validates the current data plane without producing or serving a UI. It demonstrates a small read-only cockpit substrate while preserving the important negative evidence: no stable project identity, no persisted browser-owned project goal, no trusted ask-to-project authority, and no exercised non-empty live ask. The probe, measurement, inventory, and focused checks are committed at `4f98613fa814a210b1a36c7f9ab4758b03542d5a`; no rolling prototype ref was updated.

## Stage Report: shaping (cycle 2)

- DONE: Reproduce and correct the visible `Last` disclosure collapse from a live dashboard revision rather than treating it as a timer.
  The falsifier opened the focused session's native `<details>`, advanced the dashboard payload, and proved `render(d)` replaced `#app.innerHTML` with a new closed node. Commit `2dea3605cf05ee5ad98423b5aa116c005c68ab9f` captures the outgoing disclosure state by exact `harness:sid` before each replacement and restores both explicit open and explicit closed state. The executed DOM test proves closed → open across advancing revisions → explicitly closed across the next revision.
- DONE: Rebase the owned prototype onto Cargento 0.15 and audit the project-first source, UI, and state boundaries before revising product code.
  Fetched `origin/main` at `7317941` and replayed all 66 prototype commits; `origin/main` is an ancestor of the final checkpoint. The rebase retains 0.15's canonical Git common-directory project key and short name, separately assembled `?next=true` page, current-payload project/session/Spacedock plan views, Claude completed-task snapshot, tab-local workstream and ten-minute delegation metrics, and namespaced local-only steer/guardrail controls. The prototype reuses the canonical project identity and page/server assembly seams. Its restart-safe 24-hour semantic work history, explicit FO/task relation graph, browser focus text, and exact read-only terminal origin remain Explore-only; they are not represented as 0.15 production behavior.
- DONE: Preserve the terminal and task-lane contracts while resolving rebase-specific schema/test drift.
  The rebased collector retains measured child `started_at`, exact workflow-path identity, and the stopped-versus-running task boundary. The registered origin remains exact collected session `codex:01a035ee-2a7b-76f0-873f-eaddc97860c3` → tmux `$0/@0/%0`, stable server PID 4792 and tty `/dev/ttys006`, source grid 202×58, streamed read-only with keyboard input not exposed.
- DONE: Restore and verify the stable review surface at the exact rebased checkpoint.
  `http://127.0.0.1:8766/` runs PID 84208 and serves assembled page SHA-256 `4418c2fa462226aaff0df8aeb775048175c41aba38dc49dba6aef2cc256a41ab`. A 25-second live stream produced four successive revision events (`1787724418.5` through `.8`). The same render reducer exercised by those revisions preserves the disclosure state; the focused origin lookup reports registered, stream connected, and 202×58. Browser automation exposed no controllable browser, so executable DOM/API/SSE proof is recorded separately from visual judgment.
- DONE: Run the focused quality checks appropriate to the rebased prototype.
  Ruff, Ruff format, mypy over 115 files, `scripts/lint_embedded.py`, the 42-test project cockpit module, and a 192-test rebase-sensitive set covering Codex, interaction origin, byte oracles, and project behavior passed. The canonical default-page byte oracles were recomputed from the assembled assets after the additive rebase.

### Summary

The project cockpit is rebased onto Cargento 0.15 and keeps explicit `Last` disclosure state across live outer renders. The live 8766 generation is stable at `2dea360`, its SSE stream is advancing, and its exact read-only terminal remains attached. Cargento 0.15's canonical project identity and isolated project-first preview are reused where authoritative; durable semantic history, FO/task topology, remembered focus, and terminal adjacency remain clearly bounded prototype exploration.

## Stage Report: shaping (cycle 3)

- DONE: Every operator-controlled mirror disclosure, including Last and history, remains open across dashboard revisions and only closes by explicit operator action.
  Commit `c63073a1419bbc3117078cd802ffacfc18e28131` gives every focused-mirror disclosure one exact `harness:sid + control` state key. The executed DOM test opens Last, Past work, and Evidence across advancing outer renders, preserves an explicit Past-work close, proves a second session starts closed, and restores only the first session's remembered states.
- DONE: The prototype branch is fetched and rebased onto current origin/main without touching .spacedock/dev or pushing/integrating.
  `origin/main` at `7317941` remains an ancestor of the 67-commit Explore-only checkpoint; no code push, integration, or `.spacedock/dev` mutation occurred.
- DONE: The history label and contents truthfully cover the measured source-backed time window, with exact oldest/newest timestamps and omissions reported.
  The exact focused root transcript is 24.7 MB, below the bounded 32 MiB cold-scan cap, and its persisted cursor resumes by source signature plus overlap. The initial audit retained 69 normalized events across nearly 24 hours; at final live measurement the rolling cutoff retained 65 events from `2026-08-25T14:12:36Z` through `2026-08-26T06:31:10Z`, a 16h19m observed span after an isolated near-cutoff event expired and exposed a real 7.6-hour source-event gap.
- DONE: Keep the primary graph concise while making the complete retained semantic projection discoverable.
  The five history heads and three steering rows are labeled `Past work · N` and `newest first`, not `24h history`. Evidence exposes all 65 retained normalized source events with the measured span and `24h retention`; the final set is 59 operator directions, 3 assignments, 1 stage transition, 1 final output, and 1 observed goal.
- DONE: Report the source boundary rather than letting lifecycle noise impersonate history.
  Raw transcript rows remain authoritative; lifecycle, reasoning, token, and tool-envelope rows are intentionally absent from semantic history. Consequential child mailbox/transcript output, authoritative Spacedock status history, generic Git commits without exact binding, and task returns remain unavailable or uncollected; the live relation set has three dispatches, three bindings, 59 derived directions, and zero returns.
- DONE: Restore and verify the exact live review checkpoint without regressing terminal authority.
  `http://127.0.0.1:8766/` runs PID 7198 and serves SHA-256 `f7342fe463f5955a72a69ac2d7979071d95f29b5b7fcbf166c337271b09be3a4`; four real SSE revisions (`1787725679.6` through `.9`) arrived in 25 seconds. Root re-registered exact `$0/@0/%0`; lookup reports 202×58, stream connected, read-only, and keyboard input not exposed.
- DONE: Exercise the correction and record inherited branch failures separately.
  The 44 cockpit tests and 197-test source-sensitive set pass with Ruff, format, mypy, and frontend lint. The one full 1,824-test run reports 5 failures and 4 errors inherited outside this correction: earlier prototype CLI mock/import-allowlist drift, collector fixture expectations, lane CSS variable audit, and a surrogate-path loader error.

### Summary

The captain's live rejection identified two distinct truth failures: outer renders erased native disclosure state, and a sparse task-head projection claimed to be the whole rolling day. The corrected checkpoint preserves every focused disclosure per exact session, names the primary projection as past work, and makes the full retained semantic event set discoverable with its measured span and retention policy. The stable 8766 generation remains Explore-only and keeps the exact read-only terminal and FO/task graph contracts.
