#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""EP01 v5 프롬프트의 의미·증거 경계·출력 손상을 독립 검수한다."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import _config  # noqa: F401


ROOT = Path(__file__).resolve().parents[1]
EP = ROOT / "산출물" / "EP01_진시황릉"


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> int:
    scenes = json.loads((EP / "02a.장면구분.json").read_text(encoding="utf-8"))
    durations = json.loads((EP / "audio_v5" / "durations.json").read_text(encoding="utf-8"))["scenes"]
    errors: list[str] = []

    if len(scenes) != len(durations):
        fail(errors, f"장면 수 불일치: 프롬프트 {len(scenes)} / TTS {len(durations)}")
    if [s.get("n") for s in scenes] != list(range(1, len(scenes) + 1)):
        fail(errors, "장면 번호가 1부터 연속되지 않음")

    image_prompts: set[str] = set()
    video_prompts: set[str] = set()
    for scene in scenes:
        n = int(scene["n"])
        src = durations[str(n)]
        image = str(scene.get("img_v2") or "")
        video = str(scene.get("vid") or "")
        text = str(scene.get("txt") or "")
        tts = float(scene.get("tts") or 0)
        omni = int(scene.get("omni") or 0)

        if text != src["text"]:
            fail(errors, f"{n:03d}: 대본 원문이 TTS 잠금본과 다름")
        if abs(tts - float(src["duration"])) > 0.001:
            fail(errors, f"{n:03d}: TTS 길이 불일치")
        if tts > omni:
            fail(errors, f"{n:03d}: TTS {tts:.3f}s가 생성 {omni}s보다 김")
        if not 700 <= len(image) <= 4500:
            fail(errors, f"{n:03d}: 이미지 프롬프트 길이 비정상 {len(image)}자")
        if not 500 <= len(video) <= 5000:
            fail(errors, f"{n:03d}: 영상 프롬프트 길이 비정상 {len(video)}자")
        if "�" in image + video + text:
            fail(errors, f"{n:03d}: 인코딩 손상 문자 발견")
        if image in image_prompts:
            fail(errors, f"{n:03d}: 이미지 프롬프트 중복")
        if video in video_prompts:
            fail(errors, f"{n:03d}: 영상 프롬프트 중복")
        image_prompts.add(image)
        video_prompts.add(video)

        for required in (
            "Ancient China, Qin dynasty, 3rd century BC",
            "9:16 vertical composition",
            "no European or Western faces",
            "no text, no labels, no letters",
        ):
            if required not in image:
                fail(errors, f"{n:03d}: 이미지 필수 잠금 누락 — {required}")
        for required in (
            "supplied locked start image", "preserve all objects", "Single continuous shot",
            "no hard cut", "no new objects", "TTS-locked timing",
        ):
            if required.lower() not in video.lower():
                fail(errors, f"{n:03d}: I2V 필수 잠금 누락 — {required}")

        beats = scene.get("tts_beats") or []
        if not beats or abs(float(beats[0]["start"])) > 0.001 or abs(float(beats[-1]["end"]) - tts) > 0.01:
            fail(errors, f"{n:03d}: TTS 비트가 전체 음성을 덮지 않음")
        joined = "".join(re.sub(r"\s", "", b["narration"]) for b in beats)
        if joined != re.sub(r"\s", "", text):
            fail(errors, f"{n:03d}: TTS 비트 나레이션이 원문을 손실함")

    # v5 서사의 필수 출토품과 보존 근거가 빠지지 않았는지 확인한다.
    all_images = "\n".join(s["img_v2"] for s in scenes).lower()
    required_artifacts = {
        "terracotta army": "병마용",
        "bronze chariot": "청동 수레와 말",
        "acrobat": "백희용",
        "waterfowl": "청동 물새",
        "stone armour": "석갑옷",
        "pigment": "채색·안료",
        "mercury": "수은 측정",
    }
    for term, label in required_artifacts.items():
        if term not in all_images:
            fail(errors, f"필수 시각 대상 누락: {label}")

    # 문헌 장면은 재현임을 밝히고, 미확인/측정 장면은 내부를 열지 않는다.
    for n in (16, 17):
        scene = scenes[n - 1]
        low = (scene["img_v2"] + " " + scene["vid"]).lower()
        if not any(term in low for term in ("textual", "manuscript", "written claim", "conceptual")):
            fail(errors, f"{n:03d}: 문헌기록 재현 경계가 약함")
        if "not excavated" not in low and "rather than presented as excavated" not in low:
            fail(errors, f"{n:03d}: 문헌 장면이 발굴 사실이 아님을 명시하지 않음")
    for n in (18, 20, 25, 26, 27):
        low = (scenes[n - 1]["img_v2"] + " " + scenes[n - 1]["vid"]).lower()
        if not any(term in low for term in ("sealed", "opaque", "no interior", "never opens", "no interior reveal")):
            fail(errors, f"{n:03d}: 미확인 중앙부의 닫힌 경계 누락")
    low19 = (scenes[18]["img_v2"] + " " + scenes[18]["vid"]).lower()
    if "soil" not in low19 or "nothing penetrates" not in low19:
        fail(errors, "019: 수은 측정을 표토 결과로 제한하지 못함")

    # 기계식 쇠뇌는 사기 문헌 장면에서만 허용한다.
    crossbow_scenes = [s["n"] for s in scenes if "crossbow" in (s["img_v2"] + s["vid"]).lower()]
    if crossbow_scenes != [16]:
        fail(errors, f"쇠뇌가 문헌 장면 외에 등장함: {crossbow_scenes}")

    image_blocks = (EP / "flow_images_v5.txt").read_text(encoding="utf-8").count("[SCENE ")
    video_blocks = (EP / "flow_videos_v5.txt").read_text(encoding="utf-8").count("[SCENE ")
    if image_blocks != len(scenes) or video_blocks != len(scenes):
        fail(errors, f"Flow 묶음 수 불일치: 이미지 {image_blocks}, 영상 {video_blocks}")

    print(f"v5 의미 자가검수: 장면 {len(scenes)} / 이미지 {image_blocks} / 영상 {video_blocks}")
    print(f"프롬프트 글자수: 이미지 {min(map(len, image_prompts))}-{max(map(len, image_prompts))}, 영상 {min(map(len, video_prompts))}-{max(map(len, video_prompts))}")
    if errors:
        for error in errors:
            print(f"  FAIL {error}")
        print(f"결과: 실패 {len(errors)}건 — Flow 투입 금지")
        return 1
    print("결과: 통과 — 출력 손상·중복·고증 경계·TTS 불일치 0건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
