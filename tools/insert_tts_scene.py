#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TTS 장면 하나를 중간에 삽입할 때 뒤 파일·매니페스트·정렬 번호를 안전하게 민다."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="TTS 장면 번호 삽입")
    parser.add_argument("audio_dir", type=Path)
    parser.add_argument("--at", type=int, required=True, help="새 장면이 들어갈 번호")
    args = parser.parse_args()
    audio_dir = args.audio_dir.resolve()
    manifest_path = audio_dir / "durations.json"
    alignment_path = audio_dir / "generation_alignment.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    alignment = json.loads(alignment_path.read_text(encoding="utf-8"))
    scenes = manifest["scenes"]
    maximum = max(map(int, scenes))

    # 삽입 위치의 기존 장면은 앞부분으로 다시 생성한다. 그 다음 장면부터 한 칸 민다.
    for number in range(maximum, args.at, -1):
        source = audio_dir / f"{number:03d}.mp3"
        target = audio_dir / f"{number + 1:03d}.mp3"
        if target.exists():
            raise SystemExit(f"[에러] 대상 파일이 이미 있음: {target}")
        source.rename(target)
        item = scenes.pop(str(number))
        item["file"] = target.name
        scenes[str(number + 1)] = item
        for field in ("signatures", "scenes"):
            bucket = alignment.get(field) or {}
            if str(number) in bucket:
                bucket[str(number + 1)] = bucket.pop(str(number))

    # 기존 삽입 위치의 음성과 기록은 새 앞·뒤 문장으로 덮어쓴다.
    scenes.pop(str(args.at), None)
    for field in ("signatures", "scenes"):
        (alignment.get(field) or {}).pop(str(args.at), None)
    manifest["scene_count"] = maximum
    manifest["total_duration"] = round(sum(float(v.get("duration") or 0) for v in scenes.values()), 3)
    manifest["scenes"] = dict(sorted(scenes.items(), key=lambda item: int(item[0])))
    for field in ("signatures", "scenes"):
        bucket = alignment.get(field) or {}
        alignment[field] = dict(sorted(bucket.items(), key=lambda item: int(item[0])))
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    alignment_path.write_text(json.dumps(alignment, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"장면 {args.at + 1}~{maximum + 1} 번호 이동 완료. {args.at}, {args.at + 1}을 다시 생성하세요.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
