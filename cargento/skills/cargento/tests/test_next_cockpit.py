from __future__ import annotations

import shutil
import unittest

from .next_harness import NextPageJsHarness
from .test_next_isolation import storage_prelude


@unittest.skipUnless(shutil.which("node"), "node not available")
class NextCockpitCompositionTest(NextPageJsHarness):
    FIXTURE = """
location.hash = "#n=project:cargento";
__els.app = {innerHTML: ""};
const __dashboard = {
  generated: 105, rate_window_sec: 600, window_hours: 24,
  summary: {working: 1, needs_input: 0},
  harnesses: [{key: "codex", label: "Codex"}],
  sessions: [{sid: "focus-1", harness: "codex", project: "cargento",
    project_key: "spacedock-research/cargento", state: "working", active: true,
    last_activity: 104, title: "Shape project cockpit", subagents: []}]
};
const __task = "workflow:project-cockpit";
const __semantic = {facts: [
  {fact_id:"fo-a", at:104, type:"user_message", summary:"Newest direction",
    evidence:{source:"root transcript", confidence:"exact"}},
  {fact_id:"task-a", at:103, type:"prepared_dispatch", summary:"Dispatch cockpit",
    work_item_id:__task, evidence:{source:"dispatch artifact", confidence:"exact"}},
  {fact_id:"fo-b", at:102, type:"user_message", summary:"Correct the lane order",
    evidence:{source:"root transcript", confidence:"exact"}},
  {fact_id:"task-b", at:101, type:"stage_transition", stage:"shaping",
    summary:"Shaping cockpit", work_item_id:__task,
    evidence:{source:"workflow state", confidence:"exact"}}
], work_items:[{work_item_id:__task, label:"project-cockpit", kind:"workflow_item"}],
relations:[{type:"dispatches_to", from:"fo:codex:focus-1",
  to:`task:${__task}`, evidence_ref:"task-a", confidence:"exact"}], projections:{
  operator_intents:[
    {projection_id:"intent-a", at:104, summary:"Newest direction", derived_from:"fo-a"},
    {projection_id:"intent-b", at:102, summary:"Correct the lane order", derived_from:"fo-b"}
  ], steering_episodes:[], trail_heads:[{work_item_id:__task, status:"current stage",
    stage:"shaping", latest_meaningful_event:"task-b"}],
  activity:{nodes:[{kind:"work", at:103, work_item_ids:[__task]}]}}};
__fetchImpl = async url => ({ok: true, json: async () =>
  String(url).startsWith("/api/project-context")
    ? {semantic: __semantic, child_assignments: [], observers: []}
    : __dashboard});
"""

    def run_fixture(self, checks: str, *, storage: dict[str, str] | None = None) -> object:
        return self._run_page_js(
            "await __settle();\nawait __settle();\n" + checks,
            storage_prelude(storage or {}) + self.FIXTURE,
        )

    def test_upstream_project_detail_hosts_focus_semantics_and_no_duplicate_shell(self) -> None:
        out = self.run_fixture(
            """
const html = __els.app.innerHTML;
const rows = [...html.matchAll(/<article class="pc-graph-row[\\s\\S]*?<\\/article>/g)]
  .map(match => match[0]);
console.log(JSON.stringify({html, order: rows.map(row =>
  (row.match(/data-event-id="([^"]+)/) || [])[1]),
  foSpan: rows.slice(0, 3).map(row => row.includes('data-flow-key="fo:codex:focus-1"')),
  taskSpan: rows.slice(1, 4).map(row => row.includes(
    'data-flow-key="task:workflow:project-cockpit"'))}));
"""
        )
        assert isinstance(out, dict)
        html = out["html"]

        self.assertIn('data-next-project-detail="cargento"', html)
        self.assertIn("FOCUS · THIS BROWSER", html)
        self.assertIn("SEMANTIC TIMELINE", html)
        self.assertIn('data-next-cockpit-action="graph-mode"', html)
        self.assertNotIn('data-calm="project-graph-mode"', html)
        self.assertEqual(["fo-a", "task-a", "fo-b", "task-b"], out["order"])
        self.assertEqual([True, True, True], out["foSpan"])
        self.assertEqual([True, True, True], out["taskSpan"])
        self.assertNotIn("pc-project-tabs", html)
        self.assertNotIn("Other project sessions", html)
        self.assertNotIn("Evidence / limits", html)
        self.assertNotIn("data-branch-edge=", html)
        self.assertNotIn("data-merge-edge=", html)

    def test_focus_reads_label_alias_then_saves_only_under_the_stable_project_key(self) -> None:
        label_key = "cargento.projectGoal.v1:cargento"
        stable_key = "cargento.projectGoal.v1:spacedock-research%2Fcargento"
        out = self.run_fixture(
            """
const before = __els.app.innerHTML;
const input = {value:"Stable desired outcome",
  dataset:{nextCockpitProject:"spacedock-research/cargento"},
  closest(selector){ return selector === "[data-next-cockpit-focus-input]" ? this : null; }};
__fire("input", {target:input});
const save = {dataset:{nextCockpitAction:"focus-save"},
  closest(selector){ return selector === "[data-next-cockpit-action]" ? this : null; }};
__fire("click", {target:save, preventDefault(){}});
console.log(JSON.stringify({before, stored:__store, writes:__storageWrites}));
""",
            storage={label_key: "Legacy label focus"},
        )
        assert isinstance(out, dict)

        self.assertIn("Legacy label focus", out["before"])
        self.assertIn("stable project key · spacedock-research/cargento", out["before"])
        self.assertEqual("Stable desired outcome", out["stored"][stable_key])
        self.assertEqual("Legacy label focus", out["stored"][label_key])
        self.assertIn(stable_key, out["writes"])

    def test_next_bundle_keeps_steer_local_and_terminal_input_absent(self) -> None:
        out = self.run_fixture(
            """
console.log(JSON.stringify({
  steer: nextProjectSteer("cargento", {steers:[]}),
  terminalPower: projectTerminalMount.toString(),
  originPath: projectTerminalLookup.toString(),
  parts: __els.app.innerHTML
}));
"""
        )
        assert isinstance(out, dict)

        self.assertIn("STEER · LOCAL ONLY", out["steer"])
        self.assertIn("disableStdin:true", out["terminalPower"])
        self.assertIn("/api/interaction/origin", out["originPath"])
        self.assertNotIn("/api/interaction/input", out["parts"])
        self.assertNotIn("/api/interaction/control", out["parts"])


if __name__ == "__main__":
    unittest.main()
