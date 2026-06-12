#!/usr/bin/env python3
"""caption_short.py — burn CapCut-style captions into a built Short.

No libass needed. We transcribe the narration with whisper (word-level
timestamps), group the words into punchy 1-2 word chunks, render each chunk as
a transparent PNG (big Permanent Marker caps, white with a thick dark outline,
centered in the phone-safe lower-middle), and overlay each onto the video for
its exact time window with ffmpeg. The active text appears in sync with the
voice — the moving text is what holds the swipe.

Usage:
    python pipeline/caption_short.py shorts_daily/batch01/03_venus/03_venus.mp4 \
        --audio shorts_daily/batch01/03_venus/audio/narration.mp3 \
        --out shorts_daily/batch01/03_venus/03_venus_cap.mp4
If --audio is omitted, the audio is pulled straight from the input video.
If --out is omitted, the input is captioned in place (atomic replace).
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
FONT = ROOT / "brand" / "assets" / "fonts" / "PermanentMarker.ttf"
W, H = 1080, 1920

WHITE = (255, 255, 255)
INK = (20, 20, 20)
HILITE = (255, 214, 10)   # CapCut-ish pop accent (unused in v1 plain mode)

CY = int(H * 0.60)        # caption vertical center (phone-safe lower-middle)
MAX_W = int(W * 0.86)     # keep text clear of the side edges
START_SIZE = 132
MIN_SIZE = 64
STROKE = 11               # thick dark outline so it reads on any background


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write(p.stderr[-2000:] + "\n")
        raise SystemExit(f"command failed: {' '.join(map(str, cmd))}")
    return p


def whisper_words(audio: Path, model: str, workdir: Path):
    """Run whisper with word timestamps; return a flat list of (word, start, end)."""
    run(["whisper", str(audio), "--model", model, "--word_timestamps", "True",
         "--output_format", "json", "--output_dir", str(workdir), "--language", "en"])
    js = workdir / (audio.stem + ".json")
    data = json.loads(js.read_text())
    words = []
    for seg in data.get("segments", []):
        for w in seg.get("words", []):
            t = w.get("word", "").strip()
            if t:
                words.append((t, float(w["start"]), float(w["end"])))
    return words


def chunk(words, per=2, max_dur=1.1):
    """Group words into <=`per`-word, <=max_dur chunks for punchy on-beat captions."""
    out, cur = [], []
    for tok in words:
        cur.append(tok)
        dur = cur[-1][2] - cur[0][1]
        if len(cur) >= per or dur >= max_dur:
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    def clean(s):
        return s.upper().replace(".", "").replace(",", "").replace(";", "").replace(":", "").strip()
    return [(clean(" ".join(t[0] for t in g)), g[0][1], g[-1][2]) for g in out]


def fit_font(d, text):
    size = START_SIZE
    while size > MIN_SIZE:
        f = ImageFont.truetype(str(FONT), size)
        if d.textbbox((0, 0), text, font=f, stroke_width=STROKE)[2] <= MAX_W:
            return f
        size -= 4
    return ImageFont.truetype(str(FONT), MIN_SIZE)


def render_chunk_png(text, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = fit_font(d, text)
    bb = d.textbbox((0, 0), text, font=f, stroke_width=STROKE)
    x = (W - (bb[2] - bb[0])) // 2 - bb[0]
    y = CY - (bb[3] - bb[1]) // 2 - bb[1]
    d.text((x, y), text, font=f, fill=WHITE, stroke_width=STROKE, stroke_fill=INK)
    img.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", help="built short mp4")
    ap.add_argument("--audio", default=None, help="narration mp3 (defaults to the video's audio)")
    ap.add_argument("--out", default=None, help="output mp4 (defaults to in-place)")
    ap.add_argument("--model", default="base", help="whisper model")
    ap.add_argument("--per", type=int, default=2, help="max words per caption chunk")
    args = ap.parse_args()

    video = Path(args.video)
    out = Path(args.out) if args.out else video
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        audio = Path(args.audio) if args.audio else None
        if audio is None:
            audio = tdp / "audio.wav"
            run(["ffmpeg", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(audio)])

        words = whisper_words(audio, args.model, tdp)
        if not words:
            raise SystemExit("whisper returned no words — nothing to caption")
        chunks = chunk(words, per=args.per)

        pngs = []
        for i, (text, s, e) in enumerate(chunks):
            p = tdp / f"cap_{i:03d}.png"
            render_chunk_png(text, p)
            pngs.append((p, s, e))

        # Build the ffmpeg overlay chain: base video + one looped PNG per chunk,
        # each shown only during its [start,end) window.
        cmd = ["ffmpeg", "-y", "-i", str(video)]
        for p, _, _ in pngs:
            cmd += ["-loop", "1", "-i", str(p)]
        fc, last = [], "0:v"
        for idx, (_, s, e) in enumerate(pngs, start=1):
            nxt = f"v{idx}"
            fc.append(f"[{last}][{idx}:v]overlay=0:0:enable='between(t,{s:.3f},{e:.3f})'[{nxt}]")
            last = nxt
        filter_complex = ";".join(fc)
        tmp_out = tdp / "out.mp4"
        cmd += ["-filter_complex", filter_complex, "-map", f"[{last}]", "-map", "0:a?",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", str(tmp_out)]
        run(cmd)

        out.parent.mkdir(parents=True, exist_ok=True)
        os.replace(tmp_out, out)
    print(f"captioned -> {out}  ({len(chunks)} caption chunks)")


if __name__ == "__main__":
    main()
