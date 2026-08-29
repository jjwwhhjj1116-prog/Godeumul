#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""CapCut 원생 애니메이션·전환을 채널 고정 순서로 재사용한다.

영상 애니메이션은 ``줌 1``만 먼저 적용하고, 모든 애니메이션 처리가 끝난 뒤
장면 전환 ``왼쪽으로 밀기``만 적용한다. CapCut이 같은 클립의 전환 참조를
애니메이션 앞으로 다시 저장해 애니메이션을 씹는 문제가 있으므로 한 클립에
애니메이션과 전환을 함께 붙이지 않는다. ``반동 1``과 ``페이크 줌`` 등 기존
비허용 효과는 제거한다. 영상·오디오·자막 타이밍과 볼륨은 건드리지 않는다.
CapCut 본체를 완전히 닫은 상태에서만 ``--write``가 허용된다.
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


ANIMATION_NAMES = {"zoom": "줌 1"}
TRANSITION_NAMES = {"left": "왼쪽으로 밀기"}
DISALLOWED_VIDEO_EFFECTS = {"반동 1", "페이크 줌"}
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


def clone_animation(source: dict, *, segment_duration: int) -> dict:
    material = copy.deepcopy(source)
    material["id"] = new_id()
    animation = material["animations"][0]
    animation["start"] = 0
    animation["duration"] = max(1, segment_duration)
    return material


def clone_transition(source: dict, *, segment_duration: int) -> dict:
    material = copy.deepcopy(source)
    material["id"] = new_id()
    material["duration"] = min(int(material.get("duration") or 0), max(1, segment_duration // 2))
    return material


def attach(document: dict, source: dict, *, zoom_scenes: list[int], left_joins: list[int]) -> dict:
    overlapping = sorted(set(zoom_scenes) & set(left_joins))
    if overlapping:
        joined = ", ".join(map(str, overlapping))
        raise RuntimeError(
            "CapCut 애니메이션 씹힘 방지 실패: 같은 클립에 줌 1과 전환을 "
            f"함께 붙일 수 없습니다. 겹친 장면: {joined}"
        )

    result = copy.deepcopy(document)
    segments = main_video_segments(result)
    buckets = result.setdefault("materials", {})
    animation_bucket = buckets.setdefault("material_animations", [])
    transition_bucket = buckets.setdefault("transitions", [])
    existing_names = material_name_index(result)

    # 이전 실행의 관리 대상 효과와 비허용 효과를 먼저 걷어낸다. 이렇게 해야
    # 장면 목록을 바꿔 재실행해도 요청한 배치만 남는다. 텍스트 페이드는 제외한다.
    managed_names = {
        *ANIMATION_NAMES.values(),
        *TRANSITION_NAMES.values(),
        *DISALLOWED_VIDEO_EFFECTS,
    }
    for seg in segments:
        seg["extra_material_refs"] = [
            ref for ref in seg.get("extra_material_refs", [])
            if existing_names.get(ref) not in managed_names
        ]

    def segment(scene: int) -> dict:
        if scene > len(segments):
            raise RuntimeError(f"장면 {scene}은 주 영상 {len(segments)}개 범위를 벗어납니다.")
        return segments[scene - 1]

    def has_name(seg: dict, name: str) -> bool:
        return any(existing_names.get(ref) == name for ref in seg.get("extra_material_refs", []))

    # 1단계: 모든 줌 1 애니메이션을 먼저 적용한다.
    animation_name_value = ANIMATION_NAMES["zoom"]
    animation_prototype = source_material(source, "material_animations", animation_name_value)
    for scene_number in zoom_scenes:
        seg = segment(scene_number)
        if has_name(seg, animation_name_value):
            continue
        duration = int(seg["target_timerange"]["duration"])
        material = clone_animation(animation_prototype, segment_duration=duration)
        animation_bucket.append(material)
        seg.setdefault("extra_material_refs", []).append(material["id"])
        existing_names[material["id"]] = animation_name_value

    # 2단계: 애니메이션이 모두 끝난 뒤 왼쪽으로 밀기 전환만 적용한다.
    transition_name_value = TRANSITION_NAMES["left"]
    transition_prototype = source_material(source, "transitions", transition_name_value)
    for scene_number in left_joins:
        if scene_number >= len(segments):
            raise RuntimeError(f"전환은 마지막 장면 뒤에 붙일 수 없습니다: {scene_number}")
        seg = segment(scene_number)
        if has_name(seg, transition_name_value):
            continue
        duration = int(seg["target_timerange"]["duration"])
        material = clone_transition(transition_prototype, segment_duration=duration)
        transition_bucket.append(material)
        seg.setdefault("extra_material_refs", []).append(material["id"])
        existing_names[material["id"]] = transition_name_value
    return result


def report(document: dict) -> dict[str, int]:
    counts = {name: 0 for name in (*ANIMATION_NAMES.values(), *TRANSITION_NAMES.values())}
    names = material_name_index(document)
    for segment in main_video_segments(document):
        for ref in segment.get("extra_material_refs", []):
            name = names.get(ref, "")
            if name in counts:
                counts[name] += 1
    return counts


def validate_policy(document: dict) -> None:
    """주 영상에는 허용 효과 한 종류만 붙고 같은 클립에는 겹치지 않아야 한다."""
    materials = document.get("materials", {})
    animations = {
        item.get("id", ""): animation_name(item)
        for item in materials.get("material_animations", [])
    }
    transitions = {
        item.get("id", ""): item.get("name", "")
        for item in materials.get("transitions", [])
    }
    failures: list[str] = []
    for scene_number, segment in enumerate(main_video_segments(document), 1):
        phase = "animation"
        attached_animations = 0
        attached_transitions = 0
        for ref in segment.get("extra_material_refs", []):
            if ref in animations:
                attached_animations += 1
                name = animations[ref]
                if name != ANIMATION_NAMES["zoom"]:
                    failures.append(f"장면 {scene_number}: 비허용 영상 애니메이션 {name!r}")
                if phase == "transition":
                    failures.append(f"장면 {scene_number}: 전환 뒤에 애니메이션 참조가 있음")
            elif ref in transitions:
                attached_transitions += 1
                phase = "transition"
                name = transitions[ref]
                if name != TRANSITION_NAMES["left"]:
                    failures.append(f"장면 {scene_number}: 비허용 전환 {name!r}")
        if attached_animations and attached_transitions:
            failures.append(
                f"장면 {scene_number}: 애니메이션과 전환이 같은 클립에 겹침 "
                "(CapCut 자동 재정렬로 애니메이션이 씹힐 수 있음)"
            )
    if failures:
        raise RuntimeError("CapCut 효과 정책 실패:\n- " + "\n- ".join(failures))


def main() -> int:
    parser = argparse.ArgumentParser(description="CapCut 원생 모션 마감 적용")
    parser.add_argument("draft", type=Path)
    parser.add_argument("--source", type=Path, required=True, help="사용자가 마감한 기준 draft_content.json")
    parser.add_argument("--zoom-scenes", type=parse_scene_list, default=[])
    parser.add_argument("--left-joins", type=parse_scene_list, default=[])
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
        left_joins=args.left_joins,
    )
    validate_policy(finished)
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
            left_joins=args.left_joins,
        )
        validate_policy(target_finished)
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
