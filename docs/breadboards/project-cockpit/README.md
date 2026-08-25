# Project cockpit breadboard

This is a disposable, standalone mechanism probe. It does not change the shipped Cargento page or runtime.

Open `index.html` through any static HTTP server. The page offers two project-overview shapes over the same scenario:

- **Project deck:** one bounded card per project, with goal, sessions, and interruption together.
- **Attention ledger:** a denser scan across projects, with the goal and active sessions held in columns.

The controls below the overview exercise the two risky contracts. Move the outstanding ask and verify the project-level `needs you` signal follows it. Write and remember a project goal, reload the page, publish conflicting observer text, and verify that the operator text remains visible.

## Run locally

```bash
python3 -m http.server 8765 --directory docs/breadboards/project-cockpit
```

Then open `http://127.0.0.1:8765/`.

Run the executable mechanism checks with:

```bash
node --test docs/breadboards/project-cockpit/app.test.js
```

## Survey result

The survey began from mirror prototype `e2fdaffc10ac31da5e5d39361bb2e95e3ca4c1a7`. That prototype already demonstrates the session drill-down: observer output, memory, causal history, needs-you metadata, state-of-world, and mocked steering and consistency panels. This breadboard changes only the entry point, from one session to a project overview.

The card deck makes the three facts easiest to recover for one project because attention, goal, and active work share a boundary. The ledger makes cross-project comparison faster and keeps attention from turning into a card-decoration hunt.

Production integration remains deliberately unchosen. Project/session collection and observer publication are fixtures here. Browser goal ownership, source precedence, ask reassignment, and needs-you reduction are exercised mechanisms. The page's evidence inventory names these boundaries and fails its audit if a fixture-only source is labeled live.

## Shaping recommendation

Select the **project deck as the default cockpit** and retain the attention ledger as an alternate comparison view. The evidence-derived criterion is: after the attention signal moves, can the operator name the project goal, the active work, the asking session, and the question from one bounded region without opening a transcript or mentally joining columns? Density is a tie-breaker only after that context-recovery test passes.

| Cost or tradeoff | Project deck | Attention ledger |
|---|---|---|
| Context recovery | Goal, work, and attention reason share one project boundary. Best fit for the criterion. | All facts remain on one surface, but the eye must join three columns. |
| Cross-project scan | Card height and a two-dimensional layout slow comparison as project count grows. | One row per project makes attention and goal differences fast to compare. |
| Attention reassignment | The full ask follows the highlighted card, including a session that is not in that card's session list. | The full ask follows the highlighted row; the denser third column competes with active work. |
| Goal editing | The operator can edit in context and immediately see its source precedence. | Read-only in this spike; editing would either widen the row or add a second interaction. |
| Narrow viewport | Cards collapse cleanly to one column, at the cost of more scrolling. | Rows also stack, losing the comparison advantage that justifies the shape. |
| Production cost | Requires a project-level view model and browser-owned goal adapter; the existing session mirror can remain drill-down. | Reuses the same view model, but needs a separate compact editor or an explicit jump to the deck. |

The recommendation is falsified if representative operators recover the four facts faster and with fewer wrong joins in the ledger, or if realistic project counts make card scanning materially slower before a decision is reached.

## Observed failure modes

- A project-level badge alone was insufficient after reassignment: the question became detached from its original session row. Both shapes now render the outstanding ask independently of session membership, so the reason for attention follows the signal.
- Cross-realm objects from the page harness looked structurally equal but failed strict Node assertions. The checks normalize page values before comparison; this is a harness boundary, not product evidence.
- Browser visual automation was unavailable in this worker. The artifact was served successfully and its page script was syntax-checked, but visual inspection remains a review action rather than claimed evidence.

## Choices that still matter

- Which scan dominates the operator rhythm: project cards for bounded context or the ledger for comparison.
- Whether the operator goal remains browser-owned or gains server-side persistence and multi-browser conflict handling.
- Whether an ask's project comes from the ask envelope, the owning session, or an explicit reassignment event.
- Where the existing session mirror opens from either shape, and which of its mocked panels should survive production shaping.
