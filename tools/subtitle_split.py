#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
[고대유물의 비밀] 5단계 보조 — 자막 분할기

대본을 캡컷 자막 큐로 쪼갠다. 규칙은 실제 프로젝트("투탕카멘_고대유물의 비밀")
자막 111개를 실측해서 뽑았다.

  · 무조건 한 줄. 줄바꿈을 만들지 않는다  (실측: 111개 전부 1줄)
  · 최대 16자                              (실측 최대 17자, 1자 여유)
  · 목표 9자 안팎                          (실측 중앙값 9자)
  · 어절(공백) 경계에서만 자른다
  · 조사·의존명사만 다음 줄로 넘어가지 않게 막는다
  · ★ 문장 전체를 보고 줄 길이를 고르게 나눈다(DP). 앞에서부터 욕심껏 채우면
    문장 끝에 「보죠.」 같은 3자짜리 꼬리가 남아 0.26초 만에 사라진다

사용법
  python tools/subtitle_split.py 산출물/EP01_진시황릉/01.대본.txt
  python tools/subtitle_split.py ... --max 16 --target 9
  python tools/subtitle_split.py ... --srt          # SRT도 함께 저장(길이 균등 배분)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from _config import load

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

CFG = load()
MAX_CHARS = CFG.get("자막.최대글자수", 16)
TARGET = CFG.get("자막.목표글자수", 9)
MIN_TAIL = CFG.get("자막.최소표시초", 0.35)   # 검수용 기준. 분할은 DP 가 균등하게 처리한다

# 홀로 줄 앞에 오면 어색한 것들 — 앞 어절에 붙여야 한다
DEPENDENT_HEAD = (
    "것", "겁", "게", "거", "수", "때", "적", "줄", "만큼", "뿐", "채", "듯",
    "및", "등", "때문", "동안", "대로", "지", "바",
)
# 조사로만 이루어진 꼬리 (앞 어절에서 떨어지면 안 됨)
JOSA_ONLY = re.compile(r"^(은|는|이|가|을|를|의|에|에서|으로|로|와|과|도|만|까지|부터|보다|처럼|께|한테|에게)$")

SENT_END = re.compile(r"(?<=[.!?])\s+")

# ── 절대 갈라지면 안 되는 짝 ──────────────────────────────
# 숫자(또는 한글 수사)로 끝나는 어절 + 단위로 시작하는 어절  →  "2천 / 년을" 방지
NUM_END = re.compile(r"[0-9일이삼사오육칠팔구십백천만억]$")
UNITS = ("년", "월", "일", "시", "분", "초", "명", "개", "톤", "미터", "킬로", "센티",
         "도", "배", "번", "자루", "겹", "층", "채", "마리", "권", "장", "대", "척",
         "퍼센트", "%", "만", "천", "억", "미리", "그램")
# 앞 어절이 연결어미 -아/-어 로 끝나고 뒤가 보조용언  →  "갈아 / 넣었죠" 방지
AUX_VERB = ("넣", "버리", "놓", "두", "주", "대", "내", "치")
# 구어체 강조구는 화면에서도 한 호흡으로 읽혀야 한다.
FIXED_PHRASE_PAIRS = {("싹", "다")}


# ── 한글 수사 → 아라비아 숫자 ────────────────────────────
# TTS 는 "천구백칠십이년" 으로 읽어야 자연스럽지만, **자막은 숫자로 보여야 한다.**
# 정렬(align_subtitles)은 원문으로 하고 화면 표시만 바꾸므로 큐에 둘 다 남긴다.
_DIG = {"영":0,"공":0,"일":1,"이":2,"삼":3,"사":4,"오":5,"육":6,"륙":6,
        "칠":7,"팔":8,"구":9}
_MUL = {"십":10, "백":100, "천":1000}
_BIG = {"만":10**4, "억":10**8, "조":10**12}
_NUMCH = set(_DIG) | set(_MUL) | set(_BIG)
# 수사 뒤에 이게 오면 "수"로 확정한다. 조사·대명사 오탐을 막는 장치.
_UNIT = ("년","월","일","시","분","초","명","개","톤","미터","킬로","센티","도",
         "배","번","원","살","층","권","장","대","척","마리","겹","자루","%","위","차")

def _k2n(s: str) -> int | None:
    """순수 한글 수사 한 덩어리를 정수로."""
    total = cur = 0
    for ch in s:
        if ch in _DIG:
            cur = cur * 10 + _DIG[ch] if cur and cur < 10 else _DIG[ch]
        elif ch in _MUL:
            cur = (cur or 1) * _MUL[ch]
            total += cur
            cur = 0
        elif ch in _BIG:
            total = (total + cur or 1) * _BIG[ch]
            cur = 0
        else:
            return None
    return total + cur


_NUMRUN = re.compile("[" + "".join(_NUMCH) + "]{2,}")


def to_digits(text: str) -> str:
    """자막 표시용. 단위가 뒤따르거나 3자 이상인 수사만 바꾼다."""
    def rep(m):
        s, end = m.group(), m.end()
        tail = text[end:end + 3]
        if len(s) < 3 and not tail.startswith(_UNIT):
            return s                      # "이", "일" 같은 오탐 방지
        v = _k2n(s)
        if v is None:
            return s
        # 연도에 쉼표를 찍으면 어색하다 ("1,972년" → "1972년")
        if tail.startswith("년") and 1000 <= v <= 2999:
            return str(v)
        return f"{v:,}" if v >= 10000 else str(v)
    return _NUMRUN.sub(rep, text)


def no_break(prev: str, nxt: str) -> bool:
    """이 두 어절 사이는 자르면 안 된다."""
    p = prev.rstrip(".,!?")
    n = nxt.rstrip(".,!?")
    if NUM_END.search(p) and n.startswith(UNITS):
        return True
    if p.endswith(("아", "어")) and n.startswith(AUX_VERB):
        return True
    if (p, n) in FIXED_PHRASE_PAIRS:
        return True
    return False


def atoms(words: list[str]) -> list[str]:
    """끊으면 안 되는 어절 짝을 하나로 미리 묶는다."""
    out: list[str] = []
    for w in words:
        if out and no_break(out[-1], w):
            out[-1] = out[-1] + " " + w
        else:
            out.append(w)
    return out


def sentences(text: str) -> list[str]:
    out: list[str] = []
    for para in [p.strip() for p in text.split("\n\n") if p.strip()]:
        out += [s.strip() for s in SENT_END.split(para) if s.strip()]
    return out


def bad_head(word: str) -> bool:
    """이 어절로 줄을 시작하면 어색한가."""
    if JOSA_ONLY.match(word.rstrip(".,!?")):
        return True
    bare = word.rstrip(".,!?")
    return any(bare.startswith(d) and len(bare) <= len(d) + 2 for d in DEPENDENT_HEAD)


def pack(words: list[str], max_chars: int, target: int) -> list[str]:
    """한 문장을 줄 단위로 나눈다. 경계는 항상 어절 사이.

    앞에서부터 욕심껏 채우면(greedy) 문장 끝에 「보죠.」 같은 3자짜리 꼬리가
    남는다. 0.26초 떴다 사라져서 읽히지 않는다. 그래서 문장 전체를 보고
    **모든 줄이 목표 길이에 고르게 가깝도록** 나눈다(DP).

      비용 = Σ(줄길이 − 목표)²   ← 마지막 줄도 똑같이 물린다

    제곱이라 한 줄만 유난히 짧거나 긴 배치가 강하게 걸러진다.
    """
    n = len(words)
    if n == 0:
        return []

    cum = [0]
    for w in words:
        cum.append(cum[-1] + len(w))

    def line_len(i: int, j: int) -> int:
        return cum[j] - cum[i] + (j - i - 1)      # 어절 사이 공백

    INF = float("inf")
    cost = [INF] * (n + 1)
    prev = [0] * (n + 1)
    cost[0] = 0.0

    for j in range(1, n + 1):
        for i in range(j - 1, -1, -1):
            L = line_len(i, j)
            if L > max_chars and j - i > 1:
                break                              # 더 늘려봐야 넘치기만 한다
            if cost[i] == INF:
                continue
            c = float((L - target) ** 2)
            if L > max_chars:                      # 어절 하나가 상한보다 길 때만
                c += 10_000 * (L - max_chars)
            if i > 0 and bad_head(words[i]):       # 의존 어절로 줄을 시작하지 않는다
                c += 400
            if cost[i] + c < cost[j]:
                cost[j] = cost[i] + c
                prev[j] = i

    lines, j = [], n
    while j > 0:
        i = prev[j]
        lines.append(" ".join(words[i:j]))
        j = i
    return lines[::-1]


def main() -> int:
    ap = argparse.ArgumentParser(description="캡컷 자막 분할기")
    ap.add_argument("script", type=Path)
    ap.add_argument("--max", type=int, default=MAX_CHARS)
    ap.add_argument("--target", type=int, default=TARGET)
    ap.add_argument("--out", type=Path, default=None,
                    help="출력 JSON(기본: 대본 폴더/자막.json)")
    ap.add_argument("--srt", action="store_true", help="SRT도 저장(길이 균등 배분)")
    ap.add_argument("--cps", type=float, default=CFG.get("출력.발화속도_실측", 9.35), help="SRT 타이밍용 자/초")
    args = ap.parse_args()

    if not args.script.exists():
        sys.exit(f"[에러] 파일이 없습니다: {args.script}")

    text = args.script.read_text(encoding="utf-8")
    cues: list[dict] = []
    for si, sent in enumerate(sentences(text), 1):
        for line in pack(atoms(sent.split()), args.max, args.target):
            shown = to_digits(line)
            cues.append({"n": len(cues) + 1, "sent": si,
                         "text": shown, "raw": line, "len": len(shown)})

    over = [c for c in cues if c["len"] > args.max]
    lens = [c["len"] for c in cues]

    print(f"\n대본   : {args.script}")
    print(f"자막   : {len(cues)}개")
    print(f"글자수 : 최소 {min(lens)} / 최대 {max(lens)} / 평균 {sum(lens)/len(lens):.1f}")
    print(f"상한   : {args.max}자  (실측 프로젝트 최대 17자)")
    print(f"초과   : {len(over)}개\n")

    for c in cues:
        mark = "×" if c["len"] > args.max else " "
        print(f" {mark}{c['n']:>3}. [{c['len']:>2}] {c['text']}")

    if over:
        print("\n★ 상한 초과 — 대본 문장을 줄이거나 --max 를 조정하세요:")
        for c in over:
            print(f"    {c['n']}. [{c['len']}] {c['text']}")

    if args.out is None:
        out = args.script.parent / "자막.json"
    else:
        out = args.out if args.out.is_absolute() else args.script.parent / args.out
    out.write_text(json.dumps(
        {"source": str(args.script), "max_chars": args.max, "count": len(cues),
         "cues": cues}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  자막 큐 → {out}")

    if args.srt:
        def ts(sec: float) -> str:
            h, r = divmod(sec, 3600); m, s = divmod(r, 60)
            return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s%1)*1000):03d}"
        srt, t = [], 0.0
        for c in cues:
            dur = max(0.30, c["len"] / args.cps)
            srt.append(f"{c['n']}\n{ts(t)} --> {ts(t+dur)}\n{c['text']}\n")
            t += dur + 0.02          # 실측 간격 중앙값 0.017초
        p = out.with_suffix(".srt")
        p.write_text("\n".join(srt), encoding="utf-8-sig")
        print(f"  SRT     → {p}  (총 {t/60:.2f}분 — 실제 싱크는 TTS에 맞춰 캡컷에서 조정)")

    print()
    return 1 if over else 0


if __name__ == "__main__":
    raise SystemExit(main())
