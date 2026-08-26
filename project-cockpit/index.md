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
