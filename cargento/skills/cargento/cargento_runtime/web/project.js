/* ── project cockpit ───────────────────────────────────────────────────────
   One operator task over the same live payload as the regular and calm views:
   choose the project being resumed, recover its browser-owned outcome, see its
   active sessions, and answer any real AskRegistry question attributed to it.

   Git-backed sessions carry a canonical repository key distinct from the
   basename shown here. Non-Git collectors retain their bounded label fallback. */
const PROJECT_COCKPIT_KEY = "cargento.projectCockpitProject";
const PROJECT_GOAL_PREFIX = "cargento.projectGoal.v1:";
const PROJECT_USAGE_KEY = "cargento.projectUsage.v1";
const PROJECT_VISIBLE_TASK_LANES = 3;
let projectCockpitLabel = null;
let projectQueryLabel = null;
let projectQuerySession = null;
let projectGoalNote = "";
let projectGoalEditingLabel = null;
const projectDraftByLabel = {};
const projectContextByLabel = {};
const projectContextRequests = {};
let projectContextRequestSequence = 0;
const projectDisclosureOpenBySession = new Map();
const projectDisclosurePendingBySession = new Set();
let projectUsageCounts = null;
let projectTabOrder = null;
let projectOpenedKey = null;
const projectTerminalBySession = {};
let projectTerminalOpenKey = null;
let projectTerminalSocket = null;
let projectTerminal = null;
let projectTerminalKey = null;
let projectTerminalSequence = 0;
let projectTerminalXtermPromise = null;
let projectTerminalReconnect = null;
let projectTerminalFollowLive = true;
let projectTerminalScrollTop = 0;
const PROJECT_XTERM_JS = "https://cdn.jsdelivr.net/npm/@xterm/xterm@6.0.0/lib/xterm.js";
const PROJECT_XTERM_CSS = "https://cdn.jsdelivr.net/npm/@xterm/xterm@6.0.0/css/xterm.css";
const PROJECT_XTERM_JS_INTEGRITY = "sha384-f/1U6Z9wM4D71a5eRXEZnyOTMOvjqxr2XLwh+Go1OvIl3L3tOcvUrzudnhbECwl4";
const PROJECT_XTERM_CSS_INTEGRITY = "sha384-n2n7twoohnW+d3myBKaUgl7DSiwidw6MkQy9oesGzkPpMjejKRR3XlnD+5yCdtBD";
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

function projectDisclosure(control, summary, body, className, attributes){
  const session = String(projectQuerySession || "");
  const key = `${session}\n${control}`;
  const open = session && projectDisclosureOpenBySession.get(key) === true ? " open" : "";
  const classes = className ? ` class="${esc(className)}"` : "";
  return `<details${classes}${open} data-pc-disclosure="${esc(control)}"` +
    ` data-disclosure-session="${esc(encodeURIComponent(session))}"${attributes || ""}>` +
    `<summary>${summary}</summary>${body}</details>`;
}

function projectDisclosureElementKey(details){
  if(!details || typeof details.getAttribute !== "function") return "";
  const encodedSession = String(details.getAttribute("data-disclosure-session") || "");
  let session = "";
  try{ session = decodeURIComponent(encodedSession); }catch(_error){ session = ""; }
  const control = String(details.getAttribute("data-pc-disclosure") || "");
  return session && control ? `${session}\n${control}` : "";
}

function projectCaptureDisclosureStates(){
  const app = document.getElementById("app");
  if(!app || typeof app.querySelectorAll !== "function") return;
  for(const details of app.querySelectorAll("details[data-pc-disclosure]")){
    const key = projectDisclosureElementKey(details);
    if(!key) continue;
    const open = details.open === true;
    /* A document click handler can synchronously render before the browser
       applies a summary's default toggle. In that one turn, the click intent
       is newer than the outgoing DOM property and must win. */
    if(projectDisclosurePendingBySession.has(key) &&
        projectDisclosureOpenBySession.get(key) !== open) continue;
    projectDisclosurePendingBySession.delete(key);
    projectDisclosureOpenBySession.set(key, open);
  }
}

document.addEventListener("click", event => {
  const summary = event.target && event.target.closest
    ? event.target.closest("summary") : null;
  const details = summary && summary.parentElement;
  if(!details || String(details.tagName || "").toLowerCase() !== "details") return;
  const key = projectDisclosureElementKey(details);
  if(!key) return;
  projectDisclosureOpenBySession.set(key, details.open !== true);
  projectDisclosurePendingBySession.add(key);
}, true);

document.addEventListener("toggle", event => {
  const details = event.target;
  const key = projectDisclosureElementKey(details);
  if(!key) return;
  projectDisclosureOpenBySession.set(key, details.open === true);
  projectDisclosurePendingBySession.delete(key);
}, true);

function projectTabId(label){
  return "pc-project-tab-" + encodeURIComponent(label).replaceAll("%", "_");
}

function projectGoal(label){
  if(Object.prototype.hasOwnProperty.call(projectDraftByLabel, label)){
    return projectDraftByLabel[label];
  }
  try{ return localStorage.getItem(projectGoalKey(label)) || ""; }
  catch(e){ return ""; }
}

function projectUsage(){
  if(projectUsageCounts) return projectUsageCounts;
  projectUsageCounts = {};
  try{
    const raw = JSON.parse(localStorage.getItem(PROJECT_USAGE_KEY) || "{}");
    if(raw && typeof raw === "object" && !Array.isArray(raw)){
      for(const [key, value] of Object.entries(raw).slice(0, 200)){
        const count = Math.floor(Number(value));
        if(key && count > 0) projectUsageCounts[key] = Math.min(count, 999999);
      }
    }
  }catch(e){ /* ordering falls back to live state and name */ }
  return projectUsageCounts;
}

function projectRecordUse(key){
  const usage = projectUsage();
  usage[key] = Math.min(999999, (Number(usage[key]) || 0) + 1);
  try{ localStorage.setItem(PROJECT_USAGE_KEY, JSON.stringify(usage)); }
  catch(e){ /* stable in-memory order still survives this page */ }
}

function projectObservedGoal(label){
  const entry = projectContextEntry(label);
  const observers = entry && entry.data && Array.isArray(entry.data.observers)
    ? entry.data.observers : [];
  const latest = observers.filter(row => row.goal && row.goal !== "no goal derived")
    .sort((a, b) => Number(b.observed_at) - Number(a.observed_at))[0];
  if(!latest) return null;
  return {text:String(latest.goal), stale:latest.snapshot_status === "cached-stale"};
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
  const ensure = (rawKey, rawName, alias) => {
    const label = String(rawKey || "Unlabeled project");
    const name = String(rawName || label).split("/").filter(Boolean).pop() || label;
    if(!groups.has(label)){
      groups.set(label, {label, name, aliases:[], sessions:[], asks:[], latest:0});
    }
    const group = groups.get(label);
    if(alias && !group.aliases.includes(String(alias))) group.aliases.push(String(alias));
    return group;
  };
  for(const sess of (d && Array.isArray(d.sessions) ? d.sessions : [])){
    const group = ensure(sess.project_key || sess.project, sess.project_name || sess.project,
      sess.project);
    group.sessions.push(sess);
    group.latest = Math.max(group.latest, Number(sess.last_activity) || 0);
  }
  if(d && d.ask && Array.isArray(d.asks)){
    for(const ask of d.asks){
      const raw = String(ask && ask.project || "Unlabeled project");
      const matched = Array.from(groups.values()).find(group => group.aliases.includes(raw));
      (matched || ensure(raw, raw, raw)).asks.push(ask);
    }
  }
  const usage = projectUsage();
  const rank = (a, b) => (Number(usage[b.label]) || 0) - (Number(usage[a.label]) || 0) ||
    Number(b.sessions.some(sess => sess.state === "working")) -
      Number(a.sessions.some(sess => sess.state === "working")) ||
    b.latest - a.latest || a.name.localeCompare(b.name) || a.label.localeCompare(b.label);
  const rows = Array.from(groups.values());
  if(!projectTabOrder && rows.length) projectTabOrder = rows.slice().sort(rank).map(row => row.label);
  if(projectTabOrder){
    const known = new Set(projectTabOrder);
    projectTabOrder.push(...rows.filter(row => !known.has(row.label)).sort(rank).map(row => row.label));
    const positions = new Map(projectTabOrder.map((key, index) => [key, index]));
    rows.sort((a, b) => positions.get(a.label) - positions.get(b.label));
  }
  return rows;
}

function projectCockpitGroup(d){
  const groups = projectGroups(d);
  const matches = (item, value) => item.label === value || item.aliases.includes(value);
  let group = groups.find(item => matches(item, projectQueryLabel));
  if(!group) group = groups.find(item => matches(item, projectCockpitLabel));
  if(!group && groups.length){
    group = groups[0];
    projectCockpitLabel = group.label;
  }
  if(group) projectCockpitLabel = group.label;
  if(group && projectOpenedKey === null){
    projectOpenedKey = group.label;
    projectRecordUse(group.label);
  }
  return {groups:groups, selected:group || null};
}

function projectFocusSession(group){
  if(!group || !projectQuerySession) return null;
  return group.sessions.find(sess => sessKey(sess) === projectQuerySession) || null;
}

function setProjectCockpit(label){
  projectCaptureDraft();
  projectTerminalOpenKey = null;
  projectTerminalDispose();
  projectCockpitLabel = String(label || "");
  projectQueryLabel = projectCockpitLabel;
  projectQuerySession = null;
  projectGoalNote = "";
  projectRecordUse(projectCockpitLabel);
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
  if(act === "project-goal-edit"){
    projectGoalEditingLabel = label;
    if(lastData) render(lastData);
    return true;
  }
  if(act !== "project-goal-save" && act !== "project-goal-clear") return false;
  const field = document.getElementById("pc-goal");
  try{
    if(act === "project-goal-clear"){
      localStorage.removeItem(key);
      delete projectDraftByLabel[label];
      projectGoalEditingLabel = null;
      projectGoalNote = "focus cleared";
    } else {
      const value = String(field && field.value || "").trim();
      if(!value){ projectGoalNote = "write a focus first"; }
      else {
        localStorage.setItem(key, value);
        projectDraftByLabel[label] = value;
        projectGoalEditingLabel = null;
        projectGoalNote = "focus saved";
      }
    }
  }catch(e){ projectGoalNote = "browser storage unavailable"; }
  if(lastData) render(lastData);
  return true;
}

function projectAction(act, arg){
  if(act === "project-terminal-open"){
    projectTerminalOpenKey = String(arg || "");
    projectTerminalDispose();
    projectTerminalFollowLive = true;
    projectTerminalScrollTop = 0;
    if(lastData) render(lastData);
    return true;
  }
  if(act === "project-terminal-close"){
    projectTerminalOpenKey = null;
    projectTerminalDispose();
    if(lastData) render(lastData);
    return true;
  }
  if(act === "project-terminal-jump"){
    projectTerminalFollowLive = true;
    projectTerminalScrollToLive();
    return true;
  }
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
    if(projectTerminalOpenKey && projectTerminalOpenKey !== projectQuerySession){
      projectTerminalOpenKey = null;
      projectTerminalDispose();
    }
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

document.addEventListener("keydown", e => {
  const field = e.target;
  if(!field || !field.getAttribute || field.getAttribute("role") !== "tab") return;
  if(!["ArrowLeft", "ArrowRight", "Home", "End"].includes(e.key)) return;
  const groups = lastData ? projectGroups(lastData) : [];
  if(!groups.length) return;
  const labels = groups.map(group => group.label);
  const current = field.getAttribute("data-arg") || projectCockpitLabel;
  const currentIndex = Math.max(0, labels.indexOf(current));
  const targetIndex = e.key === "Home" ? 0 : (e.key === "End" ? labels.length - 1 :
    (currentIndex + (e.key === "ArrowRight" ? 1 : -1) + labels.length) % labels.length);
  const target = labels[targetIndex];
  if(e.preventDefault) e.preventDefault();
  setProjectCockpit(target);
  const targetTab = document.getElementById(projectTabId(target));
  if(targetTab && targetTab.focus) targetTab.focus();
});

if(typeof window !== "undefined" && window.addEventListener){
  window.addEventListener("popstate", () => {
    try{
      const priorSession = projectQuerySession;
      projectQueryLabel = new URLSearchParams(location.search || "").get("project");
      projectQuerySession = new URLSearchParams(location.search || "").get("session");
      if(projectTerminalOpenKey && projectQuerySession !== priorSession){
        projectTerminalOpenKey = null;
        projectTerminalDispose();
      }
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

function projectExactAsks(d, sess, group){
  return d.ask && Array.isArray(group.asks)
    ? group.asks.filter(ask => String(ask && ask.harness || "") === String(sess.harness || "") &&
      String(ask && ask.session_id || "") === String(sess.sid || ""))
    : [];
}

function projectMirrorAttention(d, sess, group){
  const exactAsks = projectExactAsks(d, sess, group);
  if(exactAsks.length){
    return `<div class="pc-mirror-attention attention" data-request-state="ask">` +
      `<span class="pc-kicker">Needs you</span>` +
      exactAsks.map(ask => askCard(ask, null, false)).join("") +
      `<code>AskRegistry · exact focused session</code></div>`;
  }
  if((sess.state === "needs_input" || sess.needs_you === true) && sess.needs_reason){
    return `<div class="pc-mirror-attention attention" data-request-state="overlay">` +
      `<span class="pc-kicker">Needs you</span>` +
      `<strong>${esc(sess.needs_reason)}</strong>` +
      `<button type="button" class="quiet" data-calm="project-session-link-copy"` +
      ` data-arg="${esc(sessKey(sess))}">copy session link</button>` +
      `<code>live session overlay</code></div>`;
  }
  return "";
}

function projectDelegationLanes(sess, group){
  if(!sess) return [];
  const reported = Array.isArray(sess.subagent_hierarchy)
    ? sess.subagent_hierarchy
    : (Array.isArray(sess.subagents) ? sess.subagents.map(agent => Object.assign({
      depth: 1, parent_name: null
    }, agent)) : []);
  const entry = projectContextEntry(group.label);
  const observed = entry && entry.data && Array.isArray(entry.data.child_assignments)
    ? entry.data.child_assignments : [];
  return reported.map(agent => {
    const fallback = observed.find(row => row.observer_sid &&
      row.observer_sid === agent.observer_sid) || {};
    const entity = agent.workflow_entity || fallback.workflow_entity || "";
    const stage = agent.workflow_stage || fallback.workflow_stage || "";
    const workflowBinding = agent.workflow_binding || fallback.workflow_binding || "";
    const workItemId = agent.work_item_id || fallback.work_item_id || "";
    return {entity, stage, workflowBinding, workItemId,
      observerSid:agent.observer_sid || fallback.observer_sid || "",
      worker:agent.name || fallback.name || "Ensign",
      assignment:agent.assignment || fallback.assignment || "assignment unavailable",
      source:agent.assignment ? (agent.assignment_status || "exact parent dispatch") :
        (fallback.assignment ? `${fallback.source || "child observer snapshot"} · ${fallback.snapshot_status || "derived"}` :
          "assignment source unavailable"),
      relation:agent.parent_name ? `child of ${agent.parent_name}` : "direct child",
      depth:Math.max(1, Math.min(6, Number(agent.depth) || 1)),
      at:Number(sess.last_activity) || 0};
  });
}

function projectLastOutput(sess){
  if(!sess || sess.state !== "idle" || typeof sess.last_output !== "string") return "";
  const exact = sess.last_output;
  const compact = exact.replace(/\s+/g, " ").trim();
  if(!compact) return "";
  const preview = compact.length > 110 ? compact.slice(0, 109) + "…" : compact;
  return projectDisclosure("last-output", `Last · ${esc(preview)}`, `<pre>${esc(exact)}</pre>`,
    "pc-last-output", ` id="pc-last-output"`);
}

function projectTerminalDispose(){
  if(projectTerminalReconnect){ clearTimeout(projectTerminalReconnect); projectTerminalReconnect = null; }
  if(projectTerminalSocket){
    projectTerminalSocket.onclose = null;
    projectTerminalSocket.close();
    projectTerminalSocket = null;
  }
  if(projectTerminal){ projectTerminal.dispose(); projectTerminal = null; }
  projectTerminalKey = null;
  projectTerminalSequence = 0;
}

function projectTerminalBeforeRender(){
  if(!projectTerminal || !projectTerminalKey) return null;
  return document.getElementById("pc-terminal-screen");
}

function projectTerminalAfterRender(screen){
  if(screen && projectTerminal && projectTerminalKey === projectTerminalOpenKey){
    const replacement = document.getElementById("pc-terminal-screen");
    if(replacement && replacement !== screen) replacement.replaceWith(screen);
  }
  projectTerminalBindViewport();
}

function projectTerminalScrollMaximum(viewport){
  return Math.max(0, Number(viewport && viewport.scrollHeight || 0) -
    Number(viewport && viewport.clientHeight || 0));
}

function projectTerminalUpdateJump(){
  const jump = document.getElementById("pc-terminal-jump");
  if(jump) jump.hidden = projectTerminalFollowLive;
}

function projectTerminalScrollToLive(){
  const viewport = document.getElementById("pc-terminal-viewport");
  if(!viewport) return;
  projectTerminalFollowLive = true;
  viewport.scrollTop = projectTerminalScrollMaximum(viewport);
  projectTerminalScrollTop = viewport.scrollTop;
  projectTerminalUpdateJump();
}

function projectTerminalBindViewport(){
  const viewport = document.getElementById("pc-terminal-viewport");
  if(!viewport) return;
  viewport.onscroll = () => {
    projectTerminalScrollTop = Number(viewport.scrollTop) || 0;
    projectTerminalFollowLive = projectTerminalScrollMaximum(viewport) -
      projectTerminalScrollTop <= 2;
    projectTerminalUpdateJump();
  };
  if(projectTerminalFollowLive) projectTerminalScrollToLive();
  else {
    viewport.scrollTop = Math.min(projectTerminalScrollTop,
      projectTerminalScrollMaximum(viewport));
    projectTerminalScrollTop = viewport.scrollTop;
    projectTerminalUpdateJump();
  }
}

function projectTerminalSizeHost(terminal){
  const host = document.getElementById("pc-terminal-screen");
  const screen = terminal && terminal.element && terminal.element.querySelector
    ? terminal.element.querySelector(".xterm-screen") : null;
  if(!host || !host.style || !screen) return;
  const rect = screen.getBoundingClientRect ? screen.getBoundingClientRect() : null;
  const width = Math.ceil(Number(rect && rect.width) || parseFloat(screen.style && screen.style.width) || 0);
  const height = Math.ceil(Number(rect && rect.height) || parseFloat(screen.style && screen.style.height) || 0);
  if(width > 0) host.style.width = `${width}px`;
  if(height > 0) host.style.height = `${height}px`;
}

function projectTerminalLookup(d, sess){
  if(!sess) return;
  const key = sessKey(sess);
  const revision = Number(d.generated) || 0;
  const current = projectTerminalBySession[key];
  if(current && (current.loading || Number(current.revision) >= revision)) return;
  projectTerminalBySession[key] = current && current.state === "registered"
    ? {state:"registered", revision, data:current.data, loading:true}
    : {state:"loading", revision, loading:true};
  const path = "/api/interaction/origin?harness=" + encodeURIComponent(sess.harness) +
    "&sid=" + encodeURIComponent(sess.sid);
  fetch(path).then(response => {
    if(!response.ok) throw new Error(String(response.status));
    return response.json();
  }).then(data => {
    projectTerminalBySession[key] = data && data.state === "registered"
      ? {state:"registered", revision, data} : {state:"unavailable", revision};
    if(projectTerminalOpenKey === key && data && data.state !== "registered"){
      projectTerminalOpenKey = null;
      projectTerminalDispose();
    }
    if(lastData) render(lastData);
  }).catch(() => {
    projectTerminalBySession[key] = {state:"unavailable", revision};
    if(projectTerminalOpenKey === key){ projectTerminalOpenKey = null; projectTerminalDispose(); }
    if(lastData) render(lastData);
  });
}

function projectTerminalLoadXterm(){
  if(window.Terminal) return Promise.resolve();
  if(projectTerminalXtermPromise) return projectTerminalXtermPromise;
  projectTerminalXtermPromise = new Promise((resolve, reject) => {
    if(!document.querySelector("link[data-project-xterm]")){
      const link = document.createElement("link");
      link.dataset.projectXterm = "true";
      link.rel = "stylesheet";
      link.href = PROJECT_XTERM_CSS;
      link.integrity = PROJECT_XTERM_CSS_INTEGRITY;
      link.crossOrigin = "anonymous";
      document.head.append(link);
    }
    const script = document.createElement("script");
    script.src = PROJECT_XTERM_JS;
    script.integrity = PROJECT_XTERM_JS_INTEGRITY;
    script.crossOrigin = "anonymous";
    script.onload = resolve;
    script.onerror = () => reject(new Error("xterm unavailable"));
    document.head.append(script);
  });
  return projectTerminalXtermPromise;
}

function projectTerminalConnect(key, originHint, terminal){
  if(projectTerminalOpenKey !== key || projectTerminalKey !== key || projectTerminal !== terminal ||
      projectTerminalSocket) return;
  const scheme = location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${scheme}://${location.host}/api/interaction/stream`);
  projectTerminalSocket = socket;
  projectTerminalSequence = 0;
  socket.onmessage = event => {
    if(projectTerminalSocket !== socket || projectTerminal !== terminal) return;
    const frame = JSON.parse(event.data);
    if(frame.state !== "streamed"){
      terminal.writeln(`\r\n[${frame.state}: ${frame.reason}]`);
      return;
    }
    if(originHint && frame.origin_id_hint !== originHint){ socket.close(); return; }
    const chunks = Array.isArray(frame.chunks) && frame.chunks.length ? frame.chunks : [frame];
    let resetPending = !!frame.reset;
    chunks.forEach(chunk => {
      const sequence = Number(chunk.sequence);
      if(!Number.isInteger(sequence) || sequence <= projectTerminalSequence) return;
      const cols = Number(chunk.cols);
      const rows = Number(chunk.rows);
      if(!Number.isInteger(cols) || cols < 1 || !Number.isInteger(rows) || rows < 1) return;
      if(terminal.cols !== cols || terminal.rows !== rows){
        terminal.resize(cols, rows);
        projectTerminalSizeHost(terminal);
      }
      if(resetPending){ terminal.reset(); resetPending = false; }
      if(chunk.data){
        terminal.write(chunk.data, () => {
          if(projectTerminalSocket === socket && projectTerminal === terminal &&
              projectTerminalFollowLive) projectTerminalScrollToLive();
        });
      } else if(projectTerminalFollowLive){ projectTerminalScrollToLive(); }
      projectTerminalSequence = sequence;
    });
  };
  socket.onclose = event => {
    if(projectTerminalSocket !== socket) return;
    projectTerminalSocket = null;
    if(event.code !== 1008 && projectTerminalOpenKey === key){
      projectTerminalReconnect = setTimeout(() => {
        projectTerminalReconnect = null;
        projectTerminalConnect(key, originHint, terminal);
      }, 1000);
    }
  };
}

function projectTerminalMount(key, originHint){
  const screen = document.getElementById("pc-terminal-screen");
  if(!screen || projectTerminalOpenKey !== key) return;
  if(projectTerminal && projectTerminalKey === key) return;
  if(projectTerminal) projectTerminalDispose();
  projectTerminalLoadXterm().then(() => {
    if(!document.getElementById("pc-terminal-screen") || projectTerminalOpenKey !== key) return;
    if(projectTerminal && projectTerminalKey === key) return;
    const terminal = new window.Terminal({disableStdin:true, cursorBlink:false,
      scrollback:500, fontSize:12, fontFamily:"'SFMono-Regular', Consolas, monospace",
      theme:{background:"#11141a", foreground:"#dbe5ee", cursor:"#11141a"}});
    projectTerminal = terminal;
    projectTerminalKey = key;
    terminal.open(document.getElementById("pc-terminal-screen"));
    projectTerminalBindViewport();
    projectTerminalConnect(key, originHint, terminal);
  }).catch(() => { screen.textContent = "Terminal renderer unavailable."; });
}

function projectTerminalSurface(sess){
  if(!sess){
    if(projectTerminalOpenKey){ projectTerminalOpenKey = null; projectTerminalDispose(); }
    return "";
  }
  const key = sessKey(sess);
  const entry = projectTerminalBySession[key];
  if(!entry || entry.state !== "registered") return "";
  if(projectTerminalOpenKey !== key){
    return `<button type="button" class="pc-terminal-open" data-calm="project-terminal-open"` +
      ` data-arg="${esc(key)}">Open terminal</button>`;
  }
  const data = entry.data || {};
  const origin = data.origin || {};
  const title = `${origin.session_name || "tmux"}:${origin.window_index || "?"}.` +
    `${origin.pane_index || "?"}`;
  if(!projectTerminal || projectTerminalKey !== key){
    setTimeout(() => projectTerminalMount(key, data.origin_id_hint || ""), 0);
  }
  return `<aside class="pc-terminal" aria-label="Read-only terminal output">` +
    `<div class="pc-terminal-bar"><strong>${esc(title)}</strong><span>read-only</span>` +
    `<button type="button" id="pc-terminal-jump" class="quiet"` +
    ` data-calm="project-terminal-jump" data-arg="${esc(key)}"` +
    `${projectTerminalFollowLive ? " hidden" : ""}>Jump to live</button>` +
    `<button type="button" class="quiet" data-calm="project-terminal-close"` +
    ` data-arg="${esc(key)}">Close</button></div>` +
    `<div id="pc-terminal-viewport" class="pc-terminal-viewport">` +
    `<div id="pc-terminal-screen" class="pc-terminal-screen"></div></div></aside>`;
}

function projectSessionMirror(d, sess, group){
  if(!sess){
    if(!projectQuerySession) return "";
    return `<section class="pc-operator unavailable">` +
      `<div class="pc-operator-line"><strong>Unavailable</strong>` +
      `<span>Focused session state unknown</span></div>` + projectDisclosure(
        "session-metadata", "session", `<code>${esc(projectQuerySession)}</code>`
      ) + `</section>`;
  }
  projectTerminalLookup(d, sess);
  const key = sessKey(sess);
  const hierarchy = Array.isArray(sess.subagent_hierarchy) ? sess.subagent_hierarchy :
    (Array.isArray(sess.subagents) ? sess.subagents : []);
  const childCount = hierarchy.length;
  const exactAsks = projectExactAsks(d, sess, group);
  const request = exactAsks.length ? String(exactAsks[0].question || "").trim() :
    ((sess.state === "needs_input" || sess.needs_you === true) ?
      String(sess.needs_reason || "").trim() : "");
  const needs = !!request;
  const working = sess.state === "working";
  const state = needs ? "Needs you" : (working ? "Working" : "Waiting for you");
  const taskCount = Math.max(1, childCount);
  const detail = needs ? request : (working ?
    `${taskCount} ${taskCount === 1 ? "task" : "tasks"} active` : "");
  const activityAt = Number(sess.last_activity) || 0;
  const age = activityAt && Number(d.generated)
    ? Math.max(0, Number(d.generated) - activityAt) : null;
  const freshness = age === null ? "" : (age < 1 ? "Updated now" : `Updated ${fmtDur(age)} ago`);
  return `<section class="pc-operator" data-session-mirror="${esc(key)}"` +
    ` data-operator-state="${esc(state.toLowerCase().replace(/ /g, "-"))}">` +
    `<div class="pc-operator-line"><strong>${esc(state)}</strong>` +
    (detail ? `<span>${esc(detail)}</span>` : "") +
    (freshness ? `<span class="pc-operator-updated">${esc(freshness)}</span>` : "") + `</div>` +
    projectLastOutput(sess) + projectDisclosure("session-metadata", "session",
    `<div class="pc-operator-detail">` +
    `<strong>${esc(sess.title || "Untitled Codex session")}</strong><code>${esc(key)}</code>` +
    (sess.model ? `<span>model · ${esc(sess.model)}</span>` : "") +
    `<div class="pc-operator-actions">${projectRefreshControl(group.label, false)}` +
    `<button type="button" class="quiet" data-calm="project-session-link-copy"` +
    ` data-arg="${esc(key)}">copy session link</button></div>` +
    projectMirrorAttention(d, sess, group) + `</div>`) + `</section>`;
}

function projectLoadContext(d, refresh, announce){
  const group = projectCockpitGroup(d).selected;
  if(!group) return;
  const cacheKey = projectContextKey(group.label);
  const old = projectContextByLabel[cacheKey];
  const revision = Number(d && d.generated) || 0;
  const active = projectContextRequests[cacheKey];
  /* One exact-scope read may run at a time. Keep only the newest dashboard
     revision behind it so a busy stream cannot manufacture a fetch backlog. */
  if(active){
    if(revision > active.revision){
      active.pending = {data:d, revision, announce:active.announce || !!announce};
    }
    return;
  }
  const settledRevision = Number(old && (old.dashboard_revision || old.generated)) || 0;
  if(old && !refresh && settledRevision >= revision) return;
  const requestId = ++projectContextRequestSequence;
  const announceResult = announce === undefined ? !!refresh : !!announce;
  projectContextRequests[cacheKey] = {
    id: requestId, revision, pending: null, announce: announceResult
  };
  projectContextByLabel[cacheKey] = {
    state: "loading", data: old && old.data || null,
    generated: old && old.generated || revision, dashboard_revision: settledRevision
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
    const current = projectContextRequests[cacheKey];
    if(!current || current.id !== requestId) return;
    delete projectContextRequests[cacheKey];
    /* Its context predates a dashboard revision already rendered. Preserve the
       last settled graph until the coalesced read catches up. */
    if(current.pending && current.pending.revision > revision){
      projectLoadContext(current.pending.data, false,
        current.announce || current.pending.announce);
      return;
    }
    projectContextByLabel[cacheKey] = {
      state: "ready", data: data, generated: revision, dashboard_revision: revision
    };
    if(current.announce) projectGoalNote = "context refreshed";
    if(lastData) render(lastData);
  }).catch(() => {
    const current = projectContextRequests[cacheKey];
    if(!current || current.id !== requestId) return;
    delete projectContextRequests[cacheKey];
    if(current.pending && current.pending.revision > revision){
      projectLoadContext(current.pending.data, false,
        current.announce || current.pending.announce);
      return;
    }
    projectContextByLabel[cacheKey] = {
      state: "error", data: old && old.data || null,
      generated: old && old.generated || revision, dashboard_revision: revision
    };
    if(current.announce) projectGoalNote = "context refresh failed";
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
    `they do not enter the primary graph.</li>`;
}

function projectFactEvidence(fact, scope){
  const evidence = fact.evidence || {};
  const iso = Number(fact.at) ? new Date(Number(fact.at) * 1000).toISOString() : "";
  const body = `<div>` +
    `${esc(evidence.source || "source unavailable")}` +
    (evidence.confidence ? ` · ${esc(evidence.confidence)}` : "") +
    (iso ? ` · <time datetime="${esc(iso)}">${esc(iso)}</time>` : "") +
    `</div>`;
  return projectDisclosure(`fact:${scope || "event"}:${fact.fact_id || "unknown"}`,
    "evidence", body, "pc-event-evidence");
}

function projectDelegationWorkItem(model, row){
  const items = Array.isArray(model.work_items) ? model.work_items : [];
  if(row.workItemId && items.some(item => item.work_item_id === row.workItemId) &&
      !String(row.source || "").includes("derived")) return row.workItemId;
  if(!row.workflowBinding || !row.entity) return "";
  const binding = `${row.workflowBinding}:${row.entity}`;
  const item = items.find(candidate => (candidate.source_bindings || []).some(source =>
    source && source.value === binding));
  if(item) return item.work_item_id;
  const events = model.history && Array.isArray(model.history.events) ? model.history.events : [];
  const assignment = events.find(event => event.event_type === "assignment" && row.observerSid &&
    event.source_identity === `codex:${row.observerSid}`);
  return assignment && assignment.work_binding || "";
}

function projectDirectionTokens(summary){
  const ignored = new Set(["a", "again", "an", "can", "could", "i", "let", "please",
    "the", "this", "us", "we", "would", "you"]);
  return (String(summary || "").toLowerCase().match(/[a-z0-9]+/g) || [])
    .filter(token => !ignored.has(token));
}

function projectMeaningfulDirections(intents, factById){
  const lowSignal = /^(?:ok(?:ay)?|alright|thanks?|working|oh\b.*\b(?:see|got it))\W*$/i;
  const transport = /^(?:env\b|pwd\b|ls\b|cd\b|git\s|\/[A-Za-z0-9_.-]|[A-Za-z0-9_.-]+\/)/i;
  const selected = [];
  const clusters = [];
  intents.slice().sort((a, b) => Number(b.at) - Number(a.at)).forEach(intent => {
    const summary = String(intent.summary || "").trim();
    const fact = factById.get(intent.derived_from);
    if(!fact || summary.length < 4 || lowSignal.test(summary) || transport.test(summary)) return;
    const tokens = projectDirectionTokens(summary);
    if(!tokens.length) return;
    const at = Number(intent.at) || Number(fact.at) || 0;
    const duplicate = clusters.some(cluster => cluster.at - at <= 15 * 60 &&
      tokens[0] === cluster.tokens[0] &&
      new Set(tokens.filter(token => cluster.tokens.includes(token))).size /
        Math.min(new Set(tokens).size, new Set(cluster.tokens).size) >= .8);
    if(duplicate) return;
    clusters.push({at, tokens});
    selected.push(fact);
  });
  return selected;
}

function projectLaneRegistry(model, delegations, focus){
  const projections = model.projections || {};
  const facts = Array.isArray(model.facts) ? model.facts : [];
  const items = Array.isArray(model.work_items) ? model.work_items : [];
  const heads = Array.isArray(projections.trail_heads) ? projections.trail_heads : [];
  const activity = projections.activity || {};
  const episodes = Array.isArray(projections.steering_episodes)
    ? projections.steering_episodes : [];
  const intents = Array.isArray(projections.operator_intents)
    ? projections.operator_intents : [];
  const focusedKey = focus ? sessKey(focus) : (projectQuerySession || "focused");
  const foKey = `fo:${focusedKey}`;
  const itemById = new Map(items.map(item => [item.work_item_id, item]));
  const factById = new Map(facts.map(fact => [fact.fact_id, fact]));
  const headByItem = new Map(heads.map(head => [head.work_item_id, head]));
  const projectedDirections = intents.concat(Array.isArray(activity.steering)
    ? activity.steering : []);
  const projectedFactIds = new Set(projectedDirections.map(intent => intent.derived_from));
  facts.filter(fact => fact.type === "user_message" && !projectedFactIds.has(fact.fact_id))
    .forEach(fact => projectedDirections.push({projection_id:`intent:${fact.fact_id}`,
      derived_from:fact.fact_id, at:fact.at, summary:fact.summary}));
  const intentFactById = new Map(projectedDirections.map(intent =>
    [intent.projection_id, intent.derived_from]));
  const meaningfulDirections = projectMeaningfulDirections(projectedDirections, factById);
  const contributorByTask = new Map();
  const unboundContributors = [];
  delegations.forEach(row => {
    const workItemId = projectDelegationWorkItem(model, row);
    if(!workItemId){ unboundContributors.push(row); return; }
    if(!contributorByTask.has(workItemId)) contributorByTask.set(workItemId, []);
    contributorByTask.get(workItemId).push(row);
  });
  const relevance = new Map();
  const addTask = (workItemId, at, priority) => {
    const item = itemById.get(workItemId);
    if(!workItemId || !item || item.kind === "session_result") return;
    const prior = relevance.get(workItemId) || {priority:0, at:0};
    relevance.set(workItemId, {priority:Math.max(Number(priority) || 0, prior.priority),
      at:Math.max(Number(at) || 0, prior.at)});
  };
  contributorByTask.forEach((rows, workItemId) =>
    addTask(workItemId, Math.max(...rows.map(row => Number(row.at) || 0)), 3));
  let nodes = Array.isArray(activity.nodes) ? activity.nodes : [];
  if(!nodes.length && !Object.prototype.hasOwnProperty.call(activity, "nodes")){
    nodes = heads.filter(head => ["prepared", "outcome", "decision"].includes(head.status))
      .map(head => ({at:(facts.find(fact => fact.fact_id === head.latest_meaningful_event) || {}).at,
        work_item_ids:[head.work_item_id]}));
  }
  nodes.concat(Array.isArray(activity.history_nodes) ? activity.history_nodes : [])
    .forEach(node => (node.work_item_ids || []).forEach(id =>
      addTask(id, node.at, node.kind === "burst" ? 1 : 2)));
  const taskIds = [...relevance].sort((a, b) => b[1].priority - a[1].priority ||
      b[1].at - a[1].at || a[0].localeCompare(b[0]))
    .slice(0, PROJECT_VISIBLE_TASK_LANES).map(entry => entry[0]);
  const foEvents = facts.filter(fact => {
    const item = itemById.get(fact.work_item_id);
    if(["final_output", "result"].includes(fact.type) &&
        focus && focus.state === "working") return false;
    return item && item.kind === "session_result" ||
      (!fact.work_item_id && fact.type === "user_message") ||
      ["final_output", "observer_snapshot", "goal_shift"].includes(fact.type);
  }).sort((a, b) => Number(a.type === "observer_snapshot") - Number(b.type === "observer_snapshot") ||
    Number(b.at) - Number(a.at));
  const episodeByFact = new Map(episodes.map(episode =>
    [intentFactById.get(episode.intent_id), episode]).filter(entry => entry[0]));
  const foLane = {key:foKey, kind:"fo", label:"First Officer", index:0, events:foEvents,
    directions:meaningfulDirections, contributors:unboundContributors, item:null, head:null,
    branch:"none", merge:"none", episodeByFact, factById};
  const relations = Array.isArray(model.relations) ? model.relations : [];
  const relationEdge = relation => String(relation.confidence || "").includes("derived")
    ? "derived" : "solid";
  const topologyForTask = workItemId => {
    const taskKey = `task:${workItemId}`;
    const supported = relation => !String(relation.confidence || "").includes("derived");
    const branchRelations = relations.filter(relation => relation.type === "dispatches_to" &&
      relation.from === foKey && relation.to === taskKey);
    const mergeRelations = relations.filter(relation => relation.type === "returns_to" &&
      relation.from === taskKey && relation.to === foKey);
    const branches = branchRelations.filter(supported);
    const merges = mergeRelations.filter(supported);
    const strongest = selected => selected.some(relation => relationEdge(relation) === "solid")
      ? "solid" : (selected.length ? "derived" : "none");
    const relationAt = relation => Number((factById.get(relation.evidence_ref) || {}).at) || 0;
    const latestDispatchAt = Math.max(0, ...branches.map(relationAt));
    const taskResults = facts.filter(fact => fact.work_item_id === workItemId &&
      ["work_result", "result"].includes(fact.type) && fact.evidence &&
      fact.evidence.confidence === "exact");
    const latestReturnAt = Math.max(0, ...merges.map(relationAt),
      ...taskResults.map(fact => Number(fact.at) || 0));
    const retryEvidence = relations.some(relation =>
      ["retries", "retry_of", "failed_attempt"].includes(relation.type) &&
      supported(relation) && (relation.from === taskKey || relation.to === taskKey)) ||
      facts.some(fact => fact.work_item_id === workItemId &&
        ["retry", "failed_attempt"].includes(fact.source_kind) && fact.evidence &&
        fact.evidence.confidence === "exact");
    return {branch:strongest(branchRelations), merge:strongest(mergeRelations),
      dispatchCount:branches.length, latestDispatchAt, latestReturnAt, retryEvidence};
  };
  const taskLanes = taskIds.map(workItemId => {
    const taskEvents = facts.filter(fact => fact.work_item_id === workItemId)
      .sort((a, b) => Number(b.at) - Number(a.at));
    const contributors = (contributorByTask.get(workItemId) || [])
      .sort((a, b) => String(a.worker).localeCompare(String(b.worker)));
    const topology = topologyForTask(workItemId);
    const head = headByItem.get(workItemId) || null;
    const working = contributors.length > 0 || taskEvents.some(fact =>
      fact.current_state === true && fact.evidence && fact.evidence.confidence === "exact");
    const unreturned = topology.dispatchCount > 0 &&
      topology.latestDispatchAt > topology.latestReturnAt;
    const returned = topology.latestReturnAt > 0 && !unreturned;
    const current = working || unreturned;
    return {key:`task:${workItemId}`, kind:"task", workItemId,
      label:(itemById.get(workItemId) || {}).label || "Task",
      events:taskEvents, contributors, item:itemById.get(workItemId) || {},
      head, headFact:head && factById.get(head.latest_meaningful_event) || null,
      current, working, unreturned, returned, dispatchCount:topology.dispatchCount,
      retryEvidence:topology.retryEvidence,
      branch:topology.branch, merge:topology.merge};
  });
  const lanes = [foLane].concat(taskLanes);
  lanes.forEach((lane, index) => { lane.index = index; });
  return {foKey, lanes, laneByKey:new Map(lanes.map(lane => [lane.key, lane])),
    unboundContributors, omittedTaskCount:Math.max(0, relevance.size - taskLanes.length)};
}

function projectLaneRails(registry, activeLane, kind, tip, hasEvent){
  return registry.lanes.map(lane => `<span class="pc-rail-cell${lane.key === activeLane.key ? " active" : ""}"` +
    ` data-rail-key="${esc(lane.key)}">` +
    (hasEvent && lane.key === activeLane.key ? `<span class="pc-graph-mark ${esc(kind)}"` +
      (tip ? ` title="${esc(tip)}"` : "") + `></span>` : "") + `</span>`).join("");
}

function projectGraphRow(d, at, kind, registry, lane, body, attributes, tip, connectsNext){
  const age = at ? fmtDur(Math.max(0, Number(d.generated) - Number(at))) + " ago" : "";
  const style = `--lane-count:${registry.lanes.length};--lane-index:${lane.index}`;
  return `<article class="pc-graph-row ${esc(kind)}" data-graph-node="${esc(kind)}"` +
    ` data-lane-key="${esc(lane.key)}" style="${style}"` +
    (connectsNext ? ` data-lane-connect="next"` : "") +
    (attributes ? ` ${attributes}` : "") + `>` +
    `<time>${esc(age)}</time><span class="pc-graph-rail">` +
    projectLaneRails(registry, lane, kind, tip, Boolean(at)) +
    `</span><div class="pc-trail-body">${body}</div></article>`;
}

function projectLaneHistory(lane, excludedFactId){
  const events = lane.events.filter(fact => fact.fact_id !== excludedFactId);
  if(!events.length) return "";
  const summary = `${events.length} sourced event${events.length === 1 ? "" : "s"}`;
  const body = `<div class="pc-event-chain" data-lane-key="${esc(lane.key)}">` + events.map((fact, index) => {
    const prefix = fact.type === "user_message" ? "Operator intent" :
      (fact.type === "observer_snapshot" ? "Derived snapshot" : "");
    return `<div class="pc-trail-event" data-semantic-event="${esc(fact.type || "event")}"` +
      (index < events.length - 1 ? ` data-lane-connect="next"` : "") + `>` +
      `<span class="pc-trail-event-node"></span><div>` +
      (prefix ? `<strong>${prefix}:</strong> ` : "") + `<span>${esc(fact.summary || fact.type)}</span>` +
      projectFactEvidence(fact, `lane-history:${lane.key}`) + `</div></div>`;
  }).join("") + `</div>`;
  return projectDisclosure(`lane-history:${lane.key}`, summary, body, "pc-trail-history");
}

function projectFoContext(lane){
  const events = lane.events.filter(fact =>
    !["user_message", "observer_snapshot"].includes(fact.type));
  if(!events.length) return "";
  const contextLane = Object.assign({}, lane, {events});
  return projectLaneHistory(contextLane, "");
}

function projectFoLaneRows(d, registry, lane, focus){
  const contributors = lane.contributors.length ? projectDisclosure("fo-contributors",
    `${lane.contributors.length} unbound contributor${lane.contributors.length === 1 ? "" : "s"}`,
    lane.contributors.map((row, index) => `<div class="pc-trail-event">` +
      `<strong>${esc(row.assignment)}</strong><span>${esc(row.worker)}</span>` +
      projectDisclosure(`fo-contributor:${row.observerSid || row.worker || index}`, "evidence",
        `<div>${esc(row.source)}</div>`, "pc-event-evidence") + `</div>`).join(""),
    "pc-trail-history pc-fo-context") : "";
  const renderDirection = (direction, index, connectsNext) => {
    const episode = lane.episodeByFact.get(direction.fact_id);
    const reaction = episode && lane.factById.get(episode.adaptation_fact);
    const edge = episode && String(episode.confidence || "").includes("derived")
      ? "derived" : (episode ? "solid" : "none");
    const body = `<div class="pc-trail-top"><strong class="pc-lane-title">First Officer</strong>` +
      `<span>Direction</span></div><div class="pc-trail-result">${esc(direction.summary)}</div>` +
      (reaction ? `<div class="pc-trail-quiet">${esc(reaction.summary || "Linked reaction")}</div>` : "") +
      projectFactEvidence(direction, `fo-direction:${direction.fact_id}`) +
      (index === 0 ? `${projectFoContext(lane)}${contributors}` : "");
    return projectGraphRow(d, direction.at, "steering", registry, lane, body,
      `data-semantic-kind="direction" data-steering-state="${episode ? "paired" : "unpaired"}"` +
      ` data-causal-edge="${edge}"`, direction.summary, connectsNext);
  };
  if(!lane.directions.length){
    const finalOutput = focus && focus.state !== "working"
      ? lane.events.find(fact => ["final_output", "result"].includes(fact.type)) : null;
    const observedGoal = lane.events.find(fact => fact.type === "observer_snapshot") || null;
    const event = finalOutput;
    if(!event && !observedGoal && !contributors) return "";
    const kind = finalOutput ? "Result" : (observedGoal ? "Observed goal" : "Context");
    const body = `<div class="pc-trail-top"><strong class="pc-lane-title">First Officer</strong>` +
      `<span>${esc(kind)}</span></div>` +
      (event ? `<div class="pc-trail-result">${esc(event.summary)}</div>` : "") +
      (event ? projectFactEvidence(event, `fo-${kind.toLowerCase().replace(/ /g, "-")}`) :
        (observedGoal ? projectFactEvidence(observedGoal, "fo-observed-goal") : "")) +
      contributors;
    return projectGraphRow(d, event && event.at, "event", registry, lane, body,
      `data-semantic-kind="${finalOutput ? "result" : (observedGoal ? "observed_goal" : "context")}"` +
      ` data-trail-head="fo"`, event && event.summary || "Focused session");
  }
  const directDirections = lane.directions.slice(0, 4);
  const earlierDirections = lane.directions.slice(4);
  const direct = directDirections.map((direction, index) =>
    renderDirection(direction, index, index < directDirections.length - 1)).join("");
  const earlierRows = earlierDirections.map((direction, index) =>
    renderDirection(direction, index + 4, index < earlierDirections.length - 1)).join("");
  const earlier = earlierDirections.length ? projectDisclosure("earlier-directions",
    `${earlierDirections.length} earlier direction${earlierDirections.length === 1 ? "" : "s"}`,
    `<div class="pc-direction-scroll">${earlierRows}</div>`,
    "pc-direction-history") : "";
  return direct + earlier;
}

function projectTaskTitle(label){
  return String(label || "Task").replace(/-/g, " ")
    .replace(/^./, first => first.toUpperCase());
}

function projectTaskLaneRow(d, registry, lane){
  const head = lane.head || {};
  const latest = lane.headFact || lane.events[0] || {};
  const stage = lane.working ? head.stage || "" : "";
  const title = projectTaskTitle(lane.label);
  const status = lane.working ? "Working" : (lane.unreturned
    ? "No active worker · no return observed" : (lane.returned ? "Returned" : "History"));
  const result = latest.summary || "Latest state";
  const dispatchCount = Number(lane.dispatchCount) || 0;
  const retryCount = Math.max(0, dispatchCount - 1);
  const attempts = dispatchCount === 1 ? "1 dispatch" : dispatchCount > 1
    ? `${dispatchCount} dispatches` + (lane.retryEvidence
      ? ` · ${retryCount} ${retryCount === 1 ? "retry" : "retries"}` : "") : "";
  const workers = lane.contributors.map(row => row.worker).filter(Boolean).join(" · ");
  const semanticKind = lane.returned ? "result" :
    (["decision", "gate_decision"].includes(latest.type) ? "decision" :
      (["prepared_dispatch", "assignment", "work_birth"].includes(latest.type)
        ? "dispatch" : "progress"));
  const bindings = Array.isArray(lane.item.source_bindings) && lane.item.source_bindings.length
    ? lane.item.source_bindings : (latest.workflow_binding ? [{source:"task state",
      value:`${latest.workflow_binding}:${latest.workflow_entity || ""}`}] : []);
  const source = bindings.length ? projectDisclosure(`task-source:${lane.workItemId}`, "source",
    bindings.map(binding => {
      const workflow = String(binding.value || "").split(":")[0].split("/").filter(Boolean).pop();
      return `${esc(binding.source)}${workflow ? ` · workflow ${esc(workflow)}` : ""}` +
        ` · <code>${esc(binding.value)}</code>`;
    }).join("<br>"), "pc-trail-history") : "";
  const workflowBinding = latest.workflow_binding || (bindings[0] &&
    String(bindings[0].value || "").split(":")[0]) || "";
  const meta = [status, stage].filter(Boolean).join(" · ");
  const body = `<div class="pc-trail-top"><strong class="pc-lane-title">${esc(title)}</strong>` +
    `<span>${esc(meta)}</span></div>` +
    `<div class="pc-trail-result">${esc(result)}</div>` +
    (attempts ? `<div class="pc-trail-quiet" data-dispatch-count="${dispatchCount}">${esc(attempts)}</div>` : "") +
    (workers ? `<div class="pc-trail-quiet">${esc(workers)}</div>` : "") +
    projectFactEvidence(latest, `task-head:${lane.key}`) +
    projectLaneHistory(lane, latest.fact_id) + source;
  const at = Number(latest.at) || 0;
  const hasPriorEvent = lane.events.some(fact => fact.fact_id !== latest.fact_id);
  const attrs = `data-assignment-lane="task-head" data-work-item="${esc(lane.workItemId)}"` +
    ` data-semantic-kind="${esc(semanticKind)}"` +
    ` data-trail-head="${esc(head.status || "latest")}"` +
    ` data-task-current="${lane.current ? "true" : "false"}"` +
    ` data-branch-edge="${esc(lane.branch)}" data-merge-edge="${esc(lane.merge)}"` +
    (stage ? ` data-work-stage="${esc(stage)}"` : "") +
    (workflowBinding ? ` data-workflow-binding="${esc(workflowBinding)}"` : "");
  return projectGraphRow(d, at, "event", registry, lane, body, attrs, title, hasPriorEvent);
}

function projectLaneLegend(registry){
  return `<div class="pc-lane-legend" style="--lane-count:${registry.lanes.length}">` +
    `<span></span><span class="pc-lane-labels">` + registry.lanes.map(lane =>
      `<span title="${esc(lane.label)}">${esc(lane.kind === "fo" ? "First Officer" :
        projectTaskTitle(lane.label))}</span>`).join("") +
    `</span></div>`;
}

function projectHistorySpan(events){
  const times = events.map(event => Number(event.at)).filter(value => value > 0);
  if(times.length < 2) return "one observed moment";
  const seconds = Math.max(...times) - Math.min(...times);
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if(hours) return `${hours}h${minutes ? ` ${minutes}m` : ""} observed span`;
  if(minutes) return `${minutes}m observed span`;
  return `${Math.max(1, Math.floor(seconds))}s observed span`;
}

function projectSemanticTimeline(d, model, workflowLanes, focus){
  const registry = projectLaneRegistry(model, workflowLanes, focus);
  const foLane = registry.lanes.find(lane => lane.kind === "fo");
  const taskRows = registry.lanes.filter(lane => lane.kind === "task").map(lane => ({lane,
    at:Number(lane.headFact && lane.headFact.at) || Number(lane.events[0] && lane.events[0].at) || 0,
    html:projectTaskLaneRow(d, registry, lane)}));
  const currentRows = taskRows.filter(row => row.lane.current)
    .sort((a, b) => b.at - a.at);
  const historyRows = taskRows.filter(row => !row.lane.current)
    .sort((a, b) => b.at - a.at);
  const fo = foLane ? projectFoLaneRows(d, registry, foLane, focus) : "";
  const omitted = registry.omittedTaskCount ? projectDisclosure("folded-task-lanes",
    `${registry.omittedTaskCount} task lane${registry.omittedTaskCount === 1 ? "" : "s"} folded`,
    "Older task evidence remains under Evidence / limits.", "pc-semantic-overflow") : "";
  const current = `<section class="pc-activity-band" data-activity-band="current">` +
    `<h4>Current</h4>${fo}${currentRows.map(row => row.html).join("")}</section>`;
  const history = historyRows.length ? projectDisclosure("past-work",
    `Past work · ${historyRows.length}`, historyRows.map(row => row.html).join(""),
    "pc-history-band", ` data-activity-band="past-work"`) : "";
  return `<section class="pc-semantic-timeline" data-order="newest-first" data-model="fact-projection"` +
    ` data-graph-layout="fo-task-lanes">${projectLaneLegend(registry)}${current}${history}` +
    omitted + `</section>`;
}
function projectSemanticEvidence(group){
  const entry = projectContextEntry(group.label);
  const model = entry && entry.data && entry.data.semantic || {};
  const history = model.history || {};
  const projections = model.projections || {};
  const activity = projections.activity || {};
  const intents = Array.isArray(projections.operator_intents) ? projections.operator_intents : [];
  const paired = new Set((projections.steering_episodes || []).map(episode => episode.intent_id));
  const unpaired = intents.filter(intent => !paired.has(intent.projection_id));
  const facts = Array.isArray(model.facts) ? model.facts : [];
  const heads = Array.isArray(projections.trail_heads) ? projections.trail_heads : [];
  const currentWork = new Set((activity.nodes || []).flatMap(node => node.work_item_ids || []));
  const historicalHeads = heads.filter(head => head.status === "requested" &&
    !currentWork.has(head.work_item_id));
  const historical = Number(activity.historical_unresolved) || historicalHeads.length;
  const historicalDispatches = Number(activity.historical_dispatches) || historicalHeads.length;
  const contextFacts = facts.filter(fact => !fact.work_item_id &&
    ["result", "decision"].includes(fact.type));
  const historyCount = Number(history.event_count) || 0;
  const historyEvents = Array.isArray(history.events) ? history.events : [];
  const eventTypeLabels = new Map([
    ["operator_direction", ["direction", "directions"]],
    ["assignment", ["assignment", "assignments"]],
    ["stage_transition", ["stage", "stages"]],
    ["progress_head", ["progress", "progress"]],
    ["checkpoint", ["checkpoint", "checkpoints"]],
    ["gate_decision", ["gate", "gates"]],
    ["result", ["result", "results"]],
    ["final_output", ["final output", "final outputs"]],
    ["observed_goal", ["observed goal", "observed goals"]],
    ["goal_shift", ["goal shift", "goal shifts"]]
  ]);
  const eventTypeCounts = new Map();
  historyEvents.forEach(event => eventTypeCounts.set(event.event_type,
    (eventTypeCounts.get(event.event_type) || 0) + 1));
  const knownInventory = [...eventTypeLabels].filter(([type]) => eventTypeCounts.has(type))
    .map(([type, labels]) => {
      const count = eventTypeCounts.get(type);
      return `${count} ${labels[count === 1 ? 0 : 1]}`;
    });
  const unknownInventory = [...eventTypeCounts].filter(([type]) => !eventTypeLabels.has(type))
    .map(([type, count]) => `${count} ${String(type).replace(/_/g, " ")}`);
  const retainedInventory = knownInventory.concat(unknownInventory).join(" · ");
  const primaryHeads = Array.isArray(activity.history_nodes) ? activity.history_nodes.length : 0;
  const primaryDirections = Array.isArray(activity.steering) ? activity.steering.length : 0;
  const absentTypes = [["returns_to", "task returns"], ["checkpoint", "checkpoints"],
    ["progress_head", "progress"]].filter(([type]) => type === "returns_to"
      ? !(model.relations || []).some(relation => relation.type === type)
      : !eventTypeCounts.has(type)).map(([, label]) => label);
  const gateUnavailable = entry && entry.data && entry.data.sources &&
    entry.data.sources.gate && entry.data.sources.gate.status_history === "unavailable";
  const workItems = new Map((model.work_items || []).map(item => [item.work_item_id, item]));
  const historyLanes = new Map();
  historyEvents.forEach(event => {
    const key = event.work_binding || "fo";
    if(!historyLanes.has(key)) historyLanes.set(key, []);
    historyLanes.get(key).push(event);
  });
  const historySpan = projectHistorySpan(historyEvents);
  const inventory = historyCount ? `<div class="pc-history-inventory">` +
    `<span><b>Retained</b> · ${esc(retainedInventory || "no semantic events")}</span>` +
    `<span><b>Primary</b> · ${primaryHeads} heads · ${primaryDirections} directions</span>` +
    (absentTypes.length ? `<span><b>Absent</b> · ${esc(absentTypes.join(" · "))}</span>` : "") +
    (gateUnavailable ? `<span><b>Unavailable</b> · gate history</span>` : "") + `</div>` : "";
  const historyDisclosure = historyLanes.size ? projectDisclosure("semantic-source-history",
    `${historyCount} source event${historyCount === 1 ? "" : "s"} · ${historySpan}`,
    [...historyLanes].map(([key, events]) => {
      const item = workItems.get(key) || {};
      const label = key === "fo" || item.kind === "session_result" ? "FO" : item.label || "Task";
      return `<div class="pc-history-lane" data-history-lane="${esc(key === "fo" ? "fo" : `task:${key}`)}">` +
        `<b>${esc(label)}</b>` + events.map(event => {
          const fact = facts.find(candidate => candidate.fact_id === event.source_ref) || {};
          return `<div>${esc(event.summary || event.event_type)}` +
            projectFactEvidence(fact, `source-history:${key}`) + `</div>`;
        }).join("") + `</div>`;
    }).join("")) : "";
  if(!historical && !unpaired.length && !contextFacts.length && !historyCount) return "";
  return (historyCount ? `<li><b>Semantic work history · ${historyCount} source event` +
    `${historyCount === 1 ? "" : "s"}</b> · ${historySpan} · 24h retention · ` +
    `${history.persisted ? "restart-safe" : "memory only"} · raw sources remain authoritative.` +
    `${inventory}${historyDisclosure}</li>` : "") +
    `<li><b>Past dispatches without observed result · ${historicalDispatches}</b>` +
    (historical !== historicalDispatches ? ` · ${historical} distinct work label${historical === 1 ? "" : "s"}` : "") +
    ` · ${unpaired.length} intent candidate${unpaired.length === 1 ? "" : "s"} without a supported reaction.` +
    (unpaired.length ? projectDisclosure("unpaired-intents", "show unpaired intent evidence",
      unpaired.map(intent => {
        const fact = facts.find(candidate => candidate.fact_id === intent.derived_from) || {};
        return `<div><b>Operator intent:</b> ${esc(intent.summary || "Intent unavailable")}` +
          projectFactEvidence(fact, "unpaired-intent") + `</div>`;
      }).join("")) : "") +
    (historicalHeads.length ? projectDisclosure("historical-requests",
      "show historical request evidence", historicalHeads.map(head => {
        const fact = facts.find(candidate => candidate.fact_id === head.latest_meaningful_event) || {};
        return `<div>${esc(fact.summary || "Historical request")} · requested · current state unknown` +
          projectFactEvidence(fact, "historical-request") + `</div>`;
      }).join("")) : "") +
    (contextFacts.length ? projectDisclosure("ambiguous-results",
      "show ambiguous result and snapshot evidence",
      contextFacts.map(fact => `<div><b>${fact.type === "observer_snapshot" ? "Derived snapshot" : "Result"}:</b> ` +
        `${esc(fact.summary || fact.type)}${projectFactEvidence(fact, "ambiguous-result")}</div>`).join("")) : "") + `</li>`;
}

function projectGoalBlock(group, goal, note){
  const observed = projectObservedGoal(group.label);
  const editing = projectGoalEditingLabel === group.label;
  const editor = editing ? `<div class="pc-goal-editor"><textarea id="pc-goal"` +
    ` data-project="${esc(group.label)}" maxlength="500" rows="3"` +
    ` placeholder="Project focus">${esc(goal)}</textarea>` +
    `<div class="pc-goal-actions"><button type="button" data-calm="project-goal-save"` +
    ` data-arg="${esc(group.label)}">save</button>` +
    `<button type="button" class="quiet" data-calm="project-goal-clear"` +
    ` data-arg="${esc(group.label)}">clear</button></div></div>` : "";
  const focus = goal ? `<div class="pc-goal-line"><span><b>Focus</b> — ${esc(goal)}</span>` +
    `<button type="button" class="quiet" data-calm="project-goal-edit"` +
    ` data-arg="${esc(group.label)}">edit</button></div>` :
    (!editing ? `<button type="button" class="pc-focus-add" data-calm="project-goal-edit"` +
      ` data-arg="${esc(group.label)}">add focus</button>` : "");
  const observedLine = observed ? `<div class="pc-goal-observed"><b>Observed goal` +
    `${observed.stale ? " · stale" : ""}</b> — ${esc(observed.text)}</div>` : "";
  return `<div class="pc-goal">${focus}${observedLine}${editor}${note}</div>`;
}

function projectActivity(d, group, focus){
  const entry = projectContextEntry(group.label);
  const model = entry && entry.data && entry.data.semantic;
  const workflowLanes = projectDelegationLanes(focus, group);
  if((!model || !Array.isArray(model.facts) || !model.facts.length) && !workflowLanes.length){
    const reading = !entry || entry.state === "loading"
      ? "Reading deterministic session evidence…"
      : (entry.state === "error" || !entry.data
        ? "Session evidence is unavailable."
        : "No meaningful exact-session event was found.");
    return `<div class="pc-empty${entry && entry.state === "error" ? " unavailable" : ""}">${reading}</div>`;
  }
  const semantic = model || {facts: [], work_items: [], projections: {}};
  return `<div class="pc-semantic-graph" data-causal-model="explicit-relations-only">` +
    projectSemanticTimeline(d, semantic, workflowLanes, focus) + `</div>`;
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
    `<li><b>Focus:</b> Browser focus is operator-authored, keyed by the stable local project key, and is not durable project authority. <code>${esc(projectGoalKey(group.label))}</code></li>` +
    `<li><b>Requests:</b> Absence of an exact AskRegistry or live needs-input signal does not prove unblocked.</li>` +
    `<li><b>Meaning:</b> Intent is derived from timestamped non-meta user-role text, not verified captain authorship. A reaction is linked only when both ends have evidence; chronology alone is not causality.</li>` +
    `<li><b>Derived context:</b> The cached snapshot stays subordinate and may lag; its timestamp reports its age. Only explicit focused refresh runs model derivation. Stage and block are omitted when absent.</li>` +
    `<li><b>Work identity:</b> Dispatch builds are preparation, not proof that a worker started. Contributor argument labels remain unverified identities.</li>` +
    `<li><b>Observed sources:</b> ${Number(steer.live) || 0} steering records · ` +
    `${Number(gate.live) || 0} gate decisions · ${Number(work.live) || 0} work records · ` +
    `${Number(observer.live) || 0} derived snapshots · ${Number(support.suppressed_tool_calls) || 0} supporting tool calls suppressed. ` +
    `Lifecycle-only transitions stay hidden.</li>${projectSemanticEvidence(group)}${projectLifecycleEvidence(focus)}</ul>`;
}

function projectView(d, draft){
  const model = projectCockpitGroup(d);
  const groups = model.groups;
  const group = model.selected;
  const updated = new Date(d.generated * 1000).toLocaleTimeString();
  const top = `<div class="pc-top"><div><div class="brand">Cargento</div>` +
    `<div class="sub"><span id="live-status">updated ${esc(updated)}</span></div></div>` +
    `<span class="pc-mode-note">project cockpit · live dashboard data</span></div>`;
  if(!group){
    return top + `<div class="pc-nav"><span class="pc-nav-k">project</span></div>` +
      `<div class="pc-empty">No project-labelled sessions are available.</div>`;
  }
  const tabs = groups.map(item => {
    const selected = item.label === group.label;
    const working = item.sessions.some(sess => sess.state === "working");
    return `<button type="button" id="${esc(projectTabId(item.label))}" class="pc-project-tab` +
      `${selected ? " selected" : ""}" role="tab" aria-selected="${selected}"` +
      ` tabindex="${selected ? "0" : "-1"}" data-calm="project-cockpit"` +
      ` data-arg="${esc(item.label)}" title="${esc(item.aliases[0] || item.name)}">` +
      `<span class="pc-project-dot${working ? " working" : ""}"` +
      ` aria-label="${working ? "working now" : "no demonstrated work now"}"></span>` +
      `<span>${esc(item.name)}</span></button>`;
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
    : "";
  const workingNow = recent.filter(sess => sess.state === "working").length;
  const mirror = projectQuerySession ? projectSessionMirror(d, focus, group) : "";
  const terminal = projectQuerySession ? projectTerminalSurface(focus) : "";
  const workspace = mirror ? `<div class="pc-session-workspace${terminal ? " terminal-open" : ""}">` +
    `<div class="pc-session-primary">${mirror}</div>${terminal}</div>` : "";
  return top + `<nav class="pc-nav" aria-label="Projects">` +
    `<div class="pc-project-tabs" role="tablist" aria-label="Projects">${tabs}</div>` +
    `<button type="button" class="pc-link" data-calm="project-link-copy"` +
    ` data-arg="${esc(group.label)}">copy link</button></nav>` +
    `<section class="pc-focus"><div class="pc-focus-head"><div>` +
    `<span class="pc-kicker">Project context</span><h2>${esc(group.name)}</h2></div>` +
    `<div class="pc-counts">` +
    (projectQuerySession ? "" : `<span><b>${workingNow}</b> working now</span>`) +
    `<span><b>${recent.length}</b> recent</span>` +
    `</div></div>${projectGoalBlock(group, goal, note)}` +
    `${workspace}` +
    `<div class="pc-activity"><div class="pc-active-head"><h3>Work & steering</h3>` +
    `<span>newest first</span></div>` +
    `${projectActivity(d, group, focus)}</div>` +
    (sessions ? `<div class="pc-other"><div class="pc-active-head"><h3>Other project sessions</h3>` +
      `<span>surrounding context</span></div>${sessions}</div>` : "") +
    `</section>` +
    projectDisclosure("evidence-limits", "Evidence / limits",
      projectEvidenceLimits(group, focus), "pc-sources");
}
