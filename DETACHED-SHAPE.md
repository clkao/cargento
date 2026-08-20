# Detached-shape layout: how this workflow lives off Cargento's main branch

This workflow is **more detached than split-root**: both the workflow spec (this
`flow-repo`) and the entity state (`flow/.spacedock-state`) live in their own git
repos, separate from each other and from the Cargento code repo, while code
worktrees still land in Cargento. The mechanism works today with no binary change;
this note records why, because the two hard constraints are easy to forget and
re-deriving them costs an hour.

## The three repos

| repo | path | branch | origin | holds |
|------|------|--------|--------|-------|
| Cargento code | `cargento/` | `main` | (Cargento's own) | the dashboard code; worktrees land here |
| flow-repo | `cargento/spacedock/flow-repo/` | `main` | none (local) | the workflow spec: `README.md`, `_mods/` |
| state-repo | `cargento/spacedock/flow/.spacedock-state/` | `spacedock-state/flow` | none (local) | entity files (the mutable state) |

`cargento/spacedock/` and `cargento/.worktrees/` are in `cargento/.git/info/exclude`
(not `.gitignore` — see the constraint below), so Cargento's `main` branch never
sees any of this: `git status` on `main` is clean (zero churn, the split-root
invariant).

## The two hard constraints (and how the layout satisfies them)

1. **`state:` cannot use `..`.** `status.ClassifyState` rejects any `state:` path
   with a `..` segment (`{"dotdot escape rejected", "../escape", ...}`) — it
   classifies such a value as inline, not split-root. So the state checkout must
   be a relative path **under** the workflow dir. The state-repo sits at
   `flow/.spacedock-state`, under the workflow dir `flow/`, so `state: .spacedock-state`
   is valid and resolves to `cargento/spacedock/flow/.spacedock-state`.

2. **No `.git` on the `FindGitRoot` climb path from the workflow dir to Cargento.**
   `status.FindGitRoot(workflowDir)` walks up the path stat-ing `d/.git` at each
   level and returns the first hit; it does **not** resolve symlinks
   (`filepath.Abs` is lexical). `dispatch build`/`stamp` derive the worktree git
   root from `FindGitRoot(workflowDir)`, so worktrees land wherever that climb
   stops. For worktrees to land in Cargento, the climb from
   `cargento/spacedock/flow` must hit `cargento/.git` first. That means:
   `cargento/spacedock/flow/` is a **real dir, not a git repo** (no `.git` at that
   level), and `cargento/spacedock/` is not a git repo either. `flow-repo/.git`
   and `flow/.spacedock-state/.git` exist, but neither is on the climb path
   (FindGitRoot checks `d/.git` at each level `d`, not recursively into subdirs),
   so the climb passes through them and stops at `cargento`.

## The symlink trick (why the flow spec can be version-controlled off the climb path)

The workflow spec must be readable at `cargento/spacedock/flow/README.md` for
discovery, but `cargento/spacedock/flow/` cannot be a git repo (constraint 2).
So `flow/README.md` and `flow/_mods` are **symlinks** into `flow-repo/`, which is
its own git repo one dir down. Discovery reads `README.md` (follows the file
symlink); the spec is version-controlled in `flow-repo`; and because symlinks
are not resolved by `FindGitRoot`, the climb still stops at Cargento.

A whole-dir symlink `flow -> flow-repo` would have been simpler but is rejected:
`state: .spacedock-state` would then resolve through the dir symlink into
`flow-repo/.spacedock-state`, co-locating state with the flow spec — exactly
what this layout avoids. Per-file/dir symlinks for the spec plus a real
`flow/.spacedock-state` subdir keep state in its own repo.

## What works and what does not (measured on `spacedock 0.27.0-pre8+dev`)

- `status --boot` from `cargento/` root auto-discovers `spacedock/flow` through
  `info/exclude` (discovery prunes tracked-`.gitignore` patterns but not
  `info/exclude`, and does not skip untracked dirs — the overlay-contribution
  sprint's finding). ✓
- `status --workflow-dir spacedock/flow --validate` → `VALID`. ✓
- `state ready` → exits 0 (`State checkout ready (no origin remote — state is
  local-only)`). ✓
- `state commit <slug>` → commits to the state-repo on `spacedock-state/flow`
  as local-only (`Preflight` only requires the checkout's HEAD branch to match
  `StateBranch(workflowDir)` = `spacedock-state/flow`; it does not require the
  checkout to be a worktree of the workflow dir's repo; `Publish` returns
  `ResultLocalOnly` when `git remote get-url origin` fails). ✓
- `dispatch build --stamp` → worktrees land in `cargento/.worktrees/`
  (`FindGitRoot(spacedock/flow)` = `cargento`). ✓ (not yet exercised live this
  session; the path arithmetic is confirmed.)
- `state init` on a **fresh clone** → **does not work**: it runs
  `git -C workflowDir fetch origin spacedock-state/flow`, which fetches from
  Cargento's origin (the workflow dir's repo), not the state-repo. With no
  `spacedock-state/flow` branch on Cargento's origin, the fetch fails. This is
  the overlay-contribution sprint's DoD-3 gap: resume-on-fresh-clone needs the
  state-repo to carry its own origin and `state init` to fetch from it, not from
  the workflow dir's repo. For a local-only workflow with no remote, this is
  acceptable — there is nothing to resume from. If this workflow ever gets a
  remote, the state-repo needs its own origin and `state init`'s fetch source
  is the binary gap to close.

## Resuming this layout

The state-repo and flow-repo are untracked from Cargento's `main` (via
`info/exclude`), so a fresh clone of Cargento has neither. To rebuild on a fresh
clone:

1. Recreate `cargento/.git/info/exclude` entries: `spacedock/` and `.worktrees/`.
2. Restore `flow-repo/` and `flow/.spacedock-state/` from their own remotes (once
   they have remotes), or re-create them locally from this doc:
   - `git init -b main spacedock/flow-repo` and commit the spec.
   - `mkdir -p spacedock/flow && ln -s ../flow-repo/README.md spacedock/flow/README.md && ln -s ../flow-repo/_mods spacedock/flow/_mods`
   - `git init -b spacedock-state/flow spacedock/flow/.spacedock-state` and commit entity state.

Until the state-repo has its own origin, this is a single-machine workflow.
