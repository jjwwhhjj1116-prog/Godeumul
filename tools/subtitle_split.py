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
  · 너무 짧은 꼬리(3자 미만)는 앞 큐와 재분배한다

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
MIN_TAIL = 3        # 이보다 짧은 꼬리는 앞과 재분배

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


def no_break(prev: str, nxt: str) -> bool:
    """이 두 어절 사이는 자르면 안 된다."""
    p = prev.rstrip(".,!?")
    n = nxt.rstrip(".,!?")
    if NUM_END.search(p) and n.startswith(UNITS):
        return True
    if p.endswith(("아", "어")) and n.startswith(AUX_VERB):
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
    """어절을 줄 단위로 담는다. 경계는 항상 어절 사이."""
    lines: list[str] = []
    cur: list[str] = []

    def cur_len(extra: str | None = None) -> int:
        parts = cur + ([extra] if extra else [])
        return len(" ".join(parts))

    for w in words:
        if not cur:
            cur = [w]
            continue
        if cur_len(w) <= max_chars:
            # 목표를 넘었고, 다음 어절을 앞으로 보내도 어색하지 않으면 여기서 끊는다
            if cur_len() >= target and not bad_head(w) and cur_len(w) > target + 3:
                lines.append(" ".join(cur))
                cur = [w]
            else:
                cur.append(w)
        else:
            if bad_head(w) and len(cur) > 1:
                # 의존 어절은 홀로 못 넘어간다 → 앞 어절을 함께 내린다
                moved = cur.pop()
                lines.append(" ".join(cur))
                cur = [moved, w]
            else:
                lines.append(" ".join(cur))
                cur = [w]

    if cur:
        lines.append(" ".join(cur))

    # 짧은 꼬리 재분배
    if len(lines) >= 2 and len(lines[-1]) < MIN_TAIL:
        merged = lines[-2] + " " + lines[-1]
        if len(merged) <= max_chars:
            lines[-2:] = [merged]
        else:
            ws = merged.split()
            half = len(ws) // 2
            lines[-2:] = [" ".join(ws[:half]), " ".join(ws[half:])]
    return lines


def main() -> int:
    ap = argparse.ArgumentParser(description="캡컷 자막 분할기")
    ap.add_argument("script", type=Path)
    ap.add_argument("--max", type=int, default=MAX_CHARS)
    ap.add_argument("--target", type=int, default=TARGET)
    ap.add_argument("--srt", action="store_true", help="SRT도 저장(길이 균등 배분)")
    ap.add_argument("--cps", type=float, default=8.07, help="SRT 타이밍용 자/초 (실측 8.07)")
    args = ap.parse_args()

    if not args.script.exists():
        sys.exit(f"[에러] 파일이 없습니다: {args.script}")

    text = args.script.read_text(encoding="utf-8")
    cues: list[dict] = []
    for si, sent in enumerate(sentences(text), 1):
        for line in pack(atoms(sent.split()), args.max, args.target):
            cues.append({"n": len(cues) + 1, "sent": si, "text": line, "len": len(line)})

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

    out = args.script.parent / "자막.json"
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
        p = args.script.parent / "자막.srt"
        p.write_text("\n".join(srt), encoding="utf-8-sig")
        print(f"  SRT     → {p}  (총 {t/60:.2f}분 — 실제 싱크는 TTS에 맞춰 캡컷에서 조정)")

    print()
    return 1 if over else 0


if __name__ == "__main__":
    raise SystemExit(main())
