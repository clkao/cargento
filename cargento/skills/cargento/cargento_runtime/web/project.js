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
const PROJECT_STEERING_NODE_LIMIT = 3;
const PROJECT_OUTCOME_NODE_LIMIT = 4;
const PROJECT_SOURCE_LANE_WINDOW = 6;
const PROJECT_OUTCOME_KINDS = new Set([
  "gate", "checkpoint", "decision", "test_result", "ask_resolution", "outcome", "work"
]);
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
  if(!reported.length) return "";
  const rows = reported.slice().sort((a, b) =>
    (Number(a.depth) || 1) - (Number(b.depth) || 1));
  return `<div class="pc-child-tree"><span class="pc-kicker">Active child hierarchy</span>` +
    rows.map(agent => {
      const depth = Math.max(1, Math.min(6, Number(agent.depth) || 1));
      const relation = agent.parent_name ? `child of ${agent.parent_name}` : "direct child";
      const model = agent.model ? ` · ${agent.model}` : "";
      return `<div class="pc-child depth-${depth}" data-subagent-depth="${depth}">` +
        `<span class="pc-child-node"></span><strong>${esc(agent.name || "subagent")}</strong>` +
        `<span>${esc(relation + model)}</span></div>`;
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
    (sess.model ? `<span>model · ${esc(sess.model)}</span>` : "") + `</div>` +
    `<div class="pc-now"><div class="pc-mirror-state"><strong>${esc(state)}</strong>` +
    `<span>${esc(detail)}</span></div>` + projectMirrorAttention(d, sess, group) +
    projectSubagentHierarchy(sess) + `</div></section>`;
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
  const semantic = events.filter(event => Number(event.at) && event.source &&
    (event.kind === "steer" || PROJECT_OUTCOME_KINDS.has(event.kind)))
    .sort((a, b) => a.at - b.at);
  const steering = semantic.filter(event => event.kind === "steer")
    .slice(-PROJECT_SOURCE_LANE_WINDOW);
  const work = semantic.filter(event => PROJECT_OUTCOME_KINDS.has(event.kind));
  const selectedWork = work.slice(-PROJECT_SOURCE_LANE_WINDOW);
  const preserveNewest = phase => {
    const candidate = work.filter(event => event.phase === phase).slice(-1)[0];
    if(!candidate || selectedWork.some(event => event.phase === phase)) return;
    if(selectedWork.length >= PROJECT_SOURCE_LANE_WINDOW) selectedWork.shift();
    selectedWork.push(candidate);
  };
  preserveNewest("Spacedock dispatch build");
  preserveNewest("ordinary subagent task and paired result");
  return steering.concat(selectedWork).sort((a, b) => a.at - b.at);
}

function projectLifecycleEvidence(focus){
  const events = focus && Array.isArray(focus.subagent_events) ? focus.subagent_events : [];
  if(!events.length) return "";
  const count = kind => events.filter(event => event.kind === kind).length;
  return `<li data-lifecycle-suppressed="${events.length}"><b>Child telemetry:</b> ` +
    `${events.length} typed child lifecycle records · ` +
    `${count("subagent_task_started")} task starts · ${count("subagent_complete")} completions · ` +
    `${count("subagent_interrupted")} interruptions. Lifecycle labels without demonstrated results stay telemetry; ` +
    `they do not enter What happened.</li>`;
}

function projectRelationTarget(event, steering){
  if(!event.related_to || !event.relation_source) return null;
  return steering.find(item => item.id && item.id === event.related_to) || null;
}

function projectSemanticNode(d, event, kind, steering, visible){
  const ago = event.at
    ? fmtDur(Math.max(0, (Number(d.generated) || 0) - event.at)) + " ago"
    : "time unavailable";
  const iso = event.at ? new Date(Number(event.at) * 1000).toISOString() : "";
  const steeringTag = kind === "steer" && event.steering_tag && event.tag_source
    ? `<span class="pc-intent">${esc(event.steering_tag)}</span>` : "";
  const relation = kind === "outcome" && projectRelationTarget(event, steering)
    ? `<span class="pc-relation" data-causal-link="supported">linked by ${esc(event.relation_source)}</span>`
    : "";
  return `<article class="pc-semantic-node ${kind}" data-visible-node="${visible}">` +
    `<div class="pc-event-title">${esc(event.title)}</div>${steeringTag}${relation}` +
    `<details class="pc-event-evidence"><summary>evidence</summary>` +
    `<div>${esc(ago)} · ${esc(event.phase || event.kind)} · ${esc(event.source || "source unavailable")}` +
    (iso ? ` · <time datetime="${esc(iso)}">${esc(iso)}</time>` : "") +
    (event.detail ? ` · ${esc(event.detail)}` : "") + `</div></details></article>`;
}

function projectSemanticLane(d, title, kind, events, steering){
  const empty = kind === "steer"
    ? "No timestamped non-meta user-role instruction found."
    : "No demonstrated outcome found for this session.";
  const newest = events.slice().reverse();
  const limit = kind === "steer" ? PROJECT_STEERING_NODE_LIMIT : PROJECT_OUTCOME_NODE_LIMIT;
  const visible = newest.slice(0, limit);
  const overflow = newest.slice(limit);
  return `<section class="pc-semantic-lane" data-order="newest-first"` +
    ` data-semantic-lane="${kind === "steer" ? "steering" : "outcome"}">` +
    `<h4>${esc(title)}</h4>` + (visible.length
      ? visible.map(event => projectSemanticNode(d, event, kind, steering, true)).join("")
      : `<div class="pc-semantic-empty">${empty}</div>`) +
    (overflow.length ? `<details class="pc-semantic-overflow"><summary>${overflow.length} older ` +
      `${kind === "steer" ? "instructions" : "work records"}</summary>` +
      overflow.map(event => projectSemanticNode(d, event, kind, steering, false)).join("") +
      `</details>` : "") + `</section>`;
}

function projectDerivedContext(d, observers, focus){
  const rows = observers.filter(row => {
    if(!Number(row.observed_at) || !row.goal || row.goal === "no goal derived") return false;
    return !focus || (row.harness === focus.harness && row.sid === focus.sid);
  });
  if(!rows.length) return "";
  return `<section class="pc-derived-context"><h4>Derived context snapshot</h4>` +
    rows.slice().sort((a, b) => b.observed_at - a.observed_at).map(row => {
      const ago = fmtDur(Math.max(0, (Number(d.generated) || 0) - Number(row.observed_at))) + " ago";
      const iso = new Date(Number(row.observed_at) * 1000).toISOString();
      const model = row.model || {};
      const modelLine = model.model
        ? `${model.model} · reasoning ${model.reasoning_effort || "not reported"} · ${model.status || "not reported"}`
        : "deterministic observer fallback";
      return `<article class="pc-semantic-node context" data-visible-node="true"><span class="pc-context-kind">derived · subordinate</span>` +
        `<div class="pc-event-title">${esc(row.goal)}</div>` +
        `<details class="pc-event-evidence"><summary>evidence</summary>` +
        `<div>${esc(ago)} · ${esc(row.source || "bounded transcript observation")} · ${esc(modelLine)} · ` +
        `<time datetime="${esc(iso)}">${esc(iso)}</time></div></details></article>`;
    }).join("") + `</section>`;
}

function projectWorkIntervals(steering, outcomes){
  const rows = [];
  for(const outcome of outcomes){
    const linked = projectRelationTarget(outcome, steering);
    if(!linked) continue;
    rows.push({start:linked, outcome:outcome, linked:true});
  }
  return rows.slice(-2);
}

function projectWorkIntervalRows(intervals){
  if(!intervals.length) return "";
  return `<section class="pc-work-intervals"><h4>Work intervals</h4>` + intervals.map(row => {
    const elapsed = fmtDur(Math.max(0, Number(row.outcome.at) - Number(row.start.at)));
    const relation = row.linked ? "source-linked interval" : "chronology only";
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
  const observers = entry && entry.data && Array.isArray(entry.data.observers)
    ? entry.data.observers : [];
  const events = projectTimelineEvents(
    focus,
    contextEvents
  );
  const steering = events.filter(event => event.kind === "steer");
  const outcomes = events.filter(event => PROJECT_OUTCOME_KINDS.has(event.kind));
  if(!steering.length && !outcomes.length && !observers.length){
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
    projectDerivedContext(d, observers, focus) +
    projectWorkIntervalRows(projectWorkIntervals(steering, outcomes)) + `</div>`;
}

function projectEvidenceLimits(group, focus){
  const entry = projectContextEntry(group.label);
  const sources = entry && entry.data && entry.data.sources || {};
  const gate = sources.gate || {};
  const steer = sources.steer || {};
  const observer = sources.observer || {};
  const work = sources.work || {};
  return `<ul class="pc-limit-list">` +
    `<li><b>Operator note:</b> Operator note overrides derived context. It is browser-only, keyed by the exact project label, and is not durable project authority. <code>${esc(projectGoalKey(group.label))}</code></li>` +
    `<li><b>Requests:</b> Absence of an exact AskRegistry or live needs-input signal does not prove unblocked.</li>` +
    `<li><b>Meaning:</b> “What you asked” means timestamped non-meta user-role text, not verified captain authorship. Chronological proximity does not imply causality; only a source-named relation is linked.</li>` +
    `<li><b>Derived context:</b> Bounded transcript observation stays subordinate. Stage and block are omitted when absent.</li>` +
    `<li><b>Observed sources:</b> ${Number(steer.live) || 0} steering records · ` +
    `${Number(gate.live) || 0} gate decisions · ${Number(work.live) || 0} work records · ` +
    `${Number(observer.live) || 0} derived snapshots. ` +
    `Status-transition history is omitted.</li>${projectLifecycleEvidence(focus)}</ul>`;
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
    `</div>` +
    `${mirror}` +
    `<div class="pc-activity"><div class="pc-active-head"><h3>What changed</h3>` +
    `<span>newest first · verified sources only</span>` +
    `${projectQuerySession ? "" : projectRefreshControl(group.label, true)}</div>` +
    `${projectActivity(d, group, focus)}</div>` +
    `<div class="pc-other"><div class="pc-active-head"><h3>Other project sessions</h3>` +
    `<span>lightweight surrounding context</span></div>${sessions}</div>` +
    `</section>` +
    `<details class="pc-sources"><summary>Evidence / limits</summary>` +
    `${projectEvidenceLimits(group, focus)}</details>`;
}
