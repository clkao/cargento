#!/bin/sh
# setup.sh — bootstrap the detached Spacedock workflow for Cargento on a fresh clone.
#
# Run from the Cargento repo root (the clone whose origin is your fork or the
# upstream). Idempotent: safe to re-run.
#
# It recreates the .spacedock/ layout from the two remote branches:
#   spacedock-workflow  — the workflow spec (README, _mods, DETACH.md, this script)
#   dev-state           — the entity state (orphan branch)
#
# See DETACH.md for why the layout is shaped this way. This script is the
# outside-contributor resume path; the binary's `state init` does not fetch the
# README-declared state-branch today (overlay-contribution sprint DoD-3 gap).
set -e

# Resolve the Cargento clone's origin URL (the contributor's fork, or upstream
# if you have write access). The spec and state branches live there.
ORIGIN_URL=$(git remote get-url origin)
WORKFLOW_DIR=.spacedock/dev
REPO=.spacedock/repo

# 1. Keep .spacedock/ and .worktrees/ off Cargento's main branch (info/exclude,
#    not .gitignore — discovery prunes tracked-gitignore but not info/exclude).
EX=.git/info/exclude
grep -qxF '.spacedock/' "$EX" 2>/dev/null || echo '.spacedock/' >> "$EX"
grep -qxF '.worktrees/' "$EX" 2>/dev/null || echo '.worktrees/' >> "$EX"

# 2. Clone the spec branch into .spacedock/repo (skip if already present).
if [ ! -d "$REPO/.git" ]; then
  echo ">> cloning spacedock-workflow from $ORIGIN_URL -> $REPO"
  git clone -q "$ORIGIN_URL" "$REPO"
  git -C "$REPO" checkout -q spacedock-workflow
fi

# 3. Symlink the spec into the workflow dir (FindGitRoot climbs past symlinks to
#    Cargento, so worktrees land in Cargento — see DETACH.md constraint 2).
mkdir -p "$WORKFLOW_DIR"
ln -sf ../repo/README.md "$WORKFLOW_DIR/README.md"
ln -sf ../repo/_mods "$WORKFLOW_DIR/_mods"

# 4. Fetch the state branch and check it out as a linked worktree at
#    dev/.spacedock-state (the README declares state-branch: dev-state).
git -C "$REPO" fetch -q origin dev-state
if [ ! -d "$WORKFLOW_DIR/.spacedock-state" ]; then
  git -C "$REPO" worktree add "$WORKFLOW_DIR/.spacedock-state" dev-state
else
  # already present — refresh from origin so a resume sees peers' commits
  git -C "$WORKFLOW_DIR/.spacedock-state" fetch -q origin dev-state
  git -C "$WORKFLOW_DIR/.spacedock-state" pull -q --rebase origin dev-state 2>/dev/null || true
fi

# 5. Converge state (pull peers' entity commits into the worktree).
echo ">> spacedock state ready --workflow-dir $WORKFLOW_DIR"
"${SPACEDOCK_BIN:-spacedock}" state ready --workflow-dir "$WORKFLOW_DIR"

echo
echo "done. workflow at $WORKFLOW_DIR"
echo "  status:   ${SPACEDOCK_BIN:-spacedock} status --workflow-dir $WORKFLOW_DIR"
echo "  dispatch: spacedock pi  (or claude/codex)"
