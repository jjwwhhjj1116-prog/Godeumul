from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from capcut_final_lock import validate_capcut_lock  # noqa: E402


class CapCutFinalLockTests(unittest.TestCase):
    def test_rejects_missing_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ep = Path(tmp)
            report = validate_capcut_lock(ep)
            self.assertFalse(report.passed)
            self.assertTrue(any("잠금 없음" in failure for failure in report.failures))

    def test_accepts_matching_capcut_export_hash_and_gui_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ep = Path(tmp)
            video = ep / "완성본_EP99_capcut.mp4"
            video.write_bytes(b"capcut-export-test")
            digest = hashlib.sha256(video.read_bytes()).hexdigest()
            (ep / "05.캡컷마감잠금.json").write_text(json.dumps({
                "status": "PASS",
                "editor": "CapCut",
                "project_name": "EP99 QA",
                "video": video.name,
                "video_sha256": digest,
                "checks": {
                    "caption_style_verified": True,
                    "caption_sync_verified": True,
                    "motion_finish_verified": True,
                    "full_playback_verified": True,
                    "audio_policy_verified": True,
                },
            }, ensure_ascii=False), encoding="utf-8")
            report = validate_capcut_lock(ep, video)
            self.assertTrue(report.passed, report.failures)

    def test_rejects_replaced_video_after_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ep = Path(tmp)
            video = ep / "완성본_EP99_capcut.mp4"
            video.write_bytes(b"first")
            (ep / "05.캡컷마감잠금.json").write_text(json.dumps({
                "status": "PASS",
                "editor": "CapCut",
                "project_name": "EP99 QA",
                "video": video.name,
                "video_sha256": hashlib.sha256(video.read_bytes()).hexdigest(),
                "checks": {key: True for key in (
                    "caption_style_verified", "caption_sync_verified",
                    "motion_finish_verified", "full_playback_verified",
                    "audio_policy_verified",
                )},
            }, ensure_ascii=False), encoding="utf-8")
            video.write_bytes(b"replaced")
            report = validate_capcut_lock(ep, video)
            self.assertFalse(report.passed)
            self.assertTrue(any("SHA-256" in failure for failure in report.failures))


if __name__ == "__main__":
    unittest.main()
