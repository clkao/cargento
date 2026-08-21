---
title: Pi live-worker attribution — feed live ensign names to session_workflows
status: ideation
source: captain directive — source of truth is the live ensigns
id: rj497exc44z5es90d7a2bg49
gates:
    version: 1
    records:
        - id: gate:rj497exc44z5es90d7a2bg49:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:rj497exc44z5es90d7a2bg49-backlog-1
              briefing:
                id: briefing:rj497exc44z5es90d7a2bg49:backlog:attempt-1:revision-1
                digest: sha256:9db6429b8f07c980562244070249df4d71499ce8505895ddc36a6db7d0f67bd7
                request-digest: sha256:87224cad04e08e0db3c2e9a9ef602df7ca2845e96a71b822abe1ca35eb1cc25e
                room-ref: ./review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:rj497exc44z5es90d7a2bg49:backlog:1
                briefing: briefing:rj497exc44z5es90d7a2bg49:backlog:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-21T08:42:27.761264687Z"
                decision: approve
                reason: 'conn granted: ''you have the conn to push to the forked repo and open PR''. Captain directive: ''source of truth should be we have 3 ensigns actively working.'' Root cause of this session showing workflows:[] despite 3 live ensigns — Pi collector hardcodes worker_names=[].'
              application:
                target-stage: ideation
                state: consumed
---

The Pi collector passes an empty `worker_names` list to `session_workflows`, so the session view's "live workers first" source is always empty for Pi FO sessions — even when ensigns are actively running. The source of truth for "what is this session doing right now" is the live ensigns; the dashboard should reflect that.

## Problem

In `collectors/pi.py`, `session_spacedock` calls:

```python
runtime_spacedock.session_workflows(config, state, boot, [], now, window_sec)
```

The fourth argument (`worker_names`) is hardcoded `[]`. `session_workflows` already has the mechanism to use it — `attribute_worker(name, slugs, stages)` maps a live worker name to a slug/stage and marks the entity `live: True`, and the "live workers first" source is the freshest of three. But the Pi collector never extracts live worker/ensign names from the transcript, so that source is always empty.

Result: a Pi FO session with 3 ensigns actively working shows `workflows: []` (or a strip with no `live` entities), because the collector hands `session_workflows` nothing to attribute. The entity-state directory (the middle source) also yields nothing for our detached `.spacedock/dev` workflow (the boot envelopes don't resolve its entity_dir), so the session view is blank for the session that most needs it — this one.

The transcript carries the dispatch records: 60 `subagent` mentions and `"agent":"worker"` entries in this session's transcript alone. The data is there; the collector doesn't parse it into worker_names.

## Included scope

- Extract live worker/ensign names from the Pi session transcript: parse the subagent dispatch tool_use records (the `agent` field, and the dispatch file path or task text that carries the slug/stage) to build the `worker_names` list (or a richer `(name, slug, stage)` structure `attribute_worker` can consume).
- Pass the extracted list to `session_workflows` instead of `[]`.
- The session view should then show the 3 live ensigns as `live: True` entities on the workflow strip, sourced from real transcript activity — the ground truth of what this session is doing.
- Reuse `attribute_worker`'s existing slug-attribution; if the dispatch record carries the slug/stage directly (from the dispatch file path), use it rather than guessing from the worker name.
- Dogfood against THIS session (01a02216): it should show the 3 active ensigns (z4/zp/et implementation) as live entities.

## Excluded scope

- The detached-workflow boot/entity_dir resolution (separate concern — the live-worker source should work even when the entity_dir is empty, because `attribute_worker` only needs the roster for slug boundaries, and the dispatch file path can supply the slug directly).
- Rich per-entity metadata (owned by `rich-session-metadata`).
- Cross-session project overview (owned by `project-view-overview`).

## Proof needed to decide whether design should start

Whether the Pi transcript's subagent dispatch tool_use records carry enough structured data (agent name, dispatch file path, or task text with the slug) to attribute a live worker to an entity slug + stage without the entity-state roster, and whether the existing `attribute_worker` can consume a richer `(name, slug, stage)` input or needs a small extension.
