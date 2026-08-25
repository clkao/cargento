/* ── project cockpit ───────────────────────────────────────────────────────
   One operator task over the same live payload as the regular and calm views:
   choose the project being resumed, recover its browser-owned outcome, see its
   active sessions, and answer any real AskRegistry question attributed to it.

   A project label is not an id. The browser goal intentionally uses the exact
   label anyway because this is the smallest reload mechanism shaping can put
   in front of an operator without inventing a server identity or persistence
   contract. The page states the collision and rename failure beside the value. */
const PROJECT_COCKPIT_KEY = "cargento.projectCockpitProject";
const PROJECT_GOAL_PREFIX = "cargento.projectGoal.v1:";
let projectCockpitLabel = null;
let projectQueryLabel = null;
let projectQuerySession = null;
let projectGoalNote = "";
const projectDraftByLabel = {};
const projectContextByLabel = {};
try{
  projectCockpitLabel = localStorage.getItem(PROJECT_COCKPIT_KEY) || null;
}catch(e){ /* no browser storage — choose from the payload */ }
try{
  const projectParams = new URLSearchParams(location.search || "");
  projectQueryLabel = projectParams.get("project");
  projectQuerySession = projectParams.get("session");
}catch(e){ /* no URL surface — use browser storage or payload order */ }

function projectGoalKey(label){
  return PROJECT_GOAL_PREFIX + encodeURIComponent(label);
}

function projectGoal(label){
  if(Object.prototype.hasOwnProperty.call(projectDraftByLabel, label)){
    return projectDraftByLabel[label];
  }
  try{ return localStorage.getItem(projectGoalKey(label)) || ""; }
  catch(e){ return ""; }
}

function projectContextKey(label){
  return `${label}\n${projectQuerySession || ""}`;
}

function projectContextEntry(label){
  return projectContextByLabel[projectContextKey(label)] || projectContextByLabel[label];
}

function projectRefreshControl(label, compact){
  const entry = projectContextEntry(label);
  const busy = !!(entry && entry.state === "loading");
  return `<button type="button" class="quiet" data-calm="project-context-refresh"` +
    ` data-arg="${esc(label)}" aria-busy="${busy}" aria-disabled="${busy}">` +
    (busy ? "refreshing context…" : (compact ? "refresh" : "refresh context")) + `</button>`;
}

function projectPermalink(label, sessionKey){
  try{
    const url = new URL(location.href);
    url.searchParams.set("mode", "project");
    url.searchParams.set("project", label);
    if(sessionKey) url.searchParams.set("session", sessionKey);
    else url.searchParams.delete("session");
    return url.toString();
  }catch(e){
    const params = new URLSearchParams(location.search || "");
    params.set("mode", "project");
    params.set("project", label);
    if(sessionKey) params.set("session", sessionKey);
    else params.delete("session");
    return "?" + params.toString() + (location.hash || "");
  }
}

function projectSyncUrl(label, sessionKey, replace){
  const target = projectPermalink(label, sessionKey);
  try{
    if(typeof history !== "undefined" && history.pushState){
      (replace ? history.replaceState : history.pushState).call(history, {}, "", target);
      return;
    }
  }catch(e){ /* the selection still works without history */ }
}

/* Asks can name a project with no matching session row. Keep that real registry
   claim visible as its own group instead of dropping it or silently attaching
   it to the asker's session: attribution is caller-supplied at registration. */
function projectGroups(d){
  const groups = new Map();
  const ensure = raw => {
    const label = String(raw || "Unlabeled project");
    if(!groups.has(label)) groups.set(label, {label:label, sessions:[], asks:[]});
    return groups.get(label);
  };
  for(const sess of (d && Array.isArray(d.sessions) ? d.sessions : [])){
    ensure(sess.project).sessions.push(sess);
  }
  if(d && d.ask && Array.isArray(d.asks)){
    for(const ask of d.asks) ensure(ask && ask.project).asks.push(ask);
  }
  return Array.from(groups.values()).sort((a, b) => {
    if(a.asks.length !== b.asks.length) return b.asks.length - a.asks.length;
    const newest = group => Math.max(0, ...group.sessions.map(s => Number(s.last_activity) || 0));
    return newest(b) - newest(a) || a.label.localeCompare(b.label);
  });
}

function projectCockpitGroup(d){
  const groups = projectGroups(d);
  let group = groups.find(item => item.label === projectQueryLabel);
  if(!group) group = groups.find(item => item.label === projectCockpitLabel);
  if(!group && groups.length){
    group = groups[0];
    projectCockpitLabel = group.label;
  }
  if(group) projectCockpitLabel = group.label;
  return {groups:groups, selected:group || null};
}

function projectFocusSession(group){
  if(!group || !projectQuerySession) return null;
  return group.sessions.find(sess => sessKey(sess) === projectQuerySession) || null;
}

function setProjectCockpit(label){
  projectCaptureDraft();
  projectCockpitLabel = String(label || "");
  projectQueryLabel = projectCockpitLabel;
  projectQuerySession = null;
  projectGoalNote = "";
  try{ localStorage.setItem(PROJECT_COCKPIT_KEY, projectCockpitLabel); }
  catch(e){ /* selection still works for this page */ }
  projectSyncUrl(projectCockpitLabel, null, false);
  if(lastData) render(lastData);
}

function projectCaptureDraft(){
  const field = document.getElementById("pc-goal");
  if(!field) return null;
  const label = field.getAttribute ? field.getAttribute("data-project") : null;
  if(!label) return null;
  const value = String(field.value == null ? "" : field.value);
  projectDraftByLabel[label] = value;
  return {
    label: label,
    value: value,
    focused: document.activeElement === field
  };
}

function projectRestoreFocus(draft){
  if(!draft || !draft.focused) return;
  const field = document.getElementById("pc-goal");
  if(!field || !field.focus) return;
  if(field.getAttribute && field.getAttribute("data-project") !== draft.label) return;
  field.focus();
  if(field.setSelectionRange) field.setSelectionRange(field.value.length, field.value.length);
}

function projectGoalAction(act, label){
  const key = projectGoalKey(label);
  if(act === "project-reload"){
    try{ location.reload(); }catch(e){ projectGoalNote = "reload is unavailable here"; }
    return true;
  }
  if(act === "project-link-copy"){
    const link = projectPermalink(label, projectQuerySession);
    if(navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(link).then(() => {
        projectGoalNote = "project link copied";
        if(lastData) render(lastData);
      }).catch(() => {
        projectGoalNote = "copy unavailable";
        if(lastData) render(lastData);
      });
    } else {
      projectGoalNote = "copy unavailable";
      if(lastData) render(lastData);
    }
    return true;
  }
  if(act !== "project-goal-save" && act !== "project-goal-clear") return false;
  const field = document.getElementById("pc-goal");
  try{
    if(act === "project-goal-clear"){
      localStorage.removeItem(key);
      delete projectDraftByLabel[label];
      projectGoalNote = "browser goal cleared";
    } else {
      const value = String(field && field.value || "").trim();
      if(!value){ projectGoalNote = "write an outcome first"; }
      else {
        localStorage.setItem(key, value);
        projectDraftByLabel[label] = value;
        projectGoalNote = "remembered in this browser";
      }
    }
  }catch(e){ projectGoalNote = "browser storage unavailable"; }
  if(lastData) render(lastData);
  return true;
}

function projectAction(act, arg){
  if(act === "project-cockpit"){
    setProjectCockpit(arg);
    return true;
  }
  if(act === "project-context-refresh"){
    const current = projectContextEntry(projectCockpitLabel);
    if(current && current.state === "loading") return true;
    projectLoadContext(lastData, true);
    return true;
  }
  if(act === "project-session-focus"){
    projectCaptureDraft();
    projectQueryLabel = projectCockpitLabel;
    projectQuerySession = String(arg || "");
    projectGoalNote = "focused session changed";
    projectSyncUrl(projectCockpitLabel, projectQuerySession, false);
    if(lastData) render(lastData);
    return true;
  }
  if(act === "project-session-link-copy"){
    const link = projectPermalink(projectCockpitLabel, String(arg || ""));
    if(navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(link).then(() => {
        projectGoalNote = "session link copied";
        if(lastData) render(lastData);
      }).catch(() => {
        projectGoalNote = "copy unavailable";
        if(lastData) render(lastData);
      });
    }
    return true;
  }
  return projectGoalAction(act, String(arg || ""));
}

document.addEventListener("change", e => {
  const field = e.target;
  if(field && field.id === "pc-project-select") setProjectCockpit(field.value);
});

if(typeof window !== "undefined" && window.addEventListener){
  window.addEventListener("popstate", () => {
    try{
      projectQueryLabel = new URLSearchParams(location.search || "").get("project");
      projectQuerySession = new URLSearchParams(location.search || "").get("session");
      const mode = new URLSearchParams(location.search || "").get("mode");
      if(mode === "calm" || mode === "project" || mode === "regular" || mode === "session"){
        displayMode = mode;
      }
      if(lastData) render(lastData);
    }catch(e){ /* keep the current project */ }
  });
}

function projectSessionRow(sess){
  const key = sessKey(sess);
  const detail = humanTool(sess.state_detail) || sess.last_prompt || "No current detail";
  const working = sess.state === "working";
  const state = (sess.state === "needs_input" || sess.needs_you === true) ? "needs you" :
    (working ? "working now" : (sess.active ? "recent · idle" : "idle"));
  return `<button type="button" class="pc-session" data-calm="project-session-focus" data-arg="${esc(key)}">` +
    `<span class="pc-session-state ${working ? "working" : ""}"></span>` +
    `<span class="pc-session-copy"><strong>${esc(sess.title || "Untitled session")}</strong>` +
    `<span>${esc(state)} · ${esc(detail)}</span></span>` +
    `<code>${esc(key)}</code></button>`;
}

function projectSessionSection(title, rows){
  if(!rows.length) return "";
  return `<div class="pc-session-group"><div class="pc-session-group-head">` +
    `<span>${esc(title)}</span><b>${rows.length}</b></div>` +
    rows.map(projectSessionRow).join("") + `</div>`;
}

function projectMirrorAttention(d, sess, group){
  const exactAsks = d.ask && Array.isArray(group.asks)
    ? group.asks.filter(ask => String(ask && ask.harness || "") === String(sess.harness || "") &&
      String(ask && ask.session_id || "") === String(sess.sid || ""))
    : [];
  if(exactAsks.length){
    return `<div class="pc-mirror-attention attention" data-request-state="ask">` +
      `<span class="pc-kicker">Needs you</span>` +
      exactAsks.map(ask => askCard(ask, null, false)).join("") +
      `<code>AskRegistry · exact focused session</code></div>`;
  }
  if(sess.state === "needs_input" || sess.needs_you === true){
    return `<div class="pc-mirror-attention attention" data-request-state="overlay">` +
      `<span class="pc-kicker">Needs you</span>` +
      `<strong>${esc(sess.needs_reason || "live session requests attention")}</strong>` +
      `<button type="button" class="quiet" data-calm="project-session-link-copy"` +
      ` data-arg="${esc(sessKey(sess))}">copy session link</button>` +
      `<code>live session overlay</code></div>`;
  }
  return `<div class="pc-request-none" data-request-state="none">No request detected</div>`;
}

function projectSubagentHierarchy(sess){
  const reported = Array.isArray(sess.subagent_hierarchy)
    ? sess.subagent_hierarchy
    : (Array.isArray(sess.subagents) ? sess.subagents.map(agent => Object.assign({
      depth: 1, parent_name: null
    }, agent)) : []);
  if(!reported.length){
    return `<div class="pc-child-tree"><span class="pc-kicker">Active child hierarchy</span>` +
      `<span class="pc-child-empty">No active child session reported.</span></div>`;
  }
  const rows = reported.slice().sort((a, b) =>
    (Number(a.depth) || 1) - (Number(b.depth) || 1));
  return `<div class="pc-child-tree"><span class="pc-kicker">Active child hierarchy</span>` +
    rows.map(agent => {
      const depth = Math.max(1, Math.min(6, Number(agent.depth) || 1));
      const relation = agent.parent_name ? `child of ${agent.parent_name}` : "direct child";
      return `<div class="pc-child depth-${depth}" data-subagent-depth="${depth}">` +
        `<span class="pc-child-node"></span><strong>${esc(agent.name || "subagent")}</strong>` +
        `<span>${esc(relation)} · ${esc(agent.model || "model unavailable")}</span></div>`;
    }).join("") + `</div>`;
}

function projectSessionMirror(d, sess, group){
  if(!sess){
    if(!projectQuerySession) return "";
    return `<section class="pc-mirror unavailable">` +
      `<div class="pc-kicker">Focused session unavailable</div>` +
      `<p>The requested session is not present in this project's live dashboard payload.</p>` +
      `<code>${esc(projectQuerySession)}</code></section>`;
  }
  const key = sessKey(sess);
  const detail = humanTool(sess.state_detail) || sess.last_prompt || "No current detail";
  const state = sess.state === "working" ? "working now" :
    ((sess.state === "needs_input" || sess.needs_you === true) ? "needs you" :
      (sess.active ? "recent · idle" : "idle"));
  return `<section class="pc-mirror" data-session-mirror="${esc(key)}">` +
    `<div class="pc-mirror-head"><div><span class="pc-kicker">Right now</span>` +
    `<h3>${esc(sess.title || "Untitled Codex session")}</h3></div>` +
    `<div class="pc-mirror-actions">${projectRefreshControl(group.label, false)}` +
    `<button type="button" class="quiet" data-calm="project-session-link-copy"` +
    ` data-arg="${esc(key)}">copy session link</button></div></div>` +
    `<div class="pc-mirror-meta"><code>${esc(key)}</code>` +
    `<span>model · ${esc(sess.model || "unavailable")}</span></div>` +
    `<div class="pc-now"><div class="pc-mirror-state"><strong>${esc(state)}</strong>` +
    `<span>${esc(detail)}</span></div>` + projectMirrorAttention(d, sess, group) +
    projectSubagentHierarchy(sess) +
    `<div class="pc-mirror-purpose"><span class="pc-kicker">Derived purpose · subordinate</span>` +
    `${projectObserverSummary(group, true)}</div>` +
    projectRecentSteering(sess, group) + `</div></section>`;
}

function projectObserverSummary(group, focused){
  const entry = projectContextEntry(group.label);
  if(!entry || entry.state === "loading"){
    return `<div class="pc-observer-empty">Reading project transcripts and entity state…</div>`;
  }
  if(entry.state === "error" || !entry.data){
    return `<div class="pc-observer-empty">Project observer source is unavailable.</div>`;
  }
  let rows = Array.isArray(entry.data.observers) ? entry.data.observers : [];
  if(projectQuerySession){
    rows = rows.filter(sidecar => `${sidecar.harness}:${sidecar.sid}` === projectQuerySession);
  }
  if(!rows.length){
    return `<div class="pc-observer-empty">No readable Claude, Codex, or Pi transcript was found for the focused session.</div>`;
  }
  return rows.map(sidecar => {
    const key = `${sidecar.harness}:${sidecar.sid}`;
    const goal = sidecar.goal && sidecar.goal !== "no goal derived"
      ? `<div class="pc-observer-goal">${esc(sidecar.goal)}</div>`
      : `<div class="pc-observer-empty">No observer goal derived for this session.</div>`;
    const facts = focused ? [] : [
      sidecar.stage ? `stage · ${sidecar.stage}` : "workflow stage unavailable",
      sidecar.block ? `open block · ${sidecar.block}` : "open-block reading unavailable"
    ];
    const model = sidecar.model || {};
    const modelLine = model.model
      ? `${model.model} · reasoning ${model.reasoning_effort || "unavailable"} · ${model.status || "unknown"}`
      : "deterministic observer fallback";
    return `<div class="pc-observer-row">${goal}` + (facts.length
      ? `<div class="pc-observer-facts">${facts.map(f => `<span>${esc(f)}</span>`).join("")}</div>`
      : "") + `<div class="pc-observer-source">derived, subordinate · ${esc(modelLine)} · ${esc(key)}</div></div>`;
  }).join("");
}

function projectRecentSteering(sess, group){
  const entry = projectContextEntry(group.label);
  if(!entry || entry.state === "loading" && !entry.data){
    return `<div class="pc-mirror-steer unavailable">Reading recent user-role messages…</div>`;
  }
  if(entry.state === "error" || !entry.data){
    return `<div class="pc-mirror-steer unavailable">Recent message source unavailable.</div>`;
  }
  const event = (Array.isArray(entry.data.events) ? entry.data.events : []).find(row =>
    row.kind === "steer" && row.harness === sess.harness && row.sid === sess.sid);
  if(!event){
    return `<div class="pc-mirror-steer unavailable">No timestamped user-role message found for this session.</div>`;
  }
  const timestamp = Number(event.at);
  const iso = Number.isFinite(timestamp) ? new Date(timestamp * 1000).toISOString() : "";
  return `<div class="pc-mirror-steer"><span class="pc-kicker">Most recent user-role message</span>` +
    `<strong>${esc(event.title)}</strong>` +
    `<span>${esc(event.source || "source unavailable")}` +
    (iso ? ` · <time datetime="${esc(iso)}">${esc(iso)}</time>` : " · timestamp unavailable") +
    `</span></div>`;
}

function projectLoadContext(d, refresh){
  const group = projectCockpitGroup(d).selected;
  if(!group) return;
  const cacheKey = projectContextKey(group.label);
  const old = projectContextByLabel[cacheKey];
  if(old && !refresh) return;
  projectContextByLabel[cacheKey] = {
    state: "loading", data: old && old.data || null, generated: d.generated
  };
  if(refresh){
    projectGoalNote = "refreshing context…";
    if(lastData) render(lastData);
  }
  const query = "/api/project-context?project=" + encodeURIComponent(group.label) +
    (projectQuerySession ? "&session=" + encodeURIComponent(projectQuerySession) : "") +
    (refresh ? "&refresh=1" : "");
  fetch(query).then(r => {
    if(!r.ok) throw new Error("bad status");
    return r.json();
  }).then(data => {
    projectContextByLabel[cacheKey] = {state: "ready", data: data, generated: d.generated};
    if(refresh) projectGoalNote = "context refreshed";
    if(lastData) render(lastData);
  }).catch(() => {
    projectContextByLabel[cacheKey] = {state: "error", data: null, generated: d.generated};
    if(refresh) projectGoalNote = "context refresh failed";
    if(lastData) render(lastData);
  });
}

function projectTimelineEvents(focus, sourceEvents){
  const exact = row => !focus ||
    (row.harness === focus.harness && row.sid === focus.sid);
  const events = sourceEvents.filter(exact).map(row => Object.assign({}, row));
  return events.filter(event => Number(event.at)).sort((a, b) => a.at - b.at).slice(-12);
}

function projectLifecycleEvidence(focus){
  const events = focus && Array.isArray(focus.subagent_events) ? focus.subagent_events : [];
  if(!events.length) return "";
  const count = kind => events.filter(event => event.kind === kind).length;
  return `<p data-lifecycle-suppressed="${events.length}"><b>Suppressed child telemetry:</b> ` +
    `${events.length} typed child lifecycle records · ` +
    `${count("subagent_task_started")} task starts · ${count("subagent_complete")} completions · ` +
    `${count("subagent_interrupted")} interruptions. Lifecycle labels without demonstrated results stay telemetry; ` +
    `they do not enter What happened.</p>`;
}

function projectRelationTarget(event, steering){
  if(!event.related_to || !event.relation_source) return null;
  return steering.find(item => item.id && item.id === event.related_to) || null;
}

function projectSemanticNode(d, event, kind, steering){
  const ago = event.at
    ? fmtDur(Math.max(0, (Number(d.generated) || 0) - event.at)) + " ago"
    : "time unavailable";
  const iso = event.at ? new Date(Number(event.at) * 1000).toISOString() : "";
  const intent = kind === "steer" && event.intent && event.intent_source
    ? `<span class="pc-intent">intent · ${esc(event.intent)}</span>` : "";
  const relation = kind === "outcome" && projectRelationTarget(event, steering)
    ? `<span class="pc-relation" data-causal-link="supported">linked by ${esc(event.relation_source)}</span>`
    : "";
  return `<article class="pc-semantic-node ${kind}">` +
    `<div class="pc-event-title">${esc(event.title)}</div>${intent}${relation}` +
    `<details class="pc-event-evidence"><summary>${esc(ago)} · source</summary>` +
    `<div>${esc(event.phase || event.kind)} · ${esc(event.source || "source unavailable")}` +
    (iso ? ` · <time datetime="${esc(iso)}">${esc(iso)}</time>` : "") +
    (event.detail ? ` · ${esc(event.detail)}` : "") + `</div></details></article>`;
}

function projectSemanticLane(d, title, kind, events, steering){
  const empty = kind === "steer"
    ? "No timestamped non-meta user-role instruction found."
    : "No demonstrated outcome found for this session.";
  return `<section class="pc-semantic-lane" data-semantic-lane="${kind === "steer" ? "steering" : "outcome"}">` +
    `<h4>${esc(title)}</h4>` + (events.length
      ? events.map(event => projectSemanticNode(d, event, kind, steering)).join("")
      : `<div class="pc-semantic-empty">${empty}</div>`) + `</section>`;
}

function projectWorkIntervals(steering, outcomes){
  const rows = [];
  for(const outcome of outcomes){
    const linked = projectRelationTarget(outcome, steering);
    const prior = steering.filter(event => event.at <= outcome.at);
    const start = linked || prior[prior.length - 1];
    if(!start) continue;
    rows.push({start:start, outcome:outcome, linked:!!linked});
  }
  return rows;
}

function projectWorkIntervalRows(intervals){
  if(!intervals.length) return "";
  return `<section class="pc-work-intervals"><h4>Work intervals</h4>` + intervals.map(row => {
    const elapsed = fmtDur(Math.max(0, Number(row.outcome.at) - Number(row.start.at)));
    const relation = row.linked ? "source-linked interval" : "chronology only · relationship unverified";
    return `<div class="pc-work-interval" data-interval-relation="${row.linked ? "supported" : "unverified"}">` +
      `<strong>Work interval · ${esc(elapsed)}</strong><span>${relation}</span></div>`;
  }).join("") + `</section>`;
}

/* One source-honest sequence for the focused session. Each event keeps the
   identity its producer can actually prove; generic user-role rows never gain
   captain authorship here. */
function projectActivity(d, group, focus){
  const entry = projectContextEntry(group.label);
  const contextEvents = entry && entry.data && Array.isArray(entry.data.events)
    ? entry.data.events : [];
  const events = projectTimelineEvents(
    focus,
    contextEvents
  );
  const steering = events.filter(event => event.kind === "steer");
  const outcomeKinds = new Set([
    "gate", "checkpoint", "decision", "test_result", "ask_resolution", "outcome"
  ]);
  const outcomes = events.filter(event => outcomeKinds.has(event.kind));
  if(!steering.length && !outcomes.length){
    const reading = !entry || entry.state === "loading"
      ? "Reading the gate and instruction sources…"
      : (entry.state === "error" || !entry.data
        ? "Gate and instruction sources are unavailable."
        : "No timestamped exact-session change was found.");
    return `<div class="pc-empty${entry && entry.state === "error" ? " unavailable" : ""}">` +
      `${reading}</div>`;
  }
  return `<div class="pc-semantic-graph" data-causal-model="source-only">` +
    projectSemanticLane(d, "What you asked", "steer", steering, steering) +
    projectSemanticLane(d, "What happened", "outcome", outcomes, steering) +
    projectWorkIntervalRows(projectWorkIntervals(steering, outcomes)) + `</div>`;
}

function projectHistoryBoundary(sources){
  const gate = sources && sources.gate || {};
  const steer = sources && sources.steer || {};
  const missing = Array.isArray(steer.unavailable) ? steer.unavailable.length : 0;
  const omitted = Array.isArray(steer.omitted) ? steer.omitted.length : 0;
  const scope = sources && sources.scope || "selected project";
  const surrounding = Number(sources && sources.surrounding_active) || 0;
  return `<div class="pc-history-boundary">` +
    `live ${esc(scope)} · ${Number(gate.live) || 0} gate decisions · ${Number(steer.live) || 0} user-role messages · ` +
    `${Number(gate.untimestamped_prepare) || 0} gate preparations lack timestamps · ` +
    `status-transition history unavailable · ${missing} session transcript readers unavailable · ` +
    `${omitted} sessions omitted by the three-session bound · ` +
    `${surrounding} other recent project sessions remain lightweight context</div>`;
}

function projectView(d, draft){
  const model = projectCockpitGroup(d);
  const groups = model.groups;
  const group = model.selected;
  const updated = new Date(d.generated * 1000).toLocaleTimeString();
  const top = `<div class="pc-top"><div><div class="brand">Cargento</div>` +
    `<div class="sub"><span class="live" id="live-dot"></span>` +
    `<span id="live-status">live · updated ${esc(updated)}</span></div></div>` +
    `<span class="pc-mode-note">project cockpit · live dashboard data</span></div>`;
  if(!group){
    return top + `<div class="pc-nav"><span class="pc-nav-k">project</span></div>` +
      `<div class="pc-empty">No project-labelled sessions are available.</div>`;
  }
  const options = groups.map(item => {
    const on = item.label === group.label ? " selected" : "";
    return `<option value="${esc(item.label)}"${on}>${esc(item.label)} · ${item.sessions.length} recent</option>`;
  }).join("");
  const recent = group.sessions.filter(sess => sess.active);
  const focus = projectFocusSession(group);
  const goal = draft && draft.label === group.label ? draft.value : projectGoal(group.label);
  const goalKey = projectGoalKey(group.label);
  const note = `<span id="pc-status" class="pc-goal-note" role="status"` +
    ` aria-live="polite" aria-atomic="true">${esc(projectGoalNote)}</span>`;
  const surrounding = recent.filter(sess => !focus || sessKey(sess) !== sessKey(focus));
  const surroundingWorking = surrounding.filter(sess =>
    sess.state === "working" || sess.state === "needs_input" || sess.needs_you === true);
  const surroundingIdle = surrounding.filter(sess =>
    sess.state !== "working" && sess.state !== "needs_input" && sess.needs_you !== true);
  const sessions = surrounding.length
    ? projectSessionSection("Working now", surroundingWorking) +
      projectSessionSection("Recent and idle", surroundingIdle)
    : `<div class="pc-empty">No other recent sessions in this project.</div>`;
  const workingNow = recent.filter(sess => sess.state === "working").length;
  const mirror = projectQuerySession ? projectSessionMirror(d, focus, group) : "";
  const aggregateObserver = projectQuerySession ? "" :
    `<div class="pc-observer"><div class="pc-subhead"><h3>Observer context</h3>` +
    `<span>derived · subordinate</span>${projectRefreshControl(group.label, true)}</div>` +
    `${projectObserverSummary(group)}</div>`;
  return top + `<nav class="pc-nav" aria-label="Project being resumed">` +
    `<label class="pc-nav-k" for="pc-project-select">project</label>` +
    `<select id="pc-project-select">${options}</select>` +
    `<button type="button" class="pc-link" data-calm="project-link-copy"` +
    ` data-arg="${esc(group.label)}">copy link</button></nav>` +
    `<section class="pc-focus"><div class="pc-focus-head"><div>` +
    `<span class="pc-kicker">Project context</span><h2>${esc(group.label)}</h2></div>` +
    `<div class="pc-counts"><span><b>${workingNow}</b> working now</span>` +
    `<span><b>${recent.length}</b> recent</span>` +
    `</div></div><div class="pc-goal"><label for="pc-goal">` +
    `Operator note <em>remembered in this browser · precedes inference</em></label>` +
    `<textarea id="pc-goal" data-project="${esc(group.label)}" maxlength="500" rows="3"` +
    ` placeholder="What outcome do you want to remember here?">${esc(goal)}</textarea>` +
    `<div class="pc-goal-actions"><button type="button" data-calm="project-goal-save"` +
    ` data-arg="${esc(group.label)}">remember</button>` +
    `<button type="button" class="quiet" data-calm="project-reload"` +
    ` data-arg="${esc(group.label)}">reload page</button>` +
    `<button type="button" class="quiet" data-calm="project-goal-clear"` +
    ` data-arg="${esc(group.label)}">clear</button>${note}</div>` +
    `<div class="pc-key">browser-local exact-label key · ${esc(goalKey)} · observer inference never overwrites this note</div></div>` +
    `${mirror}${aggregateObserver}` +
    `<div class="pc-activity"><div class="pc-active-head"><h3>What changed</h3>` +
    `<span>chronological · verified sources only</span></div>${projectActivity(d, group, focus)}</div>` +
    `<div class="pc-other"><div class="pc-active-head"><h3>Other project sessions</h3>` +
    `<span>lightweight surrounding context</span></div>${sessions}</div>` +
    `</section>` +
    `<details class="pc-sources"><summary>Evidence and limitations</summary>` +
    `<p><b>Live:</b> sessions and asks come from this dashboard's API. Only real AskRegistry entries appear.</p>` +
    `<p><b>Derived:</b> project groups, goal keys, and permalinks use exact display-label equality. The label is not a stable id.</p>` +
    `<p><b>Browser-owned operator note:</b> each exact label has a separate key on this origin. It precedes inference but is not durable project authority; same-label projects collide, and a rename orphans the value.</p>` +
    `<p><b>Observer:</b> goals come from bounded Claude, Codex, or Pi transcripts and stay subordinate. For the present handoff, workflow stage unavailable and open-block reading unavailable remain explicit rather than inferred.</p>` +
    `<p><b>History:</b> known meta wrappers are excluded; remaining steering evidence is labeled only as timestamped user-role transcript messages because captain authorship is not recorded. Gate decisions are timestamped entity frontmatter resolutions. Untimestamped prepare and status-transition history stay unavailable.</p>` +
    `<p><b>Child lifecycle:</b> Codex hierarchy follows recorded parent thread ids. Task-start, completion, and interruption events are bounded to typed records in the 24 newest child rollouts; no spawn is inferred from a task start or from file freshness.</p>` +
    `${projectLifecycleEvidence(focus)}` +
    `<p><b>Requests:</b> “No request detected” means neither an exact focused-session AskRegistry row nor a live needs-input overlay is present. It is not proof that this session is unblocked.</p>` +
    `<p><b>Unavailable:</b> durable project identity, durable operator-note persistence, ask reassignment, steering transport, and unsupported stage, block, gate, or outcome history.</p>` +
    `${projectContextEntry(group.label) && projectContextEntry(group.label).data
      ? projectHistoryBoundary(projectContextEntry(group.label).data.sources) : ""}</details>`;
}
