#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""CapCut 오디오 정책을 검수·교정한다.

채널 표준: 영상 원음 -15dB, TTS +5dB, 두 트랙 모두 음량
노멀라이제이션만 ON(-23 LUFS), 음성 보정·노이즈 제거·보컬 분리는 OFF.
전환, 자막 페이드, 줌 1, 반동 1 등 비오디오 소재는 보존한다.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import os
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


FORBIDDEN_AUDIO_PROCESSING_BUCKETS = (
    "audio_effects", "realtime_denoises", "vocal_beautifys", "vocal_separations",
)
LOUDNESS_BUCKET = "loudnesses"
PROCESSING_TASK_LISTS = (
    "enhance_voice_segid_list",
    "normalize_loudness_segid_list",
    "normalize_loudness_audio_denoise_segid_list",
)
COMPANION_NAMES = ("draft_content.json.bak", "template-2.tmp")
DEFAULT_VIDEO_DB = -15.0
DEFAULT_NARRATION_DB = 5.0
DEFAULT_TARGET_LUFS = -23.0


for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def db_to_linear(db: float) -> float:
    return math.pow(10.0, db / 20.0)


@dataclass(frozen=True)
class AudioGuardAudit:
    forbidden_materials: dict[str, int]
    forbidden_refs: dict[str, int]
    queued_tasks: dict[str, int]
    normalization_mismatches: int
    narration_volume_mismatches: int
    video_volume_mismatches: int

    @property
    def passed(self) -> bool:
        return not any(self.forbidden_materials.values()) and not any(
            self.forbidden_refs.values()
        ) and not any(self.queued_tasks.values()) and all(value == 0 for value in (
            self.normalization_mismatches,
            self.narration_volume_mismatches,
            self.video_volume_mismatches,
        ))

    def as_dict(self) -> dict:
        return {
            "passed": self.passed,
            "forbidden_materials": self.forbidden_materials,
            "forbidden_refs": self.forbidden_refs,
            "queued_tasks": self.queued_tasks,
            "normalization_mismatches": self.normalization_mismatches,
            "narration_volume_mismatches": self.narration_volume_mismatches,
            "video_volume_mismatches": self.video_volume_mismatches,
        }


def _materials(document: dict, bucket: str) -> list[dict]:
    items = (document.get("materials") or {}).get(bucket) or []
    return [item for item in items if isinstance(item, dict)]


def _processing_enabled(bucket: str, item: dict) -> bool:
    """CapCut이 자동 복원하는 비활성 기본 구조체는 효과 사용으로 세지 않는다."""
    if bucket == "vocal_separations" and "choice" in item:
        return bool(item.get("choice")) or bool(item.get("removed_sounds"))
    if "enable" in item:
        return item.get("enable") is True
    return True


def _main_audio_segments(document: dict):
    video_materials = {
        str(item.get("id")): item for item in _materials(document, "videos") if item.get("id")
    }
    for track in document.get("tracks") or []:
        if not isinstance(track, dict):
            continue
        track_type = track.get("type")
        is_main_video = track_type == "video" and track.get("flag", 0) == 0
        if track_type != "audio" and not is_main_video:
            continue
        for segment in track.get("segments") or []:
            if not isinstance(segment, dict):
                continue
            if track_type == "audio":
                yield "narration", segment
            else:
                material = video_materials.get(str(segment.get("material_id"))) or {}
                if material.get("has_audio") is True:
                    yield "video", segment


def audit_draft(document: dict, *, narration_db: float = DEFAULT_NARRATION_DB,
                video_db: float = DEFAULT_VIDEO_DB,
                target_lufs: float = DEFAULT_TARGET_LUFS) -> AudioGuardAudit:
    forbidden_id_to_bucket: dict[str, str] = {}
    material_counts: dict[str, int] = {}
    ref_counts = {bucket: 0 for bucket in FORBIDDEN_AUDIO_PROCESSING_BUCKETS}
    for bucket in FORBIDDEN_AUDIO_PROCESSING_BUCKETS:
        ids = {
            str(item.get("id"))
            for item in _materials(document, bucket)
            if item.get("id") and _processing_enabled(bucket, item)
        }
        material_counts[bucket] = len(ids)
        forbidden_id_to_bucket.update({material_id: bucket for material_id in ids})

    loudness_by_id = {
        str(item.get("id")): item for item in _materials(document, LOUDNESS_BUCKET) if item.get("id")
    }
    expected = {"narration": db_to_linear(narration_db), "video": db_to_linear(video_db)}
    normalization_mismatches = narration_mismatches = video_mismatches = 0
    for kind, segment in _main_audio_segments(document):
        refs = [str(ref) for ref in (segment.get("extra_material_refs") or [])]
        for ref in refs:
            bucket = forbidden_id_to_bucket.get(ref)
            if bucket:
                ref_counts[bucket] += 1
        loudness = [loudness_by_id[ref] for ref in refs if ref in loudness_by_id]
        if len(loudness) != 1 or loudness[0].get("enable") is not True or abs(
            float(loudness[0].get("target_loudness", 0.0)) - target_lufs
        ) > 1e-6:
            normalization_mismatches += 1
        if abs(float(segment.get("volume", 0.0)) - expected[kind]) > 1e-6:
            if kind == "narration":
                narration_mismatches += 1
            else:
                video_mismatches += 1

    queued = {key: len(document.get(key) or []) for key in PROCESSING_TASK_LISTS}
    return AudioGuardAudit(material_counts, ref_counts, queued, normalization_mismatches,
                           narration_mismatches, video_mismatches)


def _new_loudness(segment: dict, target_lufs: float) -> dict:
    source = segment.get("source_timerange") or segment.get("target_timerange") or {}
    return {
        "id": str(uuid.uuid4()).upper(), "enable": True,
        "time_range": {"start": int(source.get("start") or 0),
                       "duration": int(source.get("duration") or 0)},
        "file_id": "", "target_loudness": target_lufs, "loudness_param": None,
    }


def sanitize_draft(document: dict, *, narration_db: float = DEFAULT_NARRATION_DB,
                   video_db: float = DEFAULT_VIDEO_DB,
                   target_lufs: float = DEFAULT_TARGET_LUFS) -> dict:
    """오디오 정책만 고친다. 전환·영상/텍스트 애니메이션은 건드리지 않는다."""
    cleaned = copy.deepcopy(document)
    materials = cleaned.setdefault("materials", {})
    forbidden_ids: set[str] = set()
    for bucket in FORBIDDEN_AUDIO_PROCESSING_BUCKETS:
        forbidden_ids.update(
            str(item.get("id")) for item in _materials(cleaned, bucket) if item.get("id")
        )
        materials[bucket] = []

    loudness_by_id = {
        str(item.get("id")): item for item in _materials(cleaned, LOUDNESS_BUCKET) if item.get("id")
    }
    used_loudness_ids: set[str] = set()
    expected = {"narration": db_to_linear(narration_db), "video": db_to_linear(video_db)}
    main_segments = {id(segment): kind for kind, segment in _main_audio_segments(cleaned)}
    for track in cleaned.get("tracks") or []:
        if not isinstance(track, dict):
            continue
        for segment in track.get("segments") or []:
            if not isinstance(segment, dict):
                continue
            refs = [str(ref) for ref in (segment.get("extra_material_refs") or [])
                    if str(ref) not in forbidden_ids]
            kind = main_segments.get(id(segment))
            if kind:
                existing = [ref for ref in refs if ref in loudness_by_id]
                if existing:
                    keep = existing[0]
                    refs = [ref for ref in refs if ref not in loudness_by_id or ref == keep]
                    loudness = loudness_by_id[keep]
                else:
                    loudness = _new_loudness(segment, target_lufs)
                    keep = str(loudness["id"])
                    loudness_by_id[keep] = loudness
                    refs.append(keep)
                loudness["enable"] = True
                loudness["target_loudness"] = target_lufs
                used_loudness_ids.add(keep)
                segment["volume"] = expected[kind]
                segment["last_nonzero_volume"] = expected[kind]
            else:
                refs = [ref for ref in refs if ref not in loudness_by_id]
            segment["extra_material_refs"] = refs
            segment["intensifies_audio"] = False

    materials[LOUDNESS_BUCKET] = [material for material_id, material in loudness_by_id.items()
                                  if material_id in used_loudness_ids]
    for key in PROCESSING_TASK_LISTS:
        cleaned[key] = []
    return cleaned


def capcut_editor_open() -> bool:
    if os.name != "nt":
        return False
    command = ("$p=Get-Process -Name CapCut -ErrorAction SilentlyContinue | "
               "Where-Object {$_.MainWindowHandle -ne 0}; if($p){'OPEN'}")
    try:
        result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", command],
                                capture_output=True, text=True, timeout=10, check=False)
        return "OPEN" in result.stdout
    except Exception:
        return True


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_guarded_files(primary: Path, *, narration_db: float = DEFAULT_NARRATION_DB,
                        video_db: float = DEFAULT_VIDEO_DB,
                        target_lufs: float = DEFAULT_TARGET_LUFS) -> list[tuple[Path, AudioGuardAudit]]:
    if capcut_editor_open():
        raise RuntimeError("CapCut 본체가 열려 있습니다. 완전히 종료한 뒤 다시 실행하세요.")
    paths = [primary]
    paths.extend(primary.parent / name for name in COMPANION_NAMES if (primary.parent / name).exists())
    loaded = [(path, load_json(path)) for path in paths]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    reports: list[tuple[Path, AudioGuardAudit]] = []
    for path, document in loaded:
        shutil.copy2(path, path.with_name(f"{path.name}.before-audio-guard-{timestamp}.bak"))
        cleaned = sanitize_draft(document, narration_db=narration_db, video_db=video_db,
                                 target_lufs=target_lufs)
        temp = path.with_name(f"{path.name}.audio-guard.tmp")
        temp.write_text(json.dumps(cleaned, ensure_ascii=False), encoding="utf-8")
        load_json(temp)
        temp.replace(path)
        report = audit_draft(cleaned, narration_db=narration_db, video_db=video_db,
                             target_lufs=target_lufs)
        if not report.passed:
            raise RuntimeError(f"교정 후 검증 실패: {path} / {report.as_dict()}")
        reports.append((path, report))
    return reports


def main() -> int:
    parser = argparse.ArgumentParser(description="CapCut 노멀라이제이션 전용 오디오 가드")
    parser.add_argument("draft_content", type=Path)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--narration-db", type=float, default=DEFAULT_NARRATION_DB)
    parser.add_argument("--video-db", type=float, default=DEFAULT_VIDEO_DB)
    parser.add_argument("--target-lufs", type=float, default=DEFAULT_TARGET_LUFS)
    args = parser.parse_args()
    primary = args.draft_content.resolve()
    if not primary.exists():
        print(f"[실패] 초안 없음: {primary}")
        return 1
    if args.write:
        try:
            reports = write_guarded_files(primary, narration_db=args.narration_db,
                                          video_db=args.video_db, target_lufs=args.target_lufs)
        except Exception as exc:
            print(f"[실패] {exc}")
            return 1
        for path, report in reports:
            print(f"[통과] {path.name}: {json.dumps(report.as_dict(), ensure_ascii=False)}")
        return 0
    report = audit_draft(load_json(primary), narration_db=args.narration_db,
                         video_db=args.video_db, target_lufs=args.target_lufs)
    print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
