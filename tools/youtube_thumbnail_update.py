#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""이미 올라간 유튜브 영상의 썸네일만 안전하게 교체한다."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from PIL import Image

from youtube_upload import CFG, SECRETS, THUMB_MAX, TOKEN, service, whoami


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="기존 유튜브 영상 썸네일 교체")
    ap.add_argument("video_id")
    ap.add_argument("thumbnail", type=Path)
    ap.add_argument("--token", type=Path, default=TOKEN)
    ap.add_argument("--client-secret", type=Path, default=SECRETS)
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()

    thumb = args.thumbnail.resolve()
    if not thumb.exists():
        sys.exit(f"[에러] 썸네일이 없습니다: {thumb}")
    if thumb.stat().st_size > THUMB_MAX:
        sys.exit(f"[에러] 썸네일이 2MB를 넘습니다: {thumb.stat().st_size:,} bytes")
    with Image.open(thumb) as im:
        if im.size != (1080, 1920):
            sys.exit(f"[에러] 1080x1920이 아닙니다: {im.size[0]}x{im.size[1]}")

    digest = sha256(thumb)
    print(f"영상 ID : {args.video_id}")
    print(f"썸네일  : {thumb}")
    print(f"SHA-256 : {digest}")
    if not args.run:
        print("\n점검만 완료. 실제 교체는 --run 을 붙이세요.")
        return 0

    from googleapiclient.http import MediaFileUpload

    yt = service(args.token.resolve(), args.client_secret.resolve())
    channel = whoami(yt)
    expected = CFG.get("업로드.채널명", "") or CFG.get("채널.이름", "")
    if expected and channel.strip() != expected.strip():
        sys.exit(f"[에러] 채널 불일치: 현재 '{channel}', 기대 '{expected}'")

    mine = yt.channels().list(part="id", mine=True).execute().get("items") or []
    owner = mine[0]["id"] if mine else ""
    videos = yt.videos().list(part="snippet,status", id=args.video_id).execute().get("items") or []
    if not videos:
        sys.exit("[에러] 영상을 찾지 못했습니다.")
    if videos[0]["snippet"].get("channelId") != owner:
        sys.exit("[에러] 이 토큰이 소유한 영상이 아닙니다.")

    yt.thumbnails().set(
        videoId=args.video_id,
        media_body=MediaFileUpload(str(thumb), mimetype="image/jpeg"),
    ).execute()
    print(f"\n교체 완료 : {channel} / https://youtube.com/shorts/{args.video_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
