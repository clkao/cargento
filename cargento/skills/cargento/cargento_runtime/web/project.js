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

function projectPermalink(label, sessionKey){
  try{
    const url = new URL(location.href);
    url.searchParams.set("project", label);
    if(sessionKey) url.searchParams.set("session", sessionKey);
    else url.searchParams.delete("session");
    return url.toString();
  }catch(e){
    const params = new URLSearchParams(location.search || "");
    params.set("project", label);
    if(sessionKey) params.set("session", sessionKey);
    else params.delete("session");
    return "?" + params.toString() + (location.hash || "");
  }
}

function projectSyncUrl(label, replace){
  const target = projectPermalink(label);
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
  projectSyncUrl(projectCockpitLabel, false);
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
    projectLoadContext(lastData, true);
    return true;
  }
  if(act === "project-session-link-copy"){
    const link = projectPermalink(projectCockpitLabel, String(arg || ""));
    if(navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(link).then(() => {
        projectGoalNote = "session link copied";
        if(lastData) render(lastData);
      }).catch(() => {});
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
      if(lastData) render(lastData);
    }catch(e){ /* keep the current project */ }
  });
}

function projectSessionRow(sess){
  const key = sessKey(sess);
  const detail = humanTool(sess.state_detail) || sess.last_prompt || "No current detail";
  const state = String(sess.state || (sess.active ? "active" : "idle"));
  return `<button type="button" class="pc-session" data-calm="session" data-arg="${esc(key)}">` +
    `<span class="pc-session-state ${sess.active ? "active" : ""}"></span>` +
    `<span class="pc-session-copy"><strong>${esc(sess.title || "Untitled session")}</strong>` +
    `<span>${esc(state)} · ${esc(detail)}</span></span>` +
    `<code>${esc(key)}</code></button>`;
}

function projectSessionMirror(sess, group){
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
    `<button type="button" class="quiet" data-calm="project-session-link-copy"` +
    ` data-arg="${esc(key)}">copy session link</button></div>` +
    `<div class="pc-mirror-state"><strong>${esc(state)}</strong><span>${esc(detail)}</span></div>` +
    `<div class="pc-mirror-meta"><code>${esc(key)}</code>` +
    `<span>project · ${esc(group.label)}</span>` +
    `<span>model · ${esc(sess.model || "unavailable")}</span>` +
    `<span>subagents · ${subagents}</span></div></section>`;
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
  const entry = projectContextByLabel[group.label];
  if(!entry || entry.state === "loading"){
    return `<div class="pc-observer-empty">Reading project transcripts and entity state…</div>`;
  }
  if(entry.state === "error" || !entry.data){
    return `<div class="pc-observer-empty">Project observer source is unavailable.</div>`;
  }
  const rows = Array.isArray(entry.data.observers) ? entry.data.observers : [];
  if(!rows.length){
    return `<div class="pc-observer-empty">No selected-project session has a readable Claude or Pi transcript.</div>`;
  }
  return rows.map(sidecar => {
    const key = `${sidecar.harness}:${sidecar.sid}`;
    const goal = sidecar.goal && sidecar.goal !== "no goal derived"
      ? `<div class="pc-observer-goal">${esc(sidecar.goal)}</div>`
      : `<div class="pc-observer-empty">No observer goal derived for this session.</div>`;
    const facts = [sidecar.stage ? `stage · ${sidecar.stage}` : "",
      sidecar.block ? `open block · ${sidecar.block}` : ""].filter(Boolean);
    const model = sidecar.model || {};
    const modelLine = model.model
      ? `${model.model} · reasoning ${model.reasoning_effort || "unavailable"} · ${model.status || "unknown"}`
      : "deterministic observer fallback";
    return `<div class="pc-observer-row">${goal}` + (facts.length
      ? `<div class="pc-observer-facts">${facts.map(f => `<span>${esc(f)}</span>`).join("")}</div>`
      : "") + `<div class="pc-observer-source">derived, subordinate · ${esc(modelLine)} · ${esc(key)}</div></div>`;
  }).join("");
}

function projectLoadContext(d, refresh){
  const group = projectCockpitGroup(d).selected;
  if(!group) return;
  const old = projectContextByLabel[group.label];
  if(old && !refresh) return;
  projectContextByLabel[group.label] = {
    state: "loading", data: old && old.data || null, generated: d.generated
  };
  const query = "/api/project-context?project=" + encodeURIComponent(group.label) +
    (refresh ? "&refresh=1" : "");
  fetch(query).then(r => {
    if(!r.ok) throw new Error("bad status");
    return r.json();
  }).then(data => {
    projectContextByLabel[group.label] = {state: "ready", data: data, generated: d.generated};
    if(lastData) render(lastData);
  }).catch(() => {
    projectContextByLabel[group.label] = {state: "error", data: null, generated: d.generated};
    if(lastData) render(lastData);
  });
}

/* The mirror prototype's causal-log shape, now fed only by the selected
   project's timestamped transcript instructions and Spacedock gate records. */
function projectActivity(d, group){
  const entry = projectContextByLabel[group.label];
  if(!entry || entry.state === "loading" && !entry.data){
    return `<div class="pc-empty">Reading the gate and instruction sources…</div>`;
  }
  if(entry.state === "error" || !entry.data){
    return `<div class="pc-empty unavailable">Gate and instruction sources are unavailable.</div>`;
  }
  const events = Array.isArray(entry.data.events) ? entry.data.events : [];
  if(!events.length){
    return `<div class="pc-empty">No timestamped gate decision or captain instruction was found.</div>` +
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
  return `<div class="pc-history-boundary">` +
    `live · ${Number(gate.live) || 0} gate decisions · ${Number(steer.live) || 0} captain instructions · ` +
    `${Number(gate.untimestamped_prepare) || 0} gate preparations lack timestamps · ` +
    `status-transition history unavailable · ${missing} session transcript readers unavailable · ` +
    `${omitted} sessions omitted by the three-session bound</div>`;
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
    return `<option value="${esc(item.label)}"${on}>${esc(item.label)} · ${item.sessions.length}</option>`;
  }).join("");
  const active = group.sessions.filter(sess => sess.active);
  const focus = projectFocusSession(group);
  const goal = draft && draft.label === group.label ? draft.value : projectGoal(group.label);
  const goalKey = projectGoalKey(group.label);
  const note = projectGoalNote ? `<span class="pc-goal-note">${esc(projectGoalNote)}</span>` : "";
  const surrounding = active.filter(sess => !focus || sessKey(sess) !== sessKey(focus));
  const sessions = surrounding.length
    ? surrounding.map(projectSessionRow).join("")
    : `<div class="pc-empty">No other active sessions in this project.</div>`;
  return top + `<nav class="pc-nav" aria-label="Project being resumed">` +
    `<label class="pc-nav-k" for="pc-project-select">project</label>` +
    `<select id="pc-project-select">${options}</select>` +
    `<button type="button" class="pc-link" data-calm="project-link-copy"` +
    ` data-arg="${esc(group.label)}">copy link</button></nav>` +
    `<section class="pc-focus"><div class="pc-focus-head"><div>` +
    `<span class="pc-kicker">Working toward</span><h2>${esc(group.label)}</h2></div>` +
    `<div class="pc-counts"><span><b>${active.length}</b> active</span>` +
    `<span class="${group.asks.length ? "attention" : ""}"><b>${group.asks.length}</b> needs you</span>` +
    `</div></div><div class="pc-goal"><label for="pc-goal">` +
    `Operator goal <em>authoritative · browser only</em></label>` +
    `<textarea id="pc-goal" data-project="${esc(group.label)}" maxlength="500" rows="3"` +
    ` placeholder="What outcome are you working toward?">${esc(goal)}</textarea>` +
    `<div class="pc-goal-actions"><button type="button" data-calm="project-goal-save"` +
    ` data-arg="${esc(group.label)}">remember</button>` +
    `<button type="button" class="quiet" data-calm="project-reload"` +
    ` data-arg="${esc(group.label)}">reload page</button>` +
    `<button type="button" class="quiet" data-calm="project-goal-clear"` +
    ` data-arg="${esc(group.label)}">clear</button>${note}</div>` +
    `<div class="pc-key">provisional exact-label key · ${esc(goalKey)} · observer text never overwrites this field</div></div>` +
    `${projectSessionMirror(focus, group)}` +
    `<div class="pc-observer"><div class="pc-subhead"><h3>Observer context</h3>` +
    `<span>derived · subordinate</span><button type="button" class="quiet"` +
    ` data-calm="project-context-refresh" data-arg="${esc(group.label)}">refresh</button></div>` +
    `${projectObserverSummary(group)}</div>` +
    `<div class="pc-columns"><div class="pc-needs"><h3>Needs you</h3>${projectAttention(d, group)}</div>` +
    `<div class="pc-active"><div class="pc-active-head"><h3>Surrounding sessions</h3>` +
    `<span>lightweight project context</span></div>${sessions}</div></div>` +
    `<div class="pc-activity"><div class="pc-active-head"><h3>Gate and steering history</h3>` +
    `<span>git-log shape · timestamped sources</span></div>${projectActivity(d, group)}</div>` +
    `</section>` +
    `<details class="pc-sources"><summary>Source and identity details</summary>` +
    `<p><b>Live:</b> sessions and asks come from this dashboard's API. Only real AskRegistry entries appear.</p>` +
    `<p><b>Derived:</b> project groups, goal keys, and permalinks use exact display-label equality. The label is not a stable id.</p>` +
    `<p><b>Browser-owned goal:</b> each exact label has a separate key on this origin. Same-label projects collide, and a rename orphans the value.</p>` +
    `<p><b>Observer:</b> goals come from bounded Claude or Pi transcripts. Stages come from declared Spacedock entity state. No project-level synthesis overwrites the operator goal.</p>` +
    `<p><b>History:</b> captain instructions are timestamped transcript user messages. Gate decisions are timestamped entity frontmatter resolutions. Untimestamped prepare and status-transition history stay unavailable.</p>` +
    `<p><b>Unavailable:</b> verified ask-to-session attribution, ask reassignment, Codex transcript observation, and steering transport.</p></details>`;
}
