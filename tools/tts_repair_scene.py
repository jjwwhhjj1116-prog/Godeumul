#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""긴 장면 TTS에서 단어가 씹힐 때 문장 단위로 재생성해 한 파일로 복구한다.

장면 번호와 승인 대본은 바꾸지 않는다. 지정한 문구 뒤에서만 TTS 요청을 둘로
나눈 뒤 같은 인코딩으로 이어 붙이고, durations.json 및 강제정렬 캐시를 갱신한다.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

from tts_generate import Config, ROOT, load_env, parse_script, probe_duration, synth
from tts_pronunciation import DEFAULT_DICTIONARY, PronunciationDictionary


def concat_audio(parts: list[Path], output: Path) -> None:
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for part in parts:
        cmd += ["-i", str(part)]
    labels = "".join(f"[{i}:a]" for i in range(len(parts)))
    cmd += [
        "-filter_complex", f"{labels}concat=n={len(parts)}:v=0:a=1[out]",
        "-map", "[out]", "-ar", "44100", "-b:a", "128k", str(output),
    ]
    subprocess.run(cmd, check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="씹힌 장면 TTS 문장 분할 복구")
    ap.add_argument("script", type=Path)
    ap.add_argument("--scene", type=int, required=True)
    ap.add_argument("--split-after", required=True, help="이 문구 뒤에서 생성 요청을 나눈다")
    ap.add_argument("--outdir", type=Path, default=None)
    ap.add_argument(
        "--env-file",
        type=Path,
        default=ROOT / ".env",
        help="ElevenLabs 키를 읽을 .env 경로(기본: 저장소 .env)",
    )
    ap.add_argument("--pronunciation-dictionary", type=Path, default=DEFAULT_DICTIONARY)
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()

    scenes = {scene.seq: scene for scene in parse_script(args.script)}
    if args.scene not in scenes:
        sys.exit(f"[에러] 장면 {args.scene}을 찾지 못했습니다.")
    scene = scenes[args.scene]
    head, marker, tail = scene.text.partition(args.split_after)
    if not marker or not head.strip() or not tail.strip():
        sys.exit("[에러] --split-after 문구가 없거나 양쪽 문장이 비었습니다.")

    chunks = [(head + marker).strip(), tail.strip()]
    pronunciation = PronunciationDictionary(args.pronunciation_dictionary)
    spoken_chunks = [pronunciation.apply(chunk)[0] for chunk in chunks]
    full_spoken, full_changes = pronunciation.apply(scene.text)
    cfg = Config.from_env(load_env(args.env_file), require_api_key=args.run)
    outdir = args.outdir or args.script.parent / "audio"
    manifest_path = outdir / "durations.json"
    destination = outdir / f"{args.scene:03d}.mp3"

    print(f"장면 {args.scene}: {len(scene.text)}자 → {len(chunks)}개 요청")
    for index, chunk in enumerate(chunks, 1):
        print(f"  {index}. {chunk}")
    if not args.run:
        print("점검만 수행했습니다. 실제 복구는 --run을 붙이세요.")
        return 0
    if not manifest_path.exists():
        sys.exit(f"[에러] 길이표가 없습니다: {manifest_path}")

    outdir.mkdir(parents=True, exist_ok=True)
    part_paths = [outdir / f".{args.scene:03d}.repair_part_{i}.mp3" for i in range(1, len(chunks) + 1)]
    combined = outdir / f".{args.scene:03d}.repair_combined.mp3"
    try:
        for text, path in zip(spoken_chunks, part_paths):
            synth(cfg, text, path)
        concat_audio(part_paths, combined)
        if destination.exists():
            backup = outdir / f"{args.scene:03d}_before_latest_repair.mp3"
            shutil.copy2(destination, backup)
        combined.replace(destination)
    finally:
        for path in part_paths:
            path.unlink(missing_ok=True)
        combined.unlink(missing_ok=True)

    duration = probe_duration(destination)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    signature = cfg.signature() + "|pron:" + pronunciation.signature
    manifest["scenes"][str(args.scene)] = {
        "hash": scene.hash(signature, full_spoken),
        "chars": len(scene.text),
        "tts_chars": len(full_spoken),
        "file": destination.name,
        "duration": duration,
        "text": scene.text,
        "tts_text": full_spoken,
        "pronunciation_changes": [asdict(change) for change in full_changes],
        "repair_split": {
            "reason": "swallowed_word",
            "split_after": args.split_after,
            "chunks": chunks,
        },
    }
    manifest["scene_count"] = len(manifest["scenes"])
    manifest["total_duration"] = round(
        sum(float(item.get("duration") or 0) for item in manifest["scenes"].values()), 3
    )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    alignment_path = outdir / "alignment.json"
    if alignment_path.exists():
        alignment = json.loads(alignment_path.read_text(encoding="utf-8"))
        alignment.get("scenes", {}).pop(str(args.scene), None)
        alignment.get("signatures", {}).pop(str(args.scene), None)
        alignment_path.write_text(json.dumps(alignment, ensure_ascii=False), encoding="utf-8")

    print(f"복구 완료: {destination} ({duration:.3f}초)")
    print(f"전체 길이: {manifest['total_duration']:.3f}초")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
