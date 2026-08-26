/* ── project cockpit ───────────────────────────────────────────────────────
   One operator task over the same live payload as the regular and calm views:
   choose the project being resumed, recover its browser-owned outcome, see its
   active sessions, and answer any real AskRegistry question attributed to it.

   Git-backed sessions carry a canonical repository key distinct from the
   basename shown here. Non-Git collectors retain their bounded label fallback. */
const PROJECT_COCKPIT_KEY = "cargento.projectCockpitProject";
const PROJECT_GOAL_PREFIX = "cargento.projectGoal.v1:";
const PROJECT_USAGE_KEY = "cargento.projectUsage.v1";
const PROJECT_VISIBLE_ACTIVITY_NODES = 5;
const PROJECT_VISIBLE_STEERING_NODES = 3;
let projectCockpitLabel = null;
let projectQueryLabel = null;
let projectQuerySession = null;
let projectGoalNote = "";
let projectGoalEditingLabel = null;
const projectDraftByLabel = {};
const projectContextByLabel = {};
const projectContextRequests = {};
let projectContextRequestSequence = 0;
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
    if(lastData) render(lastData);
    return true;
  }
  if(act === "project-terminal-close"){
    projectTerminalOpenKey = null;
    projectTerminalDispose();
    if(lastData) render(lastData);
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
    return {entity, stage, workflowBinding,
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
  return `<details class="pc-last-output"><summary>Last · ${esc(preview)}</summary>` +
    `<pre>${esc(exact)}</pre></details>`;
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
  if(!screen || !projectTerminal || projectTerminalKey !== projectTerminalOpenKey) return;
  const replacement = document.getElementById("pc-terminal-screen");
  if(replacement && replacement !== screen) replacement.replaceWith(screen);
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
      if(terminal.cols !== cols || terminal.rows !== rows) terminal.resize(cols, rows);
      if(resetPending){ terminal.reset(); resetPending = false; }
      if(chunk.data) terminal.write(chunk.data);
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
    `<button type="button" class="quiet" data-calm="project-terminal-close"` +
    ` data-arg="${esc(key)}">Close</button></div>` +
    `<div id="pc-terminal-screen" class="pc-terminal-screen"></div></aside>`;
}

function projectSessionMirror(d, sess, group){
  if(!sess){
    if(!projectQuerySession) return "";
    return `<section class="pc-operator unavailable">` +
      `<div class="pc-operator-line"><strong>Unavailable</strong>` +
      `<span>Focused session state unknown</span></div>` +
      `<details><summary>session</summary><code>${esc(projectQuerySession)}</code></details></section>`;
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
    projectLastOutput(sess) +
    `<details><summary>session</summary><div class="pc-operator-detail">` +
    `<strong>${esc(sess.title || "Untitled Codex session")}</strong><code>${esc(key)}</code>` +
    (sess.model ? `<span>model · ${esc(sess.model)}</span>` : "") +
    `<div class="pc-operator-actions">${projectRefreshControl(group.label, false)}` +
    `<button type="button" class="quiet" data-calm="project-session-link-copy"` +
    ` data-arg="${esc(key)}">copy session link</button></div>` +
    projectMirrorAttention(d, sess, group) + `</div></details></section>`;
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

function projectFactEvidence(fact){
  const evidence = fact.evidence || {};
  const iso = Number(fact.at) ? new Date(Number(fact.at) * 1000).toISOString() : "";
  return `<details class="pc-event-evidence"><summary>evidence</summary><div>` +
    `${esc(evidence.source || "source unavailable")}` +
    (evidence.confidence ? ` · ${esc(evidence.confidence)}` : "") +
    (iso ? ` · <time datetime="${esc(iso)}">${esc(iso)}</time>` : "") +
    `</div></details>`;
}

function projectGraphRow(d, at, kind, lane, body, attributes, tip){
  const age = at ? fmtDur(Math.max(0, Number(d.generated) - Number(at))) + " ago" : "";
  return `<article class="pc-graph-row ${esc(kind)}" data-graph-node="${esc(kind)}"` +
    (attributes ? ` ${attributes}` : "") + `>` +
    `<time>${esc(age)}</time><span class="pc-graph-rail lane-${Number(lane) || 0}">` +
    `<span class="pc-graph-mark ${esc(kind)}"${tip ? ` title="${esc(tip)}"` : ""}></span>` +
    `</span><div class="pc-trail-body">${body}</div></article>`;
}

function projectTrailRow(d, head, model, node, lane){
  const facts = Array.isArray(model.facts) ? model.facts : [];
  const items = Array.isArray(model.work_items) ? model.work_items : [];
  const item = items.find(candidate => candidate.work_item_id === head.work_item_id) || {};
  const latest = facts.find(fact => fact.fact_id === head.latest_meaningful_event) || {};
  const history = facts.filter(fact => fact.work_item_id === head.work_item_id)
    .sort((a, b) => Number(b.at) - Number(a.at));
  const status = head.status === "requested"
    ? "recently dispatched · current state not confirmed" : head.status;
  const kind = item.kind === "workflow_item" ? "stage" :
    (head.status === "outcome" || head.status === "decision" ? "result" : "work");
  const retries = Number(node && node.retry_count) || 0;
  const body = `<div class="pc-trail-top"><strong>${esc(item.label || latest.summary || "Work item")}</strong>` +
    `<span>${esc(status)}</span></div>` +
    `<div class="pc-trail-result">${esc(latest.summary || "Latest state")}` +
    (retries ? ` <span class="pc-trail-quiet">· ${retries} earlier retr${retries === 1 ? "y" : "ies"} folded</span>` : "") +
    `</div>` +
    `<details class="pc-trail-history"><summary>${history.length} sourced event${history.length === 1 ? "" : "s"}</summary>` +
    history.map(fact => `<div class="pc-trail-event"><span>${esc(fact.summary || fact.type)}</span>` +
      projectFactEvidence(fact) + `</div>`).join("") + `</details>`;
  return projectGraphRow(d, latest.at, kind, lane, body,
    `data-trail-head="${esc(head.status || "latest")}"`, latest.summary || item.label);
}

function projectEpisodeRow(d, episode, model){
  const facts = Array.isArray(model.facts) ? model.facts : [];
  const intent = (model.projections.operator_intents || []).find(candidate =>
    candidate.projection_id === episode.intent_id) || {};
  const adaptation = facts.find(candidate => candidate.fact_id === episode.adaptation_fact) || {};
  const action = adaptation.summary || "Demonstrated reaction";
  const intentText = intent.summary || "Operator intent unavailable";
  const confidence = String(episode.confidence || "supported");
  const edge = ["exact", "structural"].includes(confidence) ? "solid" :
    (confidence.includes("derived") ? "derived" : "supported");
  const body = `<div class="pc-trail-top"><strong>${esc(action)}</strong><span>steering response</span></div>` +
    `<details class="pc-trail-history"><summary>source-linked correction · ${esc(episode.confidence || "supported")}</summary>` +
    `<div class="pc-trail-event">Operator intent: ${esc(intentText)}</div></details>` +
    projectFactEvidence(adaptation);
  return projectGraphRow(d, adaptation.at, "steering paired", 1, body,
    `data-steering-state="paired" data-causal-edge="${esc(edge)}"`,
    `${intentText} → ${action}`);
}

function projectSteeringRow(d, intent, model){
  const summary = intent.summary || "Operator direction";
  const body = `<div class="pc-trail-top"><strong>${esc(summary)}</strong></div>`;
  return projectGraphRow(d, intent.at, "steering unpaired", 1, body,
    `data-steering-state="unpaired" data-causal-edge="none"`, summary);
}

function projectBurstRow(d, node, model, lane){
  const facts = Array.isArray(model.facts) ? model.facts : [];
  const items = Array.isArray(model.work_items) ? model.work_items : [];
  const ids = Array.isArray(node.work_item_ids) ? node.work_item_ids : [];
  const rows = ids.map(id => {
    const item = items.find(candidate => candidate.work_item_id === id) || {};
    const itemFacts = facts.filter(fact => fact.work_item_id === id)
      .sort((a, b) => Number(b.at) - Number(a.at));
    const latest = itemFacts[0] || {};
    return `<div class="pc-trail-event"><strong>${esc(item.label || "Work item")}</strong>` +
      `<span>${esc(latest.summary || "Source event unavailable")}</span></div>`;
  }).join("");
  const count = Number(node.count) || ids.length;
  const body = `<div class="pc-trail-top"><strong>${count} entities touched</strong>` +
    `<span>dispatch burst</span></div><details class="pc-trail-history"><summary>show sourced work items</summary>` +
    rows + `</details>`;
  return projectGraphRow(d, node.at, "burst", lane, body,
    `data-semantic-burst="${ids.length}"`, `${count} entities touched`);
}

function projectWorkflowLaneRow(d, row, lane){
  const title = String(row.entity || "").replace(/-/g, " ").replace(/^./, first => first.toUpperCase());
  const workflow = title && row.stage;
  const heading = workflow ? `${title} · ${row.stage}` : row.assignment;
  const status = workflow ? "current stage" : "current assignment";
  const kind = workflow ? "stage" : "work";
  const body = `<div class="pc-trail-top"><strong>${esc(heading)}</strong>` +
    `<span>${status}</span></div>` +
    (workflow ? `<div class="pc-trail-result">${esc(row.assignment)}</div>` : "") +
    `<div class="pc-trail-quiet">${esc(row.worker)}` +
    (row.relation === "direct child" ? "" : ` · ${esc(row.relation)}`) + `</div>` +
    `<details class="pc-trail-history"><summary>source</summary>${esc(row.source)}` +
    (row.workflowBinding ? ` · workflow ${esc(String(row.workflowBinding).split("/").filter(Boolean).pop() || row.workflowBinding)}` +
      `<code>${esc(row.workflowBinding)}</code>` : "") + `</details>`;
  return projectGraphRow(d, row.at, kind, lane, body,
    `data-assignment-lane="current" data-subagent-depth="${row.depth}"` +
      (workflow ? ` data-work-item="${esc(row.entity)}" data-work-stage="${esc(row.stage)}"` +
        ` data-workflow-binding="${esc(row.workflowBinding)}"` : ""),
    heading);
}

function projectSemanticTimeline(d, model, workflowLanes){
  const projections = model.projections || {};
  const facts = Array.isArray(model.facts) ? model.facts : [];
  const heads = Array.isArray(projections.trail_heads) ? projections.trail_heads : [];
  const episodes = Array.isArray(projections.steering_episodes)
    ? projections.steering_episodes : [];
  const activity = projections.activity || {};
  const liveObserverSources = new Set(workflowLanes.filter(row => row.observerSid)
    .map(row => `codex:${row.observerSid}`));
  const historyEvents = model.history && Array.isArray(model.history.events)
    ? model.history.events : [];
  const liveAssignmentBindings = new Set(historyEvents.filter(event =>
    event.event_type === "assignment" && liveObserverSources.has(event.source_identity))
    .map(event => event.work_binding));
  const items = Array.isArray(model.work_items) ? model.work_items : [];
  const pairedIntents = new Set(episodes.map(episode => episode.intent_id));
  const intentPool = Array.isArray(activity.steering) ? activity.steering :
    (Array.isArray(projections.operator_intents) ? projections.operator_intents.slice(-3).reverse() : []);
  const steering = intentPool.filter(intent => !pairedIntents.has(intent.projection_id))
    .sort((a, b) => Number(b.at) - Number(a.at))
    .slice(0, PROJECT_VISIBLE_STEERING_NODES);
  let nodes = Array.isArray(activity.nodes) ? activity.nodes : [];
  const historyNodes = Array.isArray(activity.history_nodes) ? activity.history_nodes : [];
  if(!nodes.length && !Object.prototype.hasOwnProperty.call(activity, "nodes")){
    nodes = heads.filter(head => ["prepared", "outcome", "decision"].includes(head.status))
      .slice(0, PROJECT_VISIBLE_ACTIVITY_NODES).map(head => {
      const fact = facts.find(candidate => candidate.fact_id === head.latest_meaningful_event) || {};
      return {kind:"work", at:fact.at, status:head.status,
        work_item_ids:[head.work_item_id], latest_event:head.latest_meaningful_event};
    });
  }
  const visibleEventIds = new Set(nodes.map(node => node.latest_event));
  nodes = nodes.concat(historyNodes.filter(node => !visibleEventIds.has(node.latest_event))
    .slice(0, Math.max(0, PROJECT_VISIBLE_ACTIVITY_NODES - nodes.length)));
  const headByItem = new Map(heads.map(head => [head.work_item_id, head]));
  const activityRows = nodes.filter(node => {
    const ids = node.work_item_ids || [];
    const representedByLiveLane = ids.length && ids.every(id => liveAssignmentBindings.has(id));
    return !representedByLiveLane;
  }).map((node, index) => {
    const lane = index % 3;
    if(node.kind === "burst") return {at:Number(node.at), html:projectBurstRow(d, node, model, lane)};
    const firstId = Array.isArray(node.work_item_ids) ? node.work_item_ids[0] : "";
    const head = headByItem.get(firstId) || {work_item_id:firstId, status:node.status,
      latest_meaningful_event:node.latest_event};
    return {at:Number(node.at), html:projectTrailRow(d, head, model, node, lane)};
  });
  const episodeRows = episodes.map(episode => {
    const fact = facts.find(candidate => candidate.fact_id === episode.adaptation_fact) || {};
    return {at:Number(fact.at), html:projectEpisodeRow(d, episode, model)};
  });
  const steeringRows = steering.map(intent => ({
    at:Number(intent.at), html:projectSteeringRow(d, intent, model)
  }));
  const workflowRows = workflowLanes.map((row, index) => ({
    at:Number(row.at), html:projectWorkflowLaneRow(d, row, index % 3)
  }));
  const visible = workflowRows.concat(activityRows, episodeRows, steeringRows)
    .sort((a, b) => b.at - a.at);
  if(!visible.length) return `<div class="pc-empty">No source-backed current work or reaction.</div>`;
  return `<section class="pc-semantic-timeline" data-order="newest-first" data-model="fact-projection"` +
    ` data-graph-layout="time-spine-work-lanes">` +
    visible.map(row => row.html).join("") + `</section>`;
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
    ["result", "decision", "observer_snapshot"].includes(fact.type));
  const historyCount = Number(history.event_count) || 0;
  if(!historical && !unpaired.length && !contextFacts.length && !historyCount) return "";
  return (historyCount ? `<li><b>Semantic work history · ${historyCount}</b> · ` +
    `${history.persisted ? "restart-safe" : "memory only"} · raw sources remain authoritative.</li>` : "") +
    `<li><b>Past dispatches without observed result · ${historicalDispatches}</b>` +
    (historical !== historicalDispatches ? ` · ${historical} distinct work label${historical === 1 ? "" : "s"}` : "") +
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
    projectSemanticTimeline(d, semantic, workflowLanes) + `</div>`;
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
    `<details class="pc-sources"><summary>Evidence / limits</summary>` +
    `${projectEvidenceLimits(group, focus)}</details>`;
}
