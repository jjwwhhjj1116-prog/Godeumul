#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""장면표를 I2V·T2V Flow 입력 파일과 원본 장면 매핑으로 분리한다."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import _config  # noqa: F401
from artifact_form_gate import REFERENCE_LOCK_NAME, validate_reference_lock


MODES = {"I2V_LOCKED", "T2V_CONTEXT"}
VISIBILITIES = {"IDENTIFIABLE", "NON_IDENTIFIABLE", "NONE"}
T2V_ALLOWED_SCENE_TYPES = {
    "DISCOVERY_ACTION", "EXCAVATION", "HISTORICAL_RECONSTRUCTION",
    "SITE_ESTABLISH", "CONSERVATION",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _write_blocks(path: Path, blocks: list[str]) -> None:
    path.write_text("\n\n".join(blocks) + ("\n" if blocks else ""), encoding="utf-8")


def _lock_artifact_prompt(prompt: str, artifact_name: str, prompt_token: str) -> str:
    """Flow 제출본에 유물 참조 토큰과 형태 불변 조건을 자동 주입한다."""
    if artifact_name in prompt and prompt_token in prompt:
        return prompt
    return (
        f"{prompt_token}. Exact named hero artifact: {artifact_name}. "
        "Use the actually attached Flow visual reference as the immutable form owner. "
        "Preserve exactly the same silhouette, height-to-width ratio, part count, "
        "part placement, ornament layout, patina and damage. Never redraw or substitute "
        f"a generic lookalike. {prompt}"
    )


def verify_pack(episode: Path) -> dict[str, object]:
    plan_path = episode / "04.하이브리드생성계획.json"
    if not plan_path.exists():
        raise ValueError("04.하이브리드생성계획.json이 없습니다. 2G를 먼저 실행하세요")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if plan.get("version") != 3 or plan.get("gate") != "PASS":
        raise ValueError("하이브리드 생성계획 version 3 PASS 잠금이 아닙니다")
    hashes = plan.get("source_hashes")
    if not isinstance(hashes, dict) or not hashes:
        raise ValueError("하이브리드 생성계획에 source_hashes가 없습니다")
    for relative, expected in hashes.items():
        source = episode / relative
        if not source.exists():
            raise ValueError(f"생성계획 원본 누락: {relative}")
        actual = _sha256(source)
        if actual != expected:
            raise ValueError(f"생성계획 원본 변경: {relative} — 2G를 다시 실행하세요")
    for relative in ("flow_i2v_images.txt", "flow_i2v_videos.txt", "flow_t2v_videos.txt"):
        if not (episode / relative).exists():
            raise ValueError(f"Flow 입력 파일 누락: {relative}")
    return plan


def build_pack(episode: Path) -> dict[str, object]:
    scene_path = episode / "02a.장면구분.json"
    routing_path = episode / "02d.유물장면라우팅.json"
    duration_path = episode / "audio" / "durations.json"
    reference_path = episode / "02c.유물레퍼런스.json"
    reference_lock_path = episode / REFERENCE_LOCK_NAME
    for required in (scene_path, routing_path, duration_path, reference_path, reference_lock_path):
        if not required.exists():
            raise ValueError(f"고정 순서 누락: {required.name}이 없습니다")

    reference_lock = validate_reference_lock(episode)
    if not reference_lock.passed:
        raise ValueError("Flow 유물 참조 잠금 실패: " + " / ".join(reference_lock.failures))
    artifact_name = str(reference_lock.details["artifact_name_ko"])
    prompt_token = str(reference_lock.details["prompt_token"])

    scenes = json.loads(scene_path.read_text(encoding="utf-8"))
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("02a.장면구분.json은 비어 있지 않은 배열이어야 합니다")
    routing = json.loads(routing_path.read_text(encoding="utf-8"))
    route_rows = routing.get("scenes") if isinstance(routing, dict) else None
    if not isinstance(route_rows, dict):
        raise ValueError("02d.유물장면라우팅.json의 scenes 객체가 없습니다")
    route_by_scene = {int(key): value for key, value in route_rows.items()}
    scene_numbers = {int(scene.get("n") or 0) for scene in scenes}
    if set(route_by_scene) != scene_numbers:
        raise ValueError("라우팅 파일과 장면표의 장면 번호가 정확히 일치해야 합니다")

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
        image = str(scene.get("img_v2") or scene.get("img") or "").strip()

        route = route_by_scene[n]
        route_mode = str(route.get("generation_mode") or "").strip().upper()
        visibility = str(route.get("artifact_visibility") or "").strip().upper()
        reason = str(route.get("routing_reason") or "").strip()
        if route_mode != mode:
            raise ValueError(f"장면 {n:03d}: 장면표와 라우팅의 generation_mode 불일치")
        if visibility not in VISIBILITIES:
            raise ValueError(f"장면 {n:03d}: artifact_visibility 누락 또는 오류")
        if str(scene.get("artifact_visibility") or "").strip().upper() != visibility:
            raise ValueError(f"장면 {n:03d}: 장면표와 라우팅의 artifact_visibility 불일치")
        if len(reason) < 12:
            raise ValueError(f"장면 {n:03d}: I2V/T2V 선택 근거 routing_reason이 부족합니다")
        scene_type = str(scene.get("ct") or scene.get("scene_type") or "").strip().upper()
        reference_ids = route.get("artifact_reference_ids") or []
        if visibility == "IDENTIFIABLE":
            if mode != "I2V_LOCKED" or not reference_ids:
                raise ValueError(f"장면 {n:03d}: 식별 유물은 참조가 잠긴 I2V_LOCKED여야 합니다")
            image = _lock_artifact_prompt(image, artifact_name, prompt_token)
            video = _lock_artifact_prompt(video, artifact_name, prompt_token)
        if mode == "T2V_CONTEXT":
            if visibility == "IDENTIFIABLE":
                raise ValueError(f"장면 {n:03d}: T2V에서 식별 유물을 보여 줄 수 없습니다")
            if scene_type not in T2V_ALLOWED_SCENE_TYPES:
                raise ValueError(f"장면 {n:03d}: {scene_type}는 T2V 허용 장면이 아닙니다")
            low = video.lower()
            if "do not show the named hero artifact in identifiable form" not in low:
                raise ValueError(f"장면 {n:03d}: T2V 주 유물 배제 문구가 없습니다")

        if mode == "I2V_LOCKED":
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
            "routing_reason": reason,
            "artifact_reference_ids": reference_ids,
            "flow_reference_asset": artifact_name if visibility == "IDENTIFIABLE" else None,
            "flow_reference_token": prompt_token if visibility == "IDENTIFIABLE" else None,
            "flow_reference_required": visibility == "IDENTIFIABLE",
            "mode_index": mode_index,
            "prompt_file": target_file,
            "download_name": f"{n:03d}.mp4",
        })

    _write_blocks(episode / "flow_i2v_images.txt", i2v_images)
    _write_blocks(episode / "flow_i2v_videos.txt", i2v_videos)
    _write_blocks(episode / "flow_t2v_videos.txt", t2v_videos)

    plan = {
        "version": 3,
        "fixed_order": ["1Q", "2a", "3", "2c", "2e", "2d", "2b/2v", "2G", "4"],
        "gate": "PASS",
        "source_hashes": {
            "02a.장면구분.json": _sha256(scene_path),
            "audio/durations.json": _sha256(duration_path),
            "02c.유물레퍼런스.json": _sha256(reference_path),
            REFERENCE_LOCK_NAME: _sha256(reference_lock_path),
            "02d.유물장면라우팅.json": _sha256(routing_path),
        },
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
    parser.add_argument("--verify", action="store_true",
                        help="기존 version 3 생성계획의 원본 해시만 재검증")
    args = parser.parse_args()
    episode = args.episode.resolve()
    plan = verify_pack(episode) if args.verify else build_pack(episode)
    prefix = "게이트 재검증" if args.verify else "장면 분리"
    print(
        f"{prefix} PASS · 장면 {plan['scene_count']}개 → I2V {plan['i2v_count']}개 / "
        f"T2V {plan['t2v_count']}개"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
