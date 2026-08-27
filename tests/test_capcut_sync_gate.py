from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from capcut_build import validate_sync_document  # noqa: E402


class CapCutSyncGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scenes = {
            "1": {"duration": 2.0, "text": "첫 번째 문장입니다."},
            "2": {"duration": 2.0, "text": "두 번째 문장입니다."},
        }
        self.cues = [
            {"n": 1, "raw": "첫 번째 문장입니다.", "text": "첫 번째 문장입니다."},
            {"n": 2, "raw": "두 번째 문장입니다.", "text": "두 번째 문장입니다."},
        ]
        self.document = {
            "source": "elevenlabs-forced-alignment",
            "count": 2,
            "cues": [
                {"n": 1, "scene": 1, "raw": "첫 번째 문장입니다.",
                 "text": "첫 번째 문장입니다.", "start": 0.2, "end": 1.8},
                {"n": 2, "scene": 2, "raw": "두 번째 문장입니다.",
                 "text": "두 번째 문장입니다.", "start": 2.2, "end": 3.8},
            ],
        }

    def test_accepts_complete_forced_alignment(self) -> None:
        self.assertEqual(validate_sync_document(self.document, self.cues, self.scenes), [])

    def test_rejects_approximate_or_unknown_source(self) -> None:
        document = copy.deepcopy(self.document)
        document["source"] = "character-ratio"
        failures = validate_sync_document(document, self.cues, self.scenes)
        self.assertTrue(any("forced alignment" in failure for failure in failures))

    def test_rejects_overlap_and_scene_boundary_escape(self) -> None:
        document = copy.deepcopy(self.document)
        document["cues"][1]["start"] = 1.7
        failures = validate_sync_document(document, self.cues, self.scenes)
        self.assertTrue(any("겹침" in failure for failure in failures))
        self.assertTrue(any("장면 경계" in failure for failure in failures))

    def test_rejects_caption_text_mismatch(self) -> None:
        document = copy.deepcopy(self.document)
        document["cues"][1]["raw"] = "전혀 다른 문장입니다."
        failures = validate_sync_document(document, self.cues, self.scenes)
        self.assertTrue(any("텍스트 불일치" in failure for failure in failures))
        self.assertTrue(any("TTS 장면 원문" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
