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
  const link = (key, label, state, result) => {
    const route = {view:"project", project:group.label, focus:key === "all" ? null : key};
    return `<a href="${esc(nextFragmentForRoute(route))}" data-next-cockpit-session="${esc(key)}"` +
      (selected === key ? ` aria-current="page"` : "") + `>` +
      `<strong>${esc(label)}</strong><span>${esc(state)}</span>` +
      `<small>${esc(String(result || "").replace(/\s+/g, " ").slice(0, 90))}</small></a>`;
  };
  const rows = [...group.sessions].sort((left, right) =>
    String(left.harness || "").localeCompare(String(right.harness || "")) ||
    sessKey(left).localeCompare(sessKey(right)));
  return `<nav class="next-cockpit-session-nav" aria-label="Project sessions">` +
    link("all", "All sessions", `${rows.length} sessions`, "Project-wide semantic union") +
    rows.map(session => {
      const harness = nextHarnessLabels().get(String(session.harness || "")) ||
        String(session.harness || "Session");
      return link(sessKey(session), nextCockpitSessionResult(session),
        `${harness} · ${String(session.state || "unknown")}`, "");
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
      const key = [fact.work_item_id, fact.decision, fact.stage, fact.target_stage].join("\n");
      if(seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  const row = fact => {
    const label = labels.get(String(fact.work_item_id || "")) || "Workflow item";
    const transition = fact.stage && fact.target_stage
      ? ` · ${fact.stage} → ${fact.target_stage}` : "";
    return `<li><strong>${esc(label + transition)}</strong></li>`;
  };
  const latest = decisions.slice(0, 2).map(row).join("");
  const older = decisions.slice(2);
  const history = older.length ? `<details><summary>${older.length} older ` +
    `${older.length === 1 ? "decision" : "decisions"}</summary><ul>${older.map(row).join("")}</ul></details>` : "";
  const decisionList = latest ? `<ul>${latest}</ul>${history}` :
    '<span class="next-cockpit-status-empty">No captain decisions observed</span>';
  return '<section class="next-cockpit-project-status" aria-label="Project status">' +
    `<strong>Needs you: ${needs ? `${needs} observed` : "none observed"}</strong>` +
    `<div><span>Latest decisions</span>${decisionList}</div></section>`;
}

function nextCockpitContextKey(group, focus){
  return `${nextCockpitStableKey(group)}\n${focus ? sessKey(focus) : ""}`;
}

function nextCockpitProjectObservation(group){
  const focus = nextCockpitFocusedSession(group);
  const entry = nextCockpitContexts.get(nextCockpitContextKey(group, focus));
  return entry && entry.data || null;
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

function nextCockpitTimeline(group, focus){
  const key = nextCockpitContextKey(group, focus);
  const entry = nextCockpitContexts.get(key);
  nextCockpitLoadContext(group, focus);
  if(!entry || !entry.data){
    const label = entry && entry.error ? "Semantic context unavailable." : "Loading semantic context…";
    return `<section class="next-cockpit-semantic" data-next-cockpit-semantic><h2>SEMANTIC TIMELINE</h2>` +
      `<p class="next-cockpit-empty">${label}</p></section>`;
  }
  projectQuerySession = focus ? sessKey(focus) : "";
  const cacheKey = projectContextKey(nextCockpitStableKey(group));
  projectContextByLabel[cacheKey] = {state:"ready", data:entry.data, generated:entry.revision};
  const delegationGroup = {label: nextCockpitStableKey(group)};
  const lanes = focus ? projectDelegationLanes(focus, delegationGroup) :
    group.sessions.flatMap(session => projectDelegationLanes(session, delegationGroup));
  const semantic = entry.data.semantic || {facts:[], work_items:[], projections:{}};
  const timeline = projectSemanticTimeline(nextData, semantic, lanes, focus, group.sessions)
    .replaceAll('data-calm="project-graph-mode"', 'data-next-cockpit-action="graph-mode"');
  return '<section class="next-cockpit-semantic" data-next-cockpit-semantic>' +
    '<h2>SEMANTIC TIMELINE</h2>' + timeline + '</section>';
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

function nextProjectCockpit(context){
  const group = context.group;
  const focus = nextCockpitFocusedSession(group);
  projectQuerySession = focus ? sessKey(focus) : "";
  lastData = nextData;
  return nextCockpitFocus(group) + nextCockpitTimeline(group, focus) +
    nextCockpitTerminal(group, focus);
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
