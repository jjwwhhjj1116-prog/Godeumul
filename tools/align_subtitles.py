#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
[고대유물의 비밀] 5단계 보조 — 자막 실측 싱크

글자수 비율로 자막을 배분하면 TTS와 안 맞는다. 실제 오디오에서 문자 단위
타임스탬프를 받아 자막 큐마다 정확한 시작·끝을 박는다.

정렬 방법: ElevenLabs **강제 정렬(forced alignment)**.
Whisper 받아쓰기와 달리 <내가 가진 정확한 원문>을 오디오에 맞추므로
오인식이 없다. 장면 mp3 + 그 장면 나레이션을 넣으면 문자별 초를 돌려준다.

  대본 문장 → subtitle_split 이 자른 큐 → 이 스크립트가 큐마다 실측 시각 부여
  → capcut_build 가 그 시각으로 자막 세그먼트를 놓는다.

사용법
  python tools/align_subtitles.py 산출물/EP01_진시황릉
  python tools/align_subtitles.py 산출물/EP01_진시황릉 --force   # 캐시 무시
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests

from _config import load_env as _cfg_env

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.elevenlabs.io/v1/forced-alignment"


def load_key() -> str:
    k = _cfg_env().get("ELEVENLABS_API_KEY", "")
    if not k:
        sys.exit("[에러] .env 에 ELEVENLABS_API_KEY 가 없습니다.")
    return k


def align(key: str, audio: Path, text: str) -> list[dict]:
    """문자 단위 [{char,start,end}] 를 돌려준다."""
    with audio.open("rb") as fh:
        r = requests.post(API, headers={"xi-api-key": key},
                          files={"file": (audio.name, fh, "audio/mpeg")},
                          data={"text": text}, timeout=180)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
    d = r.json()
    chars = d.get("characters") or []
    if chars:
        return [{"c": c.get("text", ""), "s": c["start"], "e": c["end"]} for c in chars]
    # characters 가 없으면 words 를 글자로 펼친다
    out = []
    for w in d.get("words") or []:
        t = w.get("text", "")
        if not t:
            continue
        step = (w["end"] - w["start"]) / len(t)
        for i, ch in enumerate(t):
            out.append({"c": ch, "s": w["start"] + i * step, "e": w["start"] + (i + 1) * step})
    return out


def norm(s: str) -> str:
    """비교용: 공백·문장부호를 뺀다."""
    return re.sub(r"[\s.,!?·…\"']", "", s)


def main() -> int:
    ap = argparse.ArgumentParser(description="자막 실측 싱크")
    ap.add_argument("episode", type=Path)
    ap.add_argument("--force", action="store_true", help="정렬 캐시 무시")
    args = ap.parse_args()

    ep = args.episode.resolve()
    man_p = ep / "audio" / "durations.json"
    cue_p = ep / "자막.json"
    cache_p = ep / "audio" / "alignment.json"
    if not man_p.exists() or not cue_p.exists():
        sys.exit("[에러] durations.json 또는 자막.json 이 없습니다. 3단계·자막분할을 먼저.")

    key = load_key()
    scenes = json.loads(man_p.read_text(encoding="utf-8"))["scenes"]
    cues = json.loads(cue_p.read_text(encoding="utf-8"))["cues"]

    cache = {}
    if cache_p.exists() and not args.force:
        cache = json.loads(cache_p.read_text(encoding="utf-8"))

    # ── 장면별 정렬 ─────────────────────────────────────
    print(f"\n에피소드 : {ep.name}")
    print(f"장면 {len(scenes)}개 · 자막 큐 {len(cues)}개\n")
    for k in sorted(scenes, key=int):
        if k in cache and not args.force:
            print(f"  [건너뜀] 장면 {k}")
            continue
        audio = ep / "audio" / scenes[k]["file"]
        try:
            cache[k] = align(key, audio, scenes[k]["text"])
            print(f"  [정렬]   장면 {k:>2}  문자 {len(cache[k]):>3}개")
        except Exception as exc:
            print(f"  [실패]   장면 {k:>2}  {exc}")
            return 1
        time.sleep(0.4)
    cache_p.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")

    # ── 큐를 장면에 배정하고 실측 시각 부여 ──────────────
    # 큐 텍스트를 장면 원문에 순서대로 이어붙여 소비하며 문자 인덱스를 따라간다.
    out, ci, scene_keys = [], 0, sorted(scenes, key=int)
    si = 0
    pos = 0                      # 현재 장면 원문에서 소비한 정규화 문자 수
    scene_norm = norm(scenes[scene_keys[0]]["text"])
    base = 0.0                   # 현재 장면의 타임라인 시작(초)
    starts = {}
    acc = 0.0
    for k in scene_keys:
        starts[k] = acc
        acc += scenes[k]["duration"]

    for cue in cues:
        cn = norm(cue["text"])
        # 현재 장면에 안 들어가면 다음 장면으로
        while si < len(scene_keys) and pos + len(cn) > len(scene_norm):
            si += 1
            if si >= len(scene_keys):
                break
            pos = 0
            scene_norm = norm(scenes[scene_keys[si]]["text"])
        if si >= len(scene_keys):
            break
        k = scene_keys[si]
        chars = [c for c in cache[k] if norm(c["c"])]      # 공백 제외
        s_idx, e_idx = pos, min(pos + len(cn) - 1, len(chars) - 1)
        if s_idx >= len(chars):
            break
        st = starts[k] + chars[s_idx]["s"]
        en = starts[k] + chars[e_idx]["e"]
        out.append({"n": len(out) + 1, "scene": int(k), "text": cue["text"],
                    "len": len(cue["text"]),
                    "start": round(st, 3), "end": round(en, 3),
                    "dur": round(en - st, 3)})
        pos += len(cn)

    # ── 검증 ────────────────────────────────────────────
    bad_order = sum(1 for a, b in zip(out, out[1:]) if b["start"] < a["start"])
    overlap = sum(1 for a, b in zip(out, out[1:]) if b["start"] < a["end"] - 0.001)
    short = [c["n"] for c in out if c["dur"] < 0.15]
    cps = [c["len"] / c["dur"] for c in out if c["dur"] > 0]

    print(f"\n큐 {len(out)}/{len(cues)}개 배치")
    print(f"  순서 역전 {bad_order} · 겹침 {overlap} · 0.15초 미만 {len(short)}")
    print(f"  표시속도 {min(cps):.1f}~{max(cps):.1f} 자/초 (중앙 {sorted(cps)[len(cps)//2]:.1f})")
    print(f"  첫 큐 {out[0]['start']:.2f}s  끝 큐 {out[-1]['end']:.2f}s")

    p = ep / "자막_싱크.json"
    p.write_text(json.dumps({"source": "elevenlabs-forced-alignment",
                             "count": len(out), "cues": out},
                            ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  싱크 자막 → {p}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
