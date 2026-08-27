#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""CapCut 원생 애니메이션·전환을 선택 장면에 재사용한다.

사용자가 직접 마감한 CapCut 기준 프로젝트에서 ``줌 1``, ``반동 1``,
``왼쪽으로 밀기``, ``페이크 줌`` 소재만 복제한다. 영상·오디오·자막의
타이밍과 볼륨은 건드리지 않는다. CapCut 본체를 완전히 닫은 상태에서만
``--write``가 허용된다.
"""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from capcut_audio_guard import COMPANION_NAMES, capcut_editor_open


ANIMATION_NAMES = {"zoom": "줌 1", "bounce": "반동 1"}
TRANSITION_NAMES = {"left": "왼쪽으로 밀기", "fake_zoom": "페이크 줌"}
LIVE_DRAFT_ROOT = (
    Path.home() / "AppData/Local/CapCut/User Data/Projects/com.lveditor.draft"
).resolve()


def is_live_draft(path: Path) -> bool:
    try:
        path.resolve().relative_to(LIVE_DRAFT_ROOT)
        return True
    except ValueError:
        return False


def parse_scene_list(value: str) -> list[int]:
    if not value.strip():
        return []
    out: list[int] = []
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        number = int(token)
        if number < 1:
            raise argparse.ArgumentTypeError("장면 번호는 1 이상이어야 합니다.")
        out.append(number)
    return out


def new_id() -> str:
    return str(uuid.uuid4()).upper()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main_video_segments(document: dict) -> list[dict]:
    for track in document.get("tracks", []):
        if track.get("type") == "video" and track.get("flag") == 0:
            return track.get("segments", [])
    raise RuntimeError("주 영상 트랙(flag=0)을 찾지 못했습니다.")


def animation_name(material: dict) -> str:
    animations = material.get("animations") or []
    return animations[0].get("name", "") if animations else ""


def source_material(document: dict, bucket: str, name: str) -> dict:
    materials = document.get("materials", {}).get(bucket, [])
    for material in materials:
        actual = animation_name(material) if bucket == "material_animations" else material.get("name", "")
        if actual == name:
            return material
    raise RuntimeError(f"기준 프로젝트에 CapCut 소재가 없습니다: {bucket}/{name}")


def material_name_index(document: dict) -> dict[str, str]:
    names: dict[str, str] = {}
    mats = document.get("materials", {})
    for material in mats.get("material_animations", []):
        names[material.get("id", "")] = animation_name(material)
    for material in mats.get("transitions", []):
        names[material.get("id", "")] = material.get("name", "")
    return names


def clone_animation(source: dict, *, segment_duration: int, bounce: bool) -> dict:
    material = copy.deepcopy(source)
    material["id"] = new_id()
    animation = material["animations"][0]
    if bounce:
        start = min(633_333, max(0, segment_duration // 8))
        animation["start"] = start
        animation["duration"] = max(1, segment_duration - start)
    else:
        animation["start"] = 0
        animation["duration"] = max(1, segment_duration)
    return material


def clone_transition(source: dict, *, segment_duration: int) -> dict:
    material = copy.deepcopy(source)
    material["id"] = new_id()
    material["duration"] = min(int(material.get("duration") or 0), max(1, segment_duration // 2))
    return material


def attach(document: dict, source: dict, *, zoom_scenes: list[int], bounce_scenes: list[int],
           left_joins: list[int], fake_zoom_joins: list[int]) -> dict:
    result = copy.deepcopy(document)
    segments = main_video_segments(result)
    buckets = result.setdefault("materials", {})
    animation_bucket = buckets.setdefault("material_animations", [])
    transition_bucket = buckets.setdefault("transitions", [])
    existing_names = material_name_index(result)

    def segment(scene: int) -> dict:
        if scene > len(segments):
            raise RuntimeError(f"장면 {scene}은 주 영상 {len(segments)}개 범위를 벗어납니다.")
        return segments[scene - 1]

    def has_name(seg: dict, name: str) -> bool:
        return any(existing_names.get(ref) == name for ref in seg.get("extra_material_refs", []))

    for scenes, key in ((zoom_scenes, "zoom"), (bounce_scenes, "bounce")):
        name = ANIMATION_NAMES[key]
        prototype = source_material(source, "material_animations", name)
        for scene_number in scenes:
            seg = segment(scene_number)
            if has_name(seg, name):
                continue
            duration = int(seg["target_timerange"]["duration"])
            material = clone_animation(prototype, segment_duration=duration, bounce=key == "bounce")
            animation_bucket.append(material)
            seg.setdefault("extra_material_refs", []).append(material["id"])
            existing_names[material["id"]] = name

    for joins, key in ((left_joins, "left"), (fake_zoom_joins, "fake_zoom")):
        name = TRANSITION_NAMES[key]
        prototype = source_material(source, "transitions", name)
        for scene_number in joins:
            if scene_number >= len(segments):
                raise RuntimeError(f"전환은 마지막 장면 뒤에 붙일 수 없습니다: {scene_number}")
            seg = segment(scene_number)
            if has_name(seg, name):
                continue
            duration = int(seg["target_timerange"]["duration"])
            material = clone_transition(prototype, segment_duration=duration)
            transition_bucket.append(material)
            seg.setdefault("extra_material_refs", []).append(material["id"])
            existing_names[material["id"]] = name
    return result


def report(document: dict) -> dict[str, int]:
    counts = {name: 0 for name in (*ANIMATION_NAMES.values(), *TRANSITION_NAMES.values())}
    for material in document.get("materials", {}).get("material_animations", []):
        name = animation_name(material)
        if name in counts:
            counts[name] += 1
    for material in document.get("materials", {}).get("transitions", []):
        name = material.get("name", "")
        if name in counts:
            counts[name] += 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="CapCut 원생 모션 마감 적용")
    parser.add_argument("draft", type=Path)
    parser.add_argument("--source", type=Path, required=True, help="사용자가 마감한 기준 draft_content.json")
    parser.add_argument("--zoom-scenes", type=parse_scene_list, default=[])
    parser.add_argument("--bounce-scenes", type=parse_scene_list, default=[])
    parser.add_argument("--left-joins", type=parse_scene_list, default=[])
    parser.add_argument("--fake-zoom-joins", type=parse_scene_list, default=[])
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    draft_path = args.draft.resolve()
    source_path = args.source.resolve()
    if not draft_path.exists() or not source_path.exists():
        raise SystemExit(f"[실패] 파일 없음: draft={draft_path.exists()} source={source_path.exists()}")
    current = load(draft_path)
    source = load(source_path)
    finished = attach(
        current,
        source,
        zoom_scenes=args.zoom_scenes,
        bounce_scenes=args.bounce_scenes,
        left_joins=args.left_joins,
        fake_zoom_joins=args.fake_zoom_joins,
    )
    print(json.dumps(report(finished), ensure_ascii=False, indent=2))
    if not args.write:
        print("\n점검만 수행했습니다. 저장하려면 --write를 붙이세요.")
        return 0
    if capcut_editor_open() and is_live_draft(draft_path):
        raise SystemExit("[실패] CapCut 본체가 열려 있습니다. 완전히 종료한 뒤 다시 실행하세요.")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    targets = [draft_path]
    targets.extend(draft_path.parent / name for name in COMPANION_NAMES
                   if (draft_path.parent / name).exists())
    for target in targets:
        target_finished = attach(
            load(target),
            source,
            zoom_scenes=args.zoom_scenes,
            bounce_scenes=args.bounce_scenes,
            left_joins=args.left_joins,
            fake_zoom_joins=args.fake_zoom_joins,
        )
        backup = target.with_name(f"{target.name}.before-motion-finish-{stamp}.bak")
        shutil.copy2(target, backup)
        temp = target.with_name(f"{target.name}.motion-finish.tmp")
        temp.write_text(json.dumps(target_finished, ensure_ascii=False), encoding="utf-8")
        load(temp)
        temp.replace(target)
        print(f"\n저장: {target}\n백업: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
