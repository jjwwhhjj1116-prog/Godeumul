#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""내 채널의 기존 영상 상태를 보존적으로 수정하고 다시 검증한다."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from youtube_upload import (
    CFG, KST, SECRETS, TOKEN, resolve_publish_datetime, service, whoami,
)


WRITABLE_STATUS_FIELDS = (
    "privacyStatus",
    "publishAt",
    "license",
    "embeddable",
    "publicStatsViewable",
    "selfDeclaredMadeForKids",
    "containsSyntheticMedia",
)


def writable_status(status: dict) -> dict:
    """읽기 전용 필드를 빼고 기존의 쓰기 가능한 설정만 보존한다."""
    return {key: status[key] for key in WRITABLE_STATUS_FIELDS if key in status}


def main() -> int:
    ap = argparse.ArgumentParser(description="기존 유튜브 영상 상태 수정")
    ap.add_argument("video_id")
    ap.add_argument("--synthetic", choices=["yes", "no"])
    ap.add_argument(
        "--schedule", nargs="?", const="auto",
        help='예약 시각 KST. 값 생략 또는 auto면 채널 정책대로 다음날 16:00',
    )
    ap.add_argument("--token", type=Path, default=TOKEN)
    ap.add_argument("--client-secret", dest="client_secret", type=Path, default=SECRETS)
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()

    if args.synthetic is None and args.schedule is None:
        sys.exit("[에러] --synthetic 또는 --schedule 중 하나는 필요합니다.")

    yt = service(args.token.resolve(), args.client_secret.resolve())
    channel = whoami(yt)
    expected = CFG.get("업로드.채널명", "") or CFG.get("채널.이름", "")
    if expected and channel.strip() != expected.strip():
        sys.exit(f"[에러] 채널 불일치: 현재 '{channel}', 기대 '{expected}'")

    mine = yt.channels().list(part="id", mine=True).execute().get("items") or []
    owner = mine[0]["id"] if mine else ""
    items = yt.videos().list(
        part="snippet,status,processingDetails", id=args.video_id,
    ).execute().get("items") or []
    if not items:
        sys.exit("[에러] 영상을 찾지 못했습니다.")
    current = items[0]
    if current["snippet"].get("channelId") != owner:
        sys.exit("[에러] 이 토큰이 소유한 영상이 아닙니다.")

    status = writable_status(current["status"])
    if args.synthetic is not None:
        status["containsSyntheticMedia"] = args.synthetic == "yes"
    if args.schedule:
        dt = resolve_publish_datetime(args.schedule)
        if dt <= datetime.now(KST):
            sys.exit(f"[에러] 예약 시각이 과거입니다: {dt:%Y-%m-%d %H:%M} KST")
        status["privacyStatus"] = "private"
        status["publishAt"] = dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    print(json.dumps({
        "channel": channel,
        "video_id": args.video_id,
        "before": writable_status(current["status"]),
        "after": status,
        "processing": current.get("processingDetails", {}).get("processingStatus"),
    }, ensure_ascii=False, indent=2))
    if not args.run:
        print("\n점검만 완료. 실제 변경은 --run 을 붙이세요.")
        return 0

    yt.videos().update(
        part="status", body={"id": args.video_id, "status": status},
    ).execute()
    verified = yt.videos().list(part="status", id=args.video_id).execute()["items"][0]["status"]
    print("\n적용 후 검증:")
    print(json.dumps(writable_status(verified), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
