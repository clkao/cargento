"""Real-source project observer and gate/steering history."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from cargento_runtime import project_context
from cargento_runtime.config import build_runtime_config
from cargento_runtime.state import build_runtime_state


def message(msg_id: str, text: str, timestamp: str) -> str:
    return json.dumps(
        {
            "type": "message",
            "id": msg_id,
            "timestamp": timestamp,
            "message": {"role": "user", "content": text},
        }
    )


class ProjectContextTest(unittest.TestCase):
    NOW = 1_800_000_000.0
    SID = "project-session"

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.workflow = self.root / "workflow"
        self.entity_dir = self.workflow / ".spacedock-state"
        self.workflow.mkdir()
        self.entity_dir.mkdir()
        (self.workflow / "README.md").write_text(
            "---\ncommissioned-by: spacedock@0.27.0\ntitle: Ship project cockpit\n"
            "stages:\n  states:\n    - name: shaping\n    - name: review\n---\n",
            encoding="utf-8",
        )
        self.transcript = self.root / "session.jsonl"
        self._write_transcript("Follow the captain revision", "2026-08-24T20:00:00Z")
        self.entity = self.entity_dir / "project-cockpit.md"
        self._write_gate("2026-08-24T20:05:00Z", "approve")
        os.utime(self.entity, (self.NOW, self.NOW))
        self.config = build_runtime_config(
            environ={"HOME": str(self.root), "CARGENTO_HOME": str(self.root / "state")},
            platform_name="linux",
            os_name="posix",
            launcher_path=self.root / "server.py",
            store_root_overrides={"pi.sessions": str(self.root)},
        )
        self.model = mock.patch.object(
            project_context.observer.CodexGoalModel,
            "__call__",
            return_value=None,
        )
        self.model.start()

    def tearDown(self) -> None:
        self.model.stop()
        self.temp.cleanup()

    def _write_transcript(self, text: str | None, timestamp: str) -> None:
        envelope = json.dumps(
            {
                "command": "boot",
                "definition_dir": str(self.workflow),
                "entity_dir": str(self.entity_dir),
            }
        )
        boot = json.dumps(
            {
                "type": "message",
                "id": "boot",
                "message": {
                    "role": "user",
                    "content": [{"type": "tool_result", "content": envelope}],
                },
            }
        )
        lines = [json.dumps({"type": "session", "id": self.SID, "cwd": str(self.root)}), boot]
        if text is not None:
            lines.append(message("captain-1", text, timestamp))
        self.transcript.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _write_gate(self, timestamp: str, decision: str) -> None:
        self.entity.write_text(
            "---\ntitle: Project cockpit\nstatus: shaping\ngates:\n  version: 1\n"
            "  records:\n    - id: gate:project-cockpit:shaping\n"
            "      stage: shaping\n      attempts:\n"
            "        - id: gate-attempt:project-cockpit-shaping-1\n"
            "          briefing:\n            id: briefing:one\n"
            "          resolution:\n            by: person:captain\n"
            f'            at: "{timestamp}"\n            decision: {decision}\n'
            "            reason: 'ready to continue'\n"
            "          application:\n            target-stage: review\n"
            "            state: consumed\n---\n",
            encoding="utf-8",
        )

    def collect(self) -> dict[str, Any]:
        state = build_runtime_state(self.config, started=self.NOW)
        sessions = [
            {
                "project": "repo/proj",
                "harness": "pi",
                "sid": self.SID,
                "last_activity": self.NOW,
                "active": True,
            }
        ]
        return project_context.collect(self.config, state, sessions, "repo/proj", now=self.NOW)

    def test_real_transcript_and_gate_frontmatter_supply_the_context(self) -> None:
        result = self.collect()

        observer = result["observers"][0]
        events = result["events"]
        self.assertEqual("Follow the captain revision", observer["goal"])
        self.assertEqual("shaping", observer["stage"])
        self.assertEqual(["gate", "steer"], [event["kind"] for event in events])
        self.assertEqual("application consumed", events[0]["phase"].split(" · ")[-1])

    def test_source_changes_move_events_and_source_removal_does_not_leave_rows(self) -> None:
        before = self.collect()
        self._write_gate("2026-08-24T20:15:00Z", "revise")
        moved = self.collect()
        self.entity.unlink()
        no_gate = self.collect()
        self._write_transcript(None, "2026-08-24T20:00:00Z")
        empty = self.collect()

        self.assertNotEqual(before["events"][0]["at"], moved["events"][0]["at"])
        self.assertEqual(0, no_gate["sources"]["gate"]["live"])
        self.assertEqual(["steer"], [event["kind"] for event in no_gate["events"]])
        self.assertEqual([], empty["events"])
        self.assertEqual(0, empty["sources"]["steer"]["live"])


if __name__ == "__main__":
    unittest.main()
