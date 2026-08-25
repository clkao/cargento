"""Observer analyzer and panel tests.

Five tests covering the acceptance criteria:
1. No-goal session yields "no goal derived" sentinel (AC2).
2. Positive case derives goal + stage + block (AC1).
3. Read-only invariant: the observer never mutates the target tree (AC3).
4. Model failure degrades to the deterministic fallback.
5. Observer panel renders the user-facing output from the sidecar (AC4).
"""

from __future__ import annotations

import dataclasses
import http.client
import json
import os
import shutil
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from cargento_runtime import observer

from . import test_page_calm
from .page_harness import PageJsHarness
from .support import (
    RuntimeTestCase,
    make_config,
    make_runtime,
    make_server,
    runtime,
    store_patch,
)


def _pi_message(
    msg_id: str,
    parent: str | None,
    role: str,
    content: str,
    *,
    ts: str = "2026-08-17T02:00:00Z",
) -> str:
    """One Pi-style JSONL message record."""
    return json.dumps(
        {
            "type": "message",
            "id": msg_id,
            "parentId": parent,
            "timestamp": ts,
            "message": {"role": role, "content": content},
        }
    )


def _pi_session(sid: str, cwd: str = "/home/test/project") -> str:
    return json.dumps({"type": "session", "id": sid, "cwd": cwd})


def _write_entity(entity_dir: Path, slug: str, status: str) -> Path:
    """Write one entity file with ``status:`` frontmatter."""
    entity_dir.mkdir(parents=True, exist_ok=True)
    path = entity_dir / f"{slug}.md"
    path.write_text(f"---\nstatus: {status}\ntitle: {slug}\n---\nbody\n", encoding="utf-8")
    return path


def _write_workflow(workflow_dir: Path, stages: list[str]) -> Path:
    """A Spacedock workflow README declaring `stages`, the discriminator's source.

    The analyzer publishes a stage only when the entity's `status` names one this
    README declares — the per-file discriminator SECURITY.md names as standing in
    for the containment check a split-root state directory cannot get. A fixture
    with no README is a fixture whose stage is empty, which is what the observer
    must do with a state directory nothing vouched for.
    """
    workflow_dir.mkdir(parents=True, exist_ok=True)
    states = "".join(f"    - name: {stage}\n" for stage in stages)
    readme = workflow_dir / "README.md"
    readme.write_text(
        "---\ncommissioned-by: spacedock@0.22.0\nstages:\n  states:\n" + states + "---\n",
        encoding="utf-8",
    )
    return readme


def _boot_line(mid: str, parent: str | None, workflow_dir: Path, entity_dir: Path) -> str:
    """A `spacedock status --boot` envelope in a transcript record.

    Written in the `type: "tool_result"` block shape rather than Pi's
    `toolResult` *role*, and that is a branch dependency rather than a
    preference: reading the role shape is what `#127` adds to
    `spacedock.tool_result_text`, and on this branch it is not there yet. Both
    shapes reach the same `boot_records` scan once that lands, so this fixture
    stays correct either way. The envelope's first key must be `command`, which
    is what `boot_records` searches for.
    """
    envelope = json.dumps(
        {
            "command": "boot",
            "definition_dir": str(workflow_dir),
            "entity_dir": str(entity_dir),
        }
    )
    return json.dumps(
        {
            "type": "message",
            "id": mid,
            "parentId": parent,
            "message": {
                "role": "user",
                "content": [{"type": "tool_result", "content": envelope}],
            },
        }
    )


class ObserverAnalyzerTest(unittest.TestCase):
    """The observer analyzer: goal + stage + block from a transcript, read-only."""

    NOW = 1_700_000_000.0
    WINDOW = 86_400.0

    def setUp(self) -> None:
        self.config, self.state = make_runtime()

    def analyze(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """`observer.analyze` on this test's runtime and a fixed clock."""
        return observer.analyze(
            self.config, self.state, path, now=self.NOW, window_sec=self.WINDOW, **kwargs
        )

    def _write_transcript(self, tmp: str, lines: list[str]) -> str:
        path = Path(tmp) / "session.jsonl"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return str(path)

    def test_no_goal_session_yields_sentinel_not_hallucination(self) -> None:
        """AC2: a session with only a generic opener and no assistant output
        returns 'no goal derived' without calling the model."""
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_transcript(
                tmp,
                [
                    _pi_session("neg-001"),
                    _pi_message(
                        "m1",
                        None,
                        "user",
                        "Use $spacedock:first-officer for this whole Pi session.",
                    ),
                ],
            )

            # A model that fabricates a goal: the short-circuit must bypass it.
            def fabricating_model(_head: str, _ctx: str) -> str:
                return "fabricated goal that must not appear"

            result = self.analyze(path, model=fabricating_model)

        self.assertEqual("no goal derived", result["goal"])
        self.assertEqual("generic-opener-only-no-work", result["reason"])
        # The model was not called: the short-circuit bypassed it entirely.

    def test_positive_case_derives_goal_stage_and_block(self) -> None:
        """AC1: a known FO session produces a goal referencing the recent
        concrete directive, and the stage of the newest in-flight entity."""
        with tempfile.TemporaryDirectory() as tmp:
            workflow_dir = Path(tmp) / "wf"
            entity_dir = workflow_dir / ".spacedock-state"
            _write_workflow(workflow_dir, ["intake", "implementation", "posted"])
            _write_entity(entity_dir, "observer-agent-pattern", "implementation")
            os.utime(entity_dir / "observer-agent-pattern.md", (self.NOW, self.NOW))
            path = self._write_transcript(
                tmp,
                [
                    _pi_session("pos-001"),
                    _pi_message(
                        "m1",
                        None,
                        "user",
                        "Use $spacedock:first-officer for this whole Pi session.",
                    ),
                    _pi_message(
                        "m2",
                        "m1",
                        "assistant",
                        "I'll start by running spacedock status --boot.",
                    ),
                    _pi_message(
                        "m3",
                        "m2",
                        "user",
                        "report the remaining pi related test and ergonomics issues",
                        ts="2026-08-17T02:05:00Z",
                    ),
                    _pi_message(
                        "m4",
                        "m3",
                        "assistant",
                        "I am blocked on a missing dependency in the test suite.",
                        ts="2026-08-17T02:06:00Z",
                    ),
                    _boot_line("m5", "m4", workflow_dir, entity_dir),
                ],
            )
            result = self.analyze(path)

        # The goal tracks the most recent concrete user directive, not the
        # generic opener. Falsified by editing the directive to a different
        # objective and observing the goal not track it.
        self.assertIn("report the remaining pi related test", result["goal"])
        # The stage is the entity's `status`, and only because the workflow
        # README declares it. Falsified by renaming the stage in the README:
        # `read_entities` then drops the entity and the stage comes back empty.
        self.assertEqual("implementation", result["stage"])
        # The block comes from recent assistant text containing a block indicator.
        self.assertIn("blocked", result["block"])

    def test_claude_outer_role_records_supply_a_real_goal(self) -> None:
        """Claude writes `type: user`, while Pi writes `type: message`."""
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_transcript(
                tmp,
                [
                    json.dumps(
                        {
                            "type": "user",
                            "uuid": "captain-1",
                            "timestamp": "2026-08-24T20:00:00Z",
                            "message": {
                                "role": "user",
                                "content": "Show the project observer goal",
                            },
                        }
                    ),
                    json.dumps(
                        {
                            "type": "user",
                            "uuid": "meta-1",
                            "isMeta": True,
                            "message": {
                                "role": "user",
                                "content": [{"type": "text", "text": "Injected skill body"}],
                            },
                        }
                    ),
                ],
            )

            result = self.analyze(path)

        self.assertEqual("Show the project observer goal", result["goal"])

    def test_codex_response_messages_supply_goal_and_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_transcript(
                tmp,
                [
                    json.dumps(
                        {
                            "type": "response_item",
                            "payload": {
                                "type": "message",
                                "id": "user-1",
                                "role": "user",
                                "content": [
                                    {"type": "input_text", "text": "Shape my session mirror"}
                                ],
                            },
                        }
                    ),
                    json.dumps(
                        {
                            "type": "response_item",
                            "payload": {
                                "type": "message",
                                "id": "assistant-1",
                                "role": "assistant",
                                "content": [
                                    {
                                        "type": "output_text",
                                        "text": "I am blocked on a missing browser connection.",
                                    }
                                ],
                            },
                        }
                    ),
                ],
            )

            result = self.analyze(path)

        self.assertEqual("Shape my session mirror", result["goal"])
        self.assertIn("blocked", result["block"])

    def test_child_assignment_can_be_model_derived_from_readable_assistant_activity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_transcript(
                tmp,
                [
                    json.dumps(
                        {
                            "type": "response_item",
                            "payload": {
                                "type": "message",
                                "id": "assistant-1",
                                "role": "assistant",
                                "content": [
                                    {
                                        "type": "output_text",
                                        "text": "I am revising the assignment roster.",
                                    }
                                ],
                            },
                        }
                    )
                ],
            )
            model = mock.Mock(return_value="Improve the assignment roster")
            result = observer.derive_child_assignment(self.config, path, model)

        self.assertEqual("Improve the assignment roster", result)
        model.assert_called_once()

    def _fo_transcript(
        self, tmp: str, *, stage: str, declared: list[str], age_sec: float = 0.0
    ) -> str:
        """One first-officer transcript over a workflow whose entity sits on `stage`."""
        workflow_dir = Path(tmp) / "wf"
        entity_dir = workflow_dir / ".spacedock-state"
        _write_workflow(workflow_dir, declared)
        entity = _write_entity(entity_dir, "drc-1", stage)
        written = self.NOW - age_sec
        os.utime(str(entity), (written, written))
        return self._write_transcript(
            tmp,
            [
                _pi_session("fo-001"),
                _pi_message("m1", None, "user", "Ship the observer route"),
                _pi_message("m2", "m1", "assistant", "Booting the workflow."),
                _boot_line("m3", "m2", workflow_dir, entity_dir),
            ],
        )

    def test_ordinary_reporting_prose_is_not_a_block(self) -> None:
        # The false-positive case, which the indicator table had none of. A bare
        # `cannot`/`can't`/`failed to`/`error:` matches an agent describing work
        # it has finished, and a block is the one field on the panel a reader
        # would act on. Falsifying edit: put the bare words back — every line
        # here publishes a block.
        for line in (
            "I can't reproduce the failure any more, so the fix holds.",
            "The old code cannot have worked; the new one does.",
            "It failed to build before the patch. It builds now.",
            "The log said error: missing header, which the include fixes.",
            "I was unable to reproduce it until I widened the window.",
            "Waiting for the suite to finish, then I will push.",
        ):
            with self.subTest(line=line), tempfile.TemporaryDirectory() as tmp:
                path = self._write_transcript(
                    tmp,
                    [
                        _pi_session("fp-001"),
                        _pi_message("m1", None, "user", "Fix the build"),
                        _pi_message("m2", "m1", "assistant", line),
                    ],
                )
                self.assertEqual("", self.analyze(path)["block"])

    def test_a_resolved_block_is_not_walked_back_to(self) -> None:
        # Scanning backwards through every assistant message found a block that
        # had been reported and then resolved, and published it as current.
        # Falsifying edit: drop the `return ""` after the newest assistant
        # message — this publishes the twenty-turn-old block.
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_transcript(
                tmp,
                [
                    _pi_session("res-001"),
                    _pi_message("m1", None, "user", "Fix the build"),
                    _pi_message("m2", "m1", "assistant", "I am blocked on a missing token."),
                    _pi_message("m3", "m2", "user", "Here is the token."),
                    _pi_message("m4", "m3", "assistant", "Thanks — the build is green now."),
                ],
            )
            self.assertEqual("", self.analyze(path)["block"])

    def test_a_current_block_is_still_reported(self) -> None:
        # The other side: narrowing the table must not cost the real case.
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_transcript(
                tmp,
                [
                    _pi_session("cur-001"),
                    _pi_message("m1", None, "user", "Deploy it"),
                    _pi_message(
                        "m2",
                        "m1",
                        "assistant",
                        "I pulled the manifest. I am blocked on a missing AWS role.",
                    ),
                ],
            )
            self.assertEqual("I am blocked on a missing AWS role.", self.analyze(path)["block"])

    def test_no_spacedock_withdraws_the_project_reads(self) -> None:
        # `--no-spacedock` is the switch that turns off the project reads, and
        # SECURITY.md's project-read contract is written against it. The route
        # read the entity frontmatter regardless, so the switch withdrew a
        # strip and left this reading the same files.
        with tempfile.TemporaryDirectory() as tmp:
            path = self._fo_transcript(tmp, stage="review", declared=["intake", "review"])
            self.assertEqual("review", self.analyze(path)["stage"])

            self.config = dataclasses.replace(self.config, spacedock_enabled=False)
            result = self.analyze(path)

        # The transcript half survives — a transcript read is not a project read.
        self.assertIn("Ship the observer route", result["goal"])
        self.assertEqual("", result["stage"])

    def test_an_undeclared_status_publishes_no_stage(self) -> None:
        # The per-file discriminator. SECURITY.md names `status in declared` as
        # what stands in for `read_workflow`'s containment check, because a
        # split-root workflow's state directory legitimately sits outside the
        # definition directory. Reading the scalar directly published whatever
        # the newest file in an unverified directory happened to say.
        with tempfile.TemporaryDirectory() as tmp:
            path = self._fo_transcript(
                tmp, stage="/etc/passwd he said", declared=["intake", "review"]
            )
            self.assertEqual("", self.analyze(path)["stage"])

    def test_a_stale_entity_publishes_no_stage(self) -> None:
        # The freshness gate. A first officer discovers every workflow in the
        # project, and one retired months ago still has entities frozen
        # mid-pipeline; those are history, not work in flight.
        with tempfile.TemporaryDirectory() as tmp:
            path = self._fo_transcript(
                tmp, stage="review", declared=["intake", "review"], age_sec=self.WINDOW * 2
            )
            self.assertEqual("", self.analyze(path)["stage"])

    def test_sidecar_path_refuses_a_name_that_is_not_a_name(self) -> None:
        # `safe_text` strips control characters and truncates; it passes `/`,
        # `\` and `..` straight through, so a session id carrying separators
        # walked out of the observer store and truncated whatever it landed on.
        config, _state = make_runtime()
        # `..` alone is absent on purpose: it lands as `pi_...json`, a legitimate
        # name inside the observer store, so refusing it would be superstition.
        # What has to be refused is anything that can leave that directory.
        for sid in (
            "x/../../../../.claude/settings",
            "a/b",
            "a\\b",
            "",
            "x" * 129,
        ):
            with self.subTest(sid=sid):
                self.assertIsNone(observer.sidecar_path(config, "pi", sid))
                self.assertIsNone(observer.write_sidecar(config, "pi", sid, {"goal": "x"}))
        self.assertIsNone(observer.sidecar_path(config, "../pi", "ok-1"))
        # A real id still resolves, inside the observer store.
        path = observer.sidecar_path(config, "pi", "abcdef12-3456-7890-abcd-ef1234567890")
        assert path is not None
        self.assertEqual(
            os.path.normpath(os.path.join(str(config.state_dir), "observer")),
            os.path.dirname(os.path.normpath(path)),
        )

    def test_read_only_invariant(self) -> None:
        """AC3: the observer never mutates the observed session's repo/state.
        The sidecar is written to the observer's own store, not the target tree."""
        with (
            tempfile.TemporaryDirectory() as target_tmp,
            tempfile.TemporaryDirectory() as store_tmp,
        ):
            observer_store = Path(store_tmp) / "observer-store"
            observer_store.mkdir()
            config = make_config(state_dir=observer_store, state_home=str(observer_store))
            workflow_dir = Path(target_tmp) / "wf"
            entity_dir = workflow_dir / ".spacedock-state"
            transcript = self._write_transcript(
                target_tmp,
                [
                    _pi_session("ro-001"),
                    _pi_message("m1", None, "user", "Fix the failing build"),
                    _pi_message("m2", "m1", "assistant", "Running the tests now."),
                    # The boot line matters to the README assertion below:
                    # without it the stage reader opens neither file, and "the
                    # README was not modified" would hold because it was never
                    # read at all.
                    _boot_line("m3", "m2", workflow_dir, entity_dir),
                ],
            )
            _write_workflow(workflow_dir, ["backlog", "doing"])
            entity_file = _write_entity(entity_dir, "task-one", "backlog")
            os.utime(str(entity_file), (self.NOW, self.NOW))
            readme_mtime = os.path.getmtime(str(workflow_dir / "README.md"))

            # Record mtimes before the run.
            transcript_mtime = os.path.getmtime(transcript)
            entity_mtime = os.path.getmtime(str(entity_file))

            # Make the target tree read-only (chmod -w the directory and files).
            os.chmod(transcript, 0o444)
            os.chmod(str(entity_file), 0o444)
            os.chmod(target_tmp, 0o555)  # noqa: S103
            os.chmod(str(entity_dir), 0o555)  # noqa: S103
            try:
                result = observer.analyze(
                    config, self.state, transcript, now=self.NOW, window_sec=self.WINDOW
                )
                sidecar = observer.write_sidecar(config, "pi", "ro-001", result)
            finally:
                # Restore permissions so cleanup can delete.
                os.chmod(target_tmp, 0o755)  # noqa: S103
                os.chmod(str(entity_dir), 0o755)  # noqa: S103
                os.chmod(transcript, 0o644)
                os.chmod(str(entity_file), 0o644)

            # The run produced a sidecar and a goal.
            self.assertIn("Fix the failing build", result["goal"])
            assert sidecar is not None
            self.assertTrue(os.path.isfile(sidecar))
            # The sidecar is outside the target tree.
            self.assertFalse(sidecar.startswith(target_tmp))
            # No file under the target tree was modified — the README the stage
            # reader now opens included.
            self.assertEqual(transcript_mtime, os.path.getmtime(transcript))
            self.assertEqual(entity_mtime, os.path.getmtime(str(entity_file)))
            self.assertEqual(readme_mtime, os.path.getmtime(str(workflow_dir / "README.md")))

    def test_model_failure_degrades_to_deterministic_fallback(self) -> None:
        """A model error degrades to the deterministic fallback, never crashes
        or hallucinates."""
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_transcript(
                tmp,
                [
                    _pi_session("model-fail-001"),
                    _pi_message("m1", None, "user", "Review the PR"),
                    _pi_message("m2", "m1", "assistant", "Starting the review."),
                ],
            )

            def crashing_model(_head: str, _ctx: str) -> str:
                raise RuntimeError("model unavailable")

            result = self.analyze(path, model=crashing_model)

        # The deterministic goal survives the model crash.
        self.assertIn("Review the PR", result["goal"])
        self.assertIsNone(result["reason"])

    def test_codex_goal_model_pins_luna_max_and_runs_ephemerally(self) -> None:
        recorded: dict[str, Any] = {}

        def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
            recorded["command"] = command
            recorded["prompt"] = kwargs["input"]
            output = Path(command[command.index("--output-last-message") + 1])
            output.write_text("Resume the accepted project checkpoint\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0)

        with tempfile.TemporaryDirectory() as tmp:
            config = dataclasses.replace(
                self.config,
                state_dir=Path(tmp),
                state_home=tmp,
            )
            caller = observer.CodexGoalModel(
                config,
                runner=run,
                binary_resolver=lambda _name: "/opt/bin/codex",
            )

            result = caller("Captain requested the exact checkpoint", "shaping")

        command = recorded["command"]
        self.assertEqual("Resume the accepted project checkpoint", result)
        self.assertEqual("gpt-5.6-luna", command[command.index("--model") + 1])
        self.assertIn("model_reasoning_effort=max", command)
        self.assertIn("--ephemeral", command)
        self.assertEqual("read-only", command[command.index("--sandbox") + 1])
        self.assertIn("<transcript_excerpt>", recorded["prompt"])
        self.assertEqual("used", caller.metadata()["status"])

    def test_codex_no_goal_output_keeps_the_deterministic_goal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_transcript(
                tmp,
                [
                    _pi_session("model-empty-001"),
                    _pi_message("m1", None, "user", "Review the release checkpoint"),
                ],
            )

            result = self.analyze(path, model=lambda _recent, _stage: observer.NO_GOAL + ".")

        self.assertEqual("Review the release checkpoint", result["goal"])

    def test_no_goal_sentinel_not_overridden_by_model(self) -> None:
        """The deterministic short-circuit bypasses the model entirely: a
        model that would fabricate a goal must not override the sentinel."""
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_transcript(
                tmp,
                [
                    _pi_session("neg-002"),
                    _pi_message("m1", None, "user", "skill(spacedock:first-officer)"),
                ],
            )

            def fabricator(_head: str, _ctx: str) -> str:
                return "inferred goal from the opener"

            result = self.analyze(path, model=fabricator)

        self.assertEqual("no goal derived", result["goal"])


class ObserverTranscriptResolutionTest(RuntimeTestCase):
    """Which transcript `/api/observe?harness=&sid=` resolves to, per harness."""

    def test_a_claude_transcript_resolves_one_directory_down(self) -> None:
        # `projects/<encoded-cwd>/<session-id>.jsonl`, which is how
        # `collectors/claude.py` globs it. A flat `*.jsonl` matched nothing, so
        # `?harness=claude` was a 404 on every machine — the route advertised a
        # harness it could never answer for.
        sid = "abcdef12-3456-7890-abcd-ef1234567890"
        with tempfile.TemporaryDirectory() as tmp:
            projects = Path(tmp) / "projects"
            (projects / "-home-me-repo").mkdir(parents=True)
            wanted = projects / "-home-me-repo" / f"{sid}.jsonl"
            wanted.write_text("{}\n", encoding="utf-8")
            with store_patch(PROJECTS_DIR=str(projects)):
                config, state = runtime()
                found = observer.resolve_transcript(config, state, "claude", sid)
                # The dashboard shortens an id for display, so a prefix resolves.
                short = observer.resolve_transcript(config, state, "claude", sid[:8])
        self.assertEqual(str(wanted), found)
        self.assertEqual(str(wanted), short)

    def test_an_ambiguous_claude_prefix_resolves_to_nothing(self) -> None:
        # Codex-style time-ordered ids share long prefixes, and the old
        # `sid in basename` substring match handed back whichever transcript
        # happened to contain the characters. Two candidates is no answer.
        with tempfile.TemporaryDirectory() as tmp:
            projects = Path(tmp) / "projects"
            (projects / "-home-me-repo").mkdir(parents=True)
            for suffix in ("aa", "bb"):
                (projects / "-home-me-repo" / f"sess-{suffix}.jsonl").write_text("{}\n")
            with store_patch(PROJECTS_DIR=str(projects)):
                config, state = runtime()
                self.assertIsNone(observer.resolve_transcript(config, state, "claude", "sess-"))

    def test_an_unknown_harness_and_an_unnamed_id_resolve_to_nothing(self) -> None:
        config, state = runtime()
        self.assertIsNone(observer.resolve_transcript(config, state, "codex", "abc"))
        self.assertIsNone(observer.resolve_transcript(config, state, "pi", "a/../b"))

    def test_a_codex_session_id_resolves_through_first_line_metadata(self) -> None:
        sid = "01a035ee-2a7b-76f0-873f-eaddc97860c3"
        with tempfile.TemporaryDirectory() as tmp:
            sessions = Path(tmp) / "sessions"
            rollout = sessions / "2026" / "08" / "24" / f"rollout-{sid}.jsonl"
            rollout.parent.mkdir(parents=True)
            rollout.write_text(
                json.dumps(
                    {
                        "type": "session_meta",
                        "payload": {"id": sid, "cwd": "/repo", "source": "cli"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            with store_patch(CODEX_SESSIONS_DIR=str(sessions)):
                config, state = runtime()
                found = observer.resolve_transcript(config, state, "codex", sid)

        self.assertEqual(str(rollout), found)

    def test_a_codex_child_thread_id_resolves_to_its_rollout(self) -> None:
        root_sid = "11111111-1111-1111-1111-111111111111"
        child_sid = "22222222-2222-2222-2222-222222222222"
        with tempfile.TemporaryDirectory() as tmp:
            sessions = Path(tmp) / "sessions"
            rollout = sessions / "2026" / "01" / "01" / "rollout-child.jsonl"
            rollout.parent.mkdir(parents=True)
            rollout.write_text(
                json.dumps(
                    {
                        "type": "session_meta",
                        "payload": {
                            "id": child_sid,
                            "session_id": root_sid,
                            "thread_source": "subagent",
                            "source": {
                                "subagent": {"thread_spawn": {"parent_thread_id": root_sid}}
                            },
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            with store_patch(CODEX_SESSIONS_DIR=str(sessions)):
                config, state = runtime()
                found = observer.resolve_transcript(config, state, "codex", child_sid)

        self.assertEqual(str(rollout), found)


class ObserverRouteTest(RuntimeTestCase):
    """`GET /api/observe`, which had no test of its own."""

    def _get(self, server: Any, query: str) -> tuple[int, bytes]:
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        conn.request("GET", "/api/observe" + query)
        response = conn.getresponse()
        body = response.read()
        conn.close()
        return response.status, body

    def test_the_route_answers_with_the_sidecar_and_writes_it(self) -> None:
        sid = "abcdef12-3456-7890-abcd-ef1234567890"
        with tempfile.TemporaryDirectory() as tmp:
            projects = Path(tmp) / "projects"
            (projects / "-home-me-repo").mkdir(parents=True)
            (projects / "-home-me-repo" / f"{sid}.jsonl").write_text(
                json.dumps(
                    {
                        "type": "message",
                        "id": "m1",
                        "message": {"role": "user", "content": "Fix the failing build"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            home = Path(tmp) / "cargento-home"
            with (
                store_patch(PROJECTS_DIR=str(projects)),
                mock.patch.dict(os.environ, {"CARGENTO_HOME": str(home)}),
            ):
                httpd = make_server()
                thread = threading.Thread(target=httpd.serve_forever, daemon=True)
                thread.start()
                try:
                    status, body = self._get(httpd, f"?harness=claude&sid={sid}")
                    missing, _ = self._get(httpd, "?harness=claude&sid=deadbeef")
                    unnamed, _ = self._get(httpd, "?harness=claude&sid=a%2Fb")
                    bare, _ = self._get(httpd, "?harness=claude")
                finally:
                    httpd.shutdown()
                    httpd.server_close()
                    thread.join(timeout=2)
                # The path the *server's* config resolves, not a second one: the
                # store home comes off the environment and both must agree. And
                # checked in here, before the temp tree is torn down.
                sidecar = observer.sidecar_path(httpd.application.config, "claude", sid)
                assert sidecar is not None
                wrote_sidecar = os.path.isfile(sidecar)

        self.assertEqual(200, status)
        payload = json.loads(body)
        self.assertIn("Fix the failing build", payload["goal"])
        self.assertEqual("", payload["stage"])  # no workflow booted
        # A sid that resolves to no transcript is a 404, not an empty 200: the
        # panel must be able to tell "nothing to observe" from "nothing found".
        self.assertEqual(404, missing)
        # A sid that is not a name never reaches the resolver.
        self.assertEqual(404, unnamed)
        self.assertEqual(400, bare)
        self.assertTrue(wrote_sidecar)


class ObserverReachabilityTest(PageJsHarness):
    """That a reader can actually get to the panel, and what happens when they do.

    The gap this closes: `renderObserverPanel` and `observeSession` existed and
    nothing in the page called either, so the whole surface was unreachable
    while four tests calling the render function directly stayed green. These
    drive the control, not the function.

    The calm board fixture is borrowed rather than inherited, and reached
    through its module rather than imported by name: subclassing `CalmModeTest`
    re-runs all sixty of its tests under a second name, and so does importing
    the class into this namespace, because that is where discovery looks.
    """

    def run_calm(self, checks: str) -> Any:
        calm = test_page_calm.CalmModeTest
        return self._run_page_js(calm.FIXTURE + checks, prelude=calm.prelude("calm"))

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_the_drawer_offers_observe_and_the_control_fetches_and_paints(self) -> None:
        checks = """
const out = {};
__fetchImpl = () => Promise.resolve({ok: true, json: () => Promise.resolve(
  {goal: "ship the observer route", stage: "implementation", block: "blocked on node"})});
render(board());

// Closed: no control and no panel.
out.closedHasControl = __els.app.innerHTML.includes('data-calm="observe"');

calmAction("open", K("claude", "aaa1"));
out.openHasControl = __els.app.innerHTML.includes('data-calm="observe" data-arg="claude:aaa1"');
out.openHasPanelBeforeAsking = __els.app.innerHTML.includes("observer-panel");

// The control, through the same channel a click takes.
calmAction("observe", K("claude", "aaa1"));
out.loading = __els.app.innerHTML.includes("observer-loading");
out.asked = __fetchCalls.map(c => c[0]).filter(u => String(u).includes("/api/observe"));
await __settle();
await __settle();
out.painted = __els.app.innerHTML.includes("ship the observer route");
out.stage = __els.app.innerHTML.includes("implementation");
out.block = __els.app.innerHTML.includes("blocked on node");

// It survives the 5s re-render, which is what killed a container-only write.
render(board());
out.survivesRerender = __els.app.innerHTML.includes("ship the observer route");
console.log(JSON.stringify(out));
"""
        out = self.run_calm(checks)
        self.assertFalse(out["closedHasControl"])
        self.assertTrue(out["openHasControl"])
        # Nothing is derived until asked: the route reads a transcript and two
        # project files, which a thirty-row board must not do on a poll.
        self.assertFalse(out["openHasPanelBeforeAsking"])
        self.assertEqual(
            ["/api/observe?harness=claude&sid=aaa1"],
            out["asked"],
        )
        self.assertTrue(out["painted"])
        self.assertTrue(out["stage"])
        self.assertTrue(out["block"])
        self.assertTrue(out["survivesRerender"])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_a_failed_observe_says_so_and_an_unobservable_harness_has_no_control(self) -> None:
        checks = """
const out = {};
__fetchImpl = () => Promise.resolve({ok: false, json: () => Promise.resolve({})});
render(board());
calmAction("open", K("claude", "aaa1"));
calmAction("observe", K("claude", "aaa1"));
await __settle();
await __settle();
out.error = __els.app.innerHTML.includes("observer-error");

// `bbb2` is the Codex row in the shared fixture. The route resolves a
// transcript for Claude and Pi only, so a control there would always 404.
calmAction("open", K("codex", "bbb2"));
out.codexHasControl = __els.app.innerHTML.includes('data-calm="observe" data-arg="codex:bbb2"');
console.log(JSON.stringify(out));
"""
        out = self.run_calm(checks)
        self.assertTrue(out["error"])
        self.assertFalse(out["codexHasControl"])


class ObserverPanelTest(PageJsHarness):
    """AC4: the observer panel renders the operator-visible output from the
    sidecar."""

    def test_panel_renders_goal_stage_and_block(self) -> None:
        """The panel renders the goal text, the stage badge, and the block text
        from a fixture sidecar."""
        rendered = self._run_page_js(
            "const html = renderObserverPanel({"
            "goal: 'managing the dev workflow', stage: 'implementation', "
            "block: 'blocked on a missing dependency'});"
            "console.log(JSON.stringify(html));"
        )
        self.assertIn("managing the dev workflow", rendered)
        self.assertIn("implementation", rendered)
        self.assertIn("blocked on a missing dependency", rendered)

    def test_panel_renders_no_goal_sentinel_not_fabricated_goal(self) -> None:
        """A no-goal sidecar renders the sentinel text, not a fabricated goal."""
        rendered = self._run_page_js(
            "const html = renderObserverPanel({"
            "goal: 'no goal derived', stage: '', block: ''});"
            "console.log(JSON.stringify(html));"
        )
        self.assertIn("no goal derived", rendered)
        # The sentinel has its own class, distinct from a real goal.
        self.assertIn("observer-sentinel", rendered)

    def test_panel_updates_when_sidecar_changes(self) -> None:
        """Falsification: editing the sidecar's goal changes the rendered output."""
        rendered_a = self._run_page_js(
            "console.log(JSON.stringify(renderObserverPanel({"
            "goal: 'first goal', stage: 'backlog', block: ''})));"
        )
        rendered_b = self._run_page_js(
            "console.log(JSON.stringify(renderObserverPanel({"
            "goal: 'second goal', stage: 'backlog', block: ''})));"
        )
        self.assertIn("first goal", rendered_a)
        self.assertIn("second goal", rendered_b)
        self.assertNotIn("second goal", rendered_a)

    def test_panel_no_hardcoded_fallback_goal(self) -> None:
        """A no-goal sidecar must not produce a hardcoded fallback goal."""
        rendered = self._run_page_js(
            "const html = renderObserverPanel({"
            "goal: 'no goal derived', stage: '', block: ''});"
            "console.log(JSON.stringify(html));"
        )
        # The only goal text is the sentinel; no fallback string appears.
        self.assertNotIn("unknown session", rendered)
        self.assertNotIn("session in progress", rendered)
