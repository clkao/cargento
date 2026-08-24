---
title: Project cockpit and remembered goal
status: backlog
source: commission seed
started:
completed:
verdict:
score: 0.95
worktree:
issue:
pr:
parent:
budget: three review cycles
integration-base: e2fdaffc10ac31da5e5d39361bb2e95e3ca4c1a7
integration-checkpoint:
development-task:
id: yehhw3jcrd6j7eb2zazad25s
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
