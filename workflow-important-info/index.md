---
title: Per-workflow important-info definition — let each workflow declare what to display
status: backlog
source: captain dogfood feedback
id: et7hb2x9k6kts3cr56mnf2k8
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
