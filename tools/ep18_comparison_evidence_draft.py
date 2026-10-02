#!/usr/bin/env python
"""Build a non-destructive CapCut preview replacing EP18 scene 007 fabrications.

The two National Museum of Korea photos are unmodified source evidence. The
underlying Flow shot remains a moving scene, but its invented comparison
objects and generated prose must be fully hidden by the evidence inserts in a
final visual check. This script creates a staging copy only; it never publishes.
"""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import uuid
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
EPISODE = ROOT / "산출물/EP18_농경문청동기"
SOURCE = EPISODE / "capcut_staging/EP18 농경문 청동기_20260930"
OUTPUT = EPISODE / "capcut_staging/EP18 농경문 청동기_실물증거교정_007_v3"
ZOOM_SOURCE = Path.home() / (
    "AppData/Local/CapCut/User Data/Projects/com.lveditor.draft/"
    "EP07 사해문서/Timelines/73D3B247-BB64-429A-928E-9E362A97A79B/draft_content.json"
)
US = 1_000_000


def uid() -> str:
    return str(uuid.uuid4()).upper()


def normalized_photo_scale(width, height, canvas_width, canvas_height,
                           max_width, max_height):
    """CapCut scale=1 already fits the source inside the project canvas."""
    if min(width, height, canvas_width, canvas_height, max_width, max_height) <= 0:
        raise ValueError("Image/canvas dimensions must be positive")
    fit = min(canvas_width / width, canvas_height / height)
    target = min(max_width / width, max_height / height)
    scale = target / fit
    return scale, width * fit * scale, height * fit * scale


def photo_insert(document: dict, *, photo: Path, start_us: int, duration_us: int,
                 photo_material: dict, photo_segment: dict, zoom_template: dict,
                 max_width: int = 980, max_height: int = 1240,
                 y: float = 0.10, render_index: int = 1) -> dict:
    width, height = Image.open(photo).size
    material = copy.deepcopy(photo_material)
    material.update({
        "id": uid(), "unique_id": uid().replace("-", "").lower(),
        "local_material_id": uid(), "path": photo.as_posix(),
        "material_name": photo.name, "width": width, "height": height,
    })
    document["materials"]["videos"].append(material)

    zoom = copy.deepcopy(zoom_template)
    zoom["id"] = uid()
    zoom["animations"][0]["start"] = 0
    zoom["animations"][0]["duration"] = duration_us
    document["materials"]["material_animations"].append(zoom)

    segment = copy.deepcopy(photo_segment)
    segment.update({
        "id": uid(), "material_id": material["id"],
        "source_timerange": None,
        "target_timerange": {"start": start_us, "duration": duration_us},
        "render_timerange": {"start": 0, "duration": 0},
        "extra_material_refs": [zoom["id"]],
        "keyframe_refs": [], "speed": 1.0, "volume": 0.0,
        "track_render_index": render_index,
    })
    # Keep each historical object large enough to read but leave the Flow
    # museum camera visible around the photo. CapCut Zoom 1 is the sole animation.
    canvas = document["canvas_config"]
    scale, rendered_w, rendered_h = normalized_photo_scale(
        width, height, canvas["width"], canvas["height"], max_width, max_height)
    assert rendered_w <= max_width + 1e-6 and rendered_h <= max_height + 1e-6
    segment["clip"] = {
        "scale": {"x": scale, "y": scale}, "rotation": 0.0,
        "transform": {"x": 0.0, "y": y},
        "flip": {"vertical": False, "horizontal": False}, "alpha": 1.0,
    }
    return segment


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Validate inputs without writing")
    args = parser.parse_args()
    if not args.check:
        from diagnostic_draft_guard import block_retired_draft_builder
        block_retired_draft_builder()
    source_json = SOURCE / "draft_content.json"
    zoom_json = ZOOM_SOURCE
    photo_a = EPISODE / "reference/NMK_Goejeongdong_shield_1846.jpg"
    photo_b = EPISODE / "reference/NMK_Namsungri_shield_3490.jpg"
    for path in (source_json, zoom_json, photo_a, photo_b):
        if not path.is_file():
            raise RuntimeError(f"Missing required source: {path}")
    document = json.loads(source_json.read_text(encoding="utf-8"))
    source_zoom = json.loads(zoom_json.read_text(encoding="utf-8"))
    zoom_template = next(
        material for material in source_zoom["materials"]["material_animations"]
        if (material.get("animations") or [{}])[0].get("name") == "줌 1"
    )
    main_track = next(t for t in document["tracks"] if t["type"] == "video" and t.get("flag") == 0)
    watermark_track = next(t for t in document["tracks"] if t["type"] == "video" and t.get("flag") == 2)
    if len(main_track["segments"]) != 21:
        raise RuntimeError("Expected 21 EP18 video scenes")
    scene_007 = main_track["segments"][6]["target_timerange"]
    if abs(scene_007["start"] / US - 47.23) > 0.5:
        raise RuntimeError(f"Scene 007 does not align to ElevenLabs timing: {scene_007}")
    # The TTS names 괴정동 first and 남성리 second. Both original photos stay
    # visible for the remainder of the comparison sentence, not invented props.
    cues = json.loads((EPISODE / "자막_싱크.json").read_text(encoding="utf-8"))["cues"]
    namsungri_cue = next(c for c in cues if c["scene"] == 7 and "아산 남성리" in c["text"])
    cue_split_us = round(namsungri_cue["start"] * US)
    if cue_split_us != 49_098_000:
        raise RuntimeError("Approved Namsungri cue changed; review timing before build")
    compare_us = int(52.51 * US)
    scene_start = scene_007["start"]
    scene_end = scene_start + scene_007["duration"]
    if not (scene_start < cue_split_us < compare_us < scene_end):
        raise RuntimeError("The two museum photo windows do not fit scene 007")
    if args.check:
        print(json.dumps({
            "scene_start_us": scene_start, "scene_end_us": scene_end,
            "goejeongdong_full": [scene_start, cue_split_us],
            "namsungri_full": [cue_split_us, compare_us],
            "two_official_objects": [compare_us, scene_end],
            "output": str(OUTPUT),
            "normalized_photo_scales": {
                p.name: {
                    "single": normalized_photo_scale(*Image.open(p).size, 1080, 1920, 980, 1240),
                    "comparison": normalized_photo_scale(*Image.open(p).size, 1080, 1920, 760, 700),
                } for p in (photo_a, photo_b)
            },
        }, ensure_ascii=False, indent=2))
        return 0
    if OUTPUT.exists():
        raise RuntimeError(f"Preserving existing staging draft: {OUTPUT}")

    photo_material = next(m for m in document["materials"]["videos"] if m.get("type") == "photo")
    photo_segment = watermark_track["segments"][0]
    overlay_a = copy.deepcopy(watermark_track)
    overlay_a["id"] = uid()
    overlay_a["flag"] = 1
    overlay_a["segments"] = [
        photo_insert(document, photo=photo_a, start_us=scene_start,
                     duration_us=cue_split_us - scene_start,
                     photo_material=photo_material, photo_segment=photo_segment,
                     zoom_template=zoom_template),
        photo_insert(document, photo=photo_a, start_us=compare_us,
                     duration_us=scene_end - compare_us,
                     photo_material=photo_material, photo_segment=photo_segment,
                     zoom_template=zoom_template,
                     max_width=760, max_height=700, y=0.37),
    ]
    overlay_b = copy.deepcopy(watermark_track)
    overlay_b["id"] = uid()
    overlay_b["flag"] = 3
    overlay_b["segments"] = [
        photo_insert(document, photo=photo_b, start_us=cue_split_us,
                     duration_us=compare_us - cue_split_us,
                     photo_material=photo_material, photo_segment=photo_segment,
                     zoom_template=zoom_template, render_index=3),
        photo_insert(document, photo=photo_b, start_us=compare_us,
                     duration_us=scene_end - compare_us,
                     photo_material=photo_material, photo_segment=photo_segment,
                     zoom_template=zoom_template,
                     max_width=760, max_height=700, y=-0.31, render_index=3),
    ]
    insert_at = document["tracks"].index(watermark_track)
    document["tracks"][insert_at:insert_at] = [overlay_a, overlay_b]

    OUTPUT.mkdir(parents=True)
    for name in ("draft_cover.jpg", "draft_meta_info.json"):
        source_file = SOURCE / name
        if source_file.is_file():
            shutil.copy2(source_file, OUTPUT / name)
    (OUTPUT / "draft_content.json").write_text(
        json.dumps(document, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    print(OUTPUT / "draft_content.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
