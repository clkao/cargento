/* ── session mode: MIRROR of the agent ──────────────────────────────────────
   The session view is NOT a workflow task list. It is a MIRROR of the agent:
   what it's here to do, what it knows, what it did, what happened, what it
   needs, whether it's being consistent. If the agent opens its own session
   view, it should see itself.

   The mirror renders six sections in priority order:
   1. Goal — what am I here to do, and am I still doing it? (model-derived)
   2. Memory — what do I not want to forget? (model-derived one-paragraph digest)
   3. Causal log — what did I do, and what happened? (dispatch history + gates)
   4. Needs-you — am I stuck, and do I need the captain? (gate metadata)
   5. State of my world — the live footprint (async workers, PRs, running server)
   6. Consistency — am I being consistent? (aspirational for the prototype)

   Plus the STEERING RHYTHM: the captain's directives as a compressed timeline
   (what I was told, not what I did), the autonomy phases between bursts, and
   generated/corrected/reframed/answered tags showing steering→outcome links.

   Task list is REVERSE CHRONOLOGICAL — the freshest action first. The
   `decision_at` timestamp orders it. Badges show MEANING: "approved to merge"
   (target_stage=done), "approved to implement" (target_stage=implementation),
   not just "approve". The active subagent is surfaced prominently at the top.

   The session target is routable via the URL hash (#session=<harness>:<sid>).
   The observer's /api/observe is auto-triggered on session view open so the
   goal + memory are fresh without a background loop. */

/* ── observer sidecar state ──────────────────────────────────────────────
   The mirror holds the last observer sidecar so it can render the model-derived
   goal + memory without re-fetching on every poll. Loaded once when the
   session view opens (auto-trigger /api/observe) and cached. */
let mirrorObserver = null;
let mirrorObserverKey = null; /* tracks which session the observer was loaded for */

async function mirrorLoadObserver(harness, sid){
  try{
    const r = await fetch("/api/observe?harness=" + encodeURIComponent(harness) +
      "&sid=" + encodeURIComponent(sid));
    if(!r.ok) return;
    mirrorObserver = await r.json();
  }catch(e){ /* gateway unavailable — degrade to deterministic fallback */ }
}

/* ── needs-you signal ──────────────────────────────────────────────────────
   Counted from gate/resolution metadata each entity carries: decision,
   target_stage, decision_by, decision_at, and live. */
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

/* ── meaningful badges ──────────────────────────────────────────────────────
   A green "approve" with no context tells the user nothing. The badge says
   what it MEANS in user terms: not just "approve" but "approved to merge"
   (target_stage=done) or "approved to implement" (target_stage=implementation).
   Show who (decision_by) and the target on hover/expand. */
function mirrorDecisionBadge(ent){
  if(!ent.decision) return "";
  const d = SD_DECISIONS[ent.decision];
  if(!d) return "";
  let effect = d.label;
  if(ent.decision === "approve" && ent.target_stage){
    if(ent.target_stage === "done") effect = "approved to merge";
    else if(ent.target_stage === "implementation") effect = "approved to implement";
    else effect = "approved → " + ent.target_stage;
  } else if(ent.decision === "revise"){
    effect = "sent back for revision";
  } else if(ent.decision === "hold"){
    effect = "on hold";
  }
  const by = ent.decision_by ? " by " + ent.decision_by.replace(/^person:/, "") : "";
  const when = ent.decision_at ? " · " + sdRelTime(ent.decision_at) : "";
  const tip = "decision: " + ent.decision + by + (ent.target_stage ? " → " + ent.target_stage : "") + when;
  return `<span class="sd-badge ${d.cls}" title="${esc(tip)}">${esc(effect)}</span>`;
}

/* ── prominent active subagent ──────────────────────────────────────────────
   The live subagent(s) surfaced clearly at the top — the answer to "what's
   happening right now." Don't bury it in the roster. */
function mirrorActiveSubagents(sess){
  const subs = (sess.subagents && sess.subagents.length) ? sess.subagents : [];
  const live = subs.filter(a => a.live !== false);
  if(!live.length) return "";
  const pills = live.map(a => {
    const model = childModelShown(sess, a);
    return `<span class="sv-mirror-active-pill">` +
      `<span class="subdot"></span>${esc(subName(a))}` +
      (model ? `<span class="sv-mirror-active-model">${esc(model)}</span>` : "") +
      `</span>`;
  }).join("");
  return `<div class="sv-mirror-active">` +
    `<span class="sv-mirror-active-k">active now</span>` +
    `<div class="sv-mirror-active-list">${pills}</div></div>`;
}

/* ── 1. Goal (model-derived) ──────────────────────────────────────────────── */
function mirrorGoalSection(sess){
  let goal = "";
  let source = "deterministic";
  /* The observer sidecar carries the model-derived goal + memory. When it's
     loaded, use it. The deterministic fallback (workflow goal) is the
     short-circuit when the model is unavailable. */
  if(mirrorObserver && mirrorObserver.goal && mirrorObserver.goal !== "no goal derived"){
    goal = mirrorObserver.goal;
    source = "model-derived";
  } else {
    const sd = sess.spacedock;
    if(sd && sd.workflows){
      const wfGoals = sd.workflows.map(w => w.goal).filter(Boolean);
      if(wfGoals.length) goal = wfGoals.join(" · ");
    }
  }
  if(!goal){
    /* No goal from model or workflow. Show a loading hint if the observer
       hasn't loaded yet, or the sentinel if it has. */
    if(!mirrorObserver){
      goal = "deriving from transcript…";
      source = "loading";
    } else {
      return "";
    }
  }
  return `<div class="sv-mirror-section sv-mirror-goal">` +
    `<div class="sv-mirror-sec-k">goal</div>` +
    `<div class="sv-mirror-sec-v sv-mirror-goal-text${source === "loading" ? " sv-loading-text" : ""}">` +
    `${esc(goal)}</div>` +
    `<div class="sv-mirror-sec-src">${esc(source)}</div></div>`;
}

/* ── 2. Memory (model-derived one-paragraph digest) ──────────────────────── */
function mirrorMemorySection(){
  if(!mirrorObserver){
    /* Show a loading hint while the observer fetches. */
    return `<div class="sv-mirror-section sv-mirror-memory">` +
      `<div class="sv-mirror-sec-k">memory</div>` +
      `<div class="sv-mirror-sec-v sv-mirror-memory-text sv-loading-text">compressing transcript…</div></div>`;
  }
  if(!mirrorObserver.memory) return "";
  return `<div class="sv-mirror-section sv-mirror-memory">` +
    `<div class="sv-mirror-sec-k">memory</div>` +
    `<div class="sv-mirror-sec-v sv-mirror-memory-text">${esc(mirrorObserver.memory)}</div></div>`;
}

/* ── 3. Causal log (reverse-chronological) ──────────────────────────────────
   What I did and what happened. The dispatch history is the agent's actions;
   the gate decisions are what the world said back. REVERSE CHRONOLOGICAL:
   the freshest action first, ordered by decision_at (or dispatch ts). */
function mirrorCausalLog(sd){
  const wfs = (sd && sd.workflows) || [];
  const history = (sd && sd.dispatch_history) || [];
  const items = [];
  const wfNames = [];

  /* Collect causal events: each dispatched entity + its gate resolution. */
  for(const wf of wfs){
    wfNames.push(wf.workflow);
    const entMap = {};
    for(const ent of (wf.entities || [])) entMap[ent.slug] = ent;
    /* Match dispatch history to entities for gate metadata. */
    const seen = new Set();
    for(let i = history.length - 1; i >= 0; i--){
      const disp = history[i];
      if(!(disp.slug in entMap)) continue;
      if(seen.has(disp.slug)) continue;
      seen.add(disp.slug);
      const ent = entMap[disp.slug];
      const live = ent && ent.live;
      const cls = live ? " sd-live" : "";
      const cyc = ent && ent.cycle ? ` <span class="sv-cyc">${esc(ent.cycle)}</span>` : "";
      const decBadge = ent ? mirrorDecisionBadge(ent) : "";
      const curStage = ent ? ent.stage : disp.stage;
      /* For ordering: use decision_at if available, else dispatch ts. */
      const orderTs = ent && ent.decision_at ? Date.parse(ent.decision_at) / 1000 : (disp.ts || 0);
      items.push({
        ts: orderTs,
        html: `<div class="sv-disp${cls}">` +
          `<span class="sv-disp-slug" title="${esc(disp.slug)}">${esc(sdSlug(disp.slug))}${cyc}</span>` +
          `<span class="sv-disp-stage">${esc(curStage)}</span>` +
          (decBadge ? `<span class="sv-dec">${decBadge}</span>` : "") +
          (ent && ent.decision_at ? `<span class="sv-disp-when" title="${esc(ent.decision_at)}">${esc(sdRelTime(ent.decision_at))}</span>` : "") +
          `</div>`,
      });
    }
  }

  /* Sort reverse-chronological by ts (newest first). */
  items.sort((a, b) => (b.ts || 0) - (a.ts || 0));

  if(!items.length){
    /* No dispatch history: show the entities from the workflow directly,
       so the mirror still reflects what the session is working on for
       sessions that carry no dispatch records (non-Pi sessions). */
    for(const wf of wfs){
      for(const ent of (wf.entities || [])){
        const live = ent.live;
        const cls = live ? " sd-live" : "";
        const cyc = ent.cycle ? ` <span class="sv-cyc">${esc(ent.cycle)}</span>` : "";
        const decBadge = ent.decision ? mirrorDecisionBadge(ent) : "";
        items.push({
          ts: ent.decision_at ? Date.parse(ent.decision_at) / 1000 : 0,
          html: `<div class="sv-disp${cls}">` +
            `<span class="sv-disp-slug" title="${esc(ent.slug)}">${esc(sdSlug(ent.slug))}${cyc}</span>` +
            `<span class="sv-disp-stage">${esc(ent.stage)}</span>` +
            (decBadge ? `<span class="sv-dec">${decBadge}</span>` : "") +
            (ent.decision_at ? `<span class="sv-disp-when" title="${esc(ent.decision_at)}">${esc(sdRelTime(ent.decision_at))}</span>` : "") +
            `</div>`,
        });
      }
    }
    items.sort((a, b) => (b.ts || 0) - (a.ts || 0));
  }
  if(!items.length) return "";
  const namesHtml = wfNames.length
    ? `<div class="sv-wf-name">${esc(wfNames.join(" · "))}</div>`
    : "";
  return `<div class="sv-mirror-section sv-mirror-causal">` +
    `<div class="sv-mirror-sec-k">what I did</div>` +
    `<div class="sv-mirror-sec-body">${namesHtml}` +
    `<div class="sv-dispatch-hist">${items.map(it => it.html).join("")}</div></div></div>`;
}

/* ── 4. Needs-you (gate metadata) ─────────────────────────────────────────── */
function mirrorNeedsSection(sd){
  const needs = sessionNeeds(sd);
  if(!needs.approvedMerge && !needs.awaitingCaptain && !needs.inFlight) return "";
  return `<div class="sv-mirror-section sv-mirror-needs">` +
    `<div class="sv-mirror-sec-k">needs you</div>` +
    `<div class="sv-mirror-sec-v">${sessionNeedsBanner(needs) || "no blockers"}</div></div>`;
}

/* ── 5. State of my world ────────────────────────────────────────────────────
   The live footprint: async workers running, PRs open, the integration branch.
   For the prototype, surface what the API carries (subagents, workflow state)
   and mock the rest as a follow-up note. */
function mirrorStateSection(sess, sd){
  const parts = [];
  const subs = (sess.subagents && sess.subagents.length) ? sess.subagents : [];
  const liveSubs = subs.filter(a => a.live !== false);
  if(liveSubs.length){
    parts.push(`<span class="sv-mirror-state-item">${liveSubs.length} live worker${liveSubs.length === 1 ? "" : "s"}</span>`);
  }
  const wfs = (sd && sd.workflows) || [];
  for(const wf of wfs){
    const ents = (wf.entities || []);
    const approved = ents.filter(e => e.decision === "approve" && e.target_stage === "done" && e.stage !== "done");
    if(approved.length){
      parts.push(`<span class="sv-mirror-state-item">${approved.length} approved-awaiting-merge</span>`);
    }
    const inProgress = ents.filter(e => e.live);
    if(inProgress.length && !liveSubs.length){
      parts.push(`<span class="sv-mirror-state-item">${inProgress.length} in-flight entit${inProgress.length === 1 ? "y" : "ies"}</span>`);
    }
  }
  if(!parts.length) return "";
  return `<div class="sv-mirror-section sv-mirror-state">` +
    `<div class="sv-mirror-sec-k">state of my world</div>` +
    `<div class="sv-mirror-sec-v">${parts.join(" · ")}</div></div>`;
}

/* ── 6. Consistency (aspirational) ──────────────────────────────────────────
   Did I say "verify user impact" but then approve on suite-green? Hold
   commitments against actions. For the prototype, this is mocked. */
function mirrorConsistencySection(){
  /* The observer will derive this for real later (compare stated commitments
     in the transcript head against actual gate decisions). For now, mock the
     shape so the section is visible. */
  return `<div class="sv-mirror-section sv-mirror-consistency">` +
    `<div class="sv-mirror-sec-k">consistency</div>` +
    `<div class="sv-mirror-sec-v sv-mirror-consistency-text">No inconsistencies detected. ` +
    `Stated commitment: "every task should have user impact." ` +
    `All recent approvals verified user impact.</div></div>`;
}

/* ── Steering rhythm ───────────────────────────────────────────────────────
   The captain's directives as a compressed, timestamped timeline — what I was
   told, NOT what I did. Plus autonomy phases between bursts, steering density,
   and generated/corrected/reframed/answered tags.

   For the PROTOTYPE, the steering log is mocked with realistic content from
   this session. The observer will derive it for real later (parse user messages
   from the transcript head, tag by theme, derive the gaps). The mock shows what
   the shape WOULD look like so the UX is visible. */

/* The steering bursts: each is a captain's directive tagged by intent.
   - generated: created new work/idea (highest leverage)
   - corrected: fixed existing work
   - reframed: changed direction
   - answered: the agent asked, the captain answered
   Generated bursts carry a "result" link showing what they produced. */
const STEERING_BURSTS = [
  {time: "07:28", tag: "generated", text: "You have the conn + 5 priorities for the day", result: "session bootstrapped"},
  {time: "08:40", tag: "reframed", text: "Integration branch is priority, PR cleanup can wait"},
  {time: "09:30", tag: "corrected", text: "Every task should have user impact"},
  {time: "10:15", tag: "generated", text: "Send 9t back — prototype E2E", result: "prototype + cost estimate"},
  {time: "10:45", tag: "generated", text: "Session view as a mirror of yourself", result: "mirror view prototype"},
  {time: "11:00", tag: "reframed", text: "Reverse chrono + meaningful badges"},
  {time: "11:10", tag: "answered", text: "Checkpoint after each round"},
  {time: "11:20", tag: "generated", text: "Steering rhythm + generated tags", result: "steering log section"},
];

const STEERING_TAG_META = {
  generated: {cls: "sv-steer-gen", label: "generated"},
  corrected: {cls: "sv-steer-corr", label: "corrected"},
  reframed: {cls: "sv-steer-reframe", label: "reframed"},
  answered: {cls: "sv-steer-answer", label: "answered"},
};

function mirrorSteeringSection(){
  const bursts = STEERING_BURSTS;
  /* Autonomy phases: the gaps between steering bursts. Each gap shows the
     duration and a mock outcome summary. */
  const phases = [];
  for(let i = 1; i < bursts.length; i++){
    const prev = bursts[i - 1];
    const curr = bursts[i];
    /* Parse HH:MM to minutes for the gap. */
    const toMin = t => { const [h, m] = t.split(":").map(Number); return h * 60 + m; };
    const gap = toMin(curr.time) - toMin(prev.time);
    if(gap > 0){
      const outcomes = [
        "workers dispatched, gates progressed",
        "4 ideation workers completed, 3 gates approved",
        "suite green, 2 PRs opened",
        "prototype built, self-critique done",
        "mirror sections wired",
      ];
      phases.push({
        after: prev.time,
        before: curr.time,
        gap: gap,
        outcome: outcomes[(i - 1) % outcomes.length],
      });
    }
  }

  const burstHtml = bursts.map(b => {
    const meta = STEERING_TAG_META[b.tag] || {cls: "", label: b.tag};
    const resultLink = b.result
      ? ` <span class="sv-steer-result">→ ${esc(b.result)}</span>`
      : "";
    return `<div class="sv-steer-burst ${meta.cls}">` +
      `<span class="sv-steer-time">${esc(b.time)}</span>` +
      `<span class="sv-steer-tag ${meta.cls}">${esc(meta.label)}</span>` +
      `<span class="sv-steer-text">${esc(b.text)}${resultLink}</span>` +
      `</div>`;
  }).join("");

  const phaseHtml = phases.map(p => {
    return `<div class="sv-steer-phase">` +
      `<span class="sv-steer-phase-gap">${esc(p.after)}–${esc(p.before)} (${p.gap}min)</span>` +
      `<span class="sv-steer-phase-out">${esc(p.outcome)}</span></div>`;
  }).join("");

  /* Steering density: simple count + trend. For the prototype, show the count
     and a flat-declining trend (good delegation). */
  const density = `${bursts.length} bursts over ~4h`;
  const trend = "↘ declining (good delegation)";

  return `<div class="sv-mirror-section sv-mirror-steering">` +
    `<div class="sv-mirror-sec-k">steering rhythm</div>` +
    `<div class="sv-steer-bursts">${burstHtml}</div>` +
    (phaseHtml ? `<div class="sv-steer-phases">` +
      `<div class="sv-steer-phases-h">autonomy phases</div>${phaseHtml}</div>` : "") +
    `<div class="sv-steer-density">` +
      `<span class="sv-steer-density-n">${esc(density)}</span>` +
      `<span class="sv-steer-density-trend">${esc(trend)}</span></div></div>`;
}

/* ── last instruction ──────────────────────────────────────────────────────── */
function mirrorLastInstruction(sess){
  if(!sess.last_prompt) return "";
  return `<div class="sv-last-instr"><span class="sv-last-instr-k">last instruction</span>` +
    `<span class="sv-last-instr-v">${esc(sess.last_prompt)}</span></div>`;
}

/* ── latest response (collapsed) ───────────────────────────────────────────── */
function mirrorLastResponse(sess){
  return sess.last_response
    ? `<details class="sv-last-resp"><summary>latest response</summary>` +
      `<div class="sv-last-resp-body">${esc(sess.last_response)}</div></details>` : "";
}

/* The session card: the shared card anatomy from sessionCardCore, wrapped
   for the mirror view. */
function mirrorSessionCard(d, sess){
  return `<div class="card sv-card">` +
    sessionCardCore(d, sess, {working: false, lead: false, spark: false, consumption: false}) +
    `</div>`;
}

/* ── the full mirror view ────────────────────────────────────────────────── */
function mirrorView(d, sess){
  const sd = sess.spacedock;
  const needs = sd ? sessionNeeds(sd) : {approvedMerge: 0, awaitingCaptain: 0, inFlight: 0};
  const needsBanner = sessionNeedsBanner(needs);

  /* The active subagent is surfaced prominently at the top — the answer to
     "what's happening right now." */
  const activeSubs = mirrorActiveSubagents(sess);

  /* The six mirror sections, in priority order. */
  const goalSec = mirrorGoalSection(sess);
  const memorySec = mirrorMemorySection();
  const steeringSec = mirrorSteeringSection();
  const causalSec = sd ? mirrorCausalLog(sd) : "";
  const needsSec = sd ? mirrorNeedsSection(sd) : "";
  const stateSec = mirrorStateSection(sess, sd);
  const consistencySec = mirrorConsistencySection();

  /* The last instruction and latest response anchor the bottom. */
  const lastInstr = mirrorLastInstruction(sess);
  const lastResp = mirrorLastResponse(sess);

  return sessionBackBar() + needsBanner +
    `<div class="sv-mirror">` +
    mirrorSessionCard(d, sess) +
    activeSubs +
    goalSec +
    memorySec +
    steeringSec +
    causalSec +
    needsSec +
    stateSec +
    consistencySec +
    lastInstr +
    lastResp +
    `</div>`;
}

/* ── session picker (unchanged from prior) ────────────────────────────────── */
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
  return `<div class="sv-picker"><div class="sv-picker-h">Select a session to view its mirror</div>${rows}</div>`;
}

function sessionBackBar(){
  return `<div class="sv-back-bar">` +
    `<button type="button" class="sv-back" data-calm="mode" data-arg="regular">← overview</button>` +
    `</div>`;
}

/* One workflow's dispatch history as a session-centric work log (kept for
   non-mirror rendering paths and tests that exercise the tree fallback). */
function sessionWorkflow(wf, sd){
  const stages = wf.stages || [];
  const entities = wf.entities || [];
  const goal = wf.goal || "";
  const goalHtml = goal ? `<div class="sv-goal">${esc(goal)}</div>` : "";
  const history = (sd && sd.dispatch_history) || [];
  const entMap = {};
  for(const ent of entities) entMap[ent.slug] = ent;
  if(history.length){
    const histRows = [];
    const seen = new Set();
    for(let i = history.length - 1; i >= 0; i--){
      const disp = history[i];
      if(!(disp.slug in entMap)) continue;
      if(seen.has(disp.slug)) continue;
      seen.add(disp.slug);
      const ent = entMap[disp.slug];
      const live = ent && ent.live;
      const cls = live ? " sd-live" : "";
      const cyc = ent && ent.cycle ? ` <span class="sv-cyc">${esc(ent.cycle)}</span>` : "";
      const decBadge = ent && ent.decision ? sdDecisionBadge(ent.decision) : "";
      const when = disp.ts ? fmtDur(nowSec() - disp.ts) + " ago" : "";
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

/* Distinct empty states for sessions with no Spacedock data. */
function sessionEmptyState(d, sess){
  const sd = sess.spacedock;
  if(!sd){
    return mirrorSessionCard(d, sess) +
      `<div class="sv-empty sv-empty-type">` +
      `<div class="sv-empty-h">Not a Spacedock session</div>` +
      `<div class="sv-empty-p">This session is not driving a Spacedock workflow.</div>` +
      `</div>`;
  }
  if(sd.role === "first-officer"){
    return mirrorSessionCard(d, sess) +
      `<div class="sv-empty sv-empty-fo">` +
      `<div class="sv-empty-h">First officer with no in-flight entities</div>` +
      `<div class="sv-empty-p">No workflow entities are fresh enough to show. ` +
      `This may be a freshness-gate issue (see fix-spacedock-freshness-gate).</div>` +
      `</div>`;
  }
  const role = sd.role || "worker";
  return mirrorSessionCard(d, sess) +
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
  return mirrorView(d, sess);
}
