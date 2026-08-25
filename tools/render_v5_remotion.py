#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Render the locked V5 episode with Remotion.

Only editorial layers are added here: exact V5 narration, forced-alignment
captions, a restrained grade and the channel watermark. Scene-integrated 3D
graphics remain owned by the Flow/Veo clips.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MOTION = ROOT / "motion-graphics"
FONT = Path("C:/Windows/Fonts/NotoSansKR-VF.ttf")


def run(cmd: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (result.stdout or "") + (result.stderr or "")
    if result.returncode:
        raise RuntimeError(output[-5000:])
    return output


def probe(path: Path) -> dict:
    raw = run([
        "ffprobe", "-v", "error", "-show_entries",
        "stream=codec_type,codec_name,width,height,r_frame_rate",
        "-show_entries", "format=duration,size", "-of", "json", str(path),
    ])
    return json.loads(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render locked V5 with Remotion")
    parser.add_argument("episode", type=Path)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    episode = args.episode.resolve()
    clips_dir = episode / "clips_v5"
    audio_dir = episode / "audio_v5"
    duration_file = audio_dir / "durations.json"
    caption_file = episode / "자막_싱크_v5.json"
    audio_name = f"{episode.name}_TTS검수본_v5.mp3"
    audio_file = audio_dir / audio_name
    output = (args.out or (episode / f"{episode.name}_최종_v5.mp4")).resolve()

    required = [duration_file, caption_file, audio_file, ROOT / "자산워터마크.png", FONT]
    missing = [str(path) for path in required if not path.exists()]
    clips = sorted(clips_dir.glob("*.mp4"))
    if len(clips) != 27:
        missing.append(f"clips_v5 MP4 count: {len(clips)} (expected 27)")
    if missing:
        sys.exit("[ERROR] Missing V5 inputs:\n" + "\n".join(missing))

    durations = json.loads(duration_file.read_text(encoding="utf-8"))
    scene_durations = [float(durations["scenes"][str(i)]["duration"]) for i in range(1, 28)]
    clip_durations = [float(probe(path)["format"]["duration"]) for path in clips]
    captions = json.loads(caption_file.read_text(encoding="utf-8"))["cues"]
    total = sum(scene_durations)

    if abs(total - float(durations["total_duration"])) > 0.05:
        sys.exit("[ERROR] Scene duration total does not match durations.json")
    if any(cue["scene"] < 1 or cue["scene"] > 27 for cue in captions):
        sys.exit("[ERROR] Caption scene index is out of range")
    if captions[-1]["end"] > total + 0.05:
        sys.exit("[ERROR] Last caption exceeds the narration duration")

    shutil.copyfile(FONT, episode / "NotoSansKR-VF.ttf")
    shutil.copyfile(ROOT / "자산워터마크.png", episode / "watermark.png")

    qa_dir = episode / "qa_v5"
    qa_dir.mkdir(exist_ok=True)
    props_file = qa_dir / "remotion_props.json"
    props = {
        "sceneDurations": scene_durations,
        "clipDurations": clip_durations,
        "captions": captions,
        "audioFile": f"audio_v5/{audio_name}",
        "fontFile": "NotoSansKR-VF.ttf",
        "watermarkFile": "watermark.png",
    }
    props_file.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")

    frames = math.ceil(total * 30)
    print(f"Episode : {episode.name}")
    print(f"Scenes  : {len(clips)}")
    print(f"Captions: {len(captions)}")
    print(f"Duration: {total:.3f}s / {frames} frames")
    print(f"Output  : {output}")
    if not args.run:
        print("Plan only. Add --run to render.")
        return 0

    npx = shutil.which("npx")
    if not npx:
        sys.exit("[ERROR] npx is not available")
    cmd = [
        npx, "remotion", "render", "src/index.ts", "V5Final", str(output),
        "--codec", "h264", "--audio-codec", "aac", "--crf", "16",
        "--pixel-format", "yuv420p", "--public-dir", str(episode),
        "--props", str(props_file), "--concurrency", "50%", "--overwrite",
    ]
    print(run(cmd, cwd=MOTION))

    info = probe(output)
    video = next(stream for stream in info["streams"] if stream["codec_type"] == "video")
    audio = next((stream for stream in info["streams"] if stream["codec_type"] == "audio"), None)
    actual = float(info["format"]["duration"])
    ok = (
        video.get("width") == 1080
        and video.get("height") == 1920
        and video.get("r_frame_rate") == "30/1"
        and audio is not None
        and actual < 180
        and abs(actual - total) < 0.2
    )
    print(f"Rendered: {video.get('width')}x{video.get('height')} {video.get('r_frame_rate')} {actual:.3f}s")
    if not ok:
        sys.exit("[ERROR] Rendered file failed the delivery specification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

