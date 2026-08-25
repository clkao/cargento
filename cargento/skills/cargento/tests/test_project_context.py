"""Real-source project observer and gate/steering history."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from cargento_runtime import observer, project_context, spacedock
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


def codex_message(text: str, timestamp: str) -> dict[str, object]:
    return {
        "timestamp": timestamp,
        "type": "response_item",
        "payload": {"type": "message", "role": "user", "content": text},
    }


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
            observer.CodexGoalModel,
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

    def collect(self, *, refresh: bool = True) -> dict[str, Any]:
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
        return project_context.collect(
            self.config,
            state,
            sessions,
            "repo/proj",
            now=self.NOW,
            refresh=refresh,
            focus=("pi", self.SID),
        )

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

    def test_bound_omissions_are_not_reported_as_unreadable_transcripts(self) -> None:
        state = build_runtime_state(self.config, started=self.NOW)
        sessions = [
            {
                "project": "repo/proj",
                "harness": "pi",
                "sid": f"missing-{index}",
                "last_activity": self.NOW - index,
                "active": True,
            }
            for index in range(project_context.MAX_PROJECT_OBSERVERS + 1)
        ]

        result = project_context.collect(
            self.config,
            state,
            sessions,
            "repo/proj",
            now=self.NOW,
        )

        self.assertEqual(
            project_context.MAX_PROJECT_OBSERVERS, len(result["sources"]["observer"]["unavailable"])
        )
        self.assertEqual(1, len(result["sources"]["observer"]["omitted"]))

    def test_focus_identity_excludes_surrounding_sessions_from_analysis(self) -> None:
        state = build_runtime_state(self.config, started=self.NOW)
        sessions = [
            {
                "project": "repo/proj",
                "harness": "pi",
                "sid": f"newer-{index}",
                "last_activity": self.NOW + index,
                "active": True,
            }
            for index in range(project_context.MAX_PROJECT_OBSERVERS)
        ]
        sessions.append(
            {
                "project": "repo/proj",
                "harness": "pi",
                "sid": self.SID,
                "last_activity": self.NOW - 100,
                "active": True,
            }
        )

        result = project_context.collect(
            self.config,
            state,
            sessions,
            "repo/proj",
            now=self.NOW,
            refresh=True,
            focus=("pi", self.SID),
        )

        self.assertEqual(self.SID, result["observers"][0]["sid"])
        self.assertTrue(result["focus"]["observed"])
        self.assertEqual([], result["sources"]["observer"]["omitted"])
        self.assertEqual("focused session", result["sources"]["scope"])
        self.assertEqual(
            project_context.MAX_PROJECT_OBSERVERS,
            result["sources"]["surrounding_active"],
        )

    def test_automatic_context_uses_stale_cache_without_model_wait(self) -> None:
        refreshed = self.collect()
        observed_at = refreshed["observers"][0]["observed_at"]
        self._write_transcript("A newer steering record", "2026-08-24T20:20:00Z")

        with mock.patch.object(observer.CodexGoalModel, "__call__") as model:
            automatic = self.collect(refresh=False)

        model.assert_not_called()
        self.assertEqual(observed_at, automatic["observers"][0]["observed_at"])
        self.assertEqual("cached-stale", automatic["observers"][0]["snapshot_status"])
        self.assertEqual("A newer steering record", automatic["events"][0]["title"])

    def test_automatic_context_without_cache_returns_timeline_only(self) -> None:
        path = observer.sidecar_path(self.config, "pi", self.SID)
        if path is not None:
            Path(path).unlink(missing_ok=True)

        with mock.patch.object(observer.CodexGoalModel, "__call__") as model:
            automatic = self.collect(refresh=False)

        model.assert_not_called()
        self.assertEqual([], automatic["observers"])
        self.assertEqual(["gate", "steer"], [event["kind"] for event in automatic["events"]])

    def test_codex_response_item_is_a_timestamped_instruction(self) -> None:
        event = project_context._instruction_event(
            self.config,
            codex_message("Captain changed the shape", "2026-08-24T20:10:00Z"),
            "codex",
            self.SID,
        )

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual("Captain changed the shape", event["title"])
        self.assertEqual("user-role instruction", event["phase"])
        self.assertNotIn("detail", event)
        self.assertEqual("timestamped non-meta user-role record", event["source"])

    def test_instruction_is_condensed_and_tagged_only_by_explicit_wording(self) -> None:
        event = project_context._instruction_event(
            self.config,
            codex_message(
                "Captain clarification: Keep the graph concise.\n"
                "Infrastructure prose that must not become the directive.",
                "2026-08-24T20:10:00Z",
            ),
            "codex",
            self.SID,
        )

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual("Keep the graph concise.", event["title"])
        self.assertEqual("reframed", event["steering_tag"])
        self.assertEqual("explicit user-role wording", event["tag_source"])
        self.assertNotIn("Infrastructure prose", event["title"])

    def test_pi_work_events_normalize_dispatch_and_subagent_results(self) -> None:
        records = [
            {
                "type": "message",
                "timestamp": "2026-08-24T20:00:00Z",
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "toolCall",
                            "id": "raw-build-id",
                            "name": "bash",
                            "arguments": {
                                "command": "echo preparing\n"
                                "spacedock dispatch build --workflow-dir /work task-one "
                                "--stage shaping\n"
                            },
                        },
                        {
                            "type": "toolCall",
                            "id": "raw-batch-id",
                            "name": "subagent",
                            "arguments": {
                                "tasks": [
                                    {"task": "Inspect architecture", "agent": "one"},
                                    {"task": "Inspect interaction", "agent": "two"},
                                ]
                            },
                        },
                        {
                            "type": "toolCall",
                            "id": "raw-status-id",
                            "name": "subagent",
                            "arguments": {"action": "status"},
                        },
                        {
                            "type": "toolCall",
                            "id": "raw-open-id",
                            "name": "subagent",
                            "arguments": {"task": "Check the unresolved edge"},
                        },
                    ],
                },
            },
            {
                "type": "message",
                "timestamp": "2026-08-24T20:01:00Z",
                "message": {
                    "role": "toolResult",
                    "toolCallId": "raw-build-id",
                    "isError": False,
                    "content": [{"type": "text", "text": "built"}],
                },
            },
            {
                "type": "message",
                "timestamp": "2026-08-24T20:02:00Z",
                "message": {
                    "role": "toolResult",
                    "toolCallId": "raw-batch-id",
                    "isError": False,
                    "content": [{"type": "text", "text": "done"}],
                },
            },
        ]
        self.transcript.write_text(
            "\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8"
        )

        events = project_context.work_events(self.config, str(self.transcript), "pi", self.SID)

        self.assertEqual(
            [
                "prepared_dispatch",
                "task_started",
                "task_started",
                "task_result",
                "task_result",
                "task_started",
            ],
            [event["kind"] for event in events],
        )
        self.assertEqual("task-one → shaping", events[0]["title"])
        self.assertEqual("Inspect architecture", events[1]["title"])
        self.assertEqual("Technical review completed by 2 contributors", events[3]["title"])
        self.assertNotIn("raw-status-id", json.dumps(events))
        self.assertNotIn("preparing", json.dumps(events))

    def test_semantic_layers_keep_work_items_distinct_from_contributors(self) -> None:
        events = [
            {
                "at": 1.0,
                "kind": "steer",
                "title": "Change course",
                "source": "user row",
            },
            {
                "at": 2.0,
                "kind": "prepared_dispatch",
                "title": "workflow-task → shaping",
                "source": "build call",
                "entity": "workflow-task",
                "stage": "shaping",
            },
            {
                "at": 3.0,
                "kind": "task_started",
                "title": "Shared implementation",
                "source": "subagent call",
                "lineage": "call-one:0",
                "work_item_binding": "shared-work",
                "contributor_ref": "worker-a",
            },
            {
                "at": 4.0,
                "kind": "task_started",
                "title": "Shared implementation handoff",
                "source": "subagent call",
                "lineage": "call-two:0",
                "work_item_binding": "shared-work",
                "contributor_ref": "worker-b",
            },
            {
                "at": 5.0,
                "kind": "task_started",
                "title": "One-off investigation",
                "source": "subagent call",
                "lineage": "call-three:0",
                "contributor_ref": "worker-a",
            },
        ]

        model = project_context._semantic_model(events, [])
        shared = next(
            item
            for item in model["work_items"]
            if {"source": "explicit task binding", "value": "shared-work"}
            in item["source_bindings"]
        )
        one_off = next(
            item for item in model["work_items"] if item["label"] == "One-off investigation"
        )
        prepared = next(item for item in model["work_items"] if item["label"] == "workflow-task")
        contributors = {item["source_label"]: item for item in model["contributors"]}

        self.assertEqual(
            [
                contributors["worker-a"]["contributor_id"],
                contributors["worker-b"]["contributor_id"],
            ],
            shared["contributor_refs"],
        )
        self.assertEqual("one_off", one_off["kind"])
        self.assertNotIn("head_event", shared)
        self.assertFalse(
            any(
                fact["type"] == "work_birth" and fact["work_item_id"] == prepared["work_item_id"]
                for fact in model["facts"]
            )
        )
        worker_a_links = [
            relation
            for relation in model["relations"]
            if relation["from"] == contributors["worker-a"]["contributor_id"]
            and relation["type"] == "contributes_to"
        ]
        self.assertEqual(2, len(worker_a_links))
        self.assertTrue(all(link["confidence"] == "source-labeled" for link in worker_a_links))
        self.assertEqual("unverified source label", contributors["worker-a"]["identity_status"])
        self.assertEqual([], model["projections"]["steering_episodes"])
        self.assertEqual([], model["projections"]["candidate_goal_shifts"])

    def test_birth_only_is_requested_history_not_demonstrated_current_work(self) -> None:
        model = project_context._semantic_model(
            [
                {
                    "at": 2.0,
                    "kind": "task_started",
                    "title": "task is DONE",
                    "source": "historical subagent call",
                    "lineage": "old-call:0",
                }
            ],
            [],
        )

        self.assertEqual("requested", model["projections"]["trail_heads"][0]["status"])
        self.assertFalse(
            any(
                head["status"] in {"started", "working"}
                for head in model["projections"]["trail_heads"]
            )
        )

    def test_structural_assistant_turn_promotes_short_command_and_one_reaction(self) -> None:
        model = project_context._semantic_model(
            [
                {
                    "at": 1.0,
                    "kind": "steer",
                    "title": "redispatch",
                    "source": "Pi user record",
                    "intent_promotable": False,
                    "harness": "pi",
                    "sid": self.SID,
                    "record_id": "user-redispatch",
                    "parent_id": "previous-assistant",
                    "turn_id": "user-redispatch",
                    "branch_id": "user-redispatch",
                },
                {
                    "at": 2.0,
                    "kind": "task_started",
                    "title": "Fix causal encoder",
                    "source": "Pi subagent task label",
                    "harness": "pi",
                    "sid": self.SID,
                    "lineage": "call-fix:0",
                    "record_id": "assistant-dispatch",
                    "parent_id": "tool-preflight",
                    "turn_id": "user-redispatch",
                    "branch_id": "assistant-preflight",
                },
                {
                    "at": 3.0,
                    "kind": "steer",
                    "title": "and do the comparison at the same time",
                    "source": "Pi user record",
                    "intent_promotable": True,
                    "harness": "pi",
                    "sid": self.SID,
                    "record_id": "user-compare",
                    "parent_id": "assistant-dispatch",
                    "turn_id": "user-compare",
                    "branch_id": "user-compare",
                },
            ],
            [],
            now=3.0,
        )

        intents = model["projections"]["operator_intents"]
        episodes = model["projections"]["steering_episodes"]
        self.assertIn("redispatch", [intent["summary"] for intent in intents])
        self.assertEqual(1, len(episodes))
        self.assertEqual("structural", episodes[0]["confidence"])
        redispatch = next(intent for intent in intents if intent["summary"] == "redispatch")
        comparison = next(
            intent
            for intent in intents
            if intent["summary"] == "and do the comparison at the same time"
        )
        self.assertEqual(redispatch["projection_id"], episodes[0]["intent_id"])
        self.assertNotEqual(comparison["projection_id"], episodes[0]["intent_id"])
        links = [relation for relation in model["relations"] if relation["type"] == "elicits"]
        self.assertEqual(1, len(links))
        self.assertEqual("structural", links[0]["confidence"])

    def test_pi_turn_identity_reaches_a_descendant_subagent_call(self) -> None:
        rows = [
            {"type": "session", "id": self.SID, "cwd": str(self.root)},
            {
                "type": "message",
                "id": "user-redispatch",
                "parentId": None,
                "timestamp": "2026-08-24T20:00:00Z",
                "message": {"role": "user", "content": "redispatch"},
            },
            {
                "type": "message",
                "id": "assistant-preflight",
                "parentId": "user-redispatch",
                "timestamp": "2026-08-24T20:00:01Z",
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "toolCall",
                            "id": "call-preflight",
                            "name": "bash",
                            "arguments": {"command": "pwd"},
                        }
                    ],
                },
            },
            {
                "type": "message",
                "id": "preflight-result",
                "parentId": "assistant-preflight",
                "timestamp": "2026-08-24T20:00:02Z",
                "message": {
                    "role": "toolResult",
                    "toolCallId": "call-preflight",
                    "content": str(self.root),
                },
            },
            {
                "type": "message",
                "id": "assistant-dispatch",
                "parentId": "preflight-result",
                "timestamp": "2026-08-24T20:00:03Z",
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "toolCall",
                            "id": "call-fix",
                            "name": "subagent",
                            "arguments": {"task": "Fix causal encoder"},
                        }
                    ],
                },
            },
        ]
        self.transcript.write_text(
            "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
        )

        instructions = project_context.instruction_events(
            self.config, str(self.transcript), "pi", self.SID
        )
        work, _stats = project_context._work_evidence(
            self.config, str(self.transcript), "pi", self.SID
        )

        self.assertEqual("user-redispatch", instructions[0]["record_id"])
        started = next(event for event in work if event["kind"] == "task_started")
        self.assertEqual("assistant-dispatch", started["record_id"])
        self.assertEqual("preflight-result", started["parent_id"])
        self.assertEqual("user-redispatch", started["turn_id"])
        self.assertEqual("assistant-preflight", started["branch_id"])

    def test_activity_floor_uses_collection_time_not_newest_work(self) -> None:
        model = project_context._semantic_model(
            [
                {
                    "at": self.NOW - (42 * 60),
                    "kind": "task_started",
                    "title": "Stale unmatched ASR dispatch",
                    "source": "Pi subagent task label",
                    "lineage": "old-call:0",
                }
            ],
            [],
            now=self.NOW,
        )

        activity = model["projections"]["activity"]
        self.assertEqual([], activity["nodes"])
        self.assertEqual(1, activity["historical_unresolved"])
        self.assertEqual(self.NOW - project_context.SEMANTIC_CURRENT_HORIZON_SEC, activity["current_after"])

    def test_primary_activity_collapses_dispatch_burst_and_old_retry(self) -> None:
        events = [
            {
                "at": 1.0,
                "kind": "task_started",
                "title": "Fix causal encoder",
                "source": "old task call",
                "harness": "pi",
                "sid": self.SID,
                "lineage": "old-call:0",
            },
            {
                "at": 2.0,
                "kind": "task_started",
                "title": "Historical unrelated request",
                "source": "old task call",
                "harness": "pi",
                "sid": self.SID,
                "lineage": "older-call:0",
            },
        ]
        events.extend(
            {
                "at": 4_500.0,
                "kind": "task_started",
                "title": "Fix causal encoder" if index == 0 else f"Entity {index}",
                "source": "batch task call",
                "harness": "pi",
                "sid": self.SID,
                "lineage": f"batch-call:{index}",
            }
            for index in range(8)
        )
        events.append(
            {
                "at": 5_000.0,
                "kind": "steer",
                "title": "Later conversation must not erase work",
                "source": "user row",
                "intent_promotable": True,
            }
        )

        activity = project_context._semantic_model(events, [])["projections"]["activity"]

        self.assertEqual(1, len(activity["nodes"]))
        self.assertEqual("burst", activity["nodes"][0]["kind"])
        self.assertEqual(8, activity["nodes"][0]["count"])
        self.assertEqual(1, activity["historical_unresolved"])
        self.assertEqual(2, activity["historical_dispatches"])

    def test_intent_promotion_rejects_output_code_and_path_rows(self) -> None:
        rejected = (
            ", mode, buffering, encoding, errors, newline)",
            'raise RuntimeError("no benchmark samples selected")',
            "find ~/.cache/whisperlivekit/benchmark_data",
            "Saved metadata to /Users/example/long_samples.json",
        )

        for text in rejected:
            with self.subTest(text=text):
                self.assertFalse(project_context._intent_promotable(text, text))
        self.assertTrue(
            project_context._intent_promotable(
                "redispatch the causal bug fix worker",
                "redispatch the causal bug fix worker",
            )
        )

    def test_primary_steering_prefers_directives_to_recent_questions(self) -> None:
        intents = [
            {"at": 1.0, "summary": "before running benchmark, validate model size"},
            {"at": 2.0, "summary": "redispatch the causal bug fix worker"},
            {"at": 2.5, "summary": "please redispatch the causal bug fix worker again"},
            {"at": 3.0, "summary": "how far are we?"},
            {"at": 4.0, "summary": "is this a raw subagent?"},
        ]

        steering = project_context._recent_steering_nodes(intents)

        self.assertEqual(
            [
                "please redispatch the causal bug fix worker again",
                "before running benchmark, validate model size",
            ],
            [item["summary"] for item in steering],
        )

    def test_primary_steering_keeps_recent_meaningful_questions(self) -> None:
        intents = [
            {"at": 1.0, "summary": "how far are we?"},
            {"at": 2.0, "summary": "why is there also audio alignment?"},
            {"at": 3.0, "summary": "where is the attention head shipped?"},
        ]

        steering = project_context._recent_steering_nodes(intents)

        self.assertEqual(
            [
                "where is the attention head shipped?",
                "why is there also audio alignment?",
            ],
            [item["summary"] for item in steering],
        )

    def test_exact_dispatch_artifact_binds_spawn_and_result_to_workflow_item(self) -> None:
        artifact = "/tmp/spacedock-dispatch/spacedock-ensign-search-review.md"
        model = project_context._semantic_model(
            [
                {
                    "at": 1.0,
                    "kind": "prepared_dispatch",
                    "title": "search → review",
                    "source": "build call",
                    "workflow_binding": "/workflow/asr",
                    "entity": "search",
                    "stage": "",
                    "dispatch_artifact": "",
                    "dispatch_artifact_prefix": (
                        "/tmp/spacedock-dispatch/spacedock-ensign-search-"
                    ),
                },
                {
                    "at": 2.0,
                    "kind": "task_started",
                    "title": f"Read {artifact} and treat its content as your assignment.",
                    "source": "Pi subagent task label",
                    "lineage": "spawn:0",
                    "dispatch_artifact": artifact,
                },
                {
                    "at": 3.0,
                    "kind": "task_result",
                    "title": "Dispatch result returned",
                    "source": "Pi subagent paired result",
                    "lineage": "spawn:0",
                    "dispatch_artifact": artifact,
                },
            ],
            [],
        )

        self.assertEqual(1, len(model["work_items"]))
        self.assertEqual("workflow_item", model["work_items"][0]["kind"])
        self.assertEqual("search · review", model["work_items"][0]["label"])
        self.assertEqual("outcome", model["projections"]["trail_heads"][0]["status"])
        summaries = {fact["summary"] for fact in model["facts"]}
        self.assertIn("search · review dispatched", summaries)
        self.assertIn("search · review result returned", summaries)
        self.assertFalse(any("/tmp/spacedock-dispatch" in str(value) for value in summaries))

    def test_dispatch_artifact_binding_rejects_ambiguous_or_similar_labels(self) -> None:
        artifact = "/tmp/spacedock-dispatch/spacedock-ensign-shared-review.md"
        events = [
            {
                "at": float(index),
                "kind": "prepared_dispatch",
                "title": "shared → review",
                "source": "build call",
                "workflow_binding": f"/workflow/{index}",
                "entity": "shared",
                "stage": "review",
                "dispatch_artifact": artifact,
            }
            for index in (1, 2)
        ]
        events.extend(
            [
                {
                    "at": 3.0,
                    "kind": "task_started",
                    "title": f"Read {artifact}",
                    "source": "subagent call",
                    "lineage": "ambiguous:0",
                    "dispatch_artifact": artifact,
                },
                {
                    "at": 4.0,
                    "kind": "task_started",
                    "title": "Review shared task",
                    "source": "subagent call",
                    "lineage": "similar-only:0",
                },
            ]
        )

        model = project_context._semantic_model(events, [])

        self.assertEqual(4, len(model["work_items"]))
        self.assertEqual(1, sum(item["kind"] == "one_off" for item in model["work_items"]))

    def test_async_dispatch_ack_is_birth_only_and_artifact_supplies_identity(self) -> None:
        artifact = "/tmp/spacedock-dispatch/spacedock-ensign-search-review.md"
        events = project_context._subagent_events(
            {"task": f"Read {artifact} and treat its content as your assignment."},
            call_key="chatcmpl-tool-b27704648c9029bc",
            at=2.0,
            result={
                "succeeded": True,
                "at": 3.0,
                "text": "Async: worker [...] The async run is detached and running in the background.",
            },
            harness="pi",
            sid=self.SID,
        )

        self.assertEqual(["task_started"], [event["kind"] for event in events])
        model = project_context._semantic_model(events, [])
        work_item = model["work_items"][0]
        self.assertEqual("workflow_item", work_item["kind"])
        self.assertEqual("search · review", work_item["label"])
        self.assertIn(
            {"source": "structured Spacedock dispatch artifact", "value": artifact},
            work_item["source_bindings"],
        )
        self.assertEqual("requested", model["projections"]["trail_heads"][0]["status"])
        self.assertFalse(any(fact["type"] == "work_result" for fact in model["facts"]))

    def test_dispatch_artifact_title_supplies_assignment_without_claiming_result(self) -> None:
        artifact = "/tmp/spacedock-dispatch/spacedock-ensign-search-review.md"
        with mock.patch(
            "cargento_runtime.project_context.runtime_io.iter_bounded_text_lines",
            return_value=iter(
                [
                    "You are working on: Review the search release evidence\n",
                    "Stage: review\n",
                ]
            ),
        ):
            assignment = project_context._dispatch_file_assignment(artifact)

        self.assertEqual("Review the search release evidence", assignment)
        self.assertEqual("", project_context._dispatch_file_assignment("/tmp/unrelated.md"))

    def test_active_child_assignment_uses_refreshable_snapshot_or_unavailable(self) -> None:
        session = {
            "subagent_hierarchy": [
                {
                    "name": "Volta",
                    "depth": 1,
                    "parent_name": None,
                    "observer_sid": "child-thread",
                    "assignment": None,
                    "assignment_status": "unavailable",
                    "workflow_entity": "project-cockpit",
                    "workflow_stage": "shaping",
                }
            ]
        }
        with (
            mock.patch.object(observer, "resolve_transcript", return_value="/tmp/child.jsonl"),
            mock.patch.object(
                project_context,
                "_observe_session",
                return_value={
                    "goal": "Improve the assignment roster",
                    "observed_at": 12.0,
                    "snapshot_status": "refreshed",
                },
            ) as observe,
        ):
            refreshed = project_context._active_child_assignments(
                self.config,
                mock.Mock(),
                session,
                now=self.NOW,
                refresh=True,
            )

        self.assertEqual("Improve the assignment roster", refreshed[0]["assignment"])
        self.assertEqual("derived", refreshed[0]["confidence"])
        self.assertEqual("project-cockpit", refreshed[0]["workflow_entity"])
        self.assertEqual("shaping", refreshed[0]["workflow_stage"])
        self.assertTrue(observe.call_args.kwargs["refresh"])

        with (
            mock.patch.object(observer, "resolve_transcript", return_value="/tmp/child.jsonl"),
            mock.patch.object(
                project_context,
                "_observe_session",
                return_value={
                    "goal": "Earlier assignment",
                    "observed_at": 10.0,
                    "snapshot_status": "cached-stale",
                },
            ),
        ):
            stale = project_context._active_child_assignments(
                self.config,
                mock.Mock(),
                session,
                now=self.NOW,
                refresh=False,
            )
        self.assertEqual("cached-stale", stale[0]["snapshot_status"])

        with mock.patch.object(observer, "resolve_transcript", return_value=None):
            unavailable = project_context._active_child_assignments(
                self.config,
                mock.Mock(),
                session,
                now=self.NOW,
                refresh=False,
            )
        self.assertIsNone(unavailable[0]["assignment"])
        self.assertEqual("unavailable", unavailable[0]["confidence"])

    def test_subagent_result_category_uses_directive_and_rejects_unavailable_review(self) -> None:
        succeeded = {"succeeded": True, "text": "A substantive result was returned."}
        unavailable = {
            "succeeded": True,
            "text": "Acceptance cannot be requested explicitly; no reviewer result was supplied.",
        }

        self.assertEqual(
            "Implementation pass completed",
            project_context._subagent_result_title(
                ["Implement the reviewed design after reading its corrections."], succeeded
            ),
        )
        self.assertEqual(
            "Implementation review completed",
            project_context._subagent_result_title(
                ["Review the implementation for correctness."], succeeded
            ),
        )
        self.assertEqual(
            "",
            project_context._subagent_result_title(
                ["Review the implementation for correctness."], unavailable
            ),
        )

    def test_only_context_sufficient_user_rows_become_intent_projections(self) -> None:
        rows = [
            ("do it", False),
            ("why do we need that?", False),
            ("Error: command returned an internal failure\nraw stack row", False),
            (".venv/bin/python scripts/check.py --verbose", False),
            ("Keep the selected project as the context boundary.", True),
        ]
        events = []
        for index, (text, expected) in enumerate(rows):
            event = project_context._instruction_event(
                self.config,
                codex_message(text, f"2026-08-24T20:1{index}:00Z"),
                "codex",
                self.SID,
            )
            self.assertIsNotNone(event)
            assert event is not None
            self.assertIs(expected, event["intent_promotable"])
            events.append(event)

        model = project_context._semantic_model(events, [])

        self.assertEqual(
            5, len([fact for fact in model["facts"] if fact["type"] == "user_message"])
        )
        self.assertEqual(1, len(model["projections"]["operator_intents"]))
        self.assertEqual(
            "Keep the selected project as the context boundary.",
            model["projections"]["operator_intents"][0]["summary"],
        )

    def test_semantic_ids_include_workflow_and_survive_order_changes(self) -> None:
        first = {
            "at": 2.0,
            "kind": "gate",
            "title": "shared · review · approve",
            "source": "entity record",
            "workflow_binding": "/workflows/one",
            "entity": "shared",
            "decision": "approve",
        }
        second = {
            "at": 3.0,
            "kind": "gate",
            "title": "shared · review · revise",
            "source": "entity record",
            "workflow_binding": "/workflows/two",
            "entity": "shared",
            "decision": "revise",
        }
        model = project_context._semantic_model([first, second], [])
        reordered = project_context._semantic_model(
            [second, {"at": 1.0, "kind": "steer", "title": "Earlier", "source": "row"}, first],
            [],
        )

        self.assertEqual(2, len(model["work_items"]))
        self.assertTrue(all(fact["scope"] == "workflow" for fact in model["facts"]))
        fact_ids = {fact["fact_id"] for fact in model["facts"]}
        reordered_ids = {fact["fact_id"] for fact in reordered["facts"]}
        self.assertTrue(fact_ids.issubset(reordered_ids))
        node_ids = fact_ids | {item["work_item_id"] for item in model["work_items"]}
        node_ids |= {item["contributor_id"] for item in model["contributors"]}
        projections = model["projections"]
        node_ids |= {item["projection_id"] for item in projections["operator_intents"]}
        self.assertTrue(
            all(
                relation["from"] in node_ids and relation["to"] in node_ids
                for relation in model["relations"]
            )
        )

    def test_environment_context_is_not_steering(self) -> None:
        event = project_context._instruction_event(
            self.config,
            codex_message(
                "<environment_context>\n  <cwd>/private/project</cwd>\n</environment_context>",
                "2026-08-24T20:10:00Z",
            ),
            "codex",
            self.SID,
        )

        self.assertIsNone(event)

    def test_codex_function_output_can_supply_boot_provenance(self) -> None:
        envelope = (
            '{"command":"boot","id_style":"slug",'
            '"definition_dir":"/w/one","entity_dir":"/w/one",'
            '"dispatchable":[]}'
        )
        record = json.dumps(
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call_output",
                    "output": "=== BOOT ===\n" + envelope,
                },
            }
        ).encode()
        pasted = json.dumps(codex_message(envelope, "2026-08-24T20:10:00Z")).encode()

        self.assertEqual(1, len(spacedock.boot_records(self.config, record)))
        self.assertEqual([], spacedock.boot_records(self.config, pasted))

    def test_codex_custom_output_blocks_can_supply_boot_provenance(self) -> None:
        envelope = (
            '{"command":"boot","id_style":"slug",'
            '"definition_dir":"/w/one","entity_dir":"/w/one",'
            '"dispatchable":[]}'
        )
        record = json.dumps(
            {
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call_output",
                    "output": [{"type": "input_text", "text": "=== BOOT ===\n" + envelope}],
                },
            }
        ).encode()

        self.assertEqual(1, len(spacedock.boot_records(self.config, record)))


if __name__ == "__main__":
    unittest.main()
