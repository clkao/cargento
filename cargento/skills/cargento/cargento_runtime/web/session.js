/* ── session mode ────────────────────────────────────────────────────────────
   A third display of the same /api/data payload both overviews already consume:
   one session's dispatch tree. No new endpoint, no new collector — the
   `spacedock.workflows` array is already published per session by
   collectors/claude.py → session_spacedock. The view renders each workflow as a
   vertical tree of stage-colored entity nodes along the workflow's ordered
   `stages` spine, with live workers (`live: true`) highlighted, and a one-line
   goal header above the tree when the workflow frontmatter carries a `title`
   scalar (published as `workflow.goal`). When no `title` is present, no goal
   line renders — the view shows the tree alone, never a fabricated objective.

   The session target is routable via the URL hash (`#session=<harness>:<sid>`),
   set by mode.js's hash sync. This lets the view be navigated to directly and
   shared. Distinct empty states cover the four cases a session view can land
   in: loading (session not found in the current data), not-a-Spacedock-session
   (spacedock null), first-officer with no in-flight entities (freshness gate),
   and ensign/worker sessions. */

/* The session picker: rendered when session mode is entered with no target
   session (null key). Each row is a `data-calm="session"` control so the
   existing click channel selects it without a second handler. */
function sessionPicker(d){
  const sessions = (d && d.sessions) || [];
  if(!sessions.length){
    return `<div class="sv-empty">No sessions to view. Switch to regular or calm to see the board.</div>`;
  }
  const rows = sessions.map(s => {
    const key = sessKey(s);
    const title = s.title || s.last_prompt || s.project;
    return `<div class="sv-pick" data-calm="session" data-arg="${esc(key)}" role="button">` +
      badge(s.harness, s.active) +
      `<span class="sv-pick-title">${esc(title)}</span>` +
      `<span class="sv-pick-meta">${esc(s.project)} · ${esc(s.session)}</span></div>`;
  }).join("");
  return `<div class="sv-picker"><div class="sv-picker-h">Select a session to view its dispatch tree</div>${rows}</div>`;
}

function sessionBackBar(){
  return `<div class="sv-back-bar">` +
    `<button type="button" class="sv-back" data-calm="mode" data-arg="regular">← overview</button>` +
    `</div>`;
}

/* The session card: the shared card anatomy from `sessionCardCore`, wrapped
   for the session view without board-only elements (no Working pill, no lead
   pill, no sparkline, no consumption, no subagents, no sdBlock, no taskBlock).
   Reuses the board's `.card` CSS so the two views cannot disagree about what
   a session is doing. */
function sessionCard(d, sess){
  return `<div class="card sv-card">` +
    sessionCardCore(d, sess, {working: false, lead: false, spark: false, consumption: false}) +
    `</div>`;
}

/* One workflow's dispatch history as a session-centric work log: each
   dispatched (slug, stage) with when it was dispatched and the last gate
   decision. Live dispatched ensigns carry the `sd-live` class. When the
   session has no dispatch history, the stage-spine tree is preserved so the
   view still shows the workflow's entity roster. Non-dispatched workflow
   entities are labeled "other workflow entities" — not "NOT TOUCHED" —
   because the session may have advanced them without a live worker right now. */
function sessionWorkflow(wf, sd){
  const stages = wf.stages || [];
  const entities = wf.entities || [];
  const goal = wf.goal || "";
  const goalHtml = goal ? `<div class="sv-goal">${esc(goal)}</div>` : "";
  const history = (sd && sd.dispatch_history) || [];
  /* Build a slug → entity lookup so each dispatch can cross-reference the
     workflow's entities for gate decision and live status. */
  const entMap = {};
  for(const ent of entities) entMap[ent.slug] = ent;
  /* When the session has a dispatch history, render it as the work log.
     Only dispatches whose slug matches this workflow's entities appear — a
     dispatch for another workflow's entity is not this workflow's work. */
  if(history.length){
    const dispatchedSlugs = new Set();
    const histRows = [];
    for(const disp of history){
      if(!(disp.slug in entMap)) continue;
      dispatchedSlugs.add(disp.slug);
      const ent = entMap[disp.slug];
      const live = ent && ent.live;
      const cls = live ? " sd-live" : "";
      const cyc = ent && ent.cycle ? ` <span class="sv-cyc">${esc(ent.cycle)}</span>` : "";
      const decBadge = ent && ent.decision ? sdDecisionBadge(ent.decision) : "";
      const when = disp.ts ? fmtDur(nowSec() - disp.ts) + " ago" : "";
      histRows.push(`<div class="sv-disp${cls}">` +
        `<span class="sv-disp-slug" title="${esc(disp.slug)}">${esc(sdSlug(disp.slug))}${cyc}</span>` +
        `<span class="sv-disp-stage">${esc(disp.stage)}</span>` +
        (decBadge ? `<span class="sv-dec">${decBadge}</span>` : "") +
        (when ? `<span class="sv-disp-when">${esc(when)}</span>` : "") +
        `</div>`);
    }
    /* Non-dispatched workflow entities: the roster minus what this session
       dispatched. Labeled accurately, never "NOT TOUCHED." */
    const otherEnts = entities.filter(e => !dispatchedSlugs.has(e.slug));
    const otherRows = otherEnts.length ? otherEnts.map(ent => {
      const live = ent.live ? " sd-live" : "";
      const cyc = ent.cycle ? ` <span class="sv-cyc">${esc(ent.cycle)}</span>` : "";
      const decBadge = ent.decision ? sdDecisionBadge(ent.decision) : "";
      return `<div class="sv-disp${live}">` +
        `<span class="sv-disp-slug" title="${esc(ent.slug)}">${esc(sdSlug(ent.slug))}${cyc}</span>` +
        `<span class="sv-disp-stage">${esc(ent.stage)}</span>` +
        (decBadge ? `<span class="sv-dec">${decBadge}</span>` : "") +
        `</div>`;
    }).join("") : "";
    const otherSection = otherRows
      ? `<div class="sv-other-sep"><span class="sd-k">other workflow entities</span></div>${otherRows}`
      : "";
    return `<div class="sv-wf"><div class="sv-wf-name">${esc(wf.workflow)}</div>${goalHtml}` +
      `<div class="sv-dispatch-hist">${histRows.join("")}</div>${otherSection}</div>`;
  }
  /* No dispatch history: preserve the stage-spine tree so the view still
     renders the workflow's entity roster for sessions that carry no
     dispatch records (non-Pi sessions). */
  const byStage = {};
  for(const ent of entities){
    const stage = ent.stage || "";
    (byStage[stage] = byStage[stage] || []).push(ent);
  }
  const spine = stages.map(stage => {
    const ents = byStage[stage] || [];
    const entHtml = ents.length ? ents.map(ent => {
      const live = ent.live ? " sd-live" : "";
      const cyc = ent.cycle ? ` <span class="sv-cyc">${esc(ent.cycle)}</span>` : "";
      return `<div class="sv-ent${live}" title="${esc(ent.slug)}">${esc(sdSlug(ent.slug))}${cyc}</div>`;
    }).join("") : `<div class="sv-ent-empty">—</div>`;
    return `<div class="sv-stage"><div class="sv-stage-name">${esc(stage)}</div>` +
      `<div class="sv-ents">${entHtml}</div></div>`;
  }).join("");
  return `<div class="sv-wf"><div class="sv-wf-name">${esc(wf.workflow)}</div>${goalHtml}` +
    `<div class="sv-tree">${spine}</div></div>`;
}

/* Distinct empty states for the four cases the session view can land in when
   the session is found but has no dispatch tree to render. Each gives a
   heading, a one-line explanation, and a back link — never a blank panel that
   reads as "stuck". */
function sessionEmptyState(d, sess){
  const sd = sess.spacedock;
  if(!sd){
    return sessionCard(d, sess) +
      `<div class="sv-empty sv-empty-type">` +
      `<div class="sv-empty-h">Not a Spacedock session</div>` +
      `<div class="sv-empty-p">This session is not driving a Spacedock workflow.</div>` +
      `</div>`;
  }
  if(sd.role === "first-officer"){
    return sessionCard(d, sess) +
      `<div class="sv-empty sv-empty-fo">` +
      `<div class="sv-empty-h">First officer with no in-flight entities</div>` +
      `<div class="sv-empty-p">No workflow entities are fresh enough to show. ` +
      `This may be a freshness-gate issue (see fix-spacedock-freshness-gate).</div>` +
      `</div>`;
  }
  const role = sd.role || "worker";
  return sessionCard(d, sess) +
    `<div class="sv-empty sv-empty-worker">` +
    `<div class="sv-empty-h">${esc(role)} session</div>` +
    `<div class="sv-empty-p">This Spacedock session has no in-flight workflow entities.</div>` +
    `</div>`;
}

function sessionView(d){
  if(!sessionViewKey){
    return sessionPicker(d);
  }
  const sess = ((d && d.sessions) || []).find(s => sessKey(s) === sessionViewKey);
  if(!sess){
    /* Loading state: the session was requested (via URL hash or picker) but is
       not in the current data. On a fresh page load the first fetch may not
       include it yet; on an established board it may be outside the display
       window. Either way the reader needs to know the page is working, not
       stuck on a blank panel. */
    return sessionBackBar() +
      `<div class="sv-loading">` +
      `<div class="sv-loading-text">Looking for session ${esc(sessionViewKey)}…</div>` +
      `<div class="sv-loading-p">It may be outside the display window. ` +
      `Try <a href="?all=1${location.hash ? "&" + location.hash.slice(1) : ""}">showing all sessions</a>.` +
      `</div></div>`;
  }
  const sd = sess.spacedock;
  if(!sd || !sd.workflows || !sd.workflows.length){
    return sessionBackBar() + sessionEmptyState(d, sess);
  }
  return sessionBackBar() + sessionCard(d, sess) +
    sd.workflows.map(wf => sessionWorkflow(wf, sd)).join("");
}
