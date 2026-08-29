#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""EP07 사해문서 승인 TTS에서 고증 잠금 I2V 장면표와 Flow 입력을 만든다."""

from __future__ import annotations

import build_ep05_storyboard as base


base.EPISODE = base.ROOT / "산출물" / "EP07_사해문서"
base.EPISODE_LABEL = "EP07 사해문서"
base.SCENE_COUNT_NOTE = "승인 대본의 23개 의미·행동·장소·증거 전환과 실측 TTS에서 파생했으며 고정 컷 수가 아니다."
base.STYLE = (
    "premium full-frame cinematic archaeological 3D diorama, unmistakably a museum-scale crafted miniature world and not live-action, "
    "immersive macro-lens depth cues, restrained tilt-shift, layered foreground-midground-background depth, physically based PBR materials, "
    "high-frequency parchment fibre, limestone dust, clay pores and ink microtexture, sharp material separation, global illumination, high fidelity, "
    "4K source detail, 9:16 vertical composition"
)
base.ANCIENT_CIV = (
    "Second Temple period Judea from the third century BCE to the first century CE, Qumran settlement and marl-limestone caves beside the Dead Sea"
)
base.MODERN_CIV = (
    "documented Dead Sea Scrolls discovery and research history: 1947 Ta'amireh Bedouin discovery tradition, 1949-1956 Qumran cave archaeology, "
    "and restrained modern conservation, multispectral imaging and ancient-DNA laboratories"
)
base.ANCIENT_PEOPLE = (
    "Levantine Judean scribes and community members with olive-brown skin, dark hair and beards, undyed linen or wool tunics, simple leather belts, "
    "sandals and restrained headcloths appropriate to the Second Temple period"
)
base.MODERN_PEOPLE = (
    "Taamireh Bedouin youths in historically restrained 1940s desert clothing, mid-twentieth-century archaeologists in period field wear, "
    "or modern conservators in neutral laboratory clothing only as the scene requires"
)
base.ANCIENT_ARCH = (
    "Qumran low pale-stone and mud-plaster communal rooms, stepped water installations, simple timber shelves and tables, and the steep eroded marl cliffs and natural caves above the Dead Sea"
)
base.NEGATIVE = (
    "no Christian cross, no Jesus portrait, no church, no Islamic mosque, no medieval monk, no European castle, no Egyptian pharaoh, no East Asian costume, "
    "no Roman legion unless explicitly requested, no fantasy temple, no magical glow, no treasure chest, no modern book, no printed Bible, no glossy new parchment, "
    "no intact library of hundreds of perfect scrolls, no fabricated readable Hebrew, Aramaic or Greek text, no English letters, no map labels, no fake manuscript title, "
    "no invented author portrait, no DNA double helix floating HUD, no ancient costume on modern researchers, no plastic toy surface, no exterior cube frame, no low-poly game asset, no gore, no watermark, no text, no labels, no letters"
)
base.LOCK_BASE = {
    "civilization": "Second Temple period Judean manuscript culture and the Qumran cave assemblage",
    "era": "third century BCE to first century CE manuscripts",
    "region": "Qumran and the marl-limestone cliffs on the northwest shore of the Dead Sea",
    "people_lock": "Levantine Judean scribes and community members in period-correct linen and wool clothing",
    "forbidden_culture": ["Christian medieval", "Islamic medieval", "Egyptian pharaonic", "East Asian", "European castle", "fantasy"],
    "diorama_style": "CINEMATIC_ARCHAEOLOGICAL_DIORAMA",
    "material_fidelity": "PBR_MICROTEXTURE_HIGH_FIDELITY",
}
base.MODERN_LOCK_UPDATE = {
    "civilization": "Documented 1947-1956 Qumran discovery and modern scientific research history",
    "era": "1947-1956 discovery and archaeology or contemporary conservation science",
    "people_lock": "Ta'amireh Bedouin, mid-century archaeologists or modern conservators in exact period clothing and equipment",
}
base.COMPACT_ANCIENT_CONTEXT = "Second Temple Judea and Qumran, 3rd century BCE to 1st century CE."
base.COMPACT_MODERN_CONTEXT = "Documented Qumran discovery and scroll research from 1947 to modern science."


def choose_duration(tts: float) -> int:
    """Flow 최대 10초. 10~12초 TTS는 0.83~1.0 배속의 안전 범위에서 맞춘다."""
    for value in (4, 6, 8, 10):
        if tts <= value:
            return value
    if tts <= 12.0:
        return 10
    raise ValueError(f"안전 배속으로 흡수할 수 없는 TTS 장면: {tts:.3f}")


base.choose_duration = choose_duration
cam = base.cam
graphic = base.graphic
spec = base.spec


base.SPECS = [
    spec(
        "1. 항아리가 깨진 순간", "DISCOVERY_ACTION", "문헌기록",
        "Inside a dark Cave 1-style Qumran cavity, a tall cylindrical buff-clay storage jar with a fitted bowl lid has just cracked along one existing seam on the limestone floor; dry clay shards separate only slightly and several compact dark-brown ancient parchment rolls and wrapped fragments become visible among limestone dust, dramatic raking torchlike light but no person, no explosion and no readable writing",
        "IAA discovery tradition and Cave 1 cylindrical scroll jars",
        ["tall cylindrical buff-clay jar with bowl lid", "dry Qumran limestone cave floor", "dark compact parchment rolls protected inside"],
        "Crash toward the existing crack as one shard tips outward, pass through the real opening beside falling limestone dust and settle inches above the first dark parchment roll; no object appears from nowhere.",
        ["Break open the 2,000-year-old jar.", "Reveal the blackened scrolls inside."],
        cam("fresh clay fracture edge", "through the widening real seam between two shards", "first dark parchment roll", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "IMMERSIVE_POV_DOLLY", "SURFACE_TO_INTERIOR", "jar fracture and scroll together", "1.8s dust burst at the seam", "5.0s rack focus from clay pore to parchment fibre"),
        modern=True,
    ),
    spec(
        "1. 사해문서와 염소", "ARTIFACT_MACRO", "측정확인",
        "Hero macro of a genuine-style Dead Sea Scroll parchment fragment: irregular torn beige-to-dark-brown animal-skin edge, stitched sheet seam, dense but fully unreadable carbon-ink line texture and curled dry fibres, resting on a neutral conservation support; in deep background a 1947 Bedouin goat silhouette searches a Qumran cliff ledge, artifact remains dominant, no modern printed page",
        "Israel Museum Great Isaiah Scroll material and IAA discovery tradition",
        ["irregular animal-skin fibre edge", "ancient stitched sheet seam", "dense carbon-ink line texture kept unreadable"],
        "Race along the torn fibre edge, widen to the full fragment, then pull focus through the cave mouth to the distant goat and stop on the contradiction between monumental manuscript and accidental discovery.",
        ["Identify the thousand-year-older manuscript evidence.", "Turn the reveal toward the lost-goat discovery question."],
        cam("split parchment fibre", "along the stitched seam then backward through cave depth", "goat silhouette at cliff ledge", "MACRO_PROBE_SETTLE", "MACRO_PROBE", "ORBIT_REVEAL", "scroll foreground and goat background", "3.4s focus snap to ink texture", "7.1s focus pull to goat"),
        modern=True,
    ),
    spec(
        "2. 메마른 절벽의 모순", "SITE_ESTABLISH", "발굴확인",
        "Sweeping museum-scale diorama of the northwest Dead Sea shore at Qumran: pale eroded marl cliffs, steep ravines, tiny natural cave mouths, salt-blue water far below and almost no vegetation; one narrow ancient footpath climbs toward several separate caves, no giant fantasy cavern and no modern road",
        "IAA Qumran discovery sites and regional topography",
        ["eroded pale marl cliffs", "multiple small natural cave mouths", "Dead Sea basin below the plateau"],
        "Start at the salt-crusted shoreline, accelerate up the ravine in a low flying handheld-gimbal move, bank across three cave mouths and end deep at one impossible storage ledge.",
        ["Establish the hostile Dead Sea cliff.", "Ask how hundreds of manuscripts reached the caves."],
        cam("salt crystal on the shoreline", "up one ravine then laterally across the cliff face", "narrow cave storage ledge", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "SECTION_DIVE", "cliff and distant Dead Sea aligned", "2.6s bank around marl spur", "5.2s near-miss past cave mouth"),
        architecture=True,
    ),
    spec(
        "2. 천 년 빠른 성서 사본", "TEXT_RECORD", "학술해석",
        "Dark museum conservation-table diorama with several genuine-style Qumran biblical fragments arranged around one long Isaiah-scroll section, each parchment piece bearing physically carved-looking but unreadable carbon-ink line texture; a much later medieval codex silhouette remains far behind and softly out of focus only for age comparison, no legible letters and no modern Bible cover",
        "IAA scroll content and Israel Museum Great Isaiah Scroll",
        ["Qumran parchment fragments from multiple biblical books", "long stitched Isaiah sheet", "later codex held only as distant chronology contrast"],
        "Slide rapidly over several fragments, snap to the Isaiah stitched seam, then crane backward so the ancient scroll plane dominates while the later codex recedes by physical depth.",
        ["Open the scrolls and trigger the scholarly shock.", "Reveal the corpus as roughly a millennium earlier than the known medieval witnesses."],
        cam("carbon-ink line beside a torn edge", "across fragment field to Isaiah seam then upward", "ancient-scroll plane above later codex", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "MACRO_PROBE", "ORBIT_REVEAL", "ancient and later material separated by depth", "2.2s snap to Isaiah seam", "6.1s crane reveals chronology contrast"),
        modern=True,
    ),
    spec(
        "2. 성서만이 아니었다", "DISCOVERY_REVEAL", "문헌기록",
        "A central biblical parchment fragment on a matte dark support rotates only a few degrees while surrounding verified-style categories emerge from existing shadow: a rule-scroll fragment, a calendrical table fragment and a war-scroll fragment, all on distinct parchment shades with no readable generated writing; restrained forensic lighting and real material depth",
        "IAA scroll content: biblical and non-biblical compositions",
        ["biblical parchment centre", "community-rule and calendar fragments", "war-scroll manuscript fragment"],
        "Begin close on the biblical fragment, whip-orbit around its torn edge and settle on the wider ring of non-biblical texts already present in the darkness.",
        ["Hold the biblical explanation.", "Reverse it by revealing the non-biblical manuscripts."],
        cam("biblical fragment torn corner", "short whip-orbit into the surrounding evidence ring", "rule-calendar-war fragment group", "CONTROLLED_ORBIT_REVEAL", "CRANE_ORBIT_REVEAL", "SURFACE_TO_INTERIOR", "all document classes visible together", "2.0s orbit direction change", "4.2s light sweep across evidence ring"),
        modern=True,
    ),
    spec(
        "2. 문헌군의 범위", "INVENTORY_TABLEAU", "문헌기록",
        "Archaeological inventory diorama with four separate evidence stations: a community-rule parchment, a 364-day calendar-style ruled fragment, a darker war-scroll fragment, and the real-form Copper Scroll as two heavily oxidized green copper cylinders and opened thin copper sheet fragments; tiny sealed containers suggest treasure locations without showing treasure, no gold piles and no readable text",
        "IAA and Library of Congress representative scroll categories and Copper Scroll",
        ["community-rule parchment", "calendar and war manuscript fragments", "oxidized copper-sheet scroll without treasure"],
        "Crane fast from the rule fragment to the calendar, descend across the war fragment, then arc around the oxidized copper sheet and stop before the empty space where treasure would have been.",
        ["Inventory rules, calendar and war texts.", "End on the Copper Scroll's unverified treasure list."],
        cam("community-rule torn edge", "across four physical evidence stations", "oxidized copper-sheet opening", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "four categories in one evidence field", "2.4s drop from calendar to war fragment", "5.3s orbit around copper corrosion"),
        modern=True,
    ),
    spec(
        "2. 거대한 고대 도서관", "CUTAWAY", "학술해석",
        "Vertical cliff cutaway diorama of several separate small Qumran cave chambers, each containing only a few clay jars, wrapped scroll bundles or scattered fragments appropriate to different archaeological contexts; limestone strata and narrow connecting exterior paths are physically visible, no single gigantic library hall, no shelves full of perfect books",
        "IAA 11 Qumran cave assemblages; conceptual distribution only",
        ["separate natural cave chambers", "few jars or fragment groups per chamber", "continuous marl-limestone cliff strata"],
        "Dive through the exposed cliff section, enter one cave, exit through the real mouth, traverse the rock face to another chamber and end on the unresolved network of deposits.",
        ["Question the simple storage-room explanation.", "Expand the question to the person and motive behind the distributed library."],
        cam("outer marl stratum seam", "through first cave then along cliff to a second chamber", "separate deposit network", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "IMMERSIVE_POV_DOLLY", "SECTION_DIVE", "multiple caves aligned in cutaway", "2.1s pass through first chamber", "5.0s direction change along cliff"),
        architecture=True,
    ),
    spec(
        "3. 1947년 발견 전승", "HISTORICAL_RECONSTRUCTION", "문헌기록",
        "Historically restrained 1947 Judean Desert scene: a young Taamireh Bedouin herder in simple period desert clothing stands below a small cave mouth while goats move among pale rocks; his hand has just released one ordinary stone toward the darkness, no exact facial claim, no heroic pose and no modern gear",
        "IAA discovery account explicitly framed as tradition",
        ["young Ta'amireh Bedouin herder", "small Qumran cave mouth", "goats among pale marl rocks"],
        "Follow the thrown stone in a rapid handheld arc into the cave, strike the existing clay jar, recoil with the crack and settle on seven bundled scroll forms inside.",
        ["Follow the traditional lost-goat and thrown-stone account.", "Hear the jar crack and reveal the first seven scrolls."],
        cam("stone leaving the herder's hand", "ballistic arc through the small cave mouth", "jar fracture beside seven scroll bundles", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "SURFACE_TO_INTERIOR", "fractured jar and first bundles", "1.8s cave-entry exposure change", "4.3s impact recoil"),
        people=True, modern=True,
        i2v_guard="Treat the exact stone-and-jar sequence as a discovery tradition, not a filmed fact; avoid identifying one named individual.",
    ),
    spec(
        "3. 11개 동굴", "SPATIAL_MAP", "발굴확인",
        "Large vertical terrain diorama of roughly eight kilometres of Qumran cliffs represented as one continuous eroded ridge above the Dead Sea, eleven distinct real cave openings distributed along the face and thousands of tiny parchment fragments clustered only near their archaeological cave zones; no intact 900 perfect scrolls, no map labels or numerals",
        "IAA 1951-1956 survey: 11 manuscript caves across about 8 kilometres, over 900 documents",
        ["continuous eight-kilometre cliff-ridge model", "eleven distinct cave openings", "fragment clusters rather than 900 intact books"],
        "Race laterally along the ridge, pass each cave mouth as a restrained warm light activates in physical depth, then crane up to reveal the whole distribution and fragment field.",
        ["Expand the search along the Qumran cliff line.", "Reveal 11 caves and a corpus of more than 900 documents."],
        cam("first Cave 1-style opening", "fast lateral ridge traverse past separate cave mouths", "overhead full cliff distribution", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "IMMERSIVE_POV_DOLLY", "ORBIT_REVEAL", "whole survey ridge in one view", "3.0s near-miss past cave cluster", "6.4s crane to overhead"),
        modern=True,
        veo=graphic("ROUTE_PATH", "A physical survey route links only the documented cave openings and does not invent a hidden tunnel", "thin warm sand-coloured route ribbon hugging the cliff surface", "first cave mouth", ["central cave cluster", "Cave 4-style opening"], "last documented cave zone", "each already-present cave mouth catches one restrained amber reflection"),
    ),
    spec(
        "3. 한 동굴에서 문서군으로", "INVENTORY_TABLEAU", "발굴확인",
        "Overhead archaeological sorting diorama: seven larger scroll bundles at one side expand visually into many trays of real-looking irregular fragments from multiple caves, with Cave 4-style dense fragment trays dominating but every piece remaining torn, dusty and incomplete; no modern printed index, no perfect scroll army",
        "IAA discovery publication history and Cave 4 fragment concentration",
        ["first seven scroll bundles", "many irregular manuscript-fragment trays", "Cave 4-style dense fragment concentration"],
        "Start on the seven bundles, pull back rapidly as tray after tray enters the same physical table, then orbit the different parchment colours and stop on the unresolved single-versus-multiple-library question.",
        ["Grow the discovery from seven scrolls into a huge corpus.", "Ask whether it came from one library or many sources."],
        cam("first seven wrapped bundles", "rapid pullback over expanding conservation trays", "full multi-cave fragment field", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "bundles and fragment field together", "2.3s first tray expansion", "5.5s orbit across parchment colours"),
        modern=True,
    ),
    spec(
        "4. 쿰란 도서관 가설", "SITE_ESTABLISH", "발굴확인",
        "Qumran settlement scriptorium-style room diorama based on the archaeological interpretation: pale stone walls, mud plaster, one long low writing table and two small dark ceramic inkwells on a plain surface; sparse shelves and reed pens, no ornate synagogue, no medieval desks and no piles of perfect scrolls",
        "Qumran settlement inkwells and long-table interpretation, presented as evidence not certainty",
        ["two small ceramic inkwells", "long low plastered table", "simple Qumran pale-stone communal room"],
        "Enter through the low doorway in a quick handheld move, skim inches over the long table, orbit both inkwells and end looking from the room toward the distant manuscript caves.",
        ["Trace manuscript production to the Qumran settlement.", "Build the community-library hypothesis from the inkwells and table."],
        cam("low stone doorway threshold", "over the table surface around both inkwells", "window axis toward cave cliffs", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "ORBIT_REVEAL", "inkwells, table and caves aligned", "2.1s skim over table", "5.6s focus pull toward caves"),
        architecture=True, modern=True,
        i2v_guard="Present the room as an archaeological interpretation supported by inkwells and a long table, not a conclusively identified script workshop.",
    ),
    spec(
        "4. 가설을 흔든 다양성", "SCIENTIFIC_EVIDENCE", "학술해석",
        "Three adjacent conservation planes hold Hebrew-, Aramaic- and Greek-script manuscript fragments, distinguished only by authentic-looking physical line rhythms and parchment materials while all characters remain unreadable; many different scribal styles appear through line weight, spacing and correction marks, with an empty provenance slot at the centre",
        "IAA languages and scripts; palaeographic diversity",
        ["three script traditions on real fragment materials", "multiple line weights and scribal correction patterns", "empty ownership-provenance slot"],
        "Macro-probe one ink stroke, strafe across all three script planes, snap between several distinct scribal hands and stop at the empty provenance slot.",
        ["Reveal three languages and many hands.", "Arrive at the missing ownership and transport record."],
        cam("thick carbon-ink stroke", "laterally across three fragment planes and correction marks", "empty provenance slot", "MACRO_PROBE_SETTLE", "MACRO_PROBE", "ORBIT_REVEAL", "diverse fragments surrounding one absence", "2.0s first script-plane crossing", "5.0s focus snap across scribal styles"),
        modern=True,
    ),
    spec(
        "4. 단서는 넘치고 주인은 없다", "DIAGRAM", "미확인",
        "Forensic puzzle-table diorama of many documented-style parchment fragments, inkwells, clay jar shards and cave sediment samples connected by restrained physical threads that converge toward one empty central silhouette; every thread stops before contact, showing abundant evidence without naming an owner, no detective corkboard text and no face",
        "Synthesis of documented evidence limits; exact owner remains unknown",
        ["realistic parchment and jar evidence", "separate cave-sediment samples", "empty owner position with all links stopping short"],
        "Orbit the evidence quickly, follow three threads toward the centre, let each stop short in turn and finish on the unfilled owner silhouette.",
        ["Stack the clues until the answer seems near.", "Break every route before it can identify an owner."],
        cam("jar shard with cave sediment", "around evidence ring then along three physical threads", "empty central owner position", "CONTROLLED_ORBIT_REVEAL", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "evidence ring and empty centre", "2.2s first thread stop", "4.6s second direction change"),
        modern=True,
        veo=graphic("FORCE_PATH", "Links encode real evidence relations but terminate where provenance is missing", "thin dusty-amber physical filaments resting on the table and passing behind fragments", "jar sediment sample", ["inkwell", "script-style group"], "empty owner boundary", "all filaments dim when they reach the unresolved boundary"),
    ),
    spec(
        "5. 글자에서 가죽으로", "SCIENTIFIC_EVIDENCE", "측정확인",
        "Extreme macro conservation-lab diorama of one Dead Sea Scroll parchment fragment under neutral raking light: animal-skin fibre bundles, follicles, cracked collagen layers and carbon ink are visibly distinct; one tiny non-destructive sampling zone is marked only by physical illumination, no floating DNA helix, no screen HUD and no text",
        "Cell 2020 ancient-DNA analysis of Dead Sea Scroll parchment",
        ["animal-skin fibre and follicle microstructure", "carbon ink resting above parchment", "minute documented-style sampling zone"],
        "Push through the ink surface into the visible fibre layers, turn ninety degrees along a follicle channel and settle on the minute sampling zone as the question shifts from words to skin.",
        ["Abandon the unreadable ownership clues in the text.", "Enter the parchment material itself as the new evidence."],
        cam("carbon-ink ridge", "through cracked collagen fibres then along a follicle channel", "minute sampling zone", "MACRO_PROBE_SETTLE", "MACRO_PROBE", "SURFACE_TO_INTERIOR", "ink and skin layers together", "2.0s dive beneath ink ridge", "4.0s turn along follicle"),
        modern=True,
    ),
    spec(
        "5. 양피지 DNA의 실마리", "SCIENTIFIC_EVIDENCE", "측정확인",
        "Modern clean conservation-table diorama with several parchment fragments grouped by compatible animal-skin material signatures; Qumran limestone sample sits at one side while one verified outside-origin group is physically separated across a shallow terrain model, no species labels, no readable charts and no floating molecular icons",
        "Cell 2020: ancient parchment DNA groups fragments and suggests some manuscripts came from outside Qumran",
        ["fragment groups separated by animal-skin signature", "Qumran limestone reference sample", "one physically distant outside-origin group"],
        "Begin inside one parchment fibre, pull out to the grouped fragments, follow a world-space material route across the terrain and settle on the outside-origin group.",
        ["Classify fragments by ancient parchment DNA.", "Reveal that some biblical scrolls arrived from outside Qumran."],
        cam("parchment fibre bundle", "pull out over grouped fragments then across terrain", "outside-origin parchment group", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "IMMERSIVE_POV_DOLLY", "SECTION_DIVE", "Qumran and outside groups in one depth field", "2.4s scale transition to table", "6.5s route arrival"),
        modern=True,
        veo=graphic("ROUTE_PATH", "The route visualizes only the study's outside-origin inference and never names an unknown exact city", "thin parchment-coloured world-space ribbon following the terrain surface", "Qumran fragment group", ["terrain saddle"], "outside-origin group", "the destination fragment catches a restrained warm edge light"),
    ),
    spec(
        "5. 대이사야서", "ARTIFACT_MACRO", "측정확인",
        "A museum-scale Great Isaiah Scroll diorama unrolled as a very long stitched parchment sheet across a dark curved conservation surface, genuine beige animal skin with vertical stitched joins, 54 column-like blocks of fully unreadable dark ink texture and irregular lower damage; enough side depth to understand 7.34-metre length without generated numbers",
        "Israel Museum Great Isaiah Scroll: 7.34 metres, 54 columns, nearly complete 66 chapters",
        ["7.34-metre long stitched parchment sheet", "54 physical column blocks kept unreadable", "nearly complete Isaiah content with real edge damage"],
        "Fly low along the full stitched sheet at speed, pass seam after seam, rise to reveal the extraordinary length and settle on the final damaged edge.",
        ["Compare the manuscript contents and sharpen the scale.", "Reveal the 7.34-metre nearly complete Isaiah Scroll."],
        cam("first stitched sheet seam", "low flight along successive columns and seams", "far damaged terminal edge", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "IMMERSIVE_POV_DOLLY", "ORBIT_REVEAL", "entire long scroll readable as one object", "2.2s seam near-miss", "5.6s crane rise over full length"),
        modern=True,
        veo=graphic("DIMENSION_LINE", "The physical line expresses the published total length while exact numbers stay in narration and captions", "thin warm-ivory survey line lying beside the parchment edge without numerals", "first surviving edge", ["central stitched seam"], "far terminal edge", "small light ticks contact only the two real surviving ends"),
    ),
    spec(
        "5. 필사와 공동체 생활", "HISTORICAL_RECONSTRUCTION", "학술해석",
        "Split-depth Second Temple Judean scriptorium and communal-room diorama: a Levantine scribe copies onto parchment with reed pen while another corrects one existing ink line; beyond a stone divider, community members in plain linen follow a shared meal and calendar routine, all manuscript marks unreadable and no named sect claim",
        "Great Isaiah Scroll corrections, Community Rule and calendar documents",
        ["reed-pen copying and visible correction stroke", "plain Qumran communal meal setting", "calendar rhythm suggested by changing light, not labels"],
        "Follow the reed pen across one correction, pass through the stone divider, orbit the communal meal and accelerate through a day-to-night light change to the calendar routine.",
        ["Reveal textual differences and scribal corrections.", "Extend the manuscripts into daily community rules and calendar life."],
        cam("reed-pen tip at correction stroke", "across parchment then through divider into communal room", "community routine under changing light", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "SECTION_DIVE", "scribe and communal life aligned", "2.5s correction-rack-focus", "5.2s divider passage"),
        people=True, architecture=True,
    ),
    spec(
        "5. 기록의 세계 복원", "CUTAWAY", "학술해석",
        "Deep archaeological cutaway of Qumran daily life reconstructed only from document categories and settlement evidence: writing room, ritual water installation, shared meal room and cave storage zone occupy connected but distinct levels; translucent absence around the central owner figure remains unresolved, no crowded fantasy city",
        "IAA and LOC Qumran community evidence; identity remains bounded",
        ["writing room with parchment evidence", "stepped ritual-water installation", "shared meal and cave storage zones"],
        "Dive from one fragment into the cutaway writing room, travel through the water installation and shared meal, then pull back to reveal the whole recovered world while leaving the owner void unfilled.",
        ["Turn fragment evidence into a lived historical world.", "Preserve the boundary: the world returns, the exact owner does not."],
        cam("torn manuscript edge", "through writing room, stepped pool and meal room", "full Qumran-life cutaway", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "IMMERSIVE_POV_DOLLY", "SECTION_DIVE", "reconstructed world around unresolved centre", "2.0s fragment-to-room scale transition", "5.0s underwater-to-meal direction change"),
        people=True, architecture=True,
    ),
    spec(
        "6. 사해문서의 정체", "INVENTORY_TABLEAU", "학술해석",
        "Authoritative artifact-first diorama of the Dead Sea Scrolls corpus: biblical manuscript fragments, rule and calendar fragments, interpretation and prayer fragments, one Copper Scroll section and clay jar shards arranged as a coherent archaeological assemblage around the Great Isaiah Scroll; no single secret book and no religious propaganda",
        "IAA scroll content and Library of Congress Qumran Library",
        ["biblical and non-biblical fragments together", "Great Isaiah Scroll as one member not the whole", "Copper Scroll and jar context retained"],
        "Orbit rapidly from one supposed secret scroll outward as every document class enters the frame, then settle on the complete diverse corpus as the confirmed answer.",
        ["Reject the single secret-Bible idea.", "Identify a diverse Second Temple Jewish manuscript corpus."],
        cam("single closed scroll silhouette", "outward orbit across every artifact class", "complete corpus tableau", "CONTROLLED_ORBIT_REVEAL", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "all artifact classes together", "2.0s first category reveal", "5.0s orbit widens to corpus"),
        modern=True,
    ),
    spec(
        "6. 남은 주인과 은닉 이유", "DIAGRAM", "미확인",
        "Two-layer Qumran cave cutaway: upper layer shows scroll bundles distributed among several real cave chambers, lower layer shows provenance records torn away and early-market movement represented by empty wrapping and displaced fragment trays; owner and hiding motive remain an unfilled central space, no thief caricature and no claimed Roman-escape scene",
        "IAA and LOC: ownership, deposit history and exact hiding purpose remain unconfirmed",
        ["scroll deposits in separate cave chambers", "missing ownership and hiding record", "disturbed early provenance represented without accusation"],
        "Traverse the cave deposits, dive through the strata to the missing-record layer, follow displaced fragments toward the central void and stop before any owner or motive appears.",
        ["State what present methods cannot decide.", "Show why missing records and disturbed provenance block the owner and motive."],
        cam("wrapped bundle in upper cave", "through cave strata to displaced provenance trays", "unfilled owner-and-motive void", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "IMMERSIVE_POV_DOLLY", "SECTION_DIVE", "caves and missing record layer together", "2.5s strata dive", "6.0s evidence route breaks"),
        modern=True,
    ),
    spec(
        "6. 미래의 증거", "SCIENTIFIC_EVIDENCE", "측정확인",
        "Modern conservation-science diorama combining a parchment fibre sample, multispectral camera, neutral material-analysis instruments and an untouched newly found cave sediment layer sealed in situ; no futuristic hologram, no excavated new scroll claim and no readable computer screen",
        "Future-evidence scenario bounded by existing DNA, material analysis and provenance methods",
        ["parchment micro-sample and spectral camera", "neutral material-analysis instrument", "undisturbed cave sediment context"],
        "Move from fibre to spectral light, race along a physical analysis path into the untouched cave layer and settle on one sealed context boundary waiting to be tested.",
        ["Name the next evidence: better DNA and material analysis.", "Add the decisive condition of an undisturbed new cave context."],
        cam("parchment fibre under spectral light", "through analysis bay into sealed cave sediment section", "untouched context boundary", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "MACRO_PROBE", "SECTION_DIVE", "analysis and provenance context linked", "2.1s spectral-light sweep", "5.0s transition into cave strata"),
        modern=True,
        veo=graphic("SCAN_WAVE", "The scan visualizes analysis of already-present material and never invents a new manuscript", "restrained blue-white volumetric sheet with parchment-gold reflection", "parchment fibre", ["material sample", "cave sediment layer"], "sealed context boundary", "the boundary produces one soft reflected pulse and remains closed"),
    ),
    spec(
        "6. 두루마리의 여정", "SPATIAL_MAP", "학술해석",
        "Continuous deep diorama from a Second Temple parchment workshop through several anonymous hands and transport bundles to a Qumran cave mouth, with every stage physically present but separated by translucent gaps where evidence is missing; no named city, author or exact route claim",
        "Bounded future reconstruction goal: production, circulation and deposition sequence",
        ["anonymous parchment production stage", "multiple transfer hands without named identity", "Qumran cave deposition endpoint with evidence gaps"],
        "Follow one world-space route from prepared skin to copied scroll, pass hand to hand, bank through desert terrain and enter the cave, briefly darkening at every unknown gap before arrival.",
        ["Imagine reconstructing where each scroll was written and handled.", "Complete the route only as a future possibility ending at the cave."],
        cam("prepared parchment on workshop frame", "through anonymous hands across desert to cave mouth", "wrapped scroll at cave deposition point", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "IMMERSIVE_POV_DOLLY", "SECTION_DIVE", "whole possible journey in depth", "2.2s first handoff", "5.4s desert bank", "8.0s cave entry"),
        people=True, architecture=True,
        veo=graphic("ROUTE_PATH", "The route is explicitly a future reconstruction target and dims at every unsupported link", "thin parchment-gold physical ribbon following surfaces and hands", "prepared animal skin", ["copied scroll", "anonymous transfer bundle"], "Qumran cave deposit", "the ribbon fades across uncertainty gaps and brightens only at physical evidence anchors"),
    ),
    spec(
        "6. 남은 미스터리", "ARTIFACT_MACRO", "미확인",
        "Final hero diorama inside a quiet Qumran cave: one cracked cylindrical clay jar, one partially unrolled dark parchment scroll and several authentic fragments rest on limestone dust under a narrow warm shaft of light; beyond them multiple cave mouths recede into darkness, artifact razor-sharp against restrained background, no person, no text and no magical glow",
        "Synthesis: corpus identity confirmed, exact owner and hiding motive unresolved",
        ["cracked cylindrical Qumran jar", "dark parchment scroll with unreadable ink texture", "multiple cave mouths fading into unresolved depth"],
        "Begin moving at once through the last cave mouth, orbit the jar and parchment in a fast half-circle, push into the unreadable ink fibres, then pull back slowly until the artifact remains bright and the ownerless cave network falls dark.",
        ["Leave the owner and hiding reason as the precise mystery.", "Close on the artifact and the channel's buried-history signature."],
        cam("last cave-mouth limestone edge", "half-orbit around jar then macro push to parchment and pullback", "artifact hero against dark cave network", "CONTROLLED_ORBIT_REVEAL", "CRANE_ORBIT_REVEAL", "SURFACE_TO_INTERIOR", "jar and scroll isolated in light", "2.0s orbit direction change", "5.0s macro ink arrival", "7.2s slow final pullback"),
        modern=True,
    ),
]


if __name__ == "__main__":
    base.build()
