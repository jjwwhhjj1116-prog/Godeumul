#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""고대유물의 비밀 2단계 검수 — 장면 구조·고증·프롬프트 검증기.

검사 범위
  A 장면 구조      번호 연속, 대본·이미지·영상 1:1, 증거 상태
  B 시간            생성 길이 4/6/8/10초, TTS보다 짧지 않음
  C 고증            고증 카드의 문명·인물·건축·금지어·네거티브
  D 생성 안정성     9:16, 이미지 문자 금지, I2V 연속 촬영 지시

사용법
  python tools/prompt_check.py 산출물/EP01_진시황릉
  python tools/prompt_check.py 산출물/EP01_진시황릉 -v
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ALLOWED_SECONDS = {4, 6, 8, 10}
EVIDENCE_STATES = {"발굴확인", "측정확인", "문헌기록", "학술해석", "미확인"}
SCENE_TYPES = {
    "DISCOVERY_ACTION", "DISCOVERY_REVEAL", "SITE_ESTABLISH", "EXCAVATION",
    "ARTIFACT_MACRO", "INVENTORY_TABLEAU", "HISTORICAL_RECONSTRUCTION",
    "SPATIAL_MAP", "CUTAWAY", "TEXT_RECORD", "SCIENTIFIC_EVIDENCE",
    "CONSERVATION", "SEALED_UNKNOWN", "DIAGRAM", "EXPLODED", "MECHANISM",
}

PEOPLE_HINT = re.compile(
    r"\b(figures?|farmers?|excavators?|archaeologists?|laborers?|labourers?|"
    r"workers?|artisans?|masons?|soldiers?|guards?|officials?|priests?|"
    r"crowd|people|men|women|hands?)\b", re.I)
ARCH_HINT = re.compile(
    r"\b(palace|town|city|temple|building|roofs?|courtyards?|hall|walls?|"
    r"gate|tower|mausoleum|tomb complex)\b", re.I)


class Report:
    def __init__(self) -> None:
        self.rows: list[tuple[bool, int, str, str]] = []

    def add(self, ok: bool, scene: int, item: str, detail: str = "") -> None:
        self.rows.append((ok, scene, item, detail))

    @property
    def fails(self) -> list[tuple[bool, int, str, str]]:
        return [row for row in self.rows if not row[0]]


def compact(value: str) -> str:
    return " ".join(value.split())


def section(text: str, heading: str) -> str:
    match = re.search(
        rf"^##+\s+[^\n]*{re.escape(heading)}[^\n]*\n(.*?)(?=^##+\s|\Z)",
        text,
        re.M | re.S,
    )
    return match.group(1) if match else ""


def first_code_block(text: str) -> str:
    match = re.search(r"```(?:text)?\s*\n(.*?)\n```", text, re.S | re.I)
    return compact(match.group(1)) if match else ""


def anchor_head(text: str, words: int) -> str:
    tokens = re.findall(r"[A-Za-z0-9-]+", text)
    return " ".join(tokens[:words]).lower()


def load_card(episode: Path) -> dict[str, object]:
    path = episode / "02b.고증카드.md"
    if not path.exists():
        sys.exit(f"[에러] 고증 카드가 없습니다: {path}")

    text = path.read_text(encoding="utf-8")
    civ = first_code_block(section(text, "문명"))
    people = first_code_block(section(text, "인물"))
    architecture = first_code_block(section(text, "건축"))
    negative = first_code_block(section(text, "네거티브"))
    if not civ:
        sys.exit(f"[에러] 고증 카드의 '문명' 절에 영문 코드 블록이 없습니다: {path}")

    banned: list[str] = []
    people_section = section(text, "인물")
    banned_line = re.search(r"금지어[^:：]*[:：]\s*([^\n]+)", people_section, re.I)
    if banned_line:
        raw = re.sub(r"[`*.]", "", banned_line.group(1))
        banned = [word.strip().lower() for word in raw.split(",") if word.strip()]

    negative_clauses = [part.strip().lower() for part in negative.split(",") if part.strip()]
    return {
        "civ": civ,
        "civ_head": anchor_head(civ.split(",")[0], 2),
        "people": people,
        "people_head": anchor_head(people, 3),
        "architecture": architecture,
        "architecture_head": anchor_head(architecture, 2),
        "banned": banned,
        "negative": negative,
        "negative_heads": negative_clauses[:2],
    }


def selected_image(scene: dict, requested: str | None) -> str:
    if requested:
        return str(scene.get(requested, ""))
    return str(scene.get("img_v2") or scene.get("img") or "")


def scene_number(value: object, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def main() -> int:
    parser = argparse.ArgumentParser(description="장면 구조·고증·프롬프트 검증")
    parser.add_argument("episode", type=Path)
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--필드", dest="field", default=None,
                        help="검사할 이미지 필드(기본: img_v2 우선, 없으면 img)")
    args = parser.parse_args()

    episode = args.episode.resolve()
    card = load_card(episode)
    scene_path = episode / "02a.장면구분.json"
    if not scene_path.exists():
        sys.exit(f"[에러] 장면표가 없습니다: {scene_path}")
    scenes = json.loads(scene_path.read_text(encoding="utf-8"))
    if not isinstance(scenes, list) or not scenes:
        sys.exit(f"[에러] 장면표가 빈 배열이거나 형식이 잘못됐습니다: {scene_path}")

    report = Report()
    print(f"\n에피소드 : {episode.name}")
    print(f"문명 앵커 : {card['civ']}")
    print(f"장면      : {len(scenes)}개\n")

    numbers = [scene_number(scene.get("n"), index) for index, scene in enumerate(scenes, 1)]
    expected = list(range(1, len(scenes) + 1))
    report.add(numbers == expected, 0, "장면 번호 연속",
               "" if numbers == expected else f"현재 {numbers} / 기대 {expected}")

    for index, scene_data in enumerate(scenes, 1):
        n = scene_number(scene_data.get("n"), index)
        image = selected_image(scene_data, args.field)
        video = str(scene_data.get("vid") or "")
        narration = str(scene_data.get("txt") or "").strip()
        evidence = str(scene_data.get("evidence") or scene_data.get("증거상태") or "").strip()
        scene_type = str(scene_data.get("ct") or scene_data.get("type") or "").strip()
        low = image.lower()

        # A. 한 장면 1:1 구조
        report.add(bool(narration), n, "나레이션 1개", "" if narration else "txt 없음")
        report.add(bool(image), n, "이미지 프롬프트 1개", "" if image else "img/img_v2 없음")
        report.add(bool(video), n, "영상 프롬프트 1개", "" if video else "vid 없음")
        report.add(evidence in EVIDENCE_STATES, n, "증거 상태",
                   "" if evidence in EVIDENCE_STATES else f"'{evidence or '없음'}'")
        report.add(scene_type in SCENE_TYPES, n, "장면 유형",
                   "" if scene_type in SCENE_TYPES else f"'{scene_type or '없음'}'")

        # B. TTS와 생성 길이
        duration = scene_data.get("omni")
        try:
            duration_number = int(duration)
        except (TypeError, ValueError):
            duration_number = -1
        report.add(duration_number in ALLOWED_SECONDS, n, "생성 길이",
                   "" if duration_number in ALLOWED_SECONDS else f"{duration!r}초")

        tts = scene_data.get("tts")
        try:
            tts_number = float(tts)
        except (TypeError, ValueError):
            tts_number = -1.0
        report.add(tts_number > 0, n, "TTS 실측", "" if tts_number > 0 else f"{tts!r}")
        if tts_number > 0 and duration_number in ALLOWED_SECONDS:
            report.add(tts_number <= duration_number, n, "TTS≤생성 길이",
                       "" if tts_number <= duration_number
                       else f"TTS {tts_number:.2f}초 > 생성 {duration_number}초")
            report.add(tts_number <= 9.0, n, "장면 분할 검토",
                       "" if tts_number <= 9.0 else f"TTS {tts_number:.2f}초 — 장면 분할 필요")

        if not image:
            continue

        # 네거티브 문구에 들어간 사람 단어는 인물 탐지에서 제외한다.
        positive_scene = re.sub(r"\bno\s+[a-z ,'-]+", "", image, flags=re.I)

        # C. 고증 카드 앵커
        civ_head = str(card["civ_head"])
        report.add(bool(civ_head and civ_head in low), n, "문명 앵커",
                   "" if civ_head and civ_head in low else f"'{civ_head}' 없음")

        if PEOPLE_HINT.search(positive_scene):
            people_head = str(card["people_head"])
            report.add(bool(people_head and people_head in low), n, "인물 앵커",
                       "" if people_head and people_head in low else f"'{people_head}' 없음")

        if ARCH_HINT.search(positive_scene):
            architecture_head = str(card["architecture_head"])
            report.add(bool(architecture_head and architecture_head in low), n, "건축 앵커",
                       "" if architecture_head and architecture_head in low
                       else f"'{architecture_head}' 없음")

        for banned_word in card["banned"]:
            if re.search(r"\b" + re.escape(str(banned_word)) + r"\b", low):
                report.add(False, n, "고증 금지어", f"'{banned_word}'")

        missing_negative = [clause for clause in card["negative_heads"] if clause not in low]
        report.add(not missing_negative, n, "고증 네거티브",
                   "" if not missing_negative else f"누락: {missing_negative}")

        # D. 생성 안정성
        report.add("9:16" in image, n, "세로 규격", "" if "9:16" in image else "9:16 없음")
        no_generated_text = (
            "no text" in low and "no labels" in low and "no letters" in low
            and not re.search(r'reading\s+"[^"]+"', image, re.I)
        )
        report.add(bool(no_generated_text), n, "이미지 문자 금지",
                   "" if no_generated_text else "no text/no labels/no letters 누락 또는 생성 라벨 존재")

        video_low = video.lower()
        continuous = "continuous" in video_low and "no hard cut" in video_low
        report.add(continuous, n, "I2V 연속 촬영",
                   "" if continuous else "continuous와 no hard cut 지시 필요")
        preserve = "no new object" in video_low or "preserve all object" in video_low
        report.add(preserve, n, "I2V 새 물체 금지",
                   "" if preserve else "no new objects 또는 preserve all objects 지시 필요")

        if args.verbose:
            rows = [row for row in report.rows if row[1] == n]
            failures = [row for row in rows if not row[0]]
            mark = "OK " if not failures else "★  "
            print(f"  {mark}장면 {n:>3} {scene_type or '-':<26} 검사 {len(rows)}개"
                  + ("" if not failures else " → "
                     + "; ".join(f"{item}({detail})" for _, _, item, detail in failures)))

    failures = report.fails
    if not args.verbose:
        by_scene: dict[int, list[str]] = {}
        for _, n, item, detail in failures:
            by_scene.setdefault(n, []).append(item + (f" ({detail})" if detail else ""))
        for n in sorted(by_scene):
            label = "전체" if n == 0 else f"장면 {n:>3}"
            print(f"  ★ {label}  " + " · ".join(by_scene[n]))

    print(f"\n{'─' * 72}")
    print(f"검사 {len(report.rows)}건 · 통과 {len(report.rows) - len(failures)} · 실패 {len(failures)}")
    if failures:
        failed_scenes = {row[1] for row in failures if row[1] != 0}
        print(f"\n★ {len(failed_scenes)}개 장면이 FLOW 투입 조건을 통과하지 못했습니다.")
        print("  장면표·고증카드·이미지/I2V 프롬프트를 고친 뒤 다시 검사하세요.\n")
        return 1

    print("\n장면 구조·고증·생성 안정성 이상 없음. FLOW 투입 가능.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
