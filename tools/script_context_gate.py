#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TTS 전에 한국어 대본의 문맥 검수 잠금을 확인한다.

이 도구는 LLM 흉내를 내는 맞춤법 검사기가 아니다. Humanizer KO와 채널
편집 기준으로 사람이/에이전트가 수행한 문서·문단·문장 검수가 현재 대본과
동일한지, 필요한 다섯 검문이 빠짐없이 PASS인지 결정적으로 확인한다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from script_tone_check import analyze, narration_text


for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


REQUIRED_CHECKS = (
    "paragraph_roles_and_flow",
    "adjacent_sentence_relations",
    "connector_deletion_test",
    "duplicate_information",
    "tts_release_gate",
)

# 길이가 긴 표지를 먼저 검사해 `그런데 말이죠`를 `그런데`와 중복 집계하지 않는다.
REVIEW_MARKERS = (
    "그런데 말이죠",
    "여기서 끝이 아닙니다",
    "그 답은 잠시 뒤에 보겠습니다",
    "자, 이제",
    "그러니까",
    "그런데",
    "하지만",
    "그래서",
    "다만",
    "먼저",
    "옷은 더",
)
MARKER_RE = re.compile("|".join(re.escape(x) for x in sorted(REVIEW_MARKERS, key=len, reverse=True)))
WORD_RE = re.compile(r"[가-힣A-Za-z0-9]+")
STOPWORDS = {
    "그", "이", "저", "것", "수", "한", "더", "안", "속", "앞", "뒤", "사람",
    "있습니다", "있었죠", "아닙니다", "하지만", "그런데", "그러니까",
}


@dataclass
class ContextGateReport:
    script: Path
    review: Path
    paragraphs: int
    sentences: int
    marker_count: int
    failures: list[str]
    warnings: list[str]

    @property
    def passed(self) -> bool:
        return not self.failures


def sha256_text(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _paragraphs(raw: str) -> list[str]:
    out: list[str] = []
    for block in re.split(r"\n\s*\n", raw):
        lines = [line.strip() for line in block.splitlines()
                 if line.strip() and not line.lstrip().startswith(("#", "["))]
        if lines:
            out.append(" ".join(lines))
    return out


def _marker_occurrences(sentences: list[str]) -> list[dict]:
    out: list[dict] = []
    for sentence_number, sentence in enumerate(sentences, 1):
        for hit in MARKER_RE.finditer(sentence):
            out.append({"sentence": sentence_number, "text": hit.group(0)})
    return out


def _tokens(sentence: str) -> set[str]:
    return {word for word in WORD_RE.findall(sentence) if len(word) > 1 and word not in STOPWORDS}


def duplicate_candidates(sentences: list[str]) -> list[tuple[int, int, float]]:
    candidates: list[tuple[int, int, float]] = []
    token_sets = [_tokens(sentence) for sentence in sentences]
    for left in range(len(sentences)):
        if len(token_sets[left]) < 4:
            continue
        for right in range(left + 1, len(sentences)):
            if len(token_sets[right]) < 4:
                continue
            union = token_sets[left] | token_sets[right]
            score = len(token_sets[left] & token_sets[right]) / max(1, len(union))
            if score >= 0.72:
                candidates.append((left + 1, right + 1, round(score, 3)))
    return candidates


def validate_context_review(script: Path, review: Path) -> ContextGateReport:
    failures: list[str] = []
    warnings: list[str] = []
    if not script.exists():
        return ContextGateReport(script, review, 0, 0, 0, [f"대본 없음: {script}"], [])
    if not review.exists():
        return ContextGateReport(script, review, 0, 0, 0, [f"문맥 검수 잠금 없음: {review}"], [])

    raw = script.read_text(encoding="utf-8")
    tone = analyze(raw)
    paragraphs = _paragraphs(raw)
    markers = _marker_occurrences(tone.sentences)
    try:
        doc = json.loads(review.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return ContextGateReport(script, review, len(paragraphs), len(tone.sentences), len(markers),
                                 [f"문맥 검수 JSON 오류: {exc}"], [])

    if doc.get("status") != "PASS":
        failures.append("문맥 검수 status가 PASS가 아님")
    if doc.get("script_sha256") != sha256_text(script):
        failures.append("대본 SHA-256이 검수 잠금과 다름 — 대본 수정 뒤 재검수 필요")

    checks = doc.get("checks") or {}
    for key in REQUIRED_CHECKS:
        if checks.get(key) != "PASS":
            failures.append(f"필수 검문 미통과: {key}")

    reviewed_paragraphs = doc.get("paragraphs") or []
    paragraph_numbers = {item.get("n") for item in reviewed_paragraphs if item.get("role") and item.get("summary")}
    expected_paragraphs = set(range(1, len(paragraphs) + 1))
    if paragraph_numbers != expected_paragraphs:
        failures.append(
            f"문단 역할 검수 범위 불일치: {sorted(paragraph_numbers)} / 필요 {sorted(expected_paragraphs)}"
        )

    transitions = doc.get("transitions") or []
    transition_pairs = {
        (item.get("from"), item.get("to"))
        for item in transitions
        if item.get("status") == "PASS" and item.get("relation") and item.get("reason")
    }
    expected_transitions = {(n, n + 1) for n in range(1, len(paragraphs))}
    if transition_pairs != expected_transitions:
        failures.append(
            f"문단 전환 검수 범위 불일치: {sorted(transition_pairs)} / 필요 {sorted(expected_transitions)}"
        )

    connector_reviews = doc.get("connectors") or []
    reviewed_connectors = {
        (item.get("sentence"), item.get("text"))
        for item in connector_reviews
        if item.get("decision") == "KEEP" and len(str(item.get("reason") or "")) >= 8
    }
    required_connectors = {(item["sentence"], item["text"]) for item in markers}
    missing_connectors = required_connectors - reviewed_connectors
    if missing_connectors:
        failures.append(f"접속·전환 표지 삭제 비교 미검수: {sorted(missing_connectors)}")

    duplicate_review = doc.get("duplicate_review") or {}
    if duplicate_review.get("status") != "PASS":
        failures.append("중복 정보 검수가 PASS가 아님")
    candidates = duplicate_candidates(tone.sentences)
    acknowledged = {
        tuple(pair[:2]) for pair in duplicate_review.get("acknowledged_pairs", [])
        if isinstance(pair, list) and len(pair) >= 2
    }
    unreviewed_duplicates = [(a, b, score) for a, b, score in candidates if (a, b) not in acknowledged]
    if unreviewed_duplicates:
        failures.append(f"유사 문장 후보 미검수: {unreviewed_duplicates}")

    unresolved = [item.get("id", "이름 없음") for item in (doc.get("findings") or [])
                  if item.get("status") not in {"RESOLVED", "ACCEPTED"}]
    if unresolved:
        failures.append(f"미해결 문맥 지적: {unresolved}")

    if tone.failures:
        failures.extend(f"말맛 검사: {failure}" for failure in tone.failures)
    if not markers:
        warnings.append("검수 대상 접속·전환 표지가 없음")

    return ContextGateReport(
        script=script,
        review=review,
        paragraphs=len(paragraphs),
        sentences=len(tone.sentences),
        marker_count=len(markers),
        failures=failures,
        warnings=warnings,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="고대유물 대본 문맥 검수 잠금 게이트")
    parser.add_argument("script", type=Path)
    parser.add_argument("--review", type=Path, default=None)
    args = parser.parse_args()

    review = args.review or args.script.parent / "01.문맥검수.json"
    report = validate_context_review(args.script, review)
    print(f"\n대본      : {report.script}")
    print(f"검수 잠금 : {report.review}")
    print(f"문단/문장 : {report.paragraphs}/{report.sentences}")
    print(f"접속 표지 : {report.marker_count}개")
    for warning in report.warnings:
        print(f"  [주의] {warning}")
    if report.failures:
        print("\n[실패] TTS 생성 금지")
        for failure in report.failures:
            print(f"  - {failure}")
        print()
        return 1
    print("\n[통과] 문맥·전환·중복 검수 잠금이 현재 대본과 일치합니다.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
