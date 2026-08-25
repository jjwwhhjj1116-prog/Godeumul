#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
[고대유물의 비밀] 7단계 보조 — 댓글 읽기 · 답글

고증 채널은 댓글에서 사실 지적이 들어온다. 그게 이 채널의 가장 중요한 신호다.
방치하면 신뢰가 깎이고, 잘 답하면 오히려 전문성이 쌓인다.

  python tools/comments.py                       # 채널 전체 새 댓글 훑기
  python tools/comments.py --영상 s006eQm-4l4    # 한 영상만
  python tools/comments.py --초안                # 답글 초안까지 뽑기
  python tools/comments.py --답글 <댓글id> --내용 "..."         # 점검만
  python tools/comments.py --답글 <댓글id> --내용 "..." --run   # 실제 게시

★ 답글은 **공개 게시물**이다. 기본은 점검이고 `--run` 이 있어야 올라간다.
  초안은 사람이 읽고 승인한 뒤에 올린다. 자동 게시하지 않는다.

필요 스코프: youtube.force-ssl (readonly 로는 commentThreads 가 403)
스코프를 바꿨으면 token.json 을 지우고 --auth 를 다시 한다.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _config import load
from youtube_upload import service, whoami

CFG = load()
ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "산출물" / "댓글기록.json"

# 사실 지적으로 보이는 신호 — 고증 채널에서 최우선으로 봐야 할 댓글
FACT_HINT = (
    "틀렸", "아닌데", "아닙니다", "잘못", "오류", "사실이", "근거", "출처",
    "실제로는", "정확히", "녹는점", "연대", "고증", "왜곡", "가짜", "거짓",
)
QUESTION_HINT = ("?", "궁금", "알려주", "뭔가요", "인가요", "일까")


def classify(text: str) -> str:
    t = text.replace(" ", "")
    if any(k in t for k in FACT_HINT):
        return "사실지적"
    if any(k in text for k in QUESTION_HINT):
        return "질문"
    return "일반"


def fetch(yt, video_id: str, max_threads: int = 100) -> list[dict]:
    out, tok = [], None
    while len(out) < max_threads:
        r = yt.commentThreads().list(
            part="snippet,replies", videoId=video_id,
            maxResults=min(100, max_threads - len(out)),
            order="time", textFormat="plainText", pageToken=tok).execute()
        for t in r.get("items", []):
            c = t["snippet"]["topLevelComment"]["snippet"]
            out.append({
                "id": t["id"],
                "author": c["authorDisplayName"],
                "text": c["textOriginal"],
                "likes": c["likeCount"],
                "at": c["publishedAt"][:16].replace("T", " "),
                "replies": t["snippet"]["totalReplyCount"],
                "kind": classify(c["textOriginal"]),
                "mine": [r_["snippet"]["textOriginal"]
                         for r_ in (t.get("replies", {}) or {}).get("comments", [])],
            })
        tok = r.get("nextPageToken")
        if not tok:
            break
    return out


def my_videos(yt, limit: int = 20) -> list[dict]:
    ch = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]
    up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    r = yt.playlistItems().list(part="snippet", playlistId=up,
                                maxResults=limit).execute()
    return [{"id": i["snippet"]["resourceId"]["videoId"],
             "title": i["snippet"]["title"]} for i in r.get("items", [])]


def main() -> int:
    ap = argparse.ArgumentParser(description="댓글 읽기·답글")
    ap.add_argument("--영상", dest="video", default=None, help="영상 ID (없으면 전체)")
    ap.add_argument("--답글", dest="reply_to", default=None, help="답글 달 댓글 ID")
    ap.add_argument("--내용", dest="body", default=None, help="답글 본문")
    ap.add_argument("--run", action="store_true", help="실제로 게시한다")
    ap.add_argument("--초안", dest="draft", action="store_true", help="답글 초안 틀 출력")
    args = ap.parse_args()

    yt = service()

    # ── 답글 게시 ───────────────────────────────────────
    if args.reply_to:
        if not args.body:
            sys.exit("[에러] --내용 이 필요합니다.")
        if len(args.body) > 9000:
            sys.exit("[에러] 답글이 너무 깁니다.")
        print(f"\n대상 댓글 : {args.reply_to}")
        print(f"답글 내용 : {args.body}")
        print(f"길이      : {len(args.body)}자")
        if not args.run:
            print("\n  (점검만 했습니다. 실제로 올리려면 --run)\n")
            return 0
        r = yt.comments().insert(part="snippet", body={"snippet": {
            "parentId": args.reply_to, "textOriginal": args.body}}).execute()
        print(f"\n  게시 완료. 답글 ID {r['id']}\n")
        rec = json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else []
        rec.append({"parent": args.reply_to, "text": args.body, "id": r["id"]})
        LOG.parent.mkdir(parents=True, exist_ok=True)
        LOG.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        return 0

    # ── 읽기 ────────────────────────────────────────────
    print(f"\n채널 : {whoami(yt)}")
    vids = ([{"id": args.video, "title": args.video}] if args.video
            else my_videos(yt))

    total = {"사실지적": 0, "질문": 0, "일반": 0}
    for v in vids:
        try:
            cs = fetch(yt, v["id"])
        except Exception as exc:
            msg = str(exc)
            if "insufficientPermissions" in msg or "403" in msg:
                sys.exit("\n[에러] 스코프가 부족합니다 (force-ssl 필요).\n"
                         "       token.json 을 지우고 --auth 를 다시 하세요:\n"
                         f"       {ROOT / 'token.json'}\n")
            print(f"  {v['title'][:40]} — 조회 실패: {msg[:120]}")
            continue
        if not cs:
            continue
        print(f"\n■ {v['title'][:60]}")
        print(f"  https://youtu.be/{v['id']}  · 댓글 {len(cs)}개")
        for c in sorted(cs, key=lambda x: (x["kind"] != "사실지적", -x["likes"])):
            total[c["kind"]] += 1
            mark = {"사실지적": "★", "질문": "?", "일반": " "}[c["kind"]]
            done = "  [답글함]" if c["mine"] else ""
            print(f"\n  {mark} {c['author']} · 좋아요 {c['likes']} · {c['at']}{done}")
            for line in c["text"].splitlines():
                print(f"     {line}")
            print(f"     [id] {c['id']}")
            for m in c["mine"]:
                print(f"       ↳ (우리) {m[:100]}")

    print(f"\n{'─'*60}")
    print(f"사실지적 {total['사실지적']} · 질문 {total['질문']} · 일반 {total['일반']}")

    if args.draft:
        print("""
답글 원칙 (고증 채널)
  1. 지적이 맞으면 **먼저 인정한다.** "맞습니다. 제가 틀렸습니다."
  2. 그다음 정확한 값과 **출처**를 댄다. 출처 없으면 "확인해보겠습니다"
  3. 변명하지 않는다. 길게 쓰지 않는다. 3줄 이내
  4. 틀린 지적이면 근거를 대되 **상대를 깎지 않는다**
  5. 심각한 오류면 답글로 끝내지 말고 **설명란에도 정정**을 넣는다

게시:
  python tools/comments.py --답글 <id> --내용 "..."        # 점검
  python tools/comments.py --답글 <id> --내용 "..." --run  # 게시
""")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
