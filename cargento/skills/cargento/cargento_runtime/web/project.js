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
const PROJECT_VISIBLE_ACTIVITY_NODES = 5;
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

function projectLiveAssignments(sess, group){
  const reported = Array.isArray(sess.subagent_hierarchy)
    ? sess.subagent_hierarchy
    : (Array.isArray(sess.subagents) ? sess.subagents.map(agent => Object.assign({
      depth: 1, parent_name: null
    }, agent)) : []);
  if(!reported.length) return "";
  const entry = projectContextEntry(group.label);
  const observed = entry && entry.data && Array.isArray(entry.data.child_assignments)
    ? entry.data.child_assignments : [];
  const rows = reported.slice().sort((a, b) =>
    (Number(a.depth) || 1) - (Number(b.depth) || 1));
  const workflowTitle = entity => {
    const words = String(entity || "").replace(/-/g, " ");
    return words ? words.charAt(0).toUpperCase() + words.slice(1) : "";
  };
  return `<div class="pc-assignment-group" data-assignment-group="working">` +
    `<div class="pc-assignment-head"><strong>Working now</strong><b>${rows.length}</b></div>` +
    rows.map(agent => {
      const depth = Math.max(1, Math.min(6, Number(agent.depth) || 1));
      const relation = agent.parent_name ? `child of ${agent.parent_name}` : "direct child";
      const fallback = observed.find(row => row.observer_sid && row.observer_sid === agent.observer_sid) || {};
      const assignment = agent.assignment || fallback.assignment || "assignment unavailable";
      const source = agent.assignment ? (agent.assignment_status || "exact parent dispatch") :
        (fallback.assignment ? `${fallback.source || "child observer snapshot"} · ${fallback.snapshot_status || "derived"}` :
          "no readable parent dispatch or cached child snapshot");
      const observedAt = Number(fallback.observed_at)
        ? ` · ${new Date(Number(fallback.observed_at) * 1000).toISOString()}` : "";
      const entity = agent.workflow_entity || fallback.workflow_entity || "";
      const stage = agent.workflow_stage || fallback.workflow_stage || "";
      if(entity && stage){
        return `<div class="pc-work-item depth-${depth}" data-subagent-depth="${depth}"` +
          ` data-assignment-state="working" data-work-item="${esc(entity)}"` +
          ` data-work-stage="${esc(stage)}"><span class="pc-child-node"></span>` +
          `<div class="pc-work-copy"><strong>${esc(workflowTitle(entity))}` +
          ` <b>· ${esc(stage)}</b></strong><span>${esc(assignment)}</span>` +
          `<small>${esc(agent.name || "Ensign")} · ${esc(relation)} · ${esc(source + observedAt)}</small>` +
          `</div><em>working now</em></div>`;
      }
      return `<div class="pc-assignment depth-${depth}" data-subagent-depth="${depth}"` +
        ` data-assignment-state="working"><span class="pc-child-node"></span>` +
        `<div class="pc-assignment-copy"><strong>${esc(agent.name || "Subagent")}</strong>` +
        `<span>${esc(assignment)}</span><small>${esc(relation)}</small>` +
        `<details><summary>source</summary>${esc(source + observedAt)}</details></div>` +
        `<em>working now</em></div>`;
    }).join("") + `</div>`;
}

function projectAssignmentRow(row, model){
  const facts = Array.isArray(model.facts) ? model.facts : [];
  const items = Array.isArray(model.work_items) ? model.work_items : [];
  const fact = facts.find(candidate => candidate.fact_id === row.assignment_fact) || {};
  const item = items.find(candidate => candidate.work_item_id === row.work_item_id) || {};
  const worker = row.worker_kind === "ensign" ? "Ensign" : "Subagent";
  const itemLabel = item.label || "";
  const assignment = row.assignment || itemLabel || "assignment unavailable";
  const distinctLabel = itemLabel && itemLabel !== assignment;
  if(item.kind === "workflow_item" || row.worker_kind === "ensign"){
    return `<div class="pc-work-item" data-assignment-state="${esc(row.state || "unknown")}">` +
      `<span class="pc-child-node"></span><div class="pc-work-copy">` +
      `<strong>${esc(itemLabel || assignment)}</strong>` +
      (distinctLabel ? `<span>${esc(assignment)}</span>` : "") +
      `<small>${esc(worker)} · ${row.state === "completed" ? "result returned" : "awaiting result"}</small>` +
      projectFactEvidence(fact) + `</div>` +
      `<em>${row.state === "completed" ? "completed" : "awaiting result"}</em></div>`;
  }
  return `<div class="pc-assignment" data-assignment-state="${esc(row.state || "unknown")}">` +
    `<span class="pc-child-node"></span><div class="pc-assignment-copy"><strong>${esc(worker)}</strong>` +
    (distinctLabel ? `<b>${esc(itemLabel)}</b>` : "") + `<span>${esc(assignment)}</span>` +
    projectFactEvidence(fact) + `</div>` +
    `<em>${row.state === "completed" ? "completed" : "awaiting result"}</em></div>`;
}

function projectAssignmentRoster(group, sess){
  const entry = projectContextEntry(group.label);
  const model = entry && entry.data && entry.data.semantic || {};
  const projections = model.projections || {};
  const assignments = Array.isArray(projections.assignments) ? projections.assignments : [];
  const awaiting = assignments.filter(row => row.state === "awaiting_result");
  const completed = assignments.filter(row => row.state === "completed");
  const live = projectLiveAssignments(sess, group);
  const pending = awaiting.length ? `<div class="pc-assignment-group" data-assignment-group="awaiting">` +
    `<div class="pc-assignment-head"><strong>Dispatched / awaiting result</strong><b>${awaiting.length}</b></div>` +
    awaiting.map(row => projectAssignmentRow(row, model)).join("") + `</div>` : "";
  const doneRows = completed.map(row => projectAssignmentRow(row, model)).join("");
  const done = completed.length ? ((live || awaiting.length)
    ? `<details class="pc-assignment-completed"><summary>Completed · ${completed.length}</summary>${doneRows}</details>`
    : `<div class="pc-assignment-group" data-assignment-group="completed"><div class="pc-assignment-head">` +
      `<strong>Completed</strong><b>${completed.length}</b></div>${doneRows}</div>`) : "";
  const loading = !entry || entry.state === "loading"
    ? `<div class="pc-child-empty">Reading assignment evidence…</div>` : "";
  if(!live && !pending && !done && !loading) return "";
  return `<div class="pc-assignment-roster"><span class="pc-kicker">Assignments</span>` +
    live + pending + done + loading + `</div>`;
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
  const activityAt = Number(sess.last_activity) || 0;
  const freshness = activityAt && Number(d.generated)
    ? `latest session evidence · ${fmtDur(Math.max(0, Number(d.generated) - activityAt))} ago`
    : "latest session evidence · time unavailable";
  return `<section class="pc-mirror" data-session-mirror="${esc(key)}">` +
    `<div class="pc-mirror-head"><div><span class="pc-kicker">Right now</span>` +
    `<h3>${esc(sess.title || "Untitled Codex session")}</h3></div>` +
    `<div class="pc-mirror-actions">${projectRefreshControl(group.label, false)}` +
    `<button type="button" class="quiet" data-calm="project-session-link-copy"` +
    ` data-arg="${esc(key)}">copy session link</button></div></div>` +
    `<div class="pc-mirror-meta"><code>${esc(key)}</code>` +
    (sess.model ? `<span>model · ${esc(sess.model)}</span>` : "") +
    `<span>${esc(freshness)}</span></div>` +
    `<div class="pc-now"><div class="pc-mirror-state"><strong>${esc(state)}</strong>` +
    `<span>${esc(detail)}</span></div>` + projectMirrorAttention(d, sess, group) +
    projectAssignmentRoster(group, sess) + `</div></section>`;
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
    projectContextByLabel[cacheKey] = {
      state: "error", data: old && old.data || null, generated: d.generated
    };
    if(refresh) projectGoalNote = "context refresh failed";
    if(lastData) render(lastData);
  });
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

function projectFactEvidence(fact){
  const evidence = fact.evidence || {};
  const iso = Number(fact.at) ? new Date(Number(fact.at) * 1000).toISOString() : "";
  return `<details class="pc-event-evidence"><summary>evidence</summary><div>` +
    `${esc(evidence.source || "source unavailable")}` +
    (evidence.confidence ? ` · ${esc(evidence.confidence)}` : "") +
    (iso ? ` · <time datetime="${esc(iso)}">${esc(iso)}</time>` : "") +
    `</div></details>`;
}

function projectTrailRow(d, head, model, node){
  const facts = Array.isArray(model.facts) ? model.facts : [];
  const items = Array.isArray(model.work_items) ? model.work_items : [];
  const item = items.find(candidate => candidate.work_item_id === head.work_item_id) || {};
  const latest = facts.find(fact => fact.fact_id === head.latest_meaningful_event) || {};
  const history = facts.filter(fact => fact.work_item_id === head.work_item_id)
    .sort((a, b) => Number(b.at) - Number(a.at));
  const status = head.status === "requested"
    ? "requested · current state unknown" : head.status;
  const age = latest.at ? fmtDur(Math.max(0, Number(d.generated) - Number(latest.at))) + " ago" : "";
  const kind = item.kind === "workflow_item" ? " workflow" : "";
  const retries = Number(node && node.retry_count) || 0;
  return `<article class="pc-trail${kind}" data-trail-head="${esc(head.status || "latest")}">` +
    `<span class="pc-trail-dot ${esc(head.status || "latest")}${kind}"></span><div class="pc-trail-body">` +
    `<div class="pc-trail-top"><strong>${esc(item.label || latest.summary || "Work item")}</strong>` +
    `<span>${esc(status)}${age ? ` · ${esc(age)}` : ""}</span></div>` +
    `<div class="pc-trail-result">${esc(latest.summary || "Latest state")}` +
    (retries ? ` <span class="pc-trail-quiet">· ${retries} earlier retr${retries === 1 ? "y" : "ies"} folded</span>` : "") +
    `</div>` +
    `<details class="pc-trail-history"><summary>${history.length} sourced event${history.length === 1 ? "" : "s"}</summary>` +
    history.map(fact => `<div class="pc-trail-event"><span>${esc(fact.summary || fact.type)}</span>` +
      projectFactEvidence(fact) + `</div>`).join("") + `</details></div></article>`;
}

function projectEpisodeRow(d, episode, model){
  const facts = Array.isArray(model.facts) ? model.facts : [];
  const intent = (model.projections.operator_intents || []).find(candidate =>
    candidate.projection_id === episode.intent_id) || {};
  const adaptation = facts.find(candidate => candidate.fact_id === episode.adaptation_fact) || {};
  const age = adaptation.at ? fmtDur(Math.max(0, Number(d.generated) - Number(adaptation.at))) + " ago" : "";
  const action = adaptation.summary || "Demonstrated reaction";
  const intentText = intent.summary || "Operator intent unavailable";
  return `<article class="pc-trail episode" data-steering-state="paired">` +
    `<span class="pc-trail-dot intent" title="${esc(intentText)}"></span><div class="pc-trail-body">` +
    `<div class="pc-trail-top"><strong>${esc(action)}</strong><span>${esc(age)}</span></div>` +
    `<details class="pc-trail-history"><summary>source-linked correction · ${esc(episode.confidence || "supported")}</summary>` +
    `<div class="pc-trail-event">Operator intent: ${esc(intentText)}</div></details>` +
    projectFactEvidence(adaptation) + `</div></article>`;
}

function projectBurstRow(d, node, model){
  const facts = Array.isArray(model.facts) ? model.facts : [];
  const items = Array.isArray(model.work_items) ? model.work_items : [];
  const ids = Array.isArray(node.work_item_ids) ? node.work_item_ids : [];
  const age = node.at ? fmtDur(Math.max(0, Number(d.generated) - Number(node.at))) + " ago" : "";
  const rows = ids.map(id => {
    const item = items.find(candidate => candidate.work_item_id === id) || {};
    const itemFacts = facts.filter(fact => fact.work_item_id === id)
      .sort((a, b) => Number(b.at) - Number(a.at));
    const latest = itemFacts[0] || {};
    return `<div class="pc-trail-event"><strong>${esc(item.label || "Work item")}</strong>` +
      `<span>${esc(latest.summary || "Source event unavailable")}</span></div>`;
  }).join("");
  return `<article class="pc-trail burst" data-semantic-burst="${ids.length}">` +
    `<span class="pc-trail-dot burst"></span><div class="pc-trail-body">` +
    `<div class="pc-trail-top"><strong>${Number(node.count) || ids.length} entities touched</strong>` +
    `<span>${esc(age)}</span></div><details class="pc-trail-history"><summary>show sourced work items</summary>` +
    rows + `</details></div></article>`;
}

function projectSemanticTimeline(d, model){
  const projections = model.projections || {};
  const facts = Array.isArray(model.facts) ? model.facts : [];
  const heads = Array.isArray(projections.trail_heads) ? projections.trail_heads : [];
  const episodes = Array.isArray(projections.steering_episodes)
    ? projections.steering_episodes : [];
  const activity = projections.activity || {};
  let nodes = Array.isArray(activity.nodes) ? activity.nodes : [];
  if(!nodes.length && !Object.prototype.hasOwnProperty.call(activity, "nodes")){
    nodes = heads.filter(head => ["prepared", "outcome", "decision"].includes(head.status))
      .slice(0, PROJECT_VISIBLE_ACTIVITY_NODES).map(head => {
      const fact = facts.find(candidate => candidate.fact_id === head.latest_meaningful_event) || {};
      return {kind:"work", at:fact.at, status:head.status,
        work_item_ids:[head.work_item_id], latest_event:head.latest_meaningful_event};
    });
  }
  const headByItem = new Map(heads.map(head => [head.work_item_id, head]));
  const activityRows = nodes.map(node => {
    if(node.kind === "burst") return {at:Number(node.at), html:projectBurstRow(d, node, model)};
    const firstId = Array.isArray(node.work_item_ids) ? node.work_item_ids[0] : "";
    const head = headByItem.get(firstId) || {work_item_id:firstId, status:node.status,
      latest_meaningful_event:node.latest_event};
    return {at:Number(node.at), html:projectTrailRow(d, head, model, node)};
  });
  const episodeRows = episodes.map(episode => {
    const fact = facts.find(candidate => candidate.fact_id === episode.adaptation_fact) || {};
    return {at:Number(fact.at), html:projectEpisodeRow(d, episode, model)};
  });
  const visible = activityRows.concat(episodeRows)
    .sort((a, b) => b.at - a.at);
  if(!visible.length) return `<div class="pc-empty">No source-backed current work or reaction.</div>`;
  return `<section class="pc-semantic-timeline" data-order="newest-first" data-model="fact-projection">` +
    visible.map(row => row.html).join("") + `</section>`;
}

function projectSemanticEvidence(group){
  const entry = projectContextEntry(group.label);
  const model = entry && entry.data && entry.data.semantic || {};
  const projections = model.projections || {};
  const activity = projections.activity || {};
  const intents = Array.isArray(projections.operator_intents) ? projections.operator_intents : [];
  const paired = new Set((projections.steering_episodes || []).map(episode => episode.intent_id));
  const unpaired = intents.filter(intent => !paired.has(intent.projection_id));
  const facts = Array.isArray(model.facts) ? model.facts : [];
  const heads = Array.isArray(projections.trail_heads) ? projections.trail_heads : [];
  const historicalHeads = heads.filter(head => head.status === "requested");
  const historical = Number(activity.historical_unresolved) || historicalHeads.length;
  const contextFacts = facts.filter(fact => !fact.work_item_id &&
    ["result", "decision", "observer_snapshot"].includes(fact.type));
  if(!historical && !unpaired.length && !contextFacts.length) return "";
  return `<li><b>Collapsed semantic evidence:</b> ${historical} historical unresolved request${historical === 1 ? "" : "s"}` +
    ` · ${unpaired.length} intent candidate${unpaired.length === 1 ? "" : "s"} without a supported reaction.` +
    (unpaired.length ? `<details><summary>show unpaired intent evidence</summary>` +
      unpaired.map(intent => {
        const fact = facts.find(candidate => candidate.fact_id === intent.derived_from) || {};
        return `<div><b>Operator intent:</b> ${esc(intent.summary || "Intent unavailable")}` +
          projectFactEvidence(fact) + `</div>`;
      }).join("") + `</details>` : "") +
    (historicalHeads.length ? `<details><summary>show historical request evidence</summary>` +
      historicalHeads.map(head => {
        const fact = facts.find(candidate => candidate.fact_id === head.latest_meaningful_event) || {};
        return `<div>${esc(fact.summary || "Historical request")} · requested · current state unknown` +
          projectFactEvidence(fact) + `</div>`;
      }).join("") + `</details>` : "") +
    (contextFacts.length ? `<details><summary>show ambiguous result and snapshot evidence</summary>` +
      contextFacts.map(fact => `<div><b>${fact.type === "observer_snapshot" ? "Derived snapshot" : "Result"}:</b> ` +
        `${esc(fact.summary || fact.type)}${projectFactEvidence(fact)}</div>`).join("") +
      `</details>` : "") + `</li>`;
}

function projectActivity(d, group){
  const entry = projectContextEntry(group.label);
  const model = entry && entry.data && entry.data.semantic;
  if(!model || !Array.isArray(model.facts) || !model.facts.length){
    const reading = !entry || entry.state === "loading"
      ? "Reading deterministic session evidence…"
      : (entry.state === "error" || !entry.data
        ? "Session evidence is unavailable."
        : "No meaningful exact-session event was found.");
    return `<div class="pc-empty${entry && entry.state === "error" ? " unavailable" : ""}">${reading}</div>`;
  }
  return `<div class="pc-semantic-graph" data-causal-model="explicit-relations-only">` +
    projectSemanticTimeline(d, model) + `</div>`;
}

function projectEvidenceLimits(group, focus){
  const entry = projectContextEntry(group.label);
  const sources = entry && entry.data && entry.data.sources || {};
  const gate = sources.gate || {};
  const steer = sources.steer || {};
  const observer = sources.observer || {};
  const work = sources.work || {};
  const support = work.support || {};
  return `<ul class="pc-limit-list">` +
    `<li><b>Operator note:</b> Operator note overrides derived context. It is browser-only, keyed by the exact project label, and is not durable project authority. <code>${esc(projectGoalKey(group.label))}</code></li>` +
    `<li><b>Requests:</b> Absence of an exact AskRegistry or live needs-input signal does not prove unblocked.</li>` +
    `<li><b>Meaning:</b> Intent is derived from timestamped non-meta user-role text, not verified captain authorship. A reaction is linked only when both ends have evidence; chronology alone is not causality.</li>` +
    `<li><b>Derived context:</b> The cached snapshot stays subordinate and may lag; its timestamp reports its age. Only explicit focused refresh runs model derivation. Stage and block are omitted when absent.</li>` +
    `<li><b>Work identity:</b> Dispatch builds are preparation, not proof that a worker started. Contributor argument labels remain unverified identities.</li>` +
    `<li><b>Observed sources:</b> ${Number(steer.live) || 0} steering records · ` +
    `${Number(gate.live) || 0} gate decisions · ${Number(work.live) || 0} work records · ` +
    `${Number(observer.live) || 0} derived snapshots · ${Number(support.suppressed_tool_calls) || 0} supporting tool calls suppressed. ` +
    `Status-transition history is omitted.</li>${projectSemanticEvidence(group)}${projectLifecycleEvidence(focus)}</ul>`;
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
    `<span>newest first · verified sources only</span></div>` +
    `${projectActivity(d, group, focus)}</div>` +
    `<div class="pc-other"><div class="pc-active-head"><h3>Other project sessions</h3>` +
    `<span>lightweight surrounding context</span></div>${sessions}</div>` +
    `</section>` +
    `<details class="pc-sources"><summary>Evidence / limits</summary>` +
    `${projectEvidenceLimits(group, focus)}</details>`;
}
