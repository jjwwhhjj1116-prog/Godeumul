#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""CapCut에서 실제로 확인·내보낸 게시 마스터를 해시로 잠근다.

드래프트 생성이나 Remotion/ffmpeg 렌더만으로는 이 잠금을 만들 수 없다.
CapCut GUI에서 자막 스타일, 싱크, 마감 효과, 전체 재생을 확인한 뒤 실행한다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from _config import load
from capcut_audio_guard import audit_draft
from script_context_gate import validate_context_review


CFG = load()
LOCK_NAME = "05.캡컷마감잠금.json"
REQUIRED_CHECKS = (
    "caption_style_verified",
    "caption_sync_verified",
    "motion_finish_verified",
    "full_playback_verified",
    "audio_policy_verified",
)


for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


@dataclass
class FinalLockReport:
    video: Path
    lock: Path
    failures: list[str]
    details: dict

    @property
    def passed(self) -> bool:
        return not self.failures


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def probe_video(path: Path) -> tuple[dict, list[str]]:
    failures: list[str] = []
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_streams", "-show_format",
             "-of", "json", str(path)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", check=True,
        )
        raw = json.loads(result.stdout)
    except Exception as exc:
        return {}, [f"ffprobe 실패: {exc}"]

    video_stream = next((s for s in raw.get("streams", []) if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in raw.get("streams", []) if s.get("codec_type") == "audio"), None)
    if not video_stream:
        failures.append("비디오 스트림 없음")
    if not audio_stream:
        failures.append("오디오 스트림 없음")

    width = int((video_stream or {}).get("width") or 0)
    height = int((video_stream or {}).get("height") or 0)
    want_width, want_height = CFG.get("출력.해상도", [1080, 1920])
    scale_x = width / want_width if want_width else 0.0
    scale_y = height / want_height if want_height else 0.0
    if scale_x not in (1.0, 2.0) or scale_y != scale_x:
        failures.append(
            f"해상도 {width}x{height} — 기대 {want_width}x{want_height} 또는 "
            f"4K {want_width * 2}x{want_height * 2}"
        )

    rate = str((video_stream or {}).get("avg_frame_rate") or "0/1")
    try:
        numerator, denominator = rate.split("/", 1)
        fps = float(numerator) / max(float(denominator), 1.0)
    except (ValueError, ZeroDivisionError):
        fps = 0.0
    want_fps = float(CFG.get("출력.fps", 30))
    if abs(fps - want_fps) > 0.1:
        failures.append(f"프레임레이트 {fps:.3f} — 기대 {want_fps:.3f}")

    duration = float((raw.get("format") or {}).get("duration") or 0.0)
    if duration <= 0:
        failures.append("영상 길이를 읽을 수 없음")
    if duration >= 180:
        failures.append(f"영상 길이 {duration:.3f}초 — 쇼츠 180초 상한 초과")

    return {
        "width": width,
        "height": height,
        "fps": round(fps, 3),
        "duration": round(duration, 3),
        "video_codec": (video_stream or {}).get("codec_name"),
        "audio_codec": (audio_stream or {}).get("codec_name"),
    }, failures


def validate_capcut_lock(ep: Path, video: Path | None = None) -> FinalLockReport:
    ep = ep.resolve()
    lock_path = ep / LOCK_NAME
    failures: list[str] = []
    if not lock_path.exists():
        return FinalLockReport(video or ep, lock_path, [f"CapCut 마감 잠금 없음: {lock_path}"], {})
    try:
        doc = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return FinalLockReport(video or ep, lock_path, [f"CapCut 마감 잠금 JSON 오류: {exc}"], {})

    locked_video = ep / str(doc.get("video") or "")
    selected = (video or locked_video).resolve()
    if doc.get("status") != "PASS":
        failures.append("CapCut 마감 잠금 status가 PASS가 아님")
    if doc.get("editor") != "CapCut":
        failures.append("최종 편집기가 CapCut으로 기록되지 않음")
    if selected != locked_video.resolve():
        failures.append(f"선택 영상이 잠금 영상과 다름: {selected.name} / {locked_video.name}")
    if not selected.exists():
        failures.append(f"잠금 영상 없음: {selected}")
    else:
        actual_hash = sha256_file(selected)
        if doc.get("video_sha256") != actual_hash:
            failures.append("영상 SHA-256이 CapCut 마감 잠금과 다름 — 재검수·재잠금 필요")
    checks = doc.get("checks") or {}
    for key in REQUIRED_CHECKS:
        if checks.get(key) is not True:
            failures.append(f"CapCut GUI 필수 확인 누락: {key}")
    if not str(doc.get("project_name") or "").strip():
        failures.append("CapCut 프로젝트 이름 누락")
    return FinalLockReport(selected, lock_path, failures, doc)


def main() -> int:
    parser = argparse.ArgumentParser(description="CapCut 게시 마스터 검수·해시 잠금")
    parser.add_argument("episode", type=Path)
    parser.add_argument("--video", type=Path, default=None,
                        help="CapCut에서 내보낸 mp4. 기본은 에피소드 폴더의 *_capcut.mp4")
    parser.add_argument("--project-name", default="", help="실제 확인한 CapCut 프로젝트 이름")
    parser.add_argument("--write", action="store_true", help="검수 통과 시 잠금 파일 작성")
    parser.add_argument("--caption-style-verified", action="store_true")
    parser.add_argument("--caption-sync-verified", action="store_true")
    parser.add_argument("--motion-finish-verified", action="store_true")
    parser.add_argument("--full-playback-verified", action="store_true")
    parser.add_argument("--audio-policy-verified", action="store_true",
                        help="모든 음원 노멀라이즈 ON, 음성 보정 OFF, 영상 -15dB/TTS +5dB 확인")
    parser.add_argument("--draft-content", type=Path, default=None,
                        help="실제 내보낸 CapCut 프로젝트의 draft_content.json")
    args = parser.parse_args()

    ep = args.episode.resolve()
    if not args.write:
        report = validate_capcut_lock(ep, args.video.resolve() if args.video else None)
        if report.failures:
            print("\n[실패] CapCut 마감 잠금")
            for failure in report.failures:
                print(f"  - {failure}")
            print()
            return 1
        print(f"\n[통과] CapCut 게시 마스터: {report.video}\n")
        return 0

    video = args.video
    if video is None:
        hits = sorted(ep.glob("*_capcut.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not hits:
            print("[실패] *_capcut.mp4를 찾지 못했습니다. --video로 지정하세요.")
            return 1
        video = hits[0]
    video = video.resolve()
    failures: list[str] = []
    if not video.exists():
        failures.append(f"영상 없음: {video}")
    if video.parent != ep:
        failures.append("게시 마스터는 에피소드 폴더 안에 있어야 함")
    if "capcut" not in video.stem.lower():
        failures.append("파일명에 capcut이 없음 — Remotion/ffmpeg 미리보기와 구분 필요")
    if not args.project_name.strip():
        failures.append("--project-name 필요")
    checks = {
        "caption_style_verified": args.caption_style_verified,
        "caption_sync_verified": args.caption_sync_verified,
        "motion_finish_verified": args.motion_finish_verified,
        "full_playback_verified": args.full_playback_verified,
        "audio_policy_verified": args.audio_policy_verified,
    }
    for key, passed in checks.items():
        if not passed:
            failures.append(f"CapCut GUI 확인 플래그 누락: {key}")

    draft_guard: dict = {}
    if args.draft_content is None:
        failures.append("--draft-content 필요 — 캡컷 오디오 정책을 자동 검증해야 함")
    else:
        draft_path = args.draft_content.resolve()
        if not draft_path.exists():
            failures.append(f"CapCut 초안 없음: {draft_path}")
        else:
            try:
                draft_document = json.loads(draft_path.read_text(encoding="utf-8"))
                draft_report = audit_draft(draft_document)
                draft_guard = {
                    "path": str(draft_path),
                    "sha256": sha256_file(draft_path),
                    **draft_report.as_dict(),
                }
                if not draft_report.passed:
                    failures.append(f"CapCut 오디오 정책 가드 실패: {draft_report.as_dict()}")
            except (OSError, json.JSONDecodeError) as exc:
                failures.append(f"CapCut 초안 검사 실패: {exc}")

    context = validate_context_review(ep / "01.대본.txt", ep / "01.문맥검수.json")
    failures.extend(f"문맥 QA: {failure}" for failure in context.failures)
    media_info: dict = {}
    if video.exists():
        media_info, media_failures = probe_video(video)
        failures.extend(media_failures)
    if failures:
        print("\n[실패] CapCut 게시 마스터 잠금 생성 금지")
        for failure in failures:
            print(f"  - {failure}")
        print()
        return 1

    doc = {
        "status": "PASS",
        "editor": "CapCut",
        "project_name": args.project_name.strip(),
        "video": video.name,
        "video_sha256": sha256_file(video),
        "locked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "checks": checks,
        "media": media_info,
        "context_review": "01.문맥검수.json",
        "draft_audio_guard": draft_guard,
    }
    lock_path = ep / LOCK_NAME
    lock_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[잠금 완료] {lock_path}\n  영상: {video.name}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
