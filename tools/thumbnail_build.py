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
  python tools/thumbnail_build.py ... --title "미 이 라" --kicker "마왕퇴 한나라 무덤의"
  python tools/thumbnail_build.py ... --bg 산출물/EP01_진시황릉/images/001.jpg
  python tools/thumbnail_build.py ... --title "진시황릉" --dry     # 배경 없이 미리보기
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

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


def multistop_gradient(size: tuple[int, int], stops: list[tuple[float, str]]) -> Image.Image:
    """채널 레퍼런스처럼 밝고 어두운 금속 띠가 반복되는 세로 그라데이션."""
    w, h = size
    stops = sorted(stops)
    strip = Image.new("RGB", (1, h))
    for y in range(h):
        p = y / max(1, h - 1)
        left, right = stops[0], stops[-1]
        for idx in range(len(stops) - 1):
            if stops[idx][0] <= p <= stops[idx + 1][0]:
                left, right = stops[idx], stops[idx + 1]
                break
        span = max(1e-6, right[0] - left[0])
        r = (p - left[0]) / span
        a, b = hex2rgb(left[1]), hex2rgb(right[1])
        strip.putpixel((0, y), tuple(int(a[i] + (b[i] - a[i]) * r) for i in range(3)))
    return strip.resize((w, h))


def shifted(mask: Image.Image, dx: int, dy: int) -> Image.Image:
    out = Image.new("L", mask.size, 0)
    out.paste(mask, (dx, dy))
    return out


def procedural_gold_texture(size: tuple[int, int]) -> Image.Image:
    """작은 화면에서도 금박/양각으로 읽히는 결정론적 미세 문양."""
    w, h = size
    tex = Image.new("RGBA", size, (0, 0, 0, 0))
    td = ImageDraw.Draw(tex)
    rng = random.Random(240826)

    # 미세한 금박 입자
    for _ in range(max(1500, (w * h) // 900)):
        x, y = rng.randrange(w), rng.randrange(h)
        if rng.random() < 0.55:
            c = (255, 249, 188, rng.randrange(18, 46))
        else:
            c = (118, 65, 4, rng.randrange(12, 34))
        td.point((x, y), fill=c)

    # 레퍼런스의 금속 표면처럼 보이는 옅은 곡선 문양
    step = 72
    for y in range(-step, h + step, step):
        for x in range(-step, w + step, step):
            box = (x, y, x + 58, y + 42)
            td.arc(box, 190, 350, fill=(255, 247, 166, 38), width=2)
            td.arc((x + 22, y + 17, x + 80, y + 59), 10, 170,
                   fill=(111, 59, 2, 28), width=2)
    return tex


def reference_gold_face(size: tuple[int, int], target_y: int, target_h: int,
                        texture_path: Path | None) -> Image.Image:
    """샘플 제목에서 추출한 금박 표면을 반복·반전해 글자 면 전체에 채운다."""
    W, H = size
    if not texture_path or not texture_path.exists():
        local = multistop_gradient(
            (W, max(1, target_h)),
            [(0.0, "#FFF48E"), (0.45, "#F8CE47"), (1.0, "#D69B16")],
        )
    else:
        src = Image.open(texture_path).convert("RGB")
        ratio = target_h / max(1, src.height)
        tile_w = max(24, int(src.width * ratio))
        tile = src.resize((tile_w, max(1, target_h)), Image.LANCZOS)
        local = Image.new("RGB", (W, max(1, target_h)))
        x, n = 0, 0
        while x < W:
            part = ImageOps.mirror(tile) if n % 2 else tile
            local.paste(part, (x, 0))
            x += tile_w
            n += 1
        # 타일 경계만 아주 약하게 누르고 샘플의 금속 대비는 유지한다.
        local = ImageEnhance.Contrast(local.filter(ImageFilter.GaussianBlur(0.25))).enhance(1.08)
    out = Image.new("RGB", (W, H), (0, 0, 0))
    out.paste(local, (0, target_y))
    return out


def draw_reference_gold_title(base: Image.Image, title: str, font_path: str,
                              max_w: int, start_size: int, y: int,
                              style: dict) -> tuple[int, int]:
    """금속 양각 + 검은 외곽선 + 아래로 깊은 3D 돌출 제목을 그린다."""
    W, H = base.size
    font = fit_font(font_path, title, max_w, start_size)
    bb = font.getbbox(title, stroke_width=0)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    tx = (W - tw) // 2 - bb[0]
    ty = y - bb[1]

    face = Image.new("L", (W, H), 0)
    ImageDraw.Draw(face).text((tx, ty), title, font=font, fill=255)

    outline_width = int(style.get("제목외곽선폭", 8))
    rim_width = int(style.get("제목금테두리폭", 3))
    depth_max = int(style.get("제목돌출깊이", 14))
    shadow_xy = style.get("제목그림자오프셋", [6, 17])
    shadow_blur = int(style.get("제목그림자블러", 7))

    outer = Image.new("L", (W, H), 0)
    ImageDraw.Draw(outer).text(
        (tx, ty), title, font=font, fill=255,
        stroke_width=outline_width, stroke_fill=255
    )

    # 샘플처럼 제목 바로 아래에 붙는 짧고 단단한 투영 그림자
    shadow = shifted(outer, int(shadow_xy[0]), int(shadow_xy[1])).filter(
        ImageFilter.GaussianBlur(shadow_blur)
    )
    base.paste((0, 0, 0), mask=shadow.point(lambda v: int(v * 0.72)))

    # 아래쪽으로 쌓이는 3D 돌출부: 먼 층부터 가까운 층 순서
    far = hex2rgb(style.get("제목돌출색_먼쪽", "#090704"))
    near = hex2rgb(style.get("제목돌출색_가까운쪽", "#3A2506"))
    for depth in range(depth_max, 0, -1):
        r = depth / max(1, depth_max)
        color = tuple(int(far[i] + (near[i] - far[i]) * (1 - r)) for i in range(3))
        base.paste(color, mask=shifted(outer, max(2, depth // 3), depth))

    # 두꺼운 먹색 테두리와 얇은 금색 림
    base.paste(hex2rgb(style.get("제목외곽선", "#080603")), mask=outer)
    gold_rim = Image.new("L", (W, H), 0)
    ImageDraw.Draw(gold_rim).text(
        (tx, ty), title, font=font, fill=255,
        stroke_width=rim_width, stroke_fill=255
    )
    base.paste(hex2rgb(style.get("제목금테두리", "#A96908")), mask=gold_rim)

    # 샘플에서 직접 추출한 금박 문양·색·세로 명암을 글자 면에 적용한다.
    texture_setting = style.get("제목금박텍스처")
    texture_path = (ROOT / texture_setting).resolve() if texture_setting else None
    gold_face = reference_gold_face((W, H), y, th, texture_path)
    base.paste(gold_face, mask=face)

    # 위·왼쪽 밝은 날과 아래·오른쪽 내측 그림자로 양각을 완성
    hi = ImageChops.subtract(face, shifted(face, 0, 3)).filter(ImageFilter.GaussianBlur(0.7))
    lo = ImageChops.subtract(face, shifted(face, 0, -4)).filter(ImageFilter.GaussianBlur(1.0))
    base.paste((255, 250, 185), mask=hi.point(lambda v: int(v * 0.88)))
    base.paste((121, 67, 2), mask=lo.point(lambda v: int(v * 0.58)))
    return font.size, tw


def save_youtube_jpeg(image: Image.Image, out: Path, max_bytes: int = 1_950_000) -> None:
    """유튜브 썸네일 2MB 제한 아래가 될 때까지 품질을 안전하게 낮춘다."""
    out.parent.mkdir(parents=True, exist_ok=True)
    for quality in range(94, 79, -2):
        image.convert("RGB").save(out, quality=quality, subsampling=0, optimize=True)
        if out.stat().st_size <= max_bytes:
            return
    image.convert("RGB").save(out, quality=80, subsampling=2, optimize=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="썸네일 합성기")
    ap.add_argument("episode", type=Path)
    ap.add_argument("--title", required=True, help="유물명 (초대형 골드 텍스트)")
    ap.add_argument("--kicker", default=None,
                    help="상단 미스터리 한 줄 (없으면 채널 기본 문구)")
    ap.add_argument("--bg", type=Path, default=None, help="배경 이미지 (기본: 자산/썸네일배경.png → images/001.jpg)")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--dry", action="store_true", help="배경 없이 단색으로 미리보기")
    args = ap.parse_args()

    ep = args.episode.resolve()
    W, H = CFG.get("출력.해상도", [1080, 1920])
    T = CFG.get("썸네일", {})
    brand = args.kicker or T.get("상단문구", CFG.get("채널.이름", ""))

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
    band_h = int(H * T.get("텍스트영역_상단비율", 0.22))
    shade_strength = int(T.get("텍스트영역_암도", 180))
    shade = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(shade)
    for y in range(band_h):
        sd.line([(0, y), (W, y)],
                fill=int(shade_strength * (1 - y / band_h) ** 0.8))
    base = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), base, shade)

    d = ImageDraw.Draw(base)
    margin = int(W * 0.06)

    # ── 상단 채널명 ─────────────────────────────────────
    bf = fit_font(T.get("상단폰트"), brand, W - margin * 2,
                  int(H * T.get("상단문구크기비율", 0.033)))
    bw = bf.getbbox(brand)[2] - bf.getbbox(brand)[0]
    by = int(H * T.get("상단문구Y비율", 0.03))
    draw_outlined(d, ((W - bw) // 2, by), brand, bf, (255, 255, 255), (0, 0, 0), 5)

    # ── 초대형 유물명 (레퍼런스형 금속 양각) ─────────────
    title = args.title
    tf_size, tw = draw_reference_gold_title(
        base,
        title,
        T.get("제목폰트"),
        int(W * T.get("제목최대폭비율", 0.9)),
        int(H * T.get("제목시작크기비율", 0.14)),
        int(H * T.get("제목Y비율", 0.075)),
        T,
    )

    out = args.out or (ep / "썸네일.jpg")
    save_youtube_jpeg(base, out)

    print(f"\n제목   : {title}")
    print(f"채널명 : {brand}")
    print(f"크기   : {W}x{H}  ({out.stat().st_size // 1024} KB)")
    print(f"글자   : 제목 {tf_size}px / 채널명 {bf.size}px")
    if tw > W * 0.92:
        print("★ 제목이 화면 폭에 꽉 찹니다. 더 짧은 유물명을 권합니다.")
    print(f"\n  썸네일 → {out}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
