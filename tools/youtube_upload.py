#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
[고대유물의 비밀] 7단계 — 유튜브 업로드 (브라우저 없음)

크롬을 제어할 필요가 없다. YouTube Data API v3 의 videos.insert 로
파일을 그대로 쏜다. 브라우저 자동화는 화면이 바뀌면 깨지지만 API 는 안 깨진다.

  업로드 1회 = 1,600 쿼터 (기본 한도 10,000/일 → 하루 6편)
  썸네일 설정 = 50 쿼터
  최초 1회만 브라우저로 로그인 동의(OAuth), 이후엔 token.json 재사용

준비 (최초 1회, 자세한 건 07.업로드지침.md)
  1. Google Cloud 콘솔에서 프로젝트 생성 → YouTube Data API v3 사용 설정
  2. OAuth 클라이언트 ID → 유형 "데스크톱 앱" → JSON 내려받기
  3. 저장소 루트에 client_secrets.json 로 저장  (.gitignore 처리되어 있음)
  4. python tools/youtube_upload.py --auth        ← 브라우저가 한 번 열린다

사용법
  python tools/youtube_upload.py 산출물/EP01_진시황릉                 # 점검만
  python tools/youtube_upload.py 산출물/EP01_진시황릉 --run           # 비공개 업로드
  python tools/youtube_upload.py 산출물/EP01_진시황릉 --run --공개 예약

기본 게시 절차는 비공개 업로드 → 처리·저작권 확인 → youtube_status_update.py의
자동 예약이다. 채널설정에서 즉시 공개를 금지하면 `--공개 공개`는 실행되지 않는다.

메타데이터는 에피소드 폴더의 06.메타.json 에서 읽는다.
  {"제목": "...", "설명": "...", "태그": ["..."]}

체크포인트 v2는 영상 SHA-256·업로드 요청 메타·채널 ID가 일치할 때만 기존 ID를
재사용한다. 완료 기록은 원격 조회만, 미완료 후속 단계는 같은 ID로 이어간다.
ID 없는 중단/응답 유실 및 식별 증거 없는 구형 기록은 수동 대조 전 새 업로드를
막는다. 같은 요청의 5xx 오류는 최대 5회까지, 1·2·4·8초 간격으로 시도한다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from _config import load
from capcut_final_lock import validate_capcut_lock

CFG = load()
ROOT = Path(__file__).resolve().parent.parent
def _find_secrets() -> Path:
    """구글이 내려주는 파일명이 제각각이라(client_secret.json,
    client_secret_326341392012-xxxx.apps.googleusercontent.com.json …)
    이름을 하나로 강요하지 않고 폴더에서 찾는다."""
    exact = [ROOT / "client_secrets.json", ROOT / "client_secret.json"]
    for p in exact:
        if p.exists():
            return p
    hits = sorted(ROOT.glob("client_secret*.json"))
    return hits[0] if hits else exact[0]


SECRETS = _find_secrets()
TOKEN = ROOT / "token.json"
# force-ssl 은 댓글 읽기·답글에 필요하다. readonly 로는 commentThreads 가 403 난다.
# ★ 스코프를 바꾸면 기존 token.json 은 무효다. --auth 를 다시 한 번 돌려야 한다.
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.force-ssl"]
KST = timezone(timedelta(hours=9))

# 공식 쿼터표
Q_UPLOAD, Q_THUMB, Q_PLAYLIST = 1600, 50, 50
THUMB_MAX = 2 * 1024 * 1024          # 유튜브 썸네일 상한 2MB
UPLOAD_MAX_ATTEMPTS = 5             # 전체 업로드의 5xx 재시도 예산: 최초 시도 + 4회
UPLOAD_BACKOFF_SECONDS = 1
UPLOAD_BACKOFF_MAX_SECONDS = 30
UPLOADED_STATES = {
    "VIDEO_UPLOADED_THUMBNAIL_PENDING", "THUMBNAIL_APPLIED_VERIFIED", "PACKAGING_COMPLETE",
}


class UploadRecoveryError(RuntimeError):
    """이전 업로드 결과를 확인하기 전 새 영상 생성을 차단한다."""


def configured_publish_datetime(now: datetime | None = None) -> datetime:
    """채널설정의 고정 예약 정책을 KST 시각으로 계산한다."""
    now = now or datetime.now(KST)
    days = int(CFG.get("업로드.예약정책.일수후", 1))
    clock = str(CFG.get("업로드.예약정책.시각", "16:00"))
    try:
        hour, minute = (int(part) for part in clock.split(":", 1))
    except (TypeError, ValueError):
        sys.exit(f"[에러] 채널설정 업로드.예약정책.시각 오류: {clock!r}")
    return (now + timedelta(days=days)).replace(
        hour=hour, minute=minute, second=0, microsecond=0,
    )


def resolve_publish_datetime(
    value: str | None,
    now: datetime | None = None,
    *,
    allow_policy_override: bool = False,
) -> datetime:
    """`auto`는 고정 정책을 적용하고, 명시 예약은 승인된 예외만 허용한다."""
    expected = configured_publish_datetime(now)
    if not value or value.strip().lower() == "auto":
        return expected
    dt = datetime.strptime(value, "%Y-%m-%d %H:%M").replace(tzinfo=KST)
    if (CFG.get("업로드.예약정책.시각고정", True)
            and dt != expected and not allow_policy_override):
        sys.exit(
            "[에러] 예약 정책 위반: 항상 예약 실행일 기준 다음날 "
            f"{expected:%H:%M} KST만 허용합니다. 이번 허용 시각: {expected:%Y-%m-%d %H:%M}"
        )
    return dt


def _need_libs() -> None:
    try:
        import googleapiclient.discovery      # noqa: F401
        import google_auth_oauthlib.flow      # noqa: F401
    except ImportError:
        sys.exit("[에러] 라이브러리가 없습니다:\n"
                 "  pip install google-api-python-client google-auth-oauthlib google-auth-httplib2")


def service(token_path: Path = TOKEN, secrets_path: Path = SECRETS):
    """인증된 youtube 서비스를 돌려준다. 토큰이 없으면 브라우저를 한 번 연다."""
    _need_libs()
    from google.auth.transport.requests import Request
    from google.auth.exceptions import RefreshError
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())          # 정상 만료는 조용히 갱신한다
            token_path.write_text(creds.to_json(), encoding="utf-8")
        except RefreshError:
            # 테스트 OAuth 토큰의 7일 만료·철회는 새 동의 흐름으로 복구한다.
            creds = None
    if not creds or not creds.valid:
        if not secrets_path.exists():
            sys.exit(f"[에러] client_secrets.json 이 없습니다: {secrets_path}\n"
                     "       07.업로드지침.md 의 '최초 1회 설정'을 보세요.")
        flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), SCOPES)
        # ★ 구글이 인증 후 http://localhost:<포트> 로 돌려보낸다. 그때까지 이 프로세스가
        #   살아 있어야 한다. 죽어 있으면 브라우저에 ERR_CONNECTION_REFUSED 가 뜨고
        #   토큰이 안 생긴다. 포트는 실행마다 바뀌므로 **이번 실행의 URL**을 써야 한다.
        print("\n" + "=" * 62)
        print("  브라우저가 열립니다. 안 열리면 아래 URL 을 직접 붙여넣으세요.")
        print("  ★ 동의를 마칠 때까지 이 창을 닫지 마세요 (Ctrl+C 금지).")
        print("  ★ 이전에 나왔던 URL 은 죽어 있습니다. 이번 것만 씁니다.")
        print("  계정이 여러 개면 시크릿 창에 붙여넣는 쪽이 확실합니다.")
        print("=" * 62 + "\n")
        creds = flow.run_local_server(
            port=0, prompt="consent", open_browser=True,
            authorization_prompt_message="여기로 접속하세요:\n\n{url}\n",
            success_message="인증 완료. 이 창을 닫고 PowerShell 로 돌아가세요.",
            timeout_seconds=600)
        token_path.write_text(creds.to_json(), encoding="utf-8")
        print(f"\n  토큰 저장 -> {token_path}  (이제 브라우저는 다시 안 열립니다)")
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def channel_identity(yt) -> tuple[str, str]:
    """채널명 검사와 재개 기록에 사용할 실제 소유 채널 ID."""
    r = yt.channels().list(part="snippet", mine=True).execute()
    items = r.get("items") or []
    if len(items) != 1 or not items[0].get("id"):
        sys.exit("[에러] 이 토큰의 단일 유튜브 채널 ID를 확인하지 못했습니다.")
    return items[0]["id"], items[0]["snippet"]["title"]


def whoami(yt) -> str:
    """토큰이 물고 있는 채널 이름."""
    return channel_identity(yt)[1]


def find_video(ep: Path) -> Path | None:
    """캡컷에서 내보낸 완성본을 찾는다. clips/ 의 소재는 제외."""
    lock = ep / "05.캡컷마감잠금.json"
    if lock.exists():
        try:
            name = json.loads(lock.read_text(encoding="utf-8")).get("video")
            if name and (ep / name).exists():
                return ep / name
        except (OSError, json.JSONDecodeError):
            pass
    for pat in ("*_capcut.mp4", "*CapCut*.mp4"):
        hits = [h for h in ep.glob(pat) if h.parent.name != "clips"]
        if hits:
            return max(hits, key=lambda p: p.stat().st_mtime)
    return None


def load_meta(ep: Path) -> dict:
    p = ep / "06.메타.json"
    if not p.exists():
        sys.exit(f"[에러] {p} 가 없습니다.\n"
                 '       형식: {"제목": "...", "설명": "...", "태그": ["..."]}')
    m = json.loads(p.read_text(encoding="utf-8"))
    for k in ("제목", "설명"):
        if not m.get(k):
            sys.exit(f"[에러] 06.메타.json 에 '{k}' 가 비어 있습니다.")
    return m


def check_meta(m: dict, ep: Path) -> list[str]:
    """07 지침의 게이트를 코드로 옮긴 것. 걸리면 --run 을 막는다."""
    bad = []
    title, desc = m["제목"], m["설명"]
    tags = m.get("태그", [])
    mx = CFG.get("업로드.해시태그최대", 5)

    if len(title) > 100:
        bad.append(f"제목이 100자를 넘습니다 ({len(title)}자, 유튜브 상한)")
    elif len(title) > 40:
        bad.append(f"제목이 40자를 넘습니다 ({len(title)}자, 채널 규칙)")
    if len(desc) > 5000:
        bad.append(f"설명이 5,000자를 넘습니다 ({len(desc)}자)")
    ht = [w for w in desc.split() if w.startswith("#")]
    if len(ht) > mx:
        bad.append(f"설명의 해시태그가 {len(ht)}개입니다 (최대 {mx})")
    if len(tags) > mx:
        bad.append(f"태그가 {len(tags)}개입니다 (최대 {mx})")
    if "<" in title or ">" in title:
        bad.append("제목에 < > 는 쓸 수 없습니다")
    if CFG.get("업로드.합성콘텐츠고지", True) and "AI" not in desc:
        bad.append("설명에 AI 재현물 고지가 없습니다 (07-3)")
    if (ep / "00.팩트체크.md").exists() and "재현" not in desc and "추정" not in desc:
        bad.append("팩트체크가 있는데 설명에 재현·추정 고지가 없습니다")
    return bad


def check_release_status(ep: Path) -> list[str]:
    """진행표에 명시된 배포 차단을 업로드보다 우선한다."""
    status = ep / "00.진행상황.md"
    if not status.exists():
        return []
    text = status.read_text(encoding="utf-8")
    if "배포 차단" in text or "업로드 금지" in text:
        return ["00.진행상황.md가 배포 차단 상태입니다. 새 대본·최종본 승인 전 업로드 금지"]
    return []


def check_thumb(p: Path | None) -> list[str]:
    """썸네일이 유튜브 규격에 맞는가."""
    if p is None:
        return []
    bad = []
    kb = p.stat().st_size / 1024
    if p.stat().st_size > THUMB_MAX:
        bad.append(f"썸네일이 {kb:.0f}KB — 상한 2,048KB 초과")
    try:
        from PIL import Image
        with Image.open(p) as im:
            w, h = im.size
        want_w, want_h = CFG.get("출력.해상도", [1080, 1920])
        if (w, h) != (want_w, want_h):
            bad.append(f"썸네일이 {w}x{h} — 기대 {want_w}x{want_h}")
    except ImportError:
        pass
    return bad


def find_playlist(yt, name: str) -> str | None:
    """내 채널에서 이름이 정확히 일치하는 재생목록의 id."""
    tok = None
    while True:
        r = yt.playlists().list(part="snippet", mine=True,
                                maxResults=50, pageToken=tok).execute()
        for it in r.get("items", []):
            if it["snippet"]["title"].strip() == name.strip():
                return it["id"]
        tok = r.get("nextPageToken")
        if not tok:
            return None


def add_to_playlist(yt, vid: str, name: str) -> None:
    pid = find_playlist(yt, name)
    if not pid:
        raise UploadRecoveryError(f"재생목록 '{name}'을 못 찾았습니다. 기존 영상 ID로 다시 확인하세요.")
    # 직전 insert 응답 유실 또는 완료 기록 직전 중단에도 중복 항목을 만들지 않는다.
    existing = yt.playlistItems().list(
        part="id", playlistId=pid, videoId=vid, maxResults=1,
    ).execute().get("items") or []
    if existing:
        print(f"  재생목록 : '{name}' 에 이미 있음")
        return
    yt.playlistItems().insert(part="snippet", body={"snippet": {
        "playlistId": pid,
        "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute()
    print(f"  재생목록 : '{name}' 에 추가")


def build_body(m: dict, privacy: str, publish_at: str | None) -> dict:
    lang = CFG.get("업로드.언어", "ko")
    body = {
        "snippet": {
            "title": m["제목"],
            "description": m["설명"],
            "tags": m.get("태그", []),
            "categoryId": str(CFG.get("업로드.카테고리ID", 27)),
            "defaultLanguage": lang,
            "defaultAudioLanguage": lang,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": bool(CFG.get("업로드.아동용", False)),
            "containsSyntheticMedia": bool(CFG.get("업로드.합성콘텐츠고지", True)),
            "license": "youtube",
            "embeddable": True,
        },
    }
    if publish_at:
        body["status"]["publishAt"] = publish_at
    return body


def set_and_verify_thumbnail(yt, vid: str, thumb: Path) -> dict:
    """맞춤 썸네일을 설정하고 유튜브가 돌려준 원격 썸네일까지 확인한다."""
    from googleapiclient.http import MediaFileUpload

    result = yt.thumbnails().set(
        videoId=vid,
        media_body=MediaFileUpload(str(thumb), mimetype="image/jpeg"),
    ).execute()
    response_items = result.get("items") or []
    if not response_items:
        raise RuntimeError("유튜브가 맞춤 썸네일 등록 결과를 반환하지 않았습니다.")

    videos = yt.videos().list(part="snippet", id=vid).execute().get("items") or []
    if not videos:
        raise RuntimeError("썸네일 등록 후 영상을 다시 조회하지 못했습니다.")
    remote = videos[0]["snippet"].get("thumbnails") or {}
    if not remote:
        raise RuntimeError("썸네일 등록 후 원격 썸네일 주소가 없습니다.")

    urls = {name: data.get("url", "") for name, data in remote.items() if data.get("url")}
    print(f"  썸네일   : {thumb.name} 적용 및 원격 조회 확인")
    return {
        "applied": True,
        "verified": True,
        "source": str(thumb),
        "remote_urls": urls,
    }


def _write_upload_checkpoint(path: Path | None, *, exclusive: bool = False, **fields) -> None:
    """첫 생성은 독점 생성하고, 후속 기록은 원자 교체해 복구 증거를 보존한다."""
    if path is None:
        return
    payload = {
        **fields,
        "updated_at": datetime.now(KST).isoformat(timespec="seconds"),
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if exclusive:
        # 같은 회차를 동시에 실행해도 새 videos.insert는 한 실행만 진입한다.
        with path.open("x", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        return
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=path.name + ".", suffix=".tmp", delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def upload_identity(video: Path, body: dict, channel_id: str) -> dict:
    """파일 경로가 바뀌어도 실제 바이트·요청 메타·소유 채널이 같아야 재개한다."""
    if not channel_id:
        raise UploadRecoveryError("업로드 대상 채널 ID가 없습니다.")
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "video_sha256": _sha256(video),
        "video_size": video.stat().st_size,
        "metadata_sha256": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
        "channel_id": channel_id,
    }


def read_upload_checkpoint(path: Path) -> dict | None:
    """불완전·구형 기록도 신규 업로드 허가로 해석하지 않는다."""
    if not path.exists():
        if (path.parent / "07.업로드결과.json").exists():
            raise UploadRecoveryError("기존 업로드 결과는 있지만 체크포인트가 없습니다. 기존 영상부터 확인하세요.")
        return None
    try:
        checkpoint = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise UploadRecoveryError("체크포인트를 읽지 못했습니다. 기존 업로드 결과 확인 전 새 업로드 금지.") from exc
    if not isinstance(checkpoint, dict) or checkpoint.get("version") != 2:
        raise UploadRecoveryError("구형·잘못된 체크포인트입니다. 기존 영상 ID와 파일·메타·채널 증거를 먼저 대조하세요.")
    if (checkpoint.get("status") not in UPLOADED_STATES
            or not isinstance(checkpoint.get("video_id"), str) or not checkpoint["video_id"].strip()):
        raise UploadRecoveryError("이전 업로드 결과가 불명확합니다. YouTube Studio에서 기존 영상 확인 전 새 업로드 금지.")
    identity = checkpoint.get("identity")
    if (not isinstance(identity, dict)
            or not all(identity.get(key) for key in ("video_sha256", "metadata_sha256", "channel_id"))
            or not isinstance(identity.get("video_size"), int)):
        raise UploadRecoveryError("체크포인트에 파일·메타·채널 식별 증거가 없습니다. 새 업로드 금지.")
    if (checkpoint["status"] in {"THUMBNAIL_APPLIED_VERIFIED", "PACKAGING_COMPLETE"}
            and checkpoint.get("thumbnail_sha256")):
        result = checkpoint.get("thumbnail_result")
        if (not isinstance(result, dict) or result.get("applied") is not True
                or result.get("verified") is not True or not result.get("remote_urls")):
            raise UploadRecoveryError("체크포인트의 썸네일 완료 증거가 불완전합니다. 기존 영상부터 확인하세요.")
    return checkpoint


def verify_existing_video(yt, checkpoint: dict, identity: dict, body: dict) -> dict:
    if checkpoint["identity"] != identity:
        raise UploadRecoveryError("체크포인트의 영상 파일·메타데이터·채널이 현재 요청과 다릅니다. 새 업로드 금지.")
    vid = checkpoint["video_id"]
    items = yt.videos().list(
        part="snippet,status,processingDetails", id=vid,
    ).execute().get("items") or []
    if len(items) != 1 or items[0].get("id") != vid:
        raise UploadRecoveryError("체크포인트의 기존 영상을 조회하지 못했습니다. 새 업로드 금지.")
    remote = items[0]
    snippet = remote.get("snippet") or {}
    if snippet.get("channelId") != identity["channel_id"]:
        raise UploadRecoveryError("기존 영상의 소유 채널 ID가 다릅니다. 새 업로드 금지.")
    for key, expected in body["snippet"].items():
        actual = snippet.get(key, [] if key == "tags" else None)
        if key == "tags":
            actual, expected = sorted(actual), sorted(expected)
        if actual != expected:
            raise UploadRecoveryError(f"기존 영상의 원격 메타데이터 불일치: {key}. 수동 확인이 필요합니다.")
    status = remote.get("status") or {}
    processing = remote.get("processingDetails", {}).get("processingStatus")
    if (status.get("uploadStatus") not in {"uploaded", "processed"}
            or processing in {"failed", "terminated"}):
        raise UploadRecoveryError("기존 영상의 업로드·처리 상태를 확인하지 못했습니다. 새 업로드 금지.")
    for key in ("selfDeclaredMadeForKids", "containsSyntheticMedia"):
        if status.get(key) != body["status"][key]:
            raise UploadRecoveryError(f"기존 영상의 원격 설정 불일치: {key}. 수동 확인이 필요합니다.")
    # 예약/공개 상태는 별도 상태 변경 도구가 바꿀 수 있다. 재개가 이를 덮어쓰지 않는다.
    print(f"  기존 영상 : {vid} / 공개 {status.get('privacyStatus')} / 처리 {processing}")
    return remote


def upload(
    yt,
    video: Path,
    body: dict,
    thumb: Path | None,
    checkpoint_path: Path | None = None,
    *,
    channel_id: str | None = None,
) -> tuple[str, dict | None]:
    checkpoint_path = checkpoint_path or video.parent / "youtube.upload.checkpoint.json"
    checkpoint = read_upload_checkpoint(checkpoint_path)
    owner = channel_id or channel_identity(yt)[0]
    identity = upload_identity(video, body, owner)
    thumb_hash = _sha256(thumb) if thumb else None
    if checkpoint is not None:
        remote = verify_existing_video(yt, checkpoint, identity, body)
        if checkpoint.get("thumbnail_sha256") != thumb_hash:
            raise UploadRecoveryError("체크포인트 이후 썸네일이 달라졌습니다. 기존 영상용 썸네일 변경 도구를 사용하세요.")
        vid = checkpoint["video_id"]
        thumbnail_result = checkpoint.get("thumbnail_result")
        if thumb and isinstance(thumbnail_result, dict) and thumbnail_result.get("verified"):
            if not remote["snippet"].get("thumbnails"):
                raise UploadRecoveryError("기존 영상의 원격 썸네일을 조회하지 못했습니다.")
            return vid, thumbnail_result
    else:
        from googleapiclient.errors import HttpError
        from googleapiclient.http import MediaFileUpload

        media = MediaFileUpload(str(video), chunksize=8 * 1024 * 1024,
                                resumable=True, mimetype="video/mp4")
        checkpoint = {
            "version": 2, "status": "UPLOAD_OUTCOME_UNKNOWN", "identity": identity,
            "video_id": None, "video": str(video),
            "thumbnail": str(thumb) if thumb else None, "thumbnail_sha256": thumb_hash,
        }
        # 요청 전 의도를 영속화한다. 응답 유실/강제 종료 뒤에도 신규 insert를 막는다.
        _write_upload_checkpoint(checkpoint_path, exclusive=True, **checkpoint)
        req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
        print("\n  업로드 중...")
        resp, last, errors = None, -1, 0
        while resp is None:
            try:
                status, resp = req.next_chunk(num_retries=0)
            except HttpError as exc:
                errors += 1
                checkpoint.update(retry_errors=errors, last_http_status=exc.resp.status)
                _write_upload_checkpoint(checkpoint_path, **checkpoint)
                if exc.resp.status not in (500, 502, 503, 504):
                    raise
                if errors >= UPLOAD_MAX_ATTEMPTS:
                    raise UploadRecoveryError(
                        f"서버 오류 {UPLOAD_MAX_ATTEMPTS}회로 재시도를 중단했습니다. "
                        "체크포인트를 보존했습니다. 기존 업로드 결과 확인 전 새 업로드 금지."
                    ) from exc
                delay = min(UPLOAD_BACKOFF_SECONDS * 2 ** (errors - 1), UPLOAD_BACKOFF_MAX_SECONDS)
                print(f"    일시 오류 {exc.resp.status} - {delay}초 후 같은 요청 재시도 ({errors}/{UPLOAD_MAX_ATTEMPTS - 1})")
                time.sleep(delay)
                continue
            if status:
                pct = int(status.progress() * 100)
                if pct >= last + 10:
                    print(f"    {pct:3d}%")
                    last = pct
        if not isinstance(resp, dict) or not isinstance(resp.get("id"), str) or not resp["id"].strip():
            raise UploadRecoveryError("업로드 응답에 영상 ID가 없습니다. 기존 업로드 결과 확인 전 새 업로드 금지.")
        vid = resp["id"]
        checkpoint.update(status="VIDEO_UPLOADED_THUMBNAIL_PENDING", video_id=vid)
        _write_upload_checkpoint(checkpoint_path, **checkpoint)
        print(f"    100%\n\n  영상 ID : {vid}")
        print(f"  주소     : https://youtu.be/{vid}")
        thumbnail_result = None

    if thumb:
        thumbnail_result = set_and_verify_thumbnail(yt, vid, thumb)
        checkpoint.update(status="THUMBNAIL_APPLIED_VERIFIED", thumbnail_result=thumbnail_result)
        _write_upload_checkpoint(checkpoint_path, **checkpoint)
    return vid, thumbnail_result


def main() -> int:
    ap = argparse.ArgumentParser(description="유튜브 업로드 (Data API v3)")
    ap.add_argument("episode", nargs="?", type=Path)
    ap.add_argument("--run", action="store_true", help="실제로 올린다 (없으면 점검만)")
    ap.add_argument("--auth", action="store_true", help="최초 1회 로그인만 하고 끝낸다")
    ap.add_argument("--token", type=Path, default=TOKEN,
                    help="기존 OAuth token.json 경로 (기본: 저장소 루트)")
    ap.add_argument("--client-secret", dest="client_secret", type=Path, default=SECRETS,
                    help="OAuth client_secret JSON 경로 (기본: 저장소 루트에서 자동 검색)")
    ap.add_argument("--공개", dest="privacy",
                    default=CFG.get("업로드.기본공개상태", "비공개"),
                    choices=["비공개", "일부공개", "공개", "예약"])
    ap.add_argument("--시각", dest="when", default=None,
                    help='예약 시각 KST. 생략 또는 auto면 채널 고정 정책(다음날 16:00)')
    ap.add_argument("--예약정책예외", action="store_true",
                    help="사용자가 명시적으로 다른 예약 시각을 승인한 경우에만 사용")
    ap.add_argument("--영상", dest="video", type=Path, default=None)
    ap.add_argument("--썸네일", dest="thumb", type=Path, default=None)
    ap.add_argument("--재생목록", dest="playlist", default=None,
                    help="기본값은 채널설정.json 의 업로드.재생목록")
    args = ap.parse_args()

    if args.auth:
        yt = service(args.token, args.client_secret)
        title = whoami(yt)
        it = yt.channels().list(part="statistics", mine=True).execute()["items"][0]
        print(f"\n  채널   : {title}")
        print(f"  구독자 : {it['statistics'].get('subscriberCount', '비공개')}")
        print(f"  영상   : {it['statistics'].get('videoCount', 0)}편")

        want = CFG.get("업로드.채널명", "") or CFG.get("채널.이름", "")
        if want and title.strip() != want.strip():
            print(f"\n  ★ 기대한 채널은 '{want}' 입니다. 계정을 잘못 고른 것 같습니다.")
            print(f"     token.json 을 지우고 --auth 를 다시 하세요:\n       {args.token}\n")
            return 1
        print(f"\n  '{want}' 확인. 이제 업로드할 수 있습니다.\n" if want else "")
        return 0

    if not args.episode:
        sys.exit("[에러] 에피소드 폴더를 지정하세요. (--auth 는 예외)")
    ep = args.episode.resolve()
    if not ep.exists():
        sys.exit(f"[에러] 폴더가 없습니다: {ep}")

    m = load_meta(ep)
    video = args.video or find_video(ep)
    thumb = args.thumb or next((p for p in (ep / "썸네일.jpg", ep / "썸네일.png")
                                if p.exists()), None)
    playlist = args.playlist or CFG.get("업로드.재생목록", "")

    privacy = {"비공개": "private", "일부공개": "unlisted",
               "공개": "public", "예약": "private"}[args.privacy]
    if args.privacy == "공개" and CFG.get("업로드.즉시공개금지", True):
        sys.exit("[에러] 채널 정책상 즉시 공개는 금지됩니다. 비공개 업로드 뒤 다음날 16:00로 예약하세요.")
    publish_at = None
    if args.privacy == "예약":
        dt = resolve_publish_datetime(
            args.when, allow_policy_override=args.예약정책예외,
        )
        args.when = dt.strftime("%Y-%m-%d %H:%M")
        if dt <= datetime.now(KST):
            sys.exit(f"[에러] 예약 시각이 과거입니다: {dt:%Y-%m-%d %H:%M} KST")
        publish_at = dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ── 점검 ────────────────────────────────────────────
    if video and video.exists():
        vtxt = f"{video.name}  ({video.stat().st_size / 1048576:.1f}MB)"
    elif video:
        vtxt = f"★ 없음: {video}"
    else:
        vtxt = "★ 없음"
    sched = f"  -> {args.when} KST 예약" if publish_at else ""

    print(f"\n에피소드 : {ep.name}")
    print(f"제목     : {m['제목']}  ({len(m['제목'])}자)")
    print(f"설명     : {len(m['설명'])}자 · 태그 {len(m.get('태그', []))}개")
    print(f"영상     : {vtxt}")
    print(f"썸네일   : {thumb.name if thumb else '없음 (자동 프레임 사용)'}")
    print(f"공개     : {args.privacy}{sched}")
    print(f"카테고리 : {CFG.get('업로드.카테고리ID')} · 아동용 {CFG.get('업로드.아동용')}")
    print(f"재생목록 : {playlist or '없음'}")
    q = Q_UPLOAD + (Q_THUMB if thumb else 0) + (Q_PLAYLIST if playlist else 0)
    print(f"쿼터     : {q} / 10,000")

    bad = check_release_status(ep) + check_meta(m, ep) + check_thumb(thumb)
    if not video or not video.exists():
        bad.append("CapCut 게시 마스터를 못 찾았습니다. *_capcut.mp4로 내보내고 마감 잠금을 만드세요.")
    else:
        final_lock = validate_capcut_lock(ep, video)
        bad.extend(f"CapCut 마감: {failure}" for failure in final_lock.failures)
    checkpoint = ep / "youtube.upload.checkpoint.json"
    try:
        previous = read_upload_checkpoint(checkpoint)
        if (previous and previous["status"] == "PACKAGING_COMPLETE"
                and previous.get("playlist", "") != playlist):
            bad.append("완료한 체크포인트와 재생목록 요청이 다릅니다. 기존 영상의 재생목록을 직접 확인하세요.")
    except UploadRecoveryError as exc:
        bad.append(str(exc))
    if bad:
        print("\n  ★ 게이트 위반")
        for b in bad:
            print(f"    - {b}")
        print()
        return 1
    print("\n  게이트 통과.")

    if not args.run:
        print("  (점검만 했습니다. 실제로 올리려면 --run)\n")
        return 0

    print("\n  변형·합성 콘텐츠 고지 : API로 자동 적용")

    yt = service(args.token, args.client_secret)

    # ★ 계정이 여러 개면 엉뚱한 채널에 올라가는 게 최악이다. 올리기 직전에 확인한다.
    owner, title = channel_identity(yt)
    want = CFG.get("업로드.채널명", "") or CFG.get("채널.이름", "")
    print(f"\n  대상 채널 : {title}")
    if want and title.strip() != want.strip():
        print(f"\n  ★ 중단합니다. 기대한 채널은 '{want}' 인데 토큰은 '{title}' 을 물고 있습니다.")
        print(f"     token.json 을 지우고 --auth 를 다시 하세요:\n       {args.token}\n")
        return 1

    try:
        vid, thumbnail_result = upload(
            yt, video, build_body(m, privacy, publish_at), thumb, checkpoint,
            channel_id=owner,
        )
        if previous and previous["status"] == "PACKAGING_COMPLETE":
            print("\n  기존 업로드 완료 기록과 원격 영상을 확인했습니다. 새 업로드 없음.")
            print(f"  스튜디오 : https://studio.youtube.com/video/{vid}/edit\n")
            return 0
        if playlist:
            add_to_playlist(yt, vid, playlist)
    except UploadRecoveryError as exc:
        print(f"\n  ★ 업로드 중단: {exc}\n")
        return 1

    (ep / "07.업로드결과.json").write_text(json.dumps(
        {"video_id": vid, "url": f"https://youtu.be/{vid}",
         "제목": m["제목"], "공개": args.privacy, "예약": args.when,
         "재생목록": playlist,
         "합성콘텐츠고지": bool(CFG.get("업로드.합성콘텐츠고지", True)),
         "썸네일": thumbnail_result,
         "올린시각": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"),
         "남은일": ["첫 댓글 고정"]},
        ensure_ascii=False, indent=1), encoding="utf-8")
    completed = read_upload_checkpoint(checkpoint)
    completed.update(
        status="PACKAGING_COMPLETE", thumbnail_result=thumbnail_result,
        playlist=playlist, publish_at=publish_at,
    )
    _write_upload_checkpoint(checkpoint, **completed)

    print("\n  남은 일 : 첫 댓글 고정 (07-2)")
    print(f"  스튜디오 : https://studio.youtube.com/video/{vid}/edit\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
