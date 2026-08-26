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
    use_v5_layout = (episode / "clips_v5").is_dir() and (episode / "audio_v5").is_dir()
    clips_dir = episode / ("clips_v5" if use_v5_layout else "clips")
    audio_dir = episode / ("audio_v5" if use_v5_layout else "audio")
    duration_file = audio_dir / "durations.json"
    caption_file = episode / ("자막_싱크_v5.json" if use_v5_layout else "자막_싱크.json")
    audio_name = f"{episode.name}_TTS검수본_v5.mp3" if use_v5_layout else "narration_remotion.m4a"
    audio_file = audio_dir / audio_name
    default_name = f"{episode.name}_최종_v5.mp4" if use_v5_layout else f"완성본_{episode.name}_remotion.mp4"
    output = (args.out or (episode / default_name)).resolve()

    required = [duration_file, caption_file, ROOT / "자산워터마크.png", FONT]
    if use_v5_layout:
        required.append(audio_file)
    missing = [str(path) for path in required if not path.exists()]
    clips = sorted(clips_dir.glob("*.mp4"))
    duration_doc = json.loads(duration_file.read_text(encoding="utf-8")) if duration_file.exists() else {}
    scene_doc = duration_doc.get("scenes") or {}
    scene_ids = sorted((int(key) for key in scene_doc), key=int)
    expected_count = len(scene_ids)
    if len(clips) != expected_count:
        missing.append(f"{clips_dir.name} MP4 count: {len(clips)} (expected {expected_count})")
    expected_names = {f"{scene:03d}.mp4" for scene in scene_ids}
    if {path.name for path in clips} != expected_names:
        missing.append(f"{clips_dir.name} numbered clip set does not match durations.json")
    scene_audio_files = [audio_dir / f"{scene:03d}.mp3" for scene in scene_ids]
    if not use_v5_layout:
        missing.extend(str(path) for path in scene_audio_files if not path.exists())
    if missing:
        sys.exit("[ERROR] Missing Remotion inputs:\n" + "\n".join(missing))

    durations = duration_doc
    scene_durations = [float(scene_doc[str(i)]["duration"]) for i in scene_ids]
    clip_durations = [float(probe(path)["format"]["duration"]) for path in clips]
    captions = json.loads(caption_file.read_text(encoding="utf-8"))["cues"]
    total = sum(scene_durations)
    impact_file = episode / "remotion_impacts.json"
    impact_cues = json.loads(impact_file.read_text(encoding="utf-8")).get("cues", []) if impact_file.exists() else []

    manifest_total = float(durations.get("total_duration", total))
    if abs(total - manifest_total) > 0.05:
        sys.exit("[ERROR] Scene duration total does not match durations.json")
    if any(cue["scene"] not in scene_ids for cue in captions):
        sys.exit("[ERROR] Caption scene index is out of range")
    if captions[-1]["end"] > total + 0.05:
        sys.exit("[ERROR] Last caption exceeds the narration duration")

    qa_dir = episode / "qa_v5"
    qa_dir.mkdir(exist_ok=True)
    props_file = qa_dir / "remotion_props.json"
    props = {
        "sceneDurations": scene_durations,
        "clipDurations": clip_durations,
        "captions": captions,
        "audioFile": f"{audio_dir.name}/{audio_name}",
        "fontFile": "NotoSansKR-VF.ttf",
        "watermarkFile": "watermark.png",
        "clipDirectory": clips_dir.name,
        "impactCues": impact_cues,
    }
    props_file.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")

    frames = math.ceil(total * 30)
    print(f"Episode : {episode.name}")
    print(f"Scenes  : {len(clips)}")
    print(f"Captions: {len(captions)}")
    print(f"Impacts : {len(impact_cues)}")
    print(f"Duration: {total:.3f}s / {frames} frames")
    print(f"Output  : {output}")
    if not args.run:
        print("Plan only. Add --run to render.")
        return 0

    shutil.copyfile(FONT, episode / "NotoSansKR-VF.ttf")
    shutil.copyfile(ROOT / "자산워터마크.png", episode / "watermark.png")
    if not use_v5_layout:
        concat_file = qa_dir / "audio_concat.txt"
        concat_file.write_text(
            "".join(f"file '{path.as_posix()}'\n" for path in scene_audio_files),
            encoding="utf-8",
        )
        run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", str(audio_file),
        ])

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
