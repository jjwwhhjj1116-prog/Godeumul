import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from subtitle_split import atoms, dangling_determiners, pack  # noqa: E402


class SubtitleSplitTests(unittest.TestCase):
    def split(self, text: str) -> list[str]:
        return pack(atoms(text.split()), max_chars=16, target=9)

    def test_binds_demonstrative_to_following_noun_phrase(self):
        lines = self.split("대체 고대 그리스인은 이 기계로 무엇을 계산했던 걸까요?")
        self.assertTrue(any("이 기계로" in line for line in lines), lines)
        self.assertFalse(dangling_determiners(lines), lines)

    def test_binds_geu_to_following_location_phrase(self):
        lines = self.split("배 안에는 청동상과 대리석상이 쏟아져 있었고, 그 틈에서 큰 사전만 한 부식 덩어리도 건져 올렸어요.")
        self.assertTrue(any("그 틈에서" in line for line in lines), lines)
        self.assertFalse(dangling_determiners(lines), lines)

    def test_reports_dangling_determiner(self):
        self.assertEqual(dangling_determiners(["대체 고대 그리스인은 이", "기계로 무엇을"]),
                         [(1, "대체 고대 그리스인은 이")])


if __name__ == "__main__":
    unittest.main()
