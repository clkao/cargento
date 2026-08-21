---
title: Publish dispatch_history to the session view API
status: backlog
source: session-centric-view verification gap
id: m9p5hfmw1va6zyj4vhkew5jx
---

`session-centric-view` computes `dispatch_history` in the Pi collector (pi.py:357, aggregating all dispatch batches ordered by timestamp) but does not attach it to the published workflow dict — the API only carries `workflow`, `stages`, `entities`. The ordered work log ("what this session did, and when") is computed but never reaches the frontend.

## Problem
The session-centric-view's secondary user impact — an ordered dispatch history showing what the session did, not just the current roster — is not delivered because `dispatch_history` is built in the collector but not wired into the published `session_workflows` output. The frontend `session.js` has no field to render.

## Included scope
- Attach `dispatch_history` (list of `{slug, stage, at}` ordered by dispatch time) to the workflow dict in `session_workflows` so it reaches the API.
- Render it in the session view as the session's work log (ordered, with timestamps), distinct from the current entity roster.
- Dogfood against THIS session: the session view shows the ordered dispatch history (all 12+ dispatches this session made, with when).

## Proof needed
Whether `dispatch_history` should be a separate field on the workflow dict or folded into the entities list (e.g. a `dispatched_at` per entity), and how the frontend renders the ordered log.
