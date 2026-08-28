#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
[고대유물의 비밀] 5단계 검수 — 캡컷 드래프트 자가 점검

"올려도 되는 영상인가"를 사람 눈 대신 숫자로 답한다.
영상·나레이션·자막이 같은 시간축 위에 정확히 놓였는지 전수 검사한다.

검사 항목
  A 캔버스·길이     1080x1920 / 30fps / 3분 미만
  B 트랙 구성       영상·나레이션·자막·워터마크가 다 있는가
  C 영상 타임라인   틈·겹침·배속 안전범위
  D 나레이션 축     틈·겹침·durations.json 과 일치
  E ★ 영상↔음성 싱크  컷 N 화면과 컷 N 나레이션이 같은 구간에 있는가
  F ★ 자막 싱크      자막이 제 장면 나레이션 안에 들어가는가 (강제정렬 실측 대조)
  G 자막 표시        표시 시간·글자수·읽기 속도
  H 참조 무결성     세그먼트가 가리키는 소재가 전부 존재하는가
  I 파일 실재       경로의 미디어가 디스크에 실제로 있는가
  J 마무리          끝 프레임이 검게 끝나지 않는가, 오디오가 잘리지 않는가

사용법
  python tools/verify_draft.py 산출물/EP01_진시황릉
  python tools/verify_draft.py 산출물/EP01_진시황릉 --드래프트 "EP01 진시황릉"
  python tools/verify_draft.py 산출물/EP01_진시황릉 -v      # 컷별 전체 표
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _config import load

CFG = load()
US = 1_000_000                       # 캡컷은 마이크로초 단위
DRAFT_ROOT = Path.home() / "AppData/Local/CapCut/User Data/Projects/com.lveditor.draft"
FRAME = US / 30                      # 33,333us. 1프레임 이내 오차는 정상


class Report:
    """통과/경고/실패를 모아 마지막에 한 번에 낸다."""

    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str, str]] = []

    def ok(self, sec, name, detail=""):
        self.rows.append(("OK", sec, name, detail))

    def warn(self, sec, name, detail=""):
        self.rows.append(("주의", sec, name, detail))

    def fail(self, sec, name, detail=""):
        self.rows.append(("실패", sec, name, detail))

    @property
    def fails(self):
        return [r for r in self.rows if r[0] == "실패"]

    @property
    def warns(self):
        return [r for r in self.rows if r[0] == "주의"]

    def dump(self):
        mark = {"OK": "  o ", "주의": "  ! ", "실패": "  X "}
        cur = None
        for st, sec, name, detail in self.rows:
            if sec != cur:
                print(f"\n[{sec}]")
                cur = sec
            line = f"{mark[st]}{name}"
            if detail:
                line += f"  —  {detail}"
            print(line)


def fmt(us: float) -> str:
    s = us / US
    return f"{int(s // 60)}:{s % 60:05.2f}"


def seg_range(s) -> tuple[int, int]:
    t = s["target_timerange"]
    return t["start"], t["start"] + t["duration"]


def check_track_flow(segs, label, rep, sec, gap_tol=FRAME):
    """한 트랙 안의 틈·겹침·순서를 본다."""
    rs = [seg_range(s) for s in segs]
    if rs != sorted(rs):
        rep.fail(sec, f"{label} 순서", "타임라인 순서가 뒤섞여 있다")
        rs = sorted(rs)
    gaps, overlaps = [], []
    for i, ((_, e), (s2, _)) in enumerate(zip(rs, rs[1:]), 1):
        d = s2 - e
        if d > gap_tol:
            gaps.append((i, d))
        elif d < -gap_tol:
            overlaps.append((i, -d))
    if gaps:
        worst = max(gaps, key=lambda g: g[1])
        rep.fail(sec, f"{label} 틈", f"{len(gaps)}곳 · 최대 {worst[1]/1000:.0f}ms (컷{worst[0]} 앞)")
    else:
        rep.ok(sec, f"{label} 틈", "없음")
    if overlaps:
        worst = max(overlaps, key=lambda g: g[1])
        rep.fail(sec, f"{label} 겹침", f"{len(overlaps)}곳 · 최대 {worst[1]/1000:.0f}ms")
    else:
        rep.ok(sec, f"{label} 겹침", "없음")
    return rs


def main() -> int:
    ap = argparse.ArgumentParser(description="캡컷 드래프트 자가 검수")
    ap.add_argument("episode", type=Path)
    ap.add_argument("--드래프트", dest="draft", default=None)
    ap.add_argument("-v", "--verbose", action="store_true", help="컷별 전체 표")
    args = ap.parse_args()

    ep = args.episode.resolve()
    # capcut_build 가 만드는 이름과 같은 규칙을 쓴다. 이름이 갈리면
    # 낡은 드래프트를 검수하고 통과했다고 착각하게 된다.
    name = args.draft or f"{ep.name}_자동"
    draft = DRAFT_ROOT / name
    if not draft.exists():
        stem = ep.name.split("_")[0]
        cands = [p.name for p in DRAFT_ROOT.iterdir() if p.is_dir() and stem in p.name]
        sys.exit(f"[에러] 드래프트가 없습니다: {draft}\n"
                 f"       후보: {cands}\n"
                 f"       --드래프트 로 지정하세요.")

    d = json.loads((draft / "draft_content.json").read_text(encoding="utf-8"))
    rep = Report()

    print(f"\n에피소드 : {ep.name}")
    print(f"드래프트 : {draft}")

    # ── A. 캔버스 · 길이 ────────────────────────────────
    cv = d.get("canvas_config", {})
    want_w, want_h = CFG.get("출력.해상도", [1080, 1920])
    if (cv.get("width"), cv.get("height")) == (want_w, want_h):
        rep.ok("A 캔버스", "해상도", f"{cv['width']}x{cv['height']}")
    else:
        rep.fail("A 캔버스", "해상도", f"{cv.get('width')}x{cv.get('height')} (기대 {want_w}x{want_h})")

    fps = d.get("fps")
    want_fps = CFG.get("출력.fps", 30)
    (rep.ok if fps == want_fps else rep.fail)("A 캔버스", "프레임레이트", f"{fps}fps")

    total = d.get("duration", 0)
    if total < 180 * US:
        rep.ok("A 캔버스", "전체 길이", f"{fmt(total)} (쇼츠 3분 미만)")
    else:
        rep.fail("A 캔버스", "전체 길이", f"{fmt(total)} — 3분을 넘어 쇼츠로 안 잡힌다")

    if d.get("group_container") is not None:
        rep.fail("A 캔버스", "group_container", "None 이어야 한다 (템플릿 잔재)")
    else:
        rep.ok("A 캔버스", "group_container", "None")

    # ── B. 트랙 구성 ────────────────────────────────────
    tracks = d["tracks"]
    vids = [t for t in tracks if t["type"] == "video"]
    auds = [t for t in tracks if t["type"] == "audio"]
    txts = [t for t in tracks if t["type"] == "text"]
    if not (vids and auds and txts):
        sys.exit("[에러] 영상·오디오·자막 트랙 중 없는 게 있습니다.")

    main_v = max(vids, key=lambda t: len(t["segments"]))
    wm = [t for t in vids if t is not main_v]
    aud = max(auds, key=lambda t: len(t["segments"]))
    txt = max(txts, key=lambda t: len(t["segments"]))

    n_cut, n_aud, n_sub = len(main_v["segments"]), len(aud["segments"]), len(txt["segments"])
    rep.ok("B 트랙", "구성", f"영상 {n_cut}컷 · 나레이션 {n_aud}개 · 자막 {n_sub}개")
    if n_cut == n_aud:
        rep.ok("B 트랙", "컷↔나레이션 개수", f"{n_cut} = {n_aud}")
    else:
        rep.fail("B 트랙", "컷↔나레이션 개수", f"영상 {n_cut} ≠ 음성 {n_aud}")

    if wm and wm[0]["segments"]:
        w = wm[0]["segments"][0]
        ws, we = seg_range(w)
        cover = (we - ws) / total * 100
        det = f"{fmt(ws)}~{fmt(we)} (전체의 {cover:.0f}%)"
        (rep.ok if cover > 95 else rep.warn)("B 트랙", "워터마크", det)
    else:
        rep.warn("B 트랙", "워터마크", "트랙이 없다")

    # ── C. 영상 타임라인 ────────────────────────────────
    vsegs = sorted(main_v["segments"], key=lambda s: s["target_timerange"]["start"])
    vr = check_track_flow(vsegs, "영상", rep, "C 영상")

    if vr[0][0] == 0:
        rep.ok("C 영상", "시작", "0초에서 시작")
    else:
        rep.fail("C 영상", "시작", f"{fmt(vr[0][0])} 부터 — 앞이 비어 있다")

    speeds = [s.get("speed", 1.0) for s in vsegs]
    lo, hi = CFG.get("영상.배속_안전", [0.75, 3.0])
    bad = [(i, sp) for i, sp in enumerate(speeds, 1) if not (lo <= sp <= hi)]
    if bad:
        rep.fail("C 영상", "배속 안전범위",
                 "  ".join(f"컷{i} {sp:.2f}x" for i, sp in bad[:6]))
    else:
        rep.ok("C 영상", "배속 안전범위",
               f"{min(speeds):.2f}~{max(speeds):.2f}x (허용 {lo}~{hi})")

    # 소스를 다 못 쓰고 잘라낸 컷이 있는지 (원본보다 길게 늘린 건 없는지)
    over = []
    for i, s in enumerate(vsegs, 1):
        src = s.get("source_timerange") or {}
        need = s["target_timerange"]["duration"] * s.get("speed", 1.0)
        if src.get("duration") and need - src["duration"] > FRAME:
            over.append(i)
    if over:
        rep.fail("C 영상", "소스 길이", f"원본보다 길게 쓴 컷 {over[:6]}")
    else:
        rep.ok("C 영상", "소스 길이", "전 컷 원본 범위 안")

    # ── D. 나레이션 축 ──────────────────────────────────
    asegs = sorted(aud["segments"], key=lambda s: s["target_timerange"]["start"])
    ar = check_track_flow(asegs, "나레이션", rep, "D 나레이션")

    man_p = ep / "audio" / "durations.json"
    scenes = {}
    if man_p.exists():
        scenes = json.loads(man_p.read_text(encoding="utf-8"))["scenes"]
        keys = sorted(scenes, key=int)
        if len(keys) == len(asegs):
            diffs = []
            for i, (k, (s0, e0)) in enumerate(zip(keys, ar), 1):
                want = int(round(scenes[k]["duration"] * US))
                gap = abs((e0 - s0) - want)
                if gap > FRAME:
                    diffs.append((i, gap))
            if diffs:
                rep.fail("D 나레이션", "실측 길이 일치",
                         f"{len(diffs)}컷 불일치 · 최대 {max(d for _, d in diffs)/1000:.0f}ms")
            else:
                rep.ok("D 나레이션", "실측 길이 일치", "전 컷 1프레임 이내")
        else:
            rep.fail("D 나레이션", "실측 길이 일치",
                     f"durations.json {len(keys)}개 ≠ 트랙 {len(asegs)}개")
        tot_tts = sum(scenes[k]["duration"] for k in keys)
        rep.ok("D 나레이션", "총 나레이션", f"{tot_tts:.2f}초 ({fmt(tot_tts*US)})")
    else:
        rep.warn("D 나레이션", "실측 대조", "durations.json 이 없어 건너뜀")

    import math
    vols = {round(s.get("volume", 1.0), 4) for s in asegs}
    want_db = float(CFG.get("오디오.음성dB", 5.0))
    want = 10 ** (want_db / 20)
    if len(vols) > 1:
        rep.fail("D 나레이션", "볼륨", f"컷마다 다르다: {sorted(vols)}")
    else:
        v = vols.pop()
        db = 20 * math.log10(v) if v > 0 else -99
        if abs(v - want) < 0.01:
            rep.ok("D 나레이션", "볼륨", f"{v} ({db:+.1f}dB)")
        else:
            rep.fail("D 나레이션", "볼륨",
                     f"{v} ({db:+.1f}dB) — 채널 표준 {want_db:+.1f}dB와 다르다")

    # 실제 파일의 라우드니스·트루피크 (audio_normalize 가 남긴 기록)
    ln_p = ep / "audio" / "loudness.json"
    if ln_p.exists():
        ln = json.loads(ln_p.read_text(encoding="utf-8"))
        a = ln.get("after", {})
        i, tp = a.get("lufs"), a.get("true_peak")
        tp_max = CFG.get("오디오.트루피크상한dBFS", -1.5)
        tgt = CFG.get("오디오.목표LUFS", -16.0)
        if tp is not None and tp > tp_max + 0.2:
            rep.fail("D 나레이션", "트루피크", f"{tp:+.1f} dBFS — 상한 {tp_max} 초과 (클리핑)")
        else:
            rep.ok("D 나레이션", "트루피크", f"{tp:+.1f} dBFS (상한 {tp_max})")
        if i is not None and abs(i - tgt) > 1.5:
            rep.warn("D 나레이션", "라우드니스", f"{i:.1f} LUFS (목표 {tgt})")
        else:
            rep.ok("D 나레이션", "라우드니스", f"{i:.1f} LUFS (목표 {tgt})")
    else:
        rep.warn("D 나레이션", "라우드니스", "loudness.json 없음 — audio_normalize 를 안 돌렸다")

    # ── E. ★ 영상 ↔ 나레이션 싱크 ───────────────────────
    if len(vr) == len(ar):
        drift = [(i, abs(v[0] - a[0]), abs(v[1] - a[1]))
                 for i, (v, a) in enumerate(zip(vr, ar), 1)]
        worst_s = max(drift, key=lambda x: x[1])
        worst_e = max(drift, key=lambda x: x[2])
        off = [x for x in drift if x[1] > FRAME or x[2] > FRAME]
        if off:
            rep.fail("E 싱크", "컷↔나레이션 정렬",
                     f"{len(off)}컷 어긋남 · 최대 시작 {worst_s[1]/1000:.0f}ms / 끝 {worst_e[2]/1000:.0f}ms")
            for i, ds, de in off[:8]:
                rep.fail("E 싱크", f"  컷{i}", f"시작 {ds/1000:+.0f}ms · 끝 {de/1000:+.0f}ms")
        else:
            rep.ok("E 싱크", "컷↔나레이션 정렬",
                   f"전 {len(drift)}컷 1프레임 이내 (최대 {worst_e[2]/1000:.0f}ms)")
    else:
        rep.fail("E 싱크", "컷↔나레이션 정렬", "개수가 달라 대조 불가")

    if abs(vr[-1][1] - ar[-1][1]) <= FRAME:
        rep.ok("E 싱크", "끝 지점", f"영상·음성 모두 {fmt(vr[-1][1])}")
    else:
        rep.warn("E 싱크", "끝 지점",
                 f"영상 {fmt(vr[-1][1])} vs 음성 {fmt(ar[-1][1])}")

    # ── F. ★ 자막 싱크 ──────────────────────────────────
    tsegs = sorted(txt["segments"], key=lambda s: s["target_timerange"]["start"])
    tr = [seg_range(s) for s in tsegs]

    bad_order = sum(1 for a, b in zip(tr, tr[1:]) if b[0] < a[0])
    ov = [(i, a[1] - b[0]) for i, (a, b) in enumerate(zip(tr, tr[1:]), 1) if b[0] < a[1] - 1]
    (rep.ok if not bad_order else rep.fail)("F 자막", "순서", f"역전 {bad_order}건")
    if ov:
        rep.fail("F 자막", "겹침", f"{len(ov)}곳 · 최대 {max(o for _, o in ov)/1000:.0f}ms")
    else:
        rep.ok("F 자막", "겹침", "없음")

    # 자막이 자기 장면의 나레이션 구간 밖으로 나갔는가
    sync_p = ep / "자막_싱크.json"
    if sync_p.exists():
        cues = json.loads(sync_p.read_text(encoding="utf-8"))["cues"]
        rep.ok("F 자막", "타이밍 출처", "ElevenLabs 강제정렬 실측 (자막_싱크.json)")
        if len(cues) == len(tr):
            err = [abs(int(round(c["start"] * US)) - t[0]) for c, t in zip(cues, tr)]
            worst = max(err)
            if worst <= FRAME:
                rep.ok("F 자막", "드래프트↔실측 일치",
                       f"전 {len(cues)}개 1프레임 이내 (최대 {worst/1000:.0f}ms)")
            else:
                rep.fail("F 자막", "드래프트↔실측 일치",
                         f"최대 {worst/1000:.0f}ms 차이 · {sum(1 for e in err if e > FRAME)}개")
        else:
            rep.fail("F 자막", "드래프트↔실측 개수", f"싱크 {len(cues)} ≠ 트랙 {len(tr)}")

        # 장면 경계를 넘어가는 자막
        if scenes:
            keys = sorted(scenes, key=int)
            bounds, acc = {}, 0.0
            for k in keys:
                bounds[int(k)] = (acc, acc + scenes[k]["duration"])
                acc += scenes[k]["duration"]
            spill = []
            for c in cues:
                b = bounds.get(c["scene"])
                if not b:
                    continue
                if c["start"] < b[0] - 0.034 or c["end"] > b[1] + 0.034:
                    spill.append(c["n"])
            if spill:
                rep.fail("F 자막", "장면 경계 이탈",
                         f"{len(spill)}개 — 나레이션이 끝났는데 자막이 남는다 {spill[:8]}")
            else:
                rep.ok("F 자막", "장면 경계", "전 자막이 제 나레이션 안에 있다")
    else:
        rep.fail("F 자막", "타이밍 출처",
                 "자막_싱크.json 이 없다 — 글자수 비율 근사치일 가능성. align_subtitles 를 돌릴 것")
        cues = []

    if tr[0][0] < 0.05 * US:
        rep.warn("F 자막", "첫 자막", f"{tr[0][0]/1000:.0f}ms — 시작하자마자 뜬다")
    else:
        rep.ok("F 자막", "첫 자막", fmt(tr[0][0]))
    if tr[-1][1] <= total + FRAME:
        rep.ok("F 자막", "마지막 자막", f"{fmt(tr[-1][1])} (영상 끝 안쪽)")
    else:
        rep.fail("F 자막", "마지막 자막", f"{fmt(tr[-1][1])} — 영상 끝을 넘어간다")

    # ── G. 자막 표시 ────────────────────────────────────
    tmat = {m["id"]: m for m in d["materials"].get("texts", [])}
    texts = []
    for s in tsegs:
        m = tmat.get(s["material_id"], {})
        try:
            texts.append(json.loads(m.get("content", "{}")).get("text", ""))
        except json.JSONDecodeError:
            texts.append(m.get("content", ""))

    lens = [len(t) for t in texts if t]
    if lens:
        mx = CFG.get("자막.최대글자수", 16)
        over_len = [(i, t) for i, t in enumerate(texts, 1) if len(t) > mx]
        if over_len:
            rep.fail("G 자막표시", "글자수",
                     f"{len(over_len)}개가 {mx}자 초과: " +
                     ", ".join(f"#{i}({len(t)}자)" for i, t in over_len[:5]))
        else:
            rep.ok("G 자막표시", "글자수", f"최대 {max(lens)}자 / 평균 {sum(lens)/len(lens):.1f}자")
        multiline = [i for i, t in enumerate(texts, 1) if "\n" in t]
        (rep.ok if not multiline else rep.fail)(
            "G 자막표시", "한 줄 고정", "전부 한 줄" if not multiline else f"{multiline[:5]} 이 여러 줄")

    durs = [(e - s) / US for s, e in tr]
    min_show = CFG.get("자막.최소표시초", 0.35)
    short = [i for i, x in enumerate(durs, 1) if x < min_show]
    if short:
        rep.warn("G 자막표시", "표시 시간",
                 f"{min_show}초 미만 {len(short)}개 {short[:6]} — 읽기 전에 사라진다")
    else:
        rep.ok("G 자막표시", "표시 시간", f"{min(durs):.2f}~{max(durs):.2f}초")

    cps = [len(t) / x for t, x in zip(texts, durs) if t and x > 0]
    if cps:
        fast = sum(1 for c in cps if c > 20)
        det = f"{min(cps):.1f}~{max(cps):.1f}자/초 (중앙 {sorted(cps)[len(cps)//2]:.1f})"
        (rep.ok if fast == 0 else rep.warn)(
            "G 자막표시", "읽기 속도", det + ("" if fast == 0 else f" · 20자/초 초과 {fast}개"))

    covered = sum(e - s for s, e in tr) / total * 100
    rep.ok("G 자막표시", "자막 점유", f"전체의 {covered:.0f}%")

    # ── H. 참조 무결성 ──────────────────────────────────
    ids = set()
    for lst in d["materials"].values():
        if isinstance(lst, list):
            for m in lst:
                if isinstance(m, dict) and "id" in m:
                    ids.add(m["id"])
    missing, dangling = [], []
    for t in tracks:
        for s in t["segments"]:
            if s.get("material_id") and s["material_id"] not in ids:
                missing.append(s["material_id"][:8])
            for r in s.get("extra_material_refs", []):
                if r not in ids:
                    dangling.append(r[:8])
    if missing or dangling:
        rep.fail("H 참조", "소재 참조",
                 f"본체 {len(missing)}건 · 부속 {len(dangling)}건 끊김")
    else:
        rep.ok("H 참조", "소재 참조", f"전부 해소 (소재 {len(ids)}개)")

    dup = [t["id"] for t in tracks]
    if len(dup) != len(set(dup)):
        rep.fail("H 참조", "트랙 id", "중복")
    else:
        rep.ok("H 참조", "트랙 id", "중복 없음")

    # ── I. 파일 실재 ────────────────────────────────────
    gone, sizes = [], 0
    for kind in ("videos", "audios"):
        for m in d["materials"].get(kind, []):
            p = m.get("path") or ""
            if not p:
                continue
            f = Path(p)
            if f.exists():
                sizes += f.stat().st_size
            else:
                gone.append(f.name)
    if gone:
        rep.fail("I 파일", "미디어 실재", f"{len(gone)}개 없음: {gone[:5]}")
    else:
        rep.ok("I 파일", "미디어 실재", f"전부 있음 ({sizes/1048576:.1f}MB)")

    rel = [m.get("path", "") for kind in ("videos", "audios")
           for m in d["materials"].get(kind, [])
           if m.get("path") and not Path(m["path"]).is_absolute()]
    (rep.ok if not rel else rep.fail)("I 파일", "절대 경로",
                                      "전부 절대 경로" if not rel else f"{len(rel)}개가 상대 경로")

    cover = draft / "draft_cover.jpg"
    if cover.exists():
        import hashlib
        h = hashlib.md5(cover.read_bytes()).hexdigest()[:8]
        tmpl = DRAFT_ROOT / CFG.get("캡컷.템플릿드래프트", "") / "draft_cover.jpg"
        if tmpl.exists() and hashlib.md5(tmpl.read_bytes()).hexdigest()[:8] == h:
            rep.fail("I 파일", "표지", "★ 템플릿 표지와 동일 — 이전 회차 이미지가 뜬다")
        else:
            rep.ok("I 파일", "표지", f"고유 ({cover.stat().st_size//1024}KB)")
    else:
        rep.warn("I 파일", "표지", "draft_cover.jpg 없음")

    # 최신 CapCut은 프로젝트를 실제로 열고 저장한 뒤 아래 보조 파일·폴더를
    # 정상적으로 생성하기도 한다. 존재만으로 실패 처리하면 수동 마감 완료본을
    # copytree 잔재로 오판하므로 경고만 남기고, 최종 잠금 검수에서 실제 열기·
    # 전체 재생·내보내기 성공을 별도로 증명한다.
    helpers = ("draft.extra", "key_value.json", "Timelines", "subdraft",
               "crypto_key_store.dat")
    present_helpers = [name for name in helpers if (draft / name).exists()]
    if present_helpers:
        rep.warn("I 파일", "CapCut 보조 파일",
                 f"{', '.join(present_helpers)} — 실제 열기·내보내기는 최종 잠금에서 확인")
    else:
        rep.ok("I 파일", "CapCut 보조 파일", "추가 보조 파일 없음")

    # ── J. 마무리 ───────────────────────────────────────
    tail = (vr[-1][1] - ar[-1][1]) / US
    if tail < -0.05:
        rep.fail("J 마무리", "끝 여백", f"나레이션이 영상보다 {-tail:.2f}초 길다 — 소리가 잘린다")
    elif tail > 1.5:
        rep.warn("J 마무리", "끝 여백", f"나레이션 후 {tail:.2f}초 무음 — 이탈 구간")
    else:
        rep.ok("J 마무리", "끝 여백", f"{tail:.2f}초")

    last_sub_gap = (total - tr[-1][1]) / US
    if last_sub_gap > 2.0:
        rep.warn("J 마무리", "자막 후 여백", f"{last_sub_gap:.2f}초 동안 자막 없음")
    else:
        rep.ok("J 마무리", "자막 후 여백", f"{last_sub_gap:.2f}초")

    # ── 컷별 표 ─────────────────────────────────────────
    if args.verbose:
        print("\n컷별 상세")
        print(f"  {'컷':>3} {'영상 구간':>17} {'배속':>6} {'나레이션 구간':>17} "
              f"{'차이':>7} {'자막':>4}")
        for i, (v, a) in enumerate(zip(vr, ar), 1):
            nsub = sum(1 for s, e in tr if v[0] <= s < v[1])
            print(f"  {i:>3} {fmt(v[0])+'~'+fmt(v[1]):>17} {speeds[i-1]:>5.2f}x "
                  f"{fmt(a[0])+'~'+fmt(a[1]):>17} {(v[0]-a[0])/1000:>+6.0f}ms {nsub:>4}")

    # ── 결과 ────────────────────────────────────────────
    rep.dump()
    print("\n" + "─" * 66)
    n_ok = len([r for r in rep.rows if r[0] == "OK"])
    print(f"통과 {n_ok} · 주의 {len(rep.warns)} · 실패 {len(rep.fails)}")
    if rep.fails:
        print("\n★ 올리면 안 됩니다. 위 실패 항목을 먼저 고치세요.\n")
        return 1
    if rep.warns:
        print("\n올려도 되지만 위 주의 항목은 한 번 보세요.\n")
        return 0
    print("\n올려도 됩니다.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
