#!/usr/bin/env python3
"""기존 CapCut 드래프트의 자막 애니메이션만 채널 표준으로 교체한다.

영상 클립의 `줌 1`·`반동 1` 같은 조합 애니메이션은 그대로 보존하고,
text 트랙 세그먼트가 참조하는 material_animation만 `페이드 인 0.25초`로
바꾼다. CapCut을 닫은 상태에서 ``--write``로 실행한다.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
from pathlib import Path
from types import SimpleNamespace

from capcut_build import CAPTION_FADE_DURATION_US, set_caption_fade_in


def load_draft(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def animation_map(draft: dict) -> dict[str, dict]:
    return {
        item["id"]: item
        for item in draft.get("materials", {}).get("material_animations", [])
        if isinstance(item, dict) and item.get("id")
    }


def referenced_animation_names(draft: dict, track_type: str) -> list[str]:
    by_id = animation_map(draft)
    names: list[str] = []
    for track in draft.get("tracks", []):
        if track.get("type") != track_type:
            continue
        for segment in track.get("segments", []):
            for ref in segment.get("extra_material_refs", []):
                material = by_id.get(ref)
                if not material:
                    continue
                animations = material.get("animations") or []
                if animations:
                    names.append(str(animations[0].get("name", "")))
    return names


def text_animation_refs(draft: dict) -> tuple[list[str], int]:
    by_id = animation_map(draft)
    refs: list[str] = []
    segment_count = 0
    for track in draft.get("tracks", []):
        if track.get("type") != "text":
            continue
        for segment in track.get("segments", []):
            segment_count += 1
            matches = [
                ref for ref in segment.get("extra_material_refs", []) if ref in by_id
            ]
            if not matches:
                raise ValueError(f"자막 세그먼트 {segment.get('id')}에 애니메이션 참조가 없습니다.")
            refs.extend(matches)
    return refs, segment_count


def apply_caption_fade(draft: dict) -> dict:
    result = copy.deepcopy(draft)
    refs, segment_count = text_animation_refs(result)
    materials = result.get("materials", {}).get("material_animations", [])
    before_video = referenced_animation_names(result, "video")

    set_caption_fade_in(SimpleNamespace(out={"material_animations": materials}), refs)

    by_id = animation_map(result)
    bad = []
    for ref in refs:
        animation = (by_id[ref].get("animations") or [{}])[0]
        if (
            animation.get("name") != "페이드 인"
            or animation.get("duration") != CAPTION_FADE_DURATION_US
        ):
            bad.append(ref)
    if bad:
        raise ValueError(f"페이드 인 변환 실패: {len(bad)}개")

    after_video = referenced_animation_names(result, "video")
    if before_video != after_video:
        raise ValueError("영상 클립 애니메이션이 변경되어 저장을 중단합니다.")

    return {
        "draft": result,
        "segments": segment_count,
        "refs": len(refs),
        "video_animations": after_video,
    }


def atomic_write(path: Path, draft: dict) -> Path:
    backup = path.with_name(path.name + ".before-caption-fade.bak")
    temp = path.with_name(path.name + ".caption-fade.tmp")
    shutil.copy2(path, backup)
    try:
        with temp.open("w", encoding="utf-8", newline="\n") as fh:
            json.dump(draft, fh, ensure_ascii=False, separators=(",", ":"))
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()
    return backup


def companion_drafts(primary: Path) -> list[Path]:
    """CapCut이 복구 원본으로 쓰는 같은 폴더의 JSON 사본을 함께 찾는다."""
    candidates = [
        primary,
        primary.with_name("draft_content.json.bak"),
        primary.with_name("template-2.tmp"),
    ]
    result: list[Path] = []
    for path in candidates:
        if path.exists() and path not in result:
            result.append(path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("draft", type=Path, help="draft_content.json 경로")
    parser.add_argument("--write", action="store_true", help="백업 후 실제 저장")
    args = parser.parse_args()

    paths = companion_drafts(args.draft) if args.write else [args.draft]
    for path in paths:
        draft = load_draft(path)
        result = apply_caption_fade(draft)
        print(
            f"[PASS] {path.name}: 자막 {result['segments']}개 / "
            f"애니메이션 참조 {result['refs']}개 -> "
            f"페이드 인 {CAPTION_FADE_DURATION_US / 1_000_000:.2f}초"
        )
        print(
            f"[PASS] {path.name}: 영상 조합 애니메이션 "
            f"{len(result['video_animations'])}개 보존"
        )
        if args.write:
            backup = atomic_write(path, result["draft"])
            print(f"[저장] {path}")
            print(f"[백업] {backup}")
    if not args.write:
        print("[DRY-RUN] --write를 붙이면 실제 저장합니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
