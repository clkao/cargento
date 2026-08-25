#!/usr/bin/env python3
"""Exercise opt-in delivery through two disposable tmux sessions.

This is a falsifying spike, not production code. It starts an isolated tmux
server with two receiver processes. Only one receiver gets an origin
registration. The spike then exercises exact delivery and each required
failure state without reading a harness store or an existing terminal.
"""

from __future__ import annotations

import dataclasses
import json
import os
import secrets
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Final

ACK_TIMEOUT_SEC: Final = 1.0
POLL_SEC: Final = 0.01
TEXT_CAP_CHARS: Final = 500

RECEIVER_SOURCE: Final = r"""#!/usr/bin/env python3
import json
import pathlib
import sys

capture = pathlib.Path(sys.argv[1])
receipts = pathlib.Path(sys.argv[2])
ready = pathlib.Path(sys.argv[3])
ready.touch()
for line in sys.stdin:
    envelope = json.loads(line)
    record = {"id": envelope["id"], "text": envelope["text"]}
    with capture.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, separators=(",", ":")) + "\n")
    if envelope["text"].startswith("silent:"):
        continue
    state = "rejected" if envelope["text"].startswith("reject:") else "acknowledged"
    with receipts.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"id": envelope["id"], "state": state}) + "\n")
"""


@dataclasses.dataclass(frozen=True)
class Registration:
    """One opt-in interaction origin that the browser cannot alter."""

    channel_id: str
    pane_id: str
    server_pid: str
    expires_at: float


class DisposableTmux:
    """An isolated tmux server with two line receivers."""

    def __init__(self, root: Path) -> None:
        executable = shutil.which("tmux")
        if executable is None:
            raise RuntimeError("tmux is required for this breadboard")
        self.executable = executable
        self.socket = f"cargento-breadboard-{os.getpid()}-{secrets.token_hex(4)}"
        self.root = root
        self.receiver = root / "receiver.py"
        self.receiver.write_text(RECEIVER_SOURCE, encoding="utf-8")
        self.paths = {
            name: {kind: root / f"{name}-{kind}.jsonl" for kind in ("capture", "receipts", "ready")}
            for name in ("registered", "unregistered")
        }

    def run(
        self,
        *args: str,
        input_text: str | None = None,
        timeout: float = 2.0,
    ) -> subprocess.CompletedProcess[str]:
        """Run one command against only this disposable tmux server."""
        return subprocess.run(  # noqa: S603 - executable and arguments are local constants
            [self.executable, "-L", self.socket, "-f", "/dev/null", *args],
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )

    def start(self) -> None:
        """Start two candidates and wait until both receiver loops are ready."""
        for index, name in enumerate(("registered", "unregistered")):
            paths = self.paths[name]
            command = shlex.join(
                [
                    sys.executable,
                    str(self.receiver),
                    str(paths["capture"]),
                    str(paths["receipts"]),
                    str(paths["ready"]),
                ]
            )
            verb = "new-session"
            result = self.run(verb, "-d", "-s", name, command)
            if result.returncode != 0:
                raise RuntimeError(f"candidate {index + 1} did not start: {result.stderr.strip()}")
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            if all(self.paths[name]["ready"].exists() for name in self.paths):
                return
            time.sleep(POLL_SEC)
        raise RuntimeError("the disposable receivers did not become ready")

    def pane_id(self, name: str) -> str:
        result = self.run("display-message", "-p", "-t", f"{name}:0.0", "#{pane_id}")
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        return result.stdout.strip()

    def server_pid(self) -> str | None:
        result = self.run("display-message", "-p", "#{pid}")
        return result.stdout.strip() if result.returncode == 0 else None

    def capture(self, name: str) -> list[dict[str, str]]:
        path = self.paths[name]["capture"]
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def receipt(self, name: str, message_id: str) -> dict[str, str] | None:
        path = self.paths[name]["receipts"]
        deadline = time.monotonic() + ACK_TIMEOUT_SEC
        while time.monotonic() < deadline:
            if path.exists():
                for line in path.read_text(encoding="utf-8").splitlines():
                    candidate: dict[str, str] = json.loads(line)
                    if candidate.get("id") == message_id:
                        return candidate
            time.sleep(POLL_SEC)
        return None

    def paste(self, registration: Registration, message_id: str, text: str) -> dict[str, str]:
        """Paste one JSON envelope and wait for an application receipt."""
        if self.server_pid() != registration.server_pid:
            return {"state": "unknown", "reason": "transport-disconnected"}
        buffer_name = f"cargento-{message_id}"
        envelope = json.dumps({"id": message_id, "text": text}, separators=(",", ":")) + "\n"
        loaded = self.run("load-buffer", "-b", buffer_name, "-", input_text=envelope)
        if loaded.returncode != 0:
            return {"state": "unknown", "reason": "transport-disconnected"}
        pasted = self.run(
            "paste-buffer",
            "-b",
            buffer_name,
            "-t",
            registration.pane_id,
            "-d",
        )
        if pasted.returncode != 0:
            return {"state": "unknown", "reason": "transport-disconnected"}
        receipt = self.receipt("registered", message_id)
        if receipt is None:
            return {"state": "unknown", "reason": "receipt-timeout"}
        return {"state": receipt["state"], "reason": "application-receipt"}

    def stop(self) -> None:
        """Stop only the isolated server that this object started."""
        self.run("kill-server")


class RegisteredRouter:
    """Resolve a browser request through one server-owned registration."""

    def __init__(self, transport: DisposableTmux, registration: Registration) -> None:
        self.transport = transport
        self.registration = registration
        self.sequence = 0

    def replace_registration(self, registration: Registration) -> None:
        self.registration = registration

    def deliver(self, request: dict[str, Any], *, now: float) -> dict[str, str]:
        """Refuse invalid origins before the transport receives any bytes."""
        if set(request) != {"channel_id", "text"}:
            return {"state": "refused", "reason": "malformed-request"}
        channel_id = request["channel_id"]
        text = request["text"]
        if not isinstance(channel_id, str) or not isinstance(text, str):
            return {"state": "refused", "reason": "malformed-request"}
        if len(text) > TEXT_CAP_CHARS:
            return {"state": "refused", "reason": "text-too-large"}
        if channel_id != self.registration.channel_id:
            return {"state": "refused", "reason": "unregistered-origin"}
        if now >= self.registration.expires_at:
            return {"state": "refused", "reason": "stale-registration"}
        self.sequence += 1
        message_id = f"m{self.sequence}"
        result = self.transport.paste(self.registration, message_id, text)
        return {"id": message_id, **result}


def _case(
    name: str,
    outcome: dict[str, str],
    *,
    expected_state: str,
    expected_reason: str,
    details: dict[str, Any],
) -> dict[str, Any]:
    if outcome.get("state") != expected_state or outcome.get("reason") != expected_reason:
        raise AssertionError(f"{name}: unexpected outcome {outcome}")
    return {"case": name, "outcome": outcome, **details}


def exercise() -> dict[str, Any]:
    """Run the required cases and return a small, path-free result record."""
    with tempfile.TemporaryDirectory(prefix="cargento-origin-breadboard-") as temporary:
        tmux = DisposableTmux(Path(temporary))
        tmux.start()
        try:
            now = time.time()
            registration = Registration(
                channel_id=secrets.token_urlsafe(16),
                pane_id=tmux.pane_id("registered"),
                server_pid=tmux.server_pid() or "",
                expires_at=now + 60.0,
            )
            router = RegisteredRouter(tmux, registration)
            cases: list[dict[str, Any]] = []

            acknowledged_text = "alpha text: [] {} / spaces"
            acknowledged = router.deliver(
                {"channel_id": registration.channel_id, "text": acknowledged_text}, now=now
            )
            cases.append(
                _case(
                    "acknowledged",
                    acknowledged,
                    expected_state="acknowledged",
                    expected_reason="application-receipt",
                    details={
                        "registered_text_intact": tmux.capture("registered")[-1]["text"]
                        == acknowledged_text,
                        "unregistered_candidate_delivered_bytes": sum(
                            len(item["text"].encode()) for item in tmux.capture("unregistered")
                        ),
                    },
                )
            )

            before = tmux.capture("unregistered")
            unregistered = router.deliver(
                {"channel_id": "candidate-two", "text": "must not arrive"}, now=now
            )
            cases.append(
                _case(
                    "unregistered target",
                    unregistered,
                    expected_state="refused",
                    expected_reason="unregistered-origin",
                    details={
                        "unregistered_candidate_delivered_bytes": sum(
                            len(item["text"].encode()) for item in tmux.capture("unregistered")
                        ),
                        "capture_unchanged": tmux.capture("unregistered") == before,
                    },
                )
            )

            rejected_text = "reject: session policy"
            rejected = router.deliver(
                {"channel_id": registration.channel_id, "text": rejected_text}, now=now
            )
            cases.append(
                _case(
                    "rejected",
                    rejected,
                    expected_state="rejected",
                    expected_reason="application-receipt",
                    details={
                        "registered_text_intact": tmux.capture("registered")[-1]["text"]
                        == rejected_text
                    },
                )
            )

            silent_text = "silent: no receipt"
            no_receipt = router.deliver(
                {"channel_id": registration.channel_id, "text": silent_text}, now=now
            )
            cases.append(
                _case(
                    "acknowledgement path removed",
                    no_receipt,
                    expected_state="unknown",
                    expected_reason="receipt-timeout",
                    details={
                        "registered_text_intact": tmux.capture("registered")[-1]["text"]
                        == silent_text
                    },
                )
            )

            marker = Path(temporary) / "shell-interpolation-must-not-run"
            adversarial_text = f"literal; $(touch {marker}); `touch {marker}` && touch {marker}"
            before_count = len(tmux.capture("registered"))
            locator_attack = router.deliver(
                {
                    "channel_id": registration.channel_id,
                    "text": adversarial_text,
                    "target": f"unregistered:0.0; touch {marker}",
                },
                now=now,
            )
            cases.append(
                _case(
                    "browser supplies a terminal locator",
                    locator_attack,
                    expected_state="refused",
                    expected_reason="malformed-request",
                    details={
                        "registered_capture_delta": len(tmux.capture("registered")) - before_count,
                        "shell_command_ran": marker.exists(),
                    },
                )
            )

            literal = router.deliver(
                {"channel_id": registration.channel_id, "text": adversarial_text}, now=now
            )
            cases.append(
                _case(
                    "shell metacharacters are literal application data",
                    literal,
                    expected_state="acknowledged",
                    expected_reason="application-receipt",
                    details={
                        "registered_text_intact": tmux.capture("registered")[-1]["text"]
                        == adversarial_text,
                        "shell_command_ran": marker.exists(),
                    },
                )
            )

            stale_registration = dataclasses.replace(registration, expires_at=now - 1.0)
            router.replace_registration(stale_registration)
            before_count = len(tmux.capture("registered"))
            stale = router.deliver(
                {"channel_id": registration.channel_id, "text": "must stay stale"}, now=now
            )
            cases.append(
                _case(
                    "stale registration",
                    stale,
                    expected_state="refused",
                    expected_reason="stale-registration",
                    details={
                        "registered_capture_delta": len(tmux.capture("registered")) - before_count
                    },
                )
            )

            live_registration = dataclasses.replace(registration, expires_at=now + 60.0)
            router.replace_registration(live_registration)
            tmux.run("kill-pane", "-t", live_registration.pane_id)
            before_count = len(tmux.capture("registered"))
            disconnected = router.deliver(
                {"channel_id": registration.channel_id, "text": "must not claim success"}, now=now
            )
            cases.append(
                _case(
                    "transport disconnected",
                    disconnected,
                    expected_state="unknown",
                    expected_reason="transport-disconnected",
                    details={
                        "registered_capture_delta": len(tmux.capture("registered")) - before_count
                    },
                )
            )

            if any(
                item.get("registered_text_intact") is False
                or item.get("capture_unchanged") is False
                or item.get("shell_command_ran") is True
                or item.get("registered_capture_delta", 0) != 0
                or item.get("unregistered_candidate_delivered_bytes", 0) != 0
                for item in cases
            ):
                raise AssertionError("a byte-integrity or isolation assertion failed")
            version = subprocess.run(  # noqa: S603 - resolved local executable, fixed argument
                [tmux.executable, "-V"],
                text=True,
                capture_output=True,
                check=True,
                timeout=2.0,
            ).stdout.strip()
            return {
                "artifact": "session interaction origin breadboard",
                "tmux_version": version,
                "candidate_sessions": 2,
                "registered_sessions": 1,
                "cases": cases,
            }
        finally:
            tmux.stop()


def main(argv: list[str]) -> int:
    output = exercise()
    rendered = json.dumps(output, indent=2, sort_keys=True) + "\n"
    if len(argv) == 3 and argv[1] == "--output":
        Path(argv[2]).write_text(rendered, encoding="utf-8")
    elif len(argv) == 1:
        sys.stdout.write(rendered)
    else:
        raise SystemExit("usage: session-interaction-origin-breadboard.py [--output PATH]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
