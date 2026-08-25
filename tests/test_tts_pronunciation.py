from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from tts_pronunciation import (  # noqa: E402
    PronunciationDictionary,
    integer_to_korean,
    original_to_spoken_map,
)


class PronunciationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dictionary = PronunciationDictionary(ROOT / "tts_pronunciation.json")

    def test_original_and_tts_text_are_separate(self) -> None:
        original = "1974년, 방아쇠와 AI를 조사했습니다."
        tts_text, changes = self.dictionary.apply(original)
        self.assertEqual(original, "1974년, 방아쇠와 AI를 조사했습니다.")
        self.assertEqual(tts_text, "천구백칠십사년, 방아쐬와 에이아이를 조사했습니다.")
        self.assertEqual(len(changes), 3)

    def test_korean_integer_groups(self) -> None:
        self.assertEqual(integer_to_korean(2002), "이천이")
        self.assertEqual(integer_to_korean(700000), "칠십만")
        self.assertEqual(integer_to_korean(5625), "오천육백이십오")

    def test_original_caption_maps_to_longer_spoken_text(self) -> None:
        original = "1974년 방아쇠와 AI"
        spoken, _ = self.dictionary.apply(original)
        mapping = original_to_spoken_map(original, spoken)
        self.assertEqual(len(mapping), len("1974년방아쇠와AI"))
        self.assertEqual(mapping[0][0], 0)
        self.assertGreater(mapping[-1][1], mapping[-2][1])


if __name__ == "__main__":
    unittest.main()
