"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const model = require("./model.js");

test("groups only supplied session and ask rows while retaining identity", () => {
  const payload = {
    ask: true,
    sessions: [
      { project: "one", harness: "codex", sid: "same", active: true, last_activity: 20 },
      { project: "two", harness: "claude", sid: "same", active: false, last_activity: 10 },
    ],
    asks: [{ id: "a1", project: "two", harness: "claude", session_id: "same", question: "Q" }],
  };
  const groups = model.groupPayload(payload);
  assert.deepEqual(groups.map(group => group.label), ["two", "one"]);
  assert.equal(groups[0].asks[0], payload.asks[0]);
  assert.equal(groups[1].sessions[0], payload.sessions[0]);
  assert.equal(model.sessionKey(payload.sessions[0]), "codex:same");
  assert.equal(model.sessionKey(payload.sessions[1]), "claude:same");
});

test("does not display ask-shaped rows without the advertised capability", () => {
  const payload = {
    ask: false,
    sessions: [{ project: "one", harness: "pi", sid: "s1" }],
    asks: [{ id: "fixture-shaped", project: "one", question: "not live" }],
  };
  assert.deepEqual(model.normalizedAsks(payload), []);
  assert.equal(model.groupPayload(payload)[0].asks.length, 0);
});

test("uses an explicit provisional label key for browser persistence", () => {
  assert.equal(
    model.goalStorageKey("same label / other tree"),
    "cargento.prototype.project-goal.v1:same%20label%20%2F%20other%20tree",
  );
});

test("served source contains no historical fixture payload", () => {
  const root = __dirname;
  const source = ["index.html", "model.js", "app.js"]
    .map(file => fs.readFileSync(path.join(root, file), "utf8"))
    .join("\n");
  assert.doesNotMatch(source, /\bFIXTURE\b/);
  assert.doesNotMatch(source, /codex:8f21|Launch notes|Cards or ledger/);
  assert.match(source, /fetch\("\/live-data"/);
});
