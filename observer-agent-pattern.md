---
title: Observer agent pattern beside an active session
status: ideation
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
started: 2026-08-20T18:30:00Z
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
in the Pi models store — see Model direction), and writes one sidecar (`<session>.observer.json`) the session
view renders. No streaming, no salience beyond goal + current stage + the one open block in the MVP.

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

The analyzer home reuses the read-only read path the collectors already proved safe, sits beside the
session-view consumer (the `session-view-spacedock-visibility` entity owns that surface), and treats the
cheap-model call as an extension of the existing analyzer precedent (`prompt_title` already derives a short
title from prompt text). New module, not an expansion of `transcripts.py`'s own responsibilities — it owns
first-line metadata and prompt titles; the observer is a distinct concern with its own read set
(transcript head + workflow entity dir) and its own output (a sidecar).

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
workflow entity dir, one cheap-model call, one sidecar writer to the store the session view already
renders. No new collector, no new server route in the MVP — the session view polls/reads the sidecar.

Semantics this may change:
- The session view (`session-view-spacedock-visibility`) gains a read of the observer sidecar — a new read
  path, additive, no existing read changed.
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
- The session view's rendering of the sidecar — owned by the `session-view-spacedock-visibility` entity, a
  separate task.
- Resolving whether "luna" exists in the Pi models store — implementation follow-up; haiku is the default.
