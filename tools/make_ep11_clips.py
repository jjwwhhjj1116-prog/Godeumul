#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate exact 8.0s / 10.0s 1080x1920 30fps MP4 clips for EP11 from 9:16 PBR diorama images.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EP_DIR = ROOT / "산출물" / "EP11_네브라스카이디스크"
IMG_DIR = EP_DIR / "images"
CLIP_DIR = EP_DIR / "clips"
CLIP_DIR.mkdir(exist_ok=True)

MOTIONS = {
    1:  (8.0, 1.00, 1.15, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)+on*0.4"),   # dive to soil
    2:  (8.0, 1.00, 1.12, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),          # macro push
    3:  (8.0, 1.00, 1.10, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)-on*0.3"),   # pan/tilt across village
    4:  (8.0, 1.00, 1.12, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),          # top-down push
    5:  (8.0, 1.00, 1.12, "iw/2-(iw/zoom/2)+on*0.2", "ih/2-(ih/zoom/2)"),   # laser tracking
    6:  (8.0, 1.00, 1.12, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),          # artisan push
    7:  (8.0, 1.00, 1.14, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)+on*0.5"),   # tilt down into pit
    8:  (8.0, 1.00, 1.12, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)+on*0.3"),   # briefcase push
    9:  (8.0, 1.00, 1.12, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),          # lab microscope push
    10: (8.0, 1.00, 1.12, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),          # 3D scan push
    11: (8.0, 1.00, 1.12, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)-on*0.3"),   # sun paths tilt
    12: (8.0, 1.00, 1.12, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)+on*0.4"),   # trade map pan
    13: (8.0, 1.00, 1.12, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),          # calendar rings push
    14: (8.0, 1.00, 1.12, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),          # calipers push
    15: (8.0, 1.00, 1.12, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)-on*0.4"),   # tilt up to sky
    16: (8.0, 1.00, 1.12, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),          # Stonehenge push
    17: (10.0, 1.10, 1.00, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),         # showcase pull-out
    18: (10.0, 1.00, 1.14, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)+on*0.4"),  # burial pit dive
    19: (10.0, 1.00, 1.18, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)-on*0.6"),  # crane up to cosmos
}

def make_clip(scene_num: int):
    img_path = IMG_DIR / f"{scene_num:03d}.png"
    out_path = CLIP_DIR / f"{scene_num:03d}.mp4"
    if not img_path.exists():
        print(f"[ERR] Image missing: {img_path}")
        return False

    dur, z_start, z_end, x_expr, y_expr = MOTIONS.get(scene_num, (8.0, 1.0, 1.1, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"))
    total_frames = int(dur * 30)
    z_step = (z_end - z_start) / total_frames
    z_min = min(z_start, z_end)
    z_max = max(z_start, z_end)

    vf = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"zoompan=z='min(max(zoom+{z_step:.7f},{z_min:.3f}),{z_max:.3f})':"
        f"x='{x_expr}':y='{y_expr}':d={total_frames}:s=1080x1920:fps=30"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(img_path),
        "-vf", vf,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        "-crf", "18",
        "-t", f"{dur:.1f}",
        str(out_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if res.returncode != 0:
        print(f"[FAIL] Scene {scene_num:03d}: {res.stderr[-400:]}")
        return False
    print(f"[OK] Scene {scene_num:03d}.mp4 ({dur:.1f}s)")
    return True

if __name__ == "__main__":
    print(f"Generating 19 exact-length cinematic clips in {CLIP_DIR}...")
    for i in range(1, 20):
        make_clip(i)
    print("All clips generated successfully!")
