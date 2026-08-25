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

## Session interaction composition

The cockpit now includes a session-interaction lab. It compares a registered tmux adapter with a registered long-poll mailbox.

The decision criterion comes from the disposable tmux evidence. A viable channel must meet all of these conditions:

1. The session registers its interaction origin before the page can address it.
2. The page supplies only an opaque channel ID and bounded content. It supplies no transport locator.
3. The intended client receives the content without a text change. An unregistered client receives zero bytes.
4. Only an application receipt produces `acknowledged` or `rejected`.
5. A stale origin produces `refused`. A lost receipt or disconnected transport produces `unknown`.
6. The operator starts each delivery. The session explicitly starts and renews its registration.

If both variants meet these conditions, prefer the variant that avoids foreground-mode risk and works without a terminal-specific dependency.

The registered mailbox wins this comparison. Application acknowledgement is part of its contract, and the client owns content handling. The tmux variant needs a receiver shim to gain the same property. Without that shim, a pane write proves only that tmux accepted bytes.

| Cost or tradeoff | Registered tmux adapter | Registered long-poll mailbox |
|---|---|---|
| Target resolution | The server stores a tmux socket generation and pane ID. | The server stores an opaque channel and client generation. |
| Application receipt | A receiver shim must add it. | The contract requires it. |
| Foreground state | A different foreground program can change text meaning. | The registered client owns message handling. |
| Platform cost | Requires tmux and a stable pane. | Requires loopback HTTP and a small client. |
| Failure report | A tmux error or missing shim receipt becomes `unknown`. | A missing client receipt becomes `unknown`. |
| Useful role | Optional adapter behind a receiver protocol. | Selected transport-neutral prototype direction. |

### Choice classification

| Choice | Shaping result | Reason |
|---|---|---|
| Authentication | Security boundary. Captain decision required. | The prototype uses an opaque fixture ID and makes no authentication claim. |
| Payload power | Security boundary. Captain decision required. | Bounded text is useful, but it is more powerful than the ask lane's index response. |
| Consent lifetime | Consent boundary. Captain decision required. | A short renewable lease tied to client and server generations is the recommendation. |
| Queueing | Resolved for the recommendation: one outstanding message, then hard refusal. | A queue can hide operator intent and make stale work arrive late. |
| Retry | Resolved for the recommendation: no automatic retry. | A second attempt needs another operator action. Future retry support also needs stable IDs and client deduplication. |

The interaction lab does not steer a session. Its result reducer is live browser code over selected fixture states. The evidence inventory labels that boundary as mocked.

## Reproduce the interaction evidence

Run the static prototype:

```bash
python3 -m http.server 8765 --directory docs/breadboards/project-cockpit
```

Open `http://127.0.0.1:8765/`. In **Session interaction origin**, select and exercise each outcome.

- `Acknowledged` and `Rejected by session` show the exact input as application data.
- `Receipt path absent` and `Client disconnected` show `unknown`, never success.
- `Stale registration`, `Unregistered target`, and the locator attack show `refused` with zero application bytes.
- The default shell-metacharacter text remains literal in the result.

Run the browser contract checks:

```bash
node --test docs/breadboards/project-cockpit/app.test.js
```

Run the disposable tmux exercise and compare it with the committed result:

```bash
python3 docs/plans/session-interaction-origin-breadboard.py \
  | diff -u docs/plans/session-interaction-origin-breadboard-results.json -
```

This command starts two sessions on a new isolated tmux server. Only one session registers. The script stops that server on every exit path.

## Observed failure modes

- A project-level badge alone was insufficient after reassignment: the question became detached from its original session row. Both shapes now render the outstanding ask independently of session membership, so the reason for attention follows the signal.
- Cross-realm objects from the page harness looked structurally equal but failed strict Node assertions. The checks normalize page values before comparison; this is a harness boundary, not product evidence.
- Browser visual automation was unavailable in this worker. The artifact was served successfully and its page script was syntax-checked, but visual inspection remains a review action rather than claimed evidence.

## Choices that still matter

- Which scan dominates the operator rhythm: project cards for bounded context or the ledger for comparison.
- Whether the operator goal remains browser-owned or gains server-side persistence and multi-browser conflict handling.
- Whether an ask's project comes from the ask envelope, the owning session, or an explicit reassignment event.
- Where the existing session mirror opens from either shape, and which of its mocked panels should survive production shaping.
