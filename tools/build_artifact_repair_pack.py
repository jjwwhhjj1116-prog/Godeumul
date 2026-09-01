#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""형태 QA 실패 장면을 같은 Flow 유물 참조 자산으로 재생성하는 복구 팩을 만든다."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from artifact_form_gate import validate_reference_lock


def blocks(path: Path, values: list[str]) -> None:
    path.write_text("\n\n".join(values) + "\n", encoding="utf-8")


def build(episode: Path, pro: list[int], ultra: list[int], static_scene: int | None) -> dict:
    reference = validate_reference_lock(episode)
    if not reference.passed:
        raise ValueError("유물 참조 잠금 실패: " + " / ".join(reference.failures))
    scenes = json.loads((episode / "02a.장면구분.json").read_text(encoding="utf-8"))
    by_scene = {int(row["n"]): row for row in scenes}
    selected = pro + ultra
    static_scenes = [static_scene] if static_scene else []
    missing = [scene for scene in selected + static_scenes if scene not in by_scene]
    if missing:
        raise ValueError(f"장면표에 없는 장면: {missing}")

    name = str(reference.details["artifact_name_ko"])
    token = str(reference.details["prompt_token"])
    prefix = (
        f"{token}. Exact named hero artifact: {name}. Use the actually attached Flow visual "
        "reference as the immutable form owner. Preserve exactly the same silhouette, "
        "height-to-width ratio, part count, part placement, ornament layout, patina and damage. "
        "Never redraw or substitute a generic lookalike. "
    )
    image_prompts: list[str] = []
    video_prompts: list[str] = []
    mapping: list[dict] = []
    for account, numbers in (("jy04210810@gmail.com", pro), ("jjwwhhjj1116@gmail.com", ultra)):
        for scene_number in numbers:
            row = by_scene[scene_number]
            image_prompt = prefix + str(row.get("img_v2") or row.get("img") or "")
            video_prompt = prefix + str(row.get("vid") or "")
            image_prompts.append(image_prompt)
            video_prompts.append(video_prompt)
            mapping.append({
                "scene": scene_number,
                "account": account,
                "credits": 12,
                "resolution": "720p",
                "seconds": int(row.get("omni") or 8),
                "artifact_name_ko": name,
                "flow_reference_token": token,
                "reference_required": True,
                "download_name": f"{scene_number:03d}.mp4",
            })

    blocks(episode / "flow_repair_images.txt", image_prompts)
    blocks(episode / "flow_repair_videos.txt", video_prompts)
    plan = {
        "version": 1,
        "status": "READY_FOR_FLOW_REFERENCE_ATTACHMENT",
        "artifact_name_ko": name,
        "flow_reference_token": token,
        "diorama_reference": reference.details["diorama_file"],
        "diorama_sha256": reference.details["diorama_sha256"],
        "pro_credit_budget": len(pro) * 12,
        "ultra_credit_budget": len(ultra) * 12,
        "regenerate_count": len(mapping),
        "static_exact_form_scene": ({
            "scene": static_scene,
            "source": reference.details["diorama_file"],
            "edit": "CapCut 줌 1만 적용; 유물 형태를 생성 모델에 다시 맡기지 않음",
        } if static_scene else None),
        "mapping": mapping,
    }
    (episode / "04.유물재생성계획.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return plan


def parse_scenes(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="유물 형태 실패 장면 Flow 복구 팩 생성")
    parser.add_argument("episode", type=Path)
    parser.add_argument("--pro", default="")
    parser.add_argument("--ultra", default="2,4,5,6,8,9,12,13,14,15,16,17,18,19,21,22,23")
    parser.add_argument("--static-scene", type=int, default=0)
    args = parser.parse_args()
    plan = build(
        args.episode.resolve(), parse_scenes(args.pro), parse_scenes(args.ultra),
        args.static_scene or None,
    )
    print(
        f"복구 팩 완료: Flow {plan['regenerate_count']}컷 "
        f"(Pro {plan['pro_credit_budget']} / Ultra {plan['ultra_credit_budget']} 크레딧) "
        f"+ 정지형태 {1 if plan['static_exact_form_scene'] else 0}컷"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
