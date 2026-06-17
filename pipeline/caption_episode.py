#!/usr/bin/env python3
"""caption_episode.py — burn readable bottom subtitles into a LONG-FORM episode.

Unlike the one-word CapCut captions on shorts, long-form gets calm, readable
phrase-level subtitles (~5-7 words) at the bottom. Script-locked (whisper supplies
timing, the real script supplies the words — fixes homophones like "a sense of I"
heard as "eye"). White text + dark outline reads perfectly on the moody dark art.

Usage:
    python pipeline/caption_episode.py episodes/0017_childhood-amnesia/rough_cut.mp4 \
        --audio episodes/0017_childhood-amnesia/audio/narration.mp3 \
        --script episodes/0017_childhood-amnesia/01_script.md \
        --end 388 --out episodes/0017_childhood-amnesia/rough_cut_sub.mp4
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from caption_short import whisper_words, script_tokens, align_to_script, run  # noqa: E402

FONT = ROOT / "brand" / "assets" / "fonts" / "PatrickHand.ttf"   # clean handwritten — readable for long reads
W, H = 1920, 1080
CY = int(H * 0.88)          # subtitle baseline near the bottom
MAXW = int(W * 0.86)
SIZE = 58
STROKE = 7
WHITE = (255, 255, 255)
INK = (10, 10, 10)
ENDERS = ".?!"


def lines(words, max_words=7, max_dur=3.6, min_words=4):
    """Group aligned (text,start,end) words into readable subtitle lines. Packs short
    sentences together (Logan's edit made many sentences short); only breaks on a
    sentence end once the line already has a few words, so we never flash 1-2 words."""
    out, cur = [], []
    for w in words:
        cur.append(w)
        dur = cur[-1][2] - cur[0][1]
        ends_sentence = w[0].rstrip()[-1:] in ENDERS
        if len(cur) >= max_words or dur >= max_dur or (ends_sentence and len(cur) >= min_words):
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return [(" ".join(t[0] for t in g).strip(), g[0][1], g[-1][2]) for g in out]


def render(text, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    size = SIZE
    f = ImageFont.truetype(str(FONT), size)
    while d.textbbox((0, 0), text, font=f, stroke_width=STROKE)[2] > MAXW and size > 34:
        size -= 2; f = ImageFont.truetype(str(FONT), size)
    bb = d.textbbox((0, 0), text, font=f, stroke_width=STROKE)
    x = (W - (bb[2] - bb[0])) // 2 - bb[0]
    y = CY - (bb[3] - bb[1]) // 2 - bb[1]
    d.text((x, y), text, font=f, fill=WHITE, stroke_width=STROKE, stroke_fill=INK)
    img.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--audio", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--end", type=float, default=None, help="stop subtitles at this time (s)")
    ap.add_argument("--model", default="small")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    # temp on the roomy project disk (the OS tmpfs can be tiny/full); clean up at the end
    work = Path(args.out).resolve().parent / "_subtmp"
    work.mkdir(exist_ok=True)
    try:
        words = whisper_words(Path(args.audio), args.model, work)
        words = align_to_script(words, script_tokens(Path(args.script)))
        subs = lines(words)
        if args.end is not None:
            subs = [(t, s, min(e, args.end)) for (t, s, e) in subs if s < args.end]

        # Render with drawtext (CPU-light, single pass) instead of image overlays —
        # looped-PNG overlays decode each subtitle across the WHOLE clip and are
        # brutally slow over a 6-min 1080p video. One drawtext per line, timed.
        font = str(FONT).replace("\\", "/")
        parts = []
        for i, (text, s, e) in enumerate(subs):
            tf = work / f"t_{i:03d}.txt"
            tf.write_text(text, encoding="utf-8")
            parts.append(
                f"drawtext=fontfile='{font}':textfile='{tf}':fontcolor=white:fontsize=50:"
                f"borderw=5:bordercolor=black:line_spacing=8:"
                f"x=(w-text_w)/2:y=h-170:enable='between(t,{s:.3f},{e:.3f})'")
        vf = ",".join(parts)
        run(["ffmpeg", "-y", "-i", str(args.video), "-vf", vf,
             "-c:v", "libx264", "-preset", "medium", "-crf", "19",
             "-pix_fmt", "yuv420p", "-c:a", "copy", str(args.out)])
    finally:
        import shutil
        shutil.rmtree(work, ignore_errors=True)
    print(f"subtitled -> {args.out}  ({len(subs)} lines)")


if __name__ == "__main__":
    main()
