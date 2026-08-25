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
  const state = String(sess.state || (sess.active ? "active" : "idle"));
  return `<button type="button" class="pc-session" data-calm="project-session-focus" data-arg="${esc(key)}">` +
    `<span class="pc-session-state ${sess.active ? "active" : ""}"></span>` +
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
  const overlayNeeds = sess.state === "needs_input" || sess.needs_you === true;
  const liveNeeds = overlayNeeds || exactAsks.length > 0;
  let reading;
  if(liveNeeds){
    const reason = sess.needs_reason || (exactAsks.length
      ? `${exactAsks.length} live registered question${exactAsks.length === 1 ? "" : "s"}`
      : "live session needs-input state");
    reading = `<strong>Attention requested</strong><span>${esc(reason)}</span>`;
  }else if(!d.ask){
    reading = `<strong>Registry unavailable</strong>` +
      `<span>session overlay has no live needs-input signal</span>`;
  }else{
    reading = `<strong>No live needs-captain signal</strong>` +
      `<span>this is not proof that the session is unblocked</span>`;
  }
  return `<div class="pc-mirror-attention ${liveNeeds ? "attention" : ""}"` +
    ` data-needs-captain="${liveNeeds ? "requested" : "clear"}">` +
    `<span class="pc-kicker">Needs captain</span>${reading}` +
    `<code>session overlay + AskRegistry</code></div>`;
}

function projectSessionMirror(d, sess, group, operatorNote){
  if(!sess){
    if(!projectQuerySession) return "";
    return `<section class="pc-mirror unavailable">` +
      `<div class="pc-kicker">Focused session unavailable</div>` +
      `<p>The requested session is not present in this project's live dashboard payload.</p>` +
      `<code>${esc(projectQuerySession)}</code></section>`;
  }
  const key = sessKey(sess);
  const detail = humanTool(sess.state_detail) || sess.last_prompt || "No current detail";
  const state = String(sess.state || (sess.active ? "active" : "idle"));
  const subagents = Array.isArray(sess.subagents) ? sess.subagents.length : 0;
  return `<section class="pc-mirror" data-session-mirror="${esc(key)}">` +
    `<div class="pc-mirror-head"><div><span class="pc-kicker">Primary session mirror</span>` +
    `<h3>${esc(sess.title || "Untitled Codex session")}</h3></div>` +
    `<div class="pc-mirror-actions">${projectRefreshControl(group.label, false)}` +
    `<button type="button" class="quiet" data-calm="project-session-link-copy"` +
    ` data-arg="${esc(key)}">copy session link</button></div></div>` +
    `<div class="pc-now"><span class="pc-kicker">Right now</span>` +
    `<div class="pc-mirror-state"><strong>${esc(state)}</strong><span>${esc(detail)}</span></div>` +
    `<div class="pc-mirror-outcome"><span class="pc-kicker">Outcome remembered here</span>` +
    (operatorNote
      ? `<strong>${esc(operatorNote)}</strong><span>operator note in this browser · precedes inference</span>`
      : `<strong>Outcome unavailable</strong><span>no operator note is remembered in this browser</span>`) +
    `</div><div class="pc-mirror-purpose"><span class="pc-kicker">Observer inference</span>` +
    `${projectObserverSummary(group)}</div>` +
    projectMirrorAttention(d, sess, group) +
    projectRecentSteering(sess, group) + `</div>` +
    `<div class="pc-mirror-meta"><code>${esc(key)}</code>` +
    `<span>project · ${esc(group.label)}</span>` +
    `<span>model · ${esc(sess.model || "unavailable")}</span>` +
    `<span>${sess.harness === "codex" ? "running Codex children" : "reported subagents"} · ` +
    `${subagents}</span></div></section>`;
}

function projectAttention(d, group){
  if(!d.ask){
    return `<div class="pc-empty unavailable">Ask registry unavailable in this run.</div>`;
  }
  if(!group.asks.length){
    return `<div class="pc-empty">No session in this project is asking through Cargento.</div>`;
  }
  return `<div class="pc-ask-boundary">Live registry · project and session attribution are caller-supplied</div>` +
    group.asks.map(a => askCard(a, null, false)).join("");
}

function projectObserverSummary(group){
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
    const facts = [sidecar.stage ? `stage · ${sidecar.stage}` : "workflow stage unavailable",
      sidecar.block ? `open block · ${sidecar.block}` : "open-block reading unavailable"];
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

/* The mirror prototype's causal-log shape, now fed only by the selected
   project's timestamped transcript instructions and Spacedock gate records. */
function projectActivity(d, group){
  const entry = projectContextEntry(group.label);
  if(!entry || entry.state === "loading" && !entry.data){
    return `<div class="pc-empty">Reading the gate and instruction sources…</div>`;
  }
  if(entry.state === "error" || !entry.data){
    return `<div class="pc-empty unavailable">Gate and instruction sources are unavailable.</div>`;
  }
  const events = Array.isArray(entry.data.events) ? entry.data.events : [];
  if(!events.length){
    return `<div class="pc-empty">No timestamped gate decision or non-meta user-role message was found.</div>` +
      projectHistoryBoundary(entry.data.sources);
  }
  const rows = events.slice(0, 12).map(event => {
    const ago = event.at ? fmtDur(Math.max(0, (Number(d.generated) || 0) - event.at)) + " ago" : "time unavailable";
    return `<div class="pc-event"><span class="pc-event-node"></span><div>` +
      `<div class="pc-event-meta"><span>${esc(event.phase || event.kind)}</span><time>${esc(ago)}</time></div>` +
      `<div class="pc-event-title">${esc(event.title)}</div>` +
      `<div class="pc-event-detail">${esc(event.detail)} · ${esc(event.source)}</div></div></div>`;
  }).join("");
  return `<div class="pc-log">${rows}</div>` + projectHistoryBoundary(entry.data.sources);
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
  const surroundingNeeds = surrounding.filter(sess =>
    sess.state === "needs_input" || sess.needs_you === true);
  const surroundingWorking = surrounding.filter(sess =>
    sess.state === "working" && sess.needs_you !== true);
  const surroundingIdle = surrounding.filter(sess =>
    sess.state !== "working" && sess.state !== "needs_input" && sess.needs_you !== true);
  const sessions = surrounding.length
    ? projectSessionSection("Needs captain now", surroundingNeeds) +
      projectSessionSection("Working now", surroundingWorking) +
      projectSessionSection("Recent · idle", surroundingIdle)
    : `<div class="pc-empty">No other recent sessions in this project.</div>`;
  const workingNow = recent.filter(sess => sess.state === "working").length;
  const mirror = projectQuerySession ? projectSessionMirror(d, focus, group, goal) : "";
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
    `<span class="pc-kicker">Working toward</span><h2>${esc(group.label)}</h2></div>` +
    `<div class="pc-counts"><span><b>${workingNow}</b> working now</span>` +
    `<span><b>${recent.length}</b> recent</span>` +
    `<span class="${group.asks.length ? "attention" : ""}"><b>${group.asks.length}</b> registered asks</span>` +
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
    `<div class="pc-columns"><div class="pc-needs"><h3>Needs you</h3>${projectAttention(d, group)}</div>` +
    `<div class="pc-active"><div class="pc-active-head"><h3>Surrounding sessions</h3>` +
    `<span>lightweight project context</span></div>${sessions}</div></div>` +
    `<div class="pc-activity"><div class="pc-active-head"><h3>Gate and steering evidence</h3>` +
    `<span>git-log shape · timestamped sources</span></div>${projectActivity(d, group)}</div>` +
    `</section>` +
    `<details class="pc-sources"><summary>Source and identity details</summary>` +
    `<p><b>Live:</b> sessions and asks come from this dashboard's API. Only real AskRegistry entries appear.</p>` +
    `<p><b>Derived:</b> project groups, goal keys, and permalinks use exact display-label equality. The label is not a stable id.</p>` +
    `<p><b>Browser-owned operator note:</b> each exact label has a separate key on this origin. It precedes inference but is not durable project authority; same-label projects collide, and a rename orphans the value.</p>` +
    `<p><b>Observer:</b> goals come from bounded Claude, Codex, or Pi transcripts. Stages come from declared Spacedock entity state. No project-level synthesis overwrites the operator goal.</p>` +
    `<p><b>History:</b> known meta wrappers are excluded; remaining steering evidence is labeled only as timestamped user-role transcript messages because captain authorship is not recorded. Gate decisions are timestamped entity frontmatter resolutions. Untimestamped prepare and status-transition history stay unavailable.</p>` +
    `<p><b>Unavailable:</b> verified ask-to-session attribution, ask reassignment, and steering transport.</p></details>`;
}
