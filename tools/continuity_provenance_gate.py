#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Read-only gate for a connected Flow/VEO scene route and selected clip provenance.

This is structural validation, not visual QA. It never labels an unseen video PASS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

BRIDGES = {"SPATIAL_CONTINUE", "MATCH_CUT", "MOTIVATED_TIME_JUMP"}
FLOW_KINDS = {"FLOW_VEO_I2V", "FLOW_VEO_OMNI_EDIT"}
LOCAL_MARKERS = ("preview", "remotion", "local_graphic", "true_plate_preview")


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(episode: Path, phase: str = "selection") -> list[str]:
    episode = episode.resolve()
    errors: list[str] = []
    contract_path = episode / "02G.연속탐방계약.json"
    if not contract_path.is_file():
        match = re.match(r"EP(\d+)(?:_|$)", episode.name, flags=re.IGNORECASE)
        if match and int(match.group(1)) < 16:
            return []  # Historical locks remain unchanged; new gate starts at EP16.
        return [f"연속탐방 계약 누락: {contract_path}"]
    try:
        contract = _read(contract_path)
    except (OSError, ValueError) as exc:
        return [f"연속탐방 계약 읽기 실패: {exc}"]

    mode_path = episode / '02d.영상생성모드.json'
    if mode_path.is_file():
        try:
            mode = _read(mode_path)
        except (OSError, ValueError) as exc:
            return [f'생성 모드 읽기 실패: {exc}']
        if mode.get('mode') == 'T2V_OUTPUT_FRAME_CHAIN_LOCKED':
            from output_frame_chain_gate import validate_output_chain
            return validate_output_chain(episode, phase, mode, contract)
        if contract.get('mode') == 'T2V_OUTPUT_FRAME_CHAIN_LOCKED':
            return ['선언된 생성 모드와 output-chain 계약이 다름']

    count = int(contract.get("scene_count") or 0)
    route = contract.get("route") or []
    shared_frames = contract.get("shared_frames") or []
    links = contract.get("links") or []
    graphics = contract.get("graphics") or []
    if count < 2 or [row.get("n") for row in route] != list(range(1, count + 1)):
        errors.append("전체 탐방 경로가 1..N 장면을 순서대로 덮지 않음")
    if [row.get("after") for row in links] != list(range(1, count)):
        errors.append("인접 B→A 연결이 N-1개 모두 순서대로 없음")
    if [row.get("n") for row in graphics] != list(range(1, count + 1)):
        errors.append("VEO 설명 그래픽/없음 계약이 1..N 전 컷에 없음")
    if [row.get("n") for row in shared_frames] != list(range(1, count + 2)):
        errors.append("공유 프레임 F001..F(N+1) 계획 누락")
    else:
        for row in shared_frames:
            if row.get("file") != f"images_shared/F{row['n']:03d}.png":
                errors.append(f"공유 프레임 {row['n']}: 파일명/순번 불일치")
            if not str(row.get("visible_state") or "").strip():
                errors.append(f"공유 프레임 {row['n']}: 보이는 결과 상태 누락")
        if "사리" not in str(shared_frames[1].get("visible_state") or ""):
            errors.append("F002: 컷 001 끝에서 사리기 공개 결과가 보이지 않음")
    for row in route:
        n = row.get("n")
        for key in ("era_place", "entry", "exit", "narration_evidence"):
            if not str(row.get(key) or "").strip():
                errors.append(f"컷 {n}: 탐방 경로 {key} 누락")
    for row in graphics:
        n = row.get("n")
        if row.get("owner") != "FLOW_VEO":
            errors.append(f"컷 {n}: 설명 동작 소유자가 Flow/VEO가 아님")
        if row.get("kind") == "NONE":
            if not str(row.get("reason") or "").strip():
                errors.append(f"컷 {n}: 그래픽 없는 이유 누락")
        else:
            for key in ("kind", "anchor", "cue", "action"):
                if not str(row.get(key) or "").strip():
                    errors.append(f"컷 {n}: VEO 월드 설명동작 {key} 누락")
    mandatory_graphics = {9, 10, 11, 13, 14, 18, 19}
    if len(graphics) == count:
        for n in mandatory_graphics.intersection(range(1, count + 1)):
            if graphics[n - 1].get("kind") == "NONE":
                errors.append(f"컷 {n}: 대본 수치/공간범위를 말하는데 VEO 설명동작 없음")
    for row in links:
        n = row.get("after")
        if row.get("type") not in BRIDGES:
            errors.append(f"{n}→{n+1}: 연결 종류 오류")
        for key in ("b_anchor", "a_anchor", "visible_match", "narration_motivation"):
            if not str(row.get(key) or "").strip():
                errors.append(f"{n}→{n+1}: {key} 누락")
        if row.get("type") == "SPATIAL_CONTINUE" and row.get("b_anchor") != row.get("a_anchor"):
            errors.append(f"{n}→{n+1}: 같은 공간인데 B/A 앵커 문자열이 다름")
        if isinstance(n, int) and 1 <= n < count and len(route) == count:
            if route[n - 1].get("exit") != row.get("b_anchor"):
                errors.append(f"{n}→{n+1}: B 앵커가 앞 컷 도착점과 다름")
            if route[n].get("entry") != row.get("a_anchor"):
                errors.append(f"{n}→{n+1}: A 앵커가 다음 컷 출발점과 다름")

    if phase == "plan":
        return errors

    selected_path = episode / "04Q.선택영상_22컷.json"
    if not selected_path.is_file():
        return errors + ["게시 후보 영상 선택 목록 누락"]
    try:
        selected = _read(selected_path)
    except (OSError, ValueError) as exc:
        return errors + [f"게시 후보 영상 목록 읽기 실패: {exc}"]
    visuals = selected.get("visuals") or []
    if [row.get("n") for row in visuals] != list(range(1, count + 1)):
        errors.append("게시 후보가 연속 1..N 컷과 일치하지 않음")
    for row in visuals:
        n = row.get("n")
        source = str(row.get("source") or "")
        kind = str(row.get("source_kind") or "")
        if any(marker in source.lower() for marker in LOCAL_MARKERS):
            errors.append(f"컷 {n}: LOCAL_GRAPHIC_IN_MASTER ({source})")
        if kind not in FLOW_KINDS:
            errors.append(f"컷 {n}: 검증된 Flow/VEO 출처 종류 누락 ({kind or '미기록'})")
        for key in ("flow_result_id", "a_file", "b_file", "a_asset_id", "b_asset_id", "a_sha256", "b_sha256", "video_sha256"):
            if not str(row.get(key) or "").strip():
                errors.append(f"컷 {n}: 영상 출처 {key} 누락")
        if source:
            media = (episode / source).resolve()
            if not media.is_file():
                errors.append(f"컷 {n}: 선택 원본 파일 없음 ({source})")
            elif row.get("video_sha256"):
                actual = _sha256(media)
                if actual.lower() != str(row["video_sha256"]).lower():
                    errors.append(f"컷 {n}: 선택 영상 SHA가 실제 파일과 다름")
        a_file = str(row.get("a_file") or "")
        b_file = str(row.get("b_file") or "")
        if a_file and b_file:
            a_path, b_path = (episode / a_file).resolve(), (episode / b_file).resolve()
            if not a_path.is_file() or not b_path.is_file():
                errors.append(f"컷 {n}: 실제 A/B 이미지 파일 누락")
            elif _sha256(a_path) == _sha256(b_path):
                errors.append(f"컷 {n}: 동일 A/A 이미지는 연속 탐방 후보 아님")
            else:
                if row.get("a_sha256") and _sha256(a_path).lower() != str(row["a_sha256"]).lower():
                    errors.append(f"컷 {n}: A 이미지 SHA 불일치")
                if row.get("b_sha256") and _sha256(b_path).lower() != str(row["b_sha256"]).lower():
                    errors.append(f"컷 {n}: B 이미지 SHA 불일치")
        if isinstance(n, int) and 1 <= n <= count:
            if a_file != f"images_shared/F{n:03d}.png" or b_file != f"images_shared/F{n+1:03d}.png":
                errors.append(f"컷 {n}: F{n:03d}+F{n+1:03d} 정확한 공유 프레임 쌍 아님")
    if len(visuals) == count:
        for left, right in zip(visuals, visuals[1:]):
            n = left.get("n")
            if left.get("b_file") != right.get("a_file"):
                errors.append(f"{n}→{n+1}: 동일 공유 이미지 파일 아님")
            if left.get("b_sha256") != right.get("a_sha256"):
                errors.append(f"{n}→{n+1}: 동일 공유 이미지 SHA 아님")
            if left.get("b_asset_id") != right.get("a_asset_id"):
                errors.append(f"{n}→{n+1}: 동일 Flow 이미지 자산 ID 아님")

    if phase == "release":
        review_path = episode / "04R.연속탐방_실영상검수.json"
        if not review_path.is_file():
            return errors + ["원본 전체·21개 경계 실제 재생 검수 누락"]
        try:
            review = _read(review_path)
        except (OSError, ValueError) as exc:
            return errors + [f"실영상 검수 읽기 실패: {exc}"]
        if review.get("status") != "PASS":
            errors.append("실영상 검수 PASS 아님")
        rows = review.get("scenes") or []
        boundaries = review.get("boundaries") or []
        if [row.get("n") for row in rows] != list(range(1, count + 1)):
            errors.append("원본 전체 재생 검수가 N개 모두 없음")
        if [row.get("after") for row in boundaries] != list(range(1, count)):
            errors.append("컷 경계 실제 재생 검수가 N-1개 모두 없음")
        for row in rows:
            if row.get("status") != "PASS" or row.get("full_clip_played") is not True:
                errors.append(f"컷 {row.get('n')}: 원본 전체 동작 검수 PASS 아님")
        for row in boundaries:
            if row.get("status") != "PASS" or row.get("last_first_second_played") is not True:
                errors.append(f"{row.get('after')}→{row.get('after', 0)+1}: 경계 재생 검수 PASS 아님")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="연속 탐방·Flow/VEO 출처 읽기 전용 검문")
    parser.add_argument("episode", type=Path)
    parser.add_argument("--phase", choices=("plan", "selection", "release"), default="selection")
    args = parser.parse_args()
    errors = validate(args.episode, args.phase)
    for error in errors:
        print("FAIL", error)
    if not errors:
        print(f"STRUCTURAL_PASS phase={args.phase}; 영상미 실제 재생 검수는 별도")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
