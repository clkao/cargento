const NEXT_COCKPIT_FOCUS_ALIAS_PREFIX = "cargento.projectGoal.v1:";
const nextCockpitContexts = new Map();
const nextCockpitRequests = new Map();
const nextCockpitFocusDrafts = new Map();
let nextCockpitTerminalScreen = null;

function nextCockpitStableKey(group){
  const keys = new Set(group.sessions.map(session => String(session.project_key || "")).filter(Boolean));
  return keys.size === 1 ? [...keys][0] : group.label;
}

function nextCockpitFocusKey(group){
  return NEXT_COCKPIT_FOCUS_ALIAS_PREFIX + encodeURIComponent(nextCockpitStableKey(group));
}

function nextCockpitLabelFocusKey(group){
  return NEXT_COCKPIT_FOCUS_ALIAS_PREFIX + encodeURIComponent(group.label);
}

function nextCockpitReadFocus(group){
  if(nextCockpitFocusDrafts.has(nextCockpitStableKey(group))){
    return nextCockpitFocusDrafts.get(nextCockpitStableKey(group));
  }
  try{
    return localStorage.getItem(nextCockpitFocusKey(group)) ||
      localStorage.getItem(nextCockpitLabelFocusKey(group)) || "";
  }catch(_error){
    return "";
  }
}

function nextCockpitFocusedSession(group){
  if(!nextRoute || nextRoute.view !== "project" || !nextRoute.focus) return null;
  return group.sessions.find(session => sessKey(session) === nextRoute.focus) || null;
}

function nextCockpitSessionResult(session){
  if(session.state === "working") return session.title || "working";
  return session.last_output || session.title || session.state || "state unavailable";
}

function nextCockpitSessionNav(group, focus){
  const selected = focus ? sessKey(focus) : "all";
  const link = (key, label, subtitle) => {
    const route = {view:"project",project:group.label,focus:key === "all" ? null : key,
      tab:nextRoute && nextRoute.tab || "now"};
    return `<a href="${esc(nextFragmentForRoute(route))}" data-next-cockpit-session="${esc(key)}"` +
      (selected === key ? ` aria-current="page"` : "") + `>` +
      `<strong>${esc(label)}</strong>` +
      `<small>${esc(String(subtitle || "").replace(/\s+/g, " ").slice(0, 90))}</small></a>`;
  };
  const rows = [...group.sessions].sort((left, right) =>
    String(left.harness || "").localeCompare(String(right.harness || "")) ||
    sessKey(left).localeCompare(sessKey(right)));
  return `<nav class="next-cockpit-session-nav" aria-label="Project sessions">` +
    link("all", "All sessions", `${rows.length} sessions · project-wide evidence`) +
    rows.map(session => {
      const harness = nextHarnessLabels().get(String(session.harness || "")) ||
        String(session.harness || "Session");
      return link(sessKey(session), `${harness} · ${String(session.state || "unknown")}`,
        nextCockpitSessionResult(session));
    }).join("") + `</nav>`;
}

function nextCockpitHumanLabel(value){
  const words = String(value || "work").replace(/[-_]+/g, " ").trim();
  return words ? words[0].toUpperCase() + words.slice(1) : "Work";
}

function nextCockpitProjectNeeds(group){
  const identities = new Set(group.sessions.map(session => sessKey(session)));
  const asks = nextData && nextData.ask === true && Array.isArray(nextData.asks)
    ? nextData.asks : [];
  const waiting = asks.filter(ask => identities.has(
    `${String(ask && ask.harness || "")}:${String(ask && ask.session_id || "")}`));
  const blocked = group.sessions.filter(session => session.state === "needs_input");
  return new Set([
    ...waiting.map(ask => `${String(ask.harness || "")}:${String(ask.session_id || "")}`),
    ...blocked.map(session => sessKey(session)),
  ]).size;
}

function nextCockpitProjectStatus(group, semantic){
  const needs = nextCockpitProjectNeeds(group);
  const labels = new Map((semantic.work_items || []).map(item =>
    [String(item.work_item_id || ""), nextCockpitHumanLabel(item.label)]));
  const seen = new Set();
  const decisions = (semantic.facts || []).filter(fact =>
    fact && fact.type === "gate_decision" && fact.by === "person:captain")
    .sort((left, right) => Number(right.at || 0) - Number(left.at || 0))
    .filter(fact => {
      const key = [fact.work_item_id, fact.decision, fact.stage, fact.application_state,
        fact.target_stage].join("\n");
      if(seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  const row = fact => {
    const label = labels.get(String(fact.work_item_id || "")) || "Workflow item";
    return `<li><strong>${esc(label + " · " + projectGateApplicationResult(fact))}</strong></li>`;
  };
  const latest = decisions.slice(0, 2).map(row).join("");
  const older = decisions.slice(2);
  const history = older.length ? `<details><summary>${older.length} older ` +
    `${older.length === 1 ? "decision" : "decisions"}</summary><ul>${older.map(row).join("")}</ul></details>` : "";
  const decisionList = latest ? `<ul>${latest}</ul>${history}` :
    '<span class="next-cockpit-status-empty">No captain decisions observed</span>';
  return '<section class="next-cockpit-project-status" aria-label="Project status">' +
    `<strong>${needs ? `Gate or ask observed · ${needs}` : "No gate or ask observed"}</strong>` +
    `<div><span>Latest decisions</span>${decisionList}</div></section>`;
}

function nextCockpitCaptainDecisionCounts(semantic){
  const counts = {pending:0, unknown:0, superseded:0, applied:0};
  for(const fact of semantic && Array.isArray(semantic.facts) ? semantic.facts : []){
    if(!fact || fact.type !== "gate_decision" || fact.by !== "person:captain") continue;
    const state = String(fact.application_state || "unknown").toLowerCase();
    if(state === "pending" || state === "unspent") counts.pending += 1;
    else if(state === "consumed" || state === "applied") counts.applied += 1;
    else if(state === "superseded") counts.superseded += 1;
    else counts.unknown += 1;
  }
  return counts;
}

function nextCockpitRecoveryOutcome(group, observation){
  const local = nextCockpitReadFocus(group).trim();
  if(local) return local;
  const discovery = observation && observation.workflow_discovery || {};
  const workflows = Array.isArray(discovery.workflows) ? discovery.workflows : [];
  if(discovery.state === "observed"){
    const workflow = workflows.find(row => String(row && row.goal || "").trim());
    if(workflow) return String(workflow.goal).trim();
  }
  return "Outcome not recorded";
}

function nextCockpitSourceFailures(observation){
  const failures = [];
  const sources = observation && observation.sources || {};
  for(const channel of Object.values(sources)){
    if(!channel || !Array.isArray(channel.unavailable)) continue;
    for(const row of channel.unavailable){
      const reason = String(row && row.reason || "source unavailable").trim();
      if(reason && !failures.includes(reason)) failures.push(reason);
    }
  }
  return failures;
}

function nextCockpitCommandAttention(group, observation){
  const attention = [];
  const add = (owner, label, source, confidence = "exact") => attention.push({
    owner, label, evidence:{source, confidence},
  });
  const semantic = observation && observation.semantic || {};
  const projected = semantic.projections && Array.isArray(semantic.projections.command_attention)
    ? semantic.projections.command_attention : [];
  for(const item of projected){
    if(!item || item.owner !== "CAPTAIN") continue;
    const label = item.kind === "push_pr"
      ? `authorize push + PR for ${String(item.label || "Codex session result")}`
      : String(item.question || item.label || "answer explicit authorization request");
    attention.push({owner:"CAPTAIN",label,evidence:item.evidence || {}});
  }
  const needs = nextCockpitProjectNeeds(group);
  if(needs) add("CAPTAIN", `${needs} gate or ask ${needs === 1 ? "needs" : "need"} attention`,
    "AskRegistry or exact session needs-input state");

  const discovery = observation && observation.workflow_discovery || {};
  if(discovery.state === "error"){
    const reason = String(discovery.reason || "source error").trim();
    add("FO", `workflow discovery failed${reason ? ` · ${reason}` : ""}`,
      String(discovery.source || "project workflow discovery"));
  }else if(discovery.state === "unavailable"){
    const reason = String(discovery.reason || "source unavailable").trim();
    add("FO", `workflow discovery unavailable${reason ? ` · ${reason}` : ""}`,
      String(discovery.source || "project workflow discovery"));
  }
  const failures = nextCockpitSourceFailures(observation);
  if(failures.length) add("FO", `source unavailable · ${failures[0]}` +
    (failures.length > 1 ? ` · ${failures.length - 1} more` : ""), "project context sources");

  const decisions = nextCockpitCaptainDecisionCounts(semantic);
  const unresolvedDecisions = decisions.pending + decisions.unknown;
  if(unresolvedDecisions){
    const parts = [];
    if(decisions.pending) parts.push(`${decisions.pending} pending`);
    if(decisions.unknown) parts.push(`${decisions.unknown} unknown`);
    add("FO", `decision application · ${parts.join(" · ")}`,
      "exact captain gate decision facts");
  }

  const trails = semantic.projections && Array.isArray(semantic.projections.trail_heads)
    ? semantic.projections.trail_heads : [];
  const unreturned = trails.filter(row => row && ["prepared", "requested"].includes(row.status));
  if(unreturned.length){
    const retried = unreturned.filter(row => Number(row.dispatch_count || 0) > 1).length;
    add("FO", `assignment return not observed · ${unreturned.length}` +
      (retried ? ` · ${retried} retried` : ""), "semantic task trail heads");
  }

  const idle = group.sessions.filter(session => session.state === "idle");
  const stale = group.sessions.filter(session => {
    const age = nextAgeSeconds(session.last_activity);
    return session.state !== "idle" && age != null && age >= NEXT_PROJECT_STALLED_SEC;
  });
  if(idle.length || stale.length){
    const parts = [];
    if(idle.length) parts.push(`owner idle · ${idle.length}`);
    if(stale.length) parts.push(`owner stale · ${stale.length}`);
    add("FO", parts.join(" · "), "exact session state");
  }
  return attention;
}

function nextCockpitRecoveryAttention(group, observation, commandAttention){
  const attention = commandAttention || nextCockpitCommandAttention(group, observation);
  if(!attention.length) return '<strong>No attention observed</strong>';
  const row = item => `<strong>${esc(item.owner + " · " + item.label)}</strong>` +
    `<small>${esc(String(item.evidence && item.evidence.source || "source unavailable"))} · ` +
    `${esc(String(item.evidence && item.evidence.confidence || "confidence unavailable"))}</small>`;
  const rest = attention.slice(1);
  return row(attention[0]) + (rest.length
    ? `<details><summary>${rest.length} more</summary><ul>${rest.map(item => `<li>${row(item)}</li>`).join("")}</ul></details>`
    : "");
}

function nextCockpitRecoveryDecisions(semantic){
  const counts = nextCockpitCaptainDecisionCounts(semantic);
  const total = Object.values(counts).reduce((sum, value) => sum + value, 0);
  if(!total) return "No captain decisions observed";
  const labels = {pending:"pending", unknown:"unknown", superseded:"superseded",
    applied:"consumed/applied"};
  return ["pending", "unknown", "superseded", "applied"]
    .filter(key => counts[key])
    .map(key => `${labels[key]} ${counts[key]}`)
    .join(" · ");
}

function nextCockpitRecoveryStrip(group, observation, commandAttention){
  const semantic = observation && observation.semantic || {};
  return '<section class="next-cockpit-recovery" aria-label="Recovery summary">' +
    `<div><span>OUTCOME</span><strong>${esc(nextCockpitRecoveryOutcome(group, observation))}</strong></div>` +
    `<div><span>ATTENTION</span>${nextCockpitRecoveryAttention(group, observation, commandAttention)}</div>` +
    `<div><span>DECISIONS</span><strong>${esc(nextCockpitRecoveryDecisions(semantic))}</strong></div>` +
    '</section>';
}

function nextCockpitContextKey(group, focus){
  return `${nextCockpitStableKey(group)}\n${focus ? sessKey(focus) : ""}`;
}

function nextCockpitProjectObservation(group){
  const entry = nextCockpitContexts.get(nextCockpitContextKey(group, null));
  return entry && entry.data || null;
}

function nextCockpitCanonicalSemantic(group, semantic){
  const observation = nextCockpitProjectObservation(group);
  const projectSemantic = observation && observation.semantic || {};
  const labels = new Map((projectSemantic.work_items || []).map(item =>
    [String(item.work_item_id || ""), String(item.label || "")]));
  return Object.assign({}, semantic, {work_items:(semantic.work_items || []).map(item => {
    const label = labels.get(String(item.work_item_id || ""));
    return label ? Object.assign({}, item, {label}) : item;
  })});
}

function nextCockpitLoadContext(group, focus){
  if(!nextData) return;
  const key = nextCockpitContextKey(group, focus);
  const revision = nextFiniteNumber(nextData.generated);
  const settled = nextCockpitContexts.get(key);
  if(nextCockpitRequests.has(key) || settled && settled.revision >= revision) return;
  nextCockpitRequests.set(key, revision);
  const query = "/api/project-context?project=" + encodeURIComponent(nextCockpitStableKey(group)) +
    (focus ? "&session=" + encodeURIComponent(sessKey(focus)) : "");
  fetch(query).then(response => {
    if(!response.ok) throw new Error(String(response.status));
    return response.json();
  }).then(data => {
    if(nextCockpitRequests.get(key) !== revision) return;
    nextCockpitRequests.delete(key);
    nextCockpitContexts.set(key, {data, revision});
    renderNext();
  }).catch(() => {
    if(nextCockpitRequests.get(key) !== revision) return;
    nextCockpitRequests.delete(key);
    nextCockpitContexts.set(key, {data: settled && settled.data || null, revision, error: true});
    renderNext();
  });
}

function nextCockpitFocus(group){
  const stableKey = nextCockpitStableKey(group);
  const labelAlias = stableKey === group.label ? "" :
    `<small>stable project key · ${esc(stableKey)} · label alias ${esc(group.label)}</small>`;
  return '<section class="next-cockpit-focus" data-next-cockpit-focus>' +
    '<header><span>FOCUS · THIS BROWSER</span>' + labelAlias + '</header>' +
    `<textarea data-next-cockpit-focus-input data-next-cockpit-project="${esc(stableKey)}" ` +
    `placeholder="What outcome should this project preserve?">${esc(nextCockpitReadFocus(group))}</textarea>` +
    '<div><button type="button" data-next-cockpit-action="focus-save">save focus</button>' +
    '<button type="button" data-next-cockpit-action="focus-clear">clear</button></div></section>';
}

function nextCockpitProjectScope(){
  return '<section class="next-cockpit-scope next-cockpit-scope--project">' +
    '<strong>PROJECT OVERVIEW</strong>' +
    '<span>Session selection filters Course, Decisions, and Console; Now remains project-wide.</span>' +
    '</section>';
}

function nextCockpitEvidenceScope(focus){
  const selected = focus ? `${nextHarnessLabels().get(String(focus.harness || "")) ||
    String(focus.harness || "Session")} · ${String(focus.state || "unknown")}` : "All sessions";
  return '<header class="next-cockpit-scope next-cockpit-scope--evidence">' +
    `<strong>SESSION EVIDENCE</strong><span>${esc(selected)}</span></header>`;
}

function nextCockpitSemantic(observation){
  return observation && observation.semantic || {facts:[],work_items:[],projections:{}};
}

function nextCockpitCurrentTask(observation){
  const semantic = nextCockpitSemantic(observation);
  const items = new Map((semantic.work_items || []).map(item =>
    [String(item.work_item_id || ""), item]));
  const heads = semantic.projections && Array.isArray(semantic.projections.trail_heads)
    ? semantic.projections.trail_heads : [];
  const head = heads.find(row => row && row.status === "current stage") ||
    heads.find(row => row && row.stage) || null;
  const item = head && items.get(String(head.work_item_id || ""));
  const fallback = (semantic.work_items || []).find(row => row && row.kind === "workflow_item");
  return {
    id:String(head && head.work_item_id || fallback && fallback.work_item_id || ""),
    label:nextCockpitHumanLabel(item && item.label || fallback && fallback.label || "Project work"),
    stage:nextCockpitHumanLabel(head && head.stage || "state unavailable"),
  };
}

function nextCockpitTaskSubject(observation){
  const task = nextCockpitCurrentTask(observation);
  return '<section class="next-cockpit-task-subject" data-next-cockpit-task-subject ' +
    `data-work-item="${esc(task.id)}"><span>CURRENT TASK</span>` +
    `<h2>${esc(task.label)} <small>· ${esc(task.stage)}</small></h2>` +
    '<p>Task and stage come from exact workflow evidence.</p></section>';
}

function nextCockpitTabList(){
  const selected = NEXT_PROJECT_TABS.includes(nextRoute && nextRoute.tab)
    ? nextRoute.tab : "now";
  return '<nav class="next-cockpit-tabs" role="tablist" aria-label="Project cockpit views">' +
    NEXT_PROJECT_TABS.map(tab => {
      const label = nextCockpitHumanLabel(tab);
      const current = tab === selected;
      return `<button type="button" role="tab" data-next-cockpit-action="tab" ` +
        `data-arg="${tab}" aria-controls="next-cockpit-panel-${tab}" ` +
        `aria-selected="${current}" tabindex="${current ? 0 : -1}">${label}</button>`;
    }).join("") + '</nav>';
}

function nextCockpitLatestCompletedResult(semantic){
  const results = (semantic.facts || []).filter(fact => fact && fact.type === "result")
    .sort((left, right) => Number(right.at || 0) - Number(left.at || 0));
  for(const fact of results){
    const detail = String(fact.detail || fact.summary || "");
    const firstLine = detail.trimStart().split(/\r?\n/, 1)[0];
    if(!/^(?:fixed|completed|done)\b.*\blive\b/i.test(firstLine)) continue;
    const checkpoint = detail.match(/(?:checkpoint\s*:?\s*|\bat\s+)`?([0-9a-f]{7,40})`?/i);
    if(checkpoint) return {fact,checkpoint:checkpoint[1]};
  }
  return null;
}

function nextCockpitNowState(observation){
  const semantic = nextCockpitSemantic(observation);
  const task = nextCockpitCurrentTask(observation);
  const completed = nextCockpitLatestCompletedResult(semantic);
  const result = completed
    ? `<div><span>COMPLETED RESULT · EXACT</span><strong>${esc(completed.checkpoint)}</strong>` +
      `<small>${esc(completed.fact.summary || "Exact returned result")}</small></div>`
    : '<div><span>COMPLETED RESULT</span><strong>No completed result observed</strong></div>';
  return '<section class="next-cockpit-now-state" aria-label="Current task state">' +
    `<div><span>CURRENT · EXACT WORKFLOW STATE</span><strong>${esc(task.label + " · " + task.stage)}</strong></div>` +
    '<div><span>CURRENT FOCUS · DERIVED</span><strong>Browser-local operator interpretation</strong></div>' +
    result + '</section>';
}

function nextCockpitActiveDelegation(group, observation){
  const task = nextCockpitCurrentTask(observation);
  const delegationGroup = {label:nextCockpitStableKey(group)};
  const lanes = group.sessions.flatMap(session => projectDelegationLanes(session, delegationGroup));
  if(!lanes.length){
    return '<section class="next-cockpit-active-delegation"><h2>ACTIVE DELEGATION</h2>' +
      '<p>No active task delegation observed.</p></section>';
  }
  const rows = lanes.map(lane => `<li data-work-item="${esc(lane.workItemId || "")}" ` +
    `data-parent-session="${esc(lane.parentSession || "")}"><strong>${esc(lane.worker)}</strong> · ` +
    `${esc(lane.assignment)}<small>${esc(lane.source || "source unavailable")}</small></li>`).join("");
  return '<section class="next-cockpit-active-delegation" data-next-cockpit-active-delegation>' +
    '<h2>ACTIVE DELEGATION</h2>' +
    `<strong>${esc(task.label)} · ${lanes.length} active ` +
    `${lanes.length === 1 ? "assignment" : "assignments"}</strong>` +
    `<details><summary>${lanes.length} ${lanes.length === 1 ? "contributor" : "contributors"}</summary>` +
    `<ul>${rows}</ul></details></section>`;
}

function nextCockpitReviewFindings(detail){
  const lines = String(detail || "").split(/\r?\n/);
  let collecting = false;
  const findings = [];
  for(const raw of lines){
    const line = raw.replace(/^\s*\d+\.\s*/, "").replace(/\*\*/g, "").trim();
    if(/^review changed the course\s*:/i.test(line)){
      collecting = true;
      continue;
    }
    if(!collecting) continue;
    const bullet = line.match(/^[-*]\s+(.+)/);
    if(bullet){ findings.push(bullet[1].trim()); continue; }
    if(line) break;
  }
  return findings;
}

function nextCockpitCourseEvidence(fact, contributors){
  const evidence = fact.evidence || {};
  const names = contributors.length
    ? `<div><b>Contributors</b> · ${esc(contributors.join(" · "))}</div>` : "";
  return '<details class="next-course-evidence"><summary>Evidence</summary>' +
    `<div><b>Source</b> · ${esc(evidence.source || fact.source_kind || "source unavailable")} · ` +
    `${esc(evidence.confidence || "confidence unavailable")}</div>` +
    `<div><b>Fact</b> · ${esc(fact.fact_id || "identity unavailable")}</div>${names}</details>`;
}

function nextCockpitCourseRow(episode){
  const body = episode.findings && episode.findings.length
    ? `<ul>${episode.findings.map(finding => `<li>${esc(finding)}</li>`).join("")}</ul>`
    : `<p>${esc(episode.summary)}</p>`;
  return `<article class="next-course-episode" data-epistemic-kind="${esc(episode.epistemic)}">` +
    `<header><span>${esc(episode.badge)}</span></header>` +
    `<strong>${esc(episode.task + " · " + episode.label)}</strong>${body}` +
    nextCockpitCourseEvidence(episode.fact, episode.contributors || []) + '</article>';
}

function nextCockpitCourseEpisodes(semantic, lanes){
  const items = new Map((semantic.work_items || []).map(item =>
    [String(item.work_item_id || ""), nextCockpitHumanLabel(item.label)]));
  const current = nextCockpitCurrentTask({semantic});
  const taskFor = fact => items.get(String(fact.work_item_id || "")) || current.label;
  const intentIds = new Set((semantic.projections && semantic.projections.operator_intents || [])
    .map(row => String(row && row.derived_from || "")).filter(Boolean));
  const contributorNames = fact => [...new Set((lanes || []).filter(lane =>
    !fact.work_item_id || String(lane.workItemId || "") === String(fact.work_item_id))
    .map(lane => String(lane.worker || "")).filter(Boolean))];
  const episodes = [];
  const used = new Set();
  const results = (semantic.facts || []).filter(fact => fact && fact.type === "result")
    .sort((left, right) => Number(right.at || 0) - Number(left.at || 0));
  const review = results.find(fact => nextCockpitReviewFindings(fact.detail).length);
  if(review){
    used.add(String(review.fact_id || ""));
    episodes.push({at:Number(review.at || 0),fact:review,task:taskFor(review),
      label:"Course change",badge:"DERIVED COURSE CHANGE",epistemic:"derived-course-change",
      findings:nextCockpitReviewFindings(review.detail),contributors:contributorNames(review)});
  }else{
    const unavailable = results.find(fact => /\breview\b/i.test(String(fact.summary || fact.detail || "")));
    if(unavailable){
      used.add(String(unavailable.fact_id || ""));
      episodes.push({at:Number(unavailable.at || 0),fact:unavailable,task:taskFor(unavailable),
        label:"Course change",badge:"DERIVED COURSE CHANGE",epistemic:"derived-course-change",
        summary:"Review outcome unavailable from collected result detail.",
        contributors:contributorNames(unavailable)});
    }
  }
  const lifecycle = new Set();
  for(const fact of semantic.facts || []){
    if(!fact || fact.type === "gate_decision" || used.has(String(fact.fact_id || ""))) continue;
    if(fact.type === "user_message"){
      if(fact.intent_promoted !== true && !intentIds.has(String(fact.fact_id || ""))) continue;
      episodes.push({at:Number(fact.at || 0),fact,task:taskFor(fact),label:"User direction",
        badge:"EXACT INPUT",epistemic:"exact-input",summary:String(fact.summary || "Direction unavailable")});
      continue;
    }
    if(!["prepared_dispatch", "stage_transition", "result"].includes(fact.type)) continue;
    const lifecycleKey = fact.type === "result" ? String(fact.fact_id || "") :
      `${fact.type}\n${String(fact.work_item_id || "")}\n${String(fact.stage || fact.source_kind || "")}`;
    if(lifecycle.has(lifecycleKey)) continue;
    lifecycle.add(lifecycleKey);
    const completed = fact.type === "result"
      ? nextCockpitLatestCompletedResult({facts:[fact]}) : null;
    const summary = String(fact.summary || fact.stage || "Work observed") +
      (completed ? ` · checkpoint ${completed.checkpoint}` : "");
    episodes.push({at:Number(fact.at || 0),fact,task:taskFor(fact),label:"Observed work",
      badge:"EXACT WORK",epistemic:"exact-work",summary,
      contributors:contributorNames(fact)});
  }
  return episodes.sort((left, right) => left.at - right.at);
}

function nextCockpitCourse(group, semantic, lanes){
  const episodes = nextCockpitCourseEpisodes(semantic, lanes);
  if(!episodes.length){
    return '<p class="next-cockpit-empty">No source-backed course-changing episodes observed.</p>';
  }
  const visible = episodes.slice(-8);
  const earlier = episodes.slice(0, -8);
  const disclosure = earlier.length ? '<details class="next-course-earlier"><summary>' +
    `${earlier.length} Earlier</summary>${earlier.map(nextCockpitCourseRow).join("")}</details>` : "";
  return `<div class="next-cockpit-course" data-next-cockpit-course>${disclosure}` +
    visible.map(nextCockpitCourseRow).join("") + '</div>';
}

function nextCockpitTimeline(group, focus, mode = "active"){
  const key = nextCockpitContextKey(group, focus);
  const entry = nextCockpitContexts.get(key);
  const projectEntry = nextCockpitContexts.get(nextCockpitContextKey(group, null));
  nextCockpitLoadContext(group, focus);
  if(!entry || !entry.data || focus && (!projectEntry || !projectEntry.data)){
    const failed = entry && entry.error || focus && projectEntry && projectEntry.error;
    const label = failed ? "Semantic context unavailable." : "Loading semantic context…";
    return `<section class="next-cockpit-semantic" data-next-cockpit-semantic><h2>SEMANTIC TIMELINE</h2>` +
      `<p class="next-cockpit-empty">${label}</p></section>`;
  }
  projectQuerySession = focus ? sessKey(focus) : "";
  const cacheKey = projectContextKey(nextCockpitStableKey(group));
  projectContextByLabel[cacheKey] = {state:"ready", data:entry.data, generated:entry.revision};
  const delegationGroup = {label: nextCockpitStableKey(group)};
  const lanes = focus ? projectDelegationLanes(focus, delegationGroup) :
    group.sessions.flatMap(session => projectDelegationLanes(session, delegationGroup));
  const semantic = nextCockpitCanonicalSemantic(
    group,
    entry.data.semantic || {facts:[], work_items:[], projections:{}},
  );
  if(mode === "decisions" && !(semantic.facts || []).some(fact =>
    fact && fact.type === "gate_decision" && fact.by === "person:captain")){
    return '<section class="next-cockpit-semantic" data-next-cockpit-semantic>' +
      '<h2>CAPTAIN DECISIONS</h2>' +
      '<p class="next-cockpit-empty">No explicit captain decisions observed.</p></section>';
  }
  const timeline = projectSemanticTimeline(nextData, semantic, lanes, focus, group.sessions,
    mode === "decisions" ? {mode:"decisions",controls:false} : null)
    .replaceAll('data-calm="project-graph-mode"', 'data-next-cockpit-action="graph-mode"');
  return '<section class="next-cockpit-semantic" data-next-cockpit-semantic>' +
    `<h2>${mode === "decisions" ? "CAPTAIN DECISIONS" : "SEMANTIC TIMELINE"}</h2>` +
    timeline + '</section>';
}

function nextCockpitCoursePanel(group, focus){
  const key = nextCockpitContextKey(group, focus);
  const entry = nextCockpitContexts.get(key);
  const projectEntry = nextCockpitContexts.get(nextCockpitContextKey(group, null));
  nextCockpitLoadContext(group, focus);
  if(!entry || !entry.data || focus && (!projectEntry || !projectEntry.data)){
    const failed = entry && entry.error || focus && projectEntry && projectEntry.error;
    return `<p class="next-cockpit-empty">${failed ? "Course evidence unavailable." :
      "Loading course evidence…"}</p>`;
  }
  const delegationGroup = {label:nextCockpitStableKey(group)};
  const lanes = focus ? projectDelegationLanes(focus, delegationGroup) :
    group.sessions.flatMap(session => projectDelegationLanes(session, delegationGroup));
  const semantic = nextCockpitCanonicalSemantic(
    group,
    entry.data.semantic || {facts:[],work_items:[],projections:{}},
  );
  return nextCockpitCourse(group, semantic, lanes);
}

function nextCockpitTerminal(group, focus){
  if(!focus) return "";
  projectTerminalLookup(nextData, focus);
  const surface = projectTerminalSurface(focus);
  if(!surface) return "";
  return '<section class="next-cockpit-terminal" data-next-cockpit-terminal>' +
    '<h2>EXACT SESSION TERMINAL</h2>' +
    surface.replaceAll('data-calm="project-terminal-', 'data-next-cockpit-action="terminal-') +
    '</section>';
}

function nextCockpitPanel(context, focus, observation, commandAttention, status){
  const tab = NEXT_PROJECT_TABS.includes(nextRoute && nextRoute.tab) ? nextRoute.tab : "now";
  let body = "";
  if(tab === "now"){
    body = nextCockpitProjectScope() + status +
      nextCockpitRecoveryStrip(context.group, observation, commandAttention) +
      nextCockpitNowState(observation) + nextCockpitFocus(context.group) +
      nextCockpitActiveDelegation(context.group, observation) +
      '<div class="next-project-detail-layout"><main class="next-project-detail-main" data-next-project-main>' +
      `<div data-next-project-section="plan">${nextProjectPlanBlock(context)}</div>` +
      `<div data-next-project-section="going-on">${nextProjectGoingOn(context, commandAttention)}</div>` +
      `<div data-next-project-section="done">${nextProjectDone(context)}</div></main>` +
      '<aside class="next-project-detail-rail" data-next-project-rail>' +
      `${nextProjectDelegation(context)}${nextProjectControls(context)}</aside></div>`;
  }else if(tab === "course"){
    body = nextCockpitEvidenceScope(focus) + nextCockpitCoursePanel(context.group, focus);
  }else if(tab === "decisions"){
    body = nextCockpitEvidenceScope(focus) + nextCockpitTimeline(context.group, focus, "decisions");
  }else{
    body = nextCockpitEvidenceScope(focus) + (focus
      ? nextCockpitTerminal(context.group, focus)
      : '<p class="next-cockpit-empty">Select one exact session to open its read-only console.</p>');
  }
  return `<section class="next-cockpit-panel" id="next-cockpit-panel-${tab}" role="tabpanel" ` +
    `data-next-cockpit-panel="${tab}" aria-label="${nextCockpitHumanLabel(tab)}">${body}</section>`;
}

function nextProjectCockpit(context, observation, commandAttention, status){
  const group = context.group;
  const focus = nextCockpitFocusedSession(group);
  projectQuerySession = focus ? sessKey(focus) : "";
  lastData = nextData;
  return nextCockpitTaskSubject(observation) + nextCockpitTabList() +
    nextCockpitPanel(context, focus, observation, commandAttention, status);
}

function nextCockpitBeforeRender(){
  projectCaptureDisclosureStates();
  nextCockpitTerminalScreen = projectTerminalBeforeRender();
}

function nextCockpitAfterRender(){
  projectTerminalAfterRender(nextCockpitTerminalScreen);
  nextCockpitTerminalScreen = null;
}

function nextCockpitActionTarget(event){
  return event.target && event.target.closest
    ? event.target.closest("[data-next-cockpit-action]") : null;
}

document.addEventListener("input", event => {
  const input = event.target && event.target.closest
    ? event.target.closest("[data-next-cockpit-focus-input]") : null;
  if(input) nextCockpitFocusDrafts.set(String(input.dataset.nextCockpitProject || ""), input.value);
});

document.addEventListener("click", event => {
  const target = nextCockpitActionTarget(event);
  if(!target) return;
  const action = String(target.dataset.nextCockpitAction || "");
  const group = nextRoute.view === "project"
    ? nextProjectGroups().find(candidate => candidate.label === nextRoute.project) : null;
  if(action === "tab"){
    const tab = String(target.dataset.arg || "");
    if(!group || !NEXT_PROJECT_TABS.includes(tab)) return;
    event.preventDefault();
    navigateNext({view:"project",project:group.label,focus:nextRoute.focus || null,tab});
    return;
  }
  if(action === "focus-save" || action === "focus-clear"){
    if(!group) return;
    event.preventDefault();
    const stableKey = nextCockpitStableKey(group);
    const value = action === "focus-clear" ? "" : String(nextCockpitFocusDrafts.get(stableKey) || "").trim();
    try{
      if(value) localStorage.setItem(nextCockpitFocusKey(group), value);
      else localStorage.removeItem(nextCockpitFocusKey(group));
    }catch(_error){ /* the in-tab draft remains authoritative */ }
    nextCockpitFocusDrafts.set(stableKey, value);
    renderNext();
    return;
  }
  const key = String(target.dataset.arg || projectQuerySession || "");
  if(action === "graph-mode"){
    event.preventDefault();
    if(["active", "all", "decisions"].includes(String(target.dataset.arg || ""))){
      projectGraphModeBySession.set(projectQuerySession, String(target.dataset.arg));
      renderNext();
    }
  }else if(action === "terminal-open"){
    event.preventDefault();
    projectTerminalOpenKey = key;
    projectTerminalFollowLive = true;
    projectTerminalScrollTop = 0;
    renderNext();
  }else if(action === "terminal-close"){
    event.preventDefault();
    projectTerminalOpenKey = null;
    projectTerminalDispose();
    renderNext();
  }else if(action === "terminal-jump"){
    event.preventDefault();
    projectTerminalScrollToLive();
  }
});

function nextCockpitHandleKeydown(event){
  const target = nextCockpitActionTarget(event);
  if(!target || String(target.dataset.nextCockpitAction || "") !== "tab") return false;
  if(!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return false;
  const current = String(target.dataset.arg || "now");
  const index = Math.max(0, NEXT_PROJECT_TABS.indexOf(current));
  const next = event.key === "Home" ? 0 : event.key === "End" ? NEXT_PROJECT_TABS.length - 1 :
    (index + (event.key === "ArrowRight" ? 1 : -1) + NEXT_PROJECT_TABS.length) %
      NEXT_PROJECT_TABS.length;
  event.preventDefault();
  navigateNext({view:"project",project:nextRoute.project,focus:nextRoute.focus || null,
    tab:NEXT_PROJECT_TABS[next]});
  return true;
}
