---
title: Session view should carry the session card, then improve session-centric from there
status: ideation
source: captain dogfood — "we could at least have the card in the session view, and improve from there"
id: 0c3re8kepj1984gnaenr5a7f
gates:
    version: 1
    records:
        - id: gate:0c3re8kepj1984gnaenr5a7f:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:0c3re8kepj1984gnaenr5a7f-backlog-1
              briefing:
                id: briefing:0c3re8kepj1984gnaenr5a7f:backlog:attempt-1:revision-1
                digest: sha256:c522de102e2ec2a3091c4e6f5a30702cfda8d305959409fbff7df91b8fd192e1
                request-digest: sha256:6bf57e0d45d2f4b772759367d5d9e54b8089d6c8894a09775e61c273457ccc7a
                room-ref: ./review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:0c3re8kepj1984gnaenr5a7f:backlog:1
                briefing: briefing:0c3re8kepj1984gnaenr5a7f:backlog:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-21T14:15:24.53516178Z"
                decision: approve
                reason: 'conn granted. Captain: ''at least have the card in the session view, and improve from there.'''
              application:
                target-stage: ideation
                state: consumed
---

The session view (the third `session` display mode, reached via `#session=...`) renders the workflow's entity roster without the session card. The regular board view already has a rich per-session card — title, project, sid, model, provider, rate (tok/min), state, state_detail, elapsed/eta. The session view should at least show that card, then improve toward session-centric.

## The minimum first step

Render the session card at the top of the session view. The card content already exists on the session object and is already rendered in the regular board view — reuse it in `session.js`/the session-view mode. Concretely the card shows:
- Title (e.g. "Use $spacedock:first-officer for this whole Pi session.")
- `project · sid · via provider · model`
- rate (e.g. "433 TOK / MIN")
- state + state_detail (e.g. "NOW running bash")
- elapsed / eta / progress

That alone makes the session view "about the session" rather than a bare task list.

## Then improve toward session-centric

After the card, the workflow section should be reframed (the deeper work):
1. Keep the workflow name + role line ("SPACEDOCK DEV first officer").
2. The entity list should reflect what THIS session did/does, not the workflow's full roster. The dispatch records in the session transcript (which pi-live-worker-attribution already parses) are this session's work log — every `(slug, stage)` it dispatched is a thing it did. Use the FULL dispatch history (all batches, ordered by when the dispatch happened), not just the newest live batch, as the session's work log with last decision + when.
3. Drop the misleading "NOT TOUCHED" label — this session advanced all 11 entities; "not touched" means "no active worker right now," not "this session never touched it." Either label the non-live rows accurately ("other workflow entities") or omit them.
4. The live dispatched ensign(s) stay highlighted (current pi-live behavior).

## Included scope

- First: render the session card in the session view (reuse the existing board-view card rendering).
- Then: reframe the workflow section to be session-centric — show the session's dispatched entities (full history), accurate labels, live highlight.
- Dogfood against THIS session: the session view should open with the card (title/project/sid/model/rate/state) above the workflow strip, and the strip should reflect what this session did.

## Excluded scope

- The project view (multi-session) — owned by project-view-overview.
- Per-workflow important-info — owned by workflow-important-info.
- The boot-scan-window fix (this session finding its envelope) — owned separately; this task depends on it for the dogfood to show at all.

## Proof needed

Whether the session card rendering can be factored out of the board view and reused in the session view without duplication, and whether the full dispatch history (all batches, ordered) gives an accurate "what this session did, and when."
