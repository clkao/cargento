---
title: Fix Spacedock entity-state freshness gate (mtime staleness blanks the workflow strip)
status: ideation
source: captain dogfood feedback
id: tzrvnebvdb10fddfr40szvtm
gates:
    version: 1
    records:
        - id: gate:tzrvnebvdb10fddfr40szvtm:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:tzrvnebvdb10fddfr40szvtm-backlog-1
              briefing:
                id: briefing:tzrvnebvdb10fddfr40szvtm:backlog:attempt-1:revision-1
                digest: sha256:dcc36568f0e286ebec8cd255fb4e498078cc37ae00d8e4e30277bd769226699a
                request-digest: sha256:58bd5b698c28c45a4c3f880b662a9c7b7934ec4911dce85aff57207fc42b62f9
                room-ref: ./review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:tzrvnebvdb10fddfr40szvtm:backlog:1
                briefing: briefing:tzrvnebvdb10fddfr40szvtm:backlog:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-21T07:28:23.355151244Z"
                decision: approve
                reason: 'FO autonomous approval (conn granted: ''you have the conn to push to the forked repo and open PR''; reinforced: ''when you have the conn, you should still do gate attempt and record your autonomous approval as resolution''). Backlog seed names a user-facing end value and a concrete dashboard surface; proof-needed well-scoped. Advancing to ideation.'
              application:
                target-stage: ideation
                state: consumed
---

A long-running first-officer session that has been driving a workflow for hours
shows `workflows: []` on the dashboard — no strip, no entities — even though it
is classified as a first officer and the entity state is committed and current.

## Problem

`spacedock.read_entities` gates every entity file by `is_fresh(config, now,
info.st_mtime, window_sec)` — the file's **mtime** must be within the freshness
window (default 1 hour). But Spacedock entity state is committed via git; a file's
mtime reflects the last checkout/write, not the last logical change. A session
that committed entity state 2 hours ago and has been doing PR review since has
stale mtime → `read_entities` returns `[]` → `workflows: []` → the strip blanks.

Measured: this session (a Pi FO driving the `dev` workflow for hours) shows
`spacedock: {"role": "first-officer", "workflows": []}` on the dashboard. The
entity dir exists, the boot envelope resolves, the entity files are committed
and current — but their mtime is hours old, so `read_entities` filters them out.

## Included scope

- Replace or supplement the mtime freshness gate in `read_entities` with a signal
  that reflects actual workflow activity: the git commit time of the entity file,
  or the entity file's frontmatter `started`/`completed` timestamps, or drop the
  freshness gate for Spacedock state entirely (the boot envelope's
  `entity_dir_present` already proves the workflow is live).
- Keep the "don't show retired workflows" intent — but gate on workflow
  activity (boot envelope recency, entity dir presence), not file mtime.

## Excluded scope

- Changing the session freshness window for non-Spacedock collectors.
- The session view's rendering of the empty state (owned by
  `session-view-spacedock-visibility`).

## Proof needed to decide whether design should start

Whether `read_entities` is the only mtime-gated path, and whether git commit time
(or frontmatter timestamps) is reachable read-only without a git dependency.
