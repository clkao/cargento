---
title: Pi agent view shows Spacedock state
status: backlog
source: captain seed
id: hdz7pr9bmw5vpc5ah52sbcmb
---

Cargento already derives Spacedock workflow cartography for Claude first officers — `collectors/claude.py` decides a session is a first officer from its transcript's `agentSetting`, then asks `cargento_runtime/spacedock.py` for the workflow strip. The Pi collector (`collectors/pi.py`) does not yet surface this, so a Pi first officer renders on the dashboard without the workflow context a Claude officer gets.

## Problem

A Pi first officer running `spacedock pi` writes the same durable state a Claude officer does, and Cargento's Spacedock parser is harness-agnostic, but the Pi collector never calls it. The dashboard's session card for a Pi FO omits the workflow strip the design (`docs/design-spacedock.md`, S-1..S-4) exists to provide.

## Proposed approach

{Ideation: how `collectors/pi.py` classifies a Pi session as a first officer and where `spacedock.read_workflow` plugs into the Pi collection lane, reusing the existing harness-agnostic parser.}

## Risk evidence

{Backlog: confirm a Pi FO transcript carries a discoverable first-officer marker and that `spacedock.py`'s inputs are reachable from Pi session metadata.}

## Expected surface and tolerance

Estimate: {ideation fills}
Semantics this may change: {ideation fills}

## Acceptance criteria

{Ideation: at least one AC measures the end value — a Pi FO session on the dashboard shows the same workflow strip a Claude FO session does — verified by a test or live scenario, not a grep over `pi.py` or this README.}

## Test plan

{Ideation fills.}

### Feedback Cycles

## Out of scope

- Rewriting `spacedock.py` — it is harness-agnostic by design; this task wires the Pi collector to it.
- Widening Spacedock cartography features — S-4 deliberately takes only the stage.
