#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""실물 유물 픽셀을 재생성하지 않고 확대·색분리·배경감광만 적용한다."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


def feathered_artifact_mask(size: tuple[int, int]) -> Image.Image:
    """중앙 유물과 바닥 접점을 감싸는 넓고 부드러운 선택 마스크."""
    width, height = size
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(
        (
            int(width * 0.12), int(height * 0.20),
            int(width * 0.88), int(height * 1.05),
        ),
        fill=255,
    )
    return mask.filter(ImageFilter.GaussianBlur(int(width * 0.075)))


def top_title_shade(size: tuple[int, int], end_ratio: float = 0.29) -> Image.Image:
    width, height = size
    end = max(1, int(height * end_ratio))
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    for y in range(end):
        ratio = y / end
        draw.line((0, y, width, y), fill=int(150 * (1.0 - ratio) ** 1.5))
    return mask


def emphasize(source: Path, output: Path, scale: float) -> None:
    image = Image.open(source).convert("RGB")
    width, height = 1080, 1920
    source_ratio = image.width / image.height
    target_ratio = width / height
    if source_ratio > target_ratio:
        crop_width = round(image.height * target_ratio)
        left = (image.width - crop_width) // 2
        image = image.crop((left, 0, left + crop_width, image.height))
    elif source_ratio < target_ratio:
        crop_height = round(image.width / target_ratio)
        top = (image.height - crop_height) // 2
        image = image.crop((0, top, image.width, top + crop_height))
    image = image.resize((width, height), Image.Resampling.LANCZOS)
    if not 1.0 <= scale <= 1.25:
        raise ValueError("확대 배율은 1.00~1.25만 허용합니다")

    scaled = image.resize((round(width * scale), round(height * scale)), Image.Resampling.LANCZOS)
    left = max(0, (scaled.width - width) // 2)
    # 유물의 바닥 접점은 화면 아래에 남기면서 상단 제목 공간을 지킨다.
    source_base_y = int(height * 0.927)
    target_base_y = int(height * 0.994)
    top = max(0, min(scaled.height - height, round(source_base_y * scale - target_base_y)))
    image = scaled.crop((left, top, left + width, top + height))

    mask = feathered_artifact_mask(image.size)
    artifact = ImageEnhance.Color(image).enhance(1.30)
    artifact = ImageEnhance.Contrast(artifact).enhance(1.13)
    artifact = ImageEnhance.Brightness(artifact).enhance(1.045)
    artifact = ImageEnhance.Sharpness(artifact).enhance(1.22)

    background = ImageEnhance.Brightness(image).enhance(0.88)
    background = ImageEnhance.Color(background).enhance(0.92)
    composed = Image.composite(artifact, background, mask)
    composed = Image.composite(
        Image.new("RGB", composed.size, (0, 0, 0)),
        composed,
        top_title_shade(composed.size),
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    composed.save(output, format="PNG", optimize=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="실물형태 잠금 썸네일 유물 강조")
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--scale", type=float, default=1.14)
    args = parser.parse_args()
    emphasize(args.source.resolve(), args.output.resolve(), args.scale)
    print(f"유물 형상 유지 확대·색분리 완료 → {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
