---
commissioned-by: spacedock@0.27.0-pre8
entity-type: probe
entity-label: probe
entity-label-plural: probes
id-style: sd-b32
state: .spacedock-state
state-branch: explore-state
stages:
  defaults:
    worktree: false
    concurrency: 2
  states:
    - name: backlog
      initial: true
      gate: true
    - name: breadboard
      worktree: true
    - name: shaping
      worktree: true
    - name: review
      worktree: true
      fresh: true
      feedback-to: breadboard
      gate: true
    - name: done
      terminal: true
---

# Discover a trustworthy Cargento operator cockpit before committing product work

This workflow reduces product, interaction, and mechanism uncertainty outside Cargento's
development workflow. Each probe asks one consequential question, exercises the cheapest
mechanisms that can answer it, compares concrete variants, and reaches a captain-reviewed
decision. Only a probe whose approach is demonstrated and whose remaining uncertainty is
ordinary implementation detail creates a task in `.spacedock/dev`.

The shared laboratory is the rolling `proto/operator-cockpit` branch, initially based on
`clkao/cargento:proto/mirror-view`. It exists to let active probes compose. It is never a
release branch, a pull-request candidate, or something merged wholesale into `main`.

## File Naming

Each probe uses folder form: `{slug}/index.md` is the canonical entity file and small
research artifacts live beside it. Suitable sibling artifacts include static mocks,
screenshots, bounded transcripts, comparison tables, and tiny reproducible spikes.

Slugs are lowercase, hyphenated, and contain no spaces. For example:
`project-cockpit/index.md` with `project-cockpit/overview-a.html` and
`project-cockpit/overview-b.html`.

Large generated data and working code stay on the probe worktree or rolling integration
branch. The probe body records the exact commit and the small evidence needed to understand
the result after those working branches are gone.

## Schema

Every probe file has YAML frontmatter. See **Probe Template** for a copyable starter.

### Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stable SD-B32 identifier; status displays the shortest unique prefix. |
| `title` | string | Human-readable probe name. |
| `status` | enum | One of: backlog, breadboard, shaping, review, done. |
| `source` | string | Where the probe came from. |
| `started` | ISO 8601 | When active investigation began. |
| `completed` | ISO 8601 | When the probe reached `done`. |
| `verdict` | enum | PASSED or REJECTED, set at terminalization. |
| `score` | number | Priority from 0.0 to 1.0. |
| `worktree` | string | Worktree path while an ensign is active; sticky until terminalization. |
| `issue` | string | Optional GitHub issue reference. |
| `pr` | string | Normally empty; exploration does not ship through a PR. |
| `parent` | string | Optional parent probe slug when this probe was split from another. |
| `budget` | string | Captain-approved time, cost, or review-cycle boundary. |
| `integration-base` | string | Exact rolling-branch commit from which isolated probing began. |
| `integration-checkpoint` | string | Exact integrated commit evaluated at review. |
| `development-task` | string | Target development-task slug after a PASSED handoff; empty otherwise. |

### ID Style

This workflow uses `sd-b32`. `spacedock new --folder` mints a 24-character stable ID.
Status output displays and accepts the shortest unique prefix, with a minimum of two
characters. Stored identifiers do not change when another probe introduces a prefix
collision.

## Stages

### `backlog`

A probe is in backlog while the captain decides whether its uncertainty is worth spending
an investigation on. This stage frames a question, not a preferred implementation or a
fixed hypothesis.

- **Inputs:** The desired operator value, the current Cargento behavior, relevant prior
  prototypes, and the uncertainty preventing a development task from being responsibly
  specified.
- **Outputs:** A bounded question; included and excluded scope; a time, cost, or three-cycle
  budget; the cheapest evidence that could change direction; and the operator decision the
  result must eventually support.
- **Good:** The probe can fail, change direction, or conclude that no product work is
  warranted without being treated as an implementation failure.
- **Bad:** Smuggling a selected architecture into the question, commissioning a probe for
  work the development workflow already knows how to execute, or starting a worktree before
  the captain has approved the learning spend.
- **Gate content:** Show the question, scope boundary, budget, existing evidence, and why the
  answer cannot be obtained more cheaply in the development workflow.

### `breadboard`

A probe is in breadboard while an ensign maps the space and exercises the riskiest unknowns
with the cheapest concrete mechanisms available.

- **Inputs:** The approved backlog framing, the exact rolling integration baseline, relevant
  Cargento runtime and UI seams, and any prior prototype named by the probe.
- **Outputs:** A bounded mechanism survey; one or more cheap falsifying spikes; observed
  failure modes; small artifacts a captain can inspect; and an updated account of which
  choices still matter.
- **Good:** The riskiest assumption is exercised end to end before visual polish or durable
  machinery is added. A failed spike narrows the space and is useful evidence.
- **Bad:** Building production-quality code, treating a mocked interaction as behavioral
  evidence, silently choosing a direction because it was easiest to implement, or merging
  speculative bytes into `main`.

### `shaping`

A probe is in shaping while an ensign compares viable variants, records the decision
criterion that emerged from the evidence, and makes the useful composition visible on the
rolling prototype branch.

- **Inputs:** Breadboard evidence, concrete variants, the current `proto/operator-cockpit`
  head, and direct captain feedback already recorded through an approved channel.
- **Outputs:** The emerged decision criterion; a side-by-side comparison of viable variants;
  costs and tradeoffs; the selected prototype checkpoint integrated by the single-writer
  lane; and the exact integration commit with a reproducible viewing procedure.
- **Good:** A captain can experience or falsify the recommendation. The comparison explains
  why the selected variant better serves the operator value, not merely why its code is
  cleaner.
- **Bad:** Allowing parallel writers on the rolling branch, overwriting an operator-authored
  goal with inferred text, recording an integration commit that was not actually exercised,
  or declaring certainty because the implementation happens to exist.

### `review`

A probe is in review while a fresh ensign independently checks the isolated evidence and the
exact rolling-integration checkpoint, then the captain decides whether the approach is ready
for development, needs revision, should be dropped, or should remain held.

- **Inputs:** The complete probe body; every breadboard and shaping artifact; the isolated
  probe branch; the exact integration checkpoint; the current workflow README; and the
  proposed development seed when PASSED is recommended.
- **Outputs:** Evidence for every acceptance criterion; the checks actually run; a comparison
  of the selected direction with the strongest rejected alternative; remaining unknowns
  classified as implementation detail or approach-changing risk; the fact that would reverse
  the recommendation; and a PASSED or REJECTED recommendation.
- **Good:** The review can reject a visually compelling prototype for wrong-target delivery,
  fabricated state, lost persistence, security ambiguity, or failure to improve the operator's
  decision. A PASSED recommendation leaves development with execution work, not research.
- **Bad:** Trusting a shaping report without reproducing its decisive path, treating suite-green
  as proof of operator value, accepting mocked data as a working channel, or asking development
  to settle a product or architecture choice the probe left open.
- **Gate content:** Lead with the recommended captain decision; show the integrated experience,
  evidence against the decision criterion, costs, approach-changing unknowns, reversal fact,
  and the exact proposed development handoff.

### `done`

A probe is done when exploration has concluded. `verdict: PASSED` means the demonstrated
approach has created a linked seed in `.spacedock/dev`; `verdict: REJECTED` means the result
was archived as a discovery with no development task.

- **Inputs:** The captain's review decision, the exact reviewed integration checkpoint, and
  the proposed development seed for a passing probe.
- **Outputs:** An archived probe with terminal verdict and completion time; for PASSED, an
  idempotently created development task whose body links back to the probe and carries the
  chosen contracts, artifacts, evidence, rejected alternatives, and remaining implementation
  details.
- **Good:** A future reader can understand what was learned and reproduce the decisive evidence
  without assuming the rolling prototype branch still exists.
- **Bad:** Merging the rolling branch wholesale, creating a development task before the captain
  accepts the approach, deleting the only copy of a decisive artifact, or calling a dropped
  probe a failed development effort.

## Workflow-specific rules

- **Decision criterion emerges; the question does not.** Backlog fixes the question, boundary,
  budget, and operator decision to support. Breadboard and shaping may discover the criterion
  by which variants should be compared. Only the captain can approve a change to the question
  or accepted value.
- **Three review cycles maximum.** A revision returns to breadboard. On the third review cycle,
  the captain must pass, reject, or explicitly commission a narrower child probe; the workflow
  does not keep polishing indefinitely.
- **One rolling laboratory per mission.** `proto/operator-cockpit` combines active cockpit probes.
  New probe worktrees record the integration commit they started from. The rolling branch is a
  composition surface and historical laboratory, never the source of truth for decisions.
- **One integration writer.** The first officer serializes shaping completions. Only the ensign
  holding the integration lane may add the selected checkpoint to the rolling branch. Other
  probes remain isolated and record their intended checkpoint until the lane is available.
- **Review an exact commit.** A review names one immutable `integration-checkpoint`. Later rolling
  changes do not become evidence retroactively.
- **Development starts clean.** A PASSED probe creates a task in `.spacedock/dev` from the current
  `main` baseline. Its task may selectively reuse proven commits, but the rolling prototype
  branch is never merged wholesale.
- **Small artifacts remain with the probe.** Mocks, screenshots, bounded comparison data, and
  tiny spikes that explain the result live in the probe folder. Large or executable experiments
  stay in Git and are cited by exact commit.
- **Direct captain communication is judgment-only.** An ensign contacts the captain directly to
  choose among concrete visual variants, report evidence that changes the probe's meaning, obtain
  consent involving private data, external services, cost, or a live session, or conduct a live
  operator exercise that cannot be simulated. Routine status and delegated mechanics go in the
  Stage Report.
- **Use the narrowest channel that fits.** A small bounded blocking choice uses Cargento's existing
  ask lane and appears in the project-level Needs you surface beside the saved project goal. Rich
  artifact feedback uses a Subspace review. Scope, authority, open-ended clarification, and gates
  remain in the first-officer conversation. A session-origin steering channel is not trusted until
  its own probe passes review.
- **Operator text outranks inference.** A persisted goal written by the operator is never replaced
  by a transcript-derived or model-derived goal. Inference may appear as a separately labeled
  suggestion or fallback only.
- **No self-referential proof.** Re-reading this README or the probe body cannot establish an
  acceptance criterion. Evidence must come from a runnable mechanism, observable artifact,
  recorded interaction, or other falsifiable external check.

## Workflow State

The first officer discovers this workflow automatically. To inspect it directly:

```bash
spacedock status --workflow-dir .spacedock/explore
```

To find probes ready for work:

```bash
spacedock status --workflow-dir .spacedock/explore --next
```

## Probe Template

```yaml
---
id:
title: Probe name
status: backlog
source:
started:
completed:
verdict:
score:
worktree:
issue:
pr:
parent:
budget:
integration-base:
integration-checkpoint:
development-task:
---

State the consequential question in one sentence.

## Question

Name what must be learned before development can responsibly start.

## Boundaries and budget

Name included and excluded scope, the available spend, and the operator decision this probe
must support.

## Candidate directions

Record viable variants without treating the first one built as the winner.

## Evidence

Record falsifiable exercises, failures, measured costs, and links to small artifacts or exact
Git commits.

## Decision criterion

Record the measurable or judgeable criterion that emerged from the evidence and why it serves
the original operator value.

## Direct captain communication

Record each direct question, its channel, the answer, and how it changed the probe. Leave empty
when no direct judgment was required.

## Development handoff

For a passing recommendation, provide a complete development seed: chosen behavior and contracts,
relevant artifacts, rejected alternatives, security and persistence boundaries, proposed proof,
and ordinary implementation details that remain.

## Acceptance criteria

Each criterion names an exploration end-state property and an external check capable of failing.

### Feedback Cycles
```

## Commit Discipline

- Commit stage-boundary state through `spacedock state commit`.
- Commit substantive evidence and small artifacts with the probe entity.
- Commit each rolling-integration checkpoint separately and name the probe slug and review cycle.
- Never mix unrelated probe integration into one commit.
