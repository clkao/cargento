const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const script = fs.readFileSync(path.join(__dirname, "app.js"), "utf8");
const libraryContext = { window: {} };
vm.createContext(libraryContext);
vm.runInContext(script, libraryContext);
const { FIXTURE, SOURCE_INVENTORY, createModel, inventoryAudit, renderShape } = libraryContext.window.CockpitBreadboard;
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
