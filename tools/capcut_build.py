#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
[고대유물의 비밀] 5단계 — 캡컷 드래프트 생성기

캡컷을 손으로 조작하지 않는다. 검증된 기존 프로젝트를 <템플릿>으로 삼아
draft_content.json 을 다시 쓴다. 무협 파이프라인의 capcut_export.py 와 같은 전략이며,
그쪽 코드는 건드리지 않는다.

템플릿: "투탕카멘_고대유물의 비밀" (주인님이 직접 편집·검증한 프로젝트)
  → 자막 스타일(KCC간판체 12 / 획 0.08 / y=-0.206 / 페이드 인 0.25초),
    워터마크(우하단 크로마키), 캔버스(1080x1920 30fps)를 그대로 물려받는다.

바꾸는 것만 바꾼다:
  · 영상 세그먼트  ← clips/NNN.mp4 + TTS 길이에 맞춘 배속
  · 오디오 세그먼트 ← audio/NNN.mp3
  · 자막 세그먼트   ← 자막.json (한 줄 16자 이내로 이미 분할됨)
  · 워터마크 경로   ← 자산워터마크.png

사용법
  python tools/capcut_build.py 산출물/EP01_진시황릉 --check        # 준비물 점검만
  python tools/capcut_build.py 산출물/EP01_진시황릉                # 드래프트 생성
  python tools/capcut_build.py 산출물/EP01_진시황릉 --name "EP01 진시황릉"
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

from _config import load
from script_context_gate import validate_context_review

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

CFG = load()
ROOT = Path(__file__).resolve().parent.parent
DRAFT_ROOT = Path.home() / "AppData/Local/CapCut/User Data/Projects/com.lveditor.draft"
TEMPLATE = DRAFT_ROOT / CFG.get("캡컷.템플릿드래프트", "투탕카멘_고대유물의 비밀")
WATERMARK = ROOT / CFG.get("워터마크.파일", "자산워터마크.png")

US = 1_000_000            # 캡컷 시간 단위는 마이크로초
FPS = CFG.get("출력.fps", 30)
FRAME = US // FPS         # 33333
CAPTION_FADE_DURATION_US = int(float(CFG.get("자막.애니메이션.지속ms", 250)) * 1_000)
CAPTION_FADE_RESOURCE_ID = "7646371244257955092"
CAPTION_FADE_RESOURCE_PATH = (
    Path.home()
    / "AppData/Local/CapCut/User Data/Cache/effect"
    / CAPTION_FADE_RESOURCE_ID
    / "e6884981e7717e8d2951063ad1eadbdb"
)

# 템플릿의 음성 AI 소재는 실제 미디어와 무관한 이전 프로젝트 상태다.
# 이를 복제하면 CapCut이 열기/내보내기 때 음성 보정·노멀라이제이션 작업을
# 자동으로 다시 예약한다. 원본 ElevenLabs TTS와 Omni/Veo 현장음은 그대로 두고
# CapCut의 후처리 소재만 절대 상속하지 않는다.
FORBIDDEN_AUDIO_PROCESSING_BUCKETS = frozenset({
    "audio_effects",
    "realtime_denoises",
    "vocal_beautifys",
    "vocal_separations",
})
NO_AUDIO_PROCESSING_BUCKETS = frozenset({
    *FORBIDDEN_AUDIO_PROCESSING_BUCKETS,
    "loudnesses",
})


def uid() -> str:
    return str(uuid.uuid4()).upper()


def snap(us: int) -> int:
    """프레임 격자에 맞춘다. 무협 파이프라인과 같은 이유 — 안 맞추면 캡컷이 틈을 만든다."""
    return int(round(us / FRAME)) * FRAME


def probe(path: Path) -> float:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, check=True)
        return float(out.stdout.strip())
    except Exception:
        return 0.0


def has_audio_stream(path: Path) -> bool:
    """영상에 Omni/Veo가 만든 원본 효과음 스트림이 있는지 확인한다."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a:0",
             "-show_entries", "stream=index", "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, check=True,
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def db_to_linear(db: float) -> float:
    return math.pow(10.0, db / 20.0)


# ──────────────────────────────────────────────────────────────
# 템플릿에서 세그먼트를 복제한다.
# 세그먼트는 extra_material_refs 로 speed·canvas·sound_channel_mapping 등을
# 참조하므로, 참조된 소재까지 새 id 로 함께 복제해야 한다.
# ──────────────────────────────────────────────────────────────
class Cloner:
    def __init__(self, tpl: dict):
        self.tpl = tpl
        self.by_id: dict[str, tuple[str, dict]] = {}
        for bucket, items in tpl["materials"].items():
            if isinstance(items, list):
                for m in items:
                    if isinstance(m, dict) and "id" in m:
                        self.by_id[m["id"]] = (bucket, m)
        self.out: dict[str, list] = {k: [] for k in tpl["materials"] if isinstance(tpl["materials"][k], list)}

    def clone_extras(
        self,
        seg: dict,
        *,
        exclude_buckets: frozenset[str] = frozenset(),
    ) -> list[str]:
        new_refs = []
        for ref in seg.get("extra_material_refs", []):
            found = self.by_id.get(ref)
            if not found:
                continue
            bucket, m = found
            if bucket in exclude_buckets:
                continue
            m2 = copy.deepcopy(m)
            m2["id"] = uid()
            self.out.setdefault(bucket, []).append(m2)
            new_refs.append(m2["id"])
        return new_refs

    def set_speed(self, seg: dict, speed: float) -> None:
        """세그먼트의 speed 소재 값도 함께 맞춘다."""
        seg["speed"] = speed
        for ref in seg["extra_material_refs"]:
            for m in self.out.get("speeds", []):
                if m["id"] == ref:
                    m["speed"] = speed
                    if "curve_speed" in m:
                        m["curve_speed"] = None


def set_caption_fade_in(cloner: Cloner, refs: list[str]) -> None:
    """캡션 프로토타입이 물려준 등장 애니메이션을 채널 표준 페이드 인으로 고정한다.

    템플릿의 `하나씩` 33ms를 그대로 복제하지 않는다. 모든 캡션이 동일한
    CapCut 원생 페이드 인 리소스와 짧은 길이를 사용하므로 GUI에서도
    `페이드 인`으로 표시된다.
    """
    resource_path = str(CAPTION_FADE_RESOURCE_PATH).replace("\\", "/")
    for material in cloner.out.get("material_animations", []):
        if material.get("id") not in refs:
            continue
        material["type"] = "sticker_animation"
        material["animations"] = [{
            "id": CAPTION_FADE_RESOURCE_ID,
            "type": "in",
            "start": 0,
            "duration": CAPTION_FADE_DURATION_US,
            "path": resource_path,
            "platform": "all",
            "resource_id": CAPTION_FADE_RESOURCE_ID,
            "third_resource_id": "0",
            "source_platform": 1,
            "name": "페이드 인",
            "category_id": "ruchang",
            "category_name": "text",
            "panel": "",
            "material_type": "sticker",
            "anim_adjust_params": None,
            "request_id": "",
        }]
        material["multi_language_current"] = "none"


def set_loudness_normalization(
    cloner: Cloner,
    refs: list[str],
    *,
    duration_us: int,
    target_lufs: float,
) -> None:
    """원본 오디오에 CapCut 음량 노멀라이제이션만 켜고 새 분석을 요청한다."""
    for material in cloner.out.get("loudnesses", []):
        if material.get("id") not in refs:
            continue
        material["enable"] = True
        material["target_loudness"] = target_lufs
        material["time_range"] = {"start": 0, "duration": duration_us}
        material["file_id"] = ""
        material["loudness_param"] = None


def proto(tpl: dict, ttype: str, flag: int | None = None) -> dict:
    for tr in tpl["tracks"]:
        if tr["type"] == ttype and (flag is None or tr.get("flag") == flag):
            if tr["segments"]:
                return copy.deepcopy(tr["segments"][0])
    raise SystemExit(f"[에러] 템플릿에 {ttype}(flag={flag}) 세그먼트가 없습니다.")


def track_of(tpl: dict, ttype: str, flag: int | None = None) -> dict:
    for tr in tpl["tracks"]:
        if tr["type"] == ttype and (flag is None or tr.get("flag") == flag):
            return copy.deepcopy(tr)
    raise SystemExit(f"[에러] 템플릿에 {ttype}(flag={flag}) 트랙이 없습니다.")


def find_media(folder: Path, seq: int, exts: tuple[str, ...]) -> Path | None:
    for e in exts:
        p = folder / f"{seq:03d}{e}"
        if p.exists():
            return p
    return None


def normalize_caption_text(value: str) -> str:
    """대본·자막 동일성 비교용으로 공백과 문장부호만 제거한다."""
    return re.sub(r"[\s.,!?·…\"'“”‘’()]", "", value or "")


def validate_sync_document(document: dict, cues: list[dict], scenes: dict) -> list[str]:
    """CapCut에 넣기 전 forced-alignment 산출물을 다시 엄격하게 검증한다."""
    failures: list[str] = []
    synced = document.get("cues")
    if document.get("source") != "elevenlabs-forced-alignment":
        failures.append("자막_싱크.json source가 ElevenLabs forced alignment가 아님")
    if not isinstance(synced, list):
        return [*failures, "자막_싱크.json cues가 배열이 아님"]
    if document.get("count") != len(synced):
        failures.append("자막_싱크.json count와 실제 cues 개수가 다름")
    if len(synced) != len(cues):
        failures.append(f"실측 자막 {len(synced)}개 / 분할 자막 {len(cues)}개 — 전부 다시 정렬 필요")

    scene_keys = sorted(scenes, key=int)
    scene_ranges: dict[int, tuple[float, float]] = {}
    cursor = 0.0
    for key in scene_keys:
        duration = float(scenes[key].get("duration") or 0.0)
        scene_ranges[int(key)] = (cursor, cursor + duration)
        cursor += duration

    previous_start = -1.0
    previous_end = -1.0
    per_scene: dict[int, list[dict]] = {}
    for index, cue in enumerate(synced, 1):
        try:
            number = int(cue.get("n"))
            scene = int(cue.get("scene"))
            start = float(cue.get("start"))
            end = float(cue.get("end"))
        except (TypeError, ValueError):
            failures.append(f"실측 자막 {index}번의 번호·장면·시각 형식 오류")
            continue
        if number != index:
            failures.append(f"실측 자막 번호 불연속: 위치 {index}, n={number}")
        if start < previous_start - 0.001:
            failures.append(f"실측 자막 순서 역전: {number}번")
        if start < previous_end - 0.001:
            failures.append(f"실측 자막 겹침: {number}번")
        if end - start < 0.15:
            failures.append(f"실측 자막이 0.15초 미만: {number}번")
        previous_start, previous_end = start, end

        if scene not in scene_ranges:
            failures.append(f"실측 자막의 장면 번호가 TTS 길이표에 없음: {number}번/장면 {scene}")
        else:
            scene_start, scene_end = scene_ranges[scene]
            if start < scene_start - 0.001 or end > scene_end + 0.001:
                failures.append(f"실측 자막이 장면 경계를 이탈: {number}번/장면 {scene}")
            per_scene.setdefault(scene, []).append(cue)

        if index <= len(cues):
            expected = normalize_caption_text(cues[index - 1].get("raw") or cues[index - 1].get("text"))
            actual = normalize_caption_text(cue.get("raw") or cue.get("text"))
            if expected != actual:
                failures.append(f"분할 자막과 실측 자막 텍스트 불일치: {number}번")

    for key in scene_keys:
        scene = int(key)
        actual = "".join(
            normalize_caption_text(cue.get("raw") or cue.get("text"))
            for cue in per_scene.get(scene, [])
        )
        expected = normalize_caption_text(scenes[key].get("text"))
        if actual != expected:
            failures.append(f"실측 자막이 TTS 장면 원문과 다름: 장면 {scene}")
    return failures


# ──────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="캡컷 드래프트 생성기")
    ap.add_argument("episode", type=Path)
    ap.add_argument("--name", default=None, help="캡컷에 보일 프로젝트 이름")
    ap.add_argument("--check", action="store_true", help="준비물 점검만 하고 끝")
    ap.add_argument("--template", type=Path, default=TEMPLATE)
    ap.add_argument(
        "--draft-root",
        type=Path,
        default=DRAFT_ROOT,
        help="드래프트를 만들 루트. 실제 CapCut 폴더가 아닌 검수용 스테이징에도 생성 가능",
    )
    args = ap.parse_args()

    ep = args.episode.resolve()          # 캡컷은 절대경로만 인식한다
    name = args.name or f"{ep.name}_자동"
    audio_dir, clip_dir = ep / "audio", ep / "clips"
    dur_path, cue_path = audio_dir / "durations.json", ep / "자막.json"
    sync_path = ep / "자막_싱크.json"

    # ── 준비물 점검 ─────────────────────────────────────────
    problems: list[str] = []
    context = validate_context_review(ep / "01.대본.txt", ep / "01.문맥검수.json")
    problems.extend(f"문맥 QA: {failure}" for failure in context.failures)
    if not args.template.exists():
        problems.append(f"템플릿 없음: {args.template}")
    if not dur_path.exists():
        problems.append(f"durations.json 없음 — 3단계를 먼저 (경로 {dur_path})")
    if not cue_path.exists():
        problems.append(f"자막.json 없음 — tools/subtitle_split.py 를 먼저")
    if not sync_path.exists():
        problems.append("자막_싱크.json 없음 — tools/align_subtitles.py 강제 정렬을 먼저")
    if not WATERMARK.exists():
        problems.append(f"워터마크 없음: {WATERMARK}")

    scenes, cues, sync_document = {}, [], {}
    if dur_path.exists():
        scenes = json.loads(dur_path.read_text(encoding="utf-8"))["scenes"]
    if cue_path.exists():
        cues = json.loads(cue_path.read_text(encoding="utf-8"))["cues"]
    if sync_path.exists():
        try:
            sync_document = json.loads(sync_path.read_text(encoding="utf-8"))
            problems.extend(validate_sync_document(sync_document, cues, scenes))
        except (OSError, json.JSONDecodeError) as exc:
            problems.append(f"자막_싱크.json 오류: {exc}")

    missing_audio, missing_clip = [], []
    for k in sorted(scenes, key=int):
        n = int(k)
        if not find_media(audio_dir, n, (".mp3", ".wav", ".m4a")):
            missing_audio.append(n)
        if not find_media(clip_dir, n, (".mp4", ".mov", ".webm", ".mkv", ".jpg", ".png")):
            missing_clip.append(n)
    if missing_audio:
        problems.append(f"오디오 없는 장면: {missing_audio}")
    if missing_clip:
        problems.append(f"영상/이미지 없는 장면: {missing_clip}")

    print(f"\n에피소드 : {ep}")
    print(f"장면     : {len(scenes)}개   자막 : {len(cues)}개")
    print(f"템플릿   : {args.template.name}")
    if context.passed:
        print(f"문맥 QA  : PASS ({context.paragraphs}문단/{context.sentences}문장)")
    if problems:
        print("\n준비 안 된 항목:")
        for p in problems:
            print(f"  · {p}")
    else:
        print("\n준비물 이상 없음.")
    if args.check or problems:
        print()
        return 1 if problems else 0

    # ── 템플릿 로드 ─────────────────────────────────────────
    tpl = json.loads((args.template / "draft_content.json").read_text(encoding="utf-8"))
    cl = Cloner(tpl)

    v_proto = proto(tpl, "video", 0)
    a_proto = proto(tpl, "audio")
    t_proto = proto(tpl, "text")
    wm_track = track_of(tpl, "video", 2)

    v_track, a_track, t_track = track_of(tpl, "video", 0), track_of(tpl, "audio"), track_of(tpl, "text")
    for tr in (v_track, a_track, t_track):
        tr["id"] = uid()
        tr["segments"] = []
    # 워터마크 트랙은 세그먼트 1개를 그대로 재사용하므로 비우지 않는다.
    wm_track["id"] = uid()
    wm_track["segments"] = wm_track["segments"][:1]

    # ── 영상 + 오디오 ──────────────────────────────────────
    cursor = 0
    timeline: list[dict] = []
    media_registry: list[tuple[Path, str, int]] = []   # (경로, 종류, 길이us)
    used_media: list[Path] = []
    for k in sorted(scenes, key=int):
        n = int(k)
        tts = float(scenes[k]["duration"])
        dur = snap(int(tts * US))
        media = find_media(clip_dir, n, (".mp4", ".mov", ".webm", ".mkv", ".jpg", ".png"))
        is_img = media.suffix.lower() in (".jpg", ".png")
        native_audio = False if is_img else has_audio_stream(media)
        src = probe(media) if not is_img else tts
        speed = round(src / tts, 4) if (src > 0 and not is_img) else 1.0

        # 영상 소재
        vm = copy.deepcopy(tpl["materials"]["videos"][0])
        vm.update(id=uid(), path=str(media.resolve()).replace("\\", "/"),
                  material_name=media.name, local_material_id=uid(),
                  duration=int((src if src > 0 else tts) * US),
                  type="photo" if is_img else "video",
                  has_audio=native_audio,
                  width=CFG.get("출력.해상도",[1080,1920])[0],
                  height=CFG.get("출력.해상도",[1080,1920])[1])
        cl.out["videos"].append(vm)

        vs = copy.deepcopy(v_proto)
        vs["id"] = uid(); vs["material_id"] = vm["id"]
        vs["extra_material_refs"] = cl.clone_extras(
            v_proto,
            exclude_buckets=(
                FORBIDDEN_AUDIO_PROCESSING_BUCKETS
                if native_audio else NO_AUDIO_PROCESSING_BUCKETS
            ),
        )
        vs["target_timerange"] = {"start": cursor, "duration": dur}
        vs["source_timerange"] = {"start": 0, "duration": snap(int(dur * speed))}
        # Omni/Veo가 장면과 함께 만든 문·발걸음·바람·충격음은 버리지 않는다.
        # 나레이션을 가리지 않는 낮은 베드로 유지하고, 캡컷 AI 음성 처리는 금지한다.
        sfx_db = float(CFG.get("오디오.영상원음dB", -15.0))
        sfx_volume = db_to_linear(sfx_db) if native_audio else 0.0
        vs["volume"] = sfx_volume
        vs["last_nonzero_volume"] = sfx_volume
        if native_audio:
            set_loudness_normalization(
                cl,
                vs["extra_material_refs"],
                duration_us=vs["source_timerange"]["duration"],
                target_lufs=float(CFG.get("오디오.캡컷노멀라이즈LUFS", -23.0)),
            )
        cl.set_speed(vs, speed)
        v_track["segments"].append(vs)
        media_registry.append((media.resolve(), "video", int((src if src > 0 else tts) * US)))
        used_media.append(media.resolve())

        # 오디오 소재
        amedia = find_media(audio_dir, n, (".mp3", ".wav", ".m4a"))
        am = copy.deepcopy(tpl["materials"]["audios"][0])
        am.update(id=uid(), path=str(amedia.resolve()).replace("\\", "/"),
                  name=amedia.name, duration=int(tts * US), local_material_id=uid())
        cl.out["audios"].append(am)

        as_ = copy.deepcopy(a_proto)
        as_["id"] = uid(); as_["material_id"] = am["id"]
        as_["extra_material_refs"] = cl.clone_extras(
            a_proto, exclude_buckets=FORBIDDEN_AUDIO_PROCESSING_BUCKETS)
        as_["target_timerange"] = {"start": cursor, "duration": dur}
        as_["source_timerange"] = {"start": 0, "duration": dur}
        as_["speed"] = 1.0
        # 채널 수동 편집 표준: 음성 +5dB, 영상 원음 -15dB. 음성 보정은 쓰지 않고
        # TTS 트랙의 음량 노멀라이제이션만 -23 LUFS로 적용한다.
        narration_db = float(CFG.get("오디오.음성dB", 5.0))
        as_["volume"] = db_to_linear(narration_db)
        as_["last_nonzero_volume"] = as_["volume"]
        set_loudness_normalization(
            cl,
            as_["extra_material_refs"],
            duration_us=dur,
            target_lufs=float(CFG.get("오디오.캡컷노멀라이즈LUFS", -23.0)),
        )
        a_track["segments"].append(as_)
        media_registry.append((amedia.resolve(), "music", int(tts * US)))
        used_media.append(amedia.resolve())

        timeline.append({"scene": n, "start": cursor, "dur": dur,
                         "tts": tts, "speed": speed, "img": is_img})
        cursor += dur

    total = cursor

    # ── 자막 ────────────────────────────────────────────────
    # 검증을 통과한 ElevenLabs 실측 타임스탬프만 허용한다.
    # 글자수 비율 근사는 긴 영상에서 누적 드리프트를 만들므로 게시용 드래프트에서 금지한다.
    synced = sync_document["cues"]
    print(f"자막     : 실측 싱크 {len(synced)}개 (자막_싱크.json / strict PASS)")
    for c in synced:
        st = snap(int(c["start"] * US))
        en = snap(int(c["end"] * US))
        d = max(en - st, FRAME * 5)
        if st + d > total:
            d = max(total - st, FRAME * 3)
        tm = copy.deepcopy(tpl["materials"]["texts"][0])
        content = json.loads(tm["content"])
        content["text"] = c["text"]
        for stl in content.get("styles", []):
            stl["range"] = [0, len(c["text"])]
        tm["id"] = uid()
        tm["content"] = json.dumps(content, ensure_ascii=False)
        tm["base_content"] = c["text"]
        cl.out["texts"].append(tm)

        ts = copy.deepcopy(t_proto)
        ts["id"] = uid(); ts["material_id"] = tm["id"]
        ts["extra_material_refs"] = cl.clone_extras(t_proto)
        set_caption_fade_in(cl, ts["extra_material_refs"])
        ts["target_timerange"] = {"start": st, "duration": d}
        t_track["segments"].append(ts)

    # ── 워터마크 (템플릿 그대로, 경로와 길이만) ─────────────
    wseg = wm_track["segments"][0]
    wm_mat = None
    for m in tpl["materials"]["videos"]:
        if m["id"] == wseg["material_id"]:
            wm_mat = copy.deepcopy(m); break
    if wm_mat:
        wm_mat.update(id=uid(), path=str(WATERMARK.resolve()).replace("\\", "/"),
                      material_name=WATERMARK.name, local_material_id=uid())
        cl.out["videos"].append(wm_mat)
        wseg["id"] = uid(); wseg["material_id"] = wm_mat["id"]
        wseg["extra_material_refs"] = cl.clone_extras(
            wseg, exclude_buckets=NO_AUDIO_PROCESSING_BUCKETS)
        wseg["target_timerange"] = {"start": 0, "duration": total}
        wseg["source_timerange"] = None

    # ── 조립 ────────────────────────────────────────────────
    out = copy.deepcopy(tpl)
    out["id"] = uid()
    out["duration"] = total
    out["materials"] = {**tpl["materials"], **cl.out}
    out["tracks"] = [v_track, t_track, wm_track, a_track]

    out["group_container"] = None

    # ★ 템플릿 폴더를 통째로 복사하면 안 된다.
    #   draft.extra / key_value.json / Timelines/ 등 옛 프로젝트 상태가 남아
    #   캡컷이 프로젝트를 열지 못한다. 깨끗한 폴더에 3개 파일만 쓴다.
    draft_root = args.draft_root.resolve()
    dest = draft_root / name
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    (dest / "draft_content.json").write_text(
        json.dumps(out, ensure_ascii=False), encoding="utf-8")

    # ── draft_meta_info ──────────────────────────────────
    meta = json.loads((args.template / "draft_meta_info.json").read_text(encoding="utf-8"))
    now = int(time.time() * US)
    meta.update(draft_id=uid(), draft_name=name,
                draft_fold_path=str(dest).replace("\\", "/"),
                draft_root_path=str(draft_root).replace("\\", "/"),
                draft_cover="draft_cover.jpg",
                tm_draft_create=now, tm_draft_modified=now,
                tm_duration=total)
    meta["draft_timeline_materials_size_"] = sum(
        p.stat().st_size for p in used_media if p.exists())

    # 미디어 등록부(draft_materials)를 새로 채운다. 비워두면 캡컷이 소재를 못 잡는다.
    proto_media = None
    for blk in meta.get("draft_materials") or []:
        if blk.get("type") == 0 and blk.get("value"):
            proto_media = blk["value"][0]
            break
    reg = []
    for path, mtype, dur_us in media_registry:
        e = copy.deepcopy(proto_media) if proto_media else {}
        e.update({"id": uid(), "file_Path": str(path).replace("\\", "/"),
                  "metetype": mtype, "duration": int(dur_us),
                  "extra_info": path.name,
                  "width": CFG.get("출력.해상도",[1080,1920])[0] if mtype == "video" else 0,
                  "height": CFG.get("출력.해상도",[1080,1920])[1] if mtype == "video" else 0,
                  "create_time": -1, "import_time": int(time.time()),
                  "import_time_ms": now, "md5": ""})
        reg.append(e)
    for blk in meta.get("draft_materials") or []:
        blk["value"] = reg if blk.get("type") == 0 else []
    (dest / "draft_meta_info.json").write_text(
        json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    # ── 표지 (첫 클립에서 뽑는다. 템플릿 표지를 물려받으면 안 된다) ──
    first = next((p for p, k, _ in media_registry if k == "video"), None)
    if first:
        try:
            subprocess.run(["ffmpeg", "-y", "-i", str(first), "-vf",
                            "thumbnail,scale=480:-1", "-frames:v", "1",
                            str(dest / "draft_cover.jpg")],
                           capture_output=True, check=True)
        except Exception:
            pass

    # ── 보고 ────────────────────────────────────────────────
    print(f"\n{'장면':>4} {'시작':>8} {'길이':>7} {'TTS':>7} {'배속':>7}")
    print("─" * 40)
    for t in timeline:
        print(f"{t['scene']:>4} {t['start']/US:>7.2f}s {t['dur']/US:>6.2f}s "
              f"{t['tts']:>6.2f}s {t['speed']:>6.2f}x{'  (이미지)' if t['img'] else ''}")
    print("─" * 40)
    print(f"영상 {len(v_track['segments'])} · 오디오 {len(a_track['segments'])} · 자막 {len(t_track['segments'])}")
    print(f"총 길이 {total/US:.2f}초 ({int(total/US)//60}:{int(total/US)%60:02d})")
    if total / US >= 180:
        print("★ 3분을 넘습니다. 쇼츠 상한 초과.")
    print(f"\n드래프트 → {dest}")
    print("캡컷을 다시 열면 목록에 나타납니다. 배속·자막을 눈으로 확인한 뒤 내보내세요.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
