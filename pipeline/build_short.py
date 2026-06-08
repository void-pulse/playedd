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


def make_cta_card(bg_hex: str, out_png: Path):
    """Channel stamp end card: big red tilted 'YOU'RE BEING PLAYED' over a white
    card, with 'full story on my channel' and an up-arrow beneath. bg_hex unused
    (the stamp card is always white)."""
    RED = (201, 48, 32)
    INK = (34, 34, 34)
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    cx = W // 2

    # auto-fit the stamp text to the frame width
    stamp = "YOU'RE BEING PLAYED"
    max_w = int(W * 0.72)
    size = 180
    while size > 40:
        font = ImageFont.truetype(str(FONT_MARKER), size)
        bb = d.textbbox((0, 0), stamp, font=font)
        if (bb[2] - bb[0]) <= max_w:
            break
        size -= 4
    bb = d.textbbox((0, 0), stamp, font=font)
    tw, th, pad = bb[2] - bb[0], bb[3] - bb[1], 48
    layer = Image.new("RGBA", (tw + pad * 2 + 28, th + pad * 2 + 28), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rectangle([14, 14, 14 + tw + pad * 2, 14 + th + pad * 2], outline=RED, width=14)  # stamp box
    ld.text((14 + pad - bb[0], 14 + pad - bb[1]), stamp, font=font, fill=RED)
    layer = layer.rotate(7, expand=True, resample=Image.BICUBIC)                          # slammed tilt
    img.paste(layer, (cx - layer.width // 2, int(H * 0.30)), layer)

    # up-arrow beneath the stamp
    top = int(H * 0.58)
    hw, hh, sw, sh = 210, 120, 64, 150
    d.polygon([(cx - hw // 2, top + hh), (cx, top), (cx + hw // 2, top + hh)], fill=INK)
    d.rectangle([cx - sw // 2, top + hh, cx + sw // 2, top + hh + sh], fill=INK)

    # subline
    sub = "full story on my channel"
    sub_w = int(W * 0.78)
    ssize = 72
    while ssize > 28:
        sfont = ImageFont.truetype(str(FONT_MARKER), ssize)
        sb = d.textbbox((0, 0), sub, font=sfont)
        if (sb[2] - sb[0]) <= sub_w:
            break
        ssize -= 4
    sb = d.textbbox((0, 0), sub, font=sfont)
    d.text((cx - (sb[2] - sb[0]) // 2 - sb[0], int(H * 0.72)), sub, font=sfont, fill=INK)
    img.save(out_png)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("narration", help="short narration mp3")
    ap.add_argument("--images", nargs="+", required=True, help="ordered image paths")
    ap.add_argument("--music", default=None, help="optional music bed (ducked low)")
    ap.add_argument("--bg", default="#1A1A1A", help="solid background color")
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
    make_cta_card(args.bg, cta)

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
