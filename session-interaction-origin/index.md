---
title: Session interaction origin
status: backlog
source: commission seed
started:
completed:
verdict:
score: 0.85
worktree:
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
