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


def review_v3_for(script: Path) -> dict:
    doc = review_v2_for(script)
    doc["version"] = 3
    doc["checks"].update({
        "korean_three_layer_review": "PASS",
        "all_adjacent_sentence_pairs": "PASS",
        "major_fact_reveal_ladders": "PASS",
        "information_prerequisites": "PASS",
        "hook_compactness_and_payload": "PASS",
        "script_editorial_separation": "PASS",
        "investigation_arc_and_future_evidence": "PASS",
        "fixed_chapter_story_flow": "PASS",
        "approved_predecessor_flow_review": "PASS",
    })
    doc["korean_review"] = {
        "status": "PASS",
        "reviewer": "korean-proofreader + godeumul-context-qa",
        "document": "PASS",
        "paragraph": "PASS",
        "sentence": "PASS",
    }
    doc["sentence_links"] = [
        {
            "from": 1,
            "to": 2,
            "relation": "발견에서 질문",
            "reason": "발견된 몸을 곧바로 보존 원인 질문으로 확장한다.",
            "status": "PASS",
        },
        {
            "from": 2,
            "to": 3,
            "relation": "질문에서 추가 증거",
            "reason": "몸의 보존 질문을 관 주변 생활용품이라는 추가 증거로 잇는다.",
            "status": "PASS",
        },
        {
            "from": 3,
            "to": 4,
            "relation": "증거에서 조사 순서",
            "reason": "새로 공개한 생활용품을 다음 조사 대상으로 바로 회수한다.",
            "status": "PASS",
        },
    ]
    doc["hook_review"] = {
        "status": "PASS",
        "sentence_start": 1,
        "sentence_end": 2,
        "artifact": "여성",
        "visual_action": "무덤에서 여성의 몸이 발견된다",
        "scale_or_contradiction": "몸이 예외적으로 남았다",
        "open_question": "왜 이 몸만 남았을까",
    }
    doc["prerequisite_review"] = {
        "status": "PASS",
        "unintroduced_terms": [],
        "pronoun_referents": "PASS",
    }
    doc["major_fact_inventory"] = ["F01"]
    doc["reveal_blocks"] = [
        {
            "id": "F01",
            "setup": "몸만 남았다는 첫 질문",
            "reveal": "관 주변 생활용품도 함께 남았다",
            "meaning": "보존 원인과 장례 맥락을 함께 봐야 한다",
            "next_question": "관 주변에는 무엇이 놓였는가",
            "status": "PASS",
        }
    ]
    doc["investigation_review"] = {
        "status": "PASS",
        "discovered_anomaly": "무덤에서 여성의 몸이 예외적으로 보존됐다",
        "investigation_goal": "몸이 남은 원인과 무덤의 성격을 확인한다",
        "method_or_evidence": "관 주변 생활용품과 매장 환경을 함께 대조한다",
        "initial_hypothesis": "다층 밀봉이 보존을 만들었다는 가설을 세운다",
        "why_hypothesis_failed": "매장 당시 환경을 완전히 재현할 수 없어 단일 원인으로 확정하지 못한다",
        "question_shift": "원인 하나 대신 무덤 전체의 보존 조건을 묻는다",
        "newly_visible_information": "생활용품과 장례 구조가 함께 보이기 시작한다",
        "confirmed_progress": "밀봉과 매장 환경이 보존에 기여했음을 확인한다",
        "unresolved_core": "각 보존 조건의 정확한 기여 비율은 남는다",
        "why_unresolved": "매장 직후의 온도와 화학 환경 기록이 없다",
        "future_evidence": "비교 가능한 봉분과 더 정밀한 환경 복원 자료가 필요하다",
        "expected_historical_gain": "한나라 장례와 보존 과정의 실제 순서를 복원할 수 있다",
    }
    doc["chapter_flow_review"] = {
        "status": "PASS",
        "structure_type": "SHORT_6",
        "chapters": [
            {
                "n": n,
                "role": f"챕터 {n}의 고정 역할",
                "must_contain": f"챕터 {n}이 반드시 담을 증거와 질문",
                "next_handoff": f"챕터 {n}의 답에서 다음 질문으로 이동",
                "status": "PASS",
            }
            for n in range(1, 7)
        ],
    }
    doc["predecessor_flow_review"] = {
        "status": "PASS",
        "reference_scripts": [
            {
                "path": "산출물/EP05_로제타석/01.대본.txt",
                "flow_summary": "발견 뒤 해독 실패와 비교 방법의 전환으로 정체를 밝힌다",
                "preserved_principle": "조사 목표와 방법, 실패 이유를 순서대로 보여 준다",
                "avoided_mistake": "이전 회차의 유물과 인물을 현재 회차에 복사하지 않는다",
                "status": "PASS",
            }
        ],
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

    def test_v3_accepts_full_sentence_and_reveal_review(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "01.대본.txt"
            review = root / "01.문맥검수.json"
            script.write_text(SCRIPT, encoding="utf-8")
            review.write_text(json.dumps(review_v3_for(script), ensure_ascii=False), encoding="utf-8")
            report = validate_context_review(script, review)
            self.assertTrue(report.passed, report.failures)

    def test_v3_rejects_one_missing_adjacent_sentence_pair(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "01.대본.txt"
            review = root / "01.문맥검수.json"
            script.write_text(SCRIPT, encoding="utf-8")
            doc = review_v3_for(script)
            doc["sentence_links"] = doc["sentence_links"][:-1]
            review.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
            report = validate_context_review(script, review)
            self.assertFalse(report.passed)
            self.assertTrue(any("인접 문장 전수 검수" in failure for failure in report.failures))

    def test_v3_rejects_flat_major_fact_without_full_reveal_ladder(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "01.대본.txt"
            review = root / "01.문맥검수.json"
            script.write_text(SCRIPT, encoding="utf-8")
            doc = review_v3_for(script)
            del doc["reveal_blocks"][0]["meaning"]
            review.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
            report = validate_context_review(script, review)
            self.assertFalse(report.passed)
            self.assertTrue(any("미니후킹 검수" in failure for failure in report.failures))

    def test_v3_rejects_unintroduced_information(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "01.대본.txt"
            review = root / "01.문맥검수.json"
            script.write_text(SCRIPT, encoding="utf-8")
            doc = review_v3_for(script)
            doc["prerequisite_review"]["unintroduced_terms"] = ["성경만 보관했다"]
            review.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
            report = validate_context_review(script, review)
            self.assertFalse(report.passed)
            self.assertTrue(any("설명 전에 사용된 정보" in failure for failure in report.failures))

    def test_v3_rejects_editorial_explanation_inside_script(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "01.대본.txt"
            review = root / "01.문맥검수.json"
            contaminated = SCRIPT + " 이렇게 가면 충격이 단계적으로 커집니다."
            script.write_text(contaminated, encoding="utf-8")
            doc = review_v3_for(script)
            doc["sentence_links"].append({
                "from": 4,
                "to": 5,
                "relation": "편집 설명 혼입",
                "reason": "검출 테스트를 위해 편집자 설명을 일부러 대본에 넣었다.",
                "status": "PASS",
            })
            review.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
            report = validate_context_review(script, review)
            self.assertFalse(report.passed)
            self.assertTrue(any("편집자 설명 문구" in failure for failure in report.failures))

    def test_v3_rejects_missing_investigation_turn(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "01.대본.txt"
            review = root / "01.문맥검수.json"
            script.write_text(SCRIPT, encoding="utf-8")
            doc = review_v3_for(script)
            del doc["investigation_review"]["question_shift"]
            review.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
            report = validate_context_review(script, review)
            self.assertFalse(report.passed)
            self.assertTrue(any("조사 서사 필드 누락" in failure for failure in report.failures))

    def test_v3_rejects_missing_one_fixed_chapter_role(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "01.대본.txt"
            review = root / "01.문맥검수.json"
            script.write_text(SCRIPT, encoding="utf-8")
            doc = review_v3_for(script)
            doc["chapter_flow_review"]["chapters"] = doc["chapter_flow_review"]["chapters"][:-1]
            review.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
            report = validate_context_review(script, review)
            self.assertFalse(report.passed)
            self.assertTrue(any("고정 챕터 역할" in failure for failure in report.failures))

    def test_v3_rejects_missing_predecessor_flow_review(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "01.대본.txt"
            review = root / "01.문맥검수.json"
            script.write_text(SCRIPT, encoding="utf-8")
            doc = review_v3_for(script)
            doc["predecessor_flow_review"]["reference_scripts"] = []
            review.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
            report = validate_context_review(script, review)
            self.assertFalse(report.passed)
            self.assertTrue(any("이전 승인 대본 전개 비교 기록" in failure for failure in report.failures))

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
