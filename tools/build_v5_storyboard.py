#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""EP01 v5 공개본의 고증 잠금 이미지·I2V 프롬프트를 재현하는 보관용 빌더.

장면 수는 이 파일에서 정하지 않는다. audio_v5/durations.json의 잠긴 TTS 장면을
입력으로 사용하고, 각 장면의 의미·행동 명세(SPECS)와 1:1인지 검증한 뒤 산출한다.

주의: 이 파일의 full-scale/slow 카메라 문법은 공개된 EP01 감사 기록이라 유지한다.
신규 회차에 복사하지 말고 02 지침 v5와 prompt_check.py의 camera_path 정책을 사용한다.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import _config  # noqa: F401


ROOT = Path(__file__).resolve().parents[1]
EPISODE = ROOT / "산출물" / "EP01_진시황릉"

STYLE = (
    "museum-quality cinematic archaeological 3D diorama reconstruction, full-scale immersive "
    "camera perspective with subtle diorama depth cues, physically based materials, high-frequency "
    "microtexture, micro-displacement, global illumination, sharp material separation, high fidelity, "
    "documentary realism rather than a toy miniature, 4K source detail, 9:16 vertical composition"
)
CIV = "Ancient China, Qin dynasty, 3rd century BC, Shaanxi loess plain below the Li mountain ridge"
MODERN_CIV = (
    "Present-day Qin Shi Huang Mausoleum landscape at Lintong, Xi'an, Shaanxi, on the loess plain "
    "north of Mount Li; archaeological documentary reconstruction, not an ancient reenactment"
)
PEOPLE = (
    "East Asian Chinese figures with East Asian facial features, Qin dynasty dress: knee-length hemp "
    "work robes, cross-collared and closing to the right, cloth waist sashes, hair gathered into a "
    "topknot, straw or cloth shoes, bare-headed or with simple cloth caps"
)
MODERN_PEOPLE = (
    "East Asian Chinese archaeologists and scientists only, wearing practical period-correct modern "
    "field clothing and protective equipment appropriate to the stated research date; no Qin costume "
    "on researchers, no historical reenactment"
)
ARCH = (
    "Qin architecture: rammed-earth walls, timber post-and-beam frames, grey ceramic tile roofs with "
    "gently upturned eaves, bracket sets under the eaves, no curved Japanese gables, no classical columns"
)
NEGATIVE_SHARED = (
    "no European or Western faces, no Roman or Greek tunics or togas, no classical columns, no medieval "
    "European clothing or armor, no Japanese or Indian architecture, no anachronistic tools or machinery, "
    "no round natural-looking hill for the mound, no fantasy pyramid, no generic tomb, "
    "no toy-like plastic surface, no low-poly game asset, no watermark, no text, no labels, no letters"
)
NEGATIVE_ANCIENT = NEGATIVE_SHARED + ", no modern clothing"
NEGATIVE_MODERN = (
    NEGATIVE_SHARED
    + ", no ancient costume on modern researchers, no exposed entrance unless archaeologically documented"
)

VISUAL_LOCK_BASE = {
    "civilization": "Qin China",
    "era": "late third century BCE; modern scenes explicitly marked present-day",
    "region": "Lintong District, Xi'an, Shaanxi; loess plain north of Mount Li",
    "people_lock": "East Asian Chinese only; Qin dress in ancient scenes; Chinese archaeologists in modern scenes",
    "forbidden_culture": ["European", "Roman", "Greek", "medieval European", "Japanese", "Indian", "Egyptian"],
    "diorama_style": "CINEMATIC_ARCHAEOLOGICAL_DIORAMA",
    "material_fidelity": "PBR_MICROTEXTURE_HIGH_FIDELITY",
}


def spec(
    chapter: str,
    scene_type: str,
    evidence: str,
    image: str,
    source: str,
    fingerprints: list[str],
    beat_actions: list[str],
    video: str,
    *,
    people: bool = False,
    architecture: bool = False,
    modern: bool = False,
    motion_owner: str = "GENERATED_PHYSICS",
    motion_space: str = "WORLD_3D",
    veo_graphic: dict[str, object] | None = None,
) -> dict[str, object]:
    return locals()


SPECS = [
    spec(
        "1. 진시황릉과 우물 아래 군대", "SITE_ESTABLISH", "미확인",
        "Present-day wide aerial three-quarter view of the real Qin Shi Huang mausoleum landscape at Lintong: a broad low square-trapezoidal rammed-loess burial mound softened by two millennia of erosion, its four sloping sides and broad flat summit fully covered in mature green grass and low vegetation, straight footprint still legible from the air, open archaeological landscape and the Mount Li ridge beyond. Show the protected mound exactly as it appears today, not a reconstruction: no ancient palace buildings, no perimeter walls, no exposed stair terraces, no excavated entrance, no terracotta figures at the mound, and no geometric ziggurat. The documented exterior is visible while the central chamber remains a completely opaque sealed earth volume, early-morning haze, restrained ochre and jade palette",
        "UNESCO Mausoleum of the First Qin Emperor site description and published site photography",
        ["present-day vegetated square-trapezoidal rammed-loess mound", "broad flat summit and legible straight footprint", "sealed opaque central earth volume"],
        ["Begin already close enough to read the square mound; hold the sealed center as the visual question.", "Ease upward just enough to reveal the full mausoleum landscape without exposing any interior."],
        "A slow descending crane settles toward the squared mound, then makes a restrained half-orbit that reveals its straight corners. Thin ground mist drifts across the loess plain; grass moves lightly. The camera stops at the sealed center and never crosses the ground surface.",
        architecture=False, modern=True,
    ),
    spec(
        "1. 진시황릉과 우물 아래 군대", "DISCOVERY_ACTION", "발굴확인",
        "March 1974 on the rural outskirts of Xi'an: a Chinese farmer inside a narrow hand-dug well pit, both hands gripping a wooden-handled iron pickaxe at the instant its point catches a hard reddish terracotta fragment embedded in compact loess; gritty soil grains, worn wood fibres, chipped pottery edge, tense low macro angle, no modern machinery",
        "Qin Mausoleum museum account of the March 1974 well-digging discovery",
        ["hand-dug rural well pit", "iron pickaxe striking a reddish terracotta shard", "compact Shaanxi loess around the impact"],
        ["Track the farmer's descending pickaxe through the well pit.", "On impact, snap focus from the hands to the terracotta edge and hold the discovery."],
        "The farmer completes one believable pickaxe stroke. The iron point stops abruptly against the buried shard, loose loess jumps from the impact, and his wrists recoil slightly. The camera tracks the tool tip and performs one rack focus onto the exposed terracotta edge; no second strike.",
        people=True, architecture=True,
    ),
    spec(
        "1. 진시황릉과 우물 아래 군대", "DISCOVERY_REVEAL", "발굴확인",
        "Macro view of the same reddish terracotta shard in compact loess at the well edge, with the curved cheek and ear of a life-size terracotta warrior only partly emerging nearby; behind the foreground soil, a carefully opened archaeological cutaway hints at long parallel rows of warriors and clay horses continuing into darkness, distinct earthenware grains and faint pigment traces, discovery not fantasy spectacle",
        "Museum excavation record for Pit 1 and terracotta warrior discovery context",
        ["same embedded terracotta shard continuity", "partly exposed life-size warrior face", "parallel subsurface rows of warriors and horses"],
        ["Start on the single shard and brush away only a thin veil of soil.", "Push through the soil edge as the cutaway opens to reveal ordered rows extending underground."],
        "A soft archaeological brush clears loose grains from the shard. The camera makes a macro push past its curved edge; the surrounding loess peels open as a clean physical section along the same axis, revealing already-present parallel ranks below. Dust falls down the cut face and settles between the rows.",
        motion_owner="GENERATED_PHYSICS+VEO_INTEGRATED_3D",
        motion_space="WORLD_3D",
        veo_graphic={
            "function": "SECTION_REVEAL", "evidence_relation": "Excavated Pit 1 layout; reveal only the documented pit, not the central chamber",
            "visual_language": "thin ochre section edge and falling loess grains, physically cut into the terrain",
            "start": "the exposed shard at the well edge", "via": ["the vertical loess cut face"], "end": "the documented parallel rows in Pit 1",
            "occlusion": "section edge passes in front of near rows, then near warriors occlude deeper ranks",
            "timing": "0.0-2.5s brush and macro focus; 2.5-6.5s section opens; final second holds",
            "camera_relation": "world-space section remains fixed and shows parallax during the push-in",
            "arrival_reaction": "a small fall of loess dust at the first revealed row",
        },
    ),
    spec(
        "1. 진시황릉과 우물 아래 군대", "EXCAVATION", "발굴확인",
        "High oblique archaeological diorama of Terracotta Army Pit 1, an immense rectangular timber-roofed excavation approximately 230 metres east-west by 62 metres north-south, long rammed-earth partition walls, life-size terracotta infantry, clay horses and wooden-chariot traces arranged in disciplined parallel corridors; two elegant unnumbered bronze-gold dimension lines are embedded along the pit's long and short edges, no generated numerals",
        "Emperor Qinshihuang's Mausoleum Site Museum dimensions and Pit 1 plan",
        ["rectangular Pit 1 with parallel corridors", "life-size infantry, horses and chariot formation", "230-by-62-metre documented footprint represented by two orthogonal dimension lines"],
        ["Reveal the formation immediately from a high oblique angle.", "Sweep the long dimension line from west to east, then the short line north to south.", "Lower slightly toward the ordered soldiers, horses and chariot traces."],
        "The camera cranes along the pit's long axis while the first thin bronze-gold dimension line grows between the physical end walls. A second shorter line grows across the width after the turn. Both lines are anchored to the excavated edges, receive perspective and pass behind raised partitions. Finish by lowering toward the front rank.",
        people=True,
        architecture=True,
        motion_owner="VEO_INTEGRATED_3D",
        motion_space="WORLD_3D",
        veo_graphic={
            "function": "DIMENSION_LINE", "evidence_relation": "Published museum dimensions of Pit 1: 230 m by 62 m; numbers remain in narration/captions",
            "visual_language": "slender aged-bronze survey lines with short perpendicular end ticks, no text",
            "start": "western exterior wall of Pit 1", "via": ["long corridor axis", "northern partition edge"], "end": "eastern and southern physical wall anchors",
            "occlusion": "lines disappear behind raised rammed-earth partitions and reappear in open corridors",
            "timing": "0.0-2.0s establish; 2.0-5.0s long line; 5.0-6.5s short line; final hold",
            "camera_relation": "dimension lines are fixed in world space and show correct parallax under the crane move",
            "arrival_reaction": "brief warm glint at each physical end tick",
        },
    ),
    spec(
        "1. 진시황릉과 우물 아래 군대", "SPATIAL_MAP", "측정확인",
        "Top-down-to-oblique 3D terrain map of the Qin mausoleum precinct showing the squared central mound at the true center and Terracotta Army pits clearly isolated to the east; a narrow muted-gold world-space route ribbon begins at Pit 1 and runs over the terrain to the sealed mound, with no numbers or labels, real loess topography and rectilinear enclosure traces",
        "Published archaeological site plan and measured approximately 1.5 km separation",
        ["central squared mound", "Terracotta Army pits east of the mound", "single measured east-west route relationship"],
        ["Begin over the eastern army pits and mark their separation from the center.", "Let the route ribbon travel west across the terrain toward the mound.", "Descend toward the opaque center and stop before it, leaving the question unresolved."],
        "A muted-gold route ribbon emerges from the physical center of Pit 1, travels west across documented ground, bends only with terrain relief, briefly passes behind an enclosure ridge, and arrives at the eastern foot of the squared mound. The camera follows from a high map view into an oblique descent, stopping at the sealed center.",
        architecture=True,
        motion_owner="VEO_INTEGRATED_3D",
        motion_space="WORLD_3D",
        veo_graphic={
            "function": "ROUTE_PATH", "evidence_relation": "Published plan places the army pits roughly 1.5 km east of the central mound",
            "visual_language": "thin muted-gold terrain-following ribbon with a short fading tail, no arrow icon and no text",
            "start": "documented center of Terracotta Army Pit 1", "via": ["eastern precinct terrain", "outer enclosure trace"], "end": "eastern foot of the central mound",
            "occlusion": "route passes behind the raised enclosure ridge and beneath foreground scrub before reappearing",
            "timing": "0.0-2.0s pit establish; 2.0-7.5s route travel; 7.5-9.5s sealed-center hold",
            "camera_relation": "ribbon is fixed to the terrain and gains parallax as map view becomes oblique",
            "arrival_reaction": "subtle dust ring at the mound-side ground anchor",
        },
    ),
    spec(
        "2. 무덤이 아니라 지하 제국", "SPATIAL_MAP", "발굴확인",
        "Museum-grade oblique terrain diorama of the more-than-56-square-kilometre mausoleum landscape, the squared mound surrounded by inner and outer enclosure traces and many documented pits, workshops, burial grounds and ritual features represented as hundreds of small physically recessed archaeological footprints; one soft amber scan wave spreads across the actual terrain, revealing density without invented buildings",
        "UNESCO description and museum inventory of more than 600 archaeological elements across the mausoleum area",
        ["broad mausoleum precinct exceeding the mound", "rectilinear inner and outer enclosures", "dense distributed archaeological features shown as ground footprints"],
        ["Start tight on the central mound so it appears to be one tomb.", "Pull back as a low scan wave reveals feature after feature across the larger precinct."],
        "The camera steadily pulls upward and backward from the mound. A low translucent amber scan wave begins at the inner enclosure, travels outward over the terrain, and leaves brief pinprick glints at already-present archaeological footprints before they return to natural color. It never creates buildings or text.",
        architecture=True,
        motion_owner="VEO_INTEGRATED_3D",
        motion_space="WORLD_3D",
        veo_graphic={
            "function": "SCAN_WAVE", "evidence_relation": "Surveyed mausoleum precinct and reported inventory of more than 600 elements",
            "visual_language": "low amber terrain-hugging scan sheet and brief warm ground glints",
            "start": "inner enclosure around the central mound", "via": ["outer enclosure", "documented pit clusters"], "end": "outer surveyed precinct boundary",
            "occlusion": "scan wave dips behind terrain rises and reappears across lower loess fields",
            "timing": "0.0-2.0s mound; 2.0-6.8s pullback and scan; final second wide hold",
            "camera_relation": "scan is world-anchored to terrain while the camera climbs",
            "arrival_reaction": "one restrained warm pulse at the outer boundary",
        },
    ),
    spec(
        "2. 무덤이 아니라 지하 제국", "ARTIFACT_MACRO", "발굴확인",
        "The excavated Qin bronze chariot and horse ensemble displayed as a museum-quality archaeological diorama: half-life-size bronze horses harnessed before an ornate covered chariot, cast bronze surfaces with controlled green patina, surviving gold and silver ornament, fine chains and canopy fittings, dark conservation-studio background, no driver invented, macro material realism",
        "Emperor Qinshihuang's Mausoleum Site Museum bronze chariots and horses",
        ["two documented half-size bronze chariot ensembles implied by paired plinths", "four bronze horses harnessed to a covered chariot", "gold and silver ornament over green-patinated bronze"],
        ["Glide from a gold-and-silver fitting toward the full chariot group.", "Continue past the horses to reveal the covered imperial carriage form."],
        "A raking museum light travels across the gold and silver fittings as the camera performs a slow lateral macro glide. Tiny chain elements sway almost imperceptibly; the camera widens only enough to connect the horses with the covered chariot, preserving every component.",
    ),
    spec(
        "2. 무덤이 아니라 지하 제국", "INVENTORY_TABLEAU", "발굴확인",
        "Excavated terracotta acrobat sculptures from the K9901 pit and solemn civil-official terracotta statues interpreted from another burial pit, arranged in two connected conservation bays within one archaeological diorama; athletic torsos and dynamic limbs on one side, long-robed administrative posture and headgear on the other, unglazed clay, fractures, restoration seams and soil residue sharply visible",
        "Museum publications for acrobat figures and civil-official interpreted terracotta statues",
        ["dynamic acrobat terracotta bodies", "long-robed official-type terracotta statues", "separate excavated contexts shown as adjacent conservation bays"],
        ["Track past the dynamic acrobat statues first.", "Rack focus across the bay divider to the still official-type statues."],
        "The camera moves laterally through the acrobat bay, following one extended clay arm, then slows at the physical divider and racks focus to the official-type statues. A conservation light moves with the camera, revealing cracks and clay grains; statues remain motionless.",
        people=True,
    ),
    spec(
        "2. 무덤이 아니라 지하 제국", "ARTIFACT_MACRO", "발굴확인",
        "A separate excavated pit with life-size bronze waterfowl—cranes, geese and swans—placed along a narrow reconstructed watercourse, each bird showing thin cast legs, beaks, feather modelling and mottled green-brown corrosion; damp dark soil and controlled museum excavation light, no palace interior",
        "Museum documentation of bronze waterfowl pit K0007",
        ["life-size bronze cranes, geese and swans", "linear placement along a watercourse-like pit", "mottled green-brown bronze corrosion"],
        ["Begin on the corroded beak and eye of one bronze crane, then glide along the line of birds."],
        "A narrow band of reflected light slides across the bronze crane's beak. The camera glides low beside the watercourse-like trench, revealing geese and swans receding in depth. Only a faint ripple moves in the shallow reconstruction water; the bronze birds remain still.",
    ),
    spec(
        "2. 무덤이 아니라 지하 제국", "ARTIFACT_MACRO", "발굴확인",
        "Excavated stone armour made from hundreds of small pale limestone plates, each plate drilled at the edges and connected by thin bronze wire, laid in a careful articulated armour form on a dark conservation table; powdery stone pores, saw marks, chips, drilled holes and green wire corrosion in extreme macro detail",
        "Museum documentation of stone armour from pit K9801",
        ["many small limestone plates", "edge-drilled holes linked by bronze wire", "articulated armour arrangement rather than a solid cuirass"],
        ["Orbit slowly over the interlinked plates, ending on a drilled hole and corroded bronze connector."],
        "The camera makes a shallow macro orbit across overlapping limestone plates. Raking light reveals powdery pores and tool marks; a final focus pull lands on one drilled hole and its green-corroded bronze wire. Nothing assembles or floats.",
    ),
    spec(
        "2. 무덤이 아니라 지하 제국", "INVENTORY_TABLEAU", "학술해석",
        "A dark museum study table holding four verified artifact groups in separate pools of warm light—terracotta warrior fragment, bronze chariot fitting, official-type clay head and acrobat torso—with their excavation context represented by distinct soil plinths rather than treasure piles; no gold-hoard fantasy, every object separated and readable",
        "Synthesis of excavated artifact groups and their interpreted functions",
        ["four distinct excavated object groups", "separate context plinths", "study-table comparison rather than treasure heap"],
        ["Let the first light make the group resemble a treasure display.", "Shift to four separate controlled light pools that isolate each object's different role."],
        "The camera begins with a compressed view that makes the objects overlap, then slides sideways as four warm light pools separate the groups on their own soil plinths. The final composition reads as an evidence table, not a treasure heap.",
        people=True,
    ),
    spec(
        "2. 무덤이 아니라 지하 제국", "INVENTORY_TABLEAU", "학술해석",
        "A wide circular archaeological evidence tableau in one coherent underground precinct model: terracotta infantry formation, bronze imperial chariot, official-type clay statues and acrobat sculptures occupy four physically connected zones around the squared mound; thin recessed bronze pathways in the floor connect each zone to its interpreted social role without text or icons",
        "Scholarly interpretation of differentiated functions within the mausoleum precinct",
        ["military terracotta zone", "imperial chariot zone", "official and entertainment statue zones"],
        ["Circle past the soldiers and chariot, then continue the same orbit across the official and acrobat zones until all four read as parts of one system."],
        "The camera makes one slow clockwise orbit. As each zone enters the foreground, its recessed bronze pathway warms briefly and then cools, guiding the eye from army to chariot to officials to acrobats. Pathways remain embedded in the physical floor and no text appears.",
        people=True,
        motion_owner="VEO_INTEGRATED_3D",
        motion_space="WORLD_3D",
        veo_graphic={
            "function": "ROUTE_PATH", "evidence_relation": "Interpretive link between excavated object groups and court or imperial functions",
            "visual_language": "subtle recessed bronze pathways that warm one at a time, no arrows or icons",
            "start": "terracotta infantry zone", "via": ["bronze chariot zone", "official-type statue zone"], "end": "acrobat sculpture zone",
            "occlusion": "pathways pass beneath artifact plinths and are partially hidden by foreground objects",
            "timing": "0.0-1.5s army; 1.5-3.0s chariot; 3.0-4.5s officials; 4.5-6.1s acrobats",
            "camera_relation": "pathways remain fixed to the precinct floor under the orbit",
            "arrival_reaction": "one soft warm reflection on the destination plinth",
        },
    ),
    spec(
        "2. 무덤이 아니라 지하 제국", "CUTAWAY", "학술해석",
        "A monumental sectional terrain diorama of the mausoleum precinct, exterior mound and farmland above, documented surrounding pits and object zones below and around it forming a distributed subterranean imperial world; the central chamber itself is a featureless black sealed block with no visible contents, while verified outer zones remain detailed and illuminated",
        "UNESCO interpretation of a designed mausoleum complex reflecting imperial order",
        ["surface mound over a broad precinct", "documented peripheral pits with distinct functions", "central chamber rendered as an opaque unknown block"],
        ["Start on the surface mound and outer guard zone.", "Open the surrounding terrain section to reveal the distributed verified precinct while leaving the center sealed."],
        "The camera pulls through the surface into a clean sectional view. A warm section edge travels outward around the mound, revealing only the documented surrounding pits and their different zones. The central black volume never opens; all detail stops at its boundary.",
        architecture=True,
        motion_owner="VEO_INTEGRATED_3D",
        motion_space="WORLD_3D",
        veo_graphic={
            "function": "SECTION_REVEAL", "evidence_relation": "Interpretation combines documented peripheral pits; central chamber remains unknown",
            "visual_language": "warm ochre section rim around verified zones, absolute matte-black central unknown",
            "start": "surface edge beside the mound", "via": ["documented eastern and western pits"], "end": "outer precinct section boundary",
            "occlusion": "cut earth edge occludes deeper zones until it passes; the black center occludes everything behind it",
            "timing": "0.0-1.5s surface; 1.5-4.5s section reveal; final second sealed-center hold",
            "camera_relation": "section geometry is fixed in world space during the pull-through",
            "arrival_reaction": "settling soil dust only along the verified outer cut edge",
        },
    ),
    spec(
        "2. 무덤이 아니라 지하 제국", "HISTORICAL_RECONSTRUCTION", "학술해석",
        "A restrained Qin imperial-order reconstruction shown as a museum diorama above a documented site plan: the rectilinear capital Xianyang and formal court processional order echo the mausoleum's rectilinear enclosures and specialized pits below, all figures small, orderly and non-dramatic; no claim that the two spaces are physically identical",
        "UNESCO statement that the mausoleum reflects the urban plan of Xianyang and imperial order",
        ["rectilinear Qin capital planning", "formal processional hierarchy", "visual echo with mausoleum enclosures and specialized zones"],
        ["Glide across the capital's ordered axis.", "Tilt down to the mausoleum plan below, aligning the visual rhyme without merging them as fact."],
        "A slow axial glide crosses the restrained Qin capital reconstruction. The camera tilts down as the city axis and the separate mausoleum plan below align for one moment, then parallax clearly separates the two models. Tiny processional groups move at walking pace.",
        people=True, architecture=True,
    ),
    spec(
        "3. 봉토 아래의 문헌과 측정", "SEALED_UNKNOWN", "미확인",
        "Symmetrical cutaway of the squared mound divided by one sharp vertical boundary: on the left, brightly documented outer pits and surveyed enclosure geometry; on the right, an aged bamboo-slip manuscript resting outside a completely opaque central earth block, making physical evidence and written record visibly separate; no interior objects shown",
        "Evidence-state synthesis: excavated outer precinct versus unexcavated central chamber and textual claims",
        ["documented outer-pit side", "separate bamboo-slip record side", "opaque sealed central volume between them"],
        ["Approach the center question through the mound.", "Slide the camera across the boundary so excavated evidence and written record occupy distinct sides."],
        "The camera pushes toward the sealed center, then makes a precise lateral slide across the physical boundary between excavated terrain and the bamboo-slip evidence table. A thin neutral light seam grows along that boundary and stops; the central volume remains opaque.",
    ),
    spec(
        "3. 봉토 아래의 문헌과 측정", "TEXT_RECORD", "문헌기록",
        "Ancient bamboo slips of Sima Qian's Shiji on a dark archival table, tied with aged cord and bearing only abstract non-legible ink texture; above the slips floats a small translucent sepia conceptual diorama containing a palace silhouette, strange treasure glints and a Qin crossbow silhouette aimed toward an empty passage, clearly contained inside the manuscript's projected frame rather than presented as excavated reality",
        "Shiji, Basic Annals of Qin Shi Huang; written roughly a century after the emperor's death",
        ["aged bamboo-slip manuscript", "conceptual palace and treasure imagery contained above the record", "Qin crossbow silhouette contained in the same textual projection"],
        ["Scan across the physical bamboo slips, then let the record cast one translucent reconstruction containing palace, treasure and crossbow motifs."],
        "A warm raking light scans the bamboo surfaces. From the manuscript plane, one translucent sepia reconstruction rises only a few centimetres, with palace, treasure glints and crossbow remaining ghostlike and bounded by the slip edges. The camera never enters the reconstruction.",
        architecture=True,
    ),
    spec(
        "3. 봉토 아래의 문헌과 측정", "TEXT_RECORD", "문헌기록",
        "A large aged bamboo-slip manuscript of Sima Qian's Shiji dominates the foreground as the unmistakable evidence source. Directly above the slips, one deliberately translucent sepia glass-like textual vignette contains only a dark conceptual ceiling filled with sparse star points and a floor map crossed by branching mirror-silver waterways; it is explicitly record-based and not excavated evidence, not an excavated chamber. Behind the main manuscript, a second isolated weathered manuscript plinth sits farther away and slightly out of focus to express the century-later authorship gap without numbers or labels. No palace exterior, no city, no construction site, no workers, no monumental building, no mountain dominating the frame",
        "Shiji textual description of constellations and mercury rivers; chronology of the text",
        ["star points on a conceptual ceiling", "branching silver conceptual waterways", "separate later textual time-layer plinth"],
        ["Move from the star points down to the silver channels inside the textual vignette.", "Pull back to reveal the separate later manuscript time layer and weaken the reconstruction."],
        "Inside the bounded textual vignette, dim star points brighten in sequence and restrained silver streams travel along pre-existing channels. The camera tilts down from ceiling to floor, then pulls back to reveal the later manuscript plinth. The reconstruction fades to a weaker translucency but does not disappear.",
        architecture=False,
        motion_owner="VEO_INTEGRATED_3D",
        motion_space="WORLD_3D",
        veo_graphic={
            "function": "MATERIAL_FLOW", "evidence_relation": "Visualization is limited to Shiji's written claim; it is not excavated evidence",
            "visual_language": "mirror-silver liquid strands confined inside a translucent sepia manuscript vignette",
            "start": "first conceptual channel beneath the star ceiling", "via": ["branching floor channels"], "end": "small conceptual basin inside the vignette",
            "occlusion": "silver streams pass behind miniature conceptual walls and remain clipped by the manuscript frame",
            "timing": "0.0-3.5s stars and channel flow; 3.5-6.5s pullback to manuscript; final second fade",
            "camera_relation": "all conceptual flow is anchored inside the small textual model and shows its own parallax",
            "arrival_reaction": "one faint silver reflection on the manuscript cord",
        },
    ),
    spec(
        "3. 봉토 아래의 문헌과 측정", "SEALED_UNKNOWN", "미확인",
        "Present-day scientific cutaway of the squared mound as a solid, unbroken mass of rammed loess; the central chamber region is an opaque black volume surrounded by undisturbed strata, with an empty conservation tray in the foreground to emphasize that no object has been removed from it; outer excavated finds remain far outside the sealed boundary",
        "Current archaeological status: the central chamber has not been excavated",
        ["unbroken mound strata", "opaque central unknown", "empty tray and zero central-chamber artifacts"],
        ["Track from the empty tray toward the mound section.", "Stop at the opaque chamber boundary and hold long enough to register that nothing came out."],
        "The camera passes over the empty tray and pushes slowly into the mound section. Soil layers show slight parallax, but the black central volume absorbs the light and reveals nothing. The camera comes to a complete stop at the boundary.",
        modern=True,
    ),
    spec(
        "3. 봉토 아래의 문헌과 측정", "SCIENTIFIC_EVIDENCE", "측정확인",
        "Present-day 1985 soil-sampling reconstruction over a documented cross-section of the squared mound: Chinese scientists in period-appropriate 1980s field clothing collect shallow soil cores across the mound surface; within the visible earth, numerous small sample points are fixed in their real surface positions, with a restrained amber scan wave converging toward a denser central cluster, no chamber interior shown",
        "1985 geochemical survey reporting anomalous mercury concentrations in mound soil",
        ["surface soil-core sampling grid", "scientists outside the sealed mound", "denser measured central sample response without interior claim"],
        ["Follow a soil core being lifted from the mound surface.", "Transition to the wider sampling grid as a scan wave converges on the anomalous central cluster."],
        "A scientist lifts one shallow soil core; loose grains fall back into the sampling hole. The camera cranes upward to the full grid. A restrained amber scan wave travels from outer sample points toward the denser central cluster, each physical marker pulsing once. Nothing penetrates or opens the chamber.",
        people=True, modern=True,
        motion_owner="GENERATED_PHYSICS+VEO_INTEGRATED_3D",
        motion_space="WORLD_3D",
        veo_graphic={
            "function": "SCAN_WAVE", "evidence_relation": "Measured anomalous mercury concentration in mound soil, not proof of river geometry",
            "visual_language": "thin amber terrain-following scan and restrained single pulses at physical sampling markers",
            "start": "outer surface sampling points", "via": ["mid-slope soil cores"], "end": "denser central surface sample cluster",
            "occlusion": "scan dips behind the mound ridge and reappears on the near slope",
            "timing": "0.0-2.5s soil core; 2.5-6.0s crane and scan; final second central cluster hold",
            "camera_relation": "scan and sample pulses stay fixed to the mound surface under the crane move",
            "arrival_reaction": "central soil grains catch one faint amber reflection",
        },
    ),
    spec(
        "3. 봉토 아래의 문헌과 측정", "SCIENTIFIC_EVIDENCE", "측정확인",
        "Split-depth scientific evidence diorama: a translucent surface map of measured mercury anomaly aligns above the still-opaque mound, while far to one side the Shiji manuscript holds its own faint silver river motif; the two patterns overlap only as semi-transparent projections above the surface, and below them the real central volume remains black and unreadable",
        "Comparison of Shiji claim with surface mercury anomaly; exact interior distribution unknown",
        ["measured surface anomaly map", "separate textual river motif", "black unknown interior that neither layer resolves"],
        ["Align the measured surface pattern with the manuscript motif to show the intriguing overlap.", "Then rotate slightly so the patterns separate and the unknown interior remains obvious."],
        "The camera eases sideways until the amber measured surface pattern and the faint silver manuscript motif briefly overlap. It then continues into a small orbit that separates the two translucent layers in depth. The sealed black volume below never changes.",
    ),
    spec(
        "4. 왜 열지 않는가", "CONSERVATION", "발굴확인",
        "A conservation-focused excavation tableau at Terracotta Army Pit 1: a newly uncovered warrior head still carries vivid mineral pigments and lacquer ground on the buried side, while the already air-exposed side shows fragile curling color layers; a transparent boundary between moist soil microclimate and open excavation air is visible as condensation and dust, not as a flat infographic",
        "Documented pigment loss observed during Terracotta Army excavation",
        ["newly exposed terracotta head", "vivid pigment and lacquer-ground traces", "physical boundary between damp burial soil and dry air"],
        ["Begin with the tempting view of opening the soil around the warrior.", "Pause at the exposed-air boundary so the problem is visible.", "Cross the air boundary and hold on the first fragile pigment response."],
        "A brush removes the final thin soil veil from the warrior's cheek. As open air reaches it, condensation retreats and tiny edges of pigment begin to curl. The camera stops pushing and holds on the vulnerable surface rather than celebrating the reveal.",
    ),
    spec(
        "4. 왜 열지 않는가", "ARTIFACT_MACRO", "발굴확인",
        "Close frontal museum reconstruction of a life-size Qin terracotta warrior as originally polychromed: deep red and purple robe panels, dark lamellar armour, skin tones and black hair survive in irregular documented patches over matte earthenware, with adjacent present-day earth-coloured portions visible for direct comparison; mineral pigment, lacquer ground and clay pores sharply separated",
        "Published conservation research and surviving pigment evidence on Terracotta Army figures",
        ["Qin lamellar armour and side topknot", "irregular surviving polychrome patches", "visible earthenware areas for comparison"],
        ["Move a narrow raking light from the current earth-coloured side to the reconstructed polychrome side."],
        "A narrow raking light travels across the warrior from bare earthenware into irregular colored regions, revealing lacquer gloss only in tiny surviving patches. The camera makes a restrained five-degree orbit; the statue remains completely still.",
        people=True,
    ),
    spec(
        "4. 왜 열지 않는가", "CONSERVATION", "발굴확인",
        "Extreme macro cross-section of terracotta pigment stratigraphy at the moment of air exposure: porous clay body, thin dark lacquer ground and mineral color layer are physically distinct; the lacquer ground dries, contracts and curls upward, carrying a small color flake with it, every crack and fibre-scale edge visible, neutral conservation lighting",
        "Journal of Cultural Heritage research on conservation of polychromy from the Terracotta Army",
        ["porous terracotta substrate", "thin lacquer ground beneath pigment", "drying curl and delamination at the exposed edge"],
        ["Watch the damp lacquer ground lose sheen and contract.", "Follow one pigment edge as it curls and detaches into the air."],
        "Moist sheen retreats across the lacquer ground, which contracts by a tiny believable amount. One colored edge slowly curls upward and a single flake releases, rotating once before settling nearby. The camera tracks that flake with macro focus; no mass disintegration.",
    ),
    spec(
        "4. 왜 열지 않는가", "CONSERVATION", "학술해석",
        "A controlled archaeological section showing a stable 2,200-year-old sealed loess microenvironment on one side and the same exposed section after excavation on the other: humidity beads, compact soil and intact pigment remain protected behind the sealed boundary, while air flow, drying cracks and detached microscopic evidence appear only on the opened side; no disaster spectacle",
        "Conservation interpretation based on excavated pigment deterioration",
        ["sealed humid loess microenvironment", "opened dry-air boundary", "evidence loss localized to exposure"],
        ["Hold the stable sealed side almost motionless.", "Let the boundary open slightly and trace the cascade of humidity loss, crack growth and one detached flake."],
        "The sealed side breathes only through tiny moisture glints. A narrow opening forms at the physical boundary; dry air moves through it, condensation retreats, one crack lengthens and a single pigment flake falls. The camera stays locked so the before-and-after contrast is unmistakable.",
    ),
    spec(
        "4. 왜 열지 않는가", "SCIENTIFIC_EVIDENCE", "미확인",
        "Present-day non-invasive research diorama around the fully sealed real mausoleum mound: a broad low grass-covered square-trapezoidal earthen mass with a broad flat summit and four continuous unbroken slopes. Chinese conservators, structural engineers and environmental scientists work only at the outside perimeter with ground sensors, vapor-safe sampling tubes, surveying tripods and conservation mock-ups. Three restrained physical pathways—silver for mercury risk, ochre for structural load and pale blue for preservation climate—stop at the intact earth boundary. No excavation trench, no doorway, no portal, no stairs, no ramp, no tunnel, no path piercing the mound, no cutaway and no exposed chamber",
        "Current rationale: mercury, structural safety and artifact conservation constraints",
        ["sealed mound with no excavation", "three external research disciplines", "three risk pathways stopping at the boundary"],
        ["Negate the trap myth by showing an undisturbed, quiet mound.", "Orbit through mercury sampling, structural monitoring and conservation tests, all stopping outside the center."],
        "The camera makes one calm orbit around the sealed mound. A silver sampling path reaches an external soil probe, an ochre structural hazard load path travels through a test section, and pale-blue preservation hazard particles circulate inside a conservation mock-up. Each path remains anchored to its physical apparatus and stops before the mound center.",
        people=True, modern=True,
        motion_owner="VEO_INTEGRATED_3D",
        motion_space="WORLD_3D",
        veo_graphic={
            "function": "DANGER_ZONE", "evidence_relation": "Three active research constraints: mercury exposure, structural safety and conservation, not a verified mechanical trap",
            "visual_language": "three muted material pathways tied to real external instruments; no warning icon or HUD",
            "start": "external mercury soil probe", "via": ["structural test section", "preservation-climate mock-up"], "end": "sealed boundary shared by all three constraints",
            "occlusion": "paths pass behind instruments and foreground technicians, then stop visibly at the earth boundary",
            "timing": "0.0-1.5s quiet mound; 1.5-5.8s three instruments; final half-second all paths stop",
            "camera_relation": "all pathways are fixed to apparatus and receive orbit parallax",
            "arrival_reaction": "one soft desaturated reflection at the sealed boundary",
        },
    ),
    spec(
        "4. 왜 열지 않는가", "SCIENTIFIC_EVIDENCE", "미확인",
        "Present-day premium scientific archaeological diorama with the research apparatus as the foreground subject: on flat continuous undisturbed ground outside the protected perimeter, a modern Chinese non-invasive survey team has arranged one ground-penetrating radar cart, a low-frequency sensor tripod, shallow environmental probes and a sealed climate-controlled conservation test case containing pigment replicas. Each instrument is physically separate and museum-clear at camera height. Far behind them, the real mausoleum mound rises positively above the plain as one intact broad low grass-covered square-trapezoidal earthwork with a broad flat rectangular summit and continuous unbroken vegetated slopes; it is softly focused but unmistakably solid and sealed. No pit, no depression, no sunken square, no negative landform, no doorway, no portal, no black hole, no stairs, no ramp, no tunnel, no excavation trench, no exposed chamber, no cutaway and no cross-section. The source frame is quiet and static so a thin warm scan path can leave the foreground sensors, travel only across the exterior ground, touch the mound perimeter and return during I2V",
        "Current archaeological and conservation problem: investigation without destructive excavation",
        ["opaque central unknown", "non-invasive survey wave returning from boundaries", "external conservation test replicas"],
        ["State the remaining mystery by approaching the dark center.", "Send a non-invasive scan envelope around the boundary and receive it back without opening anything.", "Pull out to place the scientific method, not a treasure reveal, as the ending answer."],
        "The camera advances toward the opaque central volume, slows, and stops. A thin warm scan envelope travels from surface sensors around the outer boundary, bends with the mound geometry, and returns to the instruments. The camera then pulls back to include conservation mock-ups; no door opens and no interior appears.",
        modern=True,
        motion_owner="VEO_INTEGRATED_3D",
        motion_space="WORLD_3D",
        veo_graphic={
            "function": "SCAN_WAVE", "evidence_relation": "Conceptual non-invasive research goal; no claim that the central chamber has been imaged in detail",
            "visual_language": "thin warm boundary-following scan envelope with a faint returning tail",
            "start": "surface sensor array", "via": ["outer rammed-loess strata", "sealed chamber boundary"], "end": "the same external sensor array",
            "occlusion": "scan disappears behind the opaque center and is visible again only when returning through mapped outer soil",
            "timing": "0.0-2.5s approach; 2.5-6.5s scan circuit; 6.5-8.0s pullback",
            "camera_relation": "scan is locked to mound geometry and shows depth parallax during both push and pull",
            "arrival_reaction": "one restrained data-light pulse on the external sensor housing",
        },
    ),
    spec(
        "4. 왜 열지 않는가", "SITE_ESTABLISH", "미확인",
        "Final dignified late-golden-hour high oblique aerial of the real present-day Qin Shi Huang mausoleum landscape beneath Mount Li. The actual mound must read unmistakably as a broad low square-trapezoidal rammed-loess earthwork: its complete straight four-sided rectangular footprint and all four squared corners are visible, each long side slopes continuously toward a broad flat rectangular summit that is much wider than the mound is tall, mature grass and low vegetation soften but do not erase the geometry. The foreground perspective emphasizes one crisp straight corner and the distant opposite corner. No round hill, no conical mound, no bell-shaped silhouette, no natural mountain shape, no reconstructed Qin palace, no perimeter wall, no exposed terraces, no excavated entrance, no stairs and no ziggurat. Warm side light grazes the vegetated earthen planes while the center remains quiet and sealed; faint distant modern conservation lights stay only outside the mound perimeter, restrained world-heritage documentary atmosphere, no interior reveal",
        "UNESCO World Heritage site and present archaeological status",
        ["present-day vegetated square-trapezoidal mound silhouette", "Mount Li and loess landscape", "quiet sealed center with conservation presence only at perimeter"],
        ["Begin with the wide world-heritage landscape.", "Make one slow pullback as the last warm light leaves the mound, ending on stillness."],
        "A slow, almost imperceptible pullback reveals more of the loess plain and Mount Li. Grass moves in a light evening wind, distant perimeter lights warm gently, and the mound stays sealed. Motion settles to complete stillness for the closing beat.",
        architecture=False, modern=True,
    ),
]


def sentence_parts(text: str) -> list[str]:
    protected = re.sub(r"(?<=\d)\.(?=\d)", "<DECIMAL>", text)
    parts = [
        part.replace("<DECIMAL>", ".").strip()
        for part in re.findall(r"[^.!?。！？]+[.!?。！？]?", protected)
        if part.strip()
    ]
    return parts or [text]


def generate_beats(text: str, duration: float, actions: list[str]) -> list[dict[str, object]]:
    parts = sentence_parts(text)
    if len(parts) != len(actions):
        raise ValueError(f"TTS 비트 수 불일치: 문장 {len(parts)} / 행동 {len(actions)}\n{text}")
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
            "graphic": "scene-integrated only; exact Korean and numbers remain in captions",
        })
        cursor = end
    return beats


def choose_duration(tts: float) -> int:
    for value in (4, 6, 8, 10):
        if tts + 0.25 <= value:
            return value
    raise ValueError(f"10초를 넘는 TTS 장면: {tts:.3f}")


def image_prompt(item: dict[str, object]) -> str:
    anchors = [STYLE, MODERN_CIV if item["modern"] else CIV]
    if item["people"]:
        anchors.append(MODERN_PEOPLE if item["modern"] else PEOPLE)
    if item["architecture"]:
        anchors.append(ARCH)
    anchors.extend([str(item["image"]), NEGATIVE_MODERN if item["modern"] else NEGATIVE_ANCIENT])
    return ". ".join(anchor.rstrip(". ") for anchor in anchors) + "."


def video_prompt(item: dict[str, object], beats: list[dict[str, object]]) -> str:
    schedule = " ".join(
        f"{beat['start']:.2f}-{beat['end']:.2f}s: {beat['action']}"
        for beat in beats
    )
    shared = (
        "Use the supplied locked start image and preserve all objects, identities, site geometry, artifact "
        "fingerprints, materials, culture, lighting and composition. Single continuous shot, no hard cut, no "
        "teleport, no morph, no new objects. "
    )
    if "VEO_INTEGRATED_3D" in str(item["motion_owner"]):
        shared += (
            "Every explanatory line, path, scan or particle is anchored in the physical world space, receives "
            "camera parallax, correct surface perspective and natural occlusion by architecture or artifacts. "
            "No floating HUD, no screen-space graphics, no text. "
        )
    return shared + str(item["video"]) + " TTS-locked timing: " + schedule + " No voice, no music, no subtitles."


def build() -> None:
    duration_data = json.loads((EPISODE / "audio_v5" / "durations.json").read_text(encoding="utf-8"))
    source_scenes = duration_data["scenes"]
    if len(source_scenes) != len(SPECS):
        raise ValueError(f"잠긴 TTS {len(source_scenes)}장면과 시각 명세 {len(SPECS)}장면이 다릅니다")

    rows: list[dict[str, object]] = []
    for n, item in enumerate(SPECS, 1):
        source = source_scenes[str(n)]
        narration = source["text"]
        tts = float(source["duration"])
        beats = generate_beats(narration, tts, item["beat_actions"])
        lock = dict(VISUAL_LOCK_BASE)
        lock.update({
            "source_reference": item["source"],
            "site_artifact_fingerprint": item["fingerprints"],
        })
        row = {
            "n": n,
            "chapter": item["chapter"],
            "ct": item["scene_type"],
            "txt": narration,
            "tts": tts,
            "omni": choose_duration(tts),
            "evidence": item["evidence"],
            "generation_mode": "I2V_LOCKED",
            "architecture_anchor_required": bool(item["architecture"]),
            "modern_scene": bool(item["modern"]),
            "motion_owner": item["motion_owner"],
            "motion_space": item["motion_space"],
            "visual_lock": lock,
            "tts_beats": beats,
            "img_v2": image_prompt(item),
            "vid": video_prompt(item, beats),
            "status": "PROMPT_LOCKED_IMAGE_PENDING",
        }
        if tts > 9.0:
            row["long_scene_review"] = "CONTINUOUS_SPATIAL_ACTION_REVIEWED_AND_FITS_10S"
        if item["veo_graphic"] is not None:
            row["veo_graphic"] = item["veo_graphic"]
        rows.append(row)

    (EPISODE / "02a.장면구분.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    md = [
        "# EP01 진시황릉 — 장면 구분표 v5", "",
        "> 장면 수는 잠긴 대본·실측 TTS·의미/행동 변화에서 파생했다. 목표 컷 수가 아니다.", "",
        "| 장면 | 장 | TTS | 생성 | 유형 | 증거 | 모션 | 핵심 화면 |",
        "|---:|---|---:|---:|---|---|---|---|",
    ]
    for row, item in zip(rows, SPECS):
        core = str(item["image"]).split(":", 1)[0][:70].replace("|", "/")
        md.append(
            f"| {row['n']:03d} | {row['chapter']} | {row['tts']:.3f}s | {row['omni']}s | "
            f"{row['ct']} | {row['evidence']} | {row['motion_owner']} | {core} |"
        )
    (EPISODE / "02a.장면구분표.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    visual = [
        "# EP01 진시황릉 — 고증 잠금 I2V 시각화 v5", "",
        f"scene_count: {len(rows)}", "scene_count_basis: SCRIPT_TTS_MEANING_ACTION_DERIVED",
        "generation_mode: I2V_LOCKED", "image_model: Nano Banana 2", "video_model: Veo/Flow Omni",
        "aspect_ratio: 9:16", "image_count_per_scene: 1", "video_count_per_scene: 1", "",
    ]
    image_lines: list[str] = []
    video_lines: list[str] = []
    for row in rows:
        visual.extend([
            f"## 장면 {row['n']:03d} — {row['ct']} / {row['evidence']}", "",
            f"- TTS: {row['tts']:.3f}s", f"- 생성 길이: {row['omni']}s",
            f"- 모션 소유권: {row['motion_owner']}", f"- 모션 공간: {row['motion_space']}",
            f"- 나레이션: {row['txt']}", "", "### IMAGE", "", row["img_v2"], "", "### I2V", "", row["vid"], "",
        ])
        image_lines.append(f"[SCENE {row['n']:03d}]\n{row['img_v2']}")
        video_lines.append(f"[SCENE {row['n']:03d} / {row['omni']}s]\n{row['vid']}")
    (EPISODE / "02.시각화.txt").write_text("\n".join(visual), encoding="utf-8")
    (EPISODE / "flow_images_v5.txt").write_text("\n\n".join(image_lines) + "\n", encoding="utf-8")
    (EPISODE / "flow_videos_v5.txt").write_text("\n\n".join(video_lines) + "\n", encoding="utf-8")
    print(f"v5 시각화 빌드 완료: {len(rows)}장면")


if __name__ == "__main__":
    build()
