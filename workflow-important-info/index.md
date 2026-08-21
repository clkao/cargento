---
title: Per-workflow important-info definition — let each workflow declare what to display
status: ideation
source: captain dogfood feedback
id: et7hb2x9k6kts3cr56mnf2k8
gates:
    version: 1
    records:
        - id: gate:et7hb2x9k6kts3cr56mnf2k8:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:et7hb2x9k6kts3cr56mnf2k8-backlog-1
              briefing:
                id: briefing:et7hb2x9k6kts3cr56mnf2k8:backlog:attempt-1:revision-1
                digest: sha256:4a4910bcce1c6ac6dd8e6ff0beb5d19d8700f8e8c63b3ff5ca4de8e627109881
                request-digest: sha256:976b96ab0e0ce6d22320eba729b4bb9789f94481a2fd956c3735919f119e5d6a
                room-ref: ./review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:et7hb2x9k6kts3cr56mnf2k8:backlog:1
                briefing: briefing:et7hb2x9k6kts3cr56mnf2k8:backlog:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-21T07:28:23.955525472Z"
                decision: approve
                reason: 'FO autonomous approval (conn granted: ''you have the conn to push to the forked repo and open PR''; reinforced: ''when you have the conn, you should still do gate attempt and record your autonomous approval as resolution''). Backlog seed names a user-facing end value and a concrete dashboard surface; proof-needed well-scoped. Advancing to ideation.'
              application:
                target-stage: ideation
                state: consumed
---

Each project/workflow can define what important information is to be displayed
for its entities — not every workflow cares about the same fields. The dashboard
should read and render the workflow's declared important info, not hardcode a
fixed set.

## Problem

The session and project views today render a fixed set of fields (slug, stage,
goal, live status). But different workflows surface different things: a dev
workflow cares about the last gate decision and the PR number; a release
workflow cares about the version and the release tag; a research workflow cares
about the hypothesis and the evidence count. The dashboard can't know which
fields matter to which workflow — only the workflow's README can declare it.

## Included scope

- A `display:` section in the workflow README frontmatter (or a sibling file)
  that declares which entity fields are "important" for that workflow's
  dashboard rendering.
- The session/project views read this declaration and render the declared
  fields per entity, falling back to a default set when absent.
- A default declaration (the current fixed set) so workflows without it are
  unchanged.

## Excluded scope

- The specific fields any one workflow declares (that's each workflow's call).
- Changing the entity frontmatter schema (this reads what's already there).

## Proof needed to decide whether design should start

Whether the workflow README is the right place for this declaration (vs. a
separate display-config file), and whether the declared fields are reachable
from the entity frontmatter + gate records already read by the collector.
