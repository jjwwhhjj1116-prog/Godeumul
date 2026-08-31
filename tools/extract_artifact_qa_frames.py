#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""식별 유물 클립의 10%·50%·90% 프레임을 추출하고 수동 형태 QA 표를 만든다."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

import _config  # noqa: F401


RATIOS = (0.1, 0.5, 0.9)


def probe_duration(ffprobe: str, clip: Path) -> float:
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(clip)],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return float(result.stdout.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="식별 유물 시작·중간·끝 형태 QA 프레임 추출")
    parser.add_argument("episode", type=Path)
    parser.add_argument("--mark-fail", action="store_true",
                        help="이미 실물 대조 불합격이 확인된 현재 클립을 FAIL로 기록")
    parser.add_argument("--reason", default="", help="--mark-fail 근거")
    args = parser.parse_args()
    episode = args.episode.resolve()
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise SystemExit("ffmpeg/ffprobe가 PATH에 없습니다")

    scenes = json.loads((episode / "02a.장면구분.json").read_text(encoding="utf-8"))
    targets = [scene for scene in scenes if scene.get("artifact_visibility") == "IDENTIFIABLE"]
    output_dir = episode / "QA_유물형태키프레임"
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []

    for scene in targets:
        n = int(scene["n"])
        clip = episode / "clips" / f"{n:03d}.mp4"
        if not clip.exists():
            rows.append({"scene": n, "status": "MISSING_CLIP", "frames": []})
            continue
        duration = probe_duration(ffprobe, clip)
        frames: list[str] = []
        for ratio in RATIOS:
            stamp = min(max(duration * ratio, 0.01), max(duration - 0.04, 0.01))
            tag = int(ratio * 100)
            frame = output_dir / f"scene_{n:03d}_t{tag:02d}.jpg"
            subprocess.run(
                [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{stamp:.3f}", "-i", str(clip), "-frames:v", "1", str(frame)],
                check=True,
            )
            frames.append(str(frame.relative_to(episode)).replace("\\", "/"))
        check_status = "FAIL" if args.mark_fail else "PENDING"
        scene_status = "ARTIFACT_FORM_FAIL" if args.mark_fail else "PENDING_HUMAN_COMPARISON"
        rows.append({
            "scene": n,
            "reference_ids": scene.get("artifact_reference_ids", []),
            "frames": frames,
            "checks": {
                "silhouette_and_proportion": check_status,
                "support_and_part_count": check_status,
                "lid_and_summit_ornament": check_status,
                "surface_and_damage": check_status
            },
            "status": scene_status
        })

    report = {
        "version": 1,
        "reference_manifest": "02c.유물레퍼런스.json",
        "policy": "10%·50%·90% 세 프레임과 형태 소유자를 확대 대조; 한 프레임이라도 다르면 FAIL",
        "overall_status": "ARTIFACT_FORM_FAIL" if args.mark_fail else "PENDING_HUMAN_COMPARISON",
        "manual_review_reason": args.reason if args.mark_fail else "",
        "scenes": rows,
    }
    (episode / "04.유물형태키프레임검수.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"식별 유물 {len(targets)}개 장면 × 3프레임 추출")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
