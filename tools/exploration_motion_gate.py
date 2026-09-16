"""Fail-closed EP14+ exploration contract checks. No generation, no auto visual QA.

Evidence declarations cannot prove aesthetics; reviewers must watch actual motion.
This gate binds those observations to the contract, submitted frames and exact files.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

CONTRACT = '02F.탐험연출계약.json'
REVIEW = '04.탐험동작검수.json'
SCENES = '02a.장면구분.json'
FORBIDDEN = re.compile(
    r'camera\s+(?:is\s+)?locked|locked\s+camera|hold the camera|'
    r'camera never move|no zoom|no pan|no orbit|no reframing|'
    r'identical start and end|exact artifact pixels|pixel geometry|'
    r'almost imperceptible|카메라\s*고정', re.I)
FIELDS = ('narration', 'visual_action', 'camera_start', 'camera_route', 'camera_end',
          'foreground', 'midground', 'background', 'parallax_evidence',
          'context_role', 'context_reason', 'source_basis', 'motion_family',
          'start_image_prompt', 'end_image_prompt')

def enabled(ep: Path) -> bool:
    m = re.match(r'EP(\d+)(?:_|$)', ep.name, re.I)
    return (bool(m) and int(m[1]) >= 14) or (ep / CONTRACT).exists()

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def finite(value, low, high) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and low <= value <= high)

def check_file(ep, path, expected):
    p = Path(path) if isinstance(path, str) and path else None
    if p is None:
        return False
    p = p if p.is_absolute() else ep / p
    return p.is_file() and isinstance(expected, str) and digest(p) == expected.lower()

def validate(ep: Path, phase='video', master: Path | None = None) -> list[str]:
    if not enabled(ep):
        return []  # Historical episodes remain untouched.
    errors = []
    try:
        scenes, contract = read(ep / SCENES), read(ep / CONTRACT)
        if not isinstance(scenes, list) or not scenes or not isinstance(contract, dict):
            raise ValueError('장면/계약 형식')
        specs = contract.get('scenes')
        if contract.get('version') != 1 or not isinstance(specs, dict):
            raise ValueError('계약 version/scenes')
        ids = [str(s['n']) for s in scenes]
        if len(set(ids)) != len(ids) or set(specs) != set(ids):
            raise ValueError('장면 번호 계약 불일치')
        if not check_file(ep, '01.대본.txt', contract.get('script_sha256')):
            errors.append('SCRIPT_CHANGED: 대본 해시 계약 불일치')
        families = set()
        for s in scenes:
            n = str(s['n']); spec = specs[n]
            prefix = f'컷 {n}: '
            if not isinstance(spec, dict):
                errors.append(prefix + '계약 객체 필요'); continue
            if any(not isinstance(spec.get(k), str) or not spec[k].strip() for k in FIELDS):
                errors.append(prefix + '탐험 구도/행동/고증 필드 누락')
            if spec.get('narration') != s.get('txt') or s.get('exploration') != spec:
                errors.append(prefix + 'CONTRACT_DRIFT: 수리로 원래 대본/연출 계약 변경 금지')
            if spec.get('camera_start') == spec.get('camera_end'):
                errors.append(prefix + 'SAME_COMPOSITION: 다른 도착 구도 필요')
            if spec.get('start_image_prompt') == spec.get('end_image_prompt'):
                errors.append(prefix + 'SAME_IMAGE_PLAN: 출발/도착 이미지 프롬프트를 별도로 설계')
            if not finite(spec.get('active_motion_ratio'), .8, 1):
                errors.append(prefix + '연출 목표 이동 구간 80% 이상 필요')
            if not finite(spec.get('end_hold_seconds'), 0, .7):
                errors.append(prefix + '마지막 홀드 0.7초 이하 필요')
            families.add(spec.get('motion_family', ''))
            cp = s.get('camera_path') or {}
            if cp.get('single_axis') == 'LOCKED' or cp.get('speed_profile') in {'EVIDENCE_HOLD','SLOW_OBSERVATIONAL_EXCEPTION'}:
                errors.append(prefix + 'STATIC_CAMERA: 고정 카메라 예외 폐기')
            if FORBIDDEN.search(str(s.get('vid', ''))):
                errors.append(prefix + 'STATIC_PROMPT: 이동 금지/픽셀 고정 문구')
            if phase != 'image':
                if s.get('i2v_binding') != 'START_END_FRAME':
                    errors.append(prefix + '실제 시작/종료 프레임 쌍 필요')
                a, b = s.get('image_sha256'), s.get('end_image_sha256')
                if isinstance(a, str) and isinstance(b, str) and a.lower() == b.lower():
                    errors.append(prefix + 'IDENTICAL_ENDPOINTS: 시작/종료 동일 이미지 금지')
                for key, sha in [('image_file','image_sha256'),('end_image_file','end_image_sha256')]:
                    if not check_file(ep, s.get(key), s.get(sha)):
                        errors.append(prefix + f'실제 프레임/해시 누락: {key}')
        if len(scenes) >= 3 and len(families - {''}) < 2:
            errors.append('MONOTONY: 의미에 맞는 서로 다른 이동 문법 최소 2종 필요')
        if phase == 'release':
            qa = read(ep / REVIEW)
            if qa.get('contract_sha256') != digest(ep / CONTRACT) or qa.get('scene_manifest_sha256') != digest(ep / SCENES):
                errors.append('STALE_REVIEW: 계약/장면표 변경 후 재검수 필요')
            if master is None or not master.is_file() or qa.get('master_sha256') != digest(master):
                errors.append('MASTER_CHANGED: 최종 편집 해시 불일치')
            reviews = qa.get('scenes', {})
            if not isinstance(reviews, dict) or set(reviews) != set(ids):
                errors.append('전 컷 동작 검수 필요'); return errors
            for s in scenes:
                n = str(s['n']); r = reviews[n]
                if not isinstance(r, dict):
                    errors.append(f'컷 {n}: 검수 객체 필요'); continue
                for key in ('camera_motion','explanation_action','artifact_form','narration_sync','final_speed_motion'):
                    if r.get(key) != 'PASS':
                        errors.append(f'컷 {n}: {key} 실영상 검수 미통과')
                for key in ('observed_path','observed_action','reviewed_at','submitted_start_asset_id','submitted_end_asset_id'):
                    if not isinstance(r.get(key), str) or not r[key].strip():
                        errors.append(f'컷 {n}: 관찰/첨부 증거 누락 {key}')
                if r.get('full_clip_playback_reviewed') is not True:
                    errors.append(f'컷 {n}: 원본 연속 재생 검수 필요')
                if not finite(r.get('observed_motion_ratio'), .8, 1):
                    errors.append(f'컷 {n}: 실제 지속 이동 검수 미달')
                if not check_file(ep, r.get('video_file'), r.get('video_sha256')):
                    errors.append(f'컷 {n}: 생성 원본 해시 불일치')
                for key in ('image_sha256','end_image_sha256'):
                    if str(r.get(key, '')).lower() != str(s.get(key, '')).lower():
                        errors.append(f'컷 {n}: 제출 프레임 검수 불일치')
                if r.get('submitted_start_asset_id') == r.get('submitted_end_asset_id'):
                    errors.append(f'컷 {n}: 제출 A/B 자산 동일')
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        errors.append(f'EXPLORATION_EVIDENCE_MISSING: {exc}')
    return errors

def require(ep, phase='video', master=None):
    failures = validate(ep, phase, master)
    if failures:
        raise ValueError('탐험 연출 검문 실패:\n' + '\n'.join(failures))

def reject_static_repair():
    raise SystemExit('중단: 카메라 고정/A=A 정적 수리 폐기. 02E 기준의 다른 A/B와 원래 설명 동작을 설계하세요. 파일은 변경하지 않았습니다.')

if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('episode', type=Path)
    p.add_argument('--phase', choices=['image','video','release'], default='video')
    p.add_argument('--master', type=Path)
    a = p.parse_args(); failures = validate(a.episode.resolve(), a.phase, a.master)
    print('\n'.join(failures) if failures else 'PASS: 서류/해시 검문만 통과; 영상미 자동 판정 아님')
    raise SystemExit(bool(failures))
