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
    return top + `<div class="pc-intro"><span class="pc-step">Your next decision</span>` +
      `<h1>Which project are you working toward?</h1></div>` +
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
  return top + `<section class="pc-intro"><span class="pc-step">Your next decision</span>` +
    `<h1>Which project are you working toward?</h1>` +
    `<p>Choose one label, recover its outcome, then open the active session that needs you.</p>` +
    `<div class="pc-projects" role="group" aria-label="Project being resumed">${chips}</div></section>` +
    `<section class="pc-focus"><div class="pc-focus-head"><div>` +
    `<span class="pc-kicker">Working toward</span><h2>${esc(group.label)}</h2></div>` +
    `<div class="pc-counts"><span><b>${active.length}</b> active</span>` +
    `<span class="${group.asks.length ? "attention" : ""}"><b>${group.asks.length}</b> needs you</span>` +
    `</div></div><div class="pc-columns"><div class="pc-goal"><label for="pc-goal">` +
    `Remembered outcome <em>browser only</em></label>` +
    `<textarea id="pc-goal" maxlength="500" rows="3"` +
    ` placeholder="What outcome should you recover on reload?">${esc(goal)}</textarea>` +
    `<div class="pc-goal-actions"><button type="button" data-calm="project-goal-save"` +
    ` data-arg="${esc(group.label)}">remember</button>` +
    `<button type="button" class="quiet" data-calm="project-reload"` +
    ` data-arg="${esc(group.label)}">reload page</button>` +
    `<button type="button" class="quiet" data-calm="project-goal-clear"` +
    ` data-arg="${esc(group.label)}">clear</button>${note}</div>` +
    `<div class="pc-key">provisional exact-label key · ${esc(goalKey)}</div></div>` +
    `<div class="pc-needs"><h3>Needs you</h3>${projectAttention(d, group)}</div></div>` +
    `<div class="pc-active"><div class="pc-active-head"><h3>Active sessions</h3>` +
    `<span>identity: (harness, sid)</span></div>${sessions}</div></section>` +
    `<details class="pc-sources"><summary>Source and identity details</summary>` +
    `<p><b>Live:</b> sessions and asks come from this dashboard's API. Only real AskRegistry entries appear.</p>` +
    `<p><b>Derived:</b> project groups use exact display-label equality; the label is not a stable id.</p>` +
    `<p><b>Browser-owned prototype:</b> the outcome survives reload on this origin. Same-label projects collide, renames orphan it, and no observer conflict rule exists.</p>` +
    `<p><b>Unavailable:</b> verified ask-to-session attribution, ask reassignment, project-level observer synthesis, and steering.</p></details>`;
}
