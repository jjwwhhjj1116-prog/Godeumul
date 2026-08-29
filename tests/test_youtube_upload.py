from __future__ import annotations

import sys
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from youtube_upload import build_body, resolve_publish_datetime  # noqa: E402
from youtube_status_update import writable_status  # noqa: E402


class YoutubeUploadTests(unittest.TestCase):
    def test_explicit_schedule_override_requires_flag(self) -> None:
        from datetime import datetime, timedelta, timezone

        kst = timezone(timedelta(hours=9))
        now = datetime(2026, 8, 30, 0, 0, tzinfo=kst)
        with self.assertRaises(SystemExit):
            resolve_publish_datetime("2026-08-30 10:00", now)
        resolved = resolve_publish_datetime(
            "2026-08-30 10:00", now, allow_policy_override=True,
        )
        self.assertEqual(resolved.strftime("%Y-%m-%d %H:%M"), "2026-08-30 10:00")

    def test_upload_body_declares_synthetic_media(self) -> None:
        body = build_body({
            "제목": "테스트 제목",
            "설명": "AI 재현물입니다.",
            "태그": ["고대유물"],
        }, "private", None)
        self.assertIs(body["status"]["containsSyntheticMedia"], True)
        self.assertEqual(body["status"]["privacyStatus"], "private")

    def test_existing_status_update_drops_read_only_fields(self) -> None:
        status = writable_status({
            "privacyStatus": "private",
            "uploadStatus": "processed",
            "containsSyntheticMedia": True,
        })
        self.assertEqual(status, {
            "privacyStatus": "private",
            "containsSyntheticMedia": True,
        })


if __name__ == "__main__":
    unittest.main()
