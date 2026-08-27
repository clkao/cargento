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
  `http://127.0.0.1:8766/` runs PID 7198 and serves SHA-256 `f7342fe463f5955a72a69ac2d7979071d95f29b5b7fcbf166c337271b09be3a4`; four real SSE revisions (`1787725679.6` through `.9`) arrived in 25 seconds. Root re-registered exact `$0/@0/%0`; the measured lookup reported 202×58, stream connected, read-only, and keyboard input not exposed. When the renewal PTY later ended, final lookup refused `stale-registration`, so the terminal action correctly lost authority instead of surviving its lease.
- DONE: Exercise the correction and record inherited branch failures separately.
  The 44 cockpit tests and 197-test source-sensitive set pass with Ruff, format, mypy, and frontend lint. The one full 1,824-test run reports 5 failures and 4 errors inherited outside this correction: earlier prototype CLI mock/import-allowlist drift, collector fixture expectations, lane CSS variable audit, and a surrogate-path loader error.

### Summary

The captain's live rejection identified two distinct truth failures: outer renders erased native disclosure state, and a sparse task-head projection claimed to be the whole rolling day. The corrected checkpoint preserves every focused disclosure per exact session, names the primary projection as past work, and makes the full retained semantic event set discoverable with its measured span and retention policy. The stable 8766 generation remains Explore-only and keeps the exact read-only terminal and FO/task graph contracts.

## Stage Report: shaping (cycle 4)

- DONE: The globally time-sorted timeline interleaves FO and task events while preserving stable lane identity and source-backed vertical/horizontal edges.
  Commit `5d6d5f26e0b7972050a0cb726eefeae543fc2b5c` rebased the crash-surviving two-file correction onto `origin/main` `e153fc1`, then proved an A-B-A-B FO/task fixture renders in exact timestamp order with same-lane vertical continuity across intervening rows. Captain feedback removed illegible default horizontal edges at final checkpoint `68478afca32c4c2eb0e50de5ea4b49d6c310f008`; exact dispatch/return relations remain readable inside their source entry's details.
- DONE: Meaningful-event and Active/All filtering quiets low-value history without deleting unresolved lanes or reassigning events.
  The live ledger audits every previously rendered row against whether it changes understanding of intent, work, decision, or outcome. Of 66 audited rows, 46 remain semantic entries and 20 fragments, acknowledgements, process/status rows, or duplicate attempts leave the timeline. The default working set is the newest seven source-backed rows; `Earlier meaningful · 39` preserves the other disjoint entries without compressing them into one FO node.
- DONE: The crash-surviving two-file diff is reconciled, tested, committed, and served at stable 8766 without touching .spacedock/dev or pushing/integrating.
  The recovered `project.js`/`styles.css` diff was stashed, the branch rebased cleanly from `7317941` to current `origin/main` `e153fc1`, then restored and completed. Commits `5d6d5f2` and `68478af` are local to `spacedock-ensign/project-cockpit`; no code push, integration, version edit, or `.spacedock/dev` mutation occurred.
- DONE: Make every retained entry itself the source/provenance interaction and remove the separate Evidence surface.
  Each of the 46 live entries is an exact-session persistent disclosure. Its expansion states why it belongs, exact source/confidence/time, task binding, and any legible relation or folded assignment-attempt detail. The newest retained FO entry owns nested source-only messages, so excluded source text remains inspectable without returning as timeline meaning. The separate `Evidence / limits` section is absent, and explicit open plus explicit close survive the same loading/settle, outer-render, SSE, navigation, and fallback-refresh order that previously collapsed nested history.
- DONE: Reconcile the source-backed stage transition to the canonical Project cockpit lane.
  The live source emitted `workflow-unbound:project-cockpit`, while exact dispatches emitted `workflow:df5a30b2a535380b0c33:project-cockpit`. A unique normalized workflow-item match now binds the stage event to the canonical key; live projection reports one Project cockpit lane, while ambiguous same-name workflows remain distinct.
- DONE: Record the exact current source inventory and its primary/source-only boundary.
  Final live measurement retained 74 source events from `2026-08-25T14:12:36.551Z` through `2026-08-26T09:58:30.356767Z`: 68 operator directions, 5 assignments, and 1 stage transition. Relations are 68 derived directions, 5 dispatches, 5 bindings, and zero returns. Forty-six events enter the semantic timeline; excluded messages and three older matching Project cockpit assignments are available only through retained entry details. Task returns, checkpoints, progress heads beyond the stage fact, gate history, and consequential child mailbox/transcript results remain unavailable or uncollected.
- DONE: Verify and serve the exact corrected checkpoint without regressing terminal authority.
  `http://127.0.0.1:8766/` runs PID 17837 from `68478af`, serving 438,155 bytes at SHA-256 `71092de480f15f2e157ee83007cd5b477f9aa913802b27abe499eaf721037511`. Live SSE produced revisions `1787735787.4` through `.6`. Exact collected session `codex:01a035ee-2a7b-76f0-873f-eaddc97860c3` is registered to tmux `$0/@0/%0`, stream connected, read-only, with keyboard input not exposed.
- DONE: Exercise the correction and separate inherited branch failures.
  The 49 cockpit tests, 115 page byte/contract tests, and CSS-variable contract pass together: 165/165. Ruff, Ruff format, mypy over 115 source files, frontend lint, and plugin validation pass. The broader 1,834-test discovery retains unrelated prototype/mock/environment failures in CLI `CapturingServer` signatures, import/surrogate fixtures, and collector timing/import allowlists; all changed project/page/CSS contracts pass alone.

### Summary

The cycle converts a dense causal-looking log into a quiet, inspectable semantic timeline: seven current entries, 39 meaningful earlier entries, stable globally interleaved lanes, and only source-backed same-lane vertical continuity. Every retained row now explains its own inclusion and evidence; duplicate task identity, default horizontal lines, and the separate Evidence section are gone. The final Explore-only checkpoint is committed, live on 8766, and ready for the first-officer gate without any code push or production integration.

## Stage Report: shaping (cycle 5)

- DONE: Fetch and rebase the prototype branch onto current Cargento 0.16 without touching `.spacedock/dev` or pushing/integrating.
  Fetched `origin/main` at `d4e3904e76992c7ec6d65cc0621ec61ceb9ac72a` (`chore(release): v0.16.0`) and replayed all 72 prototype commits. One expected frontend byte-pin conflict occurred in `test_page.py`; it was resolved from the composed assets rather than choosing either stale side. `origin/main` is an ancestor of final checkpoint `1ff7aac89186948ee4f83226f5c17c1b9d5ba95a`; the code worktree is clean, no code ref was pushed, and `.spacedock/dev` was not read or changed.
- DONE: Map the prototype against the real 0.16 next-UI data, UI, and browser-state seams before changing product code.

  | Concern | Decision | Exact 0.16/prototype seam and reason |
  |---|---|---|
  | Project navigation / identity | extend upstream seam | Reuse hash routing and project hierarchy in `web/next/next-boot.js:17-42`, `next-chrome.js:7-108`, and `next-projects.js:78-96`. Keep the upstream display-label route, but scope Focus/context to the focused session's canonical `project_key` with an explicit display-label alias in `next-cockpit.js:7-44`; this avoids silently replacing the prototype's stable Git identity. |
  | Session drill-down | reuse upstream | `next-session.js:8-252` owns lookup, asks, health, tasks, subagents, and token scope. The candidate adds no second session list or mirror-status shell. |
  | Live state | reuse upstream | `next-live.js:1-107` owns the namespaced leader lease, SSE revision refresh, fallback polling, and stalled state; `next-activity.js:7-65` owns active/gated cards and current elapsed values. |
  | Activity history | reuse upstream, extend with semantics | `next-workstream.js:108-254` remains the tab-local sampled activity record. The source-backed semantic timeline is separate meaning, not a second sampler, and is hosted below it. |
  | Measurement | reuse upstream | `next-workstream.js:108-254` and `next-delegation.js:13-177` retain idle/unobserved exclusion, gate coalescing, observed-window labels, and honest unknown rate/scope. No prototype delegation or claimed 24-hour metric is rendered. |
  | Theme / type / motion | reuse upstream | `web/next/styles.css:1-35,244-246` retains bundled Space Grotesk/Mono, system light/dark tokens, and reduced-motion-aware live pulse. |
  | Steer preview / receipts | reuse upstream | `next-controls.js:52-67,137-169` retains ordered, tab-local receipts and the explicit `Not delivered` boundary. No delivery, control, or terminal-input API was added. |
  | Browser persistence | extend upstream seam | Upstream owns namespaced guardrails/workstream state in `next-controls.js:1-50` and `next-workstream.js:7-33`. `next-cockpit.js:7-44,150-188` adds only stable-key per-project Focus with visible legacy label fallback. |
  | Semantic timeline | reuse shared prototype mechanism | `web/page.py:45-52,128-141` injects the accepted `web/project.js:876-1565` renderer byte-for-byte after a next-only vocabulary shim; `next-cockpit.js:89-112` supplies context and host markup. This deletes the need for a second semantic renderer and preserves global newest-first ordering, stable lanes, same-lane rails, Active/All, entry-owned provenance, semantic filtering, and Earlier disclosure. |
  | Per-project Focus | prototype-only | `next-cockpit.js:7-44,78-87,150-188` is browser-local, stable-keyed, visibly aliased, and never presented as durable project authority. Upstream has no equivalent outcome field. |
  | Exact tmux origin / terminal | prototype-only shared mechanism | `web/project.js:538-762`, hosted by `next-cockpit.js:114-143`, retains one-use exact-session registration, output-only WebSocket, read-only xterm, follow-live viewport, and no keyboard/control path. |

  Duplicate mechanisms deliberately absent from the next candidate: legacy project tabs, a second project/session inventory, mirror attention/status shell, parallel activity/delegation/history measurement, the separate Evidence section, default horizontal relation edges, and any steer-delivery transport.
- DONE: Implement the smallest coherent next-UI composition while preserving the current dashboard and accepted semantic/terminal contracts.
  Commit `1ff7aac89186948ee4f83226f5c17c1b9d5ba95a` adds one project-detail host beneath upstream PLAN / GOING ON / DONE / WORKSTREAM. It contributes only stable-key Focus, the shared semantic timeline, and the shared exact terminal. `?next=true` remains a separately assembled opt-in artifact; the default page remains byte-pinned and unchanged in behavior. The A-B-A-B falsifier renders `fo-a, task-a, fo-b, task-b` in exact global timestamp order, with both lane rails spanning the intervening rows and no branch/merge edge markup. Active/All is routed through the next host without changing lane keys.
- DONE: Verify the rebased candidate and restore stable 8766 for captain interaction.
  The 145-test `test_next*.py` discovery and 214-test prototype-sensitive set (`test_page_project`, `test_interaction_prototype`, `test_project_context`, `test_semantic_history`, `test_page`) pass. Ruff, Ruff format, strict mypy over 116 source files, embedded frontend lint, plugin validation, and `git diff --check` pass. No inherited failure appeared in the changed/focused scope; the unrelated broad-suite failures recorded in cycle 4 were not reclassified or hidden.
  Stable 8766 runs PID `96919` from `1ff7aac`. `/` serves 438,181 bytes at SHA-256 `2e6570693249f04062d2e6fc8e45032992b6aaa899db65a7192f78ad93df0dcd`; `/?next=true` serves 332,058 bytes at SHA-256 `fa7c8a4a5fe19f110aa878644d6282d63e7160141724d9272896ff23d33d3bc5`. SSE emitted revision `1787761517.2`. The exact semantic read retained 71 facts (64 operator directions, 5 dispatches, 1 stage transition, 1 source-backed result), 4 work items, and 74 relations (64 derived-from, 5 dispatches-to, 5 binds-to) from `2026-08-25T17:05:29.127Z` through `2026-08-26T16:33:29.087384Z`; unavailable return relations remain zero rather than inferred.
  The original/root session completed the one-use bootstrap after crash recovery. Exact collected session `codex:01a035ee-2a7b-76f0-873f-eaddc97860c3` now resolves to current tmux `$4/@4/%10` (`Cargento:1.1`, tty `/dev/ttys027`, 102×36), stream connected, `read-only-control-stream`, with keyboard input `not-exposed`. Browser automation remains unavailable, so source/DOM/CSS geometry and contrast are falsified in tests while final visual judgment remains captain-owned.

### Summary

Rebased the accepted cockpit onto Cargento 0.16 and composed it inside the upstream opt-in project hierarchy instead of carrying a second dashboard shell. Upstream continues to own project/session navigation, live activity, measurement, design system, browser state, and local-only steer receipts. The candidate adds only the three missing bounded mechanisms—stable-key Focus, the accepted source-backed semantic timeline, and exact read-only tmux output—at committed checkpoint `1ff7aac`, now live on 8766 for captain interaction before any integration decision.

## Stage Report: shaping (cycle 6)

- DONE: Replace session-metadata inference with project-root Spacedock discovery while preserving the existing session-plan and semantic-evidence sources.
  Commit `dae3ed0c53ed1b5cd6e1874b99e4f0bc2c89a0a2` resolves the focused transcript's recorded cwd, verifies its collector/stable-project identity, follows a linked worktree's Git `commondir` to the canonical checkout, and invokes the fixed no-shell `${SPACEDOCK_BIN:-spacedock} status --discover` command there. The command has a 2-second timeout, 64 KiB/64-directory output bounds, a 30-second detached cache, static failure reasons, and a subprocess failure boundary. Only immediate `.spacedock/<workflow>` children are accepted; no filesystem path reaches the browser.
- DONE: Expose the actual project workflow definitions without weakening session-recorded workflow containment or inventing live entity state.
  Project discovery may resolve a workflow README link only when both the workflow directory and link target remain inside the already verified project `.spacedock` definition root. The default session-recorded reader still refuses that broader link. The live response now reports `dev` with `backlog · ideation · implementation · validation · done` and `explore` with `backlog · breadboard · shaping · review · done`, each marked definition `read`; browser rendering labels these as project workflow definitions and explicitly says no live entity state is inferred.
- DONE: Keep live attachment metadata, semantic workflow evidence, project declarations, and unavailable/error states distinct in the 0.16 project page.
  Upstream `session.spacedock.workflows` remains the only authority for the full live PLAN/entity renderer. With no live plan, project-context discovery renders `dev` and `explore` separately. First-officer and ensign attachments are described only as attachments; source-backed semantic work is described only as timeline activity; valid empty discovery, unavailable project root/command, non-zero/error, and timeout each retain distinct honest copy. The removed `This project declares no workflow.` claim cannot return through any tested empty-state branch.
- DONE: Falsify the correction at the server, source-boundary, browser-render, linked-worktree, and live-project seams.
  Forty-eight focused discovery/source-split tests pass, including no session metadata plus two discovered workflows, first-officer without a current plan, ensign-only metadata, semantic workflow evidence, truly empty discovery, missing command, timeout, cache reuse, project-local linked definitions, and a focused transcript inside `.worktrees/<name>` whose command cwd must be the canonical checkout. The complete 146-test next-UI set and 254-test project/page/semantic/Spacedock set pass. Ruff, Ruff format, strict mypy over 116 source files, embedded frontend lint, plugin validation, byte oracles, and `git diff --check` pass. The broader 89-test HTTP module retains one inherited `1ff7aac` failure: its `CapturingServer` double does not accept the pre-existing `interaction_prototype` constructor keyword; the exact live project-context and interaction APIs pass independently.
- DONE: Serve and verify the exact correction checkpoint without mutating development workflow state or pushing/integrating code.
  Stable `http://127.0.0.1:8766/` runs PID `18029` from `dae3ed0`. The default page remains 438,181 bytes at SHA-256 `2e6570693249f04062d2e6fc8e45032992b6aaa899db65a7192f78ad93df0dcd`; `/?next=true` is 336,080 bytes at SHA-256 `48ca191c3fd19c353dafa0f41bc3bd7e474a1c777f153dc44e12f1e1aae1605b`. SSE emitted revision `1787766052.11`. Exact collected root session `codex:01a035ee-2a7b-76f0-873f-eaddc97860c3` resolves to current tmux `$4/@4/%10` (`Cargento:1.1`, tty `/dev/ttys027`, 174×42), stream connected, `read-only-control-stream`, with keyboard input `not-exposed`. The in-app browser runtime could not initialize in this worker, so executable DOM/source geometry remains the worker proof and final visual judgment remains captain-owned. No `.spacedock/dev` state was changed, and no code ref was pushed or integrated.

### Summary

The rejected empty state now observes workflow truth at the project boundary instead of treating a session's absent attachment strip as a declaration about the repository. Cargento resolves the selected session to the canonical checkout, asks Spacedock for commissioned workflow directories, renders `dev` and `explore` as separate definition-only sections, and keeps live session plans plus semantic activity as distinct sources. The correction is committed at `dae3ed0`, live on 8766 with the accepted Focus/timeline/terminal composition intact, and ready for captain interaction.

## Stage Report: shaping (cycle 7)

- DONE: Bind every transcript-derived fact to its exact source session without relying on an optional branch record.
  Commit `f0806ecb9e20804dd54a32bae76f9349114fe401` adds `source_session` to normalized transcript facts, observer snapshots, final outputs, and persisted history. Structured child assignments additionally retain their exact child source, verified contributor label, canonical work item, and proven parent session. The live all-project union contains exact Codex, Pi, and Claude source identities; no session-scoped fact is unattributed.
- DONE: Make focused semantics a source boundary while retaining honest project truth.
  A focused response now keeps only that session's transcript facts, structurally proven children whose `parent_session` is the focus, and project-scoped facts. A bounded peer read imports only canonical gate/entity state when the focused transcript does not expose that workflow; it never imports the peer transcript. On live `spacedock-v1`, Codex focus contains 17 own/child session facts plus 49 gates, Pi contains 24 own facts plus 49 gates, and Claude contains 96 own facts plus 49 gates. Each has zero foreign transcript facts.
- DONE: Keep gate decisions project/task scoped and reject time-proximity inference.
  Gate facts retain exact `person:captain`, decision, stage, target stage, workflow, and work item, but no originating session because the entity record does not prove one. The live union has 49 canonical gates and 4 separate raw `approve` messages with zero relations between them. Decisions therefore stand on their own source identity rather than being folded by nearby timestamps.
- DONE: Default the project cockpit to the complete session scope and make every peer directly reachable.
  `All sessions` is the default route. Compact project-local navigation lists Codex, Pi, and Claude, including both idle sessions, with harness/session label, state, last meaningful result, selected state, and a copyable hash permalink. A focused permalink fetches that exact `harness:sid`; the all-project route fetches the deduplicated union.
- DONE: Render one global newest-first timeline with stable session and current-task lanes.
  The all-project registry creates one human-labelled FO lane per project session and one lane per relevant current task. Historical task lanes remain behind All unless selected by Decisions. Same-lane vertical continuity is preserved; no horizontal dispatch/return line returns to the default view.
- DONE: Make every visible row answer actor, action, object, and result.
  Rows expose exact `data-actor`, `data-action`, `data-object`, and `data-result` fields and render the same concise sentence. Canonical captain gates read like `You approved <task> · review → shaping`; dispatch/start/result rows distinguish FO and verified worker identity. The Decisions filter renders canonical gate rows only.
- DONE: Distinguish an unmatched task start from observed active work.
  A child assignment or historical start no longer sets `working`. Only a current exact-state fact or currently observed contributor does. The five live work births without return evidence remain unresolved and explicitly say `return not observed`; they do not appear as five active workers.
- DONE: Falsify the correction at source, model, route, DOM, asset, and live three-session seams.
  The 145-test focused set covering project context, semantic history, next cockpit/page/project/chrome, and shared project rendering passes. Ruff, Ruff format, embedded JS/CSS/DOM lint, byte oracles, and `git diff --check` pass. The next composition is 342,130 bytes at SHA-256 `92ce5c6d97844a84492bfe9fa23c1405970bd046d2c1a9a622c0ff7f2a33f05e`.
- DONE: Swap the verified candidate onto stable 8766 and restore exact read-only terminal authority.
  Candidate 8767 was verified first while PID 18029 kept the accepted page stable, then stopped after the swap. A detached renewal client was reaped and correctly became `stale-registration`; the terminal-only recovery restarted the same code and replaced it with a maintained renewal PTY. Stable 8766 now runs PID `91529` from `f0806ec` and serves the pinned next composition above. After four renewals across more than one lease interval, exact collected root session `codex:01a035ee-2a7b-76f0-873f-eaddc97860c3` remains registered to current tmux `$4/@4/%10` (`Cargento:1.1`, 174×42), stream connected, read-only, with keyboard input `not-exposed`.
- DONE: Preserve prototype scope.
  No code ref was pushed or integrated, no version field changed, and `.spacedock/dev` was not read or mutated. This is the round-zero implementation checkpoint; visual judgment and the first expert UX correction remain captain-owned round 1.

### Summary

The project cockpit now defaults to a three-session project union without leaking one session's transcript into another. Exact session, parent, contributor, task, and captain-decision identities survive normalization; canonical gates remain project truth; unmatched starts remain unresolved. The live 8766 page exposes direct idle-peer navigation, stable FO/task lanes, concise actor-to-result rows, a canonical Decisions filter, and the accepted Focus plus exact read-only terminal, ready for the first captain UX review.

## Stage Report: shaping (cycle 8)

- DONE: Make the default All view show currently observed workers from every exact project session without weakening focus boundaries.
  Commit `3968a78ef906b9ac3e0af324481d2f946073c4dd` aggregates delegation lanes across the three project sessions only when no focus is selected; focused routes continue to read one exact `harness:sid`. Every rendered contributor retains its parent session. The live `spacedock-v1` union renders currently observed Copernicus on the canonical task lane with `data-parent-session="codex:01a03f80-2b74-7ef2-b1d3-307ecc44e444"`; completed Banach correctly left the current working set instead of being preserved from an older measurement.
- DONE: Put the project and session outcome before implementation identity.
  The session switcher now sits immediately below the project header and before PLAN / GOING ON / DONE / WORKSTREAM. Each session link leads with its current title or last result, followed by a compact `<harness> · <state>` cue; opaque session IDs remain only in exact link/data identity. All, Claude, Codex, and Pi remain directly reachable by copyable hash permalink.
- DONE: Add compact exact project attention and captain-decision status.
  The header status says `Needs you: none observed` only when the exact project ask/session set is zero. It shows the two newest unique `person:captain` gate decisions, de-duplicates only exact work/decision/stage/target tuples, excludes `agent:first-officer`, and puts older unique decisions behind one disclosure. No proximity rule folds raw `approve` transcript text into a gate.
- DONE: Reconcile decision slugs and successor opaque dispatch IDs through source-backed entity identity.
  The bounded gate parser now retains the entity frontmatter ID prefix, human title, and the actual source stage. The live newest decision is `ideation → implementation` for opaque entity `yv3w8rhxrj`; it and the successor dispatch resolve to one work item, while `Dispatch checklists must not delegate status advancement out of worker scope` remains the presentation label. The previous false `gate → implementation` result and duplicate slug/opaque lanes cannot pass the focused model test.
- DONE: Falsify round 1 at source, semantic model, composed DOM, and live three-session seams.
  Ruff and Ruff format pass on the touched Python/tests; the embedded JS/CSS/DOM linter passes. Fifty cockpit/project-context tests pass, and the combined next cockpit, project context, shared project renderer, and frontend byte-contract set passes 111/111. A DOM execution over the exact 8767 payload proves header < switcher < Plan, four session choices, outcome-first Pi text, exact zero attention, the newest captain transition, and the current Copernicus task/parent binding. The composed page is 443,454 bytes at SHA-256 `3289e8e1d1c6c5a7b64a2ed8fbcde424442e8ae2d4f87bc397876dedeef2bb7b`.
- DONE: Swap only the verified candidate onto stable 8766 and preserve terminal authority.
  Candidate 8767 remained separate until the 111 tests and exact-payload DOM falsifier passed, then was stopped after the controlled swap. Stable 8766 runs PID `51962` from `3968a78` and serves the pinned page above. Exact collected root session `codex:01a035ee-2a7b-76f0-873f-eaddc97860c3` is registered to tmux `$4/@4/%10` at 174×42, stream connected, `read-only-control-stream`, with keyboard input `not-exposed`; the maintained client renewed fifteen times and the API remained registered after another full lease interval.
- DONE: Keep observation limits and prototype scope explicit.
  Both the accepted and corrected servers report the same bounded discovery error for `spacedock-v1`: installed Spacedock advertises `docs/dev`, while this prototype's project-definition parser accepts only immediate `.spacedock/<workflow>` children. Round 1 does not hide or reclassify that unchanged limitation and does not broaden workflow-path trust. The in-app browser client could not initialize because its bundled runtime requested a restricted Node module, so the exact-payload DOM harness is the worker's interaction proof and fresh visual judgment remains captain-owned. No code ref was pushed or integrated, no version field changed, and `.spacedock/dev` was not read or mutated.

### Summary

UX round 1 turns the project header into a compact recovery surface: outcome-first session navigation, exact attention state, and the latest unique captain decisions precede the existing project sections. All now exposes workers observed in any exact project session, while focus remains an exact-session source boundary. Gate stage, opaque entity identity, and human task title survive together, so the live decision and dispatch occupy one truthful lane. Checkpoint `3968a78` is live on 8766 with the exact read-only terminal restored; work stops here for the fresh information-architecture review.

## Stage Report: shaping (cycle 9)

- DONE: The page explicitly distinguishes project-wide overview/status from session-filtered evidence, and session selection states exactly which surfaces change.
  Commit `d042adc0e94761e5be14c879c9117bb370d6af00` adds compact `PROJECT OVERVIEW` and `SESSION EVIDENCE` ownership markers plus the single sentence `Session selection filters Timeline and Terminal; project overview remains project-wide.` The DOM falsifier requires both labels and that exact boundary statement; removing or moving either scope request fails it.
- DONE: A focused session retains canonical project gate decisions for work items evidenced in that session, so approval → dispatch/progress consequence remains traceable without importing peer transcript facts.
  Focus now admits a project gate only when its canonical work item occurs in the selected transcript, an exact child assignment, or an exact `(workflow, slug)` current-plan attachment. Live All contains 50 gates across 20 items and Codex/Pi/Claude facts; live Pi focus contains 8 gates across only 4 evidenced/plan items and only Pi transcript facts. The source test inserts an unrelated peer gate and fails if it survives.
- DONE: Project and focused views use one canonical human task label map; session navigation leads with concise harness/state identity, prompt text is secondary, and the timeline filter says `All events`.
  A focus waits for all-project context, then maps labels by exact canonical work-item ID only. Exact gate entity aliases also bind artifact-only starts without fuzzy text or timestamp matching. The live Pi lane is `Embed the stage-report protocol in the dispatch artifact`, never `t4rqqmmrqh`; navigation leads with `Codex · working`, `Pi · idle`, and `Claude · idle`, and the control text is `All events`.
- DONE: Keep Project status stable across session selection without expanding session evidence.
  Project status always reads the all-session context while Timeline reads the focused context. The exact live DOM renders byte-identical status across Pi and Codex focus, retains `Needs you: none observed` plus the newest unique captain decisions, and issues separate all-project and focused requests; substituting focused semantic data for status fails the DOM test.
- DONE: Exercise and serve the round-2 checkpoint without widening prototype authority.
  Strict mypy passes over 116 source files; Ruff, Ruff format, embedded frontend lint, and byte oracles pass. The 153-test next suite and 112-test project-context/semantic/shared-page suite pass. Candidate 8767 was stopped after the controlled swap; no code ref was pushed or integrated, no version field changed, and `.spacedock/dev` was not read or mutated.
- DONE: Preserve the exact live terminal and report the served checkpoint.
  Stable 8766 runs PID `57200` from `d042adc`, serving 443,870 bytes at SHA-256 `80a57347ff1e4d747880634deababb1b55a77ffb60e85fa2540520981cdf3782`. Exact collected root session `codex:01a035ee-2a7b-76f0-873f-eaddc97860c3` remains registered at tmux `$4/@4/%10`, 174×42, stream connected, read-only, keyboard input `not-exposed`, after 18 renewals beyond a full lease interval.

### Summary

IA round 2 makes the project/session boundary visible and enforces it in the source model: overview, status, plan, activity, Focus, and delegation remain project-wide, while only Timeline and Terminal follow session selection. Canonical gate identity now scopes focused evidence and supplies one human label map across views. Checkpoint `d042adc` is live on 8766 and work stops here for the fresh AI/data-semantics review.

## Stage Report: shaping (cycle 10)

- DONE: Persisted history replays only facts explicitly promoted as human operator intent; injected collaboration/interruption envelopes remain evidence and never render as `You directed`.
  Commit `b4faf97b9b29f84bdd6bb73da30c66e946f6e846` stores `intent_promoted` on every user-message fact, persists both decisions, and replays only `true`; the restart/DOM falsifier fails if a rejected `do it` row or measured `Message Type: MESSAGE` collaboration envelope becomes an intent or `You` action. Live 8766 exposes 23 rejected and 91 promoted facts with zero injected-envelope intents.
- DONE: Focused gate eligibility includes exact current and persisted session/child task evidence plus workflow-bound aliases, retaining only those tasks' project gates without cross-workflow slug collapse.
  Focus eligibility is built before project-gate filtering from current transcript/backfill events, restart-safe facts belonging to the selected root or verified children, and structured child assignments. The falsifier keeps current, child-only, and persisted-only gates while removing a peer gate and the same slug from another workflow; changing either exact workflow or entity identity fails it.
- DONE: Gate application state survives event → fact → persistence → renderer; pending, superseded, or unapplied approvals read as recorded decisions without a completed stage-transition arrow.
  `application_state`, `target_stage`, decision, and `by` now survive parser, semantic fact, persisted history, and API. DOM tests require arrows only for `consumed`/`applied`; `pending`/`unspent` say pending application, `superseded` says superseded, and a missing application says unknown.
- DONE: Serve and exercise the AI/data-semantics round-3 checkpoint without widening prototype authority.
  Stable `http://127.0.0.1:8766/?next=true#n=project:spacedock-research%2Fspacedock-v1` runs PID `981` from `b4faf97`, serving 347,728 bytes at SHA-256 `de9ac2026b08085a689331398a64ff4625966ce7afc74ac0bbc515435ef8526b`. The 156-test focused suite, six boundary tests, Ruff, format, strict mypy over 116 files, embedded lint, plugin validation, version parity, live API, focus isolation, and exact-payload DOM harness are green; browser control could not initialize in this runtime, so no browser-only claim is made.
- DONE: Preserve the exact live hierarchy and read-only terminal while stopping for the next review.
  Exact collected root session `codex:01a035ee-2a7b-76f0-873f-eaddc97860c3` is registered at tmux `$4/@4/%10`, 174×42, stream connected, `read-only-control-stream`, keyboard input `not-exposed`. Candidate 8767 and its renewal client were stopped after the controlled swap; no code ref was pushed or integrated, no version field changed, and `.spacedock/dev` was not read or mutated.

### Summary

AI/data-semantics round 3 makes operator intent and gate consequence explicit data decisions instead of renderer inference. Restart-safe focus now follows exact task provenance without importing peer or cross-workflow gates, and approval arrows appear only after exact application. Checkpoint `b4faf97` is live on 8766 and work stops here for the COO/operations review requested by the captain.

## Stage Report: shaping (cycle 11)

- DONE: Focused views derive from the project semantic graph filtered by exact source session and bound tasks, so selecting the active owner never erases its own persisted/relevant evidence.
  Commit `363eb7792c89c87e4aa85b5550c8936fae97eccc` builds the bounded all-project graph before applying an exact focus filter. The filter retains facts from the selected `harness:sid`, verified children of that exact parent, tasks bound by those facts or current structured assignments, and project gates bound to those tasks. The source falsifier retains owner, child, task, and gate while rejecting peer transcript facts and peer gates. On live 8766, Codex All has 47 facts and Codex focus has 48 facts from only the exact root and verified child; Pi focus has 269 Pi-only facts and Claude focus has 5 exact-session facts.
- DONE: A compact recovery strip above Plan reports Outcome, Attention, and Decisions from existing evidence, with explicit unknown/absent states and attention ordered by intervention cost.
  Outcome reads browser-local Focus first, then a goal returned by project workflow discovery, then exactly `Outcome not recorded`; prompt and last-instruction text are never substitutes. Attention orders gate/ask, source or discovery failure, pending/unknown decision application, unreturned/retried assignment, then stale/idle owner. It shows one primary condition and puts every remaining measured condition behind one count disclosure. Decisions lead with pending and unknown counts before superseded and combined consumed/applied counts.
- DONE: `No gate or ask observed` is not used as a broader all-clear; source failures, pending/unknown decisions, unreturned or retried assignments, and stale/idle ownership remain visible attention states.
  The project-status zero line now names only the measured gate/ask channel. Recovery Attention independently evaluates the broader ordered set; workflow discovery `state:error` and `state:unavailable` are visible source attention, `return not observed` is retained without claiming the worker remains active, and idle ownership is never labeled a blocker. The DOM falsifier requires attention to remain non-empty across the exact live Codex, Pi, and Claude focus payloads even while the gate/ask zero line is present.
- DONE: Exercise the operations checkpoint at source, API, composed DOM, and static boundaries.
  The focused project-context, semantic-history, shared renderer, next-cockpit, next-project, next-page, and byte-contract suite passes 159/159. Ruff, Ruff format, strict mypy over 116 source files, embedded JS/CSS/DOM lint, plugin validation, version parity, and `git diff --check` pass. Exact live All/Codex/Pi/Claude API and DOM runs prove non-empty focus, exact source isolation, recovery-strip order before Plan, broader attention visibility, and Terminal only on the registered Codex session.
- DONE: Serve the verified checkpoint on stable 8766 and preserve prototype authority.
  Candidate 8767 remained isolated until the source, API, DOM, and static checks passed, then was stopped after the controlled swap. Stable 8766 runs PID `48707` from `363eb77`, serving 354,040 bytes at SHA-256 `e3a0325f46183986f8d03e048a3e25286a8374f71f4b43cc2b35999b35c087e3`. Exact collected root session `codex:01a035ee-2a7b-76f0-873f-eaddc97860c3` is registered at tmux `$4/@4/%10`, 225×56 at the final check, stream connected, `read-only-control-stream`, and keyboard input `not-exposed`. No code ref was pushed or integrated, no version field changed, and `.spacedock/dev` was not read or mutated.

### Summary

COO/operations round 4 turns the project header into a terse recovery checkpoint and makes focused history a provenance filter over the project graph instead of an independent reconstruction. Outcome, intervention-cost attention, and captain decision application counts now precede Plan without weakening exact session, child, task, gate, or terminal authority. Checkpoint `363eb77` is live on 8766 and work stops here for the first-officer command review requested by the captain.

## Stage Report: shaping (cycle 12)

- DONE: The existing recovery strip exposes one ordered command-attention list with explicit `CAPTAIN` or `FO` ownership, including exact unresolved authorization/questions observed outside AskRegistry.
  Commit `2133126d121d81c8fa8bbfef5ec711802dbaf3ed` recognizes an authorization only when one exact final result contains both an explicit authorization-required statement and a direct push/PR interrogative. Live DOM leads with `CAPTAIN · authorize push + PR for The completion-guard error names the failing sub-check`, retains `assistant final_answer followed by terminal turn state · exact`, then assigns workflow discovery, decision application, return reconciliation, and idle/stale ownership to `FO`. A later exact authorization or pushed/created-PR result retires the item; a general recommendation cannot create it.
- DONE: An exact terminal/session result binds to a task return only through unique workflow/task alias evidence; otherwise it remains an unattributed session result, and one task cannot simultaneously read returned and `return not observed`.
  The binding requires one complete workflow work ID with an exact same-session assignment, an exact stored task title, and a unique stored workflow entity beginning with the result's explicit Markdown alias. The live `9xn` result binds to `workflow:633bbd4f7a6a4a1b05b1:9xnaq83nry`; its one trail head is `returned`, its latest event is the exact final-answer fact, and it no longer contributes to unreturned counts. Tests leave missing proof as `session:codex:*`, leave two exact candidates ambiguous, and fail if a returned task also remains prepared/requested.
- DONE: Gate/ask and Going On empty copy is conditional on the broader command-attention list, so the page never presents an all-clear while a captain or FO action is evidenced.
  `No gate or ask observed` remains a narrow measured-channel statement. When command attention is nonempty, an empty Going On section says `No session currently running. Command attention remains above.` and suppresses `Nothing active or waiting on you in this project`; the live focused payload renders the narrow zero line beside nonempty CAPTAIN/FO attention.
- DONE: Exercise and serve the final first-officer command checkpoint without advancing or integrating.
  The focused semantic-history, project-context, shared renderer, next-cockpit, next-activity, next-project, next-page, and byte-contract suite passes 173/173; Ruff, Ruff format, strict mypy over 116 files, embedded JS/CSS/DOM lint, plugin validation, version parity, and diff checks pass. Candidate 8767 was stopped after the controlled swap. Stable 8766 runs PID `12364` from `2133126`, serving 355,712 bytes at SHA-256 `088087f7e1fb7c938df058a48c65f754fc29f19fb14e46b022416486b40a84cf`. Exact root terminal remains registered at tmux `$4/@4/%10`, 225×56, stream connected, read-only, and keyboard input `not-exposed`; no code ref was pushed or integrated, no version field changed, `.spacedock/dev` was not read or mutated, and workflow status remains shaping.

### Summary

The final first-officer command round turns recovery Attention into one evidence-backed command queue with explicit ownership. Exact alias/title/session proof reconciles the live `9xn` result with its workflow task, while ambiguous results stay unattributed and direct authorization remains captain-owned until exact resolution. Checkpoint `2133126` is live on 8766 and work stops here for the captain's final report without advancing or integrating.

## Stage Report: shaping (cycle 13)

- DONE: All, Active, and Decisions keep the event text in one stable reading column; changing filters does not horizontally reflow it.
  Commit `179a80d2d8331849172d0e1e8264ef70142de182` separates filter membership from timeline geometry: the mode-specific registry decides which rows remain, while every row and the lane legend render against the full canonical lane registry. The exact live `spacedock-v1` payload produces the same `--lane-count:2` text origin in Active, All, and Decisions while retaining four independent decision rows.
- DONE: Decision rows show only the decision, human task label, and application disposition; stage transitions and result/evidence prose are disclosed on expansion.
  The primary live scan lines now read `Approved Embed the stage report protocol in the dispatch artifact · pending application`, `superseded`, or `applied`. They do not contain the author, stage, arrow, source, or evidence. The existing row disclosure owns `Captain`, `validation → done`, application disposition, inclusion rationale, timestamp, and exact `Spacedock entity gate frontmatter` provenance; canonical actor/action/object/result data attributes remain intact for consumers.
- DONE: An exact live-payload regression test proves the compact decision wording and stable filter geometry, and the focused frontend tests pass.
  The regression uses exact live work item `workflow:633bbd4f7a6a4a1b05b1:t4rqqmmrqh`, gate fact `fact:e42c0b40b80c3555`, human task label, pending application state, and exact source. The focused project renderer, next cockpit, next page, project context, and byte-contract suite passes 144/144. Ruff, Ruff format, strict mypy over 116 files, embedded frontend lint, plugin validation, version parity, and `git diff --check` pass.
- DONE: Serve only the verified correction and preserve prototype authority.
  Candidate 8767 stayed isolated until the focused suite, static checks, and exact-payload DOM falsifier passed, then stopped after the controlled swap. Stable 8766 runs PID `77949` from `179a80d`, serving 356,894 bytes at SHA-256 `7d6248481941e1bc766e6cb06500f4662ed29a2f4da94e793b283af4e51d733c`. Exact root session `codex:01a035ee-2a7b-76f0-873f-eaddc97860c3` remains registered at tmux `$4/@4/%10`, 225×56, stream connected, `read-only-control-stream`, with keyboard input `not-exposed`. No code ref was pushed or integrated, no version field changed, `.spacedock/dev` was not read or mutated, and workflow status remains shaping.

### Summary

Shaping cycle 13 makes decision rows scannable without weakening their evidence and fixes filter-induced horizontal reflow at the registry boundary. The exact live decision set keeps one reading column across Active, All, and Decisions, while each row preserves its own expandable mechanics and provenance. Checkpoint `179a80d` is live on 8766; work stops here without advancing or integrating.

## Stage Report: shaping (cycle 14)

- DONE: The project/cockpit task remains the page subject while four real tabs—Now, Course, Decisions, Console—separate distinct operator questions without duplicating the same dense content.
  Commit `3b912140de9f2242f857bb0778ea7b6043b0ceaa` keeps `Project cockpit · Shaping` above one keyboard-accessible, permalink-preserving tab panel; executed route assertions fail if Now, Course, Decisions, or Console leaks another tab's owned dense regions.
- DONE: Course renders task-centric semantic episodes from exact session/workflow evidence: user direction, observed work, review-caused course changes, corrections, and results; contributor names and lifecycle evidence stay behind disclosure.
  The exact live-payload DOM exercise requires `EXACT INPUT`, `EXACT WORK`, and five source-backed `DERIVED COURSE CHANGE` findings under the task subject; it also requires the contributor name to follow a collapsed Evidence disclosure and fails if `Future` appears.
- DONE: The live current Cargento session distinguishes the completed timeline-row correction from the still-open page-organization shaping, shows no invented Future, and preserves truthful current delegation and decision application state.
  The exact payload renders completed checkpoint `179a80d` separately from current `Project cockpit · Shaping`; task-first active delegation and canonical decision metadata remain source-backed while Decisions truthfully reports no explicit captain decision when none is collected.
- DONE: Record the captain feedback, resulting criterion, and accepted interaction that authorized this composition.
  Exact captain directions said the page was too busy and the contributor name was not the subject; the approved scope assigned one operator question per tab, and the final recorded interaction `ok, let's try this.` accepted that direction before implementation.
- DONE: Resolve the recovered Console falsifier at its actual boundary without changing correct composition.
  The failure was an immediate sample before the asynchronous origin lookup settled; the new DOM test proves pending → `Open terminal` → explicit `read-only` output, with Now, Course, and Decisions absent throughout.
- DONE: Exercise the candidate at renderer, source-boundary, static, and live-server seams.
  Nineteen cockpit tests, 163 next-UI tests, 222 project-context/semantic/shared-renderer/page tests, and a 59-test focused composition set pass; Ruff, format, strict mypy over 116 files, embedded lint, plugin validation, version parity, and diff checks pass.
- DONE: Serve the verified checkpoint with the preserved exact read-only terminal and prototype authority.
  Stable `http://127.0.0.1:8766/?next=true#n=project:spacedock-research%2Fcargento` runs PID `91705`, serving 374,651 bytes at SHA-256 `bed3dbd3eed846a9b77de8b6c8d429c5859b87cd1bb4b2183e33474bda7e42a5`; candidate 8767 is stopped.
  Exact root `codex:01a035ee-2a7b-76f0-873f-eaddc97860c3` remains registered at tmux `$4/@4/%10`, stream connected, `read-only-control-stream`, keyboard input `not-exposed`, after six renewals across more than one lease interval.
- DONE: Preserve the authorized prototype-only boundary.
  The code commit is local to `spacedock-ensign/project-cockpit`; no code ref was pushed or integrated, no version field changed, and `.spacedock/dev` was neither read nor mutated.

### Summary

Cycle 14 reshapes the project mirror around four operator questions while keeping the task—not a contributor—the stable subject. Course now separates exact direction and work from source-backed derived course change, Now distinguishes the live shaping task from completed checkpoint `179a80d`, Decisions keeps explicit application semantics, and Console retains exact read-only output. The committed Explore-only checkpoint is live on 8766 with the root terminal preserved and is ready for the first-officer gate.

## Stage Report: shaping (cycle 15)

- DONE: The session chooser is a left, tree-like scope filter rooted at the project—not a second tab strip—and preserves exact project/session permalinks and active-state cues.
  Commit `ce7be1ea1be063b8fcc2fc08520cf58c22550d2c` renders one native-link `Project scope` navigation: normalized project root plus indented exact-session children with live state; executed tests fail if `All sessions`, session tab roles, horizontal-card styling, selection, or scope+tab round-trip regress.
- DONE: Human-authored Focus and Outcome edit and persist independently for the normalized project scope and each exact session scope, without cross-project/session leakage or overwriting observer-derived context.
  Versioned v2 keys combine canonical project identity, optional exact `harness:sid`, and field; input autosaves bounded 500-character values, reports saved/storage-unavailable state, treats corrupt values as empty, and renders empty session memos without project inheritance.
- DONE: The four operator-question tabs remain a separate axis, the exact live Cargento payload is usable at wide and narrow layouts, and focused renderer/static suites pass before the stable server swaps.
  The live project/root-session DOM exercise edits both project memos and both session memos, switches scopes, clears renderer drafts, reloads from storage, proves isolation, and round-trips exact Decisions scope while Course remains a separate local tab.
- DONE: Preserve human versus derived ownership in Now.
  `HUMAN · OUTCOME` and `HUMAN · FOCUS` sit in a captain-memo surface scoped by the selected tree node; a separate `DERIVED` line names semantic task/stage evidence and never reads or writes memo text.
- DONE: Reflow scope navigation without returning to horizontal pills.
  Wide CSS fixes a `180–230px` left scope column beside content; the executed narrow-layout contract requires a one-column stack at 760px and forbids horizontal overflow on the wide shell.
- DONE: Record the captain feedback and accepted decision criterion.
  The captain-authorized cycle-15 correction distinguished scope from operator question, made the project root the all-session action, and assigned human notes to the selected exact scope; the implementation follows that accepted criterion without adding another content surface.
- DONE: Exercise, serve, and preserve prototype authority.
  Twenty cockpit tests and the full 165-test next-UI suite pass with Ruff, format, strict mypy over 116 files, embedded lint, plugin validation, version parity, and diff checks; candidate 8767 stayed isolated until these and the exact-payload exercise passed.
  Stable `http://127.0.0.1:8766/?next=true#n=project:spacedock-research%2Fcargento` runs PID `44838`, serving 376,636 bytes at SHA-256 `ad612400443cbb30ed1ca27a243984fb38e5e93f5a705877aeb9e1e1be7d9fd8`; candidate 8767 is stopped.
  Exact root `codex:01a035ee-2a7b-76f0-873f-eaddc97860c3` remains registered at tmux `$4/@4/%10`, stream connected, `read-only-control-stream`, keyboard input `not-exposed`, after six renewals across more than one lease interval.
- DONE: Preserve the authorized prototype-only boundary.
  The code commit is local to `spacedock-ensign/project-cockpit`; no code ref was pushed or integrated, no version field changed, and `.spacedock/dev` was neither read nor mutated.

### Summary

Cycle 15 separates the cockpit's two navigation axes: a project-rooted scope tree chooses whose evidence and notes are in view, while Now, Course, Decisions, and Console remain content tabs. Outcome and Focus are now explicit human memos with exact-scope browser persistence, storage failure boundaries, and no inheritance or semantic-history contamination. The committed Explore-only checkpoint is live on 8766 with the root terminal preserved and is ready for the first-officer gate.

## Stage Report: shaping (cycle 16)

- DONE: Project-wide and session-specific content use one consistent, non-color-only scope grammar: explicit label, distinct marker shape, and structural position/connector.
  Commit `e5ef8f557d328d0b7fa610a8513c292e15048bd2` renders flush-left solid-rule square `PROJECT`, indented branch-connector round `SESSION`, and quiet `SCOPE UNKNOWN` cues; selection remains an independent inset state, and the layout test fails if marker shape, connector, or 760px stack regresses.
- DONE: The cue follows exact scope provenance across the scope tree, selected-scope human memos, Course episodes, Decisions, and Console without relabeling derived or unknown records as exact.
  Renderer tests classify exact `source_session` as session, proven sessionless workflow/task/gate contracts as project, and everything else as unknown; mixed-source derivation stays at one exact session only when all cited facts agree, while `DERIVED COURSE CHANGE` remains a separate epistemic label.
- DONE: Exact mixed-scope live-payload and narrow-layout falsifiers pass with no duplicate legend/panel, preserved tab/filter permalinks, and the stable server swaps only after focused/static checks.
  The fresh 16-session/30-fact project and exact root-session payloads render project tree/memo/root-Console cues beside truthfully session-scoped Course/root-Console evidence, retain an empty Decisions state because no live gate fact exists, reload isolated project/session memos, and round-trip the exact Decisions permalink; no legend or horizontal cockpit scroller appears.
- DONE: Preserve project decision scope under session focus and use the narrowest truthful Course scope.
  Executed mixed-provenance tests interleave project, session, and unknown Course rows; a project gate decision stays `PROJECT` while viewing a session, an explicit session gate becomes `SESSION`, and a session-sourced derived review change stays both `SESSION` and `DERIVED COURSE CHANGE`.
- DONE: Keep the task/page subject primary while annotating scoped Now evidence and human ownership.
  `Project cockpit · Shaping` remains above the four tabs; project workflow state, unknown browser-derived focus, selected-scope Outcome/Focus, completed results, and exact active delegation now reuse the same grammar without IDs, models, reasoning settings, contributor names, or a legend as the cue.
- DONE: Record the captain feedback, resulting criterion, and accepted interaction.
  The captain-authorized cycle-16 correction made non-color scope legibility the acceptance criterion—square/flush project versus round/branched session everywhere scope is material—and this served checkpoint is the direct implementation of that accepted direction without another panel or metadata strip.
- DONE: Exercise, serve, and preserve the exact read-only interaction origin.
  Twenty-four cockpit tests, all 169 next-UI tests, 50 shared project-renderer tests, classic/next byte oracles, Ruff, format, strict mypy over 116 files, embedded lint, plugin validation, version parity, and diff checks pass; isolated 8767 was stopped only after the controlled swap.
  Stable `http://127.0.0.1:8766/?next=true#n=project:spacedock-research%2Fcargento` runs PID `57468`, serving 381,667 bytes at SHA-256 `b7708594c701768d1110746b2dfa890153390b6223a17cd6ec9b9faa908f3d3b`.
  Exact root `codex:01a035ee-2a7b-76f0-873f-eaddc97860c3` is registered at tmux `$4/@4/%10`, stream connected, `read-only-control-stream`, keyboard input `not-exposed`; durable renewal client window `@15` passed nine renewals across more than one lease after the stale-window/process-bound renewal failure was isolated and corrected.
- DONE: Preserve the authorized prototype-only boundary.
  The code commit remains local to `spacedock-ensign/project-cockpit`; no code ref was pushed or integrated, no version field changed, and `.spacedock/dev` was neither read nor mutated.

### Summary

Cycle 16 makes scope legible through one structural grammar rather than repeated explanatory UI: project items are square and flush to a solid spine, session items are round and branched, and uncertain provenance stays explicitly unknown. Scope now follows evidence rather than screen selection across the tree, human memos, Course, Decisions, Console, and scoped Now evidence, while epistemic labels and the task subject remain independent. Checkpoint `e5ef8f5` is live on 8766 with the exact root terminal durably renewed and is ready for the first-officer gate.

## Stage Report: shaping (cycle 17)

- DONE: Now becomes a calm command briefing with only human Outcome/Focus, one current task, captain-owned attention, and active work; empty and secondary surfaces do not occupy primary space.
  Commit `f673d045ddcb4a0c31c35e26fb0f276b1bb4a6ca` renders exactly four primary regions; empty memos are compact `Not set` rows, only the selected field opens, captain attention excludes FO work, and unassigned children cannot impersonate active assignments.
- DONE: Decisions, history/results, plan detail, FO/system diagnostics, steering, guardrails, metrics, and raw interaction mechanics remain available only in their owning tab or disclosure, with no duplicate dense blocks in Now.
  Renderer ownership tests fail if decision counts leave Decisions, completed work leaves Course, Console loses raw session state/Going On/metrics/controls/terminal, or the closed plan/system disclosures reopen into primary Now.
- DONE: The exact screenshot/live-payload falsifier proves a substantial visible-text and primary-region reduction, compact edit-on-demand memos, truthful captain attention, preserved scope semantics/permalinks, and green focused/static checks before swap.
  The screenshot-shaped fixture falls from 197 to 33 visible Now words with four regions; the exact 8767 payload rendered 26 words, one task/stage, `Nothing needs you`, truthful active root work, no textarea, no unavailable assignment, and none of the six removed dense surfaces.
- DONE: Preserve edit, reload, scope isolation, and responsive structure while subtracting the old dashboard.
  Executed tests click Outcome/Focus independently, autosave and reload exact project/session keys, preserve scope+tab fragments and square/round cues, and falsify a wide 2:5 briefing that does not collapse to one column at 760px.
- DONE: Record the captain feedback, resulting criterion, and accepted interaction.
  The captain identified layered old-dashboard ownership as the failure; the resulting criterion was subtraction to task, captain need, active work, and human memos, and the accepted interaction is compact read/edit/done with Course, Decisions, Console, and plan disclosure retaining detail.
- DONE: Exercise, serve, and preserve the exact read-only interaction origin.
  All 173 Next tests, 228 shared page/project/context/snapshot tests, Ruff, format, mypy over 116 files, embedded lint, plugin validation, and diff checks pass; isolated 8767 was stopped after the swap.
  Stable `http://127.0.0.1:8766/?next=true#n=project:spacedock-research%2Fcargento` runs PID `63133`, serving 386,228 bytes at SHA-256 `68c05f321b1e8af92f30c8f358f03f5cc82b6fcaae5c0eac95c3f01f705de6c6`.
  Exact root `codex:01a035ee-2a7b-76f0-873f-eaddc97860c3` is registered at tmux `$4/@4/%10`, stream connected, `read-only-control-stream`, keyboard input `not-exposed`; renewal client `@16/%65` reread the new server generation after the old lease correctly disconnected.
- FAILED: The pre-existing whole-repository discovery suite is not green outside this frontend scope.
  Under load it ran 1,920 tests with three failures and five errors; isolated Contracts/Droid retained three baseline expectation failures, `test_spacedock` retained its surrogate-import error, and the documented HTTP/quota contention modules timed out, while every changed renderer/static group passed independently.
- DONE: Preserve the authorized prototype-only boundary.
  The code commit remains local to `spacedock-ensign/project-cockpit`; no code ref was pushed or integrated, no version field changed, and `.spacedock/dev` was neither read nor mutated.

### Summary

Cycle 17 removes the layered dashboard from Now and gives each secondary mechanism one owner, leaving a four-region command briefing whose exact live payload is under one seventh of the failing screenshot fixture's text. Human memos remain exact-scope and edit-on-demand, captain attention is truthful, active work rejects unavailable assignments, and all retained detail is reachable through Course, Decisions, Console, or disclosure. Checkpoint `f673d04` is live on 8766 with the exact root terminal renewed read-only; the candidate is stopped and the unrelated baseline suite failures are recorded rather than hidden.

## Stage Report: shaping (cycle 18)

- DONE: Missing semantic task identity is now explicitly unobserved instead of being replaced with an invented current task.
  Commit `02e37c8f0f3a7096dededc81b1b52fe709b58f05` requires an exact matching work-item ID, label, and trail-head stage before rendering `CURRENT TASK`; otherwise Now renders `WORKFLOW TASK` / `Not observed`, omits the task identity attribute, and never emits `Project work`, `State unavailable`, or an empty `data-work-item`.
- DONE: Observed session activity remains independent of workflow-task identity.
  An exact working session without an exact task binding renders `Work is active` with its measured `running 1 subagent · Codex` detail; `Current task is active` is reserved for a non-empty matching session work-item binding, and an unassigned child is neither promoted nor named.
- DONE: The scope tree removes duplicated state text while retaining one useful exact activity detail and correct plurality.
  The live root appears once as `working` with `running 1 subagent` beneath it, and the project root says `1 session`; empty or state-duplicating subtitles are omitted rather than replaced with another fallback label.
- DONE: The exact Round-1 live-shape falsifier preserves the cycle-17 subtraction and phone-width tab ownership.
  A working untitled Codex root, one unassigned child, and empty semantic `work_items` / `trail_heads` render four primary Now regions and 27 visible words, with no invented task/current-task wording, empty task identity, unavailable assignment, or contributor promoted as subject. A 420px contract fixes the four content tabs to equal min-width columns without overflow or pill styling.
- DONE: Focused renderer and static gates pass before the stable swap.
  All 175 Next tests and 228 shared page/project/context/snapshot tests pass; Ruff, format, strict mypy over 116 files, embedded JS/CSS lint, plugin validation, byte oracles, and diff checks pass. The initial validator invocation used a system Python without PyYAML; the repository virtual environment completed the validator successfully.
- DONE: The isolated candidate and served checkpoint match the committed bytes, with the exact read-only origin restored after the controlled swap.
  Candidate 8767 served 387,068 bytes at SHA-256 `499c360b15c9af3d9671e0997b9705231489bf2d5e6c0f00b13e4ce471c631d2` and proved the empty semantic payload plus exact working-state DOM before it was stopped.
  Stable `http://127.0.0.1:8766/?next=true#n=project:spacedock-research%2Fcargento` runs PID `18543` with the same bytes and digest. Exact root `codex:01a035ee-2a7b-76f0-873f-eaddc97860c3` is registered at tmux `$4/@4/%10`, stream connected, `read-only-control-stream`, keyboard input `not-exposed`; post-start renewal client `@18/%70` replaced a waiting client whose pre-stop registration deadline expired during shutdown.
- DONE: Preserve the authorized prototype-only boundary.
  The code commit remains local to `spacedock-ensign/project-cockpit`; no code ref was pushed or integrated, no version field changed, and `.spacedock/dev` was neither read nor mutated.

### Summary

Cycle 18 corrects the Round-1 truthfulness failure without adding another surface: unknown workflow task identity is visibly unobserved, while exact working-session activity remains visible as a separate fact. The four-region, low-text Now briefing, scope grammar, content-tab ownership, exact-scope memos, and read-only root console remain intact. Checkpoint `02e37c8` is live on 8766 with the exact root terminal renewed read-only; candidate 8767 is stopped and the correction is ready for first-officer review.

## Stage Report: shaping (cycle 19)

- DONE: Selected-session views explicitly distinguish project task/project-wide briefing facts from the viewing-session filter, including a compact narrow scope switcher rather than the full tree above content.
  Commit `1b78d7bb562c16231e0f6734194a00a01838a7e2` adds one PROJECT cue to the known/unobserved workflow-task subject, Needs you, and Active work; selected views add `Viewing session · Codex · working`, while the 760px contract hides the wide tree and exposes a selected-scope `Change scope` disclosure containing exact project/session links.
- DONE: Course defaults to source-backed course changes; exact directions that did not change course are preserved in one collapsed disclosure rather than becoming equal primary episodes.
  The failing 16-direction/zero-change regression now has zero primary episodes and one chronological `Other directions (16)` disclosure with source evidence; stage changes, decisions, completed checkpoint results, paired adaptations, and review findings remain primary, and a paired-direction test fails on either duplication or loss.
- DONE: Closed human memos visibly remain browser-local, and stale exact-session permalinks render an explicit outside-window state instead of silently falling back to project scope.
  Closed Outcome/Focus always says `This browser only`; removing the selected session from the payload preserves `#n=project:cargento:pi%3Api-idle:course`, renders `Session filter is outside this payload window` plus a tab-preserving project-root link, and emits no project memo or Course panel.
- DONE: Preserve the four-region subtraction, task truthfulness, scope grammar, exact memo isolation, and four content-tab ownership.
  All 179 Next tests and 228 shared page/project/context/snapshot tests pass; Ruff, format, strict mypy over 116 files, embedded JS/CSS lint, plugin validation, byte oracles, and diff checks pass, including a 54-test cockpit/page group that fails if the new IA surfaces regress.
- DONE: Exercise the exact live payload across project/session × Now/Course/Decisions/Console before swapping the stable server.
  All eight states rendered the requested panel with PROJECT task ownership and no stale fallback; live Now retained four regions at 33 project / 34 session visible words, exact memo owners, and persistent browser-only copy, while both Course views rendered zero primary episodes and a collapsed `Other directions (17)` for the current exact payload.
- DONE: Record the captain feedback, resulting criterion, and accepted interaction.
  The Round-2 authorized correction identified missing shared-scope ownership, direction-heavy Course, mobile tree dominance, hidden persistence limits, and silent stale-route fallback; the accepted criterion was explicit project/session IA without promoting the session to task subject or adding another primary Now region, and this served checkpoint implements that dispatched interaction.
- DONE: Serve the isolated checkpoint and preserve the exact read-only interaction origin.
  Candidate 8767 served 392,214 bytes at SHA-256 `5f7b190a6b3a95c1ade16368af3da56b60f647b33846520212601a388b301284`, passed the exact matrix, and is stopped. Stable `http://127.0.0.1:8766/?next=true#n=project:spacedock-research%2Fcargento` runs PID `93831` with the same bytes and digest.
  Exact root `codex:01a035ee-2a7b-76f0-873f-eaddc97860c3` is registered at tmux `$4/@4/%10`, stream connected, `read-only-control-stream`, keyboard input `not-exposed`, through renewal client `@19/%73` created only after the new one-use registration file existed.
- DONE: Preserve the authorized prototype-only boundary.
  The code commit remains local to `spacedock-ensign/project-cockpit`; no code ref was pushed or integrated, no version field changed, and `.spacedock/dev` was neither read nor mutated.

### Summary

Cycle 19 makes scope and ownership explicit without undoing the compact Now briefing: project-wide facts name their project scope, a selected session remains a filter, and mobile users get a compact scope disclosure. Course now separates source-backed changes from retrievable exact directions, while browser-local memos and stale session permalinks state their limits honestly. Checkpoint `1b78d7b` is live on 8766 with the exact root console renewed read-only and is ready for the next review round.

## Stage Report: shaping (cycle 20)

- DONE: Course admission now requires an independently meaningful, temporally ordered, exactly task-bound change; structural direction/result pairing is annotation rather than proof that course changed.
  Commit `c510e618a21a2af521ee30e682c202beddff2f8e` removes the current-task renderer fallback, requires the fact and any annotating direction to share a known non-empty work-item binding, rejects inverted time, and admits only an exact stage, decision, completed checkpoint result, or sourced substantive review finding. An unrelated unbound result renders no primary episode, cross-task or inverted pairing leaves the direction under `Other directions`, and a legitimate same-task stage/result after the direction remains one deduplicated Course change.
- DONE: Review completion requires substantive structured review evidence; generic lifecycle success is narrow telemetry.
  Empty, generic, and contributor-count-only successful review calls now render `Review call returned`; contributor counts cannot manufacture `review completed`. A non-empty `Review changed the course` findings block or structured findings field retains the implementation/technical review-completed title and its paired-result source, while generic lifecycle activity cannot independently enter Course.
- DONE: Project captain attention is independent of the three-session expensive observer cap and carries explicit bounded coverage.
  A cheap newest-first final-output scan covers up to 64 in-scope active sessions, feeds exact unresolved authorization facts through the existing semantic-history dedupe, and publishes `command_attention_coverage` with state, scanned, total, omitted, and source. The fourth active session's exact push/PR authorization now appears in captain attention; a 65th-session falsifier reports `Captain-attention coverage incomplete` and suppresses `Nothing needs you`, while complete zero-item coverage retains the calm empty state.
- DONE: Preserve direction retrieval, application truthfulness, source/session scope, memo isolation, four-region Now, and four-tab ownership.
  The six new causal/review/coverage falsifiers pass; all 94 project-context, semantic-history, and cockpit tests pass. The adjacent 261-test renderer run had no behavioral failure and only the expected changed-asset byte-oracle mismatch; the recomputed part/assembled oracle then passes. Ruff, format, strict mypy, embedded frontend lint, plugin validation, version parity, and diff checks pass.
- DONE: Record full-suite results without hiding unrelated baseline failures.
  The completed full discovery ran 1,931 tests in 181.956 seconds with 84.1% coverage and reported three failures, four errors, and one skip. Isolated reruns reproduce the untouched baseline failures in interaction-prototype HTTP/observation test doubles, stale Codex contract state, runtime import allowlist, Droid timestamp expectation, runtime-file inventory, and the Python 3.13 surrogate fixture import; none touches the Round-3 files or appears in the green focused surface.
- DONE: Exercise the exact live payload across project/session × Now/Course/Decisions/Console, then perform a controlled stable swap.
  All eight exact live routes render their requested panel with `Project cockpit` as subject, no Future or cross-tab content, and the compact four-region Now. The current exact evidence truthfully yields zero primary Course episodes while retaining exact directions under `Other directions`; the exact session Console resolves and opens the read-only terminal with no keyboard-input affordance.
  Candidate 8767 served 393,158 bytes at SHA-256 `086c2472101243dc5e12538b91b78a9ecb712144da4b1950e1bfded48eed195d` and is stopped. Stable `http://127.0.0.1:8766/?next=true#n=project:spacedock-research%2Fcargento` runs PID `64763` with the same bytes and digest. Exact root `codex:01a035ee-2a7b-76f0-873f-eaddc97860c3` remains registered at tmux `$4/@4/%10`, stream connected, `read-only-control-stream`, keyboard input `not-exposed`, through renewal client `@22/%79`.
- DONE: Preserve the authorized prototype-only boundary.
  The code commit remains local to `spacedock-ensign/project-cockpit`; no code ref was pushed or integrated, no version field changed, and `.spacedock/dev` was neither read nor mutated.

### Summary

Cycle 20 corrects the Round-3 AI/data-semantics faults at their admission boundaries. Directions remain retrievable evidence of input but cannot promote generic or unbound work into Course; review completion requires sourced substance; and captain attention covers active sessions independently of expensive observation or names incomplete coverage instead of claiming calm. Checkpoint `c510e61` is live on 8766 with the exact root console preserved read-only and is ready for the next review round.

## Stage Report: shaping (cycle 21)

- DONE: The Now view never states that captain attention is empty when project context is pending, failed, or incompletely scanned; successful empty attention shows its exact coverage.
  Commit `b7929f925299a113397cedc2492d9b9bcb451e45` treats null/loading, request failure, malformed coverage, and incomplete coverage as non-authoritative. Unavailable reads render `Captain attention unavailable`; incomplete reads retain a captain-owned coverage condition; both suppress `Nothing needs you`. A successful empty live scan renders `Nothing needs you` only beside `Coverage complete · 1 of 1 active session`.
- DONE: The existing recovery briefing is mounted above the tabs and gives a compact, copyable handoff from only observed data: browser-local Outcome/Focus, active sessions or assignments, latest exact direction/result, decision counts, and attention coverage.
  The same recovery region now precedes the four-tab list and contains five compact cells plus one `Copy briefing` action. The copied 525-character live handoff includes seeded browser-local Outcome/Focus, exact active root ID/state, zero exact assignments, latest exact direction, absent exact result, explicit empty decision state, and complete attention coverage. The real JS harness proves the copy caused no additional fetch; there is no server persistence path.
- DONE: Only a trail head explicitly marked current stage can be called CURRENT TASK; prepared or requested work remains a clearly owned follow-up.
  The staged-head fallback is removed. Focused falsifiers require prepared-only/requested heads to leave the workflow task unobserved and appear, when actionable, as FO follow-up rather than contradicting an idle project. The healthy live payload has no current-stage trail head and truthfully renders no `CURRENT TASK`.
- DONE: Preserve scope, tab, decision, Console, and stale-route ownership while mounting recovery once.
  Project/session scope cues and Now/Course/Decisions/Console remain unchanged owners; explicit empty Decisions and exact application states retain their focused tests. The real NextPageJsHarness exercised project and exact-session scope across all four tabs from the 8767 APIs: every requested panel rendered, recovery preceded the tabs, the complete coverage cue remained present, and the stale exact permalink did not fall back to project memos. The exact-session Console opened its read-only surface; the origin API resolved only `codex:01a035ee-2a7b-76f0-873f-eaddc97860c3` at `$4/@4/%10`, with keyboard input `not-exposed`. This is an API and executed-DOM proof; no screenshot or computed-layout claim is made.
- DONE: Exercise focused, static, full-suite, and served-checkpoint boundaries without hiding the baseline.
  The four new failure/incomplete/prepared/copy falsifiers pass 4/4 and the cockpit module passes 39/39. A 359-test focused renderer group had only the two expected pre-repin byte-oracle mismatches; after recomputing the changed assets, the isolated byte oracle passes. Ruff, format, strict mypy over 116 files, embedded lint, plugin validation, version parity, version-diff guard, and diff checks pass.
  The completed full discovery ran 1,935 tests in 202.563 seconds with 84.1% coverage and reported three failures, four errors, and one skip; the script group ran 184 tests in 1.870 seconds with its one runtime-inventory failure. These reproduce the untouched baseline classes: interaction-prototype CapturingServer doubles, Python 3.13 surrogate import, stale Codex state, runtime import allowlist, Droid timestamp, and runtime inventory. No cockpit or renderer regression appears.
- DONE: Serve the verified checkpoint locally and preserve exact terminal authority.
  Candidate 8767 served 400,726 bytes at SHA-256 `a70a5bdc523ea6bdd38fe1810427bf9d956ba1a5dd3cacc1c11dff9958683df8`, passed the exact live matrix, and was stopped; its exact client window `@23` was removed. Stable `http://127.0.0.1:8766/?next=true#n=project:spacedock-research%2Fcargento` runs PID `74472` with the same bytes and digest. Exact root `codex:01a035ee-2a7b-76f0-873f-eaddc97860c3` is registered at tmux `$4/@4/%10`, stream connected, `read-only-control-stream`, keyboard input `not-exposed`, through renewal client `@24/%83`.
- DONE: Preserve the authorized prototype-only boundary.
  The code commit remains local to `spacedock-ensign/project-cockpit`; no code ref was pushed or integrated, no version field changed, `.spacedock/dev` was neither read nor mutated, and workflow status remains shaping.

### Summary

Cycle 21 makes the existing recovery strip a truthful crash handoff without adding another page region. Captain attention cannot claim calm until its scan is authoritative, browser-local intent can be copied with exact observed state without a server write, and only an explicit current-stage trail head can own `CURRENT TASK`. Checkpoint `b7929f9` is live on 8766 with the exact root console renewed read-only; candidate 8767 is stopped and the correction is ready for first-officer review.

## Stage Report: shaping (cycle 22)

- DONE: The canonical briefing preserves the complete bounded delegation lifecycle without inventing task content.
  Commit `f834227aa5a0d083b0df8b20a05aa39954b0c150` keeps every active child even when its assignment is unavailable and separately names the newest returned child across the project. The exact live mirror says `Harvey · active · assignment unavailable` and `Hooke · returned · assignment unavailable · result unavailable`, binds both to source session `codex:01a035ee-2a7b-76f0-873f-eaddc97860c3`, and assigns both missing-evidence checks to FO. Non-text lifecycle values cannot become `[object Object]`; they remain explicitly unavailable.
- DONE: Captain attention is calibrated, ordered, and bounded by its actual evidence source.
  CAPTAIN rows sort before FO rows regardless of payload order. A complete zero-item scan says exactly `No captain action observed` and retains `Coverage complete · 1 of 1 active session · bounded active-session final-output scan`; incomplete or unavailable coverage retains its existing guard. A failed project-context refresh marks retained exact direction/result facts `stale cached`, so cached evidence never reads as current. The six adversarial falsifiers cover unavailable active assignment, unavailable latest-return result, coverage-source copy, failed-refresh staleness, CAPTAIN-first ordering, and duplicate-Now subtraction; all pass 6/6.
- DONE: The mounted recovery briefing is the single glanceable project mirror while its exact sources and browser-local controls remain reachable.
  Workflow task truth, active children, the bounded latest return, exact direction/result and source sessions, attention and coverage source, decision state, plus editable Outcome/Focus now live in one recovery region above the four tabs. The separately mounted workflow-task subject and duplicate Now memo, Needs, Active, and System cards are removed; FO detail is collapsed inside `System details`, and Now retains only the project-plan disclosure. The exact live payload truthfully renders workflow task `Not observed`, latest exact direction `restart 5-round review loop` from the root session, and latest exact result `Not observed`.
- DONE: Preserve project/session ownership, four-tab routing, stale-permalink behavior, exact decision semantics, and client-only copy.
  A real `NextPageJsHarness` run against the 8767 dashboard, project-context, exact-session context, and exact-origin responses exercised project and root-session scope across Now, Course, Decisions, and Console. Every route rendered one briefing before four tabs; project and session cues remained exact; Now contained none of the removed duplicate cards; and the copied handoff caused no additional fetch. The selected-session Console resolved `Cargento:1.1`, opened an output-only read-only surface, and exposed neither an input nor control endpoint. This is live API and executed-DOM evidence; no screenshot or computed-layout claim is made.
- DONE: Record the short operator handoff in the same authority order as the mounted briefing.
  Spoken handoff: Workflow task not observed. Harvey is active, with assignment unavailable. Hooke is the latest returned child, with assignment and result unavailable. The latest exact direction is `restart 5-round review loop` from the root session; no exact result is observed. No captain action is observed in the complete one-session bounded scan. FO should verify Harvey's assignment and Hooke's return evidence. Stable checkpoint `f834227` is live read-only on 8766.
- DONE: Exercise focused, static, full-suite, and byte-contract boundaries without hiding unrelated failures.
  The cockpit module passes 45/45, the focused cockpit/project/page/project-context/semantic group passes 186/186, and all Next tests pass 191/191. Ruff, Ruff format, strict mypy over 116 source files, embedded frontend lint, plugin validation, version parity, version-diff guard, byte oracles, and `git diff --check` pass. The completed full discovery ran 1,941 tests in 205.887 seconds with four failures, four errors, one skip, and 84.1% coverage; the script group ran 184 tests in 2.186 seconds with one failure. The unchanged baseline classes are the three `interaction_prototype` CapturingServer errors, Python 3.13 surrogate import, Codex timestamp precision, stale Codex state, runtime import allowlist, Droid timestamp, and runtime inventory. No cockpit or renderer regression appears.
- DONE: Serve the committed checkpoint and preserve the exact read-only interaction origin.
  Candidate 8767 served 408,409 bytes at SHA-256 `c40cd0b8926b53c117a26b2571c92a396a573e057b544270a5126d14e0d0c73f`, passed the exact live matrix, and was stopped; its exact tmux window `@25` was removed. Stable `http://127.0.0.1:8766/?next=true#n=project:spacedock-research%2Fcargento` runs PID `69500` with the same bytes and digest. Exact root `codex:01a035ee-2a7b-76f0-873f-eaddc97860c3` is registered at tmux `$4/@4/%10`, 284×70, connected and stream connected, `read-only-control-stream`, keyboard input `not-exposed`, with 12 renewals observed after the swap.
- DONE: Preserve the authorized prototype-only boundary and the recorded review direction.
  The final review direction was to preserve uncertainty, rank authority correctly, and subtract duplication; this checkpoint implements that correction without widening control or adding another primary surface. The code commit remains local to `spacedock-ensign/project-cockpit`; no code ref was pushed or integrated, no version field changed, `.spacedock/dev` was neither read nor mutated, and workflow status remains shaping.

### Summary

Cycle 22 turns the recovery briefing into the canonical project mirror: exact workflow-task truth, active and returned child lifecycle, source sessions, bounded attention coverage, browser-local intent, and decision state now share one authority-ordered region. Missing assignments and results remain visibly unavailable, cached facts become visibly stale after refresh failure, CAPTAIN always precedes FO, and duplicate Now cards are removed. Checkpoint `f834227` is live on 8766 with the exact root console renewed read-only; candidate 8767 is stopped and the final mirror correction is ready for first-officer review.

## Stage Report: shaping (cycle 23)

- DONE: Make the five-second briefing lead with the first actionable FO recovery when no captain action exists, while keeping captain emptiness and coverage secondary.
  Commits `943248c761c99bbaeb4fc80523036bc2176a76e3` and `5fc6b6b5c7bc0498b2121beed5e2d0b2686226c5` promote `FO · verify Harvey assignment — assignment missing` into ATTENTION when the captain list is empty. `Captain · none observed` and exact bounded coverage remain smaller secondary evidence. A separate payload-order falsifier proves that any CAPTAIN row still leads every FO row.
- DONE: Exclude acknowledgement-only text from latest actionable direction and distinguish semantic results from attributable session output.
  `intent_promoted:false` text such as `great.` cannot become direction. A semantic result remains `Latest exact result`; otherwise attributable `last_output` is labeled `Latest session result` with source and uncertainty, or the briefing says `Result evidence not captured`. The visible fallback is one bounded line, while Copy briefing preserves its full text.
- DONE: Compress empty memo and returned-child uncertainty without hiding ownership or evidence.
  Empty Outcome/Focus is one line, `Outcome/focus not set · Add context`; existing context retains separate edit controls. Active and returned rows lead with the child's name and lifecycle state, name missing assignment/result evidence next, and disclose exact IDs and sources only under Evidence and in copied briefing.
- DONE: Preserve the canonical mirror's task, scope, stale-evidence, and control boundaries.
  Workflow task remains `Not observed`; unavailable and stale evidence remain qualified; FO owns recovery checks; bounded captain coverage guards remain intact. Project/session scope, four tabs, read-only Console, client-only memo copy, and prepared-only course admission remain unchanged.
- DONE: Establish six targeted mutation-sensitive falsifiers for the correction.
  The tests fail if a non-promotable acknowledgement becomes direction, if attributable output lacks honest result labeling/source/uncertainty, if empty-captain FO is not primary, if CAPTAIN-first depends on payload order, if empty memos expand, or if returned-child IDs become primary copy. All six pass; the cockpit module passes 50/50 and the focused cockpit/project/page/context/semantic group passes 191/191.
- DONE: Complete static and full-suite verification without hiding contention or unrelated baselines.
  Ruff check, Ruff format over 156 files, strict mypy over 116 source files, embedded lint, plugin validation, version parity at 0.16.0, version-diff guard, byte oracles, and `git diff --check` pass. The completed full discovery ran 1,946 tests in 551.752 seconds with three failures, ten errors, one skip, and 84.1% coverage; its long runtime matches documented contention. All five loopback/timeout cases pass 5/5 in immediate isolation. Remaining failures are the untouched CapturingServer, Python 3.13 surrogate, stale Codex state, runtime allowlist, Droid timestamp, and runtime inventory baselines; no cockpit regression appears.
- DONE: Inspect the authoritative before image, apply the dispatched review criterion, and verify the corrected live hierarchy.
  `/tmp/cargento-mirror-round1-before.png` showed captain emptiness hiding the FO recovery, `great.` masquerading as direction, verbose empty memos, and ID-heavy child rows. The resulting criterion was subtractive: preserve uncertainty, rank action authority correctly, and disclose evidence without making it primary. A live Playwright probe across the exact payload confirmed the FO action, acknowledgement exclusion, attributable result fallback, collapsed IDs, all four tabs, and output-only Console.
- DONE: Capture and inspect the required 1440×1000 full-page after screenshot.
  `/tmp/cargento-mirror-round1-after.png` is 101,733 bytes at SHA-256 `b439c88570fe59ff4686a18c42463c3fff989285b65afb7cb926b7989845bbd5`. Inspection confirms the FO recovery is the primary ATTENTION line; captain emptiness/coverage is secondary; `great.` is absent; the latest session result is one sentence; the empty memo is one line; child IDs are collapsed; and the four-tab hierarchy fits without overflow.
- DONE: Serve the committed checkpoint and preserve the exact read-only interaction origin.
  Candidate 8767 served the verified checkpoint and is stopped. Stable `http://127.0.0.1:8766/?next=true#n=project:spacedock-research%2Fcargento` runs PID `66025`, serving 412,740 bytes at SHA-256 `3c73fb0457c534e53b271c79e797cac0e85edbbd8e5f864604996c494083dbd8`. Exact root `codex:01a035ee-2a7b-76f0-873f-eaddc97860c3` remains registered at tmux `$4/@4/%10`, connected and stream connected, `read-only-control-stream`, keyboard input `not-exposed`, with 26 renewals observed after the swap.
- DONE: Preserve the authorized prototype-only boundary.
  The code commits remain local to `spacedock-ensign/project-cockpit`; no code ref was pushed or integrated, no version or workflow status changed, no other report content was modified, and `.spacedock/dev` was neither read nor mutated.

### Completion checklist

- [x] The five-second briefing exposes the first FO-owned recovery action whenever no captain action is observed, while captain emptiness and scan coverage remain secondary and exact.
- [x] The latest-direction/result region excludes non-promotable acknowledgments, uses the latest actionable direction and attributable session result with honest labels, and never presents an acknowledgment such as great. as work direction.
- [x] Empty Outcome/Focus and returned-child uncertainty are compressed into minimal actionable lines; identifiers move to copied or expanded evidence, and the post-swap Playwright-Chrome screenshot proves the hierarchy visually.

### Summary

Cycle 23 makes the recovery hierarchy visually undeniable without adding another surface. When captain evidence is empty, the first FO recovery becomes the action; captain coverage remains supporting evidence. Acknowledgements cannot impersonate direction, attributable output stays explicitly uncertain, and empty memo/child evidence is compressed behind clear ownership. Checkpoint `5fc6b6b` is live on 8766 with the exact root console renewed read-only; candidate 8767 is stopped and the inspected Round-1 screenshot records the accepted correction.

## Stage Report: shaping (cycle 24)

- DONE: Inspect the authoritative Round-2 before image and apply the resulting IA criterion.
  `/tmp/cargento-mirror-round2-before.png` showed browser-local memo before task truth, missing evidence split from execution, repeated SESSION decoration, empty Decisions duplication, and `0 subagents` contradicting the selected project. The dispatched criterion was assignment, missing/owner, execution, evidence, optional note.
- DONE: Make authoritative assignment truth the first briefing cell without confusing it with browser-local context.
  Commit `e7c9913802e497f7e2f80fa5acf9d2dfe2121b7b` renders `ASSIGNMENT` first and states absent authority once as `Not observed · task, outcome, stage, done condition`; the browser memo moves to `OPTIONAL HUMAN NOTE · THIS BROWSER` at the end and remains editable.
- DONE: Consolidate CAPTAIN/FO-owned gaps into one missing/next-action surface.
  CAPTAIN requests precede FO actions; authoritative empty state says `Captain · no request observed` once. Active and returned gaps become owner-first `FO · verify NAME assignment[/result]` lines, while source/confidence stays in one Evidence disclosure and failed/incomplete coverage guards remain authoritative.
- DONE: Group observed execution once under each exact root without repeating session ornament.
  The live mirror renders `Codex · working`, then plain `Harvey · active` and `Ohm · returned` rows. Full session/work-item identifiers are absent from primary child copy and remain in expanded Evidence and Copy briefing.
- DONE: Subtract empty Decisions and preserve evidence, scope, and control ownership.
  The recovery strip has no Decisions primary cell; the Decisions tab remains canonical. Latest actionable direction and attributable result follow execution as `LATEST EVIDENCE`; semantic filtering, stale/unavailable labels, project/session routes, four tabs, and read-only Console remain intact.
- DONE: Make project identity and header counts compatible and explicitly scoped.
  The full project path appears once in the primary title, while the breadcrumb keeps the compact navigable leaf. The header says `All projects` and derives active children from the same working-session hierarchy as the briefing, omitting a zero child claim rather than contradicting project execution.
- DONE: Add falsifiers for reading order, consolidated missing evidence, optional-memo subordination, empty-Decisions subtraction, child grouping, and compatible scoped counts.
  All six pass and fail if any requested hierarchy or subtraction is reversed. The cockpit/chrome group passes 68/68, the focused renderer/context group passes 209/209, and the final changed-surface group passes 89/89 after recomputing byte oracles.
- DONE: Complete static and full verification without hiding unrelated baselines.
  Ruff, formatting over 156 files, strict mypy over 116 source files, embedded lint, plugin validation, version parity at 0.16.0, version-diff guard, byte oracles, and diff checks pass. Full discovery completed 1,952 tests in 182.269 seconds with three failures, four errors, one skip, and 84.1% coverage; the separate 184-test script group reproduced its one runtime-inventory failure. All reds are the unchanged CapturingServer, Python 3.13 surrogate, stale Codex state, import allowlist, Droid timestamp, and runtime-inventory baselines; no cockpit or contention failure appears.
- DONE: Exercise the exact candidate and preserve output-only Console behavior.
  Candidate 8767 served 413,130 bytes at SHA-256 `df91fbfb18c7fecad56520696081f038580e38a5a7f2dd1de1f20ebee185b73f`; standalone Playwright Chrome proved the five-part order, singular assignment absence, hidden IDs, accurate active-child count, all four tabs, and zero control requests from terminal keystrokes. Candidate 8767 is stopped.
- DONE: Capture and inspect the required post-swap 1440×1000 Chrome screenshot.
  `/tmp/cargento-mirror-round2-after.png` is 88,694 bytes at SHA-256 `cbbe322b1d8bce77bcc0c1d909e7bcf0242ed30caeea92bf861e0fb10a4def87`. Inspection confirms assignment first; CAPTAIN/FO missing evidence second; one root-grouped execution cell; latest evidence after execution; optional note last; compatible scoped count; compact breadcrumb; no repeated session glyph, empty Decisions cell, or overflow.
- DONE: Serve the committed checkpoint and preserve the exact read-only interaction origin.
  Stable `http://127.0.0.1:8766/?next=true#n=project:spacedock-research%2Fcargento` runs PID `13203` with the verified bytes and digest. Exact root `codex:01a035ee-2a7b-76f0-873f-eaddc97860c3` is registered at tmux `$4/@4/%10`, 166×40, connected and stream connected, `read-only-control-stream`, keyboard input `not-exposed`, with eight renewals observed after the swap.
- DONE: Preserve the authorized prototype-only boundary and recorded captain interaction.
  The Round-2 review supplied the authoritative before image and requested hierarchy; the live candidate and inspected after image exercise that accepted correction. The code commit remains local to `spacedock-ensign/project-cockpit`; no code ref was pushed or integrated, no version or workflow status changed, and `.spacedock/dev` was neither read nor mutated.

### Completion checklist

- DONE: The canonical visual order is assignment truth first, then consolidated missing evidence and its CAPTAIN/FO owner, then observed execution and latest evidence; optional browser-local context is subordinate and edit-on-demand.
  The live DOM order indices were strictly increasing across all five regions, and the after screenshot confirms the same visual order.
- DONE: Absent assignment is stated once as the missing task/outcome/stage/done-condition binding, and child assignment/result gaps are consolidated into the owned next-action surface without contradictory or repetitive absence vocabulary.
  The live falsifier counted one authoritative absence sentence and found no assignment-missing vocabulary in execution rows.
- DONE: Project/session identity and activity counts use explicit scope and one compatible child derivation; repeated session glyphs/labels and empty decision duplication are removed, with the post-swap Chrome screenshot proving the hierarchy visually.
  The live header reports `All projects · 1 running · 1 active child`; the inspected after image shows one full identity, plain child rows, and no empty Decisions cell.

### Summary

Cycle 24 inverts the recovery mirror around operator action: assignment truth, owned missing evidence, observed execution, latest evidence, then optional human context. It removes duplicate session and decision decoration, reconciles global counts with project execution, and preserves uncertainty, scope, semantic admission, and output-only Console behavior. Checkpoint `e7c9913` is live on 8766 with its exact origin renewed read-only; candidate 8767 is stopped and the Round-2 after image records the corrected hierarchy.

## Stage Report: shaping (cycle 25)

- DONE: Recover substantive root work deterministically when no exact workflow current-stage task exists.
  Commit `66c273d32938d77502ce0e82cabc4d5f5298fb3a` selects an exact promoted root direction only after excluding acknowledgement-only, URL-only, status-update, and browser/sandbox mechanism chatter. The exact live payload has no workflow trail head and now renders `Restart 5-round review loop` with `Exact operator direction · Workflow stage not linked`; the newer `this is not codex's builtin browser, but playwright-chrome` message is absent, and no task outcome, stage, or done condition is invented.
- DONE: Apply the three-state missing-information policy without generic verification copy.
  Readable exact workflow state, structured assignments, substantive root direction, and same-work/session output recover automatically without an action. Named readable lifecycle gaps produce one concrete FO operation such as `FO · inspect Schrodinger handoff`; a source-less active assignment says `Source unavailable · Harvey assignment`. CAPTAIN rows now require an exact projected request or AskRegistry question, while needs-input without an exact question becomes FO inspection. Complete empty attention says `No explicit captain request · scan 1/1`; failed and incomplete scan guards remain explicit and do not impersonate captain requests.
- DONE: Keep execution and result evidence time- and assignment-scoped.
  Returned children carry exact event age and become visibly stale at the existing ten-minute threshold. The exact live mirror qualifies `Schrodinger · returned · 25m ago · stale`; the lifecycle source remains under Evidence. Semantic results require the displayed work-item or source-session binding, and session-output fallback requires the displayed assignment's exact source session. The adversarial Pi fixture proves a newer unrelated peer result/output cannot appear next to current work.
- DONE: Subtract inert uncertainty and preserve the established ownership boundaries.
  Once assignment is recovered, the bundled task/outcome/stage/done-condition absence disappears. `Result evidence not captured` is omitted when no linked result exists; empty browser context is one `+ Add human context · this browser` control; and the project header omits `no estimate left · no confidence` when both are unknown. Assignment-first order, consolidated ownership, root-grouped execution, project/session scope, compatible counts, stale-context and decision-application truth, four tabs, client-only copy, and output-only Console remain intact.
- DONE: Add and pass the six adversarial semantic falsifiers plus focused and static verification.
  The falsifiers cover substantive work versus later mechanism clarification, deterministic recovery without FO, named FO handoff inspection, exact captain request, same-session result affinity versus unrelated Pi output, and ancient-return qualification. The cockpit module passes 61/61; the final cockpit/isolation/page group passes 179/179. The changed cockpit/isolation/page/project group passes 96/96. Ruff, Ruff format, strict mypy over 116 source files, embedded frontend lint, plugin validation, version parity at 0.16.0, changed byte oracles, and diff checks pass.
- DONE: Complete proportionate full verification and isolate every red instead of attributing it to contention.
  The completed discovery ran 1,958 tests in 292.773 seconds with seven failures, four errors, and one skip. Four changed-asset/header expectations were corrected and pass 2/2 in isolation. The remaining seven named baseline cases reproduce in isolation outside this correction: three interaction-prototype `CapturingServer` signature errors, stale Codex state, runtime import allowlist, Droid `started_at`, and the Python surrogate-path `test_spacedock` import. These are real pre-existing branch failures, not contention artifacts; no cockpit, renderer, or changed-oracle regression remains.
- DONE: Exercise the exact candidate, inspect the required Chrome frame, and perform a controlled stable swap.
  Candidate 8767 served 419,119 bytes at SHA-256 `23ef5f0b4e3850e2046fbf3925ffd0110e66e415962f4308648575553163f97b`. Standalone Playwright Chrome rendered a 76-word briefing with exact Assignment, scan 1/1, one named FO handoff action, source-less Harvey assignment, grouped execution, stale returned work, compact add-context control, and all four tabs. Exact-session Console opened `Cargento:1.1` read-only with no content-editable or control-input surface.
- DONE: Capture and inspect the post-swap 1440×1000 Chrome screenshot.
  `/tmp/cargento-mirror-round3-after.png` is 77,560 bytes at SHA-256 `9f7cb4647d0e2bee73b6797bc9cf2ae70d58b75f47f4c97f6462d78c11edde6c`. Compared with the authoritative before frame, inspection confirms exact recovered assignment replaced the absence bundle; mechanism chatter, inert result absence, expanded optional-note placeholder, and unknown estimate/confidence copy are gone; returned work is visibly stale; and the compact briefing fits without overflow.
- DONE: Serve the committed bytes and preserve the authorized Explore-only boundary.
  Stable `http://127.0.0.1:8766/?next=true#n=project:spacedock-research%2Fcargento` runs PID `2904` with the verified bytes and digest. Exact root `codex:01a035ee-2a7b-76f0-873f-eaddc97860c3` is registered at tmux `$4/@4/%10`, connected, stream connected, `read-only-control-stream`, keyboard input `not-exposed`, through the renewed stable client. Candidate 8767 is stopped. The code commit remains local to `spacedock-ensign/project-cockpit`; no code ref was pushed or integrated, no version or workflow status changed, and `.spacedock/dev` was neither read nor mutated.

### Completion checklist

- DONE: When no workflow task is linked, the Assignment cell recovers the best exact substantive root work directive without promoting mechanism chatter; stage/done-condition absence is disclosed only when it changes action.
  The exact live Assignment is `Restart 5-round review loop · Exact operator direction · Workflow stage not linked`; the later Playwright mechanism message and the bundled outcome/stage/done-condition absence are absent.
- DONE: Missing information follows a falsifiable three-state rule—recover automatically from readable exact sources, FO inspect a named stale/unreadable/ambiguous source, or ask CAPTAIN only for an explicit request/gate/needs-input or proven unresolved choice.
  Six adversarial tests cover all three states. The live payload recovers Assignment without an action, assigns the named Schrodinger handoff to FO, leaves source-less Harvey assignment explicitly unavailable, and reports no explicit captain request after the complete 1/1 scan.
- DONE: Execution and evidence remain time/scoped: returned work has bounded age, output fallback requires same-session or exact work affinity, unlinked output cannot imply a result, and visually inert unknowns are subtracted in the post-swap screenshot.
  The screenshot shows the stale 25-minute return and none of the unrelated-output, result-absence, expanded-note, or unknown estimate/confidence copy; the exact-affinity falsifier rejects newer Pi evidence.

### Summary

Cycle 25 corrects the Round-3 semantic hierarchy at its source boundaries. With no linked workflow task, the briefing recovers the substantive root assignment rather than mechanism chatter; missing data either recovers deterministically, names one FO inspection, or remains explicitly source-unavailable without escalating to CAPTAIN. Returned work is age-qualified, result fallback is affinity-bound, and inert uncertainty is removed. Checkpoint `66c273d` is live on 8766 with the exact root Console renewed read-only; candidate 8767 is stopped and the inspected Round-3 screenshot records the accepted correction.
