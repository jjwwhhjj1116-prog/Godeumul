#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""02d.유물장면라우팅.json을 장면표에 적용해 형태 잠금 프롬프트를 만든다."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import _config  # noqa: F401


IMAGE_FORM_LOCK = (
    "Use the supplied artifact reference asset as the exact form owner. Preserve its "
    "pixel geometry, silhouette, proportions, part count, ornament layout, patina and "
    "damage; edit only the environment and lighting. Do not redraw, restore, beautify "
    "or redesign the artifact. "
)
VIDEO_FORM_LOCK = (
    " Preserve the exact supplied reference artifact pixel geometry and silhouette. "
    "The artifact remains completely rigid and unchanged for the entire shot. Move only "
    "the physical camera, focus, light and environmental smoke. No redesign, no "
    "beautification, no restoration, no added ornament, no changed part count."
)
T2V_ARTIFACT_BAN = " Do not show the named hero artifact in identifiable form."


def apply_routing(episode: Path) -> int:
    routing_path = episode / "02d.유물장면라우팅.json"
    scene_path = episode / "02a.장면구분.json"
    routing = json.loads(routing_path.read_text(encoding="utf-8"))
    scenes = json.loads(scene_path.read_text(encoding="utf-8"))
    route_by_scene = {int(key): value for key, value in routing["scenes"].items()}
    if set(route_by_scene) != {int(scene["n"]) for scene in scenes}:
        raise ValueError("라우팅 파일과 장면표의 장면 번호가 정확히 일치해야 합니다")

    for scene in scenes:
        n = int(scene["n"])
        route = route_by_scene[n]
        mode = str(route["generation_mode"]).upper()
        visibility = str(route["artifact_visibility"]).upper()
        reason = str(route.get("routing_reason") or "").strip()
        if len(reason) < 12:
            raise ValueError(f"장면 {n:03d}: routing_reason을 구체적으로 기록해야 합니다")
        scene["generation_mode"] = mode
        scene["artifact_visibility"] = visibility
        scene["routing_reason"] = reason
        scene["artifact_reference_ids"] = route.get("artifact_reference_ids", [])

        if visibility == "IDENTIFIABLE":
            scene["artifact_form_policy"] = "SOURCE_PHOTO_GEOMETRY_LOCK"
            scene["allowed_artifact_changes"] = [
                "camera", "lighting", "focus", "environmental_smoke"
            ]
            scene["forbidden_artifact_changes"] = [
                "silhouette", "proportion", "part_count", "ornament_layout", "patina_pattern"
            ]
            image_key = "img_v2" if scene.get("img_v2") else "img"
            image = str(scene.get(image_key) or "")
            if not image.startswith(IMAGE_FORM_LOCK):
                scene[image_key] = IMAGE_FORM_LOCK + image
            video = str(scene.get("vid") or "")
            if VIDEO_FORM_LOCK.strip() not in video:
                scene["vid"] = video.rstrip() + VIDEO_FORM_LOCK
        else:
            for key in (
                "artifact_form_policy", "allowed_artifact_changes", "forbidden_artifact_changes"
            ):
                scene.pop(key, None)

        if mode == "T2V_CONTEXT":
            video = str(scene.get("vid") or "")
            if T2V_ARTIFACT_BAN.strip() not in video:
                scene["vid"] = video.rstrip() + T2V_ARTIFACT_BAN

    scene_path.write_text(
        json.dumps(scenes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return len(scenes)


def main() -> int:
    parser = argparse.ArgumentParser(description="유물 장면 라우팅·형태 잠금 적용")
    parser.add_argument("episode", type=Path)
    args = parser.parse_args()
    count = apply_routing(args.episode.resolve())
    print(f"유물 라우팅 적용: {count}개 장면")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
