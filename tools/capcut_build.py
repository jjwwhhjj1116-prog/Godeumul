#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
[고대유물의 비밀] 5단계 — 캡컷 드래프트 생성기

캡컷을 손으로 조작하지 않는다. 검증된 기존 프로젝트를 <템플릿>으로 삼아
draft_content.json 을 다시 쓴다. 무협 파이프라인의 capcut_export.py 와 같은 전략이며,
그쪽 코드는 건드리지 않는다.

템플릿: "투탕카멘_고대유물의 비밀" (주인님이 직접 편집·검증한 프로젝트)
  → 자막 스타일(KCC간판체 12 / 획 0.08 / y=-0.206 / 하나씩 33ms),
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
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
DRAFT_ROOT = Path.home() / "AppData/Local/CapCut/User Data/Projects/com.lveditor.draft"
TEMPLATE = DRAFT_ROOT / "투탕카멘_고대유물의 비밀"
WATERMARK = ROOT / "자산워터마크.png"

US = 1_000_000            # 캡컷 시간 단위는 마이크로초
FPS = 30
FRAME = US // FPS         # 33333


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

    def clone_extras(self, seg: dict) -> list[str]:
        new_refs = []
        for ref in seg.get("extra_material_refs", []):
            found = self.by_id.get(ref)
            if not found:
                continue
            bucket, m = found
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


# ──────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="캡컷 드래프트 생성기")
    ap.add_argument("episode", type=Path)
    ap.add_argument("--name", default=None, help="캡컷에 보일 프로젝트 이름")
    ap.add_argument("--check", action="store_true", help="준비물 점검만 하고 끝")
    ap.add_argument("--template", type=Path, default=TEMPLATE)
    args = ap.parse_args()

    ep = args.episode
    name = args.name or f"{ep.name}_자동"
    audio_dir, clip_dir = ep / "audio", ep / "clips"
    dur_path, cue_path = audio_dir / "durations.json", ep / "자막.json"

    # ── 준비물 점검 ─────────────────────────────────────────
    problems: list[str] = []
    if not args.template.exists():
        problems.append(f"템플릿 없음: {args.template}")
    if not dur_path.exists():
        problems.append(f"durations.json 없음 — 3단계를 먼저 (경로 {dur_path})")
    if not cue_path.exists():
        problems.append(f"자막.json 없음 — tools/subtitle_split.py 를 먼저")
    if not WATERMARK.exists():
        problems.append(f"워터마크 없음: {WATERMARK}")

    scenes, cues = {}, []
    if dur_path.exists():
        scenes = json.loads(dur_path.read_text(encoding="utf-8"))["scenes"]
    if cue_path.exists():
        cues = json.loads(cue_path.read_text(encoding="utf-8"))["cues"]

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
    for k in sorted(scenes, key=int):
        n = int(k)
        tts = float(scenes[k]["duration"])
        dur = snap(int(tts * US))
        media = find_media(clip_dir, n, (".mp4", ".mov", ".webm", ".mkv", ".jpg", ".png"))
        is_img = media.suffix.lower() in (".jpg", ".png")
        src = probe(media) if not is_img else tts
        speed = round(src / tts, 4) if (src > 0 and not is_img) else 1.0

        # 영상 소재
        vm = copy.deepcopy(tpl["materials"]["videos"][0])
        vm.update(id=uid(), path=str(media).replace("\\", "/"),
                  material_name=media.name, local_material_id=uid(),
                  duration=int((src if src > 0 else tts) * US),
                  type="photo" if is_img else "video",
                  has_audio=False, width=1080, height=1920)
        cl.out["videos"].append(vm)

        vs = copy.deepcopy(v_proto)
        vs["id"] = uid(); vs["material_id"] = vm["id"]
        vs["extra_material_refs"] = cl.clone_extras(v_proto)
        vs["target_timerange"] = {"start": cursor, "duration": dur}
        vs["source_timerange"] = {"start": 0, "duration": snap(int(dur * speed))}
        vs["volume"] = 0.0
        cl.set_speed(vs, speed)
        v_track["segments"].append(vs)

        # 오디오 소재
        amedia = find_media(audio_dir, n, (".mp3", ".wav", ".m4a"))
        am = copy.deepcopy(tpl["materials"]["audios"][0])
        am.update(id=uid(), path=str(amedia).replace("\\", "/"),
                  name=amedia.name, duration=int(tts * US), local_material_id=uid())
        cl.out["audios"].append(am)

        as_ = copy.deepcopy(a_proto)
        as_["id"] = uid(); as_["material_id"] = am["id"]
        as_["extra_material_refs"] = cl.clone_extras(a_proto)
        as_["target_timerange"] = {"start": cursor, "duration": dur}
        as_["source_timerange"] = {"start": 0, "duration": dur}
        as_["speed"] = 1.0
        a_track["segments"].append(as_)

        timeline.append({"scene": n, "start": cursor, "dur": dur,
                         "tts": tts, "speed": speed, "img": is_img})
        cursor += dur

    total = cursor

    # ── 자막 ────────────────────────────────────────────────
    # 장면별 나레이션 길이 안에서 큐를 글자수 비율로 배분한다.
    by_scene: dict[int, list[dict]] = {}
    sent_to_scene: dict[int, int] = {}
    # 자막 큐의 문장 번호를 장면 순서에 비례해 배분(대본 문장 → 장면 매핑이 없을 때의 근사)
    tl_by_scene = {t["scene"]: t for t in timeline}
    per = max(1, len(cues) // max(1, len(timeline)))
    for i, c in enumerate(cues):
        sc = timeline[min(i // per, len(timeline) - 1)]["scene"]
        by_scene.setdefault(sc, []).append(c)

    for sc, group in by_scene.items():
        t = tl_by_scene[sc]
        chars = sum(max(1, len(c["text"])) for c in group)
        pos = t["start"]
        for j, c in enumerate(group):
            share = max(1, len(c["text"])) / chars
            d = snap(int(t["dur"] * share))
            if j == len(group) - 1:
                d = t["start"] + t["dur"] - pos
            if d < FRAME * 6:          # 0.2초 미만은 붙인다
                d = FRAME * 6

            tm = copy.deepcopy(tpl["materials"]["texts"][0])
            content = json.loads(tm["content"])
            content["text"] = c["text"]
            for st in content.get("styles", []):
                st["range"] = [0, len(c["text"])]
            tm["id"] = uid()
            tm["content"] = json.dumps(content, ensure_ascii=False)
            tm["base_content"] = c["text"]
            cl.out["texts"].append(tm)

            ts = copy.deepcopy(t_proto)
            ts["id"] = uid(); ts["material_id"] = tm["id"]
            ts["extra_material_refs"] = cl.clone_extras(t_proto)
            ts["target_timerange"] = {"start": pos, "duration": d}
            t_track["segments"].append(ts)
            pos += d

    # ── 워터마크 (템플릿 그대로, 경로와 길이만) ─────────────
    wseg = wm_track["segments"][0]
    wm_mat = None
    for m in tpl["materials"]["videos"]:
        if m["id"] == wseg["material_id"]:
            wm_mat = copy.deepcopy(m); break
    if wm_mat:
        wm_mat.update(id=uid(), path=str(WATERMARK).replace("\\", "/"),
                      material_name=WATERMARK.name, local_material_id=uid())
        cl.out["videos"].append(wm_mat)
        wseg["id"] = uid(); wseg["material_id"] = wm_mat["id"]
        wseg["extra_material_refs"] = cl.clone_extras(wseg)
        wseg["target_timerange"] = {"start": 0, "duration": total}
        wseg["source_timerange"] = None

    # ── 조립 ────────────────────────────────────────────────
    out = copy.deepcopy(tpl)
    out["id"] = uid()
    out["duration"] = total
    out["materials"] = {**tpl["materials"], **cl.out}
    out["tracks"] = [v_track, t_track, wm_track, a_track]

    dest = DRAFT_ROOT / name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(args.template, dest, ignore=shutil.ignore_patterns(
        "draft_content.json*", "template-*.tmp", "*.bak"))
    (dest / "draft_content.json").write_text(
        json.dumps(out, ensure_ascii=False), encoding="utf-8")

    meta_p = dest / "draft_meta_info.json"
    if meta_p.exists():
        meta = json.loads(meta_p.read_text(encoding="utf-8"))
        now = int(time.time() * US)
        meta.update(draft_id=uid(), draft_name=name,
                    draft_fold_path=str(dest).replace("\\", "/"),
                    draft_root_path=str(DRAFT_ROOT).replace("\\", "/"),
                    tm_draft_create=now, tm_draft_modified=now,
                    tm_duration=total)
        meta_p.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")

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
