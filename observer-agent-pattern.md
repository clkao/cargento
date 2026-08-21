---
title: Observer agent pattern beside an active session
status: backlog
source: captain seed
id: 9t63gp52zec23rh0k9t160ft
---

An active coding session accumulates context a bystander cannot easily recover: what it set out to do, what it decided, where it got stuck, what it is doing right now. An observer agent — a separate agent that sits beside an active session, reads its transcript read-only, and derives its goal and the important things (decisions, blocks, in-flight work) — would let an operator ask "what is this session for and what matters in it right now?" without interrupting the session or relying on its self-report.

## Problem

There is no pattern for an agent that passively observes another active session and produces a durable, queryable summary of its goal and salient facts. Cargento already reads session transcripts read-only (the collectors), and Spacedock already derives workflow state from durable files — but neither derives a goal/salience summary from a live transcript. This task designs the observer pattern: where it reads, what it derives, how it stays read-only, and how its output is consumed.

## Proposed approach

{Ideation: the observer is a read-only agent that reads the observed session's transcript via the same bounded, freshness-windowed reads Cargento collectors use, derives a goal line (from the session's opening directive, its workflow/roadmap context, or its in-flight entity titles) and a salience set (decisions, blocks, current stage, open findings), and writes its output to a durable sidecar. Decide: dispatched ensign, standing background agent, or Cargento-side analyzer in `transcripts.py`. The riskiest mechanism is deriving a goal that is not fabricated when the transcript carries none — exercise that first.}

## Risk evidence

{Backlog: confirm a read-only agent can read another session's transcript without joining it, and that the "derive a goal, do not fabricate one" failure mode is exercisable before building.}

## Expected surface and tolerance

Estimate: {ideation fills}
Semantics this may change: {ideation fills}

## Acceptance criteria

{Ideation: at least one AC measures the end value — an observer attached to a known session produces a goal line and salience set matching the session's actual stated objective and in-flight work, verified by a live scenario with a negative case (a session with no stated goal produces "no goal derived", not a hallucinated one). One AC proves the observer never mutates the observed session's repo/state.}

## Test plan

{Ideation fills.}

### Feedback Cycles

## Out of scope

- Making the observer write to the observed session's workflow state — it is read-only; its output is a sidecar.
- Replacing Cargento's existing collectors — the observer is a new pattern, not a refactor.
- Real-time streaming of the observer's output — follow-up.
