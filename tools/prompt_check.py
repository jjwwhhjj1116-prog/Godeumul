#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
[고대유물의 비밀] 2단계 검수 — 시각화 프롬프트 고증 검증기

이 채널은 **유물의 고증을 설명하는 채널**이다. 동양 유물인데 서양 그림이 나오면
채널의 존재 이유가 무너진다. EP01에서 실제로 그랬다 — 중국 진나라 인부가
유럽인 얼굴에 로마식 튜닉으로 나왔고, 사각 계단식 봉토가 둥근 풀언덕이 됐다.

지침에 적어두는 것만으로는 부족했다. **이 검증기가 FLOW 에 넣기 전에 막는다.**

검사
  A 문명 앵커      모든 프롬프트에 문명·시대·지역 문장이 있는가
  B 인물 앵커      사람이 나오는 컷에 민족·복식·두발 앵커가 있는가
  C 금지어         tunic/toga 등 타 문명 복식 단어가 없는가
  D 유물 형태      고증 카드에 등록한 유물이 형태 문장과 함께 나오는가
  E 건축 앵커      건물이 나오는 컷에 양식 단어가 있는가
  F 네거티브       타 문명 차단 문구가 꼬리에 있는가
  G 라벨·해상도    라벨 1개 이하, 9:16 명시

사용법
  python tools/prompt_check.py 산출물/EP01_진시황릉
  python tools/prompt_check.py 산출물/EP01_진시황릉 -v     # 컷별 상세
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from _config import load

CFG = load()

# ── 규칙 ────────────────────────────────────────────────
# 타 문명 복식·건축 단어. 하나라도 있으면 실패.
BANNED = {
    "tunic": "로마·중세 유럽 복식",
    "toga": "로마 복식",
    "chiton": "그리스 복식",
    "doublet": "중세 유럽 복식",
    "tabard": "중세 유럽 복식",
    "loincloth": "이집트·열대 복식",
    "chainmail": "중세 유럽 갑옷",
    "chain mail": "중세 유럽 갑옷",
    "plate armor": "중세 유럽 갑옷",
    "corinthian": "그리스 기둥",
    "doric": "그리스 기둥",
    "ionic column": "그리스 기둥",
    "pharaoh": "이집트",
    "hieroglyph": "이집트",
    "pagoda": "일본·동남아 양식(중국 주제일 때)",
    "samurai": "일본",
    "kimono": "일본",
}

# 사람이 등장한다는 신호
PEOPLE_HINT = re.compile(
    r"\b(figures?|laborers?|labourers?|workers?|artisans?|masons?|soldiers?|"
    r"guards?|robbers?|intruders?|priests?|crowd|people|men|women)\b", re.I)
# 인물 앵커가 갖춰졌다는 신호 (민족 + 복식)
PEOPLE_OK = re.compile(r"east asian|chinese figures|chinese labo", re.I)
DRESS_OK = re.compile(r"cross-collared|topknot|dynasty dress", re.I)

# 건축이 등장한다는 신호
ARCH_HINT = re.compile(r"\b(palace|town|city|temple|building|roofs?|courtyards?|hall)\b", re.I)
ARCH_OK = re.compile(r"upturned eaves|bracket sets|rammed-earth walls|post-and-beam", re.I)

NEG_REQUIRED = ["no European or Western faces", "no anachronistic"]


class R:
    def __init__(self):
        self.rows = []

    def add(self, ok, cut, item, detail=""):
        self.rows.append((ok, cut, item, detail))

    @property
    def fails(self):
        return [r for r in self.rows if not r[0]]


def load_card(ep: Path) -> dict:
    """고증 카드에서 문명 앵커 문장과 유물 형태 키워드를 뽑는다."""
    p = ep / "02b.고증카드.md"
    if not p.exists():
        sys.exit(f"[에러] 고증 카드가 없습니다: {p}\n"
                 "       02 지침 「시대·문명 고증 앵커」 규칙 1 — 프롬프트보다 먼저 씁니다.")
    t = p.read_text(encoding="utf-8")
    blocks = re.findall(r"```\n(.*?)\n```", t, re.S)
    if not blocks:
        sys.exit(f"[에러] 고증 카드에 영문 앵커 블록(```)이 없습니다: {p}")
    civ = " ".join(blocks[0].split())
    return {"civ": civ, "civ_head": civ.split(",")[0].strip()}


def main() -> int:
    ap = argparse.ArgumentParser(description="시각화 프롬프트 고증 검증")
    ap.add_argument("episode", type=Path)
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--필드", dest="field", default=None,
                    help="검사할 필드 (기본: img_v2 있으면 그것, 없으면 img)")
    args = ap.parse_args()

    ep = args.episode.resolve()
    card = load_card(ep)
    sc = json.loads((ep / "02a.장면구분.json").read_text(encoding="utf-8"))
    rep = R()

    print(f"\n에피소드 : {ep.name}")
    print(f"문명 앵커 : {card['civ'][:70]}…")
    print(f"컷       : {len(sc)}개\n")

    for s in sc:
        n = s["n"]
        img = s.get(args.field) if args.field else (s.get("img_v2") or s.get("img", ""))
        if not img:
            rep.add(False, n, "프롬프트 없음")
            continue
        low = img.lower()

        # 인물·건축 탐지는 <실제 장면 묘사>에서만 한다.
        #   · 라벨 문구  reading "NO GUARDS"  → GUARDS 가 인물로 잡힌다
        #   · 네거티브   no people in the foreground → people 이 인물로 잡힌다
        scene = re.sub(r'reading "[^"]*"', "", img)
        scene = re.sub(r"\bno [a-z ]*?(people|figures?|faces|men|women)\b", "", scene, flags=re.I)

        # A 문명 앵커
        rep.add(card["civ_head"].lower() in low, n, "문명 앵커",
                "" if card["civ_head"].lower() in low else f"'{card['civ_head']}' 없음")

        # B 인물 앵커
        if PEOPLE_HINT.search(scene):
            ok = bool(PEOPLE_OK.search(img) and DRESS_OK.search(img))
            hit = PEOPLE_HINT.search(scene).group(0)
            rep.add(ok, n, "인물 앵커",
                    "" if ok else f"'{hit}' 가 있는데 민족·복식 앵커가 없다")

        # C 금지어
        for w, why in BANNED.items():
            if re.search(r"\b" + re.escape(w) + r"\b", low):
                rep.add(False, n, "금지어", f"'{w}' — {why}")

        # E 건축 앵커
        if ARCH_HINT.search(scene):
            ok = bool(ARCH_OK.search(img))
            hit = ARCH_HINT.search(scene).group(0)
            rep.add(ok, n, "건축 앵커",
                    "" if ok else f"'{hit}' 가 있는데 양식 단어가 없다")

        # F 네거티브
        miss = [k for k in NEG_REQUIRED if k.lower() not in low]
        rep.add(not miss, n, "네거티브", "" if not miss else f"누락: {miss}")

        # G 라벨 1개 이하 · 9:16
        labels = re.findall(r'reading "([^"]+)"', img)
        rep.add(len(labels) <= 1, n, "라벨 수",
                "" if len(labels) <= 1 else f"{len(labels)}개: {labels}")
        rep.add("9:16" in img, n, "세로 규격", "" if "9:16" in img else "9:16 없음")

        if args.verbose:
            mine = [r for r in rep.rows if r[1] == n]
            bad = [r for r in mine if not r[0]]
            mark = "OK " if not bad else "★  "
            print(f"  {mark}컷{n:>2} {s['ct']:<9} 검사 {len(mine)}개"
                  + ("" if not bad else "  → " + "; ".join(f"{i}({d})" for _, _, i, d in bad)))

    # ── 결과 ────────────────────────────────────────────
    fails = rep.fails
    if not args.verbose:
        by_cut = {}
        for _, n, item, detail in fails:
            by_cut.setdefault(n, []).append(f"{item}" + (f" ({detail})" if detail else ""))
        for n in sorted(by_cut):
            print(f"  ★ 컷{n:>2}  " + " · ".join(by_cut[n]))

    print(f"\n{'─'*66}")
    print(f"검사 {len(rep.rows)}건 · 통과 {len(rep.rows)-len(fails)} · 실패 {len(fails)}")
    if fails:
        print(f"\n★ {len(set(f[1] for f in fails))}개 컷이 고증 검증을 통과하지 못했습니다.")
        print("  이 상태로 FLOW 에 넣으면 서양 그림이 나옵니다.")
        print("  02b.고증카드.md 의 앵커를 프롬프트에 넣으세요.\n")
        return 1
    print("\n고증 이상 없음. FLOW 에 넣어도 됩니다.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
