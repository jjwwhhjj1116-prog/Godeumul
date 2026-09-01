#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""실물 유물 디오라마·Flow 참조·형태 QA를 게시 단계까지 강제한다."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


REFERENCE_LOCK_NAME = "02e.FLOW유물참조잠금.json"
FLOW_BINDING_NAME = "04.FLOW참조첨부기록.json"
FORM_QA_NAME = "04.유물형태키프레임검수.json"
PASS_STATES = {"PASS", "ARTIFACT_FORM_PASS"}


@dataclass
class ArtifactGateReport:
    failures: list[str]
    details: dict

    @property
    def passed(self) -> bool:
        return not self.failures


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _read_json(path: Path, failures: list[str], label: str) -> dict:
    if not path.exists():
        failures.append(f"{label} 없음: {path.name}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"{label} JSON 오류: {exc}")
        return {}
    if not isinstance(value, dict):
        failures.append(f"{label}은 JSON 객체여야 함")
        return {}
    return value


def identifiable_scenes(episode: Path) -> list[int]:
    routing_path = episode / "02d.유물장면라우팅.json"
    if not routing_path.exists():
        return []
    try:
        routing = json.loads(routing_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rows = routing.get("scenes") if isinstance(routing, dict) else None
    if not isinstance(rows, dict):
        return []
    result: list[int] = []
    for raw_scene, row in rows.items():
        if not isinstance(row, dict):
            continue
        if str(row.get("artifact_visibility") or "").upper() == "IDENTIFIABLE":
            try:
                result.append(int(raw_scene))
            except (TypeError, ValueError):
                continue
    return sorted(result)


def validate_reference_lock(episode: Path) -> ArtifactGateReport:
    """이미지 프롬프트 전에 실물→동일형태 디오라마→Flow 자산 잠금을 검증한다."""
    failures: list[str] = []
    manifest = _read_json(episode / "02c.유물레퍼런스.json", failures, "실물 유물 레퍼런스")
    lock = _read_json(episode / REFERENCE_LOCK_NAME, failures, "Flow 유물 참조 잠금")
    if not manifest or not lock:
        return ArtifactGateReport(failures, {"manifest": manifest, "lock": lock})

    artifact_name = str(manifest.get("artifact_name_ko") or "").strip()
    failures.extend([] if artifact_name else ["02c artifact_name_ko 누락"])
    if lock.get("version") != 1:
        failures.append("02e.FLOW유물참조잠금.json version은 1이어야 함")
    if str(lock.get("artifact_name_ko") or "").strip() != artifact_name:
        failures.append("02e 유물명이 02c artifact_name_ko와 정확히 일치하지 않음")
    if str(lock.get("prompt_anchor") or "").strip() != artifact_name:
        failures.append("prompt_anchor는 정확한 한글 유물명과 같아야 함")

    approved = lock.get("approved_diorama") or {}
    if not isinstance(approved, dict):
        approved = {}
    relative = str(approved.get("file") or "").strip()
    expected_hash = str(approved.get("sha256") or "").strip().upper()
    diorama_path = episode / relative if relative else episode / "__missing__"
    if str(approved.get("shape_identity_review") or "").upper() != "PASS":
        failures.append("실물 사진과 디오라마의 생김새 동일성 검수가 PASS가 아님")
    derived = approved.get("derived_from_reference_ids") or []
    if not isinstance(derived, list) or not derived:
        failures.append("디오라마가 어느 실물 형태 소유자에서 파생됐는지 누락")
    if not relative or not diorama_path.exists():
        failures.append(f"승인 디오라마 파일 없음: {relative or 'file 누락'}")
    elif not expected_hash or sha256_file(diorama_path) != expected_hash:
        failures.append("승인 디오라마 SHA-256 불일치")

    flow_reference = lock.get("flow_reference") or {}
    if not isinstance(flow_reference, dict):
        flow_reference = {}
    asset_name = str(flow_reference.get("asset_name") or "").strip()
    prompt_token = str(flow_reference.get("prompt_token") or "").strip()
    binding = str(flow_reference.get("preferred_binding") or "").strip().upper()
    if asset_name != artifact_name:
        failures.append("Flow 참조 자산명은 정확한 한글 유물명과 같아야 함")
    if prompt_token != f"@{artifact_name}":
        failures.append(f"Flow 프롬프트 토큰은 @{artifact_name} 이어야 함")
    if binding not in {
        "INGREDIENT", "CHARACTER", "INGREDIENT_AND_CHARACTER",
        "START_FRAME", "START_END_FRAME", "INGREDIENT_AND_START_END_FRAME",
    }:
        failures.append("Flow 참조 방식은 애셋/캐릭터 또는 승인된 시작·종료 프레임이어야 함")

    details = {
        "artifact_name_ko": artifact_name,
        "prompt_token": prompt_token,
        "diorama_file": relative,
        "diorama_sha256": expected_hash,
        "preferred_binding": binding,
        "lock": lock,
    }
    return ArtifactGateReport(failures, details)


def validate_artifact_release_gate(episode: Path) -> ArtifactGateReport:
    """식별 유물이 있는 회차는 실제 Flow 첨부 기록과 형태 QA까지 PASS여야 한다."""
    scenes = identifiable_scenes(episode)
    if not scenes:
        return ArtifactGateReport([], {"applicable": False, "identifiable_scenes": []})

    reference = validate_reference_lock(episode)
    failures = list(reference.failures)
    binding = _read_json(episode / FLOW_BINDING_NAME, failures, "Flow 참조 첨부 기록")
    qa = _read_json(episode / FORM_QA_NAME, failures, "유물 형태 키프레임 검수")

    artifact_name = str(reference.details.get("artifact_name_ko") or "")
    diorama_hash = str(reference.details.get("diorama_sha256") or "").upper()
    if binding:
        if binding.get("version") != 1:
            failures.append("04.FLOW참조첨부기록.json version은 1이어야 함")
        if str(binding.get("artifact_name_ko") or "").strip() != artifact_name:
            failures.append("Flow 참조 첨부 기록의 유물명이 참조 잠금과 다름")
        if str(binding.get("asset_name") or "").strip() != artifact_name:
            failures.append("Flow에 첨부한 자산명이 정확한 한글 유물명과 다름")
        if str(binding.get("diorama_sha256") or "").strip().upper() != diorama_hash:
            failures.append("Flow에 첨부한 참조 이미지 SHA가 승인 디오라마와 다름")
        project_id = str(binding.get("flow_project_id") or "").strip()
        if not project_id:
            failures.append("Flow 프로젝트 ID 누락")
        rows = binding.get("scenes") or {}
        if not isinstance(rows, dict):
            rows = {}
        for scene in scenes:
            row = rows.get(str(scene)) or {}
            if not isinstance(row, dict) or row.get("attached") is not True:
                failures.append(f"장면 {scene:03d}: Flow 참조 자산 실제 첨부 확인 누락")
                continue
            if str(row.get("asset_name") or "").strip() != artifact_name:
                failures.append(f"장면 {scene:03d}: 잘못된 Flow 참조 자산명")
            if str(row.get("binding") or "").strip().upper() not in {
                "INGREDIENT", "CHARACTER", "INGREDIENT_AND_CHARACTER",
                "START_FRAME", "START_END_FRAME", "INGREDIENT_AND_START_END_FRAME",
            }:
                failures.append(f"장면 {scene:03d}: Flow 참조 첨부 방식 누락")

    if qa:
        if str(qa.get("overall_status") or "").upper() not in PASS_STATES:
            failures.append(f"유물 형태 전체 QA가 PASS가 아님: {qa.get('overall_status')}")
        rows = qa.get("scenes") or []
        by_scene = {
            int(row.get("scene")): row for row in rows
            if isinstance(row, dict) and str(row.get("scene") or "").isdigit()
        }
        for scene in scenes:
            row = by_scene.get(scene)
            if not row:
                failures.append(f"장면 {scene:03d}: 유물 형태 10/50/90% QA 누락")
            elif str(row.get("status") or "").upper() not in PASS_STATES:
                failures.append(f"장면 {scene:03d}: 유물 형태 QA FAIL")

    return ArtifactGateReport(failures, {
        "applicable": True,
        "identifiable_scenes": scenes,
        "reference": reference.details,
        "binding": binding,
        "qa": qa,
    })
