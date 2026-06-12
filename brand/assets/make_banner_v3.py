#!/usr/bin/env python3
"""Generate Playedd channel banner v3 — v2 lockup + tagline.

Same dark charcoal bg and face|PLAYEDD lockup as make_banner_v2.py, but the
logo group is nudged up to make room for a brand-red tagline line below it:
"DAILY MIND-BENDERS · WEEKLY DEEP DIVES" — flagging both lanes (daily shorts +
weekly long-form). Everything stays inside the YouTube safe zone (the center
strip that shows on every device).
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

random.seed(11)  # same seed family as make_playedd.py for a matching wobble

HERE = Path(__file__).resolve().parent
FONTS = HERE / "fonts"
OUT = HERE / "banner_playedd_v3_2560x1440.png"

CHARCOAL = (26, 26, 26)     # #1A1A1A background
OFFWHITE = (250, 249, 244)  # #FAF9F4 strokes + wordmark
RED = (201, 48, 32)         # brand red (matches the CTA card)

W, H = 2560, 1440
SAFE_W, SAFE_H = 1546, 423
SAFE_L = (W - SAFE_W) // 2      # 507
SAFE_R = SAFE_L + SAFE_W        # 2053
SAFE_T = (H - SAFE_H) // 2      # 508
SAFE_B = SAFE_T + SAFE_H        # 931
CX, CY = W // 2, H // 2         # 1280, 720

AVATAR_R = 235          # native avatar radius (do not change: sets proportions)
FACE_DIAM = 250         # target on-banner face diameter (smaller than v2 to fit tagline)
WORD_SIZE = 150         # PLAYEDD marker size
GAP = 100               # space between face and wordmark
GROUP_CY = 648          # logo group vertical center (nudged up from CY for the tagline)
TAGLINE = "DAILY MIND-BENDERS · WEEKLY DEEP DIVES"
TAG_CY = 858            # tagline vertical center


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
    pad = 40
    t = 2 * AVATAR_R + 2 * pad
    tile = Image.new("RGBA", (t, t), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    face(td, t // 2, t // 2, AVATAR_R, stroke=OFFWHITE, mood="dismay")
    scale = FACE_DIAM / (2 * AVATAR_R)
    new = round(t * scale)
    tile = tile.resize((new, new), Image.BICUBIC)
    margin = (new - FACE_DIAM) / 2.0
    return tile, new, margin


def fit_tagline(d, text, max_w, start=78, lo=40):
    size = start
    while size > lo:
        f = marker(size)
        if d.textbbox((0, 0), text, font=f)[2] <= max_w:
            return f
        size -= 2
    return marker(lo)


def main():
    img = Image.new("RGB", (W, H), CHARCOAL)
    d = ImageDraw.Draw(img)

    tile, tile_px, margin = build_face_tile()

    tf = marker(WORD_SIZE)
    word = "PLAYEDD"
    bb = d.textbbox((0, 0), word, font=tf)
    ww = bb[2] - bb[0]

    # Center the [face | gap | wordmark] group horizontally; vertical center = GROUP_CY.
    group_w = FACE_DIAM + GAP + ww
    group_left = CX - group_w / 2.0

    tile_x = round(group_left - margin)
    tile_y = round(GROUP_CY - tile_px / 2.0)
    img.paste(tile, (tile_x, tile_y), tile)

    wm_x = group_left + FACE_DIAM + GAP
    tx = round(wm_x - bb[0])
    ty = round(GROUP_CY - (bb[1] + bb[3]) / 2.0)
    d.text((tx, ty), word, font=tf, fill=OFFWHITE)

    # Tagline: brand red, centered horizontally, auto-fit inside the safe width.
    tagf = fit_tagline(d, TAGLINE, int(SAFE_W * 0.95))
    tb = d.textbbox((0, 0), TAGLINE, font=tagf)
    tag_x = round(CX - (tb[2] - tb[0]) / 2.0 - tb[0])
    tag_y = round(TAG_CY - (tb[1] + tb[3]) / 2.0)
    d.text((tag_x, tag_y), TAGLINE, font=tagf, fill=RED)

    img.save(OUT)

    # Report bounds for safe-zone verification.
    face_l, face_r = group_left, group_left + FACE_DIAM
    face_t, face_b = GROUP_CY - FACE_DIAM / 2, GROUP_CY + FACE_DIAM / 2
    tag_l, tag_r = tag_x + tb[0], tag_x + tb[2]
    tag_t, tag_b = tag_y + tb[1], tag_y + tb[3]
    print(f"saved {OUT} ({W}x{H})")
    print(f"safe zone: L={SAFE_L} R={SAFE_R} T={SAFE_T} B={SAFE_B}")
    print(f"face : x {face_l:.0f}..{face_r:.0f}  y {face_t:.0f}..{face_b:.0f}")
    print(f"tag  : x {tag_l:.0f}..{tag_r:.0f}  y {tag_t:.0f}..{tag_b:.0f}")
    inside = (face_l >= SAFE_L and tag_r <= SAFE_R and tag_l >= SAFE_L and
              face_t >= SAFE_T and tag_b <= SAFE_B)
    print(f"all inside safe zone: {inside}")


if __name__ == "__main__":
    main()
