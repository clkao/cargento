---
title: Rich session metadata — entities touched, state, decisions, and progress
status: ideation
source: captain dogfood feedback
id: z4tjfzz9y4dz1vvaz588mc81
gates:
    version: 1
    records:
        - id: gate:z4tjfzz9y4dz1vvaz588mc81:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:z4tjfzz9y4dz1vvaz588mc81-backlog-1
              briefing:
                id: briefing:z4tjfzz9y4dz1vvaz588mc81:backlog:attempt-1:revision-1
                digest: sha256:ccc42b201dd9818ef37d42815ce44b7fa89e69fdc08cc57858eb11ed3842bc8e
                request-digest: sha256:890c71dca7bf7c2b8552257358643bc0729d51f3c3e816367634a987885790f6
                room-ref: ./review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:z4tjfzz9y4dz1vvaz588mc81:backlog:1
                briefing: briefing:z4tjfzz9y4dz1vvaz588mc81:backlog:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-21T07:28:23.481133823Z"
                decision: approve
                reason: 'FO autonomous approval (conn granted: ''you have the conn to push to the forked repo and open PR''; reinforced: ''when you have the conn, you should still do gate attempt and record your autonomous approval as resolution''). Backlog seed names a user-facing end value and a concrete dashboard surface; proof-needed well-scoped. Advancing to ideation.'
              application:
                target-stage: ideation
                state: consumed
---

The session view should show, for the session being viewed, the entities it
touched, their current state, the decisions made on them, and what progressed
and when — not just the dispatch tree spine.

## Problem

The current session view renders the dispatch tree (stage-colored entity nodes
along the workflow spine) and a goal line. An operator watching one session
cannot see what that session actually DID — which entities it advanced, what
decisions were made (approve/revise/hold), what stage each entity is at now, and
when it last progressed. The spine shows WHERE in the pipeline each entity sits,
not WHAT happened to it.

## Included scope

- Per-entity card in the session view: slug, current stage, the last gate
  decision (approve/revise/hold) and its reason, the last state-change timestamp,
  and a one-line "what progressed since when" (e.g. "advanced to validation 12m
  ago").
- Secondary section: other dispatchable entities NOT touched by this session
  (the rest of the workflow's backlog), dimmed or separated.
- Data source: the entity state files' frontmatter + the `### Feedback Cycles`
  section + gate records, read read-only.

## Excluded scope

- Cross-session project overview (owned by a separate task).
- Per-workflow important-info definition (owned by a separate task).

## Proof needed to decide whether design should start

Whether the entity frontmatter + gate records + feedback cycles carry enough
structured data to render "last decision + when" without parsing free-form stage
reports, and whether the session view can attribute entity changes to this
session vs. a peer.
