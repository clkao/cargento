---
title: Observer agent pattern beside an active session
status: validation
source: captain seed
id: 9t63gp52zec23rh0k9t160ft
gates:
    version: 1
    records:
        - id: gate:9t63gp52zec23rh0k9t160ft:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:9t63gp52zec23rh0k9t160ft-backlog-1
              briefing:
                id: briefing:9t63gp52zec23rh0k9t160ft:backlog:attempt-1:revision-1
                digest: sha256:fbff56f12de99a83492a3bbdb7f509a2dc39df737835a9e92099569b2a4f7cbd
                request-digest: sha256:8e5e8dab2166b09143c0965f23510b9d53070f1da96e54259ab127c557062a1d
                room-ref: ./observer-agent-pattern/review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:9t63gp52zec23rh0k9t160ft:backlog:1
                briefing: briefing:9t63gp52zec23rh0k9t160ft:backlog:attempt-1:revision-1
                by: person:captain
                at: "2026-08-21T01:23:48.070296Z"
                decision: approve
                reason: 'approve: captain directs the observer agent (the deliverable) use a cheap model (haiku or luna). MVP delight: an operator points the observer at any active session — including one they didn''t start, running for hours — and gets back, in seconds from a cheap model, one line (goal) + 3-5 salient bullets (decisions, blocks, in-flight work), read-only, no interruption. MVP cut: goal + current stage + the one open block, derived from the transcript head + the workflow entity dir, written to a sidecar the session view renders. No streaming, no salience beyond goal+stage+block in the MVP.'
              application:
                target-stage: ideation
                state: consumed
        - id: gate:9t63gp52zec23rh0k9t160ft:ideation
          stage: ideation
          attempts:
            - id: gate-attempt:9t63gp52zec23rh0k9t160ft-ideation-1
              briefing:
                id: briefing:9t63gp52zec23rh0k9t160ft:ideation:attempt-1:revision-1
                digest: sha256:a7ff3cd9784f46ddaa98f7b4f1c8d3a023355684364869eabb51c7ccf9b5fb57
                request-digest: sha256:4235eacc7d3f6d87b8eb37f526e80ee289493994dfe34b9d788dd926b6f53ba8
                room-ref: ./observer-agent-pattern/review/ideation/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:9t63gp52zec23rh0k9t160ft:ideation:1
                briefing: briefing:9t63gp52zec23rh0k9t160ft:ideation:attempt-1:revision-1
                by: person:captain
                at: "2026-08-21T03:43:47.849119381Z"
                decision: revise
                reason: 'Revise (captain via Subspace, anchored on the ''Mock: none — backend-only analyzer'' line): every task must have user impact — the observer task is NOT backend-only with no mock. Rework the ideation to address WHERE the observer''s output appears to the user: identify the concrete user-facing dashboard surface this task owns, and produce a mock of that surface.'
            - id: gate-attempt:9t63gp52zec23rh0k9t160ft-ideation-2
              briefing:
                id: briefing:9t63gp52zec23rh0k9t160ft:ideation:attempt-2:revision-1
                digest: sha256:bc8f0bf4f2116ffa5a0a844e42f1e17b96cba293a4dfd0f9601b25c4a5bfebff
                request-digest: sha256:a6bd24d134604a2996bf99b25d0cd1c162560ac5c2223abe60d9a08be5fe256d
                room-ref: ./observer-agent-pattern/review/ideation/briefing-2
              resolution:
                type: Resolution
                id: resolution:spacedock:9t63gp52zec23rh0k9t160ft:ideation:2
                briefing: briefing:9t63gp52zec23rh0k9t160ft:ideation:attempt-2:revision-1
                by: person:captain
                at: "2026-08-21T04:08:11.572940334Z"
                decision: approve
                reason: 'Captain approved the reworked ideation via Subspace (binding resolution, decision approve, no annotations). Attempt 2 addresses the prior revise: observer panel as user-facing surface, mock with 4 variants, AC-4 measuring user-facing end value.'
              application:
                target-stage: implementation
                state: consumed
        - id: gate:9t63gp52zec23rh0k9t160ft:validation
          stage: validation
          attempts:
            - id: gate-attempt:9t63gp52zec23rh0k9t160ft-validation-1
              briefing:
                id: briefing:9t63gp52zec23rh0k9t160ft:validation:attempt-1:revision-1
                digest: sha256:2ecc4e22ecc903570e034c750ec2f126a9ffc88aa1b32998fe3a60bdf3f85dbd
                request-digest: sha256:0de2f6f8ee7c8c44154b3352631eba514868d17aac3243ab036881c679ebdc1e
                room-ref: ./observer-agent-pattern/review/validation/briefing-1
started: 2026-08-20T18:30:00Z
worktree: .worktrees/spacedock-ensign-observer-agent-pattern
---

An active coding session accumulates context a bystander cannot easily recover: what it set out to do, what it decided, where it got stuck, what it is doing right now. An observer agent — a separate agent that sits beside an active session, reads its transcript read-only, and derives its goal and the important things (decisions, blocks, in-flight work) — would let an operator ask "what is this session for and what matters in it right now?" without interrupting the session or relying on its self-report.

## Problem

There is no pattern for an agent that passively observes another active session and produces a durable, queryable summary of its goal and salient facts. Cargento already reads session transcripts read-only (the collectors), and Spacedock already derives workflow state from durable files — but neither derives a goal/salience summary from a live transcript. This task designs the observer pattern: where it reads, what it derives, how it stays read-only, and how its output is consumed.

## Proposed approach

**Home: Cargento-side analyzer** (the `transcripts.py` lineage — prompt-title derivation is the existing
analyzer precedent). The observer is a read-only analyzer module in `cargento_runtime` that, on demand,
reads the target session's transcript via the same bounded, freshness-windowed, append-only-tree reads the
Pi/Claude collectors already use, reads the target's workflow entity dir read-only (titles + statuses — the
spike confirms this is the goal source for workflow sessions), invokes a cheap model (haiku, or luna if it lands
in the Pi models store — see Model direction), and writes one sidecar (`<session>.observer.json`) the observer
panel renders. No streaming, no salience beyond goal + current stage + the one open block in the MVP.

**Model direction (captain, verbatim):** "the observer agent (the deliverable) should use a cheap model —
haiku or luna." "luna" may not be in the Pi models store yet. Resolution: default to haiku; if luna becomes
available, the model id is a single config field swapped without changing the analyzer. Recording luna's
absence as an implementation follow-up, not a design decision — the analyzer's model is parameterized.

**MVP delight (captain, verbatim):** "an operator points the observer at ANY active session — including one
they didn't start and one running for hours — and gets back, in seconds from a cheap model, one line (the
goal) + 3-5 salient bullets (decisions, blocks, in-flight work), read-only, no interruption. MVP cut: goal +
current stage + the one open block, derived from the transcript head + the workflow entity dir, written to a
sidecar the session view renders. No streaming, no salience beyond goal+stage+block in the MVP."

**Why the other homes cannot deliver the MVP:**

1. **Dispatched ensign** — rejected. Ensigns are entity-scoped workflow-stage workers: they are dispatched
   against a workflow entity and write to the state checkout. The MVP must observe ANY active session,
   including one the operator didn't start and one not running a workflow at all. A non-workflow session has
   no entity to scope the ensign to, and the ensign's write target (the state checkout) is not the session-view
   sidecar. Coupling the observer to the workflow it happens to be observing breaks the "any session"
   requirement and would make the observer a workflow participant rather than a bystander.
2. **Standing background agent** — rejected. The MVP is on-demand ("operator points the observer ... gets back,
   in seconds"), read-only, no interruption. A standing agent incurs continuous cost (contradicts the
   cheap-model direction), needs lifecycle/health management, and its persistent presence risks the very
   interruption and mutation the read-only contract forbids. The MVP is request-scoped, not continuous.

The analyzer home reuses the read-only read path the collectors already proved safe. The observer ships
**two** things: (1) the analyzer module that reads the transcript + entity dir, invokes the cheap model,
and writes the sidecar; (2) a minimal observer panel — a compact card that reads the sidecar and renders the
derived goal + current stage + one open block to the operator. The panel is self-contained: it renders from
the sidecar alone, without the dispatch tree.

**Boundary with the sibling** (`session-view-spacedock-visibility`): the sibling owns the session view mode
— the dispatch tree of workflow entities along the stage spine + the workflow-frontmatter goal line (a
static `title` scalar). The observer panel renders the session's **live semantic state** (what the session
is doing right now, where it is stuck) — a different, narrower surface the frontmatter goal line cannot
provide. The sibling's session view may embed the observer panel as a header or side panel in the future,
but that integration is the sibling's task; the MVP ships the panel standalone so the operator sees the
observer's output without the sibling.

The cheap-model call is an extension of the existing analyzer precedent (`prompt_title` already derives a
short title from prompt text). New module, not an expansion of `transcripts.py`'s own responsibilities — it
owns first-line metadata and prompt titles; the observer is a distinct concern with its own read set
(transcript head + workflow entity dir) and its own output (a sidecar + a panel that renders it).

**Simplest rejected alternative for the surface:** defer the entire render to the sibling
session-view-spacedock-visibility task and ship the sidecar alone (the prior ideation's framing). Rejected
because the sibling's goal line is a static frontmatter `title`, not the derived live goal the observer
produces from the transcript head — without its own panel, the operator cannot see the observer's output
without the sibling, and the observer would be backend-only with no user impact. The captain rejects that
framing: every task must have user impact, and this task must own where the observer's output appears.

## Risk evidence

**Riskiest mechanism exercised: deriving a goal that is not fabricated when the transcript carries none.**
A spike was run against two real Pi session transcripts in
`/Users/clkao/.pi/agent/sessions/--Users-clkao-git-spacedock-research-spacedock-v1--/` (read-only — the spike
opened files with `mode="r"`, never wrote):

- **Positive case** — a real first-officer session driving the Spacedock `dev` workflow
  (`2026-08-17T01-58-14-472Z_01a00d70-...jsonl`, 305 messages). Its opening directive is generic
  (`Use $spacedock:first-officer for this whole Pi session.`) and carries no goal by itself. The goal is
derivable only once the observer reads the opening directive AND a bounded recent (current-focus) window
AND the workflow entity dir. The spike derived: *"managing Spacedock dev workflow; current focus: <most
recent concrete directive>"* from recent concrete user directives ("report", "what are the remaining pi related
test and ergonomics issues") + the entity dir titles. Current stage `ideation` came from the entity dir
(the observed entity's `status:` frontmatter). One open block came from a bounded scan of recent assistant
text.
- **Negative case** — a 0-token aborted session
  (`2026-08-17T01-47-49-957Z_01a00d67-...jsonl`, 1 user message, 0 assistant text turns). Its only content is
the generic opener; no assistant work was produced. The spike returned *"no goal derived"* (evidence:
`generic-opener-only-no-work`), not a hallucinated goal. **The negative case reds the grade.**

**Proven mechanisms (no further spike needed):**
- A read-only agent can read another session's transcript without joining it — the Pi collector already
does this; the spike confirmed the append-only JSONL tree is readable from a separate process with no join.
- The "derive a goal, do not fabricate" failure mode is exercisable before building: the negative case is
detectable by a cheap model given a strict prompt ("derive a goal line OR return the literal string 'no goal
derived'; do not infer a goal from a generic skill-load directive alone"). The rule-based sentinel in the
spike is the deterministic fallback that bounds the model: when the only user message is a generic opener
and no assistant text was produced, the analyzer short-circuits to "no goal derived" without calling the
model.

Spike artifact: `/tmp/observer_spike2.py` (deterministic, read-only, asserts the negative case).

## Expected surface and tolerance

Estimate: small. One new analyzer module in `cargento_runtime` (e.g. `observer.py`), one read-only entry
point that reads the target transcript head (opening directive + bounded recent window) and the target
workflow entity dir, one cheap-model call, one sidecar writer to the store, and one observer panel
(~60–100 lines of JS in `web/observer.js`) that reads the sidecar and renders the derived goal + current
stage + one open block. One new server route (`/api/observe?harness=<h>&sid=<s>`) triggers the analyzer on
demand and returns the sidecar JSON; the panel fetches it when the operator clicks "observe" on a session
card. No new collector; the route is a thin trigger, not a polling endpoint.

Semantics this may change:
- The observer panel (`web/observer.js`) is a new JS module loaded by the page (`APP_PARTS` gains one entry).
  It renders from the sidecar alone; the sibling session view may later embed it, but the MVP ships it
  standalone. The assembled page hash changes, which the refactor test checks — that test must be updated.
- One new server route (`/api/observe`) triggers the analyzer on demand. It is a thin trigger: read
  transcript + entity dir, call the model, write the sidecar, return the JSON. Not a polling endpoint — the
  operator triggers it by clicking "observe".
- A cheap-model call is introduced into the Cargento runtime where none existed before. Tolerance: the call
  is on-demand (triggered by an operator pointing the observer at a session), not on every dashboard
  refresh; a model failure degrades to the deterministic "no goal derived" / rule-based stage+block fallback,
  never to a crash or a hallucination.
- Read set widens from "transcript only" (collectors) to "transcript head + workflow entity dir". The entity
  dir read is read-only and bounded (titles + statuses from frontmatter); it must not follow into entity
  bodies or worktrees.

Tolerance for the MVP cut: goal + current stage + the one open block. Anything beyond that (decisions set,
full salience bullets, streaming) is explicitly out of scope for the MVP.

## Acceptance criteria

1. **Goal + salience match the session's actual objective/in-flight work (live scenario).** An observer
   pointed at a known first-officer session produces a goal line and a current-stage/one-open-block set that
   match the session's stated objective and in-flight work. **Verified by:** a live scenario against the
   real FO transcript used in the spike (or a fresh equivalent) — the test asserts the derived goal references
   the session's current focus directive and the entity dir's stage, and would be falsified by editing the
   session's most recent concrete user directive to a different objective and observing the derived goal not
   update to track it (the negative case reds the grade: a session whose only content is a generic opener
   must yield "no goal derived", and a test asserting otherwise would fail).
2. **No-goal session yields "no goal derived", not a hallucination (negative case).** An observer pointed at a
   session with no stated goal (generic opener only, no assistant output) returns the literal string "no goal
   derived". **Verified by:** the spike's negative-case assertion (`assert goal_n == "no goal derived"`); a
   test that edits the cheap-model prompt to permit fabrication, or removes the deterministic short-circuit,
   would fail this assertion.
3. **The observer never mutates the observed session's repo/state.** The observer opens the target
   transcript and workflow entity dir read-only and writes only to its own sidecar (outside the observed
   session's repo/state). **Verified by:** a test that runs the observer against a target session whose repo
   and state dir are on a read-only filesystem mount (or `chmod -w` the target tree before the run) and
   asserts the run still produces the sidecar and exits 0 — any write into the observed tree would raise and
   fail the run. The sidecar is written to the observer's own store, not the observed session's tree.
4. **The observer panel renders the operator-visible output from the sidecar (user-facing end value).**
   When the operator clicks "observe" on a known session, the panel renders (a) the derived goal line (or the
   "no goal derived" sentinel) from the sidecar, (b) the current stage badge, and (c) the one open block. The
   operator sees these three fields without opening the sibling session view. **Verified by:** a test that
   feeds a fixture sidecar JSON (`{goal, stage, block}`) into the panel render function and asserts the
   rendered HTML contains the goal text, the stage name, and the block text; a second fixture with
   `goal: "no goal derived"` asserts the sentinel text appears in the rendered output, not a fabricated goal.
   **Falsified by:** (a) editing the sidecar's goal to a different string and observing the panel not
   update, (b) rendering a `no goal derived` sidecar with a hardcoded fallback goal and observing the
   fabricated text appear instead of the sentinel.

## Test plan

1. **Negative-case unit test (no-goal derivation).** Feed the analyzer a transcript fixture whose only user
   message is a generic skill-load opener and whose assistant output is empty; assert the analyzer returns
   "no goal derived" without invoking the model. Falsified by removing the deterministic short-circuit.
2. **Positive-case unit test (goal + stage + block).** Feed the analyzer the real FO transcript head fixture
   + the real entity dir fixture; assert the derived goal references the session's most recent concrete
   directive and the entity dir's stage. Falsified by editing the fixture's recent directive to a different
   objective and observing the goal not track it.
3. **Read-only invariant test.** Run the analyzer against a target transcript + entity dir placed on a
   read-only mount; assert the sidecar is still produced and the run exits 0, and assert no file under the
   target tree was modified (mtime unchanged). Falsified by any write into the target tree.
4. **Cheap-model failure-degradation test.** Inject a model call that errors/returns empty; assert the
   analyzer degrades to the deterministic fallback ("no goal derived" or rule-based stage+block) and never
   raises or hallucinates. Falsified by letting a model error propagate as a crash or a fabricated goal.
5. **Observer-panel render test (user-facing).** Feed a fixture sidecar JSON through the panel render
   function; assert the rendered HTML contains the goal text, the stage name, and the block text. Feed a
   `no goal derived` sidecar; assert the sentinel text appears, not a fabricated goal. Falsified by editing
   the sidecar's goal to a different string and observing the panel not update, or by adding a hardcoded
   fallback goal when the sidecar carries the sentinel.

Fixtures derive from the two real transcripts used in the spike (paths recorded in Risk evidence); the test
materializes bounded, redacted copies rather than depending on the live session dir (no hidden machine
dependency).

### Feedback Cycles

## Out of scope

- Making the observer write to the observed session's workflow state — it is read-only; its output is a sidecar.
- Replacing Cargento's existing collectors — the observer is a new pattern, not a refactor.
- Real-time streaming of the observer's output — follow-up.
- Full salience beyond the MVP cut (goal + current stage + the one open block) — the 3-5 bullets of decisions/
  in-flight work are a follow-up beyond the MVP cut.
- The session view's dispatch tree and workflow-frontmatter goal line — owned by the
  `session-view-spacedock-visibility` entity. This task ships the observer panel (goal + stage + block from
  the sidecar); the sibling ships the dispatch tree (entity nodes along the stage spine). The sibling may
  later embed the observer panel in its session view, but that integration is the sibling's task.
- Resolving whether "luna" exists in the Pi models store — implementation follow-up; haiku is the default.

## Stage Report: ideation

- DONE: Choose the observer's home
  Selected Cargento-side analyzer (the transcripts.py analyzer lineage); rejected dispatched ensign (entity-scoped, writes to state checkout, can't observe arbitrary non-workflow sessions) and standing background agent (continuous cost contradicts cheap/on-demand, risks interruption).
- DONE: Exercise the riskiest mechanism first — derive a goal without fabrication
  Spike `/tmp/observer_spike2.py` (read-only) ran against a real FO session (positive: goal derived from recent concrete directives + entity dir) and a 0-token aborted session (negative: returned "no goal derived", assert passed). Proven mechanisms: read-only transcript read without joining; no-goal detection via generic-opener short-circuit.
- DONE: Define external-proof ACs
  Three ACs with Verified-by clauses: (1) goal+salience match live scenario, falsified by editing the session's recent directive; (2) no-goal session yields "no goal derived", falsified by removing the short-circuit; (3) observer never mutates observed repo/state, verified by running against a read-only mount.
- DONE: Record the captain's model direction and MVP delight cut
  Recorded verbatim in Proposed approach: cheap model haiku-or-luna (luna absence noted as impl follow-up); MVP cut goal + current stage + the one open block, read-only, seconds, sidecar consumed by session view.

### Summary

Selected the Cargento-side analyzer as the observer's home (reuses the collectors' read-only read path; sits beside the session-view consumer). Exercised the riskiest mechanism with a read-only spike against two real Pi transcripts: a first-officer workflow session (positive — goal derivable from recent concrete directives + workflow entity dir) and a 0-token aborted session (negative — "no goal derived", asserted, not hallucinated). Wrote three falsifiable ACs (live-scenario match with a red negative case, no-goal sentinel, read-only invariant via read-only mount) and recorded the captain's haiku-or-luna model direction and the goal+stage+block MVP cut verbatim. No frontmatter touched; committed path-scoped to dev-state and pushed.

## Stage Report: ideation (cycle 2)

- DONE: Identify the concrete user-facing dashboard surface THIS task owns (where the operator sees the observer output)
  The observer panel — a compact card rendering the derived goal + current stage + one open block from the sidecar. Self-contained: renders from the sidecar alone, without the dispatch tree. Boundary with sibling: sibling owns the session view mode (dispatch tree + frontmatter goal line); this task owns the observer panel (live semantic state). Mock at observer-agent-pattern/mock.html renders four variants.
- DONE: Mock at observer-agent-pattern/mock.* renders that user-facing surface
  mock.html created: four variants — (A) active session with derived goal + stage + block, (B) no-goal session with "no goal derived" sentinel, (C) model failure degraded to rule-based fallback, (D) idle/not-yet-observed state. Static HTML sketch the captain can react to.
- DONE: At least one AC measures the user-facing end value (what the operator sees), not only the backend mechanism
  AC-4 added: the observer panel renders the operator-visible output (goal + stage + block) from the sidecar. Verified by feeding a fixture sidecar into the panel render function and asserting the rendered HTML contains goal text, stage name, and block text; a no-goal fixture asserts the sentinel appears. Falsified by editing the sidecar goal or adding a hardcoded fallback goal.
- DONE: Approach names the simplest rejected alternative and why it cannot deliver the MVP value
  For the surface: deferring the entire render to the sibling (the prior framing) — rejected because the sibling's goal line is a static frontmatter title, not the derived live goal; without its own panel, the observer is backend-only with no user impact. The captain rejects that framing.
- DONE: Riskiest mechanism exercised first (or no-spike-needed with proven mechanisms named)
  Spike `/tmp/observer_spike2.py` (read-only) stands: positive case (goal derived from transcript head + entity dir) and negative case (no goal derived, asserted). No further spike needed for the panel — it renders from the sidecar, a proven JSON-to-DOM path.
- DONE: Each AC carries an external Verified-by clause with the concrete falsifying edit
  AC-1: live scenario, falsified by editing the recent directive. AC-2: no-goal sentinel, falsified by removing the short-circuit. AC-3: read-only invariant, falsified by any write into the target tree. AC-4: panel render, falsified by editing the sidecar goal or adding a hardcoded fallback.

### Summary

Reworked the ideation per captain revise: the observer now ships its own user-facing surface (the observer panel — a compact card rendering goal + stage + block from the sidecar), not just a backend-only analyzer. Created a mock at observer-agent-pattern/mock.html with four variants (active, no-goal, model-failure fallback, idle). Added AC-4 measuring the user-facing end value (what the operator sees in the panel). Updated the boundary with the sibling session-view task: sibling owns the dispatch tree + frontmatter goal; this task owns the observer panel (live semantic state). Kept the existing three ACs and the no-fabrication spike evidence. Named the simplest rejected alternative for the surface (defer all rendering to the sibling — rejected because it leaves the observer backend-only with no user impact).

## Stage Report: implementation

- DONE: Change satisfies the ideation ACs: analyzer derives goal+stage+block (AC1)
  `observer.analyze()` derives the goal from the most recent concrete user directive, the stage from the entity dir's frontmatter `status`, and the block from a bounded scan of recent assistant text for block indicators. Falsified by editing the fixture's recent directive to a different objective and observing the goal not track it (test_observer.py: test_positive_case_derives_goal_stage_and_block).
- DONE: no-goal sentinel (AC2)
  A session whose only user message is a generic skill-load opener with no assistant output short-circuits to "no goal derived" without calling the model. The short-circuit bypasses the model entirely: a fabricating model cannot override the sentinel. Falsified by removing the deterministic short-circuit (test_observer.py: test_no_goal_session_yields_sentinel_not_hallucination, test_no_goal_sentinel_not_overridden_by_model).
- DONE: read-only invariant (AC3)
  The analyzer opens the target transcript and entity dir read-only and writes only to its own sidecar (under config.state_dir, outside the target tree). Test runs the analyzer against a read-only mount (chmod -w), asserts the sidecar is produced and no file under the target tree was modified. Falsified by any write into the target tree (test_observer.py: test_read_only_invariant).
- DONE: observer panel renders user-facing output (AC4)
  `renderObserverPanel(sidecar)` renders the goal text, stage badge, and block text from the sidecar alone. A no-goal sidecar renders the sentinel, not a fabricated goal. Falsified by editing the sidecar's goal to a different string and observing the panel not update, or by adding a hardcoded fallback goal (test_observer.py: test_panel_renders_goal_stage_and_block, test_panel_renders_no_goal_sentinel_not_fabricated_goal, test_panel_updates_when_sidecar_changes, test_panel_no_hardcoded_fallback_goal).
- DONE: Tests written first and watched fail for the right reason
  Five test classes covering the five test-plan cases: negative-case (no-goal derivation), positive-case (goal + stage + block), read-only-mount, model-failure-degradation, panel-render. All 9 tests pass; each asserts a specific falsifiable claim.
- DONE: Observer panel renders from the sidecar alone (goal + stage + block; no-goal sentinel; no hardcoded fallback)
  `renderObserverPanel` takes a sidecar JSON and returns HTML containing the goal, stage badge, and block. A `no goal derived` sidecar renders the sentinel with a distinct `observer-sentinel` class, never a hardcoded fallback.
- DONE: Pre-PR suite run green: ruff check, ruff format --check, mypy, lint_embedded.py, validate_plugins.py, coverage
  All pass: ruff check (0 errors), ruff format --check (111 files formatted), mypy --strict (0 issues in 82 files), lint_embedded.py (clean), validate_plugins.py (1 skill validated), coverage 88.6% (threshold 73). 1186 unit tests pass + 157 script tests.

### Summary

Implemented the observer agent pattern as a new `observer.py` analyzer module in `cargento_runtime`, a new `observer.js` panel in `web/`, and a new `/api/observe` route in `http_api.py`. The analyzer reads the target session's transcript head (opening directive + bounded recent window) and the workflow entity dir read-only, derives goal + current stage + one open block deterministically, and writes a sidecar to its own store. The no-goal short-circuit bypasses the model for generic-opener-only sessions; a model failure degrades to the deterministic fallback. The panel renders the sidecar's goal + stage + block without the dispatch tree. Three config fields added (observer_head_bytes, observer_goal_cap_chars, observer_block_cap_chars). Import graph and runtime file inventory updated. Byte oracles in test_page.py and test_lifecycle.py updated for the new JS part.

## Stage Report: validation

- DONE: Each AC's Verified-by reproduced independently (not trusting self-report)
  AC1: ran a standalone script feeding a transcript with directive "Fix the authentication bug" + entity dir status "implementation" — derived goal tracked the directive, stage matched frontmatter, block matched "blocked" in assistant text. Falsifying edit (changed directive to "Refactor the database layer") produced a different goal tracking the new directive. AC2: ran a standalone script with a generic-opener-only transcript + a fabricating model — goal returned "no goal derived", reason "generic-opener-only-no-work", fabricated text absent. AC3: ran the analyzer against a chmod -w target tree — sidecar produced outside the target, transcript and entity file mtimes unchanged. AC4: ran renderObserverPanel under node with 5 fixture sidecars — goal+stage+block rendered, no-goal sentinel rendered with observer-sentinel class, sidecar change updated output, no hardcoded fallback, null sidecar rendered idle state.
- DONE: no-goal sentinel is NOT overridden by a fabricating model (independent check of the deterministic short-circuit)
  Confirmed two ways: (1) a fabricating model passed to analyze() with a generic-opener-only transcript returned "no goal derived" (model return value never appeared); (2) source inspection confirms the model branch is gated by `if goal != NO_GOAL and model is not None` — when the short-circuit sets goal to NO_GOAL, the model callable is never invoked.
- DONE: Observer panel renders from the sidecar alone; no hardcoded fallback goal (independent check)
  renderObserverPanel reads only its sidecar argument — no fetch, no global state, no hardcoded goal string. A no-goal sidecar renders the literal sentinel text with class observer-sentinel; assertions for "unknown session" and "session in progress" both returned false. A sidecar with a different goal string produces different output (falsified).
- DONE: Pre-PR suite re-run green from the validation lane: ruff, mypy, lint_embedded, validate_plugins, coverage
  ruff check: All checks passed. ruff format --check: 111 files already formatted. mypy: Success, no issues found in 82 source files. lint_embedded.py: Frontend assets clean. validate_plugins.py: Validated 1 skill. coverage: 88.6% (threshold 73). 1186 unit tests + 157 script tests, all OK. bump_version --current: 0.11.0.
- DONE: Reviewer findings recorded under workflow labels with a PASSED/REJECTED recommendation
  No new findings discovered during validation. All four ACs independently reproduced with falsifying edits exercised. Recommendation: PASSED.

### Summary

Independently reproduced every AC's Verified-by clause rather than trusting the implementation's self-report. AC1: goal tracks the most recent concrete directive (falsified by changing the directive). AC2: no-goal sentinel returned for generic-opener-only transcripts, not overridden by a fabricating model (confirmed by source: model branch gated on `goal != NO_GOAL`). AC3: read-only invariant holds — sidecar produced outside the chmod -w target tree, target mtimes unchanged. AC4: observer panel renders goal+stage+block from the sidecar alone, no hardcoded fallback. Pre-PR suite green: ruff, mypy, lint_embedded, validate_plugins, coverage 88.6%. No new findings. Recommendation: PASSED.
