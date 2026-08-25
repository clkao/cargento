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
let projectGoalNote = "";
try{
  projectCockpitLabel = localStorage.getItem(PROJECT_COCKPIT_KEY) || null;
}catch(e){ /* no browser storage — choose from the payload */ }

function projectGoalKey(label){
  return PROJECT_GOAL_PREFIX + encodeURIComponent(label);
}

function projectGoal(label){
  try{ return localStorage.getItem(projectGoalKey(label)) || ""; }
  catch(e){ return ""; }
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
  let group = groups.find(item => item.label === projectCockpitLabel);
  if(!group && groups.length){
    group = groups[0];
    projectCockpitLabel = group.label;
  }
  return {groups:groups, selected:group || null};
}

function setProjectCockpit(label){
  projectCockpitLabel = String(label || "");
  projectGoalNote = "";
  try{ localStorage.setItem(PROJECT_COCKPIT_KEY, projectCockpitLabel); }
  catch(e){ /* selection still works for this page */ }
  if(lastData) render(lastData);
}

function projectCaptureDraft(){
  const field = document.getElementById("pc-goal");
  if(!field || !projectCockpitLabel) return null;
  return {
    label: projectCockpitLabel,
    value: String(field.value == null ? "" : field.value),
    focused: document.activeElement === field
  };
}

function projectRestoreFocus(draft){
  if(!draft || !draft.focused || draft.label !== projectCockpitLabel) return;
  const field = document.getElementById("pc-goal");
  if(!field || !field.focus) return;
  field.focus();
  if(field.setSelectionRange) field.setSelectionRange(field.value.length, field.value.length);
}

function projectGoalAction(act, label){
  const key = projectGoalKey(label);
  if(act === "project-reload"){
    try{ location.reload(); }catch(e){ projectGoalNote = "reload is unavailable here"; }
    return true;
  }
  if(act !== "project-goal-save" && act !== "project-goal-clear") return false;
  const field = document.getElementById("pc-goal");
  try{
    if(act === "project-goal-clear"){
      localStorage.removeItem(key);
      projectGoalNote = "browser goal cleared";
    } else {
      const value = String(field && field.value || "").trim();
      if(!value){ projectGoalNote = "write an outcome first"; }
      else {
        localStorage.setItem(key, value);
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
  return projectGoalAction(act, String(arg || ""));
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

function projectObserverSession(group){
  return group.sessions.filter(sess => sess.harness === "claude" || sess.harness === "pi")
    .sort((a, b) => (Number(b.last_activity) || 0) - (Number(a.last_activity) || 0))[0] || null;
}

/* Observer output remains session-scoped. The project page chooses the most
   recently active observable session and labels that boundary; it never folds
   one session's derived goal into the operator's project goal. */
function projectObserverSummary(group){
  const sess = projectObserverSession(group);
  if(!sess){
    return `<div class="pc-observer-empty">No Claude or Pi transcript is available for observation.</div>`;
  }
  const key = sessKey(sess);
  const entry = observerBySid[key];
  if(!entry || entry.state === "loading"){
    return `<div class="pc-observer-empty">Deriving from ${esc(key)}…</div>`;
  }
  if(entry.state === "error" || !entry.sidecar){
    return `<div class="pc-observer-empty">Observer unavailable for ${esc(key)}.</div>`;
  }
  const sidecar = entry.sidecar;
  const goal = sidecar.goal && sidecar.goal !== "no goal derived"
    ? `<div class="pc-observer-goal">${esc(sidecar.goal)}</div>`
    : `<div class="pc-observer-empty">No observer goal derived.</div>`;
  const facts = [sidecar.stage ? `stage · ${sidecar.stage}` : "",
    sidecar.block ? `open block · ${sidecar.block}` : ""].filter(Boolean);
  return goal + (facts.length
    ? `<div class="pc-observer-facts">${facts.map(f => `<span>${esc(f)}</span>`).join("")}</div>`
    : "") + `<div class="pc-observer-source">session-scoped · ${esc(key)}</div>`;
}

function projectObserveSelected(d){
  const group = projectCockpitGroup(d).selected;
  const sess = group ? projectObserverSession(group) : null;
  if(!sess) return;
  const key = sessKey(sess);
  if(!observerBySid[key]) observeSession(sess.harness, sess.sid || sess.session, key);
}

function projectWorkflowBit(sess){
  const workflows = (sess.spacedock && sess.spacedock.workflows) || [];
  const live = [];
  for(const workflow of workflows){
    for(const entity of (workflow.entities || [])){
      if(entity.live) live.push(`${sdSlug(entity.slug)} · ${entity.stage || "unknown stage"}`);
    }
  }
  return live.length ? live.join(" · ") : "";
}

/* The mirror prototype's causal-log shape, fed only with facts current 825746a
   publishes: live asks and each session's latest instruction/state. It is not a
   fabricated transcript timeline; historical decisions are named unavailable. */
function projectActivity(d, group){
  const events = [];
  for(const ask of group.asks){
    events.push({
      at: (Number(d.generated) || 0) - (Number(ask.age_sec) || 0),
      tag: "decision requested",
      title: ask.question || "Question text unavailable",
      detail: (ask.harness || "unverified") + ":" + (ask.session_id || "unverified")
    });
  }
  for(const sess of group.sessions){
    const workflow = projectWorkflowBit(sess);
    const latest = sess.last_prompt || humanTool(sess.state_detail) || "No current detail";
    events.push({
      at: Number(sess.last_activity) || 0,
      tag: sess.last_prompt ? "latest instruction" : "latest state",
      title: latest,
      detail: `${sessKey(sess)} · ${sess.state || (sess.active ? "active" : "idle")}` +
        (workflow ? ` · ${workflow}` : "")
    });
  }
  events.sort((a, b) => b.at - a.at);
  if(!events.length) return `<div class="pc-empty">No live project activity is published.</div>`;
  const rows = events.slice(0, 12).map(event => {
    const ago = event.at ? fmtDur(Math.max(0, (Number(d.generated) || 0) - event.at)) + " ago" : "time unavailable";
    return `<div class="pc-event"><span class="pc-event-node"></span><div>` +
      `<div class="pc-event-meta"><span>${esc(event.tag)}</span><time>${esc(ago)}</time></div>` +
      `<div class="pc-event-title">${esc(event.title)}</div>` +
      `<div class="pc-event-detail">${esc(event.detail)}</div></div></div>`;
  }).join("");
  return `<div class="pc-log">${rows}</div>` +
    `<div class="pc-history-boundary">Latest published state only · historical steering and gate decisions are unavailable on this API.</div>`;
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
  const chips = groups.map(item => {
    const on = item.label === group.label;
    return `<button type="button" class="pc-project${on ? " on" : ""}"` +
      ` data-calm="project-cockpit" data-arg="${esc(item.label)}" aria-pressed="${on}">` +
      `${esc(item.label)}<span>${item.sessions.length}</span></button>`;
  }).join("");
  const active = group.sessions.filter(sess => sess.active);
  const goal = draft && draft.label === group.label ? draft.value : projectGoal(group.label);
  const goalKey = projectGoalKey(group.label);
  const note = projectGoalNote ? `<span class="pc-goal-note">${esc(projectGoalNote)}</span>` : "";
  const sessions = active.length
    ? active.map(projectSessionRow).join("")
    : `<div class="pc-empty">No active sessions in this project.</div>`;
  return top + `<nav class="pc-nav" aria-label="Project being resumed">` +
    `<span class="pc-nav-k">project</span><div class="pc-projects" role="group">${chips}</div></nav>` +
    `<section class="pc-focus"><div class="pc-focus-head"><div>` +
    `<span class="pc-kicker">Working toward</span><h2>${esc(group.label)}</h2></div>` +
    `<div class="pc-counts"><span><b>${active.length}</b> active</span>` +
    `<span class="${group.asks.length ? "attention" : ""}"><b>${group.asks.length}</b> needs you</span>` +
    `</div></div><div class="pc-goal"><label for="pc-goal">` +
    `Operator goal <em>authoritative · browser only</em></label>` +
    `<textarea id="pc-goal" maxlength="500" rows="3"` +
    ` placeholder="What outcome are you working toward?">${esc(goal)}</textarea>` +
    `<div class="pc-goal-actions"><button type="button" data-calm="project-goal-save"` +
    ` data-arg="${esc(group.label)}">remember</button>` +
    `<button type="button" class="quiet" data-calm="project-reload"` +
    ` data-arg="${esc(group.label)}">reload page</button>` +
    `<button type="button" class="quiet" data-calm="project-goal-clear"` +
    ` data-arg="${esc(group.label)}">clear</button>${note}</div>` +
    `<div class="pc-key">provisional exact-label key · ${esc(goalKey)} · observer text never overwrites this field</div></div>` +
    `<div class="pc-observer"><div class="pc-subhead"><h3>Observer context</h3>` +
    `<span>derived · subordinate</span></div>${projectObserverSummary(group)}</div>` +
    `<div class="pc-columns"><div class="pc-needs"><h3>Needs you</h3>${projectAttention(d, group)}</div>` +
    `<div class="pc-active"><div class="pc-active-head"><h3>Active sessions</h3>` +
    `<span>open for session mirror</span></div>${sessions}</div></div>` +
    `<div class="pc-activity"><div class="pc-active-head"><h3>Recent activity and decisions</h3>` +
    `<span>git-log shape · live facts</span></div>${projectActivity(d, group)}</div>` +
    `</section>` +
    `<details class="pc-sources"><summary>Source and identity details</summary>` +
    `<p><b>Live:</b> sessions and asks come from this dashboard's API. Only real AskRegistry entries appear.</p>` +
    `<p><b>Derived:</b> project groups use exact display-label equality; the label is not a stable id.</p>` +
    `<p><b>Browser-owned prototype:</b> the outcome survives reload on this origin. Same-label projects collide, renames orphan it, and no observer conflict rule exists.</p>` +
    `<p><b>Unavailable:</b> verified ask-to-session attribution, ask reassignment, project-level observer synthesis, historical steering/decision events, and steering transport.</p></details>`;
}
