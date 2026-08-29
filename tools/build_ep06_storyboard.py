#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""EP06 안티키테라 기계 승인 TTS에서 고증 잠금 I2V 장면표와 Flow 입력을 만든다."""

from __future__ import annotations

import build_ep05_storyboard as base


base.EPISODE = base.ROOT / "산출물" / "EP06_안티키테라기계"
base.EPISODE_LABEL = "EP06 안티키테라 기계"
base.SCENE_COUNT_NOTE = "승인 대본의 21개 실측 TTS 의미 단위에서 파생했으며 고정 컷 수가 아니다."
base.STYLE = (
    "premium full-frame cinematic archaeological 3D diorama, unmistakably a museum-scale crafted "
    "miniature world and not live-action, immersive macro-lens depth cues, restrained tilt-shift, "
    "layered foreground-midground-background depth, physically based PBR materials, high-frequency "
    "microtexture and micro-displacement, sharp material separation, global illumination, high fidelity, "
    "4K source detail, 9:16 vertical composition"
)
base.ANCIENT_CIV = (
    "Hellenistic Greek Mediterranean world, 150-100 BCE, and a Roman-era merchant ship carrying Greek "
    "luxury cargo that sank near Antikythera around 70 BCE"
)
base.MODERN_CIV = (
    "documented Greek Antikythera recovery and research history: Symi sponge divers in 1900-1901, "
    "Athens museum examination from 1902, X-ray study in the 1970s and Anglo-Greek microfocus CT in 2005"
)
base.ANCIENT_PEOPLE = (
    "Hellenistic Greek astronomers and bronze instrument makers with eastern Mediterranean features, "
    "short curled dark hair or trimmed beards, undyed linen chitons, wool himatia or practical leather aprons"
)
base.MODERN_PEOPLE = (
    "Greek Symi sponge divers in 1900 with heavy canvas suits, copper helmets, air hoses, lead chest weights "
    "and weighted boots; later Greek museum conservators and Anglo-Greek researchers in period-correct clothing"
)
base.ANCIENT_ARCH = (
    "Hellenistic Greek limestone-and-timber bronze instrument workshop, Roman-era Mediterranean timber merchant ship, "
    "rocky Antikythera seabed, and restrained Athens museum or CT laboratory spaces only as the scene requires"
)
base.NEGATIVE = (
    "no Egyptian pharaoh imagery, no Chinese or East Asian gears, no Roman legionaries, no Viking ship, "
    "no medieval clock, no Renaissance workshop, no Victorian costume in ancient scenes, no steampunk fantasy, "
    "no electricity, no digital screen, no modern calculator, no intact shiny factory-made mechanism, "
    "no fabricated readable Greek text, no invented maker signature, no Archimedes portrait claim, "
    "no modern scuba tank in 1900, no treasure chest, no magical glow, no alien technology, no plastic toy surface, "
    "no ancient costume on modern researchers, no low-poly game asset, no gore, no watermark, no text, no labels, no letters"
)
base.LOCK_BASE = {
    "civilization": "Hellenistic Greek astronomy and bronze instrument making; Roman-era Antikythera shipwreck",
    "era": "150-100 BCE mechanism; circa 70 BCE shipwreck",
    "region": "Hellenistic eastern Mediterranean and the rocky seabed off Antikythera",
    "people_lock": "Hellenistic Greek artisans and astronomers with eastern Mediterranean features and period clothing",
    "forbidden_culture": ["Egyptian pharaoh", "East Asian", "medieval European", "Viking", "Renaissance", "steampunk", "alien"],
    "diorama_style": "CINEMATIC_ARCHAEOLOGICAL_DIORAMA",
    "material_fidelity": "PBR_MICROTEXTURE_HIGH_FIDELITY",
}
base.MODERN_LOCK_UPDATE = {
    "civilization": "Documented Greek Antikythera recovery and scientific research history",
    "era": "1900-1902 recovery and recognition; 1970s X-ray; 2005 microfocus CT",
    "people_lock": "Greek Symi sponge divers, museum conservators and Anglo-Greek researchers in exact period equipment",
}
base.COMPACT_ANCIENT_CONTEXT = "Hellenistic Greek world, 150-100 BCE, and the Antikythera merchant-ship context."
base.COMPACT_MODERN_CONTEXT = "Documented Greek Antikythera recovery and research from 1900 to 2005."


cam = base.cam
graphic = base.graphic
spec = base.spec


base.SPECS = [
    spec(
        "1. 바닷속 기계", "ARTIFACT_MACRO", "발굴확인",
        "Hero macro of Antikythera Fragment A: irregular opaque green-brown marine concretion, thin bronze plates crushed sideways into one layered mass, only a few broken triangular tooth tips peeking through white calcareous crust, half embedded in dark Aegean seabed stones, fully underwater, warm pin light against cold deep water, razor-sharp artifact silhouette; no clean circular gear face, intact exposed wheel, clock motif, museum glass or display case",
        "National Archaeological Museum surviving Fragment A and marine corrosion",
        ["Fragment A layered bronze mass", "triangular gear teeth in marine corrosion", "green-brown patina with white calcareous accretion"],
        "Start moving at once along the corroded edge, snap through a gap between bronze layers and widen to the entire dictionary-sized lump while suspended silt trails behind the object.",
        ["Reveal the corroded object underwater.", "Identify it as the Antikythera Mechanism."],
        cam("bright copper-green tooth edge", "through one real layer gap then around the concretion", "full Fragment A silhouette", "MACRO_PROBE_SETTLE", "MACRO_PROBE", "SURFACE_TO_INTERIOR", "whole fragment isolated from the seabed", "1.8s focus snap into the layer gap", "4.2s cold-to-warm light shift"),
    ),
    spec(
        "1. 바닷속 기계", "SCIENTIFIC_EVIDENCE", "측정확인",
        "Same real Fragment A on a matte conservation cradle in a dark museum-scale imaging bay, its marine crust still opaque outside but a prepared depth axis passes through visible bronze layers; no transparent fantasy object, no readable inscription, open side space for a world-space X-ray scan plane",
        "Nature 2006 and 2005 microfocus X-ray CT of the surviving fragments",
        ["same Fragment A outline", "27 surviving gears concentrated in Fragment A", "stacked thin bronze plates hidden by corrosion"],
        "Crash toward the real outer crust, let a thin blue-white scan wave travel through the physical depth, then follow the revealed triangular teeth inward without changing the fragment silhouette.",
        ["Pass the X-ray through the opaque fragment.", "Arrive at the hidden gear teeth."],
        cam("outer calcareous crust", "straight through the prepared depth axis between bronze layers", "cluster of hidden triangular teeth", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "MACRO_PROBE", "SURFACE_TO_INTERIOR", "outer fragment and inner gears aligned", "2.0s scan plane overtakes camera", "4.4s rack focus to inner teeth"),
        modern=True,
        veo=graphic("SCAN_WAVE", "CT reveals internal bronze layers and gear teeth but does not reconstruct missing parts", "one restrained blue-white volumetric scan sheet with fine copper reflections", "outer crust", ["first bronze plate", "buried gear layer"], "deepest surviving tooth cluster", "a short cool reflection runs around each already-present tooth"),
    ),
    spec(
        "1. 중심 질문", "MECHANISM", "학술해석",
        "A research reconstruction of the Antikythera Mechanism held inside a dark walnut rectangular case with front and back bronze dials, only verified surviving gear sectors rendered opaque and missing sectors rendered as faint neutral wireframe gaps; the real corroded fragments remain visible beside it to prevent certainty, no modern clock hands and no readable generated letters",
        "Nature 2006-2021 reconstructions separated from surviving evidence",
        ["rectangular wooden case", "front and back bronze dial plates", "opaque surviving sectors beside neutral missing gaps"],
        "Orbit from the real fragment toward the restrained research model, push between two meshing verified gears and stop before the unverified front gap as the unanswered question.",
        ["Ask what the mechanism calculated.", "Stop at the missing front evidence."],
        cam("real corroded fragment edge", "half-orbit toward the model then between two gears", "neutral missing front sector", "CONTROLLED_ORBIT_REVEAL", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "model and real fragment in the same frame", "1.6s scale shift from fragment to case", "3.0s stop before wireframe gap"),
    ),
    spec(
        "2. 1900년 발견", "DISCOVERY_ACTION", "발굴확인",
        "1900 Antikythera open-sea diorama with a Symi Greek sponge diver in an accurate heavy canvas suit, copper helmet, air hose, lead weights and weighted boots descending beside a rope toward a deep rocky seabed; dark blue Aegean water, surface boat only as a tiny silhouette above, no modern scuba tank or fins",
        "Greek Ministry of Culture and National Archaeological Museum recovery history",
        ["surface-supplied copper diving helmet", "air hose rising to a small boat", "steep rocky Antikythera seabed"],
        "Dive with the weighted boots immediately, follow the air hose through rising bubbles, bank under one rock ledge and arrive at the first timber and amphora remains.",
        ["Descend with the 1900 sponge diver.", "Reach the Roman-era wreck."],
        cam("copper helmet rim and air hose", "down the hose past bubbles and under a rock ledge", "wreck timber and first amphora", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "IMMERSIVE_POV_DOLLY", "SECTION_DIVE", "diver and wreck depth aligned", "2.0s bank under rock ledge", "4.0s bubble curtain crossing"),
        people=True, modern=True,
    ),
    spec(
        "2. 난파선 화물", "INVENTORY_TABLEAU", "발굴확인",
        "Deep rocky Antikythera shipwreck cargo field fully underwater with dark timber hull ribs, stacked transport amphorae, one fallen bronze statue, pale marble sculpture fragments and glass vessels partly buried in sediment; among them sits one unremarkable dictionary-sized corroded lump, composition leading from glamorous cargo to the dull lump; no museum, display case, pedestal, X-ray plate, cleaned gear or reconstructed mechanism",
        "Greek Ministry of Culture wreck cargo and Antikythera Mechanism Research Project",
        ["Roman merchant-ship timber ribs", "Greek bronze and marble sculpture cargo", "dictionary-sized corroded lump among amphorae"],
        "Race laterally across the bronze and marble cargo, drop between amphorae with the diver's gloved hand, then rack-focus from a bright statue face to the dull mechanism lump being lifted.",
        ["Show the valuable ship cargo.", "Find the overlooked corroded lump among it."],
        cam("bright bronze-statue surface", "across amphora stacks then downward between hull ribs", "dull mechanism concretion in a rope sling", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "ORBIT_REVEAL", "glamorous cargo and dull lump together", "2.4s drop between amphorae", "4.7s rack focus to mechanism"),
        people=True, modern=True,
    ),
    spec(
        "2. 1902년 반전", "DISCOVERY_REVEAL", "발굴확인",
        "Early-1902 Athens museum conservation-table diorama with the same marine concretion just naturally split along an existing fracture, one bronze gear edge and several triangular teeth visible inside; restrained Greek conservator hands and simple period tools stay outside the fracture, no destructive smashing and no fully cleaned mechanism",
        "National Archaeological Museum research timeline: gears recognized after recovery",
        ["existing split in the marine concretion", "first visible triangular bronze teeth", "same corroded outer patina"],
        "Push along a conservator's pointing finger to the fracture, cross the real opening seam, then orbit a few degrees around the first revealed gear teeth as dust falls away.",
        ["Hold the first dismissive impression.", "Reverse it when the gear teeth appear."],
        cam("conservator fingertip beside fracture", "through the existing opening seam into the bronze layers", "first complete visible tooth arc", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "MACRO_PROBE", "SURFACE_TO_INTERIOR", "fracture and gear arc in one frame", "1.9s crossing of the fracture", "4.0s orbit around tooth arc"),
        people=True, architecture=True, modern=True,
    ),
    spec(
        "3. 남은 실물", "INVENTORY_TABLEAU", "측정확인",
        "Museum conservation tableau of all 82 surviving Antikythera fragments arranged by size on a dark neutral surface, major fragments A through G physically prominent but without generated labels, the largest layered Fragment A at centre and many small marine-corroded chips surrounding it; no invented missing pieces",
        "Scientific Reports 2021: 82 fragments, about one third survives, 30 gears",
        ["82 surviving fragments", "major fragments A-G by real relative scale", "30 surviving gears embedded across the fragments"],
        "Crane rapidly from Fragment A across the full field, then let the verified fragment groups lift only a few centimetres with visible gaps and settle back into their surviving footprint.",
        ["Reveal the 82 fragments and one-third survival.", "Locate the surviving gear-bearing pieces."],
        cam("layered Fragment A centre", "crane across the full fragment field then short overhead orbit", "complete surviving-fragment footprint", "CONTROLLED_ORBIT_REVEAL", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "all fragments readable together", "2.1s rise to overhead", "5.0s direction reversal toward Fragment A"),
        modern=True,
        veo=graphic("EXPLODED_SEQUENCE", "Only the 82 surviving fragments separate; no missing piece is invented", "original corroded bronze surfaces with thin neutral conservation-shadow gaps", "Fragment A", ["major fragments B-G", "small fragment ring"], "full surviving footprint", "each fragment settles exactly over its original dark support shadow"),
    ),
    spec(
        "3. 앞면 작동", "MECHANISM", "학술해석",
        "Front-face research model in a dark walnut case with a bronze calendar ring, central Earth position, Sun pointer and a black-white Moon-phase sphere, all verified or inscription-supported elements rendered in aged matte bronze; missing planetary sectors remain empty, the side drive axis and interlocking gear train visible through an opened case edge",
        "Nature 2006 lunar-solar calendar and Moon anomaly reconstruction",
        ["front calendar ring", "Sun and Moon indicators", "black-white rotating Moon-phase sphere"],
        "Follow the drive axis as it turns once, race through the meshing gears, emerge at the front pointer and orbit the black-white Moon sphere as its phase changes in one continuous shot.",
        ["Turn the drive axis and move the Sun and Moon indicators.", "End on the changing Moon phase."],
        cam("side drive axis", "through meshing gears toward the front dial", "black-white Moon-phase sphere", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "IMMERSIVE_POV_DOLLY", "SURFACE_TO_INTERIOR", "front dial with working Moon phase", "2.2s gear-mesh direction change", "4.5s orbit around Moon sphere"),
        veo=graphic("FORCE_PATH", "The motion path follows inscription-supported gearing for Sun, Moon and lunar phase", "thin aged-copper contact pulses travelling only at real gear-tooth engagements", "side drive axis", ["largest verified gear", "Moon-anomaly gear pair"], "front Moon indicator", "a soft bronze pulse reaches the Moon sphere exactly as its lit half turns"),
    ),
    spec(
        "4. 뒷면 공개", "ARTIFACT_MACRO", "측정확인",
        "Back dial plate of the Antikythera research reconstruction turning into view, with two physically deep spiral grooves, the upper five-turn spiral and lower four-turn spiral clearly distinct through relief and shadow; aged bronze, tiny unreadable inscription texture only, no generated numerals or labels",
        "National Archaeological Museum and Nature 2008 back-dial structure",
        ["upper five-turn spiral", "lower four-turn spiral", "aged bronze back plate with fine inscription texture"],
        "Whip-orbit from the case edge to the back plate, plunge into the upper spiral groove and settle before its first full turn.",
        ["Reverse from the front to the back.", "Enter the upper spiral dial."],
        cam("right walnut case edge", "fast half-orbit to the back then into the upper groove", "first upper spiral turn", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "MACRO_PROBE", "SURFACE_TO_INTERIOR", "both spirals visible behind the upper groove", "0.9s whip to back plate", "1.6s dive into groove"),
    ),
    spec(
        "4. 달력과 식", "MECHANISM", "측정확인",
        "Oblique back-dial mechanism model with the upper five-turn Metonic spiral and lower four-turn Saros spiral both physically visible, a real pin-follower tracking each groove while interlocking verified gears turn behind the plate; no readable generated month names, eclipse glyphs shown only as tiny verified-style notches",
        "Nature 2008: 19-year 235-month Metonic dial and 223-month Saros eclipse-prediction dial",
        ["five-turn 235-month Metonic spiral", "four-turn 223-month Saros spiral", "real groove-following pointers linked to bronze gears"],
        "Track the upper pointer through two spiral turns, change direction through the visible rear gear train, descend to the lower pointer and accelerate along the Saros groove before a brief settle.",
        ["Follow the 19-year 235-month calendar.", "Descend to the 223-month eclipse-possibility cycle."],
        cam("upper Metonic pointer tip", "along the upper groove, through rear gears, then down the lower groove", "Saros eclipse-notch sector", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "MACRO_PROBE", "SURFACE_TO_INTERIOR", "upper and lower spiral relation", "2.4s transition through rear gears", "5.6s acceleration along lower groove"),
        veo=graphic("ROUTE_PATH", "The route follows the verified physical Metonic and Saros spiral scales without adding a modern calendar", "thin moon-silver route ribbon with subtle bronze edge reflections", "upper Metonic pointer", ["rear gear bridge", "lower Saros pointer"], "verified eclipse-notch sector", "one restrained cool pulse reaches the existing notch and fades"),
    ),
    spec(
        "4. 인간의 시간", "MECHANISM", "측정확인",
        "Complete back-face research model with the small four-year Panhellenic Games subsidiary dial beside the two great spirals, then a deep diorama background linking a Hellenistic festival stadium silhouette to the Moon and Sun above; the mechanical dial remains the foreground evidence and the human scene stays secondary",
        "Nature 2008 Olympiad and Panhellenic Games dial interpretation",
        ["four-year Panhellenic Games subsidiary dial", "two large astronomical spiral dials", "human festival cycle linked to celestial cycles"],
        "Snap from the small games dial to the upper celestial spiral, pull through the case into the festival horizon and crane back so mechanism, Moon and stadium occupy one depth axis.",
        ["Reveal the four-year games dial.", "Unite celestial cycles and human institutions in one box."],
        cam("small games-dial pointer", "across the back spirals then through the case toward the festival horizon", "mechanism-Moon-stadium depth axis", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "full timekeeping world in one frame", "2.0s snap to upper spiral", "5.0s crane pullback from festival"),
        people=True, architecture=True,
        veo=graphic("ROUTE_PATH", "The verified games dial connects a four-year human festival cycle with the mechanism's astronomical cycles", "restrained warm-gold route ribbon with tiny periodic pulses", "games-dial pointer", ["Metonic spiral edge", "Moon indicator"], "festival-stadium horizon", "a soft warm reflection lands on the stadium track and disappears"),
    ),
    spec(
        "5. 바다가 지운 것", "CONSERVATION", "발굴확인",
        "Time-layer conservation diorama of the same mechanism case collapsing only through documented material loss: walnut case darkens and disappears, bronze plates crack into the real 82-fragment footprint, green chloride corrosion and pale accretion grow over existing surfaces while the verified gears remain in their real positions; no violent explosion",
        "Observed two-millennia marine corrosion and fragmentary survival",
        ["lost wooden case", "real 82-fragment breakup", "green chloride and calcareous marine accretion"],
        "Begin on the intact research outline, accelerate through a controlled time transition as wood vanishes and corrosion travels along bronze, then reverse into the present Fragment A without inventing destruction events.",
        ["Show two millennia of material loss.", "Return to the unreadable present fragment."],
        cam("intact walnut case corner", "through the bronze layers during controlled corrosion growth", "present Fragment A surface", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "MACRO_PROBE", "SURFACE_TO_INTERIOR", "real surviving fragment after loss", "2.3s wood-to-bronze transition", "4.8s reverse into present crust"),
    ),
    spec(
        "5. 비파괴 조사", "SCIENTIFIC_EVIDENCE", "측정확인",
        "Split-era research-laboratory diorama built as one continuous physical room: a restrained 1970s X-ray station with film plates on the near side and a 2005 microfocus CT scanner with Fragment A securely mounted on the far side, period-correct Greek and Anglo-Greek researchers, no futuristic hologram and no generated readable screens",
        "National Archaeological Museum timeline and Nature 2006 CT campaign",
        ["1970s X-ray film examination", "2005 microfocus CT scanner", "same Fragment A on a conservation mount"],
        "Track from an X-ray film silhouette across the shared table, accelerate beside Fragment A into the CT ring and orbit the scanner as the beam rotates around the fixed artifact.",
        ["Pass from 1970s X-ray research to 2005 CT.", "Enter the fragment layer by layer."],
        cam("1970s X-ray film edge", "across the shared lab table into the CT scanner ring", "fixed Fragment A inside the CT axis", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "SURFACE_TO_INTERIOR", "artifact centered in CT ring", "2.2s period transition across table", "4.5s orbit with scanner beam"),
        people=True, architecture=True, modern=True,
        veo=graphic("SCAN_WAVE", "The physical scan visualizes measured internal density only", "one restrained blue-white rotating scan sheet with real attenuation through bronze", "1970s film silhouette", ["Fragment A outer crust", "first internal gear layer"], "deep CT gear stack", "measured bronze edges catch a narrow cool rim as the scan passes"),
    ),
    spec(
        "5. CT가 되찾은 구조", "SCIENTIFIC_EVIDENCE", "측정확인",
        "Exploded CT evidence model of Fragment A where only measured bronze layers and 27 surviving gears separate along the scan axis with visible gaps, thousands of tiny inscription traces shown as unreadable shallow marks on plate surfaces, and the Moon-anomaly pin-and-slot pair highlighted by material contrast rather than labels",
        "Nature 2006 and Scientific Reports 2021 CT findings",
        ["27 surviving gears in Fragment A", "hidden inscription traces inside corrosion", "Moon-anomaly pin-and-slot gear pair"],
        "Dive through the CT slice stack, let measured bronze layers separate in sequence, weave between two gear planes and settle on the pin-and-slot pair moving with restrained mechanical accuracy.",
        ["Reveal hidden letters and rear gear arrangement.", "Arrive at the mechanism for irregular lunar motion."],
        cam("first CT slice at the outer crust", "through separated measured layers between gear planes", "Moon-anomaly pin-and-slot pair", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "IMMERSIVE_POV_DOLLY", "SECTION_DIVE", "pin-and-slot pair inside the fragment", "2.0s layers separate", "4.2s weave between gear planes"),
        modern=True,
        veo=graphic("EXPLODED_SEQUENCE", "Only CT-measured layers and surviving gears separate; missing front parts stay absent", "semi-opaque measured bronze slices with blue-white CT edge light", "outer Fragment A slice", ["surviving gear layer", "inner inscription plate"], "pin-and-slot pair", "the real pin completes a short arc inside its measured slot"),
    ),
    spec(
        "6. 가장 오래된 컴퓨터", "MECHANISM", "학술해석",
        "Dignified complete research model turning inside its walnut case beside the much smaller real fragments, dense bronze gears transmitting one input into several astronomical outputs, camera angle emphasizing calculation through ratios rather than modern electronics; no keyboard, screen, electricity or digital symbols",
        "Nature 2006 description as the oldest known analogue computer",
        ["single mechanical input", "multiple interlocking bronze gear ratios", "calendar and astronomical output dials"],
        "Race from one turning input gear through three ratio changes, burst out to the moving front and back pointers, then pull back to compare the model with the real fragments.",
        ["Show why it is called an analogue computer.", "Stop before the missing front becomes the new problem."],
        cam("main input gear tooth contact", "through three interlocking ratios to the output dials", "model beside real fragments", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "IMMERSIVE_POV_DOLLY", "SURFACE_TO_INTERIOR", "calculation model and evidence together", "2.1s speed change at second ratio", "4.0s burst to output dials"),
    ),
    spec(
        "6. 사라진 앞면", "TEXT_RECORD", "문헌기록",
        "Macro on real front-cover inscription traces and surviving circular holes beside an intentionally empty front-model volume; Sun, Moon and five-planet functions are represented only by seven neutral unlabelled bronze orbit rings fading into transparency where evidence is missing, no invented Greek words or complete gearing",
        "Scientific Reports 2021 front-cover inscription and missing physical evidence",
        ["front-cover inscription traces", "surviving circular holes and bearing evidence", "transparent empty space for lost planetary gearing"],
        "Probe the inscription texture, snap to each surviving bearing hole, then orbit the seven neutral rings and stop at the transparent missing-gear volume rather than completing it.",
        ["Follow the inscription evidence for Sun, Moon and five planets.", "Reveal that the associated front gears are mostly gone."],
        cam("shallow front-cover inscription texture", "across surviving bearing holes then around neutral orbit rings", "transparent missing-gear volume", "MACRO_PROBE_SETTLE", "MACRO_PROBE", "ORBIT_REVEAL", "evidence and absence in one frame", "2.0s snap between holes", "4.1s orbit stops at empty volume"),
    ),
    spec(
        "6. 복원의 경계", "EXPLODED", "학술해석",
        "Side-by-side evidence reconstruction in one deep diorama: real corroded fragments and measured opaque gears on the left, proposed front planetary gear train in translucent desaturated bronze on the right, every speculative part floating with visible gaps and no claim of exact replica; dark neutral conservation backdrop",
        "Scientific Reports 2021 explicitly states its model cannot be claimed as a replica",
        ["real fragments and measured opaque gears", "translucent proposed front gear train", "visible physical separation between evidence and hypothesis"],
        "Slide along the opaque measured gears, cross one clear boundary plane into the translucent proposal, orbit once and reverse back to the real fragment for the evidence limit.",
        ["Show the logic of modern reconstruction.", "Separate research model from the lost original."],
        cam("opaque measured gear edge", "laterally across the evidence boundary into translucent gears", "real fragment after a reverse orbit", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "CRANE_ORBIT_REVEAL", "ORBIT_REVEAL", "opaque and translucent systems separated", "2.3s boundary crossing", "5.0s reverse to real fragment"),
        modern=True,
        veo=graphic("EXPLODED_SEQUENCE", "Opaque parts are measured evidence; translucent parts are a research proposal", "opaque corroded bronze versus translucent neutral bronze with a thin cool boundary plane", "real Fragment A", ["measured opaque gears", "evidence boundary"], "translucent proposed front system", "all proposed gears fade slightly while the real fragment remains solid"),
    ),
    spec(
        "7. 제작자와 정체", "SEALED_UNKNOWN", "미확인",
        "Unclaimed Hellenistic bronze workshop diorama with an unfinished gear sheet, dividers, files, a wooden geometry board and a blank unsigned bronze cover plate on the bench; no identifiable city monument, no portrait, no maker name, with faint distant silhouettes of Syracuse and Corinthian maritime routes kept abstract and secondary",
        "Corinthian calendar names suggest regions or traditions but no maker signature survives",
        ["blank unsigned bronze cover plate", "period hand-cut gear sheet", "geographically non-specific Hellenistic workshop"],
        "Approach the blank cover plate, orbit the period tools and stop at the untouched signature area; never enter a named city or reveal a maker's face.",
        ["State that the maker remains unknown.", "Turn from the blank signature to the mechanism's confirmed identity."],
        cam("blank bronze cover corner", "around dividers, files and gear sheet", "empty signature area", "BOUNDARY_APPROACH_STOP", "LOCKED_EVIDENCE_CAMERA", "BOUNDARY_STOP", "unsigned plate and tools", "2.4s rack focus from gear sheet to blank plate", "6.0s hard stop at missing signature"),
        architecture=True,
    ),
    spec(
        "7. 고대 컴퓨터의 결론", "HISTORICAL_RECONSTRUCTION", "학술해석",
        "Hellenistic Greek astronomer and bronze instrument maker together at a limestone workshop bench, turning a restrained research reconstruction while a physical armillary sky model and Moon-phase sphere move in exact mechanical relation; eastern Mediterranean features, linen chitons and leather apron, no named historical portrait",
        "Combined archaeological and inscription evidence for mechanized mathematical astronomy",
        ["period bronze gear workshop", "mechanical sky model", "astronomer and craftsperson collaborating"],
        "Follow the craftsperson's hand into the turning gear train, pass through the case and surge outward to the moving Moon and Sun model as the astronomer checks the sky.",
        ["Gather Sun, Moon, five planets, eclipses and games into one mechanical idea.", "Conclude that ancient Greeks placed celestial time inside gears."],
        cam("craftsperson hand on drive axis", "through the case gears toward the armillary model", "moving Moon and Sun against the workshop opening", "IMMEDIATE_ACCELERATE_FOLLOW_SETTLE", "CONTROLLED_DOCUMENTARY_HANDHELD_GIMBAL", "SURFACE_TO_INTERIOR", "people, mechanism and sky model aligned", "2.1s pass through case", "4.4s surge to sky model"),
        people=True, architecture=True,
    ),
    spec(
        "7. 사라진 핵심", "SPATIAL_MAP", "미확인",
        "Deep historical continuity diorama beginning with a Hellenistic workshop bench, following one restrained chain of bronze gear silhouettes toward a Roman merchant ship, then descending with the wreck into dark seawater where the chain physically breaks; beyond the break is empty darkness, not a claim that all knowledge vanished",
        "No confirmed workshop lineage or comparable surviving device connects the mechanism to later traditions",
        ["Hellenistic workshop starting point", "Antikythera merchant ship as transfer context", "broken evidence chain after the shipwreck"],
        "Track a bronze route from the workshop through the ship's cargo deck, dive with it into the water and stop exactly where the evidence chain breaks beside the corroded fragment.",
        ["Return to the lost front assembly and absent maker identity.", "Leave the 82 fragments as a larger unanswered question."],
        cam("unfinished workshop gear", "along the cargo deck then down through water", "broken route beside Fragment A", "RAPID_DOLLY_DIRECTION_CHANGE_SETTLE", "IMMERSIVE_POV_DOLLY", "SECTION_DIVE", "fragment at the end of documented evidence", "2.3s transition from bench to ship", "4.6s plunge and route break"),
        architecture=True,
        veo=graphic("ROUTE_PATH", "The route represents the known artifact journey only and stops where documentary and archaeological continuity is absent", "aged-bronze route ribbon that corrodes into dark particles underwater", "workshop gear", ["merchant-ship cargo deck", "waterline"], "Fragment A on the seabed", "the ribbon breaks into sediment at the real fragment and does not continue"),
    ),
    spec(
        "8. 남은 미스터리", "ARTIFACT_MACRO", "발굴확인",
        "Final high-contrast museum hero portrait of real Antikythera Fragment A and two smaller gear-bearing fragments on matte black conservation supports, warm pin light revealing copper-green patina and triangular teeth, cool rim light cleanly separating every artifact edge from a deep background hint of the ancient Aegean seabed, extremely sharp surface detail and no glass reflection",
        "National Archaeological Museum surviving Antikythera fragments",
        ["real Fragment A outline", "marine-corroded triangular teeth", "green-brown patina and calcareous accretion"],
        "Begin a restrained three-degree parallax arc, let warm pin light travel across the real teeth, then hold perfectly still on the surviving fragments for the final channel line.",
        ["Name the missing front design and maker as the bounded mystery.", "Return to the real fragments and hold for the channel closing line."],
        cam("lower copper-green Fragment A edge", "three-degree parallax arc across the supports", "full surviving-fragment hero grouping", "EVIDENCE_HOLD", "LOCKED_EVIDENCE_CAMERA", "NONE", "complete artifact closing portrait", "1.2s pin-light sweep", "2.5s full still hold"),
        modern=True,
        i2v_guard="Treat every supplied start-frame fragment as immutable: never redraw, clean, complete, sharpen, replace, rotate or animate any tooth, plate, crack, accretion or silhouette. Move only the camera by a tiny parallax arc and the raking light; if fidelity conflicts with motion, keep all artifacts frozen.",
    ),
]


if __name__ == "__main__":
    base.build()
