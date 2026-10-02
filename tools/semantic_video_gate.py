#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Block CapCut assembly until every visual beat has been watched against TTS.

This gate cannot recognise images by itself. It requires a human observation for
each precommitted visual requirement, then binds that observation to the exact
script, TTS, prompt and video hashes. Missing or stale review is a failure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from visual_timeline import load_visual_timeline


CONTRACT_NAME = "02P.대본화면계약.json"
REVIEW_NAME = "04Q.대본영상의미검수.json"


def effective_media(episode: Path, scene_id: str, target: dict, errors: list[str]):
    """Explicit source selection is not a QA approval. Legacy default stays strict."""
    binding = target.get("accepted_media")
    default = episode / "clips" / f"{scene_id}.mp4"
    if binding is None:
        return default, "video", None
    if not isinstance(binding, dict):
        errors.append(f"{scene_id}: accepted_media 객체 필요")
        return default, "video", None
    name = binding.get("file", "")
    path = (episode / str(name)).resolve()
    if (not isinstance(name, str) or not name or Path(name).is_absolute()
            or not path.is_relative_to(episode) or not path.is_file()):
        errors.append(f"{scene_id}: accepted_media 회차 내부 상대 파일 필요")
    elif binding.get("sha256") != sha256_file(path):
        errors.append(f"{scene_id}: accepted_media 해시 불일치")
    if binding.get("selection_approved") is not True or not str(binding.get("authorization_basis", "")).strip():
        errors.append(f"{scene_id}: accepted_media 대체 선택 승인 근거 없음")
    kind = binding.get("type")
    if kind not in ("video", "photo"):
        errors.append(f"{scene_id}: accepted_media type 오류")
    span = binding.get("source_range")
    if kind == "video":
        if (not isinstance(span, dict) or type(span.get("start")) is not int
                or type(span.get("duration")) is not int or span['start'] < 0 or span['duration'] <= 0):
            errors.append(f"{scene_id}: accepted_media source_range 마이크로초 오류")
    elif kind == "photo":
        mode_path = episode / "02d.영상생성모드.json"
        if mode_path.is_file():
            try:
                mode = json.loads(mode_path.read_text(encoding="utf-8"))
                if mode.get("allow_photo_main_track") is False:
                    errors.append(f"{scene_id}: 현재 회차 승인 범위에서 사진 본영상 대체 금지")
            except (OSError, ValueError, AttributeError):
                errors.append(f"{scene_id}: 사진 대체 허용 정책 읽기 실패")
        if span is not None or "source_range" not in binding:
            errors.append(f"{scene_id}: 사진 source_range는 명시적 null이어야 함")
        if not target.get("evidence_assets"):
            errors.append(f"{scene_id}: 사진 대체의 공식 증거 목록 없음")
    return path, kind, binding


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def required_for(episode: Path) -> bool:
    match = re.match(r"EP(\d+)_", episode.name, re.IGNORECASE)
    return bool(match and int(match.group(1)) >= 18)


def _read_json(path: Path, errors: list[str]) -> dict:
    if not path.is_file():
        errors.append(f"필수 검수 파일 없음: {path.name}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        errors.append(f"{path.name} 파싱 실패: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path.name}의 최상위 값은 객체여야 합니다")
        return {}
    return value


def validate_contract(episode: Path) -> list[str]:
    """Pre-build check: lock the script, intended evidence and source assets.

    A still-photo evidence layer cannot be observed in a composite before the
    CapCut draft exists. Do not require the final review at this stage.
    """
    episode = Path(episode).resolve()
    if not required_for(episode):
        return []
    errors: list[str] = []
    script = episode / "01.대본.txt"
    visual = episode / "02.시각화.txt"
    durations = episode / "audio/durations.json"
    for path in (script, visual, durations):
        if not path.is_file():
            errors.append(f"필수 원본 없음: {path}")
    if errors:
        return errors

    contract = _read_json(episode / CONTRACT_NAME, errors)
    if errors:
        return errors
    try:
        audio_scenes = json.loads(durations.read_text(encoding="utf-8"))["scenes"]
        timeline = load_visual_timeline(episode, audio_scenes)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return [f"실측 TTS/장면 시간표 오류: {exc}"]

    if contract.get("version") != 1:
        errors.append("대본-화면 계약 version은 1이어야 합니다")
    for name, path in (("script_sha256", script), ("visual_sha256", visual)):
        actual = sha256_file(path)
        if contract.get(name) != actual:
            errors.append(f"계약 {name} 불일치: {path.name}")
    targets = contract.get("scenes")
    if not isinstance(targets, dict):
        return [*errors, "계약에 scenes 객체가 필요합니다"]
    expected_ids = [f"{row['visual_scene']:03d}" for row in timeline]
    if set(targets) != set(expected_ids):
        errors.append("계약 scenes 번호가 실측 영상 장면표와 다릅니다")
    for row in timeline:
        scene_id = f"{row['visual_scene']:03d}"
        audio_id = str(row["audio_scene"])
        target = targets.get(scene_id, {})
        if not isinstance(target, dict):
            errors.append(f"{scene_id}: 계약 항목이 객체가 아님")
            continue
        effective_media(episode, scene_id, target, errors)
        narration = str(audio_scenes[audio_id].get("text", ""))
        if target.get("narration") != narration:
            errors.append(f"{scene_id}: 계약 나레이션이 실제 TTS와 다름")
        must_show = target.get("must_show")
        if not isinstance(must_show, list) or not must_show or not all(
            isinstance(item, str) and item.strip() for item in must_show
        ):
            errors.append(f"{scene_id}: 계약 must_show가 비어 있음")
            continue
        if not str(target.get("arrival", "")).strip():
            errors.append(f"{scene_id}: 도착 화면이 지정되지 않음")

        prompt_name = target.get("prompt")
        if not isinstance(prompt_name, str) or not prompt_name.startswith("02v."):
            errors.append(f"{scene_id}: 선택 영상 프롬프트 경로가 없음")
        else:
            prompt = episode / prompt_name
            if not prompt.is_file() or target.get("prompt_sha256") != sha256_file(prompt):
                errors.append(f"{scene_id}: 선택 프롬프트 파일/해시 불일치")

        assets = target.get("evidence_assets", [])
        if not isinstance(assets, list):
            errors.append(f"{scene_id}: evidence_assets는 배열이어야 함")
            continue
        for asset in assets:
            if not isinstance(asset, dict) or not str(asset.get("file", "")).strip():
                errors.append(f"{scene_id}: 증거 사진 경로/역할 누락")
                continue
            path = (episode / asset["file"]).resolve()
            if not path.is_relative_to(episode) or not path.is_file():
                errors.append(f"{scene_id}: 증거 사진 경로가 없거나 회차 밖임: {asset['file']}")
            elif asset.get("sha256") != sha256_file(path):
                errors.append(f"{scene_id}: 증거 사진 해시 불일치: {asset['file']}")
            if not str(asset.get("role", "")).strip():
                errors.append(f"{scene_id}: 증거 사진의 설명 역할 누락")
    return errors


def validate(episode: Path, final_video: Path | None = None) -> list[str]:
    episode = Path(episode).resolve()
    if not required_for(episode):
        return []
    errors = validate_contract(episode)
    if errors:
        return errors
    contract_path = episode / CONTRACT_NAME
    review_path = episode / REVIEW_NAME
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    review = _read_json(review_path, errors)
    if errors:
        return errors
    audio_scenes = json.loads((episode / "audio/durations.json").read_text(encoding="utf-8"))["scenes"]
    timeline = load_visual_timeline(episode, audio_scenes)
    targets = contract["scenes"]
    observations = review.get("scenes")
    if review.get("version") != 1:
        errors.append("의미 검수 version은 1이어야 합니다")
    if review.get("contract_sha256") != sha256_file(contract_path):
        errors.append("의미 검수가 현재 대본-화면 계약의 해시와 다릅니다")
    if not isinstance(observations, dict):
        return [*errors, "의미 검수에 scenes 객체가 필요합니다"]
    expected_ids = [f"{row['visual_scene']:03d}" for row in timeline]
    if set(observations) != set(expected_ids):
        errors.append("의미 검수 scenes 번호가 실측 영상 장면표와 다릅니다")

    if final_video is not None:
        final_video = Path(final_video).resolve()
        if not final_video.is_file() or review.get("final_master_sha256") != sha256_file(final_video):
            errors.append("의미 검수의 최종 영상 해시가 실제 내보내기와 다름")
        if review.get("full_master_playback_reviewed") is not True:
            errors.append("최종 영상 전체 재생 검수가 없음")

    for row in timeline:
        scene_id = f"{row['visual_scene']:03d}"
        audio_id = str(row["audio_scene"])
        target = targets[scene_id]
        observed = observations.get(scene_id, {})
        if not isinstance(observed, dict):
            errors.append(f"{scene_id}: 검수 항목이 객체가 아님")
            continue
        must_show = target["must_show"]

        clip, media_type, binding = effective_media(episode, scene_id, target, errors)
        if binding is not None and observed.get("accepted_media") != binding:
            errors.append(f"{scene_id}: 검수 accepted_media 선택/구간 바인딩 불일치")
        audio_name = audio_scenes[audio_id].get("file", f"{int(audio_id):03d}.mp3")
        audio = episode / "audio" / audio_name
        for field, path in (("clip_sha256", clip), ("audio_sha256", audio)):
            if not path.is_file() or observed.get(field) != sha256_file(path):
                errors.append(f"{scene_id}: {field} 파일/해시 불일치")
        if observed.get("status") != "PASS" or observed.get("full_clip_playback_reviewed") is not True:
            errors.append(f"{scene_id}: 전체 재생 의미 검수 PASS가 아님")
        motion_pass = observed.get("camera_motion") == "PASS"
        if media_type == "photo":
            motion_pass = (observed.get("camera_motion") == "NOT_APPLICABLE_PHOTO"
                           and observed.get("photo_animation") == "ZOOM1_FULL_DURATION_VERIFIED"
                           and observed.get("composite_playback_reviewed") is True)
        if observed.get("narration_sync") != "PASS" or not motion_pass:
            errors.append(f"{scene_id}: TTS 싱크 또는 실제 카메라 이동 검수 실패")
        checks = observed.get("evidence_checks")
        if not isinstance(checks, list) or len(checks) != len(must_show):
            errors.append(f"{scene_id}: 필수 화면 증거 전수 관찰이 없음")
            continue
        for index, (needed, check) in enumerate(zip(must_show, checks), start=1):
            if not isinstance(check, dict) or check.get("required") != needed:
                errors.append(f"{scene_id}: 증거 {index}가 계약과 다름")
                continue
            if check.get("status") != "PASS" or not str(check.get("observed", "")).strip():
                errors.append(f"{scene_id}: 증거 {index} 관찰 PASS가 아님")
            at_s = check.get("visible_at_s")
            if not isinstance(at_s, (int, float)) or at_s < 0:
                errors.append(f"{scene_id}: 증거 {index} 확인 시각이 없음")

        assets = target.get("evidence_assets", [])
        if (final_video is not None or media_type == "photo") and assets:
            if observed.get("composite_playback_reviewed") is not True:
                errors.append(f"{scene_id}: 공식 사진을 포함한 최종 합성 화면 재생 검수가 없음")
            asset_checks = observed.get("evidence_asset_checks")
            if not isinstance(asset_checks, list) or len(asset_checks) != len(assets):
                errors.append(f"{scene_id}: 공식 사진의 최종 화면 검수가 없음")
            else:
                for asset, asset_check in zip(assets, asset_checks):
                    if (not isinstance(asset_check, dict)
                            or asset_check.get("file") != asset["file"]
                            or asset_check.get("status") != "PASS"
                            or not str(asset_check.get("observed", "")).strip()
                            or not isinstance(asset_check.get("visible_at_s"), (int, float))):
                        errors.append(f"{scene_id}: 공식 사진이 실제 영상에 보였다는 검수 없음: {asset['file']}")

    boundaries = review.get("boundaries")
    if not isinstance(boundaries, list) or len(boundaries) != max(0, len(expected_ids) - 1):
        errors.append("모든 인접 컷 경계의 끝 1초→시작 1초 검수가 필요합니다")
    else:
        for index, boundary in enumerate(boundaries):
            pair = f"{expected_ids[index]}>{expected_ids[index + 1]}"
            if (not isinstance(boundary, dict) or boundary.get("pair") != pair
                    or boundary.get("status") != "PASS"
                    or not str(boundary.get("observed", "")).strip()):
                errors.append(f"경계 {pair}: 연속성 관찰 PASS가 아님")
    return errors


def validate_draft_sources(episode: Path, draft: dict, *, require_evidence_layers: bool = True) -> list[str]:
    """Reject an exported draft that silently substitutes old-episode footage."""
    episode = Path(episode).resolve()
    if not required_for(episode):
        return []
    if not isinstance(draft, dict):
        return ["CapCut draft_content가 객체가 아님"]
    materials = draft.get("materials") or {}
    video_materials = {
        item.get("id"): item for item in materials.get("videos", [])
        if isinstance(item, dict)
    }
    tracks = [
        track for track in draft.get("tracks", [])
        if isinstance(track, dict) and track.get("type") == "video"
        and track.get("flag") == 0
    ]
    if len(tracks) != 1:
        return [f"CapCut 본영상 트랙은 정확히 하나여야 함: {len(tracks)}개"]
    segments = sorted(
        tracks[0].get("segments", []),
        key=lambda item: item.get("target_timerange", {}).get("start", -1),
    )
    try:
        count = len(load_visual_timeline(
            episode,
            json.loads((episode / "audio/durations.json").read_text(encoding="utf-8"))["scenes"],
        ))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return [f"CapCut 소스 검사용 장면표 오류: {exc}"]
    errors: list[str] = []
    contract_path = episode / CONTRACT_NAME
    contract = _read_json(contract_path, errors) if contract_path.is_file() else {}
    if len(segments) != count:
        errors.append(f"CapCut 본영상 컷 수 불일치: {len(segments)} / {count}")
    for index, segment in enumerate(segments[:count], start=1):
        expected, kind, binding = effective_media(episode, f"{index:03d}", contract.get("scenes", {}).get(f"{index:03d}", {}), errors)
        material = video_materials.get(segment.get("material_id"))
        if not isinstance(material, dict):
            errors.append(f"{index:03d}: CapCut 영상 소재 연결 누락")
            continue
        actual = Path(str(material.get("path", ""))).resolve()
        if actual != expected:
            errors.append(f"{index:03d}: CapCut 본영상이 승인 컷과 다름: {actual}")
        elif not actual.is_file():
            errors.append(f"{index:03d}: CapCut 참조 영상 파일 없음")
        if binding is not None:
            if material.get("type") != kind or segment.get("source_timerange") != binding.get("source_range"):
                errors.append(f"{index:03d}: CapCut 선택 매체 유형/소스 구간 불일치")
            if kind == "photo":
                animations = [a for m in materials.get("material_animations", [])
                              if m.get("id") in segment.get("extra_material_refs", [])
                              for a in m.get("animations", [])]
                if (len(animations) != 1 or animations[0].get("name") != "줌 1"
                        or animations[0].get("start") != 0
                        or animations[0].get("duration") != segment.get("target_timerange", {}).get("duration")):
                    errors.append(f"{index:03d}: 사진 대체 줌1 전길이 검문 실패")
    contract_path = episode / CONTRACT_NAME
    if require_evidence_layers and contract_path.is_file():
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        required_assets = {
            (episode / asset["file"]).resolve()
            for target in contract.get("scenes", {}).values()
            if isinstance(target, dict)
            for asset in target.get("evidence_assets", [])
            if isinstance(asset, dict) and asset.get("file")
        }
        overlay_material_ids = {
            segment.get("material_id")
            for track in draft.get("tracks", [])
            if isinstance(track, dict) and track.get("type") == "video"
            and track.get("flag") not in (0, 2)
            for segment in track.get("segments", [])
            if isinstance(segment, dict)
        }
        overlay_paths = {
            Path(str(video_materials[material_id].get("path", ""))).resolve()
            for material_id in overlay_material_ids
            if material_id in video_materials
        }
        for asset in sorted(required_assets):
            if asset not in overlay_paths:
                errors.append(f"CapCut 공식 사진 증거 레이어 누락: {asset}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="대본↔영상 의미·출처 검문")
    parser.add_argument("episode", type=Path)
    args = parser.parse_args()
    errors = validate(args.episode)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: 대본-화면 의미·출처·경계 검문")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
