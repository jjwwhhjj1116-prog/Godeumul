#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Flow 생성 확장프로그램용 순차·재개 가능 작업 목록을 만든다.

이 도구는 브라우저를 조작하지 않는다. 2G에서 잠긴 프롬프트를 한 컷씩 실행할
수 있는 작업으로 바꾸고, 중복 제출과 입력 변경을 실행 전에 차단한다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import _config  # noqa: F401
from build_hybrid_flow_pack import verify_pack
from exploration_motion_gate import enabled as exploration_enabled, read as read_exploration, SCENES


BATCH_NAME = "04.FLOW확장작업목록.json"
STATE_NAME = "04.FLOW확장실행상태.json"
ALLOWED_SECONDS = {4, 6, 8, 10}
LABEL_ONLY = re.compile(r"^(?:scene|shot|장면)\s*[#:_-]?\s*\d+\s*$", re.I)
HANGUL = re.compile(r"[가-힣]")
DURATION_PATTERNS = (
    re.compile(r"\b(4|6|8|10)[ -]?seconds?\b", re.I),
    re.compile(r"\b(4|6|8|10)s\s+(?:I2V|T2V|shot)\b", re.I),
)


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest().upper()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _read_strict_blocks(path: Path) -> list[str]:
    if not path.exists():
        raise ValueError(f"확장 입력 파일 누락: {path.name}")
    raw = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    if not raw.strip():
        return []
    if re.search(r"\n[ \t]+\n", raw):
        raise ValueError(f"{path.name}: 공백 문자만 든 구분 줄이 있습니다")
    if "\n\n\n" in raw:
        raise ValueError(f"{path.name}: 장면 사이 빈 줄은 정확히 1개여야 합니다")
    blocks = raw.strip("\n").split("\n\n")
    if any(not block.strip() for block in blocks):
        raise ValueError(f"{path.name}: 빈 프롬프트가 있습니다")
    return [block.strip() for block in blocks]


def _duration(prompt: str) -> int:
    found: set[int] = set()
    for pattern in DURATION_PATTERNS:
        found.update(int(value) for value in pattern.findall(prompt))
    if len(found) != 1 or next(iter(found), 0) not in ALLOWED_SECONDS:
        raise ValueError("영상 프롬프트마다 4·6·8·10초 중 정확히 하나를 명시해야 합니다")
    return next(iter(found))


def _validate_prompt(prompt: str, source: str, artifact_name: str, prompt_token: str) -> None:
    for line in prompt.splitlines():
        if LABEL_ONLY.fullmatch(line.strip()):
            raise ValueError(f"{source}: 별도 장면 라벨 줄은 확장이 프롬프트로 오인합니다")
    # Flow 애셋명이 한글이면 정확한 잠금 이름/토큰만 예외다. 그 외 본문은 영문이어야 한다.
    english_body = prompt
    for allowed in (prompt_token, artifact_name):
        if allowed:
            english_body = english_body.replace(allowed, "")
    if HANGUL.search(english_body):
        raise ValueError(f"{source}: 잠긴 Flow 애셋명 외에는 영문 프롬프트만 허용합니다")


def _load_reference_names(episode: Path) -> tuple[str, str]:
    data = json.loads((episode / "02e.FLOW유물참조잠금.json").read_text(encoding="utf-8"))
    artifact_name = str(data.get("artifact_name_ko") or "").strip()
    flow_reference = data.get("flow_reference") or {}
    prompt_token = str(flow_reference.get("prompt_token") or "").strip()
    return artifact_name, prompt_token


def _job(
    *, job_id: str, scene: int, phase: str, prompt: str, prompt_source: str,
    expected_output: str, input_image: str | None = None, depends_on: list[str] | None = None,
) -> dict[str, object]:
    row: dict[str, object] = {
        "job_id": job_id,
        "scene": scene,
        "phase": phase,
        "prompt_source": prompt_source,
        "prompt": prompt,
        "prompt_sha256": _sha_text(prompt),
        "expected_output": expected_output,
        "depends_on": depends_on or [],
    }
    if input_image:
        row["input_image"] = input_image
    if phase != "IMAGE":
        row["duration_seconds"] = _duration(prompt)
    return row


def build_batch(episode: Path) -> dict[str, object]:
    plan = verify_pack(episode)
    artifact_name, prompt_token = _load_reference_names(episode)
    image_prompts = _read_strict_blocks(episode / "flow_i2v_images.txt")
    i2v_prompts = _read_strict_blocks(episode / "flow_i2v_videos.txt")
    t2v_prompts = _read_strict_blocks(episode / "flow_t2v_videos.txt")

    if len(image_prompts) != plan["i2v_count"] or len(i2v_prompts) != plan["i2v_count"]:
        raise ValueError("I2V 이미지·영상 프롬프트 수가 생성계획 i2v_count와 다릅니다")
    if len(t2v_prompts) != plan["t2v_count"]:
        raise ValueError("T2V 프롬프트 수가 생성계획 t2v_count와 다릅니다")

    jobs: list[dict[str, object]] = []
    endpoints = ({int(s['n']): s for s in read_exploration(episode / SCENES)}
                 if exploration_enabled(episode) else {})
    image_index = i2v_index = t2v_index = 0
    seen_job_ids: set[str] = set()
    for mapping in plan["mapping"]:
        scene = int(mapping["scene"])
        mode = str(mapping["generation_mode"])
        if mode == "I2V_LOCKED":
            image_prompt = image_prompts[image_index]
            video_prompt = i2v_prompts[i2v_index]
            image_index += 1
            i2v_index += 1
            _validate_prompt(image_prompt, f"scene {scene:03d} image", artifact_name, prompt_token)
            _validate_prompt(video_prompt, f"scene {scene:03d} i2v", artifact_name, prompt_token)
            image_id = f"IMG-{scene:03d}"
            video_id = f"I2V-{scene:03d}"
            jobs.append(_job(
                job_id=image_id, scene=scene, phase="IMAGE", prompt=image_prompt,
                prompt_source="flow_i2v_images.txt", expected_output=f"images/{scene:03d}.png",
            ))
            jobs.append(_job(
                job_id=video_id, scene=scene, phase="I2V", prompt=video_prompt,
                prompt_source="flow_i2v_videos.txt", input_image=f"images/{scene:03d}.png",
                expected_output=f"clips/{scene:03d}.mp4", depends_on=[image_id],
            ))
            if endpoints:
                s = endpoints[scene]
                jobs[-1].update(
                    input_image=s['image_file'], input_image_sha256=s['image_sha256'],
                    input_end_image=s['end_image_file'],
                    input_end_image_sha256=s['end_image_sha256'],
                    i2v_binding='START_END_FRAME',
                    requires_verified_endpoint_attachment=True,
                )
        elif mode == "T2V_CONTEXT":
            prompt = t2v_prompts[t2v_index]
            t2v_index += 1
            _validate_prompt(prompt, f"scene {scene:03d} t2v", artifact_name, prompt_token)
            jobs.append(_job(
                job_id=f"T2V-{scene:03d}", scene=scene, phase="T2V", prompt=prompt,
                prompt_source="flow_t2v_videos.txt", expected_output=f"clips/{scene:03d}.mp4",
            ))
        else:
            raise ValueError(f"scene {scene:03d}: 알 수 없는 생성 방식 {mode}")

    for row in jobs:
        job_id = str(row["job_id"])
        if job_id in seen_job_ids:
            raise ValueError(f"중복 작업 ID: {job_id}")
        seen_job_ids.add(job_id)

    batch = {
        "version": 1,
        "gate": "PASS",
        "episode": episode.name,
        "source_plan": "04.하이브리드생성계획.json",
        "source_plan_sha256": _sha_file(episode / "04.하이브리드생성계획.json"),
        "execution_policy": {
            "runner": "CHROME_EXTENSION_SEQUENTIAL",
            "max_in_flight": 1,
            "aspect_ratio": "9:16",
            "image_first_gate": True,
            "download_after_each": True,
            "automatic_retry_limit": 0,
            "resume_by_job_id_and_prompt_sha256": True,
            "completion_signal": "matching generated card or downloaded file for the same job, never total tile count",
        },
        "counts": {
            "images": sum(row["phase"] == "IMAGE" for row in jobs),
            "i2v": sum(row["phase"] == "I2V" for row in jobs),
            "t2v": sum(row["phase"] == "T2V" for row in jobs),
            "jobs": len(jobs),
        },
        "jobs": jobs,
    }
    batch_path = episode / BATCH_NAME
    batch_path.write_text(json.dumps(batch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    state_path = episode / STATE_NAME
    prior: dict[str, object] = {}
    if state_path.exists():
        loaded = json.loads(state_path.read_text(encoding="utf-8"))
        if loaded.get("source_batch_sha256") == _sha_file(batch_path):
            prior = {str(row["job_id"]): row for row in loaded.get("jobs", [])}
    state_jobs = []
    for row in jobs:
        old = prior.get(str(row["job_id"]), {})
        status = old.get("status") if old.get("prompt_sha256") == row["prompt_sha256"] else "PENDING"
        state_jobs.append({
            "job_id": row["job_id"],
            "prompt_sha256": row["prompt_sha256"],
            "status": status or "PENDING",
            "attempts": int(old.get("attempts") or 0),
            "flow_result_id": old.get("flow_result_id"),
            "downloaded_file_sha256": old.get("downloaded_file_sha256"),
            "qa": old.get("qa") or "NOT_RUN",
        })
    state = {
        "version": 1,
        "source_batch_sha256": _sha_file(batch_path),
        "state": "PREPARED",
        "jobs": state_jobs,
    }
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return batch


def verify_batch(episode: Path) -> dict[str, object]:
    verify_pack(episode)
    batch_path = episode / BATCH_NAME
    state_path = episode / STATE_NAME
    if not batch_path.exists() or not state_path.exists():
        raise ValueError("확장 작업 목록/실행 상태가 없습니다. 먼저 작업 목록을 만드세요")
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if batch.get("version") != 1 or batch.get("gate") != "PASS":
        raise ValueError("확장 작업 목록 version 1 PASS가 아닙니다")
    if batch.get("source_plan_sha256") != _sha_file(episode / "04.하이브리드생성계획.json"):
        raise ValueError("하이브리드 생성계획이 바뀌었습니다. 확장 작업 목록을 다시 만드세요")
    if state.get("source_batch_sha256") != _sha_file(batch_path):
        raise ValueError("확장 작업 목록과 실행 상태 해시가 다릅니다")
    job_ids = [str(row.get("job_id")) for row in batch.get("jobs", [])]
    if len(job_ids) != len(set(job_ids)):
        raise ValueError("확장 작업 목록에 중복 작업 ID가 있습니다")
    state_ids = [str(row.get("job_id")) for row in state.get("jobs", [])]
    if state_ids != job_ids:
        raise ValueError("확장 작업 목록과 실행 상태의 작업 순서가 다릅니다")
    if exploration_enabled(episode):
        endpoints = {int(s['n']): s for s in read_exploration(episode / SCENES)}
        i2v_jobs = [row for row in batch['jobs'] if row.get('phase') == 'I2V']
        if sorted(int(row['scene']) for row in i2v_jobs) != sorted(endpoints):
            raise ValueError("전 컷 실제 A/B I2V 작업이 필요합니다")
        for row in i2v_jobs:
            s = endpoints[int(row['scene'])]
            for job_key, scene_key in (
                ('input_image','image_file'), ('input_image_sha256','image_sha256'),
                ('input_end_image','end_image_file'), ('input_end_image_sha256','end_image_sha256'),
            ):
                if row.get(job_key) != s.get(scene_key):
                    raise ValueError(f"컷 {s['n']}: 확장 작업 목록 A/B 누락 또는 변경")
            if row.get('i2v_binding') != 'START_END_FRAME' or row.get('requires_verified_endpoint_attachment') is not True:
                raise ValueError("시작/종료 실제 첨부 검문 누락")
    return batch


def main() -> int:
    parser = argparse.ArgumentParser(description="Flow 생성 확장프로그램 순차 작업 목록 생성")
    parser.add_argument("episode", type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    episode = args.episode.resolve()
    batch = verify_batch(episode) if args.verify else build_batch(episode)
    label = "재검증" if args.verify else "생성"
    print(
        f"Flow 확장 작업 목록 {label} PASS · 이미지 {batch['counts']['images']} / "
        f"I2V {batch['counts']['i2v']} / T2V {batch['counts']['t2v']} / "
        f"동시 실행 {batch['execution_policy']['max_in_flight']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
