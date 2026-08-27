#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""EP04 산싱두이 승인 TTS에서 고증 잠금 I2V 장면표를 만든다.

장면 수는 목표 컷 수가 아니라 승인 대본, 실제 TTS, 의미·행동·증거 전환에서 파생한다.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import _config  # noqa: F401


ROOT = Path(__file__).resolve().parents[1]
EPISODE = ROOT / "산출물" / "EP04_산싱두이"

STYLE = (
    "premium full-frame archaeological 3D diorama world, museum-scale crafted miniature with selective "
    "handcrafted edges, immersive macro-lens depth cues and restrained tilt-shift, not live-action, physically "
    "based PBR materials, high-frequency microtexture, micro-displacement, high fidelity material separation, "
    "global illumination, cinematic archaeological reconstruction, 4K source detail, 9:16 vertical composition"
)
ANCIENT_CIV = (
    "Bronze Age ancient Shu civilization, late second millennium BCE, Sanxingdui at Guanghan in the Sichuan "
    "Basin, southwest China"
)
MODERN_CIV = (
    "Present-day Chinese archaeology at the Sanxingdui site in Guanghan, Sichuan, reconstructed specifically "
    "as the stated 1929, 1986 or 2021 discovery and excavation context"
)
ANCIENT_PEOPLE = (
    "East Asian ancient Shu figures from Bronze Age southwest China, with East Asian facial features, dark hair, "
    "woven hemp or silk cross-collared garments, wrapped skirts or knee-length work robes, cloth belts, simple "
    "topknots and restrained bronze or jade ritual ornaments"
)
MODERN_PEOPLE = (
    "East Asian Chinese farmers workers archaeologists and conservators wearing period-correct clothing and "
    "equipment for the stated 1929, 1986 or 2021 context"
)
ARCH = (
    "Ancient Shu rammed-earth walled settlement, timber post-and-beam ritual structures, packed-earth courtyards, "
    "timber platforms and restrained thatch or wooden roofing in the Sanxingdui urban and sacrificial zone"
)
NEGATIVE = (
    "no European or Western faces, no Roman or Greek clothing, no Japanese or Korean architecture, no Egyptian "
    "or Mesoamerican imagery, no alien or science-fiction interpretation, no later imperial Chinese palace, "
    "no modern clothing in ancient scenes, no ancient costume on modern researchers, no wearable mask, no fantasy "
    "monster, no generic tomb, no plastic toy surface, no low-poly game asset, no glass display case, no museum "
    "pedestal, no exterior box frame, no measuring ruler, no arrows, no graphic overlay, no fake script or pseudo-writing, "
    "no gore, no watermark, no text, no labels, no letters"
)

LOCK_BASE = {
    "civilization": "Bronze Age ancient Shu civilization",
    "era": "late second millennium BCE, with key deposits approximately 1300-1100 BCE; modern scenes explicitly dated",
    "region": "Sanxingdui, Guanghan, Sichuan Basin, southwest China",
    "people_lock": "East Asian ancient Shu people only in ancient scenes; East Asian Chinese people only in modern scenes",
    "forbidden_culture": [
        "European", "Roman", "Greek", "Japanese", "Korean", "Egyptian", "Mesoamerican", "alien", "later imperial Chinese",
    ],
    "diorama_style": "CINEMATIC_ARCHAEOLOGICAL_DIORAMA",
    "material_fidelity": "PBR_MICROTEXTURE_HIGH_FIDELITY",
}


def cam(entry: str, route: str, destination: str, speed: str, operator: str, depth: str,
        settle: str, *interrupts: str) -> dict[str, object]:
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


def graphic(function: str, evidence: str, language: str, start: str, via: list[str], end: str,
            arrival: str) -> dict[str, object]:
    return {
        "function": function,
        "evidence_relation": evidence,
        "visual_language": language,
        "start": start,
        "via": via,
        "end": end,
        "occlusion": "the graphic passes behind foreground earth, timber, ivory or bronze and reappears with correct world-space parallax",
        "timing": "emerge only after the first camera movement, travel during its exact narration beat, settle, then fade before the end",
        "camera_relation": "anchored in the physical world and to named surfaces with correct perspective, depth, lighting, reflections and occlusion",
        "arrival_reaction": arrival,
    }


def spec(chapter: str, scene_type: str, evidence: str, image: str, source: str,
         fingerprints: list[str], action: str, beat_actions: list[str], camera_path: dict[str, object],
         *, people: bool = False, architecture: bool = False, modern: bool = False,
         veo: dict[str, object] | None = None, i2v_guard: str = "") -> dict[str, object]:
    return locals()


SPECS = [
    spec(
        "1. 거대한 얼굴", "DISCOVERY_REVEAL", "측정확인",
        "A section-ready subterranean discovery tableau: compact Sichuan earth opens along a clean physical cut face around the documented 1986 Pit 2 bronze mask with protruding pupils, the full 138-centimetre wing-to-wing width readable in one frontal composition; huge angular face, tubular eyes projecting about 16 centimetres, wing-like ears, dark green patina and soil residue; pure archaeological start frame with no dimension mark or overlay",
        "Sanxingdui Museum object dimensions and 1986 Pit 2 context",
        ["1986 Pit 2 protruding-pupil mask", "138-centimetre wing-to-wing width", "tubular pupils projecting about 16 centimetres"],
        "Earth grains break away along the pre-existing section seam as the camera dives to the mask, then a thin dimension line grows only between the real ear edges and remains behind projecting bronze details.",
        ["Open the earth section and accelerate toward the buried bronze face.", "Race across the real mask width and settle on its complete frontal form."],
        cam("fresh earth section above the left ear", "through the visible section seam and across the projecting pupils", "outer edge of the right wing-like ear", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "IMMERSIVE_POV_DOLLY", "SURFACE_TO_INTERIOR", "full frontal mask with both ear anchors readable", "earth face opens within the first beat"),
        veo=graphic("DIMENSION_LINE", "Published 138 cm mask width; exact number stays in narration and captions", "slender aged-bronze 3D survey line with short perpendicular end ticks and no numerals", "outer edge of the left ear", ["lower edge of the left pupil", "bridge of the nose"], "outer edge of the right ear", "a restrained warm glint touches both ear-edge ticks"),
    ),
    spec(
        "1. 거대한 얼굴", "ARTIFACT_MACRO", "측정확인",
        "Three-quarter macro portrait of the same documented 1986 protruding-pupil bronze mask, showing the 16-centimetre tubular pupils in true profile, flared wing-like ears, broad angular nose, cast seams, pitted green patina, compact soil in recesses and no human body; pure artifact image with no depth line, ruler or overlay",
        "Sanxingdui Museum protruding-pupil mask measurements",
        ["same 1986 Pit 2 mask", "16-centimetre pupil projection", "wing-like ears and angular cast face"],
        "The camera starts at the pupil tip, snaps backward to the socket, then strafes rapidly toward the ear while the world-anchored depth line grows between the two true bronze surfaces.",
        ["Probe from the eye tip back to the socket.", "Change direction and run laterally to the wing-like ear."],
        cam("tip of the left tubular pupil", "back along the pupil axis then laterally across the cheek", "outer tip of the left wing-like ear", "MACRO_PROBE_SETTLE", "MACRO_PROBE", "NONE", "three-quarter profile holding pupil and ear together", "focus snap from pupil tip to socket"),
        veo=graphic("DIMENSION_LINE", "Published approximately 16 cm projection of the pupils; no generated number", "thin neutral aged-bronze depth line with two tiny physical end ticks", "left eye socket rim", ["midpoint of the tubular pupil"], "tip of the tubular pupil", "one small bronze reflection runs to the pupil tip"),
    ),
    spec(
        "1. 거대한 얼굴", "ARTIFACT_MACRO", "미확인",
        "The documented giant protruding-pupil mask rises vertically from a compact excavated-earth cradle inside an artifact-scale archaeological diorama; beside it sits one plain undecorated human-head-sized clay scale form, making the impossible wearable scale obvious, while the mask's empty dark eyes remain the final visual question; no conservation stand, shelf, paper, ruler, invented deity or person wearing it",
        "Measured mask size; identity and represented being remain unknown",
        ["giant 138-centimetre mask", "plain human-head-sized comparison form", "empty undocumented identity"],
        "The camera pulls back quickly from patina pores to reveal the human-scale reference, performs a short half-orbit and stops inside the empty eye without assigning an identity.",
        ["Pull back from bronze microtexture to reveal the impossible wearable scale.", "Orbit just enough to end on the unanswered empty eye."],
        cam("patina crater beside the left eye", "fast macro pullback into a shallow half-orbit", "dark opening inside the left pupil", "CONTROLLED_ORBIT_REVEAL", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "empty pupil held as the unresolved question", "scale reference enters after the pullback"),
    ),
    spec(
        "2. 발견", "DISCOVERY_ACTION", "발굴확인",
        "1929 rural Guanghan, Sichuan: an East Asian Chinese farmer and a family member in period-correct plain work clothes dig a small irrigation pit at the field edge; the wooden-handled iron hoe has just caught a smooth jade object beneath wet brown soil, water glistens in the shallow channel, no bronze mask and no modern machine",
        "Guanghan Municipal Government discovery history",
        ["1929 irrigation-pit discovery", "period-correct Chinese farmer family", "jade objects in wet Sichuan soil"],
        "The hoe completes one believable stroke, catches hard jade and recoils; the camera follows the tool, crash-focuses to the green stone and lowers with falling wet soil.",
        ["Follow the farmer's tool into the irrigation soil.", "Snap to the first jade edge as wet dirt drops away."],
        cam("iron hoe head above the wet channel", "down the tool arc through loose soil", "newly exposed jade edge", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "NONE", "macro hold on jade and wet soil", "impact focus snap reveals green stone"),
        people=True, modern=True,
    ),
    spec(
        "2. 발견", "DISCOVERY_REVEAL", "발굴확인",
        "Summer 1986 at the Sanxingdui brick-earth works: East Asian Chinese laborers in period-correct 1980s work clothes stand beside two adjacent rectangular sacrificial-pit cutaways; one shovel edge has exposed layered bronze heads, gold foil, jade, elephant tusks and broken ritual objects in dense earthen sections, all categories spatially distinct and no intact fantasy treasure room",
        "Metropolitan Museum and National Science Review accounts of the 1986 pits",
        ["1986 brick-earth work site", "two adjacent rectangular pits", "bronze, gold, jade and ivory deposit layers"],
        "Begin on the shovel edge, dive down the open section of the first pit, bank sharply through the narrow earth divider and enter the second pit as the already-present artifact layers catch the work light.",
        ["Track the shovel from brick-earth work into the first rectangular pit.", "Cross the earth divider and reveal the second pit's layered bronze, gold, jade and ivory."],
        cam("shovel blade at the first pit rim", "down the first cut face then through the exposed divider seam", "deep artifact layer of the second rectangular pit", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "IMMERSIVE_POV_DOLLY", "SECTION_DIVE", "wide two-pit section with categories still separated", "rapid vertical descent", "hard bank across the earth divider"),
        people=True, modern=True,
        veo=graphic("SECTION_REVEAL", "Documented adjacent Pits 1 and 2 and their excavated material categories", "thin ochre earthen section seam with physically falling soil and restrained warm edges", "first rectangular pit rim", ["first pit bronze layer", "intact earth divider"], "second pit ivory-and-bronze layer", "a small fall of dry soil exposes one existing bronze edge"),
    ),
    spec(
        "2. 발견", "ARTIFACT_MACRO", "발굴확인",
        "Extreme three-quarter macro of the documented 1986 protruding-pupil mask resting in its excavated Pit 2 context; the camera-facing side clearly shows one square attachment hole and U-shaped rear edge, pitted dark green bronze, compact earth and casting thickness, with the rest of the mask still visible enough to prevent confusion with the 2021 non-protruding large mask",
        "Sanxingdui Museum and HKPM attachment-hole observations",
        ["1986 protruding-pupil mask continuity", "square attachment hole at the side", "U-shaped rear bronze edge"],
        "A fast lateral macro glide starts at the eye tube, follows the cheek edge and rack-focuses into the square attachment hole; one dust grain drops through the opening.",
        ["Connect the giant mask to its side edge.", "Probe the square attachment hole and hold its worked surface."],
        cam("outer rim of the protruding pupil", "along the cheek casting edge toward the side", "square attachment hole", "MACRO_PROBE_SETTLE", "MACRO_PROBE", "NONE", "worked inner surface of the hole", "rack focus enters the attachment hole"),
    ),
    spec(
        "3. 의식 세계", "HISTORICAL_RECONSTRUCTION", "학술해석",
        "A restrained provisional reconstruction: the same broad flat wing-eared protruding-pupil bronze mask, with no body, crown or horns, floats only a few centimetres before a thick plain timber ritual post; its real square side attachment holes align with two plain wooden pegs but remain visibly unconnected; behind it only a partial Ancient Shu timber platform and rammed-earth courtyard are visible, never a confirmed complete temple",
        "HKPM interpretation of holes and U-shaped back as possible timber mounting",
        ["same giant mask with attachment holes", "plain timber post aligned to the holes", "reconstruction kept visibly provisional"],
        "The mask and two pegs separate slightly along their real axes, the camera orbits through the gap, then the pieces ease toward alignment without completing an asserted installation; it immediately pulls beyond the post toward the larger artifact field.",
        ["Test the possible post-mounting relationship without locking it as fact.", "Pull out fast to reveal that the mask is only the first artifact."],
        cam("square hole at the mask edge", "through the mask-to-post gap then outward around the timber", "open ritual artifact field beyond the post", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "IMMERSIVE_POV_DOLLY", "ORBIT_REVEAL", "wide frame where the mask is one element among many", "orbit exposes the physical gap"),
        architecture=True,
        veo=graphic("EXPLODED_SEQUENCE", "Academic mounting hypothesis based on worked holes; the connection remains provisional", "original bronze and timber materials moving only along the proposed peg axes, no glow", "square mask attachment hole", ["plain wooden peg", "timber post face"], "unclosed alignment gap", "a faint dust mote lifts from the timber face while the gap remains visible"),
    ),
    spec(
        "3. 의식 세계", "INVENTORY_TABLEAU", "발굴확인",
        "One high-fidelity vertical excavation cutaway with four physically separated evidence zones, never an assembled shrine: the documented 262-centimetre standing bronze statue with oversized empty hands and layered robe occupies the lower foreground; reconstructed segments of the documented 395-centimetre bronze sacred tree with its real branch birds and descending dragon occupy a separate deep rear zone; gold-faced bronze heads and layered elephant tusks remain in two additional earthen deposit zones, every category at correct relative scale and provenance visibly separated; all heads and statues are excavated bronze artifacts in East Asian ancient Shu iconography, not living people",
        "National Science Review, Met and Sanxingdui Museum representative artifact dimensions",
        ["262-centimetre standing bronze figure with empty hands", "approximately 395-centimetre reconstructed bronze sacred tree", "separate gold-faced heads and ivory"],
        "Crane rapidly up the standing figure from robe hem to empty hands, whip-bank toward the sacred tree crown, descend along the dragon and land on the gold-faced heads and ivory without making any object move.",
        ["Rise the full scale of the bronze standing figure.", "Change direction across the sacred tree and finish on gold-faced heads and ivory."],
        cam("robe hem above the bronze pedestal", "up through the empty hands, across the tree crown and down its dragon", "gold-faced bronze heads beside the ivory layer", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "artifact group with correct relative scale", "fast vertical crane up the figure", "whip-bank from hands to tree crown"),
    ),
    spec(
        "3. 의식 세계", "HISTORICAL_RECONSTRUCTION", "학술해석",
        "A restrained conceptual Ancient Shu ritual-world synthesis built only from documented artifacts: the tall bronze statue, segmented sacred tree, branch birds, descending dragon, gold-faced bronze heads and ivory remain separated on distinct physical axes while the camera can visually connect their repeated human, tree, bird and material motifs; no living ritual performers, no assembled altar, no invented deity and no complete fantasy temple",
        "Scholarly interpretation of Sanxingdui ritual imagery and artifact ensemble",
        ["documented standing figure", "documented tree, birds and dragon", "gold, bronze and ivory artifact relationship"],
        "A rapid curved push threads between the figure's empty hands, circles the tree trunk and rises past one bird; controlled light briefly connects the documented materials, then the camera settles on the whole ritual-world composition.",
        ["Bind person, tree, bird and sacred material into one readable ritual world."],
        cam("gap between the standing figure's empty hands", "curved push around the sacred-tree trunk", "bird at the upper branch", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "IMMERSIVE_POV_DOLLY", "ORBIT_REVEAL", "whole documented ensemble in one frame", "tight curve around the tree trunk"),
        architecture=True,
    ),
    spec(
        "4. 파괴와 매납", "CUTAWAY", "발굴확인",
        "A verified sacrificial-pit cutaway rather than a dramatic destruction scene: broken and heat-marked bronze ritual fragments lie in compact layered earth across several distinct rectangular pit slices, with ivory above bronze only where documented; charred residues, bent gold foil, jade and bronze remain materially separate, and an intact ritual tableau is visible only as a faint upper comparison zone, not as a historical event reconstruction",
        "Metropolitan Museum, HKPM and Antiquity reports on broken, heat-affected and layered deposits",
        ["broken ritual bronze fragments", "heat-marked material and charred residue", "separate rectangular pit layers with varied ordering"],
        "The camera snaps away from the intact comparison zone, follows one broken bronze edge downward, then the earth opens only along verified pit sections and carries the viewer across two distinct layered deposits.",
        ["Reverse the intact ritual image into broken and heat-marked evidence.", "Dive through separate pit layers without making every pit identical."],
        cam("intact comparison reflection on a bronze edge", "down the fracture into the first cut face then across a second pit slice", "deep broken-bronze layer", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "IMMERSIVE_POV_DOLLY", "SECTION_DIVE", "two separate documented deposition patterns", "focus snaps from intact reflection to fracture"),
        veo=graphic("SECTION_REVEAL", "Excavated layered deposits; ivory-over-bronze ordering is shown only in documented slices", "real earth, ash and artifact materials divided by a thin warm-grey section seam", "fractured bronze edge", ["first pit ivory layer", "earthen divider"], "second pit bronze layer", "two small soil falls mark the distinct section depths"),
    ),
    spec(
        "4. 파괴와 매납", "EXCAVATION", "발굴확인",
        "2021 climate-controlled Sanxingdui Pit 3 excavation diorama seen from directly above: the documented large non-protruding bronze casting lies reverse-side-up in compact soil, showing only its plain concave green-bronze back, broad structural ribs, ancient seams, square attachment openings and wide broken outer-ear silhouette; absolutely no facial front, eyes, eyelids, pupils, eyebrows, nose, nostrils, mouth, lips or cheeks are visible anywhere; more than ten natural elephant tusks are carefully stacked beside and above its lower edge; empty excavation rails and soft work lights remain peripheral, with no person or visible hand",
        "HKPM and Sanxingdui Museum 2021 Pit 3 large-mask context",
        ["2021 Pit 3 non-protruding large mask", "reverse side proving face-down orientation", "more than ten stacked elephant tusks above"],
        "Begin macro at the left broken outer edge, make one fast lateral sweep across the full reverse-side bronze width, pull back to prove its scale, then travel only once toward the natural ivory stack and finish top-down on the highest tusks; never return to the bronze.",
        ["Read the large mask's face-down position and true width.", "Climb through the more-than-ten-tusk layer stacked above it."],
        cam("left broken outer edge of the reverse-side bronze casting", "across the full concave back then only once toward the natural ivory stack", "highest elephant tusks", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "top-down frame proving ivory above face-down bronze", "fast lateral sweep across the structural ribs", "single pullback before the ivory travel"),
        modern=True,
        i2v_guard="The giant bronze casting must remain reverse-side-up with only its plain concave back, structural ribs, seams, attachment holes and broken outer rim visible. Never create a facial front, eyes, nose or mouth. Keep every tusk and soil layer unchanged. Never use a ruler, dimension line or graphic. Move only once toward the ivory and never return to the bronze.",
    ),
    spec(
        "4. 파괴와 매납", "SEALED_UNKNOWN", "미확인",
        "Tight top-down evidence view of the same Pit 3 arrangement: more than ten natural elephant tusks form deliberate crossing layers beside the documented large non-protruding bronze casting, which remains reverse-side-up and shows only its plain concave green-bronze back, broad structural ribs, ancient seams, square attachment openings and broken outer rim; absolutely no facial front, eyes, nose or mouth are visible; one fractured bronze edge leads into opaque undisturbed soil, with no invented cause, attacker or ceremony",
        "Antiquity stratigraphic publication; motive for deposition remains unknown",
        ["same Pit 3 reverse-side-up casting", "ordered crossing ivory layers", "opaque evidence boundary beyond broken fragments"],
        "The camera glides quickly along three tusk crossings, drops to the bronze fracture and stops hard at intact soil; loose dust settles, but the unknown space never opens.",
        ["Follow the deliberate order of the deposit.", "Stop at the broken edge where the reason remains unknown."],
        cam("first natural ivory crossing", "quickly along the existing tusk stack then once toward the broken reverse-side outer rim", "adjacent opaque undisturbed soil boundary", "BOUNDARY_APPROACH_STOP", "LOCKED_EVIDENCE_CAMERA", "BOUNDARY_STOP", "fracture and sealed soil held together", "single curve from ivory to bronze fracture"),
        i2v_guard="The giant bronze casting must remain reverse-side-up with only its plain concave back, structural ribs, seams, attachment holes and broken outer rim visible. Never create a facial front, eyes, nose or mouth. Keep every tusk and soil boundary unchanged. Never use a ruler or graphic. Never reverse direction.",
    ),
    spec(
        "5. 과학 단서", "SCIENTIFIC_EVIDENCE", "측정확인",
        "Present-day Chinese archaeology at the Sanxingdui Pit 4 conservation laboratory: a documented soil-and-ash sample sits beside a polished micromorphology thin section and an unheated pit-wall sample; restrained physical instrument light reveals mineral grains, ash particles and the absence of in-situ heat alteration, with no invented charts, letters or readable screens",
        "Zhang et al., Journal of Archaeological Science 185, multi-proxy Pit 4 sediment analysis",
        ["Pit 4 soil-and-ash sample", "micromorphology thin section", "unheated pit-wall comparison"],
        "The camera macro-probes from the sampled earth into the thin section; one restrained teal scan wave follows real grain boundaries, passes behind a dark mineral and returns at the unheated wall sample.",
        ["Enter the Pit 4 soil and ash sample as the new evidence.", "Compare the residues with the unheated pit wall and reject an in-pit fire."],
        cam("Pit 4 sample clod", "through the polished thin-section edge along real grains", "unheated pit-wall comparison sample", "MACRO_PROBE_SETTLE", "MACRO_PROBE", "SURFACE_TO_INTERIOR", "side-by-side residue and wall evidence", "focus snaps into the thin section"),
        modern=True,
        veo=graphic("SCAN_WAVE", "Multi-proxy analysis supports externally derived combustion residue and no in-situ Pit 4 burning", "restrained teal-white micro-scan sheet conforming to real mineral and ash surfaces", "Pit 4 sample clod", ["ash-rich thin-section zone", "occluding dark mineral grain"], "unheated wall sample", "one faint cool reflection returns from the unheated sample"),
    ),
    spec(
        "5. 과학 단서", "CUTAWAY", "측정확인",
        "Bronze Age Pit 4 deposition cutaway grounded in measured evidence: already-placed broken ritual objects occupy the rectangular pit floor; a separate external ash-and-earth source sits visibly outside the pit, and the same dull grey-brown material is midway along an open basket-to-pit route above the section; no fire burns inside the pit and no other pit is shown",
        "Journal of Archaeological Science 185 conclusion for Pit 4 external combustion residues",
        ["Pit 4 ritual objects already placed", "external ash-and-earth source", "no in-situ burn layer on the pit walls"],
        "The camera follows the actual grey-brown material from the external source along the open route, dives through the section seam and watches it settle over the existing ritual objects; no flame appears in the pit.",
        ["Follow externally produced ash and earth toward Pit 4.", "Dive into the section as the material covers the ritual deposit."],
        cam("external ash-and-earth source", "along the open carrying route then down the pit cut face", "top of the ritual-object layer", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "IMMERSIVE_POV_DOLLY", "SECTION_DIVE", "new cover layer settling over the objects", "route bends at the pit rim"),
        veo=graphic("MATERIAL_FLOW", "Measured Pit 4 residues were moved from an external combustion context; this is not generalized to other pits", "heavy dull grey-brown granular ash-and-earth flow with real gravity and no glow", "external ash-and-earth source", ["basket lip", "Pit 4 rim"], "ritual-object layer", "a small realistic dust lift settles inside Pit 4"),
    ),
    spec(
        "5. 과학 단서", "SCIENTIFIC_EVIDENCE", "측정확인",
        "Completed Pit 4 archaeological section after deposition: ritual-object fragments form the lower layer, externally derived ash and earth cap them in a separate upper layer, pit walls show no in-situ burn front, and the top sealing soil closes the sequence; the three material boundaries are clear through PBR microtexture rather than labels",
        "Published Pit 4 depositional sequence and sediment results",
        ["lower ritual-object layer", "separate externally derived ash-and-earth cap", "unburned pit wall and final sealing soil"],
        "The camera makes a fast low orbit around the completed section, pauses at the clean wall boundary and tilts upward as sealing soil closes the top, ending on the finished deposit rather than a fire scene.",
        ["Read the complete burial sequence as the final depositional stage.", "Close the upper soil while keeping the unburned wall visible."],
        cam("lower ritual-object layer", "shallow orbit around the exposed pit section", "upper sealing soil", "CONTROLLED_ORBIT_REVEAL", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "complete Pit 4 sequence with unburned wall", "tilt changes from lower artifacts to upper cover"),
    ),
    spec(
        "6. 남은 학설", "HISTORICAL_RECONSTRUCTION", "학술해석",
        "Three physically separated, equally desaturated Ancient Shu interpretation bays share the same central excavated pit evidence: one bay suggests the quiet close of a large ritual, one shows aged ritual objects beside an incomplete timber-platform outline, and one shows a packed departure route beside a distant rammed-earth city edge; all remain translucent at their far edges, no battle, no confirmed temple destruction and no chosen answer",
        "Competing scholarly interpretations: ritual closure, temple-object retirement, conflict or center movement",
        ["same excavated pit evidence at center", "three spatially separated hypothesis bays", "no hypothesis shown as confirmed"],
        "The camera launches from the common pit, banks through the ritual-closure bay, whip-pans to the incomplete timber-platform bay, then accelerates toward the departure route and pulls upward so all three remain equally unresolved.",
        ["Test the ritual-ending possibility.", "Redirect to retired temple objects.", "Open the third possibility of conflict or center movement without choosing it."],
        cam("shared excavated pit evidence", "curved path through three separated interpretation bays", "high point above all three bays", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "balanced three-hypothesis overview", "bank from ritual bay to timber-platform bay"),
        architecture=True,
    ),
    spec(
        "6. 남은 학설", "TEXT_RECORD", "미확인",
        "Present-day Chinese archaeology evidence table with the real protruding-pupil mask on one side and an intentionally empty neutral archival tray on the other, surrounded only by excavated fragments and unmarked conservation materials; no contemporaneous sentence-bearing record, bamboo text, calligraphy or readable display exists, and the mask's empty pupils dominate the far background",
        "Current scholarly status: no contemporaneous sentence-form Ancient Shu record identified",
        ["documented protruding-pupil mask", "empty contemporaneous-text evidence tray", "unidentified ritual fragments without readable writing"],
        "The camera moves from several competing fragment groupings to the empty archival tray, makes a sharp direction change toward the mask and stops before entering its dark pupil; no writing appears.",
        ["Move past several hypotheses without selecting one.", "Reach the empty record evidence and end at the unnamed face."],
        cam("three separated fragment groupings", "across the empty archival tray then toward the mask", "dark opening of the mask pupil", "BOUNDARY_APPROACH_STOP", "LOCKED_EVIDENCE_CAMERA", "BOUNDARY_STOP", "empty record space and unnamed face together", "direction change from empty tray to mask", "hard stop before the pupil"),
        modern=True,
    ),
    spec(
        "7. 결론", "ARTIFACT_MACRO", "발굴확인",
        "Dignified frontal macro of the real 1986 protruding-pupil bronze mask against a quiet archaeological earth background; hard raking light first leaves only the strange eye geometry in shadow, while the broad nose, cast seams, wing-like ears, patina pores and attachment features remain visibly human-made and materially specific, no monstrous silhouette and no fantasy distortion",
        "Documented object form, rejecting unsupported monster or alien framing",
        ["real protruding-pupil mask geometry", "human-made casting seams and attachment features", "no fantasy alteration"],
        "A narrow light sweeps rapidly from the strange eye shadow across the cast seams and attachment edge; the camera rotates only a few degrees and settles on the complete documented face.",
        ["Remove the monster framing by revealing the actual made object."],
        cam("shadowed rim of the left pupil", "short lateral move across the nose and casting seams", "complete frontal bronze face", "MACRO_PROBE_SETTLE", "MACRO_PROBE", "NONE", "documented mask in neutral full light", "raking light exposes the casting seam"),
    ),
    spec(
        "7. 결론", "EXPLODED", "학술해석",
        "A section-ready evidence synthesis with only documented Sanxingdui forms: gold-faced bronze heads, elephant tusks, the 262-centimetre standing bronze statue, reconstructed sacred-tree segments and the protruding-pupil mask occupy their own physical axes above a rectangular deposit cutaway; original bronze, gold, ivory and earth colours remain distinct, with no invented god or completed ceremony",
        "Excavated artifact ensemble and scholarly interpretation of a deliberately dismantled sacred world",
        ["documented gold, ivory and bronze ensemble", "standing figure and sacred-tree segments", "rectangular layered deposit cutaway"],
        "The documented pieces move only a short distance along their real assembly axes to form one readable ritual world, then reverse, separate and descend through the open section into the deposit in the same material groups.",
        ["Assemble the documented materials into one sacred-world relationship.", "Reverse the motion and fold the separated objects into the excavated deposit."],
        cam("gold-faced bronze head", "through the assembled artifact axes then down the section seam", "layered rectangular deposit", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "IMMERSIVE_POV_DOLLY", "SECTION_DIVE", "separated materials settled in the pit", "orbit through assembled relationship", "rapid downward fold into the cutaway"),
        veo=graphic("EXPLODED_SEQUENCE", "Documented artifact categories and deliberate deposition; exact ritual meaning remains interpretive", "original bronze, gold and ivory pieces moving on restrained real axes with no neon", "gold-faced bronze head", ["standing-figure hand axis", "sacred-tree joint"], "rectangular deposit layer", "a small earth-and-patina dust response marks final placement"),
    ),
    spec(
        "7. 결론", "SEALED_UNKNOWN", "미확인",
        "A present-day Sanxingdui conservation-and-excavation grid: several real bronze and gold fragments from separated contexts hover only millimetres apart at plausible matching edges above their labelled-by-position but text-free trays, while the documented sacrificial area continues toward an opaque undisturbed rammed-earth boundary and faint posthole outlines; no completed object, hidden chamber or answer is generated",
        "Future evidence boundary: cross-pit joins and surrounding ritual-space archaeology",
        ["separated bronze and gold fragments", "possible matching fracture edges left visibly unjoined", "opaque surrounding ritual-zone soil boundary"],
        "Fragments approach along plausible fracture axes, rotate once for comparison and stop with a visible gap; the camera then races across the grid toward faint postholes and brakes at intact soil without opening it.",
        ["Test fragment joins without claiming a completed answer.", "Move toward the surrounding ritual space and stop at the unexcavated boundary."],
        cam("first matching bronze fracture edge", "across separated comparison trays and faint postholes", "opaque undisturbed soil boundary", "BOUNDARY_APPROACH_STOP", "LOCKED_EVIDENCE_CAMERA", "BOUNDARY_STOP", "possible join and unexcavated area held together", "fragment pair rotates to compare edges", "camera accelerates from tray to postholes"),
        modern=True,
        veo=graphic("EXPLODED_SEQUENCE", "Conceptual future fragment matching; no join is asserted until edges and provenance agree", "original patinated fragment materials moving millimetres along plausible fracture axes", "first bronze fracture edge", ["second separated fracture edge", "text-free context tray"], "visible unclosed join gap", "one tiny dust grain falls through the deliberately unclosed gap"),
    ),
    spec(
        "7. 결론", "SITE_ESTABLISH", "발굴확인",
        "Dignified closing diorama of the present-day Sanxingdui archaeological landscape at warm dawn: protected rectangular excavation zones, restrained rammed-earth settlement traces and the modern conservation perimeter occupy the Sichuan plain; the real protruding-pupil mask is integrated as a foreground artifact memory rather than a giant monument, while the unexplored ground remains opaque and quiet, no UNESCO logo or invented palace",
        "Sanxingdui archaeological site and museum stewardship",
        ["present-day Sanxingdui archaeological landscape", "protruding-pupil mask foreground memory", "quiet opaque unexplored ground"],
        "Begin close on the mask's patina, pull back rapidly through the excavation perimeter, then rise into the full Sichuan landscape and decelerate to complete stillness for the channel close.",
        ["Leave the bronze face and return to the whole buried landscape.", "Settle into stillness on the unresolved site."],
        cam("patina ridge above the mask eye", "rapid pullback across the excavation perimeter then upward", "wide Sanxingdui landscape", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "quiet wide closing frame", "macro-to-landscape scale change"),
        modern=True,
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
    parts = [part.strip() for part in re.findall(r"[^.!?。！？]+[.!?。！？]?", text) if part.strip()]
    while len(parts) < count:
        longest = max(range(len(parts)), key=lambda index: len(parts[index]))
        segment = parts.pop(longest)
        comma_cuts = [match.end() for match in re.finditer(r"[,，]", segment)]
        cut = min(comma_cuts, key=lambda value: abs(value - len(segment) / 2)) if comma_cuts else len(segment) // 2
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
    for index, (part, action, weight) in enumerate(zip(parts, actions, weights)):
        end = duration if index == len(parts) - 1 else round(cursor + duration * weight / total, 3)
        beats.append({
            "start": round(cursor, 3),
            "end": round(end, 3),
            "narration": part,
            "camera": action.split(";", 1)[0],
            "action": action,
            "graphic": "scene-integrated evidence graphics only; exact Korean words and numbers remain in final captions",
        })
        cursor = end
    return beats


def image_prompt(item: dict[str, object]) -> str:
    anchors = [STYLE, MODERN_CIV if item["modern"] else ANCIENT_CIV]
    if item["people"]:
        anchors.append(MODERN_PEOPLE if item["modern"] else ANCIENT_PEOPLE)
    if item["architecture"]:
        anchors.append(ARCH)
    anchors.append(str(item["image"]))
    depth = str(item["camera_path"]["depth_transition"])
    if depth in {"SECTION_DIVE", "SURFACE_TO_INTERIOR"}:
        anchors.append("start frame is section-ready with a visible archaeological cutaway, compact strata, physical cut face and section seam")
    anchors.append(NEGATIVE)
    return ". ".join(anchor.rstrip(". ") for anchor in anchors) + "."


def ui_image_prompt(item: dict[str, object]) -> str:
    style = (
        "9:16 cinematic archaeological 3D diorama; museum-scale miniature, macro lens, "
        "not live-action, PBR microtexture, high fidelity."
    )
    context = (
        "Sanxingdui archaeology, Guanghan, China; use the stated 1929, 1986 or 2021 context."
        if item["modern"] else
        "Bronze Age ancient Shu, Sanxingdui, Sichuan, approximately 1300-1100 BCE."
    )
    negative = (
        "No European or Western people, later Chinese, Japanese, Korean, Egyptian, Mesoamerican or alien forms; "
        "no anachronisms, wearable mask, fantasy or gore; no text, no labels, no letters, no watermark."
    )
    prompt = " ".join((style, context, str(item["image"]), negative))
    if len(prompt) > 1100:
        raise ValueError(f"Flow 이미지 프롬프트 1100자 초과: {len(prompt)}")
    required = ("9:16", "3D diorama", "Sanxingdui", "not live-action", "PBR microtexture", "no text", "no labels", "no letters")
    missing = [token for token in required if token.lower() not in prompt.lower()]
    if missing:
        raise ValueError(f"Flow 이미지 프롬프트 필수 잠금 누락: {missing}")
    return prompt


def video_prompt(item: dict[str, object], beats: list[dict[str, object]], seconds: int) -> str:
    schedule = " ".join(f"{beat['start']:.2f}-{beat['end']:.2f}s: {beat['action']}" for beat in beats)
    path = item["camera_path"]
    prompt = (
        f"Use the supplied locked start image and preserve all objects, identities, provenance, site geometry, "
        f"artifact fingerprints, materials, culture, lighting and composition. Single continuous {seconds}-second "
        f"I2V shot, no hard cut, no teleport, no morph, no new objects. Begin physical camera travel within 0.35 seconds. "
        f"Enter at {path['entry_anchor']}; travel {path['route']}; arrive at {path['destination']}; settle on {path['settle_point']}. "
    )
    if item["i2v_guard"]:
        prompt += str(item["i2v_guard"]) + " "
    if item["veo"] is not None:
        function = str(item["veo"]["function"])
        name = "physical route path ribbon" if function == "ROUTE_PATH" else function.lower().replace("_", " ")
        prompt += (
            f"Integrate one restrained {name} anchored in the physical world space. It shares perspective, depth, "
            f"lighting and reflections, receives camera parallax and natural occlusion, and never attaches to the screen. "
            f"No floating HUD, no screen-space graphics, no text, no numbers, no labels. "
        )
    prompt += str(item["action"]) + " TTS-locked timing: " + schedule
    prompt += " Preserve all objects from the start image. No voice, no music, no subtitles."
    return prompt


def ui_video_prompt(item: dict[str, object], beats: list[dict[str, object]], seconds: int) -> str:
    path = item["camera_path"]
    schedule = " ".join(
        f"{beat['start']:.2f}-{beat['end']:.2f}s {beat['action']}" for beat in beats
    )
    parts = [
        f"Preserve the locked start image exactly: objects, geometry, artifact identity, materials, era and lighting. "
        f"One continuous {seconds}s I2V shot; no hard cut, teleport, morph or new object. Start camera by 0.35s.",
        f"Start at {path['entry_anchor']}; move {path['route']}; end at {path['destination']}; "
        f"settle on {path['settle_point']}.",
    ]
    if item["i2v_guard"]:
        parts.append(str(item["i2v_guard"]))
    if item["veo"] is not None:
        function = str(item["veo"]["function"]).lower().replace("_", " ")
        parts.append(
            f"Use one restrained {function} anchored in the physical world with real perspective, parallax, "
            "surface contact, lighting and natural occlusion; no floating HUD, screen graphic, text, number or label."
        )
    parts.extend((f"TTS timing: {schedule}", "No voice, music or subtitles."))
    prompt = " ".join(parts)
    if len(prompt) > 1250:
        raise ValueError(f"Flow 영상 프롬프트 1250자 초과: {len(prompt)}")
    required = (
        "locked start image", f"continuous {seconds}s", "no hard cut", "0.35s",
        str(path["entry_anchor"]), str(path["destination"]), "TTS timing", "No voice", "subtitles",
    )
    missing = [token for token in required if token.lower() not in prompt.lower()]
    if missing:
        raise ValueError(f"Flow 영상 프롬프트 필수 잠금 누락: {missing}")
    return prompt


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
                "civilization": "Present-day Chinese archaeology at Sanxingdui",
                "era": "the stated 1929, 1986 or 2021 Chinese discovery, excavation or conservation context",
                "people_lock": "East Asian Chinese farmers, workers, archaeologists and conservators only",
            })
        lock.update({"source_reference": item["source"], "site_artifact_fingerprint": item["fingerprints"]})
        row: dict[str, object] = {
            "n": n,
            "chapter": item["chapter"],
            "ct": item["scene_type"],
            "txt": narration,
            "tts": tts,
            "omni": seconds,
            "evidence": item["evidence"],
            "generation_mode": "I2V_LOCKED",
            "architecture_anchor_required": bool(item["architecture"]),
            "modern_scene": bool(item["modern"]),
            "motion_owner": "GENERATED_PHYSICS+VEO_INTEGRATED_3D" if item["veo"] else "GENERATED_PHYSICS",
            "motion_space": "WORLD_3D",
            "camera_path": item["camera_path"],
            "visual_lock": lock,
            "tts_beats": beats,
            "img_v2": image_prompt(item),
            "status": "PROMPT_LOCKED_IMAGE_PENDING",
        }
        row["vid"] = video_prompt(item, beats, seconds)
        if tts > 9.0:
            row["long_scene_review"] = "CONTINUOUS_SPATIAL_ACTION_REVIEWED_AND_FITS_10S"
        if item["veo"] is not None:
            row["veo_graphic"] = item["veo"]
        rows.append(row)

    (EPISODE / "02a.장면구분.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    table = [
        "# EP04 산싱두이 — 장면 구분표 v2", "",
        "> 장면 수는 승인 대본·실측 TTS·의미/행동/증거 전환에서 파생했다. 목표 컷 수가 아니다.", "",
        "| 장면 | 장 | TTS | 생성 | 유형 | 증거 | 모션 | 핵심 화면 |",
        "|---:|---|---:|---:|---|---|---|---|",
    ]
    visual = [
        "# EP04 산싱두이 — 고증 잠금 I2V 시각화 v2", "", f"scene_count: {len(rows)}",
        "scene_count_basis: SCRIPT_TTS_MEANING_ACTION_EVIDENCE_DERIVED", "generation_mode: I2V_LOCKED",
        "image_model: Nano Banana", "video_model: Veo/Flow Omni", "aspect_ratio: 9:16",
        "image_count_per_scene: 1", "video_count_per_scene: 1", "",
    ]
    image_lines: list[str] = []
    video_lines: list[str] = []
    ui_image_lines: list[str] = []
    ui_video_lines: list[str] = []
    for row, item in zip(rows, SPECS):
        core = str(item["image"]).split(":", 1)[0][:76].replace("|", "/")
        table.append(
            f"| {row['n']:03d} | {row['chapter']} | {row['tts']:.3f}s | {row['omni']}s | "
            f"{row['ct']} | {row['evidence']} | {row['motion_owner']} | {core} |"
        )
        visual.extend([
            f"## 장면 {row['n']:03d} — {row['ct']} / {row['evidence']}", "",
            f"- TTS: {row['tts']:.3f}s", f"- 생성 길이: {row['omni']}s",
            f"- 모션 소유권: {row['motion_owner']}", f"- 모션 공간: {row['motion_space']}",
            f"- 나레이션: {row['txt']}", "", "### IMAGE", "", str(row["img_v2"]), "",
            "### I2V", "", str(row["vid"]), "",
        ])
        image_lines.append(f"[SCENE {row['n']:03d}]\n{row['img_v2']}")
        video_lines.append(f"[SCENE {row['n']:03d} / {row['omni']}s]\n{row['vid']}")
        ui_image_lines.append(f"[SCENE {row['n']:03d}]\n{ui_image_prompt(item)}")
        ui_video_lines.append(
            f"[SCENE {row['n']:03d} / {row['omni']}s]\n{ui_video_prompt(item, row['tts_beats'], int(row['omni']))}"
        )

    (EPISODE / "02a.장면구분표.md").write_text("\n".join(table) + "\n", encoding="utf-8")
    (EPISODE / "02.시각화.txt").write_text("\n".join(visual), encoding="utf-8")
    (EPISODE / "flow_images_ep04.txt").write_text("\n\n".join(image_lines) + "\n", encoding="utf-8")
    (EPISODE / "flow_videos_ep04.txt").write_text("\n\n".join(video_lines) + "\n", encoding="utf-8")
    (EPISODE / "flow_images_ep04_ui.txt").write_text("\n\n".join(ui_image_lines) + "\n", encoding="utf-8")
    (EPISODE / "flow_videos_ep04_ui.txt").write_text("\n\n".join(ui_video_lines) + "\n", encoding="utf-8")
    print(f"EP04 시각화 빌드 완료: {len(rows)}장면")


if __name__ == "__main__":
    build()
