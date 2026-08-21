# DETACH.md — why this workflow lives off Cargento's main branch

This workflow is **detached**: its spec and state live in one repo
(`.spacedock/repo/`) that is separate from the Cargento code repo, while
dispatched code worktrees still land in Cargento. This file records why the
layout is shaped the way it is — the two hard constraints are easy to forget
and re-deriving them costs an hour.

## Layout

```
cargento/                                  ← git repo, branch main (the dashboard code)
├── .git/info/exclude                      ← contains: .spacedock/  and  .worktrees/
├── .worktrees/                            ← where dispatched worktrees land (excluded)
└── .spacedock/                            ← excluded from cargento main; NOT a git repo
    ├── dev/                               ← workflow dir; real dir, NOT a git repo
    │   ├── README.md   → ../repo/README.md   (symlink)
    │   ├── _mods       → ../repo/_mods       (symlink)
    │   └── .spacedock-state/                ← git worktree of repo, branch spacedock-state/dev
    │       └── *.md                         (entity files)
    └── repo/                              ← THE one git repo
        ├── .git/
        ├── README.md                        (on branch main — the spec)
        ├── _mods/pr-merge.md                 (on branch main)
        └── DETACH.md                         (on branch main — this file)
```

One git repo (`.spacedock/repo/`), two branches, one object store:
- **`main`** — the workflow spec: `README.md`, `_mods/`, `DETACH.md`.
- **`spacedock-state/dev`** (orphan) — the entity state, checked out as a
  linked worktree at `dev/.spacedock-state`. The orphan branch has no common
  ancestor with `main`, so the state tree and the spec tree are disjoint.

One git repo (`.spacedock/repo/`), two branches, one object store:
- **`main`** — the workflow spec: `README.md`, `_mods/`, `DETACH.md`. Pushed to
  `origin/spacedock-workflow`.
- **`dev-state`** (orphan, declared via `state-branch: dev-state` in the README
  frontmatter) — the entity state, checked out as a linked worktree at
  `dev/.spacedock-state`. Pushed to `origin/dev-state`.

Remote: `origin = https://github.com/clkao/cargento`. This simulates an
outside-contributor shape: the workflow spec and the entity state are
independent branches on the upstream, so a contributor clones
`spacedock-workflow` for the spec and `dev-state` for the state separately,
and `state ready`/`state commit` pull/push the `dev-state` branch directly.

The local orphan branch is named `dev-state` (not the default
`spacedock-state/dev`) so the binary's `Publish`/`Pull` — which push/pull
`refs/heads/<StateBranch-result>` — hit `origin/dev-state`. `StateBranch`
reads the `state-branch:` override from the README frontmatter; without it
the binary would push to `origin/spacedock-state/dev`, a branch that does
not exist upstream, and `state ready` would fail to pull. The
`state-branch:` field is the one line that keeps the local branch name and
the remote state branch name aligned.

## Why separate branches (not inline)

The spec (`README.md` + `_mods`) and the entity state are on **separate
branches** in the same repo. This is not a workaround; it is load-bearing for
the detached shape.

Inline mode (`state: $inline`) puts entity files beside the README on one
branch. That is the simplest shape, and it is correct for a standalone
workflow repo that sits *inside* the code repo (the normal inline case). It
breaks here because of the `FindGitRoot` trick below: the workflow dir
(`.spacedock/dev/`) must be a **real, non-repo dir** (no `.git` at that
level) so `FindGitRoot` climbs past it to Cargento. If entity files landed
directly in `.spacedock/dev/` (inline), `state commit` would resolve the
worktree git root to Cargento (via the same `FindGitRoot` climb) and commit
the entity files to **Cargento's `main`** — the churn this layout exists to
avoid.

Split-root solves it: entity state lives on an orphan branch, checked out as
a worktree at `dev/.spacedock-state`. That worktree is a linked worktree of
`.spacedock/repo/`, so state commits land in `.spacedock/repo/`'s object
store on the orphan branch — not in Cargento. The orphan branch (no common
ancestor with `main`) keeps the state tree disjoint from the spec tree, so
spec history and state history never couple, and the state checkout contains
only entity files, not the spec.

## The two hard constraints

1. **`state:` cannot use `..`.** `status.ClassifyState` rejects any `state:`
   path with a `..` segment — it classifies such a value as inline, not
   split-root. So the state checkout must be a relative path **under** the
   workflow dir. The state worktree sits at `dev/.spacedock-state`, under
   the workflow dir `dev/`, so `state: .spacedock-state` is valid.

2. **No `.git` on the `FindGitRoot` climb path from the workflow dir to
   Cargento.** `status.FindGitRoot(workflowDir)` walks up the path stat-ing
   `d/.git` at each level and returns the first hit; it does **not** resolve
   symlinks (`filepath.Abs` is lexical). `dispatch build`/`stamp` derive the
   worktree git root from `FindGitRoot(workflowDir)`, so worktrees land
   wherever that climb stops. For worktrees to land in Cargento, the climb
   from `cargento/.spacedock/dev` must hit `cargento/.git` first. That means
   `cargento/.spacedock/dev/` is a real dir, not a git repo, and
   `cargento/.spacedock/` is not a git repo either. `.spacedock/repo/.git`
   exists but is not on the climb path (`FindGitRoot` checks `d/.git` at each
   level `d`, not recursively into subdirs), so the climb passes it and
   stops at Cargento.

## The symlink trick

The workflow spec must be readable at `.spacedock/dev/README.md` for
discovery, but `.spacedock/dev/` cannot be a git repo (constraint 2). So
`dev/README.md` and `dev/_mods` are **symlinks** into `repo/`, which is its
own git repo one dir down. Discovery reads `README.md` (follows the file
symlink); the spec is version-controlled in `repo/` on `main`; and because
symlinks are not resolved by `FindGitRoot`, the climb still stops at
Cargento.

A whole-dir symlink `dev -> repo` would be simpler but is rejected: it
would put `dev/.git` (via the symlink to `repo/.git`) on the climb path,
stopping `FindGitRoot` at `dev` (resolving to `repo`) — worktrees would
land in `repo`, not Cargento. Per-file symlinks for the spec plus a real
`dev/.spacedock-state` worktree subdir keep the climb path clean.

## Why `info/exclude` not `.gitignore`

Discovery prunes tracked-`.gitignore` patterns but does **not** prune
`.git/info/exclude`, and it does not skip untracked directories
(overlay-contribution sprint finding). So `.spacedock/` and `.worktrees/`
go in `cargento/.git/info/exclude`: they stay off Cargento's `main` branch
(zero churn) while remaining visible to the FO's `status --boot`
auto-discovery from the Cargento root.

## What works and what does not (measured on `spacedock 0.27.0-pre8+dev`)

- `status --boot` from `cargento/` root auto-discovers `.spacedock/dev`. ✓
- `status --workflow-dir .spacedock/dev --validate` → `VALID`. ✓
- `state ready` → exits 0, pulls from `origin/dev-state` (`State checkout
  ready — integrated peers' state from dev-state`). ✓
- `state commit <slug>` → commits to the `dev-state` worktree and pushes to
  `origin/dev-state` (`Committed and pushed <slug> to dev-state`). ✓
- `dispatch build --stamp` → worktrees land in `cargento/.worktrees/`
  (`FindGitRoot(.spacedock/dev)` = `cargento`). ✓ (path arithmetic confirmed;
  not yet exercised live this session.)
- `state init` on a **fresh clone** → fetches from the workflow dir's repo
  on the *default* state branch name (`spacedock-state/<basename>`), not the
  README-declared `state-branch: dev-state`. So it fails on a fresh clone
  unless the contributor manually fetches `dev-state` and adds the worktree
  (see Resuming). This is the overlay-contribution sprint's DoD-3 gap;
  closing it is a binary follow-up.

## Resuming this layout (outside-contributor simulation)

`.spacedock/repo/` is untracked from Cargento's `main` (via `info/exclude`),
so a fresh clone of Cargento has neither the spec nor the state. To rebuild
on a fresh clone (the outside-contributor path):

1. Recreate `cargento/.git/info/exclude` entries: `.spacedock/` and
   `.worktrees/`.
2. Clone the spec branch:
   `git clone -b spacedock-workflow https://github.com/clkao/cargento .spacedock/repo`
3. Create the workflow dir with symlinks to the spec:
   `mkdir -p .spacedock/dev && ln -s ../repo/README.md .spacedock/dev/README.md && ln -s ../repo/_mods .spacedock/dev/_mods`
4. Fetch the state branch and add it as a linked worktree:
   `git -C .spacedock/repo fetch origin dev-state && git -C .spacedock/repo worktree add ../dev/.spacedock-state dev-state`

This is single-machine-clone-friendly today. The binary's `state init`
still fetches from the workflow dir's repo on the *default* state branch
name, which is the overlay-contribution sprint's DoD-3 gap; the manual
`fetch origin dev-state` in step 4 works around it. Closing that gap (so
`state init` fetches the README-declared `state-branch`) is a binary
follow-up.

### Why two remote branches (spacedock-workflow + dev-state), not one

The workflow spec (`main` → `spacedock-workflow`) and the entity state
(`dev-state`) are separate branches on the same upstream repo so a
contributor can pull the spec without the (large, mutable) state history,
and push state without churning the spec branch. This mirrors the local
orphan-branch split (spec on `main`, state on the orphan) onto the remote:
two branches, one upstream repo, no PR between them — the state branch is
not a feature branch to review; it is the contributor's durable state
ledger, and `state ready`/`state commit` keep it in sync.
