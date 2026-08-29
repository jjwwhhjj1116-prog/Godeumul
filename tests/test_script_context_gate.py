import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from script_context_gate import validate_context_review  # noqa: E402
from tts_generate import parse_script  # noqa: E402


SCRIPT = (
    "무덤에서 한 여성의 몸이 발견됐습니다. 왜 이 몸만 남았을까요?\n\n"
    "그런데 관 주변에는 생활용품도 놓여 있었죠. 이것부터 살펴보겠습니다."
)


def review_for(script: Path) -> dict:
    return {
        "version": 1,
        "script": script.name,
        "script_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
        "reviewer": "humanizer-ko + godeumul-context-qa",
        "status": "PASS",
        "checks": {
            "paragraph_roles_and_flow": "PASS",
            "adjacent_sentence_relations": "PASS",
            "connector_deletion_test": "PASS",
            "duplicate_information": "PASS",
            "tts_release_gate": "PASS",
        },
        "paragraphs": [
            {"n": 1, "role": "QUESTION", "summary": "발견과 질문"},
            {"n": 2, "role": "EVIDENCE", "summary": "주변 증거 조사"},
        ],
        "transitions": [
            {
                "from": 1,
                "to": 2,
                "relation": "질문에서 증거 조사",
                "reason": "보존 질문에 답하기 전 주변 증거를 확인한다.",
                "status": "PASS",
            }
        ],
        "connectors": [
            {
                "sentence": 3,
                "text": "그런데",
                "relation": "추가 반전",
                "decision": "KEEP",
                "reason": "몸뿐 아니라 생활용품도 남았다는 추가 반전이다.",
            }
        ],
        "duplicate_review": {"status": "PASS", "acknowledged_pairs": []},
        "findings": [],
    }


def review_v2_for(script: Path) -> dict:
    doc = review_for(script)
    doc["version"] = 2
    doc["checks"]["conclusion_answer_and_boundary"] = "PASS"
    doc["conclusion_review"] = {
        "status": "PASS",
        "opening_question": "왜 이 몸만 남았는가",
        "confirmed_answer": "무덤의 다층 밀봉과 매장 환경이 보존에 기여했다",
        "historical_meaning": "한나라 귀족의 삶과 장례를 함께 보여준다",
        "unresolved_core": "정확한 보존 원인의 기여 비율",
        "why_unresolved": "매장 당시 환경을 완전히 재현할 수 없다",
        "fixed_closing": "시간 속에 잠든 유물, 땅속에 묻힌 역사. 이 무덤의 비밀이었습니다.",
    }
    return doc


class ScriptContextGateTests(unittest.TestCase):
    def test_passes_complete_review_lock(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "01.대본.txt"
            review = root / "01.문맥검수.json"
            script.write_text(SCRIPT, encoding="utf-8")
            review.write_text(json.dumps(review_for(script), ensure_ascii=False), encoding="utf-8")
            report = validate_context_review(script, review)
            self.assertTrue(report.passed, report.failures)

    def test_rejects_script_changed_after_review(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "01.대본.txt"
            review = root / "01.문맥검수.json"
            script.write_text(SCRIPT, encoding="utf-8")
            review.write_text(json.dumps(review_for(script), ensure_ascii=False), encoding="utf-8")
            script.write_text(SCRIPT + " 문장을 추가합니다.", encoding="utf-8")
            report = validate_context_review(script, review)
            self.assertFalse(report.passed)
            self.assertTrue(any("SHA-256" in failure for failure in report.failures))

    def test_rejects_unreviewed_connector(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "01.대본.txt"
            review = root / "01.문맥검수.json"
            script.write_text(SCRIPT, encoding="utf-8")
            doc = review_for(script)
            doc["connectors"] = []
            review.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
            report = validate_context_review(script, review)
            self.assertFalse(report.passed)
            self.assertTrue(any("삭제 비교 미검수" in failure for failure in report.failures))

    def test_v2_requires_explicit_conclusion_review(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "01.대본.txt"
            review = root / "01.문맥검수.json"
            script.write_text(SCRIPT, encoding="utf-8")
            doc = review_v2_for(script)
            del doc["conclusion_review"]["why_unresolved"]
            review.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
            report = validate_context_review(script, review)
            self.assertFalse(report.passed)
            self.assertTrue(any("결론 회수 필드 누락" in failure for failure in report.failures))

    def test_v2_accepts_answered_and_bounded_conclusion(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "01.대본.txt"
            review = root / "01.문맥검수.json"
            script.write_text(SCRIPT, encoding="utf-8")
            review.write_text(json.dumps(review_v2_for(script), ensure_ascii=False), encoding="utf-8")
            report = validate_context_review(script, review)
            self.assertTrue(report.passed, report.failures)

    def test_tts_parser_accepts_markdown_storyboard_format(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "02.시각화.txt"
            path.write_text(
                "## 장면 009 — CUTAWAY / 발굴확인\n\n"
                "- 나레이션: 그 답은 잠시 뒤에 보겠습니다.\n\n"
                "### IMAGE\nignored\n\n"
                "## 장면 010 — INVENTORY\n\n"
                "- 나레이션: 먼저 관 주변부터 살펴보죠.\n",
                encoding="utf-8",
            )
            scenes = parse_script(path)
            self.assertEqual([scene.seq for scene in scenes], [9, 10])
            self.assertEqual(scenes[0].text, "그 답은 잠시 뒤에 보겠습니다.")


if __name__ == "__main__":
    unittest.main()
