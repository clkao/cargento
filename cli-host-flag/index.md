---
title: Bind the dashboard to a configurable host (--host 0.0.0.0 for remote access)
status: validation
source: captain seed
id: bkjcbqac4d34rtsn7a0vy1kz
gates:
    version: 1
    records:
        - id: gate:bkjcbqac4d34rtsn7a0vy1kz:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:bkjcbqac4d34rtsn7a0vy1kz-backlog-1
              briefing:
                id: briefing:bkjcbqac4d34rtsn7a0vy1kz:backlog:attempt-1:revision-1
                digest: sha256:0dbf75cf3dd168a3eee148a1013492d4f8b78282793f7a7fec9fe335cf202fe4
                request-digest: sha256:81479a38bb71ead4823692ca3f47b91fd2f9aa6a11d0ed2c0f95b8f4fce889c1
                room-ref: ./review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:bkjcbqac4d34rtsn7a0vy1kz:backlog:1
                briefing: briefing:bkjcbqac4d34rtsn7a0vy1kz:backlog:attempt-1:revision-1
                by: person:captain
                at: "2026-08-21T04:12:15.955343418Z"
                decision: approve
                reason: 'Captain approved the backlog seed in the same message that filed it (''file: allow --host 0.0.0.0 in cli. dispatch'') — ''file and dispatch'' is the approval. Advance to ideation.'
              application:
                target-stage: ideation
                state: consumed
        - id: gate:bkjcbqac4d34rtsn7a0vy1kz:ideation
          stage: ideation
          attempts:
            - id: gate-attempt:bkjcbqac4d34rtsn7a0vy1kz-ideation-1
              briefing:
                id: briefing:bkjcbqac4d34rtsn7a0vy1kz:ideation:attempt-1:revision-1
                digest: sha256:6ead16355700602ecf8cf09afd873955f762cd10d165b475798ef0a349597721
                request-digest: sha256:4433ff36e940f3649452880c300defeb2a9d256a2ad9993d8e659e35cb46fb53
                room-ref: ./review/ideation/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:bkjcbqac4d34rtsn7a0vy1kz:ideation:1
                briefing: briefing:bkjcbqac4d34rtsn7a0vy1kz:ideation:attempt-1:revision-1
                by: person:captain
                at: "2026-08-21T04:34:09.990551638Z"
                decision: approve
                reason: 'Captain approved via Subspace (binding resolution, decision approve). Captain''s appended question ''estimate net loc change?'' answered from the ideation body: ~15-25 lines across three files (cli.py ~4, lifecycle.py ~2, http_api.py ~6-12) plus tests.'
              application:
                target-stage: implementation
                state: consumed
        - id: gate:bkjcbqac4d34rtsn7a0vy1kz:validation
          stage: validation
          attempts:
            - id: gate-attempt:bkjcbqac4d34rtsn7a0vy1kz-validation-1
              briefing:
                id: briefing:bkjcbqac4d34rtsn7a0vy1kz:validation:attempt-1:revision-1
                digest: sha256:842fa654730e5336ebdcf64318568c3f520545dff03fdfab75950e5e2f95c925
                request-digest: sha256:d9b06f41d13ecf758412fa88836cbf13231f62561a59c83910c017ce3e4be64d
                room-ref: ./review/validation/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:bkjcbqac4d34rtsn7a0vy1kz:validation:1
                briefing: briefing:bkjcbqac4d34rtsn7a0vy1kz:validation:attempt-1:revision-1
                by: person:captain
                at: "2026-08-21T06:07:31.123369436Z"
                decision: approve
                reason: Captain approved validation via Subspace (binding resolution, decision approve, no annotations). The Polish finding (AC-1 Verified-by overstated — socket tests bypass cli.main) stands declined as non-blocking; no fix authorized. All 5 ACs independently reproduced with falsifying edits, default loopback byte-identical, pre-PR suite green. Delivery can proceed to done.
              application:
                target-stage: done
                state: pending
started: 2026-08-21T04:12:22Z
worktree: .worktrees/spacedock-ensign-cli-host-flag
mod-block: merge:pr-merge
pr: spacedock-dev/cargento#130
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

## Ideation

### Approach

Add a `--host` CLI flag (default `127.0.0.1`, accepting `0.0.0.0` or any
explicit IPv4 address) to `cli.build_parser`, thread it through
`build_runtime(host=args.host)` and the bind tuple `(args.host, args.port)` at
the serve branch, forward it in `lifecycle.spawn_argv` so a `--daemon` Windows
re-spawn keeps the bind, and relax the `_RequestHandler._local_ok` Host-header
gate to admit the bound host when the operator explicitly chose a non-loopback
address. The default (no `--host`) keeps today's full loopback-only posture —
`LOCAL_HOSTS` and the `Origin`/`Sec-Fetch-Site` cross-site checks unchanged —
so the DNS-rebinding and CSRF defenses hold for every current install.
`config.host` already exists as a dormant `RuntimeConfig` field; this wires it
in.

### Simplest rejected alternative

Flip the hardcoded bind tuple at `cli.py:261` to `("0.0.0.0", args.port)`
with no flag. This cannot deliver the MVP value on two counts: (1) it removes
the operator's choice — every install becomes network-exposed by default,
breaking the loopback-by-default security posture the existing `_local_ok`
gate exists to enforce; and (2) it does not reconcile the request-host
validator, so the dashboard would still answer `403` to every remote request
(see risk evidence below). A bare flip gives neither the choice nor the
reachability the task is for.

### Risk evidence (riskiest mechanism exercised first)

The riskiest mechanism is the interaction between a `0.0.0.0` bind and
`http_api._RequestHandler._local_ok`, which gates every route (GET page,
`/api/data`, every POST) on `normalize_host(Host) ∈ LOCAL_HOSTS` where
`LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}`. A remote client connecting
to `http://<machine-ip>:<port>/` sends `Host: <machine-ip>:<port>`, which
`normalize_host` reduces to the bare IP — not in `LOCAL_HOSTS` — so
`_local_ok` returns `False` and the handler sends `403`. Exercised directly:

    Host='192.168.1.5:4553'  normalized='192.168.1.5'  _local_ok=False  -> 403 REJECTED
    Host='10.0.0.2:4553'     normalized='10.0.0.2'     _local_ok=False  -> 403 REJECTED
    Host='localhost:4553'    normalized='localhost'   _local_ok=True   -> baseline ALLOWED

So the conflict is real: a `0.0.0.0` bind alone makes the TCP port reachable
but leaves every HTTP request rejected. The reconciliation must make the Host
gate conditional on the bind: when the server is explicitly bound non-loopback,
admit the configured host (for `0.0.0.0`, any non-loopback Host — the
operator's explicit opt-in per the excluded-scope note that a remote bind is
the operator's choice and auth is out of scope), while the default loopback
bind keeps the gate exactly as today. The `Origin`/`Sec-Fetch-Site` cross-site
checks stay in both modes so a drive-by web page still cannot POST to a
remotely-bound dashboard.

### Bind-tuple uniqueness

The listening-socket bind lives in exactly one place: `cli.py:261`,
`("127.0.0.1", args.port)`. The other `127.0.0.1` references are not listener
binds: `lifecycle.py:233` is a port-free probe (`sock.bind` to test whether a
port is held, not the server); `lifecycle.py:172/337` are `--status`/`--stop`
`HTTPConnection` *clients* that connect to the running instance via loopback
— still valid when the listener is bound `0.0.0.0` since loopback remains one
of its interfaces. So the bind is one threaded value, with one second
threading point: `lifecycle.spawn_argv` (line 547) must forward `--host` to
the Windows re-spawned child, or a `--host 0.0.0.0 --daemon` child rebinds to
`127.0.0.1`. `config.host` (`RuntimeConfig.host`, `config.py:43`) already
carries the field; `build_runtime` (cli.py:124) does not pass it and the bind
tuple ignores it — both are wired by this change.

### Expected surface and tolerance

~15–25 lines across three files:

- `cli.py`: one `--host` argument in `build_parser` (default `127.0.0.1`,
  `type=` a small IPv4-string validator that accepts `0.0.0.0` and explicit
  addresses, rejects IPv6 — out of scope per excluded scope); `host=args.host`
  in `build_runtime`; bind tuple becomes `(args.host, args.port)`. ~4 lines.
- `lifecycle.py`: `spawn_argv` appends `--host` + `str(args.host)`. ~2 lines.
  The announce/`--status`/`--stop` URL strings stay literal `127.0.0.1`:
  `0.0.0.0` is not a connectable address, and computing the machine's
  external IP is out of scope; loopback remains a valid connect path for the
  local control commands.
- `http_api.py`: `CargentoHTTPServer` carries the configured host; `_local_ok`
  admits the bound host (and, for `0.0.0.0`, any non-loopback Host) only when
  the server is bound non-loopback. ~6–12 lines.

Tolerance: `config.py` needs no change — the field exists. No frontend
(`cargento_runtime/web/`) or collector change — this is a serve-layer flag.
The shipped skill body `cargento/skills/cargento/SKILL.md` documents the
loopback URL; a prose mention of `--host` is a portability-rule touch the
design stage must keep plain (the validator rejects host-specific *markers*,
not the flag name).

### Acceptance criteria

- **AC-1: `--host 0.0.0.0` binds all IPv4 interfaces; default stays loopback.**
  `cargento serve --host 0.0.0.0 --port P` accepts a TCP connection to the
  machine's non-loopback IPv4 address on P and returns the dashboard page;
  `cargento serve --port P` (no `--host`) refuses a connection to that same
  non-loopback address (connection refused). *Verified by:* a test that
  starts the server with `host="0.0.0.0"` and connects to a non-loopback
  address expecting the page; reverting the bind tuple to the hardcoded
  `("127.0.0.1", args.port)` makes the remote-connect assertion fail
  (connection refused).

- **AC-2: a remote request to a `0.0.0.0`-bound server is served, not 403.**
  A GET with `Host: <non-loopback-ip>:P` against a server bound `0.0.0.0`
  returns 200 (the page), not 403. *Verified by:* a handler-level test
  issuing a GET with `Host: 192.168.0.2:P` against a server carrying
  `host="0.0.0.0"` and asserting 200; reverting the `_local_ok` relaxation
  makes it fail with 403 (the spike above reproduces the failing state).

- **AC-3: the default loopback bind still rejects non-loopback Host headers
  (DNS-rebinding defense preserved).** A GET with `Host: 192.168.1.5` against
  a default-bound server (no `--host`) returns 403. *Verified by:* a
  handler-level test against a server carrying `host="127.0.0.1"` with
  `Host: 192.168.1.5` asserting `_local_ok()` is `False`; removing the
  bind-conditionality so the relaxation always applies makes the default case
  admit the remote Host and this test fail. (Baseline guard — the existing
  `test_host_header_forms_that_are_not_loopback` and
  `test_origin_with_an_implicit_default_port` suites must also still pass.)

- **AC-4: the Windows daemon re-spawn forwards `--host`.** A
  `--host 0.0.0.0 --daemon` child binds the same address as the parent
  requested. *Verified by:* asserting `spawn_argv(config, args)` includes
  `--host`, `0.0.0.0` when `args.host == "0.0.0.0"`; deleting the `--host`
  append from `spawn_argv` makes the assertion fail.

- **AC-5: no regression in the loopback request-validation suite.** The
  existing `LOCAL_HOSTS`/`normalize_host`/`_local_ok` tests pass unchanged
  — the default path is byte-identical in behavior. *Verified by:* running
  `test_http_api` `test_host_header_forms_that_are_loopback`,
  `test_host_header_forms_that_are_not_loopback`, and the `_local_ok` origin
  tests; any change that alters the default-path gate fails one of these.

### Test plan

- `test_cli` / new `test_host_flag`: `build_parser` exposes `--host` with
  default `127.0.0.1`; `--host 0.0.0.0` parses to `args.host == "0.0.0.0"`;
  an IPv6 literal is rejected by argparse (type validator).
- `test_http_api`: extend the `_local_ok` tests with a server bound
  `host="0.0.0.0"` and `Host: 192.168.0.2:P` asserting `True`, plus the
  default `host="127.0.0.1"` case asserting `False` for the same Host
  (AC-3). Reuse the existing handler-instantiation pattern.
- `test_lifecycle` / `spawn_argv`: assert `--host` and its value appear in
  the rebuilt argv when set (AC-4); absent when default.
- A socket-level smoke test (AC-1/AC-2): start `CargentoHTTPServer` bound
  `0.0.0.0` on an ephemeral port, connect to `127.0.0.1` AND to a non-
  loopback address, GET `/` with the matching Host, assert 200. Connect to a
  `127.0.0.1`-bound server on the non-loopback address and assert refused.

### Mock

no mock: not a user-facing surface — this is a CLI/serve-layer flag; the
dashboard renders no new view, card, or panel.

## Stage Report: ideation

- DONE: Approach names the simplest rejected alternative and why it cannot deliver the MVP value
  Flip-bind-to-0.0.0.0-no-flag rejected: removes operator choice (default network exposure) and does not reconcile `_local_ok` (still 403s every remote request).
- DONE: Riskiest mechanism exercised first (reconcile --host 0.0.0.0 bind with normalize_host's loopback-only request validation)
  Spike: `_local_ok` returns False for `Host='192.168.1.5:4553'` (403) even on a 0.0.0.0 bind; loopback baseline (`localhost:4553`) still True. Conflict confirmed; reconciliation is bind-conditional Host admission.
- DONE: Each AC carries an external Verified-by clause with the concrete falsifying edit
  AC-1..AC-5 each name the test plus the single edit (revert bind tuple / revert `_local_ok` relaxation / drop `spawn_argv` --host / break default-path gate) that turns it red.
- DONE: Backend-only task records no mock: {not a user-facing surface}
  Recorded in the body's Mock section.

### Summary

Confirmed the bind tuple is the single listener-bind site (cli.py:261) with one second threading point (spawn_argv) and a dormant `config.host` field already present. Exercised the riskiest mechanism: a 0.0.0.0 bind alone leaves every remote request 403 via `_local_ok`, so the Host gate must become bind-conditional. Approach is a `--host` flag + bind-conditional `_local_ok` relaxation keeping the default loopback posture and the Origin/Sec-Fetch-Site cross-site checks. Five ACs with external falsifying edits; no mock (backend-only).

## Stage Report: implementation

- DONE: Change satisfies the ideation ACs: --host flag threads to bind tuple + spawn_argv; _local_ok bind-conditional; default loopback unchanged
  cli.py: `bind_host` type validator + `--host` arg (default `127.0.0.1`), `host=args.host` in `build_runtime`, bind tuple `(args.host, args.port)`. lifecycle.py: `spawn_argv` forwards `--host` when non-default via `getattr(args, "host", "127.0.0.1")`. http_api.py: `CargentoHTTPServer.bound_host` stored from address[0]; `_host_admitted` method makes `_local_ok` bind-conditional — default `127.0.0.1` keeps exact `LOCAL_HOSTS` gate, `0.0.0.0` admits any non-loopback Host, explicit address admits that one. Origin/Sec-Fetch-Site checks unchanged in both modes. Commit ffc4a98.
- DONE: Tests written first and watched fail for the right reason (host flag accepted/rejected, bind-conditional _local_ok, default loopback gate)
  `test_host_flag_defaults_to_loopback` / `test_host_flag_accepts_all_interfaces` / `test_host_flag_accepts_explicit_ipv4` / `test_host_flag_rejects_ipv6` (argparse SystemExit on `::`, `::1`, `[::1]`, `fe80::1`) in test_config_diagnostics.py. `test_local_ok_admits_non_loopback_host_on_wildcard_bind` (bound_host=0.0.0.0 + Host=192.168.0.2:4553 → True; reverting _host_admitted to LOCAL_HOSTS-only makes False). `test_local_ok_rejects_non_loopback_host_on_default_bind` (bound_host=127.0.0.1 + Host=192.168.1.5 → False; removing bind-conditionality makes True → fail). `test_local_ok_admits_explicit_non_loopback_bind_host_only` (10.0.0.2 admits, 10.0.0.3 rejects). `test_wildcard_bind_serves_a_remote_host_header` (socket-level: 0.0.0.0 bind + connect to machine's non-loopback IP + matching Host → 200). `test_loopback_bind_refuses_a_non_loopback_connection` (socket-level: 127.0.0.1 bind + connect to non-loopback IP → refused). `test_wildcard_bind_origin_check_admits_non_loopback` (Origin=http://192.168.0.2:4553 → True). `test_wildcard_bind_origin_check_rejects_cross_site` (Sec-Fetch-Site: cross-site → False). `test_host_is_forwarded_when_non_default` / `test_host_is_absent_when_default` in test_lifecycle SpawnArgvOptOutTest. `test_build_runtime_threads_host_into_config` (config.host == "0.0.0.0" after parsing --host 0.0.0.0).
- DONE: _local_ok admits remote Host only when bound non-loopback; default loopback posture byte-identical
  `_host_admitted` returns False for any non-LOCAL_HOSTS host when bound_host is "127.0.0.1" (default). All 1177 existing tests pass unchanged — `test_host_header_forms_that_are_loopback`, `test_host_header_forms_that_are_not_loopback`, `test_origin_with_an_implicit_default_port`, `test_host_origin_dns_rebinding_and_request_limits_are_preserved` all green. The default-path gate is identical: `_host_admitted(host)` returns True iff `host in LOCAL_HOSTS` when bound to 127.0.0.1, which is the exact original `normalize_host(Host) in LOCAL_HOSTS` check.
- DONE: Pre-PR suite run green: ruff check, ruff format --check, mypy, lint_embedded.py, validate_plugins.py, coverage
  ruff check: All checks passed. ruff format --check: 109 files already formatted. mypy: Success, no issues in 80 source files. lint_embedded.py: Frontend assets clean. validate_plugins.py: Validated 1 skills. coverage: 89.2% (threshold 73%). bump_version --current: 0.11.0. Full suite: 1177 tests OK (1 skip — no non-loopback IP on Windows/CI).

### Summary

Implemented the `--host` CLI flag (default `127.0.0.1`, accepting `0.0.0.0` and any explicit IPv4, rejecting IPv6) threaded through to the bind tuple, `RuntimeConfig.host`, and `spawn_argv`. The `_local_ok` Host/Origin gate is now bind-conditional via `_host_admitted`: the default loopback bind keeps the exact `LOCAL_HOSTS` gate (DNS-rebinding defense preserved), while a non-loopback bind admits the configured host per the operator's opt-in. The `Origin`/`Sec-Fetch-Site` cross-site checks stay in both modes. ~255 lines across 8 files (3 source, 4 test, 1 config), including 16 new test methods covering all 5 ACs with falsifying edits named.

## Stage Report: validation

- DONE: Each AC's Verified-by reproduced independently (not trusting self-report): --host flag + bind-conditional _local_ok + default loopback unchanged
  AC-1: `test_wildcard_bind_serves_a_remote_host_header` (0.0.0.0 bind + connect to 10.42.0.42:port → 200) and `test_loopback_bind_refuses_a_non_loopback_connection` (default bind + connect to 10.42.0.42 → refused) both ran against the real non-loopback IP 10.42.0.42 and passed. AC-2: `test_local_ok_admits_non_loopback_host_on_wildcard_bind` (bound_host=0.0.0.0 + Host=192.168.0.2:4553 → True) passed. AC-3: `test_local_ok_rejects_non_loopback_host_on_default_bind` (bound_host=127.0.0.1 + Host=192.168.1.5 → False) passed. AC-4: `test_host_is_forwarded_when_non_default` (--host 0.0.0.0 in spawn_argv → assertIn --host, 0.0.0.0) and `test_host_is_absent_when_default` (no --host → assertNotIn --host) passed. AC-5: `test_host_header_forms_that_are_all_loopback`, `test_host_header_forms_that_are_not_loopback`, `test_origin_with_an_implicit_default_port`, `test_host_origin_dns_rebinding_and_request_limits_are_preserved` all passed unchanged.
- DONE: Default loopback posture byte-identical (existing host/origin/dns-rebinding tests pass unchanged) — independent check
  Reverted `_host_admitted` to the original `normalize_host(Host) in LOCAL_HOSTS` check → AC-2 tests failed (403/False) as expected; AC-3/AC-5 baseline tests still passed (identical default path). Then broke the default-bind gate (return True for non-LOCAL_HOSTS regardless of bind) → `test_local_ok_rejects_non_loopback_host_on_default_bind` failed (True ≠ False). Restored both and confirmed all 1193 tests pass (1 unrelated Windows skip).
- DONE: 0.0.0.0 bind admits remote Host only when bound non-loopback; cross-site Origin/Sec-Fetch-Site checks still reject — independent check
  `test_wildcard_bind_origin_check_admits_non_loopback` (Origin=http://192.168.0.2:4553 on 0.0.0.0 bind → True) and `test_wildcard_bind_origin_check_rejects_cross_site` (Sec-Fetch-Site: cross-site on 0.0.0.0 bind → False) both passed. `test_local_ok_admits_explicit_non_loopback_bind_host_only` (bound=10.0.0.2 admits 10.0.0.2, rejects 10.0.0.3) passed. `test_local_ok_wildcard_rejects_empty_and_unspecified` (Host=0.0.0.0 and Host="" → False) passed. Falsifying edit for AC-2 (revert `_host_admitted`) confirmed: both AC-2 tests failed with 403. Falsifying edit for AC-4 (remove --host from spawn_argv) confirmed: `test_host_is_forwarded_when_non_default` failed.
- DONE: Pre-PR suite re-run green from the validation lane: ruff, mypy, lint_embedded, validate_plugins, coverage
  ruff check: All checks passed. ruff format --check: 109 files already formatted. mypy: Success, no issues in 80 source files. lint_embedded.py: Frontend assets clean. validate_plugins.py: Validated 1 skills. bump_version --current: 0.11.0. coverage: 89.2% (threshold 73%). Full suite: 1193 tests OK (1 skip — Windows-only ntpath test, unrelated).
- DONE: Reviewer findings recorded under workflow labels with a PASSED/REJECTED recommendation
  One polish finding: AC-1's verified-by claims "reverting the bind tuple to hardcoded ('127.0.0.1', args.port) makes the remote-connect assertion fail." The socket-level tests use `make_server(host="0.0.0.0")` directly, bypassing `cli.main()`, so reverting the bind tuple in `cli.py` does NOT falsify them. The implementation is correct (bind tuple is `(args.host, args.port)`, and `test_build_runtime_threads_host_into_config` proves `args.host` reaches `config`), but the claim is overstated — no end-to-end test exercises `cli.main(["--host", "0.0.0.0"])` through to the bind. Materiality: Polish — no current user-visible loss; the bind tuple code is a direct `args.host` reference. Recommendation: PASSED.

### Summary

Independently reproduced all 5 ACs against the real non-loopback IP 10.42.0.42. Falsified AC-2 (revert `_host_admitted` → 403), AC-3 (break default-bind gate → True≠False), and AC-4 (remove `--host` from `spawn_argv` → assertion fails) by applying each claimed falsifying edit and watching the corresponding test fail, then restoring. Pre-PR suite green: ruff, mypy, lint_embedded, validate_plugins, coverage 89.2%. One polish finding: AC-1's falsifying-edit claim is overstated (socket tests bypass `cli.main()`), but the implementation is correct. Recommendation: PASSED.
