#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""EP08 백제 금동대향로 — 21개 승인 TTS를 23개 8초 I2V 화면으로 설계한다."""

from __future__ import annotations

import json

import build_ep05_storyboard as base


base.EPISODE = base.ROOT / "산출물" / "EP08_백제금동대향로"
base.EPISODE_LABEL = "EP08 백제 금동대향로"
base.SCENE_COUNT_NOTE = (
    "179.77초 승인 음성을 8초 I2V로 덮기 위해, 21개 TTS 장면 중 결말의 두 장면을 "
    "문장 경계에서 각각 2개 화면으로 나눈 결과다. 고정 컷 수가 아니다."
)
base.STYLE = (
    "premium full-frame cinematic archaeological 3D diorama, unmistakably a museum-scale crafted miniature world and not live-action, "
    "realistic historical architectural CG restoration, immersive macro-lens depth, restrained tilt-shift, layered foreground-midground-background, "
    "physically based PBR bronze, gilding, wet clay, timber and roof-tile microtexture, razor-sharp artifact separation, global illumination, "
    "high fidelity 4K source detail, 9:16 vertical composition"
)
base.ANCIENT_CIV = (
    "Baekje Sabi-period Korea in the sixth to seventh century CE, the Neungsan-ri royal temple workshop and royal tomb landscape at Buyeo"
)
base.MODERN_CIV = (
    "documented South Korean archaeological excavation and conservation: the 1993 Neungsan-ri temple-site excavation at Buyeo, "
    "with restrained modern museum conservation only when required"
)
base.ANCIENT_PEOPLE = (
    "Korean Baekje people with East Asian features, period-correct Sabi-era hemp or silk garments, narrow belts, restrained hair knots and no later Joseon clothing"
)
base.MODERN_PEOPLE = (
    "South Korean archaeologists in practical 1993 field clothing or modern conservators in neutral laboratory wear, with no ancient costume"
)
base.ANCIENT_ARCH = (
    "Baekje timber temple buildings on stone foundations, dark tiled roofs, wooden workshop frames, hearth, rectangular water-and-mud sump, "
    "and low royal tomb mounds in the Buyeo landscape; no Chinese imperial palace"
)
base.NEGATIVE = (
    "no European people, no Chinese Han or Qing palace, no Japanese shrine, no Joseon hanbok, no medieval armor, no fantasy treasure room, "
    "no giant literal dragon or phoenix, no magical levitation, no polished new gold statue, no invented complete inscription, no readable generated Korean or Chinese, "
    "no pseudo-writing, no floating HUD, no modern object in ancient scenes, no plastic toy surface, no low-poly game asset, no exterior cube frame, "
    "no ancient costume on modern researchers, no gore, no watermark, no text, no labels, no letters"
)
base.LOCK_BASE = {
    "civilization": "Baekje Sabi-period royal-temple culture and Neungsan-ri workshop archaeology",
    "era": "sixth to seventh century CE, with the 660 CE collapse used only where the narration states it",
    "region": "Neungsan-ri, Buyeo, Republic of Korea",
    "people_lock": "Korean Baekje people in Sabi-period clothing; no other East Asian dynasty styling",
    "forbidden_culture": ["European", "Chinese imperial", "Japanese", "Joseon", "fantasy"],
    "artifact_lock": (
        "one real-form Baekje gilt-bronze incense burner: sculpted dragon base supporting a lotus bowl, layered lotus petals, "
        "perforated multi-peak mountain lid with tiny musicians and animals, one phoenix at the summit, aged dark bronze with restrained surviving gilding, 61.8-centimetre vertical proportion"
    ),
    "diorama_style": "CINEMATIC_ARCHAEOLOGICAL_DIORAMA",
    "material_fidelity": "PBR_MICROTEXTURE_HIGH_FIDELITY",
}
base.MODERN_LOCK_UPDATE = {
    "civilization": "Documented 1993 South Korean excavation and present-day conservation",
    "era": "1993 excavation or contemporary conservation only",
    "people_lock": "South Korean archaeologists or conservators in exact modern work clothing",
}
base.COMPACT_ANCIENT_CONTEXT = "Baekje Sabi period, 6th-7th century Korea, Neungsan-ri royal temple at Buyeo."
base.COMPACT_MODERN_CONTEXT = "Documented 1993 Korean excavation or restrained modern conservation at Neungsan-ri, Buyeo."

cam = base.cam
graphic = base.graphic
spec = base.spec


def visual(audio_scene: int, part: int, parts: int, *args, **kwargs) -> dict[str, object]:
    item = spec(*args, **kwargs)
    item.update({"audio_scene": audio_scene, "part": part, "parts": parts})
    return item


SPECS = [
    visual(1, 1, 1,
        "1. 진흙 속 금빛", "DISCOVERY_ACTION", "발굴확인",
        "Macro cutaway of a muddy rectangular workshop sump at a ruined Baekje temple in Buyeo; compact wet grey-brown clay and broken dark roof tiles surround one partly exposed gilt-bronze curved surface catching a narrow gold glint, the rest of the real-form incense burner still buried, dawn excavation light, no person",
        "1993 Neungsan-ri temple-site excavation record",
        ["wet compact mud", "broken Baekje roof tiles", "partly exposed aged gilt-bronze surface"],
        "Dive through the wet mud layers along the existing exposed seam and arrive on the first gold glint as clay grains slide naturally; one camera route, no reveal reset.",
        ["Enter the Buyeo temple-site mud.", "Reach the 1,400-year-old gold glint."],
        cam("wet clay pore at the sump edge", "down the visible mud-and-tile seam", "exposed gilt-bronze curve", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "MACRO_PROBE", "SECTION_DIVE", "gold glint inside the real pit", "2.0s clay grain slide", "5.4s focus snap to gilding"),
        architecture=True, modern=True),
    visual(2, 1, 1,
        "1. 국보와 장소 반전", "ARTIFACT_REVEAL", "측정확인",
        "Hero three-quarter portrait of the complete real-form Baekje gilt-bronze incense burner standing on a dark conservation plinth: dragon base, lotus bowl, perforated mountain lid, tiny figures and one phoenix all visible; behind it, softly focused, the humble muddy workshop sump and broken roof tiles contradict the masterpiece, restrained surviving gold over aged bronze",
        "National Museum of Korea and Buyeo National Museum object form",
        ["dragon-lotus-mountain-phoenix vertical silhouette", "aged bronze with thin restrained gilding", "humble muddy workshop pit in depth"],
        "Race upward from the dragon base to the phoenix, half-orbit the whole artifact, then pull focus to the modest workshop pit behind it and stop on the contradiction.",
        ["Reveal the national treasure.", "Turn from palace expectation to the workshop pit."],
        cam("dragon claw at the base", "fast vertical rise then short half-orbit", "workshop sump behind the artifact", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "artifact and humble pit in one depth axis", "2.2s lotus near-miss", "5.7s focus pull to pit")),
    visual(3, 1, 1,
        "1. 주차장 전 조사", "SITE_ESTABLISH", "발굴확인",
        "1993 Korean archaeological excavation diorama before parking-lot construction: measured Neungsan-ri temple workshop grid, stone foundations, broken Baekje roof tiles and a rectangular muddy sump; South Korean archaeologists kneel with hand tools, no bulldozer impact",
        "Buyeo National Museum excavation history",
        ["1993 archaeological grid", "Baekje workshop foundation", "rectangular muddy sump before parking construction"],
        "Fly low across the survey grid, follow one archaeologist's trowel toward the sump and descend through the existing open pit to end where the treasure lay.",
        ["Correct the parking-lot discovery context.", "Ask why the treasure was in the workshop sump."],
        cam("survey string at the temple foundation", "across the grid behind the trowel into the open sump", "artifact find position", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "SECTION_DIVE", "measured pit find spot", "2.4s trowel follow", "5.4s pit descent"),
        people=True, architecture=True, modern=True),
    visual(4, 1, 1,
        "2. 용에서 연꽃", "ARTIFACT_MACRO", "측정확인",
        "Extreme lower-body macro of the real-form Baekje incense burner against a dark museum-diorama background: one muscular sculpted dragon rises from stylized water and supports the round lotus bowl; layered lotus petals retain dark green-brown bronze and thin warm gilding, every casting pore razor sharp",
        "Published object morphology: dragon base and lotus body",
        ["single supporting dragon", "water-like base curls", "layered lotus petals above"],
        "Begin at the dragon's water curls, surge around its upturned neck and climb directly into the lotus petals while raking light exposes the casting texture.",
        ["Show the dragon rising from water.", "Continue upward into the lotus."],
        cam("water curl beside dragon claw", "around the dragon neck and upward", "lowest lotus-petal rim", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "MACRO_PROBE", "SURFACE_TO_INTERIOR", "dragon physically supporting lotus bowl", "2.0s turn around neck", "5.0s light sweep over petals")),
    visual(5, 1, 1,
        "2. 산악 세계와 61.8센티미터", "ARTIFACT_MACRO", "측정확인",
        "Full vertical hero of the real-form 61.8-centimetre Baekje gilt-bronze incense burner: lotus bowl below, densely layered perforated mountain peaks with five tiny period musicians and plausible real and mythical animals, one phoenix fixed at the summit; dark background, high local contrast, thin physical survey line beside the artifact without numerals",
        "Published 61.8 cm height and iconographic inventory",
        ["five musicians on mountain lid", "real and mythical animals among peaks", "single summit phoenix and 61.8 cm proportion"],
        "Spiral upward through the existing mountain paths, pass all five musicians, snap around the summit phoenix and crane back to hold the complete vertical proportion.",
        ["Reveal musicians and animals across the peaks.", "Reach the phoenix and establish the full height."],
        cam("lowest mountain perforation", "up one continuous spiral mountain path", "phoenix crown and full artifact silhouette", "CONTROLLED_ORBIT_REVEAL", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "whole 61.8-centimetre vertical world", "2.2s musician focus snap", "5.3s summit orbit"),
        veo=graphic("DIMENSION_LINE", "Published total height; exact number remains in narration and captions", "thin aged-gold physical survey line with small ticks and no numerals", "dragon-base bottom", ["lotus rim", "mountain-lid shoulder"], "phoenix crown", "a restrained warm reflection reaches the two real endpoints")),
    visual(6, 1, 1,
        "2. 살아 움직이는 청동산", "FUNCTION_RECONSTRUCTION", "학술해석",
        "Ancient Baekje royal-temple interior diorama with the same locked incense burner on a low ritual stand; a small real ember bed inside the lotus body sends restrained pale incense smoke through the already visible perforations between mountain peaks, musicians and phoenix remain cast metal and motionless, no magic",
        "Functional interpretation of perforated mountain lid",
        ["real ember bowl inside lotus body", "smoke exiting existing mountain perforations", "locked artifact geometry remains solid"],
        "Enter with the smoke through one existing perforation, weave rapidly between fixed bronze peaks, emerge beside the phoenix and pull back as the whole bronze mountain breathes through smoke only.",
        ["Ignite the incense function.", "Make the fixed bronze mountain feel alive through airflow."],
        cam("ember glow inside lotus bowl", "through real lid holes between fixed peaks", "smoke plume beside phoenix", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "IMMERSIVE_POV_DOLLY", "SURFACE_TO_INTERIOR", "whole artifact with moving smoke", "2.0s enter perforation", "5.2s emerge at summit"),
        architecture=True),
    visual(7, 1, 1,
        "3. 1993년 발견 순간", "DISCOVERY_ACTION", "발굴확인",
        "Close 1993 excavation diorama: gloved South Korean archaeologist hands use a bamboo pick and soft brush to remove wet clay beside broken roof tiles; a narrow strip of genuine aged gilt-bronze flashes beneath the mud, measured grid and film-era field equipment remain blurred in depth, no shovel impact",
        "1993-12-12 excavation documentation",
        ["hand excavation tools", "wet clay and broken roof tiles", "first gilt-bronze flash"],
        "Follow the brush bristles across wet clay, make a quick handheld push as the gold catches light, then settle inches above the exposed bronze without uncovering a new object.",
        ["Start the documented excavation.", "Hit the first gold flash between roof tiles."],
        cam("brush bristle in wet mud", "along the tile edge toward the exposed metal", "gilt-bronze flash", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "SURFACE_TO_INTERIOR", "first exposed metal", "2.4s mud rolls from brush", "5.2s exposure snap on gold"),
        people=True, architecture=True, modern=True),
    visual(8, 1, 1,
        "3. 분리 출토와 진흙 보존", "CUTAWAY", "발굴확인",
        "Forensic cutaway of the documented workshop sump: the incense-burner body and mountain lid lie separated but adjacent in compact mud among broken tiles and roughly 450 varied workshop fragments represented as a dense mixed layer; wet clay seals every void from surface air, artifact forms remain accurate and not assembled in the pit",
        "Excavation context and associated workshop finds",
        ["separated burner body and lid", "dense associated workshop-object layer", "continuous oxygen-blocking wet mud seal"],
        "Dive through the exposed sump wall, pass the separated body then lid, sweep across the associated fragments and follow the mud seal upward until the air route physically stops.",
        ["Map the separated body, lid and workshop objects.", "Show wet mud blocking outside air."],
        cam("open sump-wall soil profile", "through body, lid and associated layer", "sealed mud-to-air boundary", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "IMMERSIVE_POV_DOLLY", "SECTION_DIVE", "whole sealed find context", "2.2s body-to-lid turn", "5.5s stop at air boundary"),
        architecture=True, modern=True,
        veo=graphic("MATERIAL_FLOW", "Conceptual oxygen exclusion by compact wet mud, not a chemical certainty animation", "thin desaturated blue-grey air particles that halt at real saturated clay pores", "surface air", ["upper dry soil", "wet-clay boundary"], "sealed artifact layer", "the particles stop and fade before touching the bronze")),
    visual(9, 1, 1,
        "3. 도금은 남고 질문은 남다", "SCIENTIFIC_EVIDENCE", "측정확인",
        "Conservation macro of the same burner surface: dark aged bronze pores beneath an exceptionally thin, even surviving gold layer, with a muddy cross-section still visible behind; one separated lid silhouette remains deep in the pit background to retain the unresolved placement question, neutral lab light with warm gold edge",
        "Conservation observation of thin even gilding and mud preservation",
        ["thin even surviving gilding", "aged bronze casting pores", "separated find context retained in background"],
        "Probe across the gold-bronze boundary, rack focus to the separated pit silhouette and pull backward along the unanswered route into the dark sump.",
        ["Confirm the preserved thin gilding.", "Return to why the burner entered the pit."],
        cam("gold edge over bronze pore", "across the material boundary then backward into pit depth", "separated lid silhouette", "MACRO_PROBE_SETTLE", "MACRO_PROBE", "ORBIT_REVEAL", "gilding foreground and pit question background", "2.1s material focus snap", "5.1s focus pull into pit"),
        modern=True),
    visual(10, 1, 1,
        "4. 660년 은닉설과 기록 부재", "EVIDENCE_TIMELINE", "측정확인",
        "Continuous archaeological-section diorama of the Baekje workshop: a real burnt-earth layer and collapsed roof tiles align above the muddy sump; far behind, a restrained 660-era Sabi fire glow is visible beyond timber walls, while an empty dark archive niche makes the missing eyewitness record physically clear; no person shown hiding the burner",
        "Burnt-soil dating around 660 and absence of direct concealment record",
        ["burnt workshop soil layer", "collapsed Baekje roof tiles", "empty record niche and no hiding reenactment"],
        "Race along the burnt layer toward the distant collapse glow, reverse down through the sump and follow a physical evidence path that stops sharply at the empty archive niche.",
        ["Build the 660 emergency-concealment hypothesis.", "Break the route at the missing direct record."],
        cam("charred soil grain", "along the burn layer then down to the empty archive niche", "unfilled record gap", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "SECTION_DIVE", "dated layer connected only to an evidence gap", "2.5s direction change at roof fall", "6.0s evidence stop"),
        architecture=True,
        veo=graphic("ROUTE_PATH", "The route connects verified burnt layer and find context but stops before an unverified hiding act", "thin ember-brown physical evidence ribbon hugging soil and tile surfaces", "burnt layer", ["collapsed tile", "sump rim"], "empty archive niche", "the ribbon fractures and extinguishes at the missing-record edge")),
    visual(11, 1, 1,
        "4. 왕릉 곁 왕실 사찰", "SPATIAL_MAP", "발굴확인",
        "Large terrain-and-temple diorama of Neungsan-ri: a Baekje royal temple workshop in the foreground, low royal tomb mounds roughly 100 metres away across one continuous landscape, and a small stone sarira reliquary with authentic but completely unreadable carved surface secured inside the temple context; no modern labels or map numerals",
        "Royal-tomb proximity and 567 royal-princess sarira inscription context",
        ["temple and workshop footprint", "nearby royal tomb mounds", "stone sarira reliquary as royal patronage evidence"],
        "Launch from the sump, skim across the temple foundation to the reliquary, then follow the terrain toward the tomb mounds and crane back to show all three contexts in one axis.",
        ["Connect the temple to the nearby royal tombs and 567 reliquary.", "Narrow the burner to royal-temple ritual use."],
        cam("workshop sump rim", "through temple foundation and reliquary toward tomb mounds", "full royal-temple landscape", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "IMMERSIVE_POV_DOLLY", "ORBIT_REVEAL", "temple, reliquary and tombs together", "2.6s reliquary orbit", "6.4s crane to full terrain"),
        architecture=True,
        veo=graphic("ROUTE_PATH", "Published spatial relation between temple and royal tomb complex; exact distance remains in narration", "thin muted-gold survey ribbon following the ground surface", "temple workshop", ["stone reliquary position"], "royal tomb edge", "a small dust ring settles at each real context anchor")),
    visual(12, 1, 1,
        "4. 박산향로 비교의 막힘", "COMPARISON_TABLEAU", "학술해석",
        "Dark museum comparison table: one restrained Chinese Boshan-type incense burner silhouette with mountain lid stands at left as lineage evidence, while the locked Baekje burner at right clearly adds dragon base, lotus bowl, five musicians, animals and phoenix; a visible unfilled gap between them signals that no exact matching object exists, no national flags",
        "Boshan-burner lineage comparison and lack of exact parallel",
        ["generic Boshan mountain-lid lineage", "full Baekje dragon-lotus-mountain-phoenix synthesis", "visible non-match gap"],
        "Orbit the Boshan silhouette, snap across the empty comparison gap, climb the Baekje burner from dragon to phoenix and stop where no exact duplicate can enter.",
        ["Acknowledge the Boshan lineage.", "Show why the complete Baekje combination has no exact match."],
        cam("Boshan mountain-lid edge", "across the empty gap then vertically up the Baekje burner", "Baekje phoenix above the unfilled comparison gap", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "two lineages separated by physical gap", "2.4s gap crossing", "5.6s Baekje vertical rise"),
        modern=True),
    visual(13, 1, 1,
        "4. 단서 과잉과 발상의 전환", "INVESTIGATION_PIVOT", "학술해석",
        "Circular archaeological research-table diorama containing burnt-soil samples, tile fragments, temple plan model, sarira reliquary context and Boshan comparison object around the locked Baekje burner; every external evidence route ends short, while the burner's own dragon-to-phoenix vertical axis remains brightly available for study, no readable notes",
        "Synthesis of evidentiary dead end and object-centred iconographic method",
        ["multiple external evidence stations", "all external paths ending unresolved", "artifact's own vertical iconographic axis"],
        "Whip around the failed evidence stations, tighten rapidly toward the burner, then reverse direction and begin reading it from the dragon base upward.",
        ["Make the dead end tangible.", "Pivot from missing records to the artifact itself."],
        cam("burnt-soil evidence tray", "fast circle through evidence stations then inward to artifact base", "dragon-to-phoenix reading axis", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "CRANE_ORBIT_REVEAL", "SURFACE_TO_INTERIOR", "artifact becomes the new evidence source", "2.0s first dead-end turn", "5.0s direction reversal at dragon"),
        modern=True),
    visual(14, 1, 1,
        "5. 아래에서 위로 읽은 상징", "ICONOGRAPHIC_CUTAWAY", "학술해석",
        "Tall sectional hero diorama of the locked burner with three physically continuous evidence zones: lotus petals at the lower bowl, perforated mountain peaks and phoenix above, and the distant royal-temple landscape aligned behind; the real bronze object remains whole while restrained surface-anchored light paths link the verified symbols, no floating religious icons",
        "Iconographic interpretation: Buddhist lotus, immortal mountain-phoenix world, royal-temple context",
        ["lotus as lower visual zone", "mountain and phoenix as upper visual zone", "royal-temple archaeological context behind"],
        "Start on the lotus, accelerate through the perforated mountain, orbit the phoenix and pull focus to the royal temple behind without leaving the single vertical axis.",
        ["Read lotus, mountain and phoenix in order.", "Join them to the royal-temple context."],
        cam("lowest lotus petal", "up the artifact axis through mountain to phoenix", "royal temple aligned behind the summit", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "MACRO_PROBE", "SECTION_DIVE", "symbolic zones and site context in one axis", "2.1s lotus light contact", "5.1s phoenix orbit"),
        architecture=True,
        veo=graphic("ROUTE_PATH", "Conceptual iconographic reading of already-present verified zones, not a literal energy flow", "thin warm-gold engraved-looking path touching the bronze surface", "lotus petal", ["mountain peak", "phoenix foot"], "royal-temple foundation in depth", "each real anchor catches one restrained reflection")),
    visual(15, 1, 1,
        "5. 물에서 하늘까지와 계통", "COMPARISON_CUTAWAY", "학술해석",
        "One deep museum-scale diorama: the Baekje burner dominates centre with water-dragon base, lotus, mountain and phoenix arranged bottom-to-top; a smaller Boshan-lineage burner remains to the side on a separate dark plinth, visibly related yet far less complex, no triumphal flag or insulting caricature",
        "Vertical cosmology and comparative Boshan lineage",
        ["water-to-sky Baekje order", "separate related Boshan form", "Baekje object's unusually complete synthesis"],
        "Rise fast from water dragon to phoenix, bank sideways around the smaller lineage object, then return in a wider arc that leaves the complete Baekje world dominant.",
        ["Reveal one ordered world from water to sky.", "Compare the lineage without erasing Baekje innovation."],
        cam("dragon water curl", "vertical rise then side-bank through comparison depth", "complete Baekje burner dominant", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "lineage and innovation readable together", "2.2s summit arrival", "5.0s comparison bank"),
        modern=True),
    visual(16, 1, 1,
        "5. 백제의 자기 언어", "ARTIFACT_HERO", "학술해석",
        "Dignified high-contrast hero portrait of the locked Baekje gilt-bronze incense burner in a dark Sabi-period temple diorama; behind it, faint separate material silhouettes of lotus, mountain, musicians, animals and phoenix converge only through camera perspective into the already complete artifact, showing cultural synthesis without morphing its geometry",
        "Scholarly synthesis of received Boshan tradition and Baekje transformation",
        ["complete immutable Baekje burner", "source motifs already physically present behind", "strong Korean Baekje temple context"],
        "Follow the existing motifs through depth as they align behind the burner, execute a fast half-orbit and settle on the complete object as the world-class result; no object morphs.",
        ["Reject simple copying.", "Land on Baekje's fully transformed visual language."],
        cam("lotus silhouette in foreground", "through motif depth into a short artifact half-orbit", "complete burner hero", "CONTROLLED_ORBIT_REVEAL", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "artifact alone in final focus", "2.2s motif alignment", "5.4s hero settle"),
        architecture=True),
    visual(17, 1, 2,
        "6. 확인된 정체", "RITUAL_RECONSTRUCTION", "학술해석",
        "Evidence-bounded Baekje royal-temple ritual diorama: the locked incense burner stands on a low central ritual platform inside a restrained Sabi-period timber hall, a small ember bed and pale smoke show its real incense function, no named priest, no invented exact ceremony and no palace throne room",
        "Royal-temple context and incense-burner function",
        ["locked burner on low ritual platform", "Baekje royal-temple hall", "restrained real incense smoke"],
        "Enter through the timber doorway, follow the floor axis quickly to the burner, orbit once around the smoke path and settle on the object as an incense burner used in a royal temple.",
        ["State the confirmed royal-temple incense-burner identity."],
        cam("Baekje hall threshold", "along the floor axis into a short burner orbit", "burner on ritual platform", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "ORBIT_REVEAL", "confirmed ritual-use tableau", "3.0s doorway pass", "5.8s smoke orbit"),
        architecture=True,
        i2v_guard="Show only a generic evidence-bounded ritual setting; do not invent the exact ceremony, named officiant or event."),
    visual(17, 2, 2,
        "6. 백제를 증언하는 실물", "EVIDENCE_TABLEAU", "학술해석",
        "The burner stands central on a dark plinth. Four evidence bays show its five musicians, ceremonial motifs, fine gilt-bronze casting and a Sabi temple fragment, connecting Baekje music, ceremonies, design and metalwork, without labels",
        "Object evidence for Baekje music, ceremonies, design and metal technology",
        ["five-musician casting detail", "ritual iconography and temple context", "thin gilding and fine bronze casting"],
        "Orbit from the musician detail through ritual and metalwork bays, then pull inward to the complete burner so every claim resolves back into the real object.",
        ["Turn the artifact into evidence for Baekje culture and technology."],
        cam("tiny bronze musician detail", "through four evidence bays toward the central object", "complete burner as witness", "CONTROLLED_ORBIT_REVEAL", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "all evidence converges on artifact", "2.4s musician focus", "5.6s metal-to-whole pullback"),
        modern=True),
    visual(18, 1, 2,
        "6. 제작자와 의식의 공백", "EVIDENCE_GAP", "미확인",
        "Forensic dark-room diorama: the real-form burner stands between an empty craftsman's station and empty ritual platform. Exact burner: dragon base, lotus bowl, perforated mountain lid with tiny musicians and animals, summit phoenix; no tripod ding or generic jar. No portrait, signature, readable inscription or reenacted ceremony; two evidence paths end at empty positions",
        "No surviving maker identification or exact ritual record",
        ["empty craftsman's station", "unoccupied ritual platform", "artifact between two unresolved evidence gaps"],
        "Travel from casting tools toward the burner, reverse toward the ritual platform, and stop twice at visible gaps before any maker or ceremony can appear.",
        ["Name the unknown maker.", "Separate the unknown exact ritual."],
        cam("period casting-tool edge", "to artifact then reverse toward empty ritual platform", "two unfilled evidence gaps", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "ORBIT_REVEAL", "maker and ritual remain empty", "2.4s first evidence stop", "5.4s direction reversal"),
        architecture=True),
    visual(18, 2, 2,
        "6. 분리 출토와 은닉 여부", "CUTAWAY", "미확인",
        "Return to the documented workshop-sump cutaway: body is dragon base plus lotus bowl; separate lid is perforated mountain plus tiny musicians, animals and summit phoenix; no tripod ding or generic jar. Both lie separated in wet mud exactly as excavated among broken tiles and workshop fragments. Two equally faint route stubs suggest urgent concealment versus accidental abandonment without showing either act or person",
        "Separated find state; intention and concealment remain unconfirmed",
        ["separated body and lid in real pit context", "no person or hiding act", "two incomplete possibility routes"],
        "Dive from the sump rim to the separated parts, orbit both without assembling them, then follow each route stub only until it breaks in the mud and return to the unchanged find state.",
        ["Hold on the unexplained separation.", "Refuse to choose concealment without evidence."],
        cam("sump rim above separated parts", "down around body and lid then toward two broken route stubs", "unchanged documented find state", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "IMMERSIVE_POV_DOLLY", "SECTION_DIVE", "separated parts remain unresolved", "2.2s body-to-lid orbit", "5.3s route break"),
        architecture=True,
        veo=graphic("ROUTE_PATH", "Two hypotheses are shown as incomplete possibilities; neither is selected as fact", "two very faint earth-coloured route stubs embedded in the pit surface", "separated artifact layer", ["sump wall"], "two broken ends before the surface", "both paths crumble and disappear at the same distance")),
    visual(19, 1, 1,
        "6. 미래 증거가 잇는 생애", "FUTURE_EVIDENCE", "학술해석",
        "Four-station research diorama: empty mold bay, unreadable ritual-record niche, complete real-form burner and muddy sump. Exact burner: dragon base, lotus bowl, perforated mountain lid with tiny musicians and animals, summit phoenix; no tripod ding or generic jar. Missing links stay transparent; no false discovery",
        "Bounded future evidence: workshop molds or royal ritual records",
        ["same-workshop mold evidence bay", "royal ritual-record niche", "artifact-to-sump lifecycle stations"],
        "Race along a physical evidence route from the empty mold bay to the record niche, circle the burner and descend into the sump; the route brightens only at existing evidence and stays dim across missing links.",
        ["Name the future mold and ritual-document evidence.", "Trace the possible artifact life only as far as evidence permits."],
        cam("empty mold impression bay", "through record niche and artifact into sump", "last documented find position", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "IMMERSIVE_POV_DOLLY", "SECTION_DIVE", "bounded lifecycle route", "2.2s record-niche pass", "5.2s artifact orbit"),
        architecture=True, modern=True,
        veo=graphic("ROUTE_PATH", "Future reconstruction target that remains dim where evidence is absent", "thin aged-gold physical ribbon following tables, artifact surfaces and soil", "mold evidence bay", ["ritual-record niche", "complete burner"], "sump find position", "the ribbon brightens at real anchors and fades over missing intervals")),
    visual(20, 1, 1,
        "6. 백제는 사라졌지만", "NATIONAL_PAYOFF", "학술해석",
        "Epic but historically restrained deep diorama: a Sabi-period Baekje temple and city silhouette recedes into the smoky darkness of 660 in the background while the locked 61.8-centimetre burner remains brilliantly edged and razor-sharp in the foreground, complete dragon-to-phoenix silhouette, no burning people and no fantasy gold explosion",
        "660 collapse contrasted with surviving artifact evidence",
        ["Sabi-period landscape receding in 660", "complete 61.8 cm burner foreground", "strong material proof rather than flag imagery"],
        "Pull rapidly away from the fading Sabi landscape, pass through smoke toward the artifact, then make a forceful upward rise from dragon to phoenix and settle on the full bronze world.",
        ["Let the kingdom disappear.", "Make the surviving 61.8-centimetre world deliver the national payoff."],
        cam("fading Baekje timber roofline", "through smoke to artifact then upward along its axis", "complete burner silhouette", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CRANE_ORBIT_REVEAL", "SURFACE_TO_INTERIOR", "artifact outlasts the darkened kingdom", "2.1s smoke passage", "5.2s dragon-to-phoenix rise"),
        architecture=True),
    visual(21, 1, 1,
        "6. 고정 결말", "ARTIFACT_HERO", "발굴확인",
        "Final dignified hero portrait of the locked Baekje gilt-bronze incense burner above a subtle strip of the original muddy find context: dragon, lotus, perforated mountain, musicians, animals and phoenix all intact and razor-sharp under one warm museum beam; deep black-brown background, restrained dust, no title or logo",
        "Synthesis of verified object identity and find context",
        ["complete real-form burner", "subtle muddy excavation echo", "single warm artifact spotlight"],
        "Begin with a fast three-degree half-orbit, let one warm light sweep climb from dragon to phoenix, then pull back slightly and hold perfectly still for the closing channel line.",
        ["Return to the buried-history image.", "Close in stillness on the Baekje gilt-bronze incense burner."],
        cam("mud grain beside dragon base", "short artifact half-orbit then slight pullback", "complete closing portrait", "EVIDENCE_HOLD", "LOCKED_EVIDENCE_CAMERA", "NONE", "full artifact in final stillness", "1.8s warm light climb", "5.5s final hold"),
        i2v_guard="Treat the start-frame artifact as immutable: do not redraw, simplify, assemble, deform or animate the dragon, lotus, peaks, figures, animals or phoenix. If fidelity conflicts with motion, freeze the artifact and move only camera parallax, smoke and raking light."),
]


TYPE_MAP = {
    "ARTIFACT_REVEAL": "ARTIFACT_MACRO",
    "FUNCTION_RECONSTRUCTION": "MECHANISM",
    "EVIDENCE_TIMELINE": "DIAGRAM",
    "COMPARISON_TABLEAU": "INVENTORY_TABLEAU",
    "INVESTIGATION_PIVOT": "DIAGRAM",
    "ICONOGRAPHIC_CUTAWAY": "CUTAWAY",
    "COMPARISON_CUTAWAY": "INVENTORY_TABLEAU",
    "ARTIFACT_HERO": "ARTIFACT_MACRO",
    "RITUAL_RECONSTRUCTION": "HISTORICAL_RECONSTRUCTION",
    "EVIDENCE_TABLEAU": "INVENTORY_TABLEAU",
    "EVIDENCE_GAP": "DIAGRAM",
    "FUTURE_EVIDENCE": "SCIENTIFIC_EVIDENCE",
    "NATIONAL_PAYOFF": "ARTIFACT_MACRO",
}


def _axis(item: dict[str, object]) -> str:
    path = item["camera_path"]
    operator = str(path["operator_style"])
    route = str(path["route"]).lower()
    if "ORBIT" in operator or "orbit" in route or "around" in route:
        return "ORBIT"
    if "lateral" in route or "across" in route or "along" in route:
        return "LATERAL"
    if str(path["speed_profile"]) == "EVIDENCE_HOLD":
        return "LOCKED"
    return "FORWARD"


def _scale(item: dict[str, object]) -> str:
    image = str(item["image"]).lower()
    if any(word in image for word in ("macro", "pore", "bristle", "close 1993")):
        return "MACRO"
    if any(word in image for word in ("large terrain", "landscape", "site", "full vertical", "deep diorama")):
        return "WIDE"
    return "MEDIUM"


def _prepare_camera(item: dict[str, object]) -> None:
    path = item["camera_path"]
    if path["speed_profile"] == "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE":
        path["speed_profile"] = "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE"
    replacements = {
        "reverse direction": "continue on the same axis",
        "then reverse": "then continue on the same arc",
        "reverse toward": "continue along one lateral arc toward",
        "then pull back": "then settle in a slightly wider composition",
        "pull back slowly": "settle slowly in the final composition",
    }
    for field in ("route", "destination", "settle_point"):
        text = str(path[field])
        for old, new in replacements.items():
            text = text.replace(old, new)
        path[field] = text
    action = str(item["action"])
    for old, new in replacements.items():
        action = action.replace(old, new)
    item["action"] = action
    path.update({
        "start_frame_anchor_visible": True,
        "start_frame_anchor_evidence": f"The locked image prompt visibly places {path['entry_anchor']} at the opening camera position.",
        "single_axis": _axis(item),
        "scale_domain": _scale(item),
        "end_state": f"Last frame holds the unchanged composition on {path['settle_point']}.",
    })


def _v6_video(prompt: str, item: dict[str, object]) -> str:
    path = item["camera_path"]
    prompt = prompt.replace("reverse direction", "continue on the same axis")
    prompt = prompt.replace("then reverse", "then continue on the same arc")
    prompt = prompt.replace("then pull back", "then settle in a slightly wider composition")
    return (
        prompt
        + f" Start anchor: {path['entry_anchor']} is already visible in the locked first frame."
        + f" Mid anchor: remain on the same {str(path['single_axis']).lower()} axis through {path['route']}."
        + f" Final anchor: arrive once at {path['destination']}."
        + f" Last frame: {path['end_state']} No cut, reset, loop or restart; never return to an earlier composition; remain on the final anchor and hold there."
    )


def _compact_v6_video(item: dict[str, object], beats: list[dict[str, object]], seconds: int) -> str:
    """Flow UI actual-key prompt: keep every motion lock once, without duplicate prose."""
    path = item["camera_path"]
    source_end = float(beats[-1]["end"]) if beats else float(seconds)
    scale = min(1.0, float(seconds) / source_end) if source_end > 0 else 1.0
    schedule = " ".join(
        f"{float(beat['start']) * scale:.2f}-{float(beat['end']) * scale:.2f}s {beat['action']}"
        for beat in beats
    )
    parts = [
        f"Preserve the locked start image exactly: artifact identity, geometry, material, era and lighting. "
        f"One continuous {seconds}s I2V shot; no hard cut, teleport, morph or new object. Start camera by 0.35s.",
        f"Camera: {path['entry_anchor']} -> {path['route']} -> {path['destination']}; "
        f"settle once on {path['settle_point']} and hold the last frame.",
        str(item["action"]),
    ]
    if item["i2v_guard"]:
        parts.append(
            "Keep the start-frame artifact rigid and unchanged; never redraw, assemble, deform or animate its parts. "
            "If motion conflicts with fidelity, move only camera parallax, smoke and light."
        )
    if item["veo"] is not None:
        veo = item["veo"]
        parts.append(
            f"One restrained {str(veo['function']).lower().replace('_', ' ')} in physical world space: "
            f"{veo['visual_language']}; {veo['start']} -> {veo['end']}. "
            "Physical perspective, parallax, contact and occlusion; no floating HUD, text, number or label."
        )
    parts.extend((
        f"TTS-locked timing: {schedule}",
        "No voice, music or subtitles. No cut, reset, loop, restart or reverse; remain on the final anchor.",
    ))
    return " ".join(parts)


def _visual_states(item: dict[str, object]) -> list[dict[str, object]]:
    path = item["camera_path"]
    return [
        {"time": 0.0, "composition": f"Locked opening on {path['entry_anchor']}", "camera_pose": "initial pose on the declared single axis", "visible_anchors": [path["entry_anchor"]]},
        {"time": 4.0, "composition": f"Continuous mid-shot along {path['route']}", "camera_pose": "mid-axis travel without scale reset", "visible_anchors": [path["entry_anchor"], path["destination"]]},
        {"time": 8.0, "composition": str(path["end_state"]), "camera_pose": "settled final pose", "visible_anchors": [path["destination"], path["settle_point"]]},
    ]


def _segment_bounds(audio_scene: int, part: int, parts: int, sources: dict, cues: list[dict], starts: dict[int, float]):
    scene_cues = [cue for cue in cues if int(cue["scene"]) == audio_scene]
    groups = base.cue_groups(scene_cues, parts)
    group = groups[part - 1]
    source_duration = float(sources[str(audio_scene)]["duration"])
    if part == 1:
        local_start = 0.0
    else:
        local_start = (float(groups[part - 2][-1]["end"]) + float(group[0]["start"])) / 2 - starts[audio_scene]
    if part == parts:
        local_end = source_duration
    else:
        local_end = (float(group[-1]["end"]) + float(groups[part][0]["start"])) / 2 - starts[audio_scene]
    return group, round(local_start, 3), round(local_end, 3)


def build() -> None:
    ep = base.EPISODE
    duration_data = json.loads((ep / "audio" / "durations.json").read_text(encoding="utf-8"))
    sources = duration_data["scenes"]
    sync_cues = json.loads((ep / "자막_싱크.json").read_text(encoding="utf-8"))["cues"]
    starts: dict[int, float] = {}
    elapsed = 0.0
    for key in sorted(sources, key=int):
        starts[int(key)] = elapsed
        elapsed += float(sources[key]["duration"])

    counts: dict[int, int] = {}
    for item in SPECS:
        counts[int(item["audio_scene"])] = counts.get(int(item["audio_scene"]), 0) + 1
    if sorted(counts) != list(range(1, len(sources) + 1)):
        raise ValueError("모든 승인 TTS 장면이 최소 한 개 영상에 배정돼야 합니다")
    for item in SPECS:
        if counts[int(item["audio_scene"])] != int(item["parts"]):
            raise ValueError(f"TTS {item['audio_scene']} 분할 수 불일치")

    rows: list[dict[str, object]] = []
    for visual_n, item in enumerate(SPECS, 1):
        _prepare_camera(item)
        item["scene_type"] = TYPE_MAP.get(str(item["scene_type"]), str(item["scene_type"]))
        audio_scene = int(item["audio_scene"])
        part = int(item["part"])
        parts = int(item["parts"])
        group, local_start, local_end = _segment_bounds(audio_scene, part, parts, sources, sync_cues, starts)
        segment_duration = round(local_end - local_start, 3)
        narration = " ".join(str(cue.get("raw") or cue["text"]) for cue in group)
        segment_global_start = starts[audio_scene] + local_start
        beats = base.make_beats(audio_scene, float(sources[str(audio_scene)]["duration"]), item["beat_actions"], group, starts[audio_scene])
        for beat in beats:
            beat["start"] = round(max(0.0, float(beat["start"]) - local_start), 3)
            beat["end"] = round(min(segment_duration, float(beat["end"]) - local_start), 3)
        lock = dict(base.LOCK_BASE)
        if item["modern"]:
            lock.update(base.MODERN_LOCK_UPDATE)
        lock.update({"source_reference": item["source"], "site_artifact_fingerprint": item["fingerprints"]})
        human_guard = (
            "If any human figure is visible, it must be South Korean archaeologists in practical 1993 field clothing."
            if item["modern"] else
            "If any human figure is visible, it must be Korean Baekje people in period-correct Sabi-era clothing."
        )
        full_image = base.image_prompt(item) + " " + human_guard
        row: dict[str, object] = {
            "n": visual_n,
            "audio_scene": audio_scene,
            "audio_part": f"{part}/{parts}",
            "audio_offset_start": local_start,
            "audio_offset_end": local_end,
            "timeline_start": round(segment_global_start, 3),
            "timeline_end": round(segment_global_start + segment_duration, 3),
            "chapter": item["chapter"],
            "ct": item["scene_type"],
            "txt": narration,
            "tts": segment_duration,
            "omni": 8,
            "playback_speed": round(8.0 / segment_duration, 4) if segment_duration > 8 else 1.0,
            "evidence": item["evidence"],
            "generation_mode": "I2V_LOCKED",
            "architecture_anchor_required": bool(item["architecture"]),
            "modern_scene": bool(item["modern"]),
            "motion_owner": "VEO_INTEGRATED_3D" if item["veo"] else "GENERATED_PHYSICS",
            "motion_space": "WORLD_3D",
            "camera_path": item["camera_path"],
            "visual_lock": lock,
            "tts_beats": beats,
            "visual_states": _visual_states(item),
            "img_v2": full_image,
            "status": "PROMPT_LOCKED_IMAGE_PENDING",
            "flow_account": "jy04210810@gmail.com" if visual_n <= 21 else "jjwwhhjj1116@gmail.com",
        }
        if segment_duration > 9.0:
            row["long_scene_review"] = (
                "One indivisible evidence claim remains in one physical space; an aggressive same-axis camera move and safe 0.75-1.0 playback-speed range cover the full narration without reset."
            )
        row["vid"] = _v6_video(base.video_prompt(item, beats, 8), item)
        if item["veo"] is not None:
            row["veo_graphic"] = item["veo"]
        rows.append(row)

    (ep / "02a.장면구분.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    table = [
        f"# {base.EPISODE_LABEL} — 23개 8초 I2V 장면 구분표", "",
        f"> {base.SCENE_COUNT_NOTE}", "",
        "| 영상 | TTS | 구간 | 타임라인 | 길이 | 계정 | 유형 | 핵심 화면 |",
        "|---:|---:|---:|---:|---:|---|---|---|",
    ]
    visual_doc = [
        f"# {base.EPISODE_LABEL} — 고증 잠금 I2V 시각화", "", f"visual_scene_count: {len(rows)}",
        f"audio_scene_count: {len(sources)}", "generation_mode: I2V_LOCKED", "image_model: Nano Banana",
        "video_model: Veo/Flow Omni", "aspect_ratio: 9:16", "image_count_per_visual_scene: 1", "video_count_per_visual_scene: 1", "",
    ]
    images: list[str] = []
    videos: list[str] = []
    ui_images: list[str] = []
    ui_videos: list[str] = []
    ui_check: list[dict[str, object]] = []
    for row, item in zip(rows, SPECS):
        core = str(item["image"]).split(":", 1)[0][:76].replace("|", "/")
        table.append(
            f"| {row['n']:03d} | {row['audio_scene']:03d} | {row['audio_part']} | {row['timeline_start']:.3f}-{row['timeline_end']:.3f}s | "
            f"{row['tts']:.3f}s | {row['flow_account']} | {row['ct']} | {core} |"
        )
        visual_doc.extend([
            f"## 영상 {row['n']:03d} — TTS {row['audio_scene']:03d} ({row['audio_part']})", "",
            f"- 타임라인: {row['timeline_start']:.3f}-{row['timeline_end']:.3f}s", f"- 나레이션: {row['txt']}",
            f"- Flow 계정: {row['flow_account']}", "", "### IMAGE", "", str(row["img_v2"]), "", "### I2V", "", str(row["vid"]), "",
        ])
        images.append(str(row["img_v2"]))
        videos.append(str(row["vid"]))
        compact_image = base.compact_image_prompt(item)
        if item["people"]:
            compact_image += (
                " South Korean archaeologists in 1993 fieldwear."
                if item["modern"] else " Korean Baekje people in Sabi-era clothing."
            )
        compact_image += " No European people or Chinese imperial palace."
        if item["modern"]:
            compact_image += " No ancient costume on modern researchers."
        compact_video = _compact_v6_video(item, row["tts_beats"], 8)
        errors = base.validate_compact(row, compact_image, compact_video)
        ui_images.append(compact_image)
        ui_videos.append(compact_video)
        ui_check.append({
            "n": row["n"], "audio_scene": row["audio_scene"], "account": row["flow_account"],
            "image_chars": len(compact_image), "video_chars": len(compact_video),
            "status": "PASS" if not errors else "FAIL", "errors": errors,
        })
    (ep / "02a.장면구분표.md").write_text("\n".join(table) + "\n", encoding="utf-8")
    (ep / "02.시각화.txt").write_text("\n".join(visual_doc), encoding="utf-8")
    (ep / "flow_images.txt").write_text("\n\n".join(images) + "\n", encoding="utf-8")
    (ep / "flow_videos.txt").write_text("\n\n".join(videos) + "\n", encoding="utf-8")
    (ep / "flow_images_ui.txt").write_text("\n\n".join(ui_images) + "\n", encoding="utf-8")
    (ep / "flow_videos_ui.txt").write_text("\n\n".join(ui_videos) + "\n", encoding="utf-8")
    (ep / "flow_ui_prompt_check.json").write_text(json.dumps(ui_check, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    failures = [item for item in ui_check if item["status"] != "PASS"]
    if failures:
        raise ValueError(f"Flow UI 프롬프트 자가검수 실패: {failures}")
    print(f"{base.EPISODE_LABEL} 시각화 빌드 완료: {len(rows)}영상 / {elapsed:.3f}초")


if __name__ == "__main__":
    build()
