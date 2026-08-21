---
title: Boot envelope scan window too small for long-running Pi FO sessions
status: ideation
source: dogfood finding — this session lost its Spacedock strip
id: gr210bdejn62ssjq7t97dfd3
gates:
    version: 1
    records:
        - id: gate:gr210bdejn62ssjq7t97dfd3:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:gr210bdejn62ssjq7t97dfd3-backlog-1
              briefing:
                id: briefing:gr210bdejn62ssjq7t97dfd3:backlog:attempt-1:revision-1
                digest: sha256:5f8c85bb676f313db4349fb9466c2b9b6c2c64d5be74499faf1a5e8d9dc1444e
                request-digest: sha256:8eff20d181c0eca51b16488bb5eacc6b74d2e4bf0c0c0662c42fd6a16c266ee9
                room-ref: ./review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:gr210bdejn62ssjq7t97dfd3:backlog:1
                briefing: briefing:gr210bdejn62ssjq7t97dfd3:backlog:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-21T09:20:18.2112975Z"
                decision: approve
                reason: 'conn granted. Dogfood finding: 3MB session lost Spacedock strip (boot envelope outside 512KB scan window).'
              application:
                target-stage: ideation
                state: consumed
---

The Pi collector's `transcript_boot` reads only the last `spacedock_boot_scan_bytes` (512KB) of the session transcript to find the boot envelope. For a long-running first-officer session (3MB+ transcript after hours of work), the boot envelope written at the START of the session has scrolled out of the scan window, so `transcript_boot` returns `[]`, `session_spacedock` returns `None`, and the session shows `spacedock: null` — losing its Spacedock classification and workflow strip entirely.

## Problem

This session (01a02216, a Pi FO driving the dev workflow for hours) has a 3MB transcript. Its boot envelopes are at lines 15 and 36 (near the start). The boot scan reads only the last 512KB, which doesn't include them. Result: the session that most needs its workflow strip (the one actively driving 3+ ensigns) shows nothing.

This is the "long session" problem: the boot envelope at the start of the transcript scrolls out of the scan window as the session grows. The fix is NOT to scan the whole transcript (that would be expensive for every refresh), but to either:
- increase the scan window for Pi sessions (they have one boot envelope at the start, not repeated),
- or scan from the start for the boot envelope (reverse scan, like the transcript reader already does for other data),
- or cache the boot envelope when first found (it doesn't change mid-session).

## Included scope

- Make `transcript_boot` find the boot envelope in long Pi sessions (3MB+ transcripts where the envelope is at the start, outside the last-512KB scan window).
- The boot envelope is stable for a session's lifetime — once found, it doesn't change. A cache or a start-of-file scan is appropriate.
- Dogfood against THIS session (01a02216, 3MB transcript): it should show `role: first-officer` with its workflow strip.

## Excluded scope

- The live-worker attribution (owned by `pi-live-worker-attribution`).
- The read_workflow symlink containment (owned separately).

## Proof needed

Whether `transcript_boot` can cheaply find the boot envelope at the start of a 3MB+ transcript without scanning the whole file every refresh, and whether a reverse scan (start-of-file) or a cached boot is the right mechanism.
