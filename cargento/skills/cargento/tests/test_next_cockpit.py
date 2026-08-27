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
  harnesses: [{key: "codex", label: "Codex"}, {key:"pi", label:"Pi"},
    {key:"claude", label:"Claude"}],
  sessions: [{sid: "focus-1", harness: "codex", project: "cargento",
    project_key: "spacedock-research/cargento", state: "working", active: true,
    last_activity: 104, title: "Shape project cockpit", subagent_hierarchy: [
      {name:"Banach", observer_sid:"child-b", depth:1,
        assignment:"Fix the completion guard", assignment_status:"structured dispatch artifact",
        workflow_entity:"project-cockpit", workflow_stage:"shaping",
        workflow_binding:"/repo/.spacedock/explore", work_item_id:"workflow:project-cockpit"},
      {name:"Copernicus", observer_sid:"child-c", depth:1,
        assignment:"Fix dispatch authority", assignment_status:"structured dispatch artifact",
        workflow_entity:"project-cockpit", workflow_stage:"shaping",
        workflow_binding:"/repo/.spacedock/explore", work_item_id:"workflow:project-cockpit"}
    ], subagents: []},
    {sid:"pi-idle", harness:"pi", project:"cargento",
      project_key:"spacedock-research/cargento", state:"idle", active:true,
      last_activity:99, title:"Pi result", last_output:"Pi finished", subagents:[]},
    {sid:"claude-idle", harness:"claude", project:"cargento",
      project_key:"spacedock-research/cargento", state:"idle", active:true,
      last_activity:98, title:"Claude result", last_output:"Claude finished", subagents:[]}]
};
const __task = "workflow:project-cockpit";
const __semantic = {facts: [
  {fact_id:"fo-a", at:104, type:"user_message", summary:"Newest direction",
    source_session:{harness:"codex", sid:"focus-1"},
    evidence:{source:"root transcript", confidence:"exact"}},
  {fact_id:"task-a", at:103, type:"prepared_dispatch", summary:"Dispatch cockpit",
    source_session:{harness:"codex", sid:"focus-1"}, work_item_id:__task,
    evidence:{source:"dispatch artifact", confidence:"exact"}},
  {fact_id:"fo-b", at:102, type:"user_message", summary:"Correct the lane order",
    source_session:{harness:"codex", sid:"focus-1"},
    evidence:{source:"root transcript", confidence:"exact"}},
  {fact_id:"task-b", at:101, type:"stage_transition", stage:"shaping",
    summary:"Shaping cockpit", work_item_id:__task,
    evidence:{source:"workflow state", confidence:"exact"}},
  {fact_id:"gate-a", at:100, type:"gate_decision", source_kind:"gate",
    summary:"project-cockpit · review · approve", scope:"project", by:"person:captain",
    decision:"approve", stage:"review", application_state:"consumed",
    target_stage:"shaping", work_item_id:__task,
    evidence:{source:"entity gate", confidence:"exact"}}
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
nextRoute = nextRouteFromFragment("#n=project:cargento:course");
renderNext();
await __settle();await __settle();
const html = __els.app.innerHTML;
const rows = [...html.matchAll(/<article class="next-course-episode"[\\s\\S]*?<\\/article>/g)]
  .map(match => match[0]);
console.log(JSON.stringify({html, rows}));
"""
        )
        assert isinstance(out, dict)
        html = out["html"]

        self.assertIn('data-next-project-detail="cargento"', html)
        self.assertIn('data-next-cockpit-panel="course"', html)
        self.assertIn("Other directions (2)", html)
        self.assertIn("Project cockpit · State change", html)
        self.assertNotIn("FOCUS · THIS BROWSER", html)
        self.assertNotIn("SEMANTIC TIMELINE", html)
        self.assertNotIn('data-next-cockpit-action="graph-mode"', html)
        self.assertNotIn('data-calm="project-graph-mode"', html)
        self.assertEqual(2, len(out["rows"]))
        self.assertNotIn("pc-project-tabs", html)
        self.assertNotIn("Other project sessions", html)
        self.assertNotIn("Evidence / limits", html)
        self.assertNotIn("data-branch-edge=", html)
        self.assertNotIn("data-merge-edge=", html)

    def test_task_subject_and_four_tabs_own_one_operator_question_each(self) -> None:
        out = self.run_fixture(
            """
const html = __els.app.innerHTML;
const tabs = [...html.matchAll(/<button[^>]*role="tab"[^>]*>[\\s\\S]*?<\\/button>/g)]
  .map(match => match[0]);
const panel = (html.match(/<section[^>]*role="tabpanel"[\\s\\S]*?<\\/section>/) || [""])[0];
console.log(JSON.stringify({html,tabs,panel}));
"""
        )
        assert isinstance(out, dict)

        self.assertIn("<h2>Project cockpit <small>· Shaping</small></h2>", out["html"])
        self.assertEqual(4, len(out["tabs"]))
        for label in ("Now", "Course", "Decisions", "Console"):
            self.assertTrue(any(f">{label}</button>" in tab for tab in out["tabs"]))
        self.assertTrue(
            any('aria-selected="true"' in tab and ">Now</button>" in tab for tab in out["tabs"])
        )
        self.assertEqual(1, out["html"].count('role="tabpanel"'))
        self.assertIn('data-next-cockpit-panel="now"', out["html"])
        self.assertIn("Outcome &amp; Focus", out["html"])
        self.assertIn("Needs you", out["html"])
        self.assertIn("Active work", out["html"])
        self.assertIn("Show project plan", out["html"])
        self.assertNotIn("CURRENT FOCUS · DERIVED", out["html"])
        self.assertNotIn('data-next-project-section="plan"', out["html"])
        self.assertNotIn('data-next-project-section="going-on"', out["html"])
        self.assertNotIn("data-next-delegation", out["html"])
        self.assertNotIn("SEMANTIC TIMELINE", out["html"])
        self.assertNotIn('data-semantic-kind="decision"', out["html"])
        self.assertNotIn("EXACT SESSION TERMINAL", out["html"])
        self.assertNotIn('data-next-project-section="workstream"', out["html"])

    def test_now_is_a_calm_command_briefing_not_the_old_dashboard(self) -> None:
        out = self.run_fixture(
            """
const group=nextProjectGroups()[0];
const semantic=JSON.parse(JSON.stringify(__semantic));
semantic.projections.command_attention=[
  {projection_id:"captain-auth",at:110,owner:"CAPTAIN",kind:"push_pr",
    label:"the shaped project cockpit",question:"Approve pushing this candidate?",
    evidence:{source:"exact assistant authorization request",confidence:"exact"}},
  {projection_id:"fo-recovery",at:109,owner:"FO",kind:"recovery",
    label:"Retry workflow discovery",question:"Retry workflow discovery",
    evidence:{source:"project workflow discovery",confidence:"exact"}}
];
const observation={semantic,workflow_discovery:{state:"error",reason:"timed out"},sources:{}};
nextCockpitContexts.set(nextCockpitContextKey(group,null),{data:observation,revision:105});
renderNext();
const html=__els.app.innerHTML;
const panel=(html.match(/<section class="next-cockpit-panel"[\\s\\S]*<\\/section>/)||[""])[0];
const visible=panel
  .replace(/<details(?![^>]*\\bopen\\b)[^>]*>[\\s\\S]*?<\\/details>/g," ")
  .replace(/<[^>]+>/g," ").replace(/&[^;]+;/g," ")
  .replace(/\\s+/g," ").trim();
console.log(JSON.stringify({html,panel,visible,visibleWords:visible ? visible.split(" ").length : 0,
  primary:(html.match(/data-next-cockpit-primary/g)||[]).length}));
"""
        )
        assert isinstance(out, dict)
        panel = out["panel"]

        pre_correction_visible_words = 197
        self.assertLessEqual(out["visibleWords"] * 4, pre_correction_visible_words)
        self.assertEqual(4, out["primary"])
        self.assertIn("Project cockpit <small>· Shaping</small>", out["html"])
        self.assertIn("Approve pushing this candidate?", panel)
        self.assertIn("Fix the completion guard", panel)
        self.assertIn("Outcome", panel)
        self.assertIn("Focus", panel)
        self.assertIn("Not set", panel)
        self.assertIn('data-next-cockpit-action="memo-edit"', panel)
        for old_surface in (
            "Latest decisions",
            "CURRENT FOCUS · DERIVED",
            "COMPLETED RESULT",
            'data-next-project-section="plan"',
            "data-next-delegation",
            "STEER · LOCAL ONLY",
            "GUARDRAILS · LOCAL ONLY",
            "<textarea",
        ):
            self.assertNotIn(old_surface, panel)
        self.assertNotIn("Retry workflow discovery", out["visible"])
        self.assertNotIn("workflow discovery failed", out["visible"])
        self.assertIn("data-next-cockpit-system-details", panel)
        self.assertIn("workflow discovery failed", panel)

    def test_scope_tree_and_memos_share_project_session_marker_grammar(self) -> None:
        out = self.run_fixture(
            """
const project=__els.app.innerHTML;
const narrowest={
  same:nextCockpitFactSetScope([
    {type:"result",source_session:{harness:"codex",sid:"focus-1"}},
    {type:"user_message",source_session:{harness:"codex",sid:"focus-1"}}]),
  mixed:nextCockpitFactSetScope([
    {type:"result",source_session:{harness:"codex",sid:"focus-1"}},
    {type:"result",source_session:{harness:"pi",sid:"pi-idle"}}]),
  unknown:nextCockpitFactSetScope([
    {type:"result",source_session:{harness:"codex",sid:"focus-1"}},
    {type:"result"}])
};
nextRoute=nextRouteFromFragment("#n=project:cargento:pi%3Api-idle");
renderNext();
await __settle();await __settle();
const session=__els.app.innerHTML;
console.log(JSON.stringify({project,session,narrowest}));
"""
        )
        assert isinstance(out, dict)

        self.assertIn(
            'data-next-cockpit-scope="project" aria-current="page" data-scope-kind="project"',
            out["project"],
        )
        self.assertIn('class="next-scope-marker next-scope-marker--square"', out["project"])
        self.assertIn('class="next-scope-cue next-scope-cue--project"', out["project"])
        self.assertIn(">PROJECT</strong>", out["project"])
        self.assertIn('data-scope-owner="project"', out["project"])
        self.assertIn('data-scope-owner="pi:pi-idle"', out["session"])
        self.assertIn('class="next-scope-marker next-scope-marker--round"', out["session"])
        self.assertIn('class="next-scope-cue next-scope-cue--session"', out["session"])
        self.assertIn(">SESSION</strong>", out["session"])
        self.assertEqual("session", out["narrowest"]["same"]["kind"])
        self.assertEqual("project", out["narrowest"]["mixed"]["kind"])
        self.assertEqual("unknown", out["narrowest"]["unknown"]["kind"])
        self.assertIn('data-parent-session="codex:focus-1"', out["project"])
        self.assertIn('data-scope-owner="codex:focus-1"', out["project"])

    def test_selected_session_keeps_project_briefing_ownership_explicit(self) -> None:
        out = self.run_fixture(
            """
nextRoute=nextRouteFromFragment("#n=project:cargento:codex%3Afocus-1");
renderNext();await __settle();await __settle();
const html=__els.app.innerHTML;
const task=(html.match(/<section[^>]*data-next-cockpit-task-subject[\\s\\S]*?<\\/section>/)||[""])[0];
const needs=(html.match(/<section class="next-cockpit-needs"[\\s\\S]*?<\\/section>/)||[""])[0];
const active=(html.match(/<section[^>]*data-next-cockpit-active-delegation[\\s\\S]*?<\\/section>/)||[""])[0];
const switcher=(html.match(/<details class="next-cockpit-scope-switcher"[\\s\\S]*?<\\/details>/)||[""])[0];
console.log(JSON.stringify({html,task,needs,active,switcher}));
"""
        )
        assert isinstance(out, dict)

        self.assertIn("Viewing session · Codex · working", out["html"])
        self.assertIn('data-next-cockpit-viewing-session="codex:focus-1"', out["html"])
        for project_surface in (out["task"], out["needs"], out["active"]):
            self.assertEqual(1, project_surface.count(">PROJECT</strong>"))
            self.assertIn('data-scope-kind="project"', project_surface)
        self.assertNotIn(">SESSION</strong>", out["task"])
        self.assertIn("Viewing session · Codex · working", out["switcher"])
        self.assertIn("Change scope", out["switcher"])
        self.assertIn('data-next-cockpit-scope="project"', out["switcher"])
        self.assertIn('data-next-cockpit-scope="codex:focus-1"', out["switcher"])

    def test_course_interleaves_project_session_and_unknown_provenance_cues(self) -> None:
        out = self.run_fixture(
            """
nextCockpitContexts.clear();
const semantic=JSON.parse(JSON.stringify(__semantic));
semantic.facts.push(
  {fact_id:"unknown-input",at:101.5,type:"user_message",intent_promoted:true,
    summary:"Unattributed operator note",evidence:{source:"source unavailable",confidence:"unknown"}},
  {fact_id:"review-result",at:102.5,type:"result",summary:"Review synthesis returned",
    detail:"Review changed the course:\\n- Keep scope visible.",
    source_session:{harness:"codex",sid:"focus-1"},work_item_id:__task,
    evidence:{source:"assistant final answer",confidence:"exact"}}
);
__fetchImpl=async()=>({ok:true,json:async()=>({semantic,child_assignments:[],observers:[]})});
nextRoute=nextRouteFromFragment("#n=project:cargento:course");
renderNext();await __settle();await __settle();await __settle();
const html=__els.app.innerHTML;
const rows=[...html.matchAll(/<article class="next-course-episode"[\\s\\S]*?<\\/article>/g)]
  .map(match=>match[0]);
const directions=[...html.matchAll(/<article class="next-course-direction"[\\s\\S]*?<\\/article>/g)]
  .map(match=>match[0]);
console.log(JSON.stringify({html,rows,directions}));
"""
        )
        assert isinstance(out, dict)

        session_rows = [row for row in out["directions"] if "Newest direction" in row]
        project_rows = [row for row in out["rows"] if "Shaping cockpit" in row]
        unknown_rows = [row for row in out["directions"] if "Unattributed operator note" in row]
        derived_rows = [row for row in out["rows"] if "DERIVED COURSE CHANGE" in row]
        self.assertEqual(1, len(session_rows))
        self.assertIn('data-scope-kind="session"', session_rows[0])
        self.assertEqual(1, len(project_rows))
        self.assertIn('data-scope-kind="project"', project_rows[0])
        self.assertEqual(1, len(unknown_rows))
        self.assertIn('data-scope-kind="unknown"', unknown_rows[0])
        self.assertIn("SCOPE UNKNOWN", unknown_rows[0])
        self.assertEqual(1, len(derived_rows))
        self.assertIn('data-scope-kind="session"', derived_rows[0])
        self.assertIn("DERIVED COURSE CHANGE", derived_rows[0])

    def test_paired_direction_stays_with_its_change_and_is_not_duplicated(self) -> None:
        out = self.run_fixture(
            """
const semantic=JSON.parse(JSON.stringify(__semantic));
semantic.facts.find(fact=>fact.fact_id==="fo-a").work_item_id=__task;
semantic.facts.push({fact_id:"paired-result",at:106,type:"result",summary:"Layout corrected",
  detail:"Fixed and live on port 8766.\\n\\nCheckpoint: `abc1234`.",
  source_session:{harness:"codex",sid:"focus-1"},work_item_id:__task,
  evidence:{source:"assistant result",confidence:"exact"}});
semantic.projections.steering_episodes=[{episode_id:"pair-a",intent_id:"intent-a",
  adaptation_fact:"paired-result",confidence:"structural"}];
const html=nextCockpitCourse(nextProjectGroups()[0],semantic,[]);
const primary=(html.match(/<article class="next-course-episode"[\\s\\S]*?<\\/article>/g)||[])
  .find(row=>row.includes("Layout corrected"))||"";
const other=(html.match(/<details class="next-course-directions"[\\s\\S]*?<\\/details>/)||[""])[0];
console.log(JSON.stringify({html,primary,other}));
"""
        )
        assert isinstance(out, dict)

        self.assertIn("Newest direction", out["primary"])
        self.assertIn("Layout corrected", out["primary"])
        self.assertIn("assistant result", out["primary"])
        self.assertNotIn("Newest direction", out["other"])
        self.assertEqual(1, out["html"].count("Newest direction"))

    def test_course_pairing_requires_ordered_exact_task_binding_and_meaningful_change(self) -> None:
        out = self.run_fixture(
            """
const courseCase=(direction,result,workItems=[])=>{
  const semantic={facts:[direction,result],work_items:[
    {work_item_id:__task,label:"project-cockpit",kind:"workflow_item"},...workItems],
    relations:[],projections:{operator_intents:[{projection_id:"intent",at:direction.at,
      summary:direction.summary,derived_from:direction.fact_id}],steering_episodes:[{
      episode_id:"pair",intent_id:"intent",adaptation_fact:result.fact_id,
      confidence:"structural"}],trail_heads:[]}};
  const html=nextCockpitCourse(nextProjectGroups()[0],semantic,[]);
  return {html,primary:(html.match(/<article class="next-course-episode"/g)||[]).length,
    other:(html.match(/<article class="next-course-direction"/g)||[]).length};
};
const direction={fact_id:"direction",at:100,type:"user_message",intent_promoted:true,
  summary:"Keep the exact task boundary",work_item_id:__task,
  source_session:{harness:"codex",sid:"focus-1"},
  evidence:{source:"root transcript",confidence:"exact"}};
const unbound=courseCase(direction,{fact_id:"generic",at:101,type:"result",
  summary:"Ordinary worker returned",source_session:{harness:"codex",sid:"child"},
  evidence:{source:"ordinary child result",confidence:"exact"}});
const inverted=courseCase({...direction,at:103},{fact_id:"stage-before",at:102,
  type:"stage_transition",stage:"review",summary:"Review stage",work_item_id:__task,
  evidence:{source:"workflow state",confidence:"exact"}});
const otherTask="workflow:other";
const mismatched=courseCase(direction,{fact_id:"other-stage",at:104,
  type:"stage_transition",stage:"review",summary:"Other review stage",work_item_id:otherTask,
  evidence:{source:"workflow state",confidence:"exact"}},[
    {work_item_id:otherTask,label:"other-task",kind:"workflow_item"}]);
const positive=courseCase(direction,{fact_id:"exact-stage",at:105,
  type:"stage_transition",stage:"review",summary:"Exact review stage",work_item_id:__task,
  evidence:{source:"workflow state",confidence:"exact"}});
console.log(JSON.stringify({unbound,inverted,mismatched,positive}));
"""
        )
        assert isinstance(out, dict)

        self.assertEqual(
            {"primary": 0, "other": 1}, {key: out["unbound"][key] for key in ("primary", "other")}
        )
        for key in ("inverted", "mismatched"):
            self.assertEqual(1, out[key]["primary"])
            self.assertEqual(1, out[key]["other"])
            self.assertNotIn("<b>Direction</b>", out[key]["html"])
        self.assertEqual(1, out["positive"]["primary"])
        self.assertEqual(0, out["positive"]["other"])
        self.assertIn("<b>Direction</b>", out["positive"]["html"])

    def test_sixteen_exact_directions_fold_when_no_course_change_is_observed(self) -> None:
        out = self.run_fixture(
            """
const facts=Array.from({length:16},(_,index)=>({fact_id:`direction-${index+1}`,
  at:index+1,type:"user_message",intent_promoted:true,summary:`Direction ${index+1}`,
  source_session:{harness:"codex",sid:"focus-1"},
  evidence:{source:"root transcript",confidence:"exact"}}));
const semantic={facts,work_items:[],relations:[],projections:{
  operator_intents:facts.map((fact,index)=>({projection_id:`intent-${index+1}`,
    at:fact.at,summary:fact.summary,derived_from:fact.fact_id})),
  steering_episodes:[],trail_heads:[]}};
const html=nextCockpitCourse(nextProjectGroups()[0],semantic,[]);
const primary=[...html.matchAll(/<article class="next-course-episode"/g)].length;
console.log(JSON.stringify({html,primary}));
"""
        )
        assert isinstance(out, dict)

        self.assertEqual(0, out["primary"])
        self.assertIn("No source-backed course changes observed", out["html"])
        self.assertIn("Other directions (16)", out["html"])
        self.assertIn("<details", out["html"])
        for number in range(1, 17):
            self.assertEqual(1, out["html"].count(f"Direction {number}<"))
        self.assertLess(out["html"].index("Direction 1<"), out["html"].index("Direction 16<"))

    def test_completed_tracked_work_lives_only_in_course(self) -> None:
        out = self.run_fixture(
            """
const claude=__dashboard.sessions.find(session=>session.harness==="claude");
claude.tasks=[{status:"completed",subject:"Verify accepted project cockpit"}];
renderNext();await __settle();
const now=__els.app.innerHTML;
nextRoute=nextRouteFromFragment("#n=project:cargento:course");
renderNext();await __settle();await __settle();
console.log(JSON.stringify({now,course:__els.app.innerHTML}));
"""
        )
        assert isinstance(out, dict)

        self.assertNotIn("Verify accepted project cockpit", out["now"])
        self.assertIn("Verify accepted project cockpit", out["course"])
        self.assertIn('data-next-project-activity="done"', out["course"])

    def test_decisions_use_fact_scope_not_selected_session(self) -> None:
        out = self.run_fixture(
            """
nextCockpitContexts.clear();
const semantic=JSON.parse(JSON.stringify(__semantic));
semantic.facts.push({fact_id:"session-decision",at:100.5,type:"gate_decision",
  source_kind:"gate",scope:"session",by:"person:captain",decision:"hold",stage:"review",
  application_state:"pending",work_item_id:__task,
  source_session:{harness:"pi",sid:"pi-idle"},
  evidence:{source:"session gate",confidence:"exact"}});
__fetchImpl=async()=>({ok:true,json:async()=>({semantic,child_assignments:[],observers:[]})});
nextRoute=nextRouteFromFragment("#n=project:cargento:pi%3Api-idle:decisions");
renderNext();await __settle();await __settle();await __settle();
const rows=[...__els.app.innerHTML.matchAll(/<article class="pc-graph-row[\\s\\S]*?<\\/article>/g)]
  .map(match=>match[0]);
console.log(JSON.stringify({rows,html:__els.app.innerHTML}));
"""
        )
        assert isinstance(out, dict)

        project_rows = [row for row in out["rows"] if 'data-action="approved"' in row]
        session_rows = [row for row in out["rows"] if 'data-action="held"' in row]
        self.assertEqual(1, len(project_rows))
        self.assertIn('data-scope-kind="project"', project_rows[0])
        self.assertIn(">PROJECT</strong>", project_rows[0])
        self.assertEqual(1, len(session_rows))
        self.assertIn('data-scope-kind="session"', session_rows[0])
        self.assertIn(">SESSION</strong>", session_rows[0])

    def test_console_names_session_scope_and_project_root_stays_non_session(self) -> None:
        out = self.run_fixture(
            """
nextRoute=nextRouteFromFragment("#n=project:cargento:console");
renderNext();await __settle();
const project=__els.app.innerHTML;
nextRoute=nextRouteFromFragment("#n=project:cargento:codex%3Afocus-1:console");
renderNext();await __settle();
const session=__els.app.innerHTML;
console.log(JSON.stringify({project,session}));
"""
        )
        assert isinstance(out, dict)

        project_panel = out["project"][out["project"].index('data-next-cockpit-panel="console"') :]
        session_panel = out["session"][out["session"].index('data-next-cockpit-panel="console"') :]
        self.assertIn('data-scope-kind="project"', project_panel)
        self.assertIn(">PROJECT</strong>", project_panel)
        self.assertNotIn('data-scope-kind="session"', project_panel)
        self.assertIn('data-scope-kind="session"', session_panel)
        self.assertIn(">SESSION</strong>", session_panel)
        self.assertIn("STEER · LOCAL ONLY", project_panel)
        self.assertIn("GUARDRAILS · LOCAL ONLY", project_panel)
        self.assertIn("data-next-delegation", project_panel)
        self.assertIn("STEER · LOCAL ONLY", session_panel)
        self.assertIn("Raw project status", project_panel)
        self.assertNotIn("Latest decisions", project_panel)

    def test_local_tab_permalink_and_arrow_keys_preserve_project_session_route(self) -> None:
        out = self.run_fixture(
            """
const parsed = nextRouteFromFragment("#n=project:cargento:pi%3Api-idle:course");
const roundTrip = nextFragmentForRoute(parsed);
nextRoute = parsed;
renderNext();
await __settle();await __settle();
const course = __els.app.innerHTML;
const target = {dataset:{nextCockpitAction:"tab",arg:"course"},
  closest(selector){ return selector === "[data-next-cockpit-action]" ? this : null; }};
__fire("keydown", {target,key:"ArrowRight",preventDefault(){}});
const afterKey = __els.app.innerHTML;
console.log(JSON.stringify({parsed,roundTrip,course,afterKey,hash:location.hash}));
"""
        )
        assert isinstance(out, dict)

        self.assertEqual("pi:pi-idle", out["parsed"]["focus"])
        self.assertEqual("course", out["parsed"]["tab"])
        self.assertEqual("#n=project:cargento:pi%3Api-idle:course", out["roundTrip"])
        self.assertIn('data-next-cockpit-panel="course"', out["course"])
        self.assertIn('aria-selected="true" tabindex="0">Course</button>', out["course"])
        self.assertIn('data-next-cockpit-panel="decisions"', out["afterKey"])
        self.assertEqual("#n=project:cargento:pi%3Api-idle:decisions", out["hash"])

    def test_console_waits_for_origin_lookup_then_opens_read_only_terminal(self) -> None:
        out = self.run_fixture(
            """
__fetchImpl = async url => String(url).startsWith("/api/interaction/origin")
  ? ({ok:true,json:async()=>({state:"registered",origin:{session_name:"Cargento",
      window_index:1,pane_index:1},origin_id_hint:"origin-1"})})
  : ({ok:true,json:async()=>({semantic:__semantic,child_assignments:[],observers:[]})});
nextRoute = nextRouteFromFragment("#n=project:cargento:codex%3Afocus-1:console");
renderNext();
const pending = __els.app.innerHTML;
await __settle();
const available = __els.app.innerHTML;
const open = {dataset:{nextCockpitAction:"terminal-open",arg:"codex:focus-1"},
  closest(selector){ return selector === "[data-next-cockpit-action]" ? this : null; }};
__fire("click", {target:open,preventDefault(){}});
const opened = __els.app.innerHTML;
console.log(JSON.stringify({pending,available,opened}));
"""
        )
        assert isinstance(out, dict)

        self.assertIn('data-next-cockpit-panel="console"', out["pending"])
        self.assertNotIn("Open terminal", out["pending"])
        self.assertIn("Open terminal", out["available"])
        self.assertIn("EXACT SESSION TERMINAL", out["available"])
        self.assertIn("read-only", out["opened"])
        self.assertIn('aria-label="Read-only terminal output"', out["opened"])
        for html in out.values():
            self.assertNotIn("CURRENT FOCUS · DERIVED", html)
            self.assertNotIn("Project cockpit · User direction", html)
            self.assertNotIn('data-semantic-kind="decision"', html)

    def test_course_is_task_first_source_labeled_and_omits_future_history(self) -> None:
        out = self.run_fixture(
            """
nextCockpitContexts.clear();
const semantic = JSON.parse(JSON.stringify(__semantic));
semantic.facts.push(
  {fact_id:"review-result",at:102.5,type:"result",summary:"Review synthesis returned",
    detail:"Review changed the course:\\n- Show task ownership, not lifecycle noise.\\n" +
      "- Separate project overview from session evidence.\\n\\nFuture — proposed, not dispatched",
    source_session:{harness:"codex",sid:"focus-1"},work_item_id:__task,
    evidence:{source:"assistant final_answer followed by terminal turn state",confidence:"exact"}},
  {fact_id:"live-result",at:102.4,type:"result",summary:"Fixed and live on port 8766.",
    detail:"Fixed and live on port 8766.\\n\\nCheckpoint: `179a80d`.",
    source_session:{harness:"codex",sid:"focus-1"},work_item_id:__task,
    evidence:{source:"assistant final_answer followed by terminal turn state",confidence:"exact"}}
);
__fetchImpl = async url => ({ok:true,json:async() => ({semantic,
  child_assignments:[{name:"Banach",workItemId:__task,source:"structured assignment"}],
  observers:[]})});
nextRoute = nextRouteFromFragment("#n=project:cargento:course");
renderNext();
await __settle();await __settle();await __settle();
console.log(JSON.stringify({html:__els.app.innerHTML}));
"""
        )
        assert isinstance(out, dict)
        html = out["html"]

        self.assertIn('data-next-cockpit-panel="course"', html)
        self.assertIn("Other directions (2)", html)
        self.assertIn("EXACT DIRECTION", html)
        self.assertIn("Project cockpit · State change", html)
        self.assertIn("EXACT STATE CHANGE", html)
        self.assertIn("Project cockpit · Result", html)
        self.assertIn("EXACT RESULT", html)
        self.assertIn("Project cockpit · Course change", html)
        self.assertIn("DERIVED COURSE CHANGE", html)
        self.assertIn("Show task ownership, not lifecycle noise.", html)
        self.assertIn("Separate project overview from session evidence.", html)
        self.assertIn("Banach", html)
        self.assertIn("<details", html[: html.index("Banach")])
        self.assertNotIn("Future", html)
        self.assertNotIn("proposed, not dispatched", html)
        self.assertIn("179a80d", html)
        self.assertIn("<h2>Project cockpit <small>· Shaping</small></h2>", html)
        self.assertNotIn("CURRENT FOCUS · DERIVED", html)

    def test_defaults_to_all_sessions_and_links_every_idle_peer(self) -> None:
        out = self.run_fixture(
            """
const html = __els.app.innerHTML;
console.log(JSON.stringify({html, query:[...nextCockpitContexts.keys()]}));
"""
        )
        assert isinstance(out, dict)
        html = out["html"]

        self.assertIn('class="next-cockpit-scope-tree"', html)
        self.assertIn('data-next-cockpit-scope="project" aria-current="page"', html)
        self.assertNotIn("All sessions", html)
        self.assertNotIn('role="tablist" aria-label="Project sessions"', html)
        self.assertIn("Codex", html)
        self.assertIn("Pi", html)
        self.assertIn("Claude", html)
        self.assertIn("pi-idle", html)
        self.assertIn("claude-idle", html)
        self.assertIn("#n=project:cargento:pi%3Api-idle", html)
        self.assertTrue(any(key.endswith("\n") for key in out["query"]))

    def test_all_sessions_aggregates_exact_running_workers_with_parent_and_task(self) -> None:
        out = self.run_fixture(
            """
const html = __els.app.innerHTML;
const task = (html.match(/<section[^>]*data-next-cockpit-active-delegation[\\s\\S]*?<\\/section>/) || [""])[0];
console.log(JSON.stringify({html, task}));
"""
        )
        assert isinstance(out, dict)

        self.assertIn("Banach", out["task"])
        self.assertIn("Copernicus", out["task"])
        self.assertIn("Active work", out["task"])
        self.assertIn("Fix the completion guard", out["task"])
        self.assertIn("Fix dispatch authority", out["task"])
        self.assertNotIn("Project cockpit · 2 active assignments", out["task"])
        self.assertIn('data-work-item="workflow:project-cockpit"', out["task"])
        self.assertIn('data-parent-session="codex:focus-1"', out["task"])

    def test_active_work_does_not_promote_an_unassigned_child(self) -> None:
        out = self.run_fixture(
            """
const group=nextProjectGroups()[0];
group.sessions[0].subagent_hierarchy=[{name:"Unbound",observer_sid:"child-x",depth:1}];
const html=nextCockpitActiveDelegation(group,{semantic:__semantic});
console.log(JSON.stringify({html}));
"""
        )
        assert isinstance(out, dict)

        self.assertNotIn("assignment unavailable", out["html"])
        self.assertNotIn("Unbound", out["html"])
        self.assertIn("Shape project cockpit", out["html"])
        self.assertIn("Work is active", out["html"])
        self.assertNotIn("Current task is active", out["html"])

    def test_missing_task_identity_keeps_exact_working_activity_without_invention(self) -> None:
        out = self.run_fixture(
            """
nextData.sessions=[{sid:"focus-1",harness:"codex",project:"cargento",
  project_key:"spacedock-research/cargento",state:"working",active:true,
  last_activity:104,title:null,state_detail:"running 1 subagent",
  subagent_hierarchy:[{name:"Unbound",observer_sid:"child-x",depth:1}],subagents:[{}]}];
const group=nextProjectGroups()[0];
const observation={semantic:{facts:[],work_items:[],relations:[],projections:{
  trail_heads:[],command_attention:[]}},child_assignments:[],observers:[]};
nextCockpitContexts.clear();nextCockpitRequests.clear();
nextCockpitContexts.set(nextCockpitContextKey(group,null),{data:observation,revision:nextData.generated});
nextRoute=nextRouteFromFragment("#n=project:cargento");
renderNext();await __settle();await __settle();
const html=__els.app.innerHTML;
const task=(html.match(/<section[^>]*data-next-cockpit-task-subject[\\s\\S]*?<\\/section>/)||[""])[0];
const active=(html.match(/<section[^>]*data-next-cockpit-active-delegation[\\s\\S]*?<\\/section>/)||[""])[0];
const scope=(html.match(/<nav class="next-cockpit-scope-tree"[\\s\\S]*?<\\/nav>/)||[""])[0];
const panel=(html.match(/<section class="next-cockpit-panel"[\\s\\S]*<\\/section>/)||[""])[0];
const visible=panel.replace(/<details(?![^>]*\\bopen\\b)[^>]*>[\\s\\S]*?<\\/details>/g," ")
  .replace(/<[^>]+>/g," ").replace(/&[^;]+;/g," ").replace(/\\s+/g," ").trim();
console.log(JSON.stringify({html,task,active,scope,visibleWords:visible?visible.split(" ").length:0,
  primary:(html.match(/data-next-cockpit-primary/g)||[]).length}));
"""
        )
        assert isinstance(out, dict)

        self.assertEqual(4, out["primary"])
        self.assertLessEqual(out["visibleWords"], 48)
        self.assertIn("WORKFLOW TASK", out["task"])
        self.assertIn("Not observed", out["task"])
        self.assertEqual(1, out["task"].count(">PROJECT</strong>"))
        self.assertNotIn("data-work-item", out["task"])
        for invention in (
            "CURRENT TASK",
            "Project work",
            "State unavailable",
            "Current task is active",
            "assignment unavailable",
            "Unbound",
        ):
            self.assertNotIn(invention, out["html"])
        self.assertIn("Work is active", out["active"])
        self.assertIn("running 1 subagent", out["active"])
        self.assertIn("<small>1 session</small>", out["scope"])
        self.assertIn(
            '<span class="next-cockpit-scope-state">working</span>'
            "<small>running 1 subagent</small>",
            out["scope"],
        )
        self.assertEqual(1, out["scope"].count(">working<"))

    def test_session_switcher_is_below_header_and_outcome_first(self) -> None:
        out = self.run_fixture(
            """
const html = __els.app.innerHTML;
const nav = (html.match(/<nav class="next-cockpit-scope-tree"[\\s\\S]*?<\\/nav>/) || [""])[0];
console.log(JSON.stringify({
  header:html.indexOf('class="next-project-detail-header"'),
  nav:html.indexOf('class="next-cockpit-scope-tree"'),
  plan:html.indexOf('data-next-cockpit-plan-details'),
  html, sessionNav:nav
}));
"""
        )
        assert isinstance(out, dict)

        self.assertLess(out["header"], out["nav"])
        self.assertLess(out["nav"], out["plan"])
        self.assertIn(
            '<strong class="next-cockpit-scope-name">Codex</strong>'
            '<span class="next-cockpit-scope-state">working</span>',
            out["sessionNav"],
        )
        self.assertIn("<small>Shape project cockpit</small>", out["sessionNav"])
        self.assertNotIn("<strong>Shape project cockpit", out["sessionNav"])

    def test_focus_keeps_project_status_and_canonical_labels_from_all_context(self) -> None:
        out = self.run_fixture(
            """
nextCockpitContexts.clear();
const focused = {facts:[
  {fact_id:"task-focus",at:110,type:"prepared_dispatch",summary:"Opaque dispatch",
    source_session:{harness:"pi",sid:"pi-idle"},work_item_id:__task,
    evidence:{source:"dispatch artifact",confidence:"exact"}},
  {fact_id:"gate-focus",at:109,type:"gate_decision",source_kind:"gate",
    summary:"opaque-id · review · approve",scope:"project",by:"person:captain",
    decision:"approve",stage:"review",application_state:"consumed",target_stage:"shaping",
    work_item_id:__task,evidence:{source:"entity gate",confidence:"exact"}}
],work_items:[{work_item_id:__task,label:"opaque-id",kind:"workflow_item"}],
relations:[],projections:{operator_intents:[],steering_episodes:[],trail_heads:[
  {work_item_id:__task,status:"prepared",latest_meaningful_event:"task-focus"}],
activity:{nodes:[{kind:"work",at:110,work_item_ids:[__task]}]}}};
__fetchImpl = async url => ({ok:true,json:async() => ({
  semantic:String(url).includes("session=") ? focused : __semantic,
  child_assignments:[],observers:[]
})});
nextRoute = nextRouteFromFragment("#n=project:cargento:pi%3Api-idle:decisions");
renderNext();
await __settle();await __settle();await __settle();
const html=__els.app.innerHTML;
console.log(JSON.stringify({html,requests:[...nextCockpitContexts.keys()]}));
"""
        )
        assert isinstance(out, dict)

        self.assertTrue(any(key.endswith("\n") for key in out["requests"]))
        self.assertTrue(any(key.endswith("\npi:pi-idle") for key in out["requests"]))
        self.assertIn('data-object="Project cockpit"', out["html"])
        self.assertNotIn('data-object="Opaque id"', out["html"])
        self.assertIn('data-scope-kind="project"', out["html"])
        self.assertIn(">PROJECT</strong>", out["html"])
        self.assertIn("<h2>Project cockpit <small>· Shaping</small></h2>", out["html"])
        self.assertIn('data-next-cockpit-panel="decisions"', out["html"])
        self.assertNotIn("PROJECT OVERVIEW", out["html"])
        self.assertNotIn("All events", out["html"])

    def test_session_permalink_selects_exact_focus_and_decisions_filter_is_present(self) -> None:
        out = self.run_fixture(
            """
nextRoute = nextRouteFromFragment("#n=project:cargento:pi%3Api-idle");
renderNext();
await __settle();
await __settle();
const html = __els.app.innerHTML;
console.log(JSON.stringify({html, focus:nextCockpitFocusedSession(nextProjectGroups()[0]) &&
  sessKey(nextCockpitFocusedSession(nextProjectGroups()[0]))}));
"""
        )
        assert isinstance(out, dict)

        self.assertEqual("pi:pi-idle", out["focus"])
        self.assertIn('data-next-cockpit-scope="pi:pi-idle"', out["html"])
        self.assertIn('data-next-cockpit-scope="pi:pi-idle" aria-current="page"', out["html"])
        self.assertIn('data-arg="decisions"', out["html"])

    def test_stale_exact_session_permalink_never_falls_back_to_project_scope(self) -> None:
        out = self.run_fixture(
            """
nextData.sessions=nextData.sessions.filter(session=>sessKey(session)!=="pi:pi-idle");
nextRoute=nextRouteFromFragment("#n=project:cargento:pi%3Api-idle:course");
renderNext();await __settle();
console.log(JSON.stringify({html:__els.app.innerHTML,route:nextFragmentForRoute(nextRoute)}));
"""
        )
        assert isinstance(out, dict)

        self.assertEqual("#n=project:cargento:pi%3Api-idle:course", out["route"])
        self.assertIn("Session filter is outside this payload window", out["html"])
        self.assertIn('href="#n=project:cargento:course"', out["html"])
        self.assertIn("View project root", out["html"])
        self.assertNotIn("data-next-cockpit-memos", out["html"])
        self.assertNotIn('data-next-cockpit-panel="course"', out["html"])

    def test_decisions_view_preserves_canonical_metadata_and_compacts_scan_line(self) -> None:
        out = self.run_fixture(
            """
nextRoute = nextRouteFromFragment("#n=project:cargento:decisions");
renderNext();
await __settle();await __settle();
const html = __els.app.innerHTML;
const rows = [...html.matchAll(/<article class="pc-graph-row[\\s\\S]*?<\\/article>/g)]
  .map(match => match[0]);
console.log(JSON.stringify({html, rows}));
"""
        )
        assert isinstance(out, dict)

        self.assertEqual(1, len(out["rows"]))
        self.assertIn('data-semantic-kind="decision"', out["rows"][0])
        self.assertIn('data-actor="You"', out["rows"][0])
        self.assertIn('data-action="approved"', out["rows"][0])
        self.assertIn('data-object="Project cockpit"', out["rows"][0])
        self.assertIn('data-result="review → shaping"', out["rows"][0])
        self.assertIn("<strong>Approved</strong> Project cockpit · applied", out["rows"][0])
        self.assertIn("<b>Decision mechanics</b> · review → shaping · applied", out["rows"][0])
        self.assertIn("data-next-cockpit-decision-summary", out["html"])
        self.assertIn("Decision application · consumed/applied 1", out["html"])

    def test_gate_application_state_controls_completed_transition_wording(self) -> None:
        out = self.run_fixture(
            """
const lane = {kind:"task", label:"project-cockpit"};
const sentence = application_state => projectGlobalEventSentence({kind:"decision", fact:{
  type:"gate_decision", by:"person:captain", decision:"approve", stage:"review",
  target_stage:"shaping", application_state
}}, lane);
console.log(JSON.stringify({
  consumed:sentence("consumed"), applied:sentence("applied"),
  pending:sentence("pending"), unspent:sentence("unspent"),
  superseded:sentence("superseded"), unknown:sentence(undefined)
}));
"""
        )
        assert isinstance(out, dict)

        self.assertEqual("review → shaping", out["consumed"]["result"])
        self.assertEqual("review → shaping", out["applied"]["result"])
        self.assertEqual(
            "review · decision recorded · pending application", out["pending"]["result"]
        )
        self.assertEqual(
            "review · decision recorded · pending application", out["unspent"]["result"]
        )
        self.assertEqual("review · decision superseded", out["superseded"]["result"])
        self.assertEqual(
            "review · decision recorded · application unknown", out["unknown"]["result"]
        )

    def test_unpromoted_user_fact_never_becomes_a_you_direction(self) -> None:
        out = self.run_fixture(
            """
const semantic = JSON.parse(JSON.stringify(__semantic));
semantic.facts.push({fact_id:"injected",at:106,type:"user_message",
  summary:"Message Type: MESSAGE Sender: /root Payload: keep working",
  intent_promoted:false,source_session:{harness:"codex",sid:"focus-1"},
  evidence:{source:"injected collaboration envelope",confidence:"exact"}});
const registry = projectLaneRegistry(semantic, [], null, __dashboard.sessions);
const events = projectGlobalEvents(semantic, registry, null);
console.log(JSON.stringify({
  ids:events.map(event => event.eventId),
  sentences:events.map(event => projectGlobalEventSentence(event,
    registry.laneByKey.get(event.lane.key)))
}));
"""
        )
        assert isinstance(out, dict)

        self.assertNotIn("injected", out["ids"])
        self.assertFalse(
            any(
                row["actor"] == "You"
                and row["action"] == "directed"
                and "Message Type" in row["result"]
                for row in out["sentences"]
            )
        )

    def test_project_status_reports_exact_attention_and_collapses_older_captain_decisions(
        self,
    ) -> None:
        out = self.run_fixture(
            """
const facts = [
  {fact_id:"new",at:50,type:"gate_decision",by:"person:captain",decision:"approve",
    stage:"ideation",application_state:"consumed",target_stage:"implementation",work_item_id:"workflow:a"},
  {fact_id:"dupe",at:49,type:"gate_decision",by:"person:captain",decision:"approve",
    stage:"ideation",application_state:"consumed",target_stage:"implementation",work_item_id:"workflow:a"},
  {fact_id:"second",at:48,type:"gate_decision",by:"person:captain",decision:"revise",
    stage:"review",application_state:"pending",target_stage:"shaping",work_item_id:"workflow:b"},
  {fact_id:"third",at:47,type:"gate_decision",by:"person:captain",decision:"hold",
    stage:"validation",application_state:"superseded",target_stage:"validation",work_item_id:"workflow:c"},
  {fact_id:"fo",at:60,type:"gate_decision",by:"agent:first-officer",decision:"approve",
    stage:"validation",target_stage:"done",work_item_id:"workflow:d"}
];
const semantic = {facts, work_items:[
  {work_item_id:"workflow:a",label:"alpha"},{work_item_id:"workflow:b",label:"beta"},
  {work_item_id:"workflow:c",label:"gamma"},{work_item_id:"workflow:d",label:"delta"}
]};
console.log(JSON.stringify({html:nextCockpitProjectStatus(nextProjectGroups()[0], semantic)}));
"""
        )
        assert isinstance(out, dict)

        self.assertIn("No gate or ask observed", out["html"])
        self.assertEqual(1, out["html"].count("Alpha · ideation → implementation"))
        self.assertIn("Beta · review · decision recorded · pending application", out["html"])
        self.assertIn("1 older decision", out["html"])
        self.assertIn("Gamma · validation · decision superseded", out["html"])
        self.assertNotIn("Delta", out["html"])

    def test_project_plan_is_after_the_briefing_and_closed_by_default(self) -> None:
        out = self.run_fixture(
            """
const group = nextProjectGroups()[0];
const observation = {semantic:__semantic, workflow_discovery:{state:"observed",workflows:[
  {workflow:"dev",goal:"Discovered workflow outcome",stages:["build"]}
]}};
nextCockpitContexts.set(nextCockpitContextKey(group, null), {data:observation, revision:105});
renderNext();
const discovered = __els.app.innerHTML;
nextCockpitContexts.set(nextCockpitContextKey(group, null), {
  data:{semantic:__semantic,workflow_discovery:{state:"none",workflows:[]}}, revision:105});
renderNext();
console.log(JSON.stringify({discovered,absent:__els.app.innerHTML}));
""",
        )
        assert isinstance(out, dict)

        self.assertLess(
            out["discovered"].index("Outcome &amp; Focus"),
            out["discovered"].index("data-next-cockpit-plan-details"),
        )
        self.assertIn("<summary>Show project plan</summary>", out["discovered"])
        self.assertIn("Discovered workflow outcome", out["discovered"])
        self.assertNotIn("Outcome not recorded", out["absent"])

    def test_recovery_attention_orders_actionable_conditions_and_decision_counts(self) -> None:
        out = self.run_fixture(
            """
const group = nextProjectGroups()[0];
group.sessions[0].state = "needs_input";
const semantic = JSON.parse(JSON.stringify(__semantic));
semantic.facts.push(
  {fact_id:"pending",at:106,type:"gate_decision",by:"person:captain",
    application_state:"pending",work_item_id:__task},
  {fact_id:"unknown",at:105,type:"gate_decision",by:"person:captain",
    work_item_id:__task},
  {fact_id:"retry",at:104,type:"prepared_dispatch",source_kind:"prepared_dispatch",
    work_item_id:"workflow:retry"},
  {fact_id:"retry-again",at:103,type:"prepared_dispatch",source_kind:"prepared_dispatch",
    work_item_id:"workflow:retry"}
);
semantic.projections.trail_heads.push({work_item_id:"workflow:retry",status:"prepared",
  dispatch_count:2,latest_meaningful_event:"retry"});
const observation = {semantic,workflow_discovery:{state:"error",reason:"timed out"},
  sources:{observer:{unavailable:[]}}};
console.log(JSON.stringify({html:nextCockpitRecoveryStrip(group, observation)}));
""",
        )
        assert isinstance(out, dict)
        html = out["html"]

        self.assertLess(html.index("gate or ask"), html.index("workflow discovery failed"))
        self.assertLess(html.index("workflow discovery failed"), html.index("assignment return"))
        self.assertLess(html.index("assignment return"), html.index("owner idle"))
        self.assertLess(html.index("pending 1"), html.index("unknown 1"))
        self.assertIn("consumed/applied 1", html)
        self.assertNotIn("decision application", html)
        self.assertNotIn("blocker", html.casefold())

    def test_command_attention_leads_with_exact_authorization_and_assigns_fo_recovery(self) -> None:
        out = self.run_fixture(
            """
const group = nextProjectGroups()[0];
const semantic = JSON.parse(JSON.stringify(__semantic));
semantic.projections.command_attention = [{projection_id:"auth",at:109,
  owner:"CAPTAIN",kind:"push_pr",label:"The completion-guard error names the failing sub-check",
  question:"Approve pushing this candidate and creating the PR?",
  evidence:{source:"assistant final_answer followed by terminal turn state",confidence:"exact"}}];
semantic.facts.push({fact_id:"pending",at:108,type:"gate_decision",by:"person:captain",
  application_state:"pending",work_item_id:__task});
semantic.projections.trail_heads.push({work_item_id:"workflow:return",status:"prepared",
  dispatch_count:2,latest_meaningful_event:"return"});
const observation = {semantic,workflow_discovery:{state:"error",reason:"timed out"},sources:{}};
const items = nextCockpitCommandAttention(group, observation);
console.log(JSON.stringify({items,html:nextCockpitRecoveryStrip(group, observation, items)}));
""",
        )
        assert isinstance(out, dict)

        self.assertEqual("CAPTAIN", out["items"][0]["owner"])
        self.assertIn("authorize push + PR", out["items"][0]["label"])
        self.assertTrue(all(row["owner"] == "FO" for row in out["items"][1:]))
        self.assertIn("assistant final_answer followed by terminal turn state", out["html"])
        self.assertIn("exact", out["html"])
        self.assertLess(out["html"].index("CAPTAIN"), out["html"].index("FO"))

    def test_incomplete_attention_coverage_suppresses_nothing_needs_you(self) -> None:
        out = self.run_fixture(
            """
const group=nextProjectGroups()[0];
const semantic=JSON.parse(JSON.stringify(__semantic));
semantic.projections.command_attention=[];
semantic.projections.command_attention_coverage={state:"incomplete",scanned:64,total:65,
  omitted:1,source:"bounded active-session final-output scan"};
const observation={semantic,workflow_discovery:{state:"observed"},sources:{}};
const items=nextCockpitCommandAttention(group,observation);
console.log(JSON.stringify({items,html:nextCockpitNeedsYou(items)}));
"""
        )
        assert isinstance(out, dict)

        self.assertEqual("CAPTAIN", out["items"][0]["owner"])
        self.assertEqual("Captain-attention coverage incomplete", out["items"][0]["label"])
        self.assertIn("Captain-attention coverage incomplete", out["html"])
        self.assertNotIn("Nothing needs you", out["html"])

    def test_human_outcome_and_focus_autosave_per_exact_scope(self) -> None:
        out = self.run_fixture(
            """
const group=nextProjectGroups()[0];
const projectOutcome=nextCockpitMemoKey(group,null,"outcome");
const projectFocus=nextCockpitMemoKey(group,null,"focus");
const pi=group.sessions.find(session=>sessKey(session)==="pi:pi-idle");
const sessionOutcome=nextCockpitMemoKey(group,pi,"outcome");
const edit=(key,kind,value)=>({value,dataset:{nextCockpitMemoKey:key,nextCockpitMemoKind:kind},
  closest(selector){ return selector === "[data-next-cockpit-memo-input]" ? this : null; }});
__fire("input",{target:edit(projectOutcome,"outcome","Ship calm scope navigation")});
__fire("input",{target:edit(projectFocus,"focus","Review project truth")});
__fire("input",{target:edit(sessionOutcome,"outcome","Inspect Pi evidence")});
const action=(name,key)=>({dataset:{nextCockpitAction:name,arg:key},
  closest(selector){ return selector === "[data-next-cockpit-action]" ? this : null; }});
__fire("click",{target:action("memo-edit",projectFocus),preventDefault(){}});
const project=nextCockpitMemoFields(group,null,__semantic);
const session=nextCockpitMemoFields(group,pi,__semantic);
__fire("click",{target:action("memo-done",""),preventDefault(){}});
const closed=nextCockpitMemoFields(group,null,__semantic);
console.log(JSON.stringify({projectOutcome,projectFocus,sessionOutcome,store:__store,
  project,session,closed}));
"""
        )
        assert isinstance(out, dict)

        self.assertNotEqual(out["projectOutcome"], out["sessionOutcome"])
        self.assertEqual("Ship calm scope navigation", out["store"][out["projectOutcome"]])
        self.assertEqual("Review project truth", out["store"][out["projectFocus"]])
        self.assertEqual("Inspect Pi evidence", out["store"][out["sessionOutcome"]])
        self.assertIn("OUTCOME", out["project"])
        self.assertIn("FOCUS", out["project"])
        self.assertIn("Saved in this browser", out["project"])
        self.assertEqual(1, out["project"].count("<textarea"))
        self.assertNotIn("<textarea", out["closed"])
        self.assertIn("This browser only", out["closed"])
        self.assertNotIn("DERIVED", out["project"])
        self.assertNotIn("Ship calm scope navigation", out["session"])
        self.assertNotIn("Review project truth", out["session"])

    def test_memos_use_normalized_project_identity_and_survive_storage_failure(self) -> None:
        out = self.run_fixture(
            """
const group=nextProjectGroups()[0];
const alias={label:"worktrees/cargento-copy",sessions:group.sessions};
const normalized=nextCockpitMemoKey(group,null,"focus");
const aliased=nextCockpitMemoKey(alias,null,"focus");
localStorage.getItem=()=>{throw new Error("blocked")};
localStorage.setItem=()=>{throw new Error("blocked")};
const corruptKey=nextCockpitMemoKey(group,null,"outcome");
nextCockpitMemoDrafts.set(corruptKey,{not:"text"});
const input={value:"x".repeat(700),dataset:{nextCockpitMemoKey:corruptKey,
  nextCockpitMemoKind:"outcome"},closest(selector){
  return selector === "[data-next-cockpit-memo-input]" ? this : null; }};
__fire("input",{target:input});
nextCockpitMemoEditingKey=corruptKey;
console.log(JSON.stringify({normalized,aliased,value:nextCockpitReadMemo(corruptKey),
  html:nextCockpitMemoFields(group,null,__semantic)}));
"""
        )
        assert isinstance(out, dict)

        self.assertEqual(out["normalized"], out["aliased"])
        self.assertEqual(500, len(out["value"]))
        self.assertIn("Browser storage unavailable", out["html"])
        self.assertIn("OUTCOME", out["html"])
        self.assertEqual(1, out["html"].count("<textarea"))
        self.assertNotIn("DERIVED", out["html"])

    def test_memo_reload_restores_only_the_exact_selected_scope(self) -> None:
        key = "cargento.cockpit.memo.v2:spacedock-research%2Fcargento:project:outcome"
        out = self.run_fixture(
            """
const project=__els.app.innerHTML;
nextRoute=nextRouteFromFragment("#n=project:cargento:pi%3Api-idle");
renderNext();await __settle();await __settle();
console.log(JSON.stringify({project,session:__els.app.innerHTML}));
""",
            storage={key: "Remember the accepted cockpit"},
        )
        assert isinstance(out, dict)

        self.assertIn("Remember the accepted cockpit", out["project"])
        self.assertNotIn("<textarea", out["project"])
        self.assertNotIn("Remember the accepted cockpit", out["session"])
        self.assertIn('data-scope-owner="pi:pi-idle"', out["session"])

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
