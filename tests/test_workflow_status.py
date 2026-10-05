import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from workflow_status import FILES, snapshot, check_command, run_check, main


class WorkflowStatusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ep = Path(self.tmp.name)

    def put(self, name, data):
        p = self.ep / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def test_presence_never_means_verified_or_complete(self):
        for name in FILES.values():
            self.put(name, {"status": "PASS"})
        with patch("workflow_status.subprocess.run", side_effect=AssertionError("no process")), \
             patch.object(Path, "rglob", side_effect=AssertionError("no recursive scan")):
            report = snapshot(self.ep)
        self.assertFalse(report["verified"])
        self.assertEqual(report["completion"], "NOT_ESTABLISHED")
        self.assertEqual(report["checks"], "NOT_RUN")

    def test_explicit_current_failure_and_pending_retry(self):
        name = "qa/20261002_005_원본검수.json"
        self.put(FILES["mode"], {"mode": "T2V_OUTPUT_FRAME_CHAIN_LOCKED",
                                 "progress_note": name})
        self.put(name, {"status": "FAIL_ARTIFACT_DRIFT", "retry_authorized": False,
                       "retry_authorization_state": "QUESTION_SENT_PENDING_USER_REPLY"})
        report = snapshot(self.ep)
        self.assertEqual(report["mode"], "T2V_OUTPUT_FRAME_CHAIN_LOCKED")
        self.assertFalse(report["findings"][0]["retry_authorized"])
        self.assertEqual(report["blocker"], "RECORDED_FAILURE_OR_AUTHORIZATION_PENDING")

    def test_unreferenced_old_005_does_not_poison_other_episode(self):
        self.put("qa/20261002_005_원본검수.json", {"status": "FAIL"})
        self.put(FILES["mode"], {"mode": "SHARED_FRAME_CHAIN", "progress_note": ""})
        self.assertEqual(snapshot(self.ep)["findings"], [])
        self.assertEqual(snapshot(self.ep)["mode"], "SHARED_FRAME_CHAIN")

    def test_bad_json_is_unreadable_not_success(self):
        (self.ep / FILES["mode"]).write_text("{bad", encoding="utf-8")
        report = snapshot(self.ep)
        self.assertEqual(report["blocker"], "UNREADABLE_RECORD")
        self.assertEqual(report["records"]["mode"]["state"], "READ_ERROR")

    def fill_current_records(self):
        for name in FILES.values():
            self.put(name, {"status": "PASS"})

    def test_missing_explicit_qa_is_missing_evidence(self):
        self.fill_current_records()
        self.put(FILES["mode"], {"progress_note": "qa/current.json"})
        report = snapshot(self.ep)
        self.assertEqual(report["blocker"], "MISSING_EVIDENCE")
        self.assertEqual(report["records"]["qa/current.json"]["state"], "MISSING")
        self.assertIn("qa/current.json", report["next_action"])

    def test_core_review_failure_needs_no_progress_note_reference(self):
        self.fill_current_records()
        self.put(FILES["review"], {"status": "FAIL_SEMANTIC"})
        report = snapshot(self.ep)
        self.assertEqual(report["blocker"], "RECORDED_FAILURE_OR_AUTHORIZATION_PENDING")
        self.assertEqual(report["findings"][0]["status"], "FAIL_SEMANTIC")

    def test_direct_scene_verdicts_are_not_hidden_by_top_level_pass(self):
        self.fill_current_records()
        self.put(FILES["review"], {"status": "PASS", "scenes": {"006": {"gate": "FAIL"}}})
        report = snapshot(self.ep)
        self.assertEqual(report["findings"][0]["scene"], "006")
        self.assertFalse(report["verified"])

    def test_history_prose_does_not_create_false_failure(self):
        self.fill_current_records()
        self.put(FILES["review"], {"status": "PASS", "history": [{"status": "FAIL"}],
                                  "note": "old FAIL repaired"})
        self.assertEqual(snapshot(self.ep)["findings"], [])

    def test_direct_boundary_failure_is_not_hidden_by_scene_pass(self):
        self.fill_current_records()
        self.put(FILES["chain"], {"status": "PASS", "scenes": {"001": {"status": "PASS"}},
                                 "boundaries": [{"after": 1, "status": "FAIL"}]})
        report = snapshot(self.ep)
        self.assertEqual(report["findings"][0]["boundary"], "0")
        self.assertEqual(report["blocker"], "RECORDED_FAILURE_OR_AUTHORIZATION_PENDING")

    def test_cli_displays_blocker_before_recorded_pass(self):
        self.fill_current_records()
        self.put(FILES["review"], {"status": "FAIL"})
        output = io.StringIO()
        with patch.object(sys, "argv", ["workflow_status.py", str(self.ep)]), \
             patch("sys.stdout", output):
            self.assertEqual(main(), 0)  # successful read, not QA PASS
        first_line = output.getvalue().splitlines()[0]
        self.assertIn(": RECORDED_FAILURE_OR_AUTHORIZATION_PENDING", first_line)
        self.assertFalse(first_line.startswith(f"{self.ep.name}: PASS"))

    def test_invalid_qa_reference_does_not_read_outside_episode(self):
        self.put(FILES["mode"], {"progress_note": "qa/../../private.json"})
        report = snapshot(self.ep)
        self.assertEqual(report["findings"][0]["status"], "INVALID_REFERENCE")
        self.assertNotIn("qa/../../private.json", report["records"])

    def test_corrupt_explicit_qa_is_unreadable(self):
        self.fill_current_records()
        self.put(FILES["mode"], {"progress_note": "qa/current.json"})
        (self.ep / "qa").mkdir()
        (self.ep / "qa/current.json").write_text("{bad", encoding="utf-8")
        self.assertEqual(snapshot(self.ep)["blocker"], "UNREADABLE_RECORD")

    def test_commands_preserve_gate_mode_and_inputs(self):
        cmd = check_command(self.ep, "script")
        self.assertEqual(cmd[-3:], [str(self.ep / FILES["script"]), "--review",
                                   str(self.ep / FILES["script_review"])])
        self.assertEqual(check_command(self.ep, "continuity")[-2:], ["--phase", "release"])
        self.assertTrue(check_command(self.ep, "sources")[-2].endswith("semantic_video_gate.py"))

    @patch("workflow_status.subprocess.run")
    def test_check_failures_and_bounded_report(self, run):
        run.return_value = subprocess.CompletedProcess([], 1, "x" * 9000, "")
        report = run_check(self.ep, "sources")
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(len(report["output"]), 6000)
        self.assertTrue(report["output_truncated"])
        self.assertEqual(run.call_args.kwargs["timeout"], 90)

    @patch("workflow_status.subprocess.run")
    def test_timeout_does_not_pass(self, run):
        run.side_effect = subprocess.TimeoutExpired("gate", 90)
        self.assertEqual(run_check(self.ep, "script")["status"], "TIMEOUT")

    @patch("workflow_status.subprocess.run")
    def test_pass_is_scoped_to_executed_gate(self, run):
        run.return_value = subprocess.CompletedProcess([], 0, "PASS", "")
        self.assertEqual(run_check(self.ep, "script")["status"], "PASS")
        self.assertFalse(snapshot(self.ep)["verified"])


if __name__ == "__main__":
    unittest.main()
