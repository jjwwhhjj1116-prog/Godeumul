#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""고대유물의 비밀 대본의 구어체 말맛을 TTS 생성 전에 검사한다.

검사 목적은 유행어를 강제로 넣는 것이 아니라, 사실 문장이 `~습니다`로만
연속되는 보고서 말투를 차단하는 것이다.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path


for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


NARRATION_RE = re.compile(r"^\[한국어\s*(?:나레이션|내레이션|번역|원문)\]\s*(.*)$")
SENTENCE_RE = re.compile(r"[^.!?]+[.!?]?")
FORMAL_END_RE = re.compile(r"(?:습니다|입니다)$")
CONVERSATIONAL_END_RE = re.compile(
    r"(?:죠|거든요|고요|어요|예요|인데요|하고요|냐고요|까요|셈이죠|겁니다|거예요)$"
)

DISCOURSE_MARKERS = (
    "그런데 말이죠", "그런데", "문제는", "더 이상한 건", "그러니까",
    "자, 여기서", "쉽게 말하면", "그럼", "바로", "이쯤 되면",
)
EMPHASIS_WORDS = (
    "싹 다", "통째로", "고작", "하필", "정작", "심지어", "그야말로",
)


@dataclass
class ToneReport:
    sentences: list[str]
    formal_count: int
    conversational_count: int
    max_formal_run: int
    max_formal_run_start: int
    marker_hits: list[str]
    emphasis_hits: list[str]

    @property
    def min_conversational(self) -> int:
        if len(self.sentences) < 8:
            return 1
        return max(3, math.ceil(len(self.sentences) * 0.15))

    @property
    def failures(self) -> list[str]:
        out: list[str] = []
        if self.max_formal_run >= 3:
            start = self.max_formal_run_start + 1
            end = start + self.max_formal_run - 1
            out.append(f"`~습니다/~입니다`형이 {self.max_formal_run}문장 연속입니다: 문장 {start}~{end}")
        if self.conversational_count < self.min_conversational:
            out.append(
                f"대화형 종결이 {self.conversational_count}개뿐입니다 "
                f"(최소 {self.min_conversational}개 필요)"
            )
        return out


def narration_text(raw: str) -> str:
    narration = []
    for line in raw.splitlines():
        hit = NARRATION_RE.match(line.strip())
        if hit and hit.group(1).strip():
            narration.append(hit.group(1).strip())
    if narration:
        return " ".join(narration)

    body = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("["):
            continue
        body.append(stripped)
    return " ".join(body)


def ending_stem(sentence: str) -> str:
    return re.sub(r"[\s.!?]+$", "", sentence)


def analyze(raw: str) -> ToneReport:
    text = narration_text(raw)
    sentences = [m.group(0).strip() for m in SENTENCE_RE.finditer(text) if m.group(0).strip()]

    formal_count = 0
    conversational_count = 0
    max_run = run = 0
    max_start = run_start = 0
    for index, sentence in enumerate(sentences):
        stem = ending_stem(sentence)
        is_formal = bool(FORMAL_END_RE.search(stem))
        is_conversational = bool(CONVERSATIONAL_END_RE.search(stem))
        formal_count += int(is_formal)
        conversational_count += int(is_conversational)
        if is_formal:
            if run == 0:
                run_start = index
            run += 1
            if run > max_run:
                max_run = run
                max_start = run_start
        else:
            run = 0

    marker_hits = [word for word in DISCOURSE_MARKERS if word in text]
    emphasis_hits = [word for word in EMPHASIS_WORDS if word in text]
    return ToneReport(
        sentences=sentences,
        formal_count=formal_count,
        conversational_count=conversational_count,
        max_formal_run=max_run,
        max_formal_run_start=max_start,
        marker_hits=marker_hits,
        emphasis_hits=emphasis_hits,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="고대유물 대본 구어체 말맛 검사")
    parser.add_argument("script", type=Path)
    args = parser.parse_args()

    if not args.script.exists():
        sys.exit(f"[에러] 대본 파일이 없습니다: {args.script}")

    report = analyze(args.script.read_text(encoding="utf-8"))
    print(f"\n대본      : {args.script}")
    print(f"문장      : {len(report.sentences)}개")
    print(f"격식 종결 : {report.formal_count}개 · 최대 연속 {report.max_formal_run}개")
    print(
        f"대화 종결 : {report.conversational_count}개 "
        f"(최소 {report.min_conversational}개)"
    )
    print(f"담화 표지 : {', '.join(report.marker_hits) or '없음'}")
    print(f"강조 부사 : {', '.join(report.emphasis_hits) or '없음'}")

    if report.failures:
        print("\n[실패]")
        for failure in report.failures:
            print(f"  - {failure}")
        print()
        return 1

    print("\n[통과] 보고서식 종결 반복 없이 구어체 리듬이 확보됐습니다.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
