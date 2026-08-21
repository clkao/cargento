---
title: Session view with Spacedock visibility
status: ideation
source: captain seed
id: 6s6ft835wwg0q9hb8505rkz6
gates:
    version: 1
    records:
        - id: gate:6s6ft835wwg0q9hb8505rkz6:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:6s6ft835wwg0q9hb8505rkz6-backlog-1
              briefing:
                id: briefing:6s6ft835wwg0q9hb8505rkz6:backlog:attempt-1:revision-1
                digest: sha256:46a4904f685b2000c4a33adec4d49526c94a8907a88043939273cea15d585c95
                request-digest: sha256:0948043d557687115d613668a97634a54efa7a854af164a7befb03c8f210e65f
                room-ref: ./session-view-spacedock-visibility/review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:6s6ft835wwg0q9hb8505rkz6:backlog:1
                briefing: briefing:6s6ft835wwg0q9hb8505rkz6:backlog:attempt-1:revision-1
                by: person:captain
                at: "2026-08-21T02:50:24.961909245Z"
                decision: approve
                reason: captain directs the backlog seed to advance to ideation for design
              application:
                target-stage: ideation
                state: consumed
started: 2026-08-21T02:50:26Z
---

Cargento's dashboard has two overview modes — `regular` and `calm` — that summarize all sessions. There is no per-session view. The reference (`/private/tmp/image (1).png`) shows a "Task Map": a dispatch tree of work items connected by dependency edges with stage-colored nodes, plus panels for recent completions, active claims, available, and blocked. A session view should render that dispatch tree for one session and add a high-level goal — a sprint or stated objective — if the session carries one (stated in its workflow/roadmap context, or derived from the entities it is driving).

## Problem

An operator watching one active session cannot see, for that session alone, the dispatch tree of what it is working or the high-level goal it is pursuing. The overview modes aggregate all sessions and do not render per-session dependency trees. This task adds a session view without touching the existing `regular`/`calm` overviews or any other dashboard surface.

## Proposed approach

{Ideation: a new view mode selectable alongside `regular`/`calm`, keyed to one session id, rendering (a) a dispatch tree from the session's workflow entity state — reusing `cargento_runtime/spacedock.py` and `cargento_runtime/sessions.py` — and (b) a high-level goal line derived from the workflow's roadmap/sprint context when the session is a first officer driving a named sprint, or stated explicitly otherwise. The reference image's Task Map is the target shape.}

## Risk evidence

{Backlog: confirm the dashboard's view-mode switch (`web/mode.js`) can host a third mode additively, and that the entity-state data needed for a per-session dispatch tree is reachable from a single session id without a cross-session scan.}

## Expected surface and tolerance

Estimate: {ideation fills}
Semantics this may change: {ideation fills}

## Acceptance criteria

{Ideation: at least one AC measures the end value — selecting the session view for a known FO session renders its dispatch tree with correct entity nodes, edges, and stages — verified by a test or live render, and one AC measures the goal line against a baseline that can move the wrong way (a stated sprint goal is shown; a session with no goal shows none, not a fabricated one).}

## Test plan

{Ideation fills.}

### Feedback Cycles

## Out of scope

- Changing the `regular` or `calm` overviews — this task is additive only.
- A new cross-session data source: the dispatch tree reuses existing `spacedock.py`/`sessions.py` reads.
- LLM-summarized goal inference beyond stated/derived-from-workflow-context for this task.
