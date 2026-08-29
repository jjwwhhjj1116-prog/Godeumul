# -*- coding: utf-8 -*-
"""
채널설정.json 로더. 모든 도구가 이 모듈을 통해 설정을 읽는다.

카테고리를 바꿀 때 고치는 파일은 채널설정.json 하나뿐이고,
tools/ 안의 코드는 건드리지 않는다. 다른 PC에서 이 저장소를 받아
채널설정.json 만 갈아끼우면 같은 워크플로가 그대로 돈다.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "채널설정.json"


def _setup_stdout() -> None:
    """한국어 Windows 콘솔은 기본이 cp949라 한글·기호 출력에서 죽는다."""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


_setup_stdout()


class Config:
    def __init__(self, data: dict):
        self._d = data

    def __getitem__(self, key: str):
        return self._d[key]

    def get(self, path: str, default=None):
        """점 표기로 중첩 값을 읽는다.  cfg.get('tts.voice_id')"""
        cur = self._d
        for part in path.split("."):
            if not isinstance(cur, dict) or part not in cur:
                return default
            cur = cur[part]
        return cur

    def require(self, path: str):
        v = self.get(path, None)
        if v is None:
            sys.exit(f"[에러] 채널설정.json 에 '{path}' 가 없습니다: {CONFIG_PATH}")
        return v

    @property
    def raw(self) -> dict:
        return self._d


def load() -> Config:
    if not CONFIG_PATH.exists():
        sys.exit(f"[에러] 채널설정.json 이 없습니다: {CONFIG_PATH}")
    return Config(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))


def load_env() -> dict[str, str]:
    """의존성 없이 .env 를 읽는다(python-dotenv 불필요).

    Git에서 제외된 보안 파일을 다른 로컬 체크아웃에서 재사용할 때는
    `GODEUMUL_ENV_FILE`에 정확한 파일 경로만 지정한다. 키 값은 복사하거나
    콘솔에 출력하지 않는다.
    """
    env: dict[str, str] = {}
    override = os.environ.get("GODEUMUL_ENV_FILE", "").strip()
    p = Path(override).expanduser() if override else ROOT / ".env"
    if not p.exists():
        return env
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()
    return env
