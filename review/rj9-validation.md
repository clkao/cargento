# Validation gate — usage-banner-disclosure (rj9), implementation complete

## Deliverable
Branch in ensign worktree `.worktrees/spacedock-ensign-usage-banner-disclosure`: `d80fd45` feat(dashboard): replace the usage disclosure modal with an in-flow banner; `f19f2d6` re-pin page byte oracles; `65f488f` docs.

`.u-overlay` blocking modal → in-flow `.u-banner`: heading + Keep usage on / Turn it off actions right-aligned, three disclosure paragraphs intact, page content fully visible beneath. First-show disclosure semantics preserved; dismissable; re-notify non-blocking.

## Stage Report
- Byte-oracle tests re-pinned from modal digests to banner digests (5 failures found and fixed by the worker — the only test surface that pinned the old layout).
- FO visual verification: /tmp/banner.png read against `usage-banner-disclosure/mock.html` — banner top-of-flow, mock contract met.

## Pre-PR suite (ensign worktree, green)
ruff check ✓ · ruff format --check ✓ · mypy 80 files ✓ · lint_embedded ✓ · validate_plugins ✓ · dashboard tests OK ✓

## Recommendation
PASSED — advance to validation for fresh-agent independent verification.
