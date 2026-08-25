# Live project cockpit shaping checkpoint

This isolated prototype reads the existing Cargento dashboard on `127.0.0.1:4553`. It groups the actual `sessions[]` rows by their exact project display label and shows actual `asks[]` rows only when the source advertises `ask: true`. It does not register, answer, withdraw, move, or synthesize an ask.

Run it from the repository root:

```bash
python3 docs/prototypes/project-cockpit/server.py --port 8765 --source-port 4553
```

Open `http://127.0.0.1:8765`. The prototype server binds only to IPv4 loopback and proxies only `GET /api/data` through its same-origin `/live-data` route.

## Captain interaction

1. Under **Which project are you working toward?**, choose a recognizable project label.
2. Confirm its active work uses visible `(harness, sid)` identities and **Needs you** says no session is asking while the live registry remains empty. No illustrative ask should appear.
3. Write the outcome you are working toward and select **Remember**. Select **Reload page** and confirm the value survives.
4. Read the provisional identity key shown below the editor. Decide whether the value helps recover context enough to justify designing a stable project identity and conflict rule.
5. Toggle **Show only active sessions** and select **Refresh live snapshot**.

## Evidence boundary

- Live: all session rows, project labels, active state, timestamps, and ask cards.
- Derived in the browser: exact-label grouping, counts, sorting, filtering, and the “live ask” signal.
- Browser-owned prototype: remembered goal text under `cargento.prototype.project-goal.v1:<encoded-label>`.
- Unavailable: stable project identity, server-visible project-goal persistence, observer/project goal reconciliation, ask reassignment, and session steering.
- Historical fixture only: everything under `docs/breadboards/project-cockpit/`. None of those values enter this prototype.

The goal editor proves a browser reload mechanism, not a product identity decision. Same-label projects collide, renames orphan the value, another browser cannot see it, the server cannot read it, and observer output has no defined precedence.

## Checks

```bash
node --test docs/prototypes/project-cockpit/model.test.js
ruff check docs/prototypes/project-cockpit/server.py
ruff format --check docs/prototypes/project-cockpit/server.py
curl -fsS http://127.0.0.1:8765/health
curl -fsS http://127.0.0.1:8765/live-data
```
