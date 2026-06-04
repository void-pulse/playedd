#!/usr/bin/env python3
"""Generate Playedd channel banner v2 (dark logo lockup) with Pillow.

Dark charcoal background. The logo's bare stickman face (no red stamp) on the
left, the PLAYEDD wordmark to its right, the pair centered as a group inside
the YouTube safe zone. Face + wordmark rendered in brand off-white so they read
on dark.

The face uses the EXACT geometry from make_playedd.py's avatar (head circle,
dot eyes, dismay mouth). To preserve the avatar's proportions precisely, the
face is drawn at the avatar's native radius (235) on a transparent tile, then
scaled down to fit the banner.
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

random.seed(11)  # same seed family as make_playedd.py for a matching wobble

HERE = Path(__file__).resolve().parent
FONTS = HERE / "fonts"
OUT = HERE / "banner_playedd_v2_2560x1440.png"

CHARCOAL = (26, 26, 26)     # #1A1A1A background
OFFWHITE = (250, 249, 244)  # #FAF9F4 strokes + wordmark

W, H = 2560, 1440
SAFE_W, SAFE_H = 1546, 423
SAFE_L = (W - SAFE_W) // 2      # 507
SAFE_R = SAFE_L + SAFE_W        # 2053
SAFE_T = (H - SAFE_H) // 2      # 508
SAFE_B = SAFE_T + SAFE_H        # 931
CX, CY = W // 2, H // 2         # 1280, 720

AVATAR_R = 235          # native avatar radius (do not change: sets proportions)
FACE_DIAM = 340         # target on-banner face diameter
WORD_SIZE = 205         # PLAYEDD marker size
GAP = 130               # space between face and wordmark


def marker(sz):
    return ImageFont.truetype(str(FONTS / "PermanentMarker.ttf"), sz)


def wline(d, p0, p1, width=8, fill=OFFWHITE, jitter=3, segs=14):
    (x0, y0), (x1, y1) = p0, p1
    pts = []
    for i in range(segs + 1):
        t = i / segs
        pts.append((x0 + (x1 - x0) * t + random.uniform(-jitter, jitter),
                    y0 + (y1 - y0) * t + random.uniform(-jitter, jitter)))
    d.line(pts, fill=fill, width=width, joint="curve")


def wcircle(d, cx, cy, r, width=8, fill=OFFWHITE, jitter=3, segs=40):
    pts = []
    start = random.uniform(0, 0.3)
    for i in range(segs + 1):
        a = start + 2 * math.pi * i / segs
        rr = r + random.uniform(-jitter, jitter)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.line(pts, fill=fill, width=width, joint="curve")


def face(d, cx, cy, r, stroke, mood="dismay"):
    """EXACT face geometry from make_playedd.py, rendered in `stroke` color
    (the original hard-codes INK; here it's parameterized for the dark bg)."""
    wcircle(d, cx, cy, r, width=max(6, r // 12), fill=stroke)
    ex = r * 0.34
    d.ellipse((cx - ex - 9, cy - r * 0.28, cx - ex + 9, cy - r * 0.28 + 18), fill=stroke)
    d.ellipse((cx + ex - 9, cy - r * 0.28, cx + ex + 9, cy - r * 0.28 + 18), fill=stroke)
    if mood == "dismay":
        wline(d, (cx - r * 0.28, cy + r * 0.42), (cx + r * 0.28, cy + r * 0.42),
              width=max(4, r // 18), fill=stroke, jitter=2, segs=6)
    else:
        wline(d, (cx - r * 0.25, cy + r * 0.3), (cx + r * 0.25, cy + r * 0.4),
              width=max(4, r // 18), fill=stroke, jitter=2, segs=6)


def build_face_tile():
    """Draw the bare avatar face at native radius on transparent, then scale to FACE_DIAM."""
    pad = 40
    t = 2 * AVATAR_R + 2 * pad
    tile = Image.new("RGBA", (t, t), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    face(td, t // 2, t // 2, AVATAR_R, stroke=OFFWHITE, mood="dismay")
    scale = FACE_DIAM / (2 * AVATAR_R)
    new = round(t * scale)
    tile = tile.resize((new, new), Image.BICUBIC)
    margin = (new - FACE_DIAM) / 2.0   # transparent margin around the visible face
    return tile, new, margin


def main():
    img = Image.new("RGB", (W, H), CHARCOAL)
    d = ImageDraw.Draw(img)

    tile, tile_px, margin = build_face_tile()

    tf = marker(WORD_SIZE)
    word = "PLAYEDD"
    bb = d.textbbox((0, 0), word, font=tf)
    ww = bb[2] - bb[0]

    # Center the [face | gap | wordmark] group horizontally in the canvas.
    group_w = FACE_DIAM + GAP + ww
    group_left = CX - group_w / 2.0

    # Face: paste so the VISIBLE face (not the tile padding) starts at group_left.
    tile_x = round(group_left - margin)
    tile_y = round(CY - tile_px / 2.0)
    img.paste(tile, (tile_x, tile_y), tile)

    # Wordmark: vertically centered on CY, placed after face + gap.
    wm_x = group_left + FACE_DIAM + GAP
    tx = round(wm_x - bb[0])
    ty = round(CY - (bb[1] + bb[3]) / 2.0)
    d.text((tx, ty), word, font=tf, fill=OFFWHITE)

    img.save(OUT)

    # Report element bounds for safe-zone verification.
    face_l, face_r = group_left, group_left + FACE_DIAM
    face_t, face_b = CY - FACE_DIAM / 2, CY + FACE_DIAM / 2
    wm_l, wm_r = wm_x, wm_x + ww
    wm_t, wm_b = ty + bb[1], ty + bb[3]
    print(f"saved {OUT} ({W}x{H})")
    print(f"safe zone: L={SAFE_L} R={SAFE_R} T={SAFE_T} B={SAFE_B}")
    print(f"face  : x {face_l:.0f}..{face_r:.0f}  y {face_t:.0f}..{face_b:.0f}")
    print(f"word  : x {wm_l:.0f}..{wm_r:.0f}  y {wm_t:.0f}..{wm_b:.0f}  (w={ww})")
    inside = (face_l >= SAFE_L and wm_r <= SAFE_R and
              face_t >= SAFE_T and face_b <= SAFE_B and
              wm_t >= SAFE_T and wm_b <= SAFE_B)
    print(f"all inside safe zone: {inside}")


if __name__ == "__main__":
    main()
