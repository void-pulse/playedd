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
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import math

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT_MARKER = ROOT / "brand" / "assets" / "fonts" / "PermanentMarker.ttf"

W, H, FPS = 1080, 1920, 30
CTA_SEC = 3.0
MUSIC_DB = -22.0
CUE_DB = -14.0   # default duck for spot SFX cues so they sit under the VO
SR = 44100


def db_to_lin(db: float) -> float:
    return round(10 ** (db / 20.0), 4)


def ffdur(p: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
                         capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def hex_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


LOGO_ASSET = ROOT / "brand" / "assets" / "avatar_800.png"


def make_cta_card(bg_hex: str, out_png: Path, challenge: str = "", heading: str = "FOR FULL,BREAKDOWN",
                  badge: str = ""):
    """Drive-to-full-video end card for the teaser Short: a big Playedd logo up top, an up-arrow,
    'FOR FULL BREAKDOWN', an optional bottom challenge line, and an optional small streak badge
    (e.g. 'DAILY WONDER #63') for the standalone daily shorts. bg_hex kept for signature
    compatibility; the card is always white."""
    INK = (34, 34, 34)
    RED = (201, 48, 32)
    card = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(card)
    cx = W // 2

    def fit(line, max_w, start=170, lo=40):
        size = start
        while size > lo:
            f = ImageFont.truetype(str(FONT_MARKER), size)
            if d.textbbox((0, 0), line, font=f)[2] <= max_w:
                return f
            size -= 4
        return ImageFont.truetype(str(FONT_MARKER), lo)

    def centered(line, y, font, fill):
        bb = d.textbbox((0, 0), line, font=font)
        d.text((cx - (bb[2] - bb[0]) // 2 - bb[0], y), line, font=font, fill=fill)
        return bb[3] - bb[1]

    # Playedd logo (drop the cream/near-white bg), big, centered near the top
    if LOGO_ASSET.exists():
        logo = Image.open(LOGO_ASSET).convert("RGBA")
        px = logo.load()
        for yy in range(logo.height):
            for xx in range(logo.width):
                r, g, b, a = px[xx, yy]
                if r > 232 and g > 230 and b > 222:
                    px[xx, yy] = (r, g, b, 0)
        side = int(W * 0.66)                       # big logo (room for the badge below it)
        logo = logo.resize((side, side), Image.LANCZOS)
        card.paste(logo, (cx - side // 2, int(H * 0.09)), logo)

    # challenge like-bait line up near the logo ("HEAD: body" -> red head + black body)
    if challenge:
        head, _, body = challenge.partition(":")
        yc = int(H * 0.33)
        yc += centered(head.strip(), yc, fit(head.strip(), int(W * 0.86), start=92), RED) + 22
        if body.strip():
            fb = ImageFont.truetype(str(FONT_MARKER), 56)
            lines, cur = [], ""
            for w in body.strip().split():
                t = (cur + " " + w).strip()
                if d.textbbox((0, 0), t, font=fb)[2] <= int(W * 0.9):
                    cur = t
                else:
                    lines.append(cur); cur = w
            if cur:
                lines.append(cur)
            for ln in lines:
                yc += centered(ln, yc, fb, INK) + 14

    # streak/series badge (e.g. "DAILY WONDER #63") ABOVE the heading, in brand red
    if badge:
        centered(badge, int(H * 0.485), fit(badge, int(W * 0.74), start=74, lo=46), RED)

    # heading (e.g. BECOME A STAN / FOR FULL BREAKDOWN) below the badge, above the arrow
    y = int(H * 0.555)
    for line in [x.strip() for x in heading.split(",") if x.strip()]:
        f = fit(line, int(W * 0.82), start=132)
        y += centered(line, y, f, INK) + 30

    # thick CURVED arrow with a CLEAN sharp tip, aimed at the video-link row ~15% in from the
    # left edge with a gentle (not steep) angle. The rounded stroke stops at the arrowhead's neck
    # so the round joints never blunt the tip.
    p0 = (int(W * 0.43), int(H * 0.78))   # tail (short arrow), under the heading
    pc = (int(W * 0.32), int(H * 0.855))  # control bows the curve DOWN toward the bottom-left
    p2 = (int(W * 0.21), int(H * 0.93))   # head tip: low near the bottom, ~20% from the left edge
    width = 16
    N = 64
    pts = [(
        (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * pc[0] + t * t * p2[0],
        (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * pc[1] + t * t * p2[1],
    ) for t in (i / N for i in range(N + 1))]
    ax, ay = pts[-1][0] - pts[-7][0], pts[-1][1] - pts[-7][1]   # smooth tip tangent (avoids a kink)
    al = math.hypot(ax, ay) or 1.0
    ux, uy = ax / al, ay / al
    head_len, half_w = 64, 36
    neck = (p2[0] - ux * head_len, p2[1] - uy * head_len)
    stroke = [p for p in pts if math.hypot(p[0] - p2[0], p[1] - p2[1]) > head_len] + [neck]
    d.line(stroke, fill=RED, width=width, joint="curve")
    r = width / 2                          # round the stroke so the curve reads smooth and thick
    for (x, y) in stroke:
        d.ellipse([x - r, y - r, x + r, y + r], fill=RED)
    perpx, perpy = -uy, ux                 # clean sharp arrowhead from the neck to the tip
    d.polygon([p2,
               (neck[0] + perpx * half_w, neck[1] + perpy * half_w),
               (neck[0] - perpx * half_w, neck[1] - perpy * half_w)], fill=RED)

    card.save(out_png)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("narration", help="short narration mp3")
    ap.add_argument("--images", nargs="+", required=True, help="ordered image paths")
    ap.add_argument("--music", default=None, help="optional music bed (ducked low)")
    ap.add_argument("--bg", default="#1A1A1A", help="solid background color")
    ap.add_argument("--cta-line", default="", help="optional bottom challenge line on the CTA card, e.g. 'LAZY CHALLENGE: like this video'")
    ap.add_argument("--cta-heading", default="FOR FULL,BREAKDOWN", help="comma-split CTA heading lines")
    ap.add_argument("--badge", default="", help="small streak/series badge on the CTA card, e.g. 'DAILY WONDER #63'")
    ap.add_argument("--cuts", nargs="*", type=float, default=None,
                    help="optional explicit image start times (len == #images)")
    ap.add_argument("--cta-sec", type=float, default=CTA_SEC,
                    help="seconds the CTA/stamp end card holds during the narration")
    ap.add_argument("--tail", type=float, default=0.0,
                    help="extra seconds to hold the end card AFTER narration ends "
                         "(music tails under it and fades out)")
    ap.add_argument("--stamp-sfx", default=None,
                    help="one-shot SFX mixed in at the moment the stamp end card appears")
    ap.add_argument("--sfx-cues", default=None,
                    help="JSON list of {file, at, gain_db} spot SFX mixed into the "
                         "timeline at those times, kept subtle/low under the VO")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    narration = Path(args.narration)
    imgs = [Path(p) for p in args.images]
    for p in [narration, *imgs]:
        if not p.exists():
            sys.exit(f"Missing input: {p}")

    dur = ffdur(narration)
    cta_sec = args.cta_sec
    tail = max(0.0, args.tail)
    total = dur + tail                        # the end card is held for `tail` past narration
    window = max(0.5, dur - cta_sec)          # image region; end card fills the rest
    n = len(imgs)

    if args.cuts and len(args.cuts) == n:
        starts = sorted(args.cuts)
        durs = [(starts[i + 1] if i + 1 < n else window) - starts[i] for i in range(n)]
    else:
        per = window / n
        durs = [round(per, 3)] * n

    tmpdir = Path(tempfile.mkdtemp())
    cta = tmpdir / "cta.png"
    make_cta_card(args.bg, cta, args.cta_line, args.cta_heading, args.badge)

    listf = tmpdir / "list.txt"
    with open(listf, "w") as f:
        for img, du in zip(imgs, durs):
            f.write(f"file '{img.resolve()}'\nduration {du}\n")
        f.write(f"file '{cta.resolve()}'\nduration {round(cta_sec + tail, 3)}\n")  # hold through tail
        f.write(f"file '{cta.resolve()}'\n")   # concat demuxer: repeat last

    bg = "0x" + args.bg.lstrip("#")
    # If the source images are already ~9:16 (vertical-native), place them FULL-BLEED
    # (scale to cover, no letterbox). Otherwise letterbox 16:9 on the bg with bands.
    iw0, ih0 = Image.open(imgs[0]).size
    portrait = (ih0 / iw0) > 1.3
    if portrait:
        scale_body = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS},format=yuv420p"
        mode = "full-bleed (9:16 native)"
    else:
        scale_body = f"scale={W}:-2,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:{bg},setsar=1,fps={FPS},format=yuv420p"
        mode = "letterbox (16:9 on bg)"
    # Render the picture track with the concat FILTER, not the demuxer: the concat demuxer
    # silently drops / mis-times still frames (observed: it dropped the last vignette frame).
    previd = tmpdir / "video.mp4"
    frames = list(zip(imgs, durs)) + [(cta, round(cta_sec + tail, 3))]
    vin, vparts = [], []
    for k, (img, du) in enumerate(frames):
        vin += ["-loop", "1", "-t", f"{du}", "-i", str(img)]
        vparts.append(f"[{k}:v]{scale_body}[v{k}]")
    vparts.append("".join(f"[v{k}]" for k in range(len(frames))) + f"concat=n={len(frames)}:v=1[v]")
    vr = subprocess.run(["ffmpeg", "-y", *vin, "-filter_complex", ";".join(vparts), "-map", "[v]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-f", "mp4", str(previd)], capture_output=True, text=True)
    if vr.returncode != 0:
        sys.exit(f"video pre-render failed:\n{vr.stderr[-1800:]}")
    vfilter = f"[0:v]fps={FPS},format=yuv420p[v]"   # picture track pre-rendered; just normalize

    # optional spot SFX cues and a stamp one-shot (mixed under the VO)
    cues = []
    if args.sfx_cues:
        for c in json.loads(Path(args.sfx_cues).read_text()):
            cp = Path(c["file"])
            if not cp.exists():
                sys.exit(f"Missing sfx cue file: {cp}")
            cues.append({"file": cp, "at": float(c["at"]),
                         "gain_db": float(c.get("gain_db", CUE_DB))})
    stamp_sfx = Path(args.stamp_sfx) if args.stamp_sfx else None
    if stamp_sfx and not stamp_sfx.exists():
        sys.exit(f"Missing stamp sfx: {stamp_sfx}")

    inputs = ["-i", str(previd), "-i", str(narration)]

    if not cues and not stamp_sfx:
        # ---------- original behavior, preserved byte-for-byte ----------
        if args.music:
            if not Path(args.music).exists():
                sys.exit(f"Missing music: {args.music}")
            inputs += ["-stream_loop", "-1", "-i", str(args.music)]
            mus = db_to_lin(MUSIC_DB)
            if tail > 0:
                fade = round(min(2.0, tail + 0.6), 2)   # fade the music tail out into silence
                fc = (vfilter + ";"
                      f"[1:a]apad,atrim=0:{total:.3f},asetpts=N/SR/TB[n];"
                      f"[2:a]atrim=0:{total:.3f},asetpts=N/SR/TB,volume={mus},"
                      f"afade=t=out:st={round(total - fade, 3)}:d={fade}[m];"
                      f"[n][m]amix=inputs=2:normalize=0:duration=first:dropout_transition=0[a]")
            else:
                fc = (vfilter + ";"
                      f"[2:a]volume={mus}[m];"
                      f"[1:a][m]amix=inputs=2:normalize=0:duration=first:dropout_transition=0[a]")
            amap = ["-map", "[a]"]
        else:
            if tail > 0:
                fc = vfilter + f";[1:a]apad,atrim=0:{total:.3f},asetpts=N/SR/TB[a]"
                amap = ["-map", "[a]"]
            else:
                fc = vfilter
                amap = ["-map", "1:a"]
    else:
        # ---------- general mix: VO (full) + ducked spot cues + stamp SFX [+ ducked music] ----------
        parts, labels = [], []
        # VO is input 1; always padded to `total` so the tail has a silent bed for the stamp
        parts.append(f"[1:a]aformat=sample_rates={SR}:channel_layouts=stereo,"
                     f"apad,atrim=0:{total:.3f},asetpts=N/SR/TB[vo]")
        labels.append("[vo]")
        idx = 2
        if args.music:
            if not Path(args.music).exists():
                sys.exit(f"Missing music: {args.music}")
            inputs += ["-stream_loop", "-1", "-i", str(args.music)]
            mus = db_to_lin(MUSIC_DB)
            base = (f"[{idx}:a]aformat=sample_rates={SR}:channel_layouts=stereo,"
                    f"atrim=0:{total:.3f},asetpts=N/SR/TB,volume={mus}")
            if tail > 0:
                fade = round(min(2.0, tail + 0.6), 2)
                base += f",afade=t=out:st={round(total - fade, 3)}:d={fade}"
            parts.append(base + "[mus]")
            labels.append("[mus]")
            idx += 1
        for i, c in enumerate(cues):
            inputs += ["-i", str(c["file"])]
            ms = max(0, int(round(c["at"] * 1000)))
            parts.append(f"[{idx}:a]aformat=sample_rates={SR}:channel_layouts=stereo,"
                         f"volume={db_to_lin(c['gain_db'])},adelay={ms}:all=1[c{i}]")
            labels.append(f"[c{i}]")
            idx += 1
        if stamp_sfx:
            inputs += ["-i", str(stamp_sfx)]
            ms = max(0, int(round(window * 1000)))   # stamp lands when the image region ends
            parts.append(f"[{idx}:a]aformat=sample_rates={SR}:channel_layouts=stereo,"
                         f"adelay={ms}:all=1[st]")
            labels.append("[st]")
            idx += 1
        parts.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:"
                     f"duration=longest:dropout_transition=0,atrim=0:{total:.3f},"
                     f"alimiter=limit=0.95:level=false[a]")
        fc = vfilter + ";" + ";".join(parts)
        amap = ["-map", "[a]"]

    out = Path(args.out)
    tmp = out.with_suffix(out.suffix + ".tmp")
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", fc, "-map", "[v]", *amap,
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-r", str(FPS), "-t", f"{total:.3f}",
           "-f", "mp4", "-movflags", "+faststart", str(tmp)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        tmp.unlink(missing_ok=True)
        sys.exit(f"ffmpeg failed:\n{result.stderr[-1800:]}")
    os.replace(tmp, out)

    print(f"Short -> {out}  ({ffdur(out):.1f}s, {W}x{H}, {FPS}fps, {n} images + CTA, {mode})")


if __name__ == "__main__":
    main()
