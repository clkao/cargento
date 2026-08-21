# Detached-shape layout: how this workflow lives off Cargento's main branch

This workflow is **more detached than split-root**: the workflow spec and the
entity state live together in ONE repo (`flow-repo`) that is separate from the
Cargento code repo, while code worktrees still land in Cargento. The spec sits on
`flow-repo`'s `main` branch; the state sits on an orphan branch
`spacedock-state/flow` in the same repo, checked out as a linked worktree at
`flow/.spacedock-state`. This reuses the exact orphan-branch model split-root
already uses — just applied to a non-code repo, with symlinks for spec access so
`FindGitRoot` climbs to Cargento. The mechanism works today with no binary change;
this note records why, because the two hard constraints are easy to forget.

## The two repos

| repo | path | branch(es) | origin | holds |
|------|------|------------|--------|-------|
| Cargento code | `cargento/` | `main` | (Cargento's own) | the dashboard code; worktrees land here |
| flow-repo | `cargento/spacedock/flow-repo/` | `main` (spec) + `spacedock-state/flow` (orphan, state) | none (local) | the workflow spec on `main`; entity state on the orphan branch, checked out at `flow/.spacedock-state` |

`cargento/spacedock/` and `cargento/.worktrees/` are in `cargento/.git/info/exclude`
(not `.gitignore` — see the constraint below), so Cargento's `main` branch never
sees any of this: `git status` on `main` is clean (zero churn, the split-root
invariant).

## The two hard constraints (and how the layout satisfies them)

1. **`state:` cannot use `..`.** `status.ClassifyState` rejects any `state:` path
   with a `..` segment (`{"dotdot escape rejected", "../escape", ...}`) — it
   classifies such a value as inline, not split-root. So the state checkout must
   be a relative path **under** the workflow dir. The state worktree sits at
   `flow/.spacedock-state`, under the workflow dir `flow/`, so
   `state: .spacedock-state` is valid and resolves to
   `cargento/spacedock/flow/.spacedock-state`.

2. **No `.git` on the `FindGitRoot` climb path from the workflow dir to Cargento.**
   `status.FindGitRoot(workflowDir)` walks up the path stat-ing `d/.git` at each
   level and returns the first hit; it does **not** resolve symlinks
   (`filepath.Abs` is lexical). `dispatch build`/`stamp` derive the worktree git
   root from `FindGitRoot(workflowDir)`, so worktrees land wherever that climb
   stops. For worktrees to land in Cargento, the climb from
   `cargento/spacedock/flow` must hit `cargento/.git` first. That means:
   `cargento/spacedock/flow/` is a **real dir, not a git repo** (no `.git` at that
   level), and `cargento/spacedock/` is not a git repo either. `flow-repo/.git`
   exists, but it is not on the climb path (`FindGitRoot` checks `d/.git` at each
   level `d`, not recursively into subdirs), so the climb passes it and stops at
   `cargento`.

## The symlink trick (why the flow spec can be version-controlled off the climb path)

The workflow spec must be readable at `cargento/spacedock/flow/README.md` for
discovery, but `cargento/spacedock/flow/` cannot be a git repo (constraint 2).
So `flow/README.md` and `flow/_mods` are **symlinks** into `flow-repo/`, which is
its own git repo one dir down. Discovery reads `README.md` (follows the file
symlink); the spec is version-controlled in `flow-repo` on `main`; and because
symlinks are not resolved by `FindGitRoot`, the climb still stops at Cargento.

The state worktree at `flow/.spacedock-state` is a real dir (not a symlink) — it
is a linked worktree of `flow-repo` checked out on the orphan branch
`spacedock-state/flow`. Its `.git` is a gitdir pointer into
`flow-repo/.git/worktrees/`, so state commits land in `flow-repo`'s object store
on the orphan branch. The orphan branch keeps state off `flow-repo`'s `main`
(spec) branch — zero churn on the spec, the same property split-root gives the
code branch.

A whole-dir symlink `flow -> flow-repo` would have been simpler but is rejected:
`state: .spacedock-state` would then resolve through the dir symlink into
`flow-repo/.spacedock-state`, putting the state worktree inside `flow-repo`'s
main working tree — the orphan-branch worktree cannot live inside its own repo's
main checkout. Per-file symlinks for the spec plus a real
`flow/.spacedock-state` worktree subdir keep the state checkout under the
workflow dir (constraint 1) while the spec stays version-controlled.

## What works and what does not (measured on `spacedock 0.27.0-pre8+dev`)

- `status --boot` from `cargento/` root auto-discovers `spacedock/flow` through
  `info/exclude` (discovery prunes tracked-`.gitignore` patterns but not
  `info/exclude`, and does not skip untracked dirs — the overlay-contribution
  sprint's finding). ✓
- `status --workflow-dir spacedock/flow --validate` → `VALID`. ✓
- `state ready` → exits 0 (`State checkout ready (no origin remote — state is
  local-only)`). ✓
- `state commit <slug>` → commits to the state worktree (on the orphan branch)
  as local-only (`Preflight` only requires the checkout's HEAD branch to match
  `StateBranch(workflowDir)` = `spacedock-state/flow`; it does not require the
  checkout to be a worktree of the workflow dir's repo; `Publish` returns
  `ResultLocalOnly` when `git remote get-url origin` fails). ✓
- `dispatch build --stamp` → worktrees land in `cargento/.worktrees/`
  (`FindGitRoot(spacedock/flow)` = `cargento`). ✓ (path arithmetic confirmed;
  not yet exercised live this session.)
- `state init` on a **fresh clone** → **does not work**: it runs
  `git -C workflowDir fetch origin spacedock-state/flow`, which uses the workflow
  dir's repo — but `flow/` is not a git repo, so git climbs to Cargento's origin,
  which has no `spacedock-state/flow` branch (it lives in `flow-repo`). This is
  the overlay-contribution sprint's DoD-3 gap: resume-on-fresh-clone needs the
  state branch's own origin and `state init` to fetch from it. For a local-only
  workflow with no remote, there is nothing to resume from. If `flow-repo` ever
  gets a remote, the orphan branch rides with it, and `state init`'s fetch source
  is the binary gap to close.

## Resuming this layout

`flow-repo` is untracked from Cargento's `main` (via `info/exclude`), so a fresh
clone of Cargento has neither the spec nor the state. To rebuild on a fresh
clone (once `flow-repo` has its own remote):

1. Recreate `cargento/.git/info/exclude` entries: `spacedock/` and `.worktrees/`.
2. Clone `flow-repo` to `cargento/spacedock/flow-repo/`.
3. `mkdir -p spacedock/flow && ln -s ../flow-repo/README.md spacedock/flow/README.md && ln -s ../flow-repo/_mods spacedock/flow/_mods`
4. `git -C spacedock/flow-repo worktree add ../flow/.spacedock-state spacedock-state/flow`

Until `flow-repo` has its own origin, this is a single-machine workflow.
