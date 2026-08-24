---
title: Boot envelope scan window too small for long-running Pi FO sessions
status: validation
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
started: 2026-08-21T09:55:52Z
worktree: .worktrees/spacedock-ensign-boot-scan-window-long-sessions
mod-block: merge:pr-merge
pr: spacedock-dev/cargento#127
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

## Correction: direction of the scan window

The entity body above says `transcript_boot` reads "the last 512KB" of the transcript. The code reads the FIRST `spacedock_boot_scan_bytes` (512KB) from offset 0 — a head scan, not a tail scan. The envelope is not "scrolling out" of a trailing window; it is sitting past the leading window because Pi transcript lines are large (system prompts, tool results, context — each JSONL line can be 30–40KB+). In the dogfood session (01a02216), the envelope is at line 15, but 15 large lines push it to ~588KB, past the 512KB head window. The effect is the same — the envelope is not found — but the mechanism is a too-small head scan, not a tail scan.

## Approach: fallback full-file scan when head scan misses

`transcript_boot` (`cargento_runtime/spacedock.py:357`) reads the first `spacedock_boot_scan_bytes` (512KB) and parses boot records from it. The result is cached on `(path, min(size, scan_bytes))` — for files larger than 512KB, the key is always `(path, 512000)`, so a growing file never triggers a rescan. When the head scan misses, `[]` is cached permanently.

The fix adds a fallback: when the head scan finds no envelope and the file is larger than `spacedock_boot_scan_bytes`, read the entire file and parse boot records from it. The result is cached so the fallback cost is paid once per session, not per refresh.

The cache key for the fallback result uses the actual file size `(path, size)`, not the capped `(path, min(size, scan_bytes))`, so a growing file invalidates the fallback cache and re-checks. The head scan runs first on every refresh (cheap, ~0.9ms); the full-file fallback only runs when the head scan misses. Since the boot envelope is stable (written once at session start, never rewritten), once the fallback finds it, the session is classified for its lifetime.

### Why a cached boot, not a larger fixed window

The boot envelope is stable for a session's lifetime — written once at `spacedock status --boot` and never rewritten (see `boot_records` docstring and S-5 in `docs/design-spacedock.md`). A cached full-file scan is the right mechanism because:

- The head scan (512KB) remains the fast path for the common case (Claude sessions, short Pi sessions).
- The fallback only triggers for long Pi sessions where the envelope is past 512KB — the minority case.
- The fallback cost is ~2.7ms for a 2MB file, ~10ms for an 8MB file (measured below), paid once per session thanks to caching.
- There is no fixed window size that covers all cases: a Pi session with very large initial messages can push the envelope past any reasonable fixed limit, and widening the window for all sessions makes every head scan more expensive for no benefit.

### Simplest rejected alternative: increase `spacedock_boot_scan_bytes`

Raise the constant from 512KB to, say, 2MB or 4MB. This cannot deliver the MVP value because there is no correct fixed value. A Pi session with a long system prompt, a large tool result, or a verbose initial exchange can push the boot envelope past any fixed window. The dogfood session's envelope is at ~588KB, but a session with a 100KB system prompt per line and 20 initial messages would push it past 2MB. Widening the window for all sessions (including Claude, where the envelope is in the first few lines) makes every session's head scan proportionally more expensive — the cost the design doc rejected as "quadratic in transcript size" — without solving the general case.

## Risk evidence (spike)

**Riskiest mechanism: can `transcript_boot` find the boot envelope at the start of a 3MB+ transcript cheaply?**

Spike: built a 2.1MB Pi transcript with 15 large (~40KB each) initial messages, the boot envelope at byte 602245 (588KB), and 40 trailing filler messages. Results:

- `transcript_boot` (current head scan, 512KB) returns `[]` — **bug confirmed**.
- `boot_records` on the full file returns 1 envelope — **fallback mechanism works**.
- `boot_records` on the first 2MB also returns 1 envelope.
- The current cache caches `[]` under `(path, 512000)` and returns it on the second call — **negative result is sticky**.

Cost of full-file `boot_records` scan (100 iterations, `time.perf_counter`):

- 2.1MB file: 2.67ms per scan.
- 8.2MB file: 10.03ms per scan.
- Head scan (512KB): 0.86ms per scan.

The fallback is ~3x the head scan for a 2MB file, still sub-millisecond-equivalent per refresh when amortised by the cache. Acceptable for a one-time cost per session.

## Expected surface and tolerance

Files touched:

- `cargento/skills/cargento/cargento_runtime/spacedock.py` — `transcript_boot` function (~15 lines of change: add fallback read after head scan miss, adjust cache key).
- `cargento/skills/cargento/tests/test_pi.py` — 2–3 new tests (~40–60 lines).

No frontend changes (the dashboard already renders the workflow strip for sessions with `spacedock` data). No config changes (no new constant — the existing `spacedock_boot_scan_bytes` remains the head-scan window). No changes to `boot_records`, `session_workflows`, `session_spacedock`, or the Pi collector itself — the fix is local to `transcript_boot`.

Tolerance: the fallback read is a single `handle.read()` with no seek, bounded by the file size. The cache prevents repeated fallback reads for a stable file. A growing file invalidates the fallback cache key, but the head scan runs first and short-circuits if the envelope is in the first 512KB.

## Acceptance criteria

### AC1: Long Pi FO session (envelope past 512KB) shows its workflow strip

A Pi first-officer session with a 3MB+ transcript where the boot envelope is past the 512KB head scan window shows `role: first-officer` with its workflow strip (non-empty `workflows` array).

**Verified by:** `test_pi_fo_long_session_boot_past_scan_window` in `test_pi.py` — creates a Pi transcript with the boot envelope at ~588KB (past 512KB), runs the Pi collector, and asserts `row["spacedock"]["role"] == "first-officer"` and `len(row["spacedock"]["workflows"]) > 0`. **Falsifying edit:** remove the fallback full-file read from `transcript_boot` — the head scan returns `[]`, `session_spacedock` returns `None`, and the assertion on `role` fails.

### AC2: Short Pi FO session (envelope within 512KB) is not regressed

A Pi first-officer session where the boot envelope is within the first 512KB still shows its workflow strip — the fallback does not break the existing fast path.

**Verified by:** the existing `test_pi_fo_session_renders_spacedock_strip` in `test_pi.py` — creates a short transcript with the envelope in the head scan, runs the collector, and asserts `role` and `workflows`. **Falsifying edit:** skip the head scan and always do a full-file read — the test still passes, but `test_pi_non_fo_session_has_no_spacedock` (the baseline that must not move) confirms a session with no envelope still returns `spacedock: None`.

### AC3: The head scan remains the fast path (no full-file read when the envelope is in the head)

A session where the boot envelope is within the first 512KB does not trigger a full-file read on subsequent refreshes — the head-scan cache returns the result without the fallback.

**Verified by:** `test_transcript_boot_head_scan_caches_without_fallback` in `test_pi.py` — creates a short transcript (envelope within 512KB), calls `transcript_boot` twice, and asserts the second call returns from cache (no file re-read). **Falsifying edit:** always do a full-file read regardless of head-scan result — the second call re-reads the file, and a test asserting the cache was hit (e.g., by patching `open` or checking the cache dict) fails.

### AC4: The fallback result is cached (no repeated full-file reads for a stable file)

A long session (envelope past 512KB) that has been scanned once does not re-read the full file on the next refresh — the fallback result is cached.

**Verified by:** `test_transcript_boot_fallback_cached` in `test_pi.py` — creates a 2MB+ transcript with the envelope past 512KB, calls `transcript_boot` twice, and asserts the second call returns from cache without re-reading the file. **Falsifying edit:** don't cache the fallback result — the second call re-reads the full file, and the cache-miss assertion fails.

## Test plan

| Test | Claim | Falsifying edit |
|---|---|---|
| `test_pi_fo_long_session_boot_past_scan_window` | A 3MB+ Pi transcript with the envelope past 512KB still classifies as first-officer with a workflow strip. | Remove the fallback read from `transcript_boot`. |
| `test_transcript_boot_fallback_finds_envelope` | `transcript_boot` returns a non-empty list when the envelope is past the head scan window. | Remove the fallback read. |
| `test_transcript_boot_head_scan_still_works` | `transcript_boot` returns the envelope when it is within the head scan window (no regression). | Skip the head scan entirely. |
| `test_transcript_boot_fallback_cached` | The fallback result is cached; a second call does not re-read the file. | Don't cache the fallback result. |
| `test_pi_non_fo_session_has_no_spacedock` (existing) | A session with no boot envelope still shows `spacedock: None` (baseline does not move). | Unconditionally set `spacedock` on every session. |

## Mock

`no mock: not a user-facing surface` — this is a backend collector fix. The dashboard already renders the workflow strip for sessions that carry `spacedock` data; the fix changes what the collector finds, not how the frontend renders it.

## Stage Report: ideation

- DONE: Approach names the simplest rejected alternative and why it cannot deliver the MVP value
  Increasing `spacedock_boot_scan_bytes` has no correct fixed value — large Pi initial messages push the envelope past any fixed window, and widening the window for all sessions makes every head scan more expensive.
- DONE: Riskiest mechanism exercised first: confirm whether transcript_boot can find the boot envelope at the START of a 3MB+ transcript cheaply (reverse scan or cached boot)
  Spike: 2.1MB transcript, envelope at 588KB (past 512KB head scan). `transcript_boot` returns `[]` (bug confirmed). `boot_records` on the full file finds 1 envelope. Full-file scan cost: 2.67ms (2.1MB), 10.03ms (8.2MB). Current cache permanently caches `[]` under `(path, 512000)` — negative result is sticky.
- DONE: Each acceptance criterion carries an external Verified-by clause with the concrete falsifying edit
  Four ACs (AC1–AC4), each with a named test and the specific edit that makes it fail.
- DONE: Whether a start-of-file scan or a cached boot is the right mechanism for a stable boot envelope
  Cached fallback full-file scan is the right mechanism: head scan (512KB) is the fast path, fallback reads the whole file once and caches the result. The boot envelope is stable (written once, never rewritten), so the cache is valid for the session's lifetime. A larger fixed window cannot deliver the MVP because no fixed value covers all cases.

### Summary

The bug is a too-small head scan window (512KB) in `transcript_boot`, not a tail scan as the entity body described — the code reads the first 512KB, and the envelope is at ~588KB because Pi transcript lines are large. The spike confirmed `transcript_boot` returns `[]` for a 2.1MB transcript with the envelope past 512KB, and that a full-file `boot_records` scan finds it at ~2.7ms cost. The chosen approach is a cached fallback: head scan first (fast path, unchanged), full-file read when the head scan misses (one-time cost, cached per session). The simplest rejected alternative — increasing the fixed window — cannot deliver the MVP because no fixed value covers all Pi session shapes.

## Stage Report: implementation

### Summary

Implemented the cached fallback full-file scan in `transcript_boot`. When the head scan (first `spacedock_boot_scan_bytes` = 512KB) finds no boot envelope and the file is larger than the scan window, the fallback reads the entire file and parses boot records from it. The fallback result is cached on `(path, size)` — the actual file size — so a growing file re-checks but a stable file does not. The head-scan negative result is no longer cached under the capped key for large files, fixing the sticky-negative bug where `[]` was permanently cached for growing transcripts.

### Completion checklist

- **transcript_boot: head scan (512KB) fast path unchanged; on miss, full-file read finds the boot envelope** — DONE. The head scan runs first on every call; on miss for files larger than `spacedock_boot_scan_bytes`, a full-file `handle.read()` feeds `boot_records`.
- **Cache the full-file result per session (envelope is stable, written once); negative result must NOT be sticky** — DONE. The fallback result is cached on `(path, size)`. The head-scan negative is NOT cached under the capped key for files larger than the scan window — it falls through to the fallback. A growing file invalidates the fallback key and re-checks.
- **No regression on short sessions (envelope in first 512KB)** — DONE. The existing `test_pi_fo_session_renders_spacedock_strip` and the new `test_transcript_boot_head_scan_still_works` both pass. The head-scan fast path is unchanged for files that fit in the scan window.
- **Pre-PR suite green** — DONE. `ruff check .`, `ruff format --check .`, `mypy`, and the full test suite (1188 passed, 1 skipped, 1307 subtests) all pass.

### Tests added

| Test | Claim | Falsifying edit |
|---|---|---|
| `test_pi_fo_long_session_boot_past_scan_window` | A Pi transcript with the envelope at ~588KB (past 512KB) still classifies as first-officer with a workflow strip. | Remove the fallback read from `transcript_boot`. |
| `test_transcript_boot_fallback_finds_envelope` | `transcript_boot` returns a non-empty list when the envelope is past the head scan window. | Remove the fallback read. |
| `test_transcript_boot_head_scan_still_works` | `transcript_boot` returns the envelope when it is within the head scan window (no regression). | Skip the head scan entirely. |
| `test_transcript_boot_head_scan_caches_without_fallback` | A short transcript does not trigger a full-file read on the second call — the head-scan cache returns the result. | Always do a full-file read regardless of head-scan result. |
| `test_transcript_boot_fallback_cached` | The fallback result is cached; a second call does not re-read the full file. | Don't cache the fallback result. |

### Files changed

- `cargento/skills/cargento/cargento_runtime/spacedock.py` — `transcript_boot` function: added fallback full-file read when head scan misses on files larger than `spacedock_boot_scan_bytes`; negative head-scan results no longer cached for large files; fallback cached on `(path, size)`.
- `cargento/skills/cargento/tests/test_pi.py` — 5 new tests (1 integration in `PiCollectorTest`, 4 unit in new `TranscriptBootTest` class).
- `pyproject.toml` — added `PLR0911` to the per-file ignore for `spacedock.py` (the function legitimately has 7 return statements for error and cache paths).
- `docs/design-spacedock.md` — updated the cost description to document the fallback mechanism.
