#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
[고대유물의 비밀] 5단계 대안 — 캡컷 없이 완성본 렌더

캡컷 GUI를 사람이 열어 내보내는 대신 ffmpeg 으로 바로 굽는다.
드래프트와 **같은 소스**(clips / 정규화된 audio / 자막_싱크.json / 워터마크)를
쓰므로 결과가 같아야 한다. 스타일 값은 실제 캡컷 출력물에서 실측해 맞췄다.

  자막 크기 : 캡컷 size 12  →  1080x1920 에서 **74px**
              (투탕카멘 완성본 2160x3840 프레임에서 잉크 높이 134px 실측 →
               1920 기준 67px → KCC간판체로 역산. 오차 폭 -1.1% / 높이 0.0%)
  자막 위치 : y = -0.206  →  중심 y = 960 + 0.206*960 = 1158px
  외곽선    : border_width 0.08  →  74 * 0.08 ≈ 6px
  워터마크  : 1254 정사각 → 캔버스 폭에 맞춘 1080 → x0.2304 = 249px
              중심 (540 + 0.6772*540, 960 + 0.8164*960) = (906, 1744)
              크로마키 #fcfcfc 로 흰 배경 제거

★ 한글 파일명 함정: 캡컷 폰트 캐시의 `KCC간판체.ttf` 는 디스크에 **NFD**로
  저장돼 있어 파이썬 문자열 리터럴(NFC)로는 열리지 않는다. 게다가 PIL·libass
  둘 다 비ASCII 경로에서 실패한다. 그래서 폰트를 ASCII 경로로 복사해 쓴다.

사용법
  python tools/render_final.py 산출물/EP01_진시황릉            # 계획만
  python tools/render_final.py 산출물/EP01_진시황릉 --run      # 실제 렌더
  python tools/render_final.py 산출물/EP01_진시황릉 --run --자막없이
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from _config import load
from visual_timeline import load_visual_timeline

CFG = load()
ROOT = Path(__file__).resolve().parent.parent
SCRATCH = Path(tempfile.gettempdir()) / "claude" / "godeumul_render"
FONTDIR = Path(tempfile.gettempdir()) / "claude" / "fonts"

# 캡컷 size → 픽셀. 투탕카멘 완성본 실측으로 캘리브레이션한 값.
PX_PER_SIZE = 6.167


def sh(cmd: list[str], quiet: bool = True) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0 and not quiet:
        print(out[-2000:])
    if r.returncode != 0:
        raise RuntimeError(f"명령 실패 ({r.returncode}): {' '.join(cmd[:3])}…\n{out[-1200:]}")
    return out


def probe(p: Path) -> float:
    out = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration",
              "-of", "csv=p=0", str(p)]).strip()
    return float(out)


def ensure_font() -> tuple[Path, str]:
    """캡컷 폰트를 ASCII 경로로 복사하고 (폴더, 패밀리명) 을 돌려준다."""
    FONTDIR.mkdir(parents=True, exist_ok=True)
    dst = FONTDIR / "kcc_ganpan.ttf"
    if not dst.exists():
        raw = CFG.get("자막.폰트파일", "")
        src = Path(raw)
        if not src.exists() and src.parent.exists():
            # NFD/NFC 불일치 — 폴더에서 실제 파일을 찾는다
            cand = [p for p in src.parent.iterdir() if p.suffix.lower() in (".ttf", ".otf")]
            src = cand[0] if cand else src
        if not src.exists():
            sys.exit(f"[에러] 자막 폰트를 못 찾았습니다: {raw}")
        shutil.copyfile(src, dst)
    return FONTDIR, CFG.get("자막.폰트_ascii", "KCC-Ganpan")


def ass_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def ts(sec: float) -> str:
    h, r = divmod(max(0.0, sec), 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def build_ass(cues: list[dict], out: Path, family: str) -> None:
    W, H = CFG.get("출력.해상도", [1080, 1920])
    size = round(CFG.get("자막.크기", 12) * PX_PER_SIZE)
    outline = round(size * CFG.get("자막.획", 0.08))
    y = CFG.get("자막.위치", {}).get("y", -0.206)
    cy = round(H / 2 - y * (H / 2))          # 캡컷은 음수가 아래쪽

    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: sub,{family},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,{outline},0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [f"Dialogue: 0,{ts(c['start'])},{ts(c['end'])},sub,,0,0,0,,"
             f"{{\\pos({W//2},{cy})}}{ass_escape(c['text'])}" for c in cues]
    out.write_text(head + "\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="캡컷 없이 완성본 렌더")
    ap.add_argument("episode", type=Path)
    ap.add_argument("--run", action="store_true", help="실제로 렌더한다")
    ap.add_argument("--자막없이", dest="nosub", action="store_true")
    ap.add_argument("--워터마크없이", dest="nowm", action="store_true")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("[에러] ffmpeg 이 PATH 에 없습니다.")

    ep = args.episode.resolve()
    W, H = CFG.get("출력.해상도", [1080, 1920])
    FPS = CFG.get("출력.fps", 30)
    out = args.out or (ep / f"완성본_{ep.name}.mp4")

    man = json.loads((ep / "audio" / "durations.json").read_text(encoding="utf-8"))["scenes"]
    audio_keys = sorted(man, key=int)
    try:
        visual_plan = load_visual_timeline(ep, man)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        sys.exit(f"[에러] 영상-음성 장면 매핑 실패: {exc}")
    clips = {int(p.stem): p for p in (ep / "clips").glob("*.mp4")}
    audios = {int(p.stem): p for p in (ep / "audio").glob("*.mp3")}

    missing_clips = [row["visual_scene"] for row in visual_plan
                     if row["visual_scene"] not in clips]
    missing_audio = [int(k) for k in audio_keys if int(k) not in audios]
    if missing_clips or missing_audio:
        sys.exit(f"[에러] 소재 누락 — 영상 {missing_clips}, 오디오 {missing_audio}")

    # ── 계획 ────────────────────────────────────────────
    plan, total = [], 0.0
    lo, hi = CFG.get("영상.배속_안전", [0.75, 3.0])
    for visual in visual_plan:
        n = visual["visual_scene"]
        tts = visual["duration"]
        src = probe(clips[n])
        speed = src / tts
        plan.append({"n": n, "tts": tts, "src": src, "speed": speed,
                     "clip": clips[n], "audio_scene": visual["audio_scene"],
                     "start": visual["timeline_start"]})
        total = visual["timeline_end"]

    bad = [p for p in plan if not (lo <= p["speed"] <= hi)]

    print(f"\n에피소드 : {ep.name}")
    print(f"출력     : {W}x{H} · {FPS}fps · {total:.2f}초 ({int(total//60)}:{total%60:05.2f})")
    print(f"컷       : {len(plan)}개 · 배속 {min(p['speed'] for p in plan):.2f}"
          f"~{max(p['speed'] for p in plan):.2f}x")
    if bad:
        print(f"  ★ 배속 안전범위({lo}~{hi}) 밖: " +
              ", ".join(f"컷{p['n']} {p['speed']:.2f}x" for p in bad[:5]))

    size = round(CFG.get("자막.크기", 12) * PX_PER_SIZE)
    cues = []
    sync_p = ep / "자막_싱크.json"
    if not args.nosub:
        if not sync_p.exists():
            sys.exit("[에러] 자막_싱크.json 이 없습니다. align_subtitles 를 먼저.")
        cues = json.loads(sync_p.read_text(encoding="utf-8"))["cues"]
        print(f"자막     : {len(cues)}개 · {CFG.get('자막.폰트')} {size}px · "
              f"획 {round(size*CFG.get('자막.획',0.08))}px")

    wm = ROOT / "자산워터마크.png"
    if not args.nowm and wm.exists():
        s = CFG.get("워터마크", {})
        wpx = round(W * s.get("스케일", 0.2304))
        print(f"워터마크 : {wpx}px · 크로마키 {s.get('크로마키', '#fcfcfc')}")

    ln = ep / "audio" / "loudness.json"
    if ln.exists():
        a = json.loads(ln.read_text(encoding="utf-8"))["after"]
        print(f"오디오   : {a['lufs']:.1f} LUFS · 트루피크 {a['true_peak']:+.1f} dBFS")
    else:
        print("오디오   : ★ audio_normalize 를 안 돌렸습니다. 클리핑 위험")

    print(f"출력 파일: {out}")
    if not args.run:
        print("\n  (계획만 세웠습니다. 실제로 렌더하려면 --run)\n")
        return 0

    # ── 1단계: 컷마다 규격·길이 맞추기 ──────────────────
    work = SCRATCH / ep.name
    if work.exists():
        shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)

    print(f"\n  [1/3] 컷 {len(plan)}개 정규화")
    for p in plan:
        seg = work / f"v{p['n']:03d}.mp4"
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
              f"crop={W}:{H},setpts=PTS/{p['speed']:.6f},fps={FPS}")
        sh(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(p["clip"]),
            "-vf", vf, "-an", "-t", f"{p['tts']:.6f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
            "-pix_fmt", "yuv420p", "-y", str(seg)])
        if p["n"] % 5 == 0 or p["n"] == plan[-1]["n"]:
            print(f"        {p['n']:>2}/{len(plan)}")

    (work / "v.txt").write_text(
        "".join(f"file 'v{p['n']:03d}.mp4'\n" for p in plan), encoding="utf-8")
    (work / "a.txt").write_text(
        "".join(f"file '{audios[int(k)].as_posix()}'\n" for k in audio_keys),
        encoding="utf-8")

    # ── 2단계: 나레이션 이어붙이기 ──────────────────────
    print("  [2/3] 나레이션 결합")
    nar = work / "narration.m4a"
    sh(["ffmpeg", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(work / "a.txt"),
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-y", str(nar)])

    # ── 3단계: 합성 ─────────────────────────────────────
    print("  [3/3] 워터마크·자막 합성")
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error",
           "-f", "concat", "-safe", "0", "-i", str(work / "v.txt"),
           "-i", str(nar)]
    filt, cur, nin = [], "[0:v]", 2

    if not args.nowm and wm.exists():
        s = CFG.get("워터마크", {})
        wpx = round(W * s.get("스케일", 0.2304))
        key = s.get("크로마키", "#fcfcfc").lstrip("#")
        cx = round(W / 2 + s.get("위치", {}).get("x", 0.6772) * (W / 2))
        cy = round(H / 2 - s.get("위치", {}).get("y", -0.8164) * (H / 2))
        cmd += ["-i", str(wm)]
        filt.append(f"[{nin}:v]scale={wpx}:{wpx},"
                    f"colorkey=0x{key}:0.30:0.10,format=rgba[wm]")
        filt.append(f"{cur}[wm]overlay={cx - wpx//2}:{cy - wpx//2}[vw]")
        cur, nin = "[vw]", nin + 1

    if cues:
        fdir, family = ensure_font()
        ass = work / "sub.ass"
        build_ass(cues, ass, family)
        # ffmpeg 필터 인자에서 콜론·역슬래시를 escape 해야 한다
        a_esc = str(ass).replace("\\", "/").replace(":", "\\:")
        f_esc = str(fdir).replace("\\", "/").replace(":", "\\:")
        filt.append(f"{cur}subtitles='{a_esc}':fontsdir='{f_esc}'[vs]")
        cur = "[vs]"

    if filt:
        cmd += ["-filter_complex", ";".join(filt), "-map", cur]
    else:
        cmd += ["-map", "0:v"]
    cmd += ["-map", "1:a",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-profile:v", "high", "-level", "4.2", "-pix_fmt", "yuv420p",
            "-r", str(FPS), "-g", str(FPS * 2),
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
            "-movflags", "+faststart", "-shortest", "-y", str(out)]
    sh(cmd, quiet=False)

    # ── 검증 ────────────────────────────────────────────
    info = sh(["ffprobe", "-v", "error", "-show_entries",
               "stream=codec_type,width,height,r_frame_rate,codec_name",
               "-show_entries", "format=duration,size", "-of", "json", str(out)])
    j = json.loads(info)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    dur = float(j["format"]["duration"])
    mb = int(j["format"]["size"]) / 1048576

    print(f"\n  완성본 : {out}")
    print(f"  규격   : {v['width']}x{v['height']} · {v['r_frame_rate']} · "
          f"{v['codec_name']}/{a['codec_name'] if a else '무음'}")
    print(f"  길이   : {dur:.2f}초 ({int(dur//60)}:{dur%60:05.2f}) · {mb:.1f}MB")

    ok = True
    if (v["width"], v["height"]) != (W, H):
        print(f"  ★ 해상도 불일치 (기대 {W}x{H})"); ok = False
    if abs(dur - total) > 0.5:
        print(f"  ★ 길이 불일치 (기대 {total:.2f}초)"); ok = False
    if dur >= 180:
        print("  ★ 3분 이상 — 쇼츠로 안 잡힌다"); ok = False
    if not a:
        print("  ★ 오디오 트랙 없음"); ok = False
    print("\n  " + ("규격 이상 없음.\n" if ok else "★ 위 문제를 확인하세요.\n"))

    shutil.rmtree(work, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
