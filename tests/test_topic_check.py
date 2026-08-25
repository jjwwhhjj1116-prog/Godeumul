import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "topic_check.py"
VALID_CARD = ROOT / "산출물" / "EP02_마왕퇴한묘" / "00.주제카드.json"


class TopicCheckTests(unittest.TestCase):
    def run_card(self, data: dict) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "00.주제카드.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(TOOL), str(path)],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=False,
            )

    def test_accepts_artifact_first_topic_card(self) -> None:
        data = json.loads(VALID_CARD.read_text(encoding="utf-8"))
        result = self.run_card(data)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_predecided_sensational_mechanism(self) -> None:
        data = json.loads(VALID_CARD.read_text(encoding="utf-8"))
        data["one_sentence_promise"] = "진공 밀폐로 100% 영구 보존한 완벽한 기술"
        result = self.run_card(data)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("주제 선결론·과장", result.stdout)


if __name__ == "__main__":
    unittest.main()
