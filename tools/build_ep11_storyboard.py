#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""EP11 네브라 스카이 디스크 — 19개 승인 TTS를 19개 I2V 고증 잠금 화면으로 설계한다."""

from __future__ import annotations

import json
from pathlib import Path

import _config  # noqa: F401


ROOT = Path(__file__).resolve().parents[1]
EPISODE = ROOT / "산출물" / "EP11_네브라스카이디스크"
EPISODE_LABEL = "EP11 네브라 스카이 디스크"
SCENE_COUNT_NOTE = "19개 승인 대본 의미·행동·증거 전환에서 19개 I2V 장면을 1:1로 도출했다."

STYLE = (
    "premium full-frame cinematic archaeological 3D diorama, unmistakably a museum-scale crafted miniature world and not live-action, "
    "realistic historical architectural CG restoration, immersive macro-lens depth, restrained tilt-shift, layered foreground-midground-background, "
    "physically based PBR bronze, pure gold inlay, patinated oxidized metal, forest soil and stone microtexture, razor-sharp artifact separation, global illumination, "
    "high fidelity 4K source detail, 9:16 vertical composition"
)
ANCIENT_CIV = (
    "European Bronze Age in the seventeenth to sixteenth century BCE (circa 1600 BCE), Unetice culture, the forested hill plateau of Mittelberg near Nebra, Saxony-Anhalt, Central Germany"
)
MODERN_CIV = (
    "Documented German archaeological investigation and recovery: the 1999 illicit metal-detector discovery in the Mittelberg forest, "
    "the 2002 Basel hotel police sting operation led by archaeologist Harald Meller, and subsequent scientific laboratory analysis at the Halle State Museum of Prehistory"
)
ANCIENT_PEOPLE = (
    "Central European Bronze Age people with period-correct woven wool or linen tunics, leather belts, bronze spiral armlets, and authentic bronze tools"
)
MODERN_PEOPLE = (
    "German and Swiss archaeologists in practical 1999-2002 field clothing and modern museum conservators in white lab coats and gloves"
)
ANCIENT_ARCH = (
    "Mittelberg forested hill summit (elevation 252m) with low circular earthen ditch rampart, small stone-lined hoard pit, ancient bronze workshop with charcoal smelting hearth, and dark museum conservation laboratory"
)
NEGATIVE = (
    "no Roman toga, no medieval plate armor, no Viking horned helmets, no Chinese or Japanese architecture, no Joseon costume, no fantasy treasure room, "
    "no alien figures or UFO spaceships, no sci-fi hologram, no magical levitation, no polished new brass disc, no invented complete inscription, no readable generated Korean or Chinese, "
    "no pseudo-writing, no floating HUD, no modern object in ancient scenes, no plastic toy surface, no low-poly game asset, no exterior cube frame, "
    "no ancient costume on modern researchers, no gore, no watermark, no text, no labels, no letters"
)

LOCK_BASE = {
    "civilization": "Central European Bronze Age Unetice culture and documented Mittelberg archaeology",
    "era": "circa 1600 BCE European Bronze Age, with 1999-2002 discovery and recovery context",
    "region": "Mittelberg hill near Nebra, Saxony-Anhalt, Germany",
    "people_lock": "Central European Bronze Age people in period-correct garments; documented German archaeologists and conservators after 1999",
    "forbidden_culture": ["Roman", "medieval", "Viking", "Chinese", "Japanese", "Joseon", "fantasy", "alien"],
    "artifact_lock": (
        "one real-form Nebra Sky Disc: thirty-centimetre dark oxidized patina bronze circular plate inlaid with pure gold full moon, "
        "thick crescent moon, thirty-two gold stars including seven-star Pleiades cluster, eighty-two degree gold horizon arc, gold solar ship curve at bottom, perimeter perforation holes"
    ),
    "diorama_style": "CINEMATIC_ARCHAEOLOGICAL_DIORAMA",
    "material_fidelity": "PBR_MICROTEXTURE_HIGH_FIDELITY",
}
MODERN_LOCK_UPDATE = {
    "civilization": "Documented 1999-2002 German archaeological discovery, recovery and Halle museum conservation",
    "era": "1999 discovery, 2002 Basel sting operation, and present-day museum analysis only",
    "people_lock": "German and Swiss archaeologists, police investigators, and museum conservators in exact modern work clothing",
}


def cam(entry: str, route: str, destination: str, speed: str, operator: str, depth: str,
        settle: str, axis: str = "FORWARD", scale: str = "MEDIUM", *interrupts: str) -> dict[str, object]:
    return {
        "entry_anchor": entry,
        "route": route,
        "destination": destination,
        "speed_profile": speed,
        "operator_style": operator,
        "depth_transition": depth,
        "pattern_interrupts": list(interrupts),
        "settle_point": settle,
        "single_axis": axis,
        "scale_domain": scale,
        "start_frame_anchor_visible": True,
        "start_frame_anchor_evidence": f"The locked image prompt visibly places {entry} at the opening camera position.",
        "end_state": f"Last frame holds the unchanged composition on {settle}.",
    }


def graphic(function: str, evidence: str, language: str, start: str, via: list[str], end: str,
            arrival: str) -> dict[str, object]:
    return {
        "function": function,
        "evidence_relation": evidence,
        "visual_language": language,
        "start": start,
        "via": via,
        "end": end,
        "occlusion": "the graphic passes behind the bronze disc rim, soil edge, tool, or laboratory stand in world space and reappears with correct parallax",
        "timing": "emerge only during the matching narration beat, travel through named anchors in physical world space, settle, then fade before the end; no floating HUD and no text",
        "camera_relation": "anchored to named physical surfaces in world space with correct perspective, depth, lighting, reflections, occlusion and camera parallax; no floating HUD and no text",
        "arrival_reaction": arrival,
    }


def spec(n: int, audio_scene: int, timeline: tuple[float, float], chapter: str, ct: str,
         txt: str, evidence: str, mode: str, is_modern: bool,
         motion_owner: str, motion_space: str, cam_path: dict[str, object],
         site_fingerprints: list[str], image_scene: str, i2v_action: str,
         beats: list[tuple[float, float, str, str, str, str]],
         states: list[tuple[float, str, str, list[str]]],
         flow_account: str = "jy04210810@gmail.com",
         arch_required: bool = True,
         graphic_spec: dict[str, object] | None = None,
         custom_lock: dict[str, object] | None = None,
         seconds: int = 8,
         visibility: str = "IDENTIFIABLE",
         routing_reason: str = "",
         ref_ids: list[str] | None = None) -> dict[str, object]:
    t_start, t_end = timeline
    duration = round(t_end - t_start, 3)

    lock = dict(LOCK_BASE)
    if is_modern:
        lock.update(MODERN_LOCK_UPDATE)
    if custom_lock:
        lock.update(custom_lock)
    lock["source_reference"] = "Landesmuseum für Vorgeschichte Halle official record"
    lock["site_artifact_fingerprint"] = site_fingerprints

    full_cam = dict(cam_path)

    civ = MODERN_CIV if is_modern else ANCIENT_CIV
    people = MODERN_PEOPLE if is_modern else ANCIENT_PEOPLE
    arch = ANCIENT_ARCH

    img_prompt = (
        f"{STYLE}. {civ}. {arch}. {image_scene} "
        f"the start frame already contains a physically visible section seam, depth layers and an empty camera route; no geometry may be invented later. "
        f"{NEGATIVE}. If any human figure is visible, it must be {people}."
    )

    world_space_clause = ""
    if graphic_spec:
        world_space_clause = "Integrated graphical motion operates along the designated path route strictly in physical world space with correct depth occlusion; no floating HUD and no text. "

    rigid_lock_clause = ""
    if visibility == "IDENTIFIABLE":
        rigid_lock_clause = "Keep the exact supplied reference artifact completely rigid with no redesign and no changed part count. "

    vid_prompt = (
        "Use the supplied locked start image and preserve every object, identity, artifact fingerprint, provenance, "
        f"site geometry, material, culture, lighting and composition. Single continuous {seconds}-second I2V shot, no hard cut, no teleport, no morph, no new objects. "
        f"{rigid_lock_clause}"
        f"Begin physical camera travel within 0.35 seconds. Enter at {full_cam['entry_anchor']}; "
        f"travel {full_cam['route']}; arrive at {full_cam['destination']}; settle on {full_cam['settle_point']}. "
        f"{i2v_action} {world_space_clause}"
        f"TTS-locked timing: 0.00-{seconds/2:.2f}s: {beats[0][2]}. {seconds/2:.2f}-{seconds:.2f}s: {beats[1][2]}. "
        "Preserve all objects from the start image. No voice, no music, no subtitles. "
        f"Start anchor: {full_cam['entry_anchor']} is already visible in the locked first frame. "
        f"Mid anchor: remain on the same {full_cam['single_axis'].lower()} axis through {full_cam['route']}. "
        f"Final anchor: arrive once at {full_cam['destination']}. "
        f"Last frame: {full_cam['end_state']} "
        "No cut, reset, loop or restart; never return to an earlier composition; remain on the final anchor and hold there."
    )

    row: dict[str, object] = {
        "n": n,
        "audio_scene": audio_scene,
        "audio_part": "1/1",
        "audio_offset_start": t_start,
        "audio_offset_end": t_end,
        "timeline_start": t_start,
        "timeline_end": t_end,
        "chapter": chapter,
        "ct": ct,
        "txt": txt,
        "tts": duration,
        "omni": seconds,
        "playback_speed": round(seconds / duration, 4) if duration > seconds else 1.0,
        "evidence": evidence,
        "generation_mode": mode,
        "artifact_visibility": visibility,
        "routing_reason": routing_reason,
        "architecture_anchor_required": arch_required,
        "modern_scene": is_modern,
        "motion_owner": motion_owner,
        "motion_space": motion_space,
        "camera_path": full_cam,
        "visual_lock": lock,
        "visual_states": [
            {
                "time": st[0],
                "composition": st[1],
                "camera_pose": st[2],
                "visible_anchors": st[3],
            }
            for st in states
        ],
        "tts_beats": [
            {
                "start": b[0],
                "end": b[1],
                "narration": b[2],
                "camera": b[3],
                "action": b[4],
                "graphic": b[5],
            }
            for b in beats
        ],
        "img_v2": img_prompt,
        "vid": vid_prompt,
        "image_scene_prompt": image_scene,
        "i2v_action_prompt": i2v_action,
        "status": "PROMPT_LOCKED_IMAGE_PENDING",
        "flow_account": flow_account,
    }
    if visibility == "IDENTIFIABLE":
        row["artifact_form_policy"] = "SOURCE_PHOTO_GEOMETRY_LOCK"
        row["artifact_reference_ids"] = ref_ids if ref_ids is not None else ["FORM_OWNER_NEBRA_FRONT"]
        row["allowed_artifact_changes"] = ["camera", "lighting"]
        row["forbidden_artifact_changes"] = ["silhouette", "proportion", "part_count", "ornament_layout"]
    else:
        row["artifact_reference_ids"] = []

    if duration > 9.0:
        row["long_scene_review"] = (
            "The narration is one indivisible claim-and-evidence unit in one physical location; "
            "two timed camera interruptions preserve pace without a semantic or spatial reset."
        )
    if graphic_spec:
        row["veo_integrated_graphic"] = graphic_spec
        row["veo_graphic"] = graphic_spec
    return row


def build_scenes() -> list[dict[str, object]]:
    scenes: list[dict[str, object]] = []

    # Scene 001
    scenes.append(spec(
        1, 1, (0.0, 6.4), "1. 숲속의 녹슨 원판", "DISCOVERY_ACTION",
        "독일 깊은 숲속 땅밑에서, 3,600년 동안 잠들어 있던 직경 30센티미터의 녹슨 청동 원판이 발견됐습니다.",
        "발굴확인", "I2V_LOCKED", True, "GENERATED_PHYSICS", "WORLD_3D",
        cam("forested soil surface with exposed stone edge", "descend through forest tree canopy toward the stone-lined pit", "partly exposed patinated bronze rim", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "IMMERSIVE_POV_DOLLY", "SECTION_DIVE", "exposed bronze rim in dark humus soil", "FORWARD", "MEDIUM", "1.5s canopy dive", "4.8s soil slide"),
        ["dark forest soil", "stone-lined pit edge", "partly exposed green patinated bronze disc"],
        "Macro cutaway archaeological diorama of the Mittelberg forest floor near Nebra: dense pine and oak roots, dark humus soil, and a stone-lined pit where the thirty-centimetre patinated green bronze disc emerges catching cool morning daylight.",
        "Descend rapidly from the pine canopy into the excavated forest soil pit, tracking across dark humus and tree roots along the exposed path route to settle on the thirty-centimetre green patinated bronze disc rim.",
        [(0.0, 3.2, "독일 깊은 숲속 땅밑에서 3,600년 동안 잠들어 있던", "Rapid descent from forest canopy to soil", "Soil grains part around stone edge", "none"),
         (3.2, 6.4, "직경 30센티미터의 녹슨 청동 원판이 발견됐습니다.", "Macro track to bronze rim", "Glint of gold under green patina", "none")],
        [(0.0, "Wide forest canopy cutaway", "High angle 45°", ["pine canopy", "forest ground"]),
         (4.0, "Mid-level root cross-section", "Medium dive", ["soil layer", "stone pit"]),
         (8.0, "Macro bronze rim settlement", "Low angle macro", ["bronze rim", "dark humus"])],
        seconds=8, visibility="NON_IDENTIFIABLE", routing_reason="1999년 도굴 구덩이 속 녹슨 원판 발견 맥락을 승인 프레임으로 잠그는 장면", ref_ids=[]
    ))

    # Scene 002
    scenes.append(spec(
        2, 2, (6.4, 15.2), "1. 숲속의 녹슨 원판", "ARTIFACT_MACRO",
        "표면에는 순금으로 박아 넣은 태양과 초승달, 밤하늘의 별들이 가득했죠. 바로 인류 역사상 가장 오래된 구체적인 천문도, 네브라 스카이 디스크였습니다.",
        "발굴확인", "I2V_LOCKED", False, "GENERATED_PHYSICS", "WORLD_3D",
        cam("patinated green bronze surface", "macro orbit across inlaid gold full moon and crescent", "entire celestial disk layout", "CONTROLLED_ORBIT_REVEAL", "MACRO_PROBE", "ORBIT_REVEAL", "complete hero gold constellation layout", "ORBIT", "MACRO", "2.2s gold glint burst", "5.5s Pleiades cluster focus"),
        ["dark green patina bronze plate", "pure gold full moon inlay", "gold crescent moon", "gold stars"],
        "Hero three-quarter macro portrait archaeological diorama of the real-form Nebra Sky Disc on a dark museum stand: pure gold inlaid sun, thick crescent moon, thirty-two gold stars glowing under volumetric light against dark patinated green bronze.",
        "Orbit closely across the dark green patinated surface as the inlaid pure gold full moon, thick crescent moon, and clustered stars reflect razor-sharp volumetric lighting along the orbit path route, settling on the full celestial composition.",
        [(0.0, 4.4, "표면에는 순금으로 박아 넣은 태양과 초승달, 밤하늘의 별들이 가득했죠.", "Close macro orbit on gold inlays", "Gold texture glints against patina", "none"),
         (4.4, 8.8, "바로 인류 역사상 가장 오래된 구체적인 천문도, 네브라 스카이 디스크였습니다.", "Pull back to full hero view", "Volumetric beam illuminates disc", "none")],
        [(0.0, "Close macro on gold moon", "Close macro probe", ["gold sun", "gold crescent"]),
         (3.3, "Half-orbit across stars", "Medium orbit", ["Pleiades cluster", "green patina"]),
         (6.6, "Wide three-quarter disc view", "Wide orbit", ["30cm plate", "gold inlays"]),
         (10.0, "Full hero composition", "Hero three-quarter", ["entire 30cm disc", "stand"])],
        seconds=10, visibility="IDENTIFIABLE", routing_reason="실물 네브라 디스크의 청동 원판과 순금 태양, 초승달, 별들을 식별하는 장면"
    ))

    # Scene 003
    scenes.append(spec(
        3, 3, (15.2, 23.1), "1. 숲속의 녹슨 원판", "SITE_ESTABLISH",
        "글자조차 없던 청동기 시대에 만들어진 물건이거든요. 도대체 3천 년 전 고대인들은 왜 이런 정밀한 우주를 새겨 땅속에 묻었던 걸까요?",
        "학술해석", "I2V_LOCKED", False, "VEO_INTEGRATED_3D", "WORLD_3D",
        cam("gold disc edge on dark altar stone", "crane rise over Bronze Age forested settlement", "misted Mittelberg hill summit", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CRANE_ORBIT_REVEAL", "SECTION_DIVE", "misted hill horizon and glowing bronze disc", "FORWARD", "WIDE", "2.5s settlement reveal", "5.8s celestial beam alignment"),
        ["Mittelberg hill summit", "Bronze Age timber longhouse", "glowing Nebra sky disc on altar"],
        "Atmospheric Bronze Age hill-summit archaeological diorama at Mittelberg: timber longhouses, low circular earthen enclosure, evening mist over ancient pine forest, with the Nebra Sky Disc resting on a dark ceremonial stone pedestal.",
        "Crane upward from the glowing sky disc on the ceremonial stone along the vertical path route, sweeping across the misted Bronze Age timber settlement and forest ramparts to open the central historical question.",
        [(0.0, 3.9, "글자조차 없던 청동기 시대에 만들어진 물건이거든요.", "Crane upward from disc to settlement", "Mist rolls across timber huts", "none"),
         (3.9, 7.9, "도대체 3천 년 전 고대인들은 왜 이런 정밀한 우주를 새겨 땅속에 묻었던 걸까요?", "Wide horizon sweep over Mittelberg", "Atmospheric evening sky darkens", "none")],
        [(0.0, "Disc on stone altar", "Low altar close-up", ["sky disc", "altar stone"]),
         (4.0, "Mittelberg settlement overview", "High crane wide", ["timber huts", "earthen ditch"]),
         (8.0, "Forested summit under twilight", "Extreme wide diorama", ["ancient forest", "twilight horizon"])],
        graphic_spec=graphic("SCAN_WAVE", "학술해석: 청동기 우네티체 문화권과 미텔베르크 유적의 공간적 경계", "red holographic horizon ray and coordinate beam", "altar stone", ["settlement roof", "forest boundary"], "twilight sky", "pulses red question beacon over the hill summit"),
        seconds=8, visibility="IDENTIFIABLE", routing_reason="문자 없는 청동기 시대 배경과 유물 자체의 중심 질문을 함께 보여주는 장면"
    ))

    # Scene 004
    scenes.append(spec(
        4, 4, (23.1, 32.2), "2. 규모의 충격과 모순", "ARTIFACT_MACRO",
        "자, 손바닥 두 개만 한 청동판을 조금 더 들여다보죠. 원판 중심에는 둥근 태양과 굵은 초승달이 있고, 그 곁으로 서른두 개의 황금 별이 흩어져 있습니다.",
        "측정확인", "I2V_LOCKED", False, "GENERATED_PHYSICS", "WORLD_3D",
        cam("entire thirty-centimetre disc surface", "straight macro push-in toward disc center", "central sun and crescent cluster", "MACRO_PROBE_SETTLE", "MACRO_PROBE", "SURFACE_TO_INTERIOR", "geometric center of thirty-two stars", "FORWARD", "MACRO", "2.0s sun dimension line", "5.2s 32 stars point tags"),
        ["central gold sun", "thick gold crescent", "thirty-two gold star inlays", "bronze patina texture"],
        "Top-down isometric forensic archaeological diorama of the Nebra Sky Disc: razor-sharp macro view of the central hammered gold full moon, thick gold crescent moon, and thirty-two individual gold star inlays with subtle lighting separation.",
        "Push straight down from the full thirty-centimetre disc along the central path route into the star cluster, revealing the hand-hammered gold grain of the sun, crescent, and individual star points with subtle physical lighting.",
        [(0.0, 4.5, "자, 손바닥 두 개만 한 청동판을 조금 더 들여다보죠.", "Direct vertical dolly-in", "Physical scale comparison cues appear", "none"),
         (4.5, 9.1, "원판 중심에는 둥근 태양과 굵은 초승달이 있고, 그 곁으로 서른두 개의 황금 별이 흩어져 있습니다.", "Macro probe across star coordinates", "Gold hammer facets catch light", "none")],
        [(0.0, "Full top-down disc view", "Top-down 90°", ["30cm plate", "all inlays"]),
         (3.3, "Medium push to central cluster", "Top-down 75°", ["sun inlay", "crescent moon"]),
         (6.6, "Close macro probe on stars", "Macro probe 65°", ["hammered gold", "star points"]),
         (10.0, "Tight macro on 32 star coordinates", "Macro probe 60°", ["hammered gold facets", "stars"])],
        seconds=10, visibility="IDENTIFIABLE", routing_reason="원판 중심의 태양, 굵은 초승달, 32개 별 배치를 형태 소유자와 정밀 대조하는 장면"
    ))

    # Scene 005
    scenes.append(spec(
        5, 5, (32.2, 40.7), "2. 규모의 충격과 모순", "DIAGRAM",
        "특히 일곱 개가 뭉친 무리는 밤하늘의 플레이아데스 성단이었죠. 심지어 양쪽 가장자리에는 정확히 82도 각도를 이루는 황금 호가 붙어 있었습니다.",
        "측정확인", "I2V_LOCKED", False, "VEO_INTEGRATED_3D", "WORLD_3D",
        cam("seven-star Pleiades cluster", "lateral track to lateral gold horizon arc", "82-degree measured arc apex", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "MACRO_PROBE", "NONE", "82.0-degree geometric horizon arc", "LATERAL", "MACRO", "2.4s Pleiades target ring", "5.6s 82-degree angle arc projection"),
        ["seven-star Pleiades cluster", "gold horizon arc", "82-degree geometric angle lines"],
        "Technical diagnostic archaeological diorama of the Nebra Sky Disc: red laser circle highlighting the tight seven-star Pleiades cluster, tracking laterally to the curved gold horizon band with sharp red laser lines projecting an exact 82-degree angle.",
        "Track laterally from the glowing seven-star Pleiades cluster along the rim path route across the dark bronze surface to the gold horizon band, projecting an exact 82.0-degree geometric ray cone from the disc center.",
        [(0.0, 4.2, "특히 일곱 개가 뭉친 무리는 밤하늘의 플레이아데스 성단이었죠.", "Close focus on 7-star cluster", "Target reticle snaps to Pleiades", "none"),
         (4.2, 8.5, "심지어 양쪽 가장자리에는 정확히 82도 각도를 이루는 황금 호가 붙어 있었습니다.", "Lateral slide to horizon arc", "Red angular rays project outward", "none")],
        [(0.0, "Pleiades 7-star close-up", "Macro tight", ["7 stars", "patina"]),
         (4.0, "Lateral slide across disc rim", "Medium lateral", ["disc rim", "gold band"]),
         (8.0, "82-degree geometric projection", "Three-quarter diagnostic", ["82° ray lines", "horizon arc"])],
        graphic_spec=graphic("DIMENSION_LINE", "측정확인: 실측 82.0도 중심각과 7성단 배치 구조", "thin red laser angle arc and target rings", "Pleiades cluster", ["disc center"], "horizon arc rim", "locks onto 82.0-degree angular ray overlay"),
        seconds=8, visibility="IDENTIFIABLE", routing_reason="플레이아데스 7성단과 82도 황금 지평선 호를 식별하고 각도를 투사하는 장면"
    ))

    # Scene 006
    scenes.append(spec(
        6, 6, (40.7, 49.6), "2. 규모의 충격과 모순", "HISTORICAL_RECONSTRUCTION",
        "당시 유럽은 문자 기록 하나 남기지 못한 시대였거든요. 그런 청동기인들이 정밀한 각도와 별자리를 담아냈다는 사실 자체가 상식을 깨는 모순이었던 겁니다.",
        "학술해석", "I2V_LOCKED", False, "GENERATED_PHYSICS", "WORLD_3D",
        cam("ancient bronze artisan hands holding disc", "slow upward orbit to Bronze Age workshop exterior", "forested mountain backdrop", "CONTROLLED_ORBIT_REVEAL", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "NONE", "Bronze Age artisan looking from disc to night sky", "ORBIT", "MEDIUM", "2.8s artisan hand detail", "6.0s night sky comparison"),
        ["Bronze Age artisan hands", "hammered bronze disc", "stone smelting forge", "starry night sky"],
        "Dramatic split-depth archaeological diorama: in the foreground, a Bronze Age artisan in linen tunic holds the glowing Nebra Sky Disc; in the background, a primitive timber forge and the vast real night sky contrast with the sophisticated astronomical artifact.",
        "Slowly orbit around the artisan's hands holding the finished sky disc along the circular path route, rising to frame the primitive charcoal forge against the glittering real cosmos above to dramatize the historical contradiction.",
        [(0.0, 4.4, "당시 유럽은 문자 기록 하나 남기지 못한 시대였거든요.", "Focus on raw artisan tools and forge", "Charcoal embers rise softly", "none"),
         (4.4, 8.9, "그런 청동기인들이 정밀한 각도와 별자리를 담아냈다는 사실 자체가 상식을 깨는 모순이었던 겁니다.", "Orbit to frame disc against real stars", "Gold inlays catch moonlight", "none")],
        [(0.0, "Artisan hands with disc", "Low-angle close-up", ["artisan tunic", "sky disc"]),
         (4.0, "Charcoal forge and timber hut", "Mid-level orbit", ["stone forge", "sparks"]),
         (8.0, "Disc aligned with real cosmos", "Wide dramatic three-quarter", ["real night sky", "artisan profile"])],
        seconds=8, visibility="IDENTIFIABLE", routing_reason="문자 없는 시대와 정밀 천문관측의 상식적 모순을 원판 세부와 함께 식별하는 장면"
    ))

    # Scene 007
    scenes.append(spec(
        7, 7, (49.6, 58.7), "3. 도굴과 극적 회수", "DISCOVERY_ACTION",
        "이야기는 1999년, 독일 미텔베르크 숲에서 도굴꾼들이 금속탐지기로 흙을 파헤치며 시작됩니다. 청동 검과 도끼 틈에서 녹슨 쟁반 같은 것이 딸려 나왔죠.",
        "발굴확인", "I2V_LOCKED", True, "GENERATED_PHYSICS", "WORLD_3D",
        cam("1999 night forest floor with flashlight beam", "descend into the illicit digger shovel pit", "tangled hoard of bronze swords, axes and disc", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "IMMERSIVE_POV_DOLLY", "SECTION_DIVE", "illicit hoard find position in dark soil", "FORWARD", "MEDIUM", "2.0s shovel strike", "5.4s metal detector beep cue"),
        ["Mittelberg night forest", "metal detector coil", "illicit shovel pit", "bronze swords", "bronze axes", "corroded green disc"],
        "Atmospheric 1999 night excavation archaeological diorama in Mittelberg forest: flashlight beams cut through dark trees, an illicit metal detector coil sweeps over roots, and a shovel exposes a stone-lined pit containing two Bronze Age swords, two axes, and the corroded sky disc.",
        "Dive into the illicit night excavation pit along the vertical shovel path route as dark forest soil is scraped away, revealing the tangled hoard of two bronze swords, two axe heads, and the corroded green disc.",
        [(0.0, 4.5, "이야기는 1999년, 독일 미텔베르크 숲에서 도굴꾼들이 금속탐지기로 흙을 파헤치며 시작됩니다.", "Follow metal detector sweep at night", "Flashlight beam cuts dark pine roots", "none"),
         (4.5, 9.1, "청동 검과 도끼 틈에서 녹슨 쟁반 같은 것이 딸려 나왔죠.", "Descend into fresh shovel pit", "Shovel exposes corroded hoard", "none")],
        [(0.0, "Night forest search with detector", "POV detector sweep", ["flashlight cone", "pine roots"]),
         (3.3, "Fresh soil cutaway pit", "Low pit dive", ["shovel blade", "disturbed soil"]),
         (6.6, "Stone cavity exposure", "Mid cavity dive", ["cavity stones", "soil"]),
         (10.0, "Hoard exposed in stone cavity", "Macro cavity hold", ["swords", "axes", "green disc"])],
        seconds=10, visibility="NON_IDENTIFIABLE", routing_reason="1999년 미텔베르크 숲속 불법 도굴꾼의 금속탐지기 발굴 현장을 재현하는 장면", ref_ids=[]
    ))

    # Scene 008
    scenes.append(spec(
        8, 8, (58.7, 68.0), "3. 도굴과 극적 회수", "HISTORICAL_RECONSTRUCTION",
        "도굴꾼들은 흙을 털어내고 암시장에 헐값으로 넘겼습니다. 유물은 암흑가를 떠돌다 2002년 스위스 바젤에서 고고학자와 경찰의 함정 수사 끝에 극적으로 회수됐죠.",
        "문헌기록", "I2V_LOCKED", True, "GENERATED_PHYSICS", "WORLD_3D",
        cam("leather briefcase on hotel room table", "dolly across black market briefcase to police badge and archaeologist", "secured Nebra disc on table center", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "NONE", "recovered Nebra disc under bright hotel lamp", "LATERAL", "MEDIUM", "2.2s briefcase snap open", "5.6s police badge reveal"),
        ["Basel hotel room diorama", "open black leather briefcase", "Swiss/German police badge", "archaeologist Harald Meller"],
        "Documented 2002 sting operation archaeological diorama in a Basel hotel room: warm lamplight illuminates an open black leather briefcase containing the damaged Nebra disc, with police badges and archaeologist Harald Meller inspecting the authentic artifact.",
        "Dolly across the tense hotel room table along the horizontal path route from the open black market briefcase to the recovered Nebra Sky Disc, settling as archaeologist Harald Meller confirms the authentic gold inlays under police guard.",
        [(0.0, 4.6, "도굴꾼들은 흙을 털어내고 암시장에 헐값으로 넘겼습니다.", "Track across open briefcase lining", "Black market cash and scratches visible", "none"),
         (4.6, 9.3, "유물은 암흑가를 떠돌다 2002년 스위스 바젤에서 고고학자와 경찰의 함정 수사 끝에 극적으로 회수됐죠.", "Pan to police badge and archaeologist", "Forensic lamp illuminates disc", "none")],
        [(0.0, "Briefcase on hotel table", "Medium table dolly", ["leather case", "currency"]),
         (3.3, "Disc lifted onto white cloth", "Close table view", ["damaged disc", "cloth"]),
         (6.6, "Archaeologist inspection", "Medium profile view", ["magnifying glass", "conservator"]),
         (10.0, "Secured artifact under lamp", "Three-quarter investigation", ["recovered disc", "police badge"])],
        seconds=10, visibility="NON_IDENTIFIABLE", routing_reason="2002년 스위스 바젤 호텔에서의 극적인 위장 함정 수사 회수 현장을 보여주는 장면", ref_ids=[]
    ))

    # Scene 009
    scenes.append(spec(
        9, 9, (68.0, 74.6), "3. 도굴과 극적 회수", "CONSERVATION",
        "학자들은 단 하나의 질문에 매달렸습니다. 문명도 없던 시대에 도대체 누가, 무엇을 위해 이 천문판을 만들었는가?",
        "학술해석", "I2V_LOCKED", True, "GENERATED_PHYSICS", "WORLD_3D",
        cam("Halle museum laboratory workbench", "slow macro zoom into disc center under microscope ring light", "forensic microscope objective lens", "MACRO_PROBE_SETTLE", "MACRO_PROBE", "SECTION_DIVE", "patina boundary under forensic microscope", "FORWARD", "MACRO", "2.0s microscope ring light on", "4.8s question text pulse"),
        ["Halle state museum laboratory", "stereomicroscope", "gloved conservator hands", "precision calipers"],
        "State-of-the-art conservation laboratory archaeological diorama at Halle State Museum: gloved German conservators operate precision stereomicroscopes and spectral lights over the secured Nebra Sky Disc on a neutral conservation foam cradle.",
        "Zoom smoothly along the optical path route of a forensic microscope ring light into the patinated gold boundary of the Nebra disc, framing the central scholarly inquiry.",
        [(0.0, 3.3, "학자들은 단 하나의 질문에 매달렸습니다.", "Microscope ring light illuminates disc", "Gloved hands position optical probe", "none"),
         (3.3, 6.6, "문명도 없던 시대에 도대체 누가, 무엇을 위해 이 천문판을 만들었는가?", "Deep optical dive into gold inlay seam", "Cross-section microtexture visible", "none")],
        [(0.0, "Museum laboratory wide", "Lab overview 45°", ["microscopes", "lab benches"]),
         (4.0, "Optical ring light close-up", "Macro dive", ["ring light", "disc cradle"]),
         (8.0, "Microscope optical center", "Extreme macro probe", ["gold inlay seam", "patina"])],
        seconds=8, visibility="IDENTIFIABLE", routing_reason="박물관 연구실에서 실물 원판을 현미경 및 측정 도구로 조사하는 장면"
    ))

    # Scene 010
    scenes.append(spec(
        10, 10, (74.6, 81.5), "4. 가설 붕괴와 무역망", "SCIENTIFIC_EVIDENCE",
        "그냥 밤하늘을 본뜬 제사용 장식품 아니냐고요? 하지만 수치를 재자마자 단순한 장식품이라는 가설은 산산조각이 났습니다.",
        "측정확인", "I2V_LOCKED", True, "VEO_INTEGRATED_3D", "WORLD_3D",
        cam("blue 3D laser scanner line on disc", "rapid sweep across the disc surface with point cloud mesh", "shattering decorative hypothesis graphic", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "NONE", "dense 3D point cloud coordinate grid", "LATERAL", "MEDIUM", "1.8s laser scan sweep", "4.5s red X on decorative label"),
        ["3D laser scanner arm", "blue laser line", "coordinate mesh overlay", "precision calibration target"],
        "High-tech forensic laboratory archaeological diorama: a blue 3D coordinate laser line sweeps across the Nebra disc, generating a luminous point cloud mesh while disproving the simple decorative hypothesis.",
        "Sweep a blue coordinate laser beam along the scanning path route across the disc surface, building an accurate 3D point cloud mesh that instantly disproves the simple decorative ornament hypothesis.",
        [(0.0, 3.5, "그냥 밤하늘을 본뜬 제사용 장식품 아니냐고요?", "Blue laser line sweeps across disc", "3D coordinate mesh builds upward", "none"),
         (3.5, 6.9, "하지만 수치를 재자마자 단순한 장식품이라는 가설은 산산조각이 났습니다.", "Laser points turn red with precision metrics", "Hypothesis label shatters with red X", "none")],
        [(0.0, "Laser scanner arm on disc", "Laboratory three-quarter", ["laser arm", "blue line"]),
         (4.0, "Coordinate mesh build-up", "Macro surface sweep", ["point cloud", "gold inlays"]),
         (8.0, "Forensic data verification", "Diagnostic hold", ["measurement grid", "shattered icon"])],
        graphic_spec=graphic("SCAN_WAVE", "측정확인: 정밀 3D 스캔 측정 기반 단순 장식설 반증", "blue-white 3D coordinate laser grid and red geometric boundary", "laser arm emitter", ["disc center", "rim"], "diagnostic screen", "shatters decorative hypothesis icon with technical metrics"),
        seconds=8, visibility="IDENTIFIABLE", routing_reason="단순 장식품 가설을 깨고 정밀 3D 스캔 및 각도 측정을 개시하는 장면"
    ))

    # Scene 011
    scenes.append(spec(
        11, 11, (81.5, 88.4), "4. 가설 붕괴와 무역망", "MECHANISM",
        "계산해 보니, 82도 황금 호는 네브라 지역에서 하지와 동지에 해가 뜨고 지는 지평선 각도와 소수점까지 일치했거든요.",
        "측정확인", "I2V_LOCKED", False, "VEO_INTEGRATED_3D", "WORLD_3D",
        cam("Mittelberg hill horizon panorama diorama", "celestial solar ray tracking from summer to winter solstice", "Nebra disc horizon arc alignment", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "perfect 82.5-degree solstice ray match", "ORBIT", "WIDE", "2.2s summer solstice sunset beam", "5.4s winter solstice sunset beam"),
        ["Mittelberg terrain diorama", "summer solstice sunset ray", "winter solstice sunset ray", "82.5-degree angle cone"],
        "Landscape astronomical simulation archaeological diorama: from the Mittelberg hill summit (51.3°N), two glowing sun paths for Summer Solstice sunset and Winter Solstice sunset project outward along the horizon route, matching the Nebra disc's 82.5-degree golden arc to the decimal.",
        "Track two celestial solar rays along the horizon path route from the Mittelberg summit horizon, demonstrating the exact 82.5-degree angle between Summer Solstice and Winter Solstice sunsets aligning with the disc's gold horizon arc.",
        [(0.0, 3.4, "계산해 보니, 82도 황금 호는 네브라 지역에서", "Horizon camera frames Mittelberg sunset", "Gold horizon arc aligns with terrain", "none"),
         (3.4, 6.9, "하지와 동지에 해가 뜨고 지는 지평선 각도와 소수점까지 일치했거든요.", "Dual solar rays lock onto horizon", "Summer and Winter Solstice rays converge", "none")],
        [(0.0, "Mittelberg summit horizon diorama", "Wide terrain crane", ["Mittelberg hill", "sunset horizon"]),
         (4.0, "Dual solstice solar rays emerge", "Medium celestial track", ["summer ray", "winter ray"]),
         (8.0, "82.5° angle locked to disc arc", "Diagnostic alignment view", ["82.5° ray cone", "gold arc"])],
        graphic_spec=graphic("ROUTE_PATH", "측정확인: 북위 51도 네브라의 하지·동지 일몰 각도(82.5°) 물리적 일치", "golden celestial solar azimuth rays and angular arc lines", "disc center", ["Mittelberg horizon"], "solstice sunset points", "locks onto Summer and Winter Solstice horizon points at 82.5 degrees"),
        seconds=8, visibility="IDENTIFIABLE", routing_reason="네브라 지역 하지·동지 일몰 지평선 각도(82.5°)와 황금 호의 일치를 시뮬레이션하는 장면"
    ))

    # Scene 012
    scenes.append(spec(
        12, 12, (88.4, 99.2), "4. 가설 붕괴와 무역망", "SPATIAL_MAP",
        "심지어 청동의 구리는 오스트리아에서, 금과 주석은 수천 킬로미터 떨어진 영국에서 캐온 사금이었습니다. 대륙 전체를 잇는 거대한 무역망과 정밀한 천문 관측이 한곳에 얽혀 있었던 셈이죠.",
        "측정확인", "I2V_LOCKED", False, "VEO_INTEGRATED_3D", "WORLD_3D",
        cam("3D topographical map of Bronze Age Europe", "flight path tracing trade routes from Austria and Britain to Nebra", "converging gold and copper lines at Nebra", "CONTROLLED_ORBIT_REVEAL", "IMMERSIVE_POV_DOLLY", "NONE", "Europe-wide metallurgical trade intersection at Nebra", "FORWARD", "WIDE", "3.0s Austrian Mitterberg copper route", "6.8s Cornwall Carnon gold/tin route"),
        ["Bronze Age European relief map", "Cornwall river panning site", "Mitterberg copper mine", "trade route network"],
        "Master 3D relief map archaeological diorama of Bronze Age Europe: glowing copper trade lines rise from the Austrian Alps (Mitterberg), gold and tin streams flow from Cornwall (Carnon River), all converging at Nebra in Central Germany.",
        "Fly across the 3D European relief map tracing the glowing trade route path: Austrian copper and Cornish alluvial gold and tin flowing thousands of kilometers to converge at Nebra.",
        [(0.0, 5.4, "심지어 청동의 구리는 오스트리아에서, 금과 주석은 수천 킬로미터 떨어진 영국에서 캐온 사금이었습니다.", "Trace copper line from Alps and gold from Cornwall", "River panning and alpine smelting icons glow", "none"),
         (5.4, 10.8, "대륙 전체를 잇는 거대한 무역망과 정밀한 천문 관측이 한곳에 얽혀 있었던 셈이죠.", "Routes converge at Nebra summit", "Trade network pulses across Europe", "none")],
        [(0.0, "European relief map overview", "High satellite-scale diorama", ["Alps", "British Isles", "Germany"]),
         (3.3, "Cornwall and Alps route tracking", "Medium flight path", ["Carnon river", "Mitterberg mine"]),
         (6.6, "Rhine and Danube river networks", "Wide continental sweep", ["river routes", "settlement nodes"]),
         (10.0, "Convergence at Nebra", "Continental network hold", ["Nebra node", "interlocking trade lines"])],
        graphic_spec=graphic("MATERIAL_FLOW", "측정확인: 납동위원소 및 미량원소 분석으로 확인된 알프스-콘월 원자재 교역로", "luminous copper-orange and gold-yellow flow streams", "Alps and Cornwall", ["Rhine valley", "Elbe river"], "Nebra node", "converges metallurgical flow streams into the Nebra sky disc node"),
        seconds=10, visibility="NONE", routing_reason="오스트리아 구리 광산과 영국 콘월 사금 채취지를 잇는 청동기 유럽 교역망 지도 장면", ref_ids=[]
    ))

    # Scene 013
    scenes.append(spec(
        13, 13, (99.2, 108.1), "5. 3년 윤달과 휴대용 컴퓨터", "DIAGRAM",
        "여기서 과학자들은 결정적인 단서를 찾아냅니다. 365일의 태양력과 354일의 태음력은 매년 열한 일씩 어긋나 3년이면 한 달 가까이 계절이 틀어집니다.",
        "학술해석", "I2V_LOCKED", False, "VEO_INTEGRATED_3D", "WORLD_3D",
        cam("concentric dual-ring celestial calendar clock diorama", "outer solar ring 365 days rotating vs inner lunar ring 354 days", "accumulating 11-day annual gap marker", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "NONE", "33-day three-year drift warning zone", "ORBIT", "MEDIUM", "2.2s 1-year 11-day slip", "5.8s 3-year 33-day seasonal desync"),
        ["solar cycle 365.25 days", "lunar cycle 354 days", "11-day annual gap indicator", "33-day 3-year drift graphic"],
        "Precision mechanical astronomical infographic archaeological diorama: outer glowing gold solar ring (365 days) and inner silver lunar ring (354 days) rotate, opening an 11-day gap each year that widens to a full 33-day seasonal desynchronization in 3 years.",
        "Animate the rotating concentric solar and lunar rings along the gear path route as the 11-day annual discrepancy widens into a critical 33-day seasonal drift over three cycles.",
        [(0.0, 4.4, "여기서 과학자들은 결정적인 단서를 찾아냅니다. 365일의 태양력과 354일의 태음력은", "Outer solar ring (365d) and inner lunar ring (354d) rotate", "Concentric gear tracks spin smoothly", "none"),
         (4.4, 8.9, "매년 열한 일씩 어긋나 3년이면 한 달 가까이 계절이 틀어집니다.", "11-day red wedge gap opens annually", "Gap multiplies to 33 days after 3 years", "none")],
        [(0.0, "Concentric dual calendar rings", "Top-down 80°", ["solar ring", "lunar ring"]),
         (4.0, "Annual 11-day wedge expansion", "Medium diagnostic", ["11-day red gap", "gear teeth"]),
         (8.0, "3-year 33-day desync alarm", "Macro indicator hold", ["33-day drift wedge", "seasonal desync"])],
        graphic_spec=graphic("FORCE_PATH", "학술해석: 태양력 365.25일과 태음력 354일의 11일 연간 편차 계산", "concentric red annual drift wedges and geometric degree markers", "solar ring mark", ["lunar ring mark"], "drift indicator", "expands red wedge showing 33-day seasonal desynchronization in 3 years"),
        seconds=8, visibility="NONE", routing_reason="태양력 365일과 태음력 354일의 11일 연간 오차를 시각화하는 천문 시계 그래픽 장면", ref_ids=[]
    ))

    # Scene 014
    scenes.append(spec(
        14, 14, (108.1, 116.3), "5. 3년 윤달과 휴대용 컴퓨터", "SCIENTIFIC_EVIDENCE",
        "파종 시기를 놓치면 굶어 죽는 농경 사회에서는 치명적인 문제였죠. 그런데 원판의 초승달은 얇은 달이 아니라 4.5일 된 굵은 달이었습니다.",
        "측정확인", "I2V_LOCKED", False, "GENERATED_PHYSICS", "WORLD_3D",
        cam("ancient Bronze Age wheat field diorama", "dolly to macro measurement of gold crescent moon thickness on disc", "crescent thickness caliper gauge showing 4.5-day moon", "MACRO_PROBE_SETTLE", "MACRO_PROBE", "SURFACE_TO_INTERIOR", "exact 4.5-day lunar thickness index", "FORWARD", "MACRO", "2.0s parched wheat field background", "5.2s caliper measurement on gold crescent"),
        ["Bronze Age wheat agriculture", "thick gold crescent moon", "precision thickness caliper", "4.5-day lunar phase index"],
        "Dual-depth agricultural forensic archaeological diorama: in the soft background, ancient farmers tend golden einkorn wheat fields; in the sharp foreground, forensic digital calipers measure the exact width of the Nebra gold crescent, matching a 4.5-day-old moon.",
        "Dolly from the background wheat field along the forward path route to a sharp macro of the gold crescent moon, measuring its substantial thickness corresponding specifically to a 4.5-day lunar phase.",
        [(0.0, 4.1, "파종 시기를 놓치면 굶어 죽는 농경 사회에서는 치명적인 문제였죠.", "Background wheat crops and seasonal planting", "Farming calendar urgency highlighted", "none"),
         (4.1, 8.2, "그런데 원판의 초승달은 얇은 달이 아니라 4.5일 된 굵은 달이었습니다.", "Caliper measures gold crescent width", "Lunar phase scale confirms 4.5 days", "none")],
        [(0.0, "Wheat field and agricultural diorama", "Medium agricultural wide", ["wheat fields", "farmers"]),
         (4.0, "Crescent moon macro focus", "Macro transition", ["gold crescent", "patina"]),
         (8.0, "4.5-day lunar phase caliper gauge", "Extreme macro diagnostic", ["caliper jaws", "4.5-day index"])],
        seconds=8, visibility="IDENTIFIABLE", routing_reason="농경 파종 위기 배경과 4.5일 된 굵은 초승달의 두께를 정밀 실측하는 장면"
    ))

    # Scene 015
    scenes.append(spec(
        15, 15, (116.3, 125.8), "5. 3년 윤달과 휴대용 컴퓨터", "MECHANISM",
        "봄철 저녁 서쪽 하늘에서 4.5일 된 초승달 곁에 플레이아데스가 나란히 뜰 때, 열세 번째 윤달을 넣어야 한다는 고대 역법 공식이 고스란히 박혀 있었던 겁니다.",
        "학술해석", "I2V_LOCKED", False, "VEO_INTEGRATED_3D", "WORLD_3D",
        cam("spring twilight western sky simulation diorama", "conjunction of 4.5-day crescent moon and 7-star Pleiades", "intercalary 13th month synchronization burst", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CRANE_ORBIT_REVEAL", "NONE", "perfect astronomical synchronization of the 13th leap month", "ORBIT", "WIDE", "2.4s spring western horizon alignment", "5.8s 13th intercalary month unlock"),
        ["spring western twilight sky", "4.5-day crescent moon", "Pleiades 7-star cluster", "13th intercalary month formula"],
        "Spectacular celestial alignment archaeological diorama: in a spring twilight western sky, a 4.5-day-old crescent moon glides directly beside the seven glittering stars of Pleiades, unlocking the ancient astronomical rule for adding a 13th leap month.",
        "Simulate the spring western twilight sky along the orbital path route as the 4.5-day crescent moon aligns alongside the Pleiades cluster, triggering the golden geometric calculation for inserting the 13th intercalary month.",
        [(0.0, 4.7, "봄철 저녁 서쪽 하늘에서 4.5일 된 초승달 곁에 플레이아데스가 나란히 뜰 때,", "Crescent moon and Pleiades glide into alignment", "Western twilight sky coordinates glow", "none"),
         (4.7, 9.5, "열세 번째 윤달을 넣어야 한다는 고대 역법 공식이 고스란히 박혀 있었던 겁니다.", "Golden alignment ring pulses", "+1 Intercalary Month formula locks in", "none")],
        [(0.0, "Spring western horizon diorama", "Wide celestial view", ["spring horizon", "western sky"]),
         (3.3, "Moon and Pleiades conjunction", "Medium celestial track", ["4.5d crescent", "7 stars"]),
         (6.6, "Orbital celestial geometry", "High orbital sweep", ["celestial sphere", "orbit path"]),
         (10.0, "+1 Leap Month formula locked", "Diagnostic celestial hold", ["13th month burst", "aligned symbols"])],
        graphic_spec=graphic("SECTION_REVEAL", "학술해석: 바빌로니아 점토판(MUL.APIN)과 일치하는 봄철 초승달-플레이아데스 결합 윤달 규칙", "golden alignment circle and intercalary month geometric pulse", "crescent moon", ["Pleiades cluster"], "calendar hub", "reveals +1 Intercalary 13th Month formula synchronizing solar and lunar years"),
        seconds=10, visibility="IDENTIFIABLE", routing_reason="봄철 4.5일 달과 플레이아데스 성단의 만남으로 3년 윤달을 판별하는 역법 공식을 시각화하는 장면"
    ))

    # Scene 016
    scenes.append(spec(
        16, 16, (125.8, 131.0), "5. 3년 윤달과 휴대용 컴퓨터", "INVENTORY_TABLEAU",
        "스톤헨지 없이도 손에 쥐고 계절을 맞추는 인류 최초의 휴대용 천문 컴퓨터였던 셈입니다.",
        "학술해석", "I2V_LOCKED", False, "GENERATED_PHYSICS", "WORLD_3D",
        cam("massive Stonehenge megalithic ring diorama", "scale contrast zoom to 30cm Nebra disc held in human hands", "shining gold inlays of the portable computer", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "NONE", "thirty-centimetre portable astronomical computer in hand", "FORWARD", "MEDIUM", "1.6s Stonehenge megalith scale", "3.8s portable disc in hand focus"),
        ["Stonehenge megalithic circle", "thirty-centimetre Nebra sky disc", "human hands holding disc", "golden astronomical glow"],
        "Dramatic comparative scale archaeological diorama: in the background, the multi-ton megaliths of Stonehenge stand under dawn light; in the sharp foreground, two human hands hold the thirty-centimetre Nebra Sky Disc glowing like a compact portable computer.",
        "Zoom from the massive multi-ton stones of Stonehenge directly along the scale comparison path route into human hands holding the thirty-centimetre Nebra disc, illustrating history's first portable astronomical computer.",
        [(0.0, 2.6, "스톤헨지 없이도 손에 쥐고 계절을 맞추는", "Pan from multi-ton Stonehenge megaliths", "Megalith scale comparison markers", "none"),
         (2.6, 5.2, "인류 최초의 휴대용 천문 컴퓨터였던 셈입니다.", "Zoom to 30cm disc resting in human hands", "Gold inlays emit warm computational glow", "none")],
        [(0.0, "Stonehenge megalith background", "Wide comparative scale", ["Stonehenge stones", "dawn sky"]),
         (4.0, "Dolly to foreground hands", "Medium scale transition", ["human hands", "disc"]),
         (8.0, "Portable computer in palm", "Hero macro hold", ["30cm disc in hand", "golden inlays"])],
        seconds=8, visibility="IDENTIFIABLE", routing_reason="스톤헨지와 네브라 디스크의 크기 대비 및 휴대용 천문 컴퓨터 기능을 보여주는 장면"
    ))

    # Scene 017
    scenes.append(spec(
        17, 17, (131.0, 142.4), "6. 확인된 정체와 마지막 미스터리", "HISTORICAL_RECONSTRUCTION",
        "결국 네브라 스카이 디스크는 태양과 달의 주기를 맞춰 농경의 때를 알려주던 청동기인들의 위대한 과학적 지혜였습니다. 바빌로니아 기록보다 천 년이나 앞서 우주의 법칙을 눈앞에 시각화한 증거죠.",
        "학술해석", "I2V_LOCKED", False, "VEO_INTEGRATED_3D", "WORLD_3D",
        cam("Bronze Age tribal assembly on Mittelberg summit", "orbit around sky disc held up by chieftain and artisan", "Babylonian cuneiform clay tablet timeline comparison", "CONTROLLED_ORBIT_REVEAL", "CRANE_ORBIT_REVEAL", "NONE", "pan-civilizational timeline showing 1000-year precedence", "ORBIT", "WIDE", "3.2s tribal assembly sunset view", "7.0s Babylonian cuneiform comparison"),
        ["Bronze Age tribal gathering", "elevated Nebra disc", "Babylonian cuneiform clay tablet (MUL.APIN)", "historical timeline scale"],
        "Grand historical reconstruction archaeological diorama: on the Mittelberg summit at sunset, Bronze Age community leaders hold up the Nebra Sky Disc toward the twilight sky, beside a timeline graphic showing it predates Babylonian cuneiform records by a thousand years.",
        "Orbit around the Bronze Age gathering along the circular path route as the sky disc is held toward the sunset, transitioning to a split timeline confirming it visualized cosmic laws a thousand years before Babylon.",
        [(0.0, 5.7, "결국 네브라 스카이 디스크는 태양과 달의 주기를 맞춰 농경의 때를 알려주던 청동기인들의 위대한 과학적 지혜였습니다.", "Orbit Bronze Age tribal assembly at sunset", "Disc held aloft toward twilight sky", "none"),
         (5.7, 11.4, "바빌로니아 기록보다 천 년이나 앞서 우주의 법칙을 눈앞에 시각화한 증거죠.", "Split timeline compares MUL.APIN clay tablet", "Nebra disc leads by 1,000 years", "none")],
        [(0.0, "Bronze Age summit assembly", "Wide circular diorama", ["chieftain", "artisans", "sunset"]),
         (3.3, "Disc raised toward celestial sky", "Hero three-quarter", ["raised disc", "twilight horizon"]),
         (6.6, "Timeline comparison bridge", "Wide comparison track", ["timeline axis", "historical nodes"]),
         (10.0, "Babylonian timeline comparison", "Diagnostic timeline hold", ["Nebra disc -1600 BC", "Babylon tablet -700 BC"])],
        graphic_spec=graphic("ROUTE_PATH", "학술해석: 메소포타미아 바빌로니아 뮬아핀(MUL.APIN) 천문 기록과의 1000년 시기 비교", "golden chronological timeline bridge and comparative date nodes", "Nebra Sky Disc (-1600 BC)", ["Central Europe"], "Babylonian MUL.APIN (-700 BC)", "establishes 1,000-year chronological precedence over Mesopotamian texts"),
        seconds=10, visibility="IDENTIFIABLE", routing_reason="청동기 사제·장인의 천문 관측과 바빌로니아 대비 1천 년 앞선 과학적 가치를 회수하는 장면"
    ))

    # Scene 018
    scenes.append(spec(
        18, 18, (142.4, 153.9), "6. 확인된 정체와 마지막 미스터리", "SEALED_UNKNOWN",
        "하지만 진짜 미스터리는 지금부터입니다. 문자가 없던 이들이 어떻게 이 지식을 체계화했는지, 왜 서른아홉 개의 구멍을 뚫어 쓰다가 무기들과 함께 깊은 숲속에 묻어버렸는지는 아직 아무도 모릅니다.",
        "미확인", "I2V_LOCKED", False, "GENERATED_PHYSICS", "WORLD_3D",
        cam("macro of 39 perimeter perforation holes on bronze rim", "slow track across gold-hilted bronze swords in dark burial soil", "shadowy ceremonial burial pit in Mittelberg forest", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "MACRO_PROBE", "BOUNDARY_STOP", "unresolved ceremonial hoard deposition in forest soil", "LATERAL", "MACRO", "2.8s 39 hole perforation macro", "6.2s sword hilt and axe deposition in stone cavity"),
        ["39 perimeter perforation holes", "bronze swords with gold hilt wire", "bronze axes", "stone-lined deposition cavity"],
        "Solemn ceremonial burial archaeological diorama: macro focus on the 39 perforations along the disc's rim, moving down as the disc, two gold-accented bronze swords, and two axes are solemnly lowered into a stone-lined cavity in the deep forest floor.",
        "Track along the rim perforation path route from the 39 holes down to the bronze swords and axes being buried in the stone cavity, framing the unresolved mystery of its ritual decommissioning.",
        [(0.0, 5.7, "하지만 진짜 미스터리는 지금부터입니다. 문자가 없던 이들이 어떻게 이 지식을 체계화했는지,", "Macro sweep along 39 rim perforations", "Leather cord binding ghost cues", "none"),
         (5.7, 11.5, "왜 서른아홉 개의 구멍을 뚫어 쓰다가 무기들과 함께 깊은 숲속에 묻어버렸는지는 아직 아무도 모릅니다.", "Descend to stone cavity burial with swords", "Shadows envelop the deposited hoard", "none")],
        [(0.0, "Macro 39 perforation holes", "Extreme rim macro", ["rim holes", "bronze edge"]),
         (3.3, "Swords and axes in stone cavity", "Low cavity track", ["bronze swords", "axes", "disc"]),
         (6.6, "Ceremonial stone lining", "Deep pit hold", ["stone slabs", "bronze patina"]),
         (10.0, "Solemn forest deposition", "Solemn shadow hold", ["buried hoard", "forest humus"])],
        seconds=10, visibility="IDENTIFIABLE", routing_reason="외곽 39개 타공 구멍과 청동 무기 부장품 매장 의례의 미스터리를 보여주는 장면"
    ))

    # Scene 019
    scenes.append(spec(
        19, 19, (153.9, 165.3), "6. 확인된 정체와 마지막 미스터리", "ARTIFACT_MACRO",
        "당시의 제사 의식과 교역로를 증명할 새 유적이 발굴되기 전까지, 숲속에 묻힌 청동판의 침묵은 계속될 겁니다. 시간 속에 잠든 유물, 땅속에 묻힌 역사. 네브라 스카이 디스크의 비밀이었습니다.",
        "학술해석", "I2V_LOCKED", False, "GENERATED_PHYSICS", "WORLD_3D",
        cam("dark forest soil covering the bronze disc", "smooth crane rise through misty pine trees into starry night sky", "complete Milky Way galaxy framing Mittelberg", "CONTROLLED_ORBIT_REVEAL", "CRANE_ORBIT_REVEAL", "NONE", "monumental Mittelberg hill silhouette under Milky Way", "FORWARD", "WIDE", "3.0s soil covering disc", "7.0s starry sky signature pull-back"),
        ["buried Nebra disc in earth", "Mittelberg forest summit", "Milky Way galaxy", "channel signature ending"],
        "Poetic signature ending archaeological diorama: the Nebra Sky Disc rests quietly beneath the dark forest earth while the camera ascends through misty pine branches to frame the magnificent Milky Way galaxy arching over the Mittelberg silhouette.",
        "Rise smoothly along the vertical path route from the quiet buried disc in the forest floor up through misty pine branches into the infinite night sky, holding on the arching Milky Way for the official channel closing.",
        [(0.0, 5.7, "당시의 제사 의식과 교역로를 증명할 새 유적이 발굴되기 전까지, 숲속에 묻힌 청동판의 침묵은 계속될 겁니다.", "Camera pulls up from buried disc through misty trees", "Earth and roots envelop the ancient bronze", "none"),
         (5.7, 11.4, "시간 속에 잠든 유물, 땅속에 묻힌 역사. 네브라 스카이 디스크의 비밀이었습니다.", "Ascend into magnificent night sky with Milky Way", "Cosmic stars mirror the gold disc inlays", "none")],
        [(0.0, "Buried disc in dark forest soil", "Low soil close-up", ["buried disc", "roots"]),
         (3.3, "Crane rise through misty pines", "High crane ascend", ["pine silhouettes", "mist"]),
         (6.6, "Forested ridge skyline", "Extreme wide ascend", ["tree canopy", "horizon"]),
         (10.0, "Infinite starry cosmos and Milky Way", "Monumental cosmic wide", ["Milky Way", "Mittelberg silhouette"])],
        seconds=10, visibility="IDENTIFIABLE", routing_reason="숲속에 묻힌 청동판과 밤하늘 은하수를 비추며 시그니처 엔딩을 닫는 장면"
    ))

    return scenes


def build_visualization_text(scenes: list[dict[str, object]]) -> str:
    lines = [
        f"# {EPISODE_LABEL} — 고증 잠금 I2V 시각화",
        "",
        f"visual_scene_count: {len(scenes)}",
        f"audio_scene_count: {len(scenes)}",
        "generation_mode: I2V_LOCKED",
        "image_model: Nano Banana",
        "video_model: Veo/Flow Omni",
        "aspect_ratio: 9:16",
        "image_count_per_visual_scene: 1",
        "video_count_per_visual_scene: 1",
        "",
    ]
    for s in scenes:
        n = s["n"]
        t_start = s["timeline_start"]
        t_end = s["timeline_end"]
        txt = s["txt"]
        account = s["flow_account"]
        img = s["img_v2"]
        vid = s["vid"]

        lines.extend([
            f"## 영상 {n:03d} — TTS {n:03d} (1/1)",
            "",
            f"- 타임라인: {t_start:.3f}-{t_end:.3f}s",
            f"- 나레이션: {txt}",
            f"- Flow 계정: {account}",
            "",
            "### IMAGE",
            "",
            img,
            "",
            "### I2V",
            "",
            vid,
            "",
        ])
    return "\n".join(lines)


COMPACT_ANCIENT_CONTEXT = "European Bronze Age, circa 1600 BCE, Mittelberg near Nebra."
COMPACT_MODERN_CONTEXT = "Documented 1999-2002 discovery or Halle State Museum conservation."


def compact_image_prompt(s: dict[str, object]) -> str:
    context = COMPACT_MODERN_CONTEXT if s["modern_scene"] else COMPACT_ANCIENT_CONTEXT
    token = "@네브라스카이디스크 " if s["artifact_visibility"] == "IDENTIFIABLE" else ""
    return (
        "9:16 archaeological 3D diorama miniature, macro PBR microtexture, not live-action. "
        + context + " " + token + str(s["image_scene_prompt"])
        + " No text. No labels. No letters. No fantasy, alien, watermark or exterior cube frame."
    )


def compact_video_prompt(s: dict[str, object]) -> str:
    path = s["camera_path"]
    seconds = int(s["omni"])
    beats = s["tts_beats"]
    schedule = f"0.00-{seconds/2:.2f}s: {beats[0]['action']}. {seconds/2:.2f}-{seconds:.2f}s: {beats[1]['action']}."
    rigid = "Keep the exact supplied reference artifact completely rigid with no redesign and no changed part count. " if s["artifact_visibility"] == "IDENTIFIABLE" else ""
    veo_clause = ""
    if "veo_graphic" in s:
        veo = s["veo_graphic"]
        veo_clause = (
            f"Use one restrained {veo['function'].lower().replace('_', ' ')} in physical world space: "
            f"{veo['visual_language']}; start at {veo['start']}, pass {', '.join(veo['via'])}, end at {veo['end']}. "
            "No floating HUD, text or labels. "
        )
    return (
        f"Preserve the locked start image exactly: every object, artifact identity, geometry, material and lighting. One continuous {seconds}s I2V shot; no hard cut, teleport, morph or new object. Start camera by 0.35s. "
        f"{rigid}"
        f"Start at {path['entry_anchor']}; move {path['route']}; end at {path['destination']}; settle on {path['settle_point']}. "
        f"{s['i2v_action_prompt']} {veo_clause}"
        f"TTS-locked timing: {schedule} No voice, music or subtitles."
    )


def validate_compact(row: dict[str, object], image: str, video: str) -> list[str]:
    errors: list[str] = []
    image_low = image.lower()
    video_low = video.lower()
    for token in ("9:16", "3d diorama", "not live-action", "pbr", "no text", "no labels", "no letters"):
        if token not in image_low:
            errors.append(f"image missing {token}")
    if len(image) > 720:
        errors.append(f"image too long {len(image)}")
    for token in ("locked start image", f"continuous {row['omni']}s", "0.35s", "no hard cut", "tts-locked timing", "no voice", "subtitles"):
        if token not in video_low:
            errors.append(f"video missing {token}")
    path = row["camera_path"]
    for token in (str(path["entry_anchor"]).lower(), str(path["destination"]).lower()):
        if token not in video_low:
            errors.append(f"video missing anchor {token}")
    if row.get("veo_graphic") and ("physical world space" not in video_low or "no floating hud" not in video_low):
        errors.append("video missing world-space graphic lock")
    if len(video) > 1700:
        errors.append(f"video too long {len(video)}")
    return errors


def main() -> int:
    scenes = build_scenes()

    # 1. 02a.장면구분.json
    json_path = EPISODE / "02a.장면구분.json"
    json_path.write_text(json.dumps(scenes, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Created: {json_path}")

    # 2. 02.시각화.txt
    txt_path = EPISODE / "02.시각화.txt"
    txt_content = build_visualization_text(scenes)
    txt_path.write_text(txt_content, encoding="utf-8")
    print(f"Created: {txt_path}")

    # 3. Compact UI prompts & check
    ui_images: list[str] = []
    ui_videos: list[str] = []
    ui_check: list[dict[str, object]] = []

    for row in scenes:
        c_img = compact_image_prompt(row)
        c_vid = compact_video_prompt(row)
        errs = validate_compact(row, c_img, c_vid)
        ui_images.append(c_img)
        ui_videos.append(c_vid)
        ui_check.append({
            "n": row["n"],
            "audio_scene": row["audio_scene"],
            "account": row["flow_account"],
            "image_chars": len(c_img),
            "video_chars": len(c_vid),
            "status": "PASS" if not errs else "FAIL",
            "errors": errs,
        })

    (EPISODE / "flow_images_ui.txt").write_text("\n\n".join(ui_images) + "\n", encoding="utf-8")
    (EPISODE / "flow_videos_ui.txt").write_text("\n\n".join(ui_videos) + "\n", encoding="utf-8")
    (EPISODE / "flow_ui_prompt_check.json").write_text(
        json.dumps(ui_check, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Created: {EPISODE / 'flow_images_ui.txt'}")
    print(f"Created: {EPISODE / 'flow_videos_ui.txt'}")
    print(f"Created: {EPISODE / 'flow_ui_prompt_check.json'}")

    # 4. Account assignment
    account_data = {
        "episode": "EP11_네브라스카이디스크",
        "recorded_at_kst": "2026-09-04",
        "clip_model": "Flow Omni",
        "clip_duration_seconds": 8,
        "routing": [
            {
                "scene_range": "001-010",
                "account": "jy04210810@gmail.com",
                "plan": "PRO",
                "condition": "1차 전반부 생성 계정"
            },
            {
                "scene_range": "011-019",
                "account": "jjwwhhjj1116@gmail.com",
                "plan": "ULTRA",
                "condition": "2차 후반부 생성 계정"
            }
        ],
        "safety": {
            "no_passwords_stored": True,
            "verify_visible_account_before_each_paid_generation": True,
            "generate_and_download_one_scene_before_starting_the_next": True
        }
    }
    (EPISODE / "04.FLOW계정배정.json").write_text(
        json.dumps(account_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Created: {EPISODE / '04.FLOW계정배정.json'}")

    failures = [item for item in ui_check if item["status"] != "PASS"]
    if failures:
        print(f"[경고] Flow UI 프롬프트 검수 실패 항목: {failures}")
    else:
        print("Flow UI 프롬프트 길이 및 필수 토큰 검수 19개 전 장면 100% PASS!")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

