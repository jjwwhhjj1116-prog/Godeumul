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
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path

from _config import load, load_env
from script_context_gate import validate_context_review
from tts_pronunciation import DEFAULT_DICTIONARY, PronunciationDictionary

# 한국어 Windows 콘솔은 기본이 cp949라 한글·기호 출력에서 죽는다. 먼저 막아둔다.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
API_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
API_URL_WITH_TIMESTAMPS = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"

CFG = load()
CPS_MEASURED = CFG.get("tts.실측_자당초", 9.35)
CPS_PLANNING = CFG.get("tts.기획_자당초", 8.0)


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
    def from_env(cls, env: dict[str, str], *, require_api_key: bool = True) -> "Config":
        def get(key: str, default: str) -> str:
            return os.environ.get(key) or env.get(key) or default

        api_key = get("ELEVENLABS_API_KEY", "")
        voice_id = get("ARTIFACT_VOICE_ID", CFG.get("tts.voice_id", ""))
        if not voice_id or (require_api_key and not api_key):
            sys.exit(
                "[에러] ELEVENLABS_API_KEY 또는 ARTIFACT_VOICE_ID 가 없습니다.\n"
                f"       확인할 파일: {ROOT / '.env'}"
            )
        return cls(
            api_key=api_key,
            voice_id=voice_id,
            model=get("ARTIFACT_MODEL", CFG.get("tts.model", "eleven_multilingual_v2")),
            stability=float(get("ARTIFACT_STABILITY", str(CFG.get("tts.stability", 0.4)))),
            similarity=float(get("ARTIFACT_SIMILARITY", str(CFG.get("tts.similarity", 0.85)))),
            style=float(get("ARTIFACT_STYLE", str(CFG.get("tts.style", 0.5)))),
            speaker_boost=get("ARTIFACT_SPEAKER_BOOST", str(CFG.get("tts.speaker_boost", True))).lower() in ("true","1"),
            speed=float(get("ARTIFACT_SPEED", str(CFG.get("tts.speed", 1.05)))),
            language=get("ARTIFACT_LANGUAGE", CFG.get("tts.language", "ko")),
            output_format=get("ARTIFACT_OUTPUT_FORMAT", CFG.get("tts.output_format", "mp3_44100_128")),
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
SCENE_RE = re.compile(r"^(?:\[장면\s*(\d+)\]|##\s*장면\s*(\d+)(?:\s*—.*)?)", re.M)
# 무협 파이프라인이 [한국어 번역]/[한국어 원문] 둘 다 받는 것과 같은 이유로
# 이 채널도 표기 흔들림을 흡수한다.
NARR_RE = re.compile(r"^\[한국어\s*(?:나레이션|내레이션|번역|원문)\]\s*(.*)$")
MD_NARR_RE = re.compile(r"^-\s*(?:나레이션|내레이션):\s*(.*)$")
TAG_RE = re.compile(r"^\[[^\]]+\]")


@dataclass
class Scene:
    seq: int
    text: str

    def hash(self, sig: str, tts_text: str) -> str:
        return hashlib.sha256(f"{sig}::{tts_text}".encode("utf-8")).hexdigest()[:16]


def parse_script(path: Path) -> list[Scene]:
    raw = path.read_text(encoding="utf-8")
    marks = list(SCENE_RE.finditer(raw))
    if not marks:
        sys.exit(f"[에러] '[장면 N]' 마커를 찾지 못했습니다: {path}")

    scenes: list[Scene] = []
    for i, m in enumerate(marks):
        seq = int(m.group(1) or m.group(2))
        block = raw[m.end(): marks[i + 1].start() if i + 1 < len(marks) else len(raw)]

        lines: list[str] = []
        collecting = False
        for line in block.splitlines():
            hit = NARR_RE.match(line.strip()) or MD_NARR_RE.match(line.strip())
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
def synth(cfg: Config, text: str, out: Path) -> list[dict[str, object]]:
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

    def post(body: dict) -> tuple[int, bytes, str]:
        query = urllib.parse.urlencode(
            {"output_format": cfg.output_format} if cfg.output_format else {}
        )
        url = API_URL_WITH_TIMESTAMPS.format(voice_id=cfg.voice_id)
        if query:
            url = f"{url}?{query}"
        request = urllib.request.Request(
            url,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"xi-api-key": cfg.api_key, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                response_body = response.read()
                return response.status, response_body, ""
        except urllib.error.HTTPError as exc:
            error_body = exc.read()
            error_text = error_body.decode("utf-8", errors="replace")
            return exc.code, error_body, error_text

    status, body, error_text = post(payload)
    if status != 200 and "language_code" in payload and \
            "language" in error_text.lower():
        payload.pop("language_code")
        print("    (이 모델은 language_code를 받지 않아 생략하고 재시도)")
        status, body, error_text = post(payload)

    if status != 200:
        raise RuntimeError(f"HTTP {status}: {error_text[:400]}")

    try:
        response = json.loads(body.decode("utf-8"))
        audio = base64.b64decode(response["audio_base64"])
    except (KeyError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"타임스탬프 TTS 응답 형식 오류: {exc}") from exc

    # 무협 파이프라인에서 겪은 0바이트 mp3 사고를 여기서 차단한다.
    if len(audio) < 1024:
        raise RuntimeError(f"오디오 응답이 너무 작습니다({len(audio)}바이트). 키/보이스 확인 필요.")

    alignment = response.get("alignment") or response.get("normalized_alignment") or {}
    chars = alignment.get("characters") or []
    starts = alignment.get("character_start_times_seconds") or []
    ends = alignment.get("character_end_times_seconds") or []
    if not chars or not (len(chars) == len(starts) == len(ends)):
        raise RuntimeError("TTS 응답에 문자 타임스탬프가 없거나 길이가 맞지 않습니다.")
    out.write_bytes(audio)
    return [
        {"c": str(char), "s": float(start), "e": float(end)}
        for char, start, end in zip(chars, starts, ends)
    ]


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
    ap.add_argument("--pronunciation-dictionary", type=Path, default=DEFAULT_DICTIONARY,
                    help="ElevenLabs 전송 전용 발음 치환 사전")
    ap.add_argument("--context-script", type=Path, default=None,
                    help="문맥 검수를 받은 원문 대본(기본: 입력 파일 옆 01.대본.txt)")
    ap.add_argument("--context-review", type=Path, default=None,
                    help="문맥 검수 잠금(기본: 원문 대본 옆 01.문맥검수.json)")
    args = ap.parse_args()

    if not args.script.exists():
        sys.exit(f"[에러] 대본 파일이 없습니다: {args.script}")

    context_script = args.context_script or args.script.parent / "01.대본.txt"
    context_review = args.context_review or context_script.parent / "01.문맥검수.json"
    context_report = validate_context_review(context_script, context_review)
    if not context_report.passed:
        details = "\n".join(f"  - {failure}" for failure in context_report.failures)
        sys.exit(
            "[에러] 한국어 문맥 QA를 통과하지 않아 TTS를 생성하지 않습니다.\n"
            f"대본: {context_script}\n검수: {context_review}\n{details}"
        )
    print(
        f"[문맥 QA 통과] 문단 {context_report.paragraphs} · "
        f"문장 {context_report.sentences} · 접속 표지 {context_report.marker_count}"
    )

    env_override = os.environ.get("GODEUMUL_ENV_FILE", "").strip()
    env_path = Path(env_override).expanduser() if env_override else ROOT / ".env"
    cfg = Config.from_env(load_env(env_path), require_api_key=args.run)
    all_scenes = parse_script(args.script)
    pronunciation = PronunciationDictionary(args.pronunciation_dictionary)

    wanted: set[int] = set()
    if args.only:
        wanted = {int(x) for x in args.only.replace(" ", "").split(",") if x}
    scenes = [s for s in all_scenes if not wanted or s.seq in wanted]

    outdir = args.outdir or args.script.parent / "audio"
    outdir.mkdir(parents=True, exist_ok=True)
    manifest_path = outdir / "durations.json"
    generation_alignment_path = outdir / "generation_alignment.json"

    manifest: dict = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    previous_scenes: dict = manifest.get("scenes", {})
    cache: dict = {} if args.force else previous_scenes

    generation_alignment: dict = {"signatures": {}, "scenes": {}}
    if generation_alignment_path.exists():
        try:
            generation_alignment = json.loads(generation_alignment_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            generation_alignment = {"signatures": {}, "scenes": {}}

    sig = cfg.signature() + "|pron:" + pronunciation.signature + "|aligned:v1"
    prepared = {s.seq: pronunciation.apply(s.text) for s in scenes}
    total_chars = sum(len(s.text) for s in scenes)
    total_tts_chars = sum(len(prepared[s.seq][0]) for s in scenes)

    print(f"\n대본      : {args.script}")
    print(f"출력      : {outdir}")
    print(f"보이스    : {cfg.voice_id}  ({cfg.model}, speed {cfg.speed})")
    print(f"발음사전  : {pronunciation.path.name}  (서명 {pronunciation.signature})")
    est_measured = total_tts_chars / CPS_MEASURED
    est_conservative = total_tts_chars / CPS_PLANNING
    warn = "  ← ★ 이전 실측 속도 기준 3분 초과" if est_measured >= 180 else ""
    print(f"장면      : {len(scenes)}개 / 원문 {total_chars:,}자 / TTS 입력 {total_tts_chars:,}자")
    print(f"예상 길이 : {int(est_measured)//60}:{int(est_measured)%60:02d}  "
          f"(이전 실측 {CPS_MEASURED}자/초){warn}")
    print(f"보수 상한 : {int(est_conservative)//60}:{int(est_conservative)%60:02d}  "
          f"({CPS_PLANNING}자/초)")
    print(f"모드      : {'실제 생성' if args.run else '드라이런 (크레딧 0)'}\n")

    # --only는 선택 장면만 재생성하되, 기존 길이표의 나머지 장면을
    # 보존해야 한다. 그렇지 않으면 전체 장면 매니페스트가 선택 장면만 남도록 축소된다.
    results: dict[str, dict] = dict(previous_scenes) if wanted else {}
    made = skipped = failed = 0
    billed_chars = 0

    for s in scenes:
        name = f"{s.seq:03d}.mp3"
        dest = outdir / name
        tts_text, pronunciation_changes = prepared[s.seq]
        changes_json = [asdict(change) for change in pronunciation_changes]
        digest = s.hash(sig, tts_text)
        cached = cache.get(str(s.seq))

        if not args.force and cached and cached.get("hash") == digest and dest.exists():
            results[str(s.seq)] = cached
            skipped += 1
            print(f"  [건너뜀] {name}  (변경 없음)")
            continue

        preview = s.text[:44] + ("…" if len(s.text) > 44 else "")
        tts_preview = tts_text[:44] + ("…" if len(tts_text) > 44 else "")
        if not args.run:
            print(f"  [예정]   {name}  {len(s.text):>4}자  {preview}")
            if pronunciation_changes:
                print(f"           TTS 치환 → {tts_preview}")
            results[str(s.seq)] = {"hash": digest, "chars": len(s.text),
                                   "tts_chars": len(tts_text), "file": name,
                                   "duration": None, "text": s.text,
                                   "tts_text": tts_text,
                                   "pronunciation_changes": changes_json}
            billed_chars += len(tts_text)
            continue

        try:
            character_alignment = synth(cfg, tts_text, dest)
            dur = probe_duration(dest)
            results[str(s.seq)] = {"hash": digest, "chars": len(s.text),
                                   "tts_chars": len(tts_text), "file": name,
                                   "duration": dur, "text": s.text,
                                   "tts_text": tts_text,
                                   "pronunciation_changes": changes_json}
            billed_chars += len(tts_text)
            made += 1
            generation_alignment.setdefault("signatures", {})[str(s.seq)] = hashlib.sha256(
                tts_text.encode("utf-8")
            ).hexdigest()[:16]
            generation_alignment.setdefault("scenes", {})[str(s.seq)] = character_alignment
            print(f"  [생성]   {name}  {dur:>6.2f}s  {len(s.text):>4}자  {preview}")
            if pronunciation_changes:
                print(f"           TTS 치환 → {tts_preview}")
        except Exception as exc:
            failed += 1
            print(f"  [실패]   {name}  {exc}")

    manifest = {
        "script": str(args.script),
        "voice_id": cfg.voice_id,
        "model": cfg.model,
        "speed": cfg.speed,
        "pronunciation_dictionary": str(pronunciation.path),
        "pronunciation_signature": pronunciation.signature,
        "scene_count": len(results),
        "total_duration": round(sum(v["duration"] or 0 for v in results.values()), 3),
        "scenes": dict(sorted(results.items(), key=lambda kv: int(kv[0]))),
    }
    if args.run:
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        generation_alignment_path.write_text(
            json.dumps(generation_alignment, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    print(f"\n  생성 {made} · 건너뜀 {skipped} · 실패 {failed}")
    if args.run:
        print(f"  총 길이 {manifest['total_duration']:.2f}초 "
              f"({manifest['total_duration'] / 60:.2f}분)")
        print(f"  과금 문자 {billed_chars:,}자")
    else:
        print(f"  예상 과금 {billed_chars:,}자 — 실제로 만들려면 --run 을 붙이세요.")
        print("  드라이런이므로 기존 길이표는 변경하지 않았습니다.")
    if args.run:
        print(f"  길이표 → {manifest_path}")
        print(f"  문자 정렬 → {generation_alignment_path}")
    print()

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
