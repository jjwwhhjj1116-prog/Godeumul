import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from script_tone_check import analyze  # noqa: E402
from subtitle_split import atoms  # noqa: E402


class ScriptToneCheckTests(unittest.TestCase):
    def test_rejects_three_formal_endings_in_a_row(self):
        report = analyze("문이 열렸습니다. 유물이 나왔습니다. 색이 사라졌습니다.")
        self.assertEqual(report.max_formal_run, 3)
        self.assertTrue(report.failures)

    def test_accepts_conversational_rhythm(self):
        text = (
            "문이 열렸습니다. 그런데 색이 바로 들뜨기 시작했죠. "
            "잘못하면 싹 다 사라질 수도 있거든요. 그래서 기다리는 겁니다. "
            "정작 중요한 건 무엇을 찾느냐만이 아니에요. "
            "그 흔적을 어떻게 지킬 것인가, 바로 그게 문제인 셈이죠. "
            "이제 이유가 보이죠. 함부로 열 수는 없고요."
        )
        report = analyze(text)
        self.assertLess(report.max_formal_run, 3)
        self.assertFalse(report.failures)
        self.assertIn("싹 다", report.emphasis_hits)

    def test_keeps_emphasis_phrase_in_one_caption_atom(self):
        self.assertEqual(atoms(["증거를", "싹", "다", "망가뜨립니다."]),
                         ["증거를", "싹 다", "망가뜨립니다."])

    def test_decimal_does_not_create_fake_sentence_boundary(self):
        report = analyze("길이 7.34미터입니다. 그런데 훨씬 긴 두루마리였죠.")
        self.assertEqual(report.sentences, [
            "길이 7.34미터입니다.",
            "그런데 훨씬 긴 두루마리였죠.",
        ])


if __name__ == "__main__":
    unittest.main()
