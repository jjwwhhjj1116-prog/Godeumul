#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""고대유물의 비밀 0단계 — 유물 우선 주제 카드 검증기.

사용법:
  python tools/topic_check.py 산출물/EP02_마왕퇴한묘
  python tools/topic_check.py 산출물/EP02_마왕퇴한묘/00.주제카드.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import _config  # noqa: F401


REQUIRED_FIELDS = {
    "status", "target", "one_sentence_promise", "discovery_action",
    "representative_artifacts", "historical_context", "central_question",
    "confirmed_answer_scope", "unknowns", "claims_to_avoid", "official_sources",
    "visual_route", "routing", "scores",
}
SCORE_LIMITS = {
    "artifact_context": 20,
    "historical_density": 20,
    "question_ladder": 20,
    "reference_quality": 15,
    "visual_journey": 15,
    "title_interest": 10,
}
OVERCLAIM_PATTERNS = {
    r"100\s*%": "100% 단정",
    r"완벽(?:한|히)?": "완벽 단정",
    r"영구\s*보존": "영구 보존 단정",
    r"불패": "불패 과장",
    r"외계인": "외계인 떡밥",
    r"초고대\s*문명": "초고대 문명 떡밥",
    r"진공\s*밀폐": "진공 밀폐 선결론",
}


def card_path(value: Path) -> Path:
    value = value.resolve()
    return value / "00.주제카드.json" if value.is_dir() else value


def nonempty_text(data: dict, field: str) -> bool:
    return bool(str(data.get(field) or "").strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="유물 우선 주제 카드 검증")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()

    path = card_path(args.path)
    if not path.exists():
        print(f"FAIL 주제 카드 없음: {path}")
        return 1

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"FAIL 주제 카드 읽기 오류: {exc}")
        return 1

    errors: list[str] = []
    missing = sorted(REQUIRED_FIELDS - set(data))
    if missing:
        errors.append("필수 필드 누락: " + ", ".join(missing))

    if str(data.get("status") or "").upper() != "TOPIC_APPROVED":
        errors.append("status는 TOPIC_APPROVED여야 함")

    for field in (
        "target", "one_sentence_promise", "discovery_action", "historical_context",
        "central_question", "confirmed_answer_scope", "unknowns", "routing",
    ):
        if not nonempty_text(data, field):
            errors.append(f"{field}가 비어 있음")

    artifacts = data.get("representative_artifacts")
    if not isinstance(artifacts, list) or len([v for v in artifacts if str(v).strip()]) < 3:
        errors.append("representative_artifacts는 실물 3개 이상이어야 함")

    claims = data.get("claims_to_avoid")
    if not isinstance(claims, list) or not claims:
        errors.append("claims_to_avoid는 1개 이상이어야 함")

    sources = data.get("official_sources")
    source_ok = (
        isinstance(sources, list)
        and len(sources) >= 2
        and all(
            isinstance(source, dict)
            and str(source.get("institution") or "").strip()
            and re.match(r"https?://", str(source.get("url") or ""))
            for source in sources
        )
    )
    if not source_ok:
        errors.append("official_sources는 기관명+URL을 가진 공식 출처 2개 이상이어야 함")

    route = data.get("visual_route")
    if not isinstance(route, list) or len([v for v in route if str(v).strip()]) < 4:
        errors.append("visual_route는 발견부터 증거 경계까지 4단계 이상이어야 함")

    scored = data.get("scores")
    total = 0
    if not isinstance(scored, dict):
        errors.append("scores 객체 필요")
    else:
        for field, maximum in SCORE_LIMITS.items():
            value = scored.get(field)
            if not isinstance(value, int) or not 0 <= value <= maximum:
                errors.append(f"scores.{field}는 0~{maximum} 정수여야 함")
            else:
                total += value
        declared_total = scored.get("total")
        if declared_total != total:
            errors.append(f"scores.total 불일치: 선언 {declared_total}, 계산 {total}")
        if total < 85:
            errors.append(f"주제 점수 {total}/100 — 우선 제작 기준 85점 미달")

    promise_and_question = " ".join(
        str(data.get(field) or "") for field in ("one_sentence_promise", "central_question")
    )
    for pattern, label in OVERCLAIM_PATTERNS.items():
        if re.search(pattern, promise_and_question, re.I):
            errors.append(f"주제 선결론·과장: {label}")

    print(f"주제 카드: {data.get('target') or path.stem}")
    print(f"실물: {len(artifacts) if isinstance(artifacts, list) else 0}개 / "
          f"공식 출처: {len(sources) if isinstance(sources, list) else 0}개 / "
          f"시각 경로: {len(route) if isinstance(route, list) else 0}단계 / 점수: {total}/100")
    if errors:
        for error in errors:
            print(f"  FAIL {error}")
        print("결과: 주제 승인 실패 — 조사·대본 작성 금지")
        return 1

    print("결과: 통과 — 조사노트 작성 가능")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
