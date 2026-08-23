#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
[고대유물의 비밀] 3단계 — 장면별 TTS 생성기

시각화 대본(02 지침 형식)을 읽어 장면마다 ElevenLabs 나레이션 mp3를 만들고,
5단계 캡컷 편집에 필요한 장면별 길이표(durations.json)를 함께 남긴다.

★ 크레딧 안전장치
  기본은 드라이런이다. 실제 생성은 --run 을 명시해야만 돈다.
  이미 만든 장면은 텍스트 해시가 같으면 건너뛴다(재실행해도 크레딧 0).

사용법
  python tools/tts_generate.py 산출물/EP01_진시황릉/02.시각화.txt
  python tools/tts_generate.py 산출물/EP01_진시황릉/02.시각화.txt --run
  python tools/tts_generate.py ... --run --only 3,7,12     # 특정 장면만 재생성
  python tools/tts_generate.py ... --run --force           # 캐시 무시
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import requests

# 한국어 Windows 콘솔은 기본이 cp949라 한글·기호 출력에서 죽는다. 먼저 막아둔다.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
API_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


# ──────────────────────────────────────────────────────────────
# 환경변수
# ──────────────────────────────────────────────────────────────
def load_env(path: Path) -> dict[str, str]:
    """의존성 없이 .env 를 읽는다(python-dotenv 불필요)."""
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    return env


@dataclass
class Config:
    api_key: str
    voice_id: str
    model: str
    stability: float
    similarity: float
    style: float
    speaker_boost: bool
    speed: float
    language: str
    output_format: str

    @classmethod
    def from_env(cls, env: dict[str, str]) -> "Config":
        def get(key: str, default: str) -> str:
            return os.environ.get(key) or env.get(key) or default

        api_key = get("ELEVENLABS_API_KEY", "")
        voice_id = get("ARTIFACT_VOICE_ID", "")
        if not api_key or not voice_id:
            sys.exit(
                "[에러] ELEVENLABS_API_KEY 또는 ARTIFACT_VOICE_ID 가 없습니다.\n"
                f"       확인할 파일: {ROOT / '.env'}"
            )
        return cls(
            api_key=api_key,
            voice_id=voice_id,
            model=get("ARTIFACT_MODEL", "eleven_multilingual_v2"),
            stability=float(get("ARTIFACT_STABILITY", "0.38")),
            similarity=float(get("ARTIFACT_SIMILARITY", "0.85")),
            style=float(get("ARTIFACT_STYLE", "0.50")),
            speaker_boost=get("ARTIFACT_SPEAKER_BOOST", "true").lower() == "true",
            speed=float(get("ARTIFACT_SPEED", "1.0")),
            language=get("ARTIFACT_LANGUAGE", "ko"),
            output_format=get("ARTIFACT_OUTPUT_FORMAT", "mp3_44100_128"),
        )

    def signature(self) -> str:
        """음성 파라미터가 바뀌면 캐시를 무효화하기 위한 서명."""
        parts = [
            self.voice_id, self.model, f"{self.stability}", f"{self.similarity}",
            f"{self.style}", f"{self.speaker_boost}", f"{self.speed}",
            self.language, self.output_format,
        ]
        return "|".join(parts)


# ──────────────────────────────────────────────────────────────
# 대본 파서
# ──────────────────────────────────────────────────────────────
SCENE_RE = re.compile(r"^\[장면\s*(\d+)\]", re.M)
# 무협 파이프라인이 [한국어 번역]/[한국어 원문] 둘 다 받는 것과 같은 이유로
# 이 채널도 표기 흔들림을 흡수한다.
NARR_RE = re.compile(r"^\[한국어\s*(?:나레이션|내레이션|번역|원문)\]\s*(.*)$")
TAG_RE = re.compile(r"^\[[^\]]+\]")


@dataclass
class Scene:
    seq: int
    text: str

    def hash(self, sig: str) -> str:
        return hashlib.sha256(f"{sig}::{self.text}".encode("utf-8")).hexdigest()[:16]


def parse_script(path: Path) -> list[Scene]:
    raw = path.read_text(encoding="utf-8")
    marks = list(SCENE_RE.finditer(raw))
    if not marks:
        sys.exit(f"[에러] '[장면 N]' 마커를 찾지 못했습니다: {path}")

    scenes: list[Scene] = []
    for i, m in enumerate(marks):
        seq = int(m.group(1))
        block = raw[m.end(): marks[i + 1].start() if i + 1 < len(marks) else len(raw)]

        lines: list[str] = []
        collecting = False
        for line in block.splitlines():
            hit = NARR_RE.match(line.strip())
            if hit:
                collecting = True
                if hit.group(1).strip():
                    lines.append(hit.group(1).strip())
                continue
            if collecting:
                stripped = line.strip()
                # 다음 태그([영어 이미지 프롬프트] 등)를 만나면 종료
                if not stripped or TAG_RE.match(stripped):
                    break
                lines.append(stripped)

        text = " ".join(lines).strip()
        if text:
            scenes.append(Scene(seq=seq, text=text))
        else:
            print(f"  [경고] 장면 {seq}: 나레이션이 비어 있어 건너뜁니다.")

    return scenes


# ──────────────────────────────────────────────────────────────
# 생성
# ──────────────────────────────────────────────────────────────
def synth(cfg: Config, text: str, out: Path) -> None:
    payload = {
        "text": text,
        "model_id": cfg.model,
        "voice_settings": {
            "stability": cfg.stability,
            "similarity_boost": cfg.similarity,
            "style": cfg.style,
            "use_speaker_boost": cfg.speaker_boost,
            "speed": cfg.speed,
        },
    }
    # 대시보드의 Language Override에 해당. 모델에 따라 거부될 수 있어 실패 시 빼고 재시도한다.
    if cfg.language:
        payload["language_code"] = cfg.language

    def post(body: dict):
        return requests.post(
            API_URL.format(voice_id=cfg.voice_id),
            headers={"xi-api-key": cfg.api_key, "Content-Type": "application/json"},
            params={"output_format": cfg.output_format} if cfg.output_format else None,
            json=body,
            timeout=180,
        )

    resp = post(payload)
    if resp.status_code != 200 and "language_code" in payload and \
            "language" in resp.text.lower():
        payload.pop("language_code")
        print("    (이 모델은 language_code를 받지 않아 생략하고 재시도)")
        resp = post(payload)

    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:400]}")

    body = resp.content
    # 무협 파이프라인에서 겪은 0바이트 mp3 사고를 여기서 차단한다.
    if len(body) < 1024:
        raise RuntimeError(f"응답이 너무 작습니다({len(body)}바이트). 키/보이스 확인 필요.")

    out.write_bytes(body)


def probe_duration(path: Path) -> float:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, check=True,
        )
        return round(float(out.stdout.strip()), 3)
    except Exception:
        return 0.0


# ──────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="[고대유물의 비밀] 장면별 TTS 생성기")
    ap.add_argument("script", type=Path, help="02 지침 형식의 시각화 대본 파일")
    ap.add_argument("--run", action="store_true", help="실제 생성(크레딧 소모). 없으면 드라이런")
    ap.add_argument("--force", action="store_true", help="캐시를 무시하고 전부 재생성")
    ap.add_argument("--only", type=str, default="", help="특정 장면만 (예: 3,7,12)")
    ap.add_argument("--outdir", type=Path, default=None, help="출력 폴더 (기본: 대본 옆 audio/)")
    args = ap.parse_args()

    if not args.script.exists():
        sys.exit(f"[에러] 대본 파일이 없습니다: {args.script}")

    cfg = Config.from_env(load_env(ROOT / ".env"))
    scenes = parse_script(args.script)

    if args.only:
        wanted = {int(x) for x in args.only.replace(" ", "").split(",") if x}
        scenes = [s for s in scenes if s.seq in wanted]

    outdir = args.outdir or args.script.parent / "audio"
    outdir.mkdir(parents=True, exist_ok=True)
    manifest_path = outdir / "durations.json"

    manifest: dict = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cache: dict = {} if args.force else manifest.get("scenes", {})

    sig = cfg.signature()
    total_chars = sum(len(s.text) for s in scenes)

    print(f"\n대본      : {args.script}")
    print(f"출력      : {outdir}")
    print(f"보이스    : {cfg.voice_id}  ({cfg.model}, speed {cfg.speed})")
    print(f"장면      : {len(scenes)}개 / 총 {total_chars:,}자")
    print(f"모드      : {'실제 생성' if args.run else '드라이런 (크레딧 0)'}\n")

    results: dict[str, dict] = {}
    made = skipped = failed = 0
    billed_chars = 0

    for s in scenes:
        name = f"{s.seq:03d}.mp3"
        dest = outdir / name
        digest = s.hash(sig)
        cached = cache.get(str(s.seq))

        if not args.force and cached and cached.get("hash") == digest and dest.exists():
            results[str(s.seq)] = cached
            skipped += 1
            print(f"  [건너뜀] {name}  (변경 없음)")
            continue

        preview = s.text[:44] + ("…" if len(s.text) > 44 else "")
        if not args.run:
            print(f"  [예정]   {name}  {len(s.text):>4}자  {preview}")
            results[str(s.seq)] = {"hash": digest, "chars": len(s.text),
                                   "file": name, "duration": None, "text": s.text}
            billed_chars += len(s.text)
            continue

        try:
            synth(cfg, s.text, dest)
            dur = probe_duration(dest)
            results[str(s.seq)] = {"hash": digest, "chars": len(s.text),
                                   "file": name, "duration": dur, "text": s.text}
            billed_chars += len(s.text)
            made += 1
            print(f"  [생성]   {name}  {dur:>6.2f}s  {len(s.text):>4}자  {preview}")
        except Exception as exc:
            failed += 1
            print(f"  [실패]   {name}  {exc}")

    manifest = {
        "script": str(args.script),
        "voice_id": cfg.voice_id,
        "model": cfg.model,
        "speed": cfg.speed,
        "scene_count": len(scenes),
        "total_duration": round(sum(v["duration"] or 0 for v in results.values()), 3),
        "scenes": dict(sorted(results.items(), key=lambda kv: int(kv[0]))),
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\n  생성 {made} · 건너뜀 {skipped} · 실패 {failed}")
    if args.run:
        print(f"  총 길이 {manifest['total_duration']:.2f}초 "
              f"({manifest['total_duration'] / 60:.2f}분)")
        print(f"  과금 문자 {billed_chars:,}자")
    else:
        print(f"  예상 과금 {billed_chars:,}자 — 실제로 만들려면 --run 을 붙이세요.")
    print(f"  길이표 → {manifest_path}\n")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
