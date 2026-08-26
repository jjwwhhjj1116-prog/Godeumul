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
    # Scene 15 deliberately moved all interpretation graphics out of the start
    # image.  Keep its UI prompt below Flow's practical failure threshold while
    # retaining both debated routes and their exact TTS timing.
    if scene.get("n") == 15:
        prompt = (
            "Preserve the supplied locked start image exactly: artifact, lacquer "
            "coffin, silk texture, motifs, era, material and lighting. One continuous "
            "8s I2V shot; no hard cut, teleport, morph, new object or identity change. "
            "Begin camera travel by 0.35s at the central funeral motif. Make a fast shallow orbit across the real "
            "painted funeral figures, then snap upward along the banner axis and settle "
            "on the complete unaltered banner. Two thin desaturated silk-light paths "
            "briefly travel inside the painted surface: one follows the funeral figures, "
            "the other the ascending motifs. Both stay anchored in the physical world space "
            "and receive real perspective, depth, "
            "parallax and foreground occlusion, then both fade without choosing a final "
            "interpretation. TTS-locked timing: 0.00-3.06s: follow the funeral reading. 3.06-7.57s: redirect "
            "upward along the soul-journey reading. No panel, plane, HUD or screen overlay. "
            "No text, no labels, no voice, no music, no subtitles and no added object."
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
    if len(prompt) > 1250:
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
