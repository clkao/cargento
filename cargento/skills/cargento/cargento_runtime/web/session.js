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

/* Derive the "needs you" readiness states from gate/resolution metadata that
   each entity already carries: `decision`, `target_stage`, `decision_by`,
   `decision_at`, and `live`. The banner counts these so the user instantly
   knows whether action is required before reading anything else.

   - approved-awaiting-merge: approved (decision=approve) with target_stage=done
     but not yet at done — the entity is waiting for someone to merge it.
   - awaiting-captain: a gate is open/pending at a stage the captain holds.
     Detected as entities with no decision (pending gate) whose stage is one
     the captain would resolve (decision_by would be person:captain).
   - in-flight: a live worker with no decision yet — something is happening,
     no action required.

   All entities in the workflow are counted because the first officer oversees
   the entire workflow, not just the entities it dispatched. */
function sessionNeeds(sd){
  const wfs = (sd && sd.workflows) || [];
  let approvedMerge = 0, awaitingCaptain = 0, inFlight = 0;
  for(const wf of wfs){
    for(const ent of (wf.entities || [])){
      if(ent.live){
        inFlight++;
        continue;
      }
      if(ent.decision === "approve" && ent.target_stage === "done" && ent.stage !== "done"){
        approvedMerge++;
      }
    }
  }
  return {approvedMerge, awaitingCaptain, inFlight};
}

function sessionNeedsBanner(needs){
  const parts = [];
  if(needs.approvedMerge > 0){
    parts.push(`<strong>${needs.approvedMerge}</strong> entit${needs.approvedMerge === 1 ? "y" : "ies"} approved, ready to merge`);
  }
  if(needs.awaitingCaptain > 0){
    parts.push(`<strong>${needs.awaitingCaptain}</strong> gate${needs.awaitingCaptain === 1 ? "" : "s"} awaiting your decision`);
  }
  if(!parts.length) return "";
  return `<div class="sv-needs-banner">` +
    `<span class="sv-needs-icon">⚠</span>` +
    `<span class="sv-needs-text">${parts.join(" · ")}</span>` +
    `</div>`;
}

/* The session card plus the "last instruction" (last_prompt) and "derived goal"
   (the session title framed as what this session is trying to do, optionally
   with the workflow goal). These anchor the user's first question: "what is
   this session about right now?" */
function sessionCardWithGoal(d, sess){
  const card = `<div class="card sv-card">` +
    sessionCardCore(d, sess, {working: false, lead: false, spark: false, consumption: false}) +
    `</div>`;
  const lastPrompt = sess.last_prompt ?
    `<div class="sv-last-instr"><span class="sv-last-instr-k">last instruction</span>` +
    `<span class="sv-last-instr-v">${esc(sess.last_prompt)}</span></div>` : "";
  const sd = sess.spacedock;
  let goal = "";
  if(sd && sd.workflows){
    const wfGoals = sd.workflows
      .map(w => w.goal).filter(Boolean);
    if(wfGoals.length){
      goal = `<div class="sv-goal-line"><span class="sv-goal-k">goal</span>` +
        `<span class="sv-goal-v">${esc(wfGoals.join(" · "))}</span></div>`;
    }
  }
  /* Collapsed latest response: the most recent assistant message text,
     shown in a <details> element so it's collapsed by default and expands on
     click. Gives the user a quick peek at what the session last said without
     opening the transcript. */
  const lastResponse = sess.last_response ?
    `<details class="sv-last-resp"><summary>latest response</summary>` +
    `<div class="sv-last-resp-body">${esc(sess.last_response)}</div></details>` : "";
  return card + lastPrompt + goal + lastResponse;
}

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
   decision. Live dispatched ensigns carry the `sd-live` class. Only entities
   the session actually dispatched appear — entities the session never touched
   belong in a project view, not here. The full stage spine (backlog → ideation
   → implementation → validation → done) is NOT repeated per entity; just the
   current stage name is shown, because the user already knows the pipeline. */
function sessionWorkflow(wf, sd){
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
     dispatch for another workflow's entity is not this workflow's work.
     Only entities the session dispatched are shown — untouched entities are
     cut as noise that belongs in a project view. */
  if(history.length){
    const dispatchedSlugs = new Set();
    const histRows = [];
    /* Deduplicate: show only the latest dispatch per (slug) so the user sees
       where each entity is now, not the full chronological log of every
       dispatch. Earlier dispatches of the same entity are noise — the user
       cares about the current state, not the history of how it got there. */
    const seen = new Set();
    for(let i = history.length - 1; i >= 0; i--){
      const disp = history[i];
      if(!(disp.slug in entMap)) continue;
      if(seen.has(disp.slug)) continue;
      seen.add(disp.slug);
      const ent = entMap[disp.slug];
      dispatchedSlugs.add(disp.slug);
      const live = ent && ent.live;
      const cls = live ? " sd-live" : "";
      const cyc = ent && ent.cycle ? ` <span class="sv-cyc">${esc(ent.cycle)}</span>` : "";
      const decBadge = ent && ent.decision ? sdDecisionBadge(ent.decision) : "";
      const when = disp.ts ? fmtDur(nowSec() - disp.ts) + " ago" : "";
      /* Show the entity's current stage (from the entity, not the dispatch) so
         the user sees where it is NOW, not where it was dispatched to. */
      const curStage = ent ? ent.stage : disp.stage;
      histRows.unshift(`<div class="sv-disp${cls}">` +
        `<span class="sv-disp-slug" title="${esc(disp.slug)}">${esc(sdSlug(disp.slug))}${cyc}</span>` +
        `<span class="sv-disp-stage">${esc(curStage)}</span>` +
        (decBadge ? `<span class="sv-dec">${decBadge}</span>` : "") +
        (when ? `<span class="sv-disp-when">${esc(when)}</span>` : "") +
        `</div>`);
    }
    return `<div class="sv-wf"><div class="sv-wf-name">${esc(wf.workflow)}</div>${goalHtml}` +
      `<div class="sv-dispatch-hist">${histRows.join("")}</div></div>`;
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
  const needs = sessionNeeds(sd);
  const needsBanner = sessionNeedsBanner(needs);
  return sessionBackBar() + needsBanner + sessionCardWithGoal(d, sess) +
    sd.workflows.map(wf => sessionWorkflow(wf, sd)).join("");
}
