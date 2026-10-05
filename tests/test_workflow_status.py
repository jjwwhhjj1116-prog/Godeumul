import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from workflow_status import FILES, snapshot, check_command, run_check


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
