---
title: Group and filter the session list by project
status: backlog
source: captain dogfood feedback
id: zp7z36m3am49jyqrp685nhz9
gates:
    version: 1
    records:
        - id: gate:zp7z36m3am49jyqrp685nhz9:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:zp7z36m3am49jyqrp685nhz9-backlog-1
              briefing:
                id: briefing:zp7z36m3am49jyqrp685nhz9:backlog:attempt-1:revision-1
                digest: sha256:68fa4cb3effa8122696f1f000bcff806ca965d6db554fb50c212d8c506fbaf78
                request-digest: sha256:39c3dfaaa1ea1469b26014559e550636b79beaa0e91b4357348dc82039367df0
                room-ref: ./review/backlog/briefing-1
---

With 18 sessions across cargento, subspace-ssh, subspace-v0, tycho, spacedock,
and tmp, the flat session list is hard to navigate. An operator wants to group by
or filter by project to find the sessions they care about.

## Problem

The dashboard's session list is a flat list of all sessions across all
projects. There is no way to group by project, filter to one project, or
collapse projects you don't care about. Finding the cargento sessions among 18
total requires scanning every row.

## Included scope

- A project grouping/filter control in the session list (regular and calm
  views): group sessions by project, or filter to a single project.
- The project is already derived per session (`session.project`); this is a
  display/navigation change, not a new data source.
- Persisted preference (like display mode) so a reload keeps the grouping.

## Excluded scope

- The per-session view itself (owned by `session-view-spacedock-visibility`).
- Cross-session entity state overview within a project (owned by a separate
  task).

## Proof needed to decide whether design should start

Whether `session.project` is reliably populated across all harnesses, and
whether the grouping control can reuse the existing mode-bar pattern.
