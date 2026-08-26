from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from capcut_caption_fade_apply import apply_caption_fade, companion_drafts  # noqa: E402


class CapCutCaptionFadeApplyTests(unittest.TestCase):
    def test_changes_text_animation_and_preserves_video_animation(self) -> None:
        draft = {
            "materials": {
                "material_animations": [
                    {
                        "id": "text-animation",
                        "animations": [{"name": "하나씩", "duration": 33_000}],
                    },
                    {
                        "id": "video-animation",
                        "animations": [{"name": "줌 1", "duration": 4_000_000}],
                    },
                ]
            },
            "tracks": [
                {
                    "type": "text",
                    "segments": [
                        {"id": "caption-1", "extra_material_refs": ["text-animation"]}
                    ],
                },
                {
                    "type": "video",
                    "segments": [
                        {"id": "scene-1", "extra_material_refs": ["video-animation"]}
                    ],
                },
            ],
        }

        result = apply_caption_fade(draft)
        animations = result["draft"]["materials"]["material_animations"]
        self.assertEqual(animations[0]["animations"][0]["name"], "페이드 인")
        self.assertEqual(animations[1]["animations"][0]["name"], "줌 1")
        self.assertEqual(draft["materials"]["material_animations"][0]["animations"][0]["name"], "하나씩")
        self.assertEqual(result["segments"], 1)
        self.assertEqual(result["video_animations"], ["줌 1"])

    def test_companion_drafts_include_capcut_recovery_copies(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            primary = root / "draft_content.json"
            recovery = root / "draft_content.json.bak"
            template = root / "template-2.tmp"
            for path in (primary, recovery, template):
                path.write_text("{}", encoding="utf-8")
            self.assertEqual(
                companion_drafts(primary), [primary, recovery, template]
            )


if __name__ == "__main__":
    unittest.main()
