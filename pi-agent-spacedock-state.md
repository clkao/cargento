---
title: Pi agent view shows Spacedock state
status: validation
source: captain seed
id: hdz7pr9bmw5vpc5ah52sbcmb
gates:
    version: 1
    records:
        - id: gate:hdz7pr9bmw5vpc5ah52sbcmb:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:hdz7pr9bmw5vpc5ah52sbcmb-backlog-1
              briefing:
                id: briefing:hdz7pr9bmw5vpc5ah52sbcmb:backlog:attempt-1:revision-1
                digest: sha256:72b0d8f8fcb2bff0cf1e538359ab0e329bfd3286f7cd7460ce441ef10b93c404
                request-digest: sha256:94ef3bab36b8c7fc5829604446fccd0d6c8b2efde923298a9f24157e7494ca20
                room-ref: ./pi-agent-spacedock-state/review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:hdz7pr9bmw5vpc5ah52sbcmb:backlog:1
                briefing: briefing:hdz7pr9bmw5vpc5ah52sbcmb:backlog:attempt-1:revision-1
                by: person:captain
                at: "2026-08-21T02:44:21.635236013Z"
                decision: approve
                reason: captain directs the backlog seed to advance to ideation for design
              application:
                target-stage: ideation
                state: consumed
        - id: gate:hdz7pr9bmw5vpc5ah52sbcmb:ideation
          stage: ideation
          attempts:
            - id: gate-attempt:hdz7pr9bmw5vpc5ah52sbcmb-ideation-1
              briefing:
                id: briefing:hdz7pr9bmw5vpc5ah52sbcmb:ideation:attempt-1:revision-1
                digest: sha256:d598f32c752c3d31f6ffd3929b934960db1a19989e105008c714e43e8f335751
                request-digest: sha256:b967f5f4eb3eaadc79f5bf1ef5efa55323def3e0749f91fa82f91f54c09ff09a
                room-ref: ./pi-agent-spacedock-state/review/ideation/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:hdz7pr9bmw5vpc5ah52sbcmb:ideation:1
                briefing: briefing:hdz7pr9bmw5vpc5ah52sbcmb:ideation:attempt-1:revision-1
                by: person:captain
                at: "2026-08-21T03:53:34.914292149Z"
                decision: approve
                reason: Captain approved via Subspace (binding resolution, decision approve, no annotations).
              application:
                target-stage: implementation
                state: consumed
        - id: gate:hdz7pr9bmw5vpc5ah52sbcmb:validation
          stage: validation
          attempts:
            - id: gate-attempt:hdz7pr9bmw5vpc5ah52sbcmb-validation-1
              briefing:
                id: briefing:hdz7pr9bmw5vpc5ah52sbcmb:validation:attempt-1:revision-1
                digest: sha256:ba47fbf6562a7454bb806bb1986c311098c9469c2f11d7e01678f81066c02d57
                request-digest: sha256:9825196df9c78b09d8483c6bbf1b732142b4a37b91a17fa1eda9ee69cfbb0f62
                room-ref: ./pi-agent-spacedock-state/review/validation/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:hdz7pr9bmw5vpc5ah52sbcmb:validation:1
                briefing: briefing:hdz7pr9bmw5vpc5ah52sbcmb:validation:attempt-1:revision-1
                by: person:captain
                at: "2026-08-21T04:14:33.064375346Z"
                decision: approve
                reason: Captain approved validation via Subspace (binding resolution, decision approve, no annotations). Both ACs reproduced with falsifying edits, toolResult additive, pre-PR suite green, diff purely additive. Delivery can proceed to done.
              application:
                target-stage: done
                state: pending
started: 2026-08-21T02:46:39Z
worktree: .worktrees/spacedock-ensign-pi-agent-spacedock-state
---

Cargento already derives Spacedock workflow cartography for Claude first officers — `collectors/claude.py` decides a session is a first officer from its transcript's `agentSetting`, then asks `cargento_runtime/spacedock.py` for the workflow strip. The Pi collector (`collectors/pi.py`) does not yet surface this, so a Pi first officer renders on the dashboard without the workflow context a Claude officer gets.

## Problem

A Pi first officer running `spacedock pi` writes the same durable state a Claude officer does, and Cargento's Spacedock parser is harness-agnostic, but the Pi collector never calls it. The dashboard's session card for a Pi FO omits the workflow strip the design (`docs/design-spacedock.md`, S-1..S-4) exists to provide.

## Proposed approach

The Pi collector classifies a session as a first officer by finding a Spacedock boot envelope in its transcript — the same `definition_dir` / `entity_dir` payload `spacedock status --boot` writes, which only a first officer runs. The boot envelope is both the classifier and the data source: its presence proves the session is a FO, and its paths feed `spacedock.session_workflows` directly.

Pi has no `agentSetting` (Claude's `--agent spacedock:first-officer` flag), so the transcript body is the only authority. A Pi FO session records the boot output as a `toolResult` role message whose `content[].text` carries the JSON envelope. The existing `spacedock.tool_result_text` only recognises Claude's `tool_result` content blocks, so it finds nothing in a Pi transcript. The change widens `tool_result_text` with a three-line branch: when `message.role == "toolResult"`, extract text from `content[]` blocks with `type: "text"` — Pi's tool-result shape. This is additive: Claude transcripts are unaffected because their tool results carry `type: "tool_result"` blocks, not `role: "toolResult"`.

With that, `spacedock.transcript_boot` works on Pi transcripts unchanged. The Pi collector gains a `session_spacedock` helper mirroring `collectors/claude.py`'s: call `transcript_boot` on the session path; if it returns envelopes, the session is a first officer; call `session_workflows` with the envelopes and an empty worker-name list (Pi subagents are not tracked as named pills in this task); return `{"role": "first-officer", "workflows": [...]}`. If no envelopes, return `None` — a non-FO session gets no strip. The `collect` function sets the `spacedock` key on the session dict, the same key `sdBlock` in `web/regular.js` already renders harness-agnostically.

The import graph allowlist (`test_contracts.py`) gains `cargento_runtime.spacedock` → `cargento_runtime.collectors.pi`, mirroring the Claude collector's existing dependency.

### Simplest rejected alternative

Classify by the first user prompt containing `"spacedock:first-officer"` or `"$spacedock"`. It cannot deliver the MVP value because the prompt text is what the user typed, not a contract — it varies by harness invocation and is absent from headless (`-p`) launches. More fundamentally, it provides no `definition_dir` or `entity_dir`, so `session_workflows` has nothing to read: without the boot envelope, there is no workflow directory to open and no entity-state directory to scan. The boot envelope is the one artifact that both proves the session is a FO and carries the paths the parser needs.

## Risk evidence

The riskiest mechanism is whether `spacedock.transcript_boot` can find a boot envelope in a real Pi FO transcript. Exercised first against two live Pi FO sessions in `~/.pi/agent/sessions/`:

- **Before the fix:** `transcript_boot` returns `[]` for both sessions. `tool_result_text` looks for `message.content[].type == "tool_result"` (Claude's shape); Pi writes tool results as `message.role == "toolResult"` with `content[].type == "text"` blocks, so no text is extracted and no envelope is found.
- **After the three-line `toolResult` branch:** `transcript_boot` finds the boot envelope in both sessions — `definition_dir` and `entity_dir` are extracted correctly. `session_workflows` then renders a workflow strip with the correct stage spine (`backlog → ideation → implementation → validation → done`) and live entity slugs from the state directory.

No spike needed beyond the above: `session_workflows`, `read_workflow`, and `read_entities` are already harness-agnostic (they take boot envelopes and paths, not transcripts), and the frontend `sdBlock` reads `sess.spacedock` without knowing which harness produced it. The only unproven link was the boot-envelope extraction from Pi's transcript format, and it is now proven.

## Expected surface and tolerance

Estimate: ~3 lines in `spacedock.tool_result_text` (add `toolResult` role branch), ~20 lines in `collectors/pi.py` (`session_spacedock` helper + `spacedock` key in `collect`'s session dict), ~1 line in `tests/test_contracts.py` (add `cargento_runtime.spacedock` to the Pi collector's allowlist entry). Total ~25 lines, tolerance ±10.

Semantics this may change:
- `tool_result_text` in `spacedock.py` now also extracts text from Pi `toolResult` role messages. This is additive — Claude transcripts carry `tool_result` content blocks, not `toolResult` role messages, so existing behaviour is unchanged. The `boot_records` function that calls it is unchanged.
- Pi sessions with a boot envelope gain a `spacedock` field (`{"role": "first-officer", "workflows": [...]}`). Non-FO Pi sessions are unchanged (`spacedock` is absent).
- The import graph allowlist gains one edge: `cargento_runtime.collectors.pi` → `cargento_runtime.spacedock`. This is the same dependency shape `collectors.claude` already has.

## Acceptance criteria

### AC-1: A Pi FO session on the dashboard shows the same workflow strip a Claude FO session does

A Pi session whose transcript contains a Spacedock boot envelope renders with `spacedock.role == "first-officer"` and a non-empty `spacedock.workflows` list whose first entry carries the workflow's ordered `stages` spine and at least one entity. The strip shape matches what a Claude FO session would produce for the same workflow directory and entity state.

**Verified by:** `test_pi_fo_session_renders_spacedock_strip` — builds a Pi session JSONL with a session header, a user prompt, an assistant tool call, and a `toolResult` message whose text is a boot envelope JSON (with `definition_dir` and `entity_dir`); writes a workflow README with `commissioned-by: spacedock@` frontmatter and a `stages.states[]` block; writes an entity state file with `status: ideation`; runs `pi_collector.collect`; asserts the session's `spacedock` field has `role == "first-officer"` and `workflows[0].stages` matches the workflow's declared stage names. **Falsifying edit:** remove the `toolResult` branch from `tool_result_text` — `transcript_boot` returns `[]`, `spacedock` is `None`, the assertion fails.

### AC-2: A non-FO Pi session shows no Spacedock strip — the baseline does not move

A Pi session with no boot envelope in its transcript has no `spacedock` field (or `spacedock` is `None`). This is the same behaviour as today, before the change.

**Verified by:** `test_pi_non_fo_session_has_no_spacedock` — builds a Pi session JSONL with a normal user/assistant exchange and no boot envelope; runs `pi_collector.collect`; asserts `spacedock` is absent from the session dict (or `None`). **Falsifying edit:** unconditionally set `spacedock` on every Pi session regardless of boot presence — the test fails, which is the baseline moving the wrong way: every Pi session would show a Spacedock badge.

## Test plan

1. **`test_pi_fo_session_renders_spacedock_strip`** (new, in `tests/test_pi.py`). The end-value test (AC-1). Constructs a Pi session JSONL with a `toolResult` message carrying a boot envelope, a workflow README with `commissioned-by` and stages, and an entity state file with a non-resting `status`. Runs `pi_collector.collect` and asserts `spacedock.role` and `spacedock.workflows[0].stages`. Fails if the `toolResult` branch is removed from `tool_result_text`.
2. **`test_pi_non_fo_session_has_no_spacedock`** (new, in `tests/test_pi.py`). The baseline test (AC-2). Same fixture without the boot envelope. Asserts `spacedock` is absent or `None`. Fails if `spacedock` is unconditionally set.
3. **`test_boot_records_finds_pi_tool_result_format`** (new, in `tests/test_spacedock.py`). Directly tests that `spacedock.boot_records` extracts a boot envelope from a Pi-format `toolResult` record. Fails if the `toolResult` branch is removed from `tool_result_text`.
4. **Import graph allowlist update** (`tests/test_contracts.py`). Add `cargento_runtime.spacedock` to the `cargento_runtime.collectors.pi` expected-dependency set. The existing `test_runtime_import_graph_matches_the_reviewed_allowlist` test enforces it.

All tests run on every runner (fixtures, no network, no live `spacedock` binary).

### Feedback Cycles

## Out of scope

- Rewriting `spacedock.py` — it is harness-agnostic by design; this task wires the Pi collector to it. The one change to `spacedock.py` (`tool_result_text` gaining a `toolResult` branch) is a three-line addition that makes the existing boot-reader work on a second transcript format, not a structural rework.
- Widening Spacedock cartography features — S-4 deliberately takes only the stage.
- Tracking Pi subagents as named worker pills for live-entity attribution — the `worker_names` list passed to `session_workflows` is empty; entities still surface from the state directory and boot snapshot. Live-worker attribution is a follow-up.

## Stage Report: ideation

- DONE: Approach names the simplest rejected alternative and why it cannot deliver the MVP value
  Classifying by the first user prompt containing `"spacedock:first-officer"` was rejected: the prompt text is not a contract, varies by invocation, and provides no `definition_dir`/`entity_dir` — `session_workflows` has nothing to read without the boot envelope.
- DONE: Riskiest mechanism exercised first (or no-spike-needed with proven mechanisms named)
  Exercised `spacedock.transcript_boot` against two live Pi FO transcripts: before the fix it returns `[]` (Pi `toolResult` role not recognised); after a three-line `toolResult` branch in `tool_result_text` it finds the boot envelope and `session_workflows` renders the correct stage spine and entities. `session_workflows`/`read_workflow`/`read_entities` and `sdBlock` are already harness-agnostic.
- DONE: Each AC carries an external Verified-by clause with the concrete falsifying edit
  AC-1 verified by `test_pi_fo_session_renders_spacedock_strip` asserting `spacedock.role` and `workflows[0].stages`; fails if the `toolResult` branch is removed. AC-2 verified by `test_pi_non_fo_session_has_no_spacedock` asserting no `spacedock` field; fails if `spacedock` is unconditionally set — the baseline moving the wrong way.

### Summary

Filled all ideation placeholders: the Pi collector classifies a FO by finding a boot envelope in its transcript (Pi has no `agentSetting`), `tool_result_text` gains a three-line `toolResult` branch so `transcript_boot` works on Pi transcripts, and `session_workflows` is called with the envelopes to produce the same `spacedock` field a Claude FO session already publishes. Two ACs with falsifying edits, a four-test plan, and a mock at `pi-agent-spacedock-state/mock.html` rendering the Pi FO card with the workflow strip.

## Stage Report: implementation

- DONE: Change satisfies the ideation ACs: Pi FO session renders the same workflow strip a Claude FO does; non-FO Pi session shows no strip
  `test_pi_fo_session_renders_spacedock_strip` asserts `spacedock.role == "first-officer"` and `workflows[0].stages == ["intake","review","posted"]` with entity `drc-1`; `test_pi_non_fo_session_has_no_spacedock` asserts `spacedock` is None for a plain session.
- DONE: Tests written first and watched fail for the right reason (test_pi_fo_session_renders_spacedock_strip, test_pi_non_fo_session_has_no_spacedock)
  All three new tests failed before implementation: `test_boot_records_finds_pi_tool_result_format` got `1 != 0` (no `toolResult` branch), `test_pi_fo_session_renders_spacedock_strip` got `AssertionError` on `assert sd is not None` (no `session_spacedock`), `test_pi_non_fo_session_has_no_spacedock` passed trivially (no `spacedock` key yet). The contracts test failed on the allowlist mismatch.
- DONE: toolResult branch in tool_result_text is additive (Claude tool_result content blocks unchanged)
  The `toolResult` branch returns early only when `message.role == "toolResult"`; Claude transcripts carry `type: "tool_result"` content blocks under a different role, so they fall through to the existing loop unchanged. `test_boot_records_require_tool_result_provenance` still passes.
- DONE: Pre-PR suite run green: ruff check, ruff format --check, mypy, lint_embedded.py, validate_plugins.py, coverage
  ruff check: All checks passed. ruff format --check: 109 files already formatted. mypy: Success, no issues in 80 files. lint_embedded: clean. validate_plugins: validated. coverage: 89.2% (threshold 73%). Full suite: 1180+157 tests OK.

### Summary

Added a `toolResult` role branch to `spacedock.tool_result_text` (additive — Claude's `tool_result` blocks unchanged), wired `collectors/pi.py` to the shared Spacedock cartography via `session_spacedock` (classifies FO by boot envelope, calls `session_workflows` with empty worker names), and added `cargento_runtime.spacedock` to the Pi collector's import-graph allowlist. Three new tests plus the allowlist update; all pre-PR checks green. Commit `4f3fbc0` on `spacedock-ensign/pi-agent-spacedock-state`.

## Stage Report: validation

- DONE: Each AC's Verified-by reproduced independently (not trusting self-report): AC1 Pi FO strip, AC2 non-FO no strip
  AC-1: ran `test_pi_fo_session_renders_spacedock_strip` — passes; removed the `toolResult` branch from `tool_result_text`, re-ran, got `AssertionError` on `assert sd is not None` (transcript_boot returned [], spacedock is None) — fail confirmed. Restored; passes. AC-2: ran `test_pi_non_fo_session_has_no_spacedock` — passes; replaced the `session_spacedock` call with an unconditional `{"role":"first-officer","workflows":[]}`, re-ran, got `AssertionError: {'role': 'first-officer', 'workflows': []} is not None` — fail confirmed. Restored; passes.
- DONE: Pre-PR suite re-run green from the validation lane: ruff, mypy, lint_embedded, validate_plugins, coverage
  ruff check: All checks passed. ruff format --check: 109 files already formatted. mypy: Success, no issues in 80 files. lint_embedded: clean. validate_plugins: validated. bump_version --current: 0.11.0. coverage: 89.2% (threshold 73%). Full suite: 1180+157 tests OK.
- DONE: toolResult branch is additive against Claude transcripts (Claude tool_result content blocks unchanged) — independent check
  Wrote a standalone script exercising `tool_result_text`: a Claude `role:"tool"` record with `type:"tool_result"` content blocks extracts `["=== BOOT ===\n{}", "second"]` unchanged; a Pi `role:"toolResult"` record extracts `["=== BOOT ===\n{}"]`; a conversation `role:"assistant"` with `type:"text"` blocks returns `[]` (provenance preserved). `test_boot_records_require_tool_result_provenance` (27 spacedock tests) still passes. The branch returns early only on `role == "toolResult"`; Claude's `tool_result` blocks fall through to the existing loop untouched.
- DONE: Reviewer findings recorded under workflow labels with a PASSED/REJECTED recommendation
  Diff is purely additive (185 insertions, 0 deletions, 5 files). Scope matches the ideation tolerance (~25 lines, ±10): 18 lines in spacedock.py, 32 in pi.py, 1 in test_contracts.py, 103+31 test lines. No frontmatter touched, no agents/references files touched. Recommendation: PASSED.

### Summary

Independently reproduced both ACs and their falsifying edits from the validation lane: AC-1 (Pi FO strip) fails when the `toolResult` branch is removed; AC-2 (non-FO no strip) fails when spacedock is set unconditionally. The `toolResult` branch is proven additive — Claude `tool_result` content blocks extract unchanged, conversation `text` blocks stay excluded. Pre-PR suite fully green (ruff, mypy, lint_embedded, validate_plugins, coverage 89.2%). Diff is purely additive, in-scope. Recommendation: PASSED — delivery can proceed to `done`.
