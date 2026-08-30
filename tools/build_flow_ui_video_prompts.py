#!/usr/bin/env python3
"""Build compact, self-audited Flow I2V prompts from the locked storyboard.

The storyboard remains the canonical source.  This tool keeps every scene's
duration, route, TTS beats, start-image lock and world-space graphic intent,
while removing wording that is duplicated across all scenes.  The result is
shorter and safer to type into Flow's Slate editor.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import _config  # noqa: F401  # Windows 콘솔 UTF-8 설정


def _clean(value: object) -> str:
    return " ".join(str(value or "").split()).rstrip(".")


def compact_video(scene: dict) -> str:
    prompt = " ".join(scene["vid"].split())
    prompt = prompt.replace(
        "Use the supplied locked start image and preserve all objects, identities, "
        "provenance, site geometry, artifact fingerprints, materials, culture and lighting.",
        "Preserve the supplied locked start image exactly: objects, identities, "
        "provenance, geometry, artifacts, materials, culture and lighting.",
    )
    duration = int(scene["omni"])
    prompt = prompt.replace(
        f"Single continuous {duration}-second I2V shot",
        f"One continuous {duration}s I2V shot",
    )
    prompt = prompt.replace(
        "Begin physical camera travel within 0.35 seconds.",
        "Begin physical camera travel by 0.35s.",
    )
    prompt = prompt.replace(
        "It receives camera parallax, correct surface perspective, material contact "
        "and natural occlusion.",
        "Give it parallax, surface perspective, material contact and natural occlusion.",
    )
    return prompt


def validate(scene: dict, prompt: str) -> list[str]:
    errors: list[str] = []
    duration = int(scene["omni"])
    lower = prompt.lower()
    required = (
        "locked start image",
        f"continuous {duration}s",
        "0.35s",
        _clean(scene["camera_path"].get("entry_anchor")),
        _clean(scene["camera_path"].get("destination")),
        "tts-locked timing",
        "no hard cut",
        "no voice",
        "subtitles",
    )
    for token in required:
        if token and token.lower() not in lower:
            errors.append(f"missing {token!r}")
    if len(prompt) > 1500:
        errors.append(f"too long ({len(prompt)} chars)")
    beats = scene.get("tts_beats", [])
    timed_beats = re.findall(r"\d+\.\d{2}-\d+\.\d{2}s:", prompt)
    if len(beats) != len(timed_beats):
        errors.append("TTS beat count mismatch")
    if scene.get("veo_graphic"):
        if "physical world space" not in prompt:
            errors.append("world-space 3D evidence graphic missing")
        if "no text" not in lower:
            errors.append("3D graphic scene missing no-text lock")
    camera_path = scene.get("camera_path") or {}
    continuity_fields = (
        "start_frame_anchor_visible", "start_frame_anchor_evidence",
        "single_axis", "scale_domain", "end_state",
    )
    missing_continuity = [field for field in continuity_fields if field not in camera_path]
    if missing_continuity:
        errors.append(f"camera continuity fields missing: {missing_continuity}")
    if camera_path.get("start_frame_anchor_visible") is not True:
        errors.append("selected start-image anchor not visually confirmed")
    expected_states = {4: 2, 6: 3, 8: 3, 10: 4}[duration]
    visual_states = scene.get("visual_states") or []
    if len(visual_states) != expected_states:
        errors.append(f"visual_states must contain {expected_states} states")
    if duration >= 8:
        for token in (
            "start anchor", "mid anchor", "final anchor", "last frame",
            "reset", "loop", "restart",
        ):
            if token not in lower:
                errors.append(f"long-take lock missing {token!r}")
        if not any(token in lower for token in (
            "never return", "remain there", "remain on", "hold there",
        )):
            errors.append("long-take final composition hold missing")
    risky_phrases = (
        "then pull back", "then pull out", "then retreat", "reverse direction",
        "then reverse", "rise then dive", "dive then rise", "orbit then enter",
        "impossible storage",
    )
    found_risks = [phrase for phrase in risky_phrases if phrase in lower]
    if found_risks:
        errors.append(f"camera reversal/scale risk: {found_risks}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("episode", type=Path)
    args = ap.parse_args()

    scenes = json.loads((args.episode / "02a.장면구분.json").read_text(encoding="utf-8"))
    blocks: list[str] = []
    report: list[dict] = []
    failures: list[str] = []

    for scene in scenes:
        prompt = compact_video(scene)
        errors = validate(scene, prompt)
        blocks.append(f"[SCENE {scene['n']:03d}]\n{prompt}")
        report.append(
            {
                "n": scene["n"],
                "duration": scene["omni"],
                "tts_beats": len(scene.get("tts_beats", [])),
                "chars": len(prompt),
                "status": "PASS" if not errors else "FAIL",
                "errors": errors,
            }
        )
        if errors:
            failures.append(f"scene {scene['n']:03d}: {', '.join(errors)}")

    (args.episode / "flow_videos_ui_compact.txt").write_text(
        "\n\n".join(blocks) + "\n", encoding="utf-8"
    )
    (args.episode / "flow_videos_ui_compact_check.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"compact video prompts: {len(scenes)} scenes")
    print(f"length: {min(x['chars'] for x in report)}-{max(x['chars'] for x in report)} chars")
    if failures:
        print("\n".join(failures))
        return 1
    print("self-check: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
