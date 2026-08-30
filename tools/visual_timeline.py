#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Map generated visual scenes onto the approved TTS timeline.

Most episodes use one generated clip per TTS scene.  Long sentences can be
split into two or more visual scenes in ``02a.장면구분.json`` without changing
the approved audio.  Editing and preview tools use this module so those extra
visuals are not silently dropped or shifted.
"""

from __future__ import annotations

import json
from pathlib import Path


def load_visual_timeline(episode: Path, audio_scenes: dict) -> list[dict]:
    """Return a validated, chronological visual plan.

    Falls back to the legacy one-visual-per-audio mapping when the storyboard
    file does not exist.  When a storyboard exists, malformed or incomplete
    mappings are errors because falling back would publish the wrong footage.
    """

    episode = Path(episode)
    storyboard = episode / "02a.장면구분.json"
    audio_keys = [int(k) for k in sorted(audio_scenes, key=int)]

    if not storyboard.exists():
        cursor = 0.0
        rows: list[dict] = []
        for scene in audio_keys:
            duration = float(audio_scenes[str(scene)]["duration"])
            rows.append({
                "visual_scene": scene,
                "audio_scene": scene,
                "audio_part": "1/1",
                "timeline_start": cursor,
                "timeline_end": cursor + duration,
                "duration": duration,
                "audio_offset_start": 0.0,
                "audio_offset_end": duration,
            })
            cursor += duration
        return rows

    raw = json.loads(storyboard.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"비어 있거나 잘못된 장면표: {storyboard}")

    rows = []
    required = {
        "n", "audio_scene", "timeline_start", "timeline_end",
        "audio_offset_start", "audio_offset_end",
    }
    for item in raw:
        if not isinstance(item, dict) or not required.issubset(item):
            missing = sorted(required - set(item if isinstance(item, dict) else {}))
            raise ValueError(f"장면표 필수 필드 누락 {missing}: {storyboard}")
        start = float(item["timeline_start"])
        end = float(item["timeline_end"])
        if end <= start:
            raise ValueError(f"장면 {item['n']} 길이가 0 이하입니다: {start}~{end}")
        rows.append({
            "visual_scene": int(item["n"]),
            "audio_scene": int(item["audio_scene"]),
            "audio_part": str(item.get("audio_part", "1/1")),
            "timeline_start": start,
            "timeline_end": end,
            "duration": end - start,
            "audio_offset_start": float(item["audio_offset_start"]),
            "audio_offset_end": float(item["audio_offset_end"]),
        })

    rows.sort(key=lambda row: row["visual_scene"])
    expected_visuals = list(range(1, len(rows) + 1))
    actual_visuals = [row["visual_scene"] for row in rows]
    if actual_visuals != expected_visuals:
        raise ValueError(f"영상 장면 번호가 연속이 아닙니다: {actual_visuals}")

    mapped_audio = sorted({row["audio_scene"] for row in rows})
    if mapped_audio != audio_keys:
        raise ValueError(
            f"TTS 장면 매핑 불일치: 장면표={mapped_audio}, durations.json={audio_keys}"
        )

    tolerance = 0.05
    previous_end = 0.0
    for row in rows:
        if abs(row["timeline_start"] - previous_end) > tolerance:
            raise ValueError(
                f"영상 장면 {row['visual_scene']} 타임라인에 틈/겹침: "
                f"{previous_end:.3f} -> {row['timeline_start']:.3f}"
            )
        audio_duration = float(audio_scenes[str(row["audio_scene"])]["duration"])
        if row["audio_offset_start"] < -tolerance or row["audio_offset_end"] > audio_duration + tolerance:
            raise ValueError(
                f"영상 장면 {row['visual_scene']}의 TTS 오프셋이 장면 길이를 벗어납니다"
            )
        if abs((row["audio_offset_end"] - row["audio_offset_start"]) - row["duration"]) > tolerance:
            raise ValueError(
                f"영상 장면 {row['visual_scene']}의 오디오 구간과 타임라인 길이가 다릅니다"
            )
        previous_end = row["timeline_end"]

    total_audio = sum(float(audio_scenes[str(scene)]["duration"]) for scene in audio_keys)
    if abs(previous_end - total_audio) > tolerance:
        raise ValueError(
            f"영상 타임라인 총 길이 {previous_end:.3f}s와 TTS {total_audio:.3f}s가 다릅니다"
        )
    return rows

