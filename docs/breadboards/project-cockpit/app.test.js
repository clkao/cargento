const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const script = fs.readFileSync(path.join(__dirname, "app.js"), "utf8");
function loadLibrary(source = script) {
  const context = { window: {} };
  vm.createContext(context);
  vm.runInContext(source, context);
  return context.window.CockpitBreadboard;
}
const library = loadLibrary();
const {
  FIXTURE,
  SOURCE_INVENTORY,
  createInteractionModel,
  createModel,
  exerciseLiveInventory,
  interactionMarkup,
  inventoryAudit,
  renderShape,
} = library;
const plain = value => JSON.parse(JSON.stringify(value));

class MemoryStorage {
  constructor() { this.values = new Map(); }
  getItem(key) { return this.values.has(key) ? this.values.get(key) : null; }
  setItem(key, value) { this.values.set(key, String(value)); }
  removeItem(key) { this.values.delete(key); }
}

function element(props = {}) {
  const listeners = {};
  return Object.assign({
    innerHTML: "",
    textContent: "",
    dataset: {},
    addEventListener(type, callback) { listeners[type] = callback; },
    fire(type, event = {}) { listeners[type](Object.assign({ currentTarget: this }, event)); },
    setAttribute(name, value) { this[name] = value; },
  }, props);
}

function createPage(storage) {
  const elements = {
    cockpit: element(),
    "exercise-log": element(),
    "active-count": element(),
    "attention-count": element(),
    "interaction-case": element({ value: "acknowledged" }),
    "interaction-input": element({ value: "literal input" }),
    "interaction-result": element(),
    "interaction-run": element(),
    "move-ask": element(),
    "publish-conflict": element(),
    "reset-demo": element(),
    inventory: element(),
  };
  const shapeButtons = ["deck", "ledger"].map(shape => element({ dataset: { shape } }));
  let forms = {};
  const document = {
    getElementById(id) { return elements[id]; },
    querySelectorAll(selector) {
      if (selector === "[data-shape]") return shapeButtons;
      if (selector !== ".goal-editor") return [];
      forms = Object.fromEntries(FIXTURE.projects.map(project => {
        const textarea = element({ value: "" });
        const form = element({
          dataset: { project: project.id },
          querySelector(query) { return query === "textarea" ? textarea : null; },
          textarea,
        });
        return [project.id, form];
      }));
      return Object.values(forms);
    },
  };
  const context = { window: { document, localStorage: storage } };
  vm.createContext(context);
  vm.runInContext(script, context);
  return { elements, get forms() { return forms; } };
}

test("moving an outstanding ask moves the one project-level needs-you signal", () => {
  const storage = new MemoryStorage();
  const page = createPage(storage);
  assert.equal(page.elements["active-count"].textContent, "3");
  assert.match(page.elements.cockpit.innerHTML, /needs-you[^>]*data-project="cockpit"/);

  page.elements["move-ask"].fire("click");
  assert.match(page.elements.cockpit.innerHTML, /needs-you[^>]*data-project="launch-notes"/);
  assert.match(page.elements.cockpit.innerHTML, /Cards or ledger for the first scan\?/);

  const model = createModel(storage, FIXTURE);
  const before = model.snapshot();
  assert.deepEqual(plain(before.map(project => [project.id, project.needsYou])), [["cockpit", true], ["launch-notes", false]]);
  assert.equal(before.flatMap(project => project.sessions).filter(session => session.active).length, 3);

  model.moveAsk("ask-1", "launch-notes");
  const after = model.snapshot();
  assert.deepEqual(plain(after.map(project => [project.id, project.needsYou])), [["cockpit", false], ["launch-notes", true]]);
  assert.equal(after.find(project => project.id === "launch-notes").asks[0].sessionId, "codex:8f21");
  for (const shape of ["deck", "ledger"]) {
    const html = renderShape(shape, after);
    assert.match(
      html,
      /class="[^"]*needs-you[^"]*" data-project="launch-notes"[\s\S]*Cards or ledger for the first scan\?/,
    );
  }

  model.moveAsk("ask-1", "cockpit");
  const returned = model.snapshot();
  assert.deepEqual(
    plain(returned.map(project => [project.id, project.needsYou])),
    [["cockpit", true], ["launch-notes", false]],
  );
});

test("ask project comes from the ask envelope while its session stays put", () => {
  const model = createModel(new MemoryStorage(), FIXTURE);
  model.moveAsk("ask-1", "launch-notes");
  const projects = model.snapshot();
  const cockpit = projects.find(project => project.id === "cockpit");
  const launch = projects.find(project => project.id === "launch-notes");
  assert.ok(cockpit.sessions.some(session => session.id === "codex:8f21"));
  assert.ok(!launch.sessions.some(session => session.id === "codex:8f21"));
  assert.equal(launch.asks[0].sessionId, "codex:8f21");
  assert.equal(cockpit.asks.length, 0);

  for (const shape of ["deck", "ledger"]) {
    const html = renderShape(shape, projects);
    const cockpitRegion = html.slice(
      html.indexOf('data-project="cockpit"'),
      html.indexOf('data-project="launch-notes"'),
    );
    const launchRegion = html.slice(html.indexOf('data-project="launch-notes"'));
    assert.match(cockpitRegion, /Breadboard project overview/);
    assert.doesNotMatch(cockpitRegion, /Cards or ledger for the first scan\?/);
    assert.match(launchRegion, /Cards or ledger for the first scan\?/);
    assert.match(launchRegion, /codex:8f21/);
    assert.doesNotMatch(launchRegion, /Breadboard project overview/);
  }
});

test("operator goal survives a model reload and conflicting observer publication", () => {
  const storage = new MemoryStorage();
  const firstPage = createPage(storage);
  firstPage.forms.cockpit.textarea.value = "Keep projects legible at a glance.";
  firstPage.forms.cockpit.fire("submit", { preventDefault() {} });

  const reloadedPage = createPage(storage);
  assert.match(reloadedPage.elements.cockpit.innerHTML, /Keep projects legible at a glance\./);
  reloadedPage.elements["publish-conflict"].fire("click");
  assert.match(reloadedPage.elements.cockpit.innerHTML, /Keep projects legible at a glance\./);
  assert.doesNotMatch(reloadedPage.elements.cockpit.innerHTML, /OBSERVER CONFLICT/);

  const afterConflict = createModel(storage, FIXTURE).publishObserverGoal("cockpit", "Infer a transcript-first goal instead.");
  assert.deepEqual(plain(afterConflict), {
    text: "Keep projects legible at a glance.",
    source: "operator · browser storage",
    authoritative: true,
  });
});

test("inventory refuses a fixture-only source labeled live", () => {
  assert.deepEqual(plain(inventoryAudit(SOURCE_INVENTORY)), []);
  const dishonest = SOURCE_INVENTORY.concat({
    source: "Production projects",
    kind: "live",
    mechanism: "fixture-only constant",
  });
  assert.match(inventoryAudit(dishonest).join("\n"), /fixture-only source cannot be called live/);
});

test("registered interaction resolves one exact target and preserves literal text", () => {
  const model = createInteractionModel();
  const text = "literal; $(touch /tmp/not-run); `echo nope` && <tag>";
  const acknowledged = model.exercise("acknowledged", text);
  assert.deepEqual(plain(acknowledged), {
    state: "acknowledged",
    reason: "application-receipt",
    deliveredBytes: 52,
    messageId: "m1",
    receivedText: text,
  });
  assert.equal(model.inbox.length, 1);
  assert.equal(model.inbox[0].text, text);

  const unregistered = model.exercise("unregistered", "must not arrive");
  assert.deepEqual(plain(unregistered), {
    state: "refused",
    reason: "unregistered-origin",
    deliveredBytes: 0,
  });
  assert.equal(model.inbox.length, 1);

  const locator = model.exercise("locator-attack", text);
  assert.deepEqual(plain(locator), {
    state: "refused",
    reason: "malformed-request",
    deliveredBytes: 0,
  });
  assert.equal(model.inbox.length, 1);
  assert.doesNotMatch(interactionMarkup(acknowledged), /<tag>/);
  assert.match(interactionMarkup(acknowledged), /&lt;tag&gt;/);
});

test("interaction outcomes never promote missing evidence to success", () => {
  const cases = Object.fromEntries([
    "acknowledged",
    "rejected",
    "receipt-timeout",
    "stale",
    "disconnected",
  ].map(name => [name, createInteractionModel().exercise(name, "payload")]));

  assert.equal(cases.acknowledged.state, "acknowledged");
  assert.equal(cases.rejected.state, "rejected");
  assert.deepEqual(
    plain([cases["receipt-timeout"].state, cases["receipt-timeout"].reason]),
    ["unknown", "receipt-timeout"],
  );
  assert.deepEqual(plain([cases.stale.state, cases.stale.deliveredBytes]), ["refused", 0]);
  assert.deepEqual(
    plain([cases.disconnected.state, cases.disconnected.deliveredBytes]),
    ["unknown", 0],
  );
});

test("one pending mailbox entry causes a hard refusal and no automatic retry", () => {
  const model = createInteractionModel();
  const request = { channelId: "origin-a", text: "deliver once" };
  const queued = model.deliver(request, "pending", 50);
  assert.deepEqual(plain([queued.state, queued.reason]), ["queued", "awaiting-application-receipt"]);
  assert.equal(model.inbox.length, 1);

  const second = model.deliver(request, "acknowledged", 50);
  assert.deepEqual(plain(second), {
    state: "refused",
    reason: "mailbox-busy",
    deliveredBytes: 0,
  });
  assert.equal(model.inbox.length, 1);
});

test("interaction control renders the selected result on the page", () => {
  const page = createPage(new MemoryStorage());
  page.elements["interaction-case"].value = "rejected";
  page.elements["interaction-input"].value = "do not infer success";
  page.elements["interaction-run"].fire("click");
  assert.match(page.elements["interaction-result"].innerHTML, /class="outcome rejected">rejected/);
  assert.match(page.elements["interaction-result"].innerHTML, /do not infer success/);
});

test("each live inventory probe catches a fixture-only replacement", () => {
  const expected = {
    "ask-reassignment-bidirectional": {
      route: ["cockpit", "launch-notes", "cockpit"],
      sessionOwner: "cockpit",
    },
    "operator-goal-roundtrip": {
      cockpit: "Operator goal alpha",
      launchNotes: "Operator goal beta",
    },
  };
  assert.deepEqual(plain(exerciseLiveInventory(new MemoryStorage(), FIXTURE)), expected);

  const mutations = [
    ['ask.projectId = projectId;', 'ask.projectId = "launch-notes";'],
    [
      'storage.setItem(goalKey(projectId), normalized);',
      'storage.setItem(goalKey(projectId), "fixture goal");',
    ],
  ];
  for (const [live, fixtureConstant] of mutations) {
    assert.match(script, new RegExp(live.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
    const mutant = loadLibrary(script.replace(live, fixtureConstant));
    const result = plain(mutant.exerciseLiveInventory(new MemoryStorage(), mutant.FIXTURE));
    assert.notDeepEqual(result, expected, `fixture mutation survived: ${fixtureConstant}`);
  }
});
