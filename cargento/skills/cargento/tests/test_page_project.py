"""The shipped project cockpit over live session and ask payloads."""

from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
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
  recentIdleSection: h.includes("Recent and idle") && h.includes("pi:idle-1"),
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
        out = self.run_project(checks, query_project="repo/proj", query_session="claude:aaa1")
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
  chosen: h.includes("Project context</span><h2>repo/proj</h2>"),
  active: h.includes("1</b> recent"),
  identity: h.includes("claude:aaa1"),
  goalFirst: h.indexOf("add focus") < h.indexOf("Work & steering") &&
    !h.includes("Observed goal") && !h.includes("Goal · derived"),
  mirrorDrilldown: h.includes('data-calm="project-session-focus" data-arg="claude:aaa1"'),
  secondary: h.indexOf("Evidence / limits") > h.indexOf("Other project sessions")
}));
"""
        out = self.run_project(checks)
        self.assertEqual("project", out["mode"])
        self.assertEqual("wrap project", out["className"])
        self.assertTrue(out["compactNav"])
        self.assertTrue(out["chosen"])
        self.assertTrue(out["active"])
        self.assertTrue(out["identity"])
        self.assertTrue(out["goalFirst"])
        self.assertTrue(out["mirrorDrilldown"])
        self.assertTrue(out["secondary"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_real_observer_context_stays_subordinate_to_operator_goal(self) -> None:
        checks = """
projectContextByLabel["repo/proj"] = {state: "ready", generated: 100000, data: {
  observers: [{harness: "claude", sid: "aaa1", goal: "Derived session goal",
    stage: "shaping", block: "waiting for captain", observed_at: 99990,
    snapshot_status: "cached-stale", source: "bounded transcript and entity state"}], events: [], semantic: {
    facts: [{fact_id: "observer-1", at: 99990, type: "observer_snapshot",
      summary: "Derived session goal", work_item_id: null,
      evidence: {source: "cached observer snapshot", confidence: "derived"}}],
    work_items: [], relations: [], projections: {operator_intents: [], trail_heads: [],
      steering_episodes: [], candidate_goal_shifts: []}},
  sources: {gate: {}, steer: {unavailable: []}}
}};
render(projectBoard());
const h = __els.app.innerHTML;
console.log(JSON.stringify({
  operator: h.includes("<b>Focus</b> — Operator-owned goal"),
  observed: h.includes("Derived session goal"),
  scoped: h.includes("Derived snapshot") && h.includes("cached observer snapshot"),
  separate: h.indexOf("<b>Focus</b>") < h.indexOf("Observed goal · stale</b> — Derived session goal"),
  noOverwrite: h.includes("Browser focus is operator-authored"),
  once: h.split("Derived session goal").length - 1 === 2 &&
    !h.includes('class="pc-observer"') && !h.includes("Goal · derived")
}));
"""
        out = self.run_project(checks, goal="Operator-owned goal")
        self.assertTrue(out["operator"])
        self.assertTrue(out["observed"])
        self.assertTrue(out["scoped"])
        self.assertTrue(out["separate"])
        self.assertTrue(out["noOverwrite"])
        self.assertTrue(out["once"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_observed_goal_and_operator_focus_have_distinct_ownership(self) -> None:
        checks = """
projectContextByLabel["repo/proj"] = {state: "ready", generated: 100000, data: {
  observers: [{harness: "codex", sid: "focus-1", goal: "Keep the exact work visible",
    observed_at: 99990, source: "bounded transcript and entity state"}],
  events: [], semantic: {facts: [], work_items: [], relations: [], projections: {
    operator_intents: [], trail_heads: [], steering_episodes: [], candidate_goal_shifts: []}},
  sources: {gate: {}, steer: {unavailable: []}}
}};
render(projectBoard());
const h = __els.app.innerHTML;
const primary = h.slice(0, h.indexOf("Evidence / limits"));
console.log(JSON.stringify({
  oneLine: primary.split("Observed goal").length - 1 === 1 &&
    primary.includes("Observed goal</b> — Keep the exact work visible"),
  sourceLabel: !primary.includes("Goal · derived") && !primary.includes("<b>Focus</b>") &&
    primary.includes("Observed goal"),
  placed: primary.indexOf("Observed goal") < primary.indexOf("Right now"),
  hiddenEditor: !primary.includes('<textarea id="pc-goal"') &&
    primary.includes('>add focus</button>'),
  compact: !primary.includes("Operator note <em>") && !primary.includes("not available")
}));
"""
        out = self.run_project(checks, query_session="claude:aaa1")
        self.assertTrue(out["oneLine"])
        self.assertTrue(out["sourceLabel"])
        self.assertTrue(out["placed"])
        self.assertTrue(out["hiddenEditor"])
        self.assertTrue(out["compact"])

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
  identity: h.includes("codex:focus-1") && h.includes("model · gpt-5.6-sol"),
  hierarchy: h.indexOf("add focus") < h.indexOf("Right now"),
  surrounding: h.includes("Other project sessions") && h.includes("claude:around-1"),
  noDuplicate: !h.slice(h.indexOf("Other project sessions"),
    h.indexOf("Evidence / limits")).includes("codex:focus-1"),
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
    def test_normal_mirror_reorients_without_recovery_framing(self) -> None:
        checks = """
projectContextByLabel[projectContextKey("repo/proj")] = {state: "ready", generated: 100000,
  data: {observers: [], events: [], semantic: {facts: [
    {fact_id: "result-1", at: 99995, type: "result", summary: "Assignment roster restored",
      work_item_id: "work-1", evidence: {source: "paired result", confidence: "exact"}}
  ], work_items: [{work_item_id: "work-1", label: "Project cockpit", kind: "workflow_item"}],
  projections: {assignments: [], operator_intents: [], steering_episodes: [],
    candidate_goal_shifts: [], trail_heads: [{work_item_id: "work-1", status: "outcome",
      latest_meaningful_event: "result-1"}]}},
  sources: {gate: {}, steer: {unavailable: []}}}};
const d = payload([mk({project: "repo/proj", harness: "codex", sid: "focus-1",
  active: true, state: "working", last_activity: 99990, subagent_hierarchy: [
    {name: "Einstein", depth: 1, assignment: "Project cockpit and remembered goal",
      assignment_status: "structured dispatch artifact", workflow_entity: "project-cockpit",
      workflow_stage: "shaping"},
    {name: "Ampere", depth: 1, assignment: "Session interaction origin",
      assignment_status: "structured dispatch artifact",
      workflow_entity: "session-interaction-origin", workflow_stage: "shaping"},
    {name: "James", depth: 1, assignment: "Review cockpit taxonomy",
      assignment_status: "exact parent dispatch"}
  ]})]);
Object.assign(d, {generated: 100000, ask: true, asks: []});
render(d);
const h = __els.app.innerHTML;
console.log(JSON.stringify({
  ordinary: !h.includes("Recovery mirror") && !h.includes("Safe resume") &&
    !h.includes("checkpoint") && h.includes("Project context") && h.includes("Right now"),
  toward: h.includes("Maintain orientation from ordinary project context"),
  assignments: h.includes('data-work-item="project-cockpit"') &&
    h.includes('data-work-item="session-interaction-origin"') &&
    h.includes('data-work-stage="shaping"') &&
    h.includes("Project cockpit") && h.includes("Project cockpit and remembered goal") &&
    h.includes("Session interaction origin") && h.includes("structured dispatch artifact"),
  taskFirst: !h.includes("<strong>Einstein</strong>") && !h.includes("<strong>Ampere</strong>") &&
    h.indexOf("Project cockpit") < h.indexOf("Einstein") &&
    h.indexOf("Session interaction origin") < h.indexOf("Ampere") &&
    h.indexOf("Review cockpit taxonomy") < h.indexOf("James"),
  oneTaxonomy: h.split('data-assignment-lane="current"').length - 1 === 3 &&
    h.split('data-work-stage="shaping"').length - 1 === 2 &&
    h.includes("Review cockpit taxonomy") && h.includes("current assignment") &&
    !h.includes("Assignments</span>"),
  compact: h.split('data-work-item=').length - 1 === 2 &&
    h.includes('data-graph-layout="time-spine-work-lanes"') &&
    !h.includes('class="pc-work-item') && !h.includes("<details><summary>source</summary>"),
  changed: h.includes("Assignment roster restored") && h.includes("5s ago") &&
    h.includes('data-trail-head="outcome"'),
  freshness: h.includes("latest session evidence · 10s ago"),
  continueAt: h.includes("codex:focus-1") && h.includes("copy session link")
}));
"""
        out = self.run_project(
            checks,
            goal="Maintain orientation from ordinary project context",
            query_project="repo/proj",
            query_session="codex:focus-1",
        )
        self.assertTrue(out["ordinary"])
        self.assertTrue(out["toward"])
        self.assertTrue(out["assignments"])
        self.assertTrue(out["taskFirst"])
        self.assertTrue(out["oneTaxonomy"])
        self.assertTrue(out["compact"])
        self.assertTrue(out["changed"])
        self.assertTrue(out["freshness"])
        self.assertTrue(out["continueAt"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_focused_attention_is_quiet_until_an_exact_real_request_exists(self) -> None:
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
d.asks = [];
d.sessions[0].needs_you = true;
d.sessions[0].needs_reason = "approval required";
render(d);
const overlay = __els.app.innerHTML;
console.log(JSON.stringify({
  clear: clear.includes("No request detected") && !clear.includes('class="pc-needs"') &&
    clear.indexOf("does not prove unblocked") >
      clear.indexOf("Evidence / limits") &&
    clear.includes('data-request-state="none"'),
  exactOnly: !clear.includes("Choose the release path?") && asked.includes("Needs you") &&
    asked.includes("Choose the release path?") && asked.includes(">safe</button>") &&
    asked.includes('data-request-state="ask"'),
  askSource: asked.includes("AskRegistry · exact focused session"),
  overlay: overlay.includes("Needs you") && overlay.includes("approval required") &&
    overlay.includes("live session overlay") && overlay.includes('data-request-state="overlay"')
}));
"""
        out = self.run_project(
            checks,
            query_project="repo/proj",
            query_session="codex:focus-1",
        )
        self.assertTrue(out["clear"])
        self.assertTrue(out["exactOnly"])
        self.assertTrue(out["askSource"])
        self.assertTrue(out["overlay"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_focused_right_now_unifies_live_and_derived_truth(self) -> None:
        checks = """
projectContextByLabel["repo/proj"] = {state: "ready", generated: 100000, data: {
  observers: [{harness: "codex", sid: "focus-1", goal: "Shape the focused mirror",
    stage: null, block: null, model: {model: "gpt-5.6-luna", reasoning_effort: "max",
      status: "used"}, observed_at: 99995, source: "bounded transcript and entity state"}],
  events: [{at: 99990, kind: "steer", phase: "user-role transcript message",
    title: "Keep the project as context", detail: "codex:focus-1",
    source: "transcript user-role message", harness: "codex", sid: "focus-1"}],
  semantic: {facts: [
    {fact_id: "observer-1", at: 99995, type: "observer_snapshot",
      summary: "Shape the focused mirror", work_item_id: null,
      evidence: {source: "cached observer snapshot", confidence: "derived"}},
    {fact_id: "fact-1", at: 99990, type: "user_message",
      summary: "Keep the project as context", work_item_id: null,
      evidence: {source: "timestamped non-meta user-role record", confidence: "exact"}}
  ], work_items: [], relations: [], projections: {
    operator_intents: [{projection_id: "intent-1", at: 99990, kind: "operator_intent",
      summary: "Keep the project as context", derived_from: "fact-1"}],
    trail_heads: [], steering_episodes: [], candidate_goal_shifts: []}},
  sources: {scope: "focused session", gate: {}, steer: {live: 1, unavailable: []}}
}};
const d = payload([mk({project: "repo/proj", harness: "codex", sid: "focus-1",
  active: true, state: "working", state_detail: "running exec", needs_you: null})]);
Object.assign(d, {ask: true, asks: []});
render(d);
const h = __els.app.innerHTML;
console.log(JSON.stringify({
  hierarchy: h.indexOf("<b>Focus</b>") < h.indexOf("Right now") &&
    h.indexOf("Right now") < h.indexOf("Work & steering") &&
    h.indexOf("Observed goal</b> — Shape the focused mirror") < h.indexOf("Right now"),
  motion: h.includes("working now") && h.includes("running exec"),
  purpose: h.includes("Derived snapshot") && h.includes("Shape the focused mirror") &&
    !h.includes("reasoning max") &&
    h.split("Shape the focused mirror").length - 1 === 2,
  workflowBoundary: !h.includes("workflow stage unavailable") &&
    !h.includes("open-block reading unavailable") &&
    h.includes("Stage and block are omitted when absent"),
  attention: h.includes("No request detected") && !h.includes("Needs captain"),
  steering: h.includes("Operator intent") && h.includes("Keep the project as context") &&
    h.includes("timestamped non-meta user-role record") && h.includes("1970-01-02T03:46:30.000Z"),
  identity: h.includes("codex:focus-1"),
  operatorPrecedence: h.includes("Browser focus is operator-authored"),
  noDuplicateObserver: !h.includes('class="pc-observer"') &&
    h.split("Derived snapshot").length - 1 === 1
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
        self.assertTrue(out["noDuplicateObserver"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_what_changed_separates_real_steering_from_demonstrated_outcomes(self) -> None:
        checks = """
projectContextByLabel["repo/proj"] = {state: "ready", generated: 100000, data: {
  observers: [], events: [
    {at: 99980, kind: "steer", phase: "user-role transcript message",
      title: "Prepare release path", detail: "claude:aaa1",
      source: "transcript user-role message", harness: "claude", sid: "aaa1"},
    {at: 99990, kind: "gate", phase: "gate decision · application consumed",
      title: "project-cockpit · shaping · approve", detail: "explore · claude:aaa1",
      source: "Spacedock entity gate frontmatter", harness: "claude", sid: "aaa1"},
    {at: 99985, kind: "activity", phase: "unrelated activity",
      title: "unrelated read", detail: "claude:aaa1",
      source: "activity source", harness: "claude", sid: "aaa1"}
  ], semantic: {facts: [
    {fact_id: "fact-gate", at: 99990, type: "gate_decision",
      summary: "project-cockpit · shaping · approve", work_item_id: "workflow:project-cockpit",
      evidence: {source: "Spacedock entity gate frontmatter", confidence: "exact"}},
    {fact_id: "fact-intent", at: 99980, type: "user_message",
      summary: "Prepare release path", work_item_id: null,
      evidence: {source: "timestamped non-meta user-role record", confidence: "exact"}}
  ], work_items: [{work_item_id: "workflow:project-cockpit", label: "project-cockpit",
    kind: "workflow_item", source_bindings: [], contributor_refs: []}],
  relations: [{from: "fact-gate", to: "workflow:project-cockpit", type: "decides",
    confidence: "structural"}], projections: {
    operator_intents: [{projection_id: "intent-1", at: 99980, kind: "operator_intent",
      summary: "Prepare release path", derived_from: "fact-intent"}],
    trail_heads: [{work_item_id: "workflow:project-cockpit", status: "decision",
      latest_meaningful_event: "fact-gate"}], steering_episodes: [], candidate_goal_shifts: []}},
  sources: {gate: {live: 1, untimestamped_prepare: 2, status_history: "unavailable"},
    steer: {live: 1, unavailable: []}}
}};
render(projectBoard());
const h = __els.app.innerHTML;
console.log(JSON.stringify({
  graph: h.includes('data-model="fact-projection"') && !h.includes("What you asked") &&
    !h.includes("What happened"),
  instruction: h.includes("Operator intent") && h.includes("Prepare release path") &&
    h.includes("timestamped non-meta user-role record") && !h.includes("captain instruction"),
  decision: h.includes('data-trail-head="decision"') && h.includes("shaping · approve"),
  unrelated: !h.includes("unrelated read") && !h.includes("caused") &&
    !h.includes('data-causal-link="supported"') && !h.includes("Work interval") &&
    h.includes("chronology alone is not causality"),
  boundary: h.indexOf("Status-transition history is omitted") >
    h.indexOf("Evidence / limits"),
  noMockTags: !h.includes("generated</span>") && !h.includes("consistency")
}));
"""
        out = self.run_project(checks, query_project="repo/proj", query_session="claude:aaa1")
        self.assertTrue(out["graph"])
        self.assertTrue(out["instruction"])
        self.assertTrue(out["decision"])
        self.assertTrue(out["unrelated"])
        self.assertTrue(out["boundary"])
        self.assertTrue(out["noMockTags"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_work_intervals_link_only_when_source_names_the_instruction(self) -> None:
        checks = """
projectContextByLabel["repo/proj"] = {state: "ready", generated: 100000, data: {
  observers: [], events: [
    {id: "instruction:0", at: 99960, kind: "steer", phase: "user-role transcript message",
      title: "Earlier instruction", intent: "unsupported guess", detail: "codex:focus-1",
      source: "transcript user-role message", harness: "codex", sid: "focus-1"},
    {id: "instruction:1", at: 99970, kind: "steer", phase: "user-role instruction",
      title: "Prepare checkpoint", steering_tag: "generated",
      tag_source: "explicit user-role wording", detail: "codex:focus-1",
      source: "transcript user-role message", harness: "codex", sid: "focus-1"},
    {at: 99980, kind: "activity", phase: "read", title: "Unrelated activity",
      source: "activity source", harness: "codex", sid: "focus-1"},
    {at: 99990, kind: "checkpoint", phase: "checkpoint",
      title: "Checkpoint recorded", detail: "verified checkpoint",
      source: "checkpoint manifest", harness: "codex", sid: "focus-1",
      related_to: "instruction:1", relation_source: "checkpoint manifest relation"}
  ], semantic: {facts: [
    {fact_id: "fact-adapt", at: 99990, type: "result", summary: "Checkpoint recorded",
      work_item_id: null, evidence: {source: "checkpoint manifest", confidence: "exact"}},
    {fact_id: "fact-new", at: 99970, type: "user_message", summary: "Prepare checkpoint",
      work_item_id: null, evidence: {source: "timestamped non-meta user-role record", confidence: "exact"}},
    {fact_id: "fact-old", at: 99960, type: "user_message", summary: "Earlier instruction",
      work_item_id: null, evidence: {source: "timestamped non-meta user-role record", confidence: "exact"}}
  ], work_items: [], relations: [
    {from: "fact-adapt", to: "intent-new", type: "responds_to", confidence: "exact",
      provenance: "checkpoint manifest relation"}
  ], projections: {operator_intents: [
    {projection_id: "intent-new", at: 99970, summary: "Prepare checkpoint", derived_from: "fact-new"},
    {projection_id: "intent-old", at: 99960, summary: "Earlier instruction", derived_from: "fact-old"}
  ], trail_heads: [], steering_episodes: [
    {intent_id: "intent-new", adaptation_fact: "fact-adapt", confidence: "exact"}
  ], candidate_goal_shifts: []}}, sources: {gate: {}, steer: {live: 1, unavailable: []}}
}};
const d = payload([mk({project: "repo/proj", harness: "codex", sid: "focus-1",
  active: true, state: "working"})]);
Object.assign(d, {ask: true, asks: []});
render(d);
const h = __els.app.innerHTML;
console.log(JSON.stringify({
  linked: h.includes('data-steering-state="paired"') &&
    h.includes('data-causal-edge="solid"') &&
    h.includes("source-linked correction") && h.includes("Checkpoint recorded"),
  interval: !h.includes("Work interval") && h.includes("Prepare checkpoint") &&
    h.includes("Checkpoint recorded"),
  newest: h.indexOf("Prepare checkpoint") < h.indexOf("Earlier instruction") &&
    h.includes('data-order="newest-first"'),
  intentBoundary: !h.includes("unsupported guess</span>"),
  noAutonomyClaim: !h.includes("autonomous") && !h.includes("autonomy phase"),
  unrelatedHidden: !h.includes("Unrelated activity")
}));
"""
        out = self.run_project(
            checks,
            query_project="repo/proj",
            query_session="codex:focus-1",
        )
        self.assertTrue(out["linked"])
        self.assertTrue(out["interval"])
        self.assertTrue(out["newest"])
        self.assertTrue(out["intentBoundary"])
        self.assertTrue(out["noAutonomyClaim"])
        self.assertTrue(out["unrelatedHidden"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_mixed_work_stays_semantic_bounded_and_provenance_secondary(self) -> None:
        checks = """
projectContextByLabel[projectContextKey("git/asr")] = {state: "ready", generated: 100000,
  data: {observers: [{harness: "pi", sid: "asr-root", goal: "Resume the ASR work",
    observed_at: 99999, source: "bounded transcript", model: {model: "gpt-5.6-luna",
      reasoning_effort: "max", status: "used"}}], events: [
    {at: 99910, kind: "steer", title: "Keep the first directive", harness: "pi",
      sid: "asr-root", source: "timestamped non-meta user-role record"},
    {at: 99950, kind: "steer", title: "Correct the session grouping", steering_tag: "corrected",
      tag_source: "explicit user-role wording", harness: "pi", sid: "asr-root",
      source: "timestamped non-meta user-role record"},
    {at: 99930, kind: "steer", title: "Do not infer ownership", steering_tag: "generated",
      harness: "pi", sid: "asr-root", source: "timestamped non-meta user-role record"},
    {at: 99940, kind: "steer", title: "Condense steering", harness: "pi", sid: "asr-root",
      source: "timestamped non-meta user-role record"},
    {at: 99920, kind: "steer", title: "Use mixed work as evidence", harness: "pi",
      sid: "asr-root", source: "timestamped non-meta user-role record"},
    {at: 99955, kind: "work", title: "Built dispatch package · task-one · shaping",
      harness: "pi", sid: "asr-root", source: "Pi bash tool call and paired result"},
    {at: 99960, kind: "outcome", title: "2 background tasks contributed", harness: "pi",
      sid: "asr-root", source: "Pi subagent tool call and paired result"},
    {at: 99965, kind: "work", title: "Built dispatch package · task-two · review",
      harness: "pi", sid: "asr-root", source: "Pi bash tool call and paired result"},
    {at: 99970, kind: "outcome", title: "Background task returned · Inspect latency",
      harness: "pi", sid: "asr-root", source: "Pi subagent tool call and paired result"},
    {at: 99975, kind: "work", title: "Built dispatch package · task-three · review",
      harness: "pi", sid: "asr-root", source: "Pi bash tool call and paired result"},
    {at: 99980, kind: "outcome", title: "Background task returned · Check routing",
      harness: "pi", sid: "asr-root", source: "Pi subagent tool call and paired result"}
  ], sources: {gate: {}, work: {live: 6}, steer: {live: 5, unavailable: []},
    observer: {live: 1}}}};
projectContextByLabel[projectContextKey("git/asr")].data.semantic = {
  facts: [
    {fact_id: "observer", at: 99999, type: "observer_snapshot", summary: "Resume the ASR work",
      work_item_id: null, evidence: {source: "cached observer snapshot", confidence: "derived"}},
    {fact_id: "intent-new", at: 99998, type: "user_message", summary: "Correct the session grouping",
      work_item_id: null, evidence: {source: "timestamped non-meta user-role record", confidence: "exact"}},
    {fact_id: "intent-old", at: 99920, type: "user_message", summary: "Use mixed work as evidence",
      work_item_id: null, evidence: {source: "timestamped non-meta user-role record", confidence: "exact"}},
    ...Array.from({length: 7}, (_, i) => ({fact_id: `result-${i}`, at: 99990 - i,
      type: i === 6 ? "prepared_dispatch" : "work_result",
      summary: i === 6 ? "task-one → shaping" : `Meaningful result ${i + 1}`,
      work_item_id: `work-${i}`, evidence: {source: "paired task evidence", confidence: "exact"}}))
  ],
  work_items: Array.from({length: 7}, (_, i) => ({work_item_id: `work-${i}`,
    label: i === 6 ? "task-one" : `Work item ${i + 1}`,
    kind: i === 6 ? "workflow_item" : "one_off", source_bindings: [], contributor_refs: []})),
  contributors: [], relations: [], projections: {
    operator_intents: [
      {projection_id: "intent-proj-new", at: 99998, summary: "Correct the session grouping", derived_from: "intent-new"},
      {projection_id: "intent-proj-old", at: 99920, summary: "Use mixed work as evidence", derived_from: "intent-old"}
    ], trail_heads: Array.from({length: 7}, (_, i) => ({work_item_id: `work-${i}`,
      status: i === 6 ? "prepared" : "outcome", latest_meaningful_event: `result-${i}`})),
    activity: {nodes: [
      {kind: "burst", at: 99990, count: 6,
        work_item_ids: Array.from({length: 6}, (_, i) => `work-${i}`), latest_event: "result-0"},
      {kind: "work", at: 99984, status: "prepared", work_item_ids: ["work-6"],
        latest_event: "result-6", retry_count: 0}
    ], historical_unresolved: 0}, steering_episodes: [], candidate_goal_shifts: []}
};
const d = payload([mk({project: "git/asr", harness: "pi", sid: "asr-root",
  active: true, state: "working", subagent_events: [
    {kind: "task_started", source: "raw lifecycle"},
    {kind: "task_complete", source: "raw lifecycle"}
  ]})]);
Object.assign(d, {ask: true, asks: []});
render(d);
const h = __els.app.innerHTML;
const graph = h.slice(h.indexOf("Work & steering"), h.indexOf("Other project sessions"));
const visibleText = graph;
const primaryText = Array.from(visibleText.matchAll(
  /<div class="pc-trail-top">([\\s\\S]*?)<\\/div>/g
)).map(match => match[1]).join("");
console.log(JSON.stringify({
  bounded: (visibleText.match(/<article class="pc-graph-row/g) || []).length === 4 &&
    graph.includes("6 entities touched") &&
    graph.includes('data-graph-layout="time-spine-work-lanes"'),
  separated: graph.includes('data-model="fact-projection"') &&
    !graph.includes("What you asked") && !graph.includes("What happened"),
  mixed: graph.includes("task-one → shaping") && graph.includes("Meaningful result"),
  quietPrimary: !primaryText.includes("asr-root") && !primaryText.includes("pi:") &&
    !primaryText.includes("gpt-5.6-luna") && !primaryText.includes("reasoning") &&
    !primaryText.includes("transcript message") && !primaryText.includes("source"),
  supportedTagOnly: primaryText.includes("Correct the session grouping") &&
    graph.includes('data-steering-state="unpaired"') &&
    !primaryText.includes("generated</span>"),
  noCausalGuess: (graph.match(/data-causal-edge="none"/g) || []).length === 2 &&
    !graph.includes('data-causal-edge="solid"') &&
    !graph.includes('data-causal-edge="derived"'),
  noRepeatedUnpairedProse: !primaryText.includes("unpaired") &&
    !graph.includes("No demonstrated reaction is linked") &&
    !graph.includes("unpaired · no causal edge"),
  lifecycleSuppressed: !graph.includes("task_started") && !graph.includes("task_complete") &&
    !graph.includes("raw lifecycle")
}));
"""
        out = self.run_project(
            checks,
            project="git/asr",
            query_project="git/asr",
            query_session="pi:asr-root",
        )
        self.assertTrue(out["bounded"])
        self.assertTrue(out["separated"])
        self.assertTrue(out["mixed"])
        self.assertTrue(out["quietPrimary"])
        self.assertTrue(out["supportedTagOnly"])
        self.assertTrue(out["noCausalGuess"])
        self.assertTrue(out["noRepeatedUnpairedProse"])
        self.assertTrue(out["lifecycleSuppressed"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_recent_intent_selection_enters_graph(self) -> None:
        checks = """
projectContextByLabel[projectContextKey("repo/proj")] = {state: "ready", generated: 100000,
  data: {observers: [], events: [], semantic: {facts: [
    {fact_id: "intent-1", at: 99997, type: "user_message", summary: "Show current intents",
      work_item_id: null, evidence: {source: "user-role record", confidence: "exact"}},
    {fact_id: "intent-2", at: 99998, type: "user_message", summary: "Keep the lane grammar",
      work_item_id: null, evidence: {source: "user-role record", confidence: "exact"}}
  ], work_items: [], contributors: [], relations: [], projections: {operator_intents: [
    {projection_id: "projection-1", at: 99997, summary: "Show current intents",
      derived_from: "intent-1"},
    {projection_id: "projection-2", at: 99998, summary: "Keep the lane grammar",
      derived_from: "intent-2"}
  ], trail_heads: [], activity: {nodes: [], steering: [
    {projection_id: "projection-2", at: 99998, summary: "Keep the lane grammar",
      derived_from: "intent-2"},
    {projection_id: "projection-1", at: 99997, summary: "Show current intents",
      derived_from: "intent-1"}
  ]}, steering_episodes: [],
  candidate_goal_shifts: []}}, sources: {gate: {}, steer: {unavailable: []}}}};
const d = payload([mk({project: "repo/proj", harness: "codex", sid: "focus-1",
  active: true, state: "working"})]);
Object.assign(d, {ask: true, asks: []});
render(d);
const h = __els.app.innerHTML;
const graph = h.slice(h.indexOf("Work & steering"), h.indexOf("Other project sessions"));
console.log(JSON.stringify({
  visible: graph.includes("Show current intents") && graph.includes("Keep the lane grammar"),
  diamonds: (graph.match(/data-steering-state="unpaired"/g) || []).length === 2,
  noEdges: (graph.match(/data-causal-edge="none"/g) || []).length === 2 &&
    !graph.includes('data-causal-edge="solid"') && !graph.includes('data-causal-edge="derived"')
}));
"""
        out = self.run_project(
            checks,
            query_project="repo/proj",
            query_session="codex:focus-1",
        )
        self.assertTrue(out["visible"])
        self.assertTrue(out["diamonds"])
        self.assertTrue(out["noEdges"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_primary_trails_demote_birth_only_and_unbound_validation_history(self) -> None:
        checks = """
projectContextByLabel[projectContextKey("git/asr")] = {state: "ready", generated: 100000,
  data: {observers: [], events: [], semantic: {facts: [
    {fact_id: "validation", at: 99999, type: "result", summary: "42 validation checks passed",
      work_item_id: null, evidence: {source: "unbound tool result", confidence: "exact"}},
    {fact_id: "birth", at: 99998, type: "work_birth", summary: "task is DONE",
      work_item_id: "old-task", evidence: {source: "historical task call", confidence: "exact"}},
    {fact_id: "outcome", at: 99990, type: "work_result", summary: "Search index shipped",
      work_item_id: "finished-task", evidence: {source: "paired result", confidence: "exact"}}
  ], work_items: [
    {work_item_id: "old-task", label: "Old task", kind: "one_off",
      source_bindings: [], contributor_refs: []},
    {work_item_id: "finished-task", label: "Search index", kind: "one_off",
      source_bindings: [], contributor_refs: []}
  ], contributors: [], relations: [], projections: {operator_intents: [], trail_heads: [
    {work_item_id: "old-task", status: "requested", latest_meaningful_event: "birth"},
    {work_item_id: "finished-task", status: "outcome", latest_meaningful_event: "outcome"}
  ], steering_episodes: [], candidate_goal_shifts: []}},
  sources: {gate: {}, steer: {unavailable: []}}}};
const d = payload([mk({project: "git/asr", harness: "pi", sid: "asr-root",
  active: true, state: "idle"})]);
Object.assign(d, {ask: true, asks: []});
render(d);
const h = __els.app.innerHTML;
const graph = h.slice(h.indexOf("Work & steering"),
  __els.app.innerHTML.indexOf("Other project sessions"));
const primary = graph.split('<details class="pc-semantic-overflow">')[0];
console.log(JSON.stringify({
  finalPrimary: primary.includes("Search index shipped") && primary.includes('data-trail-head="outcome"'),
  historicalHidden: !primary.includes("task is DONE") && !primary.includes("42 validation checks passed"),
  historyPreserved: h.includes("task is DONE") && h.includes("42 validation checks passed") &&
    h.includes("requested · current state unknown") &&
    h.indexOf("task is DONE") > h.indexOf("Evidence / limits"),
  noFalseCurrent: !graph.includes('data-trail-head="started"') &&
    !graph.includes("current state unverified")
}));
"""
        out = self.run_project(
            checks,
            project="git/asr",
            query_project="git/asr",
            query_session="pi:asr-root",
        )
        self.assertTrue(out["finalPrimary"])
        self.assertTrue(out["historicalHidden"])
        self.assertTrue(out["historyPreserved"])
        self.assertTrue(out["noFalseCurrent"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_primary_copy_omits_empty_fields_and_each_material_limit_appears_once(self) -> None:
        checks = """
projectContextByLabel[projectContextKey("repo/proj")] = {state: "ready", generated: 100000,
  data: {observers: [], events: [], sources: {gate: {}, steer: {unavailable: []}}}};
const d = payload([mk({project: "repo/proj", harness: "codex", sid: "focus-1",
  active: true, state: "working", state_detail: "running exec", model: null,
  subagents: [], subagent_events: []})]);
Object.assign(d, {ask: true, asks: []});
render(d);
const h = __els.app.innerHTML;
const primary = h.slice(0, h.indexOf("Evidence / limits"));
const count = phrase => h.split(phrase).length - 1;
console.log(JSON.stringify({
  omittedEmpty: !primary.includes("Active child hierarchy") &&
    !primary.includes("model unavailable") && !primary.includes("workflow stage unavailable") &&
    !primary.includes("open-block reading unavailable"),
  concisePrimary: primary.includes("No request detected") &&
    !primary.includes("not proof") && !primary.includes("source unavailable"),
  limitsOnce: count("Browser focus is operator-authored") === 1 &&
    count("No request detected") === 1 &&
    count("does not prove unblocked") === 1 &&
    count("chronology alone is not causality") === 1 &&
    count("Stage and block are omitted when absent") === 1,
  oneEvidence: count("Evidence / limits") === 1
}));
"""
        out = self.run_project(
            checks,
            query_project="repo/proj",
            query_session="codex:focus-1",
        )
        self.assertTrue(out["omittedEmpty"])
        self.assertTrue(out["concisePrimary"])
        self.assertTrue(out["limitsOnce"])
        self.assertTrue(out["oneEvidence"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_live_child_hierarchy_stays_primary_while_lifecycle_is_suppressed(self) -> None:
        checks = """
projectContextByLabel[projectContextKey("repo/proj")] = {state: "ready", generated: 100000,
  data: {observers: [], events: [], sources: {gate: {}, steer: {unavailable: []}}}};
const d = payload([mk({project: "repo/proj", harness: "codex", sid: "focus-1",
  active: true, state: "working", state_detail: "running 2 subagents",
  subagent_hierarchy: [
    {name: "Volta", model: "gpt-5.6-sol", depth: 1, parent_name: null,
      assignment: "Make assignments visible"},
    {name: "Turing", model: "gpt-5.6-sol", depth: 2, parent_name: "Volta",
      assignment: null}
  ],
  subagent_events: [
    {at: 99985, kind: "subagent_task_started", name: "Turing", model: "gpt-5.6-sol",
      depth: 2, parent_name: "Volta", source: "Codex child rollout lifecycle"},
    {at: 99986, kind: "subagent_task_started", name: "Turing", task_label: "Compile release",
      depth: 2, parent_name: "Volta", source: "Codex child rollout lifecycle"},
    {at: 99995, kind: "subagent_complete", name: "Turing", model: "gpt-5.6-sol",
      depth: 2, parent_name: "Volta", source: "Codex child rollout lifecycle"},
    {at: 99996, kind: "subagent_complete", name: "Turing", model: "gpt-5.6-sol",
      depth: 2, parent_name: "Volta", source: "Codex child rollout lifecycle"}
  ]
})]);
Object.assign(d, {ask: true, asks: []});
render(d);
const h = __els.app.innerHTML;
const graph = h.slice(h.indexOf("Work & steering"), h.indexOf("Other project sessions"));
const evidence = h.slice(h.indexOf("Evidence / limits"));
console.log(JSON.stringify({
  tree: graph.split('data-assignment-lane="current"').length - 1 === 2 &&
    h.includes('data-subagent-depth="1"') && h.includes('data-subagent-depth="2"'),
  nested: graph.indexOf("Make assignments visible") < graph.indexOf("Volta") &&
    graph.indexOf("assignment unavailable") < graph.indexOf("Turing") &&
    graph.includes("child of Volta") &&
    !h.includes("gpt-5.6-sol"),
  noRoster: !h.includes("Assignments</span>") && !h.includes('class="pc-assignment'),
  lifecycleHidden: !graph.includes("child task started") && !graph.includes("child completed") &&
    !graph.includes("Compile release") && !graph.includes("Codex child rollout lifecycle"),
  collapsed: evidence.includes("4 typed child lifecycle records") &&
    evidence.includes("2 task starts · 2 completions · 0 interruptions"),
  labelWithoutOutcome: !graph.includes("Compile release") &&
    evidence.includes("Lifecycle labels without demonstrated results stay telemetry")
}));
"""
        out = self.run_project(
            checks,
            query_project="repo/proj",
            query_session="codex:focus-1",
        )
        self.assertTrue(out["tree"])
        self.assertTrue(out["nested"])
        self.assertTrue(out["noRoster"])
        self.assertTrue(out["lifecycleHidden"])
        self.assertTrue(out["collapsed"])
        self.assertTrue(out["labelWithoutOutcome"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_semantic_assignments_do_not_enter_the_current_worker_roster(self) -> None:
        checks = """
projectContextByLabel[projectContextKey("git/asr")] = {state: "ready", generated: 100000,
  data: {observers: [], events: [], semantic: {facts: [
    {fact_id: "stage-report", at: 99999, type: "work_birth",
      summary: "Append the missing Stage Report", work_item_id: "ordinary",
      assignment: "Append the missing Stage Report", worker_kind: "subagent",
      evidence: {source: "Pi subagent task label", confidence: "exact"}},
    {fact_id: "ensign-birth", at: 99998, type: "work_birth",
      summary: "release-cockpit · implementation dispatched", work_item_id: "ensign",
      assignment: "Implement the assignment roster", worker_kind: "ensign",
      evidence: {source: "structured dispatch artifact", confidence: "exact"}},
    {fact_id: "done", at: 99990, type: "work_result", summary: "Review completed",
      work_item_id: "review", assignment: "Review the roster", worker_kind: "subagent",
      evidence: {source: "paired result", confidence: "exact"}}
  ], work_items: [
    {work_item_id: "ordinary", label: "Append the missing Stage Report", kind: "one_off"},
    {work_item_id: "ensign", label: "release-cockpit · implementation", kind: "workflow_item"},
    {work_item_id: "review", label: "Review the roster", kind: "one_off"}
  ], contributors: [], relations: [], projections: {assignments: [
    {work_item_id: "ordinary", assignment_fact: "stage-report", state_fact: "stage-report",
      state: "awaiting_result", worker_kind: "subagent", assignment: "Append the missing Stage Report"},
    {work_item_id: "ensign", assignment_fact: "ensign-birth", state_fact: "ensign-birth",
      state: "awaiting_result", worker_kind: "ensign", assignment: "Implement the assignment roster"},
    {work_item_id: "review", assignment_fact: "done", state_fact: "done",
      state: "completed", worker_kind: "subagent", assignment: "Review the roster"}
  ], operator_intents: [], trail_heads: [], steering_episodes: [], candidate_goal_shifts: []}},
  sources: {gate: {}, steer: {unavailable: []}}}};
const d = payload([mk({project: "git/asr", harness: "pi", sid: "asr-root",
  active: true, state: "idle", subagent_hierarchy: []})]);
Object.assign(d, {ask: true, asks: []});
render(d);
const h = __els.app.innerHTML;
console.log(JSON.stringify({
  noRoster: !h.includes("Dispatched / awaiting result") && !h.includes("Completed · 1") &&
    !h.includes('data-assignment-state="awaiting_result"') &&
    !h.includes('data-assignment-state="completed"'),
  transportHidden: !h.includes("/tmp/spacedock-dispatch") && !h.includes("task is DONE") &&
    !h.includes("gpt-") && !h.includes("toolCall")
}));
"""
        out = self.run_project(
            checks,
            project="git/asr",
            query_project="git/asr",
            query_session="pi:asr-root",
        )
        self.assertTrue(out["noRoster"])
        self.assertTrue(out["transportHidden"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_one_recent_and_twelve_old_pi_births_render_as_work_not_workers(self) -> None:
        checks = """
const facts = Array.from({length: 13}, (_, i) => ({fact_id: `birth-${i}`,
  at: i === 0 ? 99999 : 98000 - i, type: "work_birth",
  summary: i === 0 ? "Fix current encoder fault" : `Historical dispatch ${i}`,
  work_item_id: `work-${i}`, evidence: {source: "Pi subagent task label", confidence: "exact"}}));
const workItems = Array.from({length: 13}, (_, i) => ({work_item_id: `work-${i}`,
  label: i === 0 ? "Fix current encoder fault" : `Historical dispatch ${i}`, kind: "one_off"}));
const heads = Array.from({length: 13}, (_, i) => ({work_item_id: `work-${i}`,
  status: "requested", latest_meaningful_event: `birth-${i}`}));
projectContextByLabel[projectContextKey("git/asr")] = {state: "ready", generated: 100000,
  data: {observers: [], events: [], semantic: {facts, work_items: workItems,
  contributors: [], relations: [], projections: {operator_intents: [], trail_heads: heads,
  assignments: heads.map((head, i) => ({work_item_id: head.work_item_id,
    assignment_fact: `birth-${i}`, state: "awaiting_result"})),
  activity: {nodes: [{kind: "work", at: 99999, status: "requested",
    work_item_ids: ["work-0"], latest_event: "birth-0", retry_count: 0}],
    historical_unresolved: 12, historical_dispatches: 12, steering: []},
  steering_episodes: [], candidate_goal_shifts: []}},
  sources: {gate: {}, steer: {unavailable: []}}}};
const d = payload([mk({project: "git/asr", harness: "pi", sid: "asr-root",
  active: true, state: "idle", subagent_hierarchy: []})]);
Object.assign(d, {ask: true, asks: []});
render(d);
const h = __els.app.innerHTML;
const rightNow = h.slice(h.indexOf("Right now"), h.indexOf("Work & steering"));
const graph = h.slice(h.indexOf("Work & steering"), h.indexOf("Other project sessions"));
const evidence = h.slice(h.indexOf("Evidence / limits"));
console.log(JSON.stringify({
  noFalseRoster: !rightNow.includes("Assignments") &&
    !rightNow.includes('data-assignment-state="awaiting_result"'),
  currentWork: graph.includes("Fix current encoder fault") &&
    graph.includes("recently dispatched · current state not confirmed"),
  historyCollapsed: evidence.includes("Past dispatches without observed result · 12") &&
    evidence.includes("show historical request evidence") &&
    !graph.includes("Historical dispatch 1")
}));
"""
        out = self.run_project(
            checks,
            project="git/asr",
            query_project="git/asr",
            query_session="pi:asr-root",
        )
        self.assertTrue(out["noFalseRoster"])
        self.assertTrue(out["currentWork"])
        self.assertTrue(out["historyCollapsed"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_live_child_uses_cached_derived_assignment_only_as_a_labeled_fallback(self) -> None:
        checks = """
projectContextByLabel[projectContextKey("repo/proj")] = {state: "ready", generated: 100000,
  data: {child_assignments: [
    {name: "Volta", observer_sid: "child-1", assignment: "Improve the assignment roster",
      confidence: "derived", source: "cached child observer snapshot",
      snapshot_status: "cached-stale", observed_at: 99990}
  ], observers: [], events: [], sources: {gate: {}, steer: {unavailable: []}}}};
const d = payload([mk({project: "repo/proj", harness: "codex", sid: "focus-1",
  active: true, state: "working", subagent_hierarchy: [
    {name: "Volta", depth: 1, parent_name: null, observer_sid: "child-1",
      assignment: null, assignment_status: "unavailable"}
  ]})]);
Object.assign(d, {ask: true, asks: []});
render(d);
const h = __els.app.innerHTML;
const row = h.slice(h.indexOf('data-assignment-lane="current"'), h.indexOf("Other project sessions"));
console.log(JSON.stringify({
  visible: row.includes("Volta") && row.includes("Improve the assignment roster") &&
    row.includes("working now"),
  derivedSecondary: row.includes("cached child observer snapshot · cached-stale") &&
    row.indexOf("<details") < row.indexOf("cached child observer snapshot"),
  noGuess: !row.includes("exact parent dispatch") && !row.includes("gpt-")
}));
"""
        out = self.run_project(
            checks,
            query_project="repo/proj",
            query_session="codex:focus-1",
        )
        self.assertTrue(out["visible"])
        self.assertTrue(out["derivedSecondary"])
        self.assertTrue(out["noGuess"])

    def test_project_narrow_width_rules_keep_primary_content_wrappable(self) -> None:
        styles = (
            Path(__file__).resolve().parents[1] / "cargento_runtime" / "web" / "styles.css"
        ).read_text(encoding="utf-8")
        self.assertIn("@media(max-width:520px)", styles)
        self.assertIn(".pc-nav select{width:100%;max-width:100%}", styles)
        self.assertIn(".pc-mirror-head{flex-direction:column}", styles)
        self.assertIn(".pc-event-meta{align-items:flex-start;flex-wrap:wrap}", styles)
        self.assertIn("overflow-wrap:anywhere", styles)

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
  boundary: after.includes("AskRegistry · exact focused session")
}));
"""
        out = self.run_project(
            checks,
            query_project="repo/proj",
            query_session="claude:aaa1",
        )
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
render(projectBoard());
const hiddenBeforeEdit = !__els.app.innerHTML.includes('<textarea id="pc-goal"');
projectGoalAction("project-goal-edit", "repo/proj");
const revealed = __els.app.innerHTML.includes('<textarea id="pc-goal"');
__els["pc-goal"] = {value: "Ship the smallest useful cockpit", focus(){}};
projectGoalAction("project-goal-save", "repo/proj");
const key = projectGoalKey("repo/proj");
const saved = __store[key];
render(projectBoard());
const shown = __els.app.innerHTML.includes("Ship the smallest useful cockpit");
projectGoalAction("project-goal-clear", "repo/proj");
console.log(JSON.stringify({key, saved, hiddenBeforeEdit, revealed, shown,
  cleared: !(key in __store)}));
"""
        out = self.run_project(checks)
        self.assertEqual("cargento.projectGoal.v1:repo%2Fproj", out["key"])
        self.assertEqual("Ship the smallest useful cockpit", out["saved"])
        self.assertTrue(out["hiddenBeforeEdit"])
        self.assertTrue(out["revealed"])
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
console.log(JSON.stringify({chosen: h.includes("Project context</span><h2>repo/other</h2>"),
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
  selected: __els.app.innerHTML.includes("Project context</span><h2>repo/other</h2>"),
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
        out = self.run_project(checks, query_project="repo/proj", query_session="claude:aaa1")
        self.assertEqual(2, len(out["calls"]))
        self.assertNotIn("refresh=1", out["calls"][0])
        self.assertIn("refresh=1", out["calls"][1])
        self.assertTrue(out["refreshControl"])


if __name__ == "__main__":
    unittest.main()
