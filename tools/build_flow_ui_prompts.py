#!/usr/bin/env python3
"""EP02 마왕퇴한묘 전용 compact Flow image prompts.

The canonical prompts in ``02a.장면구분.json`` remain the audit source.  This
tool removes repeated boilerplate only; it does not rewrite scene evidence.
The compact prompts are short enough to enter through Flow's Slate editor with
real keystrokes, avoiding silent paste truncation.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import _config  # noqa: F401  # Windows 콘솔 UTF-8 설정


DROP_PREFIXES = (
    "premium full-frame archaeological 3D diorama world",
    "Western Han China, early second century BCE",
    "Present-day Chinese archaeology at Mawangdui",
    "East Asian Chinese archaeologists and scientists",
    "Western Han timber tomb architecture",
    "start frame is section-ready",
    "no European or Western faces",
)

STYLE = (
    "9:16 immersive archaeological 3D diorama, PBR microtexture, cinematic "
    "depth, no visible model border."
)
ANCIENT = (
    "Early Western Han Mawangdui, Hunan; Chinese people, Chu black-red lacquer "
    "and silk culture."
)
MODERN = (
    "Mawangdui excavation, China, 1971-1972; Chinese workers and archaeologists "
    "with period-correct clothes and tools."
)
CONSERVATION = (
    "Single Chinese conservation teaching room; one continuous table, no "
    "excavation vignette or split-screen collage."
)
MEDICAL = (
    "Mawangdui evidence in an early-1970s Chinese medical laboratory; Chinese "
    "scientists and period-correct analogue equipment."
)
ARTIFACT_LAB = (
    "Mawangdui, China, 1971-1972 archaeology conservation laboratory; artifact-only "
    "worktable, no people or reenactment."
)
ARCH = (
    "Keep verified earthen shaft, timber chamber and nested-coffin geometry."
)
NEG = (
    "No European, Roman, Egyptian, fantasy or museum case. No text, labels, "
    "hanging scrolls, calligraphy, later-imperial decor, Egyptian mummy "
    "wrapping, bandages, gore or watermark."
)


def compact_image(scene: dict) -> str:
    parts = re.split(r"\.\s+", scene["img_v2"].strip())
    evidence = [p.rstrip(".") for p in parts if p and not p.startswith(DROP_PREFIXES)]
    if not evidence:
        raise ValueError(f"scene {scene['n']:03d}: evidence sentence missing")
    if scene.get("ct") == "CONSERVATION":
        context = CONSERVATION
    elif scene.get("ct") == "SCIENTIFIC_EVIDENCE":
        context = MEDICAL
    elif scene.get("ct") == "TEXT_RECORD" and scene.get("modern_scene"):
        context = ARTIFACT_LAB
    else:
        context = MODERN if scene.get("modern_scene") else ANCIENT
    pieces = [STYLE, context]
    if scene.get("architecture_anchor_required"):
        pieces.append(ARCH)
    pieces.extend(f"{p}." for p in evidence)
    pieces.append(NEG)
    return " ".join(pieces)


def validate(scene: dict, prompt: str) -> list[str]:
    errors: list[str] = []
    required = ("9:16", "3D diorama", "Mawangdui", "No European", "museum case", "no text")
    lower = prompt.lower()
    for token in required:
        if token.lower() not in lower:
            errors.append(f"missing {token!r}")
    if len(prompt) > 950:
        errors.append(f"too long ({len(prompt)} chars)")
    if scene.get("modern_scene") and scene.get("ct") not in {"CONSERVATION", "SCIENTIFIC_EVIDENCE"} and not re.search(r"1971|1972", prompt):
        errors.append("modern scene missing 1971/1972 lock")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("episode", type=Path)
    args = ap.parse_args()

    if args.episode.name != "EP02_마왕퇴한묘":
        ap.error(
            "이 도구는 마왕퇴 전용 문명·연대 문구를 포함합니다. "
            "다른 회차에는 사용하지 마세요."
        )

    src = args.episode / "02a.장면구분.json"
    scenes = json.loads(src.read_text(encoding="utf-8"))
    blocks: list[str] = []
    report: list[dict] = []
    failures: list[str] = []

    for scene in scenes:
        prompt = compact_image(scene)
        errs = validate(scene, prompt)
        if errs:
            failures.append(f"scene {scene['n']:03d}: {', '.join(errs)}")
        blocks.append(f"[SCENE {scene['n']:03d}]\n{prompt}")
        report.append({"n": scene["n"], "chars": len(prompt), "status": "PASS" if not errs else "FAIL"})

    (args.episode / "flow_images_ui_compact.txt").write_text(
        "\n\n".join(blocks) + "\n", encoding="utf-8"
    )
    (args.episode / "flow_images_ui_compact_check.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"compact prompts: {len(scenes)} scenes")
    print(f"length: {min(x['chars'] for x in report)}-{max(x['chars'] for x in report)} chars")
    if failures:
        print("\n".join(failures))
        return 1
    print("self-check: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
