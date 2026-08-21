---
title: Bind the dashboard to a configurable host (--host 0.0.0.0 for remote access)
status: backlog
source: captain seed
id: bkjcbqac4d34rtsn7a0vy1kz
---

An operator running the Cargento dashboard on a shared or remote machine cannot
make it reachable from another host: the server binds `127.0.0.1` only
(`cli.py` hardcodes `("127.0.0.1", args.port)` at the serve branch), and there is
no `--host` flag to ask for any other bind address. The end value: an operator
can run `cargento serve --host 0.0.0.0` and reach the dashboard from another
machine on the network (a remote dev box, a browser on a phone, a shared
workstation), not just localhost.

## Problem

The dashboard server is loopback-only by construction. An operator who wants to
view it from another machine has no supported way to do so — the bind address is
not exposed by the CLI. `0.0.0.0` is a one-line change at the bind tuple, but
the CLI exposes no flag to request it, and the validator's stance on a non-
loopback bind (`http_api.normalize_host` rejects `localhost`/`::1` as non-local
on the request side) needs to be reconciled with binding all interfaces.

## Included scope

- A `--host` CLI flag in `cli.py` (default `127.0.0.1`, accepting `0.0.0.0` and
  any explicit IPv4 address), threaded through to the bind tuple at the serve
  branch.
- Reconcile bind-host with the request-host validator: binding `0.0.0.0` must
  not break the loopback-only request validation that exists today.

## Excluded scope

- IPv6 binds (`::` / `::1`) — follow-up; IPv4-only matches the existing server.
- Authentication or access control for a remotely-bound dashboard — a `0.0.0.0`
  bind is the operator's explicit choice; this task does not add auth.

## Proof needed to decide whether design should start

Whether the bind tuple is the only place `127.0.0.1` is hardcoded (so the change
is genuinely one flag + one threaded value), and whether `normalize_host`'s
rejection of non-local request hosts conflicts with serving on `0.0.0.0` (a
risk to exercise at ideation, not a blocker for the seed).
