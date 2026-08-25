#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
[고대유물의 비밀] 3단계 보조 — 나레이션 라우드니스 정규화

캡컷은 오디오에 **선형 배율**만 걸 수 있다. 리미터가 없으니 배율을 키우면
피크가 0dBFS를 그냥 뚫고 하드 클리핑이 난다. EP01 투탕카멘 템플릿에서 물려받은
볼륨 1.778(+5.0dB)이 실제로 트루피크 +4.2dBFS를 만들고 있었다.

그래서 게인은 캡컷이 아니라 **여기서 파일에 굽는다.**

  1. 장면별 mp3 를 이어붙여 <전체 프로그램> 라우드니스를 잰다
  2. 목표 LUFS 까지 필요한 게인을 하나 구한다  ← 장면마다 따로 재지 않는다.
     장면별 정규화는 조용해야 할 대목까지 끌어올려 강약을 뭉갠다
  3. 모든 파일에 같은 게인 + 트루피크 리미터를 걸어 다시 쓴다
  4. 길이가 1ms라도 변했으면 되돌린다 (자막 싱크가 어긋나므로)

끝나면 캡컷 볼륨은 1.0 이면 된다. capcut_build 가 채널설정.json 의
`오디오.캡컷볼륨` 을 읽어 그렇게 넣는다.

사용법
  python tools/audio_normalize.py 산출물/EP01_진시황릉            # 측정만
  python tools/audio_normalize.py 산출물/EP01_진시황릉 --run      # 실제로 다시 씀
  python tools/audio_normalize.py 산출물/EP01_진시황릉 --audio-dir audio_v4 --run
  python tools/audio_normalize.py 산출물/EP01_진시황릉 --복구     # 백업에서 되돌림
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from _config import load

CFG = load()
BACKUP = "_원본"
SCENE_AUDIO_RE = re.compile(r"^\d{3}\.mp3$")
MP3_TRUE_PEAK_MARGIN_DB = 0.5


def run(cmd: list[str]) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return (r.stdout or "") + (r.stderr or "")


def have_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def duration(p: Path) -> float:
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "csv=p=0", str(p)]).strip()
    try:
        return float(out)
    except ValueError:
        return -1.0


def measure(files: list[Path], gain_db: float = 0.0) -> tuple[float, float]:
    """이어붙인 전체의 (통합 LUFS, 트루피크 dBFS)."""
    lst = files[0].parent / "_concat.txt"
    lst.write_text("".join(f"file '{f.name}'\n" for f in files), encoding="utf-8")
    af = "ebur128=peak=true" if not gain_db else f"volume={gain_db}dB,ebur128=peak=true"
    try:
        out = run(["ffmpeg", "-hide_banner", "-f", "concat", "-safe", "0",
                   "-i", str(lst), "-af", af, "-f", "null", "-"])
    finally:
        lst.unlink(missing_ok=True)
    i = re.search(r"^\s+I:\s+(-?[\d.]+) LUFS", out, re.M)
    pk = re.search(r"Peak:\s+(-?[\d.]+) dBFS", out)
    if not i or not pk:
        sys.exit(f"[에러] 라우드니스 측정 실패:\n{out[-800:]}")
    return float(i.group(1)), float(pk.group(1))


def main() -> int:
    ap = argparse.ArgumentParser(description="나레이션 라우드니스 정규화")
    ap.add_argument("episode", type=Path)
    ap.add_argument("--audio-dir", default="audio",
                    help="에피소드 아래 오디오 폴더(기본: audio)")
    ap.add_argument("--run", action="store_true", help="실제로 파일을 다시 쓴다")
    ap.add_argument("--복구", dest="restore", action="store_true")
    args = ap.parse_args()

    if not have_ffmpeg():
        sys.exit("[에러] ffmpeg / ffprobe 가 PATH 에 없습니다.")

    ep = args.episode.resolve()
    adir = ep / args.audio_dir
    bdir = adir / BACKUP
    # 장면 원본만 처리한다. 합본·미리듣기 mp3를 포함하면
    # 프로그램 길이와 라우드니스가 이중 계산된다.
    files = sorted(p for p in adir.glob("*.mp3") if SCENE_AUDIO_RE.match(p.name))
    if not files:
        sys.exit(f"[에러] mp3 가 없습니다: {adir}")

    # ── 복구 ────────────────────────────────────────────
    if args.restore:
        if not bdir.exists():
            sys.exit(f"[에러] 백업이 없습니다: {bdir}")
        n = 0
        for b in bdir.glob("*.mp3"):
            shutil.copy2(b, adir / b.name)
            n += 1
        print(f"\n  {n}개 파일을 백업에서 되돌렸습니다.\n")
        return 0

    target = CFG.get("오디오.목표LUFS", -16.0)
    tp_max = CFG.get("오디오.트루피크상한dBFS", -1.5)
    gain_cap = CFG.get("오디오.게인상한dB", 12.0)

    print(f"\n에피소드 : {ep.name}")
    print(f"파일     : {len(files)}개")
    print(f"목표     : {target} LUFS · 트루피크 {tp_max} dBFS 이하\n")

    # ★ 게인은 <변환의 입력이 될 파일> 기준으로 재야 한다.
    #   백업이 있으면 변환은 백업(원본)에서 하므로, 측정도 백업에서 한다.
    #   현재 파일에서 재면 두 번째 실행부터 게인이 틀어진다.
    backup_files = sorted(
        p for p in bdir.glob("*.mp3") if SCENE_AUDIO_RE.match(p.name)
    ) if bdir.exists() else []
    src_files = backup_files or files
    src_label = "원본(백업)" if bdir.exists() else "현재"

    print(f"  {src_label} 측정 중…")
    cur_i, cur_tp = measure(src_files)
    gain = round(min(target - cur_i, gain_cap), 1)

    print(f"  {src_label:<9}: {cur_i:>6.1f} LUFS · 트루피크 {cur_tp:>5.1f} dBFS")
    print(f"  필요 게인: {gain:>+6.1f} dB")
    if gain >= gain_cap:
        print(f"  ★ 게인 상한({gain_cap}dB)에 걸렸습니다. 원본이 너무 작습니다.")

    # 게인만 걸면 피크가 얼마나 뚫는지
    naive_tp = cur_tp + gain
    if naive_tp > tp_max:
        print(f"  게인만 걸면 트루피크 {naive_tp:+.1f} dBFS "
              f"→ {naive_tp - tp_max:.1f}dB 초과. 리미터가 필요합니다.")
    else:
        print(f"  게인만 걸어도 트루피크 {naive_tp:+.1f} dBFS — 리미터 불필요.")

    if abs(gain) < 0.2 and cur_tp <= tp_max:
        print("\n  이미 목표에 맞습니다. 할 일 없음.\n")
        return 0

    # volume → alimiter(트루피크 상한) 순서. alimiter 는 선형 진폭을 받는다.
    # MP3 인코딩 후 인터샘플 피크가 약간 다시 오를 수 있다.
    # 채널 상한보다 0.5dB 낮게 리미트해 재인코딩 후에도 상한을 지킨다.
    limit_db = tp_max - MP3_TRUE_PEAK_MARGIN_DB
    limit = 10 ** (limit_db / 20)

    if not args.run:
        print(f"\n  적용할 필터: volume={gain}dB,"
              f"alimiter=limit={limit:.4f}:level=disabled")
        print("  (측정만 했습니다. 실제로 쓰려면 --run)\n")
        return 0

    # ── 백업 후 다시 쓰기 ───────────────────────────────
    bdir.mkdir(exist_ok=True)
    print(f"\n  백업 → {bdir}")
    for f in files:
        b = bdir / f.name
        if not b.exists():
            shutil.copy2(f, b)

    def apply(g: float) -> tuple[list[tuple[str, float, float]], str]:
        """원본에서 게인 g + 리미터를 걸어 다시 쓴다. 길이가 변한 파일 목록을 돌려준다."""
        flt = f"volume={g}dB,alimiter=limit={limit:.4f}:level=disabled"
        bad = []
        for f in files:
            src = bdir / f.name
            before = duration(src)
            tmp = f.with_suffix(".tmp.mp3")
            out = run(["ffmpeg", "-hide_banner", "-loglevel", "error",
                       "-i", str(src), "-af", flt,
                       "-ar", "44100", "-b:a", "128k", "-y", str(tmp)])
            if not tmp.exists() or tmp.stat().st_size < 1024:
                sys.exit(f"[에러] {f.name} 변환 실패:\n{out[-500:]}")
            after = duration(tmp)
            if abs(after - before) > 0.001:
                tmp.unlink(missing_ok=True)
                bad.append((f.name, before, after))
                continue
            tmp.replace(f)
        return bad, flt

    # 리미터가 피크를 깎으면 결과가 목표보다 조금 낮게 앉는다.
    # 원본에서 다시 굽는 방식이라 몇 번을 돌려도 세대열화가 없다 → 목표까지 수렴시킨다.
    print("  다시 쓰는 중…")
    drift, af = apply(gain)
    new_i, new_tp = measure(files)
    for _ in range(3):
        if drift or abs(new_i - target) <= 0.3:
            break
        adj = round(min(gain + (target - new_i), gain_cap), 1)
        if abs(adj - gain) < 0.1:
            break
        gain = adj
        print(f"    보정 게인 {gain:+.1f} dB  (직전 결과 {new_i:.1f} LUFS)")
        drift, af = apply(gain)
        new_i, new_tp = measure(files)

    if drift:
        print(f"\n  ★ 길이가 변한 파일 {len(drift)}개 — 적용하지 않았습니다:")
        for n, b, a in drift[:5]:
            print(f"      {n}  {b:.3f} → {a:.3f}s")
        print("      자막 싱크가 어긋나므로 그대로 두었습니다.")
        return 1

    print(f"\n  결과     : {new_i:>6.1f} LUFS · 트루피크 {new_tp:>5.1f} dBFS")
    ok_tp = new_tp <= tp_max + 0.2
    print(f"  트루피크 : {'통과' if ok_tp else '★ 초과'} (상한 {tp_max})")
    print(f"  길이     : 전 {len(files)}개 1ms 이내 보존")

    (adir / "loudness.json").write_text(json.dumps(
        {"before": {"lufs": cur_i, "true_peak": cur_tp},
         "after": {"lufs": new_i, "true_peak": new_tp},
         "gain_db": gain, "filter": af,
         "capcut_volume": CFG.get("오디오.캡컷볼륨", 1.0)},
        ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n  캡컷 볼륨은 {CFG.get('오디오.캡컷볼륨', 1.0)} 로 두세요. "
          f"드래프트를 다시 만들면 자동 반영됩니다.")
    print(f"  되돌리려면: python tools/audio_normalize.py {args.episode} --복구\n")
    return 0 if ok_tp else 1


if __name__ == "__main__":
    raise SystemExit(main())
