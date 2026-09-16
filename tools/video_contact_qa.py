#!/usr/bin/env python
"""Create start/middle/end contact sheets and mechanical freeze checks for scene clips."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def probe(ffprobe: str, clip: Path) -> dict[str, object]:
    raw = subprocess.check_output([
        ffprobe, "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,width,height,r_frame_rate:format=duration",
        "-of", "json", str(clip),
    ], text=True, encoding="utf-8")
    return json.loads(raw)


def extract(ffmpeg: str, clip: Path, at: float, dest: Path) -> None:
    subprocess.run([
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{at:.3f}",
        "-i", str(clip), "-frames:v", "1", "-vf", "scale=240:426", "-q:v", "2", str(dest),
    ], check=True)


def freeze_events(ffmpeg: str, clip: Path) -> list[str]:
    result = subprocess.run([
        ffmpeg, "-hide_banner", "-nostats", "-i", str(clip),
        "-vf", "freezedetect=n=-50dB:d=0.75", "-an", "-f", "null", "-",
    ], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return [line for line in result.stderr.splitlines() if "freeze_" in line]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("episode", type=Path)
    args = parser.parse_args()
    episode = args.episode.resolve()
    clips = sorted((episode / "clips").glob("[0-9][0-9][0-9].mp4"))
    if not clips:
        raise SystemExit("No numbered MP4 clips found")
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise SystemExit("ffmpeg/ffprobe not found")
    out = episode / "videos_qa" / "shared_frame_chain_20260916"
    out.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for clip in clips:
        info = probe(ffprobe, clip)
        duration = float(info["format"]["duration"])
        times = [min(0.15, duration * .05), duration / 2, max(.01, duration - .15)]
        frames: list[str] = []
        for label, at in zip(("start", "middle", "end"), times):
            dest = out / f"{clip.stem}_{label}.jpg"
            extract(ffmpeg, clip, at, dest)
            frames.append(str(dest.relative_to(episode)).replace("\\", "/"))
        rows.append({
            "scene": int(clip.stem), "clip": str(clip.relative_to(episode)).replace("\\", "/"),
            "duration": round(duration, 3), "frames": frames,
            "freeze_events": freeze_events(ffmpeg, clip),
        })

    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 18)
    sheets: list[str] = []
    for offset in range(0, len(rows), 4):
        group = rows[offset:offset + 4]
        sheet = Image.new("RGB", (720, 1360 * len(group) // 4 + 28 * len(group)), "#151515")
        # Four scenes per sheet, three columns; each scene occupies one 454 px row.
        sheet = Image.new("RGB", (720, 454 * len(group)), "#151515")
        draw = ImageDraw.Draw(sheet)
        for ri, row in enumerate(group):
            for ci, frame in enumerate(row["frames"]):
                with Image.open(episode / frame) as image:
                    sheet.paste(image.convert("RGB"), (ci * 240, ri * 454 + 28))
                draw.text((ci * 240 + 6, ri * 454 + 5),
                          f"{int(row['scene']):03d} {('START','MID','END')[ci]}", fill="white", font=font)
        target = out / f"contact_{int(group[0]['scene']):03d}_{int(group[-1]['scene']):03d}.jpg"
        sheet.save(target, quality=92)
        sheets.append(str(target.relative_to(episode)).replace("\\", "/"))

    report = {
        "version": 1,
        "policy": "Start/middle/end visual review plus freezedetect candidates; human review remains required.",
        "clips": rows,
        "contact_sheets": sheets,
        "freeze_candidate_scenes": [row["scene"] for row in rows if row["freeze_events"]],
        "visual_review": "PENDING",
    }
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"clips": len(rows), "sheets": sheets,
                      "freeze_candidate_scenes": report["freeze_candidate_scenes"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
