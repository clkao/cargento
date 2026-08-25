---
title: Session interaction origin
status: breadboard
source: commission seed
started: 2026-08-25T03:33:48Z
completed:
verdict:
score: 0.85
worktree: .worktrees/spacedock-ensign-session-interaction-origin
issue:
pr:
parent:
budget: three review cycles
integration-base:
integration-checkpoint:
development-task:
id: a1wk3a7zaz8zdqv0d3r01wcm
gates:
    version: 1
    records:
        - id: gate:a1wk3a7zaz8zdqv0d3r01wcm:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:a1wk3a7zaz8zdqv0d3r01wcm-backlog-1
              briefing:
                id: briefing:a1wk3a7zaz8zdqv0d3r01wcm:backlog:attempt-1:revision-1
                digest: sha256:b8ad2a22b4f31d30d1b69dab5130d4c948d927fa6dfdb28793d78196da181872
                request-digest: sha256:41bbe156aa2e19d5cb5b6ab9271942720b5b12f4bb0ef4d8b1f8eac57c5d6541
                room-ref: ./review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:a1wk3a7zaz8zdqv0d3r01wcm:backlog:1
                briefing: briefing:a1wk3a7zaz8zdqv0d3r01wcm:backlog:attempt-1:revision-1
                by: person:captain
                at: "2026-08-25T03:33:24.288251Z"
                decision: approve
                reason: Captain approved the bounded interaction-origin probe using only disposable registered sessions; existing real sessions and private transcript content remain out of scope.
              application:
                target-stage: breadboard
                state: consumed
---

Discover a safe, explicit channel through which the Cargento UI can steer the intended active session and report delivery honestly.

## Question

How can an active session register its interaction origin so the operator can send it bounded input from Cargento without targeting the wrong terminal or pretending delivery succeeded?

## Boundaries and budget

Breadboard may compare a registered tmux pane with a registered long-poll mailbox. Steering must be opt-in, local, and explicit. It does not authorize arbitrary shell execution, inferred terminal targets, or production UI work. Use at most three review cycles.

## Candidate directions

Exercise literal tmux paste delivery as the cheapest end-to-end falsifier, then compare it with a transport-neutral registration and acknowledgement contract suitable for a long-poll client.

## Evidence

Cargento already has a bounded ask lane with one-slot outcomes and long polling, while the mirror prototype only displays mocked steering history. No current mechanism proves that UI input reaches a specific live session.

## Decision criterion

Shaping must derive the final comparison criterion. At minimum, a viable approach must deliver intact input to the registered target, refuse stale or unregistered targets, expose acknowledged, rejected, or unknown honestly, and require explicit operator and session participation.

## Direct captain communication

Ask the captain before touching a real session, using private transcript content, incurring model cost, or selecting a security boundary. A live delivery exercise requires explicit consent and must target a disposable registered session.

## Development handoff

No development task exists until review proves one channel end to end and the captain accepts its security and consent model.

## Acceptance criteria

**AC-1 — Registered input reaches exactly the intended disposable session intact and no unregistered target is addressable.**
Verified by: an end-to-end exercise with two candidate sessions in which only one registers; changing the requested target to the unregistered session must produce refusal and no delivered bytes.

**AC-2 — Delivery state is reported honestly.**
Verified by: exercises for acknowledged, explicitly rejected, stale, and transport-disconnected cases; removing the acknowledgement path must change the result to unknown rather than success.

**AC-3 — The browser cannot supply an arbitrary terminal or shell target.**
Verified by: an adversarial request containing an unregistered tmux locator and shell metacharacters; the registered-channel resolver must reject the locator or deliver the text literally without command interpolation.

### Feedback Cycles

## Stage Report: breadboard

- DONE: Compare registered tmux delivery with a transport-neutral registered mailbox contract, leaving small inspectable artifacts and naming the choices that still matter.
  Commit `cdb253b` adds the mechanism note, executable spike, stable result, comparison, recommendation, and eight open review choices.
- DONE: Exercise two disposable candidate sessions with only one registered: prove intact exact-target delivery and refusal with zero delivered bytes for the unregistered target.
  The runner starts one isolated tmux server with two candidates, registers one, proves exact text, and asserts zero bytes for the second.
- DONE: Exercise acknowledged, rejected, stale, disconnected, and adversarial shell-metacharacter cases while touching no existing real session or private transcript content.
  The runner fails on a wrong state, changed text, new bytes after refusal, a shell marker, or a result that differs from the committed JSON.

### Summary

The tmux spike proved server-owned resolution and literal delivery through a registered receiver. It also proved that tmux transport success cannot support an acknowledgement label without an application receipt. The breadboard recommends a registered long-poll mailbox, pending captain review of authentication, payload power, consent lifetime, queueing, and retry semantics.
