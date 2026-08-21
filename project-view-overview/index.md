---
title: Project view — multi-session entity state overview across sessions
status: ideation
source: captain dogfood feedback
id: 5semdnyk5x3w5gh8vkjxfqxw
gates:
    version: 1
    records:
        - id: gate:5semdnyk5x3w5gh8vkjxfqxw:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:5semdnyk5x3w5gh8vkjxfqxw-backlog-1
              briefing:
                id: briefing:5semdnyk5x3w5gh8vkjxfqxw:backlog:attempt-1:revision-1
                digest: sha256:8648661b2b61037f98090c248689c5ebbd7ac16bf3d4262032b4914d7fc3c5a8
                request-digest: sha256:6342b6256f817feb0f7c335a522c0524157bc1a620d502b7a29d962adf063cb1
                room-ref: ./review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:5semdnyk5x3w5gh8vkjxfqxw:backlog:1
                briefing: briefing:5semdnyk5x3w5gh8vkjxfqxw:backlog:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-21T07:28:23.818279884Z"
                decision: approve
                reason: 'FO autonomous approval (conn granted: ''you have the conn to push to the forked repo and open PR''; reinforced: ''when you have the conn, you should still do gate attempt and record your autonomous approval as resolution''). Backlog seed names a user-facing end value and a concrete dashboard surface; proof-needed well-scoped. Advancing to ideation.'
              application:
                target-stage: ideation
                state: consumed
---

In a project with multiple sessions (e.g. cargento has this FO session plus two
dispatched ensign workers), the dashboard should show the overview entity state
across all the project's sessions — which session is driving which entity, and
the aggregate state of the workflow across the project's active sessions.

## Problem

The session view shows one session's dispatch tree. But a project's workflow is
driven by multiple sessions: a first officer and its dispatched ensigns. An
operator cannot see, for one project, the aggregate picture — which entities are
being worked by which session, what's blocked, what's dispatchable — across all
the project's sessions in one view.

## Included scope

- A project-level view (selectable when grouping by project) that shows, for
  one project's workflow, the entity state aggregated across all the project's
  active sessions: each entity with its current stage, which session is driving
  it, and the workflow's overall progress.
- Reuse `spacedock.workflows` data already published per session; aggregate by
  slug across the project's sessions.

## Excluded scope

- Per-session detail view (owned by `session-view-spacedock-visibility`).
- Per-workflow important-info definition (owned by a separate task).

## Proof needed to decide whether design should start

Whether entity slugs are unique across sessions in a project (so aggregation by
slug is well-defined), and whether the project view can be built from the
existing `/api/data` payload without a new endpoint.
