---
title: Usage-limit disclosure is a blocking modal — should be a dismissable banner
status: ideation
source: captain seed
id: rj95tbw2vde46v8xjgcvgm9q
gates:
    version: 1
    records:
        - id: gate:rj95tbw2vde46v8xjgcvgm9q:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:rj95tbw2vde46v8xjgcvgm9q-backlog-1
              briefing:
                id: briefing:rj95tbw2vde46v8xjgcvgm9q:backlog:attempt-1:revision-1
                digest: sha256:61051bb5e93413c97c0a3e171b3b10f36505269fa9fcf2d2eb2da9f1bc2e0066
                request-digest: sha256:a5fbbfac59fb160ba00aeee38055876ac470c79d1c2934212298962823c5ae56
                room-ref: ./review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:rj95tbw2vde46v8xjgcvgm9q:backlog:1
                briefing: briefing:rj95tbw2vde46v8xjgcvgm9q:backlog:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-22T05:53:26.336853232Z"
                decision: approve
                reason: 'Conn: captain granted ''you have the conn to push to the forked repo and open PR; when you have the conn, you should still do gate attempt and record your autonomous approval as resolution'' (session 01a02216, reaffirmed ''just do some'' this session). Evidence: seed verified against live 4553 screenshot showing modal walling the product; ACs screenshot-falsifiable; presentation-only scope (usage.js + styles.css). Ideation owes banner placement + calm-palette design consistent with the 3-piece IA.'
              application:
                target-stage: ideation
                state: consumed
---
# Usage-limit disclosure is a blocking modal — should be a dismissable banner

## Problem
Cargento's usage/quota disclosure (`usageModal` in `usage.js`) renders as a
full-screen overlay (`u-overlay`) on first load, gating the entire dashboard
behind a "Show usage and rate limits?" modal with two buttons. It's an
intentional first-time consent (localStorage `cargento.usageModalSeen` gates it
to once per browser), but the blocking-overlay form means a captain opening
the dashboard fresh cannot see ANY of the product until they dismiss it. That's
a bad first impression: the thing the dashboard exists to show — sessions,
goals, activity — is hidden behind an OAuth/privacy consent wall.

Confirmed by a headless screenshot of the live integration server
(`http://127.0.0.1:4553/`): the modal overlays the session view, the timeline
and goal headline are invisible until "Keep usage on" / "Turn it off" is
clicked.

## Acceptance criteria
- **AC-1**: On first load (fresh browser, no localStorage flag), the dashboard
  renders fully and visibly — sessions, the session view, all the product
  surface — WITHOUT being obscured by a modal overlay.
- **AC-2**: The usage-limit disclosure (the privacy/consent text + "Keep
  usage on" / "Turn it off") still appears on first load, but as a
  NON-blocking inline banner (top or bottom of the page), not a full-screen
  overlay. The captain can see the product AND read the disclosure at once.
- **AC-3**: The existing `data-calm="umodal"` + `data-arg="on"/"off"` handlers
  keep working (they set the localStorage flag + enable/disable usage fetch).
  Clicking "Keep usage on" or "Turn it off" dismisses the banner for future
  loads.
- **AC-4**: The disclosure text is unchanged (the same OAuth-token, no
  transcript content, quota-numbers explanation). Only the PRESENTATION
  changes: overlay → banner.

## Scope notes
- This is a presentation-layer change in `web/usage.js` + `web/styles.css`
  (the `u-overlay` / `u-modal` CSS becomes a `u-banner` inline block).
- The localStorage gating (`USAGE_MODAL_KEY`, `usageModalSeen`) stays — the
  banner still shows once per browser, just non-blockingly.
- A user impact gate (not just suite-green): a fresh browser opens the
  dashboard and the session view is immediately visible alongside the usage
  banner, not hidden behind it. Verify with a screenshot or by clearing
  localStorage and reloading.

## Why it matters
The dashboard's job is to mirror the agent at a glance. A first-time visitor
who lands on a modal wall doesn't get that — they get a consent form. Moving
the disclosure to a banner lets the product earn its position on first
impression, same as every subsequent visit.
