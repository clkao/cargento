"""Restart, dedupe, and replacement contracts for semantic work history."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cargento_runtime import semantic_history
from cargento_runtime.config import build_runtime_config
from cargento_runtime.state import build_runtime_state


class SemanticHistoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = build_runtime_config(
            environ={"HOME": str(self.root), "CARGENTO_HOME": str(self.root / "state")},
            platform_name="linux",
            os_name="posix",
            launcher_path=self.root / "server.py",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def _fact(
        fact_id: str,
        at: float,
        fact_type: str,
        source_kind: str,
        summary: str,
        work_item_id: str | None,
    ) -> dict[str, object]:
        return {
            "fact_id": fact_id,
            "at": at,
            "type": fact_type,
            "source_kind": source_kind,
            "summary": summary,
            "scope": "session",
            "work_item_id": work_item_id,
            "stage": "shaping",
            "branch": {"harness": "codex", "sid": "root", "record_id": fact_id},
            "evidence": {"source": "structured rollout record", "confidence": "exact"},
        }

    def test_restart_dedupes_replaces_progress_and_suppresses_lifecycle_only(self) -> None:
        work_item_id = "workflow:project-cockpit"
        facts = [
            self._fact("assign", 10, "work_birth", "task_started", "Shape cockpit", work_item_id),
            self._fact("progress-1", 11, "work_result", "task_result", "First draft", work_item_id),
            self._fact(
                "progress-2", 12, "work_result", "task_result", "Graph visible", work_item_id
            ),
            self._fact("checkpoint", 13, "result", "checkpoint", "Checkpoint fb056", work_item_id),
            self._fact("lifecycle", 14, "task_complete", "task_complete", "worker stopped", None),
        ]
        semantic = {
            "facts": facts,
            "work_items": [
                {
                    "work_item_id": work_item_id,
                    "label": "Project cockpit",
                    "kind": "workflow_item",
                    "source_bindings": [
                        {"source": "structured dispatch artifact", "value": "project-cockpit"}
                    ],
                    "contributor_refs": [],
                }
            ],
        }
        session = {
            "harness": "codex",
            "sid": "root",
            "state": "idle",
            "last_activity": 15.0,
            "title": "Cockpit shaping",
            "last_output": "Ready for review.\nExact bounded final output.",
        }
        first = semantic_history.update(
            self.config,
            build_runtime_state(self.config, started=1),
            "git:project",
            semantic,
            [session],
        )
        restarted = semantic_history.update(
            self.config,
            build_runtime_state(self.config, started=2),
            "git:project",
            semantic,
            [session],
        )
        self.assertEqual(first["events"], restarted["events"])
        event_types = [event["event_type"] for event in restarted["events"]]
        self.assertNotIn("task_complete", event_types)
        self.assertEqual(1, event_types.count("progress_head"))
        self.assertIn("checkpoint", event_types)
        self.assertIn("final_output", event_types)
        assignment = next(
            event for event in restarted["events"] if event["event_type"] == "assignment"
        )
        self.assertEqual("shaping", assignment["fact"]["stage"])
        checkpoint = next(
            event for event in restarted["events"] if event["event_type"] == "checkpoint"
        )
        self.assertEqual(work_item_id, checkpoint["work_binding"])
        final = next(
            event for event in restarted["events"] if event["event_type"] == "final_output"
        )
        self.assertEqual("Ready for review.\nExact bounded final output.", final["fact"]["detail"])
        self.assertTrue(restarted["persisted"])
        self.assertEqual(final["event_id"], restarted["cursors"]["codex:root"]["event_id"])

    def test_unchanged_observer_refresh_replaces_freshness_and_change_records_shift(self) -> None:
        state = build_runtime_state(self.config, started=1)

        def model(fact_id: str, at: float, goal: str) -> dict[str, object]:
            return {
                "facts": [self._fact(fact_id, at, "observer_snapshot", "observer", goal, None)],
                "work_items": [],
            }

        first = semantic_history.update(
            self.config, state, "git:project", model("g1", 10, "Ship"), []
        )
        same = semantic_history.update(
            self.config, state, "git:project", model("g2", 20, "Ship"), []
        )
        changed = semantic_history.update(
            self.config, state, "git:project", model("g3", 30, "Review"), []
        )
        self.assertEqual(1, len(first["events"]))
        self.assertEqual(["observed_goal"], [event["event_type"] for event in same["events"]])
        self.assertEqual(
            ["goal_shift", "observed_goal"],
            [event["event_type"] for event in changed["events"]],
        )
        self.assertTrue(all(len(event["summary"]) <= 240 for event in changed["events"]))

    def test_current_workflow_and_generic_children_share_assignment_vocabulary(self) -> None:
        result = semantic_history.update(
            self.config,
            build_runtime_state(self.config, started=1),
            "git:project",
            {"facts": [], "work_items": []},
            [],
            [
                {
                    "name": "Einstein",
                    "observer_sid": "child-one",
                    "assignment": "Shape cockpit",
                    "confidence": "exact",
                    "source": "structured dispatch artifact",
                    "workflow_entity": "project-cockpit",
                    "workflow_stage": "shaping",
                    "workflow_binding": "/repo/.spacedock/explore",
                },
                {
                    "name": "James",
                    "observer_sid": "child-two",
                    "assignment": "Review navigation",
                    "confidence": "exact",
                    "source": "exact parent dispatch",
                },
            ],
            now=100,
        )
        events = result["events"]
        self.assertEqual(["assignment", "assignment"], [event["event_type"] for event in events])
        workflow = next(
            event for event in events if event["work_binding"].endswith(":project-cockpit")
        )
        generic = next(event for event in events if event is not workflow)
        self.assertEqual("shaping", workflow["fact"]["stage"])
        self.assertNotIn("stage", generic["fact"])
        self.assertEqual("one_off", generic["work_item"]["kind"])

    def test_same_entity_slug_in_two_workflows_retains_distinct_exact_bindings(self) -> None:
        assignments = [
            {
                "name": name,
                "observer_sid": sid,
                "assignment": f"Shape {workflow}",
                "confidence": "exact",
                "source": "structured dispatch artifact",
                "workflow_entity": "project-cockpit",
                "workflow_stage": "shaping",
                "workflow_binding": f"/repo/.spacedock/{workflow}",
            }
            for name, sid, workflow in (
                ("Einstein", "explore-child", "explore"),
                ("Legacy", "dev-child", "dev"),
            )
        ]
        result = semantic_history.update(
            self.config,
            build_runtime_state(self.config, started=1),
            "git:project",
            {"facts": [], "work_items": []},
            [],
            assignments,
            now=100,
        )
        bindings = {event["work_binding"] for event in result["events"]}
        self.assertEqual(2, len(bindings))
        self.assertTrue(all(binding.endswith(":project-cockpit") for binding in bindings))
        sources = {event["work_item"]["source_bindings"][0]["value"] for event in result["events"]}
        self.assertEqual(
            {
                "/repo/.spacedock/explore:project-cockpit",
                "/repo/.spacedock/dev:project-cockpit",
            },
            sources,
        )

    def test_rolling_day_prunes_old_events_and_persists_dispatch_relation(self) -> None:
        now = 100_000.0
        work_item_id = "workflow:project-cockpit"
        recent = self._fact(
            "dispatch-recent",
            now - semantic_history.HISTORY_WINDOW_SEC + 1,
            "prepared_dispatch",
            "prepared_dispatch",
            "Project cockpit dispatched",
            work_item_id,
        )
        old = self._fact(
            "dispatch-old",
            now - semantic_history.HISTORY_WINDOW_SEC - 1,
            "prepared_dispatch",
            "prepared_dispatch",
            "Old task dispatched",
            "workflow:old",
        )
        semantic = {
            "facts": [recent, old],
            "work_items": [
                {
                    "work_item_id": work_item_id,
                    "label": "Project cockpit",
                    "kind": "workflow_item",
                },
                {"work_item_id": "workflow:old", "label": "Old task", "kind": "workflow_item"},
            ],
            "relations": [
                {
                    "from": "dispatch-recent",
                    "to": work_item_id,
                    "type": "binds_to",
                    "confidence": "structural",
                }
            ],
        }
        state = build_runtime_state(self.config, started=1)
        first = semantic_history.update(self.config, state, "git:project", semantic, [], now=now)
        duplicate = semantic_history.update(
            self.config, state, "git:project", semantic, [], now=now
        )
        restarted = semantic_history.update(
            self.config,
            build_runtime_state(self.config, started=2),
            "git:project",
            {"facts": [], "work_items": [], "relations": []},
            [],
            now=now,
        )
        self.assertEqual(["dispatch-recent"], [row["event_id"] for row in first["events"]])
        self.assertEqual(first["events"], duplicate["events"])
        self.assertEqual(first["events"], restarted["events"])
        self.assertEqual("binds_to", restarted["events"][0]["relations"][0]["type"])
        self.assertEqual(semantic_history.HISTORY_WINDOW_SEC, restarted["window_sec"])

    def test_backfill_cursor_skips_unchanged_and_rescans_bounded_overlap(self) -> None:
        state = build_runtime_state(self.config, started=1)
        signature = {"size": 1_000_000, "mtime_ns": 10}
        cold = semantic_history.backfill_scan_bytes(
            self.config,
            state,
            "git:project",
            "codex:root",
            signature,
            full_max_bytes=2_000_000,
        )
        semantic_history.update(
            self.config,
            state,
            "git:project",
            {"facts": [], "work_items": []},
            [],
            now=100,
            source_scans={"codex:root": signature},
        )
        cached = semantic_history.backfill_scan_bytes(
            self.config,
            state,
            "git:project",
            "codex:root",
            signature,
            full_max_bytes=2_000_000,
        )
        resumed = semantic_history.backfill_scan_bytes(
            self.config,
            state,
            "git:project",
            "codex:root",
            {"size": 1_001_000, "mtime_ns": 11},
            full_max_bytes=2_000_000,
        )
        rotated = semantic_history.backfill_scan_bytes(
            self.config,
            state,
            "git:project",
            "codex:root",
            {"size": 500_000, "mtime_ns": 12},
            full_max_bytes=2_000_000,
        )
        self.assertEqual(1_000_000, cold)
        self.assertEqual(0, cached)
        self.assertEqual(1_000 + semantic_history.RESCAN_OVERLAP_BYTES, resumed)
        self.assertEqual(500_000, rotated)
