/* ── the observer panel ───────────────────────────────────────────────────────
   A compact card in a calm row's drawer: the derived goal, the current stage
   and one open block, from the sidecar `GET /api/observe` returns.

   State lives here rather than in the DOM, because the page rebuilds #app on
   every 5s refresh and anything written straight into a container is gone at
   the next paint. `observerBySid` holds the last answer per row so a re-render
   redraws it, and the fetch is fired by the row's `observe` control through
   the same [data-calm] channel every other control uses. */

const observerBySid = {};       /* row key -> {state, sidecar} */

function renderObserverPanel(sidecar){
  if(!sidecar) return '<div class="observer-empty">Not yet observed.</div>';
  const goal = sidecar.goal || "";
  const stage = sidecar.stage || "";
  const block = sidecar.block || "";
  const noGoal = goal === "no goal derived";
  const goalHtml = noGoal
    ? '<div class="observer-goal observer-sentinel">no goal derived</div>'
    : '<div class="observer-goal">' + esc(goal) + '</div>';
  const stageHtml = stage
    ? '<span class="observer-stage">' + esc(stage) + '</span>'
    : '';
  const blockHtml = block
    ? '<div class="observer-block">' + esc(block) + '</div>'
    : '';
  return '<div class="observer-panel">' + goalHtml + stageHtml + blockHtml + '</div>';
}

/* What the drawer draws for a row: nothing until the reader asks, because the
   derivation reads the transcript and two project files and a board of thirty
   rows must not do that on a poll. */
function observerBlock(key){
  const entry = observerBySid[key];
  if(!entry) return "";
  if(entry.state === "loading") return '<div class="observer-loading">observing…</div>';
  if(entry.state === "error") return '<div class="observer-error">observe failed</div>';
  return renderObserverPanel(entry.sidecar);
}

async function observeSession(harness, sid, key){
  observerBySid[key] = {state: "loading", sidecar: null};
  if(typeof lastData !== "undefined" && lastData) render(lastData);
  try{
    const r = await fetch("/api/observe?harness=" + encodeURIComponent(harness) +
      "&sid=" + encodeURIComponent(sid));
    if(!r.ok) throw new Error("bad status");
    observerBySid[key] = {state: "ready", sidecar: await r.json()};
  }catch(e){
    observerBySid[key] = {state: "error", sidecar: null};
  }
  if(typeof lastData !== "undefined" && lastData) render(lastData);
}

/* The row key is `<harness>:<sid>`, the same key every other calm control
   carries, so the control needs no second argument. */
function observeAction(key){
  const cut = String(key || "").indexOf(":");
  if(cut <= 0) return;
  observeSession(key.slice(0, cut), key.slice(cut + 1), key);
}
