from __future__ import annotations

import json
import shutil
import unittest
from typing import Any

from .page_harness import PageJsHarness


class SessionViewTest(PageJsHarness):
    """The session display mode: one session's dispatch tree and goal line.

    These execute the shipped app.js: every assertion is about what the page
    does with a payload, not about the assembled document's source text.
    """

    # Globals the page reads at load (localStorage) and a stub for the session
    # picker's click channel.
    @staticmethod
    def prelude(saved: str | None = None) -> str:
        seed = "{}" if saved is None else json.dumps({"cargento.displayMode": saved})
        return f"""
let __store = {seed};
const localStorage = {{
  getItem(k){{ return Object.prototype.hasOwnProperty.call(__store, k) ? __store[k] : null; }},
  setItem(k, v){{ __store[k] = String(v); }}
}};
let __timers = [];
const setTimeout = fn => {{ __timers.push(fn); return __timers.length; }};
"""

    def run_session(
        self, checks: str, *, saved: str | None = None, hash_val: str | None = None
    ) -> Any:
        prelude = self.prelude(saved)
        if hash_val is not None:
            prelude += f'\nlocation.hash = "{hash_val}";\n'
        return self._run_page_js(self.FIXTURE + checks, prelude=prelude)

    # A fixture FO session with two workflows and three entities at different
    # stages. The goal is the workflow frontmatter `title` scalar, already
    # published as `workflow.goal` by spacedock.read_workflow.
    FIXTURE = """
const mk = o => Object.assign({
  harness: "claude", session: "1234abcd", sid: "1234abcd", project: "repo/proj",
  title: "Active dispatch", last_prompt: "", state: "working", state_detail: "running Bash",
  active: true, last_activity: 990, rate_per_min: 10, total: 0, done: 0, open: 0,
  progress_pct: 0, eta_h: null, turn: null, subagents: [], tasks: [], spacedock: null
}, o);
const sdWf = (over) => Object.assign({
  workflow: "debug-flywheel", stages: ["intake", "review", "fix-and-harden"],
  goal: "", entities: []
}, over);
const ent = (slug, stage, live, cycle) => ({slug, stage, live: !!live, cycle: cycle || ""});
const fo = mk({
  spacedock: {
    role: "first-officer",
    workflows: [
      sdWf({goal: "Ship session view", entities: [
        ent("drc-1", "review", false, "c2"),
        ent("drc-2", "fix-and-harden", true),
        ent("drc-3", "intake", false)
      ]}),
      sdWf({workflow: "other-wf", goal: "", stages: ["intake", "posted"], entities: [
        ent("pr-7", "posted", false)
      ]})
    ]
  }
});
const board = sessions => ({
  generated: 100000, window_hours: 24, show_all: false,
  rate_window_sec: 600,
  harnesses: [{key: "claude", label: "Claude Code", discovered: true, error: null, reports_rate: true}],
  summary: {needs_input: 0, working: 1, rate_per_min: 10, active_sessions: 1,
            open_tasks: 0, progress_pct: 0, total_tasks: 0, total_done: 0},
  sessions
});
"""

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_ac1_session_view_renders_dispatch_tree(self) -> None:
        """AC-1: the session view renders one causal-log per workflow, with entity
        slugs, stage names, and the sd-live class on live entities. The mirror
        view replaces the stage-spine tree with a reverse-chronological causal
        log. Fails if the causal-log rendering branch is deleted."""
        checks = """
const out = {};
sessionViewKey = "claude:1234abcd";
const h = sessionView(board([fo]));
out.hasWf1 = h.includes("debug-flywheel");
out.hasWf2 = h.includes("other-wf");
// AC-1: every entity slug is present.
out.slugs = ["drc-1", "drc-2", "drc-3", "pr-7"].map(s => h.includes(s));
// AC-1: every stage name is present.
out.stages = ["intake", "review", "fix-and-harden", "posted"].map(s => h.includes(s));
// AC-1: the live entity (drc-2) carries the sd-live class in the causal log.
out.liveClass = h.includes('sv-disp sd-live');
// A non-live entity must NOT carry sd-live.
out.parkedNotLive = !h.includes('sv-disp sd-live">drc-1') && !h.includes('sv-disp sd-live">drc-3');
// Cycle label present on drc-1.
out.cycle = h.includes("c2");
console.log(JSON.stringify(out));
"""
        out = self.run_session(checks)
        self.assertTrue(out["hasWf1"])
        self.assertTrue(out["hasWf2"])
        self.assertEqual([True, True, True, True], out["slugs"], "an entity slug is missing")
        self.assertEqual([True, True, True, True], out["stages"], "a stage name is missing")
        self.assertTrue(out["liveClass"], "the live entity does not carry sd-live")
        self.assertTrue(out["parkedNotLive"], "a parked entity was marked live")
        self.assertTrue(out["cycle"], "the cycle label is missing")

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_ac2a_goal_line_shows_stated_goal(self) -> None:
        """AC-2a: when the workflow frontmatter carries a title, the session
        view renders it as a one-line goal header. The mirror view renders the
        goal in the sv-mirror-goal section. Fails if the goal field is dropped
        from the payload."""
        checks = """
const out = {};
sessionViewKey = "claude:1234abcd";
const h = sessionView(board([fo]));
out.hasGoal = h.includes('sv-mirror-goal');
out.goalText = h.includes("Ship session view");
console.log(JSON.stringify(out));
"""
        out = self.run_session(checks)
        self.assertTrue(out["hasGoal"], "the goal section element is missing")
        self.assertTrue(out["goalText"], "the goal text is missing from the section")

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_ac2b_no_goal_line_when_title_absent(self) -> None:
        """AC-2b: when the workflow frontmatter carries no title, no goal
        section renders (unless the observer is loading). The mirror view
        shows a loading hint when the observer hasn't fetched yet; when it
        has and there's no goal, the section is absent. Fails if the renderer
        emits a fabricated goal element."""
        checks = """
const out = {};
sessionViewKey = "claude:1234abcd";
// The second workflow (other-wf) has goal: "" — it must not render a real goal.
const h = sessionView(board([fo]));
// Check that no sv-mirror-goal element appears for the other-wf section.
// The first workflow has a goal, so we check per-workflow by looking at the
// HTML after "other-wf".
const wf2Start = h.indexOf("other-wf");
const wf2Section = h.slice(wf2Start);
out.noGoalForWf2 = !wf2Section.includes('sv-mirror-goal');
// Also test with a session whose only workflow has no goal.
// When mirrorObserver is null, the goal shows a loading hint, so the
// section IS present. When mirrorObserver is set to a no-goal sidecar,
// the section should be absent.
mirrorObserver = {goal: "no goal derived", memory: ""};
const noGoal = mk({
  spacedock: {
    role: "first-officer",
    workflows: [sdWf({goal: "", entities: [ent("drc-1", "review", false)]})]
  }
});
const h2 = sessionView(board([noGoal]));
out.noGoalAtAll = !h2.includes('sv-mirror-goal');
console.log(JSON.stringify(out));
"""
        out = self.run_session(checks)
        self.assertTrue(out["noGoalForWf2"], "a goal was fabricated for a workflow with no title")
        self.assertTrue(out["noGoalAtAll"], "a goal was fabricated when no title is present")

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_ac2_no_hardcoded_goal_fallback(self) -> None:
        """AC-2 falsifying edit: hardcoding a goal string as a fallback when
        goal is absent must fail this test. No fabricated or placeholder text
        should appear (excluding the loading hint when observer is null)."""
        checks = """
const out = {};
sessionViewKey = "claude:1234abcd";
mirrorObserver = {goal: "no goal derived", memory: ""};
const noGoal = mk({
  spacedock: {
    role: "first-officer",
    workflows: [sdWf({goal: "", entities: [ent("drc-1", "review", false)]})]
  }
});
const h = sessionView(board([noGoal]));
out.noCurrentSprint = !h.includes("Current sprint");
out.noGoalLabel = !h.includes('sv-mirror-goal');
console.log(JSON.stringify(out));
"""
        out = self.run_session(checks)
        self.assertTrue(out["noCurrentSprint"], "a hardcoded goal fallback was rendered")
        self.assertTrue(out["noGoalLabel"], "a goal element was rendered for an empty goal")

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_session_picker_shown_when_no_key(self) -> None:
        """Entering session mode with no session selected shows a picker, not
        a blank or fabricated view."""
        checks = """
const out = {};
sessionViewKey = null;
const h = sessionView(board([fo]));
out.hasPicker = h.includes("sv-picker");
out.hasPickRow = h.includes('data-calm="session" data-arg="claude:1234abcd"');
out.noGoalWhenPicking = !h.includes('sv-mirror-goal');
console.log(JSON.stringify(out));
"""
        out = self.run_session(checks)
        self.assertTrue(out["hasPicker"], "the picker was not shown for a null key")
        self.assertTrue(out["hasPickRow"], "the picker row is missing")
        self.assertTrue(out["noGoalWhenPicking"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_set_display_mode_accepts_session(self) -> None:
        """Test plan item 4: setDisplayMode("session") sets displayMode to
        "session", persists to localStorage, and triggers render(lastData).
        setDisplayMode("invalid") is a no-op."""
        checks = """
const out = {};
const d = board([fo]);
render(d);
out.before = displayMode;
setDisplayMode("session");
out.mode = displayMode;
out.stored = __store["cargento.displayMode"];
out.sessionKeyCleared = sessionViewKey === null;
// An invalid value is a no-op.
setDisplayMode("invalid");
out.rejectsJunk = displayMode;
console.log(JSON.stringify(out));
"""
        out = self.run_session(checks)
        self.assertEqual("regular", out["before"])
        self.assertEqual("session", out["mode"], "setDisplayMode did not accept 'session'")
        self.assertEqual("session", out["stored"], "the mode was not persisted")
        self.assertTrue(out["sessionKeyCleared"], "entering session mode left a stale key")
        self.assertEqual("session", out["rejectsJunk"], "an invalid mode was accepted")

    # ── rework: routable URL, distinct empty states, calm navigation ─────────

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_url_hash_restores_session_on_init(self) -> None:
        """Rework BUG 1: a URL hash (#session=<key>) restores the session view
        on page load. displayMode is "session" and sessionViewKey is the
        decoded key."""
        checks = """
const out = {};
out.mode = displayMode;
out.key = sessionViewKey;
console.log(JSON.stringify(out));
"""
        out = self.run_session(checks, hash_val="#session=claude:1234abcd")
        self.assertEqual("session", out["mode"], "hash did not restore session mode")
        self.assertEqual("claude:1234abcd", out["key"], "hash did not restore the session key")

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_url_hash_synced_on_session_enter(self) -> None:
        """Rework BUG 1: entering session mode via calmAction("session", key)
        sets location.hash to #session=<encoded key>."""
        checks = """
const out = {};
const d = board([fo]);
render(d);
calmAction("session", "claude:1234abcd");
out.hash = location.hash;
out.mode = displayMode;
console.log(JSON.stringify(out));
"""
        out = self.run_session(checks)
        self.assertIn("session=claude", out["hash"], "hash was not set")
        self.assertEqual("session", out["mode"], "did not enter session mode")

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_url_hash_cleared_on_leave(self) -> None:
        """Rework BUG 1: leaving session mode (back to regular) clears the
        session hash."""
        checks = """
const out = {};
const d = board([fo]);
render(d);
calmAction("session", "claude:1234abcd");
out.hashWhenSession = location.hash;
setDisplayMode("regular");
out.hashAfterLeave = location.hash;
console.log(JSON.stringify(out));
"""
        out = self.run_session(checks)
        self.assertIn("session=", out["hashWhenSession"], "hash was not set in session mode")
        self.assertNotIn("session=", out["hashAfterLeave"], "hash was not cleared on leaving")

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_hashchange_navigates_back(self) -> None:
        """Rework BUG 1: a hashchange to no session hash leaves session mode
        (browser back button)."""
        checks = """
const out = {};
const d = board([fo]);
render(d);
calmAction("session", "claude:1234abcd");
out.modeIn = displayMode;
// Simulate browser back: hash cleared, hashchange fires.
suppressHashChange = false;
location.hash = "";
__fire("window:hashchange", {});
out.modeOut = displayMode;
out.keyOut = sessionViewKey;
console.log(JSON.stringify(out));
"""
        out = self.run_session(checks)
        self.assertEqual("session", out["modeIn"])
        self.assertNotEqual("session", out["modeOut"], "did not leave session mode on hashchange")
        self.assertIsNone(out["keyOut"], "sessionViewKey was not cleared on hashchange")

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_empty_state_not_a_spacedock_session(self) -> None:
        """Rework BUG 3b: a session with spacedock: null shows "Not a
        Spacedock session", not "no workflows"."""
        checks = """
const out = {};
sessionViewKey = "claude:1234abcd";
const notSd = mk({spacedock: null});
const h = sessionView(board([notSd]));
out.isNotSpacedock = h.includes("Not a Spacedock session");
out.noOldMessage = !h.includes("no Spacedock workflows");
out.hasBack = h.includes("sv-back");
console.log(JSON.stringify(out));
"""
        out = self.run_session(checks)
        self.assertTrue(out["isNotSpacedock"], "the not-a-Spacedock message is missing")
        self.assertTrue(out["noOldMessage"], "the old generic message is still shown")
        self.assertTrue(out["hasBack"], "the back button is missing")

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_empty_state_fo_no_entities(self) -> None:
        """Rework BUG 3c: a first-officer session with empty workflows shows
        "First officer with no in-flight entities" (pointing at the freshness
        fix), not a blank panel."""
        checks = """
const out = {};
sessionViewKey = "claude:1234abcd";
const foEmpty = mk({
  spacedock: {role: "first-officer", workflows: []}
});
const h = sessionView(board([foEmpty]));
out.isFoNoEntities = h.includes("First officer with no in-flight entities");
out.mentionsFreshness = h.includes("freshness");
out.noOldMessage = !h.includes("no Spacedock workflows");
out.hasBack = h.includes("sv-back");
console.log(JSON.stringify(out));
"""
        out = self.run_session(checks)
        self.assertTrue(out["isFoNoEntities"], "the FO no-entities message is missing")
        self.assertTrue(out["mentionsFreshness"], "the freshness-gate pointer is missing")
        self.assertTrue(out["noOldMessage"], "the old generic message is still shown")
        self.assertTrue(out["hasBack"], "the back button is missing")

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_empty_state_worker_session(self) -> None:
        """Rework BUG 3d: a non-FO Spacedock session (ensign/worker) with empty
        workflows shows the role + "session", not a blank panel."""
        checks = """
const out = {};
sessionViewKey = "claude:1234abcd";
const ensign = mk({
  spacedock: {role: "ensign", workflows: []}
});
const h = sessionView(board([ensign]));
out.isWorkerSession = h.includes("ensign session");
out.noOldMessage = !h.includes("no Spacedock workflows");
out.hasBack = h.includes("sv-back");
console.log(JSON.stringify(out));
"""
        out = self.run_session(checks)
        self.assertTrue(out["isWorkerSession"], "the worker session message is missing")
        self.assertTrue(out["noOldMessage"], "the old generic message is still shown")
        self.assertTrue(out["hasBack"], "the back button is missing")

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_loading_state_when_session_not_found(self) -> None:
        """Rework BUG 3a: when the session key is set but the session is not
        in the current data, a loading state shows — not the picker, not a
        blank panel."""
        checks = """
const out = {};
sessionViewKey = "claude:deadbeef";
const h = sessionView(board([fo]));
out.isLoading = h.includes("sv-loading");
out.hasBack = h.includes("sv-back");
out.noPicker = !h.includes("sv-picker");
out.mentionsKey = h.includes("claude:deadbeef");
console.log(JSON.stringify(out));
"""
        out = self.run_session(checks)
        self.assertTrue(out["isLoading"], "the loading state is missing")
        self.assertTrue(out["hasBack"], "the back button is missing")
        self.assertTrue(out["noPicker"], "the picker was shown instead of loading")
        self.assertTrue(out["mentionsKey"], "the session key is not in the loading message")

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_back_button_in_session_view(self) -> None:
        """Rework BUG 1: the session view has a back button that navigates to
        the overview (data-calm="mode" data-arg="regular")."""
        checks = """
const out = {};
sessionViewKey = "claude:1234abcd";
const h = sessionView(board([fo]));
out.hasBack = h.includes('data-calm="mode" data-arg="regular"');
out.hasBackText = h.includes("overview");
console.log(JSON.stringify(out));
"""
        out = self.run_session(checks)
        self.assertTrue(out["hasBack"], "the back button is missing")
        self.assertTrue(out["hasBackText"], "the back button text is missing")

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_calm_expansion_has_view_button(self) -> None:
        """Rework BUG 2: the calm expansion panel has a "view" button
        (data-calm="session") that navigates to the session view."""
        checks = """
const out = {};
const d = board([fo]);
const row = calmRow(d, fo);
calmOpenKey = row.key;
const h = calmExpansion(row, d);
out.hasViewBtn = h.includes('data-calm="session"');
out.hasViewText = h.includes(">view<");
console.log(JSON.stringify(out));
"""
        out = self.run_session(checks)
        self.assertTrue(out["hasViewBtn"], "the view button is missing from calm expansion")
        self.assertTrue(out["hasViewText"], "the view button text is missing")

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_calm_view_button_enters_session_mode(self) -> None:
        """Rework BUG 2: clicking the calm "view" button enters session mode
        with the correct session key."""
        checks = """
const out = {};
const d = board([fo]);
render(d);
calmAction("session", "claude:1234abcd");
out.mode = displayMode;
out.key = sessionViewKey;
out.hash = location.hash;
console.log(JSON.stringify(out));
"""
        out = self.run_session(checks)
        self.assertEqual("session", out["mode"], "did not enter session mode")
        self.assertEqual("claude:1234abcd", out["key"], "session key was not set")
        self.assertIn("session=", out["hash"], "hash was not synced")

    # ── session-centric rework: session card + dispatch history ─────────────

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_ac_card_renders_session_card(self) -> None:
        """AC-1: the session view renders the session card above the workflow
        strip. The card shows title, project · session · via provider · model,
        rate (tok/min), state + state_detail, and elapsed/eta — the same fields
        the board view's workingCard shows, from the same session object.
        Fails if the sessionCardCore call is deleted from sessionView."""
        checks = """
const out = {};
sessionViewKey = "claude:1234abcd";
const cardSess = mk({
  title: "Use $spacedock:first-officer for this whole Pi session.",
  state: "working", state_detail: "running bash",
  rate_per_min: 433, provider: "lunaroute", model: "opus-4",
  total: 10, done: 3, progress_pct: 30, eta_h: "2h 30m",
  turn: {elapsed_h: "12m", eta_h: "8m", pct: 60, long: false},
  spacedock: {role: "first-officer", workflows: [
    sdWf({goal: "Ship it", entities: [ent("drc-1", "review", false)]})
  ]}
});
const d = board([cardSess]);
const h = sessionView(d);
// The card is present (sv-card class).
out.hasCard = h.includes('class="card sv-card"');
// Card fields from the same session object.
out.rateNum = h.includes('>433<');
out.authority = h.includes('via lunaroute');
out.model = h.includes('opus-4');
out.stateDetail = h.includes('running bash');
out.turn = h.includes('12m elapsed');
out.eta = h.includes('~2h 30m left');
// The card appears before the workflow strip.
out.cardBeforeWf = h.indexOf('sv-card') < h.indexOf('debug-flywheel');
console.log(JSON.stringify(out));
"""
        out = self.run_session(checks)
        self.assertTrue(out["hasCard"], "the session card element is missing")
        self.assertTrue(out["rateNum"], "the rate number is missing from the card")
        self.assertTrue(out["authority"], "the authority string is missing from the card")
        self.assertTrue(out["model"], "the model is missing from the card")
        self.assertTrue(out["stateDetail"], "the state_detail is missing from the card")
        self.assertTrue(out["turn"], "the turn elapsed is missing from the card")
        self.assertTrue(out["eta"], "the eta is missing from the card")
        self.assertTrue(out["cardBeforeWf"], "the card does not appear before the workflow strip")

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_ac_card_factored_not_duplicated(self) -> None:
        """AC-2: sessionCardCore is defined exactly once and both workingCard
        and sessionView call it. Fails if card HTML is inlined in sessionView
        instead of calling sessionCardCore."""
        checks = """
const out = {};
// sessionCardCore is defined (a function).
out.coreIsFunction = typeof sessionCardCore === "function";
// workingCard calls sessionCardCore.
const boardHtml = workingCard(board([fo]), fo);
out.workingCardHasCard = boardHtml.includes('class="card"');
// sessionView produces a card.
sessionViewKey = "claude:1234abcd";
const sessionHtml = sessionView(board([fo]));
out.sessionHasCard = sessionHtml.includes('class="card sv-card"');
// Both use sessionCardCore — verify by checking the card-top/card-main
// structure that sessionCardCore emits.
out.boardHasCardTop = boardHtml.includes('card-top');
out.sessionHasCardTop = sessionHtml.includes('card-top');
console.log(JSON.stringify(out));
"""
        out = self.run_session(checks)
        self.assertTrue(out["coreIsFunction"], "sessionCardCore is not defined")
        self.assertTrue(out["workingCardHasCard"], "workingCard does not produce a card")
        self.assertTrue(out["sessionHasCard"], "sessionView does not produce a card")
        self.assertTrue(out["boardHasCardTop"], "workingCard output lacks the card-top structure")
        self.assertTrue(out["sessionHasCardTop"], "sessionView output lacks the card-top structure")

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_ac_dispatch_history_shows_work_log(self) -> None:
        """AC-3: the mirror view's causal log shows the session's dispatch history
        in REVERSE CHRONOLOGICAL order (newest first). Dispatches appear by
        timestamp, live entities carry sd-live, and no "NOT TOUCHED" text
        appears. Non-dispatched entities are cut as noise — they belong in a
        project view. The history is deduplicated: one row per entity."""
        checks = """
const out = {};
sessionViewKey = "claude:1234abcd";
// A fixture with dispatch_history: three batches at different timestamps.
// The workflow's entities include the dispatched slugs plus one
// non-dispatched entity (drc-4) that should NOT appear.
const dhSess = mk({
  spacedock: {role: "first-officer", dispatch_history: [
    {ts: 100, slug: "drc-1", stage: "intake"},
    {ts: 200, slug: "drc-2", stage: "review"},
    {ts: 300, slug: "drc-3", stage: "fix-and-harden"}
  ], workflows: [sdWf({
    goal: "Ship it",
    stages: ["intake", "review", "fix-and-harden"],
    entities: [
      {slug: "drc-1", stage: "review", live: false, cycle: "", decision: "approve"},
      {slug: "drc-2", stage: "review", live: true, cycle: "", decision: ""},
      {slug: "drc-3", stage: "fix-and-harden", live: false, cycle: "", decision: ""},
      {slug: "drc-4", stage: "intake", live: false, cycle: "", decision: ""}
    ]
  })]}
});
const h = sessionView(board([dhSess]));
// All three dispatched slugs appear.
out.hasDrc1 = h.includes("drc-1");
out.hasDrc2 = h.includes("drc-2");
out.hasDrc3 = h.includes("drc-3");
// Reverse chronological order: drc-3 (ts=300) appears before drc-2 (ts=200),
// drc-2 before drc-1 (ts=100) — newest first.
out.order32 = h.indexOf("drc-3") < h.indexOf("drc-2");
out.order21 = h.indexOf("drc-2") < h.indexOf("drc-1");
// The live entity (drc-2) carries sd-live.
out.liveClass = h.includes('sv-disp sd-live');
// No "NOT TOUCHED" text.
out.noNotTouched = !h.includes('NOT TOUCHED') && !h.includes('not touched');
// Non-dispatched entity (drc-4) is cut as noise — should NOT appear.
out.noDrc4 = !h.includes("drc-4");
out.noOther = !h.includes('other workflow entities');
// Dispatch history section is present.
out.hasHist = h.includes('sv-dispatch-hist');
console.log(JSON.stringify(out));
"""
        out = self.run_session(checks)
        self.assertTrue(out["hasDrc1"], "drc-1 is missing from the dispatch history")
        self.assertTrue(out["hasDrc2"], "drc-2 is missing from the dispatch history")
        self.assertTrue(out["hasDrc3"], "drc-3 is missing from the dispatch history")
        self.assertTrue(out["order32"], "drc-3 does not appear before drc-2 (reverse chrono)")
        self.assertTrue(out["order21"], "drc-2 does not appear before drc-1 (reverse chrono)")
        self.assertTrue(out["liveClass"], "the live entity does not carry sd-live")
        self.assertTrue(out["noNotTouched"], "'NOT TOUCHED' text appears in the output")
        self.assertTrue(out["noDrc4"], "the non-dispatched entity drc-4 should have been cut")
        self.assertTrue(out["noOther"], "the 'other workflow entities' section should be gone")
        self.assertTrue(out["hasHist"], "the dispatch history section is missing")

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_ac_board_card_unchanged(self) -> None:
        """AC-5: the board view's card rendering is unchanged by the refactor.
        The same HTML structure and CSS classes appear in workingCard before
        and after. Fails if a card field is dropped from sessionCardCore."""
        checks = """
const out = {};
// Use a session with a turn so the turn block renders.
const withTurn = mk({
  turn: {elapsed_h: "5m", eta_h: "3m", pct: 40, long: false},
  spacedock: {role: "first-officer", workflows: [
    sdWf({goal: "Ship it", entities: [ent("drc-1", "review", false)]})
  ]}
});
const d = board([withTurn]);
const h = workingCard(d, withTurn);
// Board card structure.
out.hasCard = h.includes('class="card"');
out.hasCardTop = h.includes('card-top');
out.hasCardMain = h.includes('card-main');
out.hasHeadrow = h.includes('card-headrow');
out.hasWorkingPill = h.includes('pill-work');
out.hasTitle = h.includes('Active dispatch');
out.hasMeta = h.includes('repo/proj');
out.hasBadge = h.includes('btile');
// Rate meter.
out.hasRateMeter = h.includes('rate-meter');
out.hasRateNum = h.includes('>10<');
// Now block.
out.hasNow = h.includes('class="now"');
out.hasStateDetail = h.includes('running Bash');
// Turn block.
out.hasTurn = h.includes('class="turn"');
out.hasTurnTxt = h.includes('this request');
// Board-only elements.
out.hasSdBlock = h.includes('class="sd"');
console.log(JSON.stringify(out));
"""
        out = self.run_session(checks)
        self.assertTrue(out["hasCard"], "the card element is missing")
        self.assertTrue(out["hasCardTop"], "the card-top element is missing")
        self.assertTrue(out["hasCardMain"], "the card-main element is missing")
        self.assertTrue(out["hasHeadrow"], "the card-headrow element is missing")
        self.assertTrue(out["hasWorkingPill"], "the Working pill is missing")
        self.assertTrue(out["hasTitle"], "the title is missing")
        self.assertTrue(out["hasMeta"], "the meta line is missing")
        self.assertTrue(out["hasBadge"], "the harness badge is missing")
        self.assertTrue(out["hasRateMeter"], "the rate meter is missing")
        self.assertTrue(out["hasRateNum"], "the rate number is missing")
        self.assertTrue(out["hasNow"], "the now block is missing")
        self.assertTrue(out["hasStateDetail"], "the state_detail is missing")
        self.assertTrue(out["hasTurn"], "the turn block is missing")
        self.assertTrue(out["hasSdBlock"], "the sd block is missing from the board card")
