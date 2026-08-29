#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""EP05 로제타석 승인 TTS에서 고증 잠금 I2V 장면표와 Flow 입력을 만든다."""

from __future__ import annotations

import json
from pathlib import Path

import _config  # noqa: F401


ROOT = Path(__file__).resolve().parents[1]
EPISODE = ROOT / "산출물" / "EP05_로제타석"
EPISODE_LABEL = "EP05 로제타석"
SCENE_COUNT_NOTE = "승인 대본·실측 TTS·의미/행동/장소/증거 전환에서 파생했다. 목표 컷 수가 아니다."

STYLE = (
    "premium full-frame cinematic archaeological 3D diorama, unmistakably a museum-scale crafted "
    "miniature world and not live-action, immersive macro-lens depth cues, restrained tilt-shift, "
    "layered foreground-midground-background depth, physically based PBR materials, high-frequency "
    "microtexture, micro-displacement, sharp material separation, global illumination, high fidelity, "
    "4K source detail, 9:16 vertical composition"
)
ANCIENT_CIV = (
    "Ptolemaic Egypt, 196 BCE, Memphis priestly decree under Ptolemy V, with the surviving fragment "
    "found near Rashid in the western Nile Delta"
)
MODERN_CIV = (
    "Late eighteenth and early nineteenth century Mediterranean archaeology, specifically French "
    "military engineering near Rashid in 1799 and scholarly study in Britain and France through 1822"
)
ANCIENT_PEOPLE = (
    "Ptolemaic Egyptian priests and scribes with North African Egyptian features, shaved or close-cropped "
    "priestly heads, clean white linen temple garments, alongside restrained Macedonian Greek royal court "
    "dress appropriate to second-century BCE Egypt"
)
MODERN_PEOPLE = (
    "Late eighteenth and early nineteenth century European French military engineers and scholars in "
    "historically accurate 1799 campaign uniforms or sober 1800s study clothing, with no modern equipment"
)
ANCIENT_ARCH = (
    "Ptolemaic Egyptian temple architecture with sandstone pylons, columned courts, carved relief registers, "
    "mudbrick service walls and stone stela bases, without pyramids or New Kingdom royal tomb interiors"
)
NEGATIVE = (
    "no East Asian people or architecture, no medieval European armor, no Roman legionaries, no Tutankhamun "
    "mask, no pyramids, no fantasy treasure chamber, no occult magic, no alien glyphs, no basalt-black glass, "
    "no invented complete stela top, no modern equipment in historical scenes, no pseudo-writing, no generated "
    "readable inscription, no ancient costume on modern researchers, no plastic toy surface, no low-poly game asset, no exterior cube frame, no gore, "
    "no watermark, no text, no labels, no letters"
)

LOCK_BASE = {
    "civilization": "Ptolemaic Egypt and documented 1799-1822 decipherment history",
    "era": "196 BCE decree; 1799 discovery; 1802-1822 decipherment study",
    "region": "Memphis and the western Nile Delta near Rashid; Britain and France for later scholarship",
    "people_lock": "Ptolemaic Egyptian and Macedonian Greek court context in antiquity; documented European discoverers and scholars after 1799",
    "forbidden_culture": ["East Asian", "medieval European", "Roman legionary", "Tutankhamun", "fantasy", "alien"],
    "diorama_style": "CINEMATIC_ARCHAEOLOGICAL_DIORAMA",
    "material_fidelity": "PBR_MICROTEXTURE_HIGH_FIDELITY",
}
MODERN_LOCK_UPDATE = {
    "civilization": "Documented French discovery and European decipherment history",
    "era": "1799 Rashid fortification work or early nineteenth-century scholarship through 1822",
    "people_lock": "late-eighteenth-century French military engineers or early-nineteenth-century European scholars only",
}
COMPACT_ANCIENT_CONTEXT = "Ptolemaic Egypt, 196 BCE."
COMPACT_MODERN_CONTEXT = "Period-correct 1799-1822 Egypt and European scholarship."


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
        "occlusion": "the graphic passes behind the stone edge, document, column, wall or terrain and reappears with correct world-space parallax",
        "timing": "emerge only during the matching narration beat, travel through named anchors, settle, then fade before the end",
        "camera_relation": "anchored to named physical surfaces with correct perspective, depth, lighting, reflections, occlusion and camera parallax",
        "arrival_reaction": arrival,
    }


def spec(chapter: str, scene_type: str, evidence: str, image: str, source: str,
         fingerprints: list[str], action: str, beat_actions: list[str], camera_path: dict[str, object],
         *, people: bool = False, architecture: bool = False, modern: bool = False,
         veo: dict[str, object] | None = None, i2v_guard: str = "") -> dict[str, object]:
    return locals()


SPECS = [
    spec(
        "1. 잃어버린 목소리", "ARTIFACT_MACRO", "측정확인",
        "Hero front view of the real surviving Rosetta Stone fragment, a broad dark grey granodiorite slab 112.3 centimetres high and 75.7 centimetres wide, irregular jagged missing upper portion, thick mineral-grained edges, weathered flat face and three visibly different horizontal densities of shallow carved texture copied from the museum object reference but kept unreadable; freestanding within a dark archaeological gallery diorama, warm raking light, no glass case and no title card",
        "British Museum object EA24 official dimensions and object photography",
        ["dark grey granodiorite mineral grain", "irregular broken upper outline", "three surviving horizontal inscription-density zones"],
        "The camera starts moving immediately across the mineral edge, snaps to the carved face and widens to the whole broken slab while raking light travels from upper fracture to lower register.",
        ["Reveal the stone and its recovered voice immediately.", "Widen to identify the whole Rosetta Stone fragment."],
        cam("left mineral-grained broken edge", "rapid macro push across the shallow carved face", "complete surviving slab", "MACRO_PROBE_SETTLE", "MACRO_PROBE", "NONE", "full artifact hero frame", "0.25s focus snap from edge to face"),
    ),
    spec(
        "1. 잃어버린 목소리", "HISTORICAL_RECONSTRUCTION", "학술해석",
        "Immersive Ptolemaic Egyptian temple-wall diorama filled with dense authentic-looking carved relief registers and column shafts based on surviving Egyptian temple surfaces, all marks treated as unreadable physical carving rather than generated writing; a lone early scholar-scale silhouette at the threshold cannot interpret them, dust and shadow filling the corridor",
        "British Museum history of hieroglyphic decipherment and surviving temple inscriptions",
        ["sandstone relief registers", "deep columned temple corridor", "unreadable carved surfaces before decipherment"],
        "Begin already beside the carved wall, rush along its unreadable registers, change direction past one column and settle behind the powerless observer at the dark threshold.",
        ["Track the unreadable temple and tomb inscriptions.", "End on the historical inability to read them."],
        cam("raking-lit carved sandstone register", "along the wall then around the nearest column", "observer at the dark threshold", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "IMMERSIVE_POV_DOLLY", "ORBIT_REVEAL", "wall and observer held together", "2.8s direction change behind column"),
        architecture=True,
    ),
    spec(
        "1. 잃어버린 목소리", "ARTIFACT_MACRO", "미확인",
        "Extreme macro on the Rosetta Stone's real jagged upper fracture, chipped granodiorite crystals and incomplete carved lines disappearing into the missing portion; behind it, a deep miniature field of Egyptian temple relief fragments recedes softly out of focus, making one broken object appear impossibly small against a lost written civilization",
        "British Museum object photography and fragment status",
        ["jagged missing upper portion", "carved lines ending at the break", "granodiorite crystals visible in the fracture"],
        "Crash-push into the fracture, skim along one interrupted carved line, then pull back fast enough to reveal the deep field of unreadable reliefs without inventing the missing top.",
        ["Approach the broken fragment as the question.", "Reveal the much larger historical world it unlocked."],
        cam("fresh-looking crystal pocket in the ancient fracture", "along an interrupted carved groove then backward through relief depth", "small full fragment against the relief field", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "MACRO_PROBE", "ORBIT_REVEAL", "broken stone held as the unanswered key", "2.1s scale-change pullback"),
    ),
    spec(
        "2. 1799년 발견", "SITE_ESTABLISH", "문헌기록",
        "1799 western Nile Delta near Rashid: a historically restrained French military-engineering camp beside the later Fort Julien masonry, Nile-side flat terrain, sun-baked brick and reused stone walls, canvas work shelters, period surveying tools and French campaign uniforms, no pyramids and no modern excavation equipment; crafted archaeological reconstruction rather than exact discovery claim",
        "British Museum discovery account: French fortification work near Rashid in July 1799",
        ["western Nile Delta lowland near Rashid", "French 1799 engineering camp", "fort wall containing reused masonry"],
        "Begin low beside a survey stake, accelerate through the work area, bank toward the reused masonry wall and settle on the exact wall section about to be dismantled.",
        ["Enter the 1799 Rashid setting.", "Arrive at the fortification work area."],
        cam("wooden survey stake in Nile-delta soil", "through the engineering camp toward reused fort masonry", "wall section under repair", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "ORBIT_REVEAL", "reused wall stones ready for the next scene", "2.4s bank from camp to wall"),
        people=True, modern=True,
    ),
    spec(
        "2. 1799년 발견", "DISCOVERY_ACTION", "문헌기록",
        "Close low-angle reconstruction of late-eighteenth-century French military engineers removing one heavy dark granodiorite slab from a fort foundation wall near Rashid; gloved and bare hands grip period iron pry bars and rope, the slab's jagged edge and shallow carved texture just becoming visible between ordinary reused blocks, action paused immediately before the stone tips free",
        "British Museum discovery account; exact finder and motion remain incompletely recorded",
        ["granodiorite slab reused in fort masonry", "period iron pry bars and rope", "first exposure of the carved face"],
        "Two engineers complete one careful lever action; mortar dust falls, the slab pivots only a few centimetres on the real support edge, and the camera follows the pry bar to rack-focus on the first exposed carved texture.",
        ["Follow the fort work into the old wall.", "Reveal the stone fragment within the reused masonry."],
        cam("iron pry-bar tip under the dark slab", "along the lever and falling mortar to the opening seam", "first exposed carved face", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "NONE", "exposed stone texture at the wall seam", "impact recoil and rack focus at 2.6s"),
        people=True, modern=True,
        i2v_guard="Do not assert one named discoverer; show a restrained documented fort-work reconstruction only.",
    ),
    spec(
        "2. 물성과 치수", "ARTIFACT_MACRO", "측정확인",
        "Three-quarter artifact-scale view of the same surviving Rosetta Stone on a plain matte neutral conservation support, with its true 112.3-by-75.7-by-28.4-centimetre proportions readable through depth: broad carved front plane, thick right side, jagged missing top and granular dark grey granodiorite; completely empty, unoccupied background and floor with clean open space beside the two real outer edges for world-space dimension ticks, absolutely no papers, scrolls, statues, tools, miniatures, ruler or numerals",
        "British Museum object EA24 measurements and material identification",
        ["112.3 cm surviving height", "75.7 cm width and 28.4 cm thickness", "granodiorite rather than basalt"],
        "Orbit rapidly from the thick right edge to the front plane while one warm-grey dimension line grows between the surviving top and bottom edges, then a shorter line snaps between the side faces.",
        ["Measure the surviving height and width.", "Land on the granular material and thickness."],
        cam("thick right granodiorite edge", "short three-quarter orbit across the front plane", "lower-left surviving corner", "CONTROLLED_ORBIT_REVEAL", "MACRO_PROBE", "ORBIT_REVEAL", "front and side thickness in one frame", "2.5s direction change from side to face"),
        veo=graphic("DIMENSION_LINE", "British Museum published dimensions; exact numbers remain in narration and captions", "thin warm-grey 3D survey ticks and lines with a mineral-matte finish, no numerals", "highest surviving fracture point", ["left surviving edge", "bottom edge"], "right side thickness edge", "a small neutral reflection touches each real edge tick"),
    ),
    spec(
        "2. 물성과 치수", "ARTIFACT_MACRO", "발굴확인",
        "Macro-to-medium view of the Rosetta Stone face beginning at the irregular broken top where surviving carved rows are abruptly cut, with the middle and lower register textures already visible beneath in one continuous deep composition; genuine dark grey granodiorite pores, chips, worn grooves and compact residue, no reconstructed missing crown",
        "British Museum object photography and surviving line counts",
        ["upper carved lines cut by fracture", "three stacked surviving registers", "no invented complete upper section"],
        "Race down from the jagged fracture along the physical face, change focus at each real register boundary and settle at the dense lower carved field.",
        ["Show the missing upper portion.", "Follow the three surviving carved zones down the face."],
        cam("uppermost interrupted carved row", "straight downward over the two physical register boundaries", "dense lower register texture", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "MACRO_PROBE", "SURFACE_TO_INTERIOR", "three register zones readable at once", "2.3s focus step at first boundary"),
    ),
    spec(
        "3. 세 문자", "TEXT_RECORD", "발굴확인",
        "Front-facing Rosetta Stone surface divided only by its authentic physical layout into three horizontal inscription-density zones: sparse larger hieroglyphic forms in the surviving top band, flowing compact Demotic texture in the middle, and tightly ruled Greek-line texture below, all copied as shallow unreadable relief texture from the museum reference and never rendered as new legible writing; open side depth for parallax",
        "British Museum line counts: 14 hieroglyphic, 32 Demotic, 54 Greek",
        ["upper hieroglyphic band", "middle Demotic band", "lower Greek band"],
        "A restrained blue-white scan wave begins only after the camera moves, travels down the real stone face band by band, slips behind the protruding left edge during a shallow orbit and ends at the lower register.",
        ["Identify the upper and middle script zones.", "Continue to the lower Greek zone that could still be read."],
        cam("surviving upper hieroglyphic band", "down the stone face through middle and lower bands during a shallow orbit", "lower Greek register", "MACRO_PROBE_SETTLE", "MACRO_PROBE", "SURFACE_TO_INTERIOR", "whole face with three zones", "3.0s orbit exposes edge depth"),
        veo=graphic("SCAN_WAVE", "The three surviving script zones are physically verified; the scan does not translate or invent characters", "one thin restrained blue-white surface scan with 25 percent transparency", "upper surviving carved band", ["middle Demotic register"], "lower Greek register", "one shallow groove catches a brief cool reflection"),
    ),
    spec(
        "3. 세 문자", "DIAGRAM", "학술해석",
        "Oblique artifact diorama of the same Rosetta Stone with its three physical carved registers visible as stacked planes that remain attached to the slab; three restrained matching sample tiles hover only millimetres from their source zones with visible gaps, showing two languages carried by three scripts without producing any readable translation or invented symbols",
        "British Museum explanation: Egyptian in hieroglyphic and Demotic scripts plus Greek",
        ["three physical source registers", "two Egyptian-script zones distinguished from Greek", "same-decree comparison without generated translation"],
        "The camera strafes across the stacked registers while one scan pulse samples each zone in order; the three sample tiles separate slightly on real surface normals and stop with visible gaps.",
        ["Correct the common three-language misconception.", "Reveal that all three registers carry the same decree."],
        cam("upper register surface edge", "laterally across all three attached register planes", "aligned three-zone comparison", "CONTROLLED_ORBIT_REVEAL", "MACRO_PROBE", "ORBIT_REVEAL", "whole stone and three source zones", "2.7s lateral direction change"),
        veo=graphic("EXPLODED_SEQUENCE", "Conceptual comparison of the verified three script zones; no literal translation is generated", "original granodiorite-grey sample surfaces with thin warm-ivory separation rims", "upper register surface", ["middle register surface"], "lower register surface", "one soft focus snap joins all three zones in the same plane"),
    ),
    spec(
        "4. 평범한 포고문", "TEXT_RECORD", "문헌기록",
        "Ptolemaic temple-court diorama at the moment before a public decree is installed: an ordinary dark stone stela fragment and a plain full stela support stand in an open sandstone court while Egyptian priests and scribes prepare a formal proclamation, no sealed chamber, no treasure, no magical glow; the camera can move from dramatic shadow on the carving into the visibly public courtyard",
        "Memphis Decree content and instruction for temple display",
        ["public temple-court setting", "formal decree stela support", "absence of secret-treasure context"],
        "Start in dramatic macro shadow on the carved surface, crash-pull into the sunlit public court and settle on priests preparing an ordinary proclamation rather than a hidden secret.",
        ["Hold the expectation of a secret document.", "Reverse it into a public administrative decree."],
        cam("shadowed shallow carving on the stela", "fast pullback through the open court axis", "priests beside the public stela support", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "IMMERSIVE_POV_DOLLY", "ORBIT_REVEAL", "ordinary public decree scene", "1.8s exposure shift from shadow to daylight"),
        people=True, architecture=True,
    ),
    spec(
        "4. 평범한 포고문", "HISTORICAL_RECONSTRUCTION", "문헌기록",
        "Memphis priestly decree scene in 196 BCE: Ptolemaic Egyptian priests and scribes with North African Egyptian features in white linen occupy the foreground around a stone decree, while a restrained 13-year-old Ptolemy V appears at a respectful distance in Macedonian Greek royal court dress, youthful scale and posture clear but exact facial likeness unclaimed; no crown fantasy and no adult conqueror physique",
        "Memphis Decree of 196 BCE and Ptolemy V chronology",
        ["Memphis priest assembly", "thirteen-year-old Ptolemy V", "formal decree affirming royal and divine status"],
        "Follow a scribe's hand from the decree surface to the assembled priests, then change direction toward the distant young king and settle without turning the scene into a triumphal spectacle.",
        ["Show the priests issuing the 196 BCE decree.", "Reveal the young king being praised and affirmed."],
        cam("scribe hand beside the stone decree", "across the priest assembly then toward the royal dais", "youthful Ptolemy V at a distance", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "ORBIT_REVEAL", "decree, priests and young king in one depth axis", "3.6s direction change toward dais"),
        people=True, architecture=True,
    ),
    spec(
        "4. 평범한 포고문", "SPATIAL_MAP", "문헌기록",
        "Museum-scale Ptolemaic Egypt terrain-and-temple diorama beginning at Memphis with several physically separate verified-style temple stela silhouettes distributed along the Nile valley, each copy retaining the same three-register layout but no legible generated writing; the terrain is dry ochre and river green, no city labels and no pyramids",
        "Decree instruction to erect copies in major temples and survival of other copies",
        ["Memphis starting point", "multiple temple stela copies", "same three-register decree structure"],
        "A warm ivory route ribbon leaves the Memphis temple base, follows the Nile terrain behind one foreground pylon and branches only at visible temple anchors; the camera tracks the first branch then pulls up to reveal the repeated copies.",
        ["Follow the instruction to place the decree in temples.", "Reveal repetition as the comparison key."],
        cam("Memphis temple stela base", "north and south along the Nile terrain past temple anchors", "wide view of repeated stela copies", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "copies distributed across the terrain", "3.1s branch and crane rise"),
        architecture=True,
        veo=graphic("ROUTE_PATH", "The decree explicitly ordered temple copies; the path shows distribution, not a proven route of this surviving fragment", "warm ivory stone-dust route ribbon with small restrained directional pulses", "Memphis temple base", ["first Nile-side temple", "foreground sandstone pylon"], "other visible temple stela bases", "a small dust lift appears at each already-present stela base"),
    ),
    spec(
        "5. 해독은 즉시가 아니었다", "TEXT_RECORD", "학술해석",
        "Extreme archaeological-study macro of one authentic cartouche-shaped carved enclosure and adjacent hieroglyphic relief forms on a reference-accurate stone or rubbing surface, surrounded by plain comparison weights and unmarked study strips; the signs remain physical unreadable marks with no invented alphabet equivalents, while the composition makes clear that one picture cannot simply equal one meaning",
        "British Museum decipherment history: hieroglyphs combine phonetic and semantic functions",
        ["cartouche enclosure", "mixed hieroglyphic sign forms", "no one-picture-one-meaning key"],
        "Probe along the cartouche edge, change direction across several sign forms and let a restrained scan wave stop at different carved elements without translating them.",
        ["Show why the scripts were not read immediately.", "Reject the simple picture-equals-meaning model."],
        cam("carved cartouche boundary", "around the enclosure then across adjacent sign forms", "cluster of unlike carved signs", "MACRO_PROBE_SETTLE", "MACRO_PROBE", "SURFACE_TO_INTERIOR", "cartouche and mixed signs in one frame", "2.6s direction change across sign cluster"),
        veo=graphic("SCAN_WAVE", "The scan marks structural comparison only and never supplies an unverified translation", "thin low-glow amber survey pulse attached to the carved surface", "cartouche boundary", ["first carved sign", "second unlike sign"], "mixed sign cluster", "rack focus shifts from the enclosure to the final carved sign"),
    ),
    spec(
        "5. 해독은 즉시가 아니었다", "TEXT_RECORD", "문헌기록",
        "Early-nineteenth-century British study-room diorama with Thomas Young represented as a sober scholar at a wooden desk, comparing a high-quality Rosetta Stone copy, a cartouche rubbing and unmarked phonetic comparison slips; period coat, candle and daylight, brass instruments and paper fibres, no readable generated English or Greek text",
        "British Museum decipherment timeline: Thomas Young identified phonetic values in Ptolemy's royal name",
        ["Thomas Young study context", "Ptolemy cartouche rubbing", "phonetic comparison across the royal name"],
        "Track from Young's fingertip around the cartouche, snap across the arranged comparison slips and settle on the repeated royal-name shape as he records a partial sound clue.",
        ["Follow Thomas Young to the royal name.", "Reveal the partial phonetic clue rather than a complete decipherment."],
        cam("Young's fingertip at the cartouche edge", "around the rubbing then across comparison slips", "repeated royal-name enclosure", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "NONE", "partial comparison evidence on the desk", "3.0s snap from rubbing to slips"),
        people=True, modern=True,
    ),
    spec(
        "5. 해독은 즉시가 아니었다", "TEXT_RECORD", "문헌기록",
        "Early-1820s French study-room diorama with Jean-Francois Champollion represented in sober period clothing at a crowded wooden desk, comparing several royal-name cartouche reproductions, Coptic reference pages shown only as unreadable physical print texture and Egyptian inscription copies; layered paper fibres, ink, wax seals and daylight, no magical revelation and no modern tools",
        "British Museum decipherment timeline: Champollion used other royal names, Coptic and additional texts",
        ["multiple royal-name cartouches", "Coptic comparison material", "several Egyptian inscription copies rather than one stone alone"],
        "Begin on one cartouche, accelerate laterally through the other royal names, bank toward the Coptic reference pages and settle on Champollion linking sound and meaning across the whole desk.",
        ["Compare other royal names and Coptic evidence.", "Arrive at the mixed sound-and-meaning system."],
        cam("first royal-name cartouche", "across other cartouches then toward Coptic reference pages", "whole comparison desk before Champollion", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "ORBIT_REVEAL", "scholar and multi-source evidence", "2.2s focus snap across the royal names", "3.7s bank from cartouches to Coptic pages"),
        people=True, modern=True,
    ),
    spec(
        "6. 1822년 돌파구", "DIAGRAM", "문헌기록",
        "A physical early-nineteenth-century research-desk timeline diorama: the 1799 stone discovery sketch and wall fragment occupy the near-left end, successive unlabelled copies and comparison sheets form a long path across the desk, and an 1822 scholarly letter and assembled cartouche studies occupy the far-right end; no readable dates or writing generated in the image",
        "British Museum timeline from 1799 discovery to Champollion's September 1822 announcement",
        ["1799 discovery evidence at one end", "multi-stage comparison documents", "1822 announcement material at the other end"],
        "One restrained bronze-gold route path grows from the discovery sketch across the actual stack of study materials, passes behind a raised book and arrives at the 1822 letter while the camera races beside it then brakes.",
        ["Travel from discovery through more than twenty years of study.", "Arrive at the 1822 announcement."],
        cam("1799 discovery sketch edge", "along the full physical desk and document sequence", "1822 announcement letter and comparison sheets", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "IMMERSIVE_POV_DOLLY", "NONE", "end of the long evidence chain", "2.5s route passes behind raised book"),
        modern=True,
        veo=graphic("ROUTE_PATH", "Documented chronology from 1799 discovery to the 1822 decipherment announcement", "slender aged-bronze route ribbon with small moving pulses and no numbers", "1799 discovery sketch", ["Young comparison sheets", "raised reference book"], "1822 announcement letter", "one restrained warm reflection crosses the wax seal"),
    ),
    spec(
        "6. 1822년 돌파구", "INVENTORY_TABLEAU", "학술해석",
        "Circular research-room diorama that begins tight on one scholar's hands but already contains several separate period worktables in depth, each holding different Rosetta copies, royal-name cartouches, language references and correspondence; Thomas Young and Champollion occupy different documented study contexts rather than sharing one fictional meeting, linked only by copied materials",
        "British Museum history of cumulative work by Young, Champollion and earlier scholars",
        ["multiple separate scholar worktables", "different evidence types on each table", "no single instant lone-genius solution"],
        "Pull away fast from one pair of hands, orbit across the separate worktables and settle on the full network of copied evidence without merging the scholars into one meeting.",
        ["Reject the stone solving itself or one genius solving it instantly.", "Reveal the wider scholarly network."],
        cam("one scholar's hands over a rubbing", "backward through separate worktables in a short orbit", "wide network of study stations", "CONTROLLED_ORBIT_REVEAL", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "all evidence tables visible but separate", "2.2s scale-change pullback"),
        people=True, modern=True,
    ),
    spec(
        "6. 1822년 돌파구", "DIAGRAM", "학술해석",
        "Layered museum-scale evidence diorama with an ancient three-register decree fragment at the center, several physically separate temple-copy fragments around the lower ring and early-nineteenth-century comparison desks around the upper ring, every layer retaining its own era and material; no literal giant key object and no mixed-costume crowd",
        "Synthesis of repeated decree text, royal names, Coptic comparison and cumulative scholarly work",
        ["central three-register decree", "separate ancient copies", "separate modern comparison evidence"],
        "Three warm ivory route segments begin at the ancient copies and study desks only during their narration beats, pass behind the central stone and converge on its three real registers; the camera dives through the layered evidence and settles on the combined comparison.",
        ["Follow the repeated ancient sentence into the comparison process.", "Converge the evidence and time into the decipherment key."],
        cam("outer temple-copy fragment", "through the lower ancient ring and upper study ring", "three central Rosetta registers", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "IMMERSIVE_POV_DOLLY", "SURFACE_TO_INTERIOR", "all evidence converging without mixing eras", "3.4s bank from ancient ring to study ring"),
        veo=graphic("ROUTE_PATH", "Conceptual synthesis of documented evidence sources; paths indicate comparison, not physical historical travel", "three thin warm-ivory stone-dust route ribbons with restrained pulses", "outer temple-copy fragment", ["Young comparison desk", "Champollion comparison desk"], "central three-register stone face", "a soft focus snap brings all three registers into clarity"),
    ),
    spec(
        "7. 문명이 다시 읽히다", "TEXT_RECORD", "학술해석",
        "Deep archive-and-temple diorama containing three evidence planes: royal-name cartouches carved on stone in the foreground, temple relief records on sandstone columns in the middle, and papyrus household records on a conservation table in the rear; all physical inscriptions remain reference-textured and unreadable to the image model, but their objects and contexts are distinct",
        "Historical consequence of decipherment for royal, temple and everyday Egyptian texts",
        ["royal names on stone", "temple records on relief walls", "everyday papyrus documents"],
        "A restrained blue-white scan wave begins at a royal cartouche, turns around a column with full occlusion and travels to the papyrus table while the camera follows from stone to daily life.",
        ["Reopen royal names and temple records.", "Continue into everyday life on papyrus."],
        cam("royal cartouche on foreground stone", "past the temple column toward the rear papyrus table", "papyrus household records", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "IMMERSIVE_POV_DOLLY", "ORBIT_REVEAL", "all three evidence planes legible as objects", "2.9s turn around the column"),
        architecture=True,
        veo=graphic("SCAN_WAVE", "Conceptual reading access after decipherment; no generated translation or new text", "thin restrained blue-white measurement wave hugging existing surfaces", "royal cartouche surface", ["temple relief column"], "papyrus conservation table", "one soft focus transition lands on the papyrus fibres"),
    ),
    spec(
        "7. 진짜 비밀", "DIAGRAM", "학술해석",
        "The same Rosetta Stone in three-quarter view with its three physical registers and thick mineral edge visible; a restrained comparison arrangement places three shallow reference rubbings beside their exact source zones, emphasizing method rather than secret content, with no treasure imagery and no generated readable translation",
        "Rosetta Stone as a comparative key rather than a secret-message document",
        ["same real stone identity", "three-register comparison method", "no secret treasure content"],
        "Orbit from the face to the three aligned rubbings as one scan wave samples corresponding physical lines, then pull back to show that the method—not the decree's subject—is the discovery.",
        ["Reverse the idea of a secret written on the stone.", "Reveal the comparison method as the real secret."],
        cam("lower Greek register edge", "around the thick stone side toward three aligned rubbings", "whole comparison method tableau", "CONTROLLED_ORBIT_REVEAL", "MACRO_PROBE", "ORBIT_REVEAL", "stone and comparison surfaces in one frame", "2.4s orbit exposes the comparison gap"),
        veo=graphic("SCAN_WAVE", "Conceptual comparison across the verified three registers; no translation is generated", "one thin warm-ivory surface scan with muted blue edge", "lower Greek register", ["middle Demotic register"], "upper hieroglyphic register", "all three reference surfaces enter one shared focus plane"),
    ),
    spec(
        "8. 남은 미스터리", "SEALED_UNKNOWN", "미확인",
        "Oblique Nile Delta archaeological terrain diorama with a documented Rashid fort-wall fragment location at one end and several deliberately incomplete, unlabelled Ptolemaic temple-foundation possibilities fading into opaque negative space at the other; between them lies an intact blank terrain gap with no invented route, no treasure and no asserted original temple",
        "Unknown original temple and unknown reuse route into the fort wall",
        ["Rashid fort reuse endpoint", "unidentified temple-origin possibilities", "opaque untraced terrain gap"],
        "Approach quickly from the fort-wall stone toward the blank terrain gap, let the camera change height to search the incomplete temple foundations and stop completely at the opaque missing route.",
        ["Ask which temple originally held the stela.", "Stop where the route into the fort wall disappears."],
        cam("dark reused slab in the Rashid fort wall", "out over the blank Delta terrain toward incomplete foundations", "opaque untraced gap", "BOUNDARY_APPROACH_STOP", "LOCKED_EVIDENCE_CAMERA", "BOUNDARY_STOP", "empty evidence boundary", "2.8s height change to inspect foundations"),
    ),
    spec(
        "8. 남은 미스터리", "SEALED_UNKNOWN", "미확인",
        "Quiet paradox diorama: the surviving Rosetta Stone stands sharply lit in the foreground, while behind it an empty weathered Ptolemaic stela base and incomplete temple foundation recede into darkness, separated by a broad untouched gap; the artifact is fully present but its first physical place remains absent, no speculative complete temple",
        "Decipherment succeeded while the artifact's original archaeological context remains lost",
        ["surviving stone in foreground", "empty stela base", "unresolved spatial gap between them"],
        "Pull back from the recovered carved face toward the empty stela base, pass behind the stone edge for natural occlusion and stop before the dark gap that cannot be crossed.",
        ["Hold the recovered voice of the civilization.", "Reveal the lost first place of the key itself."],
        cam("shallow carving on the recovered stone", "backward around the thick edge toward the empty base", "dark gap before the incomplete foundation", "BOUNDARY_APPROACH_STOP", "LOCKED_EVIDENCE_CAMERA", "BOUNDARY_STOP", "stone and absent origin held together", "2.1s occlusion behind stone edge"),
        architecture=True,
    ),
    spec(
        "9. 고정 결말", "SITE_ESTABLISH", "학술해석",
        "Wide closing archaeological diorama linking only verified stages without blending them: a Ptolemaic temple-stela foundation occupies one distant plane, the 1799 Rashid fort masonry occupies the middle plane, and the surviving Rosetta Stone occupies the near plane under restrained museum light; the unknown transitions remain dark physical gaps, warm dawn-to-gallery palette",
        "Verified production, reuse discovery and surviving artifact stages with unknown links preserved",
        ["Ptolemaic origin-era plane", "1799 fort-discovery plane", "surviving artifact foreground"],
        "Begin close on the stone, pull back rapidly through the fort plane and rise to reveal the older temple plane, preserving dark gaps between stages rather than drawing a false route.",
        ["Expand from the artifact into time and buried history.", "Hold the verified stages and their missing links together."],
        cam("Rosetta Stone lower carved edge", "backward through the fort masonry plane then upward", "wide three-stage archaeological landscape", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "wide quiet closing world", "2.5s scale-change rise"),
        architecture=True,
    ),
    spec(
        "9. 고정 결말", "ARTIFACT_MACRO", "발굴확인",
        "Final dignified hero portrait of the real surviving Rosetta Stone fragment, unmistakable dark grey granodiorite mineral grain, irregular jagged top, broad lower body and three physical inscription-density zones, isolated in a deep black-brown archaeological gallery diorama with a single warm raking beam and faint dust, no title or logo",
        "British Museum object EA24 official object identity",
        ["dark grey granodiorite", "jagged incomplete top", "three surviving carved register zones"],
        "A short controlled half-orbit starts immediately, raking light travels across the face, and the camera settles into complete stillness on the whole stone for the final channel line.",
        ["Name the Rosetta Stone one last time.", "Finish in stillness on the artifact itself."],
        cam("lower-left granodiorite edge", "short half-orbit across the carved face", "complete Rosetta Stone silhouette", "EVIDENCE_HOLD", "LOCKED_EVIDENCE_CAMERA", "NONE", "full artifact closing portrait", "light sweep changes the visible material at 1.2s"),
        i2v_guard="Treat the start-frame artifact as an immutable photographed object: do not redraw, translate, simplify, enlarge, sharpen, replace or animate any carved mark; do not alter the jagged fracture, silhouette, thickness, cracks, chips or base. Camera-only motion: at most a three-degree parallax arc created by background movement, followed by a full still hold. If fidelity conflicts with motion, keep the artifact perfectly frozen and move only the raking light and background parallax.",
    ),
]


def choose_duration(tts: float) -> int:
    for value in (4, 6, 8, 10):
        if tts <= value:
            return value
    raise ValueError(f"10초를 넘는 TTS 장면: {tts:.3f}")


def cue_groups(scene_cues: list[dict[str, object]], count: int) -> list[list[dict[str, object]]]:
    if count <= 1:
        return [scene_cues]
    if len(scene_cues) < count:
        raise ValueError(f"TTS 자막 큐 {len(scene_cues)}개를 {count}비트로 나눌 수 없습니다")
    groups: list[list[dict[str, object]]] = []
    remaining = list(scene_cues)
    for group_index in range(count - 1):
        groups_left = count - group_index
        target_chars = sum(int(cue["len"]) for cue in remaining) / groups_left
        taken: list[dict[str, object]] = []
        running = 0
        while len(remaining) > groups_left - 1:
            candidate = remaining[0]
            if taken and abs(running - target_chars) <= abs(running + int(candidate["len"]) - target_chars):
                break
            taken.append(remaining.pop(0))
            running += int(candidate["len"])
        groups.append(taken)
    groups.append(remaining)
    return groups


def make_beats(scene_number: int, duration: float, actions: list[str],
               sync_cues: list[dict[str, object]], scene_start: float) -> list[dict[str, object]]:
    scene_cues = [cue for cue in sync_cues if int(cue["scene"]) == scene_number]
    groups = cue_groups(scene_cues, len(actions))
    beats: list[dict[str, object]] = []
    for index, (group, action) in enumerate(zip(groups, actions)):
        start = 0.0 if index == 0 else round((float(groups[index - 1][-1]["end"]) + float(group[0]["start"])) / 2 - scene_start, 3)
        end = duration if index == len(groups) - 1 else round((float(group[-1]["end"]) + float(groups[index + 1][0]["start"])) / 2 - scene_start, 3)
        narration = " ".join(str(cue.get("raw") or cue["text"]) for cue in group)
        beats.append({
            "start": max(0.0, start),
            "end": min(duration, end),
            "narration": narration,
            "camera": action.split(";", 1)[0],
            "action": action,
            "graphic": "scene-integrated evidence motion only; exact Korean words and numbers remain in final captions",
        })
    return beats


def image_prompt(item: dict[str, object]) -> str:
    anchors = [STYLE, MODERN_CIV if item["modern"] else ANCIENT_CIV]
    if item["people"]:
        anchors.append(MODERN_PEOPLE if item["modern"] else ANCIENT_PEOPLE)
    if item["architecture"]:
        anchors.append(ANCIENT_ARCH)
    anchors.append(str(item["image"]))
    depth = str(item["camera_path"]["depth_transition"])
    if depth in {"SECTION_DIVE", "SURFACE_TO_INTERIOR"}:
        anchors.append("the start frame already contains a physically visible section seam, depth layers and an empty camera route; no geometry may be invented later")
    anchors.append(NEGATIVE)
    return ". ".join(anchor.rstrip(". ") for anchor in anchors) + "."


def video_prompt(item: dict[str, object], beats: list[dict[str, object]], seconds: int) -> str:
    path = item["camera_path"]
    source_end = float(beats[-1]["end"]) if beats else float(seconds)
    scale = min(1.0, float(seconds) / source_end) if source_end > 0 else 1.0
    schedule = " ".join(
        f"{float(beat['start']) * scale:.2f}-{float(beat['end']) * scale:.2f}s: {beat['action']}"
        for beat in beats
    )
    prompt = (
        f"Use the supplied locked start image and preserve every object, identity, artifact fingerprint, provenance, "
        f"site geometry, material, culture, lighting and composition. Single continuous {seconds}-second I2V shot, "
        f"no hard cut, no teleport, no morph, no new objects. Begin physical camera travel within 0.35 seconds. "
        f"Enter at {path['entry_anchor']}; travel {path['route']}; arrive at {path['destination']}; settle on {path['settle_point']}. "
    )
    if item["i2v_guard"]:
        prompt += str(item["i2v_guard"]) + " "
    if item["veo"] is not None:
        function = str(item["veo"]["function"])
        graphic_name = "physical route path ribbon" if function == "ROUTE_PATH" else function.lower().replace("_", " ")
        prompt += (
            f"Integrate one restrained {graphic_name} anchored in the physical world space. It shares perspective, "
            f"depth, lighting and reflections, receives camera parallax and natural occlusion, and never attaches to "
            f"the screen. No floating HUD, no screen-space graphics, no text, no numbers, no labels. "
        )
    prompt += str(item["action"]) + " TTS-locked timing: " + schedule
    prompt += " Preserve all objects from the start image. No voice, no music, no subtitles."
    return prompt


def compact_image_prompt(item: dict[str, object]) -> str:
    # Flow의 contenteditable 프롬프트 창은 자동 붙여넣기를 내부 생성 값으로
    # 반영하지 않는 경우가 있어 실제 키 입력으로 전송한다. 따라서 장면 고증
    # 문장은 보존하고, 모든 장면에 중복되던 스타일/금지어만 짧게 고정한다.
    context = COMPACT_MODERN_CONTEXT if item["modern"] else COMPACT_ANCIENT_CONTEXT
    return (
        "9:16 archaeological 3D diorama miniature, macro PBR microtexture, not live-action. "
        + context + " " + str(item["image"])
        + " No text. No labels. No letters. No fantasy, wrong culture, watermark or exterior cube frame."
    )


def compact_video_prompt(item: dict[str, object], beats: list[dict[str, object]], seconds: int) -> str:
    path = item["camera_path"]
    source_end = float(beats[-1]["end"]) if beats else float(seconds)
    scale = min(1.0, float(seconds) / source_end) if source_end > 0 else 1.0
    schedule = " ".join(
        f"{float(beat['start']) * scale:.2f}-{float(beat['end']) * scale:.2f}s: {beat['action']}"
        for beat in beats
    )
    parts = [
        f"Preserve the locked start image exactly: every object, artifact identity, geometry, material, era and lighting. One continuous {seconds}s I2V shot; no hard cut, teleport, morph or new object. Start camera by 0.35s.",
        f"Start at {path['entry_anchor']}; move {path['route']}; end at {path['destination']}; settle on {path['settle_point']}.",
        str(item["action"]),
    ]
    if item["i2v_guard"]:
        parts.append(str(item["i2v_guard"]))
    if item["veo"] is not None:
        veo = item["veo"]
        parts.append(
            f"Use one restrained {str(veo['function']).lower().replace('_', ' ')} in physical world space: "
            f"{veo['visual_language']}; start at {veo['start']}, pass {', '.join(veo['via'])}, end at {veo['end']}. "
            "Give it real perspective, parallax, surface contact, lighting and natural occlusion; no floating HUD, screen graphic, text, number or label."
        )
    parts.extend((f"TTS-locked timing: {schedule}", "No voice, music or subtitles."))
    return " ".join(parts)


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
    for token in (str(path["entry_anchor"]), str(path["destination"])):
        if token.lower() not in video_low:
            errors.append(f"video missing anchor {token}")
    if row.get("veo_graphic") and ("physical world space" not in video_low or "no floating hud" not in video_low):
        errors.append("video missing world-space graphic lock")
    if len(video) > 1700:
        errors.append(f"video too long {len(video)}")
    return errors


def build() -> None:
    duration_data = json.loads((EPISODE / "audio" / "durations.json").read_text(encoding="utf-8"))
    sources = duration_data["scenes"]
    sync_cues = json.loads((EPISODE / "자막_싱크.json").read_text(encoding="utf-8"))["cues"]
    if len(sources) != len(SPECS):
        raise ValueError(f"승인 TTS {len(sources)}장면과 시각 명세 {len(SPECS)}장면이 다릅니다")

    starts: dict[int, float] = {}
    elapsed = 0.0
    for key in sorted(sources, key=int):
        starts[int(key)] = elapsed
        elapsed += float(sources[key]["duration"])

    rows: list[dict[str, object]] = []
    for n, item in enumerate(SPECS, 1):
        source = sources[str(n)]
        narration = str(source["text"])
        tts = float(source["duration"])
        seconds = choose_duration(tts)
        beats = make_beats(n, tts, item["beat_actions"], sync_cues, starts[n])
        lock = dict(LOCK_BASE)
        if item["modern"]:
            lock.update(MODERN_LOCK_UPDATE)
        lock.update({"source_reference": item["source"], "site_artifact_fingerprint": item["fingerprints"]})
        row: dict[str, object] = {
            "n": n,
            "chapter": item["chapter"],
            "ct": item["scene_type"],
            "txt": narration,
            "tts": tts,
            "omni": seconds,
            "playback_speed": round(seconds / tts, 4) if tts > seconds else 1.0,
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
        if tts > 9.0:
            row["long_scene_review"] = (
                "The narration is one indivisible claim-and-evidence unit in one physical location; "
                "two timed camera interruptions preserve pace without a semantic or spatial reset."
            )
        row["vid"] = video_prompt(item, beats, seconds)
        if item["veo"] is not None:
            row["veo_graphic"] = item["veo"]
        rows.append(row)

    (EPISODE / "02a.장면구분.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    table = [
        f"# {EPISODE_LABEL} — 장면 구분표", "",
        f"> {len(rows)}장면은 {SCENE_COUNT_NOTE}", "",
        "| 장면 | 장 | TTS | 생성 | 유형 | 증거 | 모션 | 핵심 화면 |",
        "|---:|---|---:|---:|---|---|---|---|",
    ]
    visual = [
        f"# {EPISODE_LABEL} — 고증 잠금 I2V 시각화", "", f"scene_count: {len(rows)}",
        "scene_count_basis: SCRIPT_TTS_MEANING_ACTION_EVIDENCE_DERIVED", "generation_mode: I2V_LOCKED",
        "image_model: Nano Banana", "video_model: Veo/Flow Omni", "aspect_ratio: 9:16",
        "image_count_per_scene: 1", "video_count_per_scene: 1", "",
    ]
    images: list[str] = []
    videos: list[str] = []
    ui_images: list[str] = []
    ui_videos: list[str] = []
    ui_check: list[dict[str, object]] = []
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
        images.append(str(row["img_v2"]))
        videos.append(str(row["vid"]))
        compact_image = compact_image_prompt(item)
        compact_video = compact_video_prompt(item, row["tts_beats"], int(row["omni"]))
        compact_errors = validate_compact(row, compact_image, compact_video)
        ui_images.append(compact_image)
        ui_videos.append(compact_video)
        ui_check.append({
            "n": row["n"], "image_chars": len(compact_image), "video_chars": len(compact_video),
            "status": "PASS" if not compact_errors else "FAIL", "errors": compact_errors,
        })

    (EPISODE / "02a.장면구분표.md").write_text("\n".join(table) + "\n", encoding="utf-8")
    (EPISODE / "02.시각화.txt").write_text("\n".join(visual), encoding="utf-8")
    (EPISODE / "flow_images.txt").write_text("\n\n".join(images) + "\n", encoding="utf-8")
    (EPISODE / "flow_videos.txt").write_text("\n\n".join(videos) + "\n", encoding="utf-8")
    (EPISODE / "flow_images_ui.txt").write_text("\n\n".join(ui_images) + "\n", encoding="utf-8")
    (EPISODE / "flow_videos_ui.txt").write_text("\n\n".join(ui_videos) + "\n", encoding="utf-8")
    (EPISODE / "flow_ui_prompt_check.json").write_text(json.dumps(ui_check, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    failures = [item for item in ui_check if item["status"] != "PASS"]
    if failures:
        raise ValueError(f"Flow UI 프롬프트 자가검수 실패: {failures}")
    print(f"{EPISODE_LABEL} 시각화 빌드 완료: {len(rows)}장면 / {elapsed:.3f}초")


if __name__ == "__main__":
    build()
