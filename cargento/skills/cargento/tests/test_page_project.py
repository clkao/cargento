"""The shipped project cockpit over live session and ask payloads."""

from __future__ import annotations

import json
import shutil
import unittest
from typing import Any
from urllib.parse import quote, urlencode

from . import test_page_calm
from .page_harness import PageJsHarness


class ProjectCockpitTest(PageJsHarness):
    FIXTURE = (
        test_page_calm.CalmModeTest.FIXTURE
        + """
const projectBoard = asks => Object.assign(board(), {ask: true, asks: asks || []});
const liveAsk = o => Object.assign({id: "ask-live", harness: "claude",
  session_id: "aaa1", project: "repo/proj", question: "Choose the release path?",
  options: ["safe", "fast"], age_sec: 12}, o || {});
"""
    )

    @staticmethod
    def prelude(
        *,
        project: str = "repo/proj",
        goal: str | None = None,
        goals: dict[str, str] | None = None,
        query_project: str | None = None,
        query_session: str | None = None,
        stored_mode: str | None = "project",
    ) -> str:
        values = {"cargento.projectCockpitProject": project}
        if stored_mode is not None:
            values["cargento.displayMode"] = stored_mode
        seeded_goals = dict(goals or {})
        if goal is not None:
            seeded_goals[project] = goal
        for label, value in seeded_goals.items():
            values[f"cargento.projectGoal.v1:{quote(label, safe='')}"] = value
        query_items = [("mode", "project")]
        if query_project:
            query_items.append(("project", query_project))
        if query_session:
            query_items.append(("session", query_session))
        query = "?" + urlencode(query_items)
        return f"""
let __store = {json.dumps(values)};
const localStorage = {{
  getItem(k){{ return Object.prototype.hasOwnProperty.call(__store, k) ? __store[k] : null; }},
  setItem(k, v){{ __store[k] = String(v); }},
  removeItem(k){{ delete __store[k]; }}
}};
location.search = {json.dumps(query)};
location.href = "http://127.0.0.1:8766/" + location.search + location.hash;
let __historyUrls = [];
const history = {{
  pushState(_s, _t, u){{ __historyUrls.push(String(u)); const x = new URL(String(u), location.href);
    location.href = x.toString(); location.search = x.search; location.hash = x.hash; }},
  replaceState(_s, _t, u){{ this.pushState(_s, _t, u); }}
}};
let __links = [];
const navigator = {{clipboard: {{writeText(s){{ __links.push(String(s)); return Promise.resolve(); }}}}}};
let __timers = [];
const setTimeout = fn => {{ __timers.push(fn); return __timers.length; }};
"""

    def run_project(
        self,
        checks: str,
        *,
        project: str = "repo/proj",
        goal: str | None = None,
        goals: dict[str, str] | None = None,
        query_project: str | None = None,
        query_session: str | None = None,
        stored_mode: str | None = "project",
    ) -> Any:
        return self._run_page_js(
            self.FIXTURE + checks,
            prelude=self.prelude(
                project=project,
                goal=goal,
                goals=goals,
                query_project=query_project,
                query_session=query_session,
                stored_mode=stored_mode,
            ),
        )

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_cold_permalink_route_overrides_browser_fallback(self) -> None:
        checks = """
const d = payload([
  mk({project: "repo/proj", harness: "codex", sid: "focus-1", active: true}),
  mk({project: "repo/proj", harness: "claude", sid: "around-1", active: true})
]);
Object.assign(d, {ask: true, asks: []});
render(d);
const cold = __els.app.innerHTML;
projectAction("project-session-focus", "claude:around-1");
const focused = __els.app.innerHTML;
const pushed = __historyUrls[__historyUrls.length - 1] || "";
location.search = "?mode=project&project=repo%2Fproj&session=codex%3Afocus-1";
(__listeners["window:popstate"] || []).forEach(fn => fn({}));
const returned = __els.app.innerHTML;
console.log(JSON.stringify({
  coldMode: displayMode,
  coldFocus: cold.includes('data-session-mirror="codex:focus-1"'),
  siblingStayedProject: focused.includes('data-session-mirror="claude:around-1"') &&
    displayMode === "project",
  pushed,
  backReturned: returned.includes('data-session-mirror="codex:focus-1"')
}));
"""
        out = self.run_project(
            checks,
            query_project="repo/proj",
            query_session="codex:focus-1",
            stored_mode="regular",
        )
        self.assertEqual("project", out["coldMode"])
        self.assertTrue(out["coldFocus"])
        self.assertTrue(out["siblingStayedProject"])
        self.assertIn("mode=project", out["pushed"])
        self.assertIn("project=repo%2Fproj", out["pushed"])
        self.assertIn("session=claude%3Aaround-1", out["pushed"])
        self.assertTrue(out["backReturned"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_project_temporal_labels_separate_now_from_recent(self) -> None:
        checks = """
const d = payload([
  mk({project: "repo/proj", harness: "codex", sid: "focus-1", active: true,
    state: "working"}),
  mk({project: "repo/proj", harness: "claude", sid: "work-1", active: true,
    state: "working"}),
  mk({project: "repo/proj", harness: "pi", sid: "idle-1", active: true,
    state: "idle"})
]);
Object.assign(d, {ask: true, asks: []});
render(d);
const h = __els.app.innerHTML;
console.log(JSON.stringify({
  recentCount: h.includes("3</b> recent"),
  workingSection: h.includes("Working now") && h.includes("claude:work-1"),
  recentIdleSection: h.includes("Recent · idle") && h.includes("pi:idle-1"),
  noActiveClaim: !h.includes("</b> active") && !h.includes("other active sessions")
}));
"""
        out = self.run_project(
            checks,
            query_project="repo/proj",
            query_session="codex:focus-1",
        )
        self.assertTrue(out["recentCount"])
        self.assertTrue(out["workingSection"])
        self.assertTrue(out["recentIdleSection"])
        self.assertTrue(out["noActiveClaim"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_project_feedback_is_live_and_refresh_keeps_keyboard_focus(self) -> None:
        checks = """
__fetchImpl = () => Promise.resolve({ok: true, json: () => Promise.resolve({
  observers: [], events: [], sources: {gate: {}, steer: {unavailable: []}}
})});
lastData = projectBoard();
render(lastData);
await __settle(); await __settle();
const refresh = __controls().find(c => c.getAttribute("data-calm") === "project-context-refresh");
document.activeElement = refresh;
__focused = null;
projectAction("project-context-refresh", "repo/proj");
const busyHtml = __els.app.innerHTML;
await __settle(); await __settle();
const settled = __els.app.innerHTML;
console.log(JSON.stringify({
  busy: busyHtml.includes("refreshing context…") && busyHtml.includes('aria-busy="true"'),
  focus: __focused === "project-context-refresh:repo/proj",
  live: settled.includes('role="status"') && settled.includes('aria-live="polite"') &&
    settled.includes("context refreshed")
}));
"""
        out = self.run_project(checks)
        self.assertTrue(out["busy"])
        self.assertTrue(out["focus"])
        self.assertTrue(out["live"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_compact_navigation_leads_into_one_selected_project_boundary(self) -> None:
        checks = """
render(projectBoard());
const h = __els.app.innerHTML;
console.log(JSON.stringify({
  mode: displayMode,
  className: __els.app.className,
  compactNav: h.includes('id="pc-project-select"') && h.includes('class="pc-link"') &&
    !h.includes('class="pc-project'),
  chosen: h.includes("Working toward</span><h2>repo/proj</h2>"),
  active: h.includes("1</b> recent"),
  empty: h.includes("No session in this project is asking through Cargento."),
  identity: h.includes("claude:aaa1"),
  goalFirst: h.indexOf("Operator goal") < h.indexOf("Observer context"),
  mirrorDrilldown: h.includes('data-calm="project-session-focus" data-arg="claude:aaa1"'),
  secondary: h.indexOf("Source and identity details") > h.indexOf("Surrounding sessions")
}));
"""
        out = self.run_project(checks)
        self.assertEqual("project", out["mode"])
        self.assertEqual("wrap project", out["className"])
        self.assertTrue(out["compactNav"])
        self.assertTrue(out["chosen"])
        self.assertTrue(out["active"])
        self.assertTrue(out["empty"])
        self.assertTrue(out["identity"])
        self.assertTrue(out["goalFirst"])
        self.assertTrue(out["mirrorDrilldown"])
        self.assertTrue(out["secondary"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_real_observer_context_stays_subordinate_to_operator_goal(self) -> None:
        checks = """
projectContextByLabel["repo/proj"] = {state: "ready", generated: 100000, data: {
  observers: [{harness: "claude", sid: "aaa1", goal: "Derived session goal",
    stage: "shaping", block: "waiting for captain"}], events: [],
  sources: {gate: {}, steer: {unavailable: []}}
}};
render(projectBoard());
const h = __els.app.innerHTML;
console.log(JSON.stringify({
  operator: h.includes("Operator note <em>remembered in this browser · precedes inference</em>"),
  observed: h.includes("Derived session goal"),
  scoped: h.includes("derived, subordinate") && h.includes("claude:aaa1"),
  separate: h.indexOf("Operator goal") < h.indexOf("Derived session goal"),
  noOverwrite: h.includes("observer inference never overwrites this note")
}));
"""
        out = self.run_project(checks, goal="Operator-owned goal")
        self.assertTrue(out["operator"])
        self.assertTrue(out["observed"])
        self.assertTrue(out["scoped"])
        self.assertTrue(out["separate"])
        self.assertTrue(out["noOverwrite"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_session_permalink_focuses_one_primary_mirror_inside_the_project(self) -> None:
        checks = """
const d = payload([
  mk({project: "repo/proj", harness: "codex", sid: "focus-1", active: true,
    state: "working", state_detail: "running exec", model: "gpt-5.6-sol", subagents: []}),
  mk({project: "repo/proj", harness: "claude", sid: "around-1", active: true})
]);
Object.assign(d, {ask: true, asks: []});
render(d);
const h = __els.app.innerHTML;
console.log(JSON.stringify({
  mirror: h.includes('data-session-mirror="codex:focus-1"') && h.includes("running exec"),
  identity: h.includes("codex:focus-1") && h.includes("project · repo/proj"),
  hierarchy: h.indexOf("Operator goal") < h.indexOf("Primary session mirror"),
  surrounding: h.includes("Surrounding sessions") && h.includes("claude:around-1"),
  noDuplicate: !h.slice(h.indexOf("Surrounding sessions"),
    h.indexOf("Gate and steering history")).includes("codex:focus-1"),
  observerScoped: __fetchCalls.some(call => call[0].includes("session=codex%3Afocus-1"))
}));
"""
        out = self.run_project(
            checks,
            query_project="repo/proj",
            query_session="codex:focus-1",
        )
        self.assertTrue(out["mirror"])
        self.assertTrue(out["identity"])
        self.assertTrue(out["hierarchy"])
        self.assertTrue(out["surrounding"])
        self.assertTrue(out["noDuplicate"])
        self.assertTrue(out["observerScoped"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_focused_mirror_distinguishes_no_signal_from_unblocked(self) -> None:
        checks = """
const d = payload([
  mk({project: "repo/proj", harness: "codex", sid: "focus-1", active: true,
    state: "working", needs_you: null}),
  mk({project: "repo/proj", harness: "claude", sid: "around-1", active: true})
]);
Object.assign(d, {ask: true, asks: [liveAsk({session_id: "around-1"})]});
render(d);
const clear = __els.app.innerHTML;
d.asks = [liveAsk({harness: "codex", session_id: "focus-1"})];
render(d);
const asked = __els.app.innerHTML;
console.log(JSON.stringify({
  clear: clear.includes("Needs captain") && clear.includes("No live needs-captain signal") &&
    clear.includes("not proof that the session is unblocked") &&
    clear.includes('data-needs-captain="clear"'),
  exactOnly: !clear.includes("Attention requested") && asked.includes("Attention requested") &&
    asked.includes("1 live registered question") &&
    asked.includes('data-needs-captain="requested"'),
  source: asked.includes("session overlay + AskRegistry")
}));
"""
        out = self.run_project(
            checks,
            query_project="repo/proj",
            query_session="codex:focus-1",
        )
        self.assertTrue(out["clear"])
        self.assertTrue(out["exactOnly"])
        self.assertTrue(out["source"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_focused_right_now_unifies_live_and_derived_truth(self) -> None:
        checks = """
projectContextByLabel["repo/proj"] = {state: "ready", generated: 100000, data: {
  observers: [{harness: "codex", sid: "focus-1", goal: "Shape the focused mirror",
    stage: null, block: null, model: {model: "gpt-5.6-luna", reasoning_effort: "max",
      status: "used"}}],
  events: [{at: 99990, kind: "steer", phase: "captain instruction",
    title: "Keep the project as context", detail: "codex:focus-1",
    source: "transcript user message", harness: "codex", sid: "focus-1"}],
  sources: {scope: "focused session", gate: {}, steer: {live: 1, unavailable: []}}
}};
const d = payload([mk({project: "repo/proj", harness: "codex", sid: "focus-1",
  active: true, state: "working", state_detail: "running exec", needs_you: null})]);
Object.assign(d, {ask: true, asks: []});
render(d);
const h = __els.app.innerHTML;
console.log(JSON.stringify({
  hierarchy: h.indexOf("Operator goal") < h.indexOf("Primary session mirror") &&
    h.indexOf("Primary session mirror") < h.indexOf("Right now") &&
    h.indexOf("Right now") < h.indexOf("Shape the focused mirror"),
  motion: h.includes("working") && h.includes("running exec"),
  purpose: h.includes("Shape the focused mirror") && h.includes("gpt-5.6-luna") &&
    h.includes("reasoning max"),
  workflowBoundary: h.includes("workflow stage unavailable") &&
    h.includes("open-block reading unavailable"),
  attention: h.includes("No live needs-captain signal"),
  steering: h.includes("Most recent user-role message") && h.includes("Keep the project as context") &&
    h.includes("transcript user message") && h.includes("1970-01-02T03:46:30.000Z"),
  identity: h.includes("codex:focus-1"),
  operatorPrecedence: h.includes("observer inference never overwrites this note")
}));
"""
        out = self.run_project(
            checks,
            goal="Operator-owned outcome",
            query_project="repo/proj",
            query_session="codex:focus-1",
        )
        self.assertTrue(out["hierarchy"])
        self.assertTrue(out["motion"])
        self.assertTrue(out["purpose"])
        self.assertTrue(out["workflowBoundary"])
        self.assertTrue(out["attention"])
        self.assertTrue(out["steering"])
        self.assertTrue(out["identity"])
        self.assertTrue(out["operatorPrecedence"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_activity_reuses_causal_log_shape_without_mocked_history(self) -> None:
        checks = """
projectContextByLabel["repo/proj"] = {state: "ready", generated: 100000, data: {
  observers: [], events: [
    {at: 99990, kind: "steer", phase: "captain instruction", title: "Prepare release path",
      detail: "claude:aaa1", source: "transcript user message"},
    {at: 99980, kind: "gate", phase: "gate decision · application consumed",
      title: "project-cockpit · shaping · approve", detail: "explore · claude:aaa1",
      source: "Spacedock entity gate frontmatter"}
  ], sources: {gate: {live: 1, untimestamped_prepare: 2, status_history: "unavailable"},
    steer: {live: 1, unavailable: []}}
}};
render(projectBoard());
const h = __els.app.innerHTML;
console.log(JSON.stringify({
  graph: h.includes('class="pc-log"') && h.includes('class="pc-event-node"'),
  instruction: h.includes("captain instruction") && h.includes("transcript user message"),
  decision: h.includes("application consumed") && h.includes("shaping · approve"),
  boundary: h.includes("2 gate preparations lack timestamps") &&
    h.includes("status-transition history unavailable"),
  noMockTags: !h.includes("generated</span>") && !h.includes("consistency")
}));
"""
        out = self.run_project(checks)
        self.assertTrue(out["graph"])
        self.assertTrue(out["instruction"])
        self.assertTrue(out["decision"])
        self.assertTrue(out["boundary"])
        self.assertTrue(out["noMockTags"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_only_real_registry_asks_enter_the_selected_project(self) -> None:
        checks = """
const empty = projectBoard();
render(empty);
const before = __els.app.innerHTML;
const asked = projectBoard([liveAsk()]);
render(asked);
const after = __els.app.innerHTML;
console.log(JSON.stringify({
  absentBefore: !before.includes("Choose the release path?"),
  presentAfter: after.includes("Choose the release path?"),
  options: after.includes(">safe</button>") && after.includes(">fast</button>"),
  boundary: after.includes("project and session attribution are caller-supplied")
}));
"""
        out = self.run_project(checks)
        self.assertTrue(out["absentBefore"])
        self.assertTrue(out["presentAfter"])
        self.assertTrue(out["options"])
        self.assertTrue(out["boundary"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_agent_written_project_and_session_fields_are_escaped(self) -> None:
        checks = """
const d = payload([mk({project: '<img src=x onerror="boom">',
  harness: 'codex" data-calm="stop', sid: "sid<em>owned</em>", active: true})]);
Object.assign(d, {ask: true, asks: []});
projectCockpitLabel = '<img src=x onerror="boom">';
projectQueryLabel = projectCockpitLabel;
render(d);
const h = __els.app.innerHTML;
console.log(JSON.stringify({
  rawImage: h.includes("<img"),
  rawEm: h.includes("<em>owned"),
  escapedProject: h.includes("&lt;img src=x onerror=&quot;boom&quot;&gt;"),
  escapedSession: h.includes("sid&lt;em&gt;owned&lt;/em&gt;")
}));
"""
        out = self.run_project(checks)
        self.assertFalse(out["rawImage"])
        self.assertFalse(out["rawEm"])
        self.assertTrue(out["escapedProject"])
        self.assertTrue(out["escapedSession"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_browser_goal_saves_under_the_provisional_label_key_and_reloads(self) -> None:
        checks = """
__els["pc-goal"] = {value: "Ship the smallest useful cockpit", focus(){}};
projectGoalAction("project-goal-save", "repo/proj");
const key = projectGoalKey("repo/proj");
const saved = __store[key];
render(projectBoard());
const shown = __els.app.innerHTML.includes("Ship the smallest useful cockpit");
projectGoalAction("project-goal-clear", "repo/proj");
console.log(JSON.stringify({key, saved, shown, cleared: !(key in __store)}));
"""
        out = self.run_project(checks)
        self.assertEqual("cargento.projectGoal.v1:repo%2Fproj", out["key"])
        self.assertEqual("Ship the smallest useful cockpit", out["saved"])
        self.assertTrue(out["shown"])
        self.assertTrue(out["cleared"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_live_refresh_preserves_a_focused_unsaved_goal_draft(self) -> None:
        checks = """
const field = {value: "draft not saved yet", focus(){},
  getAttribute(k){ return k === "data-project" ? "repo/proj" : null; },
  setSelectionRange(){ this.restored = true; }};
__els["pc-goal"] = field;
document.activeElement = field;
render(projectBoard());
console.log(JSON.stringify({
  draft: __els.app.innerHTML.includes("draft not saved yet"),
  restored: field.restored === true,
  notStored: !(projectGoalKey("repo/proj") in __store)
}));
"""
        out = self.run_project(checks)
        self.assertTrue(out["draft"])
        self.assertTrue(out["restored"])
        self.assertTrue(out["notStored"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_project_goals_stay_distinct_across_switching_and_permalink_reload(self) -> None:
        checks = """
render(projectBoard());
const first = __els.app.innerHTML;
setProjectCockpit("repo/other");
const second = __els.app.innerHTML;
projectQueryLabel = "repo/proj";
render(projectBoard());
const returned = __els.app.innerHTML;
console.log(JSON.stringify({
  first: first.includes("Goal for project A") && !first.includes("Goal for project B"),
  second: second.includes("Goal for project B") && !second.includes("Goal for project A"),
  returned: returned.includes("Goal for project A") && !returned.includes("Goal for project B"),
  routed: __historyUrls.some(u => u.includes("mode=project") && u.includes("project=repo%2Fother"))
}));
"""
        goals = {"repo/proj": "Goal for project A", "repo/other": "Goal for project B"}
        out = self.run_project(checks, goals=goals, query_project="repo/proj")
        self.assertTrue(out["first"])
        self.assertTrue(out["second"])
        self.assertTrue(out["returned"])
        self.assertTrue(out["routed"])

        reloaded = self.run_project(
            """
render(projectBoard());
const h = __els.app.innerHTML;
console.log(JSON.stringify({chosen: h.includes("Working toward</span><h2>repo/other</h2>"),
  goal: h.includes("Goal for project B"), noLeak: !h.includes("Goal for project A")}));
""",
            goals=goals,
            query_project="repo/other",
        )
        self.assertTrue(reloaded["chosen"])
        self.assertTrue(reloaded["goal"])
        self.assertTrue(reloaded["noLeak"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_direct_permalink_selects_project_and_copy_preserves_other_query_state(self) -> None:
        checks = """
render(projectBoard());
projectGoalAction("project-link-copy", "repo/other");
await __settle();
console.log(JSON.stringify({
  selected: __els.app.innerHTML.includes("Working toward</span><h2>repo/other</h2>"),
  copied: __links[0],
  note: __els.app.innerHTML.includes("project link copied")
}));
"""
        out = self.run_project(checks, query_project="repo/other")
        self.assertTrue(out["selected"])
        self.assertIn("mode=project", out["copied"])
        self.assertIn("project=repo%2Fother", out["copied"])
        self.assertTrue(out["note"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_observer_runs_on_selection_and_only_repeats_for_explicit_refresh(self) -> None:
        checks = """
__fetchImpl = () => Promise.resolve({ok: true, json: () => Promise.resolve({
  observers: [], events: [], sources: {gate: {}, steer: {unavailable: []}}
})});
lastData = projectBoard();
render(lastData);
await __settle(); await __settle();
render(lastData);
projectAction("project-context-refresh", "repo/proj");
await __settle(); await __settle();
console.log(JSON.stringify({
  calls: __fetchCalls.map(call => call[0]).filter(url => url.includes("/api/project-context")),
  refreshControl: __els.app.innerHTML.includes('data-calm="project-context-refresh"')
}));
"""
        out = self.run_project(checks)
        self.assertEqual(2, len(out["calls"]))
        self.assertNotIn("refresh=1", out["calls"][0])
        self.assertIn("refresh=1", out["calls"][1])
        self.assertTrue(out["refreshControl"])


if __name__ == "__main__":
    unittest.main()
