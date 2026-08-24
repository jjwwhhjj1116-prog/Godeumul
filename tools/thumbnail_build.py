#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
[고대유물의 비밀] 6단계 — 썸네일 자동 합성

매번 GPT에 붙여넣는 건 자동화가 아니다. 이 스크립트는 <배경 이미지 + 한글 텍스트>를
로컬에서 합성한다. 이미지 생성 모델은 한글을 거의 항상 깨뜨리므로,
글자는 PIL 로 직접 그리는 편이 항상 깨끗하고 재현 가능하다.

  배경(유물 히어로샷, 글자 없음)  ← Flow 로 뽑거나 기존 컷 재활용
  + 상단 채널명 + 초대형 유물명   ← 여기서 합성
  = 1080x1920 썸네일

배경 프롬프트는 06 지침의 것을 쓰되 [텍스트] 항목만 빼면 된다.

사용법
  python tools/thumbnail_build.py 산출물/EP01_진시황릉 --title "진시황릉"
  python tools/thumbnail_build.py ... --bg 산출물/EP01_진시황릉/images/001.jpg
  python tools/thumbnail_build.py ... --title "진시황릉" --dry     # 배경 없이 미리보기
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from _config import load

CFG = load()
ROOT = Path(__file__).resolve().parent.parent


def hex2rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def fit_font(path: str, text: str, max_w: int, start: int) -> ImageFont.FreeTypeFont:
    """max_w 안에 들어갈 때까지 크기를 줄인다."""
    size = start
    while size > 20:
        f = ImageFont.truetype(path, size)
        if f.getbbox(text)[2] - f.getbbox(text)[0] <= max_w:
            return f
        size -= 4
    return ImageFont.truetype(path, 20)


def draw_outlined(d: ImageDraw.ImageDraw, xy, text, font, fill, outline, width: int) -> None:
    x, y = xy
    for dx in range(-width, width + 1, max(1, width // 3)):
        for dy in range(-width, width + 1, max(1, width // 3)):
            if dx or dy:
                d.text((x + dx, y + dy), text, font=font, fill=outline)
    d.text((x, y), text, font=font, fill=fill)


def gold_gradient(size: tuple[int, int], top: str, bottom: str) -> Image.Image:
    w, h = size
    g = Image.new("RGB", (1, h))
    t, b = hex2rgb(top), hex2rgb(bottom)
    for y in range(h):
        r = y / max(1, h - 1)
        g.putpixel((0, y), tuple(int(t[i] + (b[i] - t[i]) * r) for i in range(3)))
    return g.resize(size)


def main() -> int:
    ap = argparse.ArgumentParser(description="썸네일 합성기")
    ap.add_argument("episode", type=Path)
    ap.add_argument("--title", required=True, help="유물명 (초대형 골드 텍스트)")
    ap.add_argument("--bg", type=Path, default=None, help="배경 이미지 (기본: 자산/썸네일배경.png → images/001.jpg)")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--dry", action="store_true", help="배경 없이 단색으로 미리보기")
    args = ap.parse_args()

    ep = args.episode.resolve()
    W, H = CFG.get("출력.해상도", [1080, 1920])
    T = CFG.get("썸네일", {})
    brand = T.get("상단문구", CFG.get("채널.이름", ""))

    # ── 배경 ────────────────────────────────────────────
    if args.dry:
        base = Image.new("RGB", (W, H), (18, 14, 8))
    else:
        bg = args.bg
        if bg is None:
            for cand in (ep / "썸네일배경.png", ep / "썸네일배경.jpg",
                         ROOT / "자산썸네일배경.png", ep / "images" / "001.jpg"):
                if cand.exists():
                    bg = cand
                    break
        if bg is None or not Path(bg).exists():
            sys.exit("[에러] 배경 이미지를 못 찾았습니다. --bg 로 지정하세요.\n"
                     "       (유물 히어로샷, 글자 없이 뽑은 것)")
        base = Image.open(bg).convert("RGB")
        # 9:16 로 센터 크롭
        sr, tr = base.width / base.height, W / H
        if sr > tr:
            nw = int(base.height * tr)
            base = base.crop(((base.width - nw) // 2, 0, (base.width + nw) // 2, base.height))
        else:
            nh = int(base.width / tr)
            base = base.crop((0, (base.height - nh) // 2, base.width, (base.height + nh) // 2))
        base = base.resize((W, H), Image.LANCZOS)

    # 상단을 어둡게 깔아 글자가 뜨게 한다
    band_h = int(H * T.get("텍스트영역_상단비율", 0.28))
    shade = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(shade)
    for y in range(band_h):
        sd.line([(0, y), (W, y)], fill=int(215 * (1 - y / band_h) ** 0.8))
    base = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), base, shade)

    d = ImageDraw.Draw(base)
    margin = int(W * 0.06)

    # ── 상단 채널명 ─────────────────────────────────────
    bf = fit_font(T.get("상단폰트"), brand, W - margin * 2, int(H * 0.032))
    bw = bf.getbbox(brand)[2] - bf.getbbox(brand)[0]
    by = int(H * 0.035)
    draw_outlined(d, ((W - bw) // 2, by), brand, bf, (255, 255, 255), (0, 0, 0), 5)

    # ── 초대형 유물명 (골드 그라데이션) ──────────────────
    title = args.title
    tf = fit_font(T.get("제목폰트"), title, int(W * 0.90), int(H * 0.13))
    bb = tf.getbbox(title)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    tx, ty = (W - tw) // 2 - bb[0], by + int(H * 0.055)

    # 글자 마스크 → 그라데이션을 채운다
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).text((tx, ty), title, font=tf, fill=255)
    grad = gold_gradient((W, H), T.get("제목색_위", "#FFF275"), T.get("제목색_아래", "#D4AF37"))

    # 외곽선 + 그림자 먼저
    ol = Image.new("L", (W, H), 0)
    od = ImageDraw.Draw(ol)
    for dx in range(-9, 10, 3):
        for dy in range(-9, 10, 3):
            od.text((tx + dx, ty + dy), title, font=tf, fill=255)
    sh = ol.filter(ImageFilter.GaussianBlur(10))
    base = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), base,
                           sh.point(lambda v: int(v * 0.75)))
    base = Image.composite(Image.new("RGB", (W, H), hex2rgb(T.get("제목외곽선", "#1A1206"))),
                           base, ol)
    base = Image.composite(grad, base, mask)

    out = args.out or (ep / "썸네일.jpg")
    base.save(out, quality=94, subsampling=0)

    print(f"\n제목   : {title}")
    print(f"채널명 : {brand}")
    print(f"크기   : {W}x{H}  ({out.stat().st_size // 1024} KB)")
    print(f"글자   : 제목 {tf.size}px / 채널명 {bf.size}px")
    if tw > W * 0.92:
        print("★ 제목이 화면 폭에 꽉 찹니다. 더 짧은 유물명을 권합니다.")
    print(f"\n  썸네일 → {out}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
