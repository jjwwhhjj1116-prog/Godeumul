#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
[고대유물의 비밀] 5단계 보조 — 캡컷 장면별 속도표 생성기

3단계의 durations.json(TTS 길이)과 4단계의 clips/ 폴더(영상 길이)를 대조해서,
각 장면을 나레이션에 맞추려면 캡컷에서 몇 배속으로 놓아야 하는지 계산한다.

  배속 = 영상 길이 ÷ TTS 길이

  예) 8.0초 클립 · 5.2초 나레이션 → 8.0 / 5.2 = 1.54x (빠르게)
      5.0초 클립 · 6.5초 나레이션 → 5.0 / 6.5 = 0.77x (느리게)

자연스러운 범위를 벗어나면 경고한다. 그 장면은 배속으로 때우지 말고
클립을 다시 뽑거나 컷을 쪼개야 한다.

사용법
  python tools/speed_table.py 산출물/EP01_진시황릉
  python tools/speed_table.py 산출물/EP01_진시황릉 --csv
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# 실제 프로젝트("투탕카멘_고대유물의 비밀") 실측 배속은 0.78x~3.80x였다.
# 생성 클립이 대부분 느린 카메라 무빙이라 3배속도 티가 안 난다.
SPEED_OK = (0.75, 3.00)
SPEED_WARN = (0.50, 4.50)

VIDEO_EXTS = (".mp4", ".mov", ".webm", ".mkv", ".m4v")
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")


def probe(path: Path) -> float:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, check=True,
        )
        return round(float(out.stdout.strip()), 3)
    except Exception:
        return 0.0


def find_media(folder: Path, seq: int) -> tuple[Path | None, str]:
    """영상 우선, 없으면 이미지. 무협 파이프라인의 find_scene_media와 같은 순서."""
    stem = f"{seq:03d}"
    for ext in VIDEO_EXTS:
        p = folder / f"{stem}{ext}"
        if p.exists():
            return p, "video"
    for ext in IMAGE_EXTS:
        p = folder / f"{stem}{ext}"
        if p.exists():
            return p, "image"
    return None, "none"


def verdict(ratio: float) -> tuple[str, str]:
    lo, hi = SPEED_OK
    wlo, whi = SPEED_WARN
    if lo <= ratio <= hi:
        return "OK", ""
    if ratio > whi:
        return "위험", "클립이 너무 김 — 컷을 둘로 쪼개거나 짧게 재생성"
    if ratio < wlo:
        return "위험", "클립이 너무 짧음 — 길게 재생성하거나 정지컷+켄번즈로"
    if ratio > hi:
        return "주의", "빠르게 티남 — 앞뒤를 조금 잘라내는 편이 낫다"
    return "주의", "느리게 티남 — 프레임 보간을 켜거나 클립을 늘려라"


def main() -> int:
    ap = argparse.ArgumentParser(description="캡컷 장면별 속도표 생성기")
    ap.add_argument("episode", type=Path, help="에피소드 폴더 (audio/ clips/ 포함)")
    ap.add_argument("--clips", type=Path, default=None, help="클립 폴더 (기본: <episode>/clips)")
    ap.add_argument("--csv", action="store_true", help="CSV도 함께 저장")
    args = ap.parse_args()

    manifest_path = args.episode / "audio" / "durations.json"
    if not manifest_path.exists():
        sys.exit(f"[에러] durations.json 이 없습니다: {manifest_path}\n"
                 f"       3단계(tts_generate.py --run)를 먼저 돌리세요.")

    clips = args.clips or args.episode / "clips"
    if not clips.exists():
        sys.exit(f"[에러] 클립 폴더가 없습니다: {clips}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scenes = manifest.get("scenes", {})

    rows = []
    missing = []
    for key in sorted(scenes, key=int):
        seq = int(key)
        tts = scenes[key].get("duration") or 0.0
        if tts <= 0:
            missing.append((seq, "TTS 길이 없음 — --run 으로 실제 생성 필요"))
            continue

        media, kind = find_media(clips, seq)
        if media is None:
            missing.append((seq, "클립/이미지 없음"))
            continue

        if kind == "image":
            rows.append({"seq": seq, "kind": "이미지", "clip": 0.0, "tts": tts,
                         "ratio": None, "state": "—",
                         "note": f"정지컷 → {tts:.2f}초로 길이 지정 + 켄번즈",
                         "file": media.name})
            continue

        clip = probe(media)
        if clip <= 0:
            missing.append((seq, f"길이를 못 읽음: {media.name}"))
            continue

        ratio = round(clip / tts, 3)
        state, note = verdict(ratio)
        rows.append({"seq": seq, "kind": "영상", "clip": clip, "tts": tts,
                     "ratio": ratio, "state": state, "note": note,
                     "file": media.name})

    # ── 출력 ──────────────────────────────────────────────
    print(f"\n에피소드 : {args.episode}")
    print(f"클립     : {clips}")
    print(f"장면     : {len(rows)}개 처리 / {len(missing)}개 누락\n")

    head = f"  {'장면':>4} {'종류':<5} {'클립':>7} {'나레이션':>9} {'배속':>7}  {'판정':<5} 비고"
    print(head)
    print("  " + "─" * (len(head) + 12))

    warn = crit = 0
    for r in rows:
        ratio = f"{r['ratio']:.3f}x" if r["ratio"] is not None else "     —"
        clip = f"{r['clip']:.2f}s" if r["clip"] else "    —"
        mark = {"OK": " ", "주의": "!", "위험": "×", "—": " "}[r["state"]]
        if r["state"] == "주의":
            warn += 1
        if r["state"] == "위험":
            crit += 1
        print(f" {mark}{r['seq']:>4} {r['kind']:<5} {clip:>7} {r['tts']:>8.2f}s "
              f"{ratio:>8}  {r['state']:<5} {r['note']}")

    if missing:
        print("\n  누락:")
        for seq, why in missing:
            print(f"    장면 {seq:>3} — {why}")

    total_tts = sum(r["tts"] for r in rows)
    print(f"\n  나레이션 총 길이 {total_tts:.2f}초 ({total_tts / 60:.2f}분)")
    print(f"  주의 {warn}개 · 위험 {crit}개")
    if crit:
        print("  ★ 위험 장면은 배속으로 때우지 말고 클립을 다시 뽑으세요.")

    out = args.episode / "speed_table.json"
    out.write_text(json.dumps(
        {"episode": str(args.episode), "total_tts": round(total_tts, 3),
         "rows": rows, "missing": [{"seq": s, "reason": w} for s, w in missing]},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  속도표 → {out}")

    if args.csv:
        csv_path = args.episode / "speed_table.csv"
        lines = ["장면,종류,클립초,나레이션초,배속,판정,비고,파일"]
        for r in rows:
            ratio = f"{r['ratio']}" if r["ratio"] is not None else ""
            lines.append(f"{r['seq']},{r['kind']},{r['clip']},{r['tts']},"
                         f"{ratio},{r['state']},\"{r['note']}\",{r['file']}")
        csv_path.write_text("\n".join(lines), encoding="utf-8-sig")
        print(f"  CSV    → {csv_path}")

    print()
    return 1 if crit else 0


if __name__ == "__main__":
    raise SystemExit(main())
