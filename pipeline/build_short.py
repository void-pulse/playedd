#!/usr/bin/env python3
"""
build_short.py
Assemble a 9:16 vertical Short from a short narration + an ordered list of images.

- 1080x1920, 30fps. Each image is scaled to 1080 wide (keeps 16:9, ~604 tall) and
  centered vertically on a solid background, leaving empty bands top and bottom for
  captions added later in the editor.
- Images are distributed evenly across the narration (minus the CTA tail), or you
  can pass an explicit --cuts list of start times.
- A CTA end card fills the last ~3s: solid brand bg, an up-arrow, and big text
  "FULL BREAKDOWN" / "ON MY CHANNEL".
- Narration is the voice; an optional --music bed is ducked low (~-22 dB) under it.
- Atomic temp -> rename.

Usage:
    python pipeline/build_short.py short/short_narration.mp3 \
        --images img1.png img2.png ... --bg "#1A1A1A" \
        --music music/full_score.mp3 --out short/short_casino.mp4
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT_MARKER = ROOT / "brand" / "assets" / "fonts" / "PermanentMarker.ttf"

W, H, FPS = 1080, 1920, 30
CTA_SEC = 3.0
MUSIC_DB = -22.0


def ffdur(p: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
                         capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def hex_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def make_cta_card(bg_hex: str, out_png: Path):
    bg = hex_rgb(bg_hex)
    fg = (250, 249, 244)
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    cx = W // 2
    # up-arrow (head + shaft), upper-middle
    top = int(H * 0.28)
    head_w, head_h, shaft_w, shaft_h = 300, 180, 96, 200
    d.polygon([(cx - head_w // 2, top + head_h), (cx, top), (cx + head_w // 2, top + head_h)], fill=fg)
    d.rectangle([cx - shaft_w // 2, top + head_h, cx + shaft_w // 2, top + head_h + shaft_h], fill=fg)
    # text lines, auto-fit so the widest line stays within the frame margins
    lines = ["FULL BREAKDOWN", "ON MY CHANNEL"]
    max_w = int(W * 0.88)
    size = 150
    while size > 40:
        font = ImageFont.truetype(str(FONT_MARKER), size)
        widest = max(d.textbbox((0, 0), ln, font=font)[2] - d.textbbox((0, 0), ln, font=font)[0]
                     for ln in lines)
        if widest <= max_w:
            break
        size -= 4
    line_h = int(size * 1.25)
    for i, line in enumerate(lines):
        bb = d.textbbox((0, 0), line, font=font)
        w = bb[2] - bb[0]
        y = int(H * 0.50) + i * line_h
        d.text((cx - w // 2 - bb[0], y), line, font=font, fill=fg)
    img.save(out_png)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("narration", help="short narration mp3")
    ap.add_argument("--images", nargs="+", required=True, help="ordered image paths")
    ap.add_argument("--music", default=None, help="optional music bed (ducked low)")
    ap.add_argument("--bg", default="#1A1A1A", help="solid background color")
    ap.add_argument("--cuts", nargs="*", type=float, default=None,
                    help="optional explicit image start times (len == #images)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    narration = Path(args.narration)
    imgs = [Path(p) for p in args.images]
    for p in [narration, *imgs]:
        if not p.exists():
            sys.exit(f"Missing input: {p}")

    dur = ffdur(narration)
    window = max(0.5, dur - CTA_SEC)          # image region; CTA fills the tail
    n = len(imgs)

    if args.cuts and len(args.cuts) == n:
        starts = sorted(args.cuts)
        durs = [(starts[i + 1] if i + 1 < n else window) - starts[i] for i in range(n)]
    else:
        per = window / n
        durs = [round(per, 3)] * n

    tmpdir = Path(tempfile.mkdtemp())
    cta = tmpdir / "cta.png"
    make_cta_card(args.bg, cta)

    listf = tmpdir / "list.txt"
    with open(listf, "w") as f:
        for img, du in zip(imgs, durs):
            f.write(f"file '{img.resolve()}'\nduration {du}\n")
        f.write(f"file '{cta.resolve()}'\nduration {CTA_SEC}\n")
        f.write(f"file '{cta.resolve()}'\n")   # concat demuxer: repeat last

    bg = "0x" + args.bg.lstrip("#")
    vfilter = (f"[0:v]scale={W}:-2,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:{bg},"
               f"fps={FPS},format=yuv420p[v]")

    inputs = ["-f", "concat", "-safe", "0", "-i", str(listf), "-i", str(narration)]
    if args.music:
        if not Path(args.music).exists():
            sys.exit(f"Missing music: {args.music}")
        inputs += ["-stream_loop", "-1", "-i", str(args.music)]
        mus = round(10 ** (MUSIC_DB / 20.0), 4)
        fc = (vfilter + ";"
              f"[2:a]volume={mus}[m];"
              f"[1:a][m]amix=inputs=2:normalize=0:duration=first:dropout_transition=0[a]")
        amap = ["-map", "[a]"]
    else:
        fc = vfilter
        amap = ["-map", "1:a"]

    out = Path(args.out)
    tmp = out.with_suffix(out.suffix + ".tmp")
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", fc, "-map", "[v]", *amap,
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-r", str(FPS), "-t", f"{dur:.3f}",
           "-f", "mp4", "-movflags", "+faststart", str(tmp)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        tmp.unlink(missing_ok=True)
        sys.exit(f"ffmpeg failed:\n{result.stderr[-1800:]}")
    os.replace(tmp, out)

    print(f"Short -> {out}  ({ffdur(out):.1f}s, {W}x{H}, {FPS}fps, {n} images + CTA)")


if __name__ == "__main__":
    main()
