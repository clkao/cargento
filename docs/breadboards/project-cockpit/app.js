(function bootstrap(global) {
  "use strict";

  const FIXTURE = {
    projects: [
      {
        id: "cockpit",
        name: "Project cockpit",
        path: "spacedock-research/cargento",
        observerGoal: "Choose a project overview that restores context without transcript archaeology.",
      },
      {
        id: "launch-notes",
        name: "Launch notes",
        path: "spacedock-dev/launch",
        observerGoal: "Turn release evidence into a short launch narrative.",
      },
    ],
    sessions: [
      { id: "codex:8f21", projectId: "cockpit", title: "Breadboard project overview", stage: "breadboard", active: true },
      { id: "claude:22ab", projectId: "cockpit", title: "Audit observer seams", stage: "research", active: true },
      { id: "pi:909c", projectId: "launch-notes", title: "Draft release spine", stage: "shaping", active: true },
      { id: "codex:d111", projectId: "launch-notes", title: "Collect screenshots", stage: "parked", active: false },
    ],
    asks: [
      { id: "ask-1", projectId: "cockpit", sessionId: "codex:8f21", question: "Cards or ledger for the first scan?" },
    ],
  };

  const SOURCE_INVENTORY = [
    { source: "Project grouping and session facts", kind: "mocked", mechanism: "FIXTURE payload; shaped like the current grouped dashboard response" },
    { source: "Outstanding ask payload", kind: "mocked", mechanism: "Seed ask is a fixture; reassignment uses the live reducer below" },
    { source: "Ask-to-project reassignment", kind: "live", mechanism: "In-memory state transition followed by a complete re-render" },
    { source: "Operator-written goal", kind: "live", mechanism: "Browser localStorage, keyed by project; survives a real reload" },
    { source: "Observer goal publication", kind: "mocked", mechanism: "Button simulates a newly published observer payload" },
    { source: "Needs-you project signal", kind: "derived", mechanism: "Reduced from outstanding asks on every render" },
    { source: "Session mirror, memory, causal log, consistency", kind: "mocked", mechanism: "Not rendered; baseline prototype remains drill-down evidence only" },
  ];

  const clone = value => JSON.parse(JSON.stringify(value));
  const goalKey = projectId => `cargento.breadboard.project-goal.${projectId}`;

  function createModel(storage, fixture) {
    const state = clone(fixture || FIXTURE);

    function operatorGoal(projectId) {
      const saved = storage.getItem(goalKey(projectId));
      return saved && saved.trim() ? saved : null;
    }

    function goalFor(projectId) {
      const project = state.projects.find(item => item.id === projectId);
      const written = operatorGoal(projectId);
      return {
        text: written || (project ? project.observerGoal : ""),
        source: written ? "operator · browser storage" : "observer · fixture payload",
        authoritative: Boolean(written),
      };
    }

    function rememberGoal(projectId, text) {
      const normalized = String(text || "").trim();
      if (!normalized) throw new Error("goal must not be empty");
      storage.setItem(goalKey(projectId), normalized);
      return goalFor(projectId);
    }

    function publishObserverGoal(projectId, text) {
      const project = state.projects.find(item => item.id === projectId);
      if (!project) throw new Error(`unknown project: ${projectId}`);
      project.observerGoal = String(text);
      return goalFor(projectId);
    }

    function moveAsk(askId, projectId) {
      const ask = state.asks.find(item => item.id === askId);
      if (!ask) throw new Error(`unknown ask: ${askId}`);
      if (!state.projects.some(item => item.id === projectId)) throw new Error(`unknown project: ${projectId}`);
      ask.projectId = projectId;
    }

    function projectSnapshot(project) {
      const sessions = state.sessions.filter(item => item.projectId === project.id);
      const asks = state.asks.filter(item => item.projectId === project.id);
      return { ...project, sessions, asks, goal: goalFor(project.id), needsYou: asks.length > 0 };
    }

    function snapshot() {
      return state.projects.map(projectSnapshot);
    }

    function reset() {
      state.projects.forEach(project => storage.removeItem(goalKey(project.id)));
      const fresh = clone(fixture || FIXTURE);
      state.projects = fresh.projects;
      state.sessions = fresh.sessions;
      state.asks = fresh.asks;
    }

    return { goalFor, moveAsk, publishObserverGoal, rememberGoal, reset, snapshot };
  }

  function inventoryAudit(inventory) {
    const rows = inventory || SOURCE_INVENTORY;
    const allowed = new Set(["live", "mocked", "derived"]);
    const errors = [];
    rows.forEach(row => {
      if (!allowed.has(row.kind)) errors.push(`${row.source}: unknown kind`);
      if (!row.mechanism) errors.push(`${row.source}: missing mechanism`);
    });
    const fixtureClaims = rows.filter(row => row.kind === "live" && /fixture|constant/i.test(row.mechanism));
    fixtureClaims.forEach(row => errors.push(`${row.source}: fixture-only source cannot be called live`));
    return errors;
  }

  const esc = value => String(value).replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[char]));

  function sessionMarkup(session, ask) {
    return `<div class="session${ask ? " asking" : ""}">` +
      `<span class="live-dot" aria-label="${session.active ? "active" : "inactive"}" style="opacity:${session.active ? 1 : .22}"></span>` +
      `<div><div class="session-title">${esc(session.title)}</div><div class="session-meta">${esc(session.id)} · ${esc(session.stage)}</div></div>` +
      (ask ? `<div class="ask-copy">needs you · ${esc(ask.question)}</div>` : "") +
      `</div>`;
  }

  function goalEditor(project) {
    return `<form class="goal-editor" data-project="${esc(project.id)}">` +
      `<label><span>Operator goal</span><textarea rows="2" required>${esc(project.goal.text)}</textarea></label>` +
      `<button type="submit">Remember goal</button></form>`;
  }

  function deckMarkup(projects) {
    return `<div class="deck">${projects.map(project => {
      const sessions = project.sessions.map(session => sessionMarkup(session, project.asks.find(ask => ask.sessionId === session.id))).join("");
      const asks = project.asks.map(ask => `<div class="project-ask"><span class="attention">needs you</span>` +
        `<div><b>${esc(ask.question)}</b><span>${esc(ask.sessionId)}</span></div></div>`).join("");
      return `<article class="project-card${project.needsYou ? " needs-you" : ""}" data-project="${esc(project.id)}">` +
        `<div class="project-head"><div><h2>${esc(project.name)}</h2><p class="project-path">${esc(project.path)}</p></div>` +
        (project.needsYou ? `<span class="attention">needs you · ${project.asks.length}</span>` : `<span class="steady">clear</span>`) + `</div>` +
        `<div class="goal-block"><div class="label">Remembered goal</div><p class="goal-copy">${esc(project.goal.text)}</p>` +
        `<span class="goal-source">${esc(project.goal.source)}</span></div>` +
        asks + `<div class="label">Active work</div><div class="session-list">${sessions}</div>${goalEditor(project)}</article>`;
    }).join("")}</div>`;
  }

  function ledgerMarkup(projects) {
    return `<div class="ledger">${projects.map(project => {
      const sessions = project.sessions.map(session => {
        const ask = project.asks.find(item => item.sessionId === session.id);
        return `<div class="ledger-session"><span><b>${esc(session.title)}</b> · ${esc(session.stage)}</span>` +
          (ask ? `<span class="ledger-ask">${esc(ask.question)}</span>` : `<span>${session.active ? "active" : "parked"}</span>`) + `</div>`;
      }).join("");
      const asks = project.asks.map(ask => `<div class="ledger-ask"><b>${esc(ask.question)}</b><span>needs you · ${esc(ask.sessionId)}</span></div>`).join("");
      return `<article class="ledger-row${project.needsYou ? " needs-you" : ""}" data-project="${esc(project.id)}">` +
        `<div class="ledger-project"><strong>${esc(project.name)}</strong><span class="project-path">${esc(project.path)}</span>` +
        (project.needsYou ? `<div class="attention">needs you · ${project.asks.length}</div>` : "") + `</div>` +
        `<div class="ledger-goal"><span class="label">Goal</span><div>${esc(project.goal.text)}</div><span class="goal-source">${esc(project.goal.source)}</span></div>` +
        `<div class="ledger-sessions">${asks}${sessions}</div></article>`;
    }).join("")}</div>`;
  }

  function renderShape(shape, projects) {
    return shape === "ledger" ? ledgerMarkup(projects) : deckMarkup(projects);
  }

  global.CockpitBreadboard = {
    FIXTURE, SOURCE_INVENTORY, createModel, goalKey, inventoryAudit, renderShape,
  };

  if (!global.document || !global.localStorage) return;

  const document = global.document;
  const model = createModel(global.localStorage, FIXTURE);
  let shape = "deck";
  const cockpit = document.getElementById("cockpit");
  const log = document.getElementById("exercise-log");

  function bindEditors() {
    document.querySelectorAll(".goal-editor").forEach(form => form.addEventListener("submit", event => {
      event.preventDefault();
      const projectId = form.dataset.project;
      model.rememberGoal(projectId, form.querySelector("textarea").value);
      log.textContent = `Remembered an operator goal for ${projectId}. Reload now; observer text cannot replace it.`;
      render();
    }));
  }

  function render() {
    const projects = model.snapshot();
    cockpit.innerHTML = renderShape(shape, projects);
    document.getElementById("active-count").textContent = String(projects.flatMap(project => project.sessions).filter(session => session.active).length);
    document.getElementById("attention-count").textContent = String(projects.filter(project => project.needsYou).length);
    bindEditors();
  }

  document.querySelectorAll("[data-shape]").forEach(button => button.addEventListener("click", () => {
    shape = button.dataset.shape;
    document.querySelectorAll("[data-shape]").forEach(item => item.setAttribute("aria-pressed", String(item === button)));
    render();
  }));

  document.getElementById("move-ask").addEventListener("click", event => {
    const current = model.snapshot().find(project => project.asks.some(ask => ask.id === "ask-1"));
    const next = current.id === "cockpit" ? "launch-notes" : "cockpit";
    model.moveAsk("ask-1", next);
    event.currentTarget.textContent = `Move ask to ${current.name}`;
    log.textContent = `Moved ask-1 from ${current.id} to ${next}; the needs-you border and badge followed it.`;
    render();
  });

  document.getElementById("publish-conflict").addEventListener("click", () => {
    const visible = model.publishObserverGoal("cockpit", "OBSERVER CONFLICT: replace the cockpit with a transcript-first timeline.");
    log.textContent = visible.authoritative
      ? "Published conflicting observer text; the operator goal remained authoritative."
      : "Published observer text; no operator goal had been written, so the observer remains the fallback.";
    render();
  });

  document.getElementById("reset-demo").addEventListener("click", () => {
    model.reset();
    log.textContent = "Reset asks, observer fixtures, and browser-written goals.";
    render();
  });

  const audit = inventoryAudit(SOURCE_INVENTORY);
  document.getElementById("inventory").innerHTML = `<table class="inventory-table"><thead><tr><th>Source</th><th>Status</th><th>Mechanism / boundary</th></tr></thead><tbody>` +
    SOURCE_INVENTORY.map(row => `<tr><td>${esc(row.source)}</td><td><span class="kind ${esc(row.kind)}">${esc(row.kind)}</span></td><td>${esc(row.mechanism)}</td></tr>`).join("") +
    `</tbody></table><p>${audit.length ? esc(audit.join(" · ")) : "Inventory audit: every source is classified; no fixture-only source is labeled live."}</p>`;

  render();
}(typeof window === "undefined" ? globalThis : window));
