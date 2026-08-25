#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ElevenLabs 전송 전용 한국어 발음 정규화.

대본·자막 원문은 절대 수정하지 않는다. 이 모듈의 반환값만 TTS API에 보낸다.
"""

from __future__ import annotations

import hashlib
import difflib
import json
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DICTIONARY = ROOT / "tts_pronunciation.json"
NUMBER_RE = re.compile(r"(?<![A-Za-z0-9])\d[\d,]*(?:\.\d+)?")
ALIGN_STRIP_RE = re.compile(r"[\s.,!?·…\"']")


@dataclass(frozen=True)
class Change:
    kind: str
    source: str
    target: str


def _under_10000(value: int) -> str:
    if value == 0:
        return ""
    digits = "영일이삼사오육칠팔구"
    units = ((1000, "천"), (100, "백"), (10, "십"), (1, ""))
    out: list[str] = []
    remain = value
    for unit_value, unit_name in units:
        digit, remain = divmod(remain, unit_value)
        if not digit:
            continue
        if digit != 1 or unit_value == 1:
            out.append(digits[digit])
        out.append(unit_name)
    return "".join(out)


def integer_to_korean(value: int) -> str:
    if value == 0:
        return "영"
    if value < 0:
        return "마이너스" + integer_to_korean(-value)
    big_units = ("", "만", "억", "조", "경")
    chunks: list[str] = []
    unit_index = 0
    while value:
        value, chunk = divmod(value, 10000)
        if chunk:
            chunks.append(_under_10000(chunk) + big_units[unit_index])
        unit_index += 1
    return "".join(reversed(chunks))


def number_token_to_korean(token: str) -> str:
    clean = token.replace(",", "")
    if "." not in clean:
        return integer_to_korean(int(clean))
    whole, decimal = clean.split(".", 1)
    digits = "영일이삼사오육칠팔구"
    return integer_to_korean(int(whole)) + "쩜" + "".join(digits[int(ch)] for ch in decimal)


class PronunciationDictionary:
    def __init__(self, path: Path = DEFAULT_DICTIONARY) -> None:
        self.path = path.resolve()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.version = int(data.get("version", 1))
        self.number_normalization = bool(data.get("숫자한글화", True))
        replacements = data.get("치환") or {}
        if not isinstance(replacements, dict):
            raise ValueError("tts_pronunciation.json의 '치환'은 객체여야 합니다.")
        self.replacements = {
            str(source): str(target) for source, target in replacements.items()
            if str(source) and str(target)
        }
        raw = self.path.read_bytes()
        self.signature = hashlib.sha256(raw).hexdigest()[:16]

    def apply(self, original: str) -> tuple[str, list[Change]]:
        text = original
        changes: list[Change] = []

        # 긴 구문부터 바꿔 짧은 항목이 먼저 먹는 일을 막는다.
        for source in sorted(self.replacements, key=len, reverse=True):
            target = self.replacements[source]
            count = text.count(source)
            if not count:
                continue
            text = text.replace(source, target)
            changes.extend(Change("dictionary", source, target) for _ in range(count))

        if self.number_normalization:
            def replace_number(match: re.Match[str]) -> str:
                source = match.group(0)
                target = number_token_to_korean(source)
                changes.append(Change("number", source, target))
                return target

            text = NUMBER_RE.sub(replace_number, text)

        # 숫자 뒤에 흔히 붙는 영문 단위. 대소문자 오염을 피하려고 제한적으로 처리한다.
        unit_pairs = (("km", "킬로미터"), ("cm", "센티미터"), ("mm", "밀리미터"),
                      ("kg", "킬로그램"), ("%", "퍼센트"))
        for source, target in unit_pairs:
            if source not in text:
                continue
            count = text.count(source)
            text = text.replace(source, target)
            changes.extend(Change("unit", source, target) for _ in range(count))

        return text, changes


def _alignment_chars(text: str) -> list[str]:
    return list(ALIGN_STRIP_RE.sub("", text))


def original_to_spoken_map(original: str, spoken: str) -> list[tuple[int, int]]:
    """원문 자막 문자 인덱스를 발음 치환문 문자 범위로 연결한다."""
    source = _alignment_chars(original)
    target = _alignment_chars(spoken)
    if not source:
        return []
    if not target:
        return [(0, 0) for _ in source]

    mapped: list[tuple[int, int] | None] = [None] * len(source)
    matcher = difflib.SequenceMatcher(a=source, b=target, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(i2 - i1):
                mapped[i1 + offset] = (j1 + offset, j1 + offset)
            continue
        if tag == "insert":
            continue
        source_size = max(1, i2 - i1)
        target_size = j2 - j1
        for offset in range(i2 - i1):
            if target_size:
                start = j1 + (offset * target_size) // source_size
                end = j1 + (((offset + 1) * target_size + source_size - 1) // source_size) - 1
                mapped[i1 + offset] = (min(start, len(target) - 1), min(end, len(target) - 1))
            else:
                nearest = min(max(j1 - 1, 0), len(target) - 1)
                mapped[i1 + offset] = (nearest, nearest)

    last = (0, 0)
    for index, value in enumerate(mapped):
        if value is None:
            mapped[index] = last
        else:
            last = value
    return [value or (0, 0) for value in mapped]
