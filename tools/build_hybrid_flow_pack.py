#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""장면표를 I2V·T2V Flow 입력 파일과 원본 장면 매핑으로 분리한다."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import _config  # noqa: F401


MODES = {"I2V_LOCKED", "T2V_CONTEXT"}


def _write_blocks(path: Path, blocks: list[str]) -> None:
    path.write_text("\n\n".join(blocks) + ("\n" if blocks else ""), encoding="utf-8")


def build_pack(episode: Path) -> dict[str, object]:
    scene_path = episode / "02a.장면구분.json"
    scenes = json.loads(scene_path.read_text(encoding="utf-8"))
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("02a.장면구분.json은 비어 있지 않은 배열이어야 합니다")

    i2v_images: list[str] = []
    i2v_videos: list[str] = []
    t2v_videos: list[str] = []
    mapping: list[dict[str, object]] = []

    for expected_n, scene in enumerate(scenes, 1):
        n = int(scene.get("n") or 0)
        if n != expected_n:
            raise ValueError(f"장면 번호 불연속: {n} / 기대 {expected_n}")
        mode = str(scene.get("generation_mode") or "").strip().upper()
        if mode not in MODES:
            raise ValueError(f"장면 {n:03d}: 알 수 없는 generation_mode {mode!r}")
        video = str(scene.get("vid") or "").strip()
        if not video:
            raise ValueError(f"장면 {n:03d}: 영상 프롬프트 없음")

        if mode == "I2V_LOCKED":
            image = str(scene.get("img_v2") or scene.get("img") or "").strip()
            if not image:
                raise ValueError(f"장면 {n:03d}: I2V 시작 이미지 프롬프트 없음")
            i2v_images.append(image)
            i2v_videos.append(video)
            mode_index = len(i2v_videos)
            target_file = "flow_i2v_videos.txt"
        else:
            t2v_videos.append(video)
            mode_index = len(t2v_videos)
            target_file = "flow_t2v_videos.txt"

        mapping.append({
            "scene": n,
            "generation_mode": mode,
            "artifact_visibility": scene.get("artifact_visibility"),
            "mode_index": mode_index,
            "prompt_file": target_file,
            "download_name": f"{n:03d}.mp4",
        })

    _write_blocks(episode / "flow_i2v_images.txt", i2v_images)
    _write_blocks(episode / "flow_i2v_videos.txt", i2v_videos)
    _write_blocks(episode / "flow_t2v_videos.txt", t2v_videos)

    plan = {
        "version": 1,
        "scene_count": len(scenes),
        "i2v_count": len(i2v_videos),
        "t2v_count": len(t2v_videos),
        "mapping": mapping,
    }
    (episode / "04.하이브리드생성계획.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Flow I2V·T2V 입력 파일 분리")
    parser.add_argument("episode", type=Path)
    args = parser.parse_args()
    plan = build_pack(args.episode.resolve())
    print(
        f"장면 {plan['scene_count']}개 → I2V {plan['i2v_count']}개 / "
        f"T2V {plan['t2v_count']}개"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
