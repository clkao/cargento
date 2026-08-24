---
title: Usage-limit disclosure is a blocking modal — should be a dismissable banner
status: done
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
        - id: gate:rj95tbw2vde46v8xjgcvgm9q:ideation
          stage: ideation
          attempts:
            - id: gate-attempt:rj95tbw2vde46v8xjgcvgm9q-ideation-1
              briefing:
                id: briefing:rj95tbw2vde46v8xjgcvgm9q:ideation:attempt-1:revision-1
                digest: sha256:d44c437551bfd8db1bce538f506043b6acb730f042c8ac6b9217fd6eb969e0ab
                request-digest: sha256:976286c8ddb0cadf3e87145848268283f48459c196a847f198d124aec17f87c2
                room-ref: ./review/ideation/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:rj95tbw2vde46v8xjgcvgm9q:ideation:1
                briefing: briefing:rj95tbw2vde46v8xjgcvgm9q:ideation:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-22T06:14:05.377646569Z"
                decision: approve
                reason: 'Conn: ''you have the conn ... record your autonomous approval as resolution'' (session 01a02216, reaffirmed ''just do some'' this session). Evidence: checklist 3/3 DONE; mock.html FO-rendered via headless chromium — banner under control bar with product visible on first paint (AC-1/AC-2 shape); rejected alternative named with reason; AC-3/AC-4 wire tokens + unchanged disclosure text carried explicitly in design. Ready for implementation: replace u-overlay with in-flow u-banner, keep consent wiring.'
              application:
                target-stage: implementation
                state: consumed
        - id: gate:rj95tbw2vde46v8xjgcvgm9q:validation
          stage: validation
          attempts:
            - id: gate-attempt:rj95tbw2vde46v8xjgcvgm9q-validation-1
              briefing:
                id: briefing:rj95tbw2vde46v8xjgcvgm9q:validation:attempt-1:revision-1
                digest: sha256:187ed04d50e791ab828ca3141dd70d35b71204a7c47672435dbbc3c9de0ce894
                request-digest: sha256:f4a38f40cf687f3a87f7bec8befde21f695f07b9a962d50ab3d90f0e391d7d38
                room-ref: ./review/validation/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:rj95tbw2vde46v8xjgcvgm9q:validation:1
                briefing: briefing:rj95tbw2vde46v8xjgcvgm9q:validation:attempt-1:revision-1
                by: agent:first-officer
                at: "2026-08-23T05:10:18.232224194Z"
                decision: approve
                reason: 'conn: fresh validator PASSED on code/contract evidence; supervisor mechanical re-run green (12/12 probe checks after fixing the probe''s calm-mode entry assumption; tests/ruff/mypy/lint_embedded green). Report 2ded013. Non-blocking notes: byte-oracle re-pin blind spot, ''blocks until dismissed'' phrasing.'
              application:
                target-stage: done
                state: pending
started: 2026-08-22T05:54:44Z
worktree: .worktrees/spacedock-ensign-usage-banner-disclosure
mod-block: merge:pr-merge
verdict: PASSED
completed: 2026-08-24T21:00:54Z
pr: pr-merge:146
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

## Approach (ideation)

Replace the fixed overlay with an in-flow banner. One element, two placements,
one modifier class:

- **Calm view**: `.u-banner` becomes a `flex:none` row inside `.cm-frame`,
  rendered by `calmLedger(d)` directly under the control bar (`cm-ctl`) and
  above the usage band — the exact recipe the usage band itself already uses,
  so the fixed-height frame is undisturbed and `cm-body` (the frame's only
  `flex:1; min-height:0; overflow:auto` child) absorbs the banner's height.
  `--sunk` surface, `border-bottom` on `--line2`, matching the frame's other
  in-flow separators.
- **Regular view**: the same element with a `.standalone` modifier (own
  `border` + `border-radius` + `--sunk`, because `.wrap` owns gaps rather than
  separators), emitted by `render(d)` between the `.top` brand block and the
  hero tiles.
- Markup: `role="dialog" aria-modal="true"` becomes `role="region"
  aria-label="usage disclosure"` — no modal semantics, no focus management,
  nothing `position:fixed`, no backdrop.
- The consent wiring is untouched: the disclosure still fires once, on the
  first payload carrying `usage_fetch`, gated by `cargento.usageModalSeen`;
  the two buttons stay `data-calm="umodal" data-arg="on"/"off"` (AC-3 names
  these handlers verbatim, so the wire token is NOT renamed); the key string
  stays so captains who already answered the modal are not re-asked.
  `usageModal(d)` is renamed to `usageBanner(d)` at its two call sites;
  heading (`u-modal-h` → `u-banner-h`) and paragraph (`u-modal-p` →
  `u-banner-p`) classes are renamed with it. The consent clause in
  `refresh()` (`usageEnabled && usageModalSeen`) is unchanged — nothing is
  fetched before the banner is answered, exactly as today.
- Dismissal IS answering (the two buttons). A separate "close without
  answering" X is deliberately out of scope: it would need a third
  consent state ("unanswered but hidden forever") that the security contract
  does not define, and AC-3 fixes dismissal to the existing handlers.

## Rejected alternative

**Restyle the overlay in place** (shrink `.u-overlay`'s centered card into a
smaller fixed-position floating card or toast in a corner, keeping
`position:fixed` and its z-index stacking). Rejected because it cannot deliver
the non-blocking value, whatever its size: a fixed element still OCCLUDES
whatever part of the dashboard it covers — in calm view the session rows it
hides are the product (AC-1 requires the surface rendered WITHOUT being
obscured, and "obscured less" still fails it) — and it keeps the modal's
interaction model: an element visually owned by no layout lane reads as a
demand for acknowledgement, not as page content one can scroll past. An
in-flow banner takes real layout space and occludes nothing; the displacement
is absorbed by one scroller the design already spends that way on the usage
band. The in-place restyle also gains nothing in code size — the change is
the same two call sites and one CSS block either way.

## Risk evidence

`no spike needed: {proven mechanisms}`. The riskiest mechanism is inserting a
new conditional row inside `.cm-frame` (`height:calc(100vh - 132px)`, flex
column at styles.css:268). The proof already ships: `.u-band`
(styles.css:404, `flex:none`, same position class) is a conditional in-flow
row in the same frame, and `.cm-body` (styles.css:304, `flex:1; min-height:0;
overflow:auto`) is the sole flex child, so a new `flex:none` sibling subtracts
its height from the scroller rather than overflowing the frame or pushing the
footer off-screen. The consent gating behind the render (`usage_fetch`,
`usageModalSeen`, `usage=1`) is unchanged, so the contract tests in
`test_contracts.py`/`test_quota.py` that pin it are unaffected. The mock at
`usage-banner-disclosure/mock.html` exercises the banner in both placements;
its three disclosure paragraphs were diffed byte-identical against the live
`usageModal()` template literals.

## Expected surface + tolerance

- `web/usage.js` — `usageModal()` rewritten as `usageBanner()`: template
  container/classes, `role`/`aria-modal`, the leading comment sentence about
  the modal. ±25 lines in one function; no logic changes elsewhere in the
  file.
- `web/main.js` — calm path (line 35): drop `usageModal(d)` from the `#app`
  concatenation. Regular path (lines 118–123): `usageModal(d)` moves from the
  end of the concatenation to between the `.top` block and `body`, renamed.
  ±8 lines.
- `web/calm.js` — `calmLedger()` gains one `usageBanner(d)` insertion after
  the `cm-ctl` row (before `usageBandCalm(d)`). ±3 lines.
- `web/styles.css` — the `.u-overlay` rule (line 490) deleted; `.u-modal*`
  block (lines 491–494) becomes `.u-banner*` per the mock. ±15 lines.
- Docs at implementation via `/sync-docs`: `cargento/skills/cargento/SKILL.md`
  ("a modal discloses exactly what is sent") — the shipped skill body, so the
  portability rules apply, prose-only edit; `SECURITY.md` ("a modal explains
  the token read"); `docs/design-usage-quota.md` (~5 "first-run disclosure
  modal" mentions). No behavioral contract changes.
- The front-end JS is not unit-tested; it is held by `scripts/lint_embedded.py`,
  which must stay green.

## Acceptance criteria (verified)

Each AC from the backlog seed stands, now with its external proof:

- **AC-1**: On first load (fresh browser, no localStorage flag), the dashboard
  renders fully and visibly with nothing obscuring it. **Verified by:**
  screenshot of a fresh-browser load (new profile or `localStorage.clear()` +
  reload) against the live server, showing the session surface unobstructed.
  Falsifying edit: the banner re-gaining `position:fixed` + full-viewport
  coverage, or any z-index layering over `.cm-frame`/`.top` content.
- **AC-2**: The disclosure still appears on first load, inline and
  non-blocking; product and disclosure are simultaneously readable.
  **Verified by:** the same screenshot showing the banner above (calm) or
  below-top (regular) the product surface in one viewport. Falsifying edit:
  the banner not rendering on first load, or rendering fixed/absolute over
  content.
- **AC-3**: The `data-calm="umodal"` `on`/`off` handlers keep working:
  clicking either sets `cargento.usageModalSeen`, "Turn it off" also clears
  usage, and a reload shows no banner. **Verified by:** interaction proof —
  click "Keep usage on", screenshot the bannerless dashboard plus a devtools
  (or console) read of `localStorage.getItem("cargento.usageModalSeen") ===
  "1"`, then repeat on a fresh profile with "Turn it off" and confirm the
  poll carries no `usage=1`. Falsifying edit: either button failing to set
  the flag or to dismiss on reload.
- **AC-4**: The disclosure text is unchanged; only presentation changes.
  **Verified by:** string comparison of the rendered banner's three
  paragraph texts against the pre-change modal paragraphs (already proven
  byte-identical in the mock, re-proven against the shipped `usage.js`).
  Falsifying edit: any character change in the three disclosure paragraphs
  or the heading.

## Test plan

- Static gates (must stay green, no new failures): `ruff check .`, `ruff
  format --check`, `mypy`, `scripts/lint_embedded.py` (the front-end linter
  is the only tooling that parses these JS bodies), and the full unittest
  suite under `coverage` — no server-side behavior changes, so existing
  quota/contract tests pin the untouched consent path.
- Behavioral proof (the gate's falsifiable evidence): launch the integration
  server with a fetch-capable harness present, load fresh in a browser with
  cleared storage, and capture the AC-1/AC-2 screenshot in calm mode and in
  regular mode; then the AC-3 click-through sequence on both buttons.
- The mock at `usage-banner-disclosure/mock.html` is the pre-implementation
  surrogate for the same checks: balanced markup (parsed clean), disclosure
  copy diffed byte-identical against `usageModal()`.

## Mock

`usage-banner-disclosure/mock.html` — static, self-contained (real palette
tokens copied verbatim from `styles.css`, dark mode honored). Renders the
calm view with the banner under the control bar and the regular view with
the `standalone` variant between brand block and hero tiles, each captioned
with its placement. The two buttons carry the real `data-calm="umodal"
data-arg="on"/"off"` wiring tokens.

## Stage Report: ideation

- DONE: A mock at usage-banner-disclosure/mock.* renders the target banner shape concretely enough for the captain to react to it — a static HTML/CSS artifact, not a prose description of a UI
  mock.html: self-contained, real palette tokens from styles.css, both placements (calm in-flow row under cm-ctl; regular standalone variant between .top and hero); parsed balanced, no browser available for a screenshot.
- DONE: Each acceptance criterion carries an external Verified-by clause matching its level (AC-1/AC-2 proven by screenshot of a fresh-browser load), each naming its falsifying edit
  "Acceptance criteria (verified)" section: AC-1/AC-2 screenshot of fresh-browser load against live server; AC-3 click-through + localStorage interaction proof; AC-4 byte diff of disclosure text; each names the change that fails it.
- DONE: The approach names the simplest rejected alternative (restyle the overlay in place) and why it cannot deliver the non-blocking value; unchanged disclosure text (AC-4) is carried into the design, not re-litigated
  "Rejected alternative" section: fixed float still occludes the product and keeps the modal's acknowledgement interaction model; approach keeps the three paragraphs verbatim (mock copy diffed byte-identical against usageModal() template literals).

### Summary

Fixed the first-load wall: the disclosure modal becomes an in-flow banner — a calm row under the control bar and a standalone block after the regular view's brand block, one element and one modifier. Consent wiring, wire tokens (`data-calm="umodal"`, the `usageModalSeen` key) and disclosure copy are deliberately unchanged; only presentation and ARIA semantics move. No spike needed: `.u-band` already proves a conditional `flex:none` row absorbs cleanly into the fixed-height `.cm-frame` via `cm-body`. Risk surfaced for implementation: SKILL.md's "a modal discloses…" line is in the shipped skill body, so its prose edit goes through the portability rules + /sync-docs; no machine-local browser was available here, so the mock is HTML-only (AC screenshots happen at implementation).

## Stage Report: implementation

- DONE: replace the `.u-overlay` blocking modal with one in-flow `.u-banner` element per the mock
  d80fd45 — heading + Keep usage on / Turn it off actions right-aligned, the three disclosure paragraphs preserved verbatim; consent wiring, wire tokens and the usageModalSeen key untouched (presentation and ARIA only), per the ideation summary
- DONE: byte-oracle tests re-pinned to the banner build
  f19f2d6 — 5 digest failures found and re-pinned; falsifier: revert any hunk of d80fd45 and the page digests fail
- DONE: docs name the disclosure a banner, not a modal
  65f488f — prose kept to presentation naming; SKILL.md untouched
- DONE: the Cargento pre-PR suite is green in the worktree
  ruff check ✓, ruff format --check ✓, mypy 80 files ✓, lint_embedded ✓, validate_plugins ✓, dashboard tests OK ✓
- DONE: visual verification against the mock contract
  /tmp/banner.png read by the FO: in-flow banner at top, page unobstructed, actions functional — matches usage-banner-disclosure/mock.html

### Summary

The disclosure is now one in-flow banner element; the worker found the prior ensign pass's core edit staged in the worktree, validated it against mock + ACs, fixed the missed byte-oracle pins, and committed in three logical units. First-show disclosure still blocks until dismissed; later expiry re-notifies without blocking.

## Stage Report: validation

- DONE: no `.u-overlay` element is rendered; the disclosure is one in-flow `.u-banner`
  Grep over the worktree (`**/*.{js,css,py,md,html}`) for `u-overlay|u-modal`: zero matches. usage.js:803 `usageBanner()` emits a single `<div class="u-banner">` with `role="region" aria-label="usage disclosure"`; guard byte-identical to the retired modal's (baseline usage.js:798–799 ≡ 803–804). Calm placement calm.js:720 sits inside `.cm-frame` under `.cm-ctl` and above the usage band; regular placement main.js:123 is the `standalone` variant between the brand block and the hero tiles — both match the mock.
- DONE: consent wiring, wire tokens and disclosure copy unchanged
  `data-calm="umodal" data-arg="on"/"off"` buttons, key string `cargento.usageModalSeen`, the `umodal` branch of `usageAction` (off also clears `usageEnabled`, on polls immediately), the poll consent clause `usageEnabled && usageModalSeen` (main.js:151), and the three disclosure paragraphs are byte-identical to baseline (AC-3/AC-4). The banner persists until answered; token-expiry re-notification stays the in-band non-blocking `u-expired` note.
- DONE: mock contract holds in the shipped build
  styles.css:494–499 define only `.u-banner*` (flex:none row + standalone modifier), identical to the mock's proposed CSS. Implementation-stage captures (/tmp/banner-calm.png, /tmp/banner-regular.png, /tmp/banner-dismissed.png) read by the validator: banner in-flow in both views, copy intact, page unobstructed, dismissal leaves a bannerless dashboard. Note: the mock lives at .spacedock-state/usage-banner-disclosure/mock.html, not under the worktree path the dispatch quoted.
- DONE: supervisor mechanical re-run (validator session had no shell/write)
  All 12 probe checks PASS (`shot_banner_validation.mjs` on the 4799 server; probe bug fixed by the FO — default display mode is regular, calm must be set explicitly): no `.u-overlay`, one `.u-banner`, position static, content after banner, copy intact, calm rows + regular heroes visible. Suite: dashboard tests OK (skipped=1); ruff `All checks passed!`; mypy `Success: no issues found in 80 source files`; lint_embedded clean.
- DONE: adversarial check — deleting `usageBanner(d) +` at calm.js:720 silently removes the banner in calm view (consent unanswerable, fetch never fires)
  The byte oracle (test_page.py's calm.js size+sha256 pin) fails and names the part — but only as drift: the fix is a re-pin, and f19f2d6's own five-digest re-pin demonstrates how regression gets blessed. No semantic JS test exists for the banner. Severity: note; recommend re-pins enumerate the intended behavior delta.

### Summary

No blockers: the modal is gone, one in-flow banner carries unchanged copy and consent wiring in both placements, and the byte oracle catches tamper (bluntly). Mechanical re-run returned green, including the fixed calm-mode probe. Verdict: PASSED. Low-severity notes: implementation summary's "blocks until dismissed" phrasing (layout is non-blocking; the banner persists until answered), the byte-oracle re-pin blind spot (recommend re-pins enumerate the behavior delta), and the validator's mock-path note (mock.html lives in the state checkout).
