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
  python tools/youtube_upload.py 산출물/EP01_진시황릉 --run --공개 예약 --시각 "2026-08-25 19:00"
  python tools/youtube_upload.py 산출물/EP01_진시황릉 --run --공개 공개

메타데이터는 에피소드 폴더의 06.메타.json 에서 읽는다.
  {"제목": "...", "설명": "...", "태그": ["..."]}
"""

from __future__ import annotations

import argparse
import json
import sys
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
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())              # 만료돼도 조용히 갱신된다
        token_path.write_text(creds.to_json(), encoding="utf-8")
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


def whoami(yt) -> str:
    """토큰이 물고 있는 채널 이름."""
    r = yt.channels().list(part="snippet", mine=True).execute()
    items = r.get("items") or []
    if not items:
        sys.exit("[에러] 이 계정에 유튜브 채널이 없습니다. 채널을 먼저 만드세요.")
    return items[0]["snippet"]["title"]


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
        print(f"  재생목록 : ★ '{name}' 을 못 찾았습니다. 스튜디오에서 직접 추가하세요.")
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
            "license": "youtube",
            "embeddable": True,
        },
    }
    if publish_at:
        body["status"]["publishAt"] = publish_at
    return body


def upload(yt, video: Path, body: dict, thumb: Path | None) -> str:
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    media = MediaFileUpload(str(video), chunksize=8 * 1024 * 1024,
                            resumable=True, mimetype="video/mp4")
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)

    print("\n  업로드 중...")
    resp, last = None, -1
    while resp is None:
        try:
            status, resp = req.next_chunk()
        except HttpError as exc:
            # 5xx 는 재개 가능. 같은 req 로 이어서 올라간다.
            if exc.resp.status in (500, 502, 503, 504):
                print(f"    일시 오류 {exc.resp.status} - 재시도")
                continue
            raise
        if status:
            pct = int(status.progress() * 100)
            if pct >= last + 10:
                print(f"    {pct:3d}%")
                last = pct

    vid = resp["id"]
    print(f"    100%\n\n  영상 ID : {vid}")
    print(f"  주소     : https://youtu.be/{vid}")

    if thumb and thumb.exists():
        yt.thumbnails().set(videoId=vid,
                            media_body=MediaFileUpload(str(thumb))).execute()
        print(f"  썸네일   : {thumb.name} 적용")
    return vid


def main() -> int:
    ap = argparse.ArgumentParser(description="유튜브 업로드 (Data API v3)")
    ap.add_argument("episode", nargs="?", type=Path)
    ap.add_argument("--run", action="store_true", help="실제로 올린다 (없으면 점검만)")
    ap.add_argument("--auth", action="store_true", help="최초 1회 로그인만 하고 끝낸다")
    ap.add_argument("--token", type=Path, default=TOKEN,
                    help="기존 OAuth token.json 경로 (기본: 저장소 루트)")
    ap.add_argument("--client-secret", dest="client_secret", type=Path, default=SECRETS,
                    help="OAuth client_secret JSON 경로 (기본: 저장소 루트에서 자동 검색)")
    ap.add_argument("--공개", dest="privacy", default="비공개",
                    choices=["비공개", "일부공개", "공개", "예약"])
    ap.add_argument("--시각", dest="when", default=None,
                    help='예약 시각 KST. "2026-08-25 19:00"')
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
    publish_at = None
    if args.privacy == "예약":
        if not args.when:
            sys.exit("[에러] --공개 예약 은 --시각 이 필요합니다.")
        dt = datetime.strptime(args.when, "%Y-%m-%d %H:%M").replace(tzinfo=KST)
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

    # 합성 콘텐츠 고지는 API 에 필드가 없다 — 스튜디오에서 켜야 한다.
    print("\n  ※ '변형·합성 콘텐츠' 고지는 API 에 필드가 없습니다.")
    print("     업로드 후 스튜디오에서 한 번 켜야 합니다. (07-3)")

    yt = service(args.token, args.client_secret)

    # ★ 계정이 여러 개면 엉뚱한 채널에 올라가는 게 최악이다. 올리기 직전에 확인한다.
    title = whoami(yt)
    want = CFG.get("업로드.채널명", "") or CFG.get("채널.이름", "")
    print(f"\n  대상 채널 : {title}")
    if want and title.strip() != want.strip():
        print(f"\n  ★ 중단합니다. 기대한 채널은 '{want}' 인데 토큰은 '{title}' 을 물고 있습니다.")
        print(f"     token.json 을 지우고 --auth 를 다시 하세요:\n       {args.token}\n")
        return 1

    vid = upload(yt, video, build_body(m, privacy, publish_at), thumb)
    if playlist:
        add_to_playlist(yt, vid, playlist)

    (ep / "07.업로드결과.json").write_text(json.dumps(
        {"video_id": vid, "url": f"https://youtu.be/{vid}",
         "제목": m["제목"], "공개": args.privacy, "예약": args.when,
         "재생목록": playlist,
         "올린시각": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"),
         "남은일": ["스튜디오에서 합성 콘텐츠 고지 켜기", "첫 댓글 고정"]},
        ensure_ascii=False, indent=1), encoding="utf-8")

    print("\n  남은 일 : (1) 합성 콘텐츠 고지  (2) 첫 댓글 고정 (07-2)")
    print(f"  스튜디오 : https://studio.youtube.com/video/{vid}/edit\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
