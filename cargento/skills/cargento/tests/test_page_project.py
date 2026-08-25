"""The shipped project cockpit over live session and ask payloads."""

from __future__ import annotations

import json
import shutil
import unittest
from typing import Any

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
    def prelude(*, project: str = "repo/proj", goal: str | None = None) -> str:
        values = {
            "cargento.displayMode": "project",
            "cargento.projectCockpitProject": project,
        }
        if goal is not None:
            values[f"cargento.projectGoal.v1:{project.replace('/', '%2F')}"] = goal
        return f"""
let __store = {json.dumps(values)};
const localStorage = {{
  getItem(k){{ return Object.prototype.hasOwnProperty.call(__store, k) ? __store[k] : null; }},
  setItem(k, v){{ __store[k] = String(v); }},
  removeItem(k){{ delete __store[k]; }}
}};
const navigator = {{}};
let __timers = [];
const setTimeout = fn => {{ __timers.push(fn); return __timers.length; }};
"""

    def run_project(
        self, checks: str, *, project: str = "repo/proj", goal: str | None = None
    ) -> Any:
        return self._run_page_js(
            self.FIXTURE + checks,
            prelude=self.prelude(project=project, goal=goal),
        )

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_compact_navigation_leads_into_one_selected_project_boundary(self) -> None:
        checks = """
render(projectBoard());
const h = __els.app.innerHTML;
console.log(JSON.stringify({
  mode: displayMode,
  className: __els.app.className,
  compactNav: h.includes('class="pc-nav"') && !h.includes("Which project are you working toward?"),
  chosen: h.includes("Working toward</span><h2>repo/proj</h2>"),
  active: h.includes("1</b> active"),
  empty: h.includes("No session in this project is asking through Cargento."),
  identity: h.includes("claude:aaa1"),
  goalFirst: h.indexOf("Operator goal") < h.indexOf("Observer context"),
  mirrorDrilldown: h.includes('data-calm="session" data-arg="claude:aaa1"'),
  secondary: h.indexOf("Source and identity details") > h.indexOf("Active sessions")
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
observerBySid["claude:aaa1"] = {state: "ready", sidecar: {
  goal: "Derived session goal", stage: "shaping", block: "waiting for captain"
}};
render(projectBoard());
const h = __els.app.innerHTML;
console.log(JSON.stringify({
  operator: h.includes("Operator goal <em>authoritative · browser only</em>"),
  observed: h.includes("Derived session goal"),
  scoped: h.includes("session-scoped · claude:aaa1"),
  separate: h.indexOf("Operator goal") < h.indexOf("Derived session goal"),
  noOverwrite: h.includes("observer text never overwrites this field")
}));
"""
        out = self.run_project(checks, goal="Operator-owned goal")
        self.assertTrue(out["operator"])
        self.assertTrue(out["observed"])
        self.assertTrue(out["scoped"])
        self.assertTrue(out["separate"])
        self.assertTrue(out["noOverwrite"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_activity_reuses_causal_log_shape_without_mocked_history(self) -> None:
        checks = """
blocked.last_prompt = "Prepare the release path";
render(projectBoard([liveAsk()]));
const h = __els.app.innerHTML;
console.log(JSON.stringify({
  graph: h.includes('class="pc-log"') && h.includes('class="pc-event-node"'),
  instruction: h.includes("latest instruction"),
  decision: h.includes("decision requested") && h.includes("Choose the release path?"),
  boundary: h.includes("historical steering and gate decisions are unavailable"),
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


if __name__ == "__main__":
    unittest.main()
