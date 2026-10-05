import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from capcut_build import FFPROBE_TIMEOUT_SECONDS, probe_video_metadata


class CapCutProbeTests(unittest.TestCase):
    path = Path("source.mp4")

    def reply(self, payload):
        return subprocess.CompletedProcess([], 0, json.dumps(payload), "")

    @patch("capcut_build.subprocess.run")
    def test_one_json_process_returns_both_fields_with_timeout(self, run):
        run.return_value = self.reply({"format": {"duration": "8.000"}, "streams": [
            {"codec_type": "video"}, {"codec_type": "audio"}]})
        self.assertEqual(probe_video_metadata(self.path), {"duration": 8.0, "has_audio": True})
        run.assert_called_once()
        self.assertEqual(run.call_args.kwargs["timeout"], FFPROBE_TIMEOUT_SECONDS)
        self.assertTrue(run.call_args.kwargs["check"])
        self.assertIn("format=duration:stream=codec_type", run.call_args.args[0])

    @patch("capcut_build.subprocess.run")
    def test_valid_silent_video_is_not_probe_failure(self, run):
        run.return_value = self.reply({"format": {"duration": "6"},
                                       "streams": [{"codec_type": "video"}]})
        self.assertEqual(probe_video_metadata(self.path), {"duration": 6.0, "has_audio": False})

    @patch("capcut_build.subprocess.run")
    def test_invalid_json_blocks(self, run):
        run.return_value = subprocess.CompletedProcess([], 0, "not json", "")
        with self.assertRaisesRegex(ValueError, "비정상 메타데이터.*source.mp4"):
            probe_video_metadata(self.path)

    @patch("capcut_build.subprocess.run")
    def test_invalid_duration_or_streams_block(self, run):
        cases = [None, {}, {"format": {"duration": "8"}, "streams": []},
                 {"format": {"duration": "8"}, "streams": [{"codec_type": "audio"}]}]
        cases += [{"format": {"duration": value}, "streams": [{"codec_type": "video"}]}
                  for value in ("N/A", "nan", "inf", "0", "-1", None)]
        for payload in cases:
            with self.subTest(payload=payload):
                run.return_value = self.reply(payload)
                with self.assertRaisesRegex(ValueError, "비정상 메타데이터"):
                    probe_video_metadata(self.path)

    @patch("capcut_build.subprocess.run")
    def test_timeout_blocks(self, run):
        run.side_effect = subprocess.TimeoutExpired("ffprobe", FFPROBE_TIMEOUT_SECONDS)
        with self.assertRaisesRegex(ValueError, "시간 초과.*source.mp4"):
            probe_video_metadata(self.path)

    @patch("capcut_build.subprocess.run")
    def test_nonzero_exit_includes_reason_and_blocks(self, run):
        run.side_effect = subprocess.CalledProcessError(1, "ffprobe", stderr="moov atom not found")
        with self.assertRaisesRegex(ValueError, "exit 1.*moov atom not found"):
            probe_video_metadata(self.path)

    @patch("capcut_build.subprocess.run")
    def test_missing_binary_blocks(self, run):
        run.side_effect = FileNotFoundError("ffprobe unavailable")
        with self.assertRaisesRegex(ValueError, "실행 불가"):
            probe_video_metadata(self.path)


if __name__ == "__main__":
    unittest.main()
