"""The shipped project cockpit over live session and ask payloads."""

from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

from . import test_page_calm
from .page_harness import STYLES, PageJsHarness


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
  compactNav: h.includes('role="tablist"') && h.includes('class="pc-project-tab selected"') &&
    h.includes('class="pc-link"') && !h.includes('id="pc-project-select"'),
  chosen: h.includes("Project context</span><h2>proj</h2>"),
  active: h.includes("1</b> recent"),
  identity: h.includes("claude:aaa1"),
  goalFirst: h.indexOf("add focus") < h.indexOf("Work & steering") &&
    !h.includes("Observed goal") && !h.includes("Goal · derived"),
  mirrorDrilldown: h.includes('data-calm="project-session-focus" data-arg="claude:aaa1"'),
  secondary: h.includes("Other project sessions") && !h.includes("Evidence / limits")
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
    def test_project_tabs_use_exact_working_state_and_keep_permalink_navigation(self) -> None:
        checks = """
const d = payload([
  mk({project: "repo/a", harness: "codex", sid: "work-a", active: true,
    state: "working", last_activity: 99990}),
  mk({project: "repo/b", harness: "claude", sid: "idle-b", active: true,
    state: "idle", last_activity: 99999})
]);
Object.assign(d, {ask: true, asks: []});
render(d);
const cold = __els.app.innerHTML;
const aStart = cold.indexOf(`id="${projectTabId("repo/a")}"`);
const bStart = cold.indexOf(`id="${projectTabId("repo/b")}"`);
const aTab = cold.slice(aStart, cold.indexOf("</button>", aStart));
const bTab = cold.slice(bStart, cold.indexOf("</button>", bStart));
let focused = "";
__els[projectTabId("repo/a")] = {focus(){ focused = "repo/a"; }};
let prevented = false;
__fire("keydown", {key: "ArrowLeft", preventDefault(){ prevented = true; }, target: {
  getAttribute(key){ return key === "role" ? "tab" :
    (key === "data-arg" ? "repo/b" : null); }
}});
const keyed = __els.app.innerHTML;
projectAction("project-cockpit", "repo/b");
const clicked = __els.app.innerHTML;
const lastUrl = __historyUrls[__historyUrls.length - 1] || "";
console.log(JSON.stringify({
  stableOrder: aStart >= 0 && aStart < bStart,
  distinctDots: aTab.includes('pc-project-dot working') &&
    bTab.includes('class="pc-project-dot"') && !bTab.includes('pc-project-dot working'),
  exactState: !cold.includes('id="live-dot"') && bTab.includes("no demonstrated work now"),
  coldPermalink: bTab.includes('aria-selected="true"') && aTab.includes('aria-selected="false"'),
  keyboard: prevented && focused === "repo/a" &&
    keyed.includes(`id="${projectTabId("repo/a")}" class="pc-project-tab selected"`),
  click: clicked.includes(`id="${projectTabId("repo/b")}" class="pc-project-tab selected"`) &&
    lastUrl.includes("project=repo%2Fb")
}));
"""
        out = self.run_project(
            checks,
            query_project="repo/b",
            query_session=None,
        )
        self.assertTrue(out["stableOrder"])
        self.assertTrue(out["distinctDots"])
        self.assertTrue(out["exactState"])
        self.assertTrue(out["coldPermalink"])
        self.assertTrue(out["keyboard"])
        self.assertTrue(out["click"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_tabs_collapse_git_worktrees_and_freeze_persisted_usage_order(self) -> None:
        checks = """
__store[PROJECT_USAGE_KEY] = JSON.stringify({"git:other": 9, "git:cargento": 2});
const d = payload([
  mk({project: "spacedock-research/cargento", project_key: "git:cargento",
    project_name: "cargento", harness: "codex", sid: "main", active: true,
    state: "working", last_activity: 99990}),
  mk({project: ".worktrees/feature", project_key: "git:cargento",
    project_name: "cargento", harness: "codex", sid: "worktree", active: true,
    state: "idle", last_activity: 99980}),
  mk({project: "elsewhere/cargento", project_key: "git:other",
    project_name: "cargento", harness: "pi", sid: "other", active: true,
    state: "idle", last_activity: 99999})
]);
Object.assign(d, {ask: true, asks: []});
render(d);
const first = __els.app.innerHTML;
const firstOther = first.indexOf('data-arg="git:other"');
const firstRepo = first.indexOf('data-arg="git:cargento"');
projectAction("project-cockpit", "git:cargento");
projectAction("project-cockpit", "git:cargento");
const after = __els.app.innerHTML;
console.log(JSON.stringify({
  collapsed: projectGroups(d).length === 2 &&
    projectGroups(d).find(group => group.label === "git:cargento").sessions.length === 2,
  distinct: first.includes('data-arg="git:other"') && first.includes('data-arg="git:cargento"'),
  basename: (first.match(/<span>cargento<\\/span>/g) || []).length === 2 &&
    !first.includes(".worktrees/feature</span>"),
  order: firstOther >= 0 && firstOther < firstRepo &&
    after.indexOf('data-arg="git:other"') < after.indexOf('data-arg="git:cargento"'),
  permalink: first.includes('data-arg="git:cargento"') &&
    first.includes('aria-selected="true"'),
  focus: first.includes("Keep one repository together"),
  countPersisted: JSON.parse(__store[PROJECT_USAGE_KEY])["git:cargento"] === 5
}));
"""
        out = self.run_project(
            checks,
            project="git:cargento",
            goals={"git:cargento": "Keep one repository together"},
            query_project="git:cargento",
        )
        self.assertTrue(out["collapsed"])
        self.assertTrue(out["distinct"])
        self.assertTrue(out["basename"])
        self.assertTrue(out["order"])
        self.assertTrue(out["permalink"])
        self.assertTrue(out["focus"])
        self.assertTrue(out["countPersisted"])

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
  scoped: h.includes("Observed goal · stale") &&
    !h.includes('data-semantic-kind="observed_goal"'),
  separate: h.indexOf("<b>Focus</b>") < h.indexOf("Observed goal · stale</b> — Derived session goal"),
  noOverwrite: !h.includes("Evidence / limits") &&
    h.indexOf("<b>Focus</b>") < h.indexOf("Observed goal · stale"),
  once: h.split("Derived session goal").length - 1 === 1 &&
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
  placed: primary.indexOf("Observed goal") < primary.indexOf('class="pc-operator"'),
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
  mirror: h.includes('data-session-mirror="codex:focus-1"') && h.includes("1 task active") &&
    !h.includes("running exec"),
  identity: h.includes("codex:focus-1") && h.includes("model · gpt-5.6-sol"),
  hierarchy: h.indexOf("add focus") < h.indexOf('class="pc-operator"'),
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
      work_item_id: "work-1", evidence: {source: "paired result", confidence: "exact"}},
    {fact_id: "dispatch-2", at: 99994, type: "prepared_dispatch",
      summary: "Session interaction origin", work_item_id: "work-2",
      evidence: {source: "structured dispatch artifact", confidence: "exact"}}
  ], work_items: [
    {work_item_id: "work-1", label: "Project cockpit", kind: "workflow_item",
      source_bindings: [{source: "structured child assignment",
        value: "/repo/.spacedock/explore:project-cockpit"}]},
    {work_item_id: "work-2", label: "Session interaction origin", kind: "workflow_item",
      source_bindings: [{source: "structured child assignment",
        value: "/repo/.spacedock/explore:session-interaction-origin"}]}
  ],
  projections: {assignments: [], operator_intents: [], steering_episodes: [],
    candidate_goal_shifts: [], trail_heads: [
      {work_item_id: "work-1", status: "outcome", stage: "shaping",
        latest_meaningful_event: "result-1"},
      {work_item_id: "work-2", status: "prepared", stage: "shaping",
        latest_meaningful_event: "dispatch-2"}
    ]}},
  sources: {gate: {}, steer: {unavailable: []}}}};
const d = payload([mk({project: "repo/proj", harness: "codex", sid: "focus-1",
  active: true, state: "working", last_activity: 99990, subagent_hierarchy: [
    {name: "Einstein", depth: 1, assignment: "Project cockpit and remembered goal",
      assignment_status: "structured dispatch artifact", workflow_entity: "project-cockpit",
      workflow_stage: "shaping", workflow_binding: "/repo/.spacedock/explore"},
    {name: "Ampere", depth: 1, assignment: "Session interaction origin",
      assignment_status: "structured dispatch artifact",
      workflow_entity: "session-interaction-origin", workflow_stage: "shaping",
      workflow_binding: "/repo/.spacedock/explore"},
    {name: "James", depth: 1, assignment: "Review cockpit taxonomy",
      assignment_status: "exact parent dispatch"}
  ]})]);
Object.assign(d, {generated: 100000, ask: true, asks: []});
render(d);
const h = __els.app.innerHTML;
console.log(JSON.stringify({
  ordinary: !h.includes("Recovery mirror") && !h.includes("Safe resume") &&
    !h.includes("checkpoint") && h.includes("Project context") && h.includes('class="pc-operator"'),
  toward: h.includes("Maintain orientation from ordinary project context"),
  assignments: h.includes('data-work-item="work-1"') &&
    h.includes('data-work-item="work-2"') &&
    h.includes('data-work-stage="shaping"') &&
    h.includes("Project cockpit") &&
    h.includes("Session interaction origin") && h.includes("structured dispatch artifact"),
  taskFirst: !h.includes("<strong>Einstein</strong>") && !h.includes("<strong>Ampere</strong>") &&
    h.indexOf("Project cockpit") < h.indexOf("Einstein") &&
    h.indexOf("Session interaction origin") < h.indexOf("Ampere") &&
    h.indexOf("Review cockpit taxonomy") < h.indexOf("James"),
  oneTaxonomy: h.split('data-assignment-lane="task-head"').length - 1 === 2 &&
    h.split('data-work-stage="shaping"').length - 1 === 2 &&
    h.includes("Review cockpit taxonomy") && h.includes("unbound contributor") &&
    !h.includes("Assignments</span>"),
  compact: h.split('data-work-item=').length - 1 === 2 &&
    h.includes('data-graph-layout="fo-task-lanes"') &&
    !h.includes('class="pc-work-item'),
  changed: h.includes("Assignment roster restored") && h.includes("5s ago") &&
    h.includes('data-trail-head="outcome"'),
  freshness: h.includes("Working</strong><span>3 tasks active</span>") &&
    h.includes("Updated 10s ago") && !h.includes("children") && !h.includes("no request"),
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
  clear: clear.includes("Working</strong><span>1 task active</span>") &&
    !clear.includes("no request") && !clear.includes('class="pc-needs"') &&
    !clear.includes("Evidence / limits") &&
    clear.includes('data-operator-state="working"'),
  exactOnly: !clear.includes("Choose the release path?") &&
    asked.includes("Needs you</strong><span>Choose the release path?</span>") &&
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
  hierarchy: h.indexOf("<b>Focus</b>") < h.indexOf('class="pc-operator"') &&
    h.indexOf('class="pc-operator"') < h.indexOf("Work & steering") &&
    h.indexOf("Observed goal</b> — Shape the focused mirror") < h.indexOf('class="pc-operator"'),
  motion: h.includes("Working</strong><span>1 task active</span>") &&
    !h.includes("running exec") && !h.includes("no request"),
  purpose: h.includes("Observed goal") && h.includes("Shape the focused mirror") &&
    !h.includes("reasoning max") &&
    h.split("Shape the focused mirror").length - 1 === 1,
  workflowBoundary: !h.includes("workflow stage unavailable") &&
    !h.includes("open-block reading unavailable") && !h.includes("Evidence / limits"),
  attention: !h.includes("no request") && !h.includes("Needs captain"),
  steering: h.includes("First Officer") && h.includes("Keep the project as context") &&
    h.includes("timestamped non-meta user-role record") && h.includes("1970-01-02T03:46:30.000Z"),
  identity: h.includes("codex:focus-1"),
  operatorPrecedence: h.indexOf("<b>Focus</b>") < h.indexOf("Observed goal"),
  noDuplicateObserver: !h.includes('class="pc-observer"') &&
    !h.includes("Derived snapshot")
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
    def test_operator_strip_answers_wait_or_steer_without_repeating_lane_state(self) -> None:
        checks = """
const cargento = payload([mk({project: "repo/proj", harness: "codex", sid: "cargento",
  title: "Shape cockpit", active: true, state: "working", last_activity: 99999,
  subagent_hierarchy: [
    {name: "Einstein", depth: 1, assignment: "Project cockpit", workflow_entity: "project-cockpit",
      workflow_stage: "shaping"},
    {name: "Ampere", depth: 1, assignment: "Session origin", workflow_entity: "session-origin",
      workflow_stage: "shaping"},
    {name: "Gauss", depth: 1, assignment: "Review operator state"}
  ]})]);
Object.assign(cargento, {ask: true, asks: []});
projectQueryLabel = "repo/proj";
projectQuerySession = "codex:cargento";
projectCockpitLabel = "repo/proj";
render(cargento);
const c = __els.app.innerHTML;
const cOperator = c.slice(c.indexOf('class="pc-operator"'), c.indexOf("Work & steering"));
const cGraph = c.slice(c.indexOf("Work & steering"), c.indexOf("Evidence / limits"));

const asr = payload([mk({project: "git/asr", harness: "pi", sid: "asr", title: "ASR work",
  active: true, state: "working", state_detail: "running bash", last_activity: 99940,
  subagent_hierarchy: []})]);
Object.assign(asr, {ask: true, asks: []});
projectQueryLabel = "git/asr";
projectQuerySession = "pi:asr";
projectCockpitLabel = "git/asr";
render(asr);
const a = __els.app.innerHTML;
const aOperator = a.slice(a.indexOf('class="pc-operator"'), a.indexOf("Work & steering"));
console.log(JSON.stringify({
  cargento: cOperator.includes("Working</strong><span>3 tasks active</span>") &&
    cOperator.includes("Updated 1s ago") && !cOperator.includes("children"),
  asr: aOperator.includes("Working</strong><span>1 task active</span>") &&
    aOperator.includes("Updated 1m ago") && !aOperator.includes("running bash"),
  disclosure: cOperator.indexOf("<details") < cOperator.indexOf("Shape cockpit") &&
    aOperator.indexOf("<details") < aOperator.indexOf("ASR work"),
  noLaneRepeat: !cGraph.includes("working now"),
  next: c.includes('</div><div class="pc-activity"') &&
    a.includes('</div><div class="pc-activity"'),
  noEmptySurroundings: !c.includes("Other project sessions") &&
    !c.includes("No other recent sessions") && !a.includes("Other project sessions")
}));
"""
        out = self.run_project(checks)
        self.assertTrue(out["cargento"])
        self.assertTrue(out["asr"])
        self.assertTrue(out["disclosure"])
        self.assertTrue(out["noLaneRepeat"])
        self.assertTrue(out["next"])
        self.assertTrue(out["noEmptySurroundings"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_current_assignment_history_does_not_duplicate_live_work_lanes(self) -> None:
        checks = """
projectContextByLabel["repo/proj"] = {state: "ready", generated: 100000, data: {
  observers: [], events: [], child_assignments: [], semantic: {
    facts: [
      {fact_id:"a1", at:99999, type:"stage_transition", source_kind:"child_assignment",
        stage:"shaping", workflow_binding:"/repo/.spacedock/explore",
        summary:"Shape cockpit", work_item_id:"workflow:project-cockpit", evidence:{}},
      {fact_id:"a2", at:99999, type:"stage_transition", source_kind:"child_assignment",
        stage:"shaping", workflow_binding:"/repo/.spacedock/explore",
        summary:"Shape terminal", work_item_id:"workflow:session-origin", evidence:{}}
    ],
    work_items: [
      {work_item_id:"workflow:project-cockpit", label:"Project cockpit", kind:"workflow_item"},
      {work_item_id:"workflow:session-origin", label:"Session origin", kind:"workflow_item"}
    ], relations: [], history: {event_count:2, persisted:true, events:[
      {event_type:"assignment", source_identity:"codex:child-1",
        work_binding:"workflow:project-cockpit"},
      {event_type:"assignment", source_identity:"codex:child-2",
        work_binding:"workflow:session-origin"}
    ]}, projections: {operator_intents:[], trail_heads:[
      {work_item_id:"workflow:project-cockpit", status:"current stage", stage:"shaping",
        state_fact:"a1", latest_meaningful_event:"a1", dispatch_count:0},
      {work_item_id:"workflow:session-origin", status:"current stage", stage:"shaping",
        state_fact:"a2", latest_meaningful_event:"a2", dispatch_count:0}
    ], steering_episodes:[],
      activity:{nodes:[{kind:"burst", at:99999, count:2,
        work_item_ids:["workflow:project-cockpit","workflow:session-origin"],
        latest_event:"a2"}]}}
  }, sources:{gate:{},steer:{},work:{},observer:{}}
}};
const d = payload([mk({project:"repo/proj", harness:"codex", sid:"focus-1", active:true,
  state:"working", last_activity:99999, subagent_hierarchy:[
    {name:"Einstein", observer_sid:"child-1", depth:1, assignment:"Shape cockpit",
      workflow_entity:"project-cockpit", workflow_stage:"shaping",
      workflow_binding:"/repo/.spacedock/explore"},
    {name:"Ampere", observer_sid:"child-2", depth:1, assignment:"Shape terminal",
      workflow_entity:"session-origin", workflow_stage:"shaping",
      workflow_binding:"/repo/.spacedock/explore"}
  ]})]);
Object.assign(d, {ask:true, asks:[]});
render(d);
const h = __els.app.innerHTML;
console.log(JSON.stringify({
  lanes:h.includes('class="pc-lane-title">Project cockpit</strong><span>Working · shaping') &&
    h.includes('class="pc-lane-title">Session origin</strong><span>Working · shaping'),
  explore:h.includes('data-workflow-binding="/repo/.spacedock/explore"') &&
    h.includes("/repo/.spacedock/explore") && !h.includes("/repo/.spacedock/dev"),
  noDuplicate:!h.includes('data-semantic-burst="2"') && !h.includes("2 entities touched")
}));
"""
        out = self.run_project(
            checks,
            query_project="repo/proj",
            query_session="codex:focus-1",
        )
        self.assertTrue(out["lanes"])
        self.assertTrue(out["explore"])
        self.assertTrue(out["noDuplicate"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_same_entity_slug_in_two_workflows_has_distinct_lane_identity(self) -> None:
        checks = """
const d = {generated:100};
const model = {facts:[
  {fact_id:"explore", at:99, type:"stage_transition", stage:"shaping",
    workflow_binding:"/repo/.spacedock/explore", summary:"Shape prototype",
    work_item_id:"workflow:explore", evidence:{confidence:"exact"}},
  {fact_id:"dev", at:98, type:"stage_transition", stage:"shaping",
    workflow_binding:"/repo/.spacedock/dev", summary:"Shape release",
    work_item_id:"workflow:dev", evidence:{confidence:"exact"}}
], work_items:[
  {work_item_id:"workflow:explore", label:"Project cockpit", kind:"workflow_item",
    source_bindings:[{value:"/repo/.spacedock/explore:project-cockpit"}]},
  {work_item_id:"workflow:dev", label:"Project cockpit", kind:"workflow_item",
    source_bindings:[{value:"/repo/.spacedock/dev:project-cockpit"}]}
], projections:{trail_heads:[
  {work_item_id:"workflow:explore", status:"current stage", stage:"shaping",
    state_fact:"explore", latest_meaningful_event:"explore"},
  {work_item_id:"workflow:dev", status:"current stage", stage:"shaping",
    state_fact:"dev", latest_meaningful_event:"dev"}
], activity:{nodes:[
  {kind:"work", at:99, work_item_ids:["workflow:explore"]},
  {kind:"work", at:98, work_item_ids:["workflow:dev"]}
]}, operator_intents:[], steering_episodes:[]}};
const delegationRows = [
  {entity:"project-cockpit", stage:"shaping", workflowBinding:"/repo/.spacedock/explore",
    assignment:"Shape prototype", worker:"Einstein", relation:"direct child",
    source:"structured dispatch artifact", depth:1, at:99},
  {entity:"project-cockpit", stage:"shaping", workflowBinding:"/repo/.spacedock/dev",
    assignment:"Shape release", worker:"Legacy", relation:"direct child",
    source:"structured dispatch artifact", depth:1, at:98}
];
const html = projectSemanticTimeline(d, model, delegationRows,
  {harness:"codex", sid:"focus-1", last_activity:99});
console.log(JSON.stringify({
  sameHeading:(html.match(/class="pc-lane-title">Project cockpit/g) || []).length === 2 &&
    (html.match(/Working · shaping/g) || []).length === 2,
  distinct:html.includes('data-lane-key="task:workflow:explore"') &&
    html.includes('data-lane-key="task:workflow:dev"') &&
    html.includes('data-workflow-binding="/repo/.spacedock/explore"') &&
    html.includes('data-workflow-binding="/repo/.spacedock/dev"'),
  inspectable:html.includes("/repo/.spacedock/explore") && html.includes("/repo/.spacedock/dev")
}));
"""
        out = self.run_project(checks)
        self.assertTrue(out["sameHeading"])
        self.assertTrue(out["distinct"])
        self.assertTrue(out["inspectable"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_exact_registered_origin_opens_adjacent_read_only_terminal(self) -> None:
        checks = """
const key = "codex:focus-1";
projectTerminalBySession[key] = {state:"registered", revision:100000, data:{
  state:"registered", origin_id_hint:"origin01", terminal_power:"read-only-control-stream",
  keyboard_input:"not-exposed", origin:{session_name:"Cargento", window_index:"1",
    pane_index:"1", pane_id:"%0", window_id:"@0"}
}};
const d = payload([mk({project:"repo/proj", harness:"codex", sid:"focus-1", active:true,
  state:"working", last_activity:99999})]);
Object.assign(d, {generated:100000, ask:true, asks:[]});
render(d);
const closed = __els.app.innerHTML;
projectAction("project-terminal-open", key);
const opened = __els.app.innerHTML;
projectAction("project-terminal-close", key);
const reclosed = __els.app.innerHTML;
delete projectTerminalBySession[key];
render(d);
const absent = __els.app.innerHTML;
console.log(JSON.stringify({
  optIn:closed.includes("Open terminal") && !closed.includes('class="pc-terminal"'),
  adjacent:opened.includes('class="pc-session-workspace terminal-open"') &&
    opened.includes('class="pc-terminal"') && opened.includes("Cargento:1.1") &&
    opened.includes('id="pc-terminal-viewport"') &&
    opened.includes('id="pc-terminal-screen"') &&
    opened.includes('data-calm="project-terminal-jump"') &&
    opened.includes("Jump to live"),
  readOnly:(opened.match(/read-only/g) || []).length === 1 &&
    !opened.includes("Keyboard input") && !opened.includes("send-keys"),
  close:!reclosed.includes('class="pc-terminal"') && reclosed.includes("Open terminal"),
  absent:!absent.includes("Open terminal") && !absent.includes('class="pc-terminal"'),
  focus:projectQuerySession === key && !location.search.includes("terminal"),
  reconnect:projectTerminalConnect.toString().includes("setTimeout") &&
    projectTerminalConnect.toString().includes("event.code !== 1008")
}));
"""
        out = self.run_project(
            checks,
            query_project="repo/proj",
            query_session="codex:focus-1",
        )
        self.assertTrue(out["optIn"])
        self.assertTrue(out["adjacent"])
        self.assertTrue(out["readOnly"])
        self.assertTrue(out["close"])
        self.assertTrue(out["absent"])
        self.assertTrue(out["focus"])
        self.assertTrue(out["reconnect"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_terminal_rerender_reuses_one_socket_and_applies_each_sequence_once(self) -> None:
        checks = """
const key = "codex:focus-1";
location.protocol = "http:"; location.host = "127.0.0.1:8766";
const operations = [];
let terminalCount = 0;
window.Terminal = class {
  constructor(){ terminalCount += 1; this.cols = 80; this.rows = 14; }
  open(node){
    operations.push(`open:${node.name}`);
    this.element = {querySelector: selector => selector === ".xterm-screen" ? {
      style:{}, getBoundingClientRect:() => ({width:this.cols * 8, height:this.rows * 16})
    } : null};
  }
  resize(cols, rows){ this.cols = cols; this.rows = rows; operations.push(`resize:${cols}x${rows}`); }
  reset(){ operations.push("reset"); }
  write(data, done){ operations.push(`write:${data}`); if(done) done(); }
  writeln(data){ operations.push(`writeln:${data}`); }
  dispose(){ operations.push("dispose"); }
};
const sockets = [];
globalThis.WebSocket = class {
  constructor(url){ this.url = url; sockets.push(this); }
  close(){ this.closed = true; }
};
const firstScreen = {name:"first", style:{}};
const makeViewport = name => ({name, scrollTop:0, scrollHeight:928, clientHeight:340,
  onscroll:null});
const firstViewport = makeViewport("first-viewport");
const jump = {hidden:true};
__els["pc-terminal-screen"] = firstScreen;
__els["pc-terminal-viewport"] = firstViewport;
__els["pc-terminal-jump"] = jump;
projectTerminalOpenKey = key;
projectTerminalMount(key, "origin01");
await __settle(); await __settle();
projectTerminalSocket.onmessage({data:JSON.stringify({state:"streamed", sequence:5,
  reset:true, data:"\\u001b[58;115Hvisible", cols:202, rows:58,
  origin_id_hint:"origin01"})});
projectTerminalSocket.onmessage({data:JSON.stringify({state:"streamed", sequence:5,
  reset:true, data:"duplicate", cols:202, rows:58, origin_id_hint:"origin01"})});
projectTerminalSocket.onmessage({data:JSON.stringify({state:"streamed", sequence:4,
  reset:false, data:"old", cols:202, rows:58, origin_id_hint:"origin01"})});
projectTerminalSocket.onmessage({data:JSON.stringify({state:"streamed", sequence:6,
  reset:false, data:"delta", cols:202, rows:58, origin_id_hint:"origin01"})});
projectTerminalSocket.onmessage({data:JSON.stringify({state:"streamed", sequence:6,
  reset:false, data:"duplicate-delta", cols:202, rows:58, origin_id_hint:"origin01"})});
const followedResetAndDelta = firstViewport.scrollTop === 588 && jump.hidden === true;
const exactGridHost = firstScreen.style.width === "1616px" &&
  firstScreen.style.height === "928px";
firstViewport.scrollTop = 127;
firstViewport.onscroll();
const detachedTop = firstViewport.scrollTop;
projectTerminalSocket.onmessage({data:JSON.stringify({state:"streamed", sequence:7,
  reset:false, data:"while-detached", cols:202, rows:58, origin_id_hint:"origin01"})});
const detachedStayedPut = firstViewport.scrollTop === detachedTop && jump.hidden === false;
const preserved = projectTerminalBeforeRender();
let replacedWith = null;
__els["pc-terminal-screen"] = {name:"replacement", replaceWith(node){ replacedWith = node; }};
const replacementViewport = makeViewport("replacement-viewport");
__els["pc-terminal-viewport"] = replacementViewport;
projectTerminalAfterRender(preserved);
projectTerminalMount(key, "origin01");
await __settle();
const rerenderKeptDetached = replacementViewport.scrollTop === detachedTop &&
  jump.hidden === false;
projectAction("project-terminal-jump", key);
const jumpedToLive = replacementViewport.scrollTop === 588 && jump.hidden === true;
const firstSocket = projectTerminalSocket;
firstSocket.onclose({code:1006});
__timers[__timers.length - 1]();
const secondSocket = projectTerminalSocket;
secondSocket.onmessage({data:JSON.stringify({state:"streamed", sequence:8,
  reset:true, data:"reconnected", cols:202, rows:58, origin_id_hint:"origin01"})});
firstSocket.onmessage({data:JSON.stringify({state:"streamed", sequence:9,
  reset:false, data:"orphan", cols:202, rows:58, origin_id_hint:"origin01"})});
firstSocket.onclose({code:1006});
__els["pc-terminal-screen"] = firstScreen;
let settleOrigin = null;
__fetchImpl = url => String(url).includes("/api/interaction/origin")
  ? new Promise(resolve => { settleOrigin = resolve; }) : new Promise(() => {});
projectTerminalBySession[key] = {state:"registered", revision:99, data:{
  state:"registered", origin_id_hint:"origin01", origin:{session_name:"Cargento",
    window_index:"1", pane_index:"1"}}};
const session = mk({project:"repo/proj", harness:"codex", sid:"focus-1", active:true,
  state:"working", last_activity:99});
const d = payload([session]); Object.assign(d, {generated:100, ask:true, asks:[]});
lastData = d;
projectTerminalLookup(d, session);
const pendingKeepsSlot = projectTerminalBySession[key].state === "registered" &&
  projectTerminalBySession[key].loading === true &&
  projectTerminalSurface(session).includes('class="pc-terminal"');
settleOrigin({ok:true, json:() => Promise.resolve({state:"registered",
  origin_id_hint:"origin01", origin:{session_name:"Cargento", window_index:"1", pane_index:"1"}})});
await __settle(); await __settle(); await __settle();
console.log(JSON.stringify({
  oneTerminal:terminalCount === 1,
  oneSocketBeforeReconnect:sockets.length === 2 && firstSocket !== secondSocket,
  oneLiveSocket:projectTerminalSocket === secondSocket,
  pendingKeepsSlot,
  oneAfterLookup:terminalCount === 1 && sockets.length === 2,
  followedResetAndDelta,
  exactGridHost,
  detachedStayedPut,
  rerenderKeptDetached,
  jumpedToLive,
  operations,
  preserved:replacedWith === firstScreen,
  sequence:projectTerminalSequence
}));
"""
        out = self.run_project(
            checks,
            query_project="repo/proj",
            query_session="codex:focus-1",
        )
        self.assertTrue(out["oneTerminal"])
        self.assertTrue(out["oneSocketBeforeReconnect"])
        self.assertTrue(out["oneLiveSocket"])
        self.assertTrue(out["pendingKeepsSlot"])
        self.assertTrue(out["oneAfterLookup"])
        self.assertTrue(out["followedResetAndDelta"])
        self.assertTrue(out["exactGridHost"])
        self.assertTrue(out["detachedStayedPut"])
        self.assertTrue(out["rerenderKeptDetached"])
        self.assertTrue(out["jumpedToLive"])
        self.assertEqual(
            [
                "open:first",
                "resize:202x58",
                "reset",
                "write:\u001b[58;115Hvisible",
                "write:delta",
                "write:while-detached",
                "reset",
                "write:reconnected",
            ],
            out["operations"],
        )
        self.assertTrue(out["preserved"])
        self.assertEqual(8, out["sequence"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_awaiting_session_shows_escaped_final_output_compact_then_full(self) -> None:
        checks = """
const answer = "Ready for review.\\n\\n<img src=x onerror=alert(1)> exact tail";
const d = payload([mk({project: "repo/proj", harness: "codex", sid: "focus-1",
  active: true, state: "idle", state_detail: "awaiting your message",
  last_activity: 99999, last_output: answer})]);
Object.assign(d, {ask: true, asks: []});
render(d);
const h = __els.app.innerHTML;
const output = h.slice(h.indexOf('class="pc-last-output"'), h.indexOf("</details>",
  h.indexOf('class="pc-last-output"')));
console.log(JSON.stringify({
  compact: output.includes("Last · Ready for review."),
  full: output.includes("Ready for review.\\n\\n&lt;img src=x onerror=alert(1)&gt; exact tail"),
  escaped: !output.includes("<img src=x") && output.includes("<pre>"),
  idleOnly: h.includes('data-operator-state="waiting-for-you"') &&
    h.includes("Waiting for you</strong>")
}));
"""
        out = self.run_project(
            checks,
            query_project="repo/proj",
            query_session="codex:focus-1",
        )
        self.assertTrue(out["compact"])
        self.assertTrue(out["full"])
        self.assertTrue(out["escaped"])
        self.assertTrue(out["idleOnly"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_last_output_disclosure_survives_dashboard_revisions_until_explicit_close(self) -> None:
        checks = """
const row = mk({project: "repo/proj", harness: "codex", sid: "focus-1",
  active: true, state: "idle", state_detail: "awaiting your message",
  last_activity: 99999, last_output: "Ready for review."});
const d = payload([row]);
Object.assign(d, {generated:100000, ask:true, asks:[]});
render(d);
const initiallyClosed = !__els.app.innerHTML.includes('class="pc-last-output" open');
const disclosure = {
  open:true,
  getAttribute(name){
    if(name === "data-disclosure-session") return "codex%3Afocus-1";
    return name === "data-pc-disclosure" ? "last-output" : null;
  }
};
__els.app.querySelectorAll = () => [disclosure];
render(Object.assign({}, d, {generated:100001}));
const stayedOpen = __els.app.innerHTML.includes('class="pc-last-output" open');
disclosure.open = false;
render(Object.assign({}, d, {generated:100002}));
const stayedClosed = !__els.app.innerHTML.includes('class="pc-last-output" open');
console.log(JSON.stringify({initiallyClosed, stayedOpen, stayedClosed,
  remembered:projectDisclosureOpenBySession.get("codex:focus-1\\nlast-output")}));
"""
        out = self.run_project(
            checks,
            query_project="repo/proj",
            query_session="codex:focus-1",
        )
        self.assertTrue(out["initiallyClosed"])
        self.assertTrue(out["stayedOpen"])
        self.assertTrue(out["stayedClosed"])
        self.assertFalse(out["remembered"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_all_focused_disclosures_survive_revisions_without_cross_session_leak(self) -> None:
        checks = """
const semantic = sid => ({facts:[
  {fact_id:`dispatch-${sid}`, at:99990, type:"prepared_dispatch",
    source_kind:"prepared_dispatch", summary:"Dispatch task", work_item_id:"workflow:task",
    evidence:{source:"dispatch artifact", confidence:"exact"}},
  {fact_id:`result-${sid}`, at:99991, type:"work_result", summary:"Task returned",
    work_item_id:"workflow:task", evidence:{source:"exact result", confidence:"exact"}}
], work_items:[{work_item_id:"workflow:task", label:"Task", kind:"workflow_item",
  source_bindings:[]}], relations:[
  {type:"dispatches_to", from:`fo:codex:${sid}`, to:"task:workflow:task",
    evidence_ref:`dispatch-${sid}`, confidence:"exact"},
  {type:"returns_to", from:"task:workflow:task", to:`fo:codex:${sid}`,
    evidence_ref:`result-${sid}`, confidence:"exact"}
], history:{event_count:2, persisted:true, events:[]}, projections:{operator_intents:[],
  steering_episodes:[], trail_heads:[{work_item_id:"workflow:task", status:"outcome",
    latest_meaningful_event:`result-${sid}`, dispatch_count:1}],
  activity:{nodes:[{kind:"work", at:99991, work_item_ids:["workflow:task"]}]}}});
for(const sid of ["focus-1", "focus-2"]){
  projectContextByLabel[`repo/proj\\ncodex:${sid}`] = {state:"ready", generated:100000,
    data:{observers:[], events:[], semantic:semantic(sid),
      sources:{gate:{}, steer:{unavailable:[]}, work:{}, observer:{}}}};
}
projectGraphModeBySession.set("codex:focus-1", "all");
const d = payload([
  mk({project:"repo/proj", harness:"codex", sid:"focus-1", state:"idle", active:true,
    last_output:"First result", last_activity:99999}),
  mk({project:"repo/proj", harness:"codex", sid:"focus-2", state:"idle", active:true,
    last_output:"Second result", last_activity:99998})
]);
Object.assign(d, {ask:true, asks:[]});
render(d);
const detail = (control, open) => ({open, getAttribute(name){
  if(name === "data-disclosure-session") return "codex%3Afocus-1";
  return name === "data-pc-disclosure" ? control : null;
}});
const last = detail("last-output", true);
const timelineEvent = detail("timeline-event:dispatch-focus-1", true);
__els.app.querySelectorAll = () => [last, timelineEvent];
render(Object.assign({}, d, {generated:100001}));
const firstOpen = __els.app.innerHTML.includes('class="pc-last-output" open') &&
  __els.app.innerHTML.includes('class="pc-timeline-event" open') &&
  !__els.app.innerHTML.includes("Evidence / limits");
timelineEvent.open = false;
render(Object.assign({}, d, {generated:100002}));
const explicitClose = __els.app.innerHTML.includes('class="pc-last-output" open') &&
  !__els.app.innerHTML.includes('class="pc-timeline-event" open');
__els.app.querySelectorAll = () => [];
projectQuerySession = "codex:focus-2";
render(Object.assign({}, d, {generated:100003}));
const secondClosed = !__els.app.innerHTML.includes('class="pc-last-output" open') &&
  !__els.app.innerHTML.includes('class="pc-timeline-event" open');
projectQuerySession = "codex:focus-1";
render(Object.assign({}, d, {generated:100004}));
const firstRestored = __els.app.innerHTML.includes('class="pc-last-output" open') &&
  !__els.app.innerHTML.includes('class="pc-timeline-event" open');
console.log(JSON.stringify({firstOpen, explicitClose, secondClosed, firstRestored}));
"""
        out = self.run_project(
            checks,
            query_project="repo/proj",
            query_session="codex:focus-1",
        )
        self.assertTrue(out["firstOpen"])
        self.assertTrue(out["explicitClose"])
        self.assertTrue(out["secondClosed"])
        self.assertTrue(out["firstRestored"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_nested_past_work_click_survives_same_click_outer_render(self) -> None:
        checks = """
let rendered = __els.app.innerHTML;
let details = [];
const attr = (source, name) => {
  const match = source.match(new RegExp(`${name}="([^"]*)"`));
  return match ? match[1] : null;
};
Object.defineProperty(__els.app, "innerHTML", {configurable:true,
  get(){ return rendered; },
  set(value){
    rendered = String(value);
    details = [];
    const stack = [];
    for(const match of rendered.matchAll(/<details([^>]*)>|<\\/details>|<summary[^>]*>/g)){
      if(match[0].startsWith("</details")){ stack.pop(); continue; }
      if(match[0].startsWith("<summary")){
        const parent = stack[stack.length - 1];
        if(parent) parent.summary = {parentElement:parent,
          closest(selector){ return selector === "summary" ? this : null; }};
        continue;
      }
      const source = match[1];
      const parent = stack[stack.length - 1] || null;
      const node = {tagName:"DETAILS", parentElement:parent, depth:stack.length,
        open:/(?:^|\\s)open(?:\\s|$)/.test(source),
        getAttribute(name){ return attr(source, name); }};
      details.push(node);
      stack.push(node);
    }
  }
});
__els.app.querySelectorAll = selector => selector === "details[data-pc-disclosure]"
  ? details : __controls();
const task = "workflow:returned";
const context = {observers:[], events:[], semantic:{facts:[
  {fact_id:"audit", at:99992, type:"user_message", summary:"Audit each timeline entry",
    evidence:{source:"root transcript", confidence:"exact"}},
  {fact_id:"ack", at:99989, type:"user_message", summary:"ok.",
    evidence:{source:"root transcript", confidence:"exact"}},
  {fact_id:"dispatch", at:99990, type:"prepared_dispatch", source_kind:"prepared_dispatch",
    summary:"Dispatch task", work_item_id:task,
    evidence:{source:"dispatch artifact", confidence:"exact"}},
  {fact_id:"result", at:99991, type:"work_result", summary:"Task returned",
    work_item_id:task, evidence:{source:"exact result", confidence:"exact"}}
], work_items:[{work_item_id:task, label:"Returned task", kind:"workflow_item",
  source_bindings:[]}], relations:[
  {type:"dispatches_to", from:"fo:codex:focus-1", to:`task:${task}`,
    evidence_ref:"dispatch", confidence:"exact"},
  {type:"returns_to", from:`task:${task}`, to:"fo:codex:focus-1",
    evidence_ref:"result", confidence:"exact"}
], history:{event_count:2, persisted:true, events:[
  {event_id:"history-dispatch", event_type:"assignment", at:99990,
    source_ref:"dispatch", source_identity:"codex:focus-1", work_binding:task,
    summary:"Dispatch task"},
  {event_id:"history-result", event_type:"result", at:99991,
    source_ref:"result", source_identity:"codex:focus-1", work_binding:task,
    summary:"Task returned"}
]}, projections:{operator_intents:[
    {projection_id:"audit", at:99992, summary:"Audit each timeline entry", derived_from:"audit"},
    {projection_id:"ack", at:99989, summary:"ok.", derived_from:"ack"}],
  steering_episodes:[], trail_heads:[{work_item_id:task, status:"outcome",
    latest_meaningful_event:"result", dispatch_count:1}],
  activity:{nodes:[{kind:"work", at:99991, work_item_ids:[task]}]}}},
  sources:{gate:{}, steer:{unavailable:[]}, work:{}, observer:{}}};
projectContextByLabel[projectContextKey("repo/proj")] = {
  state:"ready", generated:100000, dashboard_revision:100000, data:context};
projectGraphModeBySession.set("codex:focus-1", "all");
const d = payload([mk({project:"repo/proj", harness:"codex", sid:"focus-1",
  state:"idle", active:true, last_activity:99999})]);
Object.assign(d, {ask:true, asks:[]});
render(d);
const before = details.find(row =>
  row.getAttribute("data-pc-disclosure") === "timeline-suppressed:audit");
usageCfgOpen = true;
__fire("click", {target:before.summary});
const pastOpen = () => {
  const row = details.find(item =>
    item.getAttribute("data-pc-disclosure") === "timeline-suppressed:audit");
  return row === undefined ? null : row.open;
};
const sameClick = pastOpen();
let contextFetches = 0;
let dashboardRevision = 100001;
__fetchImpl = url => {
  if(String(url).startsWith("/api/project-context")){
    contextFetches++;
    return Promise.resolve({ok:true, json:() => Promise.resolve(context)});
  }
  return Promise.resolve({ok:true, json:() => Promise.resolve(
    Object.assign({}, d, {generated:dashboardRevision++}))});
};
projectLoadContext(Object.assign({}, d, {generated:100001}), true);
const loading = pastOpen();
await __settle(); await __settle();
const settled = pastOpen();
render(Object.assign({}, d, {generated:100002}));
const outer = pastOpen();
await __settle(); await __settle();
const afterOuterContext = pastOpen();
await refresh();
const refreshed = pastOpen();
await __settle(); await __settle();
const afterRefreshContext = pastOpen();
const current = details.find(row =>
  row.getAttribute("data-pc-disclosure") === "timeline-suppressed:audit");
usageCfgOpen = true;
__fire("click", {target:current.summary});
const explicitlyClosed = pastOpen() === false;
render(Object.assign({}, d, {generated:100004}));
await __settle(); await __settle();
const stayedClosed = pastOpen() === false;
console.log(JSON.stringify({before:before.open, nested:before.depth === 1, sameClick, loading, settled, outer,
  afterOuterContext, refreshed, afterRefreshContext, explicitlyClosed, stayedClosed,
  contextFetches}));
"""
        out = self.run_project(
            checks,
            query_project="repo/proj",
            query_session="codex:focus-1",
        )
        self.assertFalse(out["before"])
        self.assertTrue(out["nested"])
        for path in (
            "sameClick",
            "loading",
            "settled",
            "outer",
            "afterOuterContext",
            "refreshed",
            "afterRefreshContext",
        ):
            self.assertTrue(out[path], path)
        self.assertTrue(out["explicitlyClosed"])
        self.assertTrue(out["stayedClosed"])
        self.assertGreaterEqual(out["contextFetches"], 3)

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_full_retained_history_is_distinct_from_primary_work_projection(self) -> None:
        checks = """
const span = 23 * 3600 + 48 * 60;
const historyEvents = Array.from({length:69}, (_, i) => ({
  event_id:`history-${i}`, event_type:i < 63 ? "operator_direction" : "assignment",
  at:1000 + Math.round(i * span / 68), source_ref:`event-${i}`,
  source_identity:"codex:focus-1", work_binding:null, summary:`Source event ${i + 1}`
}));
const facts = historyEvents.map((event, i) => ({fact_id:event.source_ref, at:event.at,
  type:i < 63 ? "user_message" : "stage_transition", summary:event.summary,
  work_item_id:null, evidence:{source:"root transcript", confidence:"exact"}}));
const intents = facts.slice(0, 63).map(fact => ({projection_id:`intent:${fact.fact_id}`,
  at:fact.at, summary:fact.summary, derived_from:fact.fact_id}));
const semantic = {facts, work_items:[], relations:[], history:{event_count:69,
  window_sec:86400, persisted:true, events:historyEvents}, projections:{operator_intents:intents,
  trail_heads:[], steering_episodes:[], candidate_goal_shifts:[], activity:{
    history_nodes:Array.from({length:5}, (_, i) => ({event_id:`history-${i}`})),
    steering:Array.from({length:3}, (_, i) => ({projection_id:`steer-${i}`})), nodes:[]}}};
projectContextByLabel[projectContextKey("repo/proj")] = {state:"ready", generated:100000,
  data:{observers:[], events:[], semantic,
    sources:{gate:{status_history:"unavailable"}, steer:{unavailable:[]},
      work:{}, observer:{}}}};
const d = payload([mk({project:"repo/proj", harness:"codex", sid:"focus-1",
  state:"idle", active:true, last_activity:99999})]);
Object.assign(d, {ask:true, asks:[]});
render(d);
const h = __els.app.innerHTML;
const primary = h.slice(h.indexOf("Work & steering"));
console.log(JSON.stringify({
  truthfulPrimary:primary.includes("newest first") && !primary.includes("24h history") &&
    !primary.includes("Semantic work history · 69 source events") &&
    !primary.includes("Evidence / limits"),
  retained:primary.includes("Source event 1") && primary.includes("Source event 63") &&
    (primary.match(/class="pc-timeline-event"/g) || []).length === 63,
  allDiscoverable:(primary.match(/data-inclusion-rationale=/g) || []).length === 63 &&
    (primary.match(/class="pc-timeline-event"/g) || []).length ===
      (primary.match(/data-inclusion-rationale=/g) || []).length,
  projectionBounded:semantic.projections.activity.history_nodes.length === 5 &&
    semantic.projections.activity.steering.length === 3,
  inventory:!primary.includes("Retained</b>") && !primary.includes("24h retention")
}));
"""
        out = self.run_project(
            checks,
            query_project="repo/proj",
            query_session="codex:focus-1",
        )
        self.assertTrue(out["truthfulPrimary"])
        self.assertTrue(out["retained"])
        self.assertTrue(out["allDiscoverable"])
        self.assertTrue(out["projectionBounded"])
        self.assertTrue(out["inventory"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_what_changed_separates_real_steering_from_demonstrated_outcomes(self) -> None:
        checks = """
projectGraphModeBySession.set("claude:aaa1", "all");
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
  instruction: h.includes("First Officer") && h.includes("Prepare release path") &&
    h.includes("timestamped non-meta user-role record") && !h.includes("captain instruction"),
  decision: h.includes('data-trail-head="decision"') && h.includes("shaping · approve"),
  unrelated: !h.includes("unrelated read") && !h.includes("caused") &&
    !h.includes('data-causal-link="supported"') && !h.includes("Work interval") &&
    !h.includes('data-branch-edge=') && !h.includes('data-merge-edge='),
  boundary: !h.includes("Evidence / limits") && h.includes("Why included"),
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
    h.includes("Checkpoint recorded"),
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
projectGraphModeBySession.set("pi:asr-root", "all");
render(d);
const h = __els.app.innerHTML;
const graph = h.slice(h.indexOf("Work & steering"));
const visibleText = graph;
const primaryText = Array.from(visibleText.matchAll(
  /<div class="pc-trail-top">([\\s\\S]*?)<\\/div>/g
)).map(match => match[1]).join("");
console.log(JSON.stringify({
  bounded: (visibleText.match(/<article class="pc-graph-row/g) || []).length === 9 &&
    !graph.includes("task lanes folded") &&
    graph.includes('data-graph-layout="fo-task-lanes"'),
  separated: graph.includes('data-model="fact-projection"') &&
    !graph.includes("What you asked") && !graph.includes("What happened"),
  mixed: graph.includes("task-one → shaping") && graph.includes("Meaningful result"),
  quietPrimary: !primaryText.includes("asr-root") && !primaryText.includes("pi:") &&
    !primaryText.includes("gpt-5.6-luna") && !primaryText.includes("reasoning") &&
    !primaryText.includes("transcript message") && !primaryText.includes("source"),
  supportedTagOnly: graph.includes("Correct the session grouping") &&
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
    def test_current_band_keeps_unreturned_dispatches_visible(self) -> None:
        checks = """
const focus = mk({project:"repo/proj", harness:"codex", sid:"focus-1", active:true,
  state:"working", last_activity:110});
const cockpit = "workflow:cockpit";
const terminal = "workflow:terminal";
const facts = [
  {fact_id:"direction", at:111, type:"user_message", summary:"Keep current work clear",
    work_item_id:null, evidence:{source:"user-role record", confidence:"exact"}},
  {fact_id:"observer", at:110, type:"observer_snapshot", summary:"Derived old goal",
    work_item_id:null, evidence:{source:"observer", confidence:"derived"}},
  {fact_id:"cockpit-state", at:109, type:"stage_transition", stage:"shaping",
    summary:"Shape cockpit", work_item_id:cockpit,
    evidence:{source:"structured assignment", confidence:"exact"}},
  ...Array.from({length:3}, (_, i) => ({fact_id:`cockpit-dispatch-${i}`, at:106-i,
    type:"prepared_dispatch", source_kind:"prepared_dispatch", stage:"shaping",
    summary:"Project cockpit", work_item_id:cockpit,
    evidence:{source:"dispatch artifact", confidence:"exact"}})),
  {fact_id:"terminal-dispatch", at:108, type:"prepared_dispatch",
    source_kind:"prepared_dispatch", stage:"shaping", summary:"Session interaction origin",
    work_item_id:terminal, evidence:{source:"dispatch artifact", confidence:"exact"}}
];
const relations = [
  ...Array.from({length:3}, (_, i) => ({from:"fo:codex:focus-1",
    to:`task:${cockpit}`, type:"dispatches_to", confidence:"structural",
    evidence_ref:`cockpit-dispatch-${i}`})),
  {from:"fo:codex:focus-1", to:`task:${terminal}`, type:"dispatches_to",
    confidence:"structural", evidence_ref:"terminal-dispatch"}
];
const model = {facts, relations, work_items:[
  {work_item_id:cockpit, label:"Project cockpit", kind:"workflow_item", source_bindings:[]},
  {work_item_id:terminal, label:"session-interaction-origin", kind:"workflow_item",
    source_bindings:[]}
], projections:{operator_intents:[{projection_id:"intent:direction", at:111,
  summary:"Keep current work clear", derived_from:"direction"}], steering_episodes:[], trail_heads:[
  {work_item_id:cockpit, status:"current stage", stage:"shaping",
    latest_meaningful_event:"cockpit-state", dispatch_count:3},
  {work_item_id:terminal, status:"prepared", stage:"shaping",
    latest_meaningful_event:"terminal-dispatch", dispatch_count:1}
], activity:{nodes:[
  {kind:"work", at:109, work_item_ids:[cockpit], latest_event:"cockpit-state"},
  {kind:"work", at:108, work_item_ids:[terminal], latest_event:"terminal-dispatch"}
]}}};
const live = [{entity:"project-cockpit", stage:"shaping", workflowBinding:"/repo/.spacedock/explore",
  workItemId:cockpit, observerSid:"child-1", worker:"Einstein", assignment:"Shape cockpit",
  source:"structured dispatch artifact", relation:"direct child", depth:1, at:110}];
const html = projectSemanticTimeline({generated:112}, model, live, focus);
const current = html;
const withoutLive = projectLaneRegistry(model, [], focus);
const withoutLiveHtml = projectSemanticTimeline({generated:112}, model, [], focus);
console.log(JSON.stringify({
  currentOnly:current.includes("Working") && current.includes("Keep current work clear") &&
    current.includes('class="pc-lane-title">Project cockpit') &&
    current.includes("Working · shaping") && current.includes("Einstein") &&
    current.includes("Session interaction origin") &&
    current.includes("No active worker · no return observed"),
  noHistory:!html.includes('data-activity-band="earlier-meaningful"'),
  topology:!html.includes('data-branch-edge=') && !html.includes('data-merge-edge=') &&
    html.includes("Exact dispatch · First Officer → Project cockpit"),
  attempts:current.includes("3 dispatches") && !current.includes("retries"),
  contributorLoss:withoutLive.laneByKey.get(`task:${cockpit}`).current === true &&
    withoutLive.laneByKey.get(`task:${cockpit}`).working === false &&
    withoutLive.laneByKey.get(`task:${cockpit}`).key === `task:${cockpit}` &&
    withoutLiveHtml.includes("No active worker · no return observed") &&
    withoutLiveHtml.includes('class="pc-lane-title">Project cockpit') &&
    !withoutLiveHtml.includes("Working · shaping"),
  derivedFolded:!current.includes("Derived old goal")
}));
"""
        out = self.run_project(checks)
        self.assertTrue(out["currentOnly"])
        self.assertTrue(out["noHistory"])
        self.assertTrue(out["topology"])
        self.assertTrue(out["attempts"])
        self.assertTrue(out["contributorLoss"])
        self.assertTrue(out["derivedFolded"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_task_lifecycle_returns_reopens_and_requires_retry_evidence(self) -> None:
        checks = """
projectGraphModeBySession.set("", "all");
const focus = mk({project:"repo/proj", harness:"codex", sid:"focus-1",
  state:"working", last_activity:10});
const task = "workflow:task";
const stageOnly = "workflow:stage-only";
const baseFacts = [
  {fact_id:"dispatch-1", at:1, type:"prepared_dispatch", source_kind:"prepared_dispatch",
    summary:"Dispatch task", work_item_id:task,
    evidence:{source:"dispatch artifact", confidence:"exact"}},
  {fact_id:"result-1", at:2, type:"work_result", summary:"Task returned",
    work_item_id:task, evidence:{source:"exact result", confidence:"exact"}},
  {fact_id:"stage-only", at:4, type:"stage_transition", stage:"shaping",
    summary:"Stage only", work_item_id:stageOnly,
    evidence:{source:"state history", confidence:"exact"}}
];
const items = [
  {work_item_id:task, label:"Task", kind:"workflow_item", source_bindings:[]},
  {work_item_id:stageOnly, label:"Stage only", kind:"workflow_item", source_bindings:[]}
];
const relation = (type, from, to, evidence_ref) =>
  ({type, from, to, evidence_ref, confidence:"exact"});
const returnedRelations = [
  relation("dispatches_to", "fo:codex:focus-1", `task:${task}`, "dispatch-1"),
  relation("returns_to", `task:${task}`, "fo:codex:focus-1", "result-1")
];
const model = (facts, relations, head) => ({facts, relations, work_items:items,
  projections:{operator_intents:[], steering_episodes:[], trail_heads:[head,
    {work_item_id:stageOnly, status:"current stage", stage:"shaping",
      latest_meaningful_event:"stage-only", dispatch_count:0}], activity:{nodes:[
    {kind:"work", at:Number((facts.find(f=>f.fact_id===head.latest_meaning_event)||{}).at)||3,
      work_item_ids:[task]},
    {kind:"work", at:4, work_item_ids:[stageOnly]}
  ]}}});
const returnedModel = model(baseFacts, returnedRelations,
  {work_item_id:task, status:"outcome", latest_meaningful_event:"result-1", dispatch_count:1});
const returnedRegistry = projectLaneRegistry(returnedModel, [], focus);
const returnedHtml = projectSemanticTimeline({generated:10}, returnedModel, [], focus);
const dispatch2 = {fact_id:"dispatch-2", at:3, type:"prepared_dispatch",
  source_kind:"prepared_dispatch", summary:"Dispatch task again", work_item_id:task,
  evidence:{source:"dispatch artifact", confidence:"exact"}};
const reopenedRelations = returnedRelations.concat([
  relation("dispatches_to", "fo:codex:focus-1", `task:${task}`, "dispatch-2")]);
const reopenedModel = model(baseFacts.concat([dispatch2]), reopenedRelations,
  {work_item_id:task, status:"prepared", latest_meaningful_event:"dispatch-2", dispatch_count:2});
const reopenedRegistry = projectLaneRegistry(reopenedModel, [], focus);
const reopenedHtml = projectSemanticTimeline({generated:10}, reopenedModel, [], focus);
const retryModel = model(baseFacts.concat([dispatch2]), reopenedRelations.concat([
  relation("retries", `task:${task}`, "dispatch-1", "dispatch-2")]),
  {work_item_id:task, status:"prepared", latest_meaningful_event:"dispatch-2", dispatch_count:2});
const retryHtml = projectSemanticTimeline({generated:10}, retryModel, [], focus);
console.log(JSON.stringify({
  returned:returnedRegistry.laneByKey.get(`task:${task}`).current === false &&
    returnedRegistry.laneByKey.get(`task:${task}`).returned === true &&
    returnedHtml.includes('data-graph-mode="all"') && returnedHtml.includes("Task returned") &&
    returnedHtml.includes('data-task-current="false"'),
  reopened:reopenedRegistry.laneByKey.get(`task:${task}`).current === true &&
    reopenedRegistry.laneByKey.get(`task:${task}`).key === `task:${task}` &&
    reopenedHtml.includes("No active worker · no return observed"),
  retries:reopenedHtml.includes("2 dispatches") && !reopenedHtml.includes("retries") &&
    retryHtml.includes("2 dispatches · 1 retry"),
  stageOnly:returnedRegistry.laneByKey.get(`task:${stageOnly}`).working === false &&
    returnedRegistry.laneByKey.get(`task:${stageOnly}`).current === false
}));
"""
        out = self.run_project(checks)
        self.assertTrue(out["returned"])
        self.assertTrue(out["reopened"])
        self.assertTrue(out["retries"])
        self.assertTrue(out["stageOnly"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_lane_registry_keeps_fo_and_task_identity_stable(self) -> None:
        checks = """
projectGraphModeBySession.set("", "all");
const focus = mk({project:"repo/proj", harness:"codex", sid:"focus-1", active:true,
  state:"working", last_activity:110});
const delegations = [
  {worker:"Einstein", assignment:"Shape cockpit", entity:"project-cockpit", stage:"shaping",
    workflowBinding:"/repo/.spacedock/explore", observerSid:"child-1", source:"structured dispatch artifact",
    relation:"direct child", depth:1, at:110},
  {worker:"Ampere", assignment:"Review cockpit", entity:"project-cockpit", stage:"shaping",
    workflowBinding:"/repo/.spacedock/explore", observerSid:"child-2", source:"structured dispatch artifact",
    relation:"direct child", depth:1, at:109},
  {worker:"Godel", assignment:"Give UX feedback", entity:"", stage:"", workflowBinding:"",
    observerSid:"child-3", source:"exact parent dispatch", relation:"direct child", depth:1, at:108}
];
const foFacts = Array.from({length:5}, (_, i) => ({fact_id:`fo-${i}`, at:100-i,
  type:i < 2 ? "user_message" : "final_output", summary:`FO event ${i + 1}`,
  work_item_id:i === 0 ? null : "session:codex:focus-1",
  evidence:{source:i === 0 ? "user-role record" : "assistant final_answer", confidence:"exact"}}));
const model = {facts: foFacts.concat([
  {fact_id:"dispatch", at:107, type:"prepared_dispatch", summary:"Cockpit dispatched",
    work_item_id:"workflow:cockpit", evidence:{source:"structured dispatch artifact", confidence:"exact"}},
  {fact_id:"stage", at:108, type:"stage_transition", stage:"shaping", summary:"Shaping",
    work_item_id:"workflow:cockpit", evidence:{source:"Explore state", confidence:"exact"}},
  {fact_id:"checkpoint", at:109, type:"checkpoint", summary:"Viewport fixed",
    work_item_id:"workflow:cockpit", evidence:{source:"bound git checkpoint", confidence:"exact"}},
  {fact_id:"result", at:110, type:"work_result", summary:"Cockpit ready",
    work_item_id:"workflow:cockpit", evidence:{source:"paired result", confidence:"exact"}},
  {fact_id:"other", at:106, type:"work_birth", summary:"Terminal dispatched",
    work_item_id:"workflow:terminal", evidence:{source:"structured dispatch artifact", confidence:"exact"}}
]), work_items:[
  {work_item_id:"session:codex:focus-1", label:"Last output", kind:"session_result"},
  {work_item_id:"workflow:cockpit", label:"Project cockpit", kind:"workflow_item",
    source_bindings:[{source:"structured child assignment",
      value:"/repo/.spacedock/explore:project-cockpit"}]},
  {work_item_id:"workflow:terminal", label:"Session origin", kind:"workflow_item"}
], relations:[
  {from:"fo:codex:focus-1", to:"task:workflow:cockpit", type:"dispatches_to",
    confidence:"structural"},
  {from:"task:workflow:cockpit", to:"fo:codex:focus-1", type:"returns_to",
    confidence:"exact"}
], history:{events:[
  {event_type:"assignment", source_identity:"codex:child-1", work_binding:"workflow:cockpit"},
  {event_type:"assignment", source_identity:"codex:child-2", work_binding:"workflow:cockpit"}
]}, projections:{operator_intents:[
  {projection_id:"intent-unpaired", at:100, summary:"FO event 1", derived_from:"fo-0"},
  {projection_id:"intent-paired", at:99, summary:"FO event 2", derived_from:"fo-1"}
], trail_heads:[
  {work_item_id:"workflow:cockpit", status:"current stage", stage:"shaping",
    state_fact:"stage", latest_meaningful_event:"result", dispatch_count:1},
  {work_item_id:"workflow:terminal", status:"prepared", latest_meaningful_event:"other",
    dispatch_count:0}
], activity:{nodes:[
  {kind:"work", at:110, status:"outcome", work_item_ids:["workflow:cockpit"], latest_event:"result"},
  {kind:"work", at:106, status:"prepared", work_item_ids:["workflow:terminal"], latest_event:"other"}
]}, steering_episodes:[{intent_id:"intent-paired", adaptation_fact:"dispatch",
  confidence:"structural"}], candidate_goal_shifts:[]}};
const shuffled = Object.assign({}, model, {facts:model.facts.slice().reverse(),
  projections:Object.assign({}, model.projections, {activity:{nodes:model.projections.activity.nodes.slice().reverse()}})});
const first = projectLaneRegistry(model, delegations, focus);
const second = projectLaneRegistry(shuffled, delegations.slice().reverse(), focus);
const html = projectSemanticTimeline({generated:111}, model, delegations, focus);
const keys = first.lanes.map(lane => lane.key);
const cockpit = first.laneByKey.get("task:workflow:cockpit");
console.log(JSON.stringify({
  stable:keys.every(key => first.laneByKey.get(key).index === second.laneByKey.get(key).index) &&
    new Set(keys).size === keys.length,
  multipleFoEvents:(html.match(/data-lane-key="fo:codex:focus-1"/g) || []).length === 2 &&
    first.laneByKey.get("fo:codex:focus-1").events.length === 2 &&
    html.includes('data-semantic-kind="direction"') &&
    html.includes('data-lane-connect="next"') && !html.includes("FO event 3"),
  oneCockpitLane:cockpit && cockpit.events.length === 4 && cockpit.contributors.length === 2 &&
    (html.match(/data-assignment-lane="task-head"/g) || []).length === 2 &&
    (html.match(/data-work-item="workflow:cockpit"/g) || []).length === 4 &&
    html.includes('class="pc-lane-title">Project cockpit') &&
    html.includes("Working · shaping") && html.includes("Ampere · Einstein") &&
    html.includes("1 dispatch") && html.includes('data-event-id="result"') &&
    html.includes("Cockpit ready"),
  godelFolded:first.lanes.filter(lane => lane.kind === "task").length === 2 &&
    first.unboundContributors.length === 1 && html.includes("Godel") &&
    !html.includes('data-lane-key="task:Godel"'),
  relations:!html.includes('data-branch-edge="solid"') &&
    !html.includes('data-merge-edge="solid"') && cockpit.branch === "solid" &&
    cockpit.merge === "solid" &&
    html.includes('data-steering-state="unpaired"') &&
    html.includes('data-causal-edge="none"') &&
    first.laneByKey.get("fo:codex:focus-1").episodeByFact.has("fo-1"),
  distinctRails:html.includes('data-rail-key="fo:codex:focus-1"') &&
    html.includes('data-rail-key="task:workflow:cockpit"') &&
    html.includes('data-rail-key="task:workflow:terminal"')
}));
"""
        out = self.run_project(checks)
        self.assertTrue(out["stable"])
        self.assertTrue(out["multipleFoEvents"])
        self.assertTrue(out["oneCockpitLane"])
        self.assertTrue(out["godelFolded"])
        self.assertTrue(out["relations"])
        self.assertTrue(out["distinctRails"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_lane_titles_are_dominant_normalized_and_narrow_safe(self) -> None:
        checks = """
const focus = mk({project:"repo/proj", harness:"codex", sid:"focus-1",
  state:"working", last_activity:100});
const cockpit = "workflow:opaque-cockpit-id";
const terminal = "workflow:opaque-terminal-id";
const model = {facts:[
  {fact_id:"direction", at:100, type:"user_message", summary:"Keep lanes readable",
    evidence:{source:"root transcript", confidence:"exact"}},
  {fact_id:"cockpit", at:99, type:"stage_transition", stage:"shaping",
    summary:"Shape cockpit", work_item_id:cockpit,
    evidence:{source:"assignment", confidence:"exact"}},
  {fact_id:"terminal", at:98, type:"stage_transition", stage:"shaping",
    summary:"Shape terminal", work_item_id:terminal,
    evidence:{source:"assignment", confidence:"exact"}}
], work_items:[
  {work_item_id:cockpit, label:"project-cockpit", kind:"workflow_item"},
  {work_item_id:terminal, label:"session-interaction-origin", kind:"workflow_item"}
], relations:[], projections:{operator_intents:[{projection_id:"intent:direction", at:100,
  summary:"Keep lanes readable", derived_from:"direction"}], steering_episodes:[], trail_heads:[
  {work_item_id:cockpit, stage:"shaping", latest_meaningful_event:"cockpit"},
  {work_item_id:terminal, stage:"shaping", latest_meaningful_event:"terminal"}
], activity:{nodes:[
  {kind:"work", at:99, work_item_ids:[cockpit]},
  {kind:"work", at:98, work_item_ids:[terminal]}
]}}};
const workers = [
  {workItemId:cockpit, worker:"Einstein", assignment:"Shape cockpit",
    source:"structured assignment", at:99},
  {workItemId:terminal, worker:"Ampere", assignment:"Shape terminal",
    source:"structured assignment", at:98}
];
const html = projectSemanticTimeline({generated:101}, model, workers, focus);
const titles = [...html.matchAll(/class="pc-lane-title">([^<]*)/g)].map(match => match[1]);
const legend = html.slice(html.indexOf('class="pc-lane-labels"'),
  html.indexOf("</div>", html.indexOf('class="pc-lane-labels"')));
console.log(JSON.stringify({
  titles,
  exact:JSON.stringify(titles) === JSON.stringify(
    ["First Officer", "Project cockpit", "Session interaction origin"]),
  secondary:html.includes("Project cockpit</strong><span>Working · shaping") &&
    html.includes("Session interaction origin</strong><span>Working · shaping"),
  legend:legend.includes("First Officer") && legend.includes("Project cockpit") &&
    legend.includes("Session interaction origin") && !legend.includes("workflow:")
}));
"""
        out = self.run_project(checks)
        self.assertTrue(out["exact"])
        self.assertTrue(out["secondary"])
        self.assertTrue(out["legend"])
        self.assertIn(
            ".pc-trail-top .pc-lane-title{font-size:var(--fs-md);line-height:1.3;"
            "color:var(--ink);overflow-wrap:anywhere}",
            STYLES,
        )
        self.assertIn(
            ".pc-lane-labels{grid-column:3;display:flex;gap:5px;flex-wrap:wrap;",
            STYLES,
        )
        narrow = STYLES[STYLES.index("@media(max-width:520px)") :]
        self.assertIn(".pc-trail-top{display:grid;grid-template-columns:minmax(0,1fr)}", narrow)
        self.assertIn(".pc-trail-top span{text-align:left}", narrow)

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_lane_topology_comes_only_from_explicit_relations(self) -> None:
        checks = """
const focus = mk({project:"repo/proj", harness:"codex", sid:"focus-1", active:true,
  state:"working", last_activity:110});
const delegations = [{worker:"Einstein", assignment:"Shape cockpit", entity:"project-cockpit",
  stage:"shaping", workflowBinding:"/repo/.spacedock/explore", observerSid:"child-1",
  source:"structured dispatch artifact", relation:"direct child", depth:1, at:110}];
const facts = [
  {fact_id:"fo-result", at:111, type:"final_output", summary:"Review complete",
    work_item_id:"session:codex:focus-1", evidence:{source:"final answer", confidence:"exact"}},
  {fact_id:"dispatch", at:108, type:"prepared_dispatch", summary:"Cockpit dispatched",
    work_item_id:"workflow:cockpit", evidence:{source:"dispatch artifact", confidence:"exact"}},
  {fact_id:"outcome", at:110, type:"work_result", summary:"Cockpit ready",
    work_item_id:"workflow:cockpit", evidence:{source:"bound result", confidence:"exact"}}
];
const base = {facts, work_items:[
  {work_item_id:"session:codex:focus-1", label:"Last output", kind:"session_result"},
  {work_item_id:"workflow:cockpit", label:"Project cockpit", kind:"workflow_item",
    source_bindings:[{source:"structured child assignment",
      value:"/repo/.spacedock/explore:project-cockpit"}]}
], relations:[], history:{events:[
  {event_type:"assignment", source_identity:"codex:child-1", work_binding:"workflow:cockpit"}
]}, projections:{operator_intents:[], steering_episodes:[], candidate_goal_shifts:[],
  trail_heads:[{work_item_id:"workflow:cockpit", status:"outcome",
    latest_meaningful_event:"outcome"}], activity:{nodes:[{kind:"work", at:110,
    status:"outcome", work_item_ids:["workflow:cockpit"], latest_event:"outcome"}]}}};
const edge = (relations, reverse=false) => {
  const model = Object.assign({}, base, {relations,
    facts:reverse ? base.facts.slice().reverse() : base.facts,
    projections:Object.assign({}, base.projections, {activity:{nodes:
      reverse ? base.projections.activity.nodes.slice().reverse() : base.projections.activity.nodes}})});
  const rows = reverse ? delegations.slice().reverse() : delegations;
  const lane = projectLaneRegistry(model, rows, focus).laneByKey.get("task:workflow:cockpit");
  return `${lane.branch}/${lane.merge}`;
};
const noRelation = projectSemanticTimeline({generated:112}, base, delegations, focus);
const oneState = Object.assign({}, base, {facts:base.facts.filter(fact => fact.fact_id !== "dispatch")});
const oneStateHtml = projectSemanticTimeline({generated:112}, oneState, delegations, focus);
const exactBranchHtml = projectSemanticTimeline({generated:112}, Object.assign({}, base,
  {relations:[{from:"fo:codex:focus-1", to:"task:workflow:cockpit", type:"dispatches_to",
    evidence_ref:"dispatch", confidence:"structural"}]}), delegations, focus);
console.log(JSON.stringify({
  none:edge([]) === "none/none" && !noRelation.includes('data-branch-edge=') &&
    !noRelation.includes('data-merge-edge='),
  exactBranch:edge([{from:"fo:codex:focus-1", to:"task:workflow:cockpit", type:"dispatches_to",
    confidence:"structural"}]) === "solid/none",
  derivedBranch:edge([{from:"fo:codex:focus-1", to:"task:workflow:cockpit", type:"dispatches_to",
    confidence:"derived-semantic"}]) === "derived/none",
  noOutcomeGuess:edge([]) === "none/none",
  exactMerge:edge([{from:"task:workflow:cockpit", to:"fo:codex:focus-1", type:"returns_to",
    confidence:"exact"}]) === "none/solid",
  shuffleStable:edge([{from:"fo:codex:focus-1", to:"task:workflow:cockpit", type:"dispatches_to",
    confidence:"structural"}, {from:"task:workflow:cockpit", to:"fo:codex:focus-1", type:"returns_to",
    confidence:"exact"}], true) === "solid/solid",
  unrelated:edge([{from:"dispatch", to:"outcome", type:"derived_from",
    confidence:"exact"}]) === "none/none" &&
    edge([{from:"dispatch", to:"workflow:cockpit", type:"binds_to",
      confidence:"structural"}]) === "none/none",
  eventGrammar:!oneStateHtml.includes('data-lane-connect="next"') &&
    noRelation.includes('data-lane-connect="next"') &&
    exactBranchHtml.includes("<b>Relation</b>") &&
    !exactBranchHtml.includes('data-branch-edge=') &&
    !exactBranchHtml.includes('data-merge-edge=')
}));
"""
        out = self.run_project(checks)
        self.assertTrue(out["none"])
        self.assertTrue(out["exactBranch"])
        self.assertTrue(out["derivedBranch"])
        self.assertTrue(out["noOutcomeGuess"])
        self.assertTrue(out["exactMerge"])
        self.assertTrue(out["shuffleStable"])
        self.assertTrue(out["unrelated"])
        self.assertTrue(out["eventGrammar"])
        self.assertIn(".pc-rail-cell{position:relative}", STYLES)
        self.assertNotIn(".pc-rail-cell{position:relative;border-left", STYLES)

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_recent_intent_selection_enters_graph(self) -> None:
        checks = """
projectContextByLabel[projectContextKey("repo/proj")] = {state: "ready", generated: 100000,
  data: {observers: [], events: [], semantic: {facts: [
    {fact_id: "intent-1", at: 99997, type: "user_message", summary: "Show current intents",
      work_item_id: null, evidence: {source: "user-role record", confidence: "exact"}},
    {fact_id: "intent-2", at: 99998, type: "user_message", summary: "Keep the lane grammar",
      work_item_id: null, evidence: {source: "user-role record", confidence: "exact"}},
    {fact_id: "intent-3", at: 99996, type: "user_message", summary: "Keep the lane grammar please",
      work_item_id: null, evidence: {source: "user-role record", confidence: "exact"}},
    {fact_id: "ack", at: 99999, type: "user_message", summary: "ok.",
      work_item_id: null, evidence: {source: "user-role record", confidence: "exact"}},
    {fact_id: "transport", at: 99995, type: "user_message", summary: "env | grep TMUX",
      work_item_id: null, evidence: {source: "user-role record", confidence: "exact"}}
  ], work_items: [], contributors: [], relations: [], projections: {operator_intents: [
    {projection_id: "projection-1", at: 99997, summary: "Show current intents",
      derived_from: "intent-1"},
    {projection_id: "projection-2", at: 99998, summary: "Keep the lane grammar",
      derived_from: "intent-2"},
    {projection_id: "projection-3", at: 99996, summary: "Keep the lane grammar please",
      derived_from: "intent-3"},
    {projection_id: "projection-ack", at: 99999, summary: "ok.", derived_from: "ack"},
    {projection_id: "projection-transport", at: 99995, summary: "env | grep TMUX",
      derived_from: "transport"}
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
const graph = h.slice(h.indexOf("Work & steering"));
console.log(JSON.stringify({
  visible: graph.includes("Show current intents") && graph.includes("Keep the lane grammar"),
  diamonds: (graph.match(/data-steering-state="unpaired"/g) || []).length === 2 &&
    (graph.match(/data-lane-connect="next"/g) || []).length === 2 &&
    !graph.includes('data-event-id="i2"') && !graph.includes('data-event-id="i4"') &&
    !graph.includes('data-event-id="i5"'),
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
const activeHtml = __els.app.innerHTML;
const activeGraph = activeHtml.slice(activeHtml.indexOf("Work & steering"));
projectAction("project-graph-mode", "all");
const h = __els.app.innerHTML;
const graph = h.slice(h.indexOf("Work & steering"));
console.log(JSON.stringify({
  finalPrimary: graph.includes("Search index shipped") && graph.includes('data-trail-head="outcome"'),
  historicalHidden: !activeGraph.includes("task is DONE") &&
    !activeGraph.includes("Search index shipped") && !activeGraph.includes("42 validation checks passed"),
  historyPreserved: graph.includes("task is DONE") &&
    !graph.includes("42 validation checks passed") && !h.includes("Evidence / limits"),
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
const primary = h;
const count = phrase => h.split(phrase).length - 1;
console.log(JSON.stringify({
  omittedEmpty: !primary.includes("Active child hierarchy") &&
    !primary.includes("model unavailable") && !primary.includes("workflow stage unavailable") &&
    !primary.includes("open-block reading unavailable"),
  concisePrimary: !primary.includes("no request") && !primary.includes("not proof") &&
    !primary.includes("source unavailable") && primary.includes("1 task active"),
  limitsOnce: count("Browser focus is operator-authored") === 0 &&
    count("does not prove unblocked") === 0 &&
    count("chronology alone is not causality") === 0 &&
    count("Stage and block are omitted when absent") === 0,
  oneEvidence: count("Evidence / limits") === 0
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
projectGraphModeBySession.set("pi:asr-root", "all");
render(d);
const h = __els.app.innerHTML;
const graph = h.slice(h.indexOf("Work & steering"));
console.log(JSON.stringify({
  tree: graph.split('data-assignment-lane="task-head"').length - 1 === 0 &&
    graph.includes('class="pc-unbound-context"') &&
    graph.includes('class="pc-lane-title">First Officer'),
  nested: graph.includes("2 unbound contributors") &&
    graph.indexOf("Volta") < graph.indexOf("Turing") &&
    graph.includes("Make assignments visible") && graph.includes("assignment unavailable") &&
    !h.includes("gpt-5.6-sol"),
  noRoster: !h.includes("Assignments</span>") && !h.includes('class="pc-assignment'),
  lifecycleHidden: !graph.includes("child task started") && !graph.includes("child completed") &&
    !graph.includes("Compile release") && !graph.includes("Codex child rollout lifecycle"),
  collapsed: !h.includes("4 typed child lifecycle records") &&
    !h.includes("2 task starts · 2 completions · 0 interruptions"),
  labelWithoutOutcome: !graph.includes("Compile release") &&
    !h.includes("Lifecycle labels without demonstrated results stay telemetry")
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
projectGraphModeBySession.set("pi:asr-root", "all");
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
const operator = h.slice(h.indexOf('class="pc-operator"'), h.indexOf("Work & steering"));
const graph = h.slice(h.indexOf("Work & steering"));
console.log(JSON.stringify({
  noFalseRoster: !operator.includes("Assignments") &&
    !operator.includes('data-assignment-state="awaiting_result"'),
  currentWork: graph.includes("Fix current encoder fault") &&
    graph.includes('data-task-current="false"') &&
    !graph.includes("recently dispatched · current state not confirmed"),
  historyCollapsed: !h.includes("Past dispatches without observed result") &&
    graph.includes("Historical dispatch 1") && graph.includes('data-graph-mode="all"') &&
    graph.includes("Why included")
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
const row = h.slice(h.indexOf("Work & steering"), h.indexOf("Evidence / limits"));
console.log(JSON.stringify({
  visible: row.includes("Volta") && row.includes("Improve the assignment roster") &&
    !row.includes("working now"),
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
        self.assertIn(".pc-nav{flex-wrap:nowrap}", styles)
        self.assertIn(".pc-project-tabs{overflow-x:auto;white-space:nowrap}", styles)
        self.assertIn(".pc-operator{padding-inline:14px}", styles)
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
console.log(JSON.stringify({chosen: h.includes("Project context</span><h2>other</h2>"),
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
  selected: __els.app.innerHTML.includes("Project context</span><h2>other</h2>"),
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

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_new_dashboard_revision_coalesces_context_and_rejects_stale_response(self) -> None:
        checks = """
const context = rows => ({observers: [], events: [], semantic: {facts: rows.map(row => ({
  fact_id: `fact-${row.id}`, at: row.at, type: "user_message", summary: row.summary,
  evidence: {source: "focused transcript", confidence: "exact"}
})), work_items: [], contributors: [], relations: [], projections: {
  operator_intents: rows.map(row => ({projection_id: `intent-${row.id}`, at: row.at,
    summary: row.summary, derived_from: `fact-${row.id}`})), trail_heads: [], assignments: [],
  activity: {nodes: [], steering: rows.map(row => ({projection_id: `intent-${row.id}`,
    at: row.at, summary: row.summary, derived_from: `fact-${row.id}`}))},
  steering_episodes: [], candidate_goal_shifts: []}},
  sources: {gate: {}, steer: {live: rows.length, unavailable: []}}});
const key = projectContextKey("repo/proj");
projectContextByLabel[key] = {state: "ready", generated: 99999, dashboard_revision: 99999,
  data: context([{id: "old", at: 99999, summary: "Keep the old direction visible"}])};
const pending = [];
__fetchImpl = url => String(url).includes("/api/interaction/origin")
  ? Promise.resolve({ok:false, status:404, json:() => Promise.resolve({})})
  : new Promise(resolve => pending.push({url, resolve}));
const first = projectBoard(); first.generated = 100000;
render(first);
const preserved = __els.app.innerHTML;
const next = projectBoard(); next.generated = 100001;
render(next);
const coalesced = pending.length;
pending[0].resolve({ok: true, json: () => Promise.resolve(context([
  {id: "stale", at: 100000, summary: "Show stale direction"}
]))});
await __settle(); await __settle();
const afterStale = __els.app.innerHTML;
const callsAfterStale = pending.length;
pending[1].resolve({ok: true, json: () => Promise.resolve(context([
  {id: "one", at: 99996, summary: "Keep first direction"},
  {id: "two", at: 99997, summary: "Keep second direction"},
  {id: "three", at: 99998, summary: "Keep third direction"},
  {id: "new", at: 100001, summary: "Show newest direction"}
]))});
await __settle(); await __settle(); await __settle();
const fresh = __els.app.innerHTML;
const graph = fresh.slice(fresh.indexOf("Work & steering"), fresh.indexOf("Evidence / limits"));
console.log(JSON.stringify({
  preserved: preserved.includes("Keep the old direction visible"),
  coalesced: coalesced === 1 && callsAfterStale === 2,
  staleRejected: afterStale.includes("Keep the old direction visible") &&
    !afterStale.includes("Show stale direction"),
  updated: graph.includes("Show newest direction") &&
    (graph.match(/data-steering-state="unpaired"/g) || []).length === 4 &&
    (graph.match(/data-lane-connect="next"/g) || []).length === 4,
  automatic: pending.every(call => !String(call.url).includes("refresh=1")),
  settled: projectContextByLabel[key].dashboard_revision === 100001
}));
"""
        out = self.run_project(
            checks,
            query_project="repo/proj",
            query_session="claude:aaa1",
        )
        self.assertTrue(out["preserved"])
        self.assertTrue(out["coalesced"])
        self.assertTrue(out["staleRejected"])
        self.assertTrue(out["updated"])
        self.assertTrue(out["automatic"])
        self.assertTrue(out["settled"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_global_timeline_interleaves_lanes_and_spans_intervening_rows(self) -> None:
        checks = """
const focus = mk({project:"repo/proj", harness:"codex", sid:"focus-1",
  active:true, state:"working", last_activity:104});
const task = "workflow:project-cockpit";
const facts = [
  {fact_id:"fo-a", at:104, type:"user_message", summary:"Newest direction",
    evidence:{source:"root transcript", confidence:"exact"}},
  {fact_id:"task-a", at:103, type:"prepared_dispatch", source_kind:"prepared_dispatch",
    summary:"Dispatch cockpit", work_item_id:task,
    evidence:{source:"dispatch artifact", confidence:"exact"}},
  {fact_id:"fo-b", at:102, type:"user_message", summary:"Correct the lane order",
    evidence:{source:"root transcript", confidence:"exact"}},
  {fact_id:"task-b", at:101, type:"stage_transition", stage:"shaping",
    summary:"Shaping cockpit", work_item_id:task,
    evidence:{source:"workflow state", confidence:"exact"}}
];
const model = {facts, work_items:[{work_item_id:task, label:"project-cockpit",
  kind:"workflow_item"}], relations:[{type:"dispatches_to", from:"fo:codex:focus-1",
  to:`task:${task}`, evidence_ref:"task-a", confidence:"exact"}], projections:{
  operator_intents:[
    {projection_id:"intent-a", at:104, summary:"Newest direction", derived_from:"fo-a"},
    {projection_id:"intent-b", at:102, summary:"Correct the lane order", derived_from:"fo-b"}
  ], steering_episodes:[], trail_heads:[{work_item_id:task, status:"current stage",
    stage:"shaping", latest_meaningful_event:"task-b"}], activity:{nodes:[
    {kind:"work", at:103, work_item_ids:[task]}
  ]}}};
const html = projectSemanticTimeline({generated:105}, model, [{workItemId:task,
  worker:"Einstein", assignment:"Shape cockpit", source:"structured assignment", at:103}], focus);
const graphRows = [...html.matchAll(/<article class="pc-graph-row[\\s\\S]*?<\\/article>/g)]
  .map(match => match[0]);
console.log(JSON.stringify({
  order:graphRows.map(row => (row.match(/data-event-id="([^"]+)/) || [])[1]),
  lanes:graphRows.map(row => (row.match(/data-lane-key="([^"]+)/) || [])[1]),
  foSpan:graphRows.slice(0, 3).map(row => row.includes('data-flow-key="fo:codex:focus-1"')),
  taskSpan:graphRows.slice(1, 4).map(row => row.includes(
    'data-flow-key="task:workflow:project-cockpit"')),
  relationDetail:graphRows[1].includes("Exact dispatch · First Officer → Project cockpit") &&
    !graphRows.some(row => row.includes('data-branch-edge=') || row.includes('data-merge-edge='))
}));
"""
        out = self.run_project(checks)
        self.assertEqual(["fo-a", "task-a", "fo-b", "task-b"], out["order"])
        self.assertEqual(
            [
                "fo:codex:focus-1",
                "task:workflow:project-cockpit",
                "fo:codex:focus-1",
                "task:workflow:project-cockpit",
            ],
            out["lanes"],
        )
        self.assertEqual([True, True, True], out["foSpan"])
        self.assertEqual([True, True, True], out["taskSpan"])
        self.assertTrue(out["relationDetail"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_active_all_filter_preserves_lane_keys_and_semantic_history(self) -> None:
        checks = """
const focus = mk({project:"repo/proj", harness:"codex", sid:"focus-1",
  active:true, state:"working", last_activity:105});
const active = "workflow:project-cockpit";
const inactive = "workflow:session-interaction-origin";
const facts = [
  {fact_id:"direction", at:105, type:"user_message", summary:"Keep the active work calm",
    evidence:{source:"root transcript", confidence:"exact"}},
  {fact_id:"active-progress", at:104, type:"stage_transition", stage:"shaping",
    summary:"Shape cockpit", work_item_id:active,
    evidence:{source:"workflow state", confidence:"exact"}},
  {fact_id:"inactive-result", at:103, type:"work_result", summary:"Origin probe returned",
    work_item_id:inactive, evidence:{source:"paired result", confidence:"exact"}},
  {fact_id:"ack", at:102, type:"user_message", summary:"ok.",
    evidence:{source:"root transcript", confidence:"exact"}},
  {fact_id:"transport", at:101, type:"user_message", summary:"env | grep TMUX",
    evidence:{source:"root transcript", confidence:"exact"}}
];
const model = {facts, work_items:[
  {work_item_id:active, label:"project-cockpit", kind:"workflow_item"},
  {work_item_id:inactive, label:"session-interaction-origin", kind:"workflow_item"}
], relations:[], projections:{operator_intents:[
  {projection_id:"direction", at:105, summary:"Keep the active work calm", derived_from:"direction"},
  {projection_id:"ack", at:102, summary:"ok.", derived_from:"ack"},
  {projection_id:"transport", at:101, summary:"env | grep TMUX", derived_from:"transport"}
], steering_episodes:[], trail_heads:[
  {work_item_id:active, status:"current stage", latest_meaningful_event:"active-progress"},
  {work_item_id:inactive, status:"outcome", latest_meaningful_event:"inactive-result"}
], activity:{nodes:[
  {kind:"work", at:104, work_item_ids:[active]},
  {kind:"work", at:103, work_item_ids:[inactive]}
]}}};
const workers = [{workItemId:active, worker:"Einstein", assignment:"Shape cockpit",
  source:"structured assignment", at:104}];
projectQuerySession = "codex:focus-1";
const activeHtml = projectSemanticTimeline({generated:106}, model, workers, focus);
projectGraphModeBySession.set(projectQuerySession, "all");
const allHtml = projectSemanticTimeline({generated:106}, model, workers, focus);
console.log(JSON.stringify({
  activeKeeps:activeHtml.includes('data-lane-key="fo:codex:focus-1"') &&
    activeHtml.includes('data-lane-key="task:workflow:project-cockpit"'),
  activeHides:!activeHtml.includes('data-lane-key="task:workflow:session-interaction-origin"'),
  allRestores:allHtml.includes('data-lane-key="task:workflow:session-interaction-origin"') &&
    allHtml.includes("Origin probe returned"),
  stable:activeHtml.includes('data-lane-key="task:workflow:project-cockpit"') &&
    allHtml.includes('data-lane-key="task:workflow:project-cockpit"'),
  filtered:!activeHtml.includes('data-event-id="ack"') &&
    !allHtml.includes('data-event-id="ack"') &&
    !activeHtml.includes('data-event-id="transport"') &&
    !allHtml.includes('data-event-id="transport"') &&
    activeHtml.includes("Source-only messages · 2") && allHtml.includes("env | grep TMUX"),
  noStructuralCompression:!activeHtml.includes('class="pc-event-scroll"') &&
    !allHtml.includes('class="pc-event-scroll"')
}));
"""
        out = self.run_project(checks)
        self.assertTrue(out["activeKeeps"])
        self.assertTrue(out["activeHides"])
        self.assertTrue(out["allRestores"])
        self.assertTrue(out["stable"])
        self.assertTrue(out["filtered"])
        self.assertTrue(out["noStructuralCompression"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_exact_live_payload_keeps_filter_origin_and_compacts_decisions(self) -> None:
        checks = """
const focus = mk({project:"repo/proj", harness:"codex", sid:"focus-1",
  active:true, state:"working", last_activity:110});
const current = "workflow:current";
const decided = "workflow:633bbd4f7a6a4a1b05b1:t4rqqmmrqh";
const facts = [
  {fact_id:"direction",at:109,type:"user_message",summary:"Keep the decision readable",
    source_session:{harness:"codex",sid:"focus-1"},
    evidence:{source:"root transcript",confidence:"exact"}},
  {fact_id:"progress",at:108,type:"stage_transition",stage:"shaping",
    summary:"Current work shaping",work_item_id:current,
    evidence:{source:"workflow state",confidence:"exact"}},
  {fact_id:"fact:e42c0b40b80c3555",at:107,type:"gate_decision",by:"person:captain",decision:"approve",
    stage:"validation",target_stage:"done",application_state:"pending",
    summary:"embed-stage-report-protocol-in-dispatch · validation · approve",work_item_id:decided,
    evidence:{source:"Spacedock entity gate frontmatter",confidence:"exact"}}
];
const model = {facts,work_items:[
  {work_item_id:current,label:"Current task",kind:"workflow_item"},
  {work_item_id:decided,label:"Embed the stage-report protocol in the dispatch artifact",
    kind:"workflow_item"}
],relations:[],projections:{operator_intents:[
  {projection_id:"intent",at:109,summary:"Keep the decision readable",derived_from:"direction"}
],steering_episodes:[],trail_heads:[
  {work_item_id:current,status:"current stage",stage:"shaping",latest_meaningful_event:"progress"},
  {work_item_id:decided,status:"decision",stage:"validation",
    latest_meaning_event:"fact:e42c0b40b80c3555",
    latest_meaningful_event:"fact:e42c0b40b80c3555"}
],activity:{nodes:[{kind:"work",at:108,work_item_ids:[current]}]}}};
const workers = [{workItemId:current,worker:"Einstein",assignment:"Current work",
  source:"structured assignment",at:108}];
projectQuerySession = "codex:focus-1";
const renderMode = mode => {
  projectGraphModeBySession.set(projectQuerySession, mode);
  return projectSemanticTimeline({generated:110},model,workers,focus);
};
const active = renderMode("active");
const all = renderMode("all");
const decisions = renderMode("decisions");
const laneCount = html => [...html.matchAll(/--lane-count:(\\d+)/g)].map(match => match[1]);
const decisionRow = (decisions.match(/<article[^>]*data-event-id="fact:e42c0b40b80c3555"[\\s\\S]*?<\\/article>/)||[])[0]||"";
const scan = (decisionRow.match(/<div class="pc-trail-result"[^>]*>([\\s\\S]*?)<\\/div>/)||[])[1]||"";
console.log(JSON.stringify({
  activeCounts:laneCount(active),allCounts:laneCount(all),decisionCounts:laneCount(decisions),
  activeHides:!active.includes('data-event-id="fact:e42c0b40b80c3555"'),
  allShows:all.includes('data-event-id="fact:e42c0b40b80c3555"'),
  decisionsOnly:decisions.includes('data-event-id="fact:e42c0b40b80c3555"') &&
    !decisions.includes('data-event-id="direction"') && !decisions.includes('data-event-id="progress"'),
  scan,decisionRow
}));
"""
        out = self.run_project(checks)

        self.assertTrue(out["activeHides"])
        self.assertTrue(out["allShows"])
        self.assertTrue(out["decisionsOnly"])
        self.assertEqual(["3", "3", "3"], out["activeCounts"])
        self.assertEqual(["3", "3", "3", "3"], out["allCounts"])
        self.assertEqual(["3", "3"], out["decisionCounts"])
        self.assertIn(
            "<strong>Approved</strong> Embed the stage report protocol in the dispatch artifact",
            out["scan"],
        )
        self.assertIn("pending application", out["scan"])
        self.assertNotIn("validation", out["scan"])
        self.assertNotIn("→", out["scan"])
        self.assertIn("validation → done", out["decisionRow"])
        self.assertIn("Spacedock entity gate frontmatter", out["decisionRow"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_live_ledger_is_bounded_rebinds_alias_and_has_entry_owned_details(self) -> None:
        checks = """
const focus = mk({project:"repo/proj", harness:"codex", sid:"focus-1",
  active:true, state:"working", last_activity:304000});
const canonical = "workflow:df5a30b2a535380b0c33:project-cockpit";
const unbound = "workflow-unbound:project-cockpit";
const origin = "workflow:df5a30b2a535380b0c33:session-interaction-origin";
const retainedIds = [
  "fact:21a8550762c3845d", "fact:82a8984895279e64", "fact:738457077778c743",
  "fact:45aa76b95428197e", "fact:6e7aa1d11f668c05", "fact:73ea27e2e5db9273",
  "fact:63bd1cd638fbe5e0", "fact:b4acc86e934536ac", "fact:413db8bf0e75803f",
  "fact:db9189af8e1aa1f1", "fact:a479a81d57875894", "fact:4205df239b956b3c",
  "fact:b7e163a322bbb958", "fact:de5c86355543403d", "fact:6c14e9d645e0dcfa",
  "fact:5b040bbb6ba97b3b", "fact:87de679d9cca1303", "fact:2cc265de3ac24202",
  "fact:782f80138452e30e", "fact:ba3aad3120ff2c99", "fact:a7a43358aed222ca",
  "fact:1a3441d444051aaf", "fact:de02775f810e1c40", "fact:e0ba4b0ee1cfdb60",
  "fact:de4e4c95dcdd24fc", "fact:938c40ff2ec3e9ef", "fact:d5812713e5f42ccd",
  "fact:1deb46a1a7f17234", "fact:fea6267d2d9026d3", "fact:5823f7f697ae7a12",
  "fact:1c555c0fa04f43fa", "fact:e95e8d3582ee2240", "fact:79e295352a3f7a62",
  "fact:560dc284cf8fedf0", "fact:5620d89de9c17f0a", "fact:cf383683d84e15c0",
  "fact:100ee43737f23ecc", "fact:362d970fddedaf22", "fact:011ecf3bbe2cd49b",
  "fact:dc4ca983e1a9d74d", "fact:85ea72266a5dadd1", "fact:55f401044ae034ce",
  "fact:b2714f3a14ea7f7f"
];
const topSummaries = [
  "look at each entry on the timeline, and justify it belongs there.",
  "we just recovered from crash.",
  "great, except they should interleve by time, that's the point.",
  "do we currently model meaningful direction / correction and task / subagent events?",
  "and we definitely have a lot of disjoint steers not like 62 sourced events compressed to FO"
];
const directionFacts = retainedIds.map((fact_id, index) => ({fact_id,
  at:303000 - index * 1000, type:"user_message",
  summary:topSummaries[index] || `intent${index} changes a distinct product requirement`,
  evidence:{source:"root transcript", confidence:"exact"}}));
const removed = [
  ["fact:8c82b1d6e4197fb7", "interleved events?"],
  ["fact:381d10a1d28f259e", "if i click last."],
  ["fact:66322f9fbba50308", "do 5 more rounds of mirror reflection."],
  ["fact:a76dcfef0cf06391", "oh now i see it."],
  ["fact:b7747c34c4f02f20", "not sure if this is useful: https://github.com/ampcode/wmux"],
  ["fact:cb07236aabf5b01d", "run it, and continue the loop."],
  ["fact:728ee4a553f90f74", "id you run the server?"],
  ["fact:a0ec17a49525f456", "we just recovered from crash."],
  ["fact:ff648881c8517e40", "read ~/git/spacedock-research/spacedock-strategy/projects/cargento/spec"],
  ["fact:9cea848e43531e01", "look here: https://example.test/mock"],
  ["fact:fedf4a634a700c37", "and tell me what you find in the mock"],
  ["fact:8f7eacbdd39672d1", "continue the rounds."],
  ["fact:0d3b8892d44f05c7", "ok let's try this"],
  ["fact:1ee81765834e5640", "what is this?"],
  ["fact:b4f74328254cdba0", "keep going"],
  ["fact:1b0bd3c98f3ac7fc", "let's get that panel review"],
  ["fact:45152d8410c089a4", "did you get a review from IA advisor and UX expert?"]
].map(([fact_id, summary], index) => ({fact_id, summary, at:200000-index*1000,
  type:"user_message", evidence:{source:"root transcript", confidence:"exact"}}));
removed[0].at = 302500;
const projectDispatches = ["dispatch-new", "dispatch-duplicate-a", "dispatch-duplicate-b",
  "dispatch-duplicate-c"].map((fact_id, index) => ({fact_id, at:302000-index*100,
  type:"prepared_dispatch", summary:"Project cockpit and remembered goal",
  work_item_id:canonical, evidence:{source:"structured dispatch artifact", confidence:"exact"}}));
const stage = {fact_id:"stage-live", at:304000, type:"stage_transition",
  source_kind:"child_assignment", stage:"shaping", summary:"Project cockpit and remembered goal",
  work_item_id:unbound, evidence:{source:"structured dispatch artifact", confidence:"exact"}};
const originDispatch = {fact_id:"origin-dispatch", at:250000, type:"prepared_dispatch",
  summary:"Session interaction origin", work_item_id:origin,
  evidence:{source:"structured dispatch artifact", confidence:"exact"}};
const facts = [stage, ...directionFacts, ...removed, ...projectDispatches, originDispatch];
const operatorIntents = facts.filter(fact => fact.type === "user_message").map(fact => ({
  projection_id:`intent:${fact.fact_id}`, at:fact.at, summary:fact.summary,
  derived_from:fact.fact_id}));
const model = {facts, work_items:[
  {work_item_id:unbound, label:"Project cockpit", kind:"workflow_item",
    source_bindings:[{source:"structured child assignment", value:"project-cockpit"}]},
  {work_item_id:canonical, label:"project-cockpit", kind:"workflow_item",
    source_bindings:[{source:"structured Spacedock dispatch artifact", value:"/tmp/dispatch.md"}]},
  {work_item_id:origin, label:"session-interaction-origin", kind:"workflow_item",
    source_bindings:[{source:"structured Spacedock dispatch artifact", value:"/tmp/origin.md"}]}
], relations:[...projectDispatches.map(fact => ({type:"dispatches_to",
  from:"fo:codex:focus-1", to:`task:${canonical}`, evidence_ref:fact.fact_id,
  confidence:"exact"})), {type:"dispatches_to", from:"fo:codex:focus-1",
  to:`task:${origin}`, evidence_ref:"origin-dispatch", confidence:"exact"}], projections:{
  operator_intents:operatorIntents, steering_episodes:[], trail_heads:[
    {work_item_id:unbound, status:"current stage", latest_meaningful_event:"stage-live"},
    {work_item_id:canonical, status:"prepared", latest_meaningful_event:"dispatch-new"},
    {work_item_id:origin, status:"prepared", latest_meaningful_event:"origin-dispatch"}],
  activity:{nodes:[{kind:"work", at:304000, work_item_ids:[unbound]},
    {kind:"work", at:302000, work_item_ids:[canonical]},
    {kind:"work", at:250000, work_item_ids:[origin]}]}}};
projectQuerySession = "codex:focus-1";
const ledgerHtml = projectSemanticTimeline({generated:305000}, model, [], focus);
const ledgerRows = [...ledgerHtml.matchAll(/<article class="pc-graph-row[\\s\\S]*?<\\/article>/g)]
  .map(match => match[0]);
const ledgerPrimary = ledgerHtml.split('data-activity-band="earlier-meaningful"')[0];
const projectKeys = new Set(ledgerRows.filter(row => row.includes("Project cockpit"))
  .map(row => (row.match(/data-lane-key="([^"]+)/) || [])[1]));
console.log(JSON.stringify({
  bounded:ledgerRows.length === 46 &&
    (ledgerPrimary.match(/<article class="pc-graph-row/g) || []).length === 7 &&
    ledgerHtml.includes("Earlier meaningful · 39"),
  exactWorkingSet:ledgerRows.slice(0, 7).map(row =>
    (row.match(/data-event-id="([^"]+)/) || [])[1]),
  removed:removed.every(fact => !ledgerHtml.includes(`data-event-id="${fact.fact_id}"`)) &&
    ledgerHtml.includes("Source-only messages · 17"),
  canonical:projectKeys.size === 1 && projectKeys.has(`task:${canonical}`) &&
    !ledgerHtml.includes(`data-lane-key="task:${unbound}"`),
  assignmentFold:ledgerRows.filter(row => row.includes("Project cockpit and remembered goal")).length === 1 &&
    ledgerHtml.includes("4 exact records; 3 older matching records folded here."),
  entryOwned:(ledgerHtml.match(/class="pc-timeline-event"/g) || []).length === 46 &&
    (ledgerHtml.match(/data-inclusion-rationale=/g) || []).length === 46 &&
    ledgerHtml.includes("<b>Why included</b>") && ledgerHtml.includes("<b>Source</b>"),
  railsOnly:!ledgerHtml.includes("Evidence / limits") && !ledgerHtml.includes('data-branch-edge=') &&
    !ledgerHtml.includes('data-merge-edge=') && ledgerHtml.includes('data-flow-key=')
}));
"""
        out = self.run_project(checks)
        self.assertTrue(out["bounded"])
        self.assertEqual(
            [
                "stage-live",
                "fact:21a8550762c3845d",
                "dispatch-new",
                "fact:82a8984895279e64",
                "fact:738457077778c743",
                "fact:45aa76b95428197e",
                "fact:6e7aa1d11f668c05",
            ],
            out["exactWorkingSet"],
        )
        self.assertTrue(out["removed"])
        self.assertTrue(out["canonical"])
        self.assertTrue(out["assignmentFold"])
        self.assertTrue(out["entryOwned"])
        self.assertTrue(out["railsOnly"])


if __name__ == "__main__":
    unittest.main()
