(function startProjectCockpit(global) {
  "use strict";

  const model = global.ProjectCockpitModel;
  const state = { payload: null, error: null, selectedProject: null };
  const elements = {
    activeCount: document.querySelector("#active-count"),
    activeOnly: document.querySelector("#active-only"),
    askCount: document.querySelector("#ask-count"),
    focusedProject: document.querySelector("#focused-project"),
    projectCount: document.querySelector("#project-count"),
    projectSelect: document.querySelector("#project-select"),
    refresh: document.querySelector("#refresh"),
    sourceCard: document.querySelector(".source-card"),
    sourceDetail: document.querySelector("#source-detail"),
    sourceState: document.querySelector("#source-state"),
  };

  function age(timestamp) {
    const seconds = Math.max(0, Math.round(Date.now() / 1000 - Number(timestamp || 0)));
    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.round(seconds / 3600)}h ago`;
    return `${Math.round(seconds / 86400)}d ago`;
  }

  function message(className, text) {
    const node = document.createElement("div");
    node.className = className;
    node.textContent = text;
    return node;
  }

  function createAsk(ask) {
    const card = document.createElement("article");
    card.className = "ask-card";
    const question = document.createElement("p");
    question.textContent = String(ask.question || "Question text unavailable");
    const project = document.createElement("span");
    project.textContent = `Live registry id ${String(ask.id || "unknown")}`;
    const identity = document.createElement("code");
    identity.textContent = `${model.askSessionKey(ask)} · caller-supplied, unverified`;
    card.append(question, identity, project);
    return card;
  }

  function createSession(session) {
    const fragment = document.querySelector("#session-template").content.cloneNode(true);
    const row = fragment.querySelector(".session-row");
    row.classList.toggle("active", Boolean(session.active));
    row.dataset.harness = String(session.harness || "");
    row.dataset.sid = String(session.sid || "");
    fragment.querySelector(".session-title").textContent = String(
      session.title || session.last_prompt || "Untitled session",
    );
    fragment.querySelector(".session-detail").textContent = [
      String(session.state || "unknown"),
      session.state_detail ? String(session.state_detail) : null,
      age(session.last_activity),
    ].filter(Boolean).join(" · ");
    fragment.querySelector(".session-id").textContent = model.sessionKey(session);
    return fragment;
  }

  function readGoal(label) {
    try {
      return localStorage.getItem(model.goalStorageKey(label)) || "";
    } catch (error) {
      return "";
    }
  }

  function bindGoal(form, label) {
    const textarea = form.querySelector("textarea");
    const status = form.querySelector(".goal-status");
    const key = model.goalStorageKey(label);
    textarea.value = readGoal(label);
    form.querySelector(".goal-key").textContent = `Provisional identity key: exact project label → ${key}`;
    form.addEventListener("submit", event => {
      event.preventDefault();
      const value = textarea.value.trim();
      if (!value) {
        status.textContent = "Enter a goal or use Clear.";
        return;
      }
      try {
        localStorage.setItem(key, value);
        textarea.value = value;
        status.textContent = "Remembered in this browser.";
      } catch (error) {
        status.textContent = "Browser storage unavailable.";
      }
    });
    form.querySelector(".clear-goal").addEventListener("click", () => {
      try {
        localStorage.removeItem(key);
        textarea.value = "";
        status.textContent = "Browser value cleared.";
      } catch (error) {
        status.textContent = "Browser storage unavailable.";
      }
    });
    form.querySelector(".reload-page").addEventListener("click", () => global.location.reload());
  }

  function createProject(group, visibleSessions) {
    const fragment = document.querySelector("#project-template").content.cloneNode(true);
    const card = fragment.querySelector(".project-card");
    card.dataset.projectLabel = group.label;
    fragment.querySelector(".project-label").textContent = group.label;
    fragment.querySelector(".project-meta").textContent = `${visibleSessions.length} shown · ${group.sessions.length} total`;
    const signal = fragment.querySelector(".project-signal");
    signal.textContent = group.asks.length ? `${group.asks.length} live ask${group.asks.length === 1 ? "" : "s"}` : "no live asks";
    signal.classList.toggle("needs-you", group.asks.length > 0);
    bindGoal(fragment.querySelector(".goal-form"), group.label);
    const sessions = fragment.querySelector(".sessions");
    if (visibleSessions.length === 0) {
      sessions.append(message("empty-state", "No sessions match this view."));
    } else {
      visibleSessions.forEach(session => sessions.append(createSession(session)));
    }
    const attention = fragment.querySelector(".project-asks");
    if (state.payload.ask !== true) {
      attention.append(message("error-state", "Unavailable: this process does not advertise the ask registry."));
    } else if (group.asks.length === 0) {
      attention.append(message("empty-state", "No session in this project is asking through the live registry."));
    } else {
      group.asks.forEach(ask => attention.append(createAsk(ask)));
    }
    return card;
  }

  function renderProjectPicker(groups) {
    const labels = new Set(groups.map(group => group.label));
    if (!state.selectedProject || !labels.has(state.selectedProject)) {
      state.selectedProject = groups[0] ? groups[0].label : null;
    }
    elements.projectSelect.replaceChildren();
    groups.forEach(group => {
      const option = document.createElement("option");
      option.value = group.label;
      option.textContent = `${group.label} · ${group.sessions.length} session${group.sessions.length === 1 ? "" : "s"}`;
      option.selected = group.label === state.selectedProject;
      elements.projectSelect.append(option);
    });
    elements.projectSelect.disabled = groups.length === 0;
  }

  function renderFocusedProject(payload, groups) {
    elements.focusedProject.replaceChildren();
    const activeOnly = elements.activeOnly.checked;
    const group = groups.find(item => item.label === state.selectedProject);
    if (!group) {
      elements.focusedProject.append(message("empty-state", "No live project group is available."));
      return;
    }
    const sessions = activeOnly ? group.sessions.filter(session => session.active) : group.sessions;
    elements.focusedProject.append(createProject(group, sessions));
  }

  function render() {
    if (!state.payload) return;
    const payload = state.payload;
    const groups = model.groupPayload(payload);
    const sessions = Array.isArray(payload.sessions) ? payload.sessions : [];
    const asks = model.normalizedAsks(payload);
    elements.projectCount.textContent = String(groups.length);
    elements.activeCount.textContent = String(sessions.filter(item => item && item.active).length);
    elements.askCount.textContent = payload.ask === true ? String(asks.length) : "—";
    renderProjectPicker(groups);
    renderFocusedProject(payload, groups);
  }

  async function refresh() {
    elements.refresh.disabled = true;
    elements.sourceCard.classList.remove("live", "error");
    elements.sourceState.textContent = "Refreshing";
    try {
      const response = await fetch("/live-data", { cache: "no-store" });
      if (!response.ok) throw new Error(`snapshot request failed (${response.status})`);
      const payload = await response.json();
      if (!payload || typeof payload !== "object") throw new TypeError("snapshot is not an object");
      state.payload = payload;
      state.error = null;
      elements.sourceCard.classList.add("live");
      elements.sourceState.textContent = "Live snapshot";
      elements.sourceDetail.textContent = `127.0.0.1:4553 · generated ${age(payload.generated)}`;
      render();
    } catch (error) {
      state.error = error;
      elements.sourceCard.classList.add("error");
      elements.sourceState.textContent = "Source unavailable";
      elements.sourceDetail.textContent = String(error.message || error);
      elements.focusedProject.replaceChildren(message("error-state", "Cannot read live Cargento sessions or asks."));
    } finally {
      elements.refresh.disabled = false;
    }
  }

  elements.activeOnly.addEventListener("change", render);
  elements.projectSelect.addEventListener("change", () => {
    state.selectedProject = elements.projectSelect.value;
    render();
  });
  elements.refresh.addEventListener("click", refresh);
  refresh();
})(globalThis);
