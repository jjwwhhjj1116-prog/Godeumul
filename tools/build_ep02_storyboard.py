#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""승인된 EP02 대본·실측 TTS에서 마왕퇴 한묘 I2V 프롬프트를 재현한다.

장면 수는 audio/durations.json의 승인 대본 장면을 그대로 따른다. 이 빌더는
Nano Banana 시작 이미지와 Veo/Flow 연속 I2V 프롬프트를 1:1로 만들고,
출토 맥락·고증·카메라 경로·설명 그래픽의 증거 경계를 JSON에 잠근다.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import _config  # noqa: F401


ROOT = Path(__file__).resolve().parents[1]
EPISODE = ROOT / "산출물" / "EP02_마왕퇴한묘"

STYLE = (
    "premium full-frame archaeological 3D diorama world, immersive cutaway scale illusion with no visible model boundary, "
    "macro-lens depth cues with restrained tilt-shift, not live-action, physically based PBR materials, "
    "high-frequency microtexture and micro-displacement, high fidelity material separation, global illumination, "
    "cinematic archaeological reconstruction with the camera physically inside the miniature world rather than "
    "looking at a display case, 4K source detail, 9:16 vertical composition"
)
ANCIENT_CIV = (
    "Western Han China, early second century BCE, Changsha Kingdom in present-day Hunan, "
    "southern Chinese Chu-influenced lacquer and silk culture"
)
MODERN_CIV = (
    "Present-day Chinese archaeology at Mawangdui in Changsha, Hunan; the stated 1971 or 1972 date is reconstructed "
    "with period-correct Chinese field equipment and documentary restraint"
)
ANCIENT_PEOPLE = (
    "East Asian Chinese figures with East Asian facial features, Western Han cross-collared robes closing to the "
    "right, layered silk or hemp garments, cloth belts, period hair buns and simple caps"
)
MODERN_PEOPLE = (
    "East Asian Chinese archaeologists and scientists, with Chinese hospital construction workers where stated, "
    "wearing period-correct early-1970s work clothes and field protection, no historical reenactment"
)
ARCH = (
    "Western Han timber tomb architecture, deep vertical earthen burial shaft, heavy wooden outer chamber, central "
    "four nested lacquered coffins, four rectangular side compartments, compact rammed earth and sealing layers"
)
NEGATIVE = (
    "no European or Western faces, no Roman or Greek clothing, no medieval European armor, no Japanese or Korean "
    "architecture, no Egyptian sarcophagus, no fantasy tomb, no modern object in ancient scenes, no ancient costume "
    "on modern researchers, no glass display case, no acrylic box, no museum room, no pedestal, no exhibit plaque, "
    "no shelf, no cabinet, no tabletop, no exterior frame around the diorama, "
    "no gore, no horror spectacle, no watermark, no text, no labels, no letters"
)

LOCK_BASE = {
    "civilization": "Western Han China",
    "era": "early second century BCE; discovery scenes explicitly marked 1971 or 1972",
    "region": "Mawangdui, Changsha, Hunan, China",
    "people_lock": "East Asian Chinese only; Western Han dress in ancient scenes; Chinese workers and archaeologists in modern scenes",
    "forbidden_culture": ["European", "Roman", "Greek", "medieval European", "Japanese", "Korean", "Egyptian"],
    "diorama_style": "CINEMATIC_ARCHAEOLOGICAL_DIORAMA",
    "material_fidelity": "PBR_MICROTEXTURE_HIGH_FIDELITY",
}


def cam(entry: str, route: str, destination: str, speed: str, operator: str,
        depth: str, settle: str, *interrupts: str) -> dict[str, object]:
    return {
        "entry_anchor": entry,
        "route": route,
        "destination": destination,
        "speed_profile": speed,
        "operator_style": operator,
        "depth_transition": depth,
        "pattern_interrupts": list(interrupts),
        "settle_point": settle,
    }


def graphic(function: str, relation: str, visual: str, start: str, via: list[str],
            end: str, reaction: str) -> dict[str, object]:
    return {
        "function": function,
        "evidence_relation": relation,
        "visual_language": visual,
        "start": start,
        "via": via,
        "end": end,
        "occlusion": "the graphic passes behind foreground wood, earth or artifacts and reappears with correct world-space parallax",
        "timing": "starts after the first physical camera move, travels during the explanation, then settles before the final beat",
        "camera_relation": "anchored to the physical world and surfaces, with perspective, depth, parallax and natural occlusion",
        "arrival_reaction": reaction,
    }


def spec(chapter: str, scene_type: str, evidence: str, image: str, source: str,
         fingerprints: list[str], action: str, beat_actions: list[str], camera_path: dict[str, object],
         *, modern: bool = False, people: bool = False, architecture: bool = False,
         veo: dict[str, object] | None = None) -> dict[str, object]:
    return locals()


SPECS = [
    spec(
        "1. 발견과 신추", "SITE_ESTABLISH", "발굴확인",
        "Exploded overview of Mawangdui Tomb 1 as a coherent evidence tableau: a deep rectangular earthen tomb cutaway with four nested black-and-red lacquer coffins at center, four side compartments holding lacquer dishes, silk clothing and musical objects, a dignified non-graphic suggestion of Lady Xin Zhui within the innermost coffin, and the T-shaped silk banner suspended above; all verified elements remain spatially distinct",
        "Hunan Museum Mawangdui Tombs exhibition and excavation plan",
        ["deep Tomb 1 earthen cutaway", "four nested lacquer coffins", "T-shaped banner and separated side-compartment artifacts"],
        "The camera immediately dives from the grave rim through the section seam, threads past the nested coffins, then curves around the preserved daily-life objects and rises toward the T-shaped banner without a cut.",
        ["Dive through the tomb section and reveal the preserved body context.", "Sweep past food, dress and music objects, then rise toward the afterlife banner."],
        cam("upper grave rim", "down the visible cut face and around the nested coffins", "T-shaped banner above the innermost coffin", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "IMMERSIVE_POV_DOLLY", "SECTION_DIVE", "wide tableau holding body, life and afterlife together", "fast section dive", "direction change around the coffin corner"),
        architecture=True,
        veo=graphic("SECTION_REVEAL", "Verified Tomb 1 structure and artifact zones; no invented chamber", "warm lacquer-edged sectional seam cut into earth and timber", "grave rim", ["wooden outer chamber", "nested coffin corner"], "banner suspension plane", "a restrained warm reflection crosses the verified objects"),
    ),
    spec(
        "1. 발견과 신추", "DISCOVERY_ACTION", "발굴확인",
        "Late 1971 at a Chinese hospital construction site in Changsha: East Asian Chinese hospital workers excavate a narrow bomb-shelter shaft with hand tools, one shovel striking unusually compact white-clay sealing material below reddish Hunan soil while archaeologists lean toward the fresh edge; period-correct work lamps, ropes and wooden shoring only",
        "Published discovery account: hospital bomb-shelter work exposed the tomb in late 1971",
        ["hospital bomb-shelter shaft", "compact white-clay sealing layer", "1971 Chinese workers and hand tools"],
        "Begin on the descending shovel, snap focus at the compact clay impact, then follow the workers' lamp down the newly exposed edge as loose Hunan soil falls.",
        ["Track the shovel into the bomb-shelter shaft.", "Snap to the compact sealing layer and follow the discovery edge downward."],
        cam("shovel blade above the shaft", "down the tool arc to the compact clay edge", "newly exposed sealing layer", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "NONE", "macro hold on the unusual clay", "impact focus snap", "lamp beam sweeps into the edge"),
        modern=True, people=True,
    ),
    spec(
        "1. 발견과 신추", "DISCOVERY_REVEAL", "발굴확인",
        "1972 excavation of Mawangdui Tomb 1 shown as a clean archaeological cutaway with compact soil strata, a visible physical cut face and section seam: a deep vertical burial shaft drops to a massive wooden outer chamber, then four nested lacquered coffins become visible inside under controlled excavation lights, ropes and timber access platforms",
        "Hunan Museum excavation record and Tomb 1 structure",
        ["deep vertical burial shaft", "massive wooden outer chamber", "four nested lacquered coffins"],
        "The camera drops rapidly with the excavation cage along the vertical shaft, passes the clean section seam into the timber chamber, then circles the four lacquer coffins and stops at the innermost lid.",
        ["Descend the deep shaft with the excavation team.", "Cross the timber threshold and orbit the four nested lacquer coffins."],
        cam("excavation platform at the shaft mouth", "straight down the cut face then through the timber chamber opening", "innermost lacquer coffin lid", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "IMMERSIVE_POV_DOLLY", "SECTION_DIVE", "tight hold on the innermost lid", "rapid vertical descent", "crane-to-orbit direction change"),
        modern=True, people=True, architecture=True,
        veo=graphic("SECTION_REVEAL", "Excavated shaft, wooden chamber and four-coffin sequence", "thin ochre physical cut edge with falling soil grains", "shaft mouth", ["compacted strata", "wooden chamber opening"], "innermost coffin", "fine dust settles on the outer coffin rim"),
    ),
    spec(
        "1. 발견과 신추", "EXCAVATION", "발굴확인",
        "Respectful 1972 archaeological view of the innermost lacquer coffin inside the wooden chamber, black-and-red lacquer lid already loosened with its wooden rim and opening clearly visible; Chinese conservators' gloved hands and lifting straps surround it, the preserved female body kept mostly in shadow and never shown as gore",
        "Hunan Museum excavation documentation of Xin Zhui from Tomb 1",
        ["innermost lacquer coffin", "black-and-red lacquer surface", "respectful first view of Xin Zhui"],
        "The lacquer lid rises once on lifting straps, the camera slips over the opening rim, and a narrow conservation light reveals the dignified outline of the woman before settling.",
        ["Lift the innermost lacquer lid with controlled physical weight.", "Move over the rim and reveal the woman respectfully."],
        cam("black lacquer lid corner", "over the opening rim under the lifting straps", "shadowed face and hands of Xin Zhui", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "NONE", "respectful still frame of the preserved woman", "lid clears the rim", "light enters the opening"),
        modern=True, people=True, architecture=True,
    ),
    spec(
        "1. 발견과 신추", "HISTORICAL_RECONSTRUCTION", "발굴확인",
        "Dignified historical reconstruction of Lady Xin Zhui in an elite Western Han residence: a mature noblewoman in layered dark-red and black silk robes stands beside her husband Li Cang, the chancellor and Marquis of Dai, with restrained lacquer furnishings and attendants placed deeper in the room; no imperial crown and no fantasy palace",
        "Historical identity of Xin Zhui as wife of Li Cang, chancellor of Changsha Kingdom and Marquis of Dai",
        ["mature Xin Zhui as elite noblewoman", "Li Cang in senior Western Han official dress", "Chu-influenced lacquer interior"],
        "Start close on Xin Zhui's silk sleeve and lacquer ornament, orbit quickly to reveal her full rank-bearing setting and Li Cang, then settle on her as the central historical subject.",
        ["Reveal Xin Zhui through the textures of elite Western Han life.", "Orbit to include Li Cang, then return focus to Xin Zhui."],
        cam("embroidered silk sleeve", "short clockwise orbit across lacquer furnishings", "Xin Zhui's composed face", "CONTROLLED_ORBIT_REVEAL", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "Xin Zhui centered with Li Cang behind", "silk-to-face rack focus", "official enters the depth plane"),
        people=True,
    ),
    spec(
        "1. 발견과 신추", "CONSERVATION", "측정확인",
        "Single-room conservation comparison on one continuous table: on one side a conventionally dried wrapped mummy reference shown only as a neutral teaching maquette, on the other the respectfully covered moist preserved body of Xin Zhui from Mawangdui with surviving soft-tissue volume and a clearly deceased dark amber-brown preserved face; no excavation vignette, no split-screen collage, no living glamour portrait, no horror and no sensational decay",
        "Published medical examination description distinguishing Xin Zhui from a dry mummy",
        ["neutral dry-mummy teaching reference", "moist preserved Xin Zhui body", "clear tissue-volume contrast"],
        "A fast lateral camera slide leaves the dry teaching reference and lands on Xin Zhui; raking light moves across the two surfaces to make the preservation contrast immediate.",
        ["Show the familiar dry-mummy expectation briefly.", "Slide decisively to Xin Zhui's very different preserved condition."],
        cam("dry teaching reference", "lateral conservation-table slide", "covered Xin Zhui body", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "MACRO_PROBE", "NONE", "material contrast under raking light", "fast lateral reveal", "raking light changes surface reading"),
        modern=True,
    ),
    spec(
        "1. 발견과 신추", "SCIENTIFIC_EVIDENCE", "측정확인",
        "Early-1970s Chinese medical examination diorama: the respectfully covered body of Xin Zhui rests on a clinical table while East Asian Chinese archaeologists and scientists operate period-correct X-ray equipment; beside it sit sealed tissue sample slides and anatomical study materials, with no gore and no modern digital screens",
        "Documented X-ray, autopsy and tissue examination of Xin Zhui",
        ["covered Xin Zhui examination table", "period-correct X-ray apparatus", "sealed tissue slides"],
        "The camera follows the X-ray head as it glides over the body; a pale scan plane remains physically anchored to the machine, then narrows into a microscope slide as focus snaps to surviving tissue structure.",
        ["Track the X-ray apparatus over the preserved body.", "Follow the evidence path from scan plane to the tissue slide."],
        cam("X-ray tube housing", "parallel to the examination table then down to the microscope slide", "surviving tissue sample", "MACRO_PROBE_SETTLE", "MACRO_PROBE", "NONE", "microscope slide in sharp focus", "machine head begins moving", "rack focus to tissue slide"),
        modern=True, people=True,
        veo=graphic("SCAN_WAVE", "Documented medical imaging and tissue examination, not invented diagnosis", "soft pale-cyan volumetric scan plane tied to the X-ray head", "X-ray tube", ["covered torso plane"], "sealed tissue slide", "a faint glass-edge glint marks the evidence handoff"),
    ),
    spec(
        "1. 발견과 신추", "SEALED_UNKNOWN", "미확인",
        "Dark conservation-room tableau centered on the closed black-and-red innermost coffin, compact sealing materials and nested coffin walls visible around it; multiple plausible preservation layers are present but no single glowing answer, no magic liquid and no vacuum machine",
        "Current scholarly uncertainty about the exact preservation mechanism",
        ["closed innermost coffin", "nested protective layers", "unresolved preservation question"],
        "The camera advances toward the closed coffin, slows sharply at its lacquered boundary, and stops without opening it while condensation and tiny dust motion settle.",
        ["Approach the physical evidence layers.", "Stop at the closed coffin boundary without revealing a single answer."],
        cam("outer sealing material", "between nested coffin walls", "closed innermost coffin", "BOUNDARY_APPROACH_STOP", "LOCKED_EVIDENCE_CAMERA", "BOUNDARY_STOP", "opaque lacquer surface", "approach decelerates at boundary", "all secondary motion settles"),
        architecture=True,
    ),
    spec(
        "2. 무덤 속 생활", "CUTAWAY", "발굴확인",
        "High oblique clean archaeological cutaway of Tomb 1 with compact soil strata, a visible cut face and section seam: four nested black-and-red lacquer coffins occupy the central wooden chamber, with the innermost lid fully closed, while four rectangular side compartments surround them like rooms, their verified object groups separated and readable; no exposed body, no mummy wrapping, no bandages",
        "Excavated plan of Mawangdui Tomb 1",
        ["central nested coffins", "four rectangular side compartments", "timber chamber inside compact sealing layers"],
        "The camera dives through the section seam, makes a fast half-orbit around the central coffins, and the four side compartments physically slide outward just enough to expose their relationship before returning to place.",
        ["Dive to the central four-coffin core.", "Orbit as the four side compartments reveal their spatial relationship."],
        cam("upper soil section seam", "down to the coffin core and outward around four compartments", "complete Tomb 1 plan", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "CRANE_ORBIT_REVEAL", "SECTION_DIVE", "oblique plan with all five zones", "section dive", "compartments separate in sequence"),
        architecture=True,
        veo=graphic("EXPLODED_SEQUENCE", "Excavated spatial relationship of central coffins and four compartments", "lacquer-and-wood components slide along their real construction axes", "central coffin block", ["north compartment", "east and west compartments"], "south compartment", "all parts settle back into the verified plan"),
    ),
    spec(
        "2. 무덤 속 생활", "INVENTORY_TABLEAU", "발굴확인",
        "One coherent Tomb 1 side-compartment inventory tableau: red-and-black lacquer bowls and cups with surviving food remains, a cosmetic box with combs, musical instruments, and five kneeling painted wooden musician-attendants are arranged in their separate excavated groups, with wet wood grain, lacquer microcracks and soil residue",
        "Hunan Museum Tomb 1 inventory including lacquerware, food, cosmetic objects, instruments and wooden attendants",
        ["red-and-black lacquer dining vessels", "cosmetic box and combs", "five kneeling painted wooden musicians"],
        "The camera moves immediately from a lacquer bowl past food and combs, passes through the frame of a musical instrument, then swings around the five wooden musicians to show an entire elite life reconstructed from objects.",
        ["Travel through food and grooming objects.", "Pass the instruments and orbit the five wooden attendants as one life-world."],
        cam("lacquer bowl rim", "through compartment objects and instrument frame", "five kneeling musician figures", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "IMMERSIVE_POV_DOLLY", "NONE", "wide inventory tableau", "macro-to-wide pull", "instrument-frame pass-through"),
    ),
    spec(
        "2. 무덤 속 생활", "ARTIFACT_MACRO", "발굴확인",
        "The plain gauze silk robe from Tomb 1 displayed as the sole hero artifact on a dark museum form, nearly transparent unlined silk floating lightly above a conservation plinth; an elegant unnumbered aged-gold vertical dimension line is physically anchored from shoulder to hem and a tiny brass balance pan supports the folded edge, no generated numerals",
        "Hunan Museum plain gauze garment measurements: 128 centimetres and 49 grams",
        ["unlined plain gauze robe", "near-transparent fine silk", "shoulder-to-hem dimension and balance relationship"],
        "The camera crashes from the full garment into the transparent weave, then pulls back as the gold dimension line grows shoulder to hem and the balance pan dips almost imperceptibly under the forty-nine-gram weight.",
        ["Reveal the full robe and its extreme lightness.", "Use a world-anchored dimension line and balance response, then dive into the weave."],
        cam("robe shoulder", "down the garment edge then into the weave", "transparent silk threads", "MACRO_PROBE_SETTLE", "MACRO_PROBE", "SURFACE_TO_INTERIOR", "individual silk filaments", "dimension line grows", "crash zoom into weave"),
        veo=graphic("DIMENSION_LINE", "Published 128-centimetre length and 49-gram mass; numerals remain in captions", "slender aged-gold survey line and a physical brass balance cue", "robe shoulder", ["waist seam"], "robe hem", "balance pan gives one restrained downward response"),
    ),
    spec(
        "2. 무덤 속 생활", "ARTIFACT_MACRO", "학술해석",
        "Extreme macro archaeological material study of the same plain gauze silk: exceptionally fine pale silk filaments cross in a remarkably even open weave, with tiny natural irregularities and aged fibre fuzz visible under raking museum light; the robe silhouette remains softly recognizable behind the macro plane",
        "Textile analysis of the Mawangdui plain gauze garment",
        ["extremely fine silk filaments", "even open gauze weave", "aged fibre microtexture"],
        "The camera becomes a macro probe moving between real silk filaments; a warm scan wave travels along warp and weft intersections, then the camera pulls back just enough to reconnect the weave to the robe.",
        ["Move through the gauze at fibre scale.", "Trace the even weave and pull back to the garment."],
        cam("one silk filament", "between warp and weft intersections", "recognizable gauze robe surface", "MACRO_PROBE_SETTLE", "MACRO_PROBE", "NONE", "weave-to-garment connection", "focus crosses one fibre junction", "macro pullback"),
        veo=graphic("SCAN_WAVE", "Weave regularity visible in textile analysis; no invented machine", "thin warm light pulse following physical warp and weft fibres", "single warp filament", ["two weave intersections"], "adjacent weft filament", "micro highlights settle along real fibres"),
    ),
    spec(
        "2. 무덤 속 생활", "EXCAVATION", "발굴확인",
        "The T-shaped painted silk funerary banner exactly above the innermost coffin during excavation, its broad upper bar and long vertical body fully visible, red-black-ochre pigments aged but legible, supported by conservators without flattening its delicate textile texture",
        "Hunan Museum excavation record and T-shaped banner from Tomb 1",
        ["T-shaped silk silhouette", "position above innermost coffin", "aged red-black-ochre painted imagery"],
        "The camera rises from the lacquer coffin lid as the silk banner carefully unfolds upward into its full T shape, then executes a quick restrained orbit to establish its location over the coffin.",
        ["Rise from the innermost coffin to the folded silk.", "Follow the banner opening into its full T shape above the coffin."],
        cam("innermost coffin lid", "vertical rise along the hanging silk", "broad upper bar of the T-shaped banner", "CONTROLLED_ORBIT_REVEAL", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "full banner and coffin relationship", "silk begins unfolding", "small orbit at full extension"),
        modern=True, architecture=True,
    ),
    spec(
        "2. 무덤 속 생활", "ARTIFACT_MACRO", "발굴확인",
        "Faithful Xin Zhui Tomb 1 T-shaped silk banner relief on aged brown-red silk. Upper register: red sun with black crow, crescent moon with toad and hare, and paired dragons. Middle: elderly East Asian Chinese Xin Zhui in profile leaning on a cane with attendants above funeral offerings. Lower: an earth-supporting giant and aquatic serpents. Preserve the crowded asymmetric Western Han composition and pigment loss. No palace gate, later deity portrait, Buddhist or Daoist temple, generic banquet, invented motif or text",
        "Hunan Museum interpretation of lower, human and heavenly registers on the T-shaped banner",
        ["lower underworld register", "central human and funeral register", "upper celestial register"],
        "The camera starts at the banner's lower point and climbs quickly across the human scene to the upper celestial bar while a muted silk-gold route path follows only the painted composition and bends behind raised pigment details.",
        ["Enter at the lower register.", "Climb through the human world and arrive at the celestial register."],
        cam("lower tip of the banner", "up the central painted axis", "upper celestial register", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "IMMERSIVE_POV_DOLLY", "SURFACE_TO_INTERIOR", "upper T bar", "route passes the human scene", "arrival at celestial figures"),
        veo=graphic("ROUTE_PATH", "Artifact's vertically organized painted registers, not a literal mapped afterlife", "muted silk-gold route ribbon embedded in the painted surface", "lower painted register", ["central human scene"], "upper celestial register", "a soft pigment-like glow disperses at the upper register"),
    ),
    spec(
        "2. 무덤 속 생활", "DIAGRAM", "학술해석",
        "Artifact-only oblique close-up of the faithful Xin Zhui Tomb 1 T-shaped banner above its lacquer coffin. Preserve the red sun with black crow, crescent moon with toad and hare, paired dragons, elderly East Asian Chinese Xin Zhui leaning on a cane, funeral offerings and lower earth-supporting figure. Show aged silk, pigment loss and folds as the only evidence. No interpretation panel, translucent plane, acrylic sheet, diagram card, plaque, palace gate, later deity portrait, temple, generic banquet or invented motif",
        "Scholarly interpretations of the T-shaped banner's ritual function and soul journey",
        ["real banner remains primary evidence", "funerary reading follows the funeral figures", "soul-journey reading follows ascending motifs but remains uncertain"],
        "A fast shallow orbit travels across the real painted funeral figures, snaps upward along the ascending motifs, and ends on the complete unaltered banner. Two restrained silk-light paths briefly travel inside the painted surface with depth and occlusion, then both fade without choosing a final interpretation.",
        ["Follow the funeral reading across the real motifs.", "Redirect upward along the soul-journey reading and end without choosing one as final."],
        cam("central funeral motif", "low arc across the actual painted figures then upward along the banner axis", "complete unaltered banner", "CONTROLLED_ORBIT_REVEAL", "CRANE_ORBIT_REVEAL", "SURFACE_TO_INTERIOR", "clean full banner with both readings unresolved", "fast lateral arc across funeral figures", "snap upward to celestial motifs"),
        veo=graphic("ROUTE_PATH", "Two debated scholarly readings tied only to visible painted motifs", "two thin desaturated silk-light paths embedded in the banner surface, never panels", "central funeral motif", ["ritual figures", "ascending forms"], "upper register", "both paths fade back into the silk without declaring a winner"),
    ),
    spec(
        "3. 가족 묘역과 지식", "SPATIAL_MAP", "발굴확인",
        "Oblique archaeological terrain diorama of the Mawangdui family cemetery with three separate tomb ground plans set into the same Changsha hillside: Tomb 1 for Xin Zhui, Tomb 2 for Li Cang, and Tomb 3 for a younger man, each represented by distinct excavated footprints and never merged; no generated labels or numerals",
        "Excavated three-tomb family complex at Mawangdui",
        ["three distinct tomb footprints", "Tomb 1 Xin Zhui context", "Tomb 2 Li Cang and Tomb 3 younger man contexts"],
        "Pull back rapidly from Tomb 1 to reveal all three tombs; a bronze route path travels between the separate ground anchors while the camera makes one continuous crane orbit and ends with all three visible.",
        ["Start at Xin Zhui's Tomb 1.", "Reveal the other two family tombs and connect the separate contexts."],
        cam("Tomb 1 footprint", "crane backward across the hillside between three ground anchors", "three-tomb family plan", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "all three tombs separated in one frame", "rapid pullback", "route reaches third tomb"),
        architecture=True,
        veo=graphic("ROUTE_PATH", "Excavated spatial relation of three family tombs; identities remain context-specific", "thin aged-bronze terrain-following route path", "Tomb 1 ground anchor", ["Tomb 2 ground anchor"], "Tomb 3 ground anchor", "three small earth-dust rings settle independently"),
    ),
    spec(
        "3. 가족 묘역과 지식", "TEXT_RECORD", "발굴확인",
        "Artifact-only conservation worktable in an early-1970s Chinese archaeology laboratory, physically separated from Tomb 1 and with no people or reenactment: Western Han Tomb 3 silk manuscripts on medicine and astronomy lie beside the Daoyin exercise chart showing rows of small painted exercise silhouettes in varied poses; silk creases, pigment loss and fibre edges are sharply visible, no modern labels",
        "Hunan Museum Tomb 3 silk manuscripts and Daoyin chart",
        ["separate Tomb 3 evidence plinth", "medical and astronomical silk manuscripts", "Daoyin chart with rows of exercise figures"],
        "The camera skims across a medical silk manuscript, pivots over an astronomical diagram, then follows one row of Daoyin figures as if walking along the silk surface, preserving the separate Tomb 3 plinth.",
        ["Move from medical to astronomical records.", "Track along the Daoyin exercise figures on the same Tomb 3 table."],
        cam("edge of medical silk manuscript", "across astronomical silk to the Daoyin rows", "final exercise figure", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "MACRO_PROBE", "NONE", "wide Tomb 3 evidence table", "pivot at astronomical diagram", "track along exercise row"),
        modern=True,
    ),
    spec(
        "3. 가족 묘역과 지식", "DIAGRAM", "학술해석",
        "An evidence-led miniature knowledge world grows only from the real Tomb 3 silk manuscripts: anatomical channels emerge as faint ink-like paths from medical text, measured star points rise from the astronomy silk, and articulated pose silhouettes lift slightly from the Daoyin chart, all still tethered to the original fabrics",
        "Historical significance of Tomb 3 medical, astronomical and exercise records",
        ["medical silk as source", "astronomical silk as source", "Daoyin chart as source"],
        "The camera follows a single ink path from medical silk, arcs through star points, then descends along a sequence of exercise poses; all 3D explanation remains anchored to the manuscripts and folds back into them.",
        ["Lift the medical and astronomical knowledge from its source silk.", "Travel through the exercise sequence and return everything to the documents."],
        cam("medical manuscript ink line", "through raised star points and Daoyin pose sequence", "original folded silk edges", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "IMMERSIVE_POV_DOLLY", "SURFACE_TO_INTERIOR", "all explanation returned to source artifacts", "ink path rises", "camera direction changes through star field"),
        veo=graphic("SCAN_WAVE", "Conceptual visualization of knowledge recorded on verified Tomb 3 textiles", "faint ink-and-silk scan energy that never leaves the source artifacts", "medical silk line", ["astronomy star points", "Daoyin pose row"], "folded silk edge", "raised forms sink back into the textile"),
    ),
    spec(
        "3. 가족 묘역과 지식", "SPATIAL_MAP", "발굴확인",
        "Two separate museum-scale excavation bays divided by a visible strip of untouched earth: Tomb 1 at left contains Xin Zhui's nested lacquer coffins, robe, lacquerware and banner; Tomb 3 at right contains the medical and astronomical silk manuscripts and Daoyin chart; no object crosses the context boundary",
        "Corrected provenance: Xin Zhui objects from Tomb 1; manuscripts and Daoyin chart from Tomb 3",
        ["Tomb 1 artifact group", "Tomb 3 document group", "untouched-earth provenance boundary"],
        "The camera begins compressed so both bays almost overlap, then makes a decisive lateral move that opens the earth boundary; two short physical route paths retreat to their correct tomb anchors and stop.",
        ["Begin with the tempting but wrong visual mixture.", "Separate Tomb 1 and Tomb 3 and return every object to its real context."],
        cam("overlapping foreground artifact edges", "lateral slide across the untouched-earth divider", "two clearly separated excavation bays", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "CRANE_ORBIT_REVEAL", "NONE", "wide provenance-correct comparison", "lateral separation", "route paths retract to anchors"),
        architecture=True,
        veo=graphic("ROUTE_PATH", "Provenance correction between Tomb 1 and Tomb 3", "two muted material route paths, lacquer-red for Tomb 1 and silk-gold for Tomb 3", "mixed foreground illusion", ["untouched-earth divider"], "separate tomb anchors", "each artifact group receives one restrained matching reflection"),
    ),
    spec(
        "4. 보존의 비밀", "SCIENTIFIC_EVIDENCE", "미확인",
        "The covered preserved body of Xin Zhui in a quiet conservation space with four nested coffin silhouettes and compact sealing layers receding behind it; the image is structured as a question, with all evidence visible but no glowing answer, no magic fluid and no vacuum icon",
        "Return to the unresolved preservation question",
        ["covered Xin Zhui body", "nested coffin silhouettes", "no single highlighted cause"],
        "Crash from the wide evidence room to the coffin boundary, then make a short orbit around the preserved body and stop as the candidate layers remain equally visible.",
        ["Return rapidly from the wider tomb story to Xin Zhui.", "Orbit the evidence and ask how the body remained."],
        cam("wide conservation tableau", "fast push to the coffin then short orbit", "covered preserved body", "CONTROLLED_ORBIT_REVEAL", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "ORBIT_REVEAL", "unresolved evidence tableau", "crash push toward coffin", "orbit reveals all candidate layers"),
        modern=True,
    ),
    spec(
        "4. 보존의 비밀", "CUTAWAY", "학술해석",
        "Scientific archaeological cutaway with compact soil strata, a visible physical cut face and section seam around Tomb 1: deep burial depth, thick sealing layers, four nested coffins, humid inner space and low-oxygen stillness are shown as distinct verified or plausible conditions, with no single condition exaggerated into a proven cause",
        "Multi-factor scholarly preservation hypotheses",
        ["deep burial", "multiple sealing and coffin layers", "humid low-oxygen inner environment"],
        "The camera dives through the soil section, penetrates each verified layer in order, and a muted environmental scan follows the same physical route to the humid inner coffin before settling without declaring a winner.",
        ["Descend through depth and sealing layers.", "Pass the nested coffins and arrive at the humid low-oxygen inner space."],
        cam("surface soil section", "through sealing strata and four coffin shells", "humid inner coffin space", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "IMMERSIVE_POV_DOLLY", "SECTION_DIVE", "all conditions visible together", "soil-to-coffin transition", "scan slows in inner space"),
        architecture=True,
        veo=graphic("SECTION_REVEAL", "Published multi-factor hypotheses; exact contribution of each factor remains unknown", "muted clay, lacquer and pale-blue environmental layers tied to physical materials", "deep soil surface", ["sealing strata", "nested coffin shells"], "humid inner space", "condensation beads settle without a conclusion pulse"),
    ),
    spec(
        "4. 보존의 비밀", "SEALED_UNKNOWN", "미확인",
        "Controlled scientific comparison around a closed lacquer coffin: a single jar of hypothetical embalming liquid and a modern vacuum chamber appear only as dim rejected test models outside the evidence boundary, while the actual deep burial, sealing earth and nested coffins remain central; no ancient technology is depicted as proven",
        "No confirmed single embalming liquid or vacuum preservation method; exact contributions unresolved",
        ["actual closed lacquer coffin", "rejected single-liquid test model", "rejected vacuum test model"],
        "A physical scan wave tests the liquid model, then the vacuum model, and both fade; the camera approaches the real coffin boundary and stops while the layered conditions remain unresolved.",
        ["Test and reject the two oversimplified explanations.", "Return to the real layered evidence and stop at uncertainty."],
        cam("single-liquid test jar", "across vacuum test chamber to actual coffin", "closed lacquer boundary", "BOUNDARY_APPROACH_STOP", "LOCKED_EVIDENCE_CAMERA", "BOUNDARY_STOP", "actual evidence layers without a winner", "test models dim", "camera stops at lacquer boundary"),
        modern=True,
        veo=graphic("SCAN_WAVE", "Conceptual rejection of unconfirmed single-cause claims", "neutral white evidence scan that loses intensity at unsupported models", "liquid test model", ["vacuum test model"], "actual closed coffin", "scan divides into several faint unresolved paths instead of one answer"),
    ),
    spec(
        "4. 보존의 비밀", "DIAGRAM", "학술해석",
        "Exploded evidence stack of Tomb 1's real preservation environment: compact burial earth, sealing materials, heavy wooden chamber and four lacquer coffins separate along one vertical axis while the covered body remains central; no fantasy mechanism, no magic bottle, and no single component glows as the answer",
        "Synthesis: preservation resulted from a complex environment rather than one verified secret technique",
        ["earth and sealing stack", "wooden chamber and four coffins", "central preserved body"],
        "The layers separate rapidly in an exploded sequence, the camera threads between them in one continuous path, then every layer closes around the body as a complex system.",
        ["Separate the verified environmental layers.", "Move through them and close the system around the body."],
        cam("outer burial earth", "through separated sealing, timber and lacquer layers", "central preserved body", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "IMMERSIVE_POV_DOLLY", "SURFACE_TO_INTERIOR", "reassembled multi-layer system", "layers explode apart", "camera threads between shells"),
        architecture=True,
        veo=graphic("EXPLODED_SEQUENCE", "Verified structural layers shown as a system, not a proven single mechanism", "earth, timber and lacquer components separate with material-specific edges", "outer earth", ["wooden chamber", "four lacquer coffins"], "central body space", "all layers close softly without a victory flash"),
    ),
    spec(
        "4. 보존의 비밀", "INVENTORY_TABLEAU", "학술해석",
        "Final integrated Mawangdui evidence tableau: the respectfully covered body, lacquer dining set and cosmetic box, plain gauze robe, T-shaped banner, and separate Tomb 3 medical and Daoyin manuscripts occupy clearly separated concentric museum plinths around the three-tomb family terrain model",
        "Synthesis of body, daily life, technology and afterlife evidence across the Mawangdui tombs",
        ["preserved body evidence", "daily-life and textile artifacts", "banner and separate Tomb 3 knowledge records"],
        "The camera makes a fast continuous spiral from the body through daily-life objects and silk technology to the banner and Tomb 3 manuscripts, widening to show how many worlds survived together.",
        ["Spiral through body, daily life and textile technology.", "Rise past the afterlife banner and separate knowledge records into one wide synthesis."],
        cam("covered body plinth", "spiral through artifact zones", "wide three-tomb evidence tableau", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "all evidence contexts readable", "spiral accelerates through artifacts", "crane rises to wide synthesis"),
        veo=graphic("SCAN_WAVE", "Conceptual synthesis of verified categories while preserving provenance", "restrained material-colored wave tied to each artifact plinth", "body evidence plinth", ["daily-life objects", "textile artifacts", "banner"], "separate Tomb 3 record plinth", "all colors return to neutral museum light"),
    ),
    spec(
        "4. 보존의 비밀", "SEALED_UNKNOWN", "미확인",
        "Three separate Mawangdui tomb silhouettes at dusk in an archaeological terrain diorama; Tomb 1 contains only a respectful soft outline of Xin Zhui's preserved body, while Tombs 2 and 3 remain distinct and do not show equivalent preservation, with the difference presented as an unresolved evidence gap rather than a dramatic answer",
        "Unresolved question of why Xin Zhui's body alone survived in this condition among the three tombs",
        ["three distinct tombs", "Xin Zhui preservation limited to Tomb 1", "unresolved comparison with Tombs 2 and 3"],
        "The camera travels from Tombs 2 and 3 toward Tomb 1, slows at the boundary, and stops; a faint scan reaches all three but returns differently without revealing a cause.",
        ["Compare the three tombs without merging them.", "Arrive at Tomb 1 and preserve the unanswered difference."],
        cam("Tomb 2 and Tomb 3 ground silhouettes", "low terrain path toward Tomb 1", "sealed Tomb 1 boundary", "BOUNDARY_APPROACH_STOP", "LOCKED_EVIDENCE_CAMERA", "BOUNDARY_STOP", "three-tomb comparison held in silence", "scan touches all three", "camera stops before Tomb 1 interior"),
        architecture=True,
        veo=graphic("SCAN_WAVE", "Comparison visualizes the unanswered preservation difference, not a discovered cause", "faint desaturated ground-hugging scan across three separate tomb anchors", "Tomb 2", ["Tomb 3"], "Tomb 1 boundary", "the final return signal remains soft and unresolved"),
    ),
    spec(
        "4. 보존의 비밀", "SITE_ESTABLISH", "학술해석",
        "Dignified closing museum-scale archaeological diorama of the Mawangdui site and its three tombs under warm dawn light, with a subtle inset of the T-shaped banner and lacquer coffin materials integrated into the terrain edges; the tombs remain quiet, historically grounded and free of a treasure reveal",
        "Mawangdui Han Tombs as a major archaeological heritage site",
        ["three-tomb Mawangdui site", "lacquer and silk material memory", "quiet unresolved archaeological landscape"],
        "Begin close on lacquer and silk texture, pull back rapidly into the full three-tomb landscape, then let the camera settle to complete stillness for the channel closing line.",
        ["Move from preserved material detail back into the site.", "End on the full Mawangdui landscape in quiet stillness."],
        cam("lacquer-and-silk material edge", "rapid pullback across the terrain", "three-tomb site at dawn", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "still wide closing frame", "macro-to-landscape transition", "final movement settles"),
        architecture=True,
    ),
]


def choose_duration(tts: float) -> int:
    for value in (4, 6, 8, 10):
        if tts <= value:
            return value
    raise ValueError(f"10초를 넘는 TTS 장면: {tts:.3f}")


def split_narration(text: str, count: int) -> list[str]:
    if count <= 1:
        return [text]
    parts = [p.strip() for p in re.findall(r"[^.!?。！？]+[.!?。！？]?", text) if p.strip()]
    while len(parts) < count:
        longest = max(range(len(parts)), key=lambda i: len(parts[i]))
        segment = parts.pop(longest)
        candidates = [m.end() for m in re.finditer(r"[,，]", segment)]
        cut = min(candidates, key=lambda x: abs(x - len(segment) / 2)) if candidates else len(segment) // 2
        parts[longest:longest] = [segment[:cut].strip(), segment[cut:].strip()]
    if len(parts) > count:
        parts = parts[:count - 1] + [" ".join(parts[count - 1:])]
    return parts


def make_beats(text: str, duration: float, actions: list[str]) -> list[dict[str, object]]:
    parts = split_narration(text, len(actions))
    weights = [max(1, len(re.sub(r"\s", "", part))) for part in parts]
    total = sum(weights)
    beats: list[dict[str, object]] = []
    cursor = 0.0
    for i, (part, action, weight) in enumerate(zip(parts, actions, weights)):
        end = duration if i == len(parts) - 1 else round(cursor + duration * weight / total, 3)
        beats.append({
            "start": round(cursor, 3), "end": round(end, 3), "narration": part,
            "camera": action.split(";", 1)[0], "action": action,
            "graphic": "only scene-integrated evidence graphics; exact Korean words and numbers remain in final captions",
        })
        cursor = end
    return beats


def image_prompt(item: dict[str, object]) -> str:
    depth = str(item["camera_path"]["depth_transition"])
    anchors = [STYLE, MODERN_CIV if item["modern"] else ANCIENT_CIV]
    if item["people"]:
        anchors.append(MODERN_PEOPLE if item["modern"] else ANCIENT_PEOPLE)
    if item["architecture"]:
        anchors.append(ARCH)
    anchors.append(str(item["image"]))
    if depth in {"SECTION_DIVE", "SURFACE_TO_INTERIOR"}:
        anchors.append("start frame is section-ready with a visible archaeological cutaway, compact strata, physical cut face and section seam")
    anchors.append(NEGATIVE)
    return ". ".join(part.rstrip(". ") for part in anchors) + "."


def video_prompt(item: dict[str, object], beats: list[dict[str, object]], seconds: int) -> str:
    schedule = " ".join(f"{b['start']:.2f}-{b['end']:.2f}s: {b['action']}" for b in beats)
    camera_path = item["camera_path"]
    shared = (
        f"Use the supplied locked start image and preserve all objects, identities, provenance, site geometry, artifact fingerprints, materials, culture and lighting. "
        f"Single continuous {seconds}-second I2V shot, no hard cut, no teleport, no morph, no new objects. Begin physical camera travel within 0.35 seconds. "
        f"Enter at {camera_path['entry_anchor']}; travel {camera_path['route']}; arrive at {camera_path['destination']}; settle on {camera_path['settle_point']}. "
    )
    if item["veo"] is not None:
        function = str(item["veo"]["function"])
        keyword = "physical route path ribbon" if function == "ROUTE_PATH" else function.lower().replace("_", " ")
        shared += (
            f"Integrate one {keyword} anchored in the physical world space. It receives camera parallax, correct surface perspective, material contact and natural occlusion. "
            "No floating HUD, no screen-space graphic, no text. "
        )
    return shared + str(item["action"]) + " TTS-locked timing: " + schedule + " No voice, no music, no subtitles."


def build() -> None:
    duration_data = json.loads((EPISODE / "audio" / "durations.json").read_text(encoding="utf-8"))
    sources = duration_data["scenes"]
    if len(sources) != len(SPECS):
        raise ValueError(f"승인 TTS {len(sources)}장면과 시각 명세 {len(SPECS)}장면이 다릅니다")

    rows: list[dict[str, object]] = []
    for n, item in enumerate(SPECS, 1):
        source = sources[str(n)]
        narration = str(source["text"])
        tts = float(source["duration"])
        seconds = choose_duration(tts)
        beats = make_beats(narration, tts, item["beat_actions"])
        lock = dict(LOCK_BASE)
        if item["modern"]:
            lock.update({
                "civilization": "Present-day Chinese archaeology",
                "era": "1971 or 1972 Chinese archaeological discovery and examination, as stated by the scene",
                "people_lock": "East Asian Chinese workers, archaeologists and scientists in period-correct early-1970s clothing",
            })
        lock.update({"source_reference": item["source"], "site_artifact_fingerprint": item["fingerprints"]})
        row: dict[str, object] = {
            "n": n, "chapter": item["chapter"], "ct": item["scene_type"],
            "txt": narration, "tts": tts, "omni": seconds, "evidence": item["evidence"],
            "generation_mode": "I2V_LOCKED", "architecture_anchor_required": bool(item["architecture"]),
            "modern_scene": bool(item["modern"]),
            "motion_owner": "GENERATED_PHYSICS+VEO_INTEGRATED_3D" if item["veo"] else "GENERATED_PHYSICS",
            "motion_space": "WORLD_3D", "camera_path": item["camera_path"], "visual_lock": lock,
            "tts_beats": beats, "img_v2": image_prompt(item),
            "status": "PROMPT_LOCKED_IMAGE_PENDING",
        }
        row["vid"] = video_prompt(item, beats, seconds)
        if tts > 9.0:
            row["long_scene_review"] = "CONTINUOUS_SPATIAL_ACTION_REVIEWED_AND_FITS_10S"
        if item["veo"] is not None:
            row["veo_graphic"] = item["veo"]
        rows.append(row)

    (EPISODE / "02a.장면구분.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = [
        "# EP02 마왕퇴 한묘 — 장면 구분표 v2", "",
        "> 장면 수는 승인 대본·실측 TTS·의미/행동/증거 전환에서 파생했다. 목표 컷 수가 아니다.", "",
        "| 장면 | 장 | TTS | 생성 | 유형 | 증거 | 모션 | 핵심 화면 |",
        "|---:|---|---:|---:|---|---|---|---|",
    ]
    visual = [
        "# EP02 마왕퇴 한묘 — 고증 잠금 I2V 시각화 v2", "", f"scene_count: {len(rows)}",
        "scene_count_basis: SCRIPT_TTS_MEANING_ACTION_EVIDENCE_DERIVED", "generation_mode: I2V_LOCKED",
        "image_model: Nano Banana 2", "video_model: Veo/Flow Omni", "aspect_ratio: 9:16",
        "image_count_per_scene: 1", "video_count_per_scene: 1", "",
    ]
    image_lines: list[str] = []
    video_lines: list[str] = []
    for row, item in zip(rows, SPECS):
        core = str(item["image"]).split(":", 1)[0][:76].replace("|", "/")
        md.append(f"| {row['n']:03d} | {row['chapter']} | {row['tts']:.3f}s | {row['omni']}s | {row['ct']} | {row['evidence']} | {row['motion_owner']} | {core} |")
        visual.extend([
            f"## 장면 {row['n']:03d} — {row['ct']} / {row['evidence']}", "",
            f"- TTS: {row['tts']:.3f}s", f"- 생성 길이: {row['omni']}s",
            f"- 모션 소유권: {row['motion_owner']}", f"- 모션 공간: {row['motion_space']}",
            f"- 나레이션: {row['txt']}", "", "### IMAGE", "", str(row["img_v2"]), "",
            "### I2V", "", str(row["vid"]), "",
        ])
        image_lines.append(f"[SCENE {row['n']:03d}]\n{row['img_v2']}")
        video_lines.append(f"[SCENE {row['n']:03d} / {row['omni']}s]\n{row['vid']}")

    (EPISODE / "02a.장면구분표.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (EPISODE / "02.시각화.txt").write_text("\n".join(visual).rstrip() + "\n", encoding="utf-8")
    (EPISODE / "flow_images_v5.txt").write_text("\n\n".join(image_lines) + "\n", encoding="utf-8")
    (EPISODE / "flow_videos_v5.txt").write_text("\n\n".join(video_lines) + "\n", encoding="utf-8")
    manifest = {
        "episode": "EP02_마왕퇴한묘", "scene_count": len(rows), "generation_mode": "I2V_LOCKED",
        "image_model": "Nano Banana 2", "video_model": "Veo Flow Omni", "aspect_ratio": "9:16",
        "image_count_per_scene": 1, "video_count_per_scene": 1,
        "status": "PROMPTS_BUILT_AWAITING_PROMPT_CHECK",
        "scenes": [{"n": r["n"], "tts": r["tts"], "omni": r["omni"], "status": r["status"]} for r in rows],
    }
    (EPISODE / "flow_v5_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"EP02 I2V 시각화 빌드 완료: {len(rows)}장면")


if __name__ == "__main__":
    build()
