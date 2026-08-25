(function installProjectCockpitModel(global) {
  "use strict";

  const GOAL_PREFIX = "cargento.prototype.project-goal.v1:";

  function text(value, fallback = "") {
    return typeof value === "string" && value ? value : fallback;
  }

  function sessionKey(session) {
    return `${text(session.harness, "unknown")}:${text(session.sid, "unknown")}`;
  }

  function goalStorageKey(projectLabel) {
    return `${GOAL_PREFIX}${encodeURIComponent(projectLabel)}`;
  }

  function normalizedAsks(payload) {
    if (payload.ask !== true || !Array.isArray(payload.asks)) return [];
    return payload.asks.filter(ask => ask && typeof ask === "object");
  }

  function groupPayload(payload) {
    const groups = new Map();
    const sessions = Array.isArray(payload.sessions)
      ? payload.sessions.filter(session => session && typeof session === "object")
      : [];
    const asks = normalizedAsks(payload);

    function ensure(project) {
      const label = text(project, "Unlabeled project");
      if (!groups.has(label)) {
        groups.set(label, { label, sessions: [], asks: [] });
      }
      return groups.get(label);
    }

    sessions.forEach(session => ensure(session.project).sessions.push(session));
    asks.forEach(ask => ensure(ask.project).asks.push(ask));
    return [...groups.values()].sort((left, right) => {
      if (left.asks.length !== right.asks.length) return right.asks.length - left.asks.length;
      const leftNewest = Math.max(0, ...left.sessions.map(item => Number(item.last_activity) || 0));
      const rightNewest = Math.max(0, ...right.sessions.map(item => Number(item.last_activity) || 0));
      return rightNewest - leftNewest || left.label.localeCompare(right.label);
    });
  }

  function askSessionKey(ask) {
    return `${text(ask.harness, "unverified")}:${text(ask.session_id, "unverified")}`;
  }

  const api = { askSessionKey, goalStorageKey, groupPayload, normalizedAsks, sessionKey };
  global.ProjectCockpitModel = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof globalThis === "undefined" ? this : globalThis);
