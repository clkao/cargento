# Stable operator cockpit server

This server keeps `http://127.0.0.1:8766/` available while the Cargento backend changes.
It starts two backend ports in sequence and publishes only a healthy backend.

The server owns a clean checkout of `clkao/proto/operator-cockpit`.
It fetches this branch and accepts only a fast-forward update.
The server does not write to `spacedock-dev/cargento`.

## Start a review checkpoint

Run this command from the review worktree:

```bash
.venv/bin/python scripts/serve_operator_cockpit.py \
  --public-port 8766 \
  --backend-port-a 18766 \
  --backend-port-b 18767 \
  --checkout /Users/clkao/.cache/cargento/proto-operator-cockpit \
  --state-dir /Users/clkao/.cache/cargento/operator-cockpit-server \
  --review-root /Users/clkao/git/spacedock-research/cargento/.worktrees/spacedock-ensign-project-cockpit \
  --review-commit <review-sha> \
  --python /Users/clkao/git/spacedock-research/cargento/.worktrees/spacedock-ensign-project-cockpit/.venv/bin/python
```

The review worktree must be clean. Its `HEAD` must equal `<review-sha>`.
The server watches this worktree and accepts only fast-forward commits.

Open `http://127.0.0.1:8766/__proto/checkpoint` to see the published checkpoint and backend port.
The HTML page requests this endpoint every 1.5 seconds.
The browser reloads when the published checkpoint changes.

## Follow an accepted remote checkpoint

After the accepted push, record the exact remote checkpoint:

```bash
.venv/bin/python scripts/serve_operator_cockpit.py \
  --checkout /Users/clkao/.cache/cargento/proto-operator-cockpit \
  --state-dir /Users/clkao/.cache/cargento/operator-cockpit-server \
  --accept-remote <pushed-sha>
```

The watcher fetches the remote branch.
It changes the source only after the branch contains `<pushed-sha>`.
This explicit step supports an accepted change that has a new SHA after a rebase.

## Stop the server

```bash
.venv/bin/python scripts/serve_operator_cockpit.py \
  --public-port 8766 \
  --checkout /Users/clkao/.cache/cargento/proto-operator-cockpit \
  --state-dir /Users/clkao/.cache/cargento/operator-cockpit-server \
  --stop
```

The stop command reads the recorded PID.
It also makes sure that this PID owns the stable URL before it sends `SIGTERM`.

## Recover the server

If the process stops, run the start command again.
After integration, use the last accepted checkout without `--review-root` and `--review-commit`:

```bash
.venv/bin/python scripts/serve_operator_cockpit.py \
  --public-port 8766 \
  --backend-port-a 18766 \
  --backend-port-b 18767 \
  --checkout /Users/clkao/.cache/cargento/proto-operator-cockpit \
  --state-dir /Users/clkao/.cache/cargento/operator-cockpit-server \
  --python /Users/clkao/git/spacedock-research/cargento/.worktrees/spacedock-ensign-project-cockpit/.venv/bin/python
```

If the checkout is dirty or the remote branch diverges, read the server error.
Do not repair the checkout with `git reset --hard`.
Move the checkout aside.
Then let the server make a new dedicated clone.

Backend logs are in `/Users/clkao/.cache/cargento/operator-cockpit-server/`.
The proxy keeps the public port during a backend replacement.
The API and SSE paths use the same proxy as the HTML page.
