#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""고대유물의 비밀 2단계 검수 — 장면 구조·고증·프롬프트 검증기.

검사 범위
  A 장면 구조      번호 연속, 대본·이미지·영상 1:1, 증거 상태
  B 시간            생성 길이 4/6/8/10초, TTS보다 짧지 않음
  C 고증            고증 카드의 문명·인물·건축·금지어·네거티브
  D 하이브리드      식별 유물 I2V·비식별 맥락 T2V 라우팅·실물 형태 소유자
  E 생성 안정성     9:16, 이미지 문자 금지, I2V 시작 이미지 보존·T2V 유물 배제
  F 카메라 경로     디오라마 스케일, 진입점·경로·도착점, 속도 곡선, 깊이 전환

사용법
  python tools/prompt_check.py 산출물/EP01_진시황릉
  python tools/prompt_check.py 산출물/EP01_진시황릉 -v
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import _config  # noqa: F401  # Windows 콘솔 UTF-8 설정


ALLOWED_SECONDS = {4, 6, 8, 10}
GENERATION_MODES = {"I2V_LOCKED", "T2V_CONTEXT"}
ARTIFACT_VISIBILITIES = {"IDENTIFIABLE", "NON_IDENTIFIABLE", "NONE"}
T2V_ALLOWED_SCENE_TYPES = {
    "DISCOVERY_ACTION", "EXCAVATION", "HISTORICAL_RECONSTRUCTION",
    "SITE_ESTABLISH", "CONSERVATION",
}
ARTIFACT_FORM_POLICY = "SOURCE_PHOTO_GEOMETRY_LOCK"
ARTIFACT_REFERENCE_FILE = "02c.유물레퍼런스.json"
EVIDENCE_STATES = {"발굴확인", "측정확인", "문헌기록", "학술해석", "미확인"}
MOTION_OWNERS = {"GENERATED_PHYSICS", "VEO_INTEGRATED_3D", "INFO_OVERLAY", "NONE"}
MOTION_SPACES = {"WORLD_3D", "SURFACE_2_5D", "SCREEN_INFO", "NONE"}
VEO_GRAPHIC_FUNCTIONS = {
    "ROUTE_PATH", "AIRFLOW_STREAM", "MATERIAL_FLOW", "FORCE_PATH",
    "DIMENSION_LINE", "SCAN_WAVE", "SECTION_REVEAL", "EXPLODED_SEQUENCE",
    "DANGER_ZONE",
}
VEO_GRAPHIC_FIELDS = {
    "function", "evidence_relation", "visual_language", "start", "via", "end",
    "occlusion", "timing", "camera_relation", "arrival_reaction",
}
VISUAL_LOCK_FIELDS = {
    "civilization", "era", "region", "source_reference", "site_artifact_fingerprint",
    "people_lock", "forbidden_culture", "diorama_style",
    "material_fidelity",
}
TTS_BEAT_FIELDS = {"start", "end", "narration", "camera", "action", "graphic"}
VISUAL_STATE_FIELDS = {"time", "composition", "camera_pose", "visible_anchors"}
VISUAL_STATE_COUNTS = {4: 2, 6: 3, 8: 3, 10: 4}
CAMERA_PATH_FIELDS = {
    "entry_anchor", "route", "destination", "speed_profile", "operator_style",
    "depth_transition", "pattern_interrupts", "settle_point",
}
CAMERA_PATH_COMMON_V6_FIELDS = {"single_axis", "scale_domain", "end_state"}
CAMERA_PATH_I2V_FIELDS = {"start_frame_anchor_visible", "start_frame_anchor_evidence"}
CAMERA_AXES = {"FORWARD", "LATERAL", "ORBIT", "LOCKED"}
SCALE_DOMAINS = {"WIDE", "MEDIUM", "MACRO"}
SPEED_PROFILES = {
    "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE",
    "CONTROLLED_ORBIT_REVEAL", "MACRO_PROBE_SETTLE", "EVIDENCE_HOLD",
    "BOUNDARY_APPROACH_STOP", "SLOW_OBSERVATIONAL_EXCEPTION",
}
OPERATOR_STYLES = {
    "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "IMMERSIVE_POV_DOLLY",
    "MACRO_PROBE", "CRANE_ORBIT_REVEAL", "LOCKED_EVIDENCE_CAMERA",
}
DEPTH_TRANSITIONS = {
    "DOOR_ENTRY", "SECTION_DIVE", "SURFACE_TO_INTERIOR", "ORBIT_REVEAL",
    "BOUNDARY_STOP", "NONE",
}
DYNAMIC_SCENE_TYPES = {
    "DISCOVERY_ACTION", "DISCOVERY_REVEAL", "EXCAVATION",
    "HISTORICAL_RECONSTRUCTION", "SPATIAL_MAP", "CUTAWAY", "EXPLODED", "MECHANISM",
}
SCENE_TYPES = {
    "DISCOVERY_ACTION", "DISCOVERY_REVEAL", "SITE_ESTABLISH", "EXCAVATION",
    "ARTIFACT_MACRO", "INVENTORY_TABLEAU", "HISTORICAL_RECONSTRUCTION",
    "SPATIAL_MAP", "CUTAWAY", "TEXT_RECORD", "SCIENTIFIC_EVIDENCE",
    "CONSERVATION", "SEALED_UNKNOWN", "DIAGRAM", "EXPLODED", "MECHANISM",
}

PEOPLE_HINT = re.compile(
    r"\b(figures?|farmers?|excavators?|archaeologists?|laborers?|labourers?|"
    r"workers?|artisans?|masons?|soldiers?|guards?|officials?|priests?|"
    r"crowd|people|men|women|hands?)\b", re.I)
ARCH_HINT = re.compile(
    r"\b(palace|town|city|temple|building|roofs?|courtyards?|hall|walls?|"
    r"gate|tower|mausoleum|tomb complex)\b", re.I)


class Report:
    def __init__(self) -> None:
        self.rows: list[tuple[bool, int, str, str]] = []

    def add(self, ok: bool, scene: int, item: str, detail: str = "") -> None:
        self.rows.append((ok, scene, item, detail))

    @property
    def fails(self) -> list[tuple[bool, int, str, str]]:
        return [row for row in self.rows if not row[0]]


def compact(value: str) -> str:
    return " ".join(value.split())


def section(text: str, heading: str) -> str:
    match = re.search(
        rf"^##+\s+[^\n]*{re.escape(heading)}[^\n]*\n(.*?)(?=^##+\s|\Z)",
        text,
        re.M | re.S,
    )
    return match.group(1) if match else ""


def first_code_block(text: str) -> str:
    match = re.search(r"```(?:text)?\s*\n(.*?)\n```", text, re.S | re.I)
    return compact(match.group(1)) if match else ""


def anchor_head(text: str, words: int) -> str:
    tokens = re.findall(r"[A-Za-z0-9-]+", text)
    return " ".join(tokens[:words]).lower()


def load_card(episode: Path) -> dict[str, object]:
    path = episode / "02b.고증카드.md"
    if not path.exists():
        sys.exit(f"[에러] 고증 카드가 없습니다: {path}")

    text = path.read_text(encoding="utf-8")
    civ = first_code_block(section(text, "문명"))
    modern_civ = first_code_block(section(text, "현대 현장"))
    people = first_code_block(section(text, "인물"))
    modern_people = first_code_block(section(text, "현대 인물"))
    architecture = first_code_block(section(text, "건축"))
    negative = first_code_block(section(text, "네거티브"))
    if not civ:
        sys.exit(f"[에러] 고증 카드의 '문명' 절에 영문 코드 블록이 없습니다: {path}")

    banned: list[str] = []
    people_section = section(text, "인물")
    banned_line = re.search(r"금지어[^:：]*[:：]\s*([^\n]+)", people_section, re.I)
    if banned_line:
        raw = re.sub(r"[`*.]", "", banned_line.group(1))
        banned = [word.strip().lower() for word in raw.split(",") if word.strip()]

    negative_clauses = [part.strip().lower() for part in negative.split(",") if part.strip()]
    return {
        "civ": civ,
        "civ_head": anchor_head(civ.split(",")[0], 2),
        "modern_civ": modern_civ,
        "modern_civ_head": anchor_head(modern_civ, 5) if modern_civ else "",
        "people": people,
        "people_head": anchor_head(people, 3),
        "modern_people": modern_people,
        "modern_people_head": anchor_head(modern_people, 6) if modern_people else "",
        "architecture": architecture,
        "architecture_head": anchor_head(architecture, 2),
        "banned": banned,
        "negative": negative,
        "negative_heads": negative_clauses[:2],
    }


def selected_image(scene: dict, requested: str | None) -> str:
    if requested:
        return str(scene.get(requested, ""))
    return str(scene.get("img_v2") or scene.get("img") or "")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_artifact_manifest(episode: Path) -> tuple[Path, dict[str, object], dict[str, dict]]:
    path = episode / ARTIFACT_REFERENCE_FILE
    if not path.exists():
        return path, {}, {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return path, {}, {}
    if not isinstance(data, dict):
        return path, {}, {}
    references = data.get("references") or []
    by_id = {
        str(item.get("id")): item
        for item in references
        if isinstance(item, dict) and str(item.get("id") or "").strip()
    }
    return path, data, by_id


def scene_number(value: object, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def main() -> int:
    parser = argparse.ArgumentParser(description="장면 구조·고증·프롬프트 검증")
    parser.add_argument("episode", type=Path)
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--필드", dest="field", default=None,
                        help="검사할 이미지 필드(기본: img_v2 우선, 없으면 img)")
    args = parser.parse_args()

    episode = args.episode.resolve()
    # 공개 완료 회차는 당시 프롬프트를 감사 기록으로 보존한다. 카메라 경로 v5 정책은
    # 아직 업로드되지 않은 신규 회차에 강제한다.
    released_episode = (episode / "07.업로드결과.json").exists()
    card = load_card(episode)
    scene_path = episode / "02a.장면구분.json"
    if not scene_path.exists():
        sys.exit(f"[에러] 장면표가 없습니다: {scene_path}")
    scenes = json.loads(scene_path.read_text(encoding="utf-8"))
    if not isinstance(scenes, list) or not scenes:
        sys.exit(f"[에러] 장면표가 빈 배열이거나 형식이 잘못됐습니다: {scene_path}")

    report = Report()
    manifest_path, artifact_manifest, artifact_references = load_artifact_manifest(episode)
    print(f"\n에피소드 : {episode.name}")
    print(f"문명 앵커 : {card['civ']}")
    print(f"장면      : {len(scenes)}개\n")

    numbers = [scene_number(scene.get("n"), index) for index, scene in enumerate(scenes, 1)]
    expected = list(range(1, len(scenes) + 1))
    report.add(numbers == expected, 0, "장면 번호 연속",
               "" if numbers == expected else f"현재 {numbers} / 기대 {expected}")

    for index, scene_data in enumerate(scenes, 1):
        n = scene_number(scene_data.get("n"), index)
        image = selected_image(scene_data, args.field)
        video = str(scene_data.get("vid") or "")
        narration = str(scene_data.get("txt") or "").strip()
        evidence = str(scene_data.get("evidence") or scene_data.get("증거상태") or "").strip()
        motion_raw = scene_data.get("motion_owner") or scene_data.get("모션소유권") or ""
        if isinstance(motion_raw, list):
            motion_owners = [str(value).strip().upper() for value in motion_raw if str(value).strip()]
        else:
            motion_owners = [value.strip().upper() for value in re.split(r"[+,|]", str(motion_raw)) if value.strip()]
        motion_space_raw = scene_data.get("motion_space") or scene_data.get("모션공간") or ""
        if isinstance(motion_space_raw, list):
            motion_spaces = [str(value).strip().upper() for value in motion_space_raw if str(value).strip()]
        else:
            motion_spaces = [value.strip().upper() for value in re.split(r"[+,|]", str(motion_space_raw)) if value.strip()]
        scene_type = str(scene_data.get("ct") or scene_data.get("type") or "").strip()
        generation_mode = str(
            scene_data.get("generation_mode") or scene_data.get("생성방식") or ""
        ).strip().upper()
        artifact_visibility = str(
            scene_data.get("artifact_visibility") or scene_data.get("유물가시성") or ""
        ).strip().upper()
        low = image.lower()

        # A. 한 장면 1:1 구조
        report.add(bool(narration), n, "나레이션 1개", "" if narration else "txt 없음")
        report.add(bool(image), n, "이미지 프롬프트 1개", "" if image else "img/img_v2 없음")
        report.add(bool(video), n, "영상 프롬프트 1개", "" if video else "vid 없음")
        report.add(evidence in EVIDENCE_STATES, n, "증거 상태",
                   "" if evidence in EVIDENCE_STATES else f"'{evidence or '없음'}'")
        motion_ok = bool(motion_owners) and all(value in MOTION_OWNERS for value in motion_owners)
        report.add(motion_ok, n, "모션 소유권",
                   "" if motion_ok else f"'{motion_raw or '없음'}'")
        motion_space_ok = bool(motion_spaces) and all(value in MOTION_SPACES for value in motion_spaces)
        report.add(motion_space_ok, n, "모션 공간",
                   "" if motion_space_ok else f"'{motion_space_raw or '없음'}'")
        if "VEO_INTEGRATED_3D" in motion_owners:
            veo_space_ok = any(value in {"WORLD_3D", "SURFACE_2_5D"} for value in motion_spaces)
            report.add(veo_space_ok, n, "Veo 통합 3D 공간",
                       "VEO_INTEGRATED_3D는 WORLD_3D 또는 SURFACE_2_5D 필요")
            veo_graphic = scene_data.get("veo_graphic") or scene_data.get("Veo통합그래픽") or {}
            graphic_is_dict = isinstance(veo_graphic, dict)
            report.add(graphic_is_dict, n, "Veo 그래픽 분석", "veo_graphic 객체 필요")
            if graphic_is_dict:
                missing = sorted(VEO_GRAPHIC_FIELDS - set(veo_graphic))
                report.add(not missing, n, "Veo 그래픽 필수 필드",
                           "" if not missing else f"누락: {', '.join(missing)}")
                function = str(veo_graphic.get("function") or "").strip().upper()
                report.add(function in VEO_GRAPHIC_FUNCTIONS, n, "Veo 그래픽 기능",
                           "" if function in VEO_GRAPHIC_FUNCTIONS else function or "없음")
                via = veo_graphic.get("via")
                report.add(isinstance(via, list) and bool(via), n, "Veo 경유 앵커",
                           "via는 1개 이상의 배열이어야 함")
                evidence_relation = str(veo_graphic.get("evidence_relation") or "").strip()
                visual_language = str(veo_graphic.get("visual_language") or "").strip()
                report.add(bool(evidence_relation), n, "Veo 증거 관계",
                           "evidence_relation에 시각화 근거·범위 필요")
                report.add(bool(visual_language), n, "Veo 시각 언어",
                           "visual_language에 장면 맞춤 형태·재질·색 필요")
                if function == "ROUTE_PATH":
                    report.add(any(word in video.lower() for word in ("route", "path", "ribbon")),
                               n, "3D 경로 프롬프트",
                               "video prompt에 route/path/ribbon 중 하나 필요")
                if function == "DANGER_ZONE":
                    report.add(any(word in video.lower() for word in ("danger", "warning", "hazard")),
                               n, "위험 그래픽 의미",
                               "DANGER_ZONE은 danger/warning/hazard 의미가 필요")
            video_low = video.lower()
            report.add("single continuous" in video_low, n, "Veo 연속 촬영",
                       "single continuous shot 필요")
            world_anchor_ok = any(term in video_low for term in (
                "physical world", "world space", "anchored to", "anchored in",
            ))
            report.add(world_anchor_ok, n, "Veo 월드 고정",
                       "physical world/world space/anchored 표현 필요")
            report.add("no floating hud" in video_low and "no text" in video_low, n,
                       "Veo HUD·문자 금지", "no floating HUD + no text 필요")
        if motion_owners == ["NONE"]:
            report.add(motion_spaces == ["NONE"], n, "무모션 공간",
                       "모션 소유권 NONE이면 모션 공간도 NONE")
        report.add(scene_type in SCENE_TYPES, n, "장면 유형",
                   "" if scene_type in SCENE_TYPES else f"'{scene_type or '없음'}'")

        # A-1. I2V·T2V 하이브리드 라우팅과 실물 형태 소유자
        report.add(generation_mode in GENERATION_MODES, n, "하이브리드 생성 방식",
                   "generation_mode은 I2V_LOCKED 또는 T2V_CONTEXT")
        report.add(artifact_visibility in ARTIFACT_VISIBILITIES, n, "유물 가시성",
                   "artifact_visibility는 IDENTIFIABLE/NON_IDENTIFIABLE/NONE")
        if generation_mode == "T2V_CONTEXT":
            report.add(scene_type in T2V_ALLOWED_SCENE_TYPES, n, "T2V 허용 장면 유형",
                       f"T2V_CONTEXT 허용: {sorted(T2V_ALLOWED_SCENE_TYPES)}")
            report.add(artifact_visibility in {"NON_IDENTIFIABLE", "NONE"}, n,
                       "T2V 주 유물 비식별",
                       "T2V_CONTEXT에서 주 유물을 식별 가능한 형태로 보여 줄 수 없음")
            t2v_ban = any(term in video.lower() for term in (
                "do not show the named hero artifact in identifiable form",
                "no identifiable hero artifact",
            ))
            report.add(t2v_ban, n, "T2V 주 유물 생성 금지",
                       "영상 프롬프트에 식별 가능한 주 유물 생성 금지 문구 필요")

        if artifact_visibility == "IDENTIFIABLE":
            report.add(generation_mode == "I2V_LOCKED", n, "식별 유물 I2V 잠금",
                       "IDENTIFIABLE 장면은 I2V_LOCKED만 허용")
            form_policy = str(scene_data.get("artifact_form_policy") or "").strip().upper()
            report.add(form_policy == ARTIFACT_FORM_POLICY, n, "실물 형태 정책",
                       f"artifact_form_policy는 {ARTIFACT_FORM_POLICY}")
            reference_ids = scene_data.get("artifact_reference_ids") or []
            references_ok = isinstance(reference_ids, list) and bool(reference_ids)
            report.add(references_ok, n, "유물 형태 레퍼런스",
                       "artifact_reference_ids는 1개 이상의 배열이어야 함")
            report.add(bool(artifact_manifest), n, "유물 레퍼런스 매니페스트",
                       f"{manifest_path.name} 필요")
            if references_ok and artifact_manifest:
                missing_ids = [rid for rid in reference_ids if str(rid) not in artifact_references]
                report.add(not missing_ids, n, "유물 레퍼런스 ID",
                           "" if not missing_ids else f"매니페스트에 없음: {missing_ids}")
                for reference_id in reference_ids:
                    reference = artifact_references.get(str(reference_id))
                    if not reference:
                        continue
                    relative_file = str(reference.get("file") or "").strip()
                    expected_hash = str(reference.get("sha256") or "").strip().upper()
                    reference_path = episode / relative_file
                    report.add(bool(relative_file) and reference_path.exists(), n,
                               f"형태 소유자 파일 {reference_id}",
                               relative_file or "file 누락")
                    if relative_file and reference_path.exists():
                        actual_hash = sha256_file(reference_path)
                        report.add(bool(expected_hash) and actual_hash == expected_hash, n,
                                   f"형태 소유자 SHA {reference_id}",
                                   "" if actual_hash == expected_hash else
                                   f"기대 {expected_hash or '없음'} / 실제 {actual_hash}")
            allowed_changes = scene_data.get("allowed_artifact_changes") or []
            forbidden_changes = scene_data.get("forbidden_artifact_changes") or []
            report.add(isinstance(allowed_changes, list) and "camera" in allowed_changes
                       and "lighting" in allowed_changes, n, "유물 허용 변화",
                       "allowed_artifact_changes에 camera와 lighting 필요")
            must_forbid = {"silhouette", "proportion", "part_count", "ornament_layout"}
            report.add(isinstance(forbidden_changes, list)
                       and must_forbid.issubset(set(forbidden_changes)), n, "유물 금지 변화",
                       "silhouette/proportion/part_count/ornament_layout 변경 금지 필요")

        # A-2. 신규 회차 카메라 경로 잠금
        camera_path = scene_data.get("camera_path") or scene_data.get("카메라경로") or {}
        camera_path_required = not released_episode
        camera_path_is_dict = isinstance(camera_path, dict) and bool(camera_path)
        if camera_path_required:
            report.add(camera_path_is_dict, n, "카메라 경로", "camera_path 객체 필요")
        if camera_path_is_dict:
            missing_camera = sorted(CAMERA_PATH_FIELDS - set(camera_path))
            report.add(not missing_camera, n, "카메라 경로 필수 필드",
                       "" if not missing_camera else f"누락: {', '.join(missing_camera)}")
            if camera_path_required:
                required_v6 = set(CAMERA_PATH_COMMON_V6_FIELDS)
                if generation_mode == "I2V_LOCKED":
                    required_v6.update(CAMERA_PATH_I2V_FIELDS)
                else:
                    required_v6.add("opening_state_evidence")
                missing_v6 = sorted(required_v6 - set(camera_path))
                report.add(not missing_v6, n, "카메라 연속성 v6 필드",
                           "" if not missing_v6 else f"누락: {', '.join(missing_v6)}")
                if generation_mode == "I2V_LOCKED":
                    anchor_visible = camera_path.get("start_frame_anchor_visible") is True
                    anchor_evidence = str(
                        camera_path.get("start_frame_anchor_evidence") or ""
                    ).strip()
                    report.add(anchor_visible and bool(anchor_evidence), n,
                               "실제 첫 프레임 앵커 확인",
                               "선택 이미지에서 보이는 위치·형태를 기록하고 visible=true 필요")
                else:
                    opening_evidence = str(camera_path.get("opening_state_evidence") or "").strip()
                    report.add(bool(opening_evidence), n, "T2V 첫 상태 증거",
                               "opening_state_evidence에 첫 구도·시대 앵커 필요")
                single_axis = str(camera_path.get("single_axis") or "").strip().upper()
                scale_domain = str(camera_path.get("scale_domain") or "").strip().upper()
                end_state = str(camera_path.get("end_state") or "").strip()
                report.add(single_axis in CAMERA_AXES, n, "단일 카메라 진행축",
                           "single_axis는 FORWARD/LATERAL/ORBIT/LOCKED 중 하나")
                report.add(scale_domain in SCALE_DOMAINS, n, "단일 화면 규모",
                           "scale_domain은 WIDE/MEDIUM/MACRO 중 하나")
                report.add(bool(end_state), n, "마지막 프레임 구도",
                           "end_state에 마지막 프레임의 고정 구도 필요")
            speed_profile = str(camera_path.get("speed_profile") or "").strip().upper()
            operator_style = str(camera_path.get("operator_style") or "").strip().upper()
            depth_transition = str(camera_path.get("depth_transition") or "").strip().upper()
            report.add(speed_profile in SPEED_PROFILES, n, "카메라 속도 곡선",
                       "" if speed_profile in SPEED_PROFILES else speed_profile or "없음")
            if camera_path_required:
                report.add(speed_profile != "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", n,
                           "신규 장면 방향 반전 속도곡선 금지",
                           "같은 진행축의 속도 펄스·전경 가림으로 바꾸거나 장면 분할")
            report.add(operator_style in OPERATOR_STYLES, n, "카메라 운용 방식",
                       "" if operator_style in OPERATOR_STYLES else operator_style or "없음")
            report.add(depth_transition in DEPTH_TRANSITIONS, n, "깊이 전환",
                       "" if depth_transition in DEPTH_TRANSITIONS else depth_transition or "없음")
            for field in ("entry_anchor", "route", "destination", "settle_point"):
                report.add(bool(str(camera_path.get(field) or "").strip()), n,
                           f"카메라 {field}", f"{field}가 비어 있음")
            interrupts = camera_path.get("pattern_interrupts")
            minimum_interrupts = 2 if int(scene_data.get("omni") or 0) >= 10 else 1
            exception = speed_profile in {"EVIDENCE_HOLD", "SLOW_OBSERVATIONAL_EXCEPTION"}
            interrupts_ok = (
                isinstance(interrupts, list)
                and (exception or len(interrupts) >= minimum_interrupts)
            )
            report.add(interrupts_ok, n, "패턴 인터럽트",
                       f"동적 {scene_data.get('omni')}초 장면은 최소 {minimum_interrupts}개 필요")

            if scene_type in DYNAMIC_SCENE_TYPES:
                dynamic_speed_ok = speed_profile not in {
                    "EVIDENCE_HOLD", "SLOW_OBSERVATIONAL_EXCEPTION"
                }
                report.add(dynamic_speed_ok, n, "동적 장면 즉시 이동",
                           "발견·진입·단면 장면은 느린 관찰 예외를 사용할 수 없음")
            if scene_type in {"DISCOVERY_REVEAL", "CUTAWAY"}:
                report.add(depth_transition in {"SECTION_DIVE", "SURFACE_TO_INTERIOR"}, n,
                           "단면 깊이 전환",
                           "DISCOVERY_REVEAL/CUTAWAY는 SECTION_DIVE 또는 SURFACE_TO_INTERIOR 필요")
            if scene_type == "SEALED_UNKNOWN":
                report.add(depth_transition in {"BOUNDARY_STOP", "NONE"}, n,
                           "미확인 경계 보존",
                           "SEALED_UNKNOWN은 문 개방·단면 진입 금지")

        # A-3. 시각 고증 잠금·TTS 비트

        visual_lock = scene_data.get("visual_lock") or scene_data.get("시각잠금") or {}
        visual_lock_is_dict = isinstance(visual_lock, dict)
        report.add(visual_lock_is_dict, n, "시각 고증 잠금", "visual_lock 객체 필요")
        if visual_lock_is_dict:
            missing_lock = sorted(VISUAL_LOCK_FIELDS - set(visual_lock))
            report.add(not missing_lock, n, "시각 잠금 필수 필드",
                       "" if not missing_lock else f"누락: {', '.join(missing_lock)}")
            fingerprints = visual_lock.get("site_artifact_fingerprint")
            report.add(isinstance(fingerprints, list) and len(fingerprints) >= 3, n,
                       "대상 고유 지문", "site_artifact_fingerprint는 3개 이상의 배열이어야 함")
            forbidden = visual_lock.get("forbidden_culture")
            report.add(isinstance(forbidden, list) and bool(forbidden), n,
                       "금지 문화권", "forbidden_culture는 1개 이상의 배열이어야 함")
            style = str(visual_lock.get("diorama_style") or "").strip().upper()
            report.add(style == "CINEMATIC_ARCHAEOLOGICAL_DIORAMA", n,
                       "3D 디오라마 스타일",
                       "diorama_style은 CINEMATIC_ARCHAEOLOGICAL_DIORAMA여야 함")
            material_fidelity = str(visual_lock.get("material_fidelity") or "").strip().upper()
            report.add(material_fidelity == "PBR_MICROTEXTURE_HIGH_FIDELITY", n,
                       "PBR 미세 재질 품질",
                       "material_fidelity는 PBR_MICROTEXTURE_HIGH_FIDELITY여야 함")

        report.add("diorama" in low and "archaeological" in low, n,
                   "이미지 3D 디오라마",
                   "image prompt에 archaeological + diorama 필요")
        pbr_terms = ("physically based", "pbr", "microtexture", "micro-texture",
                     "micro-displacement", "high-frequency texture", "high fidelity")
        report.add(sum(term in low for term in pbr_terms) >= 2, n,
                   "이미지 미세 재질 지시",
                   "PBR/physically based + microtexture/high fidelity 계열 표현 2개 이상 필요")
        if camera_path_required:
            miniature_terms = (
                "museum-scale", "crafted miniature", "miniature world", "macro-lens",
                "tilt-shift", "handcrafted terrain", "crafted physical",
            )
            report.add(sum(term in low for term in miniature_terms) >= 2, n,
                       "디오라마 축소모형 단서",
                       "museum-scale/매크로 렌즈/선택적 틸트시프트/제작 가장자리 중 2개 이상 필요")
            report.add("not live-action" in low or "rather than live-action" in low, n,
                       "실사 오인 방지", "image prompt에 not live-action 필요")

        tts_beats = scene_data.get("tts_beats") or scene_data.get("TTS비트") or []
        beats_are_list = isinstance(tts_beats, list) and bool(tts_beats)
        report.add(beats_are_list, n, "TTS 비트", "tts_beats는 1개 이상의 배열이어야 함")
        if beats_are_list:
            malformed_beats = [
                beat_index for beat_index, beat in enumerate(tts_beats, 1)
                if not isinstance(beat, dict) or TTS_BEAT_FIELDS - set(beat)
            ]
            report.add(not malformed_beats, n, "TTS 비트 필수 필드",
                       "" if not malformed_beats else f"형식 오류 비트: {malformed_beats}")

        # B. TTS와 생성 길이
        duration = scene_data.get("omni")
        try:
            duration_number = int(duration)
        except (TypeError, ValueError):
            duration_number = -1
        report.add(duration_number in ALLOWED_SECONDS, n, "생성 길이",
                   "" if duration_number in ALLOWED_SECONDS else f"{duration!r}초")

        if camera_path_required and duration_number in ALLOWED_SECONDS:
            visual_states = scene_data.get("visual_states") or []
            expected_states = VISUAL_STATE_COUNTS[duration_number]
            states_are_list = isinstance(visual_states, list)
            report.add(states_are_list and len(visual_states) == expected_states, n,
                       "시간 상태표 개수",
                       f"{duration_number}초는 visual_states {expected_states}개 필요")
            if states_are_list and visual_states:
                malformed_states = [
                    state_index for state_index, state in enumerate(visual_states, 1)
                    if not isinstance(state, dict) or VISUAL_STATE_FIELDS - set(state)
                ]
                report.add(not malformed_states, n, "시간 상태표 필수 필드",
                           "" if not malformed_states
                           else f"형식 오류 상태: {malformed_states}")
                state_times: list[float] = []
                for state in visual_states:
                    try:
                        state_times.append(float(state.get("time")))
                    except (AttributeError, TypeError, ValueError):
                        state_times.append(-1.0)
                ordered = all(
                    current > previous
                    for previous, current in zip(state_times, state_times[1:])
                )
                endpoints = (
                    bool(state_times)
                    and abs(state_times[0]) <= 0.05
                    and abs(state_times[-1] - duration_number) <= 0.1
                )
                report.add(ordered and endpoints, n, "시간 상태표 시각",
                           "첫 상태는 0초, 마지막은 생성 길이, 중간은 오름차순이어야 함")
                anchors_present = all(
                    isinstance(state, dict)
                    and bool(str(state.get("composition") or "").strip())
                    and bool(str(state.get("camera_pose") or "").strip())
                    and isinstance(state.get("visible_anchors"), list)
                    and bool(state.get("visible_anchors"))
                    for state in visual_states
                )
                report.add(anchors_present, n, "시간 상태표 화면 앵커",
                           "각 상태에 composition/camera_pose/visible_anchors 필요")

        tts = scene_data.get("tts")
        try:
            tts_number = float(tts)
        except (TypeError, ValueError):
            tts_number = -1.0
        report.add(tts_number > 0, n, "TTS 실측", "" if tts_number > 0 else f"{tts!r}")
        if tts_number > 0 and duration_number in ALLOWED_SECONDS:
            try:
                playback_speed = float(scene_data.get("playback_speed") or 1.0)
            except (TypeError, ValueError):
                playback_speed = -1.0
            effective_duration = (
                duration_number / playback_speed if playback_speed > 0 else 0.0
            )
            duration_ok = (
                tts_number <= duration_number
                or (0.75 <= playback_speed < 1.0 and effective_duration + 0.02 >= tts_number)
            )
            report.add(duration_ok, n, "TTS≤생성 길이 또는 안전 저속 재생",
                       "" if duration_ok else
                       f"TTS {tts_number:.2f}초 > 생성 {duration_number}초, "
                       f"playback_speed {playback_speed:.4f}")
            long_review = str(scene_data.get("long_scene_review") or "").strip()
            report.add(tts_number <= 9.0 or bool(long_review), n, "장면 분할 검토",
                       "" if tts_number <= 9.0 or long_review
                       else f"TTS {tts_number:.2f}초 — 10초 연속 장면 유지 근거 필요")
        if beats_are_list:
            beat_ranges: list[tuple[float, float]] = []
            for beat in tts_beats:
                try:
                    beat_ranges.append((float(beat["start"]), float(beat["end"])))
                except (KeyError, TypeError, ValueError):
                    beat_ranges = []
                    break
            ranges_ok = bool(beat_ranges) and all(
                start >= 0 and end > start
                and (beat_index == 0 or abs(start - beat_ranges[beat_index - 1][1]) <= 0.15)
                for beat_index, (start, end) in enumerate(beat_ranges)
            )
            report.add(ranges_ok, n, "TTS 비트 시간 연속",
                       "비트는 0초부터 순서대로 이어지고 겹침·공백이 없어야 함")
            if beat_ranges and tts_number > 0:
                coverage_ok = abs(beat_ranges[0][0]) <= 0.05 and abs(beat_ranges[-1][1] - tts_number) <= 0.15
                report.add(coverage_ok, n, "TTS 비트 전체 구간",
                           "첫 비트 0초부터 마지막 비트가 실제 TTS 끝까지 덮어야 함")

        if not image:
            continue

        # 네거티브 문구에 들어간 사람 단어는 인물 탐지에서 제외한다.
        positive_scene = re.sub(r"\bno\s+[^,.;]+", "", image, flags=re.I)
        positive_low = positive_scene.lower()

        # C. 고증 카드 앵커
        modern_scene = bool(scene_data.get("modern_scene"))
        civ_head = (
            str(card["modern_civ_head"] or "present-day")
            if modern_scene else str(card["civ_head"])
        )
        report.add(bool(civ_head and civ_head in low), n, "문명 앵커",
                   "" if civ_head and civ_head in low else f"'{civ_head}' 없음")

        if PEOPLE_HINT.search(positive_scene):
            people_head = (
                str(card["modern_people_head"] or "east asian chinese")
                if modern_scene else str(card["people_head"])
            )
            report.add(bool(people_head and people_head in low), n, "인물 앵커",
                       "" if people_head and people_head in low else f"'{people_head}' 없음")

        # Modern site-establishing shots may mention a mausoleum or explicitly
        # forbid reconstructed buildings.  For newly built storyboards, trust
        # the explicit scene flag instead of inferring ancient architecture
        # from those words.  Legacy storyboards keep the heuristic fallback.
        architecture_required = scene_data.get("architecture_anchor_required")
        if architecture_required is None:
            architecture_required = bool(ARCH_HINT.search(positive_scene))
        if architecture_required:
            architecture_head = str(card["architecture_head"])
            report.add(bool(architecture_head and architecture_head in low), n, "건축 앵커",
                       "" if architecture_head and architecture_head in low
                       else f"'{architecture_head}' 없음")

        for banned_word in card["banned"]:
            if re.search(r"\b" + re.escape(str(banned_word)) + r"\b", positive_low):
                report.add(False, n, "고증 금지어", f"'{banned_word}'")

        required_negatives = list(card["negative_heads"])
        if modern_scene:
            required_negatives = [clause for clause in required_negatives if clause != "no modern clothing"]
            required_negatives.append("no ancient costume on modern researchers")
        missing_negative = [clause for clause in required_negatives if clause not in low]
        report.add(not missing_negative, n, "고증 네거티브",
                   "" if not missing_negative else f"누락: {missing_negative}")

        # D. 생성 안정성
        report.add("9:16" in image, n, "세로 규격", "" if "9:16" in image else "9:16 없음")
        no_generated_text = (
            "no text" in low and "no labels" in low and "no letters" in low
            and not re.search(r'reading\s+"[^"]+"', image, re.I)
        )
        report.add(bool(no_generated_text), n, "이미지 문자 금지",
                   "" if no_generated_text else "no text/no labels/no letters 누락 또는 생성 라벨 존재")

        video_low = video.lower()
        continuous = "continuous" in video_low and "no hard cut" in video_low
        report.add(continuous, n, "생성 영상 연속 촬영",
                   "" if continuous else "continuous와 no hard cut 지시 필요")
        if camera_path_required and duration_number >= 8:
            anchor_lock = all(term in video_low for term in (
                "start anchor", "mid anchor", "final anchor", "last frame",
            ))
            report.add(anchor_lock, n, "장시간 I2V 시작·중간·끝 잠금",
                       "8~10초는 start/mid/final anchor와 last frame 지시 필요")
            no_reset = all(term in video_low for term in (
                "no cut", "reset", "loop", "restart",
            )) and any(term in video_low for term in (
                "never return", "remain there", "remain on", "hold there",
            ))
            report.add(no_reset, n, "장시간 I2V 리셋·루프 금지",
                       "no cut/reset/loop/restart와 마지막 구도 유지 지시 필요")
        if camera_path_required:
            reversal_phrases = (
                "then pull back", "then pull out", "then retreat",
                "reverse direction", "then reverse", "rise then dive",
                "dive then rise", "orbit then enter", "impossible storage",
            )
            found_reversal = [phrase for phrase in reversal_phrases if phrase in video_low]
            report.add(not found_reversal, n, "카메라 방향·규모 반전 금지",
                       "" if not found_reversal else f"위험 문구: {found_reversal}")
        if generation_mode == "I2V_LOCKED":
            preserve = "no new object" in video_low or "preserve all object" in video_low
            report.add(preserve, n, "I2V 새 물체 금지",
                       "" if preserve else "no new objects 또는 preserve all objects 지시 필요")
            locked_start = (
                ("start image" in video_low or "supplied locked" in video_low)
                and "preserve" in video_low
            )
            report.add(locked_start, n, "I2V 시작 이미지 보존",
                       "start image/supplied locked + preserve 지시 필요")
            if artifact_visibility == "IDENTIFIABLE":
                rigid_lock = all(term in video_low for term in (
                    "exact supplied reference artifact", "completely rigid",
                    "no redesign", "no changed part count",
                ))
                report.add(rigid_lock, n, "식별 유물 강체 잠금",
                           "실물 형태 보존·강체·재설계/부품 수 변경 금지 문구 필요")
        elif generation_mode == "T2V_CONTEXT":
            t2v_declared = "t2v" in video_low or "text-to-video" in video_low
            report.add(t2v_declared, n, "T2V 명시", "T2V 또는 text-to-video 문구 필요")
        if camera_path_required:
            report.add("vlog" not in video_low and "influencer" not in video_low
                       and "selfie" not in video_low, n,
                       "현대 브이로그 구도 금지", "vlog/influencer/selfie 표현 제거")
        if camera_path_is_dict:
            depth_transition = str(camera_path.get("depth_transition") or "").strip().upper()
            if depth_transition == "DOOR_ENTRY":
                image_has_door_path = (
                    any(term in low for term in ("door", "gate", "doorway"))
                    and any(term in low for term in ("hinge", "threshold", "opening", "empty passage"))
                )
                report.add(image_has_door_path, n, "문 진입 시작 이미지",
                           "문·문틀과 hinge/threshold/opening/empty passage 중 하나가 이미지에 필요")
                report.add(any(term in video_low for term in ("opens", "swings", "rotates")), n,
                           "문 개방 물리", "문짝의 회전·개방 동작 필요")
            if depth_transition in {"SECTION_DIVE", "SURFACE_TO_INTERIOR"}:
                section_ready = any(term in low for term in (
                    "cutaway", "section", "strata", "cut face", "section seam",
                ))
                report.add(section_ready, n, "단면 진입 시작 이미지",
                           "cutaway/section/strata/cut face/section seam 중 하나가 이미지에 필요")

        if args.verbose:
            rows = [row for row in report.rows if row[1] == n]
            failures = [row for row in rows if not row[0]]
            mark = "OK " if not failures else "★  "
            print(f"  {mark}장면 {n:>3} {scene_type or '-':<26} 검사 {len(rows)}개"
                  + ("" if not failures else " → "
                     + "; ".join(f"{item}({detail})" for _, _, item, detail in failures)))

    failures = report.fails
    if not args.verbose:
        by_scene: dict[int, list[str]] = {}
        for _, n, item, detail in failures:
            by_scene.setdefault(n, []).append(item + (f" ({detail})" if detail else ""))
        for n in sorted(by_scene):
            label = "전체" if n == 0 else f"장면 {n:>3}"
            print(f"  ★ {label}  " + " · ".join(by_scene[n]))

    print(f"\n{'─' * 72}")
    print(f"검사 {len(report.rows)}건 · 통과 {len(report.rows) - len(failures)} · 실패 {len(failures)}")
    if failures:
        failed_scenes = {row[1] for row in failures if row[1] != 0}
        print(f"\n★ {len(failed_scenes)}개 장면이 FLOW 투입 조건을 통과하지 못했습니다.")
        print("  장면표·고증카드·이미지/I2V 프롬프트를 고친 뒤 다시 검사하세요.\n")
        return 1

    print("\n장면 구조·고증·생성 안정성 이상 없음. FLOW 투입 가능.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
