#!/bin/sh
# setup.sh — bootstrap the detached Spacedock workflow for Cargento on a fresh clone.
#
# Run from the Cargento code clone root (the clone whose origin is your fork, or
# the upstream if you have write access). Idempotent: safe to re-run.
#
# The workflow spec and entity state live on the CANONICAL UPSTREAM
# (github.com/clkao/cargento), on three branches:
#   spacedock-workflow  — the workflow spec (README, _mods, DETACH.md, this script)
#   dev-state           — development task state (orphan branch)
#   explore-state       — exploration probe state (orphan branch)
# A contributor forks the Cargento CODE repo to open PRs, but the workflow spec
# and the durable state stay on clkao/cargento so every contributor shares the
# same workflows and ledgers. This script clones those branches from
# clkao/cargento, not from the code clone's own origin (which may be a fork).
#
# See DETACH.md for why the layout is shaped this way. This script is the
# outside-contributor resume path; the binary's `state init` does not fetch the
# README-declared state-branch today (overlay-contribution sprint DoD-3 gap).
set -e

# The canonical upstream that holds the workflow spec + state branches.
UPSTREAM=https://github.com/clkao/cargento
DEV_WORKFLOW_DIR=.spacedock/dev
EXPLORE_WORKFLOW_DIR=.spacedock/explore
REPO=.spacedock/repo

# 1. Keep .spacedock/ and .worktrees/ off Cargento's main branch (info/exclude,
#    not .gitignore — discovery prunes tracked-gitignore but not info/exclude).
EX=.git/info/exclude
grep -qxF '.spacedock/' "$EX" 2>/dev/null || echo '.spacedock/' >> "$EX"
grep -qxF '.worktrees/' "$EX" 2>/dev/null || echo '.worktrees/' >> "$EX"

# 2. Clone the spec branch into .spacedock/repo (skip if already present).
if [ ! -d "$REPO/.git" ]; then
  echo ">> cloning spacedock-workflow from $UPSTREAM -> $REPO"
  git clone -q "$UPSTREAM" "$REPO"
  git -C "$REPO" checkout -q spacedock-workflow
else
  echo ">> $REPO already present; fetching latest spec"
  git -C "$REPO" fetch -q origin spacedock-workflow
  git -C "$REPO" checkout -q spacedock-workflow
  git -C "$REPO" pull -q --ff-only origin spacedock-workflow 2>/dev/null || true
fi

# 3. Symlink the spec into the workflow dir (FindGitRoot climbs past symlinks to
#    Cargento, so worktrees land in Cargento — see DETACH.md constraint 2).
mkdir -p "$DEV_WORKFLOW_DIR" "$EXPLORE_WORKFLOW_DIR"
ln -sf ../repo/README.md "$DEV_WORKFLOW_DIR/README.md"
ln -sf ../repo/_mods "$DEV_WORKFLOW_DIR/_mods"
ln -sf ../repo/explore/README.md "$EXPLORE_WORKFLOW_DIR/README.md"

# 4. Fetch the state branch and check it out as a linked worktree at
#    dev/.spacedock-state (the README declares state-branch: dev-state).
git -C "$REPO" fetch -q "$UPSTREAM" dev-state
if [ ! -d "$DEV_WORKFLOW_DIR/.spacedock-state" ]; then
  # check out the fetched upstream dev-state as a local branch, then worktree it
  git -C "$REPO" worktree add -B dev-state "$DEV_WORKFLOW_DIR/.spacedock-state" "origin/dev-state"
else
  # already present — refresh from upstream so a resume sees peers' commits
  git -C "$DEV_WORKFLOW_DIR/.spacedock-state" fetch -q "$UPSTREAM" dev-state
  git -C "$DEV_WORKFLOW_DIR/.spacedock-state" pull -q --rebase "$UPSTREAM" dev-state 2>/dev/null || true
fi

# 5. Fetch and attach exploration state.
git -C "$REPO" fetch -q "$UPSTREAM" explore-state
if [ ! -d "$EXPLORE_WORKFLOW_DIR/.spacedock-state" ]; then
  git -C "$REPO" worktree add -B explore-state "$EXPLORE_WORKFLOW_DIR/.spacedock-state" "origin/explore-state"
else
  git -C "$EXPLORE_WORKFLOW_DIR/.spacedock-state" fetch -q "$UPSTREAM" explore-state
  git -C "$EXPLORE_WORKFLOW_DIR/.spacedock-state" pull -q --rebase "$UPSTREAM" explore-state 2>/dev/null || true
fi

# 6. Converge state (pull peers' entity commits into each worktree).
echo ">> spacedock state ready --workflow-dir $DEV_WORKFLOW_DIR"
"${SPACEDOCK_BIN:-spacedock}" state ready --workflow-dir "$DEV_WORKFLOW_DIR"
echo ">> spacedock state ready --workflow-dir $EXPLORE_WORKFLOW_DIR"
"${SPACEDOCK_BIN:-spacedock}" state ready --workflow-dir "$EXPLORE_WORKFLOW_DIR"

echo
echo "done. workflows at $DEV_WORKFLOW_DIR and $EXPLORE_WORKFLOW_DIR"
echo "  spec+state cloned from $UPSTREAM (spacedock-workflow + dev-state + explore-state)"
echo "  status:   ${SPACEDOCK_BIN:-spacedock} status --workflow-dir $DEV_WORKFLOW_DIR"
echo "  explore:  ${SPACEDOCK_BIN:-spacedock} status --workflow-dir $EXPLORE_WORKFLOW_DIR"
echo "  dispatch: spacedock pi  (or claude/codex)"
